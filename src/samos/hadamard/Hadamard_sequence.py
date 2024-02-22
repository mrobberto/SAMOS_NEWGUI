#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  9 11:43:24 2023

@author: samos_dev
"""

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
import glob
hf = sorted(glob.glob(folder+"*.bmp"))
i=0
for file in hf:
    print("\n\n *** ITERATION NR:", str(i), " OUT OF ", len(hf),"\n\n")
    i += 1
    im =np.asarray(Image.open(file), dtype='int')
    dmd.apply_shape(im)
    v = Camera.expose()
print(v)

