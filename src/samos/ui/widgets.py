"""
Custom widgets

Author:
    - Brian York
"""
from astropy.io import fits
import numpy as np
import time

import tkinter as tk
import ttkbootstrap as ttk


class VariableRegistry:
    """
    Registers a list of objects that share a name entry in a database, and makes sure that
    they all stay updated with the appropriate value.
    """
    def __init__(self, db, root, logger):
        self.logger = logger
        self.root = root
        self.db = db
        self.store = {}

    def register(self, db_name, var_object, callback=None):
        self.logger.debug(f"Registering {var_object} to {db_name}")
        if db_name not in self.store:
            self.store[db_name] = []
        self.store[db_name].append((var_object, callback))
        self.logger.debug(f"{len(self.store[db_name])} items registered to {db_name}")

    def check_name(self, db_name):
        if db_name in self.store:
            return len(self.store[db_name])
        return 0

    def update(self, db_name, var_object, *args):
        try:
            value = var_object.get()
        except tk.TclError as e:
            self.logger.warning(f"Got exception {e}")
            if isinstance(var_object, tk.IntVar):
                value = 0
            elif isinstance(var_object, tk.DoubleVar):
                value = 0.
            else:
                raise e
        self.logger.info(f"Registry: Updating {db_name} to {value} (from {var_object})")
        if self.db.update_value(db_name, value):
            self.logger.info(f"\tDatabase updated. Checking stored variables")
            for (var, callback) in self.store[db_name]:
                self.logger.info(f"\t\tChecking {var}")
                if var != var_object:
                    self.logger.info(f"\t\t\tUpdating {var} with new value {value}")
                    var.set(value)
                if callback is not None:
                    self.logger.info(f"\t\t\tActivating callback function {callback}")
                    callback()
            self.logger.info("Registry: finished update")
        else:
            self.logger.info("Registry: redundant update")
