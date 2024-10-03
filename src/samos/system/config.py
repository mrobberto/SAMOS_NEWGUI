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

from samos.utilities import get_data_file, get_fits_dir

class SAMOSConfig():
    """ Collection of parameters to be shared by the classes """

    def __init__(self):
        self.today = datetime.now()
        self.update_locations()
        
        """ Default IP address imported for all forms"""
        with open(get_data_file("system", "IP_addresses_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            self.IP_dict = {rows[0]: rows[1] for rows in reader}
            self.IP_status_dict = {rows[0]: False for rows in reader}
        # Is SAMOS running in simulated mode?
        self.simulated = False

        # Has the connection to the various components been initialized/tested?
        self.connections_initialized = False

        # Should FITS files be flipped in X on open
        self.flip_x_on_open = False
        
        # A lot of places use the SAMOS WCS, so it's now here
        self.wcs = None
        self.valid_wcs = False
        self.dmd_map_filename = None

        with open(self.potn_path) as f:
            self.PotN = yaml.safe_load(f)
        self.Observer = self.PotN['Observer']
        self.Telescope = self.PotN['Telescope']
        self.Program_ID = self.PotN['Program ID']
        self.Telescope_Operator = self.PotN['Telescope Operator']

        self.Ginga_PA = False
        
        self.status_indicators = []


    def update_locations(self):
        self.logfile_name = get_fits_dir() / f"SAMOS_LOGFILE_{self.today.strftime('%Y%m%d')}.csv"
        self.QL_images = get_fits_dir() / "ql"
        self.QL_images.mkdir(parents=True, exist_ok=True)
        self.potn_path = get_fits_dir() / "parameters_of_the_night.yaml"
        if not self.potn_path.is_file():
            default_potn = get_data_file("system", "default_parameters_of_the_night.yaml")
            self.potn_path.write_text(default_potn.read_text())


    def update_PotN(self):
        """
        Updates the parameters of the night variables and files for logging the observations
        """
        with open(self.potn_path, "w") as f:
            yaml.dump(self.PotN, f, default_flow_style=False)


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
    def logbook_exists(self):
        if self.logfile_name.is_file():
            return True
        return False


    @property
    def dmd_wcs(self):
        dmd_wcs_file = get_data_file("dmd.convert", "DMD_Mapping_WCS.fits")
        with fits.open(dmd_wcs_file) as hdul:
            dmd_wcs = wcs.WCS(hdul[0].header, relax=True)
        return dmd_wcs
