#!/usr/bin/env python
"""
Main entrypoint to SAMOS GUI
"""
import logging

from ginga.util import iqcalc
from ginga.AstroImage import AstroImage

import tkinter as tk
from tkinter import ttk

from samos.astrometry.panstarrs.image import PanStarrsImage as PS_image
from samos.astrometry.panstarrs.catalog import PanStarrsCatalog as PS_table
from samos.ccd.Class_CCD_dev import Class_Camera
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.Class_DMD_dev import DigitalMicroMirrorDevice
from samos.motors.Class_PCM import Class_PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.system import WriteFITSHead as WFH
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
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
            "main_fits_header": WFH.FITSHead(),
            "PAR": SAMOS_Parameters()
        }
        
        # Setting up Initial Things
        self.title("SAMOS Control System")
        self.resizable(False, False)

        # Creating a container
        container = tk.Frame(self, bg="#8AA7A9")#, width=1100)
        # We want to use grid rather than pack, but that means we have to adjust other
        # classes first
        container.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Initialize Frames
        self.frames = {}
        for frame_class in self.FRAME_CLASSES:
            frame = frame_class(self, container, **self.samos_classes)
            self.frames[frame_class.__name__] = frame
            frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.show_frame("ConfigPage")


    def show_frame(self, frame):
        self.logger.debug("Selecting frame {}".format(frame))
        new_frame = self.frames[frame]
        menubar = new_frame.create_menubar(self)
        self.configure(menu=menubar)
        if hasattr(new_frame, "main_frame"):
            self.geometry("{}x{}".format(new_frame.main_frame.winfo_width(), new_frame.main_frame.winfo_height()))
            print("New geometry {}x{}".format(new_frame.main_frame.winfo_width(), new_frame.main_frame.winfo_height()))
        else:
            self.geometry("{}x{}".format(new_frame.winfo_width(), new_framewinfo_height()))
            print("New geometry {}x{}".format(new_frame.winfo_width(), new_frame.winfo_height()))
        new_frame.tkraise()
    
    
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
