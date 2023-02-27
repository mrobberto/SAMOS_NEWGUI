#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 12:49:02 2022

@author: danakoeppe
"""
import sys
sys.path.append('/opt/anaconda3/envs/samos_env/lib/python3.10/site-packages')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import re
import astropy
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.wcs.utils import fit_wcs_from_points
from astropy.nddata import CCDData
from astropy.nddata import StdDevUncertainty
from astropy import wcs as astropy_wcs
from astropy import constants as const
from astropy.stats import mad_std, sigma_clipped_stats
from astropy.nddata import CCDData
from astropy.visualization import hist
from astropy.visualization import quantity_support,astropy_mpl_style, simple_norm

from photutils.detection import IRAFStarFinder


plt.rcParams.update({'font.size': 20})
plt.rcParams.update({'xtick.labelsize': 12})
plt.rcParams.update({'ytick.labelsize': 12})
plt.rcParams.update({'axes.titlesize': 15})



#from ginga.tkw.ImageViewTk import ImageViewCanvas
from ginga.misc import log
from ginga.util.loader import load_data

from ginga.AstroImage import AstroImage
img = AstroImage()
from astropy.io import fits

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
#from matplotlib.backend_bases import cursors
#import matplotlib.backends.backend_tkagg as tkagg


from pandastable import Table
import pandas as pd
import os

#sys.path.insert(0,"/Users/danakoeppe/allSAMOS/SI_camera_tests/PIX_to_DMD_mapping")
#print(sys.path)
import Coord_Transform_Helpers as CTH


from photutils.aperture import CircularAperture, EllipticalAperture


class MainWindow(tk.Toplevel):
    
    

    def __init__(self, parent):
        super().__init__(parent)

        #self.logger = logger
        self.drawcolors = ['white', 'black', 'red', 'yellow', 'blue', 'green']

        self.title("SAMOS")
       
        #self.geometry("1000x800")   
        
        #self.set_border_width(2)
        #self.connect("delete_event", lambda w, e: self.quit(w))
       
class DMD_CCD_Mapping_Main(tk.Tk):
    
    
    def __init__(self):
        super().__init__()
    
# =============================================================================
#         
#  #    FITS Files Label Frame
#         
# =============================================================================
        self.fits_hdu = None
        self.sources_table = None
        self.dmd_table = None
        self.DMD_PIX_df = None
        self.afftest = None
        self.coord_text = None
 
        
        vbox_l = tk.Frame(self,relief=tk.RAISED)
        vbox_l.pack(side=tk.LEFT)
        vbox_l.place(x=5,y=0,anchor="nw",width=220,height=550)
        self.vb_l = vbox_l
        
        self.frame0l = tk.Frame(self.vb_l,background="#9D76A4",relief=tk.RAISED)#, width=400, height=800)
        self.frame0l.place(x=4, y=0, anchor="nw", width=220, height=250)
        
        
        self.wdir = "./"
        filelist = os.listdir(self.wdir)
        
        self.file_browse_button = tk.Button(self.frame0l,text="Open FITS File",bg="#9D76A4",command=self.browse_fits_files)
        #browse_files.pack(side=tk.TOP)
        self.file_browse_button.pack()
        
        
        self.DMD_browse_button = tk.Button(self.frame0l,text="Open DMD Pattern File",bg="#9D76A4",command=self.browse_dmd_pattern_files)
        #browse_files.pack(side=tk.TOP)
        self.DMD_browse_button.pack()
        
 # =============================================================================
 #         
 #  #    Buttions for Source Extraction
 #      -Enter in number of sources to find in image.
 #      -Enter in approx FWHM for sources.
 #      -Initialize Coordinate transformation.
 #      -Enter SIP value and run coordinate WCS fit.
 #         
 # =============================================================================       
    
        labell1 = tk.LabelFrame(self.vb_l,bg="#9D76A4",text="Source Extraction",
                                font=("Roman bold",20),labelanchor="n")
        labell1.place(x=4, y=255, anchor="nw", width=220, height=320)
        
        self.frame1l = tk.Canvas(labell1,background="#9D76A4")#, width=400, height=800)
        self.frame1l.place(x=4, y=0, anchor="nw",width=200,height=260)
        #self.frame1l.pack(anchor="nw")
        
        
        source_number_input_label = tk.Label(self.frame1l, text='Enter # of sources:',bg="#9D76A4")
        source_number_input_label.config(font=('Roman', 12))
        source_number_input_label.pack(padx=10,pady=5)
        #self.frame1l.create_window(102,8,window=source_number_input_label)
        self.source_find_entry = tk.Entry(self.frame1l, state="disabled",   width=8,font=("Roman",12))
        self.source_find_entry.pack(padx=4,pady=0)
        #self.frame1l.create_window(102,33, window=self.source_find_entry)
        
        fwhm_input_label = tk.Label(self.frame1l, text='Enter FWHM:',bg="#9D76A4")
        fwhm_input_label.config(font=('Roman', 12))
        #self.frame1l.create_window(102,58,window=fwhm_input_label)
        fwhm_input_label.pack(padx=10,pady=0)
        self.source_fwhm_entry = tk.Entry(self.frame1l,state="disabled", width=8,font=("Roman",12))
       # self.frame1l.create_window(102,83, window=self.source_fwhm_entry)
        self.source_fwhm_entry.pack(anchor="n",padx=4,pady=0,)
        
        self.source_find_button = tk.Button(self.frame1l,text="Run IRAFStarFinder",bg="#9D76A4",state="disabled", command=self.irafstarfind)
        #self.source_find_button.place(x=4)
        #self.frame1l.create_window(102,120,window=self.source_find_button)
        self.source_find_button.pack(anchor="n",padx=4,pady=5)
        
        self.run_coord_transf_button = tk.Button(self.frame1l,text="Initialize Coord Transform",bg="#9D76A4",state="disabled",
                                                 command=self.run_coord_transf)
        self.run_coord_transf_button.pack(padx=15,pady=5)
        
        sip_input_label = tk.Label(self.frame1l, text='Enter SIP Degree:',bg="#9D76A4")
        sip_input_label.config(font=('Roman', 12))
        self.fit_wcs_sip_entry = tk.Entry(self.frame1l,state="disabled",width=8,font=("Roman",12))
        #self.frame1l.create_window(98,180,window=self.fit_wcs_sip_entry)
        self.fit_wcs_sip_entry.pack(padx=4,pady=5)
        self.fit_wcs_with_sip_button = tk.Button(self.frame1l,text="Run WCS Fit With SIP",bg="#9D76A4",
                                                 command=self.run_wcs_fit_with_sip,state="disabled")
        self.fit_wcs_with_sip_button.pack(padx=4,pady=1)
        #self.frame1l.create_window(98,200,window=fit_wcs_with_sip_button)
        
# =============================================================================
#         
#  #    Center frame for FITS image and table display
#         
# =============================================================================
        
        
        #self.fits_frame_0c = tk.Frame(self,background="white", width=500, height=500)
        self.fig = plt.Figure(figsize=(8,8),tight_layout=True)
        self.gs = GridSpec(nrows=1,ncols=1)
        self.ax = self.fig.add_subplot(self.gs[0])
        
        #plt.connect('motion_notify_event', self.mouse_move)
        
        vbox_c = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox_c.pack(side=tk.TOP)
        vbox_c.place(x=230, y=0, anchor="nw")#, width=500, height=800)
        
        self.vb_c = vbox_c
        self.fits_fig_canvas0c = FigureCanvasTkAgg(self.fig, master=self.vb_c)
        self.fits_fig_canvas0c.draw()
        
        self.fits_fig_canvas0c.get_tk_widget().place(x=250,y=0,anchor="n")
        self.fits_fig_canvas0c.get_tk_widget().pack()
        
        
        self.coord_label = tk.Label(self.vb_c,text=self.coord_text)
        self.coord_label.place(x=250,y=40,anchor="s")
        self.coord_label.pack()


        self.source_tab_frame_1c = tk.Frame(self.vb_c) 
        self.source_tab_frame_1c.place(x=250,y=50,anchor="s")
        self.source_tab_frame_1c.pack()
        
        
        
        
    def open_main(self):
        window = MainWindow(self)
        window.grab_set()
        
    def mouse_move(self,event):
        
        if self.fits_hdu is None:
            return
        
        x, y = event.xdata, event.ydata
        
        self.coord_text = '({},{})'.format(x,y)
        self.coord_label["text"] = (self.coord_text)
       
        
       
    def browse_fits_files(self):
        
        self.browse_fits_files = tk.filedialog.askopenfilename(initialdir = "./",filetypes=[("FITS files","*fits")], 
                            title = "Select a FITS File",parent=self.frame0l)
        
        self.fits_hdu = fits.open(self.browse_fits_files,unit='adu')
        self.image = self.ax.imshow(self.fits_hdu[0].data, cmap='gray', origin='lower',
           interpolation='none')
        
        
        self.ax.set_title(os.path.basename(self.browse_fits_files))
        self.ax.set_xlabel("NAXIS1")
        self.ax.set_ylabel("NAXIS2")
        self.fits_fig_canvas0c.draw()
        
        self.fig.canvas.mpl_connect('motion_notify_event', self.mouse_move)
        
        self.fits_fig_canvas0c.get_tk_widget().pack()
       
        
        self.source_find_button["state"] = "active"
        self.source_fwhm_entry["state"] = "normal"
        self.source_find_entry["state"] = "normal"
        
        #print(os.path.split(self.browse_fits_files)[1][:-5]+'_with_dmd_wcs.fits')
    
    def browse_dmd_pattern_files(self):
        
        self.browse_dmd_files = tk.filedialog.askopenfilename(initialdir = "./",
                                        filetypes=[("dat files","*dat"),("csv files", "*csv")], 
                                        title = "Select a DMD Pattern File",parent=self.frame0l)
        
        
        if self.browse_dmd_files != '':
            dmd_table = pd.read_csv(self.browse_dmd_files)
            
            #this line is just to deal with the misaligned CCD that the test image comes from.  Will remove later.
            trunc_dmd_table = dmd_table.where(np.logical_and(dmd_table.x>15,dmd_table.y<1060)).dropna(how='all').reset_index()
    
    
            self.dmd_table = trunc_dmd_table
            
            print(trunc_dmd_table.shape)
            if self.sources_table is not None:
                
                print(self.sources_table.shape)
                DMD_PIX_df = pd.concat((trunc_dmd_table,self.sources_table),axis=1)
        
                self.DMD_PIX_df = DMD_PIX_df
                self.source_table = Table(self.source_tab_frame_1c,dataframe=self.DMD_PIX_df,showtoolbar=True)
                self.source_table.show()
                print(self.DMD_PIX_df)
                
            #if (self.DMD_PIX_df is not None) and (self.sources_table is not None):
                self.run_coord_transf_button["state"] = "active"
        
    def irafstarfind(self,):#expected_sources=53**2,fwhm=5):
        
        fwhm = float(self.source_fwhm_entry.get())
        expected_sources = float(self.source_find_entry.get())
        
        ccd = CCDData(self.fits_hdu[0].data,header=self.fits_hdu[0].header,unit=u.adu)

        #print(ccd.header)
        mean_ccd, median_ccd, std_ccd = sigma_clipped_stats(ccd, sigma=4.0)
        
        #print(std_ccd)

        sources_table, unsorted_sources = CTH.iraf_gridsource_find(ccd,expected_sources=expected_sources,fwhm=fwhm,
                                                                   threshold=3*std_ccd)

        print(sources_table)
        self.source_table_display = source_table_display = Table(self.source_tab_frame_1c,dataframe=sources_table,showtoolbar=True)
        source_table_display.show()
        
        
        iraf_positions = np.transpose((sources_table['xcentroid'], sources_table['ycentroid']))
        
        self.sources_table = sources_table
        
        if (self.dmd_table is not None) and (self.sources_table is not None):
            
            DMD_PIX_df = pd.concat((self.dmd_table,self.sources_table),axis=1)
    
            self.DMD_PIX_df = DMD_PIX_df
            self.source_table_display = source_table_display = Table(self.source_tab_frame_1c,dataframe=self.DMD_PIX_df,showtoolbar=True)
            source_table_display.show()
            
            self.run_coord_transf_button["state"] = "active"
        
        apertures_ccd = CircularAperture(iraf_positions, r=4.)
        
        self.image = self.ax.imshow(ccd.data, cmap='gray', origin='lower',
                   interpolation='none')
        
        
        ap_plots = apertures_ccd.plot(self.ax,color='cyan', lw=1.5, alpha=0.5)
        self.fits_fig_canvas0c.draw()
        self.fits_fig_canvas0c.get_tk_widget().pack()

    def run_coord_transf(self):
        
        print(self.DMD_PIX_df)
        self.afftest = CTH.AFFtest(self.DMD_PIX_df)
        self.fit_wcs_sip_entry["state"] = "normal"
        self.fit_wcs_with_sip_button["state"] = "active"
        #fit_wcs_sip_entry = tk.Entry(self.frame1l,)
        #self.frame1l.create_window(98,180,window=fit_wcs_sip_entry)
        #fit_wcs_with_sip_button = tk.Button(self.frame1l,text="Run WCS Fit With SIP",bg="#9D76A4",
        #                                         command=afftest)
        #self.frame1l.create_window(98,200,window=fit_wcs_with_sip_button)
        
    
    def run_wcs_fit_with_sip(self):
        
        print(self.afftest.patsrc_df)
        self.afftest.fit_wcs_with_sip(int(self.fit_wcs_sip_entry.get()))
        self.add_wcs_fit_to_header()
        
    
    def add_wcs_fit_to_header(self):
        
        imdata = self.fits_hdu[0].data.copy()
        imhdr = self.fits_hdu[0].header.copy()
        imwcs = self.afftest.ccd_to_dmd_wcs.wcs
        
        imhdr.set('CRVAL1',imwcs.crval[0],'column val on DMD')
        imhdr.set('CRVAL2',imwcs.crval[1],'row val on DMD')
        
        
        imhdr.set('CTYPE1',imwcs.ctype[0],'DMD pretend ra')
        imhdr.set('CTYPE2',imwcs.ctype[1],'DMD pretend dec')
        imhdr.set('CRPIX1',imwcs.crpix[0],'column val on CCD')
        imhdr.set('CRPIX2',imwcs.crpix[1],'row val on CCD')
        
        imhdr.set('CD1_1',imwcs.cd[0,0])
        imhdr.set('CD1_2',imwcs.cd[0,1])
        imhdr.set('CD2_1',imwcs.cd[1,0])
        imhdr.set('CD2_2',imwcs.cd[1,1])
        
        ### SIP Coeffs ###
        sip_hdr = self.afftest.ccd_to_dmd_wcs.to_header(relax=True)
        
        order_keys = [i for i in sip_hdr.keys() if re.findall(r"(_ORDER$)",i)]
        a_mat_keys = [i for i in sip_hdr.keys() if re.findall(r"(^A_\d_\d)",i)]
        ap_mat_keys = [i for i in sip_hdr.keys() if re.findall(r"(^AP_\d_\d)",i)]
        b_mat_keys = [i for i in sip_hdr.keys() if re.findall(r"(^B_\d_\d)",i)]
        bp_mat_keys = [i for i in sip_hdr.keys() if re.findall(r"(^BP_\d_\d)",i)]
        
        sip_keys = order_keys+a_mat_keys+ap_mat_keys+b_mat_keys+bp_mat_keys
        
        for skey in sip_keys:
            
            imhdr.set(skey,sip_hdr[skey])
            
        imhdr.set('CRVAL1_mir',crval1_arcsec,'crval1*3600 because wcs fit needs to be in deg units')
        imhdr.set('CRVAL2_mir',crval2_arcsec,'crval2*3600 because wcs fit needs to be in deg units')
        new_hdul = fits.PrimaryHDU(data=imdata,header=imhdr)
        new_fitsname = os.path.split(self.browse_fits_files)[1][:-5]+'_with_dmd_wcs.fits'
        new_hdul.writeto("MapResults/"+new_fitsname)
        
        print(new_fitsname)
        
        
        

######

if __name__ == "__main__":
    #logger = log.get_logger("dmd_ccd_mapping_dev")
    #root = tk.Tk()
    fv = DMD_CCD_Mapping_Main()
    fv.geometry("1000x800")
    #top = fv.get_widget()
    fv.mainloop()
    

# END
