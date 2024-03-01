"""
SAMOS CCD2DMD tk Frame Class
"""
import copy
from pathlib import Path
import logging
import numpy as np
import os

from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy import units as u
from astropy import wcs
from astropy.wcs.utils import fit_wcs_from_points
from ginga.AstroImage import AstroImage
from ginga.tkw.ImageViewTk import CanvasView
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga.util.loader import load_data
import pandas as pd
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
from tkinter import ttk
import tksheet
from tkinter.filedialog import askopenfilename

from samos.dmd.pixel_mapping import Coord_Transform_Helpers as CTH
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame


"""
Coordinate transformation from DMD to Pixels (and vice versa) may need to be recalculated
User will have to take an exposure of a grid pattern, then go through steps to create a
new FITS file with the "WCS" transformation, which will be used in the CONVERT class
"""
class CCD2DMDPage(SAMOSFrame):
    """ to be written """

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "CCD-DMD Calibration", **kwargs)
        self.fits_hdu = None
        self.sources_table = None
        self.dmd_table = None
        self.DMD_PIX_df = None
        self.afftest = None
        self.coord_text = None
        self.wdir = Path(os.getcwd())
        filelist = os.listdir(self.wdir)

        # Buttons
        button_frame = tk.Frame(self.main_frame, background="cyan", borderwidth=5)
        button_frame.grid(row=0, column=0, rowspan=2, sticky=TK_STICKY_ALL, padx=5, pady=5)
        b = tk.Button(button_frame, text="Open Grid FITS File", bg="#9D76A4", command=self.browse_grid_fits_files)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.source_find_button = tk.Button(button_frame, text="Run IRAFStarFinder",
                                            bg="#9D76A4", state="disabled", command=self.iraf_starfind)
        self.source_find_button.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.run_coord_transf_button = tk.Button(button_frame, text="Initialize Coord Transform", bg="#9D76A4", 
                                                 state="disabled", command=self.run_coord_transf)
        self.run_coord_transf_button.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        
        # DMD pattern information
        tk.Label(self.main_frame, text="DMD Pattern:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.dmd_pattern_text = " "
        self.dmd_pattern_label = tk.Label(self.main_frame, text=self.dmd_pattern_text)
        self.dmd_pattern_label.grid(row=3, column=0, sticky=TK_STICKY_ALL)

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


    def cursor_cb(self, event):
        if self.fits_hdu is None:
            return
        x, y = event.xdata, event.ydata
        self.logger.info("CCD2DMD Recalibrate: Click at ({},{})".format(x, y))


    def browse_grid_fits_files(self):
        filename = askopenfilename(initialdir=get_data_file("dmd.pixel_mapping"), filetypes=[("FITS files", "*fits")],
                                   title="Select a FITS File", parent=self)

        if filename == '':
            self.logger.error("CCD2DMD Recalibrate: Null selection for FITS image!")
            tk.messagebox.showerror(title="No File Selected", message="No FITS grid file selected")
            return

        self.astro_image = load_data(filename, logger=self.logger)
        self.fitsimage.set_image(self.astro_image)
        self.fits_header = self.astro_image.as_hdu().header
        self.grid_pattern_name = self.fits_header["DMDMAP"]
        dmd_pattern_text = "DMD Pattern: {}".format(self.grid_pattern_name)
        self.dmd_pattern_label["text"] = dmd_pattern_text

        self.grid_pattern_fullPath = get_data_file("dmd.csv.slits", self.grid_pattern_name)
        dmd_table = pd.read_csv(self.grid_pattern_fullPath)
        self.dmd_table = dmd_table

        self.source_find_button["state"] = "active"
        self.run_coord_transf_button["state"] = "active"


    def rotate_dmd_table_180(self):
        numcols = int(np.sqrt(self.dmd_table.shape[0]))
        rot_dmd_tab = self.dmd_table.sort_values(by="y", ascending=False).reset_index(drop=True)

        stacked_x_rows = []
        inds = rot_dmd_tab.index.values[::11]
        for ind in range(len(inds)):
            i = inds[ind]
            if i == inds[-1]:
                sorted_row = rot_dmd_tab.iloc[i:].copy().sort_values(by="x", ascending=False)
                stacked_x_rows.extend(sorted_row.x.values)
                break
            next_ind = inds[ind+1]
            sorted_row = rot_dmd_tab.iloc[i:i + numcols].copy().sort_values(by="x", ascending=False)
            stacked_x_rows.extend(sorted_row.x.values)
        rot_dmd_tab["x"] = np.array(stacked_x_rows)


    def iraf_starfind(self):
        fwhm = 5  # float(self.source_fwhm_entry.get())
        ccd = self.astro_image.as_nddata().data

        # bright columns on left and right side of CCD that we don't want to be included 
        # in the starfinder.
        # set them to be the average of surrounding columns
        upper_avg = np.average((np.average(ccd[:, 1000:1009], axis=1), np.average(ccd[:, 1020:], axis=1)), axis=0)
        lower_avg = np.average((np.average(ccd[:, 0:20], axis=1), np.average(ccd[:, 40:50], axis=1)), axis=0)
        for col in range(1010, 1025):
            ccd[:, col] = upper_avg
        for col in range(20, 40):
            ccd[:, col] = lower_avg
        mean_ccd, median_ccd, std_ccd = sigma_clipped_stats(ccd, sigma=4.0)

        expected_sources = self.dmd_table.shape[0]
        xpixels, ypixels = [], []
        for i in self.dmd_table.index.values:
            dmd_x, dmd_y = self.dmd_table.loc[i, ["x", "y"]].values
            pix_x, pix_y = self.convert.DMD2CCD(dmd_x, dmd_y)
            xpixels.append(pix_x)
            ypixels.append(pix_y)

        xypixels = np.vstack((np.array(ypixels), np.array(xpixels))).T

        sources_table, unsorted_sources = CTH.iraf_gridsource_find(ccd, expected_sources=expected_sources, fwhm=fwhm,
                                                                   threshold=3*std_ccd)
        iraf_positions = np.transpose((sources_table['xcentroid'], sources_table['ycentroid']))
        self.sources_table = sources_table.round(3)

        DMD_PIX_df = pd.concat((self.dmd_table, self.sources_table), axis=1)
        dup_ind_col_drop = DMD_PIX_df.columns.values[0]
        DMD_PIX_df = DMD_PIX_df.drop(columns=dup_ind_col_drop)

        self.DMD_PIX_df = DMD_PIX_df
        self.tk_grid_sources_table.headers(newheaders=DMD_PIX_df.columns.values, show_headers_if_not_sheet=True, redraw=True)

        for row in DMD_PIX_df.itertuples():
            self.tk_grid_sources_table.insert_row(row=row, redraw=True)
            x_c, y_c = row.xcentroid, row.ycentroid
            reg = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)), width=40, height=40, angle=0*u.deg)
            self.fitsimage.canvas.add(r2g(reg))


    def run_coord_transf(self):
        self.afftest = CTH.AFFtest(self.DMD_PIX_df)
        self.afftest.fit_wcs_with_sip(3)

        new_hdr = self.fits_header.copy()
        imwcs = self.afftest.ccd_to_dmd_wcs.to_header(relax=True)
        imwcs.rename_keyword("PC1_1", "CD1_1")
        imwcs.rename_keyword("PC1_2", "CD1_2")
        imwcs.rename_keyword("PC2_1", "CD2_1")
        imwcs.rename_keyword("PC2_2", "CD2_2")

        for key in list(imwcs.keys()):
            new_hdr.set(key, imwcs[key])

        new_hdu = fits.PrimaryHDU(data=self.astro_image.as_nddata().data, header=new_hdr)

        img_Mapping_fpath = get_data_file("dmd.convert", "DMD_Mapping_WCS.fits")
        prev_Mapping_fname = get_data_file("dmd.convert", "DMD_Mapping_WCS_prev.fits")
        
        # change name of previous FITS file with the coordinate transformation
        # to save it just in case recalibration went wrong.
        os.rename(img_Mapping_fpath, prev_Mapping_fname)
        
        # will change this file to CONVERT/DMD_Mapping_WCS.fits once confident it works
        new_hdu.writeto(img_Mapping_fpath, overwrite=True)
        self.logger.info("New transform FITS file created")
