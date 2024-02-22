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
from regions import PixCoord, RectanglePixelRegion, PointPixelRegion, RegionVisual, RectangleSkyRegion
 
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.utilities import get_data_file
convert = CONVERT()
 
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
 
 
# popup window for Main_V7 that shows the slit setup
# when the user drops a slit somewhere, it will show up here
# user can see the slit parameters in pixel, DMD, and world coordinates.
# when user selects a slit on the canvas, it should highlight that row.
 

test_img_twirled = fits.open(get_data_file("astrometry.general", "WCS_150.1679077_-54.7886346.fits"))
test_wcs = WCS(test_img_twirled[0].header)

test_regf = get_data_file("regions.radec", "NGC3105_RADEC=150.1674444-54.788541.reg")

class SlitTableView(tk.Frame):
   
    def __init__(self, parent, container):
   
        super().__init__(container)
        
        self.parent = parent
       
        self.slit_obj_tags= []
       
        slitDF = pd.DataFrame(columns=["object","RA","DEC","image_xc","image_yc",
                                       "image_x0", "image_y0", "image_x1",
                                       "image_y1","dmd_xc","dmd_yc","dmd_x0",
                                       "dmd_y0", "dmd_x1", "dmd_y1"])
       
        self.slitDF = slitDF
       
        
            
        
        vbox = tk.Frame(parent, background="light gray")
        vbox.place(x=4, y=4, anchor="nw", width=700, height=400)
        self.vbox = vbox
        stab = tksheet.Sheet(vbox,width=700,height=400,)
        stab.enable_bindings('row_select')
        stab.headers(newheaders = slitDF.columns.values, index = None, reset_col_positions = False,
                     show_headers_if_not_sheet = True, redraw = False)
 
        stab.grid()
        #stab.insert_row(values=list(range(0,15)),redraw=True)
        #stab.highlight_cells(row=0,column=0,bg='cyan')
        #stab.highlight_rows(rows=[0],bg='red')
        self.stab = stab
 
    def recover_window(self):
       
        for i in self.slitDF.index.values:
           
            obj_num, ra, dec, x, y, x0, y0,\
                x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0,\
                                     dmd_x1, dmd_y1 = self.slitDF.loc[i].values
           
            slitrow = [int(obj_num), ra, dec, x, y, x0, y0,
                                     x1, y1, int(dmd_x), int(dmd_y), int(dmd_x0), int(dmd_y0),
                                     int(dmd_x1), int(dmd_y1)]
            #print(slitrow)
            self.stab.insert_row(values=slitrow,redraw=True)
            self.stab.row_index(0)
       
        
#        self.master.deiconify()
 
    def get_table_values_from_robj(self, obj, viewer=None):
       
        x, y = obj.center.x, obj.center.y
        width, height = obj.width, obj.height
        #print(width, height)
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
            imhead = image.as_hdu().header
            imwcs = WCS(header=imhead,relax=False)
            if image is None:
                # No image loaded
                return
            ra, dec = image.pixtoradec(fits_x, fits_y,
                                               format='float', coords='fits')
            ra, dec = np.round(ra,6), np.round(dec,6)
       
        except Exception as e:
            #self.logger.warning("Bad coordinate conversion: %s" % (
            #    str(e)))
            try:
                ra, dec = imwcs.all_pix2world(np.array([[fits_x, fits_y]]), 1)[0]
                ra, dec = np.round(ra,6), np.round(dec,6)
            except:
                ra = np.nan
                dec = np.nan
        x = np.round(x, 2)
        y = np.round(y, 2)
        x0 = np.round(x0, 2)
        y0 = np.round(y0, 2)
        x1 = np.round(x1, 2)
        y1 = np.round(y1, 2)
       
        return ra, dec, x, y, x0, y0,\
            x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0,\
                                 dmd_x1, dmd_y1
                                 
    def update_table_row_from_obj(self, obj, viewer):
        """
        

        Parameters
        ----------
        obj : Astropy region object
        viewer : tk fitsimage viewer
            - Need the viewer with WCS to do RA/Dec transformations

        Returns
        -------
        Updated version of slit table data

        """
        ra, dec, x, y, x0, y0,\
            x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0,\
                                 dmd_x1, dmd_y1 = self.get_table_values_from_robj(g2r(obj), viewer)
        
        tag_num = obj.tag.strip("@")
        df_indx = int(tag_num)-1
        
        row_vals = np.array([tag_num, ra, dec, x, y, x0, y0,
            x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0,dmd_x1, dmd_y1]).astype('float64')#
        
        self.slitDF.loc[df_indx] = row_vals
        
        row_num = list(self.stab.get_column_data(0)).index( int(tag_num) )
        self.stab.set_row_data(r=row_num, values=tuple(row_vals), redraw=True)
        
                                 
        
       
 
    def add_slit_obj(self, obj, tag, viewer):
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
       
        print('adding slit obj')
        obj_num = int(tag.strip("@"))#len(self.slitDF.index.values)+1
        #print(obj_num)
       
        ra, dec, x, y, x0, y0,\
            x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0, dmd_x1, dmd_y1 = self.get_table_values_from_robj(obj, viewer)
       
        
        new_slitrow = [int(obj_num), ra, dec, x, y, x0, y0,
                                 x1, y1, int(dmd_x), int(dmd_y), int(dmd_x0), int(dmd_y0),
                                 int(dmd_x1), int(dmd_y1)]
        if (dmd_x0<0 or dmd_x0>1090):
            print("slit obj not added, DMD coords are {},{}".format(dmd_x0, dmd_y0))
            return
       
        self.slitDF.loc[obj_num-1] = new_slitrow #pd.Series(np.array(new_slitrow))
        #print(self.slitDF)
       
        self.stab.insert_row(values=new_slitrow,redraw=True)
        self.stab.row_index(0)
       
        self.slit_obj_tags.append(tag)
       
        
 
    def update_table_from_obj(self, obj, viewer):
        
       
        """
        Parameters
        ----------
        objects : GINGA canvas object
            Used after the MainPage method 'apply_to_all' is used on an
            existing table of slit objects.
            Takes in the updated Ginga object and changes the
            DataFrame and tksheet table values
 
        """
       
        
        tag = obj.tag
        if tag not in self.slit_obj_tags:
            return
       
        tag_val = int(tag.strip("@"))
        df_idx = tag_val-1
       
        
        obj = g2r(obj)
       
        
        ra, dec, x, y, x0, y0,\
            x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0,\
                                 dmd_x1, dmd_y1 = self.get_table_values_from_robj(obj, viewer)
       
        new_slitrow = [int(df_idx), ra, dec, x, y, x0, y0,
                                 x1, y1, int(dmd_x), int(dmd_y), int(dmd_x0), int(dmd_y0),
                                 int(dmd_x1), int(dmd_y1)]
       
        if (dmd_x0<0 or dmd_x1>1090):
            return
       
        new_slitrow[0] = int(tag_val) # so row element needs to be tag val
        self.slitDF.loc[df_idx] = new_slitrow
        sheet_ind = self.stab.get_column_data(0).index(str(df_idx+1))
        self.stab.set_row_data(sheet_ind, values=tuple(new_slitrow), redraw=True)
       
        
        
            
            
    
    def load_table_from_regfile_RADEC(self, regs_RADEC=test_regf, img_wcs=None):
       
        #regs_RADEC = Regions.read(regfile_RADEC)
       
        
        
        obj_tag_fmt = '@{}'
       
        regs_CCD = []
       
        obj_num = self.stab.total_rows()
       #print(len(self.slit_obj_tags))
       
        for reg_rect in regs_RADEC:
           
            
            
            obj_tag = obj_tag_fmt.format(obj_num)
            obj_tag = self.slit_obj_tags[obj_num]
            #self.slit_obj_tags.append(obj_tag) # tags from this don't do anything yet
           
            ra = reg_rect.center.ra.degree
            dec = reg_rect.center.dec.degree
           
            if img_wcs is not None:
                pix_rect = reg_rect.to_pixel(img_wcs)
                regs_CCD.append(pix_rect)
                dmd_rect = pix_rect.to_sky(convert.ccd2dmd_wcs)
               
                pix_w, pix_h = pix_rect.width, pix_rect.height
                dmd_w, dmd_h = dmd_rect.width.value, dmd_rect.height.value
                # dmd rectangle region width and height are returned in arcsec
               
                
                
                pix_xc, pix_yc = pix_rect.center.x, pix_rect.center.y
                pix_x0, pix_y0 = pix_xc - pix_w/2, pix_yc - pix_h/2
                pix_x1, pix_y1 = pix_xc + pix_w/2, pix_yc + pix_h/2
               
                dmd_xc, dmd_yc = dmd_rect.center.ra.degree*3600, dmd_rect.center.dec.degree*3600 + convert.yoffset
                # dmd center points of region returned in deg. Must also apply y offset
                dmd_x0, dmd_y0 = dmd_xc - dmd_w/2, dmd_yc - dmd_h/2
                dmd_x1, dmd_y1 = dmd_xc + dmd_w/2, dmd_yc + dmd_h/2
           
            else:
               
                pix_xc = 0
                pix_yc = 0
                pix_x0 = 0
                pix_y0 = 0
                pix_x1 = 0
                pix_y1 = 0
                dmd_xc = 0
                dmd_yc = 0
                dmd_x0 = 0
                dmd_y0 = 0
                dmd_x1 = 0
                dmd_y1 = 0
            
            
            
            df_idx = int(obj_tag.strip("@"))   
            new_slitrow = [df_idx, np.round(ra,6), np.round(dec,6),
                           np.round(pix_xc,2), np.round(pix_yc,2),
                           np.round(pix_x0,2), np.round(pix_y0,2),
                           np.round(pix_x1,2), np.round(pix_y1,2),
                           int(dmd_xc), int(dmd_yc), int(dmd_x0),
                           int(dmd_y0), int(dmd_x1), int(dmd_y1)]
           
            
            self.stab.insert_row(values=new_slitrow,redraw=True)
            self.stab.row_index(0)
           
            self.slitDF.loc[df_idx] = new_slitrow
            obj_num += 1
           
        print('added regions to table')
        
 
    def load_table_from_regfile_CCD(self, regs_CCD, img_wcs=None):
       
 
        #regs_CCD = Regions.read(regfile_CCD)
        obj_num = self.stab.total_rows()
        filtered_regions = []
        for pix_rect in regs_CCD:
           
            
            obj_num += 1
           
            
            pix_xc = pix_rect.center.x
            pix_yc = pix_rect.center.y
           
            try:
                # if image has a wcs, get ra and dec for table
                sky_rect = pix_rect.to_sky(img_wcs) # convert to real sky coords
                ra = sky_rect.center.ra.degree
                dec = sky_rect.center.ra.degree
               
            except:
                ra, dec = np.nan, np.nan
            
            dmd_rect = pix_rect.to_sky(convert.ccd2dmd_wcs) # convert to fake dmd "sky" coords
 
            pix_w, pix_h = pix_rect.width, pix_rect.height
            dmd_w, dmd_h = dmd_rect.width.value, dmd_rect.height.value
            # dmd rectangle region width and height are returned in arcsec
           
            
            pix_xc, pix_yc = pix_rect.center.x, pix_rect.center.y
            pix_x0, pix_y0 = pix_xc - pix_w/2, pix_yc - pix_h/2
            pix_x1, pix_y1 = pix_xc + pix_w/2, pix_yc + pix_h/2
           
            dmd_xc, dmd_yc = dmd_rect.center.ra.degree*3600, dmd_rect.center.dec.degree*3600 + convert.yoffset
            # dmd center points of region returned in deg. Must also apply y offset
            dmd_x0, dmd_y0 = dmd_xc - dmd_w/2, dmd_yc - dmd_h/2
            dmd_x1, dmd_y1 = dmd_xc + dmd_w/2, dmd_yc + dmd_h/2
           
            new_slitrow = [obj_num, np.round(ra,6), np.round(dec,6),
                           np.round(pix_xc,2), np.round(pix_yc,2),
                           np.round(pix_x0,2), np.round(pix_y0,2),
                           np.round(pix_x1,2), np.round(pix_y1,2),
                           int(dmd_xc), int(dmd_yc), int(dmd_x0),
                           int(dmd_y0), int(dmd_x1), int(dmd_y1)]
           
            
            self.stab.insert_row(values=new_slitrow,redraw=True)
            self.stab.row_index(0)
           
        print('added regions to table')
        return
        
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
