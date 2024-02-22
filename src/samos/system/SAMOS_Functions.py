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

from samos.utilities import get_data_file


#define the local directory, absolute so it is not messed up when this is called
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   

class Class_SAMOS_Functions:
    def __init__(self):
        self.system_files = local_dir 
        super().__init__(self)
    
# =============================================================================
#     def read_IP_default(self):
# =============================================================================
    def read_IP_default():
        dict_from_csv = {}

        with open(get_data_file("system", "IP_addresses_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv
    
     
    
# =============================================================================
#     def read_IP_user(self):
# =============================================================================
    def read_IP_user():
        dict_from_csv = {}

        with open(get_data_file("system", "IP_addresses_user.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv   
      
# =============================================================================
#     def read_dir_default(self):
# =============================================================================
    def read_dir_default():
        dict_from_csv = {}

        with open(get_data_file("system", "dirlist_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv   

# =============================================================================
#     def read_dir_user(self):
# =============================================================================
    def read_dir_user():
        dict_from_csv = {}

        with open(get_data_file("system", "dirlist_user.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        return dict_from_csv   
    
# =============================================================================
#     def read_IP_status(self):
# =============================================================================
    def read_IP_initial_status():
        dict_from_csv = {}

        with open(get_data_file("system", "IP_initial_status_dict.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}
            
        return dict_from_csv     
    
# =============================================================================
# create directoy to store the data
# =============================================================================
    def create_fits_folder() :       

        today = datetime.now()
        
        #collect all SISI fits images in a common directory
        SISI_images_dir = "../SISI_Images"
        
        #name of the daily directory    
        fits_dir = os.path.join( parent_dir, SISI_images_dir, "SAMOS_" + today.strftime('%Y%m%d') )
        SISI_QL_images_dir = os.path.join(fits_dir,"QL_images")
         
        #create if not existing (first image of the day...)
        isdir = os.path.isdir(fits_dir)
        if isdir == False:  
            os.mkdir(fits_dir)
            os.mkdir(SISI_QL_images_dir)
        
        #write on a file the name of the directory hosting the image    
        fits_directory_file = open(get_data_file("system", "fits_current_dir_name.txt"), "w")
        fits_directory_file.write(fits_dir)
        fits_directory_file.close()    
        
        return fits_dir
    
    def read_fits_folder():
        fits_directory_file = get_data_file("system", "fits_current_dir_name.txt")
        fits_dir_open = open(fits_directory_file,'r')
        fits_dir = fits_dir_open.read()
        fits_dir_open.close() 
        return fits_dir

#print(SF.read_IP_user())    

# =============================================================================
# create directoy to store the data
# =============================================================================
    def create_log_file(Telescope='SOAR',
                        ProgramID='1',
                        ProposalTitle="Test",
                        PI="MR", 
                        Observer="SAMOS team",
                        Operator="Operator"):       
        """ Invoked to create log file"""
        today = datetime.now()
        #
        SISI_images_dir = "../SISI_Images"
        logfile_name = os.path.join( parent_dir, SISI_images_dir, "SAMOS_LOGFILE_" + today.strftime('%Y%m%d')+ '.csv' )
        logfile = open(logfile_name, 'w+')

        logfile.write("SAMOS LOGBOOK for " + today.strftime('%Y%m%d')+'\n') 
        logfile.write("Telescope" + "," + Telescope + "\n")
        logfile.write("Program ID," + ProgramID + "," + "Proposal Title," + ProposalTitle + "," + "PI," + PI + '\n' )
        logfile.write("Observer," +  Observer + "," + "Telescope Operator," + Operator +'\n')
        logfile.write("Date," + 
                      "Local Time," +
                      "Target," + 
                      "Filter," +
                      "Repeats," +
                      "Im. Exp.T," + 
                      "Im. Filename," +
                      "MaskName," +
                      "Grating," +
                      "Sp. Exp.T," + 
                      "Sp. Filename," +
                      "Comment\n")
        logfile.close()
        return logfile_name
        
    def check_log_file():
        """ Invoked to check if log file exists"""
        today = datetime.now()
        #
        SISI_images_dir = "../SISI_Images"
        logfile_name = os.path.join( parent_dir, SISI_images_dir, "SAMOS_LOGFILE_" + today.strftime('%Y%m%d')+ '.csv' )
        if os.path.isfile(logfile_name) is True:
            return logfile_name
        else:
            return False
        
