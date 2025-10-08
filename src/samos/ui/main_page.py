"""
SAMOS Main tk Frame Class
"""
from copy import deepcopy
import csv
from datetime import datetime
from functools import partial
import numpy as np
from pathlib import Path
import random
import re
import time
import twirl
import math

from astropy.coordinates import SkyCoord
from astropy.io import fits, ascii
from astropy import units as u
from astropy import wcs
from functools import partial
from ginga.AstroImage import AstroImage
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.util.loader import load_data
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView

from ginga.util import iqcalc

import pandas as pd
from PIL import Image, ImageTk
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Querybox

from samos.dmd.utilities import DMDGroup
from samos.ui.slit_table_view import SlitTableView as STView
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.utils import ccd_to_dmd, dmd_to_ccd
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled
from .progress_windows import ExposureProgressWindow
from .gs_query_frame import GSQueryFrame

from scipy.interpolate import UnivariateSpline # for PSF calculation

#imported for the Zero Point Calculation
from photutils.aperture import CircularAperture, CircularAnnulus, ApertureStats
from astropy.stats import SigmaClip, sigma_clip
from scipy.stats import norm
#from astropy import units as u
#from astropy.coordinates import SkyCoord
from photutils.aperture import SkyCircularAperture

import os


class MainPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Main Frame", **kwargs)
        self.previous_image_name = ""
        self.selected_object_tag = None
        self.last_update_time = datetime.now()
        self.iq = iqcalc.IQCalc()
        self.target_name = ""
        
#         self.initialize_slit_table()

        # keep track of the entry number for header keys that need to be added. will be used to write "OtherParameters.txt"
        self.extra_header_params = 0
        # keep string of entries to write to a file after acquisition.
        self.header_entry_string = ''
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        self.pattern_series = []
        self.sub_pattern_names = []

        # Early variable setting when variables must be valid for widgets to be enabled.
        self.loaded_reg_file = self.make_db_var(tk.StringVar, "dmd_loaded_region_file", "none")
        self.loaded_reg_file_path = None

        # Create column frames to hopefully keep things as even as possible
        fleft = ttk.Frame(self.main_frame)
        fleft.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        fctr = ttk.Frame(self.main_frame)
        fctr.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        fctr.rowconfigure(0, weight=1)
        fright = ttk.Frame(self.main_frame)
        fright.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=8)
        self.main_frame.columnconfigure(2, weight=1)

        # LEFT COLUMN
        """
        # Observation Info Frame
        frame = ttk.LabelFrame(fleft, text="Observer Information")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        frame.columnconfigure(1, weight=1)
        self.observer_names = self.make_db_var(tk.StringVar, "POTN_Observer", "")
        ttk.Label(frame, text="Observer Name(s):").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.observer_names).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.program_id = self.make_db_var(tk.StringVar, "POTN_Program", "")
        ttk.Label(frame, text="Program ID:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.program_id).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.telescope_operator = self.make_db_var(tk.StringVar, "POTN_Telescope_Operator", "")
        ttk.Label(frame, text="Telescope Operator:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.telescope_operator).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        """

        # Filter and Grating Status
        frame = ttk.LabelFrame(fleft, text="Filter and Grating Status")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Filter
        filter_frame = ttk.Label(frame, text="Filter")
        filter_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.filter_data = ascii.read(get_data_file("system", 'SAMOS_Filter_positions.txt'))
        filter_names = list(self.PCM.FILTER_WHEEL_MAPPINGS.keys())
        self.current_filter = self.make_db_var(tk.StringVar, "pcm_filter", filter_names[2])
        self.selected_filter = tk.StringVar(self, value=self.current_filter.get())
        ttk.Label(filter_frame, text="Current Filter:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        l = tk.Label(filter_frame, textvariable=self.current_filter, font=('Georgia 20'), bg='white', fg='green')
        l.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.filter_option_menu = ttk.OptionMenu(filter_frame, self.selected_filter, None, *filter_names)
        self.filter_option_menu.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(filter_frame, text="Set Filter", command=self.set_filter, bootstyle="success")
        b.grid(row=2, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        # Grating
        grating_frame = ttk.Label(frame, text="Grating")
        grating_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        grating_names = list(self.PCM.GRISM_RAIL_MAPPINGS.keys())
        self.grating_positions = list(self.filter_data['Position'][12:18])
        self.current_grating = self.make_db_var(tk.StringVar, "pcm_grating", grating_names[2])
        self.selected_grating = tk.StringVar(self, value=self.current_grating.get())
        ttk.Label(grating_frame, text="Current Grating:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        l = tk.Label(grating_frame, textvariable=self.current_grating, font=('Georgia 20'), bg='white', fg='green')
        l.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.grating_option_menu = ttk.OptionMenu(grating_frame, self.selected_grating, None, *grating_names)
        self.grating_option_menu.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(grating_frame, text="Set Grating", command=self.set_grating, bootstyle="success")
        b.grid(row=2, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # CCD Management
        frame = ttk.LabelFrame(fleft, text="CCD Setup")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        frame.columnconfigure(0, weight=1)
        # Take Image
        acquire_frame = ttk.LabelFrame(frame, text="Acquire")
        acquire_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        acquire_frame.columnconfigure(1, weight=1)
        self.image_type_options = ["Science", "Bias", "Dark", "Flat", "Buffer"]
        self.image_type = self.make_db_var(tk.StringVar, "image_type_set", self.image_type_options[0])
        ttk.Label(acquire_frame, text="Exposure Type:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        m = ttk.OptionMenu(acquire_frame, self.image_type, None, *self.image_type_options, command=self.change_acq_type)
        m.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.image_base_name = self.make_db_var(tk.StringVar, "POTN_Base_Name", "")
        ttk.Label(acquire_frame, text="Base Filename:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(acquire_frame, textvariable=self.image_base_name).grid(row=1, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.image_exptime = self.make_db_var(tk.DoubleVar, "exptime_set", 0.01)
        ttk.Label(acquire_frame, text="Exposure Time (s):").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(acquire_frame, textvariable=self.image_exptime).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.image_expnum = tk.IntVar(self, value=1)
        ttk.Label(acquire_frame, text="Exposure Nr:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.expnum = ttk.Spinbox(acquire_frame, textvariable=self.image_expnum, increment=1, from_=1, to=1000)
        self.expnum.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.image_log = self.make_db_var(tk.BooleanVar, "save_exposures_to_log", True)
        c = tk.Checkbutton(acquire_frame, text="Save to Logbook", variable=self.image_log, onvalue=True, offvalue=False)
        c.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        l = ttk.Label(acquire_frame, text="Correct Quicklook Image For:")
        l.grid(row=5, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        cframe = ttk.Frame(acquire_frame)
        cframe.grid(row=6, column=0, columnspan=2)
        self.ql_bias = self.make_db_var(tk.BooleanVar, "correct_ql_for_bias", True)
        b = tk.Checkbutton(cframe, text='Bias', variable=self.ql_bias, onvalue=True, offvalue=False)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.ql_dark = self.make_db_var(tk.BooleanVar, "correct_ql_for_dark", True)
        b = tk.Checkbutton(cframe, text='Dark', variable=self.ql_dark, onvalue=True, offvalue=False)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.ql_flat = self.make_db_var(tk.BooleanVar, "correct_ql_for_flat", True)
        b = tk.Checkbutton(cframe, text='Flat', variable=self.ql_flat, onvalue=True, offvalue=False)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.ql_buffer = self.make_db_var(tk.BooleanVar, "correct_ql_for_buffer", True)
        b = tk.Checkbutton(cframe, text='Buffer', variable=self.ql_buffer, onvalue=True, offvalue=False)
        b.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        # Image Type Frame
        self.image_frame = ttk.LabelFrame(frame, text=self.image_type.get())
        self.image_frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.image_frame.columnconfigure(1, weight=1)
        self.image_type_label_options = ["Object Name:", "Master Bias:", "Master Dark:", "Master Flat File:", "Master Buffer File:"]
        self.image_label = tk.StringVar(self, self.image_type_label_options[0])
        tk.Label(self.image_frame, textvariable=self.image_label).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.image_name = self.make_db_var(tk.StringVar, "POTN_Target", "")
        tk.Entry(self.image_frame, textvariable=self.image_name).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        ttk.Label(self.image_frame, text="Nr. of Frames:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.image_frames = self.make_db_var(tk.IntVar, "exposure_n_frames", 1)
        tk.Entry(self.image_frame, textvariable=self.image_frames).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        w = ttk.Button(self.image_frame, text="Add Comment to Log", command=self.log_comment)
        w.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.image_save_single = self.make_db_var(tk.BooleanVar, "save_single_frames", False)
        c = tk.Checkbutton(self.image_frame, text="Save Single Frames", variable=self.image_save_single, onvalue=True, offvalue=False)
        c.grid(row=3, column=0, sticky=TK_STICKY_ALL)

        # Take Exposure Frame
        exp_frame = ttk.LabelFrame(frame, text="Take Exposure")
        exp_frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        exp_frame.columnconfigure(0, weight=1)
        exp_frame.columnconfigure(1, weight=1)
        self.start_exp_button = ttk.Button(
            exp_frame, text="START", command=self.start_an_exposure, bootstyle="success"
        )
        self.start_exp_button.grid(
            row=1, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL
        )

        # FITS manager
        frame = ttk.LabelFrame(fleft, text="FITS Manager")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load Existing File", command=self.load_existing_file)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.image_flip_status = tk.BooleanVar(self, value=False)
        c = ttk.Checkbutton(
            frame,
            text="Flip Image",
            variable=self.image_flip_status,
            command=self.toggle_image_flip,
            onvalue=True,
            offvalue=False
        )
        c.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.fits_ra = tk.DoubleVar(self, value=0.)
        ttk.Label(frame, text="Pointed RA:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.fits_ra).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.fits_dec = tk.DoubleVar(self, value=0.)
        ttk.Label(frame, text="Pointed DEC:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.fits_dec).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.fits_nstars = self.make_db_var(tk.IntVar, "twirl_n_stars", 25)
        ttk.Label(frame, text="Number of Stars:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.fits_nstars).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        # Command Buttons
        b = ttk.Button(frame, text="twirl WCS", command=self.twirl_Astrometry)
        b.grid(row=5, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Send to SOAR", command=self.send_offset_to_soar, bootstyle="success")
        b.grid(row=5, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        """
        # QUERY Server
        self.gs_query_frame = GSQueryFrame(self, frame, self.Query_Survey, "target_ra", "target_dec", **self.samos_classes)
        self.gs_query_frame.grid(row=5, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        """
        # Chosen Star Frame
        target_frame = ttk.Frame(frame)
        target_frame.grid(row=6, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.ra_target = tk.DoubleVar(self, value=0.)
        ttk.Label(target_frame, text="Target RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(target_frame, textvariable=self.ra_target, w=6).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.x_offset = self.make_db_var(tk.DoubleVar, "centre_ra_offset_mm", 0.)
        ttk.Label(target_frame, text='dRA"  (+/- move tel. W/E):').grid(row=0, column=2, sticky=TK_STICKY_ALL)
        tk.Entry(target_frame, textvariable=self.x_offset, w=6).grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.dec_target = tk.DoubleVar(self, value=0.)
        ttk.Label(target_frame, text="Target DEC:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(target_frame, textvariable=self.dec_target, w=6).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.y_offset = self.make_db_var(tk.DoubleVar, "centre_dec_offset_mm", 0.)
        ttk.Label(target_frame, text='dDec" (+/- move tel. N/S):').grid(row=1, column=2, sticky=TK_STICKY_ALL)
        tk.Entry(target_frame, textvariable=self.y_offset, w=6).grid(row=1, column=3, sticky=TK_STICKY_ALL)

        # Guide Star Probe Frame
        frame = ttk.LabelFrame(fleft, text="Guide Star Probe Setup!")
        frame.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        # X_GSP00
        self.gs_x0 = tk.DoubleVar(self, 550)
        ttk.Label(frame, text="X GSP00 (pix)").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_x0).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # Y GSP00
        self.gs_y0 = tk.DoubleVar(self, 488)
        ttk.Label(frame, text="Y GSP00 (pix)").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_y0).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Command Show Buttons
        self.show_gsp00 = tk.BooleanVar(self, value=False)
        c = ttk.Checkbutton(
            frame,
            text="Show GSP00",
            variable=self.show_gsp00,
            command=self.toggle_gsp00,
            onvalue=True,
            offvalue=False
        )
        c.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.tag_gsp00 = None

       
        # CENTRE COLUMN

        # GINGA Display
        frame = ttk.LabelFrame(fctr, text="Display")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        # Image Canvas
        canvas = tk.Canvas(frame, bg="grey", width=300, height=300)
        canvas.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        fi = CanvasView(self.logger)
        fi.set_widget(canvas)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        fi.set_enter_focus(True)
        fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        fi.show_mode_indicator(True, corner='ur')
        fi.get_bindings().enable_all(True)
        self.fits_image = fi
        # Drawing Canvas
        self.draw_type = tk.StringVar(self, value="box")
        self.canvas = self.canvas_types.DrawingCanvas()
        self.canvas.enable_draw(True)
        self.canvas.enable_edit(True)
        self.canvas.set_drawtype(self.draw_type.get(), color='red')
        self.canvas.register_for_cursor_drawing(fi)
        self.canvas.add_callback('draw-event', self.draw_cb)
        self.canvas.add_callback('cursor-up', self.examine_source)
        self.canvas.set_draw_mode('draw')
        self.canvas.ui_set_active(True)
        fi.get_canvas().add(self.canvas)
        self.drawtypes = self.canvas.get_drawtypes()
        self.drawtypes.sort()
        self.readout = ttk.Label(frame, text='', font='TkFixedFont')
        self.readout.grid(row=1, column=0, sticky=TK_STICKY_ALL)

        # Ginga Tool Box
        frame = ttk.LabelFrame(fctr, text="Tools")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Early variable definition because it's needed to set an enable condition.
        self.source_pickup_enabled = self.make_db_var(tk.BooleanVar, "source_pickup_enabled", False)
        
        # Slit Configurations
        # Let's see if we can remove the Checkbutton. 
        
        """
        b = tk.Checkbutton(
            frame,
            text="Source Pickup",
            variable=self.source_pickup_enabled,
            command=self.set_slit_drawtype,
            onvalue=True,
            offvalue=False
        )
        
        self.source_pickup_enabled.set(False)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        """
        
        # Buttons
        
        #self.var_show_traces = self.make_db_var(tk.IntVar,"show_remove_traces", False)
        self.var_show_traces = tk.BooleanVar(value=True)
        """
        b = ttk.Button(frame, text="Show Traces", command=self.show_traces)
        b.grid(row=0, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Remove Traces", command=self.remove_traces)
        b.grid(row=0, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        """
        self.var_show_traces.set("False")
        self.button_show_remove_traces = ttk.Button(frame, text="Show Traces", command=self.show_remove_traces)
        self.button_show_remove_traces.grid(row=0, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        
        b = ttk.Button(frame, text="Slits Only", command=self.slits_only)
        b.grid(row=0, column=3, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Clear Canvas", command=self.clear_canvas)
        b.grid(row=0, column=4, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Get <PSF>", command=self.get_PSF)
        b.grid(row=0, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Get ZeroPoint", command=self.get_ZeroPoint)
        b.grid(row=0, column=6, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Centroid Slits", command=self.centroid_slits)
        b.grid(row=0, column=7, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame,text="Find Stars", command=self.find_stars)
        b.grid(row=0, column=8, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # Slit Configuration Frame
        frame = ttk.LabelFrame(fctr, text="Slit Configuration:")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        
        # Slit Size Controls
        slit_frame = ttk.LabelFrame(frame, text="Slit Size")
        slit_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        
        self.slit_xd = self.make_db_var(tk.IntVar, "dmd_hadamard_cross_dispersion", 9)
        ttk.Label(slit_frame, text="Slit Cross Dispersion (mirrors):").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        length_adjust_btn = tk.Spinbox(slit_frame, command=self.slit_width_length_adjust, increment=1, textvariable=self.slit_xd, width=5, 
                        from_=0, to=1080)
        length_adjust_btn.bind("<Return>", self.slit_width_length_adjust)
        length_adjust_btn.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        
        self.slit_disp = self.make_db_var(tk.IntVar, "dmd_hadamard_dispersion", 3)
        ttk.Label(slit_frame, text="Slit Dispersion (mirrors):").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        width_adjust_btn = tk.Spinbox(slit_frame, command=self.slit_width_length_adjust, increment=1, textvariable=self.slit_disp, width=5, 
                        from_=0, to=1080)
        width_adjust_btn.bind("<Return>", self.slit_width_length_adjust)
        
        width_adjust_btn.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        
        self.force_orthonormal = self.make_db_var(tk.BooleanVar, "main_slit_force_orthonormal", False)
        b = tk.Checkbutton(slit_frame, text="Force Orthonormal", variable=self.force_orthonormal, onvalue=True, offvalue=False)
        b.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(slit_frame, text="Apply to All", command=self.apply_to_all, bootstyle="success")
        b.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        
        # Slit Draw Controls
        draw_frame = ttk.LabelFrame(frame, text="Slit Mode")
        draw_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.slit_mode = self.make_db_var(tk.StringVar, "main_draw_mode", "draw")
        self.draw_mode = tk.Radiobutton(draw_frame, text="Draw", variable=self.slit_mode, value="draw", command=self.set_mode_cb)
        self.draw_mode.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.draw_mode = tk.Radiobutton(draw_frame, text="Edit", variable=self.slit_mode, value="edit", command=self.set_mode_cb)
        self.draw_mode.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.draw_mode = tk.Radiobutton(draw_frame, text="Delete", variable=self.slit_mode, value="delete", command=self.set_mode_cb)
        self.draw_mode.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.draw_mode = tk.Radiobutton(draw_frame, text="Pick", variable=self.slit_mode, value="pick", command=self.set_mode_cb)
        self.draw_mode.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Pattern Series
        pattern_frame = ttk.LabelFrame(frame, text="Create Pattern Series with No Overlapping Slits")
        pattern_frame.grid(row=0, column=2, rowspan=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(pattern_frame, text="Generate Patterns", command=self.create_pattern_series_from_traces)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.base_pattern_name = self.make_db_var(tk.StringVar, "dmd_base_pattern", "none")
        e = tk.Entry(pattern_frame, width=15, textvariable=self.base_pattern_name)
        e.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.selected_dmd_pattern = self.make_db_var(tk.StringVar, "dmd_selected_pattern", "none")
        self.pattern_group = ttk.Combobox(pattern_frame, width=25, textvariable=self.selected_dmd_pattern, style="TCombobox")
        self.pattern_group.bind("<<ComboboxSelected>>", self.selected_dmd_group_pattern)
        self.pattern_group.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(pattern_frame, text="Save Displayed Pattern", command=self.save_selected_sub_pattern)
        b.grid(row=1, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(pattern_frame, text="Save All Patterns", command=self.save_all_sub_patterns)
        b.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        
        
        # Buffer  Frame
        credits_frame = ttk.LabelFrame(fctr, text="CREDITS")
        credits_frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Create a StringVar to associate with the label
        text_var = tk.StringVar()
        text_var.set("SAMOS was funded by NSF, STScI and JHU/IDG")

        # Create the label widget with all options
        label = tk.Label(credits_frame, 
                         textvariable=text_var, 
                         anchor=tk.CENTER,       
                         bg="lightblue",      
                         height=3,              
                         width=50,              
                         bd=3,                  
                         font=("Arial", 16, "bold"), 
                         cursor="hand2",   
                         fg="red",             
                         padx=15,               
                         pady=15,                
                         justify=tk.CENTER,    
                         relief=tk.RAISED,     
                         underline=0,           
                         wraplength=250         
                        )
        label.pack()
        
        

        # RIGHT COLUMN

        # RADEC Module
        frame = ttk.LabelFrame(fright, text="Sky Regions (RA, DEC)")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load Regions from DS9/RADEC Region File", command=self.load_regions_radec)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="Loaded Region File:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, textvariable=self.loaded_reg_file).grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Get Target RADEC from Filename", command=self.push_RADEC)
        b.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="OffsetCe SOAR", command=self.send_soar_target, bootstyle="success")
        b.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        l = ttk.Label(frame, text="Point, take and image, and twirl WCS from GAIA")
        l.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Convert DS9 Regions -> Ginga", command=self.load_region_file, bootstyle="success")
        b.grid(row=6, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Save Ginga Regions -> DS9/RADEC Region File", command=self.save_ginga_regions_wcs)
        b.grid(row=7, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # CCD Module
        frame = ttk.LabelFrame(fright, text="CCD Regions (x, y)")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load (x, y) Regions from DS9/xy Region file", command=self.load_regions_pix)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.loaded_ginga_file = self.make_db_var(tk.StringVar, "dmd_loaded_ginga_file", "none")
        self.loaded_ginga_file_path = None
        ttk.Label(frame, text="Loaded File in CCD Units:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, textvariable=self.loaded_ginga_file).grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Save Ginga Regions -> DS9/xy Region File", command=self.save_ginga_regions_pix)
        b.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # DMD Module
        frame = ttk.LabelFrame(fright, text="DMD Slits")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.saved_slit_file = tk.StringVar(self, "")
        self.saved_slit_file_path = None
        b = ttk.Button(frame, text="Send Current Slits to DMD", command=self.push_slit_shape, bootstyle="success")
        b.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Save Slit List", command=self.save_slit_table)
        b.grid(row=1, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="Saved Slit List:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.saved_slit_file).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load and Push Slit List from File", command=self.load_slits)
        b.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.current_slit_file_path = None
        self.current_slit_file = tk.StringVar(self, "")
        ttk.Label(frame, text="Current Slit List:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.current_slit_file).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Convert Slit Regions to Pixels", command=self.draw_slits)
        b.grid(row=4, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)

        # HTS Module
        frame = ttk.LabelFrame(fright, text="HTS")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Load Mask
        self.current_mask_file = tk.StringVar(self, "")
        self.current_mask_file_path = None
        ttk.Label(frame, text="Loaded Mask:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.current_mask_file).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load Mask", command=self.load_masks_file_HTS)
        b.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        # Push Mask
        self.pushed_mask_file = tk.StringVar(self, "")
        ttk.Label(frame, text="Pushed Mask:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.pushed_mask_file).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Push Mask", command=self.push_masks_file_HTS)
        b.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        # Next Mask
        b = ttk.Button(frame, text="Next Mask", command=self.next_masks_file_HTS)
        b.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # Control slit motion
        frame = ttk.LabelFrame(fright, text="Control Slits")
        frame.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        # self.shift_all_slits uses CM.CompoundMixin.move_delta_pt, which takes a single value or tuple argument
        # If single value is passed, the move occurs as if (VAL, VAL) was passed.
        # For here:
        #     left arrow triggers shift of (-VAL, 0)
        #     right arrow triggers shift of (+VAL, 0)
        #     up arrow triggers shift of (0, +VAL)
        #     down arrow triggers shift of (0, -VAL)
        self.shift_value = self.make_db_var(tk.IntVar, "slit_shift_size", default=1)
        w = ttk.Label(frame, text="Shift Size (px)")
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Entry(frame, textvariable=self.shift_value)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="⬅️", command=partial(self.shift_all_slits, "left"))
        b.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="➡️", command=partial(self.shift_all_slits, "right"))
        b.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="⬆️", command=partial(self.shift_all_slits, "up"))
        b.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="⬇️", command=partial(self.shift_all_slits, "down"))
        b.grid(row=3, column=1, sticky=TK_STICKY_ALL)

        # Status Indicator Frame
        frame = ttk.LabelFrame(fright, text="STATUS")
        frame.grid(row=6, column=0, sticky=TK_STICKY_ALL)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.status_box = tk.Canvas(frame, background="gray")
        self.status_box.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.status_box.create_oval(20, 20, 60, 60, fill=INDICATOR_LIGHT_ON_COLOR, outline=None, tags=["filter_ind"])
        self.status_box.create_text(40, 70, text="Filters")
        self.status_box.create_oval(100, 20, 140, 60, fill=INDICATOR_LIGHT_ON_COLOR, tags=["grism_ind"], outline=None)
        self.status_box.create_text(120, 70, text="Grisms")
        # indicator for mirror and SOAR TCS applicable at telescope
        self.status_box.create_oval(170, 20, 210, 60, fill=INDICATOR_LIGHT_OFF_COLOR, tags=["mirror_ind"], outline=None)
        self.status_box.create_text(190, 70, text="Mirror")
        self.status_box.create_oval(240, 20, 280, 60, fill=INDICATOR_LIGHT_OFF_COLOR, tags=["tcs_ind"], outline=None)
        self.status_box.create_text(260, 70, text="TCS")
        # Register the frame with PAR
        # Give the PCM class a copy of the status box so that it can set colours as well.
        self.PCM.initialize_indicator(self.status_box)


        self.set_mode_cb()
        self.set_enabled()
        self._set_expnum()
        # Start out displaying an empty file
        # ***** Removed because it doesn't end up working, for unknown reasons.
#         self.Display(get_data_file("system", "blank.fits").as_posix())


    @check_enabled
    def send_soar_target(self):
        """
        Send the current target (as obtained from the regions file) to SOAR.
        """
        target_ra = float(self.ra_target.get())
        target_dec = float(self.dec_target.get())
        if self.SOAR.is_on == True:
            return_message_from_TCS =  self.SOAR.target(ra=target_ra, dec=target_dec)
            self.logger.info(return_message_from_TCS)
        else:
            self.logger.warning("TCS is not active")
        

    @check_enabled
    def send_offset_to_soar(self):
        if self.SOAR.is_on == True:
            d_ra = self.x_offset.get()
            d_dec = self.y_offset.get()
            message = { "offset_ra": float(d_ra), "offset_dec": float(d_dec) }
            return_message_from_TCS =  self.SOAR.offset(message)
            self.logger.info(return_message_from_TCS)
        else:
            self.logger.warning("TCS is not active")


    @check_enabled
    def save_ginga_regions_pix(self):
        """
        Save regions defined on the current canvas (and thus in Ginga (x, y) co-ordinates)
        to an astropy regions (.reg) file. This requires converting the region co-ordinates
        (using the Ginga utilities).
        """
        self.logger.info("Saving Canvas Regions to Astropy File (pixel format)")
        
        #remove regions (slit boxes) that have xradius=0, i.e. single clicks on the canvas
        for r in ginga_regions:
            if r.xradius == 0:
                objects_to_remove.append(r)
        CM.CompoundMixin.delete_objects(self.canvas, objects_to_remove)
        
        ginga_regions = CM.CompoundMixin.get_objects(self.canvas)
        astropy_regions_pix = Regions([g2r(r) for r in ginga_regions])
        #
        #SORT THE REGIONS AND CREATE THE EVEN/ODD LISTS
        sorted_regions = sorted(astropy_regions_pix, key=lambda region: region.center.x)
        odd_regions = []
        even_regions = []
        for i, region in enumerate(sorted_regions):
            # Select every second region (even index)
            if i % 2 == 0:
                even_regions.append(region)
            if i % 2 == 1:
                 odd_regions.append(region)
        #
        #CREATE THE FILE NAMES FOR OUTPUT
        #
        #The directory SHOULD BE the PIXELS directory in the last opened RegionFiles folder
        try:
            self.dir_regions_pixels = os.path.join( str(self.loaded_reg_file_path.parent),
                                                   "../PIXELS")   
        #
        except: 
            self.dir_regions_pixels = tk.filedialog.askdirectory(
                    title = 'Select the target folder for saving records',
                    initialdir=get_data_file("regions.radec") )#, 
#                    filetypes=(("Text files", "*.reg"), ("all files", "*.*")))
            
        #create it if it does not exist
        Path(self.dir_regions_pixels).mkdir(parents=True, exist_ok=True)
        #
        
        # IF EXISTS
        #the current mask name is in the variable self.loaded_reg_file_path.name, e.g. 
        # 'RMC 136-T00_RADEC=84.6787022-69.1007396.reg'
        try: 
            file_name = self.loaded_reg_file_path.name
            #and we use the target name self.target_name, e.g. 'RMC 136-T00'        
            # 1) We insert "PIXEL" in the global astropy region pix
            file_name_pixel  = self.target_name+"_PIXEL="+file_name[file_name.find("RADEC=")+6:file_name.find(".reg")]
        
            save_file = tk.filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                            defaultextension=".reg",
                                            initialfile = file_name_pixel,
                                            #initialdir=get_data_file("regions.pixels"))
                                            initialdir= self.dir_regions_pixels)
            #astropy_regions_pix.write(save_file.name, overwrite=True)
            #self.logger.info("Saved regions to {}".format(save_file.name))
            
            #save_file = os.path.join(self.dir_regions_pixels,
            #                         self.target_name+"_PIXEL_EVEN="+file_name[file_name.find("RADEC=")+6:file_name.find(".reg")]+".reg")
            
            # 2) We insert "PIXEL_EVEN" in the global astropy region pix
            save_file_even = os.path.join(self.dir_regions_pixels,
                                     self.target_name+"_PIXEL_EVEN="+file_name[file_name.find("RADEC=")+6:file_name.find(".reg")]+".reg")
            #Regions(even_regions).write(save_file_even, overwrite=True)
            #self.logger.info("Saved Even regions to {}".format(save_file_even))
            
            # 3) We insert "PIXEL_ODD" in the global astropy region pix 
            save_file_odd = os.path.join(self.dir_regions_pixels,
                                     self.target_name+"_PIXEL_ODD="+file_name[file_name.find("RADEC=")+6:file_name.find(".reg")]+".reg")
            #Regions(odd_regions).write(save_file_odd, overwrite=True)
            #self.logger.info("Saved Even regions to {}".format(save_file_odd))
        
            #IF DOES NOT EXIST (SLITS CREATED ON THE FLY, FIRST TIME BEFORE LOADING REG FILE, ETC...)
        except:
            from tkinter.simpledialog import askstring
            from tkinter.messagebox import showinfo
            file_name_pixel = askstring('Missing File Name', 'Enter file Name?')
            showinfo('Hello!', 'Entered, {}'.format(file_name_pixel))
            
            save_file = tk.filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                            defaultextension=".reg",
                                            initialfile = file_name_pixel,
                                            #initialdir=get_data_file("regions.pixels"))
                                            initialdir= self.dir_regions_pixels)
            # 2) We insert "PIXEL_EVEN" in the global astropy region pix
            endname = save_file.name.find(".reg")
            save_file_even = os.path.join(save_file.name[:endname]+"_EVEN.reg")
            # 3) We insert "PIXEL_ODD" in the global astropy region pix 
            save_file_odd = os.path.join(save_file.name[:endname]+"_ODD.reg")

        astropy_regions_pix.write(save_file.name, overwrite=True)
        self.logger.info("Saved regions to {}".format(save_file.name))        
        
        Regions(even_regions).write(save_file_even, overwrite=True)
        self.logger.info("Saved Even regions to {}".format(save_file_even))
            
        Regions(odd_regions).write(save_file_odd, overwrite=True)
        self.logger.info("Saved Even regions to {}".format(save_file_odd))
       



    @check_enabled
    def save_ginga_regions_wcs(self):
        """ 
        As above but save to ra/dec (WCS-enabled) regions instead of pixel-on-image regions.
        
        Requires
        --------
        - valid WCS
        """
        self.logger.info("Saving Canvas Regions to Astropy File (RADEC format)")
        
        #if we have already loaded a RADEC region file, we save the variant we created on the same directory
        #otherwise we save whatever we have created in the default "regions.radec" folder
        try:
            self.loaded_reg_file_path
            RADEC_region_dir = self.loaded_reg_file_path.parent
            RADEC_filename = self.loaded_reg_file_path.name
        except:
            RADEC_region_dir = get_data_file("regions.radec")
            RADEC_filename = ""
            
        self.logger.info("Saving Canvas Regions to Astropy File (WCS format)")
        save_file = tk.filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                                defaultextension=".reg",
                                                initialfile = RADEC_filename,
                                                #initialdir=get_data_file("regions.radec"))
                                                initialdir=RADEC_region_dir)
        
        ginga_regions = CM.CompoundMixin.get_objects(self.canvas)
        astropy_regions_pix = Regions([g2r(r) for r in ginga_regions])
        astropy_regions_wcs = Regions([r.to_sky(self.PAR.wcs) for r in astropy_regions_pix])

        #Oct.1, 2025, mr- corrected filename 
        astropy_regions_wcs.write(save_file.name, overwrite=True)
        self.logger.info("Saved regions to {}".format(save_file.name))


    @check_enabled
    def load_region_file(self):
        """ 
        converting ds9/radec Regions to AP/radec Regions
        - open the already exisitng ds9/radec region list and convert to AP/xy (aka RRR_xyAP)
        - convert AP/xy to Ginga/xy (aka RRR_xyGA)
        - convert AP/xy to AP/ad (aka RRR_RADec)
        
        Requires
        --------
        - valid WCS
        - Region File
        """
        self.logger.info("Displaying DS9 Region File on canvas")
        #astropy_regions_wcs = Regions.read(self.loaded_reg_file_path, format='ds9') #=ASSUME ALREADY LOADED
        #astropy_regions_pix = Regions([r.to_pixel(self.PAR.wcs) for r in astropy_regions_wcs])
        astropy_regions_pix = Regions([r.to_pixel(self.PAR.wcs) for r in self.loaded_astropy_regions])
        #self.logger.info("Loaded file {}".format(self.loaded_reg_file_path))
        ginga_regions = self.convert_astropy_to_ginga_pix(astropy_regions_pix, tag="slit")
        self.logger.info("Converted Astropy pixel regions to Ginga")
#         if self.slit_tab_view is None:
#             self.initialize_slit_table()
        #self.slit_tab_view.load_table_from_regfile_RADEC(regs_RADEC=astropy_regions_wcs, img_wcs=self.PAR.wcs)
        #self.logger.info("Finished displaying regions and loading slit tab view")


    @check_enabled
    def draw_slits(self):
        """
        Takes a slit list (.csv file with each row defining a region in slit space), uses
        the current DMD-to-CCD mapping to convert it to a list of regions in pixel space,
        and adds those regions to the canvas.
        
        Requires
        --------
        - Slit file must exist
        """
        box_tool = self.drawing_canvas.get_draw_class('Box')
        with open(current_slit_file_path, 'r') as file:
            csv_file = csv.reader(file)
            for i, row in enumerate(csv_file):
                dmd_row = [int(x) for x in row]
                x0, y0 = dmd_to_ccd(dmd_row[0], dmd_row[2], self.PAR.dmd_wcs)
                x1, y1 = dmd_to_ccd(dmd_row[1], dmd_row[3], self.PAR.dmd_wcs)
                # For a box, we need centre, width, and height
                box_x = (x0 + x1) / 2
                box_y = (y0 + y1) / 2
                box_w = (x1 - x0)
                box_h = (y1 - y0)
                obj = box_tool(box_x, box_y, box_w, box_h, color='red')
                self.canvas.add(obj, tag='@slit_{}'.format(i))
                
                
    def centroid_slits(self):
        from photutils.centroids import centroid_2dg, centroid_sources, centroid_com, centroid_1dg,centroid_quadratic
        """
        #let's refine the centering of the slit
        #consider working on the full gaia g list
        #gaias = twirl.gaia_radecs(center, fov, circular=False)
        """
        #We know the regions
        ginga_regions = CM.CompoundMixin.get_objects(self.canvas)
        
        #We know the image
        with fits.open(self.fits_image_ql) as hdul:
            data = hdul[0].data

        #We loop over the regions         
        box_size = 21
        for i in range(len(ginga_regions)):
            #We may have slits out of the field. Ignore then
            if (ginga_regions[i].x < 10) or (ginga_regions[i].x > (data.shape[1]-10)) or (ginga_regions[i].y < 10) or ginga_regions[i].y > (data.shape[0]-10):
                self.logger.info(f'skipping slit {i} out of the field')
                continue
            
            
            px1,py1 = centroid_sources(data, ginga_regions[i].x, ginga_regions[i].y, box_size = box_size,
                       centroid_func=centroid_quadratic)#1dg)#com)   
            # check if the solution is acceptable
            if np.sqrt( (px1.item() - ginga_regions[i].x)**2 + (py1.item() - ginga_regions[i].y)**2) < box_size:
                self.logger.info(f"Adjusting slit {i} from {ginga_regions[i].x:.2f},{ginga_regions[i].y:.2f} to {px1.item():.2f},{py1.item():.2f}")
                ginga_regions[i].move_to_pt([px1.item(),py1.item()])
                ginga_regions[i].color = 'blue'
                self.canvas.redraw()
                #do the substitution
                #obj = ginga_regions[i]
                #self.canvas.delete_object(ginga_regions[i])
                #self.canvas.add(obj, tag='@slit_{}'.format(i))
                #self.logger.info(f"Adjusting slit {i} from {ginga_regions[i].x:.2f, ginga_regions[i].y} to {px1.item(),py1.item()}")
            else:
                continue
        self.logger.info("All slits checked for centroid")
                
            


    @check_enabled
    def convert_astropy_to_ginga_pix(self, regions, tag='loaded'):
        """ 
        converting (x,y) Astropy Regions to (x,y) Ginga Regions
        
        Requires
        --------
        None
        """
        self.logger.info("Converting Astropy pixel regions to Ginga")
        ginga_objects = []
        for i, astropy_region in enumerate(regions):
            ginga_object = r2g(astropy_region)
            ginga_object.pickable = True
            ginga_object.add_callback('pick-down', self.pick_cb, 'down')
            ginga_object.add_callback('pick-up', self.pick_cb, 'up')
            ginga_object.add_callback('pick-key', self.pick_cb, 'key')
            ginga_object.add_callback('pick-move', self.pick_cb, 'move')
            ginga_object.add_callback('edited', self.edit_cb)
            ginga_objects.append(ginga_object)
            self.canvas.add(ginga_object, tag='@{}_{}'.format(tag, i))
        return ginga_objects


    @check_enabled
    def push_RADEC(self):
        """
        Load canvas RA/DEC from entries
        """
        self.fits_ra.set(self.ra_target.get())
        self.fits_dec.set(self.dec_target.get())


    @check_enabled
    def load_regions_radec(self):
        """ 
        Read (RA,DEC) Regions from .reg file
        - open ds9/ad file and read the regions files creating a AP/ad list of regions (aka RRR_RADec)
        - extract center RA, Dec
        
        Requires
        --------
        None
        """
        self.logger.info("Loading Region File")
        reg_file = tk.filedialog.askopenfilename(initialdir=get_data_file("regions.radec"), title="Select a File",
                                                 filetypes=(("Text files", "*.reg"), ("all files", "*.*")))
        self.loaded_reg_file_path = Path(reg_file)
        file_name = self.loaded_reg_file_path.name
        self.loaded_reg_file.set(file_name)
        initial_regions = Regions.read(self.loaded_reg_file_path, format='ds9')
        astropy_regions_radec = Regions()
        for region in initial_regions:
            if region not in astropy_regions_radec:
                astropy_regions_radec.append(region)
        self.target_name = file_name[:file_name.find("_")]
        self.db.update_value("POTN_Target", self.target_name)
        if self.image_type.get() == "Science":
            self.image_name.set(self.target_name)
        if "RADEC=" in file_name:
            radec_str = file_name
             # FIXED THIS LINE BECAUSE WAS NOT READING PROPERLY THE RADEC STRING [MR]
            #radec_str = radec_str[radec_str.find("RADEC=")+6:max([i for i,s in enumerate(str) if s.isdigit()])+1]
            radec_str = radec_str[radec_str.find("RADEC=")+6:radec_str.find(".reg")]
            if "-" in radec_str:
                str_items = radec_str.split("-")
                dec_factor = -1.
            elif "+" in radec_str:
                str_items = radec_str.split("+")
                dec_factor = 1.
            ra = float(str_items[0])
            dec = float(str_items[1]) * dec_factor
            self.ra_target.set(ra)
            self.dec_target.set(dec)
        self.loaded_astropy_regions = astropy_regions_radec


    @check_enabled
    def load_regions_pix(self):
        """ 
        read (x,y) Astropy  Regions from ds9 .reg file
        - open ds9 .reg file in pixels units
        - extract the clean filename to get RA and DEC of the central point
        - create AP.xy regions
        - visualize xyAP regions on GINGA display\n
        - convert xyAP regions to GINGA regions
        
        Requires
        --------
        - Valid WCS
        """
        
        self.logger.info("Loading DS9 pixel region file to Astropy Pixels")
        
        #cleanup the canvas
        self.delete_all()
                        
        reg_file = tk.filedialog.askopenfilename(
            filetypes=[("region files", "*.reg")],
            initialdir=get_data_file("regions.pixels")
        )
        self.loaded_ginga_file_path = Path(reg_file)
        self.loaded_ginga_file.set(self.loaded_ginga_file_path.name)
        
        initial_regions = Regions.read(self.loaded_ginga_file_path, format="ds9")
        astropy_regions_pix = Regions()
        for region in initial_regions:
            if region not in astropy_regions_pix:
                astropy_regions_pix.append(region)
        ginga_regions = self.convert_astropy_to_ginga_pix(astropy_regions_pix)
        
        #inserting a "slit" object ta needed e.g. to show trace
        counter = 0
        for object in ginga_regions:
            object.tag = '@slit_{}'.format(str(counter))
            print(object.tag)
            counter+=1
            
        self.loaded_ginga_regions = ginga_regions    
        #obj.tag = '@slit_{}'.format(obj.tag)
#         if self.slit_tab_view is None:
#             self.initialize_slit_table()
#         self.slit_tab_view.load_table_from_regfile_CCD(regs_CCD=astropy_regions_pix, img_wcs=self.PAR.wcs)

    @check_enabled
    def collect_slit_shape(self):
        """
        collect selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        self.logger.info("Collecting Slit")
        slit_regions = []
        objects = CM.CompoundMixin.get_objects(self.canvas)
        self.logger.info(f"Collected Nr. {len(objects)} slits")
        try:
            pattern_index = self.pattern_group.current()
            current_pattern = self.pattern_series[pattern_index]
            self.logger.info(f"Current Selected Pattern: {current_pattern} ({pattern_index})")
            current_pattern_tags = ["@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]
            objects = [self.canvas.get_object_by_tag(tag) for tag in current_pattern_tags]
        except Exception as e:
            self.logger.error("Exception while retrieving pattern group")
            self.logger.error("Reported error: {}".format(e))
        self.logger.info("Looping through ginga objects")
        slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for obj in objects:
            # force Orthonormal orientation if checkbox is set
            # This function is called if a checkbox forces the slits to be Orthonormal on the DMD. 
            # This is intended to havoid having slightly diagonal slits when the position angle of the image is not exactly 
            # oriented with the celestial coordinates
            if self.force_orthonormal.get() == 1:
                obj.rot_deg = 0.0
            ccd_x0, ccd_y0, ccd_x1, ccd_y1 = obj.get_llur()
            # first case: figures that have no extensions (i.e. points): do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1, y1 = ccd_to_dmd(ccd_x0, ccd_y0, self.PAR.dmd_wcs)
                x1, y1 = int(np.round(x1)), int(np.round(y1))
                slit_shape[x1, y1] = 0
                slit_regions.append([ccd_x0, ccd_x1+1, ccd_y0, ccd_y1+1])
            elif self.source_pickup_enabled.get() and obj.kind == 'point':
                x1, y1 = ccd_to_dmd(ccd_x0, ccd_y0, self.PAR.dmd_wcs)
                x1, y1 = int(np.floor(x1)), int(np.floor(y1))
                x2, y2 = ccd_to_dmd(ccd_x1, ccd_y1, self.PAR.dmd_wcs)
                x2, y2 = int(np.ceil(x2)), int(np.ceil(y2))
                slit_regions.append([ccd_x0, ccd_x1+1, ccd_y0, ccd_y1+1])
            else:
                print("generic aperture")
                # 3 load the slit pattern
                try:
                    data_box = self.AstroImage.cutout_shape(obj)
                except Exception as e:
                    self.logger.error(f"Unable to compute cutout shape at ({ccd_x0, ccd_y0}), ({ccd_x1}, {ccd_y1})")
                    continue
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                # paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion
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
                    x1, y1 = ccd_to_dmd(cx0, cy0, self.PAR.dmd_wcs)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = ccd_to_dmd(cx0, cy1, self.PAR.dmd_wcs)  # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    slit_shape[x1-2:x1, y1-2:y2+1] = 1
                    slit_regions.append([cx0, cx0+1, cy0, cy0+1])
                # paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion
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
                    x1, y1 = ccd_to_dmd(cx0, cy0, self.PAR.dmd_wcs)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = ccd_to_dmd(cx1, cy0, self.PAR.dmd_wcs)  # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    slit_shape[x1-2:x1, y1-2:y1] = 1
                    slit_regions.append([cx0, cx1+1, cy0, cy0+1])
        return slit_shape, slit_regions


    @check_enabled
    def push_slit_shape(self):
        """
        push selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        self.logger.info("Pushing slit shape to DMD")
        self.remove_traces()
        slit_shape, slit_regions = self.collect_slit_shape()
        self.push_slits(slit_shape)
        region_name = f"{self.image_name.get()}_{self.image_expnum.get():04d}"
        region_name += f"_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}_pix.reg"
        region_name = region_name.replace(" ", "_")
        
        #The following lines create a directory in /src/samos/data/tmp/SISI_images 
        #to store the loaded mask.
        if not self.PAR.fits_dir.is_dir():
            self.logger.info(f"Creating FITS directory {self.PAR.fits_dir} for tonight")
            self.PAR.fits_dir.mkdir(parents=True, exist_ok=True)

        region_file = self.PAR.fits_dir / region_name
        ginga_regions = CM.CompoundMixin.get_objects(self.canvas)
        astropy_regions_pix = Regions([g2r(r) for r in ginga_regions])
        astropy_regions_pix.write(region_file.as_posix(), overwrite=True)
        region_file = get_data_file("regions.pixels") / region_name
        astropy_regions_pix.write(region_file.as_posix(), overwrite=True)
                

    @check_enabled
    def push_slits(self, slit_shape):
        """ Actual push of the slit_shape to the DMD """
        self.logger.info("Applying slit shape to DMD")
        self.DMD.initialize()
        self.DMD._open()
        self.DMD.apply_shape(slit_shape)


    @check_enabled
    def shift_all_slits(self, shift_direction):
        shift_magnitude = self.shift_value.get()

        if shift_direction == "left":
            shift = (-shift_magnitude, 0)
        elif shift_direction == "right":
            shift = (shift_magnitude, 0)
        elif shift_direction == "up":
            shift = (0, shift_magnitude)
        elif shift_direction == "down":
            shift = (0, -shift_magnitude)

        self.logger.info(f"Shifting all slits by {shift}")
        self.slits_only()
        CM.CompoundMixin.move_delta_pt(self.canvas, off_pt=shift)
        self.canvas.redraw()


    @check_enabled
    def set_filter(self):
        self.logger.info("Setting Filter to {}".format(self.current_filter.get()))
        new_filter = self.selected_filter.get()
        self.main_fits_header.set_param("filter", new_filter)
        filter_pos = self.PCM.FILTER_WHEEL_MAPPINGS[new_filter.lower()]
        self.main_fits_header.set_param("filtpos", f"{filter_pos[0]},{filter_pos[1]}")
        command_status = self.PCM.move_filter_wheel(new_filter)
        self.logger.info("Motors returned {}".format(command_status))
        self.extra_header_params += 1
        entry_string = PARAM_ENTRY_FORMAT.format(
            self.extra_header_params,
            'String',
            'FILTER',
            new_filter,
            'Selected filter'
        )
        self.header_entry_string += entry_string
        self.current_filter.set(self.selected_filter.get())


    @check_enabled
    def set_grating(self):
        self.logger.info("Setting Grating to {}".format(self.current_grating.get()))
        new_grating = self.selected_grating.get()
        self.main_fits_header.set_param("grating", new_grating)
        grating_pos = self.PCM.GRISM_RAIL_MAPPINGS[new_grating.lower()]
        self.main_fits_header.set_param("gratpos", f"{grating_pos[0]},{grating_pos[1]}")
        command_status = self.PCM.move_grism_rails(new_grating)
        self.logger.info("Motors returned {}".format(command_status))
        self.extra_header_params += 1
        entry_string = PARAM_ENTRY_FORMAT.format(self.extra_header_params, 'String', 'GRISM', new_grating, 'Grism position')
        self.header_entry_string += entry_string
        self.current_grating.set(self.selected_grating.get())


    @check_enabled
    def set_drawparams(self, evt):
        """
        Check and update user drawing
        """
        params = {
            'color': self.draw_color.current(),
            'alpha': self.draw_alpha.get(),
            }
        if self.draw_type.get() in ('circle', 'rectangle', 'polygon', 'triangle', 'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = self.draw_fill.get() != 0
            params['fillalpha'] = params['alpha']
        self.canvas.set_drawtype(kind, **params)


    @check_enabled
    def clear_canvas(self):
        self.canvas.delete_all_objects(redraw=True)
        self.tag_gsp00 = None
        self.toggle_gsp00()

    """ NO FLIP IMAGE
    @check_enabled
    def set_image_flip(self):
        if hasattr(self, "AstroImage"):
            title = "Flip Current Image?"
            message = "Flip the current image?"
            if tk.messagebox.askyesno(title=title, message=message):
                data = self.AstroImage.get_data()
                transformed_data = np.fliplr(data)
                self.AstroImage.set_data(transformed_data)
    """
    @check_enabled
    def get_PSF(self):
        """ ta routine to analyze the current image and extract average
            photometric information, in particular the PSF
            Created October 14, 2024
        """
        self.Display(self.fits_image_ql)
        with fits.open(self.fits_image_ql) as fits_file:
            hdu = fits_file[0]
            data = hdu.data
            
        # Let's find some stars and display the image
        self.clear_canvas()
        
        "why do we care about SDSS_stars?"
        #check first if it exist, as we may have not yet queried SDSS   
        try:  
            if self.SDSS_stars is None:  #if it exist but is none, we just check the current image
                stars = twirl.find_peaks(data)[0:self.fits_nstars.get()]
            else: #if it exist, we are coming from SDSS and therefore we use the SDSS stars
                import copy
                stars = copy.deepcopy(self.SDSS_stars)
                #SDSS_stars = None  #and immediately delete them so we are free for the next searh
        except:  #if self.SDSS has never been created, we go to the basic search
             stars = twirl.find_peaks(data)[0:self.fits_nstars.get()]
    
        "display"
        xs=stars[:,0]
        ys=stars[:,1]
        radius_pix = 7
    
        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                   for x, y in stars]  # [(1, 2), (3, 4)]]
        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
            obj.color="red"
            self.canvas.add(obj)
        fwhm_x=[]
        fwhm_y=[]
        for i in range(len(xs)):
            #print(xs[i],ys[i])
            horizontal, vertical = self.profiles(data, xs[i], ys[i])
            fwhm_xi = self.interpolate_width(horizontal)
            fwhm_yi = self.interpolate_width(vertical)
            if fwhm_xi <1  or fwhm_yi<1:
                continue
            #print([i,fwhm_xi,fwhm_yi])
            fwhm_x.append(fwhm_xi)
            fwhm_y.append(fwhm_yi)    
            region = CirclePixelRegion(center=PixCoord(xs[i], ys[i]), radius=radius_pix)
            obj = r2g(region)
            obj.color="blue"
            self.canvas.add(obj)
        #print(fwhm_x,'n',fwhm_y,'\n')    
        self.logger.info("           Mean      Median     std")
        self.logger.info(f"FWHM_x:   {np.mean(fwhm_x):6.3f},   {np.median(fwhm_x):6.3f},   {np.std(fwhm_x):6.3f}")
        self.logger.info(f"FWHM_y:   {np.mean(fwhm_y):6.3f},   {np.median(fwhm_y):6.3f},   {np.std(fwhm_y):6.3f}")
        self.logger.info(f"FWHM values calculated using {len(fwhm_x)} stars")
        summary_psf_mean = np.mean([np.mean(fwhm_x),np.mean(fwhm_y)]) * 0.184
        summary_psf_median = np.mean([np.median(fwhm_x),np.median(fwhm_y)]) *0.184
        summary_psf_std = np.mean([np.std(fwhm_x),np.std(fwhm_y)]) * 0.184
        
        tk.messagebox.showinfo(title="PSF", message=(f"PSF: Mean={summary_psf_mean:.2f}, Median={summary_psf_median:.2f}, StDev=={summary_psf_std:.2f} arcsec"))
        return(np.mean(fwhm_x),np.mean(fwhm_y))

    def profiles(self,image,xpix, ypix):
        """ancillary function called by get_PSF to extract the horizontal and vertical profiles of a star"""
        xpix = round(xpix)
        ypix = round(ypix)
        #print(image[ypix,xpix])
        x = np.take(image, ypix, axis=0)[xpix-16:xpix+15]
        y = np.take(image, xpix, axis=1)[ypix-16:ypix+15]
        #print(len(x))
        x=x/max(x)
        y=y/max(y)
        #print(x)
        return x, y #these are the horizontal and vertical profiles through the star's centroid

    def interpolate_width(self,axis):
        """ second ancillary function called by get_PSF to interpolate the FWHM of a star"""
        half_max = 1/2
        # Do the interpolation
        spline = UnivariateSpline(np.arange(0,31),axis-half_max, s=0)
        r = spline.roots()
        if len(r) != 2:
            return 0
        else: 
            r1, r2 = r#spline.roots()
            return r2-r1 #this is the FWHM along the specified axis

    @check_enabled
    def start_an_exposure(self):
        """ 
        This is the landing procedure after the START button has been pressed
        """
        #CHECK TO AVOID LONG EXPOSURES BY ERROR
        duration = self.image_exptime.get() * self.image_frames.get()
        if duration > 60:
            if tk.messagebox.askyesno(title="Time Check", message="exposure longer than 60s. Continue?"):
                self.logger.info(f"Starting Exposure")
            else:
                return
                
        
        try:
            if not self.PAR.fits_dir.is_dir():
                self.logger.info(f"Creating FITS directory {self.PAR.fits_dir} for tonight")
                self.PAR.fits_dir.mkdir(parents=True, exist_ok=True)
            status = self.db.get_value("config_ip_status", default="disconnected")
            if (not self.CCD.initialized) or (not self.CCD.ccd_on) or (status == "disconnected"):
                # Open a test image
                initial_dir = self.db.get_value(
                    "config_science_targets_dir", default=Path.cwd().as_posix()
                )
                image_to_open = tk.filedialog.askopenfilename(
                    initialdir=initial_dir,
                    filetypes=[("fitsfiles", "*.fits"), ("allfiles", "*")]
                )
                input_image = Path(image_to_open)
                if input_image.is_file():
                    output_name = f"sample_{self.image_expnum.get():04d}_.fits"
                    image_output = self.PAR.fits_dir / output_name
                    image_output.write_bytes(input_image.read_bytes())
                    self.Display(image_output.as_posix())
                    self._set_expnum()
                return
            exposure_params = {
                'file_number': self.image_expnum.get(),
                'exptime': self.image_exptime.get() * 1000,  # ms
                'exp_frames': self.image_frames.get(),
                'image_name': self.image_name.get(),
                'image_type': self.image_type.get(),
                'filter': self.current_filter.get(),
                'grating': self.current_grating.get(),
                'sub_bias': self.ql_bias.get() == 1,
                'sub_dark': self.ql_dark.get() == 1,
                'sub_flat': self.ql_flat.get() == 1,
                'sub_buffer': self.ql_buffer.get() == 1,
                'save_individual': self.image_save_single.get() == 1,
                
            }
            #are we observing a new target? BCS we may haave lost the WCS solution
            if self.image_name.get() !=  self.previous_image_name:
                # yes,  we changed the target
                # therefore we lost the WCS solution
                self.PAR.valid_wcs = False
                self.previous_image_name = self.image_name.get()
            if self.image_type.get() == "Dark":
                # By default, subtract the bias in the quicklook
                self.ql_bias.set(1)
            elif self.image_type.get() == "Flat":
                # By default, subtract bias and dark
                self.ql_bias.set(1)
                self.ql_dark.set(1)

            self.start_exp_button.configure(state="disabled")
            exp_window = ExposureProgressWindow(
                self,
                self.CCD,
                self.PAR,
                self.db,
                self.main_fits_header,
                self.DMD,
                self.logger
            )
            exp_window.start_exposure(self.image_type.get(), **exposure_params)
        finally:
            self._set_expnum()


    @check_enabled
    def display_exposure(self, results):
        self.handle_log(results["images"])
        self.Display(results["superfile"].as_posix())
        self.fits_image.rotate(self.PAR.Ginga_PA)
        self._set_expnum()
        self.image_flip_status.set(False)
        self.toggle_image_flip()


    @check_enabled
    def toggle_image_flip(self):
        """
        Flip or un-flip the image X axis.
        """
        self.canvas.viewer.transform(self.image_flip_status.get(), False, False)


    @check_enabled
    def log_comment(self):
        """
        Gets the comment and adds it to the logbook.
        """
        if not self.PAR.logbook_exists:
            self.PAR.create_log_file()

        user_comment = Querybox.get_string(
            title="Comment", prompt="Enter Comment for Log:", parent=self
        )

        with open(self.PAR.logfile_name, 'a') as logbook:
            today = datetime.now()
            logbook.write(f"{today.strftime('%Y-%m-%d')},{today.strftime('%H:%M:%S')},")
            logbook.write(f"{user_comment}\n")


    @check_enabled
    def handle_log(self, newfiles):
        """ 
        handles the writeup of an entry line in the loogbook
        """
        #1) Do we want to write?
        if self.image_log.get() != 1:
            return

        # Create the logbook if it doens't exist
        if not self.PAR.logbook_exists:
            self.PAR.create_log_file()

        # now open logfile to write the writeup
        with open(self.PAR.logfile_name, 'a') as logbook:
            today = datetime.now()
            for file in newfiles:
                file_name = Path(file).name
                logbook.write(f"{today.strftime('%Y-%m-%d')},time.strftime('%H:%M:%S', self.start_time),")
                logbook.write(f"{self.db.get_value('POTN_Target')},{self.current_filter.get()},{len(newfiles)},")
                logbook.write(f"{self.image_exptime.get()},{file_name}\n")


    @check_enabled
    def change_acq_type(self, event):
        """
        When the acquisition tab is changed
        """
        self.image_frame.configure(text=self.image_type.get())
        self.image_label.set(self.image_type_label_options[self.image_type_options.index(self.image_type.get())])


    @check_enabled
    def Display(self, imagefile):
        """
        Display the raw image arrived  from SAMI, still with the original Spectral Instruments FITS header""

        Parameters
        ----------
        imagefile : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.AstroImage = load_data(imagefile, logger=self.logger)
        self.fits_image.set_image(self.AstroImage)
        self.fits_image_ql = imagefile


    @check_enabled
    def load_existing_file(self):
#        loaded_file = ttk.filedialog.askopenfilename(initialdir=self.PAR.QL_images, title="Select a File",
        loaded_file = tk.filedialog.askopenfilename(
            title="Select a File",
            filetypes=(("fits files", "*.fits"), ("all files","*.*"))
        )
        self.fits_image_ql  = loaded_file
        self.Display(loaded_file)


    @check_enabled
    def Query_Survey(self, catalog):
        self.catalog = catalog
        self.clear_canvas()
        self.logger.info("Setting local canvas")
        self.data_GS = self.catalog.image[0].data
        self.logger.info("Setting local header information")
        self.header_GS = self.catalog.image[0].header
        self.logger.info("Creating Local Image")
        self.AstroImage = AstroImage()
        self.AstroImage.load_hdu(self.catalog.image[0])
        self.fits_image.set_image(self.AstroImage)


    @check_enabled
    def twirl_Astrometry(self):
        self.PAR.valid_wcs = False
        self.Display(self.fits_image_ql)
        
        #had to change open => fits.open [MR] to make this working
        with fits.open(self.fits_image_ql) as hdul:
            raw_header = hdul[0].header
            data = hdul[0].data
        
        img_wcs = wcs.WCS(raw_header)
        #ra, dec = img_wcs.all_pix2world([[data.shape[0] / 2, data.shape[1] / 2]], 0)[0]

        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # not all headers use ra,dec
#         try:  #good header...
#             ra, dec = header["RA"], header["DEC"]
#             self.logger.info(f"From FITS header: ra={ra}, dec={dec}")
#             self.fits_ra.set(ra)
#             self.fits_dec.set(dec)
#         except:
#             self.logger.warning("no RA and  DEC in the FITS header")

        #CASE 1. WE KNOW WHERE WE ARE POINTING FROM THE REGION FILE
        if  self.ra_target.get() !=  0. and self.ra_target.get() != 0.:   
            ra = self.ra_target.get()
            dec = self.dec_target.get()
            self.logger.info("RA and DEC read from the text box")

        #CASE 2. MOST IMPORTANT, WE HOPE TO GET THE POINTED RADEC FROM SOAR TCS...   
        elif self.SOAR.is_on == True:               #was self.PAR.inoutvar.get() == "inside": 
            infoa_dict = self.SOAR_PAGE.Handle_Infox('INFOA')  # TO BE FIXED: we need to grab the INFOA message from the SOAR TCS
            ra=infoa_dict['MOUNT_RA']                          # to extract the pointed RA,DEC coordinates 
            dec=infoa_dict['MOUNT_DEC']
            self.fits_ra.set(ra)
            self.fits_dec.set(dec)
            self.logger.info("RADEC provided by the SOAR TCS")               
        else:   
            tk.messagebox.showinfo(title=None, message="cannot find RADEC, enter by hand")
            return

        self.logger.info(f"Pointed coordinates: {ra} {dec}")
        #<<<<<<<<<<<<<<<<<<<<

        center = SkyCoord(ra, dec, unit=[u.deg, u.deg])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        #shape = data.shape
        fov = 0.05
        
        """
        #clean the image background
        #NOT IMPLEMENTED
        
        coverage_mask = (data == 0)
        from astropy.stats import SigmaClip
        from photutils.background import Background2D, MedianBackground
        sigma_clip = SigmaClip(sigma=3.0)
        bkg_estimator = MedianBackground()
        bkg = Background2D(data, (50, 50), filter_size=(3, 3),
                   sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)
        
        from astropy.stats import sigma_clipped_stats, SigmaClip
        from photutils.segmentation import detect_threshold, detect_sources
        from photutils.utils import circular_footprint
        coverage_mask = (data == 0)
        bkg3 = Background2D(data, (15, 15), filter_size=(3, 3),
                            coverage_mask=coverage_mask, fill_value=0.0,
                            exclude_percentile=50.0)
        data=data - bkg3.backgroun
        
        sigma_clip = SigmaClip(sigma=3.0, maxiters=10)
        threshold = detect_threshold(data, nsigma=2.0, sigma_clip=sigma_clip)
        segment_img = detect_sources(data, threshold, npixels=10)
        footprint = circular_footprint(radius=10)
        mask = segment_img.make_source_mask(footprint=footprint)
        mean, median, std = sigma_clipped_stats(data, sigma=3.0, mask=mask)
        print(np.array((mean, median, std)))
        # mask
        from photutils import make_source_mask
        mask_sci = make_source_mask(data, snr=2, npixels=3, dilate_size=11)
        mask_ref = make_source_mask(data, snr=2, npixels=3, dilate_size=11)

        sigma_clip = SigmaClip(sigma=3) # Sigma clipping
        from photutils.background import Background2D, MedianBackground
        bkg_estimator = MedianBackground()
        
        bkg_sci = Background2D(data, (200, 150), filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator, mask=mask_sci)
        bkg_ref = Background2D(data, (200, 150), filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator, mask=mask_ref)
        """
        
        
        #
        #  FIND STARS IN THE FIELD
        #
        self.clear_canvas()
        stars = twirl.find_peaks(data)[:self.fits_nstars.get()]
       
        
       
        """
        #remove problematic peaks
        #NOT IMPLEMENTED
        
        stars_x = np.array(list(stars))[:,0]
        stars_y = np.array(list(stars))[:,1]
        peaks = data[stars_y.astype(int),stars_x.astype(int)]
        indices = np.where(peaks < 0)
        newstars = np.delete(stars, indices, axis=0)
        stars=newstars
        """
        
        #
        #  DRAW STARS IN THE FIELD, COLOR RED
        #
        radius_pix = 7
        regs = Regions([CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix) for x, y in stars])
        for i, reg in enumerate(regs):
            obj = r2g(reg)
            obj.color="red"
            self.canvas.add(obj, tag='@twirl_{}'.format(i))
        
        #Now the GAIA stars
        
        #If we are online, twirl will find the GAIA stars on the internet
        try:
            gaias = twirl.gaia_radecs(center, fov, circular=True, limit=self.fits_nstars.get())
        except:
        #If we are at the telescope, we read a Gaia catalog
            self.logger.info("We are not online, need to look for the Gaia stars on local disk")    
            self.logger.info("Loading GAIA File")
            initial_dir = self.db.get_value(
                "config_science_targets_dir", default=Path.cwd().as_posix()
            )
            if (Path(initial_dir) / self.target_name).is_dir():
                initial_dir = Path(initial_dir) / self.target_name
            GAIA_file = tk.filedialog.askopenfilename(
                title="Select a Gaia File",
                initialdir=initial_dir,
                filetypes=(("Text files", "*.csv"), ("all files", "*.*"))
            )
            csvFile = pd.read_csv(GAIA_file)
            g=np.transpose(np.array([csvFile['ra_now'].values,csvFile['dec_now'].values])) #extract RADEC
            gaias = g[:self.fits_nstars.get(),:]   #select the first Nstars
            
        #except:
        #    print("killme")
            
        # we can now compute the WCS
        self.PAR.wcs = twirl.compute_wcs(stars, gaias)
        
        """
        #now let's refine the solution
        #consider working on the full gaia g list
        #gaias = twirl.gaia_radecs(center, fov, circular=False)
        """
        px = []
        py = []
        for i in range(len(gaias)):
            ipx, ipy = self.PAR.wcs.wcs_world2pix(gaias[i][0],gaias[i][1], 1)
            if (ipx.item() < 10) or (ipx.item() > (data.shape[1]-10)) or (ipy.item() < 10) or ipy.item() > (data.shape[0]-10):
                self.logger.info(f'skipping Gaia source at (px,py)={ipx.item()},{ipy.item()}')
                continue
            else:
                px = np.append(px,ipx.item())
                py = np.append(py,ipy.item())
            
        #=>do a centroid
        from photutils.centroids import centroid_2dg, centroid_sources
        px1,py1 = centroid_sources(data, px, py, box_size=9)#,
#                        centroid_func=centroid_2dg)
        """        
        #px1=px
        #py1=py
        import astropy.wcs.utils as aputils
        wcs1 = aputils.fit_wcs_from_points(xy=[px1,py1],world_coords=SkyCoord(gaias,frame="icrs",unit="deg"),projection="TAN",sip_degree=4)
        wcs1.sip.a
        
        #TEST ON A TARGET
        aaa,ddd=[84.62021435578    , -69.10457041397]
        px1,py1 = self.PAR.wcs.all_world2pix(aaa,ddd,0) ; print(px1,py1)
        #px2,py2 = wcs1.all_world2pix(aaa,ddd,0) ; print(px2,py2)
        truex,truey = (centroid_sources(data, px1, py1, box_size=9)) 
        print(np.sqrt( (px1-truex[0])**2 + (py1-truey[0])**2)) 
        #print(np.sqrt( (px2-truex[0])**2 + (py2-truey[0])**2))
        """

        # Lets check the WCS solution
        radius_pix = 21
        #gaia_pixel = np.array(SkyCoord(gaias, unit="deg").to_pixel(self.PAR.wcs)).T
        gaia_pixel2 =np.array([px1,py1]).T
        regs_gaia = Regions([CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix) for x, y in gaia_pixel2])
        for i, reg in enumerate(regs_gaia):
            obj = r2g(reg)
            obj.color = "green"
            self.canvas.add(obj, tag='@check_{}'.format(i))

        if self.PAR.wcs is None:
            self.PAR.valid_wcs = False
            self.logger.error("No valid WCS solution found.")
            tk.messagebox.showinfo(title="Manual WCS", message="Put the target at the GS(0,0) position")
            self.create_manual_WCS()
            return
        else:
            self.PAR.valid_wcs = True
            self.logger.info("Found WCS solution")
            #We put on a dummy file the WCS just found, it will be used next time if a WCS cannot be found
            #and we need to call self.create_manual_WCS()
            fn = os.path.join(get_data_file("system"),'blank.fits')
            hdul = fits.open(fn)  
            hdr = hdul[0].header
            new_wcs = self.PAR.wcs.to_header()
            hdr.update(new_wcs)
            #hdul = fits.HDUList([hdul])
            hdul.writeto(os.path.join(get_data_file("system"),'blank.fits'),overwrite=True)
            
            
        self.logger.info(f"WCS Solution is: {self.PAR.wcs}")
        hdu_wcs = self.PAR.wcs.to_fits()  # creates a primaryHDU object 
        
        #FIND THE IMAGE SCALE; JUST A CHECK:
        scale_radec_deg = wcs.utils.proj_plane_pixel_scales(self.PAR.wcs)    
        scale_arcsec= np.mean(scale_radec_deg) * 3600
        self.logger.info(f"Scale measured: {scale_arcsec:.4f}")
        #FIND THE POSITION ANGLE, JUST A CHECK
        pc = self.PAR.wcs.pixel_scale_matrix
        position_angle = np.degrees(np.arctan2(pc[0][1], pc[0][0]))
        self.logger.info(f"Position angle: {position_angle} degrees")
                
        
        if self.loaded_reg_file_path is not None:
            hdu_wcs[0].header.set("dmdmap", self.loaded_reg_file_path.name)   #write in the fits header the name of the DMD map used
        hdu_wcs[0].data = data            # add data to fits file
        
        
        
        
        # I THINK THAT ONCE WE GET THE WCS SOLUTION WE JUST UPODATE THE FILE SUFFIX ADDING 
        #self.wcs_filename = get_fits_dir() / "WCS_{}_{}.fits".format(ra, dec)
        #self.wcs_filename = str( get_fits_dir() / "WCS_{}_{}.fits".format(ra, dec) ) # I think it's better to just use the string
        #hdu_wcs[0].writeto(self.wcs_filename, overwrite=True)
        #ADD '_QL' SUFFIX IF NOT ALREADY PRESENT
        if self.fits_image_ql[-8:-5] != '_QL':
            """
            IF WE WORK WITH THE NATIVE IMAGE, IMPROVE THE HEADER FOR THE _QL VERSION
            """
            hdu_wcs[0].header = self.fits_header_manager(raw_header, hdu_wcs[0].header)
            
            self.fits_image_ql = self.fits_image_ql[:-5] + '_QL.fits'
        #if not Path(self.fits_image_ql).is_file():
            hdu_wcs[0].writeto(self.fits_image_ql, overwrite=True)

        #self.Display(self.wcs_filename)
        #self.fits_image.rotate(self.PAR.Ginga_PA)  
        self.Display(self.fits_image_ql)
        
        #calculate the offset in mm between pointed and actual position for the GS
        #mywcs = wcs.WCS(header)
        # take the xy coordinates of the GS probe home, entered in the GSPage...
        x_GSP00 = self.gs_x0.get()
        y_GSP00 = self.gs_y0.get() 
        # determine the RA,DEC coordinates actually pof_inted by the telescope
        ra_tel, dec_tel = self.PAR.wcs.wcs_pix2world(x_GSP00, y_GSP00, 0)
        
        #Display the coordinates of the GP00 point
        #self.ra_target.set(ra_tel) 
        #self.dec_target.set(dec_tel) 
        self.fits_ra.set(ra_tel) 
        self.fits_dec.set(dec_tel)      
        
        x_pointed, y_pointed = self.PAR.wcs.wcs_world2pix(ra, dec, 0)
        self.logger.info(f"Pointed  RADEC {ra}, {dec} at {x_pointed:.3f}, {y_pointed:.3f}")
        self.logger.info(f"At {x_GSP00}, {y_GSP00} we have RADEC {ra_tel}, {dec_tel}")
        # calculate the offset in RADEC between the telescope and commanded positions
        
        #Delta_ra = float(ra_tel) - float(ra)
        #Delta_dec = float(dec_tel) - float(dec)
        #More direct
        Delta_ra = float(ra) - float(ra_tel)    # If positive the target is too far right, i.e. WEST (flipped image). Need to move the telescope WEST (ADD arcsec)
        Delta_dec = float(dec) - float(dec_tel) # If positive the target is too far North, need to offset the telescope NORH (ADD arcsec)
        self.logger.info(f"Telescope is {Delta_ra*3600:.3f}, {Delta_dec*3600:.3f} arcseconds off")
        
        #convert to arcseconds, taking into account that we want to account for the cos(dec) factor
        Delta_RA_arcsec = Delta_ra*3600.*np.cos(dec*math.pi/180.)
        Delta_DEC_arcsec = Delta_dec*3600.
        
        #display
        self.x_offset.set(Delta_RA_arcsec)
        self.y_offset.set(Delta_DEC_arcsec)
        #self.logger.info(f"{Delta_RA_arcsec}, {Delta_DEC_arcsec}")
        self.logger.info('WCS done')
        # ready to offset the telescope to the commanded position

        """ => SUPERSEDED BY THE ABOVE CODE
        #calculate the offset in mm between pointed and actual position for the GS
        mywcs = wcs.WCS(header)
        ra_target, dec_target = mywcs.all_pix2world([[data.shape[0] / 2, data.shape[1] / 2]], 0)[0]

        self.ra_target.set(ra)
        self.dec_target.set(dec)
        Delta_RA = ra - self.fits_ra.get()
        Delta_DEC = dec - self.fits_dec.get()
        Delta_RA_mm = round(Delta_RA * 3600 / SOAR_ARCS_MM_SCALE.value, 3)
        Delta_DEC_mm = round(Delta_DEC * 3600 / SOAR_ARCS_MM_SCALE.value, 3)
        self.x_offset.set(Delta_RA_mm)
        self.y_offset.set(Delta_DEC_mm)
       
        """

    def create_manual_WCS(self):
        """
        Determine an approximated WCS using the RADEC of the target for CRVAL, the CD matrix "on file" from the latest solution
        and for CRPIX the (0,0) coordinates of the guide star
        Returns
        -------
        None.

        """
        
        #1 READ THE LAST WCS 
        fn = os.path.join(get_data_file("system"),'blank.fits')
        hdul = fits.open(fn)  
        hdr = hdul[0].header
        
        
        #2 SUBSTITUE THE CRVALS with the RADEC of the target
        #  AND CRPIX with the coordinates of the (0,0) point of the Guide stars
        if  self.ra_target.get() !=  0. and self.ra_target.get() != 0.:   
            ra = self.ra_target.get()
            dec = self.dec_target.get()
            self.logger.info("RA and DEC read from the text box")
            hdr['CRVAL1'] = (ra,'[deg] Coordinate value at reference point')      
            hdr['CRVAL2'] = (dec,'[deg] Coordinate value at reference point')  
            hdr['CRPIX1'] = (self.gs_x0.get(),'[deg] Coordinate value at reference point')      
            hdr['CRPIX2'] = (self.gs_y0.get(),'[deg] Coordinate value at reference point') 
            wcs_ = wcs.WCS(hdr)
            self.PAR.wcs = WCS
        else:
            tk.messagebox.showinfo(title="Manual WCS", message="target coordinates missing")
        return 
    
    
    def fits_header_manager(self, SI_original_header, determined_wcs):
        """
        fix the header received by SI camera withg the stuff we wmay want to save in the _QL file
        """
        
        "START WITH THE SISI HEADER"
        import copy
        good_fix_header = copy.deepcopy(SI_original_header)
        
        del good_fix_header['N_PARAM']  #=                   60 / Number of Parameters                           
        del good_fix_header['PARAM1']   #=                    0 / Image Type      
        good_fix_header.rename_keyword('INSTRUME', 'CAMERA') #    10000 / Exposure Time   
        #good_fix_header.rename_keyword('PARAM2', 'EXPTIME') #    10000 / Exposure Time                                  
        #good_fix_header.rename_keyword('PARAM3', 'CCD_TSP') #     1880 / CCD Temperature Setpoint                       
        del good_fix_header['PARAM4']   #=                   20 / Shutter Close Delay                            
        del good_fix_header['PARAM5']   #  =                    0 / Server Data Source                             
        del good_fix_header['PARAM6']   #  =                    6 / Server Test Image Type                         
        del good_fix_header['PARAM7']   #  =                    1 / TDI Delay                                      
        del good_fix_header['PARAM8']   #  =                    4 / Trigger Mode                                   
        del good_fix_header['PARAM9']   #  =                    1 / Parallel Shift Delay                           
        del good_fix_header['PARAM10']   # =                   76 / CCD Temp. Setpoint Offset                      
        del good_fix_header['PARAM11']   # =                    0 / Acquisition Mode                               
        del good_fix_header['PARAM12']   # =                    0 / UART 100 byte Ack                              
        del good_fix_header['PARAM13']   # =                    8 / Serial Origin                                  
        del good_fix_header['PARAM14']   # =                  528 / Serial Length                                  
        del good_fix_header['PARAM15']   # =                    0 / Serial Post Scan                               
        del good_fix_header['PARAM16']   # =                    1 / Serial Binning                                 
        del good_fix_header['PARAM17']   # =                    2 / Serial Phasing                                 
        del good_fix_header['PARAM18']   # =                    0 / Parallel Origin                                
        del good_fix_header['PARAM19']   # =                 1032 / Parallel Length                                
        del good_fix_header['PARAM20']   # =                    0 / Parallel Post Scan                             
        del good_fix_header['PARAM21']   # =                    1 / Parallel Binning                               
        del good_fix_header['PARAM22']   # =                    0 / Parallel Phasing                               
        del good_fix_header['PARAM23']   # =                   18 / DSI Sample Time                                
        del good_fix_header['PARAM24']   # =                    0 / Analog Attenuation                             
        del good_fix_header['PARAM25']   # =                  540 / CCD 0 Port 0 Correlation Bias                  
        del good_fix_header['PARAM26']   # =                  514 / CCD 0 Port 1 Correlation Bias                  
        del good_fix_header['PARAM27']   # =                39582 / CCD 0 Port 0 ADC Offset                        
        del good_fix_header['PARAM28']   # =                40116 / CCD 0 Port 1 ADC Offset                        
        del good_fix_header['PARAM29']   # =                    3 / Port Select                                    
        good_fix_header.rename_keyword('PARAM30','SIMODEL') # =       850 / Instrument Model                               
        good_fix_header.rename_keyword('PARAM31','SISERNR') # =       406 / Instrument SN                                  
        del good_fix_header['PARAM32']   # =                    1 / Installed CCDs                                 
        del good_fix_header['PARAM33']   # =                    1 / CCD Enable Mask                                
        del good_fix_header['PARAM34']   # =                    1 / Camera De-interlace                            
        del good_fix_header['PARAM35']   # =                    1 / Rectangular Grid X                             
        del good_fix_header['PARAM36']   # =                    1 / Rectangular Grid Y                             
        del good_fix_header['PARAM37']   # =                    0 / Two Serial Registers                           
        del good_fix_header['PARAM38']   # =                    2 / Installed Ports                                
        del good_fix_header['PARAM39']   # =                   18 / Tested Speeds                                  
        del good_fix_header['PARAM40']   # =                    0 / Hardware Revision                              
        del good_fix_header['PARAM41']   # =                  560 / Serial Size                                    
        del good_fix_header['PARAM42']   # =                 1150 / Parallel Size                                  
        del good_fix_header['PARAM43']   # =                 1780 / Low Temp Limit                                 
        del good_fix_header['PARAM44']   # =                 2030 / Operational Temp                               
        del good_fix_header['PARAM45']   # =                    0 / Port 0 Connect                                 
        del good_fix_header['PARAM46']   # =                    0 / Port 0 Map                                     
        del good_fix_header['PARAM47']   # =                    0 / Port 0 Shift Direction                         
        del good_fix_header['PARAM48']   # =                    0 / Port 1 Connect                                 
        del good_fix_header['PARAM49']   # =                    1 / Port 1 Map                                     
        del good_fix_header['PARAM50']   # =                    1 / Port 1 Shift Direction                         
        del good_fix_header['PARAM51']   # =                   65 / Server Flags                                   
        del good_fix_header['PARAM52']   # =               813305 / Server Up Time                                 
        del good_fix_header['PARAM53']   # =                 3281 / Server I/O FPGA Core Temp.                     
        del good_fix_header['PARAM54']   # =               813300 / Camera Connection Duration                     
        del good_fix_header['PARAM55']   # =                98470 / Camera Status Age                              
        good_fix_header.rename_keyword('PARAM56','CCDTEMP') # =      1876 / CCD 0 CCD Temp.                                
        good_fix_header.rename_keyword('PARAM57','BKPTEMP') # =      2907 / Backplate Temperature                          
        del good_fix_header['PARAM58'] # =                      0 / Shutter Status                                 
        del good_fix_header['PARAM59'] # =                      0 / XIRQA Status                                   
        good_fix_header.rename_keyword('PARAM60','COOLER') # =                   1 / Cooler Status                                  

        """NOW ADD THE NEW INFOO FROM THE WCS SOLVER"""
        good_fix_header['WCSAXES'] = (determined_wcs['WCSAXES'], 'Number of coordinate axes')                      
        good_fix_header['CRPIX1'] = (determined_wcs['CRPIX1'],'Pixel coordinate of reference point')            
        good_fix_header['CRPIX2'] = (determined_wcs['CRPIX2'],' Pixel coordinate of reference point')         
        good_fix_header['PC1_1'] = (determined_wcs['PC1_1'],'Coordinate transformation matrix element')       
        good_fix_header['PC1_2'] = (determined_wcs['PC1_2'],'Coordinate transformation matrix element')       
        good_fix_header['PC2_1'] = (determined_wcs['PC2_1'],'Coordinate transformation matrix element')       
        good_fix_header['PC2_2'] = (determined_wcs['PC2_2'],'Coordinate transformation matrix element')       
        good_fix_header['CDELT1'] = (determined_wcs['CDELT1'],'[deg] Coordinate increment at reference point')  
        good_fix_header['CDELT2'] = (determined_wcs['CDELT2'],'[deg] Coordinate increment at reference point') 
        good_fix_header['CUNIT1'] = (determined_wcs['CUNIT1'],'Units of coordinate increment and value')   
        good_fix_header['CUNIT2'] = (determined_wcs['CUNIT2'],'Units of coordinate increment and value')        
        good_fix_header['CTYPE1'] = (determined_wcs['CTYPE1'],'Right ascension, gnomonic projection')           
        good_fix_header['CTYPE2'] = (determined_wcs['CTYPE2'],'Declination, gnomonic projection')               
        good_fix_header['CRVAL1'] = (determined_wcs['CRVAL1'],'[deg] Coordinate value at reference point')      
        good_fix_header['CRVAL2'] = (determined_wcs['CRVAL2'],'[deg] Coordinate value at reference point')      
        good_fix_header['LONPOLE'] = (determined_wcs['LONPOLE'],'[deg] Native longitude of celestial pole')       
        good_fix_header['LONPOLE'] = (determined_wcs['LONPOLE'],'[deg] Native latitude of celestial pole')        
        good_fix_header['MJDREF'] = (determined_wcs[' MJDREF'],'[d] MJD of fiducial time')                       
        good_fix_header['RADESYS'] = (determined_wcs['RADESYS'],'Equatorial coordinate system')                   
        good_fix_header['DMDMAP'] = (determined_wcs['DMDMAP'],'R136-T00_RADEC=84.67665-69.1009333.reg')       
        
        """
        THIRD SET OF KEYWORDS COMING FROM SAMOS
        """
        good_fix_header['INSTRUME'] = 'SAMOS'
        
        
        
        return good_fix_header


    @check_enabled
    def get_ZeroPoint(self):
        
        #Zero point can be derived only if we are dealing with sloan g,r,i,z filters
        griz_filters = ["sloan-g", "sloan-r", "sloan-i", "sloan-z"]
        if self.current_filter.get() not in griz_filters:
            self.logger.info("Cannot determine Zero Point for the current filter")
            return
    
        
        # LOAD THE RIGHT CATALOG, EITHER SKYMAPPER OR PANSTARRS, FOR THE FILTER
        # SOUTHERN HEMISPHERE, use SkyMapper
        #The directory must be PIXELS directory in the last opened RegionFiles folder
        dir_target = str(self.loaded_reg_file_path.parent.parent.parent)
        #target = self.target_name.split("-")[0]
        
        #limit RADEC to 4 decimals, as this is the way the script creates the filename
        #radec_center = '%.4f'%(self.ra_target.get())+' %.4f'%(self.dec_target.get())
        
        
        if self.dec_target.get() <= 0:
            for filename in os.listdir(dir_target):
                if 'SkyMapper_in_field_' in filename:    
                    SkyMap_cat = pd.read_csv(os.path.join(dir_target,filename))
                    
                    #pd.read_csv(dir_target+"/"+target+"-SkyMapper_in_field_"+radec_center+".csv")
                    SkyMap_cat.rename(columns={'g_band':'sloan-g', 'r_band':'sloan-r', 'i_band':'sloan-i', 'z_band':'sloan-z'})
                    snr=SkyMap_cat['i_band']/SkyMap_cat['e_i_psf']
                    SkyMap_cat['SNR']=snr
                    SkyMap_cat = SkyMap_cat.dropna()

        if self.dec_target.get() > 0:
            PanSTARRS_phot_pandas.to_csv(dir_name+"/"+Target_name+"-PanSTARRS_in_field_"+radec_center.to_string()+".csv")

        

        # TAKE THE BRIGHTEST CATALOG STARS
        #stars = twirl.find_peaks(data)[:self.fits_nstars.get()]
        #radius_pix = 7
        from photutils.aperture import aperture_photometry
        from regions import CirclePixelRegion
        with fits.open(self.fits_image_ql) as hdul:
            data = hdul[0].data
            hhh =  hdul[0].header
            EXPTIM = hhh['EXPTIME']
        
        #add xy coords to the catalog
        x_stars, y_stars = self.PAR.wcs.wcs_world2pix(SkyMap_cat['RA'], SkyMap_cat['DEC'], 0)
        SkyMap_cat['x'] = x_stars
        SkyMap_cat['y'] = y_stars
        
        #positions = np.column_stack((x_stars,y_stars))
        
        #select coordinates in field
        x_lower_bound = 39
        x_upper_bound = 1022
        y_lower_bound = 24
        y_upper_bound = 1000
        x_infield=[]
        y_infield=[]
        ixy_drop=[]
        import copy
        SkyMap_cat2=copy.deepcopy(SkyMap_cat)
        for ixy in range(len(x_stars)):
            if (x_lower_bound <= x_stars[ixy] <= x_upper_bound) and (y_lower_bound <=y_stars[ixy] <= y_upper_bound):
                x_infield = np.append(x_infield,x_stars[ixy])
                y_infield = np.append(y_infield,y_stars[ixy])
            else:    
                print(SkyMap_cat.index[ixy])
                ixy_drop = np.append(ixy_drop,SkyMap_cat.index[ixy])
        SkyMap_cat2 = SkyMap_cat.drop(ixy_drop)
                                             
        #refinbe position
        from photutils.centroids import centroid_2dg, centroid_sources        
        SkyMap_cat2['x'], SkyMap_cat2['y']= centroid_sources(data, x_infield, y_infield, box_size=25,
                        centroid_func=centroid_2dg)
        positions = np.column_stack((SkyMap_cat2['x'], SkyMap_cat2['y']))
        #APERTURE PHOTOMETRY FROM 
        #https://photutils.readthedocs.io/en/latest/user_guide/aperture.html#
        
        regs = Regions([CirclePixelRegion(center=PixCoord(x,y), radius=5) for x, y in positions])
        #phot_table = aperture_photometry(data, regs) 
        #annulus_aperture = CircularAnnulus(positions, r_in=10, r_out=15)
        phot_table = [aperture_photometry(data, reg)['aperture_sum'] for reg in regs]
        counts = [phot_table[i].value [0]for i in range(len(SkyMap_cat2['x']))]
        
        #counts_s = np.array(counts)/EXPTIM

        #positions = xy_stars
        
        
        aperture = CircularAperture(positions, r=5)
        annulus_aperture = CircularAnnulus(positions, r_in=10, r_out=25)
        sigclip = SigmaClip(sigma=3.0, maxiters=10)
        aper_stats = ApertureStats(data, aperture, sigma_clip=None)
        bkg_stats = ApertureStats(data, annulus_aperture, sigma_clip=sigclip)
        total_bkg = bkg_stats.median * aper_stats.sum_aper_area.value
        apersum_bkgsub = aper_stats.sum - total_bkg
        #print(apersum_bkgsub)
        counts_s = np.array(apersum_bkgsub)/(EXPTIM/1000)
        counts_s[counts_s < 0] = np.nan
        counts_s_final = copy.deepcopy(counts_s[~np.isnan(counts_s)])
        SkyMap_cat3 = copy.deepcopy(SkyMap_cat2[~np.isnan(counts_s)])
        ZP = np.array(SkyMap_cat3['i_band'])+2.5*np.log10(counts_s_final)
        #ZP = ZP[~np.isnan(ZP)]
        import matplotlib.pyplot as plt
        plt.scatter(np.array(SkyMap_cat3['i_band']), -2.5*np.log10(counts_s_final))
        
        #counts_s = counts_s[~np.isnan(counts_s)]
        #non_negative_counts_s = [num for num in counts_s if num >= 0]
        #ZP = SkyMap_cat['i_band']+2.5*np.log10(non_negative_counts_s)
        
        #ZP = ZP[~np.isnan(ZP)]
        

        ZP = sigma_clip(ZP, sigma=2, maxiters=5)
        
        import matplotlib.pyplot as plt
        counts, bin_edges, _  = plt.hist(ZP, bins=7)
        
        xmin, xmax = plt.xlim()
        x = np.linspace(xmin, xmax, 100)
        mu, std = norm.fit(ZP) # Fit a normal distribution to the data
        p = norm.pdf(x, mu, std)        
        plt.plot(x, p, 'k', linewidth=2, label=f'Fitted Normal Distribution (μ={mu:.2f}, σ={std:.2f})')
        plt.xlabel('Value')
        plt.ylabel('Density')
        plt.title('Histogram with Normal Distribution Overlay')
        plt.legend()
        plt.grid(True)
        plt.show()
        
        
        mZP = np.mean(ZP)
        sZP = np.std(ZP)
        self.logger.info(f"Zero Point: Fitted Normal Distribution (μ={mu:.2f}, σ={std:.2f})")
        self.logger.info(f"Zero Point: Mean={mZP:.2f}, StDev={sZP:.2f}")
        tk.messagebox.showinfo(title="Zero Point", message=(f"Zero Point: Mean={mZP:.2f}, StDev={sZP:.2f}"))

        

    @check_enabled
    def find_stars(self):
        self.Display(self.fits_image_ql)
#        self.fits_image.rotate(self.PAR.Ginga_PA)  
#         if self.slit_tab_view is None:
#             self.initialize_slit_table()
        
        self.set_slit_drawtype()
        with fits.open(self.fits_image_ql) as hdul:
            header = hdul[0].header
            data = hdul[0].data

        ra, dec = header["CRVAL1"], header["CRVAL2"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        #shape = data.shape
        #pixel_scale = SISI_PIXEL_SCALE
        #fov = (np.max(shape) * u.pix * pixel.to(u.deg)).value

        # Let's find some stars and display the image
        self.clear_canvas()
        threshold = 0.1
        stars = twirl.find_peaks(data, threshold)[:self.fits_nstars.get()]
        med = np.median(data)
        radius_pix = 10
        slit_width = self.slit_xd.get()
        slit_height = self.slit_disp.get()
        coords = [PixCoord(x, y) for x, y in stars]
        regions = Regions([RectanglePixelRegion(center=c, width=slit_width, height=slit_height, angle=0*u.deg) for c in coords])
        for i,region in enumerate(regions):
            obj = r2g(region)
            #tab must be slit, allowing e.g. showtraces to work...
            self.canvas.add(obj, tag='@slit_{}'.format(i))
            obj.pickable = True
            obj.color = "red"
            obj.add_callback('pick-up', self.pick_cb, 'up')
            obj.add_callback('edited', self.edit_cb)
#             self.slit_tab_view.add_slit_obj(region, obj.tag, self.fits_image)

    @check_enabled
    def toggle_gsp00(self):
        if (self.show_gsp00.get()) and (self.tag_gsp00 is None):
            # Show the position of the GSP00 on the image
            radius_pix = 15
            reg_GSP00 = CirclePixelRegion(
                center=PixCoord(self.gs_x0.get(), self.gs_y0.get()), radius=radius_pix
            )
            obj = r2g(reg_GSP00)
            obj.color = "blue"
            obj.linewidth = 3
            self.tag_gsp00 = '@check_GSP00_'+str(time.time())  #change the tag each time the circle is created
            self.canvas.add(obj, tag=self.tag_gsp00)
            self.logger.info(f"Showing {obj} {obj.tag}")
        elif (not self.show_gsp00.get()) and (self.tag_gsp00 is not None):
            # Hide the position of the GSP00 on the image
            #looking at https://ginga.readthedocs.io/en/stable/_modules/ginga/canvas/CanvasMixin.html
            #it should be possible to simply run
            #CM.CompoundMixin.delete_objects_by_tag(self.canvas,'@check_GSP00')  
            #but it does not work. Needs newer Ginga version?
            try:
                object_to_remove = self.canvas.get_object_by_tag(self.tag_gsp00)
                if object_to_remove is not None:
                    self.logger.info(f"Hiding {object_to_remove} {object_to_remove.tag}")
                    CM.CompoundMixin.delete_object(self.canvas, object_to_remove)
            except Exception as e:
                self.logger.error(f"Exception {e} trying to remove the circle. Aborting.")
            finally:
                self.tag_gsp00 = None
        self.canvas.redraw()
        
    """
    @check_enabled
    def open_quicklook_file(self):
        #to be written
        filename = tk.filedialog.askopenfilename(
            filetypes=[("fitsfiles", "*.fits"), ("allfiles", "*")]
        )
        self.Display(filename)
        if self.AstroImage.wcs.wcs.has_celestial:
            self.PAR.wcs = self.AstroImage.wcs.wcs
            self.PAR.valid_wcs = True
    """


    @check_enabled
    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        objects_to_remove = []
        for obj in CM.CompoundMixin.get_objects(self.canvas):
            if obj.tag == self.tag_gsp00:
                continue
            if "slit" not in obj.tag:
                self.logger.info(f"Removing {obj} {obj.tag}")
                objects_to_remove.append(obj)
        CM.CompoundMixin.delete_objects(self.canvas, objects_to_remove)
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)

    @check_enabled
    def delete_all(self):
        """ erase all objects in the canvas
            and also astropy regions for a frew shart with enternew regions"""
        self.logger.info("Removing all objects")
        objects_to_remove = []
        for obj in CM.CompoundMixin.get_objects(self.canvas):
            #self.logger.info(f"Removing {obj} {obj.tag}")
            objects_to_remove.append(obj)
        CM.CompoundMixin.delete_objects(self.canvas, objects_to_remove)
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)
        self.loaded_astropy_regions = ""
        

    def cursor_cb(self, viewer, button, data_x, data_y):
        """
        This gets called when the data position relative to the cursor changes.
        """
        # Start by checking if there's even an image to look at.
        if viewer.get_image() is None:
            return

        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off), int(data_y + viewer.data_off))
            value = f"{value:8g}"
        except Exception as e:
            value = "Invalid"

        fits_x = int(np.floor(data_x) + 1)
        fits_y = int(np.floor(data_y) + 1)
        text = f"FITS: ({fits_x:4d}, {fits_y:4d}). Value = {value}"
        
        
        
        dmd_x, dmd_y = ccd_to_dmd(fits_x, fits_y, self.PAR.dmd_wcs)
        dmd_x = int(np.floor(dmd_x))
        dmd_y = int(np.floor(dmd_y))
        text = f"DMD: ({dmd_x:7d}, {dmd_y:7d}). " + text

        
        
        
        # Calculate WCS RA
        try:
            # Image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_deg, dec_deg = image.pixtoradec(fits_x, fits_y)
            
            #no more used, superseeded by self.ra_target, self.dec_target; removed
            #self.ra_center, self.dec_center = image.pixtoradec(528, 516, format='str', coords='fits')
            
            text = f"(RA, DEC): ({ra_deg:8.4f}, {dec_deg:8.4f}). " + text
        except Exception as e:
            self.logger.error("Error {} in printing co-ordinates".format(e))
            text = "No Valid WCS. " + text
        self.readout.config(text=text)


    @check_enabled
    def set_slit_drawtype(self):
        self.slit_mode.set("draw")  # Possibly need to set self.draw_mode instead?
        self.set_mode_cb() # method used to set a callback function that is triggered when the viewer's active mode changes. 
        if self.source_pickup_enabled.get():
            self.draw_type.set("point")
        else:
            self.draw_type.set("box")
        self.canvas.set_drawtype(self.draw_type.get())


    """
    @check_enabled
    def set_mode_cb(self):
        mode = self.slit_mode.get()
        print('MODE =',mode)
        print('self.canvas.get_draw_mode() = ',self.canvas.get_draw_mode())
        print('self.source_pickup_enabled.get() = ',self.source_pickup_enabled.get())
        #if we are working on an existing object,  we can either 
        # - #modify it (edit(
        # - #get the properties
        # - delete it
        if mode != "draw":
            self.source_pickup_enabled.set(False)
        if mode != "delete":
            self.canvas.set_draw_mode(mode)
        else:
           self.canvas.set_draw_mode("pick")
           self.source_pickup_enabled.set(True)
        print('self.canvas.get_draw_mode() = ',self.canvas.get_draw_mode())
        print('self.source_pickup_enabled.get() = ',self.source_pickup_enabled.get())
        #if we are working on an existing object,  we can either 
    """   

    @check_enabled
    def set_mode_cb(self):
        mode = self.slit_mode.get()  # variable for the selected Radio button
        print(mode)
        #if we are working on an existing object,  we can either 
        # - #modify it (edit(
        # - #get the properties
        # - delete it
        if mode == "draw":
            self.source_pickup_enabled.set(False)
            self.canvas.set_draw_mode("draw") #  Ginga: mode must be one of: [None, 'draw', 'edit', 'pick']
        if mode == "edit":
            self.source_pickup_enabled.set(True)
            self.canvas.set_draw_mode("edit") #  Ginga: mode must be one of: [None, 'draw', 'edit', 'pick']
        if mode == "delete":
            self.source_pickup_enabled.set(True)
            self.canvas.set_draw_mode("pick") #  Ginga: mode must be one of: [None, 'draw', 'edit', 'pick']
        if mode == "pick":
            self.source_pickup_enabled.set(False)
            self.canvas.set_draw_mode("pick")#   Ginga: mode must be one of: [None, 'draw', 'edit', 'pick']
        print('MODE =',mode)
        print('self.canvas.get_draw_mode() = ',self.canvas.get_draw_mode())
        print('self.source_pickup_enabled.get() = ',self.source_pickup_enabled.get())
      


    @check_enabled
    def examine_source(self, canvas, PointEvent, x0, y0):
        """ this procedure is activated when the mouse click goes up
            thanks to line self.canvas.add_callback('cursor-up', self.examine_source)"""

        #we don't want to examine source if we are e.g. in "draw" mode, that always finishes with a click "up" of the mouse...
        if self.slit_mode.get() != "pick":
            return

        self.logger.info(f"User inspecting target on canvas/n")
        
        #grab the pixel coordinates of the click
        coords = PixCoord(x0,y0)
        
        #create a region centered on that coordinates
        region = RectanglePixelRegion(center=coords, width=21, height=21, angle=0*u.deg)
        
        #conver to ginga object (type box)
        obj = r2g(region)
        
        #add to the canvas
        canvas.add(obj)
        
        data_box = self.AstroImage.cutout_shape(obj)
        #convert to data_bax 
        
        # the box is no more needed, eliminate
        CM.CompoundMixin.delete_object(self.canvas, obj)
        
        #find the brightest pixel in the data_box
        peaks = self.iq.find_bright_peaks(data_box)
        
        #analyze the peak
        results = self.iq.evaluate_peaks(peaks, data_box)
        
        #original results contain non-necessary info
        #for key, value in results[0].items():
        #    print(f"{key}: {value}")
        
        #cleanup and display again on the console
        results[0]['objx'] = x0
        results[0]['objy'] = y0
        rrr=dict(results[0].items())
        rrr.pop('pos')
        rrr.pop('oid_x')
        rrr.pop('oid_y')
        rrr.pop('fwhm_radius')
        rrr.pop('x')
        rrr.pop('y')
        rrr.pop('ensquared_energy_fn')
        rrr.pop('encircled_energy_fn')
        for key, value in list(rrr.items()):
            print(f"{key:10}: {value:.2f}")
            
        # THIS DOES NOT WORK YET. The idea is to plot on the canvas the PSF so we don't need to peek at the console.
        #my_text = self.canvas.get_text(x0, y0, "results[0]['fwhm']", font="sans", fontsize=20, color="yellow")
        #canvas.add(my_text)
            
        #PART 2: GET THE DISTANCE FROM THE Guide Star Probe (0,0) pixel   
        x_GSP00 = self.gs_x0.get()
        y_GSP00 = self.gs_y0.get() 
        
        #Distance, in pixels
        #Dx = x0 - x_GSP00   # If Negaive the target is too far left on the screen, i.e. East (right) on the sky(flipped image!)
        Dx = x0 - x_GSP00   # If Positive the target is too far right on the screen, i.e. WEST on the sky(flipped image!)
        Dy = y0 - y_GSP00   # Positive if the target is too far north. 

        #Convert to arcseconds assumin a scale of 0.18"/pixel
        #Delta_RA_arcsec = Dx * 0.18   # If negativee, the telescope is pointing too far West and has to move EAST, removing  arcseconds
        Delta_RA_arcsec = Dx * 0.18   # If positive, the telescope is pointing too far Eest and has to move WEST, adding arcseconds
        Delta_DEC_arcsec = Dy * 0.18  # If positive, the telescope has to move North, adding arcseconds
        
        #display
        self.x_offset.set(Delta_RA_arcsec)
        self.y_offset.set(Delta_DEC_arcsec)


    @check_enabled
    def draw_cb(self, canvas, tag):
        obj = canvas.get_object_by_tag(tag)
        obj.pickable = True
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        obj.add_callback('edited', self.edit_cb)
        kind = self.draw_type.get()
        self.logger.info(f"User draw object of kind {kind} with tag {tag} on canvas {canvas}")
#         if self.slit_tab_view is None:
#             self.initialize_slit_table()
        
        if kind == "box" and self.source_pickup_enabled.get():
            # User drew a box in source-pickup mode (should never happen)
            self.logger.error("User created a box in source pickup mode.")
            try:
                r = g2r(obj)
            except ValueError as e:
                self.logger.error("Error {} converting box to astropy region".format(e))
                obj.kind = "box"

            new_obj = self.slit_handler(obj)
#             self.slit_tab_view.add_slit_obj(g2r(new_obj), new_obj.tag, self.fits_image)
        elif self.source_pickup_enabled.get() and kind == 'point':
            # User clicked on a point in source pick-up mode.
            new_obj = self.slit_handler(obj)
#             self.slit_tab_view.add_slit_obj(g2r(new_obj), new_obj.tag, self.fits_image)
        elif kind == "box" and not self.source_pickup_enabled.get():
            # a box is drawn but centroid is not searched, just drawn...

            # Declare the object as a slit by so tagging it
            obj.tag = '@slit_{}'.format(obj.tag)
            
            #in the case it is just a mouse click with the "Draw" button selected and we are in kind = "box"...']
            #
            #Oct.1 2025: from https://ginga.readthedocs.io/en/stable/dev_manual/canvas.html
            #"Box: a rectangular shape defined by a single center point, two radii and a rotation angle."
            #if obj.width <=0:
            #    return
            
            # the ginga object, a box, is converted to an astropy region
            r = g2r(obj)
            
            # the astropy object is added to the table
#             self.slit_tab_view.add_slit_obj(r, obj.tag, self.fits_image)
        # Done draw_cb


    @check_enabled
    def slit_handler(self, obj):
        self.logger.info("Creating a slit for object {} ({})".format(obj, obj.kind))
        img_data = self.AstroImage.get_data()

        if obj.kind == 'point':
            # Search centroid: Start creating box
            x_c = obj.points[0][0]-1  # really needed?
            y_c = obj.points[0][1]-1

            # Delete point object
            CM.CompoundMixin.delete_object(self.canvas, obj)

            # create area to search, use astropy and convert to ginga (historic reasons...)
            r = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)), width=15, height=15, angle=0*u.deg)
            # and we convert it to ginga.
            obj = r2g(r)
            self.canvas.add(obj)
        
        # time to do the math; collect the pixels in the Ginga box
        data_box = self.AstroImage.cutout_shape(obj)

        # we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.canvas, obj)

        # find the peak within the Ginga box
        peaks = self.iq.find_bright_peaks(data_box)
        if len(peaks) == 0:
            self.logger.warning("No peaks found")
            return
        print(peaks[:20])  # subarea coordinates
        x1 = obj.x - obj.xradius
        y1 = obj.y - obj.yradius
        px, py = round(peaks[0][0]+x1), round(peaks[0][1]+y1)
        self.logger.info("Peak found at ({}, {}) with counts {}".format(px, py, img_data[py, px]))  #order array is [py,px]!
        
        # evaluate peaks to get FWHM, center of each peak, etc.
        # from ginga.readthedocs.io
        # Each result contains the following keys:
        # 
        #    * ``objx``, ``objy``: Fitted centroid from :meth:`get_fwhm`.
        #    * ``pos``: A measure of distance from the center of the image.
        #    * ``oid_x``, ``oid_y``: Center-of-mass centroid from :meth:`centroid`.
        #    * ``fwhm_x``, ``fwhm_y``: Fitted FWHM from :meth:`get_fwhm`.
        #    * ``fwhm``: Overall measure of fwhm as a single value.
        #    * ``fwhm_radius``: Input FWHM radius.
        #    * ``brightness``: Average peak value based on :meth:`get_fwhm` fits.
        #    * ``elipse``: A measure of ellipticity.
        #    * ``x``, ``y``: Input indices of the peak.
        #    * ``skylevel``: Sky level estimated from median of data array and
        #      ``skylevel_magnification`` and ``skylevel_offset`` attributes.
        #    * ``background``: Median of the input array.
        #    * ``ensquared_energy_fn``: Function of ensquared energy for different pixel radii.
        #    * ``encircled_energy_fn``: Function of encircled energy for different pixel radii.
        results = self.iq.evaluate_peaks(peaks, data_box)
        self.logger.debug("Full Evaluation: {}".format(results))
        #self.logger.info("Peak Centroid: ({}, {})".format(results[0].objx, results[0].objy))
        self.logger.info("Peak Centroid (x,y): ({}, {})".format(results[0].objx+x1, results[0].objy+y1))
        self.logger.info("FWHM: {}, Peak Value: {}".format(results[0].fwhm, results[0].brightness))
        self.logger.info("Sky: {}, Background (median of region): {}".format(results[0].skylevel, results[0].background))
        self.logger.info("(RA, DEC) of fitted centroid: {}".format(self.AstroImage.pixtoradec(results[0].objx+x1, results[0].objy+y1)))

        # having found the centroid, we need to draw the slit
        slit_box = self.canvas.get_draw_class('box')
        xradius = self.slit_xd.get() * 0.5 * DMD_MIRROR_TO_PIXEL_SCALE
        yradius = self.slit_disp.get() * 0.5 * DMD_MIRROR_TO_PIXEL_SCALE
        new_obj = slit_box(x=results[0].objx + x1, y=results[0].objy + y1, xradius=xradius, yradius=yradius, color='red',
                           alpha=0.8, fill=False, angle=5*u.deg, pickable=True)
        self.canvas.add(new_obj, tag='@slit_{}-{}'.format(results[0].objx + x1, results[0].objy + y1))
        new_obj.add_callback('pick-up', self.pick_cb, 'up')
        new_obj.add_callback('pick-move', self.pick_cb, 'move')
        new_obj.add_callback('pick-key', self.pick_cb, 'key')
        new_obj.add_callback('edited', self.edit_cb)
        return new_obj

    @check_enabled
    def show_remove_traces(self):
        """ Show Traces """
        if self.var_show_traces.get() == False:
            # Set the variable to True for next time you enter, to delete
            self.var_show_traces.set(True)
            #change the text in the box
            self.button_show_remove_traces.config(text = "Remove Traces")
           
            # keep only the slits/boxes
            self.slits_only()
            
            bbox = self.canvas.get_bbox()
            bbox_x = [p[0] for p in bbox]
            bbox_y = [p[1] for p in bbox]
            min_x, max_x = min(bbox_x), max(bbox_x)
            min_y, max_y = min(bbox_y), max(bbox_y)
            self.logger.info(f"Window X is {min_x} {max_x}")
            self.logger.info(f"Window Y is {min_y} {max_y}")
    
            # We want to create rectangles
            Rectangle = self.canvas.get_draw_class('rectangle')
    
            # we should have only boxes/slits
            self.trace_boxes_objlist = []  # create container of the list traces
            for i, obj in enumerate(CM.CompoundMixin.get_objects(self.canvas)):
                self.logger.info(f"Checking object {obj} with tag {obj.tag}")
                if obj.alpha == 0:
                    # ***** WHY?
                    continue
                if "slit" not in obj.tag:
                    continue
                if hasattr(obj, 'x'):
                    self.logger.info(f"Object: ({obj.x}, {obj.y}) size ({obj.xradius}, {obj.yradius})")
                    ox, oy = round(obj.x), round(obj.y)
                    x1, x2 = max(ox - obj.xradius, 0), min(ox + obj.xradius, max_x)
                    y1, y2 = oy - 1024, oy + 1024
    #                 if (x1 < 0) or (x2 < 0) or (y1 < 0) or (y2 < 0):
    #                     continue
    #                 x1, x2 = max(round(obj.x) - 1024,0), round(obj.x) + 1024
    #                 y1, y2 = max(round(obj.y) - obj.yradius,0), round(obj.y) + obj.yradius
                    self.logger.info(f"Slit {i}: Trace ({x1} -> {x2}, {y1} -> {y2})")
                    r = Rectangle(x1=x1, y1=y1, x2=x2, y2=y2, angle=0*u.deg, color='yellow', fill=1, fillalpha=0.5)
                    self.canvas.add(r, tag=f'@trace_{i}')
                    self.trace_boxes_objlist.append(r)  # add the rectangle to the list of traces
                else:
                    continue    
            CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)
            return
            
        """ Delete Traces """
        
        # We have the variable set to True, therefore we are here to delete...
        self.var_show_traces.set(False)
        #change the text in the box
        self.button_show_remove_traces.config(text = " Show Traces ")
        """ 
             Use "try:/except:"
             We may call this function just to make sure that the field is clean, so
             we do not need to assume that the traces have been created
        """
        objects_to_remove = []
        for obj in CM.CompoundMixin.get_objects(self.canvas):
            if "trace" in obj.tag:
                self.logger.info(f"Removing {obj} {obj.tag}")
                objects_to_remove.append(obj)
        CM.CompoundMixin.delete_objects(self.canvas, objects_to_remove)
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)



    @check_enabled
    def show_traces(self):
        """ Show Traces """
        # keep only the slits/boxes
        self.slits_only()
        
        bbox = self.canvas.get_bbox()
        bbox_x = [p[0] for p in bbox]
        bbox_y = [p[1] for p in bbox]
        min_x, max_x = min(bbox_x), max(bbox_x)
        min_y, max_y = min(bbox_y), max(bbox_y)
        self.logger.info(f"Window X is {min_x} {max_x}")
        self.logger.info(f"Window Y is {min_y} {max_y}")

        # We want to create rectangles
        Rectangle = self.canvas.get_draw_class('rectangle')

        # we should have only boxes/slits
        self.trace_boxes_objlist = []  # create container of the list traces
        for i, obj in enumerate(CM.CompoundMixin.get_objects(self.canvas)):
            self.logger.info(f"Checking object {obj} with tag {obj.tag}")
            if obj.alpha == 0:
                # ***** WHY?
                continue
            if "slit" not in obj.tag:
                continue
            if hasattr(obj, 'x'):
                self.logger.info(f"Object: ({obj.x}, {obj.y}) size ({obj.xradius}, {obj.yradius})")
                ox, oy = round(obj.x), round(obj.y)
                x1, x2 = max(ox - obj.xradius, 0), min(ox + obj.xradius, max_x)
                y1, y2 = oy - 1024, oy + 1024
#                 if (x1 < 0) or (x2 < 0) or (y1 < 0) or (y2 < 0):
#                     continue
#                 x1, x2 = max(round(obj.x) - 1024,0), round(obj.x) + 1024
#                 y1, y2 = max(round(obj.y) - obj.yradius,0), round(obj.y) + obj.yradius
                self.logger.info(f"Slit {i}: Trace ({x1} -> {x2}, {y1} -> {y2})")
                r = Rectangle(x1=x1, y1=y1, x2=x2, y2=y2, angle=0*u.deg, color='yellow', fill=1, fillalpha=0.5)
                self.canvas.add(r, tag=f'@trace_{i}')
                self.trace_boxes_objlist.append(r)  # add the rectangle to the list of traces
            else:
                continue    
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)


    @check_enabled
    def remove_traces(self):
        """ 
        Use "try:/except:"
        We may call this function just to make sure that the field is clean, so
        we do not need to assume that the traces have been created
        """
        objects_to_remove = []
        for obj in CM.CompoundMixin.get_objects(self.canvas):
            if "trace" in obj.tag:
                self.logger.info(f"Removing {obj} {obj.tag}")
                objects_to_remove.append(obj)
        CM.CompoundMixin.delete_objects(self.canvas, objects_to_remove)
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)


    @check_enabled
    def save_all_sub_patterns(self):
        pattern_directory = self.PAR.fits_dir / "SubPatterns"
        pattern.mkdir(parents=True, exist_ok=True)
        for i, pattern in enumerate(self.pattern_series):
            pattern_name = self.sub_pattern_names[i]
            if self.PAR.valid_wcs and self.PAR.wcs.has_celestial:
                pattern_data_rows = pattern.values
                sky_regions = Regions(list(map(self.create_astropy_RectangleSkyRegion, pattern_data_rows)))
                new_file_name = pattern_directory / pattern_name + ".reg"
                sky_regions.write(new_file_name, overwrite=True, format="ds9")


    @check_enabled
    def save_selected_sub_pattern(self):
        pattern_directory = self.PAR.fits_dir / "SubPatterns"
        pattern_list_index = self.pattern_group.current()
        current_pattern = self.pattern_series[pattern_list_index]
        pattern_name = self.pattern_group.get()
        if self.PAR.valid_wcs and self.PAR.wcs.has_celestial:
            pattern_data_rows = current_pattern.values
            sky_regions = Regions(list(map(self.create_astropy_RectangleSkyRegion, pattern_data_rows)))
            new_file_name = pattern_directory / pattern_name + ".reg"
            sky_regions.write(new_file_name, overwrite=True, format="ds9")


    @check_enabled
    def create_astropy_RectangleSkyRegion(self, pattern_row):
        """
        Requires
        --------
        Valid WCS
        """
        # given
        ra, dec = pattern_row[1:3]
        x0, y0 = pattern_row[5:7]
        x1, y1 = pattern_row[7:9]

        ra_width = (x1 - x0) * self.PAR.wcs.proj_plane_pixel_scales()[0].value
        dec_length = (y1 - y0) * self.PAR.wcs.proj_plane_pixel_scales()[0].value

        center = SkyCoord(ra, dec, unit=(u.deg, u.deg), frame="fk5")
        sky_region = RectangleSkyRegion(center=center, width=ra_width*u.deg, height=dec_length*u.arcsec)
        return sky_region



    @check_enabled
    def create_pattern_series_from_traces(self):
        """
        Input: Primary DMD pattern that is shown in the display.

        Returns
        -------
        Series of patterns from a main FOV pattern where each new pattern
        contains slits with no risk of overlapping spectra.
        """
        random.seed(138578028235)
        self.remove_traces()
        self.slits_only()
        self.logger.info("Creating pattern series. Current pattern is {}".format(self.base_pattern_name_entry.get()))

        self.DMD_Group = DMDGroup(self.slit_tab_view.slitDF, self.logger, regfile=self.loaded_reg_file_path)
        good_patterns = [self.slit_tab_view.slitDF]
        redo_pattern = self.slit_tab_view.slitDF.copy()
        base_name = self.base_pattern_name_entry.get()
        if (base_name != "Base Pattern Name" and base_name.strip() != ""):
            basename = "{}".format(base_name.replace(" ", "_"))
        else:
            basename = "Pattern"

        pattern_name_txt = "{}_{}"
        self.pattern_group["values"] = "MainPattern"
        self.sub_pattern_names = ["MainPattern"]
        pattern_num = 0
        while len(redo_pattern) > 0:
            pattern_num += 1
            good_pattern, redo_pattern = self.DMD_Group.pass_through_current_slits(redo_pattern)
            good_patterns.append(good_pattern)
            pattern_name = pattern_name_txt.format(basename, pattern_num)
            self.sub_pattern_names.append(pattern_name)
            self.pattern_group["values"] += (pattern_name,)
        self.pattern_series = good_patterns
        
        drawcolors = deepcopy(NICE_COLORS_LIST)
        for pattern, pattern_name in zip(self.pattern_series[1:], self.sub_pattern_names[1:]):
            c = random.choice(drawcolors)
            drawcolors.remove(c)
            tags = ["@{}".format(int(obj_num)) for obj_num in pattern.object.values]
            for tag in tags:
                obj = self.canvas.get_object_by_tag(tag)
                obj.color = c
                obj.alpha = 1
                obj.tag = '@slit_{}_{}'.format(pattern_name, obj.tag[1:])


    @check_enabled
    def selected_dmd_group_pattern(self, event):
        self.slits_only()
        pattern_list_index = self.pattern_group.current()
        current_pattern = self.pattern_series[pattern_list_index]
        pattern_name = self.sub_pattern_names[pattern_list_index]
        current_pattern_objects = self.canvas.get_objects_by_tag_pfx(f"slit_{pattern_name}")

        # Set current pattern to opaque
        for obj in current_pattern_objects:
            obj.alpha = 1

        # Set all other patterns to transparent
        for obj in CM.CompoundMixin.get_objects(self.canvas):
            if pattern_name not in obj.tag:
                obj.alpha = 0

        self.canvas.redraw()


    @check_enabled
    def apply_to_all(self):
        """ apply the default slit width/length to all slits """
        self.slits_only()

        # do the change
        xr = self.slit_xd.get()/2.
        yr = self.slit_disp.get()/2.
        CM.CompoundMixin.set_attr_all(self.canvas, xradius=xr, yradius=yr)
        self.canvas.redraw()
        updated_objs = CM.CompoundMixin.get_objects(self.canvas)
        viewer_list = np.full(len(updated_objs), self.canvas.viewer)
#         np.array(list(map(self.slit_tab_view.update_table_from_obj, updated_objs, viewer_list)))


    @check_enabled
    def get_dmd_coords_of_picked_slit(self, picked_slit):
        """ get_dmd_coords_of_picked_slit """
        x0, y0, x1, y1 = picked_slit.get_llur()
        fits_x0, fits_y0 = x0 + 1, y0 + 1
        fits_x1, fits_y1 = x1 + 1, y1 + 1
        fits_xc, fits_yc = picked_slit.get_center_pt() + 1

        dmd_xc, dmd_yc = ccd_to_dmd(fits_xc, fits_yc, self.PAR.dmd_wcs)
        dmd_x0, dmd_y0 = ccd_to_dmd(fits_x0, fits_y0, self.PAR.dmd_wcs)
        dmd_x1, dmd_y1 = ccd_to_dmd(fits_x1, fits_y1, self.PAR.dmd_wcs)

        dmd_width = int(np.ceil(dmd_x1 - dmd_x0))
        dmd_length = int(np.ceil(dmd_y1 - dmd_y0))

        return dmd_xc, dmd_yc, dmd_x0, dmd_y0, dmd_x1, dmd_y1, dmd_width, dmd_length


    @check_enabled
    def slit_width_length_adjust(self, event=None):
        if self.selected_object_tag is None:
            self.logger.error("Trying to adjust width of selected slit with no slit selected.")
            return

        picked_slit = self.canvas.get_object_by_tag(self.selected_object_tag)

        current_dmd_width = self.width_adjust_btn.get()
        current_dmd_length = self.length_adjust_btn.get()

        half_current_dmd_width = current_dmd_width // 2
        half_current_dmd_length = current_dmd_length // 2

        fits_xc, fits_yc = picked_slit.get_center_pt()
        dmd_xc, dmd_yc = ccd_to_dmd(fits_xc + 1, fits_yc + 1, self.PAR.dmd_wcs)

        dmd_x0 = dmd_xc - half_current_dmd_width
        dmd_y0 = dmd_yc - half_current_dmd_length
        dmd_x1 = dmd_xc + half_current_dmd_width
        dmd_y1 = dmd_yc + half_current_dmd_length

        fits_x0, fits_y0 = dmd_to_ccd(dmd_x0 - 1, dmd_y0 - 1, self.PAR.dmd_wcs)
        fits_x1, fits_y1 = dmd_to_ccd(dmd_x1 - 1, dmd_y1 - 1, self.PAR.dmd_wcs)

        fits_length = np.ceil(fits_y1 - fits_y0)
        fits_width = np.ceil(fits_x1 - fits_x0)

        picked_slit.xradius = fits_width / 2
        picked_slit.yradius = fits_length / 2

        self.canvas.set_draw_mode('draw')
        self.canvas.set_draw_mode('pick')

#         obj_ind = list(self.slit_tab_view.stab.get_column_data(0)).index(self.selected_object_tag.strip("@"))
#         imcoords_txt_fmt = "{:.2f}"
# 
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=5, redraw=True, value=imcoords_txt_fmt.format(fits_x0))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=6, redraw=True, value=imcoords_txt_fmt.format(fits_y0))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=7, redraw=True, value=imcoords_txt_fmt.format(fits_x1))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=8, redraw=True, value=imcoords_txt_fmt.format(fits_y1))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=11, redraw=True, value=int(dmd_x0))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=12, redraw=True, value=int(dmd_y0))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=13, redraw=True, value=int(dmd_x1))
#         self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=14, redraw=True, value=int(dmd_y1))


    @check_enabled
    def pick_cb(self, obj, canvas, event, pt, ptype):
        self.logger.info(f"Pick {ptype} on object {obj.tag} of kind {obj.kind} at ({pt[0]}, {pt[1]})")
        if (hasattr(self, "selected_object_tag")) and (self.selected_object_tag is not None):
            self.logger.info("Unselecting existing selection")
            canvas.get_object_by_tag(self.selected_object_tag).color = 'red'
            canvas.clear_selected()

        if self.slit_mode.get() == "delete":
            if obj is not None:
                canvas.delete_object(obj)
                return True
        
        if self.slit_mode.get() == "pick":
            print("pick a ball of cotton....")

        canvas.select_add(obj.tag)
        self.selected_object_tag = obj.tag
        obj.color = 'green'

        canvas.set_draw_mode('draw')
        canvas.set_draw_mode('pick')

        self.obj_ind = int(obj.tag.strip('@'))-1
#         try:
#             self.tab_row_ind = self.slit_tab_view.stab.get_column_data(0).index(obj.tag.strip('@'))
#             dmd_x0, dmd_x1 = self.slit_tab_view.slitDF.loc[self.obj_ind, ['dmd_x0', 'dmd_x1']].astype(int)
#             dmd_y0, dmd_y1 = self.slit_tab_view.slitDF.loc[self.obj_ind, ['dmd_y0', 'dmd_y1']].astype(int)
#             dmd_width = int(dmd_x1-dmd_x0)
#             dmd_length = int(dmd_y1-dmd_y0)
#             self.slit_xd.set(dmd_width)
#             self.slit_disp.set(dmd_length)
#         except Exception as e:
#             self.logger.error(f"ERROR {e} when updating slit view table")

        if ptype == 'up' or ptype == 'down':
            canvas.delete_object(obj)
#             try:
#                 self.slit_tab_view.stab.select_row(row=self.tab_row_ind)
#                 self.slit_tab_view.stab.delete_row(self.tab_row_ind)
#                 self.slit_tab_view.stab.redraw()
#                 self.slit_tab_view.slitDF = self.slit_tab_view.slitDF.drop(index=self.obj_ind)
#                 self.slit_tab_view.slit_obj_tags.remove(self.selected_object_tag)
#                 canvas.clear_selected()
# 
#                 try:
#                     for si in range(len(self.pattern_series)):
#                         sub = self.pattern_series[si]
#                         tag = int(obj.tag.strip("@"))
#                         if tag in sub.object.values:
#                             sub_ind = sub.where(sub.object == tag).dropna(how="all").index.values[0]
#                             sub = sub.drop(index=sub_ind)
#                             self.pattern_series[si] = sub
#                 except Exception as e:
#                     self.logger.error(f"Error {e} while looping through sub-patterns")
#             except Exception as e:
#                 self.logger.error(f"Error {e} (possibly slit table does not exist)")
#                 print("No slit table created yet.")
        return True


    @check_enabled
    def edit_cb(self, obj):
        self.logger.info(f"Object {obj.kind} with tag {obj.tag} has been edited")
#         tab_row_ind = list(self.slit_tab_view.stab.get_column_data(0)).index(int(obj.tag.strip("@")))
#         self.slit_tab_view.stab.select_row(row=tab_row_ind, redraw=True)
#         self.slit_tab_view.update_table_row_from_obj(obj, self.fits_image)
        return True


#     @check_enabled
#     def initialize_slit_table(self):
#         if (not hasattr(self, "slit_window")) or (self.slit_window is None):
#             self.slit_window = tk.Toplevel()
#             self.slit_window.title("Slit Table")
#             self.slit_window.geometry("700x407")
#             self.slit_tab_view = STView(self.slit_window, self.parent, self.PAR, self.logger)
#             self.slit_window.withdraw()


#     @check_enabled
#     def show_slit_table(self):
#         try:
#             self.slit_window.deiconify()
#         except AttributeError as e:
#             self.logger.warning("No slits to show in slit table")
#         except Exception as e:
#             # need to remake the table viewing window if it is destroyed
#             if not self.slit_window.winfo_exists():
#                 # preserve the slit data frame so it is republished in the new window
#                 current_slitDF = self.slit_tab_view.slitDF
#                 self.initialize_slit_table()
#                 self.slit_tab_view.slitDF = current_slitDF
#                 # re-add the table rows
#                 if not self.slit_tab_view.slitDF.empty:
#                     self.slit_tab_view.recover_window()
#                 self.slit_window.deiconify()


    @check_enabled
    def load_slits(self):
        filename_slits = tk.filedialog.askopenfilename(
            initialdir=get_data_file("dmd.scv.slits"),
            title="Select a File",
            filetypes=(("Text files", "*.csv"), ("all files", "*.*"))
        )
        self.saved_slit_file_path = Path(filename_slits)
        self.saved_slit_file.set(self.saved_slit_file_path.name)

        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index), int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in table.index:
            slit_shape[x1[i]:x2[i], y1[i]:y2[i]] = 0
        self.push_slits(slit_shape)
        # Create a photoimage object of the image in the path
        image_map = Image.open(get_data_file("dmd", "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)
        image_map.close()


    @check_enabled
    def save_slit_table(self):
        file = tk.filedialog.asksaveasfile(filetypes=[("csv file", ".csv")],
                                           defaultextension=".csv",
                                           initialdir=get_data_file("dmd.scv.slits"),
                                           initialfile=self.filename_regfile_RADEC[0:-4]+".csv")
        slit_shape = self.collect_slit_shape()
        pandas_slit_shape = pd.DataFrame(slit_shape)
        pandas_slit_shape.to_csv(file.name)


    @check_enabled
    def load_masks_file_HTS(self):
        """load_masks_file for upload on DMD"""
        filename_masks = tk.filedialog.askopenfilename(initialdir=get_data_file('hadamard.mask_sets'),
                                                       title="Select a File",
                                                       filetypes=(("Text files", "*.bmp"),
                                                                  ("all files", "*.*")))
        self.current_mask_file_path = Path(filename_masks)
        self.current_mask_file.set(self.current_mask_file_path.name)


    @check_enabled
    def push_masks_file_HTS(self):
        slit_shape = np.asarray(Image.open(self.current_mask_file_path), dtype='int')
        self.push_slits(slit_shape)


    @check_enabled
    def next_masks_file_HTS(self):
        """look at the currently loaded mask and push the next one to the DMD"""
        # => find all positions of the '_' string in the filename
        i_ = [x for x, v in enumerate(self.current_mask_file.get()) if v == '_']

        # identify order, "signature ("a", "b", or "_" for H and S matrices) and counter of the current mask
        order = self.tail_HTS[1:i_[0]]
        ab_ = self.tail_HTS[i_[-1]-1]
        counter = self.tail_HTS[i_[-1]+1:i_[-1]+4]

        # if we have reached the last mask and we are not in Hmask_a, exit with message
        if ((int(counter) == int(order)) and (ab_ != 'a')):
            self.logger.warning("Tried to get next mask from last mask file")
            ttk.messagebox.showinfo(title='No Next Mask', message='This is the last mask in the series')
            return

        # increment and set as the current mask:
        str1 = self.tail_HTS
        list1 = list(str1)
        if ab_ == 'a':  # Hmask_a goes to Hmask_b
            list1[i_[-1]-1] = 'b'
        elif ab_ == 'b':  # Hmask_b goes to Hmask_a with increment of counter
            list1[i_[-1]-1] = 'a'
            counter_plus1 = "{:03d}".format(int(counter)+1)
            list1[i_[-1]+1:i_[-1]+4] = list(counter_plus1)
        else:  # Smask increment of counter
            counter_plus1 = "{:03d}".format(int(counter)+1)
            list1[i_[-1]+1:i_[-1]+4] = list(counter_plus1)
        new_mask_file = ''.join(list1)
        self.current_mask_file_path = self.current_mask_file_path.parent + new_mask_file
        self.current_mask_file.set(self.current_mask_file_path.name)
        # Push to the DMD
        self.push_masks_file_HTS()


    @check_enabled
    def _set_expnum(self):
        min_num = 0
        self.logger.info(f"Checking directory {self.PAR.fits_dir}")
        current_files = self.PAR.fits_dir.glob("*.fits")
        for file in current_files:
            self.logger.info(f"Checking exposure number in {file}")
            num_results = list(map(str, re.findall(r"_\d+_", file.name)))
            for str_num in num_results:
                number = int(str_num[1:-1])
                self.logger.info(f"\tFound number {number}")
                if number > min_num:
                    min_num = number
        min_num += 1
        self.logger.info(f"Setting minimum exposure number to {min_num}")
        self.expnum.config(from_=min_num)
        if self.image_expnum.get() < min_num:
            self.image_expnum.set(min_num)
        self.expnum.configure(from_=min_num)


    def update_status_box(self):
        if (datetime.now() - self.last_update_time).seconds > 5:
            self.last_update_time = datetime.now()
            self.PCM.update_status()
        if self.PCM.is_on:
            self.status_box.itemconfig("filter_ind", fill=INDICATOR_LIGHT_ON_COLOR)
            self.status_box.itemconfig("grism_ind", fill=INDICATOR_LIGHT_ON_COLOR)
            if self.PCM.filter_moving:
                self.status_box.itemconfig("filter_ind", fill=INDICATOR_LIGHT_PENDING_COLOR)
            if self.PCM.grism_moving:
                self.status_box.itemconfig("grism_ind", fill=INDICATOR_LIGHT_PENDING_COLOR)
            self.current_filter.set(self.PCM.get_filter_label())
            self.current_grating.set(self.PCM.get_grating_label())
        else:
            self.status_box.itemconfig("filter_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
            self.status_box.itemconfig("grism_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.DMD.is_on:
            self.status_box.itemconfig("mirror_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("mirror_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.SOAR.is_on:
            self.status_box.itemconfig("tcs_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("tcs_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        self.status_box.update()
