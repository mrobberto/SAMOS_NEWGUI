#!/usr/bin/env python
"""
Main entrypoint to SAMOS GUI
"""
import logging
import multiprocessing as mp
import socket
import sys

from ginga.util import iqcalc
from ginga.AstroImage import AstroImage

import tkinter as tk
from tkinter import ttk

from samos.astrometry.panstarrs.image import PanStarrsImage as PS_image
from samos.astrometry.panstarrs.catalog import PanStarrsCatalog as PS_table
from samos.ccd.Class_CCD_dev import Class_Camera
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd import DigitalMicroMirrorDevice
from samos.motors.Class_PCM import Class_PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.system import WriteFITSHead as WFH
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.ui import ConfigPage, DMDPage, CCD2DMDPage, MotorsPage, CCDPage, SOARPage, MainPage, ETCPage, GSPage
from samos.utilities.constants import *
from samos.utilities.simulator import start_simulator


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger('samos')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.info("Initializing App")
        self.PAR = SAMOS_Parameters()
        self.simulator = None
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # Instantiate the classes that represent the SAMOS hardware
        self.samos_classes = {
            "CCD": Class_Camera(dict_params=CCD_PARAMS, par=self.PAR),
            "DMD": DigitalMicroMirrorDevice(par=self.PAR),
            "PSima": PS_image(),
            "PStab": PS_table(),
            "img": AstroImage(),
            "iq": iqcalc.IQCalc(),
            "Motors": Class_PCM(),
            "SOAR": Class_SOAR(),
            "convert": CONVERT(),
            "main_fits_header": WFH.FITSHead(),
            "PAR": self.PAR
        }
        
        # Setting up Initial Things
        self.title("SAMOS Control System")
        self.resizable(False, False)

        # Create a container Notebook
        self.container = ttk.Notebook(self)
        self.container.enable_traversal()
        self.container.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Initialize Frames
        self.frames = {}
        self.frame_indices = {}
        current_index = 0
        for frame_class in self.FRAME_CLASSES:
            frame = frame_class(self, self.container, **self.samos_classes)
            self.frames[frame_class.__name__] = frame
            self.frame_indices[frame_class.__name__] = current_index
            frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.container.add(frame, text=frame_class.__name__)
            current_index += 1
        self.frames["ConfigPage"].load_IP_default()
        self.show_frame("ConfigPage")


    def show_frame(self, frame):
        self.logger.debug("Selecting frame {}".format(frame))
#         new_frame = self.frames[frame]
#         menubar = new_frame.create_menubar(self)
#         self.configure(menu=menubar)
#         if hasattr(new_frame, "main_frame"):
#             self.geometry("{}x{}".format(new_frame.main_frame.winfo_width(), new_frame.main_frame.winfo_height()))
#             print("New geometry {}x{}".format(new_frame.main_frame.winfo_width(), new_frame.main_frame.winfo_height()))
#         else:
#             self.geometry("{}x{}".format(new_frame.winfo_width(), new_framewinfo_height()))
#             print("New geometry {}x{}".format(new_frame.winfo_width(), new_frame.winfo_height()))
#         new_frame.tkraise()

        new_frame = self.frames[frame]
        menubar = new_frame.create_menubar(self)
        self.configure(menu=menubar)
        self.container.select(self.frame_indices[frame])
    
    
    def initialize_simulator(self):
        """
        Starts the simulated SAMOS telescope if it isn't already.
        """
        if self.PAR.simulated:
            self.logger.warning("Attempted to start simulator when already simulated.")
        self.logger.info("Starting Simulator")
        for key in self.PAR.IP_dict:
            host, port = self.PAR.IP_dict[key].split(":")
            if host != "127.0.0.1":
                self.logger.error("SAMOS simulator can only run on localhost!")
        self.app_pipe, sim_pipe = mp.Pipe()
        self.simulator = mp.Process(target=start_simulator, args=(self.PAR.IP_dict, sim_pipe))
        self.PAR.simulated = True
        self.simulator.daemon = True
        self.simulator.start()
        self.logger.info("Simulator Running")
    
    
    def destroy_simulator(self):
        """
        If the simulated SAMOS telescope is running, send it a shutdown message
        """
        if not self.PAR.simulated:
            self.logger.warning("Attempted to shut down already inactive simulator")
        self.logger.info("Shutting Down Simulator")
        if self.simulator is not None:
            self.simulator.terminate()
            self.app_pipe.send("SHUTDOWN!")
            self.simulator.join()
            self.simulator.close()
            self.logger.info("Simulator has shut down.")
        self.PAR.simulated = False
        self.simulator = None


    def destroy(self):
        """
        While closing, if running the simulator, close it.
        """
        self.logger.warning("Shutting down SAMOS")
        if self.simulator is not None:
            self.simulator.terminate()
            self.simulator.join()
            self.simulator.close()
            self.logger.info("Simulator has exited")
        self.logger.warning("Finished shutdown functions")
        super().destroy()

    
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


def run_samos():
    app = App()
    combostyle = ttk.Style()
    combostyle.configure("TCombobox", fieldbackground="dark gray", foreground="black", background="white")
    app.mainloop()


if __name__ == "__main__":
    run_samos()
