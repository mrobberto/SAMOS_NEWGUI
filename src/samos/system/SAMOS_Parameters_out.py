#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 17:52:35 2023

@author: samos_dev
"""
from datetime import datetime
import tkinter as tk
import os
from pathlib import Path
import sys
import csv
import json #added to handle the Parameters.txt file

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)

from samos.utilities import get_data_file, get_fits_dir

class SAMOS_Parameters():
    """ Collection of parameters to be shared by the classes """

    def __init__(self):
        today = datetime.now()
        #add the directory of the QL images
        self.QL_images = get_data_file("ql")
        
        """ Default IP address imported for all forms"""
        with open(get_data_file("system", "IP_addresses_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            self.IP_dict = {rows[0]: rows[1] for rows in reader}
            self.IP_status_dict = {rows[0]: False for rows in reader}
        # Is SAMOS running in simulated mode?
        self.simulated = False
        
        # A lot of places use the SAMOS WCS, so it's now here
        self.wcs = None
        self.valid_wcs = False
        self.dmd_map_filename = None

        # I am adding here the parameters that may change every night, saved in the 
        # Parameters.txt file as a dictionary that has to be handled as a json file. 
        # See Prameters_README.py for further info on how to handle it
        with open(get_data_file("system", "Parameters_of_the_night.txt")) as f:
            data= f.read()
        self.PotN = json.loads(data)    
        self.Observer = self.PotN['Observer']
        self.Telescope = self.PotN['Telescope']
        self.Program_ID = self.PotN['Program ID']
        self.Telescope_Operator = self.PotN['Telescope Operator']

        SISI_images_dir = get_fits_dir()
        self.logfile_name = SISI_images_dir / f"SAMOS_LOGFILE_{today.strftime('%Y%m%d')}.csv"

        self.Ginga_PA = False


    def update_PotN(self):
        """
        Updates the parameters of the night variables and files for logging the observations
        """
        with open(get_data_file("system", "Parameters_of_the_night.txt"), "w") as jsonFile:
            json.dump(self.PotN, jsonFile)


    def create_log_file():       
        """ Invoked to create log file"""
        today = datetime.now()
        pn = self.PotN
        if not self.logbook_exists:
            with open(self.logfile_name, 'w+') as logfile:
                logfile.write(f"SAMOS LOGBOOK for {today.strftime('%Y%m%d')}\n")
                logfile.write(f"Telescope,{pn['Telescope']}\n")
                logfile.write(f"Program ID,{pn['Program ID']},Proposal Title,{pn['Proposal Title']},PI,{pn['PI']}\n")
                logfile.write(f"Observer,{pn['Observer']},Telescope Operator,{pn['Telescope Operator']}\n")
                logfile.write("Date,Local Time,Target,Filter,Repeats,Exposure Time,Filename,Mask Name,")
                logfile.write("Grating,Sp. Exp.T,Sp. Filename,Comment\n")
        return self.logfile_name


    @property
    def logbook_exists(self):
        if self.logfile_name.is_file():
            return True
        return False
