"""
This module defines the common functionality of SAMOS main window frames.

Authors
-------

    - Brian York (york@stsci.edu)

Use
---

    This module is intended to be imported as the base class of SAMOS main window frames.

Dependencies
------------
    
    None.
"""
import logging
import os
from pathlib import Path
import shutil

import tkinter as tk
from tkinter import ttk

from samos.system.SAMOS_Functions import Class_SAMOS_Functions as SF
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *


class SAMOSFrame(ttk.Frame):

    def __init__(self, parent, container, name, **kwargs):
        super().__init__(container)
        self.logger = logging.getLogger("samos")
        self.parent = parent
        self.CCD = kwargs["CCD"]
        self.DMD = kwargs['DMD']
        self.img = kwargs["img"]
        self.iq = kwargs["iq"]
        self.Motors = kwargs["Motors"]
        self.SOAR = kwargs["SOAR"]
        self.convert = kwargs["convert"]
        self.main_fits_header = kwargs["main_fits_header"]
        self.PAR = kwargs["PAR"]
        self.fits_dir = get_fits_dir()

        self.main_frame = tk.LabelFrame(self, text=name, font=BIGFONT, borderwidth=5)
        self.main_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Define Our Images
        self.on_big = tk.PhotoImage(file=get_data_file("tk.icons", "on_big.png"))
        self.off_big = tk.PhotoImage(file=get_data_file("tk.icons", "off_big.png"))
        self.on_sm = tk.PhotoImage(file=get_data_file("tk.icons", "on_small.png"))
        self.off_sm = tk.PhotoImage(file=get_data_file("tk.icons", "off_small.png"))
    
    
    def create_custom_menus(self, parent, menubar):
        pass
        

    def create_menubar(self, parent):
        parent.title("SAMOS Configuration")

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")
        
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame("DMDPage"))
        filemenu.add_command(label="Recalibrate CCD2DMD", command=lambda: parent.show_frame("CCD2DMDPage"))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame("MotorsPage"))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame("CCDPage"))
        filemenu.add_command(label="SOAR TCS", command=lambda: parent.show_frame("SOARPage"))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame("MainPage"))
        filemenu.add_separator()
        filemenu.add_command(label="ETC", command=lambda: parent.show_frame("ETCPage"))
        filemenu.add_command(label="Exit", command=parent.quit)
        
        self.create_custom_menus(parent, menubar)

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame("GSPage"))        

        return menubar
