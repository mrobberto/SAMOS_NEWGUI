#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 14:42:28 2023

@author: samos_dev
"""

filenames = ['header.py', 'commands.py']
with open('test_go.py', 'w') as outfile:
    for fname in filenames:
        with open(fname) as infile:
            outfile.write(infile.read())

outfile.close()
import test_go
