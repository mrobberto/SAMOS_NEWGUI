"""
Exposure window, to handle progress bars and (non-blocking) repeat calls to read data from
the CCD device interface.

Author:
    - Brian York
"""
from astropy.io import fits
from copy import deepcopy
import numpy as np
import os
from pathlib import Path
import shutil
import time

import tkinter as tk
import ttkbootstrap as ttk
from samos.utilities.constants import *

from .common_frame import SAMOSFrame

class ExposureProgressWindow(tk.Toplevel):
    def __init__(self, parent, ccd, par, db, mfh, dmd, logger, **kwargs):
        self.parent = parent
        self.CCD = ccd
        self.PAR = par
        self.db = db
        self.main_fits_header = mfh
        self.DMD = dmd
        self.logger = logger
        super().__init__(**kwargs)

        ttk.Label(self, text="Running Exposure", font=BIGFONT).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.exposure_number = tk.StringVar(self)
        ttk.Label(self, textvariable=self.exposure_number).grid(row=1, column=0, sticky=TK_STICKY_ALL)

        self.exposure_status = tk.StringVar(self)
        ttk.Label(self, textvariable=self.exposure_status).grid(row=2, column=0, sticky=TK_STICKY_ALL)

        self.progress_status = tk.DoubleVar(self, 0.0)
        self.exposure_progress = ttk.Progressbar(self, variable=self.progress_status, maximum=100)
        self.exposure_progress.grid(row=3, column=0, sticky=TK_STICKY_ALL)


    def destroy(self):
        self.parent.start_exp_button.configure(state="normal")
        self.parent._set_expnum()
        super().destroy()


    def start_exposure(self, exptype, **params):
        """ 
        This is the landing procedure after the START button has been pressed
        """
        self.start_time = time.localtime()
        # Test and Calibration are classifications, not new hardware commands.
        # Use closed shutter for these until commissioning defines protocols.
        mappings = dict(self.CCD.EXP_MAPPINGS)
        mappings.update({"Test": "buff", "Calibration": "buff"})
        self.image_type = "sci" if mappings[exptype] == "light" else mappings[exptype]
        self.CCD.sisi_exposure_type = exptype
        self.CCD.sisi_object_name = params["image_name"]
        self.params = params
        params["ccd_temp"] = self.CCD.CCD_TEMP
        if exptype == "Science":
            params["trigger_mode"] = self.CCD.SHUTTER_OPEN
        elif exptype == "Bias":
            params["exptime"] = 0
            params["trigger_mode"] = self.CCD.SHUTTER_CLOSED
        elif exptype == "Flat":
            params["trigger_mode"] = self.CCD.SHUTTER_OPEN
        elif exptype == "Dark":
            params["trigger_mode"] = self.CCD.SHUTTER_CLOSED
        elif exptype in ("Buffer", "Test", "Calibration"):
            params["trigger_mode"] = self.CCD.SHUTTER_CLOSED
        self.expose()


    def expose(self):
        """ handle the file acquired by the SISI camera"""
        self.current_night_dir_filenames = []

        self.logger.info(f"Image Type is {self.image_type}")
        imtype = "default"
        if self.image_type in ["sci", "light"]:
            imtype = "sci_{}".format(self.params["filter"])
        elif self.image_type == "bias":
            imtype = "bias"
        elif self.image_type == "buff":
            imtype = "Buff"
        elif self.image_type == "flat":
            imtype = "flat_{}".format(self.params["filter"])
        elif self.image_type == "dark":
            imtype = "dark_{}s".format(self.params["exptime"])  # e.g. 'dark_0.01s'
        
        self.expname = "{}_{}".format(imtype, self.params['image_name'])
        self.CCD.prep_exposure(
            self.expname,
            self.params["file_number"],
            self.params["trigger_mode"],
            self.params["exptime"]
        )
        self.expnum = self.params["file_number"]
        self.collected_images = 0
        self.read_time = 0.0
        self.read_bytes = 0
        self.longest_cycle = 0
        self.start_time = time.localtime()
        self.image_number = -1
        self.collected_files = []
        self.next_exposure()


    def next_exposure(self):
        self.image_number += 1
        if self.image_number == self.params["exp_frames"]:
            self.CCD.finish_exposure(self.collected_files, self.start_time, self.read_bytes)
            self.handle_exposure()
            superfile = self.combine_files()
            results = {
                'images': self.collected_files,
                'superfile': superfile,
            }
            if getattr(self, "_ql_last_warning", ""):
                from tkinter import messagebox
                messagebox.showwarning("SISI quicklook calibration",
                                       self._ql_last_warning, parent=self)
            self.parent.display_exposure(results)
            self.destroy()
            return  # Do not initiate a new CCD exposure after final frame.
        self.exp_start_time = time.localtime()
        self.exposure_number.set(f"Exposing {self.image_number+1} of {self.params['exp_frames']}")
        self.exposure_status.set(f"Exposing for {self.params['exptime']/1000} seconds")
        self.logger.info(f"Collecting image {self.image_number+1} of {self.params['exp_frames']}")
        self.progress_status.set(0.)
        # SC3_EXPNUM_RECOVERY: reserve each number BEFORE issuing the CCD command.
        # A crash/failed exposure intentionally leaves a gap; numbers are never reused.
        from samos.system.exposure_reservations import reserve
        try:
            reserve(self.PAR.fits_dir, self.expnum,
                    object_name=self.params.get("image_name", ""),
                    exposure_type=self.params.get("image_type", ""),
                    sequence_index=self.image_number + 1)
        except (FileExistsError, OSError, ValueError) as exc:
            self.logger.error("Cannot reserve SISI exposure number %s: %s", self.expnum, exc)
            from tkinter import messagebox
            messagebox.showerror("Exposure numbering", str(exc), parent=self)
            self.destroy()
            return
        self.CCD.start_exposure()
        self.run_exposure()


    def run_exposure(self):
        if self.CCD.read_exposure(self, self.run_exposure, self.params):
            outfile, read_bytes = self.CCD.store_exposure(self.expname, self.expnum)
            self.collected_files.append(outfile)
            self.read_bytes += read_bytes
            self.expnum += 1
            self.collected_images += 1
            self.next_exposure()


    def handle_header(self, file_name, image_type, params):
        with fits.open(file_name) as hdul:
            original_header = hdul[0].header
        # Observation Parameters
        self.main_fits_header.set_param("EXPTIME", params["exptime"]/1000)
        self.main_fits_header.set_param("FILENAME", f'{Path(file_name).name}')
        self.main_fits_header.set_param("FILEDIR", f'{Path(file_name).parent}')
        # Nightly Parameters
        self.main_fits_header.set_param("OBJNAME", params["image_name"])
        self.main_fits_header.set_param("OBSTYPE", image_type)
        self.main_fits_header.set_param("COMBINED", "F")
        self.main_fits_header.set_param("NCOMBINED", 0)


    def handle_exposure(self):
        """
        Handles setting and creating a valid header, and adding a DMD map extension (if 
        available and relevant).
        """
        exptype = self.image_type
        params = self.params
        for fname in self.collected_files:
            self.handle_header(fname, exptype, params)
            with fits.open(fname, mode="update") as hdul:
                data = hdul[0].data
                original_header = hdul[0].header
                if exptype in ["sci", "flat", "buffer"]:
                    self.main_fits_header.set_param("FILTER", params["filter"])
                    self.main_fits_header.set_param("GRATING", params["grating"])
                if self.image_type == "sci":
                    if self.PAR.valid_wcs:
                        self.main_fits_header.add_astrometric_fits_keywords(original_header)
                
                if self.image_type == "sci":
                    if not hasattr(self.main_fits_header, "dmdmap"):
                        try:
                            dmd_hdu = self.create_dmd_pattern_hdu(original_header)
                            hdul.append(dmd_hdu)
                        except Exception as e:
                            self.logger.error("Unable to add DMD map to main fits header")
                            self.logger.error("Error was {}".format(e))

                # update header for new filename/filepath
                hdul[0].header = self.main_fits_header.create_fits_header(original_header)
                # Keep CCD command-dispatch provenance through header reconstruction.
                for key in ("DATE-OBS", "TIMESRC", "EXPNUM", "OBJNAME", "OBSTYPE"):
                    if key in original_header:
                        hdul[0].header[key] = original_header[key]
                # Values captured by MainPage at exposure START; not telemetry.
                hdul[0].header["GSSTATUS"] = (params.get("manual_guide_star", "UNKNOWN"),
                                              "Manual natural guide-star state")
                hdul[0].header["SAMLOOP"] = (params.get("manual_sam_loop", "UNKNOWN"),
                                             "Manual SAM laser AO-loop state")
                hdul[0].header["STATSRC"] = ("MANUAL", "Status values declared by observer")


    def combine_files(self):
        """SC3_QL_RAWSAFE_V1: never edit raw pixels during coadd/quicklook."""
        from samos.ui.ql_safe_processing import safe_combine_files
        return safe_combine_files(self)


    def create_dmd_pattern_hdu(self, primary_header):
        """
        If the DMD has a loaded pattern, create an image extension
        to add to the output file.
        """
        self.main_fits_header.set_param("extensions", True)
        dmd_hdu = fits.ImageHDU(self.DMD.current_dmd_shape)
        # check if pattern is DMD map or a grid pattern
        dmd_hdu.header["FILENAME"] = primary_header["FILENAME"]
        dmd_hdu.header["FILEDIR"] = primary_header["FILEDIR"]

        if 'unavail' in primary_header["DMDMAP"]:
            dmd_hdu.header["DMDMAP"] = primary_header["DMDMAP"]
        elif 'unavail' in primary_header["GRIDFNAM"]:
            dmd_hdu.header["GRIDFNAM"] = primary_header["GRIDFNAM"]
        return dmd_hdu


class MotorMoveProgressWindow(tk.Toplevel):
    def __init__(self, pcm, logger, wheel, destination, **kwargs):
        self.PCM = pcm
        self.logger = logger
        super().__init__(**kwargs)

        self.wheel = wheel
        self.positions = {
            "FW1": tk.DoubleVar(self, 0.),
            "FW2": tk.DoubleVar(self, 0.),
            "GR_A": tk.DoubleVar(self, 0.),
            "GR_B": tk.DoubleVar(self, 0.)
        }
        self.get_positions()
        if "GR" in wheel:
            self.wheel_type = "grism"
        else:
            self.wheel_type = "filter"
        self.destination_pos = tk.DoubleVar(self, destination)
        w = ttk.Label(self, text=f"Moving {self.wheel}", font=BIGFONT)
        w.grid(row=0, column=0, columnspan=4, sticky=TK_STICKY_ALL)
        current_row = 1
        for wheel in self.positions:
            w = ttk.Label(self, text=f"{wheel} Position:")
            w.grid(row=current_row, column=0, sticky=TK_STICKY_ALL)
            w = ttk.Label(self, textvariable=self.positions[wheel])
            w.grid(row=current_row, column=1, sticky=TK_STICKY_ALL)
            if wheel == self.wheel:
                w = ttk.Label(self, text="Destination:")
                w.grid(row=current_row, column=2, sticky=TK_STICKY_ALL)
                w = ttk.Label(self, textvariable=self.destination_pos)
                w.grid(row=current_row, column=3, sticky=TK_STICKY_ALL)
            current_row += 1
        b = ttk.Button(self, text="Stop", command=self.send_stop, bootstyle="warning")
        b.grid(row=current_row, column=3, sticky=TK_STICKY_ALL)
        self.PCM.start_move(self.wheel_type)
        self.after(2000, self.check_move)


    def get_positions(self):
        for position in self.positions:
            current_pos = self.PCM.current_filter_step(position)
            extracted_pos = self.PCM.extract_steps_from_return_string(current_pos)
            self.positions[position].set(float(extracted_pos))

    def check_move(self):
        """Check the current wheel position"""
        self.get_positions()
        if self.positions[self.wheel].get() == self.destination_pos.get():
            self.PCM.reset_indicator(self.wheel_type)
            self.destroy()
        self.after(2000, self.check_move)


    def send_stop(self):
        """Send a stop command"""
        self.PCM.motors_stop(self.wheel)
        self.PCM.reset_indicator(self.wheel_type)
        self.destroy()
