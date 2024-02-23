#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 22:05:04 2023

@author: robberto
"""
from astropy import units as u
from astropy.io import fits
import numpy as np
import pandas as pd
import re
import shutil
import tempfile
import urllib.request

from samos.utilities import get_temporary_dir


def skymapper_interrogate(ra=189.99763, dec=-11.62305, ra_size=1058, dec_size=1032, filter='r'):
    """
    ***** This documentation needs to be checked for accuracy
    Query the skymapper.nci.org.au website for information on the supplied location.
    
    Parameters
    ----------
    ra : float, default 189.99763
        RA in decimal degrees of centre of location
    dec : float, default -11.62305
        DEC in decimal degrees of centre of location 
    ra_size : int
        Size of field in the RA direction (arcseconds)
    dec_size : int
        Size of field in the DEC direction (arcseconds)
    filter: str, default 'r'
        Filter to retrieve
    
    Returns
    -------
    """
    pixel_scale = 0.18 * u.arcsec / u.pix
    base_url = "https://api.skymapper.nci.org.au/public/siap/dr2/"
    out_dir = get_temporary_dir()

    ra = ra * u.deg
    dec = dec * u.deg
    size_ra = (ra_size * u.pixel * pixel_scale).to(u.deg)
    size_dec = (dec_size * u.pixel * pixel_scale).to(u.deg)
    
    query_url = base_url + "query?POS={},{}&SIZE={},{}&BAND={}FORMAT=image/fits&INTERSECT=covers"
    query = query_url.format(ra.value, dec.value, size_ra.value, size_dec.value)
    
    with urllib.request.urlopen(query, timeout=30) as response:
       html = response.read()
    
    v=html.decode('utf-8')
    
    entrypoint = []
    [entrypoint.append(m.start()) for m in re.finditer(">SkyMapper_", v)] 
    
    for i in range(len(entrypoint)):
        image_number = v[entrypoint[i]+13:entrypoint[i]+30]
        
        image_url = base_url + "get_image?IMAGE={}&SIZE={},{}&POS={},{}&BAND={}&FORMAT=fits"
        image_query = image_url.format(image_number, ra.value, dec.value, size_ra.value, size_dec.value, filter)
        
        out_file = out_dir / f"{image_number}.fits"
        
        # Fetching URLs
        # FROM https://docs.python.org/3/howto/urllib2.html
        with urllib.request.urlopen(image_query, timeout=30) as response:
            shutil.copyfileobj(response, out_file)
        
        with open(out_file) as html:
            pass
        
        with fits.open(out_file) as hdu_in:
            header = hdu_in[0].header

        if ((ra_size == 1058) and (dec_size == 1032)):
            return(out_file)
        elif np.absolute(header['NAXIS1'] - header['NAXIS2']) <= 1:
            return(out_file)
