#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 22 11:34:16 2023

@author: danakoeppe
"""


class FITSHead(object):
    """
    Obtain instrument configurations, WCS, etc. and keep track of them with a dictionary.

    After exposure, write the contents of dictionary to FITS header using header.set(key,val,comment)
        
    Using dictionaries because they can keep track of the header keyword, value, and comments.

    Each attribute can the be combined into a main param dict, which will get written to header.
    """
    def __init__(self, par, db, logger):
        self.PAR = par
        self.db = db
        self.logger = logger

        self.filename = None  # base filename e.g. 'NGC1976_83.819696	-5.390333'
        self.filedir = None
        self.extensions = False
        self.gridfnam = None  # if image is grid, name of grid pattern file .csv
        
        self.combined = "F"
        self.ncombined = 0
        
        self.expTime = None
        self.objname = None
        self.obstype = None  # 'OBSTYPE' type of observation e.g. BIAS, FLAT, OBJ...
        self.radecSys = 'FK5'  # prob won't change
        self.radecEq = 2000  # prob won't change
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
        
        ### SAMOS Imaging CCD parameters
        self.pixsize1 = 13
        self.pixsize2 = 13
        self.pixscale1 = 0.17
        self.pixscale2 = 0.17
        
        # matrix elements for astrometric solution
        self.wcsdim = 2
        self.ctype1 = 'RA---TAN'  # RA---TAN-SIP? for distorion
        self.ctype2 = 'DEC--TAN'  # DEC--TAN-SIP?
        self.crval1 = None
        self.crval2 = None
        self.crpix1 = None
        self.crpix2 = None
        self.cd11 = None
        self.cd22 = None
        self.cd12 = None
        self.cd21 = None
        self.cdelt1 = None  # degrees per pixel serial direction
        self.cdelt2 = None  # degrees per pixel parallel direction
        
        # ---------SAMOS configuration parameters--------- #
        # including params for spec side for completeness
        self.filter = None
        self.filtpos = None
        self.grating = None
        self.gratpos = None
        self.fw1step = None
        self.fw2step = None
        self.grastep = None
        self.grbstep = None
        self.dmdmap = None  # region file of slits in in celestial coords


    def set_param(self, param, val):
        """
        Set/change parameter value 
        """
        self.logger.info(f"Changing {param} from {getattr(self, param)} to {val}")
        if not hasattr(self, param.lower()):
            self.logger.error(f"NO PARAMETER {param}!")
            return
        setattr(self, param.lower(), val)


    @property
    def main_dict(self):
        """
        Combine all the attributes into a single dictionary that will be passed to the write_fits_header method.
        """
        main_dict = {
            'FILENAME' : self.filename,
            'FILEDIR' : self.filedir,
            'EXTEND' : self.extensions,
            'OBSERVER' : (self.db.get_value("POTN_Observer"), 'Observer Name(s)'),
            'PROGID' : (self.db.get_value("POTN_Program"), 'Program ID'),
            'TONAMES' : (self.db.get_value("POTN_Telescope_Operator"), 'Telescope Operator(s)'),
            'GRIDFNAM' : (self.gridfnam, 'Grid pattern filename'),
            'EXPTIME': (self.expTime, 'Exposure time (s)'),
            'COMBO' : (self.combined, 'Is combined image (T/F)'),
            'NCOMBO': (self.ncombined, 'Number of combined images'),
            'TARGET': (self.db.get_value("POTN_Target"), 'User-defined name of object'),
            'OBJNAME': (self.objname, "User-defined object name"),
            'OBSTYPE': (self.obstype, 'Type of observation'),
            'FILTER': (self.filter, 'Name of filter'),
            'FILTPOS': (self.filtpos, 'Filter position'),
            'FW1_STEP': (self.fw1step, "Reported step position of filter wheel 1"),
            'FW2_STEP': (self.fw2step, "Reported step position of filter wheel 2"),
            'GRATING' : (self.grating, 'VPH grating name'),
            'GRATPOS': (self.gratpos, 'Grating position'),
            'GRA_STEP': (self.grastep, "Reported step position of grating rail A"),
            'GRB_STEP': (self.grbstep, "Reported step position of grating rail B"),
            'DMDMAP' : (self.dmdmap, 'Name of corresponding DMD file')
        }
        return main_dict


    @property
    def main_astrometric_dict(self):
        """
        Combine all the attributes into a single dictionary that will be passed to the write_fits_header method.
        """
        main_astrometric_dict = {  
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
            'PIXSCAL1': (self.pixscale1, 'Unbinned pixel scale for axis 1 (arcsec/pixel)'),
            'PIXSCAL2': (self.pixscale2, 'Unbinned pixel scale for axis 2 (arcsec/pixel)'),
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
            'CDELT2': self.cdelt2
        }
        return main_astrometric_dict


    def create_fits_header(self, input_header):
        """
        Set header keys based on main dictionary
        For None values, replace with empty string.
        Params:
            input_header : the CCD will create its own FITS header,
                this function will update/add values.
        """
        output_header = self._update_header_from_dict(input_header.copy(), self.main_dict)
        output_header = self._update_header_from_dict(output_header, self.main_astrometric_dict)
        return output_header


    def add_main_fits_keywords(self, input_header):
        return self._update_header_from_dict(input_header.copy(), self.main_dict)


    def add_astrometric_fits_keywords(self, input_header):
        return self._update_header_from_dict(input_header.copy(), self.main_astrometric_dict)


    def load_DMD_grid(self, gridfnam):
        """ 
        1. open the .csv dmd grid file
        2. convertto the the format adeqae for the fits header
        3. 
     
        """
        self.gridfnam = gridfnam


    def _update_header_from_dict(self, header, input_dict):
        for key in input_dict:
            value = input_dict[key]
            if isinstance(value, tuple):
                val, comment = value[0], value[1]
            else:
                val, comment = value, ""

            if val is None:
                # Don't update an existing key with nothing
                if key in header:
                    continue
                val = "unavail "

            header.set(key, val, comment)
        return header
