#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 20 15:51:40 2023

@author: samos_dev
"""

from astropy.io.votable import parse
votable = parse("/Users/samos_dev/Desktop/result.xml")
print(votable)

from astropy.io.votable import parse_single_table
table = parse_single_table("/Users/samos_dev/Desktop/result.xml")
print(table.array[0][1])