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

    def register(self, db_name, var_object):
        self.logger.debug(f"Registering {var_object} to {db_name}")
        if db_name not in self.store:
            self.store[db_name] = []
        self.store[db_name].append(var_object)
        self.logger.debug(f"{len(self.store[db_name])} items registered to {db_name}")

    def check_name(self, db_name):
        if db_name in self.store:
            return len(self.store[db_name])
        return 0

    def update(self, db_name, var_object, *args):
        value = var_object.get()
        self.logger.debug(f"Updating database {db_name} to {value} (from {var_object})")
        self.db.update_value(db_name, value)
        self.logger.debug(f"Database updated. Checking stored variables")
        for var in self.store[db_name]:
            self.logger.debug(f"Checking {var}")
            if var != var_object:
                self.logger.debug(f"Updating {var} with new value {value} ({type(value)})")
                var.set(value)
        self.logger.debug("Finished update")
