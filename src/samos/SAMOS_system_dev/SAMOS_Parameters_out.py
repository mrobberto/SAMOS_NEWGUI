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

from samos.utilities import get_data_file

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

        self.Image_on = tk.PhotoImage(file=get_data_file("tk.icons", "on.png"))
        self.Image_off = tk.PhotoImage(file=get_data_file("tk.icons", "off.png"))

        self.dir_dict = {'dir_Motors': '/motors',
                         'dir_CCD': '/ccd',
                         'dir_DMD': '/dmd',
                         'dir_SOAR': '/SAMOS_SOAR_dev',
                         'dir_SAMI': '/SAMOS_SAMI_dev',
                         'dir_Astrom': '/astrometry',
                         'dir_system': '/SAMOS_system_dev',
                         }
        #add the directory of the QL images
        self.QL_images = os.path.join(parent_dir,'SAMOS_QL_images')
        
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
        self.inoutvar.set("inside")

        self.SAMOS_arcs_mm_scale = 206265./ (4100*4) # f/4  arcsec/mm
        self.SOAR_arcs_mm_scale = 206265./ (4100*16.6) # f/4  arcsec/mm
        self.DMD_MirrorScale = self.SAMOS_arcs_mm_scale * 0.0137 # = 0.1723 #arcsecond/mirror  # 206265
        self.SISI_PixelScale = self.DMD_MirrorScale/1.125  # = 0.153  #arcsecond/pixel
        self.SISI_FieldSize_pixel = 1000
        self.scale_DMD2PIXEL = 0.892  # mirros to pixel as per e-mail by RB  Jan 207, 2023

        self.dmd_map_filename = ""

        """
        I am adding here the parameters that may change every night, 
        saved in the Parameters.txt file as a dictionary
        that has to be handled as a json file. 
        See Prameters_README.py for further info on how to handle it
        """
        Parameters_of_the_night = os.path.join(local_dir, "Parameters_of_the_night.txt")
        with open(Parameters_of_the_night) as f:
            data= f.read()
        self.PotN = json.loads(data)    
        self.Observer = self.PotN['Observer']
        self.Telescope = self.PotN['Telescope']
        self.Program_ID = self.PotN['Program ID']
        self.Telescope_Operator = self.PotN['Telescope Operator']
        #print(self.Observer)
        
        self.logbook_exists = 0
        self.Ginga_PA = 0
