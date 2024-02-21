#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 18:11:10 2022

@author: robberto
"""
import sys, os
import numpy as np
from PIL import Image

from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)  
sys.path.append(parent_dir)

params = {'Exposure Time':5000,'CCD Temperature':2300,'Trigger Mode': 4, 'NofFrames': 1}
from samos.utilities import get_data_file
from samos.ccd.Class_CCD import Class_Camera
Camera= Class_Camera(dict_params=params)
from SAMOS_MOTORS_dev.Class_PCM import Class_PCM
PCM = Class_PCM()
if PCM.MOTORS_onoff == 0:
    print('MOTORS NOT CONNECTED!!')
    sys.exit()
print('echo from server:')
print(PCM.echo_client())
PCM.power_on()

# Actually import the controller
from SAMOS_DMD_dev.Class_DMD_dev import DigitalMicroMirrorDevice
dmd = DigitalMicroMirrorDevice()#config_id='pass') 
dmd.initialize()

import pandas as pd
from PIL import Image
folder = get_data_file('hadamard.mask_sets')

"""
v = Camera.expose()
print(v)
t=PCM.move_FW_pos_wheel("B1")
print(t)

v = Camera.expose()
print(v)

slit0 = {"index": 1, "x1":440, "x2": 640, "y1":1014, "y2":1034}
slits = [slit0]
dmd.apply_slits(slits)
v = Camera.expose()
print(v)

slit1 = {"index": 1, "x1":435, "x2": 600, "y1":620, "y2":640}
dmd.apply_slits([slit1])
v = Camera.expose()
print(v)
"""
