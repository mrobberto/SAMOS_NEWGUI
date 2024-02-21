#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:14:08 2023

@author: robberto

from
https://www.geeksforgeeks.org/how-to-detect-if-a-specific-key-pressed-using-python/
"""

for _ in range(3):
 
    user_input = input(" Please enter your lucky word or type 'END' to terminate loop: ")
     
    if user_input == "geek":
        print("You are really a geek")
        break
 
    elif user_input == "END":
        break
 
    else:
        print("Try Again")