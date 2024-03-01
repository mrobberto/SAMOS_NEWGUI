"""
SAMOS DMD tk Frame Class
"""
import csv
import logging
import numpy as np
import os
from pathlib import Path
import shutil
import subprocess
import sys

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
from PIL import Image, ImageTk, ImageOps
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
from tkinter import ttk

from samos.ccd.Class_CCD_dev import Class_Camera
from samos.dmd.pixel_mapping import Coord_Transform_Helpers as CTH
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.pattern_helpers.Class_DMDGroup import DMDGroup
from samos.dmd import DigitalMicroMirrorDevice
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

from .common_frame import SAMOSFrame


class DMDPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "DMD Control", **kwargs)
        
        # Set up basic frames
        button_frame = tk.LabelFrame(self.main_frame, text="Controls", font=BIGFONT, borderwidth=3)
        button_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        display_frame = tk.Frame(self.main_frame, borderwidth=3)
        display_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        hadamard_frame = tk.Frame(self.main_frame, borderwidth=3)
        hadamard_frame.grid(row=0, column=2, sticky=TK_STICKY_ALL)

        # dmd.initialize()
        button_Initialize = tk.Button(button_frame, text="Initialize", command=self.dmd_initialize)
        button_Initialize.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Basic Patterns
        tk.Label(button_frame, text="Basic Patterns:").grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        button_Whiteout = tk.Button(button_frame, text="Blackout", bd=3, command=self.dmd_whiteout)
        button_Whiteout.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        button_Blackout = tk.Button(button_frame, text="Whiteout", bd=3, command=self.dmd_blackout)
        button_Blackout.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        button_Checkerboard = tk.Button(button_frame, text="Checkerboard", bd=3, command=self.dmd_checkerboard)
        button_Checkerboard.grid(row=3, column=2, sticky=TK_STICKY_ALL)
        button_Invert = tk.Button(button_frame, text="Invert", bd=3, command=self.dmd_invert)
        button_Invert.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        button_antInvert = tk.Button(button_frame, text="AntInvert", bd=3, command=self.dmd_antinvert)
        button_antInvert.grid(row=4, column=2, sticky=TK_STICKY_ALL)

        # Custom Patterns
        tk.Label(button_frame, text="Custom Patterns:").grid(row=6, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        button_edit = tk.Button(button_frame, text="Edit DMD Map", command=self.browse_map)
        button_edit.grid(row=7, column=0, sticky=TK_STICKY_ALL)
        button_load_map = tk.Button(button_frame, text="Load DMD Map", command=self.load_map)
        button_load_map.grid(row=7, column=2, sticky=TK_STICKY_ALL)
        label_filename = tk.Label(button_frame, text="Current DMD Map")
        label_filename.grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.str_map_filename = tk.StringVar()
        tk.Label(button_frame, textvariable=self.str_map_filename).grid(row=8, column=1, columnspan=2, sticky=TK_STICKY_ALL)

        # Custom Slit
        tk.Label(button_frame, text="Custom Slit:").grid(row=10, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        custom_frame = tk.Frame(button_frame, borderwidth=0)
        custom_frame.grid(row=11, column=0, rowspan=2, columnspan=3, sticky=TK_STICKY_ALL)
        tk.Label(custom_frame, text="x0").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.x0 = tk.IntVar(self, 540)
        tk.Entry(custom_frame, textvariable=self.x0).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        tk.Label(custom_frame, text="y0").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.y0 = tk.IntVar(self, 1024)
        tk.Entry(custom_frame, textvariable=self.y0).grid(row=0, column=3, sticky=TK_STICKY_ALL)

        tk.Label(custom_frame, text="x1").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.x1 = tk.IntVar(self, 540)
        tk.Entry(custom_frame, textvariable=self.x1).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        tk.Label(custom_frame, text="y1").grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.y1 = tk.IntVar(self, 1024)
        tk.Entry(custom_frame, textvariable=self.y1).grid(row=1, column=3, sticky=TK_STICKY_ALL)

        # Slit Buttons
        tk.Button(button_frame, text="Add", command=self.AddSlit).grid(row=13, column=0, sticky=TK_STICKY_ALL)
        tk.Button(button_frame, text="Push", command=self.PushCurrentMap).grid(row=13, column=1, sticky=TK_STICKY_ALL)
        tk.Button(button_frame, text="Save", command=self.SaveMap).grid(row=13, column=2, sticky=TK_STICKY_ALL)

        # Load Slit
        tk.Button(button_frame, text="Load Slit List", command=self.load_slits).grid(row=15, column=2, sticky=TK_STICKY_ALL)
        tk.Label(button_frame, text="Current Slit List").grid(row=16, column=0, sticky=TK_STICKY_ALL)
        self.str_filename_slits = tk.StringVar()
        t = tk.Entry(button_frame, textvariable=self.str_filename_slits)
        t.grid(row=16, column=1, columnspan=2, sticky=TK_STICKY_ALL)

        # Canvas display for DMD pattern
        self.canvas = tk.Canvas(display_frame, width=300, height=270, bg="dark gray")
        self.canvas.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        hadamard_conf_frame = tk.LabelFrame(hadamard_frame, text="Hadamard Configuration")
        hadamard_conf_frame.grid(row=0, column=0, rowspan=4, sticky=TK_STICKY_ALL)

        # Matrix Type and order
        self.SHMatrix_Checked = tk.StringVar(self, "S")
        tk.Radiobutton(hadamard_conf_frame, text="S Matrix", variable=self.SHMatrix_Checked, value="S", 
                       command=self.set_SH_matrix).grid(row=0, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        tk.Radiobutton(hadamard_conf_frame, text="H Matrix", variable=self.SHMatrix_Checked, value="H", 
                       command=self.set_SH_matrix).grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Order: ").grid(row=0, column=2, rowspan=2, sticky=TK_STICKY_ALL)
        self.Sorders = (3, 7, 11, 15, 19, 23, 31, 35, 43, 47, 63, 71, 79, 83, 103, 127, 255)
        self.Horders = (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
        self.order = tk.IntVar(self, self.Sorders[1])
        self.order_menu = ttk.OptionMenu(hadamard_conf_frame, self.order, *self.Sorders, command=self.set_SH_matrix)
        self.order_menu.grid(row=0, column=3, rowspan=2, sticky=TK_STICKY_ALL)
        
        # Slit Dimensions
        tk.Label(hadamard_conf_frame, text="Slit Width: ").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.slit_width = tk.IntVar(self, 3)
        box = tk.Entry(hadamard_conf_frame, textvariable=self.slit_width)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Length:").grid(row=3, column=3, sticky=TK_STICKY_ALL)
        self.slit_length = tk.IntVar(self, 256)
        box = tk.Entry(hadamard_conf_frame, textvariable=self.slit_length)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=4, sticky=TK_STICKY_ALL)

        # Field Centre
        tk.Label(hadamard_conf_frame, text="Centre:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Xo").grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.slit_xc = tk.IntVar(self, 540)
        tk.Entry(hadamard_conf_frame, textvariable=self.slit_xc).grid(row=4, column=2, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Yo").grid(row=4, column=3, sticky=TK_STICKY_ALL)
        self.slit_yc = tk.IntVar(self, 1045)
        tk.Entry(hadamard_conf_frame, textvariable=self.slit_yc).grid(row=4, column=4, sticky=TK_STICKY_ALL)

        # Field Width
        tk.Label(hadamard_conf_frame, text="Width:").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.field_width = tk.IntVar(self, 21)
        txt = tk.Entry(hadamard_conf_frame,  textvariable=self.field_width, bg="red", fg="white", font=BIGFONT_15)
        txt.grid(row=5, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        
        # Generate
        b = tk.Button(hadamard_conf_frame, text="GENERATE", bg='#A877BA', font=BIGFONT, command=self.generate_hts)
        b.grid(row=6, column=0, columnspan=3, sticky=TK_STICKY_ALL)

        # Name / Rename
        tk.Label(hadamard_conf_frame, text="Name:").grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.mask_name = tk.StringVar(self, "")
        tk.Label(hadamard_conf_frame, textvariable=self.mask_name).grid(row=8, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        rename_button_text = "Rename '{}' to:".format(self.mask_name.get())
        self.rename_button = tk.Button(hadamard_conf_frame, text=rename_button_text, command=self.rename_masks_file)
        self.rename_button.grid(row=9, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.rename_value = tk.StringVar(self, "")
        e = tk.Entry(hadamard_conf_frame, textvariable=self.rename_value)
        e.grid(row=9, column=2, columnspan=3, sticky=TK_STICKY_ALL)

        # Ra/Dec
        radec_frame = tk.LabelFrame(hadamard_frame, text="Generate from RA/DEC")
        radec_frame.grid(row=4, column=0, rowspan=2, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="Target RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.target_ra = tk.DoubleVar(self, 1.234567)
        tk.Entry(radec_frame, textvariable=self.target_ra).grid(row=0, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="(decimal degrees)").grid(row=0, column=3, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="Target DEC:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.target_dec = tk.DoubleVar(self, 1.234567)
        tk.Entry(radec_frame, textvariable=self.target_ra).grid(row=1, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="(decimal degrees)").grid(row=1, column=3, sticky=TK_STICKY_ALL)
        b = tk.Button(radec_frame, text="GENERATE", bg='#A877BA', font=BIGFONT_20, command=self.generate_hts_from_radec)
        b.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)


    def generate_hts_from_radec(self):
        """ 
        Generates HTS mask centered on RADEC coordinates
        
        - requires WCS (check on existence has to be written)
        - no check on the RADEC being inside the field (to be written)
        - RADEC format in decimal degrees (no HH:MM:SS, dd:mm:ss)
        """
        # get AR and DEC from input fields
        dec_HTS_center = self.target_dec.get()
        ra_HTS_center = self.target_ra.get()

        # convert radec->pixels using WCS
        # from https://gist.github.com/barentsen/548f88ef38f645276fccea1481c76fc3
        ad = np.array([[ra_HTS_center, dec_HTS_center]]).astype(float)
        x_CCD_HTS_center, y_CCD_HTS_center = WCS_global.all_world2pix(ad, 0)[0]

        # convert pixels -> DMD mirrors
        x_DMD_HTS_center, y_DMD_HTS_center = self.convert.CCD2DMD(int(x_CCD_HTS_center), int(y_CCD_HTS_center))

        # refresh entrybox field
        self.slit_xc.set(int(x_DMD_HTS_center))
        self.slit_yc.set(int(y_DMD_HTS_center))

        # generate mask
        self.generate_hts()


    def rename_masks_file(self, event=None):
        """ rename the mask file, only the part starting with 'mask' """

        old_mask_name = self.mask_name.get()
        replacement_part = old_mask_name.strip().split("_")[1]
        new_mask_name = self.rename_value.get()
        self.rename_button.config(text="Rename '{}' to:".format(new_mask_name.get()))

        mask_set_dir = get_data_file('hadamard.mask_sets')
        file_names = mask_set_dir.glob('*{}*.bmp'.format(replacement_part))
        for file in file_names:
            parent_path = file.parent
            new_name = file.name.replace(replacement_part, new_mask_name)
            file.rename(parent_path / new_name)
        self.mask_name.set(new_mask_name)
        self.rename_value.set("")


    def calculate_field_width(self, event=None):
        """ calculate_field_width """
        self.field_width.set(self.slit_width.get() * self.order)


    def set_SH_matrix(self, event=None):
        """ set_SH_matrix """
        if self.SHMatrix_Checked.get() == "S":
            self.order = self.Sorder.get()
            self.order_menu.set_menu(self.order, *self.Sorders)
            self.mask_arrays = np.arange(0, self.order)
        else:
            self.order = self.Horder.get()
            self.order_menu.set_menu(self.order, self.Horders)
            a = tuple(['a'+str(i), 'b'+str(i)] for i in range(1, 4))
            self.mask_arrays = [inner for outer in zip(*a) for inner in outer]
        self.calculate_field_width()
        self.logger.debug("Selected Order is {}".format(self.order))
        self.logger.debug("Mask Arrays are: {}".format(self.mask_arrays))


    def generate_hts(self):
        """ HTS_generate """
        DMD_size = (1080, 2048)
        matrix_type = self.SHMatrix_Checked.get()  # Two options, H or S
        # e.g. 15 Order of the hadamard matrix (or S matrix)
        order = self.order
        # NOTE that X and Y are transposed when talking to the DMD
        Xo, Yo = self.slit_yc.get(), self.slit_xc.get()

        # Slit width in number of micromirrors
        slit_width = self.slit_width.get()
        # Slit length in number of micromirrors
        slit_length = self.slit_length.get()

        folder = get_data_file('hadamard.mask_sets')
        if matrix_type == 'S':
            mask_set, matrix = make_S_matrix_masks(order, DMD_size, slit_width, slit_length, Xo, Yo, folder)
            name = f'S{order}_mask_{slit_width}w_{order:03d}.bmp'
        if matrix_type == 'H':
            mask_set_a, mask_set_b, matrix = make_H_matrix_masks(order, DMD_size, slit_width, slit_length, Xo, Yo, folder)
            name = f"H{order}_mask_{slit_width}w_ab_{order:03d}.bmp"
        self.mask_name.set(name)
        self.rename_value.set("")


    def dmd_initialize(self):
        """ dmd_initialize """
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        self.DMD.initialize(address=host, port=int(port))
        self.DMD._open()
        with Image.open(get_data_file("dmd", "current_dmd_state.png")) as image_map:
            tk_image = ImageTk.PhotoImage(image_map)
            label1 = tk.Label(self.canvas, image=tk_image)
            label1.image = tk_image
            label1.place(x=-100, y=0)
        self.str_map_filename.set("none")


    def dmd_whiteout(self):
        """ 
        sets all mirrors "ON" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "OFF"
        """
        DMD.apply_blackout()
        self._set_slit_image("whiteout_dmd_state.png", "whiteout")


    def dmd_blackout(self):
        """ 
        sets all mirrors "OFF" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "ON"
        """
        DMD.apply_whiteout()
        self._set_slit_image("blackout_dmd_state.png", "blackout")


    def dmd_checkerboard(self):
        """ dmd_checkerboard """
        DMD.apply_checkerboard()
        self._set_slit_image("checkerboard.png", "checkerboard")


    def dmd_invert(self):
        """ dmd_invert """
        DMD.apply_invert()
        with Image.open(get_data_file("dmd", "current_dmd_state.png")) as image:
            inverted_image = PIL.ImageOps.invert(image)
            inverted_image.save(get_data_file("dmd", "current_dmd_state.png"))
        if "inverted" in str_map_filename.get():
            state_name = self.str_map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.str_map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)


    def dmd_antinvert(self):
        """ dmd_antinvert """
        DMD.apply_antinvert()
        if "inverted" in str_map_filename.get():
            state_name = self.str_map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.str_map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)


    def browse_map(self):
        """ BrowseMapFiles """
        self.str_map_filename.set("")
        filename = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.csv.maps"),
                                                 title="Select a File",
                                                 filetypes=(("Text files",
                                                             "*.csv"),
                                                            ("all files",
                                                             "*.*")))
        try:
            os.startfile(filename)
        except AttributeError:
            subprocess.call(['open', filename])
        self.str_map_filename.set(Path(filename).name)


    def load_map(self):
        """ LoadMap """
        self.str_map_filename.set("")
        self.str_filename_slits.set("")
        filename = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.csv.maps"),
                                                 title="Select a File",
                                                 filetypes=(("Text files",
                                                             "*.csv"),
                                                            ("all files",
                                                             "*.*")))
        file_path = Path(filename)
        self.logger.info("Loading Map {}".format(filename))
        self.str_map_filename.set(file_path.name)
        self.main_fits_header.set_param("dmdmap", file_path.name)

        map_list = []
        with open(filename, 'r') as file:
            csv_file = csv.reader(file)
            for row in csv_file:
                map_list.append([int(r) for r in row])
        file.close()
        
        self.logger.debug("Map rows are:")
        for i, row in enumerate(map_list):
            self.logger.debug("Row {}: {}".format(i, row))

        test_shape = np.ones((1080, 2048), dtype=np.int32)  # This is the size of the DC2K
        for row in map_list:
            test_shape[row[0]:row[1], row[2]:row[3]] = row[4]

        try:
            self.DMD.apply_shape(test_shape)
        except Exception as e:
            self.logger.error("DMD Not Connected!")

        # Create astropy regions file
        self.logger.info("Creating Regions file")
        with open(get_data_file("regions.pixels", "{}.reg".format(file_path.name[:-3])), 'w') as f:
            f.write("# Region file format: DS9 astropy/regions\n")
            f.write("global edit=1 width=1 font=Sans Serif fill=0 color=red\n")
            f.write("image\n")
            for row in map_list:
                x0, y0 = self.convert.DMD2CCD(row[0], row[2])
                x1, y1 = self.convert.DMD2CCD(row[1], row[3])
                xc, yc = (x0 + x1)/2., (y0 + y1)/2.
                dx, dy = x1 - x0, y1 - y0
                output = "box({},{},{},{},0)".format(xc, yc, dx, dy)
                self.logger.debug(output)
                f.write("{}\n".format(output))

        self.str_map_filename.set(file_path.name[:-3]+"reg")
        main_page = self.parent.frames['MainPage']
        main_page.str_filename_regfile_xyAP.set(file_path.name[:-3]+"reg")
        self._set_slit_image("current_dmd_state.png", file_path.name[:-4])


    def load_slits(self):
        """ LoadSlits """
        self.string_var_filename.set("")
        self.str_filename_slits.set("")
        filename_slits = tk.filedialog.askopenfilename(initialdir=get_data_file("dmd.csv.slits"),
                                                       title="Select a File",
                                                       filetypes=(("Text files",
                                                                   "*.csv"),
                                                                  ("all files",
                                                                   "*.*")))
        file_path = Path(filename_slits)
        self.str_filename_slits.set(file_path.name)
        main_fits_header.set_param("dmdmap", file_path.name)
        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index), int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in table.index:
            slit_shape[x1[i]:x2[i], y1[i]:y2[i]] = 0
        DMD.apply_shape(slit_shape)
        self._set_slit_image("current_dmd_state.png", file_path.name[:-4])


    def AddSlit(self):
        """
        # 1. read the current filename
        # 2. open the .csv file
        # 3. add the slit
        """

        # 1. read the current filename
        filename_in_text = self.str_map_filename.get()
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
        filename_in_text = self.str_map_filename.get()
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)
        pandas_map = pd.DataFrame(self.map)
        pandas_map.to_csv(self.map_filename, index=False, header=None)
        print("Map Saved")
        
    def PushCurrentMap(self):
        """ Push to the DMD the file in Current DMD Map Textbox """

        filename_in_text = self.self.str_map_filename.get()
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)

        myList = []
        with open(self.map_filename, 'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        file.close()

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


    def _set_slit_image(self, image_file, image_name):
        """
        Set the slit image (centre frame) to the given file, which represents a DMD
        mirror configuration
        """
        with Image.open(get_data_file("dmd", image_file)) as image_map:
            tk_image = ImageTk.PhotoImage(image_map)
            label1 = tk.Label(self.canvas, image=tk_image)
            label1.image = tk_image
            label1.place(x=-100, y=0)
        self.str_map_filename.set(image_name)
