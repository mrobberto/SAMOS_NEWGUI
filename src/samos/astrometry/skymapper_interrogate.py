#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 22:05:04 2023

@author: robberto
"""
import numpy as np
import pandas as pd
import urllib.request
import shutil
import tempfile#import urllib.request
from astropy.io import fits


def skymapper_interrogate(POSx=189.99763, POSy=-11.62305, RA_Size=1058, DEC_Size=1032, filter='r'):
    POS = str(POSx)+","+str(POSy)   #"189.99763,-11.62305"
   # Sizex = np.round(0.18 / 3600 * RA_Size, 6)
   # Sizey = np.round(0.18 / 3600 * DEC_Size, 6)
    Sizex = 0.18 / 3600 * RA_Size
    Sizey = 0.18 / 3600 * DEC_Size
    SIZE = str(Sizex) + "," + str(Sizey)  #"0.05,0.1"
    FILTERS  = filter  #"g"#"g,r,i"
    string0= 'https://api.skymapper.nci.org.au/public/siap/dr2/'
    string = string0 + "query?"
    string += 'POS=' + POS + '&'
    string += 'SIZE=' + '0.05' + '&'   # first call to find the plate we use a small 5'x5' field
    string += 'BAND=' + FILTERS + '&'
    string += 'FORMAT=image/fits&INTERSECT=covers'#'&MJD_END=56970'#'&RESPONSEFORMAT=CSV'
    
    with urllib.request.urlopen(string,timeout=30) as response:
       html = response.read()
    print(html)
    
    #v=pd.read_csv(html)
    v=html.decode('UTF-8')
    
    #entrypoint  = v.find("\nSkyMapper")   #use this if &RESPONSEFORMAT=CSV' works
    #image_number = v[entrypoint+13:entrypoint+30]
    import re
    entrypoint = []
    [entrypoint.append(m.start()) for m in re.finditer(">SkyMapper_", v)] 
    
    for i in range(len(entrypoint)):
    #    entrypoint_old  = v.find(">SkyMapper_")
        image_number = v[entrypoint[i]+13:entrypoint[i]+30]
        print(entrypoint,image_number)
        
        string = string0 + "get_image?"
        string += 'IMAGE='+image_number + '&'
        string += 'SIZE=' + SIZE + '&'
        string += 'POS=' + POS + '&'
        string += 'BAND=' + FILTERS + '&'
        string += 'FORMAT=fits'
        
        print(string)
        #https://api.skymapper.nci.org.au/public/siap/dr2/get_image?IMAGE=20140425124821-10&SIZE=0.05,0.1&POS=189.99763,-11.62305&BAND=g&FORMAT=fits
        #https://api.skymapper.nci.org.au/public/siap/dr2/get_image?IMAGE=20140425124821-10&SIZE=0.0833&POS=189.99763,-11.62305&FORMAT=png
        #string='https://api.skymapper.nci.org.au/public/siap/dr2/query?POS=150.17110,-54.79004&SIZE=0.052899999999999996,0.05159999999999999&BAND=i&FORMAT=image/fits&INTERSECT=covers&MJD_END=56970'
        """
        #Fetching URLs
        #FROM https://docs.python.org/3/howto/urllib2.html
        """
        
        with urllib.request.urlopen(string,timeout=30) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
        
        with open(tmp_file.name) as html:
            pass
        
        hdu_in = fits.open(tmp_file.name)
        header = hdu_in[0].header
        #data = hdu_in[0].data
        
        #import astropy.wcs as wcs
        #mywcs = wcs.WCS(header)
        #ra, dec = mywcs.all_pix2world([[data.shape[0]/2,data.shape[1]/2]], 0)[0]
        #header['RA'] = ra
        #header['DEC'] = dec
        #fits.writeto(tmp_file, data, header=header, overwrite=True)
        if ((RA_Size == 1058) and (DEC_Size == 1032)):
            return(tmp_file)
        elif np.absolute(header['NAXIS1'] - header['NAXIS2']) <= 1:
            return(tmp_file)
        
#    from astropy.io import fits
#    hdu = fits.open(tmp_file.name)[0]
#    image = hdu.data
#    header = hdu.header
#    return(hdu)