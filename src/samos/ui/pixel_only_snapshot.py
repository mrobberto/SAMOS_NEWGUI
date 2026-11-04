"""Commit current Ginga pixel regions without requiring RADEC or a WCS.

Pixel-only snapshots are *not* science mask versions. They preserve the loaded
PIXEL designation (FULL, EVEN, ODD) without synthesizing missing masks.
No DMD command is issued here.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, uuid

def _safe_name(filename):
    name=Path(filename).stem
    # Keep original field+T##, drop archive version and pixel suffix.
    name=re.split(r'_v\d+\.\d+(?=_PIXEL_)',name, maxsplit=1)[0]
    name=re.split(r'(?i)_PIXEL_(?:FULL|EVEN|ODD)(?:=.*)?$',name, maxsplit=1)[0]
    name=re.split(r'(?i)_pixels(?:=.*)?$',name, maxsplit=1)[0]
    slug=re.sub(r'[^A-Za-z0-9_.-]+','_',name).strip('._-')
    if not slug or slug in ('.','..') or len(slug)>128:
        raise ValueError('Cannot infer a safe target name from PIXEL filename')
    return slug

def _role(filename):
    m=re.search(r'(?i)_PIXEL_(FULL|EVEN|ODD)(?:=|\.|$)', filename)
    return m.group(1).upper() if m else 'FULL'

def _exclusive(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        f.write(content)
        f.flush()
        os.fsync(f.fileno())

def save_pixel_snapshot(regions, source_filename):
    """Snapshot an existing PIXEL mask as-is, with explicit PIXEL-only manifest.

    Geometry stays in detector pixel coordinates. No WCS conversion, RADEC
    acquisition information, slit reordering, or EVEN/ODD splitting is implied.
    """
    from regions import Regions
    src=Path(source_filename).expanduser().resolve(strict=True)
    if not src.is_file() or src.suffix.lower()!='.reg':
        raise ValueError('Select an existing PIXEL .reg file')
    if src.parent.name.casefold()=='pixels':
        field_root=src.parent.parent
    else:
        field_root=src.parent
    slug=_safe_name(src.name)
    role=_role(src.name)
    pixel_dir=field_root/'PIXELS'
    manifest_dir=field_root/'MANIFESTS'
    pixel_dir.mkdir(parents=True,exist_ok=True)
    manifest_dir.mkdir(parents=True,exist_ok=True)
    if not regions:
        raise ValueError('No rectangular pixel slits available')
    # Serialize from the edited canvas. `Regions` preserves rectangle rotations.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='samos-pixel-') as td:
        staging=Path(td)/'mask.reg'
        Regions(regions).write(str(staging),format='ds9')
        region_bytes=staging.read_bytes()
    # Avoid collisions, including with other operating sessions.
    created=[]
    try:
        for attempt in range(8):
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            token=uuid.uuid4().hex[:8]
            stem=f'{slug}_{stamp}_{token}'
            filename=f'{stem}_PIXEL_{role}.reg'
            rel=f'PIXELS/{filename}'
            dst=pixel_dir/filename
            try:
                _exclusive(dst,region_bytes)
            except FileExistsError:
                continue
            created.append(dst)
            break
        else:
            raise RuntimeError('Unable to allocate a unique pixel snapshot filename')
        data={
            'schema':'SAMOS_PIXEL_ONLY_SNAPSHOT_V1',
            'source_region_file':src.name,
            'source_region_folder':src.parent.name,
            'field':slug,
            'role':role,
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'status':'ARCHIVED_NOT_COMMANDED',
            'pixel_region':f'../{rel}',
            'sha256':hashlib.sha256(region_bytes).hexdigest(),
            'slit_count':len(regions),
            'radec_region':None,
            'science_version':None,
            'note':'PIXEL-only snapshot; no WCS or celestial pointing inferred. No DMD command issued.'
        }
        manifest=manifest_dir/f'{stem}_PIXEL_{role}.json'
        _exclusive(manifest,(json.dumps(data,indent=2,sort_keys=True)+'\n').encode())
        created.append(manifest)
        return {'status':'PIXEL_ONLY_ARCHIVED_NOT_COMMANDED', 'count':len(regions),
                'path':str(manifest),'pixel_file':str(dst)}
    except BaseException:
        for path in reversed(created):
            try: path.unlink()
            except OSError: pass
        raise
