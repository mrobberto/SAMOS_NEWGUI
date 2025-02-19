#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 20 12:59:00 2023

@author: samos_dev
"""
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy import units as u
from astropy.wcs import WCS
import numpy as np
import os
import pandas as pd
from pathlib import Path
from PIL import Image, ImageTk, ImageOps
import shutil
import sys
import time

import tkinter as tk
from tkinter.filedialog import askopenfilename
import ttkbootstrap as ttk
from tksheet import Sheet
 
from ginga.AstroImage import AstroImage
from ginga.util import ap_region
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.canvas import CompoundMixin as CM
from regions import Regions, PixCoord, RectanglePixelRegion, PointPixelRegion, RegionVisual, RectangleSkyRegion
 
from samos.utilities import get_data_file
from samos.utilities.constants import *
from samos.utilities.utils import ccd_to_dmd


class SlitTableView(tk.Frame):
    def __init__(self, parent, container, par, logger):
        super().__init__(container)
        self.PAR = par
        self.parent = parent
        self.logger = logger
        self.slit_obj_tags= []
        self.df_cols = ["object", "RA", "DEC", "image_xc", "image_yc", "image_x0", "image_y0", "image_x1",
                        "image_y1", "dmd_xc", "dmd_yc", "dmd_x0", "dmd_y0", "dmd_x1", "dmd_y1"]
        self.slitDF = pd.DataFrame(columns=self.df_cols)

        self.main_frame = ttk.Frame(self, width=700, height=400)
        self.main_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.stab = Sheet(self.main_frame, width=700, height=400)
        self.stab.enable_bindings('row_select')
        self.stab.headers(newheaders=self.slitDF.columns.values, index=None, reset_col_positions=False, show_headers_if_not_sheet=True, 
                          redraw=False)
        self.stab.grid(row=0, column=0, sticky=TK_STICKY_ALL)


    def recover_window(self):
        for i in self.slitDF.index.values:
            slitrow = list(self.slitDF.loc[i].values)
            for item in [9, 10, 11, 12, 13, 14]:
                slitrow[item] = int(slitrow[item])
            self.stab.insert_row(values=slitrow, redraw=True)
            self.stab.row_index(0)


    def get_table_values_from_robj(self, obj, viewer=None):
        x, y = obj.center.x, obj.center.y
        width, height = obj.width, obj.height
        x0, x1 = x - width / 2, x + width / 2
        y0, y1 = y - height / 2, y + height / 2
        fits_x, fits_y = x + 1, y + 1
        fits_x0, fits_y0 = x0 + 1, y0 + 1
        fits_x1, fits_y1 = x1 + 1, y1 + 1

        dmd_x, dmd_y = ccd_to_dmd(fits_x, fits_y, self.PAR.dmd_wcs)
        dmd_x, dmd_y = int(np.floor(dmd_x)), int(np.floor(dmd_y))
 
        dmd_x0, dmd_y0 = ccd_to_dmd(fits_x0, fits_y0, self.dmd_PAR.wcs)
        dmd_x0, dmd_y0 = int(np.floor(dmd_x0)), int(np.floor(dmd_y0))
        
        dmd_x1, dmd_y1 = ccd_to_dmd(fits_x1, fits_y1, self.PAR.dmd_wcs)
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
            ra, dec = image.pixtoradec(fits_x, fits_y, format='float', coords='fits')
            ra, dec = np.round(ra, 6), np.round(dec, 6)
        except Exception as e:
            try:
                ra, dec = imwcs.all_pix2world(np.array([[fits_x, fits_y]]), 1)[0]
                ra, dec = np.round(ra,6), np.round(dec,6)
            except Exception as e:
                ra = np.nan
                dec = np.nan

        x, y = np.round(x, 2), np.round(y, 2)
        x0, y0 = np.round(x0, 2), np.round(y0, 2)
        x1, y1 = np.round(x1, 2), np.round(y1, 2)
       
        return ra, dec, x, y, x0, y0, x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0, dmd_x1, dmd_y1

                                 
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
        row_vals = [float(x) for x in self.get_table_values_from_robj(g2r(obj), viewer)]
        row_vals.insert(0, obj.tag)
        self.slitDF.loc[self.slitDF['object'] == obj.tag] = row_vals
        row_num = list(self.stab.get_column_data(0)).index(obj.tag)
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
        self.logger.info(f"Adding slit object {obj} with tag {tag}")
        ra, dec, x, y, x0, y0, x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0, dmd_x1, dmd_y1 = self.get_table_values_from_robj(obj, viewer)
       
        
        new_slitrow = [tag, ra, dec, x, y, x0, y0, x1, y1, int(dmd_x), int(dmd_y), int(dmd_x0), int(dmd_y0), int(dmd_x1), int(dmd_y1)]
        if (dmd_x0 < 0) or (dmd_x0 > 1090):
            self.logger.error(f"Slit object not added, DMD co-ordinates are ({dmd_x0}, {dmd_y0})")
            return

        new_row = pd.Series(new_slitrow, index=self.df_cols)
        self.slitDF = pd.concat([self.slitDF, new_row.to_frame().T], ignore_index=True)
       
        self.stab.insert_row(values=new_slitrow, redraw=True)
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
            self.logger.warning(f"Trying to update nonexistent object with tag {tag}")
            return
       
        ra, dec, x, y, x0, y0, x1, y1, dmd_x, dmd_y, dmd_x0, dmd_y0, dmd_x1, dmd_y1 = self.get_table_values_from_robj(g2r(obj), viewer)
        new_slitrow = [tag, ra, dec, x, y, x0, y0, x1, y1, int(dmd_x), int(dmd_y), int(dmd_x0), int(dmd_y0), int(dmd_x1), int(dmd_y1)]
        if (dmd_x0 < 0) or (dmd_x1 > 1090):
            self.logger.warning(f"Not adding object, DMD co-ordinates are ({dmd_x0}, {dmd_y0})")
            return
       
        self.slitDF.loc[self.slitDF['object'] == obj.tag] = new_slitrow
        row_num = self.stab.get_column_data(0).index(tag)
        self.stab.set_row_data(r=row_num, values=tuple(new_slitrow), redraw=True)


    def load_table_from_regfile_RADEC(self, regs_RADEC=None, img_wcs=None):
        obj_tag_fmt = '@{}'
        regs_CCD = []
        obj_num = self.stab.total_rows()
       
        for region in regs_RADEC:
            obj_tag = obj_tag_fmt.format(obj_num)
            self.slit_obj_tags.append(obj_tag)
            ra = region.center.ra.degree
            dec = region.center.dec.degree
           
            if img_wcs is not None:
                pix_rect = region.to_pixel(img_wcs)
                regs_CCD.append(pix_rect)
                dmd_rect = pix_rect.to_sky(self.PAR.dmd_wcs)
               
                pix_w, pix_h = pix_rect.width, pix_rect.height
                dmd_w, dmd_h = dmd_rect.width.value, dmd_rect.height.value
                
                pix_xc, pix_yc = pix_rect.center.x, pix_rect.center.y
                pix_x0, pix_y0 = pix_xc - pix_w/2, pix_yc - pix_h/2
                pix_x1, pix_y1 = pix_xc + pix_w/2, pix_yc + pix_h/2
               
                dmd_xc, dmd_yc = dmd_rect.center.ra.degree*3600, dmd_rect.center.dec.degree*3600 + CCD_DMD_Y_OFFSET
                dmd_x0, dmd_y0 = dmd_xc - dmd_w/2, dmd_yc - dmd_h/2
                dmd_x1, dmd_y1 = dmd_xc + dmd_w/2, dmd_yc + dmd_h/2
            else:
                pix_xc, pix_yc = 0, 0
                pix_x0, pix_y0 = 0, 0
                pix_x1, pix_y1 = 0, 0
                dmd_xc, dmd_yc = 0, 0
                dmd_x0, dmd_y0 = 0, 0
                dmd_x1, dmd_y1 = 0, 0

            new_slitrow = [obj_tag, np.round(ra, 6), np.round(dec, 6), np.round(pix_xc, 2), np.round(pix_yc, 2),
                           np.round(pix_x0, 2), np.round(pix_y0, 2), np.round(pix_x1, 2), np.round(pix_y1, 2),
                           int(dmd_xc), int(dmd_yc), int(dmd_x0), int(dmd_y0), int(dmd_x1), int(dmd_y1)]
            
            #[mr]: apparently the insert_row method does not accept "values" as a parameter
            self.stab.insert_row(values=new_slitrow, redraw=True)
            self.stab.row_index(0)
            

            series_row = pd.Series(new_slitrow, index=self.df_cols)
            self.slitDF = pd.concat([self.slitDF, new_row.to_frame().T], ignore_index=True)
            obj_num += 1

        self.logger.info("Added regions to table")


    def load_table_from_regfile_CCD(self, regs_CCD, img_wcs=None):
        obj_tag_fmt = '@{}'
        obj_num = self.stab.total_rows()
        filtered_regions = []

        for pix_rect in regs_CCD:
            pix_xc = pix_rect.center.x
            pix_yc = pix_rect.center.y
           
            try:
                # if image has a wcs, get ra and dec for table
                sky_rect = pix_rect.to_sky(img_wcs) # convert to real sky coords
                ra = sky_rect.center.ra.degree
                dec = sky_rect.center.ra.degree
            except Exception as e:
                ra, dec = np.nan, np.nan
            
            dmd_rect = pix_rect.to_sky(self.PAR.dmd_wcs) # convert to fake dmd "sky" coords
 
            pix_w, pix_h = pix_rect.width, pix_rect.height
            dmd_w, dmd_h = dmd_rect.width.value, dmd_rect.height.value
            pix_xc, pix_yc = pix_rect.center.x, pix_rect.center.y
            pix_x0, pix_y0 = pix_xc - pix_w/2, pix_yc - pix_h/2
            pix_x1, pix_y1 = pix_xc + pix_w/2, pix_yc + pix_h/2
           
            dmd_xc, dmd_yc = dmd_rect.center.ra.degree*3600, dmd_rect.center.dec.degree*3600 + CCD_DMD_Y_OFFSET
            dmd_x0, dmd_y0 = dmd_xc - dmd_w/2, dmd_yc - dmd_h/2
            dmd_x1, dmd_y1 = dmd_xc + dmd_w/2, dmd_yc + dmd_h/2
           
            new_slitrow = [obj_tag_fmt.format(obj_num), np.round(ra, 6), np.round(dec, 6), np.round(pix_xc, 2), np.round(pix_yc, 2),
                           np.round(pix_x0, 2), np.round(pix_y0, 2), np.round(pix_x1, 2), np.round(pix_y1, 2),
                           int(dmd_xc), int(dmd_yc), int(dmd_x0), int(dmd_y0), int(dmd_x1), int(dmd_y1)]
            self.stab.insert_row(values=new_slitrow, redraw=True)
            self.stab.row_index(0)
            series_row = pd.Series(new_slitrow, index=self.df_cols)
            self.slitDF = pd.concat([self.slitDF, new_row.to_frame().T], ignore_index=True)
            obj_num += 1
           
        self.logger.info("Added regions to table")


    def save_slit_table(self, filename):
        self.slitDF.to_csv(filename)
