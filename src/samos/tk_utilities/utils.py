"""
This module defines various utility functions for use with the tk gui.

Authors
-------

    - Brian York (york@stsci.edu)

Use
---

    This module is intended to be imported and its individual functions used on their own.

Dependencies
------------
    
    None.
"""
import tkinter as tk
from ginga.tkw.ImageViewTk import CanvasView
from ginga.AstroImage import AstroImage
from ginga.util import io_fits
from ginga.util.loader import load_data
from ginga.misc import log

def about_box():
    """
    Display a dialog with application info
    """
    ttk.messagebox.showinfo('About SAMOS', "This is the control software for the SAMOS instrument.")
