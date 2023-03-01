#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 11:34:16 2023

@author: danakoeppe
"""

import numpy as np
import pandas as pd
import os

from astropy.io import fits


class Wrapper():
    
    """
    Wrapper for main FITSHead class that updates the main dict
    whenever one of the param attributes is changed.
    Also keeps track of the original value before the change.
    """
    def __init__(self, wrapped):
        self._wrapped = wrapped
        
    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)
    
    def __setattr__(self, attr, val):
        if attr == '_wrapped':
            super(Wrapper, self).__setattr__('_wrapped', val)
        else:
            setattr(self._wrapped, 'prev_' + attr, getattr(self._wrapped, attr))
            old_val = getattr(self._wrapped, attr)
            setattr(self._wrapped, attr, val)
            self.create_main_params_dict()
            print("{} changed from {} to {}".format(attr,old_val,val))
 
           


class FITSHead():
    """
    Obtain instrument configurations, WCS, etc. and
        keep track of them with a dictionary.
    After exposure, write the contents of dictionary to FITS header
        using header.set(key,val,comment)
        
    Using dictionaries because they can keep track of the 
    header keyword, value, and comments.
    Each attribute can the be combined into a main param dict,
    which will get written to header.
    
    """
    
    def __init__(self):
        
        self.main_dict = None # main dictionary will be the container for all params
        
        self.filename = None
        
        self.expTime = None
        self.objName = None # 'OBJECT' name of object i.e. ABELL S1101
        self.obsType = None# 'OBSTYPE' type of observation i.e. BIAS, FLAT, OBJ...
        self.radecSys = 'FK5' # prob won't change
        self.radecEq = 2000# prob won't change
        self.ra = None
        self.dec = None
        
        # ---------parameters from SAM adaptive optics module (AOM)--------- #
        
        ### motor controllers, switches, and telemetry boards of AOM are connected to the instrument computer (IC)
        self.telRA = None
        self.telDEC = None
        self.hourangle = None
        self.airmass = None
        
        ## position angle of the RA and DEC axes relative to the +Y axis of CCD, positive is CCW        
        self.rapangl = None # position angle PA-90
        self.decpangl = None # position angle PA
        
        # ----------------------- #
        
        # ---------WCS related parameters--------- #
        # can probably just be fully imported after astrometry is complete
        # but writing them here for now
        
        ### SAMOS Imaging CCD parameters
        self.pixsize1 = 13
        self.pixsize2 = 13
        self.pixscale1 = 0.17
        self.pixscale2 = 0.17
        
        # matrix elements for astrometric solution
        
        self.wcsdim = 2
        self.ctype1 = 'RA---TAN' # RA---TAN-SIP? for distorion
        self.ctype2 = 'DEC--TAN' # DEC--TAN-SIP?
        self.crval1 = None
        self.crval2 = None
        self.crpix1 = None
        self.crpix2 = None
        self.cd11 = None
        self.cd22 = None
        self.cd12 = None
        self.cd21 = None
        self.cdelt1 = None # degrees per pixel serial direction
        self.cdelt2 = None # degrees per pixel parallel direction
        
        
        # ----------------------- #
        
        
        # ---------SAMOS configuration parameters--------- #
        # including params for spec side for completeness
        
        
        self.filters = None
        self.filter1 = None
        self.filter2 = None
        self.filtpos = None
        self.grating = None
        self.dmdReg = None # not a standard FITS keyword
        
    def create_main_params_dict(self):
        
        """
        Combine all the attributes into a single dictionary 
            that will be passed to the write_fits_header method.
        """
        
        ## need to put these in a better order
        
        self.main_dict = {'FILENAME' : self.filename,
                'EXPTIME': (self.expTime, 'Exposure time (s)'),
                'OBJECT': (self.objName,'User-defined name of object'),
                'OBSTYPE': (self.obsType, 'Type of observation'),
                'RADECSYS': (self.radecSys, 'Default coordinate system'),
                'RADECEQ': (self.radecEq, 'Default equinox'),
                'RA': (self.ra,'RA of object (hr)'),
                'DEC': (self.dec,'DEC of object (deg)'),
                'TELRA':(self.telRA, 'RA of telescope (hr)'),
                'TELDEC': (self.telDEC, 'DEC of telescope (deg)'),
                'HA': (self.hourangle, 'Hourangle (H:M:S)'),
                'AIRMASS': (self.airmass, 'Airmass'),
                'RAPANGL': (self.rapangl, 'Position angle of the RA axis (deg)'),
                'DECPANGL': (self.decpangl, 'Position angle of the DEC axis (deg)'),
                'PIXSIZE1': (self.pixsize1, 'Unbinned pixel size for axis 1 (microns)'),
                'PIXSIZE2': (self.pixsize2, 'Unbinned pixel size for axis 2 (microns)'),
                'PIXSCALE1': (self.pixscale1, 'Unbinned pixel scale for axis 1 (arcsec/pixel)'),
                'PIXSCALE2': (self.pixscale2, 'Unbinned pixel scale for axis 2 (arcsec/pixel)'),
                'WCSDIM': (self.wcsdim, 'WCS dimensionality'),
                'CTYPE1': (self.ctype1, 'Coordinate type'),
                'CTYPE2': (self.ctype2, 'Coordinate type'),
                'CRVAL1': (self.crval1, 'Coordinate reference value'),
                'CRVAL2': (self.crval2, 'Coordinate reference value'),
                'CRPIX1': (self.crpix1, 'Coordinate reference pixel'),
                'CRPIX2': (self.crpix2, 'Coordinate reference pixel'),
                'CD1_1': self.cd11,
                'CD2_2': self.cd22,
                'CD1_2': self.cd12,
                'CD2_1': self.cd21,
                'CDELT1': self.cdelt1,
                'CDELT2': self.cdelt2,
                'FILTERS': (self.filters, 'Names of filter wheels in A and B'),
                'FILTER1': (self.filter1, 'Name of filter wheel A'),
                'FILTER2': (self.filter2, 'Name of filter wheel B'),
                'FILTPOS': (self.filtpos, 'Filter positions A and B'),
                'GRATING' : (self.grating, 'VPH grating name'),
                'DMDREG' : (self.dmdReg, 'Name of corresponding DMD .reg file')}
        
        
    def write_fits_header(self, input_header):
        
        """
        Set header keys based on main dictionary
        For None values, replace with empty string.
        Params:
            input_header : the CCD will create its own FITS header,
                this function will update/add values.
        """
        
        output_header = input_header.copy()
        
        if self.main_dict is None:
            self.create_main_params_dict()
        
        for key, value in self.main_dict.items():
            
            if type(value)==tuple:
                val = value[0]
                comment = value[1]
                if val is None:
                    val='unavail '
                
                output_header.set(key,val,comment)
            else:
                if value is None:
                    value = 'unavail '
                output_header.set(key, value)
            
        self.output_header = output_header
        
        

#FITSHead()   
        
        
        