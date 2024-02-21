#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jan 26 10:31:57 2023

@author: danakoeppe
"""

# Say we took an image of some field of view and we wanted to put slits on different sources.
# This GUI will allow the user to pull up the recent image and click on sources to create
# a DMD pattern.

import sys
import os
import threading

import numpy as np
import pandas as pd
from pandastable import Table
import math


import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle


#from ginga.tkw.ImageViewTk import CanvasView
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.misc import log
from ginga.util.loader import load_data
from ginga.util import io_fits

from ginga.qtw.QtHelp import QtGui, QtCore, set_default_opengl_context
from ginga import colors
from ginga.qtw.ImageViewQt import CanvasView

from ginga.AstroImage import AstroImage
img = AstroImage()
from astropy.io import fits

import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename

### Needed to run ConvertSIlly by C. Loomis
import math
import pathlib

import importlib

from astropy.io import ascii
from astropy import coordinates, units as u, wcs
from astropy.wcs import WCS
from astropy.visualization import simple_norm

sys.path.insert(0,"../")
import setup_slits
importlib.reload(setup_slits)
from setup_slits import DMDSlit, DMD_Pattern_from_SlitList



matplotlib.pyplot.ion()


import warnings
warnings.filterwarnings('ignore')
global pix_scale_dmd
pix_scale_dmd = 1080/1024 # mirrors per pixel, always the same.


#import sewpy   #to run sextractor wrapper

STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'
# =============================d================================================
# 
# from Astrometry import tk_class_astrometry
# Astrometry = tk_class_astrometry
# 
# Astrometry.return_from_astrometry()
# 
# =============================================================================
import csv
from pathlib import Path
#define the local directory, absolute so it is not messed up when this is called
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
sys.path.append(local_dir)

# can be changed to any image
test_file_name = "../../IMAGES/grid11x11"

ccd2dmd_file = "./DMD_Mapping_WCS.fits"

class FitsViewer(QtGui.QMainWindow):
    def __init__(self, logger, render='widget'):

        self.logger = logger
        self.main = main
        self.test_file_name = test_file_name
        self.SlitList = []
        self.drawcolors = colors.get_colors()
        self.dc = get_canvas_types()
        
        hdul = fits.open(ccd2dmd_file)
        wcshead = hdul[0].header
        self.ccd2dmd_wcs = WCS(wcshead,relax=True)
        self.wcshead = wcshead
        
        
        
        #vbox = tk.Frame(main, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        #vbox.pack(side=tk.TOP)
        #vbox.place(x=5, y=0, anchor="nw")#, width=500, height=800)
        #self.vb = vbox
        
        fi = CanvasView(logger, render=render)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale',)
        fi.enable_autozoom('on')
        fi.set_zoom_algorithm('rate')
        fi.set_zoomrate(1.4)
        fi.show_pan_mark(True)
        fi.add_callback('drag-drop', self.drop_file_cb)
        fi.add_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
        main_canvas = self.dc.DrawingCanvas()
        main_canvas.enable_draw(True)
        main_canvas.enable_edit(True)
        main_canvas.set_drawtype('rectangle', color='lightblue')
        main_canvas.register_for_cursor_drawing(fi)
        main_canvas.add_callback('draw-event', self.draw_cb)
        main_canvas.set_draw_mode('draw')
        main_canvas.set_surface(fi)
        main_canvas.ui_set_active(True)
        self.main_canvas = main_canvas

        # add our new canvas to viewers default canvas
        fi.get_canvas().add(main_canvas)

        self.drawtypes = main_canvas.get_drawtypes()
        self.drawtypes.sort()
        
        
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')

        w = fi.get_widget()
        w.resize(512, 512)

        vbox = QtGui.QVBoxLayout()
        vbox.setContentsMargins(QtCore.QMargins(2, 2, 2, 2))
        vbox.setSpacing(1)
        vbox.addWidget(w, stretch=1)
        self.vb = vbox
        
        self.readout = QtGui.QLabel("")
        vbox.addWidget(self.readout, stretch=0,
                       alignment=QtCore.Qt.AlignCenter)

        
        """
        fig = Figure(figsize=(8,8))#,tight_layout=True,)
        ax = fig.add_axes([0,0,1,1],frameon=False)
        self.fig = fig
        self.ax = ax
        

        main_canvas = FigureCanvasTkAgg(fig, vbox,)
        main_canvas.draw()
        main_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        main_canvas.mpl_connect("motion_notify_event",self.cursor_cb)
        self.main_canvas = main_canvas
        main_canvas.mpl_connect("button_press_event",self.zoomimage)
        
        
        self.readout = tk.Label(main, text='')
        self.readout.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
        """
        #self.vbox_tab = tk.Frame(main)
        #self.vbox_tab.pack(side=tk.RIGHT)
        #self.vbox_tab.place(x=600,y=290,width=700,height=300)
        
        
        
#        vbox_zoom = tk.Frame(main, relief=tk.RAISED, borderwidth=1)
#        vbox_zoom.pack(side=tk.TOP)
#        vbox_zoom.place(x=805,y=0, anchor="ne")
        
        
        vbox_zoom = QtGui.QVBoxLayout()
        vbox_zoom.setContentsMargins(QtCore.QMargins(2, 2, 2, 2))
        vbox_zoom.setSpacing(1)
        vbox_zoom.addWidget(w, stretch=1)
        
        zfig = Figure(figsize=(3,3))#,tight_layout=True,)
        
        zax = zfig.add_axes([0,0,1,1],frameon=False)
        

        zoomcanvas = FigureCanvasTkAgg(zfig, vbox_zoom)
        zoomcanvas.draw()
        zoomcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.zoomcanvas = zoomcanvas
        zoomcanvas.mpl_connect("button_press_event",self.draw_slit_mpl)
        
        self.zfig = zfig
        self.zax = zax
        
       
        vbox_zoom_slit_x0 = tk.Frame(main)
        vbox_zoom_slit_x0.pack(anchor='n')
        vbox_zoom_slit_x0.place(x=805,y=30)
        spinvar_zx0 = tk.DoubleVar()
        self.spinvar_zx0 = spinvar_zx0
        spinvar_zx0_label = tk.Label(vbox_zoom_slit_x0,text="x0")
        spinvar_zx0_label.pack(anchor='ne',side=tk.RIGHT)
        
        slit_x0_spinbox = tk.Spinbox(vbox_zoom_slit_x0,from_=1,to=1025,
                                     textvariable=self.spinvar_zx0,
                                     command=self.edit_slit_mpl,width=5,
                                     increment=1)
        slit_x0_spinbox.pack(side=tk.TOP,fill=tk.BOTH,padx=0)
        
        #slit_x0_spinbox.place(x=600,y=200)
        
        vbox_zoom_slit_x1 = tk.Frame(main)
        vbox_zoom_slit_x1.pack(anchor='n')
        vbox_zoom_slit_x1.place(x=805,y=60)
        spinvar_zx1 = tk.DoubleVar()
        self.spinvar_zx1 = spinvar_zx1
        spinvar_zx1_label = tk.Label(vbox_zoom_slit_x1,text="x1")
        spinvar_zx1_label.pack(anchor='ne',side=tk.RIGHT)
        
        slit_x1_spinbox = tk.Spinbox(vbox_zoom_slit_x1,from_=1,to=1025,
                                     textvariable=self.spinvar_zx1,
                                     command=self.edit_slit_mpl, width=5,
                                     increment=1)
        slit_x1_spinbox.pack(side=tk.BOTTOM,fill=tk.BOTH)
        
        
        self.slit_x0_spinbox = slit_x0_spinbox
        self.slit_x1_spinbox = slit_x1_spinbox
        
        
       
        vbox_zoom_slit_y0 = tk.Frame(main)
        vbox_zoom_slit_y0.pack(anchor='n')
        vbox_zoom_slit_y0.place(x=805,y=90)
        spinvar_zy0 = tk.DoubleVar()
        self.spinvar_zy0 = spinvar_zy0
        spinvar_zy0_label = tk.Label(vbox_zoom_slit_y0,text="y0")
        spinvar_zy0_label.pack(anchor='ne',side=tk.RIGHT)
        
        slit_y0_spinbox = tk.Spinbox(vbox_zoom_slit_y0,from_=1,to=1025,
                                     textvariable=self.spinvar_zy0,
                                     command=self.edit_slit_mpl,width=5,
                                     increment=1)
        slit_y0_spinbox.pack(side=tk.TOP,fill=tk.BOTH,padx=0)
        
        vbox_zoom_slit_y1 = tk.Frame(main)
        vbox_zoom_slit_y1.pack(anchor='s')
        vbox_zoom_slit_y1.place(x=805,y=120)
        spinvar_zy1 = tk.DoubleVar()
        self.spinvar_zy1 = spinvar_zy1
        spinvar_zy1_label = tk.Label(vbox_zoom_slit_y1,text="y1")
        spinvar_zy1_label.pack(anchor='ne',side=tk.RIGHT)
        
        slit_y1_spinbox = tk.Spinbox(vbox_zoom_slit_y1,from_=1,to=1025,
                                     textvariable=self.spinvar_zy1,
                                     command=self.edit_slit_mpl, width=5,
                                     increment=1)
        slit_y1_spinbox.pack(side=tk.BOTTOM,fill=tk.BOTH)
        
        self.slit_y0_spinbox = slit_y0_spinbox
        self.slit_y1_spinbox = slit_y1_spinbox
        
 #       """
 
        
        
 #       self.slit_readout = tk.Label(main, text='')
 #       self.slit_readout.pack(side=tk.TOP, fill=tk.X, expand=0)
 #       self.slit_readout.place(x=600,y=220)
        
        slit_bbox = tk.Frame(main)
        slit_bbox.pack(side=tk.RIGHT,fill=tk.X, expand=0)
        slit_bbox.place(x=805,y=150)
        slit_button = tk.Button(slit_bbox, text="Add Slit",command=self.save_slit)
        slit_button.pack(side=tk.RIGHT)
        
        hbox1 = tk.Frame(main)
        hbox1.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
        
        
        wopen = tk.Button(hbox1, text="Open File",
                               command=self.load_file)
        wopen.pack(side=tk.LEFT,fill="none")
        
        self.hbox1 = hbox1
        
    def load_file(self):
        #FITSfiledir = './fits_image/'
        
        #self.fullpath_FITSfilename = FITSfiledir + (os.listdir(FITSfiledir))[0] 
            # './fits_image/cutout_rebined_resized.fits'
#        image = load_data(self.test_file_name, logger=self.logger)

        self.browse_fits_files = tk.filedialog.askopenfilename(initialdir = "./",filetypes=[("FITS files","*fits")], 
                    title = "Select a FITS File",parent=self.hbox1)
        
        
        image = io_fits.load_file(self.browse_fits_files)
        
        self.ImHead = image.as_hdu().header        
        self.AstroImage = image    #make the AstroImage available
        ImData = image.as_nddata().data
        self.ImData = ImData
        norm = simple_norm(ImData,stretch="log")
        self.norm = norm
        self.ax.imshow(ImData,origin='lower',norm=norm,cmap='gray')
        self.main_canvas.draw()
        #self.fitsimage.set_image(image)
            # passes the image to the viewer through the set_image() method
        self.main.title(self.test_file_name)
        


        
    def zoomimage(self, event):#viewer, button, data_x, data_y):
        
        self.zax.clear()
        #self.zoomfitsimage.clear()
        x0=int(event.xdata)
        y0=int(event.ydata)
        
        
        try:
            self.fig_point.remove()
        
        except:
            pass
        
        self.fig_point = self.ax.scatter(x0,y0,s=200,c="orangered",marker="+",linewidth=3)
        
        self.main_canvas.draw()
        
        # Draw an oval in the given co-ordinates
        
        print("zoomcenter x {}, zoomcenter y {}".format(x0,y0))
        
        half_chunk_size = 20
        xmincut = max(0,x0-half_chunk_size)
        xmaxcut = min(self.ImData.shape[1],x0+half_chunk_size)
        ymincut = max(0,y0-half_chunk_size)
        ymaxcut = min(self.ImData.shape[0],y0+half_chunk_size)
        
        zoomAstroim = AstroImage(self.AstroImage.cutout_data(xmincut,ymincut,xmaxcut,ymaxcut))#imdata[x0-50:x0+50,y0-50:y0+50]
        zoomim = self.AstroImage.cutout_data(xmincut,ymincut,xmaxcut,ymaxcut)
        
        self.zoomim = zoomim
        #self.zoomfitsimage.set_image(zoomim)
        self.zoombox_x0 = xmincut
        self.zoombox_x1 = xmaxcut
        self.zoombox_y0 = ymincut
        self.zoombox_y1 = ymaxcut
        
        
        
        
        self.zax.imshow(zoomim,norm=self.norm, origin='lower',cmap='gray',
                        extent=[xmincut,xmaxcut,ymincut,ymaxcut])
        
        
        
        xl0,xl1 = self.zax.get_xlim()
        xl0,xl1 = int(xl0),int(xl1)
        yl0,yl1 = self.zax.get_ylim()
        yl0,yl1 = int(yl0),int(yl1)
        self.zax.set_xticks(range(xl0,xl1))
        self.zax.set_yticks(range(yl0,yl1))

        self.zoomcanvas.draw()
        
        
        
        
        #x,y = self.canvas_to_image_coords(x=event.x, y=event.y, image=imdata, tagOrId='imdata') # Can also pass img_tag as tagOrId
        print(x0,y0)
        
    def draw_slit_mpl(self, event):
        
        try:
            self.patch.remove()
            
        except:
            pass
        
        zx0 = round(float(event.xdata),1) #data_x
        zy0 = round(float(event.ydata),1) #data_y
        
        fits_x0, fits_y0 = zx0 + 1, zy0 + 1
        
        
        dmd_x0, dmd_y0 = self.ccd2dmd_wcs.all_pix2world(fits_x0,fits_y0,0)
        dmd_x0, dmd_y0 = int(math.floor(dmd_x0*3600)), int(math.floor(dmd_y0*3600))
        

        print("dmd0 coords",dmd_x0,dmd_y0)
        
        
        
        # pix_scale_dmd is 1080 mirrors / 1024 (active) pixels
        # nominal slit width is 2 mirrors
        
        mirwidth = 2
        mirlength = 7
        
        pixwidth = 2*pix_scale_dmd #size of slit will be shown in pixels
        pixlength = 7*pix_scale_dmd
        
        
        
        zx1 = round(pixlength+zx0,1)
        zy1 = round(pixwidth+zy0,1)
        
        fits_x1, fits_y1 = zx1 + 1, zy1 + 1
        dmd_x1, dmd_y1 = self.ccd2dmd_wcs.all_pix2world(fits_x1,fits_y1,0)
        dmd_x1, dmd_y1 = int(math.floor(dmd_x1*3600)), int(math.floor(dmd_y1*3600))
        
        print("dmd1 coords",dmd_x1,dmd_y1)
        
        print("zx,zy:",zx0,zy0)
        self.spinvar_zx0.set(zx0)
        self.spinvar_zy0.set(zy0)
        self.spinvar_zx1.set(zx1)
        self.spinvar_zy1.set(zy1)
        
        
        patch = Rectangle((zx0,zy0),pixlength,pixwidth,facecolor='k',
                          linewidth=0.01,transform=self.zax.transData)
        
        self.patch = patch
        self.zax.add_patch(self.patch)
        
        #self.zfig.canvas.draw_idle()
        self.zoomcanvas.draw_idle()
        
        
        text_mir_coords = "dmdX0: %.2f  dmdY0: %.2f " %(dmd_x0, dmd_y0) +"\n"
        text_slit_width = "slit width: {:.0f} mirrors".format(mirwidth) +"\n"
        text_slit_length = "slit length: {:.0f} mirrors".format(mirlength)
        
        self.slit_readout.config(text=text_mir_coords+text_slit_width+text_slit_length)
        
        this_slit_num = len(self.SlitList)+1
        
        ra, dec = '-', '-'
        self.current_slit = DMDSlit(ra,dec,dmd_x0,dmd_y0,dmd_x1,dmd_y1,
                                    slit_n=this_slit_num)
        
        attrs = vars(self.current_slit)
        #print(', '.join("%s: %s" % item for item in attrs.items()))
        
        #print(self.current_slit.x0,self.current_slit.x1)
    
    def edit_slit_mpl(self):
        
        #zx0, zy0  = int(self.slit_x0_spinbox.get()), int(self.slit_y0_spinbox.get())
        #zx1, zy1 = int(self.slit_x1_spinbox.get()), int(self.slit_y1_spinbox.get())
        
        zx0, zy0  = float(self.slit_x0_spinbox.get()), float(self.slit_y0_spinbox.get())
        zx1, zy1 = float(self.slit_x1_spinbox.get()), float(self.slit_y1_spinbox.get())
        
        fits_x0, fits_y0 = zx0 + 1, zy0 + 1
        fits_x1, fits_y1 = zx1 + 1, zy1 + 1
        
        dmd_x0, dmd_y0 = self.ccd2dmd_wcs.all_pix2world(fits_x0,fits_y0,0)
        dmd_x0, dmd_y0 = int(math.floor(dmd_x0*3600)), int(math.floor(dmd_y0*3600))
        
        dmd_x1, dmd_y1 = self.ccd2dmd_wcs.all_pix2world(fits_x1,fits_y1,0)
        dmd_x1, dmd_y1 = int(math.floor(dmd_x1*3600)), int(math.floor(dmd_y1*3600))
        
        self.current_slit.ra = '-'
        self.current_slit.dec = '-'
        self.current_slit.x0 = dmd_x0
        self.current_slit.y0 = dmd_y0
        self.current_slit.x1 = dmd_x1
        self.current_slit.y1 = dmd_y1
        
        #print(self.current_slit.x0,self.current_slit.x1)
        
        new_pixlength = round(zx1-zx0,1)
        new_pixwidth = round(zy1-zy0,1)
        
        new_mirlength = int(dmd_x1-dmd_x0)
        new_mirwidth = int(dmd_y1-dmd_y0)
        
        
        
        self.patch.set_x(zx0)
        self.patch.set_y(zy0)
        self.patch.set_width(new_pixlength)
        self.patch.set_height(new_pixwidth)
        
        self.zoomcanvas.draw()
        
        
        text_mir_coords = "dmdX0: %.2f  dmdY0: %.2f " %(dmd_x0, dmd_y0) +"\n"
        text_slit_width = "slit width: {:.0f} mirrors".format(new_mirwidth) +"\n"
        text_slit_length = "slit length: {:.0f} mirrors".format(new_mirlength)
        
        self.slit_readout.config(text=text_mir_coords+text_slit_width+text_slit_length)
        
        
    
    def save_slit(self):
        
        
        savex = self.fig_point.get_offsets()[0][0]
        savey = self.fig_point.get_offsets()[0][1]
        
        try:
            self.fig_point.remove()
        except:
            pass
        
        self.ax.scatter(savex,savey,s=200,c="lime",marker="x",linewidth=3)
        
        self.main_canvas.draw()
        
        sdata = np.array([self.current_slit.slit_n, self.current_slit.ra, 
                          self.current_slit.dec, self.current_slit.x0, 
                          self.current_slit.y0,self.current_slit.x1, 
                          self.current_slit.y1, self.current_slit.xc, 
                          self.current_slit.yc, self.current_slit.dx0, 
                          self.current_slit.dy0,self.current_slit.dx1, 
                          self.current_slit.dy1, self.current_slit.dx,
                          self.current_slit.dy])
        
        slit_cols = ["slit_number", "ra", "dec", "x0", "y0", "x1", "y1", 
                     "xc", "yc", "dx0", "dy0", "dx1", "dy1", "dx", "dy"]
        
        this_slit_df = pd.DataFrame(data=[sdata],columns=slit_cols)
        if len(self.SlitList)==0:
            
            
            SlitDF = pd.DataFrame([sdata],columns=slit_cols)
            
        else:
            
            SlitDF = pd.concat([self.SlitDF,this_slit_df],axis=0)
            print(SlitDF.shape)
        
        self.SlitDF = SlitDF
        print(self.SlitDF)
        
        self.SlitList.extend([self.current_slit])
        print("slit saved to list")
        
        attrs = vars(self.current_slit)
        print(', '.join("%s: %s" % item for item in attrs.items()))
        
        self.slit_table = Table(self.vbox_tab,dataframe=self.SlitDF,showtoolbar=True,
                                height=5)
        self.slit_table.show()
        
        
    #def creat_DMD_pattern_tables(self):
    def set_drawparams(self, kind):
        index = self.wdrawtype.currentIndex()
        kind = self.drawtypes[index]
        index = self.wdrawcolor.currentIndex()
        fill = (self.wfill.checkState() != 0)
        alpha = self.walpha.value()

        params = {'color': self.drawcolors[index],
                  'alpha': alpha,
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def clear_canvas(self):
        self.canvas.delete_all_objects()

    def load_file(self, filepath):
        image = load_data(filepath, logger=self.logger)

        self.fitsimage.set_image(image)
        self.setWindowTitle(filepath)

    def open_file(self):
        res = QtGui.QFileDialog.getOpenFileName(self, "Open FITS file",
                                                ".", "FITS files (*.fits)")
        if isinstance(res, tuple):
            fileName = res[0]
        else:
            fileName = str(res)
        if len(fileName) != 0:
            self.load_file(fileName)

    def drop_file_cb(self, fitsimage, paths):
        fileName = paths[0]
        self.load_file(fileName)
        
        
    def cursor_cb(self, event):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        
        data_x = event.xdata
        data_y = event.ydata
        
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            
            value = int(self.ImData[int(data_x),int(data_y)])
            #value = int(round(viewer.get_data(int(data_x + viewer.data_off),
            #                        int(data_y + viewer.data_off))),0)
            
            fits_x, fits_y = data_x + 1, data_y + 1
            
            dmd_x, dmd_y = self.ccd2dmd_wcs.all_pix2world(fits_x,fits_y,0)
            
            """
            # Calculate WCS RA
            try:
                # NOTE: image function operates on DATA space coords
                image = viewer.get_image()
                if image is None:
                    # No image loaded
                    return
                ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                                   format='str', coords='fits')
                self.ra_center, self.dec_center = image.pixtoradec(528, 516,
                                                   format='str', coords='fits')

            except Exception as e:
                self.logger.warning("Bad coordinate conversion: %s" % (
                    str(e)))
                ra_txt = 'BAD WCS'
                dec_txt = 'BAD WCS'

            text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s" % (
                ra_txt, dec_txt, fits_x, fits_y, value)
            """

            text_pix = "imX: %.2f  imY: %.2f  Value: %s" % (fits_x, fits_y, value) +"\n"
            text_mir = "dmdX: %.2f  dmdY: %.2f " %(dmd_x*3600, dmd_y*3600)
            #self.readout.config(text=text_pix+text_mir)
            text = text_pix + text_mir
            self.readout.setText(text)
        except Exception:
            value = None
            fits_x, fits_y = None, None
            dmd_x, dmd_y = None, None


    def set_mode_cb(self, mode, tf):
        self.logger.info("canvas mode changed (%s) %s" % (mode, tf))
        if not (tf is False):
            self.canvas.set_draw_mode(mode)
        return True
    
    def draw_cb(self, canvas, tag):
        obj = canvas.get_object_by_tag(tag)
        obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        obj.add_callback('pick-hover', self.pick_cb, 'hover')
        obj.add_callback('pick-enter', self.pick_cb, 'enter')
        obj.add_callback('pick-leave', self.pick_cb, 'leave')
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.pickable = True
        obj.add_callback('edited', self.edit_cb)
    
    def pick_cb(self, obj, canvas, event, pt, ptype):
        self.logger.info("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        return True
    
    def edit_cb(self, obj):
        self.logger.info("object %s has been edited" % (obj.kind))
        return True
    
    def quit(self, *args):
        self.logger.info("Attempting to shut down the application...")
        self.deleteLater()

        
def main(options, args):

    if options.render == 'opengl':
        set_default_opengl_context()

    #QtGui.QApplication.setGraphicsSystem('raster')
    app = QtGui.QApplication(args)

    logger = log.get_logger("example2", options=options)

    w = FitsViewer(logger, render=options.render)
    w.resize(524, 540)
    w.show()
    app.setActiveWindow(w)
    w.raise_()
    w.activateWindow()

    if len(args) > 0:
        w.load_file(args[0])

    app.exec_()


if __name__ == "__main__":

    # Parse command line options
    from argparse import ArgumentParser

    argprs = ArgumentParser()

    argprs.add_argument("--debug", dest="debug", default=False,
                        action="store_true",
                        help="Enter the pdb debugger on main()")
    argprs.add_argument("-r", "--render", dest="render", default='widget',
                        help="Set render type {widget|scene|opengl}")
    argprs.add_argument("--profile", dest="profile", action="store_true",
                        default=False,
                        help="Run the profiler on main()")
    log.addlogopts(argprs)

    (options, args) = argprs.parse_known_args(sys.argv[1:])

    # Are we debugging this?
    if options.debug:
        import pdb

        pdb.run('main(options, args)')

    # Are we profiling this?
    elif options.profile:
        import profile

        print(("%s profile:" % sys.argv[0]))
        profile.run('main(options, args)')

    else:
        main(options, args)

# END


#main=tk.Tk()
#mywin=MyDMD(main)
#main.title('Hello Python')
#main.geometry("1300x800")
#main.mainloop()