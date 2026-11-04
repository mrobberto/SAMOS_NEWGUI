"""SISI quicklook calibration and master creation, offline-safe data path.

The only reads of acquired individual frames use mode='readonly' and a copy.
No raw pixel data are ever updated in this module.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import os
import shutil
import tempfile

import numpy as np
from astropy.io import fits


def _image(path: Path, expected_shape=None):
    with fits.open(path, mode="readonly", memmap=False) as hdus:
        raw = np.array(hdus[0].data, dtype=np.float64, copy=True)
        hdr = hdus[0].header.copy()
    if raw.ndim != 2 or not np.all(np.isfinite(raw)):
        raise ValueError(f"Nonfinite or non-2D FITS pixels: {path}")
    if expected_shape is not None and raw.shape != expected_shape:
        raise ValueError(f"Image dimensions {raw.shape} differ from {expected_shape}: {path}")
    return raw, hdr


def _master(path: Path, shape):
    if not path.is_file():
        raise FileNotFoundError(f"Requested quicklook master does not exist: {path}")
    data, hdr = _image(path, shape)
    return data, hdr


def _exptime_seconds(hdr, params, image_type):
    if image_type == "bias":
        return 0.0
    for key in ("EXPTIME",):
        try:
            t = float(hdr.get(key))
            if np.isfinite(t) and t > 0:
                return t
        except (ValueError, TypeError):
            pass
    try:
        t = float(hdr.get("PARAM2", 0)) / 1000.0
        if np.isfinite(t) and t > 0:
            return t
    except (ValueError, TypeError):
        pass
    t = float(params.get("exptime", 0)) / 1000.0
    if image_type != "bias" and (not np.isfinite(t) or t <= 0):
        raise ValueError("Cannot determine positive exposure time")
    return t


def correct_array(raw, image_type, exptime, selected, masters):
    """Pure calculation; returned array does not alias raw or any master.

    selected has sub_bias, sub_dark, sub_flat, sub_buffer keys.
    masters maps those same keys to arrays. Inputs are immutable to the caller.
    """
    data = np.asarray(raw, dtype=np.float64).copy()
    applied = []
    if image_type == "bias":
        return data, applied
    for key in ("sub_bias", "sub_dark", "sub_flat", "sub_buffer"):
        if not selected.get(key, False):
            continue
        if key not in masters:
            raise FileNotFoundError(f"Requested {key} master unavailable")
        m = np.asarray(masters[key], dtype=np.float64)
        if m.shape != data.shape or not np.all(np.isfinite(m)):
            raise ValueError(f"Invalid master: {key}")
        if key == "sub_dark":
            data -= m * exptime
        elif key == "sub_flat":
            if np.any(m <= 0):
                raise ValueError("Master flat has nonpositive pixels; refusing division")
            data /= m
        else:
            data -= m
        applied.append(key)
    return data, applied


def _temp_fits(path, data, hdr, overwrite=False):
    """Write a complete FITS in the destination directory, publish atomically."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".qlstage_", suffix=".fits", dir=path.parent)
    os.close(fd)
    try:
        fits.PrimaryHDU(data=np.asarray(data, dtype=np.float32), header=hdr).writeto(tmp, overwrite=True)
        if overwrite:
            os.replace(tmp, path)
        else:
            # Exclusive file creation works on Box-mounted directories and never
            # passes an "xb" handle into Astropy (which rejects that mode).
            created = False
            try:
                with path.open("xb") as dst:
                    created = True
                    with Path(tmp).open("rb") as src:
                        shutil.copyfileobj(src, dst)
            except Exception:
                if created:
                    path.unlink(missing_ok=True)
                raise
    finally:
        if Path(tmp).exists():
            Path(tmp).unlink()


def _activate_master(root, name, data, hdr, archive_key):
    """Versioned master and replaceable active copy; old version is archived."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    active = root / name
    history = root / "master_history"
    history.mkdir(exist_ok=True)
    if active.exists():
        prior = history / f"prior_{archive_key}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.fits"
        shutil.copy2(active, prior)
    version = history / f"master_{archive_key}_{datetime.now(timezone.utc):%Y%m%dT%H%M%S%fZ}.fits"
    _temp_fits(version, data, hdr, overwrite=False)
    hdr["QLMASTER"] = (version.name, "Immutable versioned calibration master")
    _temp_fits(active, data, hdr, overwrite=True)
    return active, version


def active_master_summary(ql_dir, filter_name):
    p = Path(ql_dir)
    items = []
    for title, filename in (("Bias", "superbias.fits"),
                            ("Dark", "superdark_s.fits"),
                            ("Flat", f"superflat_{filter_name}.fits")):
        f = p / filename
        if not f.exists():
            items.append(f"{title}: none")
            continue
        try:
            with fits.open(f, memmap=False) as h:
                n = h[0].header.get("NCOMBINE", "?")
                stamp = str(h[0].header.get("DATE", "?"))[:10]
            items.append(f"{title}: {filename} (N={n}, {stamp})")
        except Exception:
            items.append(f"{title}: unreadable")
    return "Active QL masters — " + " | ".join(items)


def safe_combine_files(win):
    """Replacement for ExposureProgressWindow.combine_files, preserves raw pixels.

    Saved archived COADD is the view displayed by MainPage. If a requested
    calibration master is missing/invalid, do not apply a partial set;
    archive an uncalibrated COADD flagged QLFAIL instead, and warn the user.
    """
    image_type = str(win.image_type).lower()
    params = win.params
    files = [Path(p) for p in win.collected_files]
    if not files:
        raise ValueError("No FITS frames collected")
    ql_dir = Path(win.PAR.QL_images)
    archive_dir = Path(win.PAR.fits_dir)
    ql_dir.mkdir(parents=True, exist_ok=True)
    archive_dir.mkdir(parents=True, exist_ok=True)
    first = int(params["file_number"])
    last = int(win.expnum) - 1
    filter_name = str(params.get("filter", "unknown"))
    frames, headers, times = [], [], []
    for f in files:
        arr, hdr = _image(f, frames[0].shape if frames else None)
        frames.append(arr)
        headers.append(hdr)
        times.append(_exptime_seconds(hdr, params, image_type))
    source = np.mean(np.stack(frames, axis=0), axis=0)
    out = source.copy()
    flags = {key: bool(params.get(key, False)) for key in
             ("sub_bias", "sub_dark", "sub_flat", "sub_buffer")}
    # Bias suite is never bias-subtracted; darks/flats only use relevant corrections.
    if image_type == "bias":
        selected = {}
    elif image_type == "dark":
        selected = {"sub_bias": flags["sub_bias"]}
    elif image_type == "flat":
        selected = {k: flags[k] for k in ("sub_bias", "sub_dark")}
    elif image_type == "sci":
        selected = flags
    else:
        selected = {}  # buffer/test calibration products are raw averages

    paths = {"sub_bias": ql_dir / "superbias.fits",
             "sub_dark": ql_dir / "superdark_s.fits",
             "sub_flat": ql_dir / f"superflat_{filter_name}.fits",
             "sub_buffer": ql_dir / "superbuffer.fits"}
    masters = {}
    applied = []
    warning = ""
    try:
        for key in selected:
            if selected[key]:
                masters[key], _ = _master(paths[key], source.shape)
        # Correct each exposure separately if exposure time varies.
        processed = [correct_array(raw, image_type, t, selected, masters)[0]
                     for raw, t in zip(frames, times)]
        out = np.mean(np.stack(processed, axis=0), axis=0)
        applied = [k for k in selected if selected[k]]
    except (FileNotFoundError, ValueError, FloatingPointError) as exc:
        warning = (f"Requested quicklook calibration NOT applied: {exc}. "
                   "Uncalibrated COADD saved; original raw exposures preserved.")
        win.logger.error(warning)
        out = source.copy()
        applied = []
    hdr = headers[0].copy()
    hdr["COMBINED"] = (True, "This FITS is a mean combination")
    hdr["NCOMBINE"] = (len(files), "Number of original raw frames")
    hdr["NCOMBINED"] = (len(files), "Number of original raw frames")
    hdr["OBSTYPE"] = str(win.CCD.sisi_exposure_type).upper()[:24]
    hdr["QLPROC"] = (bool(applied), "Any quicklook calibration was applied")
    hdr["QLFAIL"] = (bool(warning), "Requested corrections could not be applied")
    hdr["QLSRC"] = ("RAW", "Quicklook derived from read-only raw frames")
    for key, value in (("BIAS", "sub_bias"), ("DARK", "sub_dark"),
                       ("FLAT", "sub_flat"), ("BUFF", "sub_buffer")):
        hdr[f"QL{key}"] = (value in applied, "Correction applied to saved pixels")
    for key, keyword in (("sub_bias", "MSTRBIAS"), ("sub_dark", "MSTRDARK"),
                         ("sub_flat", "MSTRFLAT"), ("sub_buffer", "MSTRBUFF")):
        if key in applied:
            hdr[keyword] = (paths[key].name, "Master applied to saved pixels")
            hdr.add_history(f"QL {key} master {paths[key]}")
    hdr.add_history("SISI RAW individual FITS pixel arrays preserved unchanged")
    hdr.add_history("QL is arithmetic mean of raw or calibrated frames")
    if warning:
        hdr.add_history(warning[:70])
    # Keep any map extension behavior for science COADD, but never write to DMD.
    dmd_hdu = None
    if image_type == "sci":
        try:
            dmd_hdu = win.create_dmd_pattern_hdu(hdr)
        except Exception as exc:
            win.logger.warning("DMD extension omitted from quicklook: %s", exc)
    # Archive filename convention from previously validated SAMOS DEV.
    try:
        from samos.utilities.sisi_naming import safe_object_name
    except ImportError:
        # Older DEV source snapshots predate this module. Never allow a path
        # separator or traversal token into an archive filename.
        import re
        def safe_object_name(label):
            clean = re.sub(r"[^A-Za-z0-9_-]+", "_", str(label)).strip("_")
            return clean or "UNNAMED"
    tag = str(win.CCD.sisi_exposure_type).upper()
    name = f"SISI_COADD_{first:04d}-{last:04d}_{safe_object_name(params['image_name'])}_{tag}.fits"
    archive_path = archive_dir / name
    hdr["FILENAME"] = name
    hdr["FILEDIR"] = str(archive_dir)
    def _save_coadd(path, data, header, exclusive):
        # Include DMD extension only on science files.
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(prefix=".qlstage_",suffix=".fits",dir=path.parent)
        os.close(fd)
        try:
            hdus = fits.HDUList([fits.PrimaryHDU(data=np.asarray(data,dtype=np.float32),header=header)])
            if dmd_hdu is not None:
                hdus.append(dmd_hdu.copy())
            hdus.writeto(tmp,overwrite=True)
            if exclusive:
                created = False
                try:
                    with path.open("xb") as dst:
                        created = True
                        with Path(tmp).open("rb") as src:
                            shutil.copyfileobj(src,dst)
                except Exception:
                    if created:
                        path.unlink(missing_ok=True)
                    raise
            else:
                os.replace(tmp,path)
        finally:
            if Path(tmp).exists():
                Path(tmp).unlink()
    _save_coadd(archive_path,out,hdr,exclusive=True)
    # Preserve historical filter-specific quicklook filenames for SCI/FLAT.
    preview_name = (f"{image_type}_{filter_name}_coadd.fits"
                    if image_type in ("sci", "flat") else f"{image_type}_coadd.fits")
    preview = ql_dir / preview_name
    _save_coadd(preview,out,hdr,exclusive=False)
    # Create and record active masters from each successfully reduced sequence.
    # Acquisition of a new sequence explicitly selects it as the new QL master.
    if not warning:
        if image_type == "bias":
            master_name, master_data = "superbias.fits", out
        elif image_type == "dark" and flags["sub_bias"]:
            if any(t <= 0 for t in times):
                warning = "DARK master not activated: nonpositive exposure time"
                master_name, master_data = None, None
            else:
                dark_rates = [correct_array(raw,"dark",t,selected,masters)[0] / t
                              for raw,t in zip(frames,times)]
                master_name, master_data = "superdark_s.fits", np.mean(dark_rates,axis=0)
        elif image_type == "flat":
            median = np.median(out[np.isfinite(out)])
            if median <= 0:
                warning = "FLAT master not activated: nonpositive median"
                master_name, master_data = None, None
            else:
                master_name, master_data = f"superflat_{filter_name}.fits", out/median
        elif (image_type == "buff" and
              str(win.CCD.sisi_exposure_type).lower() == "buffer"):
            # Test/Calibration are mapped to buff by legacy controller code;
            # never allow these engineering frames to replace the buffer master.
            master_name, master_data = "superbuffer.fits", out
        else:
            master_name, master_data = None, None
        if master_name is not None:
            mhdr = hdr.copy()
            mhdr["DATE"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            mhdr["NCOMBINE"] = len(files)
            mhdr["COMBMETH"] = "MEAN"
            mhdr["BUNIT"] = ("ADU/s" if image_type == "dark" else
                              "relative" if image_type == "flat" else "ADU")
            mhdr["EXPTIME"] = 1.0 if image_type == "dark" else float(times[0])
            mhdr.add_history(f"Active master derived from raw files {files[0].name} .. {files[-1].name}")
            active, version = _activate_master(ql_dir,master_name,master_data,mhdr,
                                               f"{image_type}_{first:04d}-{last:04d}")
            win.logger.info("ACTIVE QL MASTER %s (version %s)", active, version)
    win._ql_last_warning = warning
    return archive_path
