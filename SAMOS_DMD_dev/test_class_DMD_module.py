#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan  6 18:11:10 2022

@author: robberto
"""
# These will come in handy to check out our data before we send it and to make some interesting test data
from IPython.display import Image
#%matplotlib inline
import matplotlib.pyplot as plt
import numpy as np
#from photutils import CircularAperture

# Actually import the controller
from Class_DMD_dev import DigitalMicroMirrorDevice
import time

import pandas as pd

t0=time.perf_counter()


# First let's instantiate our controller object
# Config ID can map to device specifics in the future
# I've left that up to whomever write the upper levels for the STUF

dmd = DigitalMicroMirrorDevice()#config_id='pass') 
dmd.initialize()

# As we run commands we can check out whether or not they're working with a little nanny cam set up here  :
# https://circle.logi.com/#/accessories/4be3b068-3008-4c44-b857-f8bb9ad6bf80
# Ask Jules or Steve Hope for the login/password

# There are two builtin states for the device, all white (ones) all black (zeros)
dmd._open()
dmd.flush()
#dmd._close()
#dmd.apply_checkerboard()
#dmd.apply_blackout()
#dmd.apply_whiteout()
#dmd.apply_invert()

#dmd.send_smart_whiteout()
#dmd.send_smart_message()

#find center
# =============================================================================
# # =============================================================================
#test_shape = np.ones((1080,2048)) # This is the size of the DC2K
# test_shape[427:543,1021:1027] = 0
# # =============================================================================
#test_shape[200:220,200:220] = 0
#test_shape[300:320,500:510] = 0
# # =============================================================================
# test_shape[400:410,600:602] = 0
# test_shape[547:563,700:737] = 0
# test_shape[600:620,800:860] = 0
# test_shape[630:940,900:960] = 0
# test_shape[700:720,1050:1060] = 0
# test_shape[730:740,1150:1160] = 0
# test_shape[745:760,1250:1260] = 0
# test_shape[830:840,1360:1390] = 0
# test_shape[845:960,1560:1590] = 0
# test_shape[930:940,1780:1860] = 0
# test_shape[940:960,1980:2048] = 0
# # # =============================================================================
# # =============================================================================
#dmd.apply_shape(test_shape)
# 
# =============================================================================
# # > CCD:515,488 = DMD:540,1024
# =============================================================================

#pinhole at the center
# =============================================================================
"""
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
xc = 540
yc = 1024
test_shape[xc:xc+1,yc:yc+1] = 0
dmd.apply_shape(test_shape)
dmd.apply_invert()    
"""
# 
#test_shape[xc-1:xc+1,yc-1:yc+1] = 0
# # > CCD:515,488 = DMD:540,1024
# =============================================================================

#
#test_shape = np.ones((1080,2048)) # This is the size of the DC2K
#test_shape[513:598,:] = 0
#dmd.apply_shape(test_shape)
# We'll now have a track of what we expect the DMD to look like, which is all ones
#print(dmd.current_dmd_shape)
# And a plot of the expected shape.

#read_table
'''
# =============================================================================
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
# =============================================================================
import pandas as pd
# #table = pd.read_csv("test_pattern1_92.03352_24.35393.dat")
table = pd.read_csv("grid 11x11x3.csv")
xoffset = 0#np.full(len(table.index),int(0))
yoffset = np.full(len(table.index),int(2048/4))
y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
slits = []# {"index": 1, "x1":x0[0], "x2": xq[0], "y1":y1[0], "y2":y2[0]} ]
for i in table.index:
    slits.append( {"index": i+1, "x1":x1[i], "x2": x2[i], "y1":y1[i], "y2":y2[i]} )
# print(slits)
dmd.apply_slits(slits)
# t1 = time.perf_counter()
# print('\m elapsed',t1-t0,' seconds')
# # 
# =============================================================================
# =============================================================================
'''

#dmd.apply_invert()    



# =============================================================================
# RANDOM SET OF CUSTOM SLITS
# =============================================================================
# =============================================================================
slit0 = {"index": 1, "x1":440, "x2": 640, "y1":848, "y2":1248}
#slit1 = {"index": 1, "x1":435, "x2": 600, "y1":620, "y2":640}
#slit2 = {"index": 2, "x1":535, "x2": 550, "y1":700, "y2":740}
#slit3 = {"index": 3, "x1":635, "x2": 650, "y1":800, "y2":840}
#slit4 = {"index": 4, "x1":735, "x2": 750, "y1":700, "y2":740}
#slit5 = {"index": 5, "x1":835, "x2": 850, "y1":800, "y2":840}
#slit6 = {"index": 6, "x1":935, "x2": 950, "y1":900, "y2":940}
#slit7 = {"index": 7, 'x1': 609, 'x2': 615, 'y1': 521, 'y2': 527}
#slit8 = {"index": 8, 'x1': 619, 'x2': 625, 'y1': 621, 'y2': 627}
#slit9 = {"index": 9, 'x1': 629, 'x2': 635, 'y1': 721, 'y2': 727}
#slit10 = {"index": 10, 'x1': 639, 'x2': 645, 'y1': 821, 'y2': 827}
# # =============================================================================
#slit11 = {"index": 11, 'x1': 649, 'x2': 665, 'y1': 921, 'y2': 927}
#slit12 = {"index": 12, 'x1': 409, 'x2': 575, 'y1': 1021, 'y2': 1027}
slits = [slit0]#[slit1,slit2,slit3,slit4,slit5,slit6,slit7,slit8,slit9,slit10,slit11,slit12]
# #slits=[slit1,slit11,slit12]
# #slits=[slit1]
#print(slits)
#dmd.apply_slits(slits)




# =============================================================================
# PINHOLE GRID WITH IMPORTED .csv table
# =============================================================================
# =============================================================================
"""
import pandas as pd
# #table = pd.read_csv("test_pattern1_92.03352_24.35393.dat")
table = pd.read_csv("grid 11x11x3.csv")
xoffset = 0#np.full(len(table.index),int(0))
yoffset = np.full(len(table.index),int(2048/4))
y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
for i in table.index:
    test_shape[x1[i]:x2[i],y1[i]:y2[i]]=0
dmd.apply_shape(test_shape)

#dmd.apply_invert()    

t1 = time.perf_counter()
print('\m elapsed',t1-t0,' seconds')
# # =============================================================================
# =============================================================================
"""

#A PINHOLE GRID OF 1 MIRROR
"""
# =============================================================================
#...
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
xc = 540
yc = 1024
for i in range(11):
    for j in range(11):
        x = xc - 100 * (i-5)
        y = yc - 100 * (j-5)
        print(x,y)
        test_shape[x,y] = 0
test_shape[528:552,1024]=0
#test_shape[540,1000:1048]=0
#test_shape[538:542,0:2047]=0
dmd.apply_shape(test_shape)
#dmd.apply_invert()    
pd_array_11x11x1 = pd.DataFrame(test_shape)
pd_array_11x11x1.to_csv("Grid 11x11x1.csv")
"""

#A DIAGONAL CROSS 
"""
# =============================================================================
#...
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
xc = 540
yc = 1024
#test_shape[0:5,0:2048] = 0
#test_shape[1076:1081,0:2048] = 0
#test_shape[0:1080,512:517] = 0
#test_shape[0:1080,1531:1536] = 0
for i in range(3,xc,10):
    print([xc-i,xc-i+1,yc-i,yc-i+1])
    test_shape[xc-i-2:xc-i+3,yc-i-2:yc-i+3] = 0
    test_shape[xc-i-2:xc-i+3,yc+i-2:yc+i+3] = 0
    test_shape[xc+i-2:xc+i+3,yc-i-2:yc-i+3] = 0
    test_shape[xc+i-2:xc+i+3,yc+i-2:yc+i+3] = 0   
#import matplotlib.pyplot as plt
plt.imshow(test_shape)
plt.show()
dmd.apply_shape(test_shape)
#pd_cross = pd.DataFrame(test_shape)
#pd_cross.to_csv("cross.csv")
#
"""

#A GRID OF LINEs
"""
# =============================================================================
#...
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
xc = 540
yc = 1024
delta=5
for i in range(50,100,2*delta):
    for j in range(50,100):
        x = i
        y = j+512
        test_shape[x:x+delta,y] = 0
#        print(x,y)
        x = i+930
        y = j+512
        test_shape[x:x+delta,y] = 0
#        print(x,y)
        x = i
        y = j+930+512
        test_shape[x:x+delta,y] = 0
        x = i+930
        y = j+930+512
        test_shape[x:x+delta,y] = 0
dmd.apply_shape(test_shape)
dmd.apply_invert()    
#pd_array_11x11x1 = pd.DataFrame(test_shape)
#pd_array_11x11x1.to_csv("Grid 11x11x1.csv")
"""


#A GRID OF 1 MIRROR PINHOLES
"""
# =============================================================================
test_shape = np.ones((1080,2048)) # This is the size of the DC2K
for l in [762,117]:
    for k in [200,865]:
        for i in range(0,25,5):
            for j in range(0,25,5):
                x = i+k
                y = j+l
                test_shape[x,y] = 0
for i in range(0,25,5):
     for j in range(0,25,5):
          x = i+530
          y = j+1030
          test_shape[x,y] = 0
#        print(x,y)
dmd.apply_shape(test_shape)
#dmd.apply_invert()    
#pd_array_11x11x1 = pd.DataFrame(test_shape)
#pd_array_11x11x1.to_csv("Grid 11x11x1.csv")
"""


