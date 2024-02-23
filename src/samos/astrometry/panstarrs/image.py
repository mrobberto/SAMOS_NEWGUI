#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 21:20:32 2023

@author: robberto

FROM https://ps1images.stsci.edu/ps1image.html

Get image from the PS1 image server
Query the PS1 image server to get a list of images and retrieve some images. This sample 
script demonstrates the use of the PS1 image services. See the PS1 Image Cutout Service 
documentation for details of the services being used.
"""
from astropy.table import Table
from io import BytesIO
import logging
import matplotlib.pyplot as plt
import numpy
from PIL import Image
import requests


"""
Helper functions to query the list of images and to extract images¶
"""

class PanStarrsImage:

    def __init__(self):
        logger = logging.getLogger('samos')
        logger.debug("Initialized PanStarrsImage")
        
    def get_images(self, ra, dec, filters="grizy"):
        """
        Query ps1filenames.py service to get a list of images
        
        Parameters
        ----------
        ra : float
            Location RA
        dec : float
            Location DEC
        filters : str, default "grizy"
            Filters to look for
        
        Returns
        -------
        table : astropy.table.Table
            Table containing search results
        """
        service = "https://ps1images.stsci.edu/cgi-bin/ps1filenames.py"
        url = f"{service}?ra={ra}&dec={dec}&filters={filters}"
        table = Table.read(url, format='ascii')
        return table
    
    def get_url(self, ra, dec, size=240, output_size=None, filters="grizy", format="jpg", color=False):
        
        """
        Get URL for images in an image table returned from `self.get_images()`

        Parameters
        ----------
        ra : float
            Location RA
        dec : float
            Location DEC
        size : int
            Extracted image size in pixels (at 0.25 arcseconds/pixel)
        output_size : int, default None
            Output image size in pixels. None produces an output the same size as size.
            output_size has no effect on FITS images.
        filters : str, default "grizy"
            Filters to look for
        format : str, default "jpg"
            Returned image format
        color : bool, default False
            If True, returns a colour image (only for jpg or png format). Default is to 
            return single-colour grayscale images.
        
        Returns
        -------
        url_results : str or list
            String containing image retrieval URL or list of strings containing image retrieval URLs
        """
        if color and format == "fits":
            raise ValueError("color images are available only for jpg or png formats")
        if format not in ("jpg", "png", "fits"):
            raise ValueError("format must be one of jpg, png, fits")

        table = self.get_images(ra, dec, filters=filters)
        url = (f"https://ps1images.stsci.edu/cgi-bin/fitscut.cgi?ra={ra}&dec={dec}&size={size}&format={format}")
        if output_size is not None:
            url += f"&output_size={output_size}"

        # sort filters from red to blue
        flist = ["yzirg".find(x) for x in table['filter']]
        table = table[numpy.argsort(flist)]
        if color:
            if len(table) > 3:
                # pick 3 filters
                table = table[[0,len(table)//2, len(table)-1]]
            for i, param in enumerate(["red", "green", "blue"]):
                url += f"&{param}={table['filename'][i]}"
            url_result = url
        else:
            url += "&red="
            url_result = [url+filename for filename in table['filename']]
        return url_result
    
    
    def get_color_im(self, ra, dec, size=240, output_size=None, filters="grizy", format="jpg"):
        
        """
        Get color image at a sky position

        Parameters
        ----------
        ra : float
            Location RA
        dec : float
            Location DEC
        size : int
            Extracted image size in pixels (at 0.25 arcseconds/pixel)
        output_size : int, default None
            Output image size in pixels. None produces an output the same size as size.
            output_size has no effect on FITS images.
        filters : str, default "grizy"
            Filters to look for
        format : str, default "jpg"
            Returned image format
        
        Returns
        -------
        im : PIL.Image
            Retrieved image
        """        
        if format not in ("jpg", "png"):
            raise ValueError("format must be jpg or png")
        url = self.get_url(ra, dec, size=size, filters=filters, output_size=output_size,
                           format=format, color=True)
        r = requests.get(url)
        im = Image.open(BytesIO(r.content))
        return im
    
    
    def get_gray_im(self, ra, dec, size=240, output_size=None, filter="g", format="jpg"):
        
        """
        Get grayscale image at a sky position
        
        Parameters
        ----------
        ra : float
            Location RA
        dec : float
            Location DEC
        size : int
            Extracted image size in pixels (at 0.25 arcseconds/pixel)
        output_size : int, default None
            Output image size in pixels. None produces an output the same size as size.
            output_size has no effect on FITS images.
        filter : str, default "g"
            Filter to look for.
        format : str, default "jpg"
            Returned image format
        
        Returns
        -------
        im : PIL.Image
            Retrieved image
        """
        
        if format not in ("jpg", "png"):
            raise ValueError("format must be jpg or png")
        if filter not in ['g', 'r', 'i', 'z', 'y']:
            raise ValueError("filter must be one of grizy")
        url = self.get_url(ra, dec, size=size, filters=filter, output_size=output_size,
                           format=format)
        r = requests.get(url[0])
        im = Image.open(BytesIO(r.content))
        return im
    


 
 
