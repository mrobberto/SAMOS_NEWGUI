#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 13 11:54:16 2023

@author: samos_dev, Dana
"""

import numpy as np
import pandas as pd


# map loaded to DMD format is x0 x1 y0 y1 0

# some .csv files are formatted x, y, dx0, dy0, dx1, dy1
# Dana will change slit selection to be DMD format but for ones formatted like
#  above, you can use this


def dxdy_from_center(csv_file):
    
    new_fname = csv_file.strip(".csv")+"_map.csv" # can include filepath
    new_f = open(new_fname, "w")
    f = open(csv_file, "r")
    
    new_map_lines = []
    
    #first line is header
    for line in f.readlines()[1:]:
        
        slit_n, x, y, dx0, dy0, dx1, dy1 = np.array(line.split(",")).astype(float)
        
        
        x0 = x-dx0
        x1 = x+dx1
        y0 = y-dy0
        y1 = y+dy1
        new_map_line = "{:n},{:n},{:n},{:n}, 0".format(x0, x1, y0, y1)
        print(new_map_line)
        
        new_f.write(new_map_line+"\n")
        
    new_f.close()
    f.close()
    
        