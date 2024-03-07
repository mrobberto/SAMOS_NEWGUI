"""
SAMOS Guide Star tk Frame Class
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
from samos.dmd import DigitalMicroMirrorDevice
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
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame


class GSPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Guide Star", **kwargs)
        self.config_tab = parent.frames["ConfigPage"]

        # keep track of the entry number for header keys that need to be added
        # will be used to write "OtherParameters.txt"
        self.extra_header_params = 0
        # keep string of entries to write to a file after acquisition.
        self.header_entry_string = ''
        self.main_fits_header.create_main_params_dict()
        self.wcs = None
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        self.loaded_regfile = None
        self.fits_dir = get_fits_dir()

        # FITS manager
        frame = tk.LabelFrame(self.main_frame, text="FITS Manager", background="pink")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        # RA, DEC Entry box
        self.ra = tk.DoubleVar(self, 150.17110)
        tk.Label(frame, text="RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.ra).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.dec = tk.DoubleVar(self, -54.79004)
        tk.Label(frame, text="Dec:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.dec).grid(row=1, column=1, sticky=TK_STICKY_ALL)

        # QUERY Server
        frame = tk.LabelFrame(self.main_frame, text="Query Image Server", font=BIGFONT)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Survey Select Menu
        tk.Label(frame, text="Survey").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.survey_options = ["SkyMapper", "SDSS", "PanSTARRS/DR1/" "DSS", "DSS2/red", 
                               "CDS/P/AKARI/FIS/N160", "2MASS/J", "GALEX", "AllWISE/W3"]
        self.survey_selected = tk.StringVar(self, self.survey_options[0])
        self.menu_survey = ttk.OptionMenu(frame, self.survey_selected, *self.survey_options)
        self.menu_survey.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.menu_survey['menu'].insert_separator(3)
        # Filter Selection
        self.survey_filter = tk.StringVar(self, "i")
        tk.Label(frame, text="Filter:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.survey_filter).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Run Query
        b = tk.Button(frame, text="Run Query", command=self.run_query)
        b.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # GINGA DISPLAY
        frame = tk.LabelFrame(self.main_frame, text="Survey Image", relief=tk.RAISED)
        frame.grid(row=0, column=1, rowspan=4, sticky=TK_STICKY_ALL)
        frame.rowconfigure(0, minsize=800, weight=1)
        frame.columnconfigure(0, minsize=800, weight=1)
        self.ginga_canvas = tk.Canvas(frame, bg="grey", height=800, width=800)
        self.ginga_canvas.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.fits_image = CanvasView(self.logger)
        self.fits_image.set_widget(self.ginga_canvas)
        self.fits_image.enable_autocuts('on')
        self.fits_image.set_autocut_params('zscale')
        self.fits_image.enable_autozoom('on')
        self.fits_image.set_enter_focus(True)
        self.fits_image.set_callback('cursor-changed', self.cursor_changed)
        self.fits_image.set_bg(0.2, 0.2, 0.2)
        self.fits_image.ui_set_active(True)
        self.fits_image.show_pan_mark(True)
        self.fits_image.show_mode_indicator(True, corner='ur')
        self.fits_image.get_bindings().enable_all(True)
        self.drawing_canvas = self.canvas_types.DrawingCanvas()
        self.drawing_canvas.enable_draw(True)
        self.drawing_canvas.enable_edit(True)
        self.drawing_canvas.set_drawtype('box', color='red')
        self.drawing_canvas.register_for_cursor_drawing(self.fits_image)
        self.drawing_canvas.add_callback('pick-up', self.pick_cb, 'up')
        self.drawing_canvas.set_draw_mode('pick')
        self.drawing_canvas.ui_set_active(True)
        self.fits_image.get_canvas().add(self.drawing_canvas)
        self.drawtypes = self.drawing_canvas.get_drawtypes()
        self.drawtypes.sort()
        self.fits_image.set_window_size(1028, 1044)
        self.readout = tk.Label(frame, text='')
        self.readout.grid(row=1, column=0, sticky=TK_STICKY_ALL)

        # Guide Star Pickup Frame
        frame = tk.LabelFrame(self.main_frame, text="Guide Star Pickup", font=BIGFONT)
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Low Mag (bright end)
        self.low_mag = tk.IntVar(self, 11)
        tk.Label(frame, text="Low Mag:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        s = tk.Spinbox(frame, command=self.check_valid_mags, increment=1, textvariable=self.low_mag, from_=0, to=25)
        s.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        s.bind("<Return>", self.check_valid_mags)
        # High mag (faint end)
        tk.Label(frame, text="High Mag:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.high_mag = tk.IntVar(self, 13)
        s = tk.Spinbox(frame, command=self.check_valid_mags, increment=1, textvariable=self.high_mag, from_=0, to=25)
        s.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        s.bind("<Return>", self.check_valid_mags)
        # SLIT POINTER ENABLED
        self.guide_star_pickup_enabled = tk.IntVar(self, 1)
        b = tk.Button(frame, text="Pick Guide Star", command=self.pick_guide_star)
        b.grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        # Candidate Guide Star Co-ordinates
        self.gs_ra = tk.DoubleVar(self, 150.17110)
        tk.Label(frame, text="RA:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_ra).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.gs_dec = tk.DoubleVar(self, -54.79004)
        tk.Label(frame, text="Dec:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_dec).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        # X Shift
        self.gs_xshift = tk.DoubleVar(self, 150.17110)
        tk.Label(frame, text="X Shift (mm)").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_xshift).grid(row=5, column=1, sticky=TK_STICKY_ALL)
        # Y Shift
        self.gs_yshift = tk.DoubleVar(self, -54.79004)
        tk.Label(frame, text="Y Shift (mm)").grid(row=6, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_yshift).grid(row=6, column=1, sticky=TK_STICKY_ALL)
        # Magnitude
        self.gs_mag = tk.DoubleVar(self, 0.0)
        tk.Label(frame, text="Magnitude:").grid(row=7, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_mag).grid(row=7, column=1, sticky=TK_STICKY_ALL)
        b = tk.Button(frame, text="Accept Guide Star", command=self.send_RADEC_to_SOAR)
        b.grid(row=8, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # Ginga Tools Box
        frame = tk.LabelFrame(self.main_frame, text="Image Tools", font=BIGFONT)
        frame.grid(row=4, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.drawtypes = self.drawing_canvas.get_drawtypes()
        # W Draw (?)
        wdrawtype = tk.Entry(frame)
        wdrawtype.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        wdrawtype.insert(0, 'box')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype
        # Draw Colour
        wdrawcolor = ttk.Combobox(frame, values=self.drawcolors, style="TCombobox")
        wdrawcolor.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        color_index = self.drawcolors.index('red')
        wdrawcolor.current(color_index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor
        # Draw Fill
        self.vfill = tk.IntVar(self, 0)
        tk.Checkbutton(frame, text="Fill", variable=self.vfill).grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.walpha = tk.DoubleVar(self, 1.0)
        tk.Label(frame, text="Alpha:").grid(row=0, column=3, sticky=TK_STICKY_ALL)
        e = tk.Entry(frame, textvariable=self.walpha)
        e.grid(row=0, column=4, sticky=TK_STICKY_ALL)
        e.bind("<Return>", self.set_drawparams)
        # Buttons
        tk.Button(frame, text="Slits Only", command=self.slits_only).grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Clear Canvas", command=self.clear_canvas).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Save Canvas", command=self.save_canvas).grid(row=1, column=2, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Open File", command=self.open_file).grid(row=1, column=3, sticky=TK_STICKY_ALL)


    def regfname_handle_focus_out(self, _):
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
        slits = CM.CompoundMixin.get_objects_by_kind(self.drawing_canvas, 'box')

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
        objects = CM.CompoundMixin.get_objects(self.drawing_canvas)

        try:
            pattern_list_index = self.pattern_group_dropdown.current()
            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects = [self.drawing_canvas.get_object_by_tag(
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
                x1, y1 = self.convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1, y1] = 0
            elif self.guide_star_pickup_enabled.get() == 1 and obj.kind == 'point':
                x1, y1 = self.convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.floor(x1)), int(np.floor(y1))
                x2, y2 = self.convert.CCD2DMD(ccd_x1, ccd_y1)
                x2, y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
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
                    x1, y1 = self.convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = self.convert.CCD2DMD(cx0, cy1)    # and the higher
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
                    x1, y1 = self.convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = self.convert.CCD2DMD(cx1, cy0)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y1] = 1


    def push_slit_shape(self):
        """
        push selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        
        # if someone forgot to remove the tracese, we do it here for safety
        self.remove_traces()
        self.collect_slit_shape()
        
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

    def set_filter(self):
        """ to be written """
        print(self.FW_filter.get())
        print('moving to filter:', self.FW_filter.get())
#        self.Current_Filter.set(self.FW_filter.get())
        filter = self.FW_filter.get()
        self.main_fits_header.set_param("filter", filter)
        filter_pos_ind = list(self.filter_data["Filter"]).index(filter)
        filter_pos = list(self.filter_data["Position"])[filter_pos_ind]
        self.main_fits_header.set_param("filtpos", filter_pos)
        print(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
        t = PCM.move_filter_wheel(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=INDICATOR_LIGHT_ON_COLOR)
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
        alpha = self.walpha.get()
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  # 'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.drawing_canvas.set_drawtype(kind, **params)

    def save_canvas(self):
        """ to be written """
        regs = ap_region.export_regions_canvas(self.drawing_canvas, logger=self.logger)

    def clear_canvas(self):
        """ to be written """
        obj_tags = list(self.drawing_canvas.tags.keys())
        # print(obj_tags)
        #for tag in obj_tags:
        #    if self.SlitTabView is not None:
        #        if tag in self.SlitTabView.slit_obj_tags:
        #            obj_ind = self.SlitTabView.slit_obj_tags.index(tag)
        #            # self.SlitTabView.stab.delete_row(int(tag.strip("@")))
        #            del self.SlitTabView.slit_obj_tags[obj_ind]
        #        self.SlitTabView.slitDF = self.SlitTabView.slitDF[0:0]

                # if not self.low_magindow.winfo_exists():
                #    self.SlitTabView.recover_window()
        self.drawing_canvas.delete_all_objects(redraw=True)


   
    def update_PotN(self):
        """
        Updates the parameters of the night variables and files for logging the observations
        """
        import json
#       How do we capture a parameter in another class/form?
        self.PAR.PotN['Telescope'] = self.config_tab.Telescope.get() #ConfigPage.Telescope.get()
        self.PAR.PotN['Program ID'] = self.program_var.get() 
        self.PAR.PotN['Proposal Title'] = self.config_tab.Proposal_Title.get()#ConfigPage.Telescope.get()
        self.PAR.PotN['Principal Investigator'] = self.config_tab.Principal_Investigator.get() #ConfigPage.Telescope.get()
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
        PotN_file = get_data_file("system", 'Parameters_of_the_night.txt')
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
        self.last_fits_file_dialog = tk.filedialog.askopenfilename(initialdir=self.fits_dir,                                                          title="Select a File",
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

    def run_query(self):
        """ to be written """
        #cleanup the canfas
        CM.CompoundMixin.delete_all_objects(self.drawing_canvas)#,redraw=True)
        self.clear_canvas()

        from astroquery.hips2fits import hips2fits
        Survey = self.survey_selected.get()

        if Survey == "SkyMapper":
            try:
                self.SkyMapper_query_GuideStar()
            except:
                print("\n Sky mapper image server is down \n")
            return

        elif Survey == "SDSS":
            self.SDSS_query()
            return
    
        elif Survey == "PanSTARRS/DR1/":
            print("\n Quering PanSTARRS/DR1")
            self.PanStarrs_query_GuideStars()

        else:
            Survey = Survey+self.survey_filter.get()
        # =============================================================================
        # Download an image centered on the coordinates passed by the main window
        #
        # =============================================================================
            # object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
            #object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'],
            #                         #                                 unit=(u.deg, u.deg), frame='icrs')
            #                         unit=(u.hourangle, u.deg), frame='icrs')
            c = SkyCoord(self.ra.get(),
                         self.ra.get(), unit=(u.deg, u.deg))
     # FROM      https://astroquery.readthedocs.io/en/latest/hips2fits/hips2fits.html
            query_params = {"NAXIS1": 1056,
                            "NAXIS2": 1032,
                            "WCSAXES": 2,
                            "CRPIX1": 1056,
                            "CRPIX2": 1032,
                            "CDELT1": self.PAR.SISI_PixelScale/3600,
                            "CDELT2": self.PAR.SISI_PixelScale/3600,
                            "CUNIT1": "deg",
                            "CUNIT2": "deg",
                            "CTYPE1": "RA---TAN",
                            "CTYPE2": "DEC--TAN",
                            "CRVAL1": c.ra.value,
                            "CRVAL2": c.dec.value}
            query_wcs = wcs.WCS(query_params)
            hips = self.survey_selected.get()
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
            hdul[0].header["FILENAME"] = f"{Survey}_{self.ra.get()}_{self.dec.get()}.fits"

            self.image = hdul
            hdul.writeto(get_data_file('astrometry.general') / 'newtable.fits', overwrite=True)
            img = AstroImage()
            Posx = self.ra.get()
            Posy = self.ra.get()
            filt = self.survey_filter.get()
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
     
            #self.button_find_stars['state'] = 'active'

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
    def SkyMapper_query_GuideStar(self):
        """ get image from SkyMapper """

        img = AstroImage()
        Posx = self.ra.get()
        Posy = self.ra.get()
        filt = self.survey_filter.get()
        
        SOAR_EFL = 68176.3    # mm
        SAMI_GUIDE_SCALE = 206265 / SOAR_EFL   # arcsec/mmm
        SAMI_GUIDE_FoV_mm = 100 # mm
        SAMI_GUIDE_FoV_arcsec = SAMI_GUIDE_FoV_mm * SAMI_GUIDE_SCALE    # arcsec [mm * arcsec/mm 
        SAMI_GUIDE_FoV_SISIpix = round(SAMI_GUIDE_FoV_arcsec / self.PAR.SISI_PixelScale)   

        filepath = skymapper_interrogate(Posx, Posy, SAMI_GUIDE_FoV_SISIpix , SAMI_GUIDE_FoV_SISIpix , filt)[0]
        with fits.open(filepath.name) as hdu_in:
            #            img.load_hdu(hdu_in[0])
            
            self.data_GS = hdu_in[0].data
            self.header_GS = hdu_in[0].header
            
            #for debug, write onfile the fits file returned by skymapper
            SkyMapperProduced = os.path.join(self.PAR.QL_images, "SkyMapperProduced.fits")
            fits.writeto(SkyMapperProduced, self.data_GS,
                         header=self.header_GS, overwrite=True)            
        self.fitsimage.rotate(self.PAR.Ginga_PA)    
        self.Display(SkyMapperProduced)
        
        """
        TABLE CONSTRUCTION
        """
        import urllib.request
        string = "https://skymapper.anu.edu.au/sm-cone/public/query?"
        string += "RA=" + Posx + "&"
        string += "DEC=" + Posy + "&"
        string += "SR=0.06&RESPONSEFORMAT=CSV"
        
        import tempfile
        with urllib.request.urlopen(string,timeout=30) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
        self.table_full = pd.read_csv(tmp_file.name)
        #rename the magnitudes using the general band names
        self.table_full = self.table_full.rename(columns={"g_psf": "g_band","r_psf": "r_band","i_psf": "i_band","z_psf": "z_band","raj2000":"RA","dej2000":"DEC"})
        
        
        
    def pick_guide_star(self):        
        """ to be written, but it seems rather obvious"""
        CM.CompoundMixin.delete_all_objects(self.drawing_canvas)#,redraw=True)
        self.clear_canvas()
        filt = self.survey_filter.get()
        if filt == "g":
            self.table_full['star_mag'] = self.table_full['g_band']
        elif filt == "r":
            self.table_full['star_mag'] = self.table_full['r_band']
        elif filt == "i":
            self.table_full['star_mag'] = self.table_full['i_band']
        elif filt == "z":
            self.table_full['star_mag'] = self.table_full['z_band']
        self.table = self.table_full[ (self.table_full['star_mag']>self.low_mag.get()) & (self.table_full['star_mag']<self.high_mag.get()) ]
        
        viewer=self.fitsimage
        image = viewer.get_image()
        x_SkyMap = [] 
        y_SkyMap = []
        i=0
        nstar = self.table.shape[0]
        i_drop=[]
        for i in range(nstar):
            x, y = image.radectopix(self.table.RA.iloc[i], self.table.DEC.iloc[i], format='str', coords='fits')
            #CHECK IF THE STAR IS OUTSIDE THE CENTRAL REGION
            if  ( (x>round(self.data_GS.shape[0]/4)) and (x<round(self.data_GS.shape[0]*3/4)) and (y>round(self.data_GS.shape[0]/4)) and (y<round(self.data_GS.shape[0]*3/4)) ):
                i_drop.append(self.table.index[i])
                continue
            elif  ( (x<0) or (x>round(self.data_GS.shape[0])) or (y<0) or (y>round(self.data_GS.shape[0])) ):
                i_drop.append(self.table.index[i])
                continue
            print(i,self.table.RA.iloc[i], self.table.DEC.iloc[i],x,y)
            x_SkyMap.append(x)
            y_SkyMap.append(y)
        self.table = self.table.drop(i_drop)
        
        print("Converted RADEC to XY for display")   
        
        
        # Draw circles around all objects
        radius_pix=10
        regions = [CirclePixelRegion(center=PixCoord(x,y), radius=radius_pix)
                        for x, y in np.transpose([x_SkyMap,y_SkyMap])]  # [(1, 2), (3, 4)]]
        regs = Regions(regions)
        i_tag = 0
        for reg in regs:
            obj = r2g(reg)
            obj.color = "red"
            obj.pickable = True
            obj.add_callback('pick-up', self.pick_cb, 'down')
            obj.tag = '@'+str(i_tag)
            i_tag += 1
            self.drawing_canvas.add(obj)
        self.circle_tags = list(self.drawing_canvas.tags.keys())    
        print(self.circle_tags)


        # LABELS NEXT TO all objects
        Text = self.drawing_canvas.get_draw_class('Text')
        z = np.transpose([x_SkyMap,y_SkyMap])
        x = z[:,0]+5
        y = z[:,1]+5
        for i in range(len(x)):
                print(x[i],y[i])
                string=Text(x=x[i], y=y[i],text=str(i),color='red')
                string.fontsize=25
                self.drawing_canvas.add(string)
        
        #DRAW  THE YELLOW AREA OF SISI
        box_region = RectanglePixelRegion(center=PixCoord(x=round(self.data_GS.shape[0]/2), y=round(self.data_GS.shape[1]/2)),
                          width=round(self.data_GS.shape[0]/2), height=round(self.data_GS.shape[1]/2),
                          angle=0*u.deg)  
        #regs = Regions(box_region)
        #regs.append(box_region)
        obj = r2g(box_region)
        obj.color = "green"

        # FINAL PLOT        
        #for reg in regs:
        #    obj = r2g(reg)
            #obj.color = "red"
            #obj.fill=True
            #obj.alpha=0.01
            #obj.alpha = "0.5"
        # add_region(self.drawing_canvas, obj, tag="twirlstars", redraw=True)
        self.drawing_canvas.add(obj)
        print("done")

        
        
    def SDSS_query(self):

#        img = AstroImage()
        Posx = self.ra.get()
        Posy = self.ra.get()
        filt = self.survey_filter.get()
        
        from astropy import units as u
        from astropy import coordinates as coords
        from astroquery.sdss import SDSS
        from astropy.nddata import Cutout2D


        pos = coords.SkyCoord(Posx,Posy, unit=(u.deg, u.deg))
        #xid = SDSS.query_region(pos, radius='10 arcsec', spectro=True)
        #print(xid)
        #if xid is None:
        #    print("\n\n\n**** FIELD NOT IN SDSS *****\n\n\n")
        #    return
        #else:
        #    self.SDSS_stars = np.transpose([xid['ra'],xid['dec']])
            
        
        im = SDSS.get_images(coordinates=pos, radius='170 arcsec', band=filt)
        number_of_nans=758*758
        for i in range(len(im)):
            hdu = im[i]
            data = hdu[0].data
            header = hdu[0].header
            """
            2D Cutout Images
            https://docs.astropy.org/en/stable/nddata/utils.html
            """
            w = wcs.WCS(header)
            xc, yc = np.round(w.world_to_pixel(pos))   
            position = (xc, yc)
            SDSS_pixel_scale = 0.396 #arcsec_pix - https://classic.sdss.org/dr3/instruments/imager/
            size = np.round((300/SDSS_pixel_scale, 300/SDSS_pixel_scale))     # pixels
            try:
                cutout = Cutout2D(data, position, size, wcs=w,mode='partial')
            except:
                continue
            if np.count_nonzero(np.isnan(cutout.data)) < number_of_nans:
                number_of_nans = np.count_nonzero(np.isnan(cutout.data))
                best_data = cutout.data
                best_header = copy.deepcopy(header)
                d=dict(cutout.wcs.to_header())
                best_header.update(d)
        
        #always needd for Pick Guide Stars
        self.data_GS = best_data
        self.header_GS = best_header

        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, best_data,
                     header=best_header, overwrite=True)    

        #hdu = fits.open(self.fits_image_ql)
        #img.load_hdu(hdu)
        #self.fitsimage.set_image(img)
        #self.AstroImage = img
        
        self.fitsimage.rotate(90)
        
        self.Display(self.fits_image_ql)
        
        
        """
        TABLE CONSTRUCTION
        """
        
        result = SDSS.query_region(pos,fields={'ra','dec','psfMag_g','psfMag_r','psfMag_i','psfMag_z'},radius=180*u.arcsec)
        
        self.table_full = result.to_pandas()
        #rename the magnitudes using the general band names;
        self.table_full = self.table_full.rename(columns={"ra":"RA", "dec":"DEC", "psfMag_g": "g_band", "psfMag_r":"r_band", "psfMag_i":"i_band", "psfMag_z":"z_band"})
        
        # not that elegant, but this is how  we convert the table to a pandas table
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(result, tmp_file)
        self.table_full = pd.read_csv(tmp_file.name)        
   

        
    def PanStarrs_query_GuideStars(self):
        
        #get ra,dec and set image size
        ra = self.ra.get()
        dec = self.ra.get()
        if dec < -30:
            print("\n Declination outside the PanStarrs survey \n")
            return
        
        filter = self.survey_filter.get()
        size = int(300 / 0.25)   # create an image 5'x5'
        
        #get the pan star image
        fitsurl = PSima.get_url(ra, dec, size=size, filters=filter, format="fits")
        fh = fits.open(fitsurl[0])
        fim = fh[0].data
        
        #also a couple of variables for the pick_guide_star
        self.data_GS = fh[0].data
        self.header_GS = fh[0].header
        
        # replace NaN values with zero for display
        fim[np.isnan(fim)] = 0.0
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, fim,
                     header=fh[0].header, overwrite=True)    
        
        self.Display(self.fits_image_ql)
        self.fitsimage.rotate(self.PAR.Ginga_PA)
 
    
        """
        TABLE CONSTRUCTION
        """
        
        """Simple positional query
        Search mean object table with nDetections > 1.

        This searches the mean object catalog for objects within 212 arcsec of radec). 
        Note that the results are restricted to objects with nDetections>1, 
        where nDetections is the total number of times the object was detected on the single-epoch images 
        in any filter at any time. Objects with nDetections=1 tend to be artifacts, so this is a quick way 
        to eliminate most spurious objects from the catalog.
        """
        radius = 212.0/3600.0
        constraints = {'nDetections.gt':1}
        # strip blanks and weed out blank and commented-out values
        columns = """objID,raMean,decMean,nDetections,ng,nr,ni,nz,ny,
            gMeanPSFMag,rMeanPSFMag,iMeanPSFMag,zMeanPSFMag,yMeanPSFMag""".split(',')
        columns = [x.strip() for x in columns]
        columns = [x for x in columns if x and not x.startswith('#')]
        results = PStab.ps_cone(ra,dec,radius,release='dr2',columns=columns,verbose=True,**constraints)
        
        tab = ascii.read(results)
        # improve the format
        for filter in 'grizy':
            col = filter+'MeanPSFMag'
            try:
                tab[col].format = ".4f"
                tab[col][tab[col] == -999.0] = np.nan
            except KeyError:
                print("{} not found".format(col))
        print(tab)
        self.table_full = tab.to_pandas()
        self.table_full = self.table_full.rename(columns={"gMeanPSFMag": "g_band","rMeanPSFMag": "r_band","iMeanPSFMag": "i_band","zMeanPSFMag": "z_band","raMean":"RA", "decMean":"DEC"})


       
  
    def load_file(self):
        """ to be written """
        self.AstroImage = load_data(
            self.fullpath_FITSfilename, logger=self.logger)
        self.drawing_canvas.set_image(self.AstroImage)
        self.root.title(self.fullpath_FITSfilename)

    def open_file(self):
        """ to be written """
        filename = tk.filedialog.askopenfilename(filetypes=[("allfiles", "*"), ("fitsfiles", "*.fits")])
        # self.load_file()
        self.AstroImage = load_data(filename, logger=self.logger)
        self.fitsimage.set_image(self.AstroImage)

        if self.AstroImage.wcs.wcs.has_celestial:
            self.wcs = self.AstroImage.wcs.wcs

    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.drawing_canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.drawing_canvas, 'point')
        print(list(points))

        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.drawing_canvas, 'point')
        list_point = list(points)
        CM.CompoundMixin.delete_objects(self.drawing_canvas, list_point)
        self.drawing_canvas.objects  # check that the points are gone

        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.drawing_canvas, ['point', 'circle',
                                                                     'rectangle', 'polygon',
                                                                     'triangle', 'righttriangle',
                                                                     'ellipse', 'square'])
        list_points = list(points)
        CM.CompoundMixin.delete_objects(self.drawing_canvas, list_points)
        self.drawing_canvas.objects  # check that the points are gone


    def cursor_changed(self, viewer, button, data_x, data_y):
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

        dmd_x, dmd_y = self.convert.CCD2DMD(fits_x, fits_y)

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
            self.ra_center, self.dec_center = image.pixtoradec(1056, 1032,
                                                               format='str', coords='fits')
            Delta_Xmm = ( ra_deg - self.ra.get() ) * 3600 / self.PAR.SOAR_arcs_mm_scale
            Delta_Ymm = ( dec_deg - self.ra.get() ) * 3600 / self.PAR.SOAR_arcs_mm_scale

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
#        dmd_text = "DMD_X: %i  DMD_Y: %i \n" % (
#            np.floor(dmd_x), np.floor(dmd_y))
        mmm_text = "Dx(mm): %.3s  Dy(mm): %.3s \n" % (
            np.floor(Delta_Xmm), np.floor(Delta_Ymm))
        text = "X: %i  Y: %i  Value: %s" % (
            np.floor(fits_x), np.floor(fits_y), value)

        text = coords_text + coords_text_DEG + mmm_text + text
        self.readout.config(text=text)

    def MASTER_quit(self):
        self.destroy()
        return True

######

    def Pickup_GuideStar(self):
        self.wdrawtype.delete(0, tk.END)
        mode = self.Draw_Edit_Pick_Checked.set("draw")
        self.set_mode_cb()
        if self.guide_star_pickup_enabled.get() == 1:
            self.wdrawtype.insert(0, "point")
        else:
            self.wdrawtype.insert(0, "box")
#            self.Draw_Edit_Pick_Checked.set("None")
        print("drawtype changed to ", self.wdrawtype.get())
#        parameters = []
#        parameters['color'] = 'red'
        self.drawing_canvas.set_drawtype(self.wdrawtype.get())#,**parameters)
            

    def set_mode_cb(self):
        """ to be written """
        mode = self.Draw_Edit_Pick_Checked.get()
        
        #we turn off here the SourcePickup_ChkBox 
        if mode != "draw":
            self.guide_star_pickup_enabled.set(0)
            
#        self.logger.info("canvas mode changed (%s) %s" % (mode))
        self.logger.info("canvas mode changed (%s)" % (mode))
        try: #all object painted red, should not be true for the traces
            for obj in self.drawing_canvas.objects:
                obj.color = 'red'
        except:
            pass

        self.drawing_canvas.set_draw_mode(mode)


    def draw_cb(self, canvas, tag):
        """ to be written """
        self.Pickup_GuideStar()
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
        
        # Pick up mode. obj.kind should always be point.
            #this case requires more sophisticated operations, hence a dedicated function            
        self.slit_handler(obj)


    def slit_handler(self, obj):
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
            self.drawing_canvas.add(obj)
        
        # time to do the math; collect the pixels in the Ginga box
        data_box = self.AstroImage.cutout_shape(obj)

        # we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.drawing_canvas, obj)

  #      obj = self.drawing_canvas.get_draw_class('rectangle')
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
#        self.drawing_canvas.add(slit_box(x1=objs[0].objx+x1-slit_w,y1=objs[0].objy+y1-slit_h,x2=objs[0].objx+x1+slit_w,y2=objs[0].objy+y1+slit_h,
#                        width=100,
#                        height=30,
#                        angle = 0*u.deg))

        #enogh with astronomy;
        # having found the centroid, we need to draw the slit
        slit_box = self.drawing_canvas.get_draw_class('box')
        xradius = self.low_mag.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        yradius = self.high_mag.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        new_slit_tag = self.drawing_canvas.add(slit_box(x=objs[0].objx+x1,
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
        """
        
        """
        #obj = self.drawing_canvas.get_object_by_tag(new_slit_tag)
        # obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.add_callback('edited', self.edit_cb)
        # self.cleanup_kind('point')
        # ssself.cleanup_kind('box')
        return self.drawing_canvas.objects[-1]

             # create box
        """     

        """
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
        """
        
        """
    def set_pattern_entry_text_color(self, event):

        if self.base_pattern_name_entry.get() != "Base Pattern Name":

            # self.base_pattern_name_entry.foreground="black"
            self.base_pattern_name_entry.config(fg="black")
        """    


    def check_valid_mags(self, event=None):
        """ to be written """
        pass
    
        """
    def delete_obj_cb(self, obj, canvas, event, pt, ptype):
        try:
            if event.key == 'd':
                # print(event.key)
                canvas.delete_object(obj)
                #print("start tab len", len(
                #    self.SlitTabView.stab.get_sheet_data()))
                #self.SlitTabView.stab.delete_row(self.tab_row_ind)
                #print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
                #self.SlitTabView.stab.redraw()
                #self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
                #    index=self.obj_ind)
                # del self.SlitTabView.slit_obj_tags[self.obj_ind]
                #self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
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
        """
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
        #try:
            #self.tab_row_ind = self.SlitTabView.stab.get_column_data(
            #    0).index(obj.tag.strip('@'))
            #dmd_x0, dmd_x1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
            #    'dmd_x0', 'dmd_x1']].astype(int)
            #dmd_y0, dmd_y1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
            #    'dmd_y0', 'dmd_y1']].astype(int)
         #   dmd_width = int(dmd_x1-dmd_x0)
         #   dmd_length = int(dmd_y1-dmd_y0)

         #   self.low_mag.set(dmd_width)
         #   self.high_mag.set(dmd_length)
         #except:
         #   pass

        if ptype == 'up' or ptype == 'down':
            
            print("picked object with index",format(obj.tag))
            
            # the obj.tas continuously incremented; we keep track of the current set in the self.circe_tags variable
            # and the first element of the self.circle_tags is subtracted off so we start from index = 0 for pandas
            index = int(obj.tag[1:]) - int(self.circle_tags[0][1:]) 
            
            #print(self.table.iloc[index])
            self.gs_ra.set(self.table['RA'].iloc[index])
            self.gs_dec.set(self.table['DEC'].iloc[index])
            Delta_RA = float(self.table['RA'].iloc[index]) - self.ra.get()
            Delta_DEC = float(self.table['DEC'].iloc[index]) - float(self.ra.get()) 
            Delta_RA_mm = round(Delta_RA * 3600 / self.PAR.SOAR_arcs_mm_scale,3)
            Delta_DEC_mm = round(Delta_DEC * 3600 / self.PAR.SOAR_arcs_mm_scale,3)
            self.gs_xshift.set(Delta_RA_mm)
            self.gs_yshift.set(Delta_DEC_mm)
            
            #print the magntude of the selected star
#            print(self.star_mag)
            self.gs_mag.set(round(self.table.star_mag.iloc[index],3))
        return True
        

    def edit_cb(self, obj):
        """ to be written """
        self.logger.info("object %s has been edited" % (obj.kind))
        #tab_row_ind = list(self.SlitTabView.stab.get_column_data(
        #    0)).index(int(obj.tag.strip("@")))
        #self.SlitTabView.stab.select_row(row=tab_row_ind, redraw=True)
        # update slit table data to reflect the new edits
        #self.SlitTabView.update_table_row_from_obj(obj, self.fitsimage)
        return True
