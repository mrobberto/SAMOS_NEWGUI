#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 22:00:03 2022

import SAMOS_Functions

@author: robberto

to use:
> import SAMOS_Functions
> SF = SAMOS_Functions.Class_SAMOS_Functions()

05.31.2023: Modified create_fits_folder() to put all .fits images in SISI_images

""" 
import csv
from pathlib import Path
import os, sys
from datetime import datetime


#define the local directory, absolute so it is not messed up when this is called
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   
sys.path.append(parent_dir)

class Class_SAMOS_Functions:
    def __init__(self):
        self.system_files = local_dir 
    
# =============================================================================
#     def read_IP_default(self):
# =============================================================================
    def read_IP_default():
        dict_from_csv = {}

        with open(os.path.join(local_dir,"IP_addresses_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv
    
     
    
# =============================================================================
#     def read_IP_user(self):
# =============================================================================
    def read_IP_user():
        dict_from_csv = {}

        with open(os.path.join(local_dir,"IP_addresses_user.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv   
      
# =============================================================================
#     def read_dir_default(self):
# =============================================================================
    def read_dir_default():
        dict_from_csv = {}

        with open(os.path.join(local_dir,"dirlist_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv   

# =============================================================================
#     def read_dir_user(self):
# =============================================================================
    def read_dir_user():
        dict_from_csv = {}

        with open(os.path.join(local_dir,"dirlist_user.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv   
    
# =============================================================================
#     def read_IP_status(self):
# =============================================================================
    def read_IP_initial_status():
        dict_from_csv = {}

        with open(os.path.join(local_dir,"IP_initial_status_dict.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}
            
        return dict_from_csv     
    
# =============================================================================
# create directoy to store the data
# =============================================================================
    def create_fits_folder() :       

        today = datetime.now()
        
        #collect all SISI fits images in a common directory
        SISI_images_dir = "SISI_Images"
        
        #name of the daily directory    
        fits_dir = os.path.join( parent_dir, SISI_images_dir, "SAMOS_" + today.strftime('%Y%m%d') )
         
        #create if not existing (first image of the day...)
        isdir = os.path.isdir(fits_dir)
        if isdir == False:  
            os.mkdir(fits_dir)
        
        #write on a file the name of the directory hosting the image    
        fits_directory_file = open(os.path.join(parent_dir,"SAMOS_system_dev","fits_current_dir_name.txt"), "w")
        fits_directory_file.write(fits_dir)
        fits_directory_file.close()    
        
        return fits_dir
    
    def read_fits_folder():
        fits_directory_file = os.path.join(parent_dir,"SAMOS_system_dev","fits_current_dir_name.txt")
        fits_dir_open = open(fits_directory_file,'r')
        fits_dir = fits_dir_open.read()
        fits_dir_open.close() 
        return fits_dir


#print(SF.read_IP_user())    

