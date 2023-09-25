#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 25 17:35:59 2023

@author: samos_dev

from : https://github.com/behrouzz/sdss
"""

from sdss import Region

ra = 179.689293428354
dec = -0.454379056007667

reg = Region(ra, dec, fov=0.033)