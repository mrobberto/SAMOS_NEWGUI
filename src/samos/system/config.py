#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 17:52:35 2023

@author: samos_dev
"""
from astropy.io import fits
from astropy import wcs
from datetime import datetime
import tkinter as tk
import os
from pathlib import Path
import sys
import csv
import yaml

from samos.utilities import get_data_file, get_temporary_dir

class SAMOSConfig():
    """ Collection of parameters to be shared by the classes """

    def __init__(self, db, logger):
        self.today = datetime.now()
        self.db = db
        self.logger = logger
        
        # Has the connection to the various components been initialized/tested?
        self.connections_initialized = False

        # A lot of places use the SAMOS WCS, so it's now here
        self.wcs = None
        self.valid_wcs = False
        self.dmd_map_filename = None

        self.Ginga_PA = False
        
        self.status_indicators = []


    def create_log_file(self):       
        """ Invoked to create log file"""
        today = datetime.now()
        pn = self.PotN
        if not self.logbook_exists:
            with open(self.logfile_name, 'w+') as logfile:
                logfile.write(f"SAMOS LOGBOOK for {today.strftime('%Y%m%d')}\n")
                logfile.write(f"Telescope,{pn['Telescope']}\n")
                logfile.write(f"Program ID,{pn['Program ID']},Proposal Title,{pn['Proposal Title']},PI,")
                logfile.write(f"{pn['Principal Investigator']}\n")
                logfile.write(f"Observer,{pn['Observer']},Telescope Operator,{pn['Telescope Operator']}\n")
                logfile.write("Date,Local Time,Target,Filter,Repeats,Exposure Time,Filename,Mask Name,")
                logfile.write("Grating,Sp. Exp.T,Sp. Filename,Comment\n")
        return self.logfile_name


    def add_status_indicator(self, widget, callback):
        indicator = {"widget": widget, "callback": callback}
        if indicator not in self.status_indicators:
            self.status_indicators.append(indicator)


    def update_status_indicators(self):
        for indicator in self.status_indicators:
            indicator["callback"]()


    @property
    def output_dir(self):
        """Currently set output directory"""
        storage_location = self.db.get_value(
            "config_files_storage_location", default="module"
        )
        if storage_location == "module":
            return get_temporary_dir()
        elif storage_location == "home":
            return Path.home()
        elif storage_location == "cwd":
            return Path.cwd()
        elif storage_location == "custom":
            return Path(self.db.get_value("config_custom_files_location"))
        raise ValueError(f"{storage_location} is not a valid storage location!")


    @property
    def fits_dir(self):
        """Return the current night's file location"""
        base_dir = self.output_dir
        return base_dir / "SISI_Images" / f"SAMOS_{self.today_str}"

    @property
    def QL_images(self):
        """Quicklook Image directory"""
        return self.fits_dir / "ql"


    @property
    def logbook_exists(self):
        if self.logfile_name.is_file():
            return True
        return False


    @property
    def today_str(self):
        """Return the saved date as a formatted date string"""
        return self.today.strftime("%Y-%m-%d")


    @property
    def is_connected(self):
        """Is SAMOS operating in connected-to-hardware mode?"""
        connection_status = self.db.get_value("config_ip_status", default="disconnected")
        return connection_status == "connected"


    @property
    def dmd_wcs(self):
        dmd_wcs_file = get_data_file("dmd.convert", "DMD_Mapping_WCS.fits")
        with fits.open(dmd_wcs_file) as hdul:
            dmd_wcs = wcs.WCS(hdul[0].header, relax=True)
        return dmd_wcs
