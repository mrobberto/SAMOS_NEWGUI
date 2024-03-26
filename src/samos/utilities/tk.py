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
from tkinter import ttk


def all_children(widget):
    """
    Return (recursively) all widgets that are contained within the given widget.
    """
    return [widget] + [subchild for child in widget.winfo_children() for subchild in all_children(child)]


def select_widgets(widget_list, key, valid_value_or_values):
    """
    From the provided list of widgets, look for all widgets that have a given key set
    to a given value (or values)
    """
    if isinstance(valid_value_or_values, list):
        valid_values = valid_value_or_values
    else:
        valid_values = [valid_value_or_values]
    matches = []
    for widget in widgets:
        if key in widget.keys():
            if widget[key] in valid_values:
                matches.append(widget)
    return matches


def set_widgets(widgets, condition_or_conditions):
    """
    For each widget in the list:
    
    - if `condition` evaluates to True, configure the widget to be enabled
    - else configure the widget to be disabled
    - combines multiple conditions with implicit "and"
    """
    if isinstance(condition_or_conditions, list):
        conditions = condition_or_conditions
    else:
        conditions = [condition_or_conditions]
    for widget in widgets:
        for condition in conditions:
            if not condition:
                widget.configure(state="disabled")
                break
        widget.configure(state="normal")


def check_widgets(widgets):
    """
    widgets is a dictionary, with each key being a tk widget, and each widget having a 
    list of conditions.
    
    Each condition is a tuple, one of:
    - ("valid_wcs", PAR): Check if the PAR object has valid_wcs == True
    - ("valid_file", VAR): Check if the pathlib.Path object VAR has is_file() == True
    - ("tkvar", widget, value): widget.get() == value
    - ("is_something, VAR"): Check if VAR is None
    - ("condition", object, attribute, value): getattr(object, attribute) == value
    
    Conditions are combined with implicit AND
    """
    for widget in widgets:
        for condition in widgets[widget]:
            print(condition)
            if condition[0] == "valid_wcs":
                if not condition[1].valid_wcs:
                    widget.configure(state="disabled")
                    break
            elif condition[0] == "valid_file":
                if (condition[1] is not None) and (not condition[1].is_file()):
                    widget.configure(state="disabled")
                    break
            elif condition[0] == "tkvar":
                if condition[1].get() != condition[2]:
                    widget.configure(state="disabled")
                    break
            elif condition[0] == "is_something":
                # check for non-None
                if condition[1] is None:
                    widget.configure(state="disabled")
                    break
            else:  # implicit condition[0] == "condition"
                if (hasattr(condition[1], condition[2])) and (getattr(condition[1], condition[2]) != condition[3]):
                    widget.configure(state="disabled")
                    break
        widget.configure(state="normal")
