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
import functools
import logging
import os
from pathlib import Path
import shutil

import tkinter as tk
from tkinter import ttk

from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *
from samos.utilities.tk import check_widgets


def check_enabled(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        result = func(self, *args, **kwargs)
        self.set_enabled()
        return result
    return wrapper


class SAMOSFrame(ttk.Frame):

    def __init__(self, parent, container, name, **kwargs):
        super().__init__(container)
        self.logger = logging.getLogger("samos")
        self.parent = parent
        self.CCD = kwargs["CCD"]
        self.DMD = kwargs['DMD']
        self.PCM = kwargs["PCM"]
        self.SOAR = kwargs["SOAR"]
        self.main_fits_header = kwargs["main_fits_header"]
        self.PAR = kwargs["PAR"]
        self.fits_dir = get_fits_dir()
        self.check_widgets = {}

        self.main_frame = ttk.LabelFrame(self, text=name, borderwidth=5)
        self.main_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Define Our Images
        self.on_big = tk.PhotoImage(file=get_data_file("tk.icons", "on_big.png"))
        self.off_big = tk.PhotoImage(file=get_data_file("tk.icons", "off_big.png"))
        self.on_sm = tk.PhotoImage(file=get_data_file("tk.icons", "on_small.png"))
        self.off_sm = tk.PhotoImage(file=get_data_file("tk.icons", "off_small.png"))


    def create_custom_menus(self, parent, menubar):
        pass
        

    def set_enabled(self, run_from_main=False):
        """
        Apply the check_widgets function to everything in the check_widgets dictionary
        """
        check_widgets(self.check_widgets)
        self.PAR.update_status_indicators()
        self.update()
        if not run_from_main:
            self.parent.do_updates()
