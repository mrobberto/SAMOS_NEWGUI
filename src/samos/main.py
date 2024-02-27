#!/usr/bin/env python
"""
Main entrypoint to SAMOS GUI
"""
import logging

from ginga.util import iqcalc
from ginga.AstroImage import AstroImage

import tkinter as tk
from tkinter import ttk

from samos.ccd.Class_CCD_dev import Class_Camera
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.Class_DMD_dev import DigitalMicroMirrorDevice
from samos.motors.Class_PCM import Class_PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.astrometry.panstarrs.image import PanStarrsImage as PS_image
from samos.astrometry.panstarrs.catalog import PanStarrsCatalog as PS_table
from samos.ui import ConfigPage, DMDPage, CCD2DMDPage, MotorsPage, CCDPage, SOARPage, MainPage, ETCPage, GSPage
from samos.utilities.constants import *


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('samos')
        self.logger.debug("Initializing App")
        
        # Instantiate the classes that represent the SAMOS hardware
        self.samos_classes = {
            "CCD": Class_Camera(dict_params=self.CCD_PARAMS),
            "DMD": DigitalMicroMirrorDevice(),
            "PSima": PS_image(),
            "PStab": PS_table(),
            "img": AstroImage(),
            "iq": iqcalc.IQCalc(),
            "Motors": Class_PCM(),
            "SOAR": Class_SOAR(),
            "convert": CONVERT(),
            "main_fits_header": WFH.FITSHead()
        }
        
        # Setting up Initial Things
        self.title("SAMOS Control System")
        self.geometry("1100x500")
        self.resizable(True, True)

        # Creating a container
        container = tk.Frame(self, bg="#8AA7A9", width=1100)
        container.pack(side="top", fill="both", expand=True).grid_rowconfigure(0, weight=1).grid_columnconfigure(0, weight=1)
        
        # Initialize Frames
        self.frames = {}
        for frame_class in self.FRAME_CLASSES:
            frame = frame_class(self, container, **self.samos_classes)
            self.frames[frame_class.__name__] = frame
            frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.show_frame(ConfigPage)


    def show_frame(self, cont):
        self.logger.debug("Selecting frame {}".format(cont.__name__))
        frame = self.frames[cont.__name__]
        menubar = frame.create_menubar(self)
        self.configure(menu=menubar)
        frame.tkraise()
    
    
    FRAME_CLASSES = [
        ConfigPage, 
        DMDPage, 
        CCD2DMDPage, 
        MotorsPage, 
        CCDPage, 
        SOARPage, 
        MainPage, 
        ETCPage, 
        GSPage
    ]

    # Trigger Mode = 4: light
    # Trigger Mode = 5: dark
    CCD_PARAMS = {'Exposure Time': 0, 'CCD Temperature': 2300, 'Trigger Mode': 4, 'NofFrames': 1}


def run_samos():
    app = App()
    combostyle = ttk.Style()
    combostyle.configure("TCombobox", fieldbackground="dark gray", foreground="black", background="white")
    app.mainloop()


if __name__ == "__main__":
    run_samos()
