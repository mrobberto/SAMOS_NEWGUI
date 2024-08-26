"""
SAMOS CCD tk Frame Class
"""
from astropy import units as u
import logging

import tkinter as tk
import ttkbootstrap as ttk
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class CCDPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "CCD Control", **kwargs)
        self.logger.debug('Initializing CCD control frame')

        # Initialize CCD Connection
        w = ttk.Button(self.main_frame, text="Initialize CCD Connection", command=self.initialize_ccd)
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self.CCD, "initialized", False)]

        # CAMERA ON/OFF SWITCH
        ttk.Label(self.main_frame, text="CCD", font=BIGFONT).grid(row=1, column=0, sticky=TK_STICKY_ALL)
        w = tk.Button(self.main_frame, image=self.cam_img, command=self.toggle_camera)
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self.CCD, "initialized", True)]
        self.button_camera = w

        # COOLER ON/OFF SWITCH
        ttk.Label(self.main_frame, text="Cooler", font=BIGFONT).grid(row=2, column=0, sticky=TK_STICKY_ALL)
        w = tk.Button(self.main_frame, image=self.cool_img, command=self.toggle_cooler)
        w.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self.CCD, "initialized", True)]
        self.button_cooler = w

        # COOLER TEMPERATURE SETUP AND VALUE
        self.Tset = tk.DoubleVar(self, -90)
        self.Tdet = tk.DoubleVar(self, 273)
        self.Tdet_c = tk.DoubleVar(self, 0)
        ttk.Label(self.main_frame, text="CCD Temperature Setpoint (C)").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Entry(self.main_frame, textvariable=self.Tset, width=5)
        w.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self.CCD, "initialized", True)]
        ttk.Label(self.main_frame, text="Current CCD Temperature (K)").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(self.main_frame, textvariable=self.Tdet, width=5).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        ttk.Label(self.main_frame, text="Current CCD Temperature (C)").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(self.main_frame, textvariable=self.Tdet_c, width=5).grid(row=5, column=1, sticky=TK_STICKY_ALL)
        self.set_enabled()


    @check_enabled
    def initialize_ccd(self):
        # Currently we just set values. If there's a way to query the CCD, we will do that
        # later.
        self.CCD.initialized = True
        self.CCD.ccd_on = False
        self.CCD.cooler_on = False


    @check_enabled
    def toggle_camera(self):
        if self.CCD.ccd_on:
            self.CCD.ccd_on = False
        else:
            self.CCD.ccd_on = True


    @check_enabled
    def toggle_cooler(self):
        if self.CCD.cooler_on:
            self.CCD.cooler_on = False
        else:
            self.CCD.cooler_on = True
    
    
    @property
    def cam_img(self):
        """
        This property points to the appropriate image for the camera button given the 
        camera state
        """
        if self.CCD.ccd_on:
            return self.on_big
        return self.off_big
    
    
    @property
    def cool_img(self):
        """
        This property points to the appropriate image for the cooler button given the 
        cooler state
        """
        if self.CCD.cooler_on:
            return self.on_big
        return self.off_big


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        self.button_camera.config(image=self.cam_img)
        self.button_cooler.config(image=self.cool_img)
        self.Tdet_c.set(self.Tdet.get() - 273.15)
