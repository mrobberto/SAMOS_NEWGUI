#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 25 17:35:59 2023

@author: samos_dev

from : https://github.com/behrouzz/sdss
"""
import os
cwd = os.getcwd()

#from sdss import Region
from astropy.io import fits

ra = 179.689293428354
dec = -0.454379056007667
reg = Region(ra, dec, fov=0.033)

from astroquery.sdss import SDSS
from astropy import coordinates as coords

RA_HMS = '0h8m05.63s' 
DEG_HMS = '+14d50m23.3s'
pos = coords.SkyCoord('0h8m05.63s +14d50m23.3s', frame='icrs')
#xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)

pos = coords.SkyCoord(RA_HMS +' ' + DEG_HMS,frame='icrs')
#xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)




from astropy import units as u
pos = coords.SkyCoord(str(ra),str(dec), unit=(u.deg, u.deg))
#pos = coords.SkyCoord(RA_HMS +' ' + DEG_HMS,frame='icrs')
xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)
print(xid)

im = SDSS.get_images(matches=xid, band='g')

hdu_0 = im[0]
data = hdu_0[0].data
header = hdu_0[0].header
fits.writeto(os.path.join(cwd,'input_file.fits'), data, header, overwrite=True)


#import cv2
#data_rotated = cv2.rotate(data, cv2.ROTATE_90_CLOCKWISE)
from scipy import ndimage
data_rotated = ndimage.rotate(data, 270, reshape=True)

import copy
header_rotated = copy.deepcopy(header)



tmp = header['NAXIS1'] ; header_rotated['NAXIS2'] = tmp
tmp = header['NAXIS2'] ; header_rotated['NAXIS1'] = tmp
tmp = header['CRPIX1'] ; header_rotated['CRPIX2'] = tmp
tmp = header['CRPIX2'] ; header_rotated['CRPIX1'] = tmp
tmp = header['CD1_1'] ; header_rotated['CD1_2'] = tmp
tmp = header['CD1_2'] ; header_rotated['CD1_1'] = -tmp
tmp = header['CD2_1'] ; header_rotated['CD2_2'] = tmp
tmp = header['CD2_2'] ; header_rotated['CD2_1'] = -tmp


fits.writeto(os.path.join(cwd,'output_file.fits'), data_rotated, header_rotated, overwrite=True)

