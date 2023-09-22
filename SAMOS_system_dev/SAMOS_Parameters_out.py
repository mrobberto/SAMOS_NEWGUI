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
sys.path.append(parent_dir)

dir_SYSTEM = os.path.join(local_dir, "SAMOS_system_dev")

class SAMOS_Parameters():
    """ Collection of paramaeters to be shared by the classes """

    def __init__(self):
        """
        Defines:
            self.Image_on/off
            self.dir_dict
            self.IP_dict
            self.IP_status_dict
            self.inoutvar
            self.scale_DMD2PIXEL = 0.892
        """

        self.Image_on = tk.PhotoImage(file=os.path.join(
            parent_dir, "tk_utilities", "Images", "on.png"))
        self.Image_off = tk.PhotoImage(file=os.path.join(
            parent_dir, "tk_utilities", "Images", "off.png"))

        self.dir_dict = {'dir_Motors': '/SAMOS_MOTORS_dev',
                         'dir_CCD': '/SAMOS_CCD_dev',
                         'dir_DMD': '/SAMOS_DMD_dev',
                         'dir_SOAR': '/SAMOS_SOAR_dev',
                         'dir_SAMI': '/SAMOS_SAMI_dev',
                         'dir_Astrom': '/SAMOS_Astrometry_dev',
                         'dir_system': '/SAMOS_system_dev',
                         }

        """ Default IP address imported for all forms"""
        ip_file_default = os.path.join(local_dir, "IP_addresses_default.csv")
        with open(ip_file_default, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        inp.close()
        self.IP_dict = {}
        self.IP_dict['IP_Motors'] = dict_from_csv['IP_Motors']
        self.IP_dict['IP_CCD'] = dict_from_csv['IP_CCD']
        self.IP_dict['IP_DMD'] = dict_from_csv['IP_DMD']
        self.IP_dict['IP_SOAR'] = dict_from_csv['IP_SOAR']
        self.IP_dict['IP_SAMI'] = dict_from_csv['IP_SAMI']

        self.IP_status_dict = {'IP_Motors': False,
                               'IP_CCD': False,
                               'IP_DMD': False,
                               'IP_SOAR': False,
                               'IP_SAMI': False,
                               }
        """ REMOVED
        self.IP_dict =  {'IP_Motors': '128.220.146.254:8889',
                         'IP_CCD'   : '128.220.146.254:8900',
                         'IP_DMD'   : '128.220.146.254:8888',
                         'IP_SOAR'  : 'TBD',
                         'IP_SAMI'  : 'TBD',
                        } 
        """

        self.inoutvar = tk.StringVar()
        self.inoutvar.set("outside")

        self.scale_DMD2PIXEL = 0.892  # mirros to pixel as per e-mail by RB  Jan 207, 2023

        self.dmd_map_filename = ""

        """
        I am adding here the parameters that may change every night, 
        saved in the Parameters.txt file as a dictionary
        that has to be handled as a json file. 
        See Prameters_README.py for further info on how to handle it
        """
        Parameters_of_the_night = os.path.join(local_dir, "Parameters.txt")
        with open(Parameters_of_the_night) as f:
            data= f.read()
        self.PotN = json.loads(data)    
        #self.Observer = PotN['Observer']
        #self.Telescope = PotN['Telescope']
        #self.Program_ID = PotN['Program ID']
        #self.Telescope_Operator = PotN['Telescope Operator']
        #print(self.Observer)
       