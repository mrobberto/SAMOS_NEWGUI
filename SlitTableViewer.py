#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 12:59:00 2023

@author: samos_dev
"""

import tkinter as tk
# Used for styling the GUI
#from tkinter import ttk
# import filedialog module
from tkinter import filedialog

from PIL import Image,ImageTk,ImageOps

import os,sys
import shutil
#from astropy.io import ascii
import time

import numpy as np
import pandas as pd

from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   
sys.path.append(parent_dir)


import tksheet
from tksheet import Sheet

import ginga
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.canvas import CompoundMixin as CM

#test plugin
#from ginga import plugin

from ginga.util import ap_region

from ginga.AstroImage import AstroImage
img = AstroImage()
from astropy.io import fits
from PIL import Image,ImageTk,ImageOps


import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

import regions
from regions import Regions
from regions import PixCoord, RectanglePixelRegion, PointPixelRegion, RegionVisual

from SAMOS_DMD_dev.CONVERT.CONVERT_class import CONVERT 
convert = CONVERT()

# popup window for Main_V7 that shows the slit setup
# when the user drops a slit somewhere, it will show up here
# user can see the slit parameters in pixel, DMD, and world coordinates.
# when user selects a slit on the canvas, it should highlight that row.

class SlitTableView(tk.Tk):
    
    def __init__(self,): #master):
    
        super().__init__()#master = master) 
    # changing the title of our master widget      
        self.title("Slit Table")
        #Creation of init_window
        self.geometry("700x407")
        
        slitDF = pd.DataFrame(columns=["object","RA","DEC","image_xc","image_yc",
                                       "image_x0", "image_y0", "image_x1", 
                                       "image_y1","dmd_xc","dmd_yc","dmd_x0",
                                       "dmd_y0", "dmd_x1", "dmd_y1"])
        
        self.slitDF = slitDF
        
        
            
        
        vbox = tk.Frame(self, background="light gray")
        vbox.place(x=4, y=4, anchor="nw", width=700, height=400)
        self.vbox = vbox
        stab = tksheet.Sheet(vbox,width=700,height=400,)
        stab.headers(newheaders = slitDF.columns.values, index = None, reset_col_positions = False, 
                     show_headers_if_not_sheet = True, redraw = False)

        stab.grid()
        #stab.insert_row(values=list(range(0,15)),redraw=True)
        self.stab = stab

            
    def add_slit_obj(self, obj, viewer):
        """
    

        Parameters
        ----------
        obj : canvas object
            Should be a rectangle or box.
        image : image canvas view.
            Get image for pix2radec conversion.

        Returns
        -------
        None.

        """
        
      
        obj_num = len(self.slitDF.index.values)+1
        
        x, y = obj.center.x, obj.center.y
        width, height = obj.width, obj.height
        
        halfw = width/2
        halfh = height/2
        
        x0 = x-halfw
        x1 = x+halfw
        y0 = y-halfh
        y1 = y+halfh
        
        fits_x, fits_y = x+1, y+1
        fits_x0, fits_y0 = x0+1, y0+1
        fits_x1, fits_y1 = x1+1, y1+1
        
        dmd_x, dmd_y = convert.CCD2DMD(fits_x, fits_y)
        dmd_x, dmd_y= int(np.floor(dmd_x)), int(np.floor(dmd_y))

        dmd_x0, dmd_y0 = convert.CCD2DMD(fits_x0, fits_y0)
        dmd_x0, dmd_y0 = int(np.floor(dmd_x0)), int(np.floor(dmd_y0))
        
        dmd_x1, dmd_y1 = convert.CCD2DMD(fits_x1, fits_y1)
        dmd_x1, dmd_y1 = int(np.floor(dmd_x1)), int(np.floor(dmd_y1))

        
        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra, dec = image.pixtoradec(fits_x, fits_y,
                                               format='float', coords='fits')
            ra, dec = np.round(ra,6), np.round(dec,6)
        except Exception as e:
            #self.logger.warning("Bad coordinate conversion: %s" % (
            #    str(e)))
            ra = np.nan
            dec = np.nan
        
        new_slitrow = pd.Series(np.array([obj_num, ra, dec, x, y, x0, y0,
                                 x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0,
                                 dmd_x1, dmd_y1]))
        
        self.slitDF.loc[obj_num-1] = new_slitrow
        
        self.stab.insert_row(values=list(new_slitrow.values),redraw=True)
    
     
    def save_slit_table(self,filename):
        print(self.stab)
        pass
#Root window created. 
#Here, that would be the only window, but you can later have windows within windows.
#root = SlitTableView()

#size of the window
#root.geometry("400x330")

#Then we actually create the instance.
#app = Tk.Window(root)    

#Finally, show it and begin the mainloop.
#root.mainloop()
