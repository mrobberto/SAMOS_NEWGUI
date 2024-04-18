"""
This module defines various tkinter utility functions, to abstract them out of UI widgets.

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
from datetime import datetime
import os
from pathlib import Path
import sys

import tkinter as tk
import ttkbootstrap as ttk

def about_box():
    """
    Display a dialog with application info
    """
    ttk.messagebox.showinfo('About SAMOS', "This is the control software for the SAMOS instrument.")


def check_widgets(widgets):
    """
    widgets is a dictionary, with each key being a tk widget, and each widget having a 
    list of conditions.
    
    Each condition is a tuple, one of:
    - ("valid_wcs", PAR): Check if the PAR object has valid_wcs == True
    - ("valid_file", VAR): Check if the pathlib.Path object VAR has is_file() == True
    - ("tkvar", widget, value): widget.get() == value
    - ("tknot", widget, value): widget.get() != value
    - ("is_something, VAR"): Check if VAR is None
    - ("condition", object, attribute, value): getattr(object, attribute) == value
    
    Conditions are combined with implicit AND
    """
    for widget in widgets:
#         sys.stdout.write("Widget {}: ".format(widget))
        for condition in widgets[widget]:
#             sys.stdout.write("Condition {}: ".format(condition))
            if condition[0] == "valid_wcs":
                if not condition[1].valid_wcs:
                    widget["state"] = "disabled"
                    widget.configure(state="disabled")
#                     sys.stdout.write("DISABLING\n")
                    break
            elif condition[0] == "valid_file":
                if (condition[1] is not None) and (not condition[1].is_file()):
                    widget["state"] = "disabled"
                    widget.configure(state="disabled")
#                     sys.stdout.write("DISABLING\n")
                    break
            elif condition[0] == "tkvar":
                if condition[1].get() != condition[2]:
                    widget["state"] = "disabled"
                    widget.configure(state="disabled")
#                     sys.stdout.write("DISABLING\n")
                    break
            elif condition[0] == "tknot":
                if condition[1].get() == condition[2]:
                    widget["state"] = "disabled"
                    widget.configure(state="disabled")
#                     sys.stdout.write("DISABLING\n")
                    break
            elif condition[0] == "is_something":
                # check for non-None
                if condition[1] is None:
                    widget["state"] = "disabled"
                    widget.configure(state="disabled")
#                     sys.stdout.write("DISABLING\n")
                    break
            else:  # implicit condition[0] == "condition"
                if (hasattr(condition[1], condition[2])) and (getattr(condition[1], condition[2]) != condition[3]):
                    widget["state"] = "disabled"
                    widget.configure(state="disabled")
#                     sys.stdout.write("DISABLING\n")
                    break
            widget["state"] = "normal"
            widget.configure(state="normal")
#             sys.stdout.write("ENABLING\n")
#     sys.stdout.flush()
