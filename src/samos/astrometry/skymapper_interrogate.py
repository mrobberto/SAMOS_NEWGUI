#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 22:05:04 2023

@author: robberto
"""
from astropy import units as u
from astropy.io import fits
import logging
import numpy as np
import pandas as pd
import re
import shutil
import tempfile
import urllib.request

from samos.utilities import get_temporary_dir


def skymapper_interrogate(ra, dec, ra_size=1058, dec_size=1032, filter='r'):
    """
    ***** This documentation needs to be checked for accuracy
    Query the skymapper.nci.org.au website for information on the supplied location.
    
    Parameters
    ----------
    ra : float
        RA in decimal degrees of centre of location
    dec : float
        DEC in decimal degrees of centre of location 
    ra_size : int, default=1058
        Size of field in the RA direction (arcseconds). Default is magic.
    dec_size : int, default=1032
        Size of field in the DEC direction (arcseconds). Default is magic.
    filter: str, default 'r'
        Filter to retrieve
    
    Returns
    -------
    """
    pixel_scale = 0.18 * u.arcsec / u.pix
    base_url = "https://api.skymapper.nci.org.au/public/siap/dr2/"
    out_dir = get_temporary_dir()
    
    logger = logging.getLogger('samos')

    # Handle formatting of values to proper units
    ra = ra * u.deg
    dec = dec * u.deg
    size_ra = (ra_size * u.pixel * pixel_scale).to(u.deg)
    size_dec = (dec_size * u.pixel * pixel_scale).to(u.deg)
    
    # Convert units to scalar values for use in the query
    ra = ra.value
    dec = dec.value
    size_ra = size_ra.value
    size_dec = size_dec.value
    
    query = base_url + "query?POS={},{}&SIZE={},{}&BAND={}&FORMAT=image/fits&INTERSECT=covers"
    query_url = query.format(ra, dec, size_ra, size_dec, filter)
    logger.debug("Query URL is {}".format(query))
    
    with urllib.request.urlopen(query_url, timeout=30) as response:
       html = response.read()
    
    v=html.decode('utf-8')
    
    entrypoint = []
    [entrypoint.append(m.start()) for m in re.finditer(">SkyMapper_", v)]
    
    out_files = []
    for i in range(len(entrypoint)):
        image_number = v[entrypoint[i]+13:entrypoint[i]+30]
        
        image_url = base_url + "get_image?IMAGE={}&SIZE={},{}&POS={},{}&BAND={}&FORMAT=fits"
        image_query = image_url.format(image_number, size_ra, size_dec, ra, dec, filter)
        logger.info("Retrieving image at {}".format(image_query))
        
        out_file = out_dir / f"{image_number}.fits"
        
        # Fetching URLs
        # FROM https://docs.python.org/3/howto/urllib2.html
        with urllib.request.urlopen(image_query, timeout=30) as response:
            with open(out_file, 'wb') as of:
                shutil.copyfileobj(response, of)
        
        with fits.open(out_file) as hdu_in:
            header = hdu_in[0].header
        
        if np.absolute(header['NAXIS1'] - header['NAXIS2']) > 1.:
            if  (ra_size != 1058) or (dec_size != 1032):
                logger.error("Bad Image Size")
                continue
        
        out_files.append(out_file)
    return out_files
