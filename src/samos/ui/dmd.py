"""
SAMOS DMD tk Frame Class
"""
import copy
import csv
from datetime import datetime
import glob
import logging
from matplotlib import pyplot as plt
import numpy as np
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import twirl
from urllib.parse import urlencode

from astropy.coordinates import SkyCoord, FK4
from astroquery.gaia import Gaia
from astropy.io import fits, ascii
from astroquery.simbad import Simbad
from astropy.stats import sigma_clipped_stats, SigmaClip
from astropy import units as u
from astropy import wcs
from astropy.wcs.utils import fit_wcs_from_points
from ginga.util import iqcalc
from ginga.AstroImage import AstroImage
from ginga.util import ap_region
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.util.loader import load_data
from ginga.misc import log
from ginga import colors as gcolors
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
import pandas as pd
from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder
from PIL import Image, ImageTk
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
from tkinter import ttk

from samos.ccd.Class_CCD_dev import Class_Camera
from samos.dmd.pixel_mapping import Coord_Transform_Helpers as CTH
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.pattern_helpers.Class_DMDGroup import DMDGroup
from samos.dmd.Class_DMD_dev import DigitalMicroMirrorDevice
from samos.motors.Class_PCM import Class_PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.astrometry.skymapper import skymapper_interrogate
from samos.astrometry.tk_class_astrometry_V5 import Astrometry
from samos.astrometry.panstarrs.image import PanStarrsImage as PS_image
from samos.astrometry.panstarrs.catalog import PanStarrsCatalog as PS_table
from samos.hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks
from samos.system import WriteFITSHead as WFH
from samos.system.SAMOS_Functions import Class_SAMOS_Functions as SF
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.system.SlitTableViewer import SlitTableView as STView
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


class DMDPage(ttk.Frame):
    """ to be written """

    def __init__(self, parent, container, **kwargs):
        """ to be written """

        super().__init__(container)
        self.convert = kwargs['convert']

        label = tk.Label(self, text="DMD Page", font=('Times', '20'))
        label.pack(pady=0, padx=0)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Startup Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.frame_startup = tk.Frame(self, background="light gray")
        self.frame_startup.place(x=4, y=4, anchor="nw", width=290, height=396)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       DMD Initialize
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # dmd.initialize()
        button_Initialize = tk.Button(
            self.frame_startup, text="Initialize", bd=3, command=self.dmd_initialize)
        button_Initialize.place(x=4, y=4)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       Load Basic Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        button_Whiteout = tk.Button(
            self.frame_startup, text="Blackout", bd=3, command=self.dmd_blackout)
        button_Whiteout.place(x=4, y=34)
        button_Blackout = tk.Button(
            self.frame_startup, text="Whiteout", bd=3, command=self.dmd_whiteout)
        button_Blackout.place(x=140, y=34)
        button_Checkerboard = tk.Button(
            self.frame_startup, text="Checkerboard", bd=3, command=self.dmd_checkerboard)
        button_Checkerboard.place(x=4, y=64)
        button_Invert = tk.Button(
            self.frame_startup, text="Invert", bd=3, command=self.dmd_invert)
        button_Invert.place(x=4, y=94)
        button_antInvert = tk.Button(
            self.frame_startup, text="AntInvert", bd=3, command=self.dmd_antinvert)
        button_antInvert.place(x=140, y=94)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       Load Custom Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        button_edit = tk.Button(self.frame_startup,
                                text="Edit DMD Map",
                                command=self.BrowseMapFiles)
        button_edit.place(x=4, y=140)

        button_load_map = tk.Button(self.frame_startup,
                                    text="Load DMD Map",
                                    command=self.LoadMap)
        button_load_map.place(x=140, y=140)

        label_filename = tk.Label(self.frame_startup, text="Current DMD Map")
        label_filename.place(x=4, y=170)
        self.str_map_filename = tk.StringVar()
        self.textbox_filename = tk.Text(self.frame_startup, height=1, width=22)
        self.textbox_filename.place(x=120, y=170)

        """ Define custom slit """

        label_x0 = tk.Label(self.frame_startup, text="x0")
        label_x0.place(x=5, y=200)
        self.x0 = tk.IntVar()
        self.x0.set(540)
        self.entry_x0 = tk.Entry(
            self.frame_startup, width=4, textvariable=self.x0)
        self.entry_x0.place(x=30, y=198)

        label_x1 = tk.Label(self.frame_startup, text="x1")
        label_x1.place(x=85, y=200)
        self.x1 = tk.IntVar()
        self.x1.set(540)
        entry_x1 = tk.Entry(self.frame_startup, width=4, textvariable=self.x1)
        entry_x1.place(x=110, y=198)

        label_y0 = tk.Label(self.frame_startup, text="y0")
        label_y0.place(x=150, y=200)
        self.y0 = tk.IntVar()
        self.y0.set(1024)
        entry_y0 = tk.Entry(self.frame_startup, width=4, textvariable=self.y0)
        entry_y0.place(x=175, y=198)


        label_y1 = tk.Label(self.frame_startup, text="y1")
        label_y1.place(x=210, y=200)
        self.y1 = tk.IntVar()
        self.y1.set(1024)
        entry_y1 = tk.Entry(self.frame_startup, width=4, textvariable=self.y1)
        entry_y1.place(x=235, y=198)

        button_add_slit = tk.Button(self.frame_startup,
                                    text="Add",
                                    command=self.AddSlit)
        button_add_slit.place(x=4, y=260)

        button_save_map = tk.Button(self.frame_startup,
                                    text="Save",
                                    command=self.SaveMap)
        button_save_map.place(x=104, y=260)

        button_push_slit = tk.Button(self.frame_startup,
                                     text="Push",
                                     command=self.PushCurrentMap)
        button_push_slit.place(x=204, y=260)


        """ Load Slit Table """
        button_load_slits = tk.Button(self.frame_startup,
                                      text="Load Slit List",
                                      command=self.LoadSlits)
        button_load_slits.place(x=140, y=320)

        # gridfnam = tk.StringVar()
        label_filename_slits = tk.Label(
            self.frame_startup, text="Current Slit List")
        label_filename_slits.place(x=4, y=350)
        # params["gridfnam"] = gridfnam
        # print(gridfnam)
        self.str_filename_slits = tk.StringVar()
        self.textbox_filename_slits = tk.Text(
            self.frame_startup, height=1, width=20)
        self.textbox_filename_slits.place(x=120, y=350)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       Display Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        self.canvas = tk.Canvas(self, width=300, height=270, bg="dark gray")
        self.canvas.place(x=300, y=4)
        """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       HADAMARD Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        """
        self.Hadamard_frame = tk.Frame(self, width=300, height=400, bg="gray")
        self.Hadamard_frame.place(x=605, y=4)
        self.HadamardConf_LabelFrame = tk.LabelFrame(
            self.Hadamard_frame, width=292, height=392, text="Hadamard Configuration")
        self.HadamardConf_LabelFrame.place(x=4, y=4)

        """ Type of Matrix: S or H?"""
# ===#====
        self.SHMatrix_Checked = tk.StringVar(None, "S")
        btn1 = tk.Radiobutton(self.HadamardConf_LabelFrame, text="S Matrix", padx=20,
                              variable=self.SHMatrix_Checked, value="S", command=self.set_SH_matrix)
        btn2 = tk.Radiobutton(self.HadamardConf_LabelFrame, text="H Matrix", padx=20,
                              variable=self.SHMatrix_Checked, value="H", command=self.set_SH_matrix)
# >>>>>>> Stashed changes
        btn1.place(x=4, y=5)
        btn2.place(x=4, y=30)  # 150, y=20)

        """ Order of H Matrix?"""
        label_order = tk.Label(self.HadamardConf_LabelFrame,
                               text="Order: ", bd=4)  # , font=("Arial", 24))
# <<<#<<<< Updated upstream
        label_order.place(x=140, y=14)

        """ Order of S Matrix?"""
# >>>>>>> Stashed changes
        self.Sorders = (3, 7, 11, 15, 19, 23, 31, 35, 43,
                        47, 63, 71, 79, 83, 103, 127, 255)
        self.Sorder = tk.IntVar()
        self.Sorder.set(self.Sorders[1])
        self.order = self.Sorder.get()
        self.Sorder_menu = tk.OptionMenu(
            self.HadamardConf_LabelFrame, self.Sorder, *self.Sorders, command=self.set_SH_matrix)
# <<<#<<<< Updated upstream
        self.Sorder_menu.place(x=190, y=15)

        """ Order of H Matrix?"""
        self.Horders = (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
        self.Horder = tk.IntVar()
        self.Horder.set(self.Horders[1])
        self.order = self.Sorder.get()
        self.Horder_menu = tk.OptionMenu(
            self.HadamardConf_LabelFrame, self.Horder, *self.Horders, command=self.set_SH_matrix)
        self.Horder_menu.place(x=1090, y=29)
# =======
        self.Sorder_menu.place(x=190, y=19)
        #

        """ Slit Width?"""
        label_width = tk.Label(self.HadamardConf_LabelFrame,
                               text="Slit Width: ", bd=4)  # , font=("Arial", 24))
        label_width.place(x=4, y=74)
        self.entrybox_width = tk.Entry(self.HadamardConf_LabelFrame, width=3)
        self.entrybox_width.bind("<Return>", self.calculate_field_width)
        self.entrybox_width.insert(0, "3")
        self.entrybox_width.place(x=80, y=73)

        """ Slit Length?"""
        label_length = tk.Label(
            self.HadamardConf_LabelFrame, text="Length:", bd=4)  # , font=("Arial", 24))
        label_length.place(x=154, y=74)
        self.entrybox_length = tk.Entry(self.HadamardConf_LabelFrame, width=4)
        self.entrybox_length.bind("<Return>", self.calculate_field_width)
        self.entrybox_length.insert(0, "256")
        self.entrybox_length.place(x=230, y=73)

        """ Center Field?"""
        label_center_x = tk.Label(
            self.HadamardConf_LabelFrame, text="Center: Xo", bd=4)  # , font=("Arial", 24))
        label_center_x.place(x=4, y=111)
        self.entrybox_center_x = tk.Entry(
            self.HadamardConf_LabelFrame, width=4)
        self.entrybox_center_x.insert(0, "540")
        self.entrybox_center_x.place(x=80, y=110)
        # , font=("Arial", 24))
        label_center_y = tk.Label(
            self.HadamardConf_LabelFrame, text="Center: Yo", bd=4)
        label_center_y.place(x=154, y=111)
        self.entrybox_center_y = tk.Entry(
            self.HadamardConf_LabelFrame, width=5)
        self.entrybox_center_y.insert(0, "1024")
        self.entrybox_center_y.place(x=230, y=110)

        """ Field With?"""
        label_field_width = tk.Label(
            self.HadamardConf_LabelFrame, text="Width:", bd=4)  # , font=("Arial", 24))
        label_field_width.place(x=4, y=148)
        self.field_width_ = tk.StringVar()
        self.field_width_.set("21")
        self.textbox_field_width = tk.Text(
            self.HadamardConf_LabelFrame,  height=1, width=4, bg="red", fg="white", font=BIGFONT_15)
        self.textbox_field_width.place(x=70, y=150)
        self.textbox_field_width.insert(tk.INSERT, "21")

        """ GENERATE """
        self.button_Generate = tk.Button(self.HadamardConf_LabelFrame, text="GENERATE", bd=3, bg='#A877BA', font=BIGFONT,
                                         command=self.HTS_generate)
        self.button_Generate.place(x=70, y=150)  # 80)
        self.textbox_masknames = tk.Text(
            self.HadamardConf_LabelFrame, height=1, width=37)
        self.textbox_masknames.place(x=4, y=190)  # 220)

        """ Rename?"""
        button_save_masks = tk.Label(self.HadamardConf_LabelFrame,
                                     text="Rename:")
        button_save_masks.place(x=4, y=213)  # 243)
        self.entrybox_newmasknames = tk.Entry(
            self.HadamardConf_LabelFrame, width=25)
        self.entrybox_newmasknames.bind("<Return>", self.rename_masks_file)
        self.entrybox_newmasknames.place(x=70, y=213)  # 243)

        self.Hadamard_RADEC_frame = tk.Frame(
            self.HadamardConf_LabelFrame, width=280, height=125, bg="gray")
        self.Hadamard_RADEC_frame.place(x=0, y=245)  # 275)
        """ Target RADEC?"""
        label_target_RA = tk.Label(
            self.Hadamard_RADEC_frame, text="Target RA:", bd=4)  # , font=("Arial", 24))
        label_target_RA.place(x=4, y=4)
        self.entrybox_target_RA = tk.Entry(
            self.Hadamard_RADEC_frame, width=14)
        self.entrybox_target_RA.insert(0, "01.234567")
        self.entrybox_target_RA.place(x=80, y=4)

        label_target_DEC = tk.Label(
            self.Hadamard_RADEC_frame, text="Target DEC:", bd=4)  # , font=("Arial", 24))
        label_target_DEC.place(x=4, y=34)
        self.entrybox_target_DEC = tk.Entry(
            self.Hadamard_RADEC_frame, width=14)
        self.entrybox_target_DEC.insert(0, "01.234567")
        self.entrybox_target_DEC.place(x=80, y=34)

        """ GENERATE FROM RADEC"""
        self.button_Generate_from_RADEC = tk.Button(self.Hadamard_RADEC_frame, text="GENERATE FROM RADEC", bd=3, bg='#A877BA', font=BIGFONT_20,
                                                    command=self.HTS_generate_from_RADEC)
        self.button_Generate_from_RADEC.place(x=10, y=64)

    def HTS_generate_from_RADEC(self):
        """ Generates HTS mask centered on RADEC coordinates
            - requires WCS (check on existence has to be written)
            - no check on the RADEC being inside the field (to be written)
            - RADEC format in decimal degrees (no HH:MM:SS, dd:mm:ss)
        """
        # get AR and DEC from input fields
        dec_HTS_center = float(self.entrybox_target_DEC.get())
        ra_HTS_center = float(self.entrybox_target_RA.get())

        # convert radec->pixels using WCS
        # from https://gist.github.com/barentsen/548f88ef38f645276fccea1481c76fc3
        ad = np.array([[ra_HTS_center, dec_HTS_center]]).astype(float)
        x_CCD_HTS_center, y_CCD_HTS_center = WCS_global.all_world2pix(ad, 0)[0]

        # convert pixels -> DMD mirrors
        x_DMD_HTS_center, y_DMD_HTS_center = self.convert.CCD2DMD(
            int(x_CCD_HTS_center), int(y_CCD_HTS_center))

        # refresh entrybox field
        self.entrybox_center_x.delete(0, tk.END)
        self.entrybox_center_x.insert(0, int(x_DMD_HTS_center))
        self.entrybox_center_y.delete(0, tk.END)
        self.entrybox_center_y.insert(0, int(y_DMD_HTS_center))

        # generate mask
        self.HTS_generate()


    def rename_masks_file(self, event=None):
        """ rename the mask file, only the part starting with 'mask' """

        oldfilename_masks = self.textbox_masknames.get("1.0", tk.END)

        # => find all positions of the '_' string in the filename
        i_ = [x for x, v in enumerate(oldfilename_masks) if v == '_']
        old_string = oldfilename_masks[i_[0]+1:i_[1]]
        # second = oldfilename_masks[i_[1]]

        old = str(oldfilename_masks[0:i_[-1]])
        new_string = self.entrybox_newmasknames.get()
        mask_set_dir = get_data_file('hadamard.mask_sets')
        file_names = mask_set_dir.glob('{}+*.bmp'.format(old))
        files = sorted(file_names)
        for ifile in range(len(files)):
            path, tail = os.path.split(files[ifile])
            oldName = files[ifile]
            newName = os.path.join(path, tail.replace(old_string, new_string))
            os.rename(oldName, newName)
        self.textbox_masknames.delete("1.0", tk.END)
        self.textbox_masknames.insert(
            tk.END, oldfilename_masks[0:-1].replace(old_string, new_string))
        self.entrybox_newmasknames.delete(0, tk.END)


    def calculate_field_width(self, event=None):
        """ calculate_field_width """
        self.textbox_field_width.delete("1.0", tk.END)
        self.field_width = int(self.entrybox_width.get()) * self.order
        self.textbox_field_width.insert(tk.INSERT, str(self.field_width))

    def set_SH_matrix(self, event=None):
        """ set_SH_matrix """
        if self.SHMatrix_Checked.get() == "S":
            self.Sorder_menu.place(x=190, y=19)
            self.Horder_menu.place(x=1900, y=19)
            self.order = self.Sorder.get()
            self.mask_arrays = np.arange(0, self.order)
        else:
            self.Sorder_menu.place(x=1900, y=19)
            self.Horder_menu.place(x=190, y=19)
            self.order = self.Horder.get()
            a = tuple(['a'+str(i), 'b'+str(i)] for i in range(1, 4))
            self.mask_arrays = [inner for outer in zip(*a) for inner in outer]
        self.calculate_field_width()
        print(self.order)
        print(self.mask_arrays)


    def HTS_generate(self):
        """ HTS_generate """
        DMD_size = (1080, 2048)
        matrix_type = self.SHMatrix_Checked.get()  # Two options, H or S
        # e.g. 15 Order of the hadamard matrix (or S matrix)
        order = self.order
        """note the flipping of xy when we talk to the DMD"""
        Xo, Yo = int(self.entrybox_center_y.get()), int(
            self.entrybox_center_x.get())
        # DMD_size[1]/2, DMD_size[0]/2   # Coordinates on the DMD to center the Hadamard matrix around

        # 4 # Slit width in number of micromirrors
        slit_width = int(self.entrybox_width.get())
        # 4 # Slit length in number of micromirrors
        slit_length = int(self.entrybox_length.get())

        # folder = 'C:/Users/Kate/Documents/hadamard/mask_sets/' # Change path to fit user needs

#        folder = os.path.join(local_dir,'Hadamard','mask_sets',os.path.sep)
        # above line was not allowing to write data
        folder = get_data_file('hadamard.mask_sets')
        if matrix_type == 'S':
            mask_set, matrix = make_S_matrix_masks(
                order, DMD_size, slit_width, slit_length, Xo, Yo, folder)  # mask_set.shape (1080,2048,7)
#            name = 'S'+str(order)+'_'+str(slit_width)+'w_mask_1-'+str(order)+'.bmp'
            name = 'S'+str(order)+'_mask_'+str(slit_width) + \
                'w_' + "{:03d}".format(order) + '.bmp'
        if matrix_type == 'H':
            mask_set_a, mask_set_b, matrix = make_H_matrix_masks(
                order, DMD_size, slit_width, slit_length, Xo, Yo, folder)
#            name = str(matrix_type)+str(order)+'_'+str(slit_width)+'w_mask_ab1-'+str(order)+'.bmp'
            name = str(matrix_type)+str(order)+'_mask_' + \
                str(slit_width) + 'w_ab_' + "{:03d}".format(order) + '.bmp'
        self.textbox_masknames.delete("1.0", tk.END)
        self.textbox_masknames.insert(tk.INSERT, str(name))
        self.entrybox_newmasknames.delete(0, tk.END)
        self.entrybox_newmasknames.insert(
            tk.INSERT, str(name[0:name.rfind("_")]))
        # self.textbox_filename_masks.delete("1.0", tk.END)
        # self.textbox_filename_masks.insert(tk.INSERT,str(name))


    def dmd_initialize(self):
        """ dmd_initialize """
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("none")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "none")


    def dmd_whiteout(self):
        """ sets all mirrors "ON" as seen by the imaging channel
            from the point of view of the DMD with its current orientation, all mirrors are "OFF" """
        DMD.apply_blackout()
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "whiteout_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("whiteout")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "whiteout")

    def dmd_blackout(self):
        """ sets all mirrors "OFF" as seen by the imaging channel
            from the point of view of the DMD with its current orientation, all mirrors are "ON" """
        DMD.apply_whiteout()
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "blackout_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("blackoutout")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "blackout")

    def dmd_checkerboard(self):
        """ dmd_checkerboard """
        DMD.apply_checkerboard()
        # global img
        shutil.copy(os.path.join(dir_DMD, "checkerboard.png"),
                    os.path.join(dir_DMD, "current_dmd_state.png"))
        time.sleep(1)
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("checkerboard")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "checkerboard")

    def dmd_invert(self):
        """ dmd_invert """
        DMD.apply_invert()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        # image=image_map.convert("L")
        # image_invert = ImageOps.invert(image)
        # image_invert.save(dir_DMD+ "/current_dmd_state.png")
        # global img
        # img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
        # self.img= ImageTk.PhotoImage(image_invert)
        # Add image to the Canvas Items
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        # self.str_map_filename.set("checkerboard")
        self.textbox_filename.insert(tk.INSERT, " inverted ")


#        # global img
#        img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
#        #Add image to the Canvas Items
#        self.canvas.create_image(104,128,image=img)

    def dmd_antinvert(self):
        """ dmd_antinvert """
        DMD.apply_antinvert()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()

    def BrowseMapFiles(self):
        """ BrowseMapFiles """
        self.textbox_filename.delete('1.0', tk.END)
        filename = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.csv.maps"),
                                                 title="Select a File",
                                                 filetypes=(("Text files",
                                                             "*.csv"),
                                                            ("all files",
                                                             "*.*")))
        if sys.platform != "win32":
            subprocess.call(['open', '-a', 'TextEdit', filename])
        else:        
            cmd = 'start "excel" "%s"' %(filename)
            os.system(cmd)
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)
        self.str_map_filename.set(tail)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load DMD map file
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def LoadMap(self):
        """ LoadMap """
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.csv.maps"),
                                                 title="Select a File",
                                                 filetypes=(("Text files",
                                                             "*.csv"),
                                                            ("all files",
                                                             "*.*")))
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)

        main_fits_header.set_param("dmdmap", tail)

        myList = []

        with open(filename, 'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        # print(myList)
        file.close()

        for i in range(len(myList)):
            print("Row " + str(i) + ": " + str(myList[i]))

        test_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]), int(
                myList[i][2]):int(myList[i][3])] = int(myList[i][4])

        try:
            DMD.apply_shape(test_shape)
        except:
            print("DMD non connected")

        """ CREATE THE astropy regions file in PIXEL UNITS """

        # 1. instantiate the convert class
        c = CONVERT()

        f = open(get_data_file("regions.pixels", tail[:-3]+'reg'), 'w')

        # 2. loop over the lines to create ds9 region files
        header = "# Region file format: DS9 astropy/regions\nglobal edit=1 width=1 font=Sans Serif fill=0 color=red\nimage"
        f.write(header + '\n')
        for i in range(len(myList)):
            x0, y0 = c.DMD2CCD(float(myList[i][0]), float(myList[i][2]))
            x1, y1 = c.DMD2CCD(float(myList[i][1]), float(myList[i][3]))
            xc = (x0 + x1)/2.
            yc = (y0 + y1)/2.
            dx = x1-x0
            dy = y1-y0
            output_string = "box("+str(xc)+","+str(yc) + \
                ","+str(dx)+","+str(dy)+",0)"
            print(output_string)
            f.write(output_string + '\n')
        f.close()

        self.m = MainPage(None, None)
        self.m.textbox_filename_regfile_xyAP.insert(tk.END, tail[:-3]+'reg')
        # Create a photoimage object of the image in the path
        # Load an image in the script
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104, 128, image=self.img)
        image_map.close()

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load Slit file
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def LoadSlits(self):
        """ LoadSlits """
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename_slits = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.csv.slits"),
                                                       title="Select a File",
                                                       filetypes=(("Text files",
                                                                   "*.csv"),
                                                                  ("all files",
                                                                   "*.*")))
        head, tail = os.path.split(filename_slits)
        self.textbox_filename_slits.insert(tk.END, tail)
        main_fits_header.set_param("dmdmap", tail)
        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index), int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        self.slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in table.index:
            self.slit_shape[x1[i]:x2[i], y1[i]:y2[i]] = 0
        DMD.apply_shape(self.slit_shape)

        # Create a photoimage object of the image in the path
        # Load the image
        # global img
        # self.img = None
#        image_map = Image.open(local_dir + "/current_dmd_state.png")
#        self.img= ImageTk.PhotoImage(image_map)
#         image_map.close()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()

        # Add image to the Canvas Items
        # print('img =', self.img)
        # self.canvas.create_image(104,128,image=self.img)

    def AddSlit(self):
        """
        # 1. read the current filename
        # 2. open the .csv file
        # 3. add the slit
        """

        # 1. read the current filename
        filename_in_text = self.textbox_filename.get("1.0",'end-1c')
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)
        
        myList = []
        # 2. that's just a string! check if file exists to load what you already inherited
        if os.path.isfile(self.map_filename) == True: 
            with open(self.map_filename, 'r') as file:
                myFile = csv.reader(file)
                for row in myFile:
                    myList.append(row)
            file.close()
 
        # 3. add the slit
        # set the four corners of the aperture
#        row = [str(int(self.x0.get())), str(int(self.y0.get())), str(
#            int(self.x1.get())), str(int(self.y1.get())), "0"]
        row = [str(int(self.x0.get())), str(int(self.x1.get())), str(
            int(self.y0.get())), str(int(self.y1.get())), "0"]
        myList.append(row)
        self.map = myList

    def SaveMap(self):
        """ SaveMap """
        print("Saving Map")
        filename_in_text = self.textbox_filename.get("1.0",'end-1c')
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)
        pandas_map = pd.DataFrame(self.map)
        pandas_map.to_csv(self.map_filename, index=False, header=None)
        print("Map Saved")
        
    def PushCurrentMap(self):
        """ Push to the DMD the file in Current DMD Map Textbox """

        filename_in_text = self.textbox_filename.get("1.0",'end-1c')
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)

        myList = []
        with open(self.map_filename, 'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        file.close()

        # for i in range(len(myList)):
        #    print("Row " + str(i) + ": " + str(myList[i]))

        test_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]), int(
                myList[i][2]):int(myList[i][3])] = int(myList[i][4])

        DMD.apply_shape(test_shape)

        # Create a photoimage object of the image in the path
        # Load an image in the script
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104, 128, image=self.img)
        image_map.close()

    def enter_command(self):
        """ enter_command """
        print('command entered:', self.Command_string.get())
        # convert StringVar to string
        t = DMD.send_command_string(self.Command_string.get())
        self.Echo_String.set(t)
        print(t)

#    def client_exit(self):
#        print("destroy")
#        self.destroy()

    def create_menubar(self, parent):
        """ create_menubar """
        parent.geometry("910x407")
        if sys.platform == "win32":
            parent.geometry("910x425")
        parent.title("SAMOS DMD Controller")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame("DMDPage"))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame("CCD2DMDPage"))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame("CCDPage"))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame("SOARPage"))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame("MainPage"))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame("ETCPage"))
        filemenu.add_command(label="Exit", command=parent.quit)

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame("GSPage"))        
        help_menu.add_separator()

        return menubar
