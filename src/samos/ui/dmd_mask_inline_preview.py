"""Small, read-only helpers for previewing archived SISI pixel masks.

IMPORTANT: This is NOT a DMD loader. .reg/.jpg files are in SISI image
coordinates, not a commandable DMD .csv format. No hardware imports.
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image


def default_pixel_root(module_file: str | Path) -> Path:
    """Given src/samos/ui/dmd.py, locate the versioned DEV region library."""
    return Path(module_file).resolve().parents[1] / "data" / "regions" / "pixels"


def jpeg_for_selection(selected: Path) -> Path:
    """Resolve a .reg to its matching preview, accepting sibling and previews/."""
    selected = Path(selected).expanduser()
    ext = selected.suffix.casefold()
    if ext == ".reg":
        sibling = selected.with_suffix(".jpg")
        nested = selected.parent / "previews" / (selected.stem + ".jpg")
        for candidate in (sibling, nested):
            if candidate.is_file() and not candidate.is_symlink():
                return candidate
        raise FileNotFoundError(
            "No matching JPEG for {}.\nRun regions_to_jpg.py --apply in the pixels folder.".format(selected.name))
    if ext in {".jpg", ".jpeg"}:
        if selected.is_file() and not selected.is_symlink():
            return selected
        raise FileNotFoundError("Preview JPEG not found: {}".format(selected))
    raise ValueError("Select a .reg, .jpg or .jpeg file, not {}".format(selected.suffix))


def letterboxed_preview(source: Image.Image, size: tuple[int, int] = (300, 270)) -> Image.Image:
    """Black 300x270 canvas, image aspect retained; never recenter slit geometry."""
    width, height = size
    if width <= 0 or height <= 0:
        raise ValueError("Invalid preview size")
    image = source.convert("RGB")
    resample = getattr(Image, "Resampling", Image).LANCZOS
    image.thumbnail((width, height), resample)
    frame = Image.new("RGB", (width, height), "black")
    frame.paste(image, ((width-image.width)//2, (height-image.height)//2))
    return frame
