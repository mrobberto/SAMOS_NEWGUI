"""DEV-only synthetic SISI camera frames for MainPage quicklook tests.

SIMULATED DATA: not an observatory acquisition. No CCD, DMD, TCS, SAMI or
network interface is imported or called by this module.

Frame arrays and metadata are written only under a dedicated simulator root.
The installed samos.ui.ql_safe_processing.safe_combine_files() combines them.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import hashlib
import json
import logging
import re

import numpy as np
from astropy.io import fits

MARKER = "SC3_SISI_OFFLINE_SIMULATOR_V1"
SHAPE = (1032, 1056)
SUPPORTED = {"Bias": "bias", "Dark": "dark", "Flat": "flat",
             "Science": "sci", "Buffer": "buff", "Test": "buff",
             "Calibration": "buff"}


def _short_label(name: str):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(name)).strip("_")[:45] or "NO_NAME"


def _synthetic_frame(kind: str, seconds: float, rng: np.random.Generator, shape=SHAPE):
    """Make plausible test arrays in ADU, not a detector physical simulator."""
    yy, xx = np.indices(shape, dtype=np.float32)
    bias = 540 + 4.0 * (xx >= shape[1] / 2) + 2 * yy / shape[0]
    # Fixed dark structure plus a few hot rows/pixels to test rate scaling.
    dark_rate = 0.6 + 0.15 * (yy / shape[0]) + 3.0 * ((xx.astype(int) % 263) == 0)
    read_noise = rng.normal(0, 1.4, size=shape).astype(np.float32)
    raw = bias + seconds * dark_rate + read_noise
    if kind == "flat":
        illumination = 1.0 - 0.15 * ((xx - shape[1]/2)/(shape[1]/2))**2
        pixel_response = 1.0 + 0.008 * np.sin(xx*0.31) * np.cos(yy*0.23)
        raw += (9000 * illumination * pixel_response).astype(np.float32)
    elif kind == "sci":
        raw += 75 * max(seconds, 0.1)
        for star_x, star_y, peak in [(190, 280, 3300), (630, 510, 7200),
                                      (890, 725, 4800), (470, 810, 1600)]:
            raw += (peak * np.exp(-((xx-star_x)**2 + (yy-star_y)**2)/(2*3.4**2))).astype(np.float32)
    return raw.astype(np.float32, copy=False)


@dataclass
class SimulationResult:
    image_type: str
    raw_files: list[Path]
    coadd: Path
    ql_dir: Path
    session_dir: Path
    before_hashes: list[str]
    after_hashes: list[str]
    header: dict
    warning: str


def pixel_hash(path: Path):
    with fits.open(path, memmap=False) as hdul:
        return hashlib.sha256(np.ascontiguousarray(hdul[0].data).tobytes()).hexdigest()


def run_simulated_suite(session_root: Path, exptype: str, nframes: int,
                        seconds: float, filter_name: str, selected: dict,
                        object_name: str = "SIM_FIELD", sequence: int = 1,
                        logger=None, shape=SHAPE) -> SimulationResult:
    """Simulates file acquisition and calls installed real quicklook combiner.

    All paths are constrained to session_root, which must be named
    'SAMOS_SC3_DEV_SISI_SIM'. Never shares real PAR.fits_dir / PAR.QL_images.
    """
    from samos.ui.ql_safe_processing import safe_combine_files

    session_root = Path(session_root).expanduser().resolve()
    if session_root.name != "SAMOS_SC3_DEV_SISI_SIM":
        raise ValueError("Simulation root MUST be named SAMOS_SC3_DEV_SISI_SIM")
    if exptype not in SUPPORTED:
        raise ValueError(f"Unsupported simulated exposure type {exptype}")
    if not (1 <= int(nframes) <= 20):
        raise ValueError("Simulation frames must be between 1 and 20")
    seconds = float(seconds)
    if seconds < 0 or seconds > 300:
        raise ValueError("Exposure seconds must be 0 through 300")
    if exptype == "Bias":
        seconds = 0.0
    elif seconds == 0.0:
        raise ValueError("Positive exposure time required except for BIAS")
    if int(sequence) < 1:
        raise ValueError("Sequence number must be >=1")
    kind = SUPPORTED[exptype]
    raw_dir = session_root / "raw"
    ql_dir = session_root / "quicklook"
    raw_dir.mkdir(parents=True, exist_ok=True)
    ql_dir.mkdir(parents=True, exist_ok=True)
    if logger is None:
        logger = logging.getLogger("samos.sisi_simulation")
    filter_name = _short_label(filter_name)
    label = _short_label(object_name)
    first = int(sequence) * 1000 + 1
    raw_files = []
    before = []
    for j in range(int(nframes)):
        number = first + j
        name = f"SIM_{kind.upper()}_{label}_{number:05d}.fits"
        raw_path = raw_dir / name
        rng = np.random.default_rng(100_000 + number + 10_000 * list(SUPPORTED).index(exptype))
        data = _synthetic_frame(kind, seconds, rng, shape=shape)
        hdr = fits.Header()
        hdr["SIMULATE"] = (True, "SYNTHETIC DATA: no detector operated")
        hdr["SIMSRC"] = (MARKER, "Simulation generator ID")
        hdr["OBSTYPE"] = exptype.upper()
        hdr["EXPTIME"] = (seconds, "Synthetic exposure length (seconds)")
        hdr["PARAM2"] = (int(round(seconds * 1000)), "Synthetic SI exposure time ms")
        hdr["DATE-OBS"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        hdr["EXPNUM"] = number
        hdr["FILTER"] = filter_name
        hdr["FILENAME"] = name
        hdr["FILEDIR"] = str(raw_dir)
        hdr["BUNIT"] = "ADU"
        hdr.add_history("Synthesized with repaired FITS header; NOT real camera data")
        # Exclusive writes prevent accidental replacement of a prior simulated exposure.
        fits.PrimaryHDU(data=data, header=hdr).writeto(raw_path, overwrite=False)
        raw_files.append(raw_path)
        before.append(pixel_hash(raw_path))
    params = {"file_number": first, "exp_frames": int(nframes),
              "exptime": int(round(seconds * 1000)), "image_name": f"SIM_{label}",
              "filter": filter_name,
              "sub_bias": bool(selected.get("sub_bias", False)),
              "sub_dark": bool(selected.get("sub_dark", False)),
              "sub_flat": bool(selected.get("sub_flat", False)),
              "sub_buffer": bool(selected.get("sub_buffer", False))}
    # Exact interface consumed by real safe_combine_files; no hardware object here.
    class FakeProgressWindow:
        def __init__(self):
            self.image_type = kind
            self.params = params
            self.expnum = first + int(nframes)
            self.collected_files = raw_files
            self.PAR = SimpleNamespace(fits_dir=raw_dir, QL_images=ql_dir)
            self.CCD = SimpleNamespace(sisi_exposure_type=exptype)
            self.logger = logger
            self._ql_last_warning = ""
        def create_dmd_pattern_hdu(self, hdr):
            return None  # hardware DMD and mask state deliberately excluded
    win = FakeProgressWindow()
    coadd = Path(safe_combine_files(win))
    after = [pixel_hash(p) for p in raw_files]
    if before != after:
        raise AssertionError("RAW pixels changed during quicklook processing")
    with fits.open(coadd, memmap=False) as h:
        hh = h[0].header.copy()
        hdr_out = {"QLPROC": bool(hh.get("QLPROC")),
                   "QLFAIL": bool(hh.get("QLFAIL")),
                   "QLBIAS": bool(hh.get("QLBIAS")),
                   "QLDARK": bool(hh.get("QLDARK")),
                   "QLFLAT": bool(hh.get("QLFLAT")),
                   "QLBUFF": bool(hh.get("QLBUFF")),
                   "NCOMBINE": hh.get("NCOMBINE")}
    result = SimulationResult(exptype, raw_files, coadd, ql_dir, session_root,
                              before, after, hdr_out, win._ql_last_warning)
    report = {"SIMULATED": True, "exptype": exptype,
              "coadd": str(coadd), "raw_files": [str(p) for p in raw_files],
              "pixel_sha256_before": before, "pixel_sha256_after": after,
              "flags": hdr_out, "selected": params,
              "warning": win._ql_last_warning}
    manifest = session_root / f"SIM_REPORT_{sequence:04d}_{kind.upper()}.json"
    with manifest.open("x", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)
    return result


def simulate_from_main(page):
    """Explicit GUI action only: no CCD exposure calls and no science logging."""
    from tkinter import messagebox
    from samos.ui.ql_safe_processing import active_master_summary
    import os

    if os.environ.get("SAMOS_ALLOW_SISI_SIM") != "1":
        messagebox.showwarning("Simulation disabled",
                               "To enable this DEV-only test, set SAMOS_ALLOW_SISI_SIM=1 "
                               "before launching the DEV GUI.", parent=page)
        return
    if "SAMOS_SC3_DEV" not in str(Path(__file__).resolve()):
        messagebox.showerror("DEV safety lock", "Simulator requires SAMOS_SC3_DEV.", parent=page)
        return
    exptype = page.image_type.get()
    root = Path.home() / "SAMOS_SC3_DEV_SISI_SIM"
    if not hasattr(page, "_sisi_sim_sequence"):
        prev = []
        for f in root.glob("SIM_REPORT_*.json"):
            hit = re.match(r"SIM_REPORT_(\d+)_", f.name)
            if hit:
                prev.append(int(hit.group(1)))
        page._sisi_sim_sequence = max(prev, default=0)
    page._sisi_sim_sequence += 1
    try:
        result = run_simulated_suite(
            root, exptype, int(page.image_frames.get()), float(page.image_exptime.get()),
            str(page.current_filter.get()),
            {"sub_bias": bool(page.ql_bias.get()), "sub_dark": bool(page.ql_dark.get()),
             "sub_flat": bool(page.ql_flat.get()), "sub_buffer": bool(page.ql_buffer.get())},
            object_name=str(page.image_name.get()) or "SIM_FIELD",
            sequence=page._sisi_sim_sequence, logger=page.logger)
        # ONLY display; do not call MainPage.display_exposure (which writes the
        # operational science log and updates the hardware numbering).
        page.Display(result.coadd.as_posix())
        page.fits_image.rotate(page.PAR.Ginga_PA)
        page._sisi_sim_status.set(
            f"SIMULATED {exptype}: {len(result.raw_files)} RAW frames, "
            f"QLFAIL={result.header['QLFAIL']}; {result.coadd.name}")
        page._sisi_sim_master_status.set(active_master_summary(result.ql_dir, page.current_filter.get()))
        if result.warning:
            messagebox.showwarning("Simulated quicklook", result.warning, parent=page)
    except Exception as exc:
        page.logger.exception("SISI offline simulation failed")
        messagebox.showerror("SISI simulation failed", str(exc), parent=page)
