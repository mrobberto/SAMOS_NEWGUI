#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 19 22:05:04 2023

@author: robberto
"""
from astropy import units as u
from astropy.io import fits
import csv
import logging
import numpy as np
import pandas as pd
import re
import shutil
import sys
import tempfile
import urllib.request

from ginga.tkw.ImageViewTk import CanvasView
from ginga.util.loader import load_data
import tkinter as Tkinter
from tkinter.filedialog import askopenfilename

from samos.utilities import get_temporary_dir
from samos.utilities.constants import *


def skymapper_interrogate(ra, dec, ra_size=1058, dec_size=1032, filter='r'):
    """
    ***** This documentation needs to be checked for accuracy
    Query the skymapper.nci.org.au website for information on the supplied location. If
    there are any matching images, further query skymapper to retrieve those images, save
    them to a temporary location, and return paths to their location.
    
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
    out_files : list
        List of file paths
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


class SkyMapperLoader(object):
    def __init__(self, logger):
        self.logger = logger
        root = Tkinter.Tk()
        root.title("SkyMapper loader")
        self.root = root

        vbox = Tkinter.Frame(root, relief=Tkinter.RAISED, borderwidth=1)
        vbox.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=1)

        canvas2 = Tkinter.Canvas(vbox, bg="grey", height=512, width=512)
        canvas2.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=1)

        fi2 = CanvasView(logger)
        fi2.set_widget(canvas2)
        fi2.enable_autocuts('on')
        fi2.set_autocut_params('zscale')
        fi2.enable_autozoom('on')
        fi2.enable_auto_orient(True)
        fi2.set_bg(0.2, 0.2, 0.2)
        fi2.ui_set_active(True)
        # tk seems to not take focus with a click
        fi2.set_enter_focus(True)
        fi2.show_pan_mark(True)
        fi2.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi2

        bd = fi2.get_bindings()
        bd.enable_pan(True)
        bd.enable_zoom(True)
        bd.enable_cuts(True)
        bd.enable_flip(True)
        bd.enable_cmap(True)
        bd.enable_rotate(True)

        fi2.configure(512, 512)

        hbox = Tkinter.Frame(root)
        hbox.pack(side=Tkinter.BOTTOM, fill=Tkinter.X, expand=0)

        self.string_RA = Tkinter.StringVar()
        self.string_RA.set("189.99763")
        label_RA = Tkinter.Label(hbox, text='RA:',  bd =3)
        entry_RA = Tkinter.Entry(hbox, width=11,  bd =3, textvariable = self.string_RA)
        
        self.string_DEC = Tkinter.StringVar()
        self.string_DEC.set("-11.62305")
        label_DEC = Tkinter.Label(hbox, text='Dec:',  bd =3)
        entry_DEC = Tkinter.Entry(hbox, width=11,  bd =3, textvariable = self.string_DEC)
        
        self.string_Filter = Tkinter.StringVar()
        self.string_Filter.set("i")
        label_Filter = Tkinter.Label(hbox, text='Filter:',  bd =3)
        entry_Filter = Tkinter.Entry(hbox, width=3,  bd =3,textvariable = self.string_Filter)

        wquery = Tkinter.Button(hbox, text="Query", command=self.query)

        wsave = Tkinter.Button(hbox, text="Save File", command=self.save_file)
        wquit = Tkinter.Button(hbox, text="Quit", command=lambda: self.quit(root))
        
        for w in (label_RA, entry_RA, label_DEC, entry_DEC, label_Filter, entry_Filter, wquery, wsave, wquit):
            w.pack(side=Tkinter.LEFT)


    def get_widget(self):
        return self.root


    def query(self):
        from ginga.AstroImage import AstroImage
        from PIL import Image
        img = AstroImage()
        from astropy.io import fits
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, filt)       
        with fits.open(filepath.name) as hdu_in:
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(1032,1056))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec
            img.load_hdu(self.hdu_res)       
            self.fitsimage.set_image(img)


    def save_file(self):
        out_file = get_temporary_dir() / "newimage_ff.fits"
        fits.writeto(out_file, self.hdu_res.data, header=self.hdu_res.header, overwrite=True) 


    def open_file(self):
        filename = askopenfilename(filetypes=[("allfiles", "*"), ("fitsfiles", "*.fits")])
        self.load_file(filename)


    def quit(self, root):
        root.quit()
        root.destroy()
        return True


def main(options, args):
    logger = logging.getLogger("samos")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(STD_FORMAT)
    stderrHdlr = logging.StreamHandler()
    stderrHdlr.setFormatter(fmt)
    logger.addHandler(stderrHdlr)

    fv = SkyMapperLoader(logger)
    top = fv.get_widget()

    if len(args) > 0:
        fv.load_file(args[0])

    top.mainloop()


if __name__ == '__main__':
    main(None, sys.argv[1:])
