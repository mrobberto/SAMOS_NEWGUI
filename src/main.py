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
import ttkbootstrap as ttk

from samos.ccd import CCD
from samos.dmd import DigitalMicroMirrorDevice
from samos.motors import PCM
from samos.sami import SAMI
from samos.soar import SOAR
from samos.system.fits_header import FITSHead
from samos.system.config import SAMOSConfig
from samos.ui import ConfigPage, DMDPage, CCD2DMDPage, MotorsPage, CCDPage, SOARPage, MainPage, ETCPage, GSPage, SAMIPage
from samos.ui.logging_window import LoggingWindow
from samos.utilities.constants import *
from samos.utilities.simulator import start_simulator
from samos.utilities.tk import about_box


class App(ttk.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('samos')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.log_window = LoggingWindow(self)
        self.log_window.text_handler.setLevel(logging.INFO)
        self.log_window.text_handler.setFormatter(formatter)
        self.logger.addHandler(self.log_window.text_handler)
        self.logger.info("Initializing App")
        self.PAR = SAMOSConfig()
        self.main_fits_header = FITSHead(self.PAR, self.logger)
        self.simulator = None
        self.protocol("WM_DELETE_WINDOW", self.destroy_all)
        
        DMD = DigitalMicroMirrorDevice(self.logger, self.PAR)
        # Instantiate the classes that represent the SAMOS hardware
        self.samos_classes = {
            "CCD": CCD(self.PAR, DMD, self.logger),
            "DMD": DMD,
            "PCM": PCM(self.PAR, self.logger, self.main_fits_header),
            "SOAR": SOAR(self.PAR),
            "SAMI": SAMI(self.PAR, self.logger),
            "main_fits_header": self.main_fits_header,
            "PAR": self.PAR
        }
        
        # Setting up Initial Things
        self.title("SAMOS Control System")
        self.resizable(True, True)

        # Create a container Notebook
        self.container = ttk.Notebook(self)
        self.container.enable_traversal()
        self.container.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # Create menus
        self.configure(menu=self.create_menubar())

        # Initialize Frames
        self.frames = {}
        self.frame_indices = {}
        current_index = 0
        for frame_class in self.FRAME_CLASSES:
            self.logger.info(f"Creating Frame {frame_class.__name__}")
            frame = frame_class(self, self.container, **self.samos_classes)
            self.frames[frame_class.__name__] = frame
            self.frame_indices[frame_class.__name__] = current_index
            frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.container.add(frame, text=frame_class.__name__)
            current_index += 1
            self.logger.info(f"Finished creating frame {frame_class.__name__}")
        self.frames["ConfigPage"].load_IP_default()
        self.show_frame("ConfigPage")
        self.lift()
        self.log_window.withdraw()


    def show_frame(self, frame):
        self.logger.debug("Selecting frame {}".format(frame))
        new_frame = self.frames[frame]
        new_frame.set_enabled()
        new_frame.update()
        self.container.select(self.frame_indices[frame])


    def do_updates(self):
        for key in self.frames:
            self.frames[key].set_enabled(run_from_main=True)
            self.frames[key].update()
        self.update()
    
    
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


    def destroy_all(self):
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
        

    def show_logging_window(self):
        self.log_window.deiconify()


    def create_menubar(self):
        menubar = tk.Menu(self, bd=3, relief=tk.RAISED, activebackground="#80B9DC")
        
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: self.show_frame("ConfigPage"))
        filemenu.add_command(label="DMD", command=lambda: self.show_frame("DMDPage"))
        filemenu.add_command(label="Recalibrate CCD2DMD", command=lambda: self.show_frame("CCD2DMDPage"))
        filemenu.add_command(label="Motors", command=lambda: self.show_frame("MotorsPage"))
        filemenu.add_command(label="CCD", command=lambda: self.show_frame("CCDPage"))
        filemenu.add_command(label="SOAR TCS", command=lambda: self.show_frame("SOARPage"))
        filemenu.add_command(label="MainPage", command=lambda: self.show_frame("MainPage"))
        filemenu.add_command(label="ETC", command=lambda: self.show_frame("ETCPage"))
        filemenu.add_separator()
        filemenu.add_command(label="Logging", command=self.show_logging_window)
        filemenu.add_command(label="Exit", command=self.destroy)  #quit)

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: self.show_frame("GSPage"))        

        return menubar


    FRAME_CLASSES = [
        ConfigPage, 
        DMDPage, 
        CCD2DMDPage, 
        MotorsPage, 
        CCDPage, 
        SOARPage, 
        SAMIPage,
        MainPage, 
        ETCPage, 
        GSPage
    ]


def run_samos():
    app = App(themename="cosmo")
#     combostyle = ttk.Style()
#     combostyle.configure("TCombobox", fieldbackground="dark gray", foreground="black", background="white")
    app.mainloop()
    
if __name__ == "__main__":
    run_samos()
