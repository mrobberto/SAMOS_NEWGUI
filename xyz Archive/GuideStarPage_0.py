"""#!/usr/bin/env python3
# -*- coding: utf-8 -*-
Created on Tue Feb 25 13:21:00 2023

"""
from sys import platform
from SAMOS_DMD_dev.DMD_get_pixel_mapping_GUI_dana import Coord_Transform_Helpers as CTH
from SAMOS_DMD_dev.CONVERT.CONVERT_class import CONVERT
from SAMOS_DMD_dev.DMD_Pattern_Helpers.Class_DMDGroup import DMDGroup
from SAMOS_DMD_dev.Class_DMD_dev import DigitalMicroMirrorDevice
from SAMOS_MOTORS_dev.Class_PCM import Class_PCM
from SAMOS_SOAR_dev.Class_SOAR import Class_SOAR
from SAMOS_CCD_dev.Class_CCD_dev import Class_Camera
# from SAMOS_CCD_dev.Class_CCD_dev import Class_Camera
from SAMOS_Astrometry_dev.skymapper_interrogate import skymapper_interrogate
from SAMOS_Astrometry_dev.tk_class_astrometry_V5 import Astrometry
from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF
from SAMOS_system_dev.SlitTableViewer import SlitTableView as STView
from SAMOS_ETC.SAMOS_SPECTRAL_ETC import ETC_Spectral_Page as ETCPage
import SAMOS_system_dev.utils as U
import SAMOS_system_dev.WriteFITSHead as WFH

from SAMOS_system_dev.SAMOS_Parameters_out import SAMOS_Parameters


import re  # re module of the standard library handles strings, e.g. use re.search() to extract substrings
# , PointPixelRegion, RegionVisual
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion
from astroquery.simbad import Simbad
# from SAMOS_MOTORS_dev.Class_PCM import Class_PCM
import time

# from SAMOS_Astrometry_dev.skymapper_interrogate_VOTABLE import skymapper_interrogate_VOTABLE
import glob
import pathlib
import math
from regions import Regions
import aplpy
import twirl
from matplotlib import pyplot as plt
from urllib.parse import urlencode
from astropy.wcs.utils import fit_wcs_from_points
from astroquery.gaia import Gaia
from ginga.util import iqcalc
from ginga.AstroImage import AstroImage
from ginga.util import ap_region
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.util.loader import load_data
from ginga.misc import log
import ginga.colors as gcolors
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import csv
import tkinter as tk
# from tkinter import *
# import tkinter as tk  #small t for Python 3f
from tkinter import ttk
from tkinter import messagebox

# import filedialog module
from tkinter import filedialog
# from tkinter.filedialog import askopenfilename
# from tkinter.filedialog import asksaveasfile

from astropy.coordinates import SkyCoord, FK4  # , ICRS, Galactic, FK5
from astropy import units as u
from astropy.io import fits, ascii
from astropy.stats import sigma_clipped_stats, SigmaClip
import astropy.wcs as wcs


from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder


import shutil
import copy
# from esutil import htm

from PIL import Image, ImageTk  # , ImageOps
from Hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks

import os
import sys
cwd = os.getcwd()
print(cwd)


# define the local directory, absolute so it is not messed up when this is called

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)
sys.path.append(parent_dir)

"""
#############################################################################################################################################
#
# ---------------------------------------- GUIDESTAR PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class GuideStarPage(tk.Tk):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """
        super().__init__(container)

        #self.DMDPage = DMDPage
        self.PAR = SAMOS_Parameters()
        self.ConfP = ConfigPage(parent,container)

        self.container = container
        
        self.initialize_slit_table()

        logger = log.get_logger("example2", options=None)
        self.logger = logger

        label = tk.Label(self, text="Main Page", font=('Times', '20'))
        label.pack(pady=0, padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        if platform == "win32":
            self.bigfont = ("Arial", 12, 'bold')
            self.bigfont_20 = ("Arial", 12, 'bold')
            self.bigfont_15 = ("Arial", 10, 'bold')
        else:
            self.bigfont = ("Arial", 24)
            self.bigfont_20 = ("Arial", 20)
            self.bigfont_15 = ("Arial", 15)

        # keep track of the entry number for header keys that need to be added
        # will be used to write "OtherParameters.txt"
        self.extra_header_params = 0
        # keep string of entries to write to a file after acquisition.
        self.header_entry_string = ''
        main_fits_header.create_main_params_dict()
        self.wcs = None
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        #self.SlitTabView = None
        self.loaded_regfile = None
        today = datetime.now()
        self.fits_dir = os.path.join(
            parent_dir, "SISI_images", "SAMOS_" + today.strftime('%Y%m%d'))



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    OBSERVER/NIGHT INFO Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.wcs_exist = None





# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    FITS manager
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame_FITSmanager = tk.Frame(self, background="pink")
        self.frame_FITSmanager.place(
            x=10, y=620, anchor="nw", width=420, height=190)

        labelframe_FITSmanager = tk.LabelFrame(
            self.frame_FITSmanager, text="FITS manager", font=self.bigfont)
        labelframe_FITSmanager.pack(fill="both", expand="yes")

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#
#
#         label_FW1 =  tk.Label(labelframe_Filters, text="Filter Wheel 1")
#         label_FW1.place(x=4,y=10)
#         entry_FW1 = tk.Entry(labelframe_Filters, width=5,  bd =3)
#         entry_FW1.place(x=100, y=10)
#         label_FW2 =  tk.Label(labelframe_Filters, text="Filter Wheel 2")
#         label_FW2.place(x=4,y=40)
#         entry_FW2 = tk.Entry(labelframe_Filters, width=5, bd =3)
#         entry_FW2.place(x=100, y=40)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        button_FITS_Load = tk.Button(labelframe_FITSmanager, text="Load existing file", bd=3,
                                     command=self.load_existing_file)
        button_FITS_Load.place(x=0, y=0)

        """ RA Entry box"""
        self.string_RA = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA.set("150.17110")  # NGC 3105
        label_RA = tk.Label(labelframe_FITSmanager, text='RA:',  bd=3)
        self.entry_RA = tk.Entry(
            labelframe_FITSmanager, width=11,  bd=3, textvariable=self.string_RA)
        label_RA.place(x=150, y=1)
        self.entry_RA.place(x=190, y=-5)

        """ DEC Entry box"""
        self.string_DEC = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC.set("-54.79004")  # NGC 3105
        label_DEC = tk.Label(labelframe_FITSmanager, text='Dec:',  bd=3)
        self.entry_DEC = tk.Entry(
            labelframe_FITSmanager, width=11,  bd=3, textvariable=self.string_DEC)
        label_DEC.place(x=150, y=20)
        self.entry_DEC.place(x=190, y=20)
        
        button_RADEC_to_SOAR = tk.Button(labelframe_FITSmanager, text="Send to SOAR", bd=3,
                             command=self.send_RADEC_to_SOAR)
        button_RADEC_to_SOAR.place(x=300, y=8)

# =============================================================================
#      QUERY Server
#
# =============================================================================
        labelframe_Query_Survey = tk.LabelFrame(labelframe_FITSmanager, text="Query Image Server",
                                                width=400, height=110,
                                                font=self.bigfont)
        labelframe_Query_Survey.place(x=5, y=45)


        self.label_SelectSurvey = tk.Label(
            labelframe_Query_Survey, text="Survey")
        self.label_SelectSurvey.place(x=5, y=5)
#        # Dropdown menu options
        Survey_options = [
            "SkyMapper",
            "SDSS",
            "PanSTARRS/DR1/", #SIMBAD - 
            "DSS",          #SIMBAD - 
            "DSS2/red",     #SIMBAD - 
            "CDS/P/AKARI/FIS/N160", #SIMBAD - 
            "2MASS/J",      #SIMBAD -  
            "GALEX",        # SIMBAD - 
            "AllWISE/W3"]   # SIMBAD - 
#        # datatype of menu text
        self.Survey_selected = tk.StringVar()
#        # initial menu text
        self.Survey_selected.set(Survey_options[0])
#        # Create Dropdown menu
        self.menu_Survey = tk.OptionMenu(
            labelframe_Query_Survey, self.Survey_selected,  *Survey_options)
        # add bar to split menu, see
        # https://stackoverflow.com/questions/55621073/add-a-separator-to-an-option-menu-in-python-with-tkinter
        self.menu_Survey['menu'].insert_separator(3)
        self.menu_Survey.place(x=65, y=5)

#        self.readout_Simbad = tk.Label(self.frame0l, text='')


#        """ SkyMapper Query """
#        #button_skymapper_query = tk.Button(labelframe_FITSmanager, text="SkyMapper Query", bd=1,
#        #                                   command=self.SkyMapper_query)
#        #button_skymapper_query.place(x=190, y=65)
#
#        """ SkyMapper or SDSS query"""
#        griz_Survey_options = [
#            "SkyMapper Query",
#            "SDSS Query"]
#        # datatype of menu text
#        self.griz_Survey_selected = tk.StringVar()
#        # initial menu text
#        self.griz_Survey_selected.set(griz_Survey_options[0])
#        # Create Dropdown menu
#        self.griz_menu_Survey = tk.OptionMenu(
#            labelframe_FITSmanager, self.griz_Survey_selected,  *griz_Survey_options)
#        self.griz_menu_Survey.place(x=190, y=65)

        
        
        """ Filter Entry box"""
        self.string_Filter = tk.StringVar()
        self.string_Filter.set("i")
        label_Filter = tk.Label(labelframe_Query_Survey, text='Filter:',  bd=3)
        entry_Filter = tk.Entry(labelframe_Query_Survey,
                                width=2,  bd=3, textvariable=self.string_Filter)
        label_Filter.place(x=195, y=5)
        entry_Filter.place(x=240, y=4)
        
        """ QUERY BUTTON"""
        button_Query_Survey = tk.Button(
            labelframe_Query_Survey, text="Query", bd=3, command=self.Query_Survey)
        button_Query_Survey.place(x=300, y=5)


        """ Nr. of Stars Entry box"""
        label_nrofstars = tk.Label(
            labelframe_Query_Survey, text="Nr. of stars:")
        label_nrofstars.place(x=5, y=36)
        self.nrofstars = tk.IntVar()
        entry_nrofstars = tk.Entry(
            labelframe_Query_Survey, width=3,  bd=3, textvariable=self.nrofstars)
        entry_nrofstars.place(x=80, y=35)
        self.nrofstars.set('25')

        """ twirl Astrometry"""
        button_twirl_Astrometry = tk.Button(labelframe_Query_Survey, text="twirl WCS", bd=3,
                                            command=self.twirl_Astrometry)
        button_twirl_Astrometry.place(x=120, y=35)

        """ find stars"""
        button_find_stars = tk.Button(labelframe_Query_Survey, text="Find stars", bd=3,
                                            command=self.find_stars, state='active')#'disabled')
        button_find_stars.place(x=220, y=35)
        self.button_find_stars = button_find_stars

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        button_Astrometry =  tk.Button(labelframe_FITSmanager, text="Astrometry", bd=3,
#                                            command=Astrometry)
#                                            command=self.load_Astrometry)
#        button_Astrometry.place(x=0,y=110)

#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# GINGA DISPLAY
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=450, y=0, anchor="nw")  # , width=500, height=800)
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
        fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        canvas = self.canvas_types.DrawingCanvas()
        canvas.enable_draw(True)
        canvas.enable_edit(True)
        canvas.set_drawtype('box', color='red')
#        canvas.set_drawtype('point', color='red')
        canvas.register_for_cursor_drawing(fi)
        canvas.add_callback('draw-event', self.draw_cb)
        canvas.set_draw_mode('draw')
        # without this call, you can only draw with the right mouse button
        # using the default user interface bindings
        # canvas.register_for_cursor_drawing(fi)

        canvas.ui_set_active(True)
        self.canvas = canvas


#        # add canvas to viewers default canvas
        fi.get_canvas().add(canvas)

        self.drawtypes = canvas.get_drawtypes()
        self.drawtypes.sort()

#        fi.configure(516, 528) #height, width
        fi.set_window_size(514, 522)

        self.readout = tk.Label(vbox, text='')
        self.readout.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
        # self.readout.place()

        """
        HORIZONTAL BOX AT THE BOTTOM WITH ORIGINAL GINGA TOOLS
        """

        hbox = tk.Frame(self)
        hbox.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.drawtypes = canvas.get_drawtypes()
        # wdrawtype = ttk.Combobox(self, values=self.drawtypes,
        # command=self.set_drawparams)
        # index = self.drawtypes.index('ruler')
        # wdrawtype.current(index)
        wdrawtype = tk.Entry(hbox, width=12)
        wdrawtype.insert(0, 'box')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype

        wdrawcolor = ttk.Combobox(
            hbox, values=self.drawcolors, style="TCombobox")  # ,
        #                           command=self.set_drawparams)
        index = self.drawcolors.index('red')
        wdrawcolor.current(index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        # wdrawcolor = tk.Entry(hbox, width=12)
        # wdrawcolor.insert(0, 'blue')
        # wdrawcolor.bind("<Return>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor

        self.vfill = tk.IntVar()
        wfill = tk.Checkbutton(hbox, text="Fill", variable=self.vfill)
        self.wfill = wfill

        walpha = tk.Entry(hbox, width=12)
        walpha.insert(0, '1.0')
        walpha.bind("<Return>", self.set_drawparams)
        self.walpha = walpha

        wrun = tk.Button(hbox, text="Slits Only",
                         command=self.slits_only)
        wclear = tk.Button(hbox, text="Clear Canvas",
                           command=self.clear_canvas)
        wsave = tk.Button(hbox, text="Save Canvas",
                          command=self.save_canvas)
        wopen = tk.Button(hbox, text="Open File",
                          command=self.open_file)
        # pressing quit button freezes application and forces kernel restart.
        wquit = tk.Button(hbox, text="Quit",
                          #command=lambda: self.quit(self))
                          command=self.MASTER_quit)

        for w in (wquit, wsave, wclear, wrun, walpha, tk.Label(hbox, text='Alpha:'),
                  #                  wfill, wdrawcolor, wslit, wdrawtype, wopen):
                  wfill, wdrawcolor, wdrawtype, wopen):
            w.pack(side=tk.RIGHT)

        # mode = self.canvas.get_draw_mode() #initially set to draw by line >canvas.set_draw_mode('draw')



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    DMD Handler Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        #, width=400, height=800)
        self.frame0r = tk.Frame(self,background="cyan")
        self.frame0r.place(x=1270, y=10, anchor="nw", width=360, height=120)

        labelframe_DMD =  tk.LabelFrame(
            self.frame0r, text="DMD", font=("Arial", 24))
        labelframe_DMD.pack(fill="both", expand="yes")

         # 1) Set the x size of the default slit
         # 2) Set the y size of the default slit
         # 3) save slit pattern to file
         # 4) save and push slit pattern
         # 5) load slit pattern
         # 6) shift slit pattern
         # 7) analyze point source
         # 8) remove slit



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load AP Region file in RADEC
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#    def save_regions_DMD_AstropyReg(self):
#        """ to be written """
#        pass

#    def push_DMD(self):
#        """ to be written """
#        pass

    def load_regfile_csv(self):
        """ to be written """
        self.LoadSlits()
        pass

    def save_regions_xy2xyfile(self):
        """ Save (x,y) Astropy Regions to .reg file """
        """ converting Ginga Regions to AP/radec Regions
            - collects/compound all Ginga Regions in RRR_xyGA
            - convert to AP/xy   (aka RRR_xyAP)
            - write to AP/xy .region file
                => requires WCS
        """

        print("saving (x,y) Astropy Regions to .reg file")
        file = filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                        defaultextension=".reg",
                                        initialdir=os.path.join(local_dir, "SAMOS_regions", "pixels"))
        # 1. Collect all
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        # 2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        # 3. Write astropy regions, pixels
        self.RRR_xyAP.write(file.name, overwrite=True)
        print("(x,y) Astropy Regions to .reg file:\n", file.name)

#    def push_CCD(self):
#        """ to be written """
#        pass

#    def change_out_fnumber(self):
#        """
#        Returns
#        -------
#        Incremental change in Exposure number to be appended to the end of filenames.
#
#        """
#        return

    def write_GingaRegions_ds9adFile(self):
        """ collect all Ginga regions and save to a ds9/ad .reg file
            - collect all Ginga xy Regions in a AP/ad list
                uses convert_GAxy_APad()
            - wites the AP/ad on file list as set of ds9/ad region files
        """
        if "RRR_RADec" not in dir(self):
            print("There are no (RA,Dec) regions to be written on file")
            return
        else:
            print("saving (RA,DEC) Astropy Regions to .reg file")
            file = filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                            defaultextension=".reg",
                                            initialdir=os.path.join(local_dir, "SAMOS_regions", "RADEC"))
        # we want to scoop all objects on the canvas
        # obj_all = CM.CompoundMixin.get_objects(self.canvas)
            self.RRR_RADec = self.convert_GAxy_APad()
            print("\ncollected all Ginga xy Regions in a AP/ad list (aka RRR_RADec")
            self.RRR_RADec.write(file.name, overwrite=True)
            print("saved  AP/ad list to ds/ad region file file:\n", file.name)
            print(
                "\ncollected all Ginga xy Regions to ads/ad region file file:\n", file.name)

    """
    def save_RADECregions_AstropyXYRegFile(self):
        print("saving (x,y) Astropy Regions to .reg file")
        self.display_ds9ad_GingaAP()
        file = filedialog.asksaveasfile(filetypes = [("txt file", ".reg")],
                                        defaultextension = ".reg",
                                        initialdir=local_dir+"/SAMOS_regions/pixels")
        self.RRR_xyAP.write(file.name, overwrite=True)
    """

    def display_ds9ad_Ginga(self):
        """ converting ds9/radec Regions to AP/radec Regions
            - open ds9/radec region file and convert to AP/xy (aka RRR_xyAP)
                -> requires WCS
            - convert AP/xy to Ginga/xy (aka RRR_xyGA)
            - convert AP/xy to AP/ad (aka RRR_RADec)
        """
        print("displaying ds9/radec Regions on Ginga\n")
        # requires wcs: class AStrometry
        if 'wcs' not in dir(self):
            print("missing self.wcs. No operation performed \n")
            return
        self.RRR_xyAP = Astrometry.APRegion_RAD2pix(
            self.filename_regfile_RADEC, self.wcs)
        print("\nopened ds9/radec region file and converted to AP/xy (aka RRR_xyAP)\n => used current WCS")

        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("\nconverted AP/xy to Ginga/xy (aka RRR_xyGA)")

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP, self.wcs)
        print("converted AP/xy to APradec (aka RRR_RADec)")
        self.SlitTabView.load_table_from_regfile_RADEC(regs_RADEC=self.RRR_RADec,
                                                       img_wcs=self.wcs)
        print("displayed APradec regions on Ginga display")

        # return self.RRR_xyAP

    def convert_GAxy_APad(self):
        """ converting Ginga Regions to AP/radec Regions
            - collects/compound all Ginga Regions in RRR_xyGA
            - convert tho AP/xy   (aka RRR_xyAP)
            - convert to AP/radec (aka RRR_RADec)
                => requires WCS
        """
        print("converting Ginga Regions to AP/radec Regions")
        # requires wcs: class AStrometry
        if 'wcs' not in dir(self):
            print("missing self.wcs. No operation performed \n")
            return
        # 1. Collect all objects in ginga canvas
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("\ncollected/compounded all Ginga Regions in RRR_GAxy")
        # 2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        print("converted GA/xy to AP/xy   (aka RRR_xyAP)")
        # 3. convert to RADEC using wcs
        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP, self.wcs)
        print("converted AP/xy converted to AP/ad (aka RRR_RADec")
        print("\nCompleted conversion Ginga Regions to AP/radec Regions ")
        return self.RRR_RADec

    def draw_slits(self):

        # all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        # color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas, color="red")
        # [print("draw-slits obj tags ", obj.tag) for obj in all_ginga_objects]
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)

    """
    def convert_regions_xyAP2slit(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        # color in RED all the regions loaded from .reg file
        # requires Dana wcs
        # returns .csv map file
        pass
    """

    def convert_regions_slit2xyAP(self):
        """ to be written """
        # requires Dana wcs
        # returns RRR_xyAP
        pass

    def convert_regions_xyAP2xyGA(self):
        """ converting (x,y) Astropy Regions to (x,y) Ginga Regions """
        print("converting (x,y) Astropy Regions to (x,y) Ginga Regions")

        # cleanup, keep only the slits
        self.slits_only()

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        # [CM.CompoundMixin.add_object(self.canvas,r2g(reg)) for reg in self.RRR_xyAP]
        for reg in range(len(self.RRR_xyAP)):
            this_reg = self.RRR_xyAP[reg]
            this_obj = r2g(this_reg)
            this_obj.pickable = True
            this_obj.add_callback('pick-down', self.pick_cb, 'down')
            this_obj.add_callback('pick-up', self.pick_cb, 'up')

            this_obj.add_callback('pick-key', self.pick_cb, 'key')
            self.canvas.add(this_obj)
            # ap_region.add_region(self.canvas, this_reg)
            if reg < 10 or reg == len(self.RRR_xyAP)-1:
                print("reg number {} tag: {}".format(reg, this_obj.tag))
            self.SlitTabView.slit_obj_tags.append(this_obj.tag)
        # [print("cm object tags", obj.tag) for obj in self.canvas.get_objects()]
        # uses r2g
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("(x,y) Astropy regions converted to (x,y) Ginga regions\nRRR_xyGA created")
        return self.RRR_xyGA
        # self.RRR_xyGA is a self.canvas.objects

    def convert_regions_xyGA2xyAP(self):
        """ converting (x,y) Ginga Regions to (x,y) Astropy Regions """
        print("converting (x,y) Ginga Regions to (x,y) Astropy Regions")
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        list_all_ginga_objects = list(all_ginga_objects)
        if len(list_all_ginga_objects) != 0:
            self.RRR_xyAP = Regions([g2r(list_all_ginga_objects[0])])
            for i in range(1, len(list_all_ginga_objects)):
                self.RRR_xyAP.append(g2r(list_all_ginga_objects[i]))
        return self.RRR_xyAP
        print("(x,y) Ginga regions converted to (x,y) Astropy regions")
        
    def push_RADEC(self):
        """ to be written """
        self.string_RA = tk.StringVar(self, self.RA_regCNTR)
        self.string_DEC = tk.StringVar(self, self.DEC_regCNTR)
        self.entry_RA.delete(0, tk.END)
        self.entry_DEC.delete(0, tk.END)
        self.entry_RA.insert(0, self.RA_regCNTR)
        self.entry_DEC.insert(0, self.DEC_regCNTR)
        print("RADEC loaded")

    def load_regfile_RADEC(self):
        """ read (RA,DEC) Regions from .reg file
        - open ds9/ad file and read the regions files creating a AP/ad list of regions (aka RRR_RADec)
        - extract center RA, Dec
        """
        print("read ds9/ad .reg file to create AP/ad regions (aka RRR_RADec")
        self.textbox_filename_regfile_RADEC.delete('1.0', tk.END)
#        self.textbox_filename_slits.delete('1.0', tk.END)
        self.filename_regfile_RADEC = filedialog.askopenfilename(initialdir=os.path.join(local_dir, "SAMOS_regions", "RADEC"),
                                                                 title="Select a File",
                                                                 filetypes=(("Text files",
                                                                             "*.reg"),
                                                                            ("all files",
                                                                             "*.*")))
        self.loaded_regfile = os.path.split(self.filename_regfile_RADEC)[1]
        # First read the file and set the regions in original RADEC units
        self.RRR_RADec = Regions.read(
            self.filename_regfile_RADEC, format='ds9')
        filtered_duplicates_regions = []
        for reg in self.RRR_RADec:
            if reg not in filtered_duplicates_regions:
                filtered_duplicates_regions.append(reg)

        self.RRR_RADec = filtered_duplicates_regions
        #
        # Then extract the clean filename to get RA and DEC of the central point
        head, tail = os.path.split(self.filename_regfile_RADEC)
        self.textbox_filename_regfile_RADEC.insert(tk.END, tail)
        
        # find the opject t name reading all characters up to the first "_"
        self.target_name = tail[0:tail.find("_")] 
        
        #write the object name in the Science tab
        self.ObjectName.set(self.target_name)        
                
        # the filename must carry the RADEC coordinates are "RADEC_". Find this string...
        s = re.search(r'RADEC=', tail)
        # extract RADEC
        RADEC = tail[s.end():-4]
        RA_cut = (re.findall('.*-', RADEC))
        # and RA, DEC as strings at disposal
        self.RA_regCNTR = RA_cut[0][:-1]
        self.DEC_regCNTR = (re.findall('-.*', RADEC))[0]
        # we return the filename
        print("(RA,DEC) Regions loaded from .reg file")

        return self.filename_regfile_RADEC

    def load_ds9regfile_xyAP(self):
        """ read (x,y) Astropy  Regions from ds9 .reg file
            - open ds9 .reg file in pixels units
            - extract the clean filename to get RA and DEC of the central point
            - create AP.xy regions (aka RRR_xyAP)
            - visualize xyAP regions on GINGA display\n
                => WCS solution needed
            - convert xyAP regions to GINGA regions (aka RRR_xyGA)
        """
        print("\n Load ds9/xy reg. file")
        reg = filedialog.askopenfilename(filetypes=[("region files", "*.reg")],
                                         initialdir=os.path.join(local_dir, 'SAMOS_regions', 'pixels'))
        print("reading (x,y) Astropy region file")
        if isinstance(reg, tuple):
            regfileName = reg[0]
        else:
            regfileName = str(reg)
        # if len(regfileName) != 0:

        # Then
        head, tail = os.path.split(regfileName)
        self.loaded_regfile = regfileName
        self.textbox_filename_regfile_xyAP.insert(tk.END, tail)

        self.RRR_xyAP = Regions.read(regfileName, format='ds9')
        print("created AP.xy regions (aka RRR_xyAP)")
        filtered_duplicates_regions = []
        for reg in self.RRR_xyAP:
            if reg not in filtered_duplicates_regions:
                filtered_duplicates_regions.append(reg)

        self.RRR_xyAP = filtered_duplicates_regions
        print("eliminated duplicated regions")

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        self.SlitTabView.load_table_from_regfile_CCD(regs_CCD=self.RRR_xyAP,
                                                     img_wcs=self.wcs)
        # if the image has a wcs, it will be used to get sky coords
        print("xyAP regions visualized on GINGA display\n   => WCS solution needed")

        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("convert xyAP regions to GINGA regions (aka RRR_xyGA)")
        # [print("first 10 xyAP obj tags ", obj.tag) for obj in self.canvas.get_objects()[:10]]

        # [print("last 10 xyAP obj tags ", obj.tag) for obj in self.canvas.get_objects()[-10:]]
        print("number of regions: ", len(self.canvas.get_objects()))
        # self.display_region_file()
        print("ds9/xy regions loaded in Ginga")
        # regfile = open(regfileName, "r")

    """
    def display_region_file(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        # color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas,color="red")
    """
    """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# DONE WITH THE FIELDS
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    """

    def regfname_handle_focus_out(self, _):
        """ to be written """

        current_text = self.regfname_entry.get()
        if current_text.strip(" ") == "":
            # self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg='grey')
            self.regfname_entry.config(bg='white')
            self.regfname_entry.insert(0, "enter pattern name")

    def regfname_handle_focus_in(self, _):
        """ to be written """

        current_text = self.regfname_entry.get()
        if current_text == "enter pattern name":

            self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg="black")

    def write_slits(self):
        """ to be written """
        # when writing a new DMD pattern, put it in the designated directory
        # don't want to clutter working dir.
        # At SOAR, this should be cleared out every night for the next observer
        created_patterns_path = path / Path("Astropy Regions/")
        pattern_name = self.regfname_entry.get()
        # check if pattern name has been proposed
        if (pattern_name.strip(" ") == "") or (pattern_name == "enter pattern name"):
            # if there is no pattern name provided, use a default based on
            # number of patterns already present
            num_patterns_thus_far = len(os.listdir(created_patterns_path))
            pattern_name = "pattern_reg{}.reg".format(num_patterns_thus_far)

        pattern_path = created_patterns_path / Path(pattern_name)

        # create astropy regions and save them after checking that there is something to save...
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas,'rectangle')
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'box')

        list_slits = list(slits)
        if len(list_slits) != 0:
            RRR = Regions([g2r(list_slits[0])])
            for i in range(1, len(list_slits)):
                RRR.append(g2r(list_slits[i]))
        RRR.write(str(pattern_path)+'.reg', overwrite=True)
        print("\nSlits written to region file\n")

    def collect_slit_shape(self):
        """
        collect selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)

        try:
            pattern_list_index = self.pattern_group_dropdown.current()
            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects = [self.canvas.get_object_by_tag(
                tag) for tag in current_pattern_tags]
        except:
            pass

        # counter = 0
        self.slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for obj in objects:
            print(obj)
          
            # force Orthonormal orientation if checkbox is set
            # This function is called if a checkbox forces the slits to be Orthonormal on the DMD. 
            # This is intended to havoid having slightly diagonal slits when the position angle of the image is not exactly 
            # oriented with the celestial coordinates
            if self.Orthonormal_ChkBox_Enabled.get() == 1:
                obj.rot_deg = 0.0
                
            ccd_x0, ccd_y0, ccd_x1, ccd_y1 = obj.get_llur()
            # first case: figures that have no extensions (i.e. points): do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1, y1 = convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1, y1] = 0
            elif self.CentroidPickup_ChkBox_Enabled.get() == 1 and obj.kind == 'point':
                x1, y1 = convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.floor(x1)), int(np.floor(y1))
                x2, y2 = convert.CCD2DMD(ccd_x1, ccd_y1)
                x2, y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))

                # dmd_corners[:][1] = corners[:][1]+500
                ####
                # x1 = round(dmd_corners[0][0])
                # y1 = round(dmd_corners[0][1])+400
                # x2 = round(dmd_corners[2][0])
                # y2 = round(dmd_corners[2][1])+400
                """
                # 3 load the slit pattern
                data_box = self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]), len(good_box[1]))
                """ paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_x):  # scanning multiple rows means each steps moves up along the y axis
                    # the indices of the y values pertinent to that x
                    iy = np.where(good_box_x == i)
                    iymin = min(iy[0])  # the smallest y index
                    iymax = max(iy[0])  # last largest y index
                    cx0 = ccd_x0 + i  # so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cy0 = ccd_y0 + good_box_y[iymin]
                    cy1 = ccd_y0 + good_box_y[iymax]
                    # get the lower value of the column at the x position,
                    x1, y1 = convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = convert.CCD2DMD(cx0, cy1)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y2+1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y2+1,x1-2:x1] = 1
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """ paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_y):  # scanning multiple rows means each steps moves up along the y axis
                    # the indices of the y values pertinent to that x
                    ix = np.where(good_box_y == i)
                    ixmin = min(ix[0])  # the smallest y index
                    ixmax = max(ix[0])  # last largest y index
                    cy0 = ccd_y0 + i  # so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cx0 = ccd_x0 + good_box_x[ixmin]
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    # get the lower value of the column at the x position,
                    x1, y1 = convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = convert.CCD2DMD(cx1, cy0)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y1,x1-2:x1] = 1
                """
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """
       #     self.slit_shape[x1:x2,y1:y2]=0
#        IP = self.PAR.IP_dict['IP_DMD']
#        [host,port] = IP.split(":")
#        DMD.initialize(address=host, port=int(port))
#        DMD._open()
#        DMD.apply_shape(self.slit_shape)

    def push_slit_shape(self):
        """
        push selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        
        # if someone forgot to remove the tracese, we do it here for safety
        self.remove_traces()
        self.collect_slit_shape()

        """# 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)

        try:

            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects =[self.canvas.get_object_by_tag(
                tag) for tag in current_pattern_tags]
        except:
            pass

        # counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            print(obj)
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()

            # first case: figures that have no extensions: do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1,y1]=0
            elif  self.CentroidPickup_ChkBox_Enabled.get() != 0 and obj.kind == 'point':
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """"""
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))

                # dmd_corners[:][1] = corners[:][1]+500
                ####
                # x1 = round(dmd_corners[0][0])
                # y1 = round(dmd_corners[0][1])+400
                # x2 = round(dmd_corners[2][0])
                # y2 = round(dmd_corners[2][1])+400
                """"""
                # 3 load the slit pattern
                data_box=self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]),len(good_box[1]))
                """""" paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion""""""
                for i in np.unique(good_box_x):  #scanning multiple rows means each steps moves up along the y axis
                    #the indices of the y values pertinent to that x
                    iy = np.where(good_box_x == i)
                    iymin = min(iy[0])   #the smallest y index
                    iymax = max(iy[0])   #last largest y index
                    cx0 = ccd_x0 + i     #so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cy0 = ccd_y0 + good_box_y[iymin]
                    cy1 = ccd_y0 + good_box_y[iymax]
                    #get the lower value of the column at the x position,
                    x1,y1 = convert.CCD2DMD(cx0,cy0)
                    x1,y1 = int(np.round(x1)), int(np.round(y1))
                    x2,y2 = convert.CCD2DMD(cx0,cy1)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y2+1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y2+1,x1-2:x1] = 1
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """""" paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion """"""
                for i in np.unique(good_box_y):  #scanning multiple rows means each steps moves up along the y axis
                    #the indices of the y values pertinent to that x
                    ix = np.where(good_box_y == i)
                    ixmin = min(ix[0])   #the smallest y index
                    ixmax = max(ix[0])   #last largest y index
                    cy0 = ccd_y0 + i     #so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cx0 = ccd_x0 + good_box_x[ixmin]
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    #get the lower value of the column at the x position,
                    x1,y1 = convert.CCD2DMD(cx0,cy0)
                    x1,y1 = int(np.round(x1)), int(np.round(y1))
                    x2,y2 = convert.CCD2DMD(cx1,cy0)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y1,x1-2:x1] = 1
                """"""
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """"""
       #     self.slit_shape[x1:x2,y1:y2]=0
#        IP = self.PAR.IP_dict['IP_DMD']
#        [host,port] = IP.split(":")
#        DMD.initialize(address=host, port=int(port))
#        DMD._open()
#        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()
        """
        
        self.push_slits()
        print("check")
                

    def push_slits(self):
        """ Actual push of the slit_shape to the DMD """
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()

    """
    def push_slits(self):
        # push selected slits to DMD pattern
        # Export all Ginga objects to Astropy region
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        # counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()

            x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            # dmd_corners[:][1] = corners[:][1]+500
            ####
            # x1 = round(dmd_corners[0][0])
            # y1 = round(dmd_corners[0][1])+400
            # x2 = round(dmd_corners[2][0])
            # y2 = round(dmd_corners[2][1])+400
        # 3 load the slit pattern
            self.slit_shape[x1:x2,y1:y2]=0
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))

#        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()

        print("check")


    def get_IP(self,device='DMD'):
        v=pd.read_csv("SAMOS_system_dev/IP_addresses_default.csv",header=None)
        if device == 'DMD':
            return(v[2][1])

        IPs = Config.load_IP_user(self)
        # print(IPs)
    """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#     def open_Astrometry(self):
#         btn = tk.Button(master,
#              text ="Click to open a new window",
#              command = openNewWindow)
#         btn.pack(pady = 10)ƒ
#         return self.Astrometry(master)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def set_filter(self):
        """ to be written """
        print(self.FW_filter.get())
        print('moving to filter:', self.FW_filter.get())
#        self.Current_Filter.set(self.FW_filter.get())
        filter = self.FW_filter.get()
        main_fits_header.set_param("filter", filter)
        filter_pos_ind = list(self.filter_data["Filter"]).index(filter)
        filter_pos = list(self.filter_data["Position"])[filter_pos_ind]
        main_fits_header.set_param("filtpos", filter_pos)
        print(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
        t = PCM.move_filter_wheel(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_on_color)
        self.canvas_Indicator.update()

        # self.Echo_String.set(t)
        print(t)

        self.Label_Current_Filter.delete("1.0", "end")
        self.Label_Current_Filter.insert(tk.END, self.FW_filter.get())

        self.extra_header_params += 1
        entry_string = param_entry_format.format(self.extra_header_params, 'String', 'FILTER',
                                                 filter, 'Selected filter')
        self.header_entry_string += entry_string

 
    def get_widget(self):
        """ to be written """
        return self.root

    def set_drawparams(self, evt):
        """ to be written """
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  # 'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def save_canvas(self):
        """ to be written """
        regs = ap_region.export_regions_canvas(self.canvas, logger=self.logger)
        # self.canvas.save_all_objects()

    def clear_canvas(self):
        """ to be written """
        # CM.CompoundMixin.delete_all_objects(self.canvas)#,redraw=True)
        obj_tags = list(self.canvas.tags.keys())
        # print(obj_tags)
        for tag in obj_tags:
            if self.SlitTabView is not None:
                if tag in self.SlitTabView.slit_obj_tags:
                    obj_ind = self.SlitTabView.slit_obj_tags.index(tag)
                    # self.SlitTabView.stab.delete_row(int(tag.strip("@")))
                    del self.SlitTabView.slit_obj_tags[obj_ind]
                self.SlitTabView.slitDF = self.SlitTabView.slitDF[0:0]

                # if not self.slit_window.winfo_exists():
                #    self.SlitTabView.recover_window()
        self.canvas.delete_all_objects(redraw=True)


   
    def update_PotN(self):
        """
        Updates the parameters of the night variables and files for logging the observations
        """
        import json
#       How do we capture a parameter in another class/form?
        self.PAR.PotN['Telescope'] = self.ConfP.Telescope.get() #ConfigPage.Telescope.get()
        self.PAR.PotN['Program ID'] = self.program_var.get() 
        self.PAR.PotN['Proposal Title'] = self.ConfP.Proposal_Title.get()#ConfigPage.Telescope.get()
        self.PAR.PotN['Principal Investigator'] = self.ConfP.Principal_Investigator.get() #ConfigPage.Telescope.get()
        # For the parameters redefinied here it is easy: capture them...
        self.PAR.PotN['Observer'] = self.names_var.get()
        self.PAR.PotN['Telescope Operator'] = self.TO_var.get()
        self.PAR.PotN['Object Name'] = self.ObjectName.get()
        self.PAR.PotN['Comment'] = self.Comment.get()
        self.PAR.PotN['Bias Comment'] = self.BiasComment.get()
        self.PAR.PotN['Dark Comment'] = self.DarkComment.get()
        self.PAR.PotN['Flat Comment'] = self.FlatComment.get()
        self.PAR.PotN['Buffer Comment'] = self.FlatComment.get()
        self.PAR.PotN['Base Filename'] = self.out_fname.get()
        
        # ..open the json file and read all...
        PotN_file = os.path.join(local_dir,'SAMOS_system_dev','Parameters_of_the_night.txt')
        with open(PotN_file, "r") as jsonFile:
            data = json.load(jsonFile)
        #... change what has to be changed...
        data["Observer"] = self.PAR.PotN['Observer'] 
        data["Program ID"] = self.PAR.PotN['Program ID'] 
        data["Proposal Title"] = self.PAR.PotN['Proposal Title'] 
        data["Principal Investigator"] = self.PAR.PotN['Principal Investigator'] 
        data["Telescope Operator"] = self.PAR.PotN['Telescope Operator'] 
        data["Object Name"] = self.PAR.PotN['Object Name'] 
        data["Comment"] = self.PAR.PotN['Comment'] 
        data["Bias Comment"] = self.PAR.PotN['Bias Comment'] 
        data["Dark Comment"] = self.PAR.PotN['Dark Comment'] 
        data["Flat Comment"] = self.PAR.PotN['Flat Comment'] 
        data["Buffer Comment"] = self.PAR.PotN['Buffer Comment'] 
        data["Base Filename"] = self.PAR.PotN['Base Filename'] 
        # ... write the json file
        with open(PotN_file, "w") as jsonFile:
            json.dump(data, jsonFile)


    def Display(self, imagefile):
        """ to be written """
#        image = load_data(fits_image_converted, logger=self.logger)

        # AstroImage object of ginga.AstroImage module
        self.AstroImage = load_data(imagefile, logger=self.logger)

        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)

    def reset_progress_bars(self):

        self.exp_progbar["value"] = 0
        self.var_perc_exp_done.set(0)
        self.exp_progbar_style.configure('text.Horizontal.TProgressbar',
                                         text='Expose {:g} %'.format(self.var_perc_exp_done.get()))
        self.readout_progbar["value"] = 0
        self.var_perc_read_done.set(0)
        self.readout_progbar_style.configure('text.Horizontal.RProgressbar',
                                             text='Readout {:g} %'.format(self.var_perc_read_done.get()))

    def load_existing_file(self):
        """ to be written """
        FITSfiledir = os.path.join(self.PAR.QL_images)
        self.last_fits_file_dialog = filedialog.askopenfilename(initialdir=self.fits_dir,                                                          title="Select a File",
                                                                 filetypes=(("fits files",
                                                                             "*.fits"),
                                                                            ("all files",
                                                                             "*.*")))
        self.fits_image_ql  = self.last_fits_file_dialog

        #self.fullpath_FITSfilename = os.path.join(
        #    self.fits_dir, self.loaded_fits_file)
        # './fits_image/newimage_ql.fits'
        self.AstroImage = load_data(
            self.last_fits_file_dialog, logger=self.logger)
        # AstroImage object of ginga.AstroImage module

        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)
#        self.root.title(self.fullpath_FITSfilename)

        #return self.filename_regfile_RADEC

    def send_RADEC_to_SOAR(self):
        pass

    def Query_Survey(self):
        """ to be written """
        from astroquery.hips2fits import hips2fits
        Survey = self.Survey_selected.get()

        if Survey == "SkyMapper":
            try:
                self.SkyMapper_query()
            except:
                print("\n Sky mapper image server is down \n")
            return

        if Survey == "SDSS":
            self.SDSS_query()
            return
            
          

        else:       # SIMBAD database
            if Survey == "PanSTARRS/DR1/":
                Survey = Survey+self.string_Filter.get()
                print("\n Quering PanSTARRS/DR1")
            """    
            print("Survey selected: ",Survey,'\n')
            coord = SkyCoord(self.string_RA.get()+'  ' +
                         self.string_DEC.get(), unit=(u.deg, u.deg), frame='fk5')
            # coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5')

            query_results = Simbad.query_region(coord)
            
            if query_results is None:
                print('\n no objects found at that RA,Dec; try again elsewhere\n')
                ra_center = self.string_RA.get()
                dec_center = self.string_DEC.get()
            else:
                print('\n SIMBAD OBJECTS: \n',query_results)
            """
        # =============================================================================
        # Download an image centered on the coordinates passed by the main window
        #
        # =============================================================================
            # object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
            #object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'],
            #                         #                                 unit=(u.deg, u.deg), frame='icrs')
            #                         unit=(u.hourangle, u.deg), frame='icrs')
            c = SkyCoord(self.string_RA.get(),
                         self.string_DEC.get(), unit=(u.deg, u.deg))
     # FROM      https://astroquery.readthedocs.io/en/latest/hips2fits/hips2fits.html
            """
             query_params = {
                 'hips': self.Survey_selected.get(), #'DSS', #
                 # 'object': object_main_id,
                 # Download an image centef on the first object in the results
                 # 'ra': object_coords[0].ra.value,
                 # 'dec': object_coords[0].dec.value,
                 'ra': c.ra.value,
                 'dec': c.dec.value,
                 'fov': (3.5 * u.arcmin).to(u.deg).value,
                 'width': 1056#528,
                 'height': 1032#516
                 }
            url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'
            hdul = fits.open(url)
            """
            query_params = {"NAXIS1": 1056,
                            "NAXIS2": 1032,
                            "WCSAXES": 2,
                            "CRPIX1": 528,
                            "CRPIX2": 516,
                            "CDELT1": 0.1875/3600,
                            "CDELT2": 0.1875/3600,
                            "CUNIT1": "deg",
                            "CUNIT2": "deg",
                            "CTYPE1": "RA---TAN",
                            "CTYPE2": "DEC--TAN",
                            "CRVAL1": c.ra.value,
                            "CRVAL2": c.dec.value}
            query_wcs = wcs.WCS(query_params)
            hips = self.Survey_selected.get()
            hdul = hips2fits.query_with_wcs(hips=hips,
                                            wcs=query_wcs,
                                            get_query_payload=False,
                                            format='fits')
    
            # Downloading http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=DSS&object=%5BT64%5D++7&ra=243.58457533549102&dec=-19.113364937196987&fov=0.03333333333333333&width=500&height=500
            # |==============================================================| 504k/504k (100.00%)         0s
            hdul.info()
            # Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
            # No.    Name      Ver    Type      Cards   Dimensions   Format
            #  0  PRIMARY       1 PrimaryHDU      22   (500, 500)   int16
            print(hdul[0].header)
            
            #to make this robust, we neeed to add a couple of parameters to the FITS header
            #(something like this may be needed by the other surveys...)
            hdul[0].header["FILENAME"] = Survey + "_" + self.string_RA.get() +"_" + self.string_DEC.get() + ".fits"

            self.image = hdul
            hdul.writeto(os.path.join(dir_Astrometry,
                         'newtable.fits'), overwrite=True)
    
            img = AstroImage()
            Posx = self.string_RA.get()
            Posy = self.string_DEC.get()
            filt = self.string_Filter.get()
            data = hdul[0].data[:, ::-1]
            try:
                image_data = Image.fromarray(data)
            except:
                print("\n  No image returned, exiting \n")
                return
            # img_res = image_data.resize(size=(1032,1056))
            img_res = image_data
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec
    
    #            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
     #           hdu.writeto(rebinned_filename,overwrite=True)
     
            self.button_find_stars['state'] = 'active'

            img.load_hdu(self.hdu_res)
            print('\n', self.hdu_res.header)
            self.fitsimage.set_image(img)
            self.AstroImage = img
    #        self.fullpath_FITSfilename = filepath.name
            hdul.close()
            self.fits_image_ql = os.path.join(
                self.PAR.QL_images, "newimage_ql.fits")
            fits.writeto(self.fits_image_ql, self.hdu_res.data,
                         header=self.hdu_res.header, overwrite=True)

        # self.root.title(filepath)

    """
    Inject image from SkyMapper to create a WCS solution using twirl
    """
    def SkyMapper_query(self):
        """ get image from SkyMapper """

        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, filt)
        # filepath = skymapper_interrogate_VOTABLE(Posx, Posy, filt)
        with fits.open(filepath.name) as hdu_in:
            #            img.load_hdu(hdu_in[0])
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(1032, 1056))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec

            output_header = copy.deepcopy(hdu_in[0].header)
            main_fits_header.add_astrometric_fits_keywords(self.hdu_res.header)
#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)
            output_header['RA'] = ra
            output_header['DEC'] = dec
            output_header['NAXIS1'] = float(1056)
            output_header['NAXIS2'] = float(1032)
            output_header['CRVAL1'] = float(ra)
            output_header['CRVAL2'] = float(dec)
            output_header['CRPIX1'] = float(528)
            output_header['CRPIX2'] = float(516)
            
            self.wcs =wcs.WCS(output_header)
            self.wcs_exist = True        
            
            img.load_hdu(self.hdu_res)

            self.fitsimage.set_image(img)
            self.AstroImage = img
            self.fullpath_FITSfilename = filepath.name
        hdu_in.close()
        
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, self.hdu_res.data,
##                     header=self.hdu_res.header, overwrite=True)
                     header=output_header, overwrite=True)
        self.Display(self.fits_image_ql)
        self.button_find_stars['state'] = 'active'
        self.wcs_exist = True
        
    def SDSS_query(self):
        """ get image from SDSS 
            Follow https://github.com/behrouzz/sdss
        """

#        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        
        from astropy import units as u
        from astropy import coordinates as coords
        from astroquery.sdss import SDSS

        pos = coords.SkyCoord(Posx,Posy, unit=(u.deg, u.deg))
        #pos = coords.SkyCoord(RA_HMS +' ' + DEG_HMS,frame='icrs')
        #xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)
        # we search a large area around the target position
        xid = SDSS.query_region(pos, radius='150 arcsec', spectro=True)
        print(xid)
        if xid is None:
            #messagebox.showinfo(title='INFO', message='Not in SDSS')
            print("\n\n\n**** FIELD NOT IN SDSS *****\n\n\n")
            return
        else:
            self.SDSS_stars = np.transpose([xid['ra'],xid['dec']])
            
        
        im = SDSS.get_images(matches=xid, band=filt)
        hdu_0 = im[0]
        data = hdu_0[0].data
        header = hdu_0[0].header
        
        #or pick up the best tile?
    
        
        #fits.writeto(os.path.join(cwd,'input_file.fits'), data, header, overwrite=True)

        from scipy import ndimage
        data_rotated = ndimage.rotate(data, 270, reshape=True)

        
        header_rotated = copy.deepcopy(header)
        tmp = header['NAXIS1'] ; header_rotated['NAXIS2'] = tmp
        tmp = header['NAXIS2'] ; header_rotated['NAXIS1'] = tmp
        tmp = header['CRPIX1'] ; header_rotated['CRPIX2'] = tmp
        tmp = header['CRPIX2'] ; header_rotated['CRPIX1'] = tmp
        tmp = header['CD1_1'] ; header_rotated['CD1_2'] = tmp
        tmp = header['CD1_2'] ; header_rotated['CD1_1'] = -tmp
        tmp = header['CD2_1'] ; header_rotated['CD2_2'] = tmp
        tmp = header['CD2_2'] ; header_rotated['CD2_1'] = -tmp
        
#        fits.writeto(os.path.join(cwd,'output_file.fits'), data_rotated, header_rotated, overwrite=True)
#
        # Resize image
        SDSS_NaturalScale = 0.396127 # arcsec/pix from https://skyserver.sdss.org/dr12/en/tools/chart/chartinfo.aspx
        SAMOS_SISIScale = 0.1875 #arcesc/pix, from 1/6" * 1.125
        FoV_SAMOS_X = 1032 * SAMOS_SISIScale #arcsec
        FoV_SAMOS_Y = 1056 * SAMOS_SISIScale #arcsec
        FoV_SDSS_Xpix = np.round(FoV_SAMOS_X/SDSS_NaturalScale)  # 488
        FoV_SDSS_Ypix = np.round(FoV_SAMOS_Y/SDSS_NaturalScale)  # 500

        #get target xy coordinatex on      
        from astropy.wcs import WCS
        w = WCS(header_rotated)
        xc, yc = np.round(w.world_to_pixel(pos))       
        data_rotated_framed  = np.zeros( (3048,2489) )
        pedestal = 500
        data_rotated_framed[pedestal:pedestal+2048, pedestal:pedestal+1489] = data_rotated

        #SDSS_cutout
        #SDSS_cutout = data_rotated[ int(xc-FoV_SDSS_Xpix/2) : int(xc+FoV_SDSS_Xpix/2),  
        #                            int(yc-FoV_SDSS_Ypix/2) : int(yc+FoV_SDSS_Ypix/2) ]
        SDSS_cutout = data_rotated_framed[ pedestal+int(yc-FoV_SDSS_Ypix/2) : pedestal+int(yc+FoV_SDSS_Ypix/2),  
                                            pedestal+int(xc-FoV_SDSS_Xpix/2) : pedestal+int(xc+FoV_SDSS_Xpix/2) ]
        
#       with fits.open(fits_file) as hdu_in:
            #            img.load_hdu(hdu_in[0])
#            data = hdu_in[0].data
        image_data = Image.fromarray(SDSS_cutout)
        img_res = image_data.resize(size=(1032, 1056))
        self.hdu_res = fits.PrimaryHDU(img_res)
        
        # ra, dec in degrees
        ra = Posx
        dec = Posy
        self.hdu_res.header['RA'] = ra
        self.hdu_res.header['DEC'] = dec
        
        img.load_hdu(self.hdu_res)

        self.fitsimage.set_image(img)
        self.AstroImage = img
        #self.fullpath_FITSfilename = os.path.join(cwd,fits_file)#filepath.name
        #hdu_in.close()
        self.button_find_stars['state'] = 'active'
        
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, self.hdu_res.data,
                     header=self.hdu_res.header, overwrite=True)     
        
    def twirl_Astrometry(self):
        """ to be written """

        self.wcs = None
        self.Display(self.fits_image_ql)
        # self.load_file()   #for ging

        hdu_Main = fits.open(self.fits_image_ql)  # for this function to work
        hdu = hdu_Main[0]
        header = hdu.header
        data = hdu.data
        hdu_Main.close()
        ra, dec = header["RA"], header["DEC"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        shape = data.shape
        pixel = 0.18 * u.arcsec
        fov = np.max(shape)*pixel.to(u.deg).value

        # Let's find some stars and display the image

        self.canvas.delete_all_objects(redraw=True)
        #check first if it exist, as we may have not yet queried SDSS        
        try:  
            if self.SDSS_stars is None:  #if it exist but is none, we just check the current image
                stars = twirl.find_peaks(data)[0:self.nrofstars.get()]
            else: #if it exist, we are coming from SDSS and therefore we use the SDSS stars
                import copy
                stars = copy.deepcopy(self.SDSS_stars)
                SDSS_stars = None  #and immediately delete them so we are free for the next searh
        except:  #if self.SDSS has never been created, we go to the basic search
             stars = twirl.find_peaks(data)[0:self.nrofstars.get()]

#        plt.figure(figsize=(8,8))
        med = np.median(data)
#        plt.imshow(data, cmap="Greys_r", vmax=np.std(data)*5 + med, vmin=med)
#        plt.plot(*stars.T, "o", fillstyle="none", c="w", ms=12)

        from regions import PixCoord, CirclePixelRegion
#        xs=stars[0,0]
#        ys=stars[0,1]
#        center_pix = PixCoord(x=xs, y=ys)
        radius_pix = 42

#        this_region = CirclePixelRegion(center_pix, radius_pix)

        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                   for x, y in stars]  # [(1, 2), (3, 4)]]
        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
        # add_region(self.canvas, obj, tag="twirlstars", draw=True)
            self.canvas.add(obj)

        # we can now compute the WCS
        gaias = twirl.gaia_radecs(center, fov, limit=self.nrofstars.get())

        self.wcs = twirl.compute_wcs(stars, gaias)

        global WCS_global   #used for HTS
        WCS_global = self.wcs

        # Lets check the WCS solution

#        plt.figure(figsize=(8,8))
        radius_pix = 25
        gaia_pixel = np.array(SkyCoord(gaias, unit="deg").to_pixel(self.wcs)).T
        regions_gaia = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                        for x, y in gaia_pixel]  # [(1, 2), (3, 4)]]
        regs_gaia = Regions(regions_gaia)
        for reg in regs_gaia:
            obj = r2g(reg)
            obj.color = "red"
        # add_region(self.canvas, obj, tag="twirlstars", redraw=True)
            self.canvas.add(obj)

        print(self.wcs)
        
        if self.wcs is None:
            self.wcs_exist = False
            print("\n WCS solution not found, returning\n")
            return
        else:
            self.wcs_exist = True            
            print("\n WCS solution found!\n")
            
        hdu_wcs = self.wcs.to_fits()

        if self.loaded_regfile is not None:
            hdu_wcs[0].header.set(
                "dmdmap", os.path.split(self.loaded_regfile)[1])

        hdu_wcs[0].data = data  # add data to fits file
        self.wcs_filename = os.path.join(
            ".", "SAMOS_Astrometry_dev", "WCS_"+ra+"_"+dec+".fits")
        hdu_wcs[0].writeto(self.wcs_filename, overwrite=True)

        self.Display(self.wcs_filename)
        self.button_find_stars['state'] = 'active'
        
        self.wcs_exist = True
        #
        # > to read:
        # hdu = fits_open(self.wcs_filename)
        # hdr = hdu[0].header
        # import astropy.wcs as apwcs
        # wcs = apwcs.WCS(hdu[('sci',1)].header)
        

    def find_stars(self):
        """ to be written """

        self.Display(self.fits_image_ql)
        self.set_slit_drawtype()
        # self.load_file()   #for ging

        hdu = fits.open(self.fits_image_ql)  # for this function to work
        
        header = hdu[0].header
        data = hdu[0].data
        hdu.close()
        ra, dec = header["RA"], header["DEC"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        shape = data.shape
        pixel = 0.18 * u.arcsec
        fov = np.max(shape)*pixel.to(u.deg).value

        # Let's find some stars and display the image

        self.canvas.delete_all_objects(redraw=True)
        threshold = 0.1
        stars = twirl.find_peaks(data, threshold)[0:self.nrofstars.get()]

#        plt.figure(figsize=(8,8))
        med = np.median(data)
#        plt.imshow(data, cmap="Greys_r", vmax=np.std(data)*5 + med, vmin=med)
#        plt.plot(*stars.T, "o", fillstyle="none", c="w", ms=12)

        from regions import PixCoord, CirclePixelRegion
#        xs=stars[0,0]
#        ys=stars[0,1]
#        center_pix = PixCoord(x=xs, y=ys)
        radius_pix = 20

#        this_region = CirclePixelRegion(center_pix, radius_pix)

#        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
        regions = [RectanglePixelRegion(center=PixCoord(x=round(x), y=round(y)),
                           width=self.slit_w.get(), height=self.slit_l.get(),
                           angle=0*u.deg)
                   for x, y in stars]  # [(1, 2), (3, 4)]]

        if self.SlitTabView is None:
            self.initialize_slit_table()

        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
        # add_region(self.canvas, obj, tag="twirlstars", draw=True)
            self.canvas.add(obj)

            obj.pickable = True
            obj.add_callback('pick-up', self.pick_cb, 'up')
            # obj.add_callback('pick-down', self.pick_cb, 'down')
            obj.add_callback('edited', self.edit_cb)

            self.SlitTabView.add_slit_obj(reg, obj.tag, self.fitsimage)
    
        self.draw_slits()
        pass


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#     def start_the_loop(self):
#         while self.stop_it == 0:
#             threading.Timer(1.0, self.load_manager_last_file).start()
#
#     def load_manager_last_file(self):
#         FITSfiledir = './fits_image/'
#         self.fullpath_FITSfilename = FITSfiledir + (os.listdir(FITSfiledir))[0]
#         print(self.fullpath_FITSfilename)
#
#     def stop_the_loop(self):
#         self.stop_it == 1
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         image = load_data(self.fullpath_FITSfilename, logger=self.logger)
#         self.fitsimage.set_image(image)
#         self.root.title(self.fullpath_FITSfilename)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def load_file(self):
        """ to be written """
        self.AstroImage = load_data(
            self.fullpath_FITSfilename, logger=self.logger)
        self.canvas.set_image(self.AstroImage)
        self.root.title(self.fullpath_FITSfilename)

    def open_file(self):
        """ to be written """
        filename = filedialog.askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        # self.load_file()
        self.AstroImage = load_data(filename, logger=self.logger)
        self.fitsimage.set_image(self.AstroImage)

        if self.AstroImage.wcs.wcs.has_celestial:
            self.wcs = self.AstroImage.wcs.wcs

    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'point')
        print(list(points))

        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'point')
        list_point = list(points)
        CM.CompoundMixin.delete_objects(self.canvas, list_point)
        self.canvas.objects  # check that the points are gone

        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas, ['point', 'circle',
                                                                     'rectangle', 'polygon',
                                                                     'triangle', 'righttriangle',
                                                                     'ellipse', 'square'])
        list_points = list(points)
        CM.CompoundMixin.delete_objects(self.canvas, list_points)
        self.canvas.objects  # check that the points are gone

        """
        # Find approximate bright peaks in a sub-area
        from ginga.util import iqcalc
        iq = iqcalc.IQCalc()
    
        r = self.canvas.objects[0]
        img_data = self.AstroImage.get_data()
        data_box = self.AstroImage.cutout_shape(r)
        
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        px,py=round(peaks[0][0]+r.x1),round(peaks[0][1]+r.y2)
        print(px,py)   #image coordinates
        print(img_data[px,py]) #actual counts
     
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)       
        # how many did we find with standard thresholding, etc.
        # see params for find_bright_peaks() and evaluate_peaks() for details
        print(len(objs))
        # example of what is returned
        o1 = objs[0]
        print(o1)
           
        # pixel coords are for cutout, so add back in origin of cutout
        #  to get full data coords RA, DEC of first object
        x1, y1, x2, y2 = r.get_llur()
        self.img.pixtoradec(x1+o1.objx, y1+o1.objy)
          
        # Draw circles around all objects
        Circle = self.canvas.get_draw_class('circle')
        for obj in objs:
            x, y = x1+obj.objx, y1+obj.objy
            if r.contains(x, y):
                self.canvas.add(Circle(x, y, radius=10, color='yellow'))
        
        # set pan and zoom to center
        self.fitsimage.set_pan((x1+x2)/2, (y1+y2)/2)
        self.fitsimage.scale_to(0.75, 0.75)
        
        r_all = self.canvas.objects[:]
        print(r_all)
        
        
        EXERCISE COMPOUNDMIXING CLASS
        r_all is a CompountMixing object, see class ginga.canvas.CompoundMixin.CompoundMixin
         https://ginga.readthedocs.io/en/stable/_modules/ginga/canvas/CompoundMixin.html#CompoundMixin.get_objects_by_kinds        
              
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        print(list(points))
        
        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        list_point=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_point)
        self.canvas.objects   #check that the points are gone
           
        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas,['point','circle',
                                                                    'rectangle', 'polygon', 
                                                                    'triangle', 'righttriangle', 
                                                                    'ellipse', 'square'])
        list_points=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_points)
        self.canvas.objects   #check that the points are gone
    
        # drawing an object can be done rather easily
        # first take an object fromt the list and change something
        objects=CM.CompoundMixin.get_objects(self.canvas)
        o0=objects[0]
        o0.y1=40
        o0.height=100
        o0.width=70
        o0.color='lightblue'
        CM.CompoundMixin.draw(self.canvas,self.canvas.viewer)
        
        END OF THE COMPOUNDMIXING EXCERCISE
        # ===#===#===#===#===#===#===#===#===#===#===#====        

        # region = 'fk5;circle(290.96388,14.019167,843.31194")'
        # astropy_region = pyregion.parse(region)
        # astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])
        # print(astropy_region)
         
        # List all regions that we have created
        # n_objects = len(self.canvas.objects)
        # for i_obj in range(n_objects):
        #   astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj])
        #   print(astropy_region) 
           
        # create a list of astropy regions, so we export a .reg file
        # first put the initial region in square brackets, argument of Regions to initiate the list
        RRR=Regions([ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])])
        # then append to the list adding all other regions
        for i_obj in range(1,len(self.canvas.objects)):
           RRR.append(ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj]))
           print(RRR) 
 
        # write the regions to file
        # this does not seem to work...
        RRR.write('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9',overwrite=True)
       
        # reading back the ds9 regions in ginga
        pyregions = Regions.read('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9')
        n_regions = len(pyregions)
        for i in range(n_regions):
            pyregion = pyregions[i]
            pyregion.width=7
            pyregion.width=3
            ap_region.add_region(self.canvas,pyregion)

        print("yay!")            
        
        # Export all Ginga objects to Astropy region
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        counter = 0
        for obj in objects:
            if counter == 0:
                astropy_regions=[g2r(obj)]  #here we create the first astropy region and the Regions list []
            else:
                astropy_regions.append(g2r(obj)) #will with the other slits 
            counter += 1
        regs = Regions(astropy_regions)     #convert to astropy-Regions
        regs.write('my_regions.reg',overwrite=True)   #write to file
        
        # 2, Extract the slits and convert pixel->DMD values
        
        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        
        # create initial DMD slit mask
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        
        regions = Regions.read('my_regions.reg')


        for i in range(len(regions)):
            reg = regions[i]
            corners = reg.corners
            # convert CCD corners to DMD corners here
            # TBD
            # dmd_corners=[] 
            # for j in range(len(corners)):
            x1,y1 = convert.CCD2DMD(corners[0][0], corners[0][1])
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(corners[2][0], corners[2][1])
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            # dmd_corners[:][1] = corners[:][1]+500
            ####   
            # x1 = round(dmd_corners[0][0])
            # y1 = round(dmd_corners[0][1])+400
            # x2 = round(dmd_corners[2][0])
            # y2 = round(dmd_corners[2][1])+400
        # 3 load the slit pattern   
            self.slit_shape[x1:x2,y1:y2]=0
        DMD.apply_shape(self.slit_shape)  
        # DMD.apply_invert()   

        
        print("check")
        """

    def cursor_cb(self, viewer, button, data_x, data_y):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            value = int(round(value, 0))
        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        dmd_x, dmd_y = convert.CCD2DMD(fits_x, fits_y)

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
            ra_deg, dec_deg = image.pixtoradec(fits_x, fits_y)
            self.ra_center, self.dec_center = image.pixtoradec(528, 516,
                                                               format='str', coords='fits')

        except Exception as e:
            # self.logger.warning("Bad coordinate conversion: %s" % (
            #    str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'
            ra_deg = 'BAD WCS'
            dec_deg = 'BAD WCS'
        coords_text = "RA: %s  DEC: %s \n" % (ra_txt, dec_txt)
#        coords_text_DEG = "RA: %s  DEC: %s \n"%(str(ra_deg), str(dec_deg))
        coords_text_DEG = "RA: %.9s DEC %.9s\n" % (str(ra_deg), str(dec_deg))
#        dmd_text = "DMD_X: %.2f  DMD_Y: %.2f \n"%(dmd_x, dmd_y)
#        dmd_text = "DMD_X: %i  DMD_Y: %i \n"%(np.round(dmd_x), round(dmd_y))
        dmd_text = "DMD_X: %i  DMD_Y: %i \n" % (
            np.floor(dmd_x), np.floor(dmd_y))
        text = "X: %i  Y: %i  Value: %s" % (
            np.floor(fits_x), np.floor(fits_y), value)

        text = coords_text + coords_text_DEG + dmd_text + text
        self.readout.config(text=text)

    def MASTER_quit(self):
        #self.ConfP.destroy()
        self.destroy()
        return True

######

    def set_slit_drawtype(self):
        self.wdrawtype.delete(0, tk.END)
        mode = self.Draw_Edit_Pick_Checked.set("draw")
        self.set_mode_cb()
        if self.CentroidPickup_ChkBox_Enabled.get() == 1:
            self.wdrawtype.insert(0, "point")
        else:
            self.wdrawtype.insert(0, "box")
#            self.Draw_Edit_Pick_Checked.set("None")
        print("drawtype changed to ", self.wdrawtype.get())
#        parameters = []
#        parameters['color'] = 'red'
        self.canvas.set_drawtype(self.wdrawtype.get())#,**parameters)
            

    def set_mode_cb(self):
        """ to be written """
        mode = self.Draw_Edit_Pick_Checked.get()
        
        #we turn off here the SourcePickup_ChkBox 
        if mode != "draw":
            self.CentroidPickup_ChkBox_Enabled.set(0)
            
#        self.logger.info("canvas mode changed (%s) %s" % (mode))
        self.logger.info("canvas mode changed (%s)" % (mode))
        try: #all object painted red, should not be true for the traces
            for obj in self.canvas.objects:
                obj.color = 'red'
        except:
            pass

        self.canvas.set_draw_mode(mode)

    def draw_cb(self, canvas, tag):
        """ to be written """
        obj = canvas.get_object_by_tag(tag)
        
#        obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.pickable = True
        obj.add_callback('pick-key', self.pick_cb, 'key')

        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        # obj.add_callback('pick-hover', self.pick_cb, 'hover')
        # obj.add_callback('pick-enter', self.pick_cb, 'enter')
        # obj.add_callback('pick-leave', self.pick_cb, 'leave')
        
        obj.add_callback('edited', self.edit_cb)
        # obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        kind = self.wdrawtype.get()
        print("kind: ", kind)
        
        # =============
        #CASE A)
        #this case should never run. 
        #If we have enabled the slit pickup mode, the ob.kind is "point" 
        if kind == "box" and self.CentroidPickup_ChkBox_Enabled.get() == 1:
            if self.SlitTabView is None:
                self.initialize_slit_table()
            try:
                kind == "box"
                # the ginga object, a box, is converted to an astropy region
                r = g2r(obj)

            except ValueError:
                # if you just click instead of drawing a box, call the slit_handler
                print("box")
                obj.kind = "box"

            new_obj = self.slit_handler(obj)
            r = g2r(new_obj)
            tag = new_obj.tag
            obj = new_obj

            self.SlitTabView.add_slit_obj(r, tag, self.fitsimage)
            # self.SlitTabView.slit_obj_tags.append(tag)

        # =============
        #CASE B)
        # Pick up mode. obj.kind should always be point.
        elif self.CentroidPickup_ChkBox_Enabled.get() == 1 and kind == 'point':  # or kind == 'box':

            #this case requires more sophisticated operations, hence a dedicated function            
            self.slit_handler(obj)

        # =============
        # CASE C)
        # a box is drawn but centroid is not searched, just drawn... 
        elif kind == "box" and self.CentroidPickup_ChkBox_Enabled.get() == 0:
            
            #if table does not exist, create it (this should not happen as table previously created)
            if self.SlitTabView is None:
                self.initialize_slit_table()
            
            # the ginga object, a box, is converted to an astropy region
            r = g2r(obj)
            
            # the astropy object is added to the table
            self.SlitTabView.add_slit_obj(r, tag, self.fitsimage)
            # self.SlitTabView.slit_obj_tags.append(tag)

            
            

    def slit_handler(self, obj):
        """ to be written """
        print('ready to associate a slit to ')
        print(obj.kind)
        img_data = self.AstroImage.get_data()

        #we are still a bit paranoid....
        if obj.kind == 'point':
            
            # Search centroid: Start creating box
            x_c = obj.points[0][0]-1  # really needed?
            y_c = obj.points[0][1]-1
            
            # create area to search, use astropy and convert to ginga (historic reasons...)
            r = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)),
                                     width=40, height=40,
                                     angle=0*u.deg)
            # and we convert it to ginga.
            obj = r2g(r)
            # Note: r as an Astropy region is a RECTANGLE
            #      obj is a Ginga region type BOX
            # obj = r2g(r)
            
            # the Ginga Box object can be added to the canvas
            self.canvas.add(obj)
        
        # time to do the math; collect the pixels in the Ginga box
        data_box = self.AstroImage.cutout_shape(obj)

        # we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.canvas, obj)

  #      obj = self.canvas.get_draw_class('rectangle')
  #      obj(x1=x_c-20,y1=y_c-20,x2=x_c+20,y2=y_c+20,
  #                      width=100,
  #                      height=30,
  #                      angle = 0*u.deg)
  #      data_box = self.img.cutout_shape(obj)
       
        # find the peak within the Ginga box
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        x1 = obj.x-obj.xradius
        y1 = obj.y-obj.yradius
        px, py = round(peaks[0][0]+x1), round(peaks[0][1]+y1)
        print('peak found at: ', px, py)  # image coordinates
        print('with counts: ', img_data[px, py])  # actual counts
        
        # GINGA MAGIC!!! 
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)
        # from ginga.readthedocs.io
        """
        Each result contains the following keys:

           * ``objx``, ``objy``: Fitted centroid from :meth:`get_fwhm`.
           * ``pos``: A measure of distance from the center of the image.
           * ``oid_x``, ``oid_y``: Center-of-mass centroid from :meth:`centroid`.
           * ``fwhm_x``, ``fwhm_y``: Fitted FWHM from :meth:`get_fwhm`.
           * ``fwhm``: Overall measure of fwhm as a single value.
           * ``fwhm_radius``: Input FWHM radius.
           * ``brightness``: Average peak value based on :meth:`get_fwhm` fits.
           * ``elipse``: A measure of ellipticity.
           * ``x``, ``y``: Input indices of the peak.
           * ``skylevel``: Sky level estimated from median of data array and
             ``skylevel_magnification`` and ``skylevel_offset`` attributes.
           * ``background``: Median of the input array.
           * ``ensquared_energy_fn``: Function of ensquared energy for different pixel radii.
           * ``encircled_energy_fn``: Function of encircled energy for different pixel radii.

        """
        print('full evaluation: ', objs)
        print('fitted centroid: ', objs[0].objx, objs[0].objy)
        print('FWHM: ', objs[0].fwhm)
        print('peak value: ', objs[0].brightness)
        print('sky level: ', objs[0].skylevel)
        print('median of area: ', objs[0].background)
        print("the four vertex of the rectangle are, in pixel coord:")
        x1, y1, x2, y2 = obj.get_llur()
        print(x1, y1, x2, y2)
        print("the RADEC of the fitted centroid are, in decimal degrees:")
        print(self.AstroImage.pixtoradec(objs[0].objx, objs[0].objy))
#        slit_w=3
#        slit_l=9
#        self.canvas.add(slit_box(x1=objs[0].objx+x1-slit_w,y1=objs[0].objy+y1-slit_h,x2=objs[0].objx+x1+slit_w,y2=objs[0].objy+y1+slit_h,
#                        width=100,
#                        height=30,
#                        angle = 0*u.deg))

        #enogh with astronomy;
        # having found the centroid, we need to draw the slit
        slit_box = self.canvas.get_draw_class('box')
        xradius = self.slit_w.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        yradius = self.slit_l.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        new_slit_tag = self.canvas.add(slit_box(x=objs[0].objx+x1,
                                                y=objs[0].objy+y1,
                                                xradius=xradius,
                                                yradius=yradius,
                                                color='red',
                                                alpha=0.8,
                                                fill=False,
                                                angle=5*u.deg,
                                                pickable=True))
        #sing a victory song...
        print("slit added")

        # some final stuff that must be here for some reason... to be reviewed?
        obj = self.canvas.get_object_by_tag(new_slit_tag)
        # obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.add_callback('edited', self.edit_cb)
        # self.cleanup_kind('point')
        # ssself.cleanup_kind('box')
        return self.canvas.objects[-1]

             # create box


    def create_astropy_RectangleSkyRegion(self, pattern_row):
        # given
        ra, dec = pattern_row[1:3]
        x0, y0 = pattern_row[5:7]
        x1, y1 = pattern_row[7:9]

        ra_width = (x1-x0)*self.wcs.proj_plane_pixel_scales()[0].value
        dec_length = (y1-y0)*self.wcs.proj_plane_pixel_scales()[0].value

        center = SkyCoord(ra, dec, unit=(u.deg, u.deg), frame="fk5")
        sky_region = RectangleSkyRegion(
            center=center, width=ra_width*u.deg, height=dec_length*u.arcsec, )

        return sky_region

    def set_pattern_entry_text_color(self, event):

        if self.base_pattern_name_entry.get() != "Base Pattern Name":

            # self.base_pattern_name_entry.foreground="black"
            self.base_pattern_name_entry.config(fg="black")




    def get_dmd_coords_of_picked_slit(self, picked_slit):
        """ get_dmd_coords_of_picked_slit """

        x0, y0, x1, y1 = picked_slit.get_llur()
        fits_x0 = x0+1
        fits_y0 = y0+1
        fits_x1 = x1+1
        fits_y1 = y1+1

        fits_xc, fits_yc = picked_slit.get_center_pt()+1

        dmd_xc, dmd_yc = convert.CCD2DMD(fits_xc, fits_yc)
        dmd_x0, dmd_y0 = convert.CCD2DMD(fits_x0, fits_y0)
        dmd_x1, dmd_y1 = convert.CCD2DMD(fits_x1, fits_y1)

        dmd_width = int(np.ceil(dmd_x1-dmd_x0))
        dmd_length = int(np.ceil(dmd_y1-dmd_y0))

        return dmd_xc, dmd_yc, dmd_x0, dmd_y0, dmd_x1, dmd_y1, dmd_width, dmd_length

    def slit_width_length_adjust(self, event=None):
        """ to be written """
        try:
            picked_slit = self.canvas.get_object_by_tag(self.selected_obj_tag)

            current_dmd_width = int(self.width_adjust_btn.get())
            current_dmd_length = int(self.length_adjust_btn.get())

            half_current_dmd_width = int(current_dmd_width)/2
            half_current_dmd_length = int(current_dmd_length)/2

            fits_xc, fits_yc = picked_slit.get_center_pt()
            dmd_xc, dmd_yc = convert.CCD2DMD(fits_xc+1, fits_yc+1)

            dmd_x0 = dmd_xc-half_current_dmd_width
            dmd_y0 = dmd_yc-half_current_dmd_length
            dmd_x1 = dmd_xc+half_current_dmd_width
            dmd_y1 = dmd_yc+half_current_dmd_length

            fits_x0, fits_y0 = convert.DMD2CCD(dmd_x0-1, dmd_y0-1)
            fits_x1, fits_y1 = convert.DMD2CCD(dmd_x1-1, dmd_y1-1)

            fits_length = np.ceil(fits_y1-fits_y0)
            fits_width = np.ceil(fits_x1-fits_x0)

            picked_slit.xradius = fits_width/2
            picked_slit.yradius = fits_length/2

            self.canvas.set_draw_mode('draw')  # stupid but necessary to show
            # which object is selected
            self.canvas.set_draw_mode('pick')

            # update the cells in the table.
            obj_ind = list(self.SlitTabView.stab.get_column_data(
                0)).index(self.selected_obj_tag.strip("@"))

            imcoords_txt_fmt = "{:.2f}"

            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=5, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_x0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=6, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_y0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=7, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_x1))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=8, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_y1))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=11, redraw=True,
                                                value=int(dmd_x0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=12, redraw=True,
                                                value=int(dmd_y0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=13, redraw=True,
                                                value=int(dmd_x1))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=14, redraw=True,
                                                value=int(dmd_y1))

        except AttributeError:
            print("Must first pick a slit to adjust width/length!!")
        pass
    
    def delete_obj_cb(self, obj, canvas, event, pt, ptype):
        try:
            if event.key == 'd':
                # print(event.key)
                canvas.delete_object(obj)
                print("start tab len", len(
                    self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.delete_row(self.tab_row_ind)
                print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.redraw()
                self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
                    index=self.obj_ind)
                # del self.SlitTabView.slit_obj_tags[self.obj_ind]
                self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
                canvas.clear_selected()

                try:

                    for si in range(len(self.pattern_series)):

                        sub = self.pattern_series[si]

                        tag = int(obj.tag.strip("@"))

                        if tag in sub.object.values:
                            sub_ind = sub.where(sub.object == tag).dropna(
                                how="all").index.values[0]
                            sub = sub.drop(index=sub_ind)

                            self.pattern_series[si] = sub

                except:
                    print("try again")

        except:
            pass

    def pick_cb(self, obj, canvas, event, pt, ptype):
        """ to be written """

        print("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        self.logger.info("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))

        try:
            canvas.get_object_by_tag(self.selected_obj_tag).color = 'red'
            canvas.clear_selected()
            print('unselect previous obj tag')
        except:
            pass

        canvas.select_add(obj.tag)
        self.selected_obj_tag = obj.tag
        obj.color = 'green'

        canvas.set_draw_mode('draw')  # stupid but necessary to show
        # which object is selected
        # this took me a solid 3 hours to figure out
        canvas.set_draw_mode('pick')

        self.obj_ind = int(obj.tag.strip('@'))-1
        try:
            self.tab_row_ind = self.SlitTabView.stab.get_column_data(
                0).index(obj.tag.strip('@'))
            dmd_x0, dmd_x1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
                'dmd_x0', 'dmd_x1']].astype(int)
            dmd_y0, dmd_y1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
                'dmd_y0', 'dmd_y1']].astype(int)
            dmd_width = int(dmd_x1-dmd_x0)
            dmd_length = int(dmd_y1-dmd_y0)

            self.slit_w.set(dmd_width)
            self.slit_l.set(dmd_length)
        except:
            pass

        if ptype == 'up' or ptype == 'down':
            
            print("picked object with tag {}".format(obj.tag))
            #if self.deleteChecked.get():#event.key == 'd':
            canvas.delete_object(obj)
            try:
                self.SlitTabView.stab.select_row(row=self.tab_row_ind)          
                print("start tab len", len(
                    self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.delete_row(self.tab_row_ind)
                print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.redraw()
                self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
                    index=self.obj_ind)
                # del self.SlitTabView.slit_obj_tags[self.obj_ind]
                self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
                canvas.clear_selected()

                try:

                    for si in range(len(self.pattern_series)):

                        sub = self.pattern_series[si]

                        tag = int(obj.tag.strip("@"))

                        if tag in sub.object.values:
                            sub_ind = sub.where(sub.object == tag).dropna(
                                how="all").index.values[0]
                            sub = sub.drop(index=sub_ind)

                            self.pattern_series[si] = sub

                except:
                    print("try again")

            except:
                print("No slit table created yet.")

        return True

    def edit_cb(self, obj):
        """ to be written """
        self.logger.info("object %s has been edited" % (obj.kind))
        tab_row_ind = list(self.SlitTabView.stab.get_column_data(
            0)).index(int(obj.tag.strip("@")))
        self.SlitTabView.stab.select_row(row=tab_row_ind, redraw=True)
        # update slit table data to reflect the new edits
        self.SlitTabView.update_table_row_from_obj(obj, self.fitsimage)
        return True

    def cleanup_kind(self, kind):
        """ to be written """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        # points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        found = CM.CompoundMixin.get_objects_by_kind(self.canvas, str(kind))
        list_found = list(found)
        CM.CompoundMixin.delete_objects(self.canvas, list_found)
        self.canvas.objects  # check that the points are gone





   
    def save(file_type):
        """ to be written """
        if file_type == None:
            files = [('All Files', '*.*')]
        elif file_type == 'py':
            files = [('Python Files', '*.py')]
        elif file_type == 'txt':
            files == ('Text Document', '*.txt')
        elif file_type == 'csv':
            files == ('DMD grid', '*.csv')
        file = filedialog.asksaveasfile(
            filetypes=files, defaultextension=files)

        # btn = ttk.Button(self, text = 'Save', command = lambda : save())

    def create_menubar(self, parent):
        """ to be written """
        
        parent.geometry("1400x900")  # was ("1280x900")
        if platform == "win32":
            parent.geometry("1400x920")
        parent.title("SAMOS Main Page")
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
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_separator()

        return menubar



if __name__ == "__main__":
    app = GuideStarPage()
    # set a style for the application so it works on various desktop themes
    # ttk.Style().theme_use("clam")
    combostyle = ttk.Style()
    combostyle.configure("TCombobox", fieldbackground="dark gray",
                         foreground="black", background="white")
    app.mainloop()

    # IF you find this useful >> Claps on Medium >> Stars on Github >> Subscription on youtube will help me
