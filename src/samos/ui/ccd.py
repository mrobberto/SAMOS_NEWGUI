"""
SAMOS CCD tk Frame Class
"""
import logging

import tkinter as tk
from tkinter import ttk

from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame


class CCDPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, **kwargs)
        self.logger.debug('Initializing CCD control frame')

        # CCD Setup Panel
        self.main_frame.config(background="cyan")

        # CAMERA ON/OFF SWITCH
        self.camera_is_on = False
        self.label_camera = tk.Label(self.main_frame, text=self.cam, fg="grey", font=BIGFONT)
        self.label_camera.grid(row=0, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.button_camera = tk.Button(self.main_frame, image=self.cam_img, bd=0, command=self.toggle_camera)
        self.button_camera.grid(row=0, column=2, sticky=TK_STICKY_ALL, padx=3, pady=3)

        # COOLER ON/OFF SWITCH
        self.cooler_is_on = False
        self.label_cooler = tk.Label(self.main_frame, text=self.cool, fg="grey", font=BIGFONT)
        self.label_cooler.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.button_cooler = tk.Button(self.main_frame, image=self.cool_img, bd=0, command=self.toggle_cooler)
        self.button_cooler.grid(row=1, column=2, sticky=TK_STICKY_ALL, padx=3, pady=3)

        # COOLER TEMPERATURE SETUP AND VALUE
        l = tk.Label(self.main_frame, text="CCD Temperature Sepoint (C)")
        l.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.Tset = tk.StringVar()
        self.Tset.set("-90")
        entry_Tset = tk.Entry(self.main_frame, textvariable=self.Tset, width=5, bd=3)
        entry_Tset.grid(row=2, column=2, sticky=TK_STICKY_ALL, padx=3, pady=3)
        l = tk.Label(self.main_frame, text="Current CCD Temperature (K)")
        l.grid(row=3, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.Tdet = tk.IntVar()
        tk.Label(self.main_frame, textvariable=self.Tdet, font=('Arial', 16), borderwidth=3, relief="sunken", 
                 bg="green", fg="white", text=str(273)).grid(row=3, column=2, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.Tdet.set(273)


    def toggle_camera(self):
        if self.camera_is_on:
            self.camera_is_on = False
        else:
            self.camera_is_on = True
        self.button_camera.config(image=self.cam_img)
        self.label_camera.config(text=self.cam, fg="grey")


    def toggle_cooler(self):
        if self.cooler_is_on:
            self.cooler_is_on = False
        else:
            self.cooler_is_on = True
        self.button_cooler.config(image=self.cool_img)
        self.label_cooler.config(text=self.cool, fg="green")
    
    
    @property
    def cam(self):
        """
        This property holds valid text for the camera button based on its current state.
        """
        if self.camera_is_on:
            return "Camera is ON"
        return "Camera is OFF"
    
    
    @property
    def cam_img(self):
        """
        This property points to the appropriate image for the camera button given the 
        camera state
        """
        if self.camera_is_on:
            return self.on_big
        return self.off_big


    @property
    def cool(self):
        """
        This property holds valid text for the cooler button based on its current state.
        """
        if self.cooler_is_on:
            return "Cooler is ON"
        return "Cooler is OFF"
    
    
    @property
    def cool_img(self):
        """
        This property points to the appropriate image for the cooler button given the 
        cooler state
        """
        if self.cooler_is_on:
            return self.on_big
        return self.off_big
