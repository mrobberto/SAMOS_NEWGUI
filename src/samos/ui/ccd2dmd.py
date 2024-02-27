"""
SAMOS CCD2DMD tk Frame Class
"""
import copy
import csv
from datetime import datetime
import glob
import logging
from matplotlib import pyplot as plt
import numpy as np
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import twirl
from urllib.parse import urlencode

from astropy.coordinates import SkyCoord, FK4
from astroquery.gaia import Gaia
from astropy.io import fits, ascii
from astroquery.simbad import Simbad
from astropy.stats import sigma_clipped_stats, SigmaClip
from astropy import units as u
from astropy import wcs
from astropy.wcs.utils import fit_wcs_from_points
from ginga.util import iqcalc
from ginga.AstroImage import AstroImage
from ginga.util import ap_region
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.util.loader import load_data
from ginga.misc import log
from ginga import colors as gcolors
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
import pandas as pd
from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder
from PIL import Image, ImageTk
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
from tkinter import ttk

from samos.ccd.Class_CCD_dev import Class_Camera
from samos.dmd.pixel_mapping import Coord_Transform_Helpers as CTH
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.pattern_helpers.Class_DMDGroup import DMDGroup
from samos.dmd.Class_DMD_dev import DigitalMicroMirrorDevice
from samos.motors.Class_PCM import Class_PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.astrometry.skymapper import skymapper_interrogate
from samos.astrometry.tk_class_astrometry_V5 import Astrometry
from samos.astrometry.panstarrs.image import PanStarrsImage as PS_image
from samos.astrometry.panstarrs.catalog import PanStarrsCatalog as PS_table
from samos.hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks
from samos.system import WriteFITSHead as WFH
from samos.system.SAMOS_Functions import Class_SAMOS_Functions as SF
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.system.SlitTableViewer import SlitTableView as STView
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


"""
Coordinate transformation from DMD to Pixels (and vice versa) may need to be recalculated
User will have to take an exposure of a grid pattern, then go through steps to create a
new FITS file with the "WCS" transformation, which will be used in the CONVERT class
"""
class CCD2DMDPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container, **kwargs):
        """ to be written """
        super().__init__(container)

    # =============================================================================
    #
    #  #    FITS Files Label Frame
    #
    # =============================================================================
        self.fits_hdu = None
        self.sources_table = None
        self.dmd_table = None
        self.DMD_PIX_df = None
        self.afftest = None
        self.coord_text = None

        logger = log.get_logger("example2", options=None)
        self.logger = logger
        vbox_l = tk.Frame(self, relief=tk.RAISED)
        vbox_l.pack(side=tk.LEFT)
        vbox_l.place(x=5, y=0, anchor="nw", width=220, height=550)
        self.vb_l = vbox_l

        # , width=400, height=800)
        self.frame0l = tk.Frame(
            self.vb_l, background="#9D76A4", relief=tk.RAISED)
        self.frame0l.place(x=4, y=0, anchor="nw", width=220, height=250)

        self.wdir = "./"
        filelist = os.listdir(self.wdir)

        self.file_browse_button = tk.Button(self.frame0l, text="Open Grid FITS File",
                                            bg="#9D76A4", command=self.browse_grid_fits_files)
        # browse_files.pack(side=tk.TOP)
        self.file_browse_button.pack()

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=250, y=0, anchor="nw")  # , width=500, height=800)
        # self.vb = vbox

#        canvas = tk.Canvas(vbox, bg="grey", height=514, width=522)
        canvas = tk.Canvas(vbox, bg="grey", height=516, width=528)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # => ImageViewTk -- a backend for Ginga using a Tk canvas widget
        fi = CanvasView(logger)

        # => Call this method with the Tkinter canvas that will be used for the display.
        fi.set_widget(canvas)
        # fi.set_redraw_lag(0.0)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        # fi.enable_draw(False)
        # tk seems to not take focus with a click
        fi.set_enter_focus(True)
        # fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        self.dmd_pattern_text = " "
        self.dmd_pattern_label = tk.Label(self, text=self.dmd_pattern_text)
        self.dmd_pattern_label.pack()
        self.dmd_pattern_label.place(x=520, y=545, anchor="s")

        vbox_c = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox_c.pack(side=tk.BOTTOM)
        vbox_c.place(x=60, y=545, anchor="nw")  # , width=500, height=800)
        import tksheet

        tk_grid_sources_table = tksheet.Sheet(vbox_c, width=900, height=300,
                                              column_width=60)  # tk_sources_table.headers()
        tk_grid_sources_table.grid()

        self.tk_grid_sources_table = tk_grid_sources_table
 # =============================================================================
 #
 #  #    Buttions for Source Extraction
 #      -Enter in number of sources to find in image.
 #      -Enter in approx FWHM for sources.
 #      -Initialize Coordinate transformation.
 #      -Enter SIP value and run coordinate WCS fit.
 #
 # =============================================================================

        self.source_find_button = tk.Button(self.frame0l, text="Run IRAFStarFinder",
                                            bg="#9D76A4", state="disabled", command=self.irafstarfind)
        # self.source_find_button.place(x=4)
        # self.frame1l.create_window(102,120,window=self.source_find_button)
        self.source_find_button.pack(anchor="n", padx=4, pady=15)
        # self.source_find_button.place(x=4, y=20)

        self.run_coord_transf_button = tk.Button(self.frame0l, text="Initialize Coord Transform", bg="#9D76A4", state="disabled",
                                                 command=self.run_coord_transf)
        self.run_coord_transf_button.pack(padx=15, pady=5)
        # self.run_coord_transf_button.place(x=4, y=40)

    def cursor_cb(self, event):
        """ to be written """
        if self.fits_hdu is None:
            return

        x, y = event.xdata, event.ydata

        self.coord_text = '({},{})'.format(x, y)
        self.coord_label["text"] = (self.coord_text)

    def browse_grid_fits_files(self):
        """ to be written """

        filename = tk.filedialog.askopenfilename(initialdir=self.PAR.QL_images, filetypes=[("FITS files", "*fits")],
                                                 title="Select a FITS File", parent=self.frame0l)

        if filename == '':
            print('no grid file selected')
            return

        self.AstroImage = load_data(filename, logger=self.logger)

        self.fitsimage.set_image(self.AstroImage)

        # self.source_find_button["state"] = "active"
        # self.source_fwhm_entry["state"] = "normal"
        # self.source_find_entry["state"] = "normal"

        self.fits_header = self.AstroImage.as_hdu().header
        self.grid_pattern_name = self.fits_header["DMDMAP"]
        dmd_pattern_text = "DMD Pattern: {}".format(self.grid_pattern_name)
        self.dmd_pattern_label["text"] = dmd_pattern_text

        self.grid_pattern_fullPath = get_data_file("dmd.csv.slits", self.grid_pattern_name)
        dmd_table = pd.read_csv(self.grid_pattern_fullPath)
        # .sort_values(by="y", ascending=False).reset_index(drop=True)
        self.dmd_table = dmd_table

        # self.rotate_dmd_table_180()
        self.source_find_button["state"] = "active"
        self.run_coord_transf_button["state"] = "active"

    def rotate_dmd_table_180(self):

        numcols = int(np.sqrt(self.dmd_table.shape[0]))
        rot_dmd_tab = self.dmd_table.sort_values(
            by="y", ascending=False).reset_index(drop=True)
        j = -1

        stacked_x_rows = []

        inds = rot_dmd_tab.index.values[::11]
        for ind in range(len(inds)):

            i = inds[ind]

            # print(sorted_row)
            if i == inds[-1]:
                sorted_row = rot_dmd_tab.iloc[i:].copy(
                ).sort_values(by="x", ascending=False)
                stacked_x_rows.extend(sorted_row.x.values)
                break

            next_ind = inds[ind+1]
            sorted_row = rot_dmd_tab.iloc[i:i +
                                          numcols].copy().sort_values(by="x", ascending=False)

            stacked_x_rows.extend(sorted_row.x.values)

        rot_dmd_tab["x"] = np.array(stacked_x_rows)
        print(rot_dmd_tab)
        # self.dmd_table = rot_dmd_tab.copy()

    def irafstarfind(self):  # expected_sources=53**2,fwhm=5):
        """ to be written """

        fwhm = 5  # float(self.source_fwhm_entry.get())

        ccd = self.AstroImage.as_nddata().data
        # bright columns on left and right side of CCD that we don't want to be included in the starfinder.
        # set them to be the average of surrounding columns
        colcorr_ccd = ccd.copy()
        for col in range(1010, 1025):
            colcorr_ccd[:, col] = np.average(
                (np.average(ccd[:, 1000:1009], axis=1), np.average(ccd[:, 1020:], axis=1)), axis=0)

        for col in range(20, 40):
            colcorr_ccd[:, col] = np.average(
                (np.average(ccd[:, 0:20], axis=1), np.average(ccd[:, 40:50], axis=1)), axis=0)

        ccd = colcorr_ccd.copy()

        # print(ccd.header)
        mean_ccd, median_ccd, std_ccd = sigma_clipped_stats(ccd, sigma=4.0)

        expected_sources = self.dmd_table.shape[0]
        # print(std_ccd)
        xpixels, ypixels = [], []
        for i in self.dmd_table.index.values:

            dmd_x, dmd_y = self.dmd_table.loc[i, ["x", "y"]].values
            pix_x, pix_y = convert.DMD2CCD(dmd_x, dmd_y)
            xpixels.append(pix_x)
            ypixels.append(pix_y)

#        xypixels = np.vstack((np.array(xpixels),np.array(ypixels))).T
        xypixels = np.vstack((np.array(ypixels), np.array(xpixels))).T

        # sources_table, unsorted_sources = CTH.iraf_gridsource_find(ccd,expected_sources=expected_sources,fwhm=fwhm,
        #                                                           threshold=3*std_ccd)# xycoords=xypixels, exclude_border=True)

        sources_table, unsorted_sources = CTH.iraf_gridsource_find(ccd, expected_sources=expected_sources, fwhm=fwhm,
                                                                   threshold=3*std_ccd)  # exclude_border=True)

        iraf_positions = np.transpose(
            (sources_table['xcentroid'], sources_table['ycentroid']))

        self.sources_table = sources_table.round(3)

        DMD_PIX_df = pd.concat((self.dmd_table, self.sources_table), axis=1)

        dup_ind_col_drop = DMD_PIX_df.columns.values[0]
        DMD_PIX_df = DMD_PIX_df.drop(columns=dup_ind_col_drop)
        print(DMD_PIX_df)
        print(DMD_PIX_df.columns)

        self.DMD_PIX_df = DMD_PIX_df
        self.tk_grid_sources_table.headers(newheaders=DMD_PIX_df.columns.values,
                                           show_headers_if_not_sheet=True,
                                           redraw=True)

        for i in DMD_PIX_df.index.values:

            row = DMD_PIX_df.iloc[i]
            self.tk_grid_sources_table.insert_row(values=row, redraw=True)

            x_c, y_c = row[["xcentroid", "ycentroid"]].values
            reg = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)),
                                       width=40, height=40,
                                       angle=0*u.deg)

            self.fitsimage.canvas.add(r2g(reg))
            # and we convert it to ginga.

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

        new_hdu = fits.PrimaryHDU(data=self.AstroImage.as_nddata().data,
                                  header=new_hdr)

        img_Mapping_fpath = get_data_file("dmd.convert", "DMD_Mapping_WCS.fits")
        prev_Mapping_fname = get_data_file("dmd.convert", "DMD_Mapping_WCS_prev.fits")
        # change name of previous FITS file with the coordinate transformation
        # to save it just in case recalibration went wrong.
        os.rename(img_Mapping_fpath, prev_Mapping_fname)
        # will change this file to CONVERT/DMD_Mapping_WCS.fits once confident it works
        new_hdu.writeto(img_Mapping_fpath, overwrite=True)

        print("New transform FITS file created")

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("910x650")
        parent.title("SAMOS Recalibrate CCD2DMD Transformation")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMDPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.MotorsPage))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOARPage))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
        filemenu.add_command(label="Exit", command=parent.quit)

        """
        # proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GSPage))        
        help_menu.add_separator()

        return menubar
