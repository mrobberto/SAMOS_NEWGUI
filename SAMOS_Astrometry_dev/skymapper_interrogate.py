#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 22:05:04 2023

@author: robberto
"""
import urllib.request

def skymapper_interrogate(POSx=189.99763, POSy=-11.62305, filter='r'):
    POS = str(POSx)+","+str(POSy)   #"189.99763,-11.62305"
    Sizex = 0.18 / 3600 *1058
    Sizey = 0.18 / 3600 *1032
    SIZE = str(Sizex) + "," + str(Sizey)  #"0.05,0.1"
    FILTERS  = filter  #"g"#"g,r,i"
    string0= 'https://api.skymapper.nci.org.au/public/siap/dr2/'
    string = string0 + "query?"
    string += 'POS=' + POS + '&'
    string += 'SIZE=' + SIZE + '&'
    string += 'BAND=' + FILTERS + '&'
    string += 'FORMAT=image/fits&INTERSECT=covers&MJD_END=56970'#'&RESPONSEFORMAT=CSV'
    
    with urllib.request.urlopen(string,timeout=30) as response:
       html = response.read()
    print(html)
    
    import pandas as pd
    #v=pd.read_csv(html)
    v=html.decode('UTF-8')
    
    #entrypoint  = v.find("\nSkyMapper")   #use this if &RESPONSEFORMAT=CSV' works
    #image_number = v[entrypoint+13:entrypoint+30]
    entrypoint  = v.find(">SkyMapper_")
    image_number = v[entrypoint+13:entrypoint+30]
    print(image_number)
    
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
    import shutil
    import tempfile#import urllib.request
    
    with urllib.request.urlopen(string,timeout=30) as response:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(response, tmp_file)
    
    with open(tmp_file.name) as html:
        pass
    
    return(tmp_file)
#    from astropy.io import fits
#    hdu = fits.open(tmp_file.name)[0]
#    image = hdu.data
#    header = hdu.header
#    return(hdu)