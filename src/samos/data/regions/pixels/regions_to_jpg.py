#!/usr/bin/env python3
"""Render DS9 pixel-coordinate SAMOS masks as individual monochrome JPG previews.

Standalone utility: no SAMOS imports, no GUI, no astropy, no FITS images.
Requires Pillow (PIL).  Never modifies .reg files.

Default: use a fixed 1056 x 1032 SISI detector frame, so each mask retains
its absolute (X,Y) position. Oversized long slits are clipped to the frame.
Optional --fitting auto/fit can zoom unusually positioned engineering masks.  Unknown celestial frames are
rejected instead of being silently plotted as detector coordinates.
"""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from dataclasses import dataclass
from typing import List, Tuple

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("ERROR: Pillow is needed. In conda env 'samos', run: python -m pip install pillow")

NUMBER_PATTERN = re.compile(r'^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$')
REGION_PATTERN = re.compile(r'([+-]?)([A-Za-z][\w]*)\s*\(([^)]*)\)')
SKIP_TOKENS = {"global", "#", "", "image", "physical", "linear", "fk5", "icrs", "galactic", "wcs", "wcsa", "wcsb"}
PIXEL_FRAMES = {"image", "physical", "linear"}
NONPIXEL_FRAMES = {"fk5", "icrs", "galactic", "wcs", "wcsa", "wcsb", "ecliptic"}
Point = Tuple[float, float]


@dataclass
class Region:
    kind: str
    values: Tuple[float, ...]
    excluded: bool = False


@dataclass
class ParsedRegions:
    regions: List[Region]
    unsupported: List[str]
    coordinate_system: str


def _num(value: str) -> float:
    value = value.strip()
    # DS9 image/physical coordinates may have an explicit pixel (p) suffix.
    if value.endswith("p"):
        value = value[:-1]
    if not NUMBER_PATTERN.fullmatch(value):
        raise ValueError("not a detector-pixel number: {!r}".format(value))
    result = float(value)
    if not math.isfinite(result):
        raise ValueError("nonfinite coordinate")
    return result


def parse_regions(text: str) -> ParsedRegions:
    regions: List[Region] = []
    unsupported: List[str] = []
    frame = "image"  # DS9 defaults to physical; our masks are in image pixels.
    for n, original in enumerate(text.splitlines(), 1):
        content = original.split("#", 1)[0].strip()
        if not content:
            continue
        # DS9 permits "image; box(...); circle(...)" on one line.
        for item in content.split(";"):
            item = item.strip()
            if not item:
                continue
            name = item.lower()
            if name in PIXEL_FRAMES or name in NONPIXEL_FRAMES:
                frame = name
                continue
            if name.startswith("global"):
                continue
            if frame in NONPIXEL_FRAMES:
                raise ValueError("line {} uses {} coordinates, not SISI pixels".format(n, frame))
            match = REGION_PATTERN.fullmatch(item)
            if match is None:
                unsupported.append("line {}: {}".format(n, item[:75]))
                continue
            sign, shape, args = match.groups()
            shape = shape.lower()
            if shape not in {"box", "rotbox", "circle", "ellipse", "line", "polygon", "point", "annulus"}:
                unsupported.append("line {}: {}".format(n, shape))
                continue
            try:
                coords = tuple(_num(s) for s in args.split(","))
            except ValueError as e:
                unsupported.append("line {}: {} ({})".format(n, shape, e))
                continue
            if shape in {"box", "rotbox"} and len(coords) not in {4, 5}:
                unsupported.append("line {}: {} requires 4 or 5 arguments".format(n, shape))
                continue
            if shape == "circle" and len(coords) != 3:
                unsupported.append("line {}: circle requires 3 arguments".format(n))
                continue
            if shape == "ellipse" and len(coords) not in {4, 5}:
                unsupported.append("line {}: ellipse requires 4 or 5 arguments".format(n))
                continue
            if shape == "line" and len(coords) != 4:
                unsupported.append("line {}: line requires 4 arguments".format(n))
                continue
            if shape == "point" and len(coords) != 2:
                unsupported.append("line {}: point requires 2 arguments".format(n))
                continue
            if shape == "polygon" and (len(coords) < 6 or len(coords) % 2):
                unsupported.append("line {}: polygon requires three or more (x,y) pairs".format(n))
                continue
            if shape == "annulus" and len(coords) < 4:
                unsupported.append("line {}: annulus requires center and radii".format(n))
                continue
            if shape in {"box", "rotbox", "ellipse"}:
                if coords[2] == 0 or coords[3] == 0:
                    unsupported.append("line {}: zero width/height".format(n))
                    continue
                # Historical SAMOS engineering .reg files can contain a
                # negative DS9 box width. Its absolute size is sufficient for
                # this outline-only cartoon; never change the input .reg file.
                if coords[2] < 0 or coords[3] < 0:
                    coords = coords[:2] + (abs(coords[2]),abs(coords[3])) + coords[4:]
            if shape in {"circle", "annulus"} and any(v <= 0 for v in coords[2:]):
                unsupported.append("line {}: nonpositive radius".format(n))
                continue
            regions.append(Region(shape, coords, excluded=(sign == "-")))
    return ParsedRegions(regions, unsupported, frame)


def rotated_points(x: float, y: float, hx: float, hy: float, degrees: float) -> List[Point]:
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    corners = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    return [(x + u*c - v*s, y + u*s + v*c) for u,v in corners]


def ellipse_points(x: float, y: float, rx: float, ry: float, degrees: float, samples: int=72) -> List[Point]:
    a = math.radians(degrees)
    c,s = math.cos(a), math.sin(a)
    p = []
    for k in range(samples):
        t = 2 * math.pi * k / samples
        u,v = rx*math.cos(t), ry*math.sin(t)
        p.append((x + u*c - v*s, y + u*s + v*c))
    return p


def geometry_points(region: Region) -> List[Point]:
    v = region.values
    if region.kind in {"box", "rotbox"}:
        return rotated_points(v[0],v[1],v[2]/2,v[3]/2,v[4] if len(v)>4 else 0)
    if region.kind == "ellipse":
        return ellipse_points(v[0],v[1],v[2],v[3],v[4] if len(v)>4 else 0)
    if region.kind == "circle":
        return ellipse_points(v[0],v[1],v[2],v[2],0)
    if region.kind == "annulus":
        return ellipse_points(v[0],v[1],max(v[2:]),max(v[2:]),0)
    if region.kind == "polygon":
        return list(zip(v[::2],v[1::2]))
    if region.kind == "line":
        return [(v[0],v[1]),(v[2],v[3])]
    if region.kind == "point":
        return [(v[0],v[1])]
    return []


def view_bounds(parsed: ParsedRegions, frame_width: float, frame_height: float,
                fitting: str) -> Tuple[Tuple[float,float,float,float], str]:
    # Coordinates are in the DS9 image frame, 1-indexed bottom-left origin.
    standard = (0.5, frame_width + 0.5, 0.5, frame_height + 0.5)
    if fitting == "fixed" or not parsed.regions:
        return standard, "fixed"
    positions = [p for reg in parsed.regions for p in geometry_points(reg)]
    if not positions:
        return standard, "fixed"
    xs,ys = zip(*positions)
    x0,x1,y0,y1 = min(xs),max(xs),min(ys),max(ys)
    if fitting == "auto":
        # Normal science masks must share the same detector scale/orientation.
        # Only engineering patterns significantly outside the detector auto-fit.
        if x0 >= -0.05*frame_width and x1 <= 1.05*frame_width and y0 >= -0.05*frame_height and y1 <= 1.05*frame_height:
            return standard, "fixed"
    dx,dy = max(x1-x0,1.0),max(y1-y0,1.0)
    side = max(dx,dy) * 1.06  # physical aspect ratio stays correct in square image
    midx,midy = (x0+x1)/2,(y0+y1)/2
    return (midx-side/2,midx+side/2,midy-side/2,midy+side/2), "fit"


def render(parsed: ParsedRegions, size: int=1024, frame_width: float=1056,
           frame_height: float=1032, fitting: str="fixed", margin: int=20,
           line_width: int=2) -> Tuple[Image.Image, str]:
    if size < 64 or margin*2 >= size or line_width < 1:
        raise ValueError("invalid output size/margin/line width")
    img = Image.new("L", (size,size), 0)
    draw = ImageDraw.Draw(img)
    bounds, actual_mode = view_bounds(parsed,frame_width,frame_height,fitting)
    x0,x1,y0,y1 = bounds
    scale = (size-2*margin)/max(x1-x0, y1-y0)
    # Center the field, with pixel y increasing upwards (DS9 'image').
    centerx,centery = (x0+x1)/2,(y0+y1)/2
    center_display = size/2
    def project(pt: Point) -> Point:
        return (center_display + (pt[0]-centerx)*scale,
                center_display - (pt[1]-centery)*scale)
    for reg in parsed.regions:
        if reg.excluded:
            # An excluded DS9 region is not an illuminated slit; rendering its
            # perimeter in white would be misleading.
            continue
        pts = [project(p) for p in geometry_points(reg)]
        if reg.kind in {"box","rotbox","ellipse","circle","polygon","annulus"}:
            if len(pts)>=3:
                draw.line(pts+[pts[0]],fill=255,width=line_width,joint="curve")
            if reg.kind == "annulus":
                for radius in reg.values[2:-1]:
                    pp = [project(p) for p in ellipse_points(reg.values[0],reg.values[1],radius,radius,0)]
                    draw.line(pp+[pp[0]],fill=255,width=line_width)
        elif reg.kind == "line":
            draw.line(pts,fill=255,width=line_width)
        elif reg.kind == "point":
            # Small cross is recognizable even on a 1024-pixel thumbnail.
            px,py = pts[0]
            d = max(3,line_width*2)
            draw.line([(px-d,py),(px+d,py)],fill=255,width=line_width)
            draw.line([(px,py-d),(px,py+d)],fill=255,width=line_width)
    return img, actual_mode


def jpg_path(reg_path: Path, output_mode: str) -> Path:
    if output_mode == "sibling":
        return reg_path.with_suffix(".jpg")
    return reg_path.parent / "previews" / (reg_path.stem+".jpg")


def save_atomic(img: Image.Image, destination: Path, quality: int) -> None:
    destination.parent.mkdir(parents=True,exist_ok=True)
    if destination.is_symlink():
        raise ValueError("refusing symlink destination: {}".format(destination))
    fd,tmppath = tempfile.mkstemp(prefix=".samos_preview_",suffix=".jpg",dir=str(destination.parent))
    try:
        with os.fdopen(fd,"wb") as f:
            img.save(f,format="JPEG",quality=quality,optimize=True)
        os.replace(tmppath, destination)
    finally:
        if os.path.exists(tmppath):
            os.unlink(tmppath)


def collect_masks(root: Path, recursive: bool) -> List[Path]:
    paths = root.rglob("*.reg") if recursive else root.glob("*.reg")
    # Do not follow symlinked files; avoid writing outside a Box-managed repo.
    return sorted((p for p in paths if p.is_file() and not p.is_symlink()),key=lambda p:str(p).lower())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One B&W JPG beside each DS9 pixel mask; never edit .reg files.")
    parser.add_argument("root",nargs="?",default=Path(__file__).resolve().parent,
                        help="regions/pixels folder (default: folder containing this script)")
    parser.add_argument("--root",dest="root_override",help="Alternative to positional root argument")
    parser.add_argument("--apply",action="store_true",help="Actually write JPGs (otherwise dry run)")
    parser.add_argument("--overwrite",action="store_true",help="Regenerate existing JPGs (only with --apply)")
    parser.add_argument("--output-mode",choices=["sibling","previews"],default="sibling",
                        help="Siblings of .reg (default) or local previews/ subfolder")
    parser.add_argument("--recursive",action="store_true",default=True,
                        help="Include all subfolders (default)")
    parser.add_argument("--top-only",dest="recursive",action="store_false",help="Only process root directory")
    parser.add_argument("--size",type=int,default=1024,help="Square JPEG size in pixels (default 1024)")
    parser.add_argument("--frame-width",type=float,default=1056,help="SISI detector X extent (default 1056)")
    parser.add_argument("--frame-height",type=float,default=1032,help="SISI detector Y extent (default 1032)")
    parser.add_argument("--fitting",choices=["auto","fixed","fit"],default="fixed",
                        help="fixed detector coordinates (default); auto/fit are optional zoom modes")
    parser.add_argument("--margin",type=int,default=20)
    parser.add_argument("--line-width",type=int,default=2)
    parser.add_argument("--quality",type=int,default=95)
    parser.add_argument("--verbose",action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root_override or args.root).expanduser().resolve()
    if "SAMOS_SC3_MAIN" in root.parts:
        parser.error("Refusing SAMOS_SC3_MAIN. Operate on DEV only.")
    if not root.is_dir():
        parser.error("Region directory does not exist: {}".format(root))
    if args.size < 64 or args.size > 8192 or args.frame_width <= 0 or args.frame_height <= 0:
        parser.error("Invalid size or frame dimensions")
    if not (1 <= args.quality <= 100):
        parser.error("JPEG quality must be 1 to 100")
    region_paths = collect_masks(root,args.recursive)
    stats = {"created":0,"updated":0,"would_create":0,"would_update":0,"existing":0,"failed":0,"unsupported":0,"empty":0,"fitted":0}
    print("ROOT:",root)
    print("MASKS:",len(region_paths)," | mode:",args.output_mode," | recursive:",args.recursive)
    print("ACTION:","WRITE JPGs" if args.apply else "DRY RUN (no files written)")
    for reg_path in region_paths:
        target = jpg_path(reg_path,args.output_mode)
        relative = reg_path.relative_to(root)
        if target.is_symlink():
            print("ERROR:",relative,"-> symlink destination refused",file=sys.stderr)
            stats["failed"]+=1
            continue
        exists = target.exists()
        if exists and not args.overwrite:
            stats["existing"]+=1
            if args.verbose:print("SKIP existing:",relative)
            continue
        try:
            parsed = parse_regions(reg_path.read_text(encoding="utf-8-sig"))
            if parsed.unsupported:
                stats["unsupported"]+=1
                # Strict: don't create an incomplete / misleading preview.
                raise ValueError("unsupported lines: " + "; ".join(parsed.unsupported[:3]))
            if any(r.excluded for r in parsed.regions):
                raise ValueError("excluded DS9 regions present; no misleading partial JPG generated")
            if not parsed.regions:stats["empty"]+=1
            bounds,fit_mode = view_bounds(parsed,args.frame_width,args.frame_height,args.fitting)
            if fit_mode=="fit":stats["fitted"]+=1
            action=("REPLACE" if exists else "CREATE")
            if args.verbose or fit_mode == "fit":
                print("{}: {} -> {}  [{}; {} shapes]".format(action,relative,target.relative_to(root),fit_mode,len(parsed.regions)))
            if args.apply:
                img,_=render(parsed,size=args.size,frame_width=args.frame_width,
                             frame_height=args.frame_height,fitting=args.fitting,
                             margin=args.margin,line_width=args.line_width)
                save_atomic(img,target,args.quality)
                stats["updated" if exists else "created"]+=1
            else:
                stats["would_update" if exists else "would_create"]+=1
        except (OSError,ValueError,UnicodeError) as error:
            print("ERROR:",relative,":",error,file=sys.stderr)
            stats["failed"]+=1
    print("RESULT:","; ".join("{}={}".format(k,v) for k,v in stats.items()))
    if stats["failed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
