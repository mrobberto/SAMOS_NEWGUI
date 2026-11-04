"""
SAMOS CCD2DMD tk Frame Class
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
import numpy as np

from astropy.stats import sigma_clipped_stats
from astropy.io import fits
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import fit_wcs_from_points
from astropy import units as u
from ginga.tkw.ImageViewTk import CanvasView
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga.util.loader import load_data
import pandas as pd
from regions import PixCoord, RectanglePixelRegion

import tkinter as tk
import ttkbootstrap as ttk
import tksheet
from tkinter.filedialog import askopenfilename

from samos.dmd.utilities import iraf_gridsource_find
from samos.utilities import get_data_file
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled

from io import BytesIO




"""Read-only CCD–DMD grid measurement against the operational gold WCS."""
class CCD2DMDPage(SAMOSFrame):
    """Measure DMD-grid spots without modifying the active calibration."""

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "CCD-DMD Calibration", **kwargs)
        self.fits_hdu = None
        self.sources_table = None
        self.dmd_table = None
        self.DMD_PIX_df = None
        self.loaded_image = False
        self.validated_new_transform = False

        # Buttons
        button_frame = ttk.Frame(self.main_frame, borderwidth=5)
        button_frame.grid(row=0, column=0, rowspan=2, sticky=TK_STICKY_ALL, padx=5, pady=5)
        # SC3_CCD2DMD_FILE_NAV_V1: distinct starting locations, same loader.
        b = ttk.Button(button_frame, text="Current Night FITS", command=self.browse_current_grid_fits)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(button_frame, text="Historical Grid FITS", command=self.browse_historical_grid_fits)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        w = ttk.Button(button_frame, text="Run IRAFStarFinder", command=self.iraf_starfind)
        w.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "loaded_image", True)]
        w = ttk.Button(button_frame, text="Generate Candidate WCS", command=self.run_coord_transform)
        w.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "validated_new_transform", True)]

        # DMD pattern information
        ttk.Label(self.main_frame, text="DMD Pattern:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.dmd_pattern_text = tk.StringVar(self, "")
        ttk.Label(self.main_frame, textvariable=self.dmd_pattern_text).grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.grid_reference_path_text = tk.StringVar(self, "No reference grid loaded")
        ttk.Label(self.main_frame, textvariable=self.grid_reference_path_text,
                  wraplength=320).grid(row=4, column=0, sticky=TK_STICKY_ALL)
        # SC3_CCD2DMD_DISPLAY_FIRST_V1: the CCD image is valid without a DMD grid.
        self.ccd_image_path_text = tk.StringVar(self, "No CCD FITS image loaded")
        ttk.Label(self.main_frame, textvariable=self.ccd_image_path_text,
                  wraplength=320).grid(row=5, column=0, sticky=TK_STICKY_ALL)

        # FITS file markup canvas
        canvas = tk.Canvas(self.main_frame, bg="grey", width=528, height=516)
        canvas.grid(row=0, column=1, rowspan=8, columnspan=8, sticky=TK_STICKY_ALL, padx=5, pady=5)
        fi = CanvasView(self.logger)
        fi.set_widget(canvas)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        fi.set_enter_focus(True)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        fi.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi
        bd = fi.get_bindings()
        bd.enable_all(True)

        # Table of sources
        self.tk_grid_sources_table = tksheet.Sheet(self.main_frame, column_width=60)
        self.tk_grid_sources_table.grid(row=8, column=0, rowspan=3, columnspan=9, sticky=TK_STICKY_ALL, padx=5, pady=5)
        self.set_enabled()


    @check_enabled
    def cursor_cb(self, event):
        if self.fits_hdu is None:
            return
        x, y = event.xdata, event.ydata
        self.logger.info("CCD2DMD Recalibrate: Click at ({},{})".format(x, y))


    # SC3_CCD2DMD_FILE_NAV_V1 — only file-navigation additions.
    def browse_current_grid_fits(self):
        return self.browse_grid_fits_files(initial_directory=self.PAR.fits_dir)

    def browse_historical_grid_fits(self):
        return self.browse_grid_fits_files(initial_directory=get_data_file("dmd.pixel_mapping"))

    @check_enabled
    def browse_grid_fits_files(self, initial_directory=None):
        from pathlib import Path
        history = Path(get_data_file("dmd.pixel_mapping"))
        directory = Path(initial_directory) if initial_directory is not None else history
        if not directory.is_dir():
            directory = history if history.is_dir() else Path.home()
        filename = askopenfilename(initialdir=str(directory), filetypes=[("FITS files", "*.fits *.fit *.fts"), ("All files", "*.*")],
                                   title="Select CCD grid exposure (FITS)", parent=self)

        try:
            if filename == '':
                self.logger.error("CCD2DMD Recalibrate: Null selection for FITS image!")
                tk.messagebox.showerror(title="No File Selected", message="No FITS grid file selected")
                return

            self.loaded_image = False
            self.astro_image = load_data(filename, logger=self.logger)
            self.fitsimage.set_image(self.astro_image)
            self.fits_header = self.astro_image.as_hdu().header
            # SC3_CCD2DMD_DISPLAY_FIRST_V1: make the FITS visible even when reference selection is cancelled.
            # update_idletasks flushes the pending Ginga/Tk redraw before a modal dialog.
            self.ccd_image_path_text.set("CCD FITS: " + str(Path(filename).resolve()))
            self.update_idletasks()
            self.logger.info("CCD2DMD CCD image displayed: %s", filename)
            # SC3_CCD2DMD_GRID_FALLBACK_V1: FITS may be ordinary SISI imaging.
            # Only an explicit grid association makes it a calibration input.
            self.loaded_image = False
            self.dmd_table = None
            self.DMD_PIX_df = None
            self.validated_new_transform = False
            self.grid_pattern_fullPath = None
            self.dmd_pattern_text.set("No reference grid selected")
            self.grid_reference_path_text.set("No reference grid selected")
            self.grid_pattern_source = None

            header_value = self.fits_header.get("DMDMAP")
            grid_name = str(header_value).strip() if header_value is not None else ""
            invalid = {"", "NONE", "NULL", "UNKNOWN", "UNAVAIL", "UNAVAILABLE", "N/A", "NO MAP", "NO_MAP"}
            has_grid = bool(grid_name) and grid_name.upper() not in invalid and not grid_name.lower().startswith("unavail")
            suggested = Path(get_data_file("dmd.csv.slits", grid_name)).resolve() if has_grid else None
            if suggested is not None and suggested.is_file() and suggested.suffix.lower() == ".csv":
                selected = suggested
                provenance = "FITS_DMDMAP"
            else:
                from tkinter import messagebox
                reason = ("The FITS header identifies a DMD map, but the reference CSV could not be found."
                          if has_grid else "This FITS image has no usable DMDMAP reference.")
                prompt = (reason + "\n\nSISI images can be taken without a DMD map. "
                          "For CCD–DMD calibration only, do you want to select the "
                          "DMD grid CSV that was actually illuminated?")
                if not messagebox.askyesno("Select calibration grid", prompt, parent=self):
                    self.logger.info("CCD2DMD grid selection cancelled for %s", filename)
                    return
                from tkinter import filedialog
                initial_dir = Path(get_data_file("dmd.csv.slits"))
                if not initial_dir.is_dir():
                    initial_dir = Path.home()
                selected_name = filedialog.askopenfilename(
                    initialdir=str(initial_dir), title="Select actual DMD reference grid CSV",
                    filetypes=[("DMD grid CSV", "*.csv"), ("All files", "*.*")], parent=self)
                if not selected_name:
                    self.logger.info("CCD2DMD manual grid selection cancelled for %s", filename)
                    return
                selected = Path(selected_name).expanduser().resolve()
                if not selected.is_file() or selected.suffix.lower() != ".csv":
                    messagebox.showerror("Invalid reference grid", "Select an existing CSV grid file.", parent=self)
                    return
                provenance = "MANUAL_CSV"
                self.logger.warning("CCD2DMD manual DMD grid association: FITS=%s grid=%s", filename, selected)
            dmd_table = pd.read_csv(selected)
            if not {"x", "y"}.issubset(dmd_table.columns) or len(dmd_table) == 0:
                raise ValueError("Reference grid CSV must have nonempty x and y coordinate columns")
            self.grid_pattern_name = selected.name
            self.grid_pattern_fullPath = selected
            self.grid_pattern_source = provenance
            self.dmd_pattern_text.set(f"{selected.name} ({provenance})")
            self.grid_reference_path_text.set(str(selected))
            self.dmd_table = dmd_table
            self.loaded_image = True
            self.set_enabled()
            self.logger.info("CCD2DMD reference grid accepted: %s (%s)", selected, provenance)
        except KeyError as k:
            if "DMDMAP" in str(k):
                msg = "Mapping file must contain a DMDMAP header keyword which contains the name of the corresponding DMD map."
                tk.messagebox.showerror(title="No DMD Map in FITS Header", message=msg)
                return
            tk.messagebox.showerror(title="Missing Key", message=f"Missing Key error for {k}")
            return
        except Exception as e:
            tk.messagebox.showerror(title="ERROR", message=f"ERROR {e} while loading FITS file")
            return


    @check_enabled
    def iraf_starfind(self):
        # SC3_GOLD_BOXES_TEST_V1 — READ ONLY. The gold WCS defines aperture identity.
        # A measurement is attached only when a unique detected centroid falls near
        # the gold-predicted CCD location. No row-order assumptions or WCS writes.
        from scipy.optimize import linear_sum_assignment
        if self.dmd_table is None or self.PAR.dmd_wcs is None:
            raise ValueError("Load a grid reference and the gold WCS first")
        if not {"x", "y"}.issubset(self.dmd_table.columns):
            raise ValueError("Reference CSV needs DMD x,y columns")
        ccd = np.array(self.astro_image.as_nddata().data, dtype=float, copy=True)
        # Preserve the displayed/original image. Suppress known bad CCD columns
        # only in this temporary detection copy; guard for cropped exposures.
        if ccd.shape[1] >= 1025:
            upper_avg = np.mean((np.mean(ccd[:, 1000:1009], axis=1),
                                 np.mean(ccd[:, 1025:], axis=1)), axis=0)
            lower_avg = np.mean((np.mean(ccd[:, :20], axis=1),
                                 np.mean(ccd[:, 40:50], axis=1)), axis=0)
            ccd[:, 1010:1025] = upper_avg[:, None]
            ccd[:, 20:40] = lower_avg[:, None]
        _, _, std_ccd = sigma_clipped_stats(ccd, sigma=4.0)
        reference = self.dmd_table.copy().reset_index(drop=True)
        # SC3_GOLD_BOXES_TEST_V2: match the independently verified gold FITS
        # inverse exactly: DMD mirror coordinates are WCS degrees * 3600,
        # with zero-based CCD pixel origin. Do NOT use legacy dmd_to_ccd()
        # here; its conversion convention differs for this calibration.
        mirror_xy = reference[["x", "y"]].to_numpy(dtype=float)
        px, py = self.PAR.dmd_wcs.all_world2pix(
            mirror_xy[:, 0] / 3600.0, mirror_xy[:, 1] / 3600.0, 0)
        predicted = np.column_stack([px, py]).astype(float)
        if predicted.shape != (len(reference), 2) or not np.isfinite(predicted).all():
            raise ValueError("Gold WCS gave invalid predicted CCD positions")
        found, _ = iraf_gridsource_find(ccd, expected_sources=len(reference),
                                        fwhm=5, threshold=3*std_ccd)
        if found is None or len(found)==0:
            raise ValueError("No IRAF centroids detected")
        measured = found[["xcentroid", "ycentroid"]].to_numpy(dtype=float)
        if not np.isfinite(measured).all():
            raise ValueError("IRAF centroids are not finite")
        sep = np.hypot(predicted[:, None, 0]-measured[None, :, 0],
                       predicted[:, None, 1]-measured[None, :, 1])
        # Minimum-total-distance one-to-one assignment; never assign remotely
        # detected spots just to make the table have 121 matches.
        row_ix, spot_ix = linear_sum_assignment(sep)
        gate_px = 20.0
        is_good = sep[row_ix, spot_ix] <= gate_px
        mapping = {int(r):int(j) for r,j,ok in zip(row_ix,spot_ix,is_good) if ok}
        output = pd.DataFrame({
            "target": reference["target"] if "target" in reference else [f"grid{i+1}" for i in range(len(reference))],
            "dmd_x": reference["x"].astype(float),
            "dmd_y": reference["y"].astype(float),
            "ccd_x_pred": predicted[:,0], "ccd_y_pred": predicted[:,1],
            "ccd_x_meas": [measured[mapping[i],0] if i in mapping else np.nan for i in range(len(reference))],
            "ccd_y_meas": [measured[mapping[i],1] if i in mapping else np.nan for i in range(len(reference))],
        })
        output["delta_x_pix"] = output.ccd_x_meas-output.ccd_x_pred
        output["delta_y_pix"] = output.ccd_y_meas-output.ccd_y_pred
        output["radial_pix"] = np.hypot(output.delta_x_pix,output.delta_y_pix)
        output["matched"] = np.isfinite(output.ccd_x_meas)
        self.DMD_PIX_df = output
        self.sources_table = found.copy()
        # Only a complete, unique 121-point match can enable candidate fitting.
        self.validated_new_transform = (
            len(reference) == 121 and len(mapping) == 121
            and np.isfinite(output[["ccd_x_meas", "ccd_y_meas"]].to_numpy()).all()
        )
        self.set_enabled()
        self.tk_grid_sources_table.set_sheet_data(output.round(4).fillna("").values.tolist(), reset_col_positions=True)
        self.tk_grid_sources_table.headers(newheaders=list(output.columns), show_headers_if_not_sheet=True, redraw=True)
        # Predicted CCD boxes are deliberately NOT centered on detected spots.
        # Their relative displacement is the visible test of the gold mapping.
        for x, y in predicted:
            reg = RectanglePixelRegion(center=PixCoord(x=float(x), y=float(y)),
                                       width=40, height=40, angle=0*u.deg)
            self.fitsimage.canvas.add(r2g(reg))
        valid = output.loc[output.matched, "radial_pix"].to_numpy(dtype=float)
        rms = float(np.sqrt(np.mean(valid**2))) if valid.size else float('nan')
        median = float(np.median(valid)) if valid.size else float('nan')
        self.logger.info("CCD2DMD gold-box test: predicted=%d detected=%d matched=%d "
                         "unmatched=%d median=%.3f RMS=%.3f CCD pixels (20-px gate)",
                         len(reference), len(found), len(mapping), len(reference)-len(mapping), median, rms)
        self.dmd_pattern_text.set(f"Gold-box test: {len(mapping)}/{len(reference)} matched; RMS {rms:.3f} px")
        if len(mapping) != len(reference):
            from tkinter import messagebox
            messagebox.showwarning("Incomplete gold-box matching",
                                   f"Matched {len(mapping)} of {len(reference)} apertures within 20 CCD pixels. "
                                   "Do not recalibrate from this incomplete set.",parent=self)


    @check_enabled
    def run_coord_transform(self):
        """Fit an INACTIVE candidate FITS; never overwrite or activate gold.

        Requires 121 independently measured CCD centroids matched uniquely to
        the known DMD mirror coordinates. Retains the exact historical units:
        DMD mirror coordinates are pseudo-world degrees times 3600, and CCD
        pixel coordinates are zero-based.
        """
        from tkinter import messagebox

        if not self.validated_new_transform or self.DMD_PIX_df is None:
            messagebox.showwarning("Candidate not ready", "Run and validate all 121 grid matches first.", parent=self)
            return
        matches = self.DMD_PIX_df.copy()
        if len(matches) != 121 or not bool(matches["matched"].all()):
            messagebox.showerror("Incomplete calibration", "All 121 unique matches are required.", parent=self)
            return
        cols = ["dmd_x", "dmd_y", "ccd_x_meas", "ccd_y_meas", "ccd_x_pred", "ccd_y_pred"]
        values = matches[cols].to_numpy(dtype=float)
        if not np.isfinite(values).all() or matches[["dmd_x", "dmd_y"]].duplicated().any():
            messagebox.showerror("Invalid calibration", "Invalid or repeated coordinate pairs.", parent=self)
            return

        # Gold is read only. Check on-disk identity immediately before fitting.
        dev = Path(__file__).resolve().parents[3]
        if dev.name != "SAMOS_SC3_DEV":
            messagebox.showerror("Unsafe location", "Candidate generation is DEV-only.", parent=self)
            return
        gold = dev / "src/samos/data/dmd/convert/DMD_Mapping_WCS.fits"
        expected_gold = "d3be4bd29cac3feab2d92e8e1afde45c0c8fec6f2f1dcd29891c68349ca8eabe"
        def sha256(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        if not gold.is_file() or gold.is_symlink() or sha256(gold) != expected_gold:
            messagebox.showerror("Gold WCS guard", "Gold FITS checksum differs from verified baseline; stopped.", parent=self)
            return

        # Fit the same forward convention as the operational WCS: CCD pixel
        # x,y -> DMD pseudo-world coordinates (mirrors / 3600 degrees).
        world = SkyCoord(ra=values[:, 0] / 3600 * u.deg,
                         dec=values[:, 1] / 3600 * u.deg, frame="icrs")
        try:
            candidate = fit_wcs_from_points(
                (values[:, 2], values[:, 3]), world,
                sip_degree=3,
            )
            predicted_x, predicted_y = candidate.all_world2pix(
                values[:, 0] / 3600, values[:, 1] / 3600, 0,
            )
            residual = np.hypot(predicted_x - values[:, 2],
                                predicted_y - values[:, 3])
            if not np.isfinite(residual).all():
                raise ValueError("Nonfinite candidate residuals")
            rms = float(np.sqrt(np.mean(residual ** 2)))
            maximum = float(np.max(residual))
            gold_rms = float(np.sqrt(np.mean(np.sum((values[:, 2:4] - values[:, 4:6])**2, axis=1))))
            # This is a validation of the fit against the training pairs,
            # not an independent cross-validation or on-sky accuracy estimate.
            if rms > 2.0 or maximum > 5.0:
                raise ValueError(f"Candidate self-fit too poor (RMS={rms:.3f}, max={maximum:.3f} pix)")
        except Exception as exc:
            self.logger.exception("CCD2DMD candidate fitting failed")
            messagebox.showerror("Candidate fit failed", str(exc), parent=self)
            return

        summary = (f"121 matched pairs\n"
                   f"Gold-vs-measured RMS: {gold_rms:.4f} CCD pix\n"
                   f"Candidate training RMS: {rms:.4f} CCD pix\n"
                   f"Candidate maximum residual: {maximum:.4f} CCD pix\n\n"
                   "Save an INACTIVE candidate outside the package?\n"
                   "This will not replace the gold FITS or update PAR.dmd_wcs.")
        if not messagebox.askyesno("Save candidate WCS (no activation)", summary, parent=self):
            return

        # Private, versioned output outside package data and operational WCS.
        output_dir = dev.parent / "_SAMOS_SC3_DEV_Cleanup_Archive" / "candidate_wcs"
        output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        stem = "DMD_Mapping_WCS_candidate_" + stamp
        candidate_path = output_dir / (stem + ".fits")
        catalog_path = output_dir / (stem + "_pairs.csv")
        summary_path = output_dir / (stem + "_report.json")
        for path in (candidate_path, catalog_path, summary_path):
            if path.exists():
                raise RuntimeError(f"Refusing to replace existing file: {path}")

        hdr = candidate.to_header(relax=True)
        hdr["DMDMAP"] = (str(self.grid_pattern_fullPath.name), "Reference grid CSV")
        hdr["CANDIDAT"] = (True, "INACTIVE calibration; do not use operationally")
        hdr.add_history("CCD2DMD candidate fit using 121 unique measured spots")
        hdr.add_history("DMD world degrees = DMD mirror coordinates / 3600")
        hdr.add_history("CCD pixel origin=0; gold WCS never modified")
        report = {
            "status": "INACTIVE CANDIDATE — NOT INSTALLED",
            "gold_file": str(gold), "gold_sha256": expected_gold,
            "grid_csv": str(self.grid_pattern_fullPath),
            "matched": 121, "sip_degree": 3, "pixel_origin": 0,
            "world_units": "DMD mirrors / 3600 degrees",
            "gold_vs_measured_rms_ccd_pix": gold_rms,
            "candidate_training_rms_ccd_pix": rms,
            "candidate_training_max_ccd_pix": maximum,
            "note": "Training residuals are not independent cross-validation.",
        }
        try:
            # exclusive creation prevents accidental overwrite
            with candidate_path.open("xb") as handle:
                buffer = BytesIO()
                fits.PrimaryHDU(
                    data=self.astro_image.as_nddata().data,
                    header=hdr
                ).writeto(buffer, output_verify="exception")

                handle.write(buffer.getvalue())
            matches.assign(candidate_fit_radial_pix=residual).to_csv(catalog_path, index=False)
            summary_path.write_text(json.dumps(report, indent=2) + "\n")
            if sha256(gold) != expected_gold:
                raise RuntimeError("Gold checksum changed unexpectedly: investigate before proceeding")
        except Exception as exc:
            self.logger.exception("CCD2DMD candidate save failed")
            messagebox.showerror("Candidate save failure", str(exc), parent=self)
            return
        self.logger.info("CCD2DMD INACTIVE candidate saved: %s; RMS=%.4f px", candidate_path, rms)
        messagebox.showinfo("Inactive candidate saved",
                            f"Candidate: {candidate_path}\n"
                            f"Pairs: {catalog_path}\n"
                            f"Report: {summary_path}\n\n"
                            f"Gold preserved; candidate RMS {rms:.4f} px.", parent=self)
