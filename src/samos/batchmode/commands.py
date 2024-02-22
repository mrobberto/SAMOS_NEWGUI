#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 11:43:24 2023

@author: samos_dev
"""
params = {'Exposure Time':1000,'CCD Temperature':2300,'Trigger Mode': 4, 'NofFrames': 1}

v = Camera.expose()
print(v)
t=PCM.move_FW_pos_wheel("B1")
print(t)

v = Camera.expose()
print(v)

#slit0 = {"index": 1, "x1":440, "x2": 640, "y1":1014, "y2":1034}
#slits = [slit0]
#dmd.apply_slits(slits)
#v = Camera.expose()
#print(v)

#slit1 = {"index": 1, "x1":435, "x2": 600, "y1":1220, "y2":1440}
#dmd.apply_slits([slit1])
#v = Camera.expose()
#print(v)
name = 'S83_4w_mask_43.bmp'
im =np.asarray(Image.open(folder+name), dtype='int')
#im = pd.read_csv(folder+name,header=None)
dmd.apply_shape(im)
v = Camera.expose()
print(v)

