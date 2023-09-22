#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 10:37:35 2023

@author: samos_dev
"""
#CREATE AND MODIFY DICTIONARY
# https://www.digitalocean.com/community/tutorials/python-add-to-dictionary

parameters = {'Observer': "SAMOS team", 
              'Telescope': "SOAR",
              'Program ID': 0,
              'Telescope Operator': 0,
              'Object Name': "NGC 3105",
              'Comment': "none",
              'Bias Comments': "none",
              'Dark Comments': "none",
              'Flat Comments': "none",
              'Buffer Comments': "none",
              'Base Filename': "Test"}

print("original dictionary: ", parameters)

#parameters['a'] = 100  # existing key, overwrite
#parameters['c'] = 3  # new key, add
#parameters['d'] = 4  # new key, add 
#print("updated dictionary: ", parameters)


#SAVE DICTIONARY AS JSON FILE
# https://www.geeksforgeeks.org/write-a-dictionary-to-a-file-in-python/

import json
with open('Parameters.txt', 'w') as convert_file:
     convert_file.write(json.dumps(parameters))

#READ DICTIONARY FROM A JSON FILE
# https://www.geeksforgeeks.org/how-to-read-dictionary-from-file-in-python/

# reading the data from the file
with open('Parameters.txt') as f:
    data = f.read()
  
print("Data type before reconstruction : ", type(data))
      
# reconstructing the data as a dictionary
js = json.loads(data)
  
print("Data type after reconstruction : ", type(js))
print(js)

print("Extract after reconstruction : ", js.keys(),js['Observer'])

#also
for key, value in js.items() :
    print(key, value)
