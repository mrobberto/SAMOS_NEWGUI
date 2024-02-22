#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb  3 11:41:59 2023

@author: danakoeppe
"""

#! /usr/bin/env python
#
# example2_qt.py -- Simple, configurable FITS viewer.
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#

import sys
import os
import threading
import pathlib

import importlib
import numpy as np
import pandas as pd
#from pandastable import Table
import math
import re

from ginga.qtw.QtHelp import QtGui, QtCore, set_default_opengl_context
from ginga import colors
from ginga.qtw.ImageViewQt import CanvasView
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.misc import log
from ginga.util.loader import load_data
from ginga.util.iqcalc import IQCalc

from PyQt5.QtGui import QPainter, QBrush, QPen
from PyQt5.QtCore import Qt as QtV
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem
from ginga.AstroImage import AstroImage
img = AstroImage()
from astropy.io import fits

from astropy.io import ascii
from astropy import coordinates, units as u, wcs
from astropy.wcs import WCS
from astropy.visualization import simple_norm
from astropy.stats import mad_std, sigma_clipped_stats
from photutils.aperture import CircularAperture, EllipticalAperture

import matplotlib
matplotlib.use('Qt5Agg')


from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


from .setup_slits import DMDSlit, write_DMD_pattern
from samos.utilities import get_data_file

STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'

import warnings
warnings.filterwarnings('ignore')
global pix_scale_dmd
pix_scale_dmd = 1080/1024 # mirrors per pixel, always the same.

import csv
#define the local directory, absolute so it is not messed up when this is called
path = pathlib.Path(__file__).parent.absolute()
local_dir = str(path.absolute())


import ap_region_massimoshacked as apreg
from regions import PixCoord, RectanglePixelRegion, PointPixelRegion, RegionVisual

ccd2dmd_file = get_data_file("dmd.pattern", "DMD_Mapping_WCS.fits")


class FitsViewer(QtGui.QMainWindow):

    def __init__(self, logger, render='widget'):
        super(FitsViewer, self).__init__()
        self.logger = logger
        self.main = main
        self.drawcolors = colors.get_colors()
        self.dc = get_canvas_types()

        hdul = fits.open(ccd2dmd_file)
        wcshead = hdul[0].header
        self.ccd2dmd_wcs = WCS(wcshead,relax=True)
        self.wcshead = wcshead
        self.SlitObjectList = []
        self.slit_number = 0
        self.saved_patterns = []
        
        main_layout = QtGui.QGridLayout()
# =============================================================================
#         
#  #    Main FITS viewing frame
#         
# =============================================================================

        fi = CanvasView(logger, render=render)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        fi.set_zoom_algorithm('rate')
        fi.set_zoomrate(1.4)
        #fi.show_pan_mark(True)
        fi.add_callback('drag-drop', self.drop_file_cb)
        fi.add_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
        canvas = self.dc.DrawingCanvas()
        canvas.enable_draw(True)
        canvas.enable_edit(True)
        canvas.set_drawtype('rectangle', color='lightblue')
        canvas.register_for_cursor_drawing(fi)
        canvas.add_callback('draw-event', self.draw_cb)
        canvas.set_draw_mode('draw')
        canvas.add_callback('pick-up', self.source_click_event)
        
        canvas.set_surface(fi)
        canvas.ui_set_active(True)
        self.canvas = canvas

        # add our new canvas to viewers default canvas
        fi.get_canvas().add(canvas)
        
        self.drawtypes = canvas.get_drawtypes()
        self.drawtypes.sort()

        # add a color bar
        #fi.show_color_bar(True)
        #fi.show_focus_indicator(True)

        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')

        w = fi.get_widget()
        w.resize(512, 512)

        vbox = QtGui.QVBoxLayout()
        #vbox.setContentsMargins(QtCore.QMargins(2, 2, 2, 2))
        vbox.setContentsMargins(1, 1, 1, 1)
        vbox.setSpacing(1)
        vbox.addWidget(w, stretch=1)
        

        self.readout = QtGui.QLabel("")
        vbox.addWidget(self.readout, stretch=0,
                       alignment=QtCore.Qt.AlignCenter)
        
        wadd_slit = QtGui.QPushButton("Add Slit")
        wadd_slit.clicked.connect(self.add_slit)
        wadd_slit.setFixedWidth(150)
        vbox.addWidget(wadd_slit, stretch=0)
        
        save_pat_hbox = QtGui.QHBoxLayout()
        save_pat_hbox.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
        save_pat_hbox.setAlignment(QtCore.Qt.AlignRight)

        wpattern_name = QtGui.QLineEdit(placeholderText="enter pattern name")
        wpattern_name.setFixedWidth(150)
        save_pat_hbox.addWidget(wpattern_name,stretch=0,alignment=QtCore.Qt.AlignRight)
        self.wpattern_name = wpattern_name
        wcreate_pattern_button = QtGui.QPushButton("Create DMD Pattern")
        wcreate_pattern_button.clicked.connect(self.create_dmd_save_pattern)
        wcreate_pattern_button.setFixedWidth(150)
        save_pat_hbox.addWidget(wcreate_pattern_button,stretch=0,alignment=QtCore.Qt.AlignRight)
        self.wcreate_pattern_button = wcreate_pattern_button
        
        save_pat_hbox.setSpacing(0)
        save_pat_hbox.addStretch(1)
        
        #vbox.addStretch(1)
        vbox.addLayout(save_pat_hbox)
        
        main_layout.addLayout(vbox, 0,1)
        
        main_layout.setHorizontalSpacing(10)

# =============================================================================
#         
#  #    Selected Area FITS viewing frame
#         
# =============================================================================

        
        zoom_fi = CanvasView(logger, render=render)
        zoom_fi.enable_autocuts('on')
        zoom_fi.set_autocut_params('zscale')
        zoom_fi.enable_autozoom('on')
        zoom_fi.set_zoom_algorithm('rate')
        zoom_fi.set_zoomrate(1.4)
        #zoom_fi.show_pan_mark(True)

        zoom_fi.set_bg(0.2, 0.2, 0.2)
        zoom_fi.ui_set_active(True)
        self.zoom_fitsimage = zoom_fi

        zoom_bd = zoom_fi.get_bindings()
        zoom_bd.enable_all(True)

        # canvas that we will draw on
        zoom_canvas = self.dc.DrawingCanvas()
        zoom_canvas.enable_draw(True)
        zoom_canvas.enable_edit(True)
        zoom_canvas.set_drawtype('rectangle', color='lightblue')
        zoom_canvas.register_for_cursor_drawing(zoom_fi)
        zoom_canvas.add_callback('draw-event', self.zoom_draw_cb)
        zoom_canvas.set_draw_mode('draw')
        
        zoom_canvas.set_surface(zoom_fi)
        zoom_canvas.ui_set_active(True)
        self.zoom_canvas = zoom_canvas

        # add our new canvas to viewers default canvas
        zoom_fi.get_canvas().add(zoom_canvas)

        self.drawtypes = zoom_canvas.get_drawtypes()
        self.drawtypes.sort()

        # add a color bar
        #zoom_fi.show_color_bar(True)
        #zoom_fi.show_focus_indicator(True)

        # add little mode indicator that shows keyboard modal states
        zoom_fi.show_mode_indicator(True, corner='ur')

        zoom_w = zoom_fi.get_widget()
        zoom_w.resize(50, 50)
        zoom_w.setFixedWidth(300)
        zoom_w.setFixedHeight(300)


        zoom_vbox = QtGui.QVBoxLayout()
        zoom_vbox.setContentsMargins(0, 0, 0, 0)
        zoom_vbox.setSpacing(1)
        zoom_vbox.addWidget(zoom_w, stretch=0)
        zoom_vbox.setAlignment(QtCore.Qt.AlignTop)
        #self.readout = QtGui.QLabel("")
        #zoom_vbox.addWidget(self.readout, stretch=0,
        #               alignment=QtCore.Qt.AlignCenter)
        
        zmode = self.zoom_canvas.get_draw_mode()
        
        zedit_btn = QtGui.QRadioButton("Edit Slit")
        zedit_btn.setChecked(zmode == 'edit')
        zedit_btn.toggled.connect(lambda val: self.zoom_set_mode_cb('edit', val))
        zedit_btn.setToolTip("Choose this to edit things on the canvas")
        zoom_vbox.addWidget(zedit_btn)
        

        zdraw_btn1 = QtGui.QRadioButton("Draw")
        zdraw_btn1.setChecked(zmode == 'draw')
        zdraw_btn1.toggled.connect(lambda val: self.zoom_set_mode_cb('draw', val))
        zdraw_btn1.setToolTip("Choose this to draw on the canvas")
        zoom_vbox.addWidget(zdraw_btn1)


        
        self.zoom_vbox = zoom_vbox
        #main_layout.addLayout(zoom_vbox,0,2)
        
        #wadd_slit = QtGui.QPushButton("Add Slit")
        #wadd_slit.clicked.connect(self.add_slit)
        #zoom_vbox.addWidget(wadd_slit)
        

# =============================================================================
#         
#  #    Readout section for Region file
#         
# =============================================================================        
        
        reg_vbox = QtGui.QVBoxLayout()
        reg_vbox.setContentsMargins(1, 1, 1, 1)
        reg_vbox.setSpacing(1)
        
        reg_readout_txt = "xcenter, ycenter, width, height, angle \n"
        self.reg_readout = QtGui.QLabel(reg_readout_txt)
        reg_vbox.addWidget(self.reg_readout, stretch=0,
                       alignment=QtCore.Qt.AlignCenter)
        #main_layout.addLayout(reg_vbox, 0,0)
        
        slitDF = pd.DataFrame(columns=["object","RA","DEC","image_xc","image_yc",
                                       "image_x0", "image_y0", "image_x1", 
                                       "image_y1","dmd_xc","dmd_yc","dmd_x0",
                                       "dmd_y0", "dmd_x1", "dmd_y1"])
        self.slitDF= slitDF
        
        wslit_table = QtWidgets.QTableWidget()
        wslit_table.setColumnCount(len(slitDF.columns))
        wslit_table.setRowCount(0)
        wslit_table.setHorizontalHeaderLabels(slitDF.columns.values)
        wslit_table.setMinimumWidth(300)
        self.wslit_table = wslit_table
        
        
        tvbox = QtGui.QVBoxLayout()
        tvbox.setContentsMargins(QtCore.QMargins(3,3,3,3))
        tvbox.addWidget(self.wslit_table, stretch=1)
        

#         
#  #    Display Mask Pattern
#         

        wreg_read = QtGui.QPushButton("Upload Region File")
        wreg_read.clicked.connect(self.read_region_file)
        
        tvbox.addWidget(wreg_read)
        main_layout.addLayout(tvbox, 0, 0)
                
        self.wslit_table.show()
        self.wreg_read = wreg_read
        
# =============================================================================
#         
#  #    Editing Parameters
#         
# =============================================================================

        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(QtCore.QMargins(1, 1, 1, 1))

        wdrawtype = QtGui.QComboBox()
        for name in self.drawtypes:
            wdrawtype.addItem(name)
        index = self.drawtypes.index('square')
        wdrawtype.setCurrentIndex(index)
        wdrawtype.activated.connect(self.set_drawparams)
        self.wdrawtype = wdrawtype
        

        wdrawcolor = QtGui.QComboBox()
        for name in self.drawcolors:
            wdrawcolor.addItem(name)
        index = self.drawcolors.index('lightblue')
        wdrawcolor.setCurrentIndex(index)
        wdrawcolor.activated.connect(self.set_drawparams)
        self.wdrawcolor = wdrawcolor

        wfill = QtGui.QCheckBox("Fill")
        wfill.stateChanged.connect(self.set_drawparams)
        self.wfill = wfill

        walpha = QtGui.QDoubleSpinBox()
        walpha.setRange(0.0, 1.0)
        walpha.setSingleStep(0.1)
        walpha.setValue(1.0)
        walpha.valueChanged.connect(self.set_drawparams)
        self.walpha = walpha

        wclear = QtGui.QPushButton("Clear Canvas")
        wclear.clicked.connect(self.clear_canvas)
        wopen = QtGui.QPushButton("Open File")
        wopen.clicked.connect(self.open_file)
        wquit = QtGui.QPushButton("Quit")
        wquit.clicked.connect(self.quit)

        hbox.addStretch(1)
        for w in (wopen, wdrawtype, wdrawcolor, wfill,
                  QtGui.QLabel('Alpha:'), walpha, wclear, wquit):
            hbox.addWidget(w, stretch=0)

        hw = QtGui.QWidget()
        hw.setLayout(hbox)
        main_layout.addWidget(hw,1,1,)# stretch=0)

        mode = self.canvas.get_draw_mode()
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(QtCore.QMargins(4, 2, 4, 2))

        btn1 = QtGui.QRadioButton("Draw")
        btn1.setChecked(mode == 'draw')
        btn1.toggled.connect(lambda val: self.set_mode_cb('draw', val))
        btn1.setToolTip("Choose this to draw on the canvas")
        hbox.addWidget(btn1)

        btn2 = QtGui.QRadioButton("Edit")
        btn2.setChecked(mode == 'edit')
        btn2.toggled.connect(lambda val: self.set_mode_cb('edit', val))
        btn2.setToolTip("Choose this to edit things on the canvas")
        hbox.addWidget(btn2)

        btn3 = QtGui.QRadioButton("Pick")
        btn3.setChecked(mode == 'pick')
        btn3.toggled.connect(lambda val: self.set_mode_cb('pick', val))
        btn3.setToolTip("Choose this to pick things on the canvas")
        hbox.addWidget(btn3)

        hbox.addWidget(QtGui.QLabel(''), stretch=1)
        hw = QtGui.QWidget()
        hw.setLayout(hbox)
        main_layout.addWidget(hw,2,1 )#stretch=0)

        vw = QtGui.QWidget()
        self.setCentralWidget(vw)
        vw.setLayout(main_layout)
        
        

    def set_drawparams(self, kind):
        index = self.wdrawtype.currentIndex()
        kind = self.drawtypes[index]
        index = self.wdrawcolor.currentIndex()
        fill = (self.wfill.checkState() != 0)
        alpha = self.walpha.value()

        params = {'color': self.drawcolors[index],
                  'alpha': alpha,
                  }
        if kind in ('square'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def clear_canvas(self):
        self.canvas.delete_all_objects()

    def load_file(self, filepath):
        image = load_data(filepath, logger=self.logger)
        
        
        self.ImHead = image.as_hdu().header        
        self.AstroImage = image    #make the AstroImage available
        ImData = image.as_nddata().data
        self.ImData = ImData


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
            
    def display_regions_from_file(self, regfilepath):       
        
        regfile = open(regfilepath, "r")
        
        slit_objs = []
        for line in regfile.readlines()[3:]:
            #print(line)
            #assuming the regions are rectangles and in pixel coordinates for now
            rline = re.sub("[box(]", '',line)
            rline = re.sub(r"[)]", "", rline).strip("\n").split(",")
            #print(rline)
            x, y, w, h, a = np.array(rline).astype(float)
            
            
            slit_obj = RectanglePixelRegion(PixCoord(x,y), w, h)
            slit_objs.append(slit_obj)
            
            apreg.add_region(canvas=self.canvas,r=slit_obj)
            
        self.slit_objs = slit_objs
        regfile.close()
    
    def read_region_file(self):
        
        reg = QtGui.QFileDialog.getOpenFileName(self, "Upload Region File",
                                                ".", "region files (*.reg)")
        print("trying to read region file")
        if isinstance(reg, tuple):
            regfileName = reg[0]
        else:
            regfileName = str(reg)
        if len(regfileName) != 0:
            self.display_region_file(regfileName)
            
        

    def drop_file_cb(self, fitsimage, paths):
        fileName = paths[0]
        self.load_file(fileName)

    def cursor_cb(self, viewer, button, data_x, data_y):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel

            
            fits_x, fits_y = data_x + 1, data_y + 1
            
            dmd_x, dmd_y = self.ccd2dmd_wcs.all_pix2world(fits_x,fits_y,0)

        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
        except Exception as e:
            self.logger.warning("Bad coordinate conversion: %s" % (
                str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'

        text_coords = "RA: %s  DEC: %s  X: %.2f  Y: %.2f" % (
            ra_txt, dec_txt, fits_x, fits_y) + "\n"
        text_pix = "imX: %.2f  imY: %.2f  Value: %s" % (fits_x, fits_y, value) +"\n"
        text_mir = "dmdX: %.2f  dmdY: %.2f " %(dmd_x*3600, dmd_y*3600)
        text = text_pix + text_coords + text_mir
        self.readout.setText(text)

    def source_click_event(self):
        
        
        print("clicked, not drawn")

    def zoom_cb(self, obj):
        
        
        upleft, loright = obj.get_data_points()
        #print(obj.get_data_points())
        xmouse, ymouse = obj.get_center_pt()#obj.get_data_points()[0]
        
        region_pix = RectanglePixelRegion(PixCoord(xmouse, ymouse), 
                                            width=100, height=100)
        #canvas_reg_box = apreg.add_region(canvas=self.canvas, r=region_pix)
        self.canvas_reg_box = obj
        
        img_shape = self.AstroImage.as_hdu().data.shape
        print(img_shape[0])
        xmincut = np.max(int(xmouse)-50,0)
        ymincut = np.max(int(ymouse)-50,0)
        xmaxcut = np.minimum(int(xmouse)+50,img_shape[1])
        ymaxcut = np.minimum(int(ymouse)+50,img_shape[0])
        
        self.xmincut = xmincut
        self.ymincut = ymincut
        self.xmaxcut = xmaxcut
        self.ymaxcut = ymaxcut
        
        zoomim = AstroImage(self.AstroImage.cutout_data(xmincut,ymincut,xmaxcut,ymaxcut))
        
        self.zoom_fitsimage.set_image(zoomim)
        
        norm = simple_norm(zoomim.get_data(),stretch='log',max_percent=99, min_percent=1)
        #self.zoomax.imshow(zoomim.get_data(),cmap='gray',norm=norm, origin='lower')
        self.detect_reg_sources()
        
        #self.zoomcanvas.draw()
        
        
        
    def detect_reg_sources(self):
        
        zoomdata = self.zoom_fitsimage.get_image().get_data()
        
        mean, median, std = sigma_clipped_stats(zoomdata, sigma=2.0)
        regsources = setup_slits.single_source_detector(zoomdata, fwhm=5, threshold=3*std)
        self.regsources = regsources
        print("trying")
        
        try:
            self.zoom_canvas.delete_object(self.zobj)
            print("removed previous slit from zoom canvas")
            self.zoomax.patches.remove(self.zoomax.patches[0])
        except:
            print("failed to remove aps")
            pass
            
        #zoom_slit_reg = RectanglePixelRegion(PixCoord(regsources.loc[0,'xcentroid'],
         #                           regsources.loc[0,'ycentroid']), 20, 3)
         
        zoom_centroid_point = PointPixelRegion(PixCoord(regsources.loc[0,'xcentroid'],
                                                         regsources.loc[0,'ycentroid']),
                                                         visual=RegionVisual(marker="x"))
        
        #zcanvas_cent_point = apreg.add_region(canvas=self.zoom_canvas,r=zoom_centroid_point)
        #self.zoom_slit_rect = zoom_slit_reg
        #slit_reg.as_mpl_selector(self.zoomax)
        #zcanvas_slit_reg = apreg.add_region(canvas=self.zoom_canvas,r=zoom_slit_reg)
        
        #self.zcanvas_slit_reg = zcanvas_slit_reg
        
        positions = np.transpose((regsources['xcentroid'], regsources['ycentroid']))
        
        ### get position in main data coordinates ###
        
        main_xc = self.xmincut+regsources.loc[0,'xcentroid']
        main_yc = self.ymincut+regsources.loc[0,'ycentroid']
        self.main_xc = main_xc
        self.main_yc = main_yc
        
        
        print("centroid in main data: {}, {}".format(main_xc,main_yc))
        #print(positions)
        #apertures = CircularAperture(positions, r=4.)
        #print(apertures)
        #ap_points = apertures.plot(self.zoomax,color='magenta', lw=1.5, alpha=0.5)
        
        
    def create_dmd_save_pattern(self):
        
        
        pattern_name = self.wpattern_name.text()
        
        if pattern_name=='':
            
            pat_num = len(self.saved_patterns)+1
            pattern_name = "pattern{}".format(pat_num)
        
        if not os.path.exists("Saved_DMD_Patterns"):
            
            os.mkdir("Saved_DMD_Patterns")
            
            
        pattern_name = "Saved_DMD_Patterns/{}.png".format(pattern_name)
        print(pattern_name)
        pattern_table, redo_inds, bin_pattern = \
                        setup_slits.write_DMD_pattern(self.slitDF,save_pattern=True,
                                                      pattern_name=pattern_name)
        print(bin_pattern)

    def add_slit(self):
        
        #main_canvas_slit_rect = RectanglePixelRegion(PixCoord(self.main_xc,self.main_yc),
        #                                             20,3)
       
        #rectangle object .get_bbox() returns ((x0,y0), (x0,y1), (x1,y1), (x1,y0)), starting from
        #the lower left and proceeding clockwise
        x0,y0 = self.main_canvas_add_reg.get_bbox()[0]
        x1,y1 = self.main_canvas_add_reg.get_bbox()[2]
        
        
        slit_width = np.abs(x1-x0)
        slit_height = np.abs(y1-y0)
        print(self.main_xc, self.main_yc)
        
        self.SlitObjectList.append(self.main_canvas_add_reg)
        
        from ginga.canvas.types.layer import CompoundObject
        self.CompoundSlitObjs = CompoundObject(self.SlitObjectList)
        

        """
        if not os.path.exists("test_regions.reg"):
             # check to see if region file has already been made
             test_regfile = open("test_regions.reg",'w')
             
             head_text = ' # Region file format: DS9 version 4.1'+'\n' + \
                         'global color=green dashlist=8 3 width=1 ' + \
                         'font="helvetica 10 normal roman" select=1 highlite=1 '+ \
                         'dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1' + \
                         '\n' + 'image \n'
             
             
             test_regfile.write(head_text)
             
        else:
             # if file exists, append to it
             test_regfile = open("test_regions.reg","a")
        """
            
        # x,y,width,height,angle
        xc = np.round(self.main_xc,3)
        yc = np.round(self.main_yc,3)
        width = self.main_canvas_slit_rect.width
        height = self.main_canvas_slit_rect.height
        angle = self.main_canvas_slit_rect.angle
        
        x0 = xc-(width/2.)
        x1 = xc+(width/2.)
        y0 = yc-(width/2.)
        y1 = yc+(width/2.)
        
        #reg_text = "box({},{},{},{},{}) \n".format(xc, yc, width, height, angle)
        #test_regfile.write(reg_text)
        
        #test_regfile.close()
        
        dmd_x, dmd_y = self.ccd2dmd_wcs.all_pix2world(xc+1,yc+1,0)
        dmd_x, dmd_y = dmd_x*3600, dmd_y*3600
        
        dmd_x0, dmd_y0 = self.ccd2dmd_wcs.all_pix2world(x0+1,y0+1,0)
        dmd_x0, dmd_y0 = dmd_x0*3600, dmd_y0*3600
        dmd_x1, dmd_y1 = self.ccd2dmd_wcs.all_pix2world(x1+1,y1+1,0)
        dmd_x1, dmd_y1 = dmd_x1*3600, dmd_y1*3600

        
        # need to pretend dmd 'world' coordinates are angular,
        # so the transformation spits out the new coordinates in arcseconds.
        
     
        
        self.slit_number += 1
        new_slit_row = pd.DataFrame(data=[[self.slit_number, "nan", "nan", xc, yc, x0, y0,
                                  x1,y1, dmd_x, dmd_y, dmd_x0, dmd_y0, dmd_x1, dmd_y1]],
                                    columns=self.slitDF.columns.values)
        
        self.slitDF = pd.concat((self.slitDF,new_slit_row),axis=0).reset_index(drop=True)
        
        
        
        if self.wslit_table.rowCount()<1:
            rowPosition=0
            i = self.slitDF.index.values[-1]
            self.wslit_table.setColumnCount(15)
        
        else:
            # get the most recent slit added to the list
            self.slitDF.index.values[-1:]
            rowPosition = self.wslit_table.rowCount()
        
        self.wslit_table.insertRow(rowPosition)
        
        #for i in self.slitDF.index.values[-1:]:
        i = self.slitDF.index.values[-1] 
        obj = str(i+1)
        ra = "nan"
        dec = "nan"
        imxc = str(self.slitDF.loc[i,"image_xc"])
        imyc = str(self.slitDF.loc[i,"image_yc"])

        imx0 = str(self.slitDF.loc[i,"image_x0"])
        imy0 = str(self.slitDF.loc[i,"image_y0"])
        imx1 = str(self.slitDF.loc[i,"image_x1"])
        imy1 = str(self.slitDF.loc[i,"image_y1"])
        dmdxc = str(self.slitDF.loc[i,"dmd_xc"])
        dmdyc = str(self.slitDF.loc[i,"dmd_yc"])
        dmdx0 = str(self.slitDF.loc[i,"dmd_x0"])
        dmdy0 = str(self.slitDF.loc[i,"dmd_y0"])
        dmdx1 = str(self.slitDF.loc[i,"dmd_x1"])
        dmdy1 = str(self.slitDF.loc[i,"dmd_y1"])
        
        row_items = [obj, ra, dec, imxc, imyc, imx0, imy0, imx1, imy1,
                     dmdxc, dmdyc, dmdx0, dmdy0, dmdx1, dmdy1]
        
        for i, item in enumerate(row_items):
            self.wslit_table.setItem(rowPosition, i, QTableWidgetItem(item))
           
        
        print("added")
        
        
        #self.canvas.delete_object(self.canvas_reg_box)
        self.read_region_file()
    
    def delete_selected_obj(self, obj):
        
        self.canvas.delete_object(obj)
    

    def draw_cb(self, canvas, tag):
        
        try:
            self.canvas.delete_object(self.obj)
        except:
            pass
        
        obj = canvas.get_object_by_tag(tag)
        obj.pickable = True
        obj.add_callback('pick-down', self.pick_cb, 'down')
        #obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        #obj.add_callback('pick-hover', self.pick_cb, 'hover')
        obj.add_callback('pick-enter', self.pick_cb, 'enter')
        #obj.add_callback('pick-leave', self.pick_cb, 'leave')
        #obj.add_callback('pick-key', self.edit_cb, 'key')
        obj.add_callback('edited', self.edit_cb)
        
        self.get_center_source_from_draw(obj)
        #self.zoom_cb(obj)
        
        self.obj = obj
        
    def get_center_source_from_draw(self, obj):
        
        upleft, loright = obj.get_data_points()
        if all(upleft==loright):
            
            xmouse,ymouse = upleft
            print("try center click", xmouse, ymouse)
            x0 = xmouse-25
            x1 = xmouse+25
            y0 = ymouse-25
            y1 = ymouse+25
            
        else:
            x0,y1 = upleft
            x1, y0 = loright
            print(upleft, loright)
            
        
        #self.canvas_reg_box = obj
        
        img_shape = self.AstroImage.as_hdu().data.shape

        
        x0 = int(np.floor(x0))
        y0 = int(np.floor(y0))
        x1 = int(np.ceil(x1))
        y1 = int(np.ceil(y1))
        
        zoomim = AstroImage(self.AstroImage.cutout_data(x0,y0,x1,y1))
        
        self.zoom_fitsimage.set_image(zoomim)
        
        norm = simple_norm(zoomim.get_data(),stretch='log',max_percent=99, min_percent=1)
        
        mean, median, std = sigma_clipped_stats(zoomim.get_data(), sigma=2.0)
        regsources = setup_slits.single_source_detector(zoomim.get_data(), fwhm=5, threshold=3*std)
        self.regsources = regsources
        print("trying")

        
        positions = np.transpose((regsources['xcentroid'], regsources['ycentroid']))
        
        ### get position in main data coordinates ###
        
        main_xc = x0+regsources.loc[0,'xcentroid']
        main_yc = y0+regsources.loc[0,'ycentroid']
        
        reg_centroid_point = PointPixelRegion(center=PixCoord(main_xc,main_yc),
                                             visual=RegionVisual(marker="x"),
                                             )
        
        
        #main_canvas_add_point_reg = apreg.add_region(canvas=self.canvas,r=reg_centroid_point)
        #main_canvas_add_point_reg.add_callback('pick-key', self.delete_selected_obj, 'd')

        data_slit_reg = RectanglePixelRegion(PixCoord(main_xc,
                                    main_yc), 20, 10)
        
        self.main_canvas_slit_rect = data_slit_reg
        
        main_canvas_add_reg = apreg.add_region(canvas=self.canvas,r=data_slit_reg)
        
        
        main_canvas_add_reg.pickable = True
        main_canvas_add_reg.add_callback('pick-up',self.pick_cb, 'up')
        self.main_canvas_add_reg = main_canvas_add_reg

        
        self.fitsimage.zoom_to(2)
        self.fitsimage.set_pan(main_xc, main_yc)
        self.canvas.delete_object(obj)
        self.main_xc = main_xc
        self.main_yc = main_yc
        
        
        
        
    def zoom_draw_cb(self, canvas, tag):
        
        zobj = canvas.get_object_by_tag(tag)
        zobj.add_callback('pick-down', self.pick_cb, 'down')
        zobj.add_callback('pick-up', self.pick_cb, 'up')
        zobj.add_callback('pick-move', self.pick_cb, 'move')
        #zobj.add_callback('pick-hover', self.pick_cb, 'hover')
        zobj.add_callback('pick-enter', self.pick_cb, 'enter')
        #zobj.add_callback('pick-leave', self.pick_cb, 'leave')
        #zobj.add_callback('pick-key', self.detect_reg_sources, 'key')
        zobj.pickable = True
        zobj.add_callback('edited', self.edit_cb)
        self.zobj = zobj
        
    def set_mode_cb(self, mode, tf):
        self.logger.info("canvas mode changed (%s) %s" % (mode, tf))
        if not (tf is False):
            self.canvas.set_draw_mode(mode)
        return True
    
    def zoom_set_mode_cb(self, mode, tf):
        self.logger.info("canvas mode changed (%s) %s" % (mode, tf))
        if not (tf is False):
            self.zoom_canvas.set_draw_mode(mode)
        return True        

        #print(obj.get_data_points())
    def pick_cb(self, obj, canvas, event, pt, ptype):
        #print(obj)
        self.logger.info("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        return True

    def edit_cb(self, obj):
        self.logger.info("object %s has been edited" % (obj.kind))
        self.obj = obj
        upleft, loright = obj.get_data_points()
        x0,y1 = upleft
        x1,y0 = loright
        
        new_width = int(np.ceil(np.abs(x1-x0)))
        new_height = int(np.ceil(np.abs(y1-y0)))
        
        self.main_canvas_slit_rect.width = new_width
        self.main_canvas_slit_rect.height = new_height
        print(self.main_canvas_slit_rect.width)
        #self.zoom_cb(obj)
        return True
    
    def zoom_edit_cb(self, obj):
        self.logger.info("object %s has been edited" % (obj.kind))
        self.zobj = obj
        self.zoom_cb(obj)
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
