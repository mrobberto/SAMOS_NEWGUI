"""
SAMOS DMD tk Frame Class
"""
import csv
from datetime import datetime
import logging
import numpy as np
import os
from pathlib import Path
import subprocess

from astropy import wcs
import pandas as pd
from PIL import Image, ImageTk, ImageOps

import tkinter as tk
import ttkbootstrap as ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

from samos.hadamard.patterns import make_S_matrix_masks, make_H_matrix_masks
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.utils import ccd_to_dmd, dmd_to_ccd
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class DMDPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "DMD Control", **kwargs)
        self.initialized = False
        self.map = None
        self.logger.info("Initializing DMD Page")
        
        # Set up basic frames
        button_frame = ttk.LabelFrame(self.main_frame, text="Controls", borderwidth=3, width=250)
        button_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        display_frame = ttk.Frame(self.main_frame, borderwidth=3, width=350)
        display_frame.grid(row=0, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        hadamard_frame = ttk.Frame(self.main_frame, borderwidth=3, width=250)
        hadamard_frame.grid(row=0, column=3, sticky=TK_STICKY_ALL)

        # dmd.initialize()
        w = ttk.Button(button_frame, text="Initialize", command=self.dmd_initialize, bootstyle="success")
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", False)]

        # Basic Patterns
        frame = ttk.LabelFrame(button_frame, text="Basic Patterns")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Blackout", command=self.dmd_blackout, bootstyle="success")
        w.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Whiteout", command=self.dmd_whiteout, bootstyle="success")
        w.grid(row=3, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Checkerboard",command=self.dmd_checkerboard, bootstyle="success")
        w.grid(row=3, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True), ("condition", self.DMD, "extended_patterns", True)]
        w = ttk.Button(frame, text="Invert", command=self.dmd_invert, bootstyle="success")
        w.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="AntInvert", command=self.dmd_antinvert, bootstyle="success")
        w.grid(row=4, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Custom Patterns
        frame = ttk.LabelFrame(button_frame, text="Custom Maps")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Edit DMD Map", command=self.browse_map)
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Load DMD Map", command=self.load_map, bootstyle="success")
        w.grid(row=0, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        ttk.Label(frame, text="Current DMD Map:", anchor="w").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.map_filename = self.make_db_var(tk.StringVar, "dmd_current_map_filename", "none")
        self.map_filename_path = None
        ttk.Label(frame, textvariable=self.map_filename).grid(row=1, column=1, sticky=TK_STICKY_ALL)

        # Custom Slit
        frame = ttk.LabelFrame(button_frame, text="Custom Slits")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        custom_frame = ttk.Frame(frame, borderwidth=0)
        custom_frame.grid(row=0, column=0, rowspan=1, columnspan=3, sticky=TK_STICKY_ALL)
        ttk.Label(custom_frame, text="x0").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.x0 = self.make_db_var(tk.IntVar, "dmd_custom_x0", 540)
        tk.Entry(custom_frame, textvariable=self.x0, width=5).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        ttk.Label(custom_frame, text="y0").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.y0 = self.make_db_var(tk.IntVar, "dmd_custom_y0", 1024)
        tk.Entry(custom_frame, textvariable=self.y0, width=5).grid(row=0, column=3, sticky=TK_STICKY_ALL)
        ttk.Label(custom_frame, text="x1").grid(row=0, column=4, sticky=TK_STICKY_ALL)
        self.x1 = self.make_db_var(tk.IntVar, "dmd_custom_x1", 540)
        tk.Entry(custom_frame, textvariable=self.x1, width=5).grid(row=0, column=5, sticky=TK_STICKY_ALL)
        ttk.Label(custom_frame, text="y1").grid(row=0, column=6, sticky=TK_STICKY_ALL)
        self.y1 = self.make_db_var(tk.IntVar, "dmd_custom_y1", 1024)
        tk.Entry(custom_frame, textvariable=self.y1, width=5).grid(row=0, column=7, sticky=TK_STICKY_ALL)
        # Slit Buttons
        self.slits_filename = self.make_db_var(tk.StringVar, "dmd_custom_filename", "none")
        self.slits_filename_path = None
        w = ttk.Button(frame, text="Add", command=self.add_slit)
        w.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True), ("valid_file", self.slits_filename_path)]
        w = ttk.Button(frame, text="Push", command=self.push_current_map, bootstyle="success")
        w.grid(row=1, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True), ("valid_file", self.slits_filename_path)]
        w = ttk.Button(frame, text="Save", command=self.save_slits)
        w.grid(row=1, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True), ("valid_file", self.slits_filename_path)]
        # Create New Slit List
        w = ttk.Button(frame, text="New Slit List", command=self.create_slits)
        w.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Load Slit List
        w = ttk.Button(frame, text="Load Slit List", command=self.load_slits)
        w.grid(row=2, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        ttk.Label(frame, text="Current Slit List:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, textvariable=self.slits_filename, anchor="w").grid(row=3, column=1, columnspan=2, sticky=TK_STICKY_ALL)

        # Canvas display for DMD pattern
        self.canvas = tk.Canvas(display_frame, width=300, height=270, bg="dark gray")
        self.canvas.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        hadamard_conf_frame = ttk.LabelFrame(hadamard_frame, text="Hadamard Configuration")
        hadamard_conf_frame.grid(row=0, column=0, rowspan=4, sticky=TK_STICKY_ALL)

        # Matrix Type and order
        self.sh_select = self.make_db_var(tk.StringVar, "dmd_hadamard_matrix_type", "S")
        self.logger.info(f"sh_select has value {self.sh_select.get()}")
        w = ttk.Radiobutton(hadamard_conf_frame, text="S Matrix", variable=self.sh_select, value="S", command=self.set_SH_matrix)
        w.grid(row=0, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Radiobutton(hadamard_conf_frame, text="H Matrix", variable=self.sh_select, value="H", command=self.set_SH_matrix)
        w.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        ttk.Label(hadamard_conf_frame, text="Order: ").grid(row=0, column=2, rowspan=2, sticky=TK_STICKY_ALL)
        self.orders = {
            "S": (3, 7, 11, 15, 19, 23, 31, 35, 43, 47, 63, 71, 79, 83, 103, 127, 255),
            "H": (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
        }
        self.order = self.make_db_var(tk.IntVar, "dmd_hadamard_order", self.orders[self.sh_select.get()][1])
        self.logger.info(f"order has value {self.order.get()}")
        self.order_menu = ttk.OptionMenu(hadamard_conf_frame, self.order, None, *self.orders[self.sh_select.get()], command=self.set_SH_matrix)
        self.order_menu.grid(row=0, column=3, rowspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.order_menu] = [("condition", self, "initialized", True)]

        # Slit Dimensions
        ttk.Label(hadamard_conf_frame, text="Slit Width:", anchor="w").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.slit_width = self.make_db_var(tk.IntVar, "dmd_hadamard_width", 3)
        box = tk.Entry(hadamard_conf_frame, textvariable=self.slit_width, width=5)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[box] = [("condition", self, "initialized", True)]
        ttk.Label(hadamard_conf_frame, text="Length:", anchor="w").grid(row=3, column=3, sticky=TK_STICKY_ALL)
        self.slit_length = self.make_db_var(tk.IntVar, "dmd_hadamard_length", 256)
        box = tk.Entry(hadamard_conf_frame, textvariable=self.slit_length, width=5)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[box] = [("condition", self, "initialized", True)]

        # Field Centre
        ttk.Label(hadamard_conf_frame, text="Field Centre:", anchor="w").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(hadamard_conf_frame, text="Xo", anchor="w").grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.slit_xc = self.make_db_var(tk.IntVar, "dmd_hadamard_xc", 540)
        tk.Entry(hadamard_conf_frame, textvariable=self.slit_xc, width=5).grid(row=4, column=2, sticky=TK_STICKY_ALL)
        ttk.Label(hadamard_conf_frame, text="Yo", anchor="w").grid(row=4, column=3, sticky=TK_STICKY_ALL)
        self.slit_yc = self.make_db_var(tk.IntVar, "dmd_hadamard_yc", 1045)
        tk.Entry(hadamard_conf_frame, textvariable=self.slit_yc, width=5).grid(row=4, column=4, sticky=TK_STICKY_ALL)

        # Field Width
        ttk.Label(hadamard_conf_frame, text="Width:", anchor="w").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.field_width = self.make_db_var(tk.IntVar, "dmd_hadamard_field_width", 21)
        txt = tk.Entry(hadamard_conf_frame,  textvariable=self.field_width, bg="red", fg="white", font=BIGFONT_15)
        txt.grid(row=5, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        
        # Generate
        w = ttk.Button(hadamard_conf_frame, text="GENERATE", command=self.generate_hts)
        w.grid(row=6, column=0, padx=2, pady=2, columnspan=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Name / Rename
        ttk.Label(hadamard_conf_frame, text="Name:").grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.mask_name = self.make_db_var(tk.StringVar, "dmd_hadamard_mask_name", "")
        tk.Label(hadamard_conf_frame, textvariable=self.mask_name).grid(row=8, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        rename_button_text = "Rename '{}' to:".format(self.mask_name.get())
        self.rename_button = ttk.Button(hadamard_conf_frame, text=rename_button_text, command=self.rename_masks_file)
        self.rename_button.grid(row=9, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.rename_button] = [("condition", self, "initialized", True), ("tknot", self.mask_name, "")]
        self.rename_value = self.make_db_var(tk.StringVar, "dmd_hadamard_mask_rename_value", "")
        e = tk.Entry(hadamard_conf_frame, textvariable=self.rename_value)
        e.grid(row=9, column=2, columnspan=3, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self, "initialized", True)]

        # Ra/Dec
        radec_frame = ttk.LabelFrame(hadamard_frame, text="Generate from RA/DEC")
        radec_frame.grid(row=4, column=0, rowspan=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(radec_frame, text="Load from current WCS", command=self.load_ra_dec)
        b.grid(row=0, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "initialized", True), ("condition", self.PAR, "valid_wcs", True)]
        ttk.Label(radec_frame, text="Target RA:", anchor="w").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.target_ra = self.make_db_var(tk.DoubleVar, "dmd_coord_ra", 1.234567)
        e = tk.Entry(radec_frame, textvariable=self.target_ra, width=10)
        e.grid(row=1, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self, "initialized", True)]
        ttk.Label(radec_frame, text="(decimal degrees)").grid(row=1, column=3, sticky=TK_STICKY_ALL)
        ttk.Label(radec_frame, text="Target DEC:", anchor="w").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.target_dec = self.make_db_var(tk.DoubleVar, "dmd_coord_dec", 1.234567)
        e = tk.Entry(radec_frame, textvariable=self.target_ra, width=10)
        e.grid(row=2, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self, "initialized", True)]
        ttk.Label(radec_frame, text="(decimal degrees)").grid(row=2, column=3, sticky=TK_STICKY_ALL)
        w = ttk.Button(radec_frame, text="GENERATE", command=self.generate_hts_from_radec)
        w.grid(row=3, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.logger.info("Finished initializing DMD Page. Setting initial widget status.")
        self.set_enabled()
        self.logger.info("Finished initial widget status.")


    @check_enabled
    def load_ra_dec(self):
        self.target_ra.set(self.db.get_value("main_ra", default=self.target_ra.get()))
        self.target_dec.set(self.db.get_value("main_dec", default=self.target_dec.get()))


    @check_enabled
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
        if not self.PAR.valid_wcs:
            self.logger.error("Attempting to generate map from RA/DEC with no valid WCS")
            ttk.messagebox.showerror(title="No valid WCS!", message="SAMOS has no valid WCS.\nUnable to set mask from RA/DEC.")
            return
        x_CCD_HTS_center, y_CCD_HTS_center = self.PAR.wcs.all_world2pix(ad, 0)[0]

        # convert pixels -> DMD mirrors
        x_DMD_HTS_center, y_DMD_HTS_center = ccd_to_dmd(x_CCD_HTS_center, y_CCD_HTS_center, self.PAR.dmd_wcs)

        # refresh entrybox field
        self.slit_xc.set(int(x_DMD_HTS_center))
        self.slit_yc.set(int(y_DMD_HTS_center))

        # generate mask
        self.generate_hts()


    @check_enabled
    def rename_masks_file(self, event=None):
        """ rename the mask file, only the part starting with 'mask' """
        old_mask_name = self.mask_name.get()
        replacement_part = old_mask_name.strip().split("_")[1]
        new_mask_name = self.rename_value.get()
        mask_set_dir = get_data_file('hadamard.mask_sets')
        file_names = mask_set_dir.glob('*{}*.bmp'.format(replacement_part))
        for file in file_names:
            parent_path = file.parent
            new_name = file.name.replace(replacement_part, new_mask_name)
            file.rename(parent_path / new_name)
        self.mask_name.set(new_mask_name)
        self.rename_value.set("")


    @check_enabled
    def calculate_field_width(self, event=None):
        """ calculate_field_width """
        self.field_width.set(self.slit_width.get() * self.order.get())


    @check_enabled
    def set_SH_matrix(self, event=None):
        """ set_SH_matrix """
        self.logger.info("Started S/H Matrix Check")
        matrix_type = self.sh_select.get()
        self.logger.info(f"Matrix type {matrix_type}")
        matrix_orders = self.orders[matrix_type]
        self.logger.info(f"Matrix orders {matrix_orders}")
        current_order = self.order.get()
        self.logger.info(f"Current order {current_order}")
        if current_order not in matrix_orders:
            self.logger.info("Matrix type changed. Setting order to first value.")
            self.order_menu.set_menu(default=None, *matrix_orders)
            self.order.set(matrix_orders[0])
        self.logger.info("Updated Menu")
        if self.sh_select.get() == "H":
            a = tuple(['a'+str(i), 'b'+str(i)] for i in range(1, 4))
            self.mask_arrays = [inner for outer in zip(*a) for inner in outer]
        else:
            self.mask_arrays = np.arange(0, self.order.get())
        self.calculate_field_width()
        self.logger.debug("Selected Order is {}".format(self.order))
        self.logger.debug("Mask Arrays are: {}".format(self.mask_arrays))


    @check_enabled
    def generate_hts(self):
        """ HTS_generate """
        DMD_size = self.DMD.dmd_size
        matrix_type = self.sh_select.get()  # Two options, H or S
        # e.g. 15 Order of the hadamard matrix (or S matrix)
        order = self.order.get()
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


    @check_enabled
    def dmd_initialize(self):
        """ dmd_initialize """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.initialize()
            self.DMD._open()
        self._set_slit_image("current_dmd_state.png", "initial state")
        self.initialized = True


    @check_enabled
    def dmd_whiteout(self):
        """ 
        sets all mirrors "ON" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "OFF"
        """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_blackout()
        self._set_slit_image("current_dmd_state.png", "whiteout")


    @check_enabled
    def dmd_blackout(self):
        """ 
        sets all mirrors "OFF" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "ON"
        """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_whiteout()
        self._set_slit_image("current_dmd_state.png", "blackout")


    @check_enabled
    def dmd_checkerboard(self):
        """ dmd_checkerboard """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_checkerboard()
        self._set_slit_image("current_dmd_state.png", "checkerboard")


    @check_enabled
    def dmd_invert(self):
        """ dmd_invert """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_invert()
        if "inverted" in self.map_filename.get():
            state_name = self.map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)


    @check_enabled
    def dmd_antinvert(self):
        """ dmd_antinvert """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_antinvert()
        if "inverted" in self.map_filename.get():
            state_name = self.map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)


    @check_enabled
    def browse_map(self):
        """ BrowseMapFiles """
        self.map_filename.set("none")
        self.map_filename_path = None
        filename = askopenfilename(
            initialdir=get_data_file("dmd.csv.maps"),
            title="Select a File",
            filetypes=(("Text files", "*.csv"), ("all files", "*.*"))
        )
        try:
            os.startfile(filename)
        except AttributeError:
            subprocess.call(['open', filename])
        self.map_filename_path = Path(filename)
        self.map_filename.set(self.map_filename_path.name)


    @check_enabled
    def load_map(self):
        """ LoadMap """
        self.map_filename.set("none")
        self.map_filename_path = None
        self.slits_filename.set("")
        self.slits_filename_path = None
        filename = askopenfilename(
            initialdir=get_data_file("dmd.csv.maps"),
            title="Select a File",
            filetypes=(("Text files", "*.csv"), ("all files", "*.*"))
        )
        self.map_filename_path = Path(filename)
        self.logger.info("Loading Map {}".format(self.map_filename_path))
        self.map_filename.set(self.map_filename_path.name)
        self.main_fits_header.set_param("dmdmap", self.map_filename_path.name)
        map_list = self._load_map(self.map_filename_path)
        dmd_shape = self._make_dmd_array(map_list)
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_shape(dmd_shape)

        # Create astropy regions file
        self.logger.info("Creating Regions file")
        with open(get_data_file("regions.pixels", "{}.reg".format(file_path.name[:-3])), 'w') as f:
            f.write("# Region file format: DS9 astropy/regions\n")
            f.write("global edit=1 width=1 font=Sans Serif fill=0 color=red\n")
            f.write("image\n")
            for row in map_list:
                x0, y0 = dmd_to_ccd(row[0], row[2], self.PAR.dmd_wcs)
                x1, y1 = dmd_to_ccd(row[1], row[3], self.PAR.dmd_wcs)
                xc, yc = (x0 + x1)/2., (y0 + y1)/2.
                dx, dy = x1 - x0, y1 - y0
                output = f"box({xc},{yc},{dx},{dy},0)"
                self.logger.debug(output)
                f.write(f"{output}\n")

        self.map_filename.set(self.map_filename_path.name[:-3]+"reg")
        # ***** DEPENDENCY *****
        main_page = self.parent.frames['MainPage']
        main_page.str_filename_regfile_xyAP.set(file_path.name[:-3]+"reg")
        # ***** DEPENDENCY *****
        self._set_slit_image("current_dmd_state.png", file_path.name[:-4])


    @check_enabled
    def create_slits(self):
        self.map_filename.set("none")
        self.map_filename_path = None
        self.slits_filename_path = Path(asksaveasfilename(initialdir=get_fits_dir(), title="Create a new Slits file"))
        self.slits_filename.set(self.slits_filename_path.name)
        self.logger.info(f"Creating new slit map {self.slits_filename_path.name}")
        map_list = [[str(x) for x in [self.x0.get(), self.x1.get(), self.y0.get(), self.y1.get(), 0]]]
        self.map = map_list
        self.save_slits()


    @check_enabled
    def load_slits(self):
        """ LoadSlits """
        self.slits_filename_path = Path(askopenfilename(initialdir=get_data_file("dmd.csv.slits"), title="Select a File"))
        self.slits_filename.set(self.slits_filename_path.name)
        self.map_filename.set("none")
        self.map_filename_path = None
        self.main_fits_header.set_param("dmdmap", self.slits_filename_path.name)
        self.map = []
        table = pd.read_csv(self.slits_filename_path)
        xoffset = 0
        yoffset = np.full(len(table.index), int(2048/4))
        y0 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y1 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x0 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x1 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        for i in table.index:
            self.map.append([x0, x1, y0, y1, 0])


    @check_enabled
    def push_slits(self):
        dmd_shape = self._make_dmd_array(self.map)
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_shape(dmd_shape)
        self._set_slit_image("current_dmd_state.png", file_path.name[:-4])


    @check_enabled
    def add_slit(self):
        """
        # 1. read the current filename
        # 2. open the .csv file
        # 3. add the slit
        """
        # 1. read the current filename
        filename_in_text = self.map_filename.get()
        if filename_in_text[-4:] != ".csv":
            filename_in_text += ".csv"
        self.map_filename_path = get_data_file("dmd.csv.maps", filename_in_text)
        map_list = self._load_map(self.map_filename_path)
        row = [str(x) for x in [self.x0.get(), self.x1.get(), self.y0.get(), self.y1.get(), 0]]
        map_list.append(row)
        self.map = map_list


    @check_enabled
    def save_slits(self):
        self._save_map(self.map, self.slits_filename_path)


    @check_enabled
    def save_map(self):
        """ SaveMap """
        self.logger.info("Saving current DMD map")
        filename_in_text = self.map_filename.get()
        
        # If there is no filename defined, create one based on current date
        if (len(filename_in_text) == 0) or (filename_in_text == "none"):
            self.logger.error("Attempted to save nonexistent map")
            filename_in_text = "map_custom_{}.csv".formate(datetime.now().strftime("%Y%m%d"))
            self.logger.info("Creating custom map file {}".format(filename_in_text))
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        if (self.map_filename_path is not None) and (filename_in_text != self.map_filename_path.name):
            self.map_filename_path = get_data_file("dmd.scv.maps", filename_in_text)
        self._save_map(self.map, self.map_filename_path)


    @check_enabled
    def push_current_map(self):
        """ Push to the DMD the file in Current DMD Map Textbox """
        self.logger.info("Pushing map to DMD")
        filename_in_text = self.map_filename.get()
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename_path = get_data_file("dmd.scv.maps", filename_in_text)
        map_list = self._load_map(self.map_filename_path)
        dmd_shape = self._make_dmd_array(map_list)
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            self.DMD.apply_shape(dmd_shape)
        self._set_slit_image("current_dmd_state.png", "Current Map")


    def _set_slit_image(self, image_file, image_name):
        """
        Set the slit image (centre frame) to the given file, which represents a DMD
        mirror configuration
        """
        with Image.open(get_data_file("dmd", image_file)) as image_map:
            image_scaled = image_map.resize((300, 270))
            tk_image = ImageTk.PhotoImage(image_scaled)
            label1 = ttk.Label(self.canvas, image=tk_image)
            label1.image = tk_image
            label1.grid(row=0, column=0)
        self.map_filename.set(image_name)
        self.map_filename_path = image_file


    def _load_map(self, filename):
        """Load CSV DMD map file"""
        map_list = []
        with open(filename, 'r') as file:
            csv_file = csv.reader(file)
            for row in csv_file:
                map_list.append([int(x) for x in row])
        return map_list


    def _make_dmd_array(self, map_list):
        """
        Convert a list of DMD positions to an array of 0,1 values that defines individual
        mirror states
        """
        # uint8 makes it easier to turn this array into an image (if we want to)
        dmd_shape = np.ones((1080, 2048), dtype=np.uint8)
        for row in map_list:
            dmd_shape[row[0]:row[1], row[2]:row[3]] = row[4]
        return dmd_shape


    def _save_map(self, map_to_save, map_file):
        pandas_map = pd.DataFrame(map_to_save)
        pandas_map.to_csv(map_file, index=False, header=None)
        self.logger.info(f"Map saved to {map_file}")


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        self.rename_button.config(text=f"Rename '{self.mask_name.get()}' to:")
