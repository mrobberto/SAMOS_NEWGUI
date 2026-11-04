# SAMOS pixel-mask JPEG previews

This folder contains DS9 region masks (`*.reg`) and matching black-and-white
JPEG previews (`*.jpg`). **One JPG belongs to one REG** and has the same
basename. These previews are quick visual maps of the slit geometry, **not**
SISI astronomical images or hardware-ready DMD bitmaps.

## Requirements

Python 3 and Pillow (`PIL`) in the usual SAMOS `samos` environment.

## Usage

Open Terminal and change into this directory:

```bash
conda activate samos
cd SAMOS_SC3_DEV/src/samos/data/regions/pixels
```

The script lives **in this same directory** and searches it recursively,
including subfolders such as `legacy/`, `active/`, and `engineering/`.

```bash
# Preview which files would be created (safe; no writes)
python regions_to_jpg.py --verbose

# Create JPGs only when a matching one does not already exist
python regions_to_jpg.py --apply

# Recreate all JPGs, e.g. after fixing the renderer or modifying masks
python regions_to_jpg.py --apply --overwrite
```

To update only one subfolder, pass its path:

```bash
python regions_to_jpg.py legacy/targets/Dolidze25 --apply
```

If you run the script from **any other directory**, the default is still the
folder containing `regions_to_jpg.py`. You can also pass an explicit directory.

## Rules

- Output: 1024 x 1024 pixel **black** JPEG, **white** region outlines.
- Filename: `MyMask.reg` -> `MyMask.jpg` **in the same folder**.
- Detector frame: fixed at **1056 x 1032 SISI pixels** by default, with DS9
  `image`-coordinate positions preserved. Slits near the left edge stay left;
  tall long slits may be clipped at top/bottom. This is intentional.
- Orientation: follows the DS9 pixel coordinate system with Y increasing
  upward; the live GUI may flip or rotate a displayed image independently.
- Existing JPGs are **skipped** unless `--overwrite` is given with `--apply`.
- No `.reg` file is ever edited, moved, or deleted.
- No code in `SAMOS_SC3_MAIN` is touched.
- `--fitting auto` and `--fitting fit` are optional zoom modes, but do **not**
  use these for comparable detector-position previews: they can recenter masks.
- Unrecognized/sky-coordinate DS9 shapes are reported, rather than silently
  producing incomplete images.
- After deleting a region file, its existing JPG is *not* deleted automatically;
  remove that individual JPG manually if desired.

## Troubleshooting

If Python reports `No module named PIL`:

```bash
python -m pip install Pillow
```

If an image was generated with the old automatic zoom and looks centered
incorrectly, regenerate in the fixed detector frame:

```bash
python regions_to_jpg.py --apply --overwrite --fitting fixed
```

The program is independent of the DMD GUI viewer. Any future GUI viewer
improvements should use the same fixed-frame display convention for these
pixel-coordinate masks.
