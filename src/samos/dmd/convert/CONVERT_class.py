#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 14 14:15:21 2023

@author: samos_dev
"""
from astropy.io import fits
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs import WCS

from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())

from samos.utilities import get_data_file


class CONVERT():
#define the local directory, absolute so it is not messed up when this is called
    
    def __init__(self):
        # FITS file with the WCS parameters to convert between CCD and DMD pixels
        ccd2dmd_file = get_data_file("dmd.convert", "DMD_Mapping_WCS.fits")
        
        # extract the astrometric WCS 
        hdul = fits.open(ccd2dmd_file)
        wcshead = hdul[0].header
        self.ccd2dmd_wcs = WCS(wcshead,relax=True)
        self.yoffset = int(2048/4)
        hdul.close()

    def CCD2DMD(self, ccd_x, ccd_y):

        fits_x, fits_y = ccd_x, ccd_y
        dmd_x, dmd_y = self.ccd2dmd_wcs.all_pix2world(fits_x,fits_y,0)
        return (dmd_x*3600., dmd_y*3600.+self.yoffset)
    
    def DMD2CCD(self, dmd_x, dmd_y):
        dmd_y = dmd_y-self.yoffset
        
        dmd_skycoord = SkyCoord(dmd_x, dmd_y, unit=u.arcsecond)
        
        dmd_sx, dmd_sy = dmd_skycoord.ra.deg , dmd_skycoord.dec.deg
        
        ccd_x, ccd_y = self.ccd2dmd_wcs.all_world2pix(dmd_sx, dmd_sy, 0)
        return ccd_x,ccd_y 
        
        #pass

