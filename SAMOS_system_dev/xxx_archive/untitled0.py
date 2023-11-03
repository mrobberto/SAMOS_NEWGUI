#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 10:37:35 2023

@author: samos_dev
"""
#CREATE AND MODIFY DICTIONARY
# https://www.digitalocean.com/community/tutorials/python-add-to-dictionary

parameters = {'Observer': "SAMOS team", 'Telescope': "SOAR"}

print("original dictionary: ", parameters)

parameters['a'] = 100  # existing key, overwrite
parameters['c'] = 3  # new key, add
parameters['d'] = 4  # new key, add 

print("updated dictionary: ", parameters)


#SAVE DICTIONARY AS JSON FILE
# https://www.geeksforgeeks.org/write-a-dictionary-to-a-file-in-python/

import json
with open('Parameters.txt', 'w') as convert_file:
     convert_file.write(json.dumps(parameters))