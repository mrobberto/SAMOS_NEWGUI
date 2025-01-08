"""
SAMOS Main tk Frame Class
"""
from copy import deepcopy
import csv
from datetime import datetime
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
import pandas as pd
from PIL import Image, ImageTk
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
import ttkbootstrap as ttk
from samos.dmd.utilities import DMDGroup
from samos.ui.slit_table_view import SlitTableView as STView
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.utils import ccd_to_dmd, dmd_to_ccd
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled
from .progress_windows import ExposureProgressWindow
from .gs_query_frame import GSQueryFrame


class MainPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Main Frame", **kwargs)
        self.previous_image_name = ""
        self.selected_object_tag = None
        self.last_update_time = datetime.now()
        
        self.initialize_slit_table()

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

        # Filter and Grating Status
        frame = ttk.LabelFrame(fleft, text="Filter and Grating Status")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Filter
        filter_frame = ttk.Label(frame, text="Filter")
        filter_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.filter_data = ascii.read(get_data_file("system", 'SAMOS_Filter_positions.txt'))
        filter_names = list(self.PCM.FILTER_WHEEL_MAPPINGS.keys())
        self.current_filter = self.make_db_var(tk.StringVar, "pcm_filter", filter_names[2])
        ttk.Label(filter_frame, text="Current Filter:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        l = tk.Label(filter_frame, textvariable=self.current_filter, font=('Georgia 20'), bg='white', fg='green')
        l.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.filter_option_menu = ttk.OptionMenu(filter_frame, self.current_filter, None, *filter_names)
        self.filter_option_menu.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(filter_frame, text="Set Filter", command=self.set_filter, bootstyle="success")
        b.grid(row=2, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True)]
        # Grating
        grating_frame = ttk.Label(frame, text="Grating")
        grating_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        grating_names = list(self.PCM.GRISM_RAIL_MAPPINGS.keys())
        self.grating_positions = list(self.filter_data['Position'][12:18])
        self.current_grating = self.make_db_var(tk.StringVar, "pcm_grating", grating_names[2])
        ttk.Label(grating_frame, text="Current Grating:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        l = tk.Label(grating_frame, textvariable=self.current_grating, font=('Georgia 20'), bg='white', fg='green')
        l.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.grating_option_menu = ttk.OptionMenu(grating_frame, self.current_grating, None, *grating_names)
        self.grating_option_menu.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(grating_frame, text="Set Grating", command=self.set_grating, bootstyle="success")
        b.grid(row=2, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True)]

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
        self.image_expnum = self.make_db_var(tk.IntVar, f"{self.PAR.today_str}_expnum", 1)
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
        ttk.Label(self.image_frame, text="Comments:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.image_comments = self.make_db_var(tk.StringVar, "POTN_Comment", "")
        tk.Entry(self.image_frame, textvariable=self.image_comments).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.image_save_single = self.make_db_var(tk.BooleanVar, "save_single_frames", False)
        c = tk.Checkbutton(self.image_frame, text="Save Single Frames", variable=self.image_save_single, onvalue=True, offvalue=False)
        c.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Take Exposure Frame
        exp_frame = ttk.LabelFrame(frame, text="Take Exposure")
        exp_frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        exp_frame.columnconfigure(0, weight=1)
        exp_frame.columnconfigure(1, weight=1)
        b = ttk.Button(exp_frame, text="START", command=self.start_an_exposure, bootstyle="success")
        b.grid(row=1, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)

        # FITS manager
        frame = ttk.LabelFrame(fleft, text="FITS Manager")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load Existing File", command=self.load_existing_file)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.fits_ra = self.make_db_var(tk.DoubleVar, "target_ra", 150.17110)
        ttk.Label(frame, text="RA:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.fits_ra).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.fits_dec = self.make_db_var(tk.DoubleVar, "target_dec", -54.79004)
        ttk.Label(frame, text="DEC:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.fits_dec).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.fits_nstars = self.make_db_var(tk.IntVar, "twirl_n_stars", 25)
        ttk.Label(frame, text="Number of Stars:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.fits_nstars).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        # Command Buttons
        b = ttk.Button(frame, text="twirl WCS", command=self.twirl_Astrometry)
        b.grid(row=4, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Send to SOAR", command=self.send_offset_to_soar, bootstyle="success")
        b.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.SOAR, "is_on", True)]
        """
        # QUERY Server
        self.gs_query_frame = GSQueryFrame(self, frame, self.Query_Survey, "target_ra", "target_dec", **self.samos_classes)
        self.gs_query_frame.grid(row=5, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        """
        # Chosen Star Frame
        cntr_frame = ttk.Frame(frame)
        cntr_frame.grid(row=6, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.ra_cntr = self.make_db_var(tk.DoubleVar, "centre_ra", self.fits_ra.get())
        ttk.Label(cntr_frame, text="CNTR RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(cntr_frame, textvariable=self.ra_cntr, w=6).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.x_offset = self.make_db_var(tk.DoubleVar, "centre_ra_offset_mm", 0.)
        ttk.Label(cntr_frame, text="X offset (arsec):").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        tk.Entry(cntr_frame, textvariable=self.x_offset, w=6).grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.dec_cntr = self.make_db_var(tk.DoubleVar, "centre_dec", self.fits_dec.get())
        ttk.Label(cntr_frame, text="CNTR DEC:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(cntr_frame, textvariable=self.dec_cntr, w=6).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.y_offset = self.make_db_var(tk.DoubleVar, "centre_dec_offset_mm", 0.)
        ttk.Label(cntr_frame, text="Y offset (arsec):").grid(row=1, column=2, sticky=TK_STICKY_ALL)
        tk.Entry(cntr_frame, textvariable=self.y_offset, w=6).grid(row=1, column=3, sticky=TK_STICKY_ALL)

        # Guide Star Probe Frame
        frame = ttk.LabelFrame(fleft, text="Guide Star Probe Setup")
        frame.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        # X_GSP00
        self.gs_x0 = tk.DoubleVar(self, 0.)
        ttk.Label(frame, text="X GSP00 (pix)").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_x0).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # Y GSP00
        self.gs_y0 = tk.DoubleVar(self, -0.)
        ttk.Label(frame, text="Y GSP00 (pix)").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_y0).grid(row=1, column=1, sticky=TK_STICKY_ALL)
       
        # CENTRE COLUMN

        # GINGA Display
        frame = ttk.LabelFrame(fctr, text="Display")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        # Image Canvas
        canvas = tk.Canvas(frame, bg="grey", width=528, height=518)
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
        self.canvas = self.canvas_types.DrawingCanvas()
        self.canvas.enable_draw(True)
        self.canvas.enable_edit(True)
        self.canvas.set_drawtype('box', color='red')
        self.canvas.register_for_cursor_drawing(fi)
        self.canvas.add_callback('draw-event', self.draw_cb)
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
        # Shape
        ttk.Label(frame, text="Shape:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.draw_type = self.make_db_var(tk.StringVar, "main_draw_type", "box")
        e = tk.Entry(frame, textvariable=self.draw_type)
        e.bind("<Return>", self.set_drawparams)
        e.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("tkvar", self.source_pickup_enabled, True)]
        # Colour
        self.draw_color = ttk.Combobox(frame, values=self.drawcolors, style="TCombobox")
        self.draw_color.current(self.drawcolors.index("red"))
        self.draw_color.bind("<<ComboboxSelected>>", self.set_drawparams)
        self.draw_color.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # Fill
        self.draw_fill = self.make_db_var(tk.BooleanVar, "main_draw_fill", False)
        c = tk.Checkbutton(frame, text="Fill", variable=self.draw_fill, onvalue=True, offvalue=False)
        c.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="Alpha:").grid(row=0, column=4, sticky=TK_STICKY_ALL)
        self.draw_alpha = self.make_db_var(tk.DoubleVar, "main_draw_alpha", 1.0)
        e = tk.Entry(frame, width=8, textvariable=self.draw_alpha)
        e.bind("<Return>", self.set_drawparams)
        e.grid(row=0, column=5, sticky=TK_STICKY_ALL)
        # Slit Configurations
        b = tk.Checkbutton(
            frame,
            text="Source Pickup",
            variable=self.source_pickup_enabled,
            command=self.set_slit_drawtype,
            onvalue=True,
            offvalue=False
        )
        b.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Buttons
        b = ttk.Button(frame, text="Show Traces", command=self.show_traces)
        b.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Remove Traces", command=self.remove_traces)
        b.grid(row=2, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Slits Only", command=self.slits_only)
        b.grid(row=2, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Clear Canvas", command=self.clear_canvas)
        b.grid(row=2, column=3, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Open File", command=self.open_quicklook_file)
        b.grid(row=2, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # Slit Configuration Frame
        frame = ttk.LabelFrame(fctr, text="Slit Configuration:")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        # Slit Size Controls
        slit_frame = ttk.LabelFrame(frame, text="Slit Size")
        slit_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.slit_w = self.make_db_var(tk.IntVar, "dmd_hadamard_width", 3)
        ttk.Label(slit_frame, text="Slit Width (mirrors):").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Spinbox(slit_frame, command=self.slit_width_length_adjust, increment=1, textvariable=self.slit_w, width=5, 
                        from_=0, to=1080)
        b.bind("<Return>", self.slit_width_length_adjust)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("is_something", self.selected_object_tag)]
        self.slit_l = self.make_db_var(tk.IntVar, "dmd_hadamard_length", 9)
        ttk.Label(slit_frame, text="Slit Length (mirrors):").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        b = tk.Spinbox(slit_frame, command=self.slit_width_length_adjust, increment=1, textvariable=self.slit_w, width=5, 
                        from_=0, to=1080)
        b.bind("<Return>", self.slit_width_length_adjust)
        b.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("is_something", self.selected_object_tag)]
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
        # Misc
        b = ttk.Button(frame, text="View Slit Table", command=self.show_slit_table)
        b.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Find Stars", command=self.find_stars)
        b.grid(row=1, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        # Pattern Series
        pattern_frame = ttk.LabelFrame(frame, text="Create Pattern Series with No Overlapping Slits")
        pattern_frame.grid(row=0, column=1, rowspan=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(pattern_frame, text="Generate Patterns", command=self.create_pattern_series_from_traces)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("valid_file", self.loaded_reg_file_path)]
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

        # RIGHT COLUMN

        # RADEC Module
        frame = ttk.LabelFrame(fright, text="Sky Regions (RA, DEC)")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load Regions from DS9/RADEC Region File", command=self.load_regions_radec)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="Loaded Region File:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, textvariable=self.loaded_reg_file).grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Get Centre/Point from Filename", command=self.push_RADEC)
        b.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        l = ttk.Label(frame, text="Point, take and image, and twirl WCS from GAIA")
        l.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Convert DS9 Regions -> Ginga", command=self.load_region_file)
        b.grid(row=5, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("valid_wcs", self.PAR), ("valid_file", self.loaded_reg_file_path)]
        b = ttk.Button(frame, text="Save Ginga Regions -> DS9 Region File", command=self.save_ginga_regions_wcs)
        b.grid(row=6, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("valid_wcs", self.PAR)]

        # CCD Module
        frame = ttk.LabelFrame(fright, text="CCD Regions (x, y)")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Load (x, y) Regions from DS9 Region file", command=self.load_regions_pix)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("valid_wcs", self.PAR)]
        self.loaded_ginga_file = self.make_db_var(tk.StringVar, "dmd_loaded_ginga_file", "none")
        self.loaded_ginga_file_path = None
        ttk.Label(frame, text="Loaded File in CCD Units:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, textvariable=self.loaded_ginga_file).grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="Save Ginga Regions -> DS9 Region File", command=self.save_ginga_regions_pix)
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
        self.check_widgets[b] = [("valid_file", self.saved_slit_file_path)]
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
        self.check_widgets[b] = [("valid_file", self.current_slit_file_path)]

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
        self.check_widgets[b] = [("valid_file", self.current_mask_file_path)]
        # Next Mask
        b = ttk.Button(frame, text="Next Mask", command=self.next_masks_file_HTS)
        b.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("valid_file", self.current_mask_file_path)]

        # Status Indicator Frame
        frame = ttk.LabelFrame(fright, text="STATUS")
        frame.grid(row=5, column=0, sticky=TK_STICKY_ALL)
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
        self.PAR.add_status_indicator(self.status_box, self.update_status_box)
        # Give the PCM class a copy of the status box so that it can set colours as well.
        self.PCM.initialize_indicator(self.status_box)
        self.set_enabled()

    """
    def send_to_soar(self):
        
        # Send the currently set target to SOAR with a move command.
        
        target = {
            "ra": self.db.get_value("target_ra"),
            "dec": self.db.get_value("target_dec"),
            "epoch": self.db_get_value("target_epoch"),
            "ra_rate": 0.,
            "dec_rate": 0.
        }
        self.SOAR.target_move(target)
    """
    @check_enabled
    def send_offset_to_soar(self):
        #push the calculated offsets in to the TCS page
        #THIS HAS TO BE FIXED: we need to send the RA,DEC to the SOAR TCS only if TCS is active
        d_ra = self.x_offset.get()
        d_dec = self.y_offset.get()
        message = { "offset_ra": float(d_ra), "offset_dec": float(d_dec) }
        return_meesage_from_TCS =  self.SOAR_PAGE.Offset_option_TCS(message)
        print(return_meesage_from_TCS)


    @check_enabled
    def save_ginga_regions_pix(self):
        """
        Save regions defined on the current canvas (and thus in Ginga (x, y) co-ordinates)
        to an astropy regions (.reg) file. This requires converting the region co-ordinates
        (using the Ginga utilities).
        """
        self.logger.info("Saving Canvas Regions to Astropy File (pixel format)")
        save_file = tk.filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                                defaultextension=".reg",
                                                initialdir=get_data_file("regions.pixels"))
        ginga_regions = CM.CompoundMixin.get_objects(self.canvas)
        astropy_regions_pix = Regions([g2r(r) for r in ginga_regions])
        astropy_regions_pix.write(save_file.name, overwrite=True)
        self.logger.info("Saved regions to {}".format(save_file.name))


    @check_enabled
    def save_ginga_regions_wcs(self):
        """ 
        As above but save to ra/dec (WCS-enabled) regions instead of pixel-on-image regions.
        
        Requires
        --------
        - valid WCS
        """
        self.logger.info("Saving Canvas Regions to Astropy File (WCS format)")
        save_file = tk.filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                                defaultextension=".reg",
                                                initialdir=get_data_file("regions.radec"))
        ginga_regions = CM.CompoundMixin.get_objects(self.canvas)
        astropy_regions_pix = Regions([g2r(r) for r in ginga_regions])
        astropy_regions_wcs = Regions([r.to_sky(self.PAR.WCS) for r in astropy_regions_pix])
        astropy_regions_wcs.write(save_file.name, overwrite=True)
        self.logger.info("Saved regions to {}".format(save_file.name))


    @check_enabled
    def load_region_file(self):
        """ 
        converting ds9/radec Regions to AP/radec Regions
        - open ds9/radec region file and convert to AP/xy (aka RRR_xyAP)
        - convert AP/xy to Ginga/xy (aka RRR_xyGA)
        - convert AP/xy to AP/ad (aka RRR_RADec)
        
        Requires
        --------
        - valid WCS
        - Region File
        """
        self.logger.info("Displaying DS9 Region File on canvas")
        astropy_regions_wcs = Regions.read(self.loaded_reg_file_path, format='ds9')
        astropy_regions_pix = Regions([r.to_pixel(self.PAR.WCS) for r in astropy_regions_wcs])
        self.logger.info("Loaded file {}".format(self.loaded_reg_file_path))
        ginga_regions = self.convert_astropy_to_ginga_pix(astropy_regions_pix)
        self.logger.info("Converted Astropy pixel regions to Ginga")
        if self.slit_tab_view is None:
            self.initialize_slit_table()
        self.slit_tab_view.load_table_from_regfile_RADEC(regs_RADEC=astropy_regions_wcs, img_wcs=self.PAR.wcs)
        self.logger.info("Finished displaying regions and loading slit tab view")


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
            ginga_objects.append(ginga_object)
            self.canvas.add(ginga_object, tag='@{}_{}'.format(tag, i))
        return ginga_objects


    @check_enabled
    def push_RADEC(self):
        """
        Load canvas RA/DEC from entries
        """
        self.fits_ra.set(self.ra_cntr.get())
        self.fits_dec.set(self.dec_cntr.get())


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
        self.loaded_reg_file.set(self.loaded_reg_file_path.name)
        initial_regions = Regions.read(self.loaded_reg_file_path, format='ds9')
        astropy_regions_radec = Regions()
        for region in initial_regions:
            if region not in astropy_regions_radec:
                astropy_regions_radec.append(region)
        self.target_name = self.loaded_reg_file_path.name[:self.loaded_reg_file_path.name.find("_")]
        self.db.update_value("POTN_Target", self.target_name)
        if self.image_type.get() == "Science":
            self.image_name.set(self.target_name)
        if "RADEC=" in self.loaded_reg_file_path.name:
            radec_str = self.loaded_reg_file_path.name
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
            self.ra_cntr.set(ra)
            self.dec_cntr.set(dec)
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
        reg_file = tk.filedialog.askopenfilename(filetypes=[("region files", "*.reg")],
                                                 initialdir=get_data_file("regions.pixels"))
        self.loaded_ginga_file_path = Path(reg_file)
        self.loaded_ginga_file.set(self.loaded_ginga_file_path.name)
        initial_regions = Regions.read(self.loaded_ginga_file_path, format="ds9")
        astropy_regions_pix = Regions()
        for region in initial_regions:
            if region not in astropy_regions_pix:
                astropy_regions_pix.append(region)
        if self.slit_tab_view is None:
            self.initialize_slit_table()
        self.slit_tab_view.load_table_from_regfile_CCD(regs_CCD=asatropy_regions_pix, img_wcs=self.PAR.wcs)
        ginga_regions = self.convert_astropy_to_ginga_pix(astropy_regions_pix)
        self.loaded_ginga_regions = ginga_regions


    @check_enabled
    def collect_slit_shape(self):
        """
        collect selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        self.logger.info("Collecting Slit")
        objects = CM.CompoundMixin.get_objects(self.canvas)
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
            elif self.source_pickup_enabled.get() and obj.kind == 'point':
                x1, y1 = ccd_to_dmd(ccd_x0, ccd_y0, self.PAR.dmd_wcs)
                x1, y1 = int(np.floor(x1)), int(np.floor(y1))
                x2, y2 = ccd_to_dmd(ccd_x1, ccd_y1, self.PAR.dmd_wcs)
                x2, y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                # 3 load the slit pattern
                data_box = self.AstroImage.cutout_shape(obj)
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
        return slit_shape


    @check_enabled
    def push_slit_shape(self):
        """
        push selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        self.logger.info("Pushing slit shape to DMD")
        self.remove_traces()
        slit_shape = self.collect_slit_shape()
        self.push_slits(slit_shape)
                

    @check_enabled
    def push_slits(self, slit_shape):
        """ Actual push of the slit_shape to the DMD """
        self.logger.info("Applying slit shape to DMD")
        self.DMD.initialize()
        self.DMD._open()
        self.DMD.apply_shape(slit_shape)


    @check_enabled
    def set_filter(self):
        self.logger.info("Setting Filter to {}".format(self.current_filter.get()))
        new_filter = self.current_filter.get()
        self.main_fits_header.set_param("filter", new_filter)
        filter_pos = self.PCM.FILTER_WHEEL_MAPPINGS[new_filter.lower()]
        self.main_fits_header.set_param("filtpos", f"{filter_pos[0]},{filter_pos[1]}")
        command_status = self.PCM.move_filter_wheel(new_filter)
        self.logger.info("Motors returned {}".format(command_status))
        self.extra_header_params += 1
        entry_string = PARAM_ENTRY_FORMAT.format(self.extra_header_params, 'String', 'FILTER', new_filter, 'Selected filter')
        self.header_entry_string += entry_string


    @check_enabled
    def set_grating(self):
        self.logger.info("Setting Grating to {}".format(self.current_grating.get()))
        new_grating = self.current_grating.get()
        self.main_fits_header.set_param("grating", new_grating)
        grating_pos = self.PCM.GRISM_RAIL_MAPPINGS[new_grating.lower()]
        self.main_fits_header.set_param("gratpos", f"{grating_pos[0]},{grating_pos[1]}")
        command_status = self.PCM.move_grism_rails(new_grating)
        self.logger.info("Motors returned {}".format(command_status))
        self.extra_header_params += 1
        entry_string = PARAM_ENTRY_FORMAT.format(self.extra_header_params, 'String', 'GRISM', new_grating, 'Grism position')
        self.header_entry_string += entry_string


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
    def start_an_exposure(self):
        """ 
        This is the landing procedure after the START button has been pressed
        """
        self.update_PotN()   #The Function update_PotN() is no more present...
        if (not self.CCD.initialized) or (not self.CCD.ccd_on):
            # Open a test image
            image_to_open = tk.filedialog.askopenfilename(filetypes=[("allfiles", "*"), ("fitsfiles", "*.fits")])
            self.Display(image_to_open)
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
        exp_window = ExposureProgressWindow(self, self.CCD, self.PAR, self.db, self.main_fits_header, self.DMD, self.logger)
        exp_window.start_exposure(self.image_type.get(), **exposure_params)


    @check_enabled
    def display_exposure(self, results):
        self.handle_log(results["images"])
        self.Display(self.fits_image_ql)
        self.fits_image.rotate(self.PAR.Ginga_PA)
        self._set_expnum()


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
        with open(self.PAR.logbook_name, 'a') as logbook:
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
        self.AstroImage = load_data(imagefile, logger=self.logger)
        self.fits_image.set_image(self.AstroImage)
        self.fits_image_ql = imagefile


    
    
    
    
    @check_enabled
    def load_existing_file(self):
#        loaded_file = ttk.filedialog.askopenfilename(initialdir=self.PAR.QL_images, title="Select a File",
        loaded_file = tk.filedialog.askopenfilename(title="Select a File",
                                                    filetypes=(("fits files", "*.fits"), ("all files","*.*")))
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
            header = hdul[0].header
            data = hdul[0].data
        
        img_wcs = wcs.WCS(header)
        ra, dec = img_wcs.all_pix2world([[data.shape[0] / 2, data.shape[1] / 2]], 0)[0]

        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # not all headers use ra,dec
        try:  #good header...
            ra, dec = header["RA"], header["DEC"]
            print(ra,dec)
            self.fits_ra.set(ra)
            self.fits_dec.set(dec)
        except:
            print("no RA and  DEC in the FITS header")
        if  self.fits_ra.get() !=  '' and self.fits_dec.get() != '':   
            ra = self.fits_ra.get()
            dec = self.fits_dec.get()
            print("RA and DEC read from the text box")

        #MOST IMPORTANT, WE HOPE TO GET THE POINTED RADEC FROM SOAR TCS...   
        elif self.SOAR.is_on == True:               #was self.PAR.inoutvar.get() == "inside": 
            infoa_dict = self.SOAR_PAGE.Handle_Infox('INFOA')  # TO BE FIXED: we need to grab the INFOA message from the SOAR TCS
            ra=infoa_dict['MOUNT_RA']                          # to extract the pointed RA,DEC coordinates 
            dec=infoa_dict['MOUNT_DEC']
            self.fits_ra.set(ra)
            self.fits_dec.set(dec)
            print("RADEC provided by the SOAR TCS")               
        else:   
            messagebox.showinfo(title=None, message="cannot find RADEC, enter by hand")
            return

        print("Pointed coordinates: ",ra,dec)
        #<<<<<<<<<<<<<<<<<<<<

        center = SkyCoord(ra, dec, unit=[u.deg, u.deg])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        shape = data.shape
        fov = 0.05

        self.canvas.delete_all_objects(redraw=True)
        stars = twirl.find_peaks(data)[:self.fits_nstars.get()]
        radius_pix = 7
        regs = Regions([CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix) for x, y in stars])
        for i, reg in enumerate(regs):
            obj = r2g(reg)
            obj.color="red"
            self.canvas.add(obj, tag='@twirl_{}'.format(i))
        # we can now compute the WCS
        gaias = twirl.gaia_radecs(center, fov, limit=self.fits_nstars.get())
        self.PAR.wcs = twirl.compute_wcs(stars, gaias)

        # Lets check the WCS solution
        radius_pix = 21
        gaia_pixel = np.array(SkyCoord(gaias, unit="deg").to_pixel(self.PAR.wcs)).T
        regs_gaia = Regions([CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix) for x, y in gaia_pixel])
        for i, reg in enumerate(regs_gaia):
            obj = r2g(reg)
            obj.color = "green"
            self.canvas.add(obj, tag='@check_{}'.format(i))

        if self.PAR.wcs is None:
            self.PAR.valid_wcs = False
            self.logger.error("No valid WCS solution found.")
            return
        else:
            self.PAR.valid_wcs = True
            self.logger.info("Found WCS solution")
            
        hdu_wcs = self.PAR.wcs.to_fits()
        if self.loaded_reg_file_path is not None:
            hdu_wcs[0].header.set("dmdmap", self.loaded_reg_file_path.name)
        print(self.PAR.wcs)
        hdu_wcs[0].data = data  # add data to fits file
        #self.wcs_filename = get_fits_dir() / "WCS_{}_{}.fits".format(ra, dec)
        self.wcs_filename = str( get_fits_dir() / "WCS_{}_{}.fits".format(ra, dec) ) # I think it's better to just use the string
        hdu_wcs[0].writeto(self.wcs_filename, overwrite=True)

        self.Display(self.wcs_filename)
        self.fits_image.rotate(self.PAR.Ginga_PA)  
        
         #calculate the offset in mm between pointed and actual position for the GS
        #mywcs = wcs.WCS(header)
        # take the xy coordinates of the GS probe home, entered in the GSPage...
        x_GSP00 = self.gs_x0.get()
        y_GSP00 = self.gs_y0.get() 
        # determine the RA,DEC coordinates actually pointed by the telescope
        ra_tel, dec_tel = self.PAR.wcs.wcs_pix2world(x_GSP00,y_GSP00,0)
        x_pointed, y_pointed = self.PAR.wcs.wcs_world2pix(ra,dec,0)
        print(x_pointed,y_pointed,ra,dec)
        print(x_GSP00,y_GSP00,ra_tel,dec_tel)
        # calculate the offset in RADEC between the telescope and commanded positions
        Delta_ra = float(ra_tel) - float(ra)
        Delta_dec = float(dec_tel) - float(dec)
        #convert to arcseconds, taking into account that we want to account for the cos(dec) factor
        Delta_RA_arcsec = Delta_ra*3600.*np.cos(dec*math.pi/180.)
        Delta_DEC_arcsec = Delta_dec*3600.
        #display
        self.x_offset.set(Delta_RA_arcsec)
        self.y_offset.set(Delta_DEC_arcsec)
        print(Delta_RA_arcsec,Delta_DEC_arcsec)
        print('done')
        # ready to offset the telescope to the commanded position

        """ => SUPERSEDED BY THE ABOVE CODE
        #calculate the offset in mm between pointed and actual position for the GS
        mywcs = wcs.WCS(header)
        ra_cntr, dec_cntr = mywcs.all_pix2world([[data.shape[0] / 2, data.shape[1] / 2]], 0)[0]

        self.ra_cntr.set(ra)
        self.dec_cntr.set(dec)
        Delta_RA = ra - self.fits_ra.get()
        Delta_DEC = dec - self.fits_dec.get()
        Delta_RA_mm = round(Delta_RA * 3600 / SOAR_ARCS_MM_SCALE.value, 3)
        Delta_DEC_mm = round(Delta_DEC * 3600 / SOAR_ARCS_MM_SCALE.value, 3)
        self.x_offset.set(Delta_RA_mm)
        self.y_offset.set(Delta_DEC_mm)
        """
        





    @check_enabled
    def find_stars(self):
        self.Display(self.fits_image_ql)
        self.fits_image.rotate(self.PAR.Ginga_PA)  
        if self.slit_tab_view is None:
            self.initialize_slit_table()
        
        self.set_slit_drawtype()
        with fits.open(self.fits_image_ql) as hdul:
            header = hdul[0].header
            data = hdul[0].data

        ra, dec = header["RA"], header["DEC"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        shape = data.shape
        pixel_scale = SISI_PIXEL_SCALE
        fov = (np.max(shape) * u.pix * pixel.to(u.deg)).value

        # Let's find some stars and display the image
        self.canvas.delete_all_objects(redraw=True)
        threshold = 0.1
        stars = twirl.find_peaks(data, threshold)[:self.fits_nstars.get()]
        med = np.median(data)
        radius_pix = 20
        slit_width = self.slit_w.get()
        slit_height = self.slt_h.get()
        coords = [PixCoord(x, y) for x, y in stars]
        regions = Regions([RectanglePixelRegion(center=c, width=slit_width, height=slit_height, angle=0*u.deg) for c in coords])
        for i,region in enumerate(regions):
            obj = r2g(region)
            self.canvas.add(obj, tag='@star_{}'.format(i))
            obj.pickable = True
            obj.color = "red"
            obj.add_callback('pick-up', self.pick_cb, 'up')
            obj.add_callback('edited', self.edit_cb)
            self.slit_tab_view.add_slit_obj(region, obj.tag, self.fits_image)


    @check_enabled
    def open_quicklook_file(self):
        """ to be written """
        filename = tk.filedialog.askopenfilename(filetypes=[("allfiles", "*"),
                                                 ("fitsfiles", "*.fits")])
        self.Display(filename)
        if self.AstroImage.wcs.wcs.has_celestial:
            self.PAR.wcs = self.AstroImage.wcs.wcs
            self.PAR.valid_wcs = True


    @check_enabled
    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        # Get all slit objects
        slit_objects = self.canvas.get_objects_by_tag_pfx("slit")
        self.logger.info("Slit objects: {}".format(slit_objects))
        for canvas_object in self.canvas.objects:
            self.logger.info("Object is {} with tag {}".format(canvas_object, canvas_object.tag))
            if canvas_object not in slit_objects:
                self.logger.info("Not a slit object, deleting.")
                self.canvas.delete_object(canvas_object, redraw=True)


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
            self.ra_center, self.dec_center = image.pixtoradec(528, 516, format='str', coords='fits')
            text = f"(RA, DEC): ({ra_deg:8.4f}, {dec_deg:8.4f}). " + text
        except Exception as e:
            self.logger.error("Error {} in printing co-ordinates".format(e))
            text = "No Valid WCS. " + text
        self.readout.config(text=text)


    @check_enabled
    def set_slit_drawtype(self):
        self.slit_mode.set("draw")  # Possibly need to set self.draw_mode instead?
        self.set_mode_cb()
        if self.source_pickup_enabled.get():
            self.draw_type.set("point")
        else:
            self.draw_type.set("box")
        self.canvas.set_drawtype(self.draw_type.get())


    @check_enabled
    def set_mode_cb(self):
        mode = self.slit_mode.get()
        if mode != "draw":
            self.source_pickup_enabled.set(False)
        self.canvas.set_draw_mode(mode)


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
        if self.slit_tab_view is None:
            self.initialize_slit_table()
        
        if kind == "box" and self.source_pickup_enabled.get():
            # User drew a box in source-pickup mode (should never happen)
            self.logger.error("User created a box in source pickup mode.")
            try:
                r = g2r(obj)
            except ValueError as e:
                self.logger.error("Error {} converting box to astropy region".format(e))
                obj.kind = "box"

            new_obj = self.slit_handler(obj)
            self.slit_tab_view.add_slit_obj(g2r(new_obj), new_obj.tag, self.fits_image)
        elif self.source_pickup_enabled.get() and kind == 'point':
            # User clicked on a point in source pick-up mode.
            new_obj = self.slit_handler(obj)
            self.slit_tab_view.add_slit_obj(g2r(new_obj), new_obj.tag, self.fits_image)
        elif kind == "box" and not self.source_pickup_enabled.get():
            # a box is drawn but centroid is not searched, just drawn...

            # Declare the object as a slit by so tagging it
            obj.tag = '@slit_{}'.format(obj.tag)
            
            # the ginga object, a box, is converted to an astropy region
            r = g2r(obj)
            
            # the astropy object is added to the table
            self.slit_tab_view.add_slit_obj(r, obj.tag, self.fits_image)
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
            r = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)), width=40, height=40, angle=0*u.deg)
            # and we convert it to ginga.
            obj = r2g(r)
            self.canvas.add(obj)
        
        # time to do the math; collect the pixels in the Ginga box
        data_box = self.AstroImage.cutout_shape(obj)

        # we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.canvas, obj)

        # find the peak within the Ginga box
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        x1 = obj.x - obj.xradius
        y1 = obj.y - obj.yradius
        px, py = round(peaks[0][0]+x1), round(peaks[0][1]+y1)
        self.logger.info("Peak found at ({}, {}) with counts {}".format(px, py, img_data[px, py]))
        
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
        results = iq.evaluate_peaks(peaks, data_box)
        self.logger.debug("Full Evaluation: {}".format(results))
        self.logger.info("Peak Centroid: ({}, {})".format(results[0].objx, results[0].objy))
        self.logger.info("FWHM: {}, Peak Value: {}".format(results[0].fwhm, results[0].brightness))
        self.logger.info("Sky: {}, Background (median of region): {}".format(results[0].skylevel, results[0].background))
        self.logger.info("(RA, DEC) of fitted centroid: ({}, {})".format(self.AstroImage.pixtoradec(results[0].objx, results[0].objy)))

        # having found the centroid, we need to draw the slit
        slit_box = self.canvas.get_draw_class('box')
        xradius = self.slit_w.get() * 0.5 * DMD_MIRROR_TO_PIXEL_SCALE
        yradius = self.slit_l.get() * 0.5 * DMD_MIRROR_TO_PIXEL_SCALE
        new_obj = slit_box(x=results[0].objx + x1, y=results[0].objy + y1, xradius=xradius, yradius=yradius, color='red',
                           alpha=0.8, fill=False, angle=5*u.deg, pickable=True)
        self.canvas_add(new_obj, tag='@slit_{}-{}'.format(results[0].objx + x1, results[0].objy + y1))
        new_obj.add_callback('pick-up', self.pick_cb, 'up')
        new_obj.add_callback('pick-move', self.pick_cb, 'move')
        new_obj.add_callback('pick-key', self.pick_cb, 'key')
        new_obj.add_callback('edited', self.edit_cb)
        return new_obj


    @check_enabled
    def show_traces(self):
        """ Show Traces """
        # keep only the slits/boxes
        self.slits_only()

        # We want to create rectangles
        Rectangle = self.canvas.get_draw_class('rectangle')

        # we should hanve only boxes/slits
        for i, obj in enumerate(CM.CompoundMixin.get_objects(self.canvas)):
            if obj.alpha == 0:
                # ***** WHY?
                continue
            x1, x2 = round(obj.x) - 1024, round(obj.x) + 1024
            y1, y2 = round(obj.y) - obj.yradius, round(obj.y) + obj.yradius
            r = Rectangle(x1=x1, y1=y1, y2=y2, angle=0*u.deg, color='yellow', fill=1, fillalpha=0.5)
            self.canvas.add(r, tag=f'@trace_{i}')
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)


    @check_enabled
    def remove_traces(self):
        """ 
        Use "try:/except:"
        We may call this function just to make sure that the field is clean, so
        we do not need to assume that the traces have been created
        """
        trace_objects = self.canvas.get_objects_by_tag_pfx("trace")
        CM.CompoundMixin.delete_objects(self.canvas, trace_objects)


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
        xr = self.slit_w.get()/2.
        yr = self.slit_l.get()/2.
        CM.CompoundMixin.set_attr_all(self.canvas, xradius=xr, yradius=yr)
        self.canvas.redraw()
        updated_objs = CM.CompoundMixin.get_objects(self.canvas)
        viewer_list = np.full(len(updated_objs), self.canvas.viewer)
        np.array(list(map(self.slit_tab_view.update_table_from_obj, updated_objs, viewer_list)))


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
        if self.selected_obj_tag is None:
            self.logger.error("Trying to adjust width of selected slit with no slit selected.")
            return

        picked_slit = self.canvas.get_object_by_tag(self.selected_obj_tag)

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

        obj_ind = list(self.slit_tab_view.stab.get_column_data(0)).index(self.selected_obj_tag.strip("@"))
        imcoords_txt_fmt = "{:.2f}"

        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=5, redraw=True, value=imcoords_txt_fmt.format(fits_x0))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=6, redraw=True, value=imcoords_txt_fmt.format(fits_y0))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=7, redraw=True, value=imcoords_txt_fmt.format(fits_x1))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=8, redraw=True, value=imcoords_txt_fmt.format(fits_y1))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=11, redraw=True, value=int(dmd_x0))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=12, redraw=True, value=int(dmd_y0))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=13, redraw=True, value=int(dmd_x1))
        self.slit_tab_view.stab.set_cell_data(r=obj_ind, c=14, redraw=True, value=int(dmd_y1))


    @check_enabled
    def pick_cb(self, obj, canvas, event, pt, ptype):
        self.logger.info(f"Pick {ptype} on object {obj.tag} of kind {obj.kind} at ({pt[0]}, {pt[1]})")
        if self.selected_obj_tag is not None:
            self.logger.info("Unselecting existing selection")
            canvas.get_object_by_tag(self.selected_obj_tag).color = 'red'
            canvas.clear_selected()

        canvas.select_add(obj.tag)
        self.selected_obj_tag = obj.tag
        obj.color = 'green'

        canvas.set_draw_mode('draw')
        canvas.set_draw_mode('pick')

        self.obj_ind = int(obj.tag.strip('@'))-1
        try:
            self.tab_row_ind = self.slit_tab_view.stab.get_column_data(0).index(obj.tag.strip('@'))
            dmd_x0, dmd_x1 = self.slit_tab_view.slitDF.loc[self.obj_ind, ['dmd_x0', 'dmd_x1']].astype(int)
            dmd_y0, dmd_y1 = self.slit_tab_view.slitDF.loc[self.obj_ind, ['dmd_y0', 'dmd_y1']].astype(int)
            dmd_width = int(dmd_x1-dmd_x0)
            dmd_length = int(dmd_y1-dmd_y0)
            self.slit_w.set(dmd_width)
            self.slit_l.set(dmd_length)
        except Exception as e:
            self.logger.error(f"ERROR {e} when updating slit view table")

        if ptype == 'up' or ptype == 'down':
            canvas.delete_object(obj)
            try:
                self.slit_tab_view.stab.select_row(row=self.tab_row_ind)
                self.slit_tab_view.stab.delete_row(self.tab_row_ind)
                self.slit_tab_view.stab.redraw()
                self.slit_tab_view.slitDF = self.slit_tab_view.slitDF.drop(index=self.obj_ind)
                self.slit_tab_view.slit_obj_tags.remove(self.selected_obj_tag)
                canvas.clear_selected()

                try:
                    for si in range(len(self.pattern_series)):
                        sub = self.pattern_series[si]
                        tag = int(obj.tag.strip("@"))
                        if tag in sub.object.values:
                            sub_ind = sub.where(sub.object == tag).dropna(how="all").index.values[0]
                            sub = sub.drop(index=sub_ind)
                            self.pattern_series[si] = sub
                except Exception as e:
                    self.logger.error(f"Error {e} while looping through sub-patterns")
            except Exception as e:
                self.logger.error(f"Error {e} (possibly slit table does not exist)")
                print("No slit table created yet.")
        return True


    @check_enabled
    def edit_cb(self, obj):
        self.logger.info(f"Object {obj.kind} has been edited")
        tab_row_ind = list(self.slit_tab_view.stab.get_column_data(0)).index(int(obj.tag.strip("@")))
        self.slit_tab_view.stab.select_row(row=tab_row_ind, redraw=True)
        self.slit_tab_view.update_table_row_from_obj(obj, self.fits_image)
        return True


    @check_enabled
    def initialize_slit_table(self):
        if (not hasattr(self, "slit_window")) or (self.slit_window is None):
            self.slit_window = tk.Toplevel()
            self.slit_window.title("Slit Table")
            self.slit_window.geometry("700x407")
            self.slit_tab_view = STView(self.slit_window, self.parent, self.PAR, self.logger)
            self.slit_window.withdraw()


    @check_enabled
    def show_slit_table(self):
        try:
            self.slit_window.deiconify()
        except AttributeError as e:
            self.logger.warning("No slits to show in slit table")
        except Exception as e:
            # need to remake the table viewing window if it is destroyed
            if not self.slit_window.winfo_exists():
                # preserve the slit data frame so it is republished in the new window
                current_slitDF = self.slit_tab_view.slitDF
                self.initialize_slit_table()
                self.slit_tab_view.slitDF = current_slitDF
                # re-add the table rows
                if not self.slit_tab_view.slitDF.empty:
                    self.slit_tab_view.recover_window()
                self.slit_window.deiconify()


    @check_enabled
    def load_slits(self):
        filename_slits = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.scv.slits"),
                                                       title="Select a File",
                                                       filetypes=(("Text files", "*.csv"),
                                                                  ("all files", "*.*")))
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
        match_str = "*_" + "[0-9]" * 4 + ".fits"
        current_files = self.PAR.fits_dir.glob(match_str)
        for file in current_files:
            num_results = list(map(int, re.findall(r"\d+", file.name)))
            for number in num_results:
                if number > min_num:
                    min_num = number
        min_num += 1
        self.expnum.config(from_=min_num)
        if self.image_expnum.get() < min_num:
            self.image_expnum.set(min_num)


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
