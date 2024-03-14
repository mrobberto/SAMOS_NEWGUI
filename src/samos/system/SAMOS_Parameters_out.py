#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep 12 17:52:35 2023

@author: samos_dev
"""
import tkinter as tk
import os
from pathlib import Path
import sys
import csv
import json #added to handle the Parameters.txt file

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)

from samos.utilities import get_data_file

class SAMOS_Parameters():
    """ Collection of parameters to be shared by the classes """

    def __init__(self):
        self.dir_dict = {'dir_Motors': '/motors',
                         'dir_CCD': '/ccd',
                         'dir_DMD': '/dmd',
                         'dir_SOAR': '/soar',
                         'dir_SAMI': '/SAMOS_SAMI_dev',
                         'dir_Astrom': '/astrometry',
                         'dir_system': '/system',
                         }
        #add the directory of the QL images
        self.QL_images = get_data_file("ql")
        
        """ Default IP address imported for all forms"""
        with open(get_data_file("system", "IP_addresses_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            self.IP_dict = {rows[0]: rows[1] for rows in reader}
        self.IP_status_dict = {
            'IP_Motors': False,
            'IP_CCD': False,
            'IP_DMD': False,
            'IP_SOAR': False,
            'IP_SAMI': False,
        }
        # Is SAMOS running in simulated mode?
        self.simulated = False

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
        
        self.logbook_exists = False
        self.Ginga_PA = False
