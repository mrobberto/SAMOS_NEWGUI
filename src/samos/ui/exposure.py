"""
Exposure window, to handle progress bars and (non-blocking) repeat calls to read data from
the CCD device interface.

Author:
    - Brian York
"""
from astropy.io import fits
import numpy as np
import time

import tkinter as tk
from tkinter import ttk

from samos.utilities import get_fits_dir
from samos.utilities.constants import *

class ExposureProgressWindow(tk.Toplevel):
    def __init__(self, parent, ccd, par, mfh, dmd, logger, **kwargs):
        self.parent = parent
        self.CCD = ccd
        self.PAR = par
        self.main_fits_header = mfh
        self.DMD = dmd
        self.logger = logger
        super().__init__(**kwargs)

        tk.Label(self, text="Running Exposure", font=BIGFONT).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.exposure_number = tk.StringVar(self)
        tk.Label(self, textvariable=self.exposure_number).grid(row=1, column=0, sticky=TK_STICKY_ALL)

        self.exposure_status = tk.StringVar(self)
        tk.Label(self, textvariable=self.exposure_status).grid(row=2, column=0, sticky=TK_STICKY_ALL)

        self.progress_status = tk.DoubleVar(self, 0.0)
        self.exposure_progress = ttk.Progressbar(self, variable=self.progress_status, maximum=100)
        self.exposure_progress.grid(row=3, column=0, sticky=TK_STICKY_ALL)


    def start_exposure(self, exptype, **params):
        """ 
        This is the landing procedure after the START button has been pressed
        """
        self.start_time = time.localtime()
        self.image_type = self.CCD.EXP_MAPPINGS[exptype]
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
        elif exptype == "Buffer":
            params["trigger_mode"] = self.CCD.SHUTTER_CLOSED
        self.expose()


    def expose(self):
        """ handle the file acquired by the SISI camera"""
        self.current_night_dir_filenames = []

        if self.image_type == "sci":
            imtype = "sci_{}".format(params["filter"])
        elif self.image_type == "bias":
            imtype = "bias"
        elif self.image_type == "buff":
            imtype = "Buff"
        elif self.image_type == "flat":
            imtype = "flat_{}".format(params["filter"])
        elif self.image_type == "dark":
            imtype = "dark_{}s".format(params["exptime"])  # e.g. 'dark_0.01s'
        
        self.expname = "{}_{}".format(imtype, params['image_name'])
        self.CCD.prep_exposure(self.exptime, params["file_number"])
        self.expnum = params["file_number"]
        self.collected_images = 0
        self.read_time = 0.0
        self.read_bytes = 0
        self.longest_cycle = 0
        self.start_time = time()
        self.image_number = -1
        self.collected_files = []
        self.next_exposure()


    def next_exposure(self):
        self.image_number += 1
        if self.image_number == self.params["exp_frames"]:
            self.CCD.finish_exposure(self.collected_files, self.start_time, self.longest_cycle, self.read_time, self.read_bytes)
            self.handle_exposure()
            superfile = self.combine_files()
            results = {
                'images': self.collected_files,
                'superfile': superfile,
            }
            if exptype == "Bias":
                shutil.copy(superfile, self.PAR.QL_images / "superbias.fits")
                results["superbias"] = self.PAR.QL_images / "superbias.fits"
            elif exptype == "Buffer":
                shutil.copy(superfile, self.PAR.QL_images / "superbuffer.fits")
                results["superbuffer"] = self.PAR.QL_images / "superbuffer.fits"
            self.parent.display_exposure(results)
            self.destroy()
        self.exp_start_time = time.time()
        self.exposure_number.set(f"Exposing {image_number+1} of {params['exp_frames']}")
        self.exposure_status.set(f"Exposing for {params['exptime']/1000} seconds")
        self.logger.info("Collecting image {} of {}".format(image_number+1, params['exp_frames']))
        self.progress_status.set(0.)
        self.ccd.start_exposure()
        self.run_exposure()


    def run_exposure(self):
        if self.CCD.read_exposure(self, self.run_exposure, self.params):
            outfile, cycle_time, read_time, read_bytes = self.CCD.store_exposure(self.expname, self.expnum)
            self.collected_files.append(outfile)
            if cycle_time > self.longest_cycle:
                self.longest_cycle = cycle_time
            self.read_time += read_time
            self.read_bytes += read_bytes
            self.expnum += 1
            self.collected_images += 1
            self.next_exposure()


    def handle_header(self, file_name, image_type, params):
        with fits.open(file_name) in hdul:
            original_header = hdul[0].header
        # Observation Parameters
        self.main_fits_header.set_param("EXPTIME", params["exptime"]/1000)
        self.main_fits_header.set_param("FILENAME", f'{file_name.name}')
        self.main_fits_header.set_param("FILEDIR", f'{file_name.parent}')
        # Nightly Parameters
        self.main_fits_header.set_param("OBSERVERS", self.PAR.PotN["Observer"])
        self.main_fits_header.set_param("PROGRAMID", self.PAR.PotN["Program ID"])
        self.main_fits_header.set_param("TELOPERATORS", self.PAR.PotN["Telescope Operator"])
        self.main_fits_header.set_param("OBJNAME", params["image_name"])
        self.main_fits_header.set_param("OBSTYPE", image_type)
        self.main_fits_header.set_param("COMBINED", "F")
        self.main_fits_header.set_param("NCOMBINED", 0)
        self.main_fits_header.create_fits_header(original_header)


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
                if exptype == "sci":
                    if self.PAR.valid_wcs:
                        self.main_fits_header.add_astrometric_fits_keywords(original_header)
                
                if exptype == "sci":
                    if not hasattr(self.main_fits_header, "dmdmap"):
                        try:
                            dmd_hdu = self.create_dmd_pattern_hdu(self.main_fits_header.output_header)
                            hdul.append(dmd_hdu)
                        except Exception as e:
                            self.logger.error("Unable to add DMD map to main fits header")
                            self.logger.error("Error was {}".format(e))

                # update header for new filename/filepath
                self.main_fits_header.create_fits_header(main_fits_header.output_header)
                hdul[0].header = self.main_fits_header.output_header


    def combine_files(self):
        """
         this procedure runs after CCD.expose()
         to handle the decision of saving all single files or just the averages
         """
        image_type = self.image_type
        files = self.collected_files
        last_number = self.expnum - 1
        params = self.params

        superfile_cube = np.zeros((1032, 1056, len(files)))  # note y,x,z

        dmd_hdu = None
        if exptype == "sci":
            if not hasattr(self.main_fits_header, "dmdmap"):
                try:
                    dmd_hdu = self.create_dmd_pattern_hdu(self.main_fits_header.output_header)
                except Exception as e:
                    self.logger.error("Unable to add DMD map to main fits header")
                    self.logger.error("Error was {}".format(e))

        # Loop through files
        for i, file_name in files:
            with fits.open(file_name, mode="update") as hdul:
                data = hdul[0].data
                if image_type in ["flat", "dark"] and params["sub_bias"]:
                    bias_file = self.PAR.QL_images / "superbias.fits"
                    if bias_file.is_file():
                        with fits.open(bias_file) as hdu_bias:
                            bias = hdu_bias[0].data
                        data -= bias
                        hdul[0].header["MSTRBIAS"] = (bias_file, "Master Bias File used for bias subtraction")

                if image_type in ["flat"] and params["sub_dark"]:
                    dark_file = self.PAR.QL_images / "superdark_s.fits"
                    if dark_file.is_file():
                        with fits.open(dark_file) as hdu_dark:
                            dark = hdu_dark[0].data
                        # Dark is in counts/s
                        dark *= params["exptime"] / 1000
                        data -= dark
                        hdul[0].header["MSTRDARK"] = (dark_file, "Master Dark File used for dark subtraction")

                if image_type == "dark":
                    # PARAM2 is the exposure time for the original single exposure
                    superfile_cube[:, :, i] = hdul[0].data / (hdul[0].header["PARAM2"] / 1000)
                else:
                    superfile_cube[:, :, i] = hdul[0].data
                superfile_header = deepcopy(hdul[0].header)
                
            # If not saving individual files
            if not params["save_individual"]:
                os.remove(file_name)

        if image_type == "flat":
            running_flat = superfile_cube.sum(axis=2)
            median_running_flat = np.median(running_flat)
            superflat = running_flat / median_running_flat
            superflat_file = self.PAR.QL_images / f"superflat_{params['filter']}.fits"
            superflat_hdu = fits.PrimaryHDU(data=superflat, header=superfile_header)
            superflat_hdu.writeto(superflat_file, overwrite=True)
        elif image_type == "dark":
            superdark_s = superfile_cube.sum(axis=2)
            superdark_s /= len(files)
            superdark_file = self.PAR.QL_images / "superdark_s.fits"
            superdark_hdu = fits.PrimaryHDU(data=superdark_s, header=superfile_header)
            superdark_hdu.header["EXPTIME"] = 1
            superdark_hdu.writeto(superdark_file, overwrite=True)

        superfile_data = superfile_cube.mean(axis=2)
        superfile_path = self.PAR.QL_images

        if image_type == "sci":
            # Check for bias file
            if params["sub_bias"]:
                bias_file = self.PAR.QL_images / "superbias.fits"
                if bias_file.is_file():
                    with fits.open(bias_file) as hdu_bias:
                        bias = hdu_bias[0].data
                    data -= bias
                    superfile_header["MSTRBIAS"] = (bias_file, "Master Bias File used for bias subtraction")

            # Check for dark file
            if params["sub_dark"]:
                dark_file = self.PAR.QL_images / "superdark_s.fits"
                if dark_file.is_file():
                    with fits.open(dark_file) as hdu_dark:
                        dark = hdu_dark[0].data
                    # Dark is in counts/s
                    dark *= params["exptime"] / 1000
                    data -= dark
                    superfile_header["MSTRDARK"] = (dark_file, "Master Dark File used for dark subtraction")

            # Check for flat file
            if params["sub_flat"]:
                flat_file = self.PAR.QL_images / "superflat_{}.fits".format(params['filter'])
                if flat_file.is_file():
                    with fits.open(flat_file) as hdu_flat:
                        flat = hdu_flat[0].data
                    data = np.divide(data, flat)
                    superfile_header["MSTRFLAT"] = (flat_file, "Master Flat File used for flat division")

            # Check for buffer file
            if params["sub_buffer"]:
                buffer_file = self.PAR.QL_images / "superbuffer.fits"
                if buffer_file.is_file():
                    with fits.open(buffer_file) as hdu_buffer:
                        buffer = hdu_buffer[0].data
                    data -= buffer
                    superfile_header["MSTRBUFF"] = (buffer_file, "Master Buffer File used for buffer subtraction")
        
        if image_type in ["sci", "flat"]:
            superfile_name = "{}_{}_coadd.fits".format(image_type, params["filter"])
            superfile_numbered = f"{image_type}_{params['filter']}s_{params['image_name']}_{last_number:04n}_coadd.fits"
        elif image_type == "dark":
            superfile_numbered = f"{image_type}_{params['exptime']/1000}_{params['image_name']}_{last_number:04n}_coadd.fits"
        else:
            superfile_name = "{}_coadd.fits".format(image_type)
            superfile_numbered = f"{image_type}_{params['image_name']}_{last_number:04n}_coadd.fits"
        
        self.main_fits_header.set_param("filename", superfile_name)
        self.main_fits_header.set_param("combined", "T")
        self.mail_fits_header.set_param("ncombined", len(files))
        self.main_fits_header.set_param("obstype", image_type.upper())
        self.main_fits_header.create_fits_header(superfile_header)
        super_hdu = fits.PrimaryHDU(header=self.main_fits_header.output_header, data=superfile_data)
        hdul = fits.HDUList(hdus=[super_hdu])
        if image_type == "sci" and dmd_hdu is not None:
            hdul.append(dmd_hdu)
        hdul.writeto(self.PAR.QL_images / superfile_name, overwrite=True)

        self.main_fits_header.set_param("filename", superfile_numbered)
        self.main_fits_header.set_param("filedir", self.fits_dir)
        self.main_fits_header.set_param("combined", "T")
        self.mail_fits_header.set_param("ncombined", len(files))
        self.main_fits_header.set_param("obstype", image_type.upper())
        self.main_fits_header.create_fits_header(superfile_header)
        super_hdu = fits.PrimaryHDU(header=self.main_fits_header.output_header, data=superfile_data)
        hdul = fits.HDUList(hdus=[super_hdu])
        if image_type == "sci" and dmd_hdu is not None:
            hdul.append(dmd_hdu)
        hdul.writeto(get_fits_dir() / superfile_numbered, overwrite=True)

        return get_fits_dir() / superfile_numbered


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

        self.main_fits_header.create_fits_header(primary_header)
        return dmd_hdu
