#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 21:42:31 2023

@author: robberto
"""

"""
Sample JPEG images
This gets single-band grayscale and color JPEG images at the position of the Crab Nebula. 
The extracted region size is 1280 pixels = 320 arcsec."
"""
import numpy
import matplotlib.pyplot as plt

from samos.astrometry.guide_stars import PanSTARRSGuideStar as PS

PS = PS()

# Crab Nebula position
ra = 83.633210
dec = 22.014460
size = 1280

# grayscale image
gim = PS.get_gray_im(ra, dec, size=size, filter="i")
# color image
cim = PS.get_color_im(ra, dec, size=size, filters="grz")

plt.rcParams.update({'font.size':12})
plt.figure(1,(12,6))
plt.subplot(121)
plt.imshow(gim,origin="upper",cmap="gray")
plt.title('Crab Nebula PS1 i')
plt.subplot(122)
plt.title('Crab Nebula PS1 grz')
plt.imshow(cim,origin="upper")


"""
Load and display a FITS image
Note that the  𝑦
 -axis is flipped in the JPEG image compared with the original FITS image.
 """
 
from astropy.io import fits
from astropy.visualization import PercentileInterval, AsinhStretch

fitsurl = PS.get_url(ra, dec, size=size, filters="i", format="fits")
fh = fits.open(fitsurl[0])
fim = fh[0].data
# replace NaN values with zero for display
fim[numpy.isnan(fim)] = 0.0
# set contrast to something reasonable
transform = AsinhStretch() + PercentileInterval(99.5)
bfim = transform(fim)

plt.figure(1,(12,6))
plt.subplot(121)
plt.imshow(gim,cmap="gray",origin="upper")
plt.title('Crab Nebula PS1 i (jpeg)')

plt.subplot(122)
plt.title('Crab Nebula PS1 i (fits)')
plt.imshow(bfim,cmap="gray",origin="lower")


plt.figure()
plt.imshow(bfim, cmap='gray')
plt.colorbar()


