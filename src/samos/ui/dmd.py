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
from tkinter import ttk
from tkinter.filedialog import askopenfilename

from samos.hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame


class DMDPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "DMD Control", **kwargs)
        self.initialized = False
        self.buttons = {}
        
        # Set up basic frames
        button_frame = tk.LabelFrame(self.main_frame, text="Controls", font=BIGFONT, borderwidth=3, width=250)
        button_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        display_frame = tk.Frame(self.main_frame, borderwidth=3, width=350)
        display_frame.grid(row=0, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        hadamard_frame = tk.Frame(self.main_frame, borderwidth=3, width=250)
        hadamard_frame.grid(row=0, column=3, sticky=TK_STICKY_ALL)

        # dmd.initialize()
        self.buttons["initialize"] = tk.Button(button_frame, text="Initialize", command=self.dmd_initialize)
        self.buttons["initialize"].grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Basic Patterns
        tk.Label(button_frame, text="Basic Patterns:", anchor="w").grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.buttons["whiteout"] = tk.Button(button_frame, text="Blackout", bd=3, command=self.dmd_whiteout)
        self.buttons["whiteout"].grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.buttons["blackout"] = tk.Button(button_frame, text="Whiteout", bd=3, command=self.dmd_blackout)
        self.buttons["blackout"].grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.buttons["checkerboard"] = tk.Button(button_frame, text="Checkerboard", bd=3, command=self.dmd_checkerboard)
        self.buttons["checkerboard"].grid(row=3, column=2, sticky=TK_STICKY_ALL)
        self.buttons["invert"] = tk.Button(button_frame, text="Invert", bd=3, command=self.dmd_invert)
        self.buttons["invert"].grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.buttons["antinvert"] = tk.Button(button_frame, text="AntInvert", bd=3, command=self.dmd_antinvert)
        self.buttons["antinvert"].grid(row=4, column=2, sticky=TK_STICKY_ALL)

        # Custom Patterns
        tk.Label(button_frame, text="Custom Patterns:", anchor="w").grid(row=6, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.buttons["edit_map"] = tk.Button(button_frame, text="Edit DMD Map", command=self.browse_map)
        self.buttons["edit_map"].grid(row=7, column=0, sticky=TK_STICKY_ALL)
        self.buttons["load_map"] = tk.Button(button_frame, text="Load DMD Map", command=self.load_map)
        self.buttons["load_map"].grid(row=7, column=2, sticky=TK_STICKY_ALL)
        label_filename = tk.Label(button_frame, text="Current DMD Map:", anchor="w")
        label_filename.grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.str_map_filename = tk.StringVar()
        l = tk.Label(button_frame, textvariable=self.str_map_filename, bg="grey")
        l.grid(row=8, column=1, columnspan=2, sticky=TK_STICKY_ALL)

        # Custom Slit
        tk.Label(button_frame, text="Custom Slit:", anchor="w").grid(row=10, column=0, sticky=TK_STICKY_ALL)
        custom_frame = tk.Frame(button_frame, borderwidth=0)
        custom_frame.grid(row=11, column=0, rowspan=1, columnspan=3, sticky=TK_STICKY_ALL)
        tk.Label(custom_frame, text="x0").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.x0 = tk.IntVar(self, 540)
        tk.Entry(custom_frame, textvariable=self.x0, width=5).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        tk.Label(custom_frame, text="y0").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.y0 = tk.IntVar(self, 1024)
        tk.Entry(custom_frame, textvariable=self.y0, width=5).grid(row=0, column=3, sticky=TK_STICKY_ALL)

        tk.Label(custom_frame, text="x1").grid(row=0, column=4, sticky=TK_STICKY_ALL)
        self.x1 = tk.IntVar(self, 540)
        tk.Entry(custom_frame, textvariable=self.x1, width=5).grid(row=0, column=5, sticky=TK_STICKY_ALL)
        tk.Label(custom_frame, text="y1").grid(row=0, column=6, sticky=TK_STICKY_ALL)
        self.y1 = tk.IntVar(self, 1024)
        tk.Entry(custom_frame, textvariable=self.y1, width=5).grid(row=0, column=7, sticky=TK_STICKY_ALL)

        # Slit Buttons
        self.buttons["add_slit"] = tk.Button(button_frame, text="Add", command=self.add_slit)
        self.buttons["add_slit"].grid(row=13, column=0, sticky=TK_STICKY_ALL)
        self.buttons["push_map"] = tk.Button(button_frame, text="Push", command=self.push_current_map)
        self.buttons["push_map"].grid(row=13, column=1, sticky=TK_STICKY_ALL)
        self.buttons["save_map"] = tk.Button(button_frame, text="Save", command=self.save_map)
        self.buttons["save_map"].grid(row=13, column=2, sticky=TK_STICKY_ALL)

        # Load Slit
        self.buttons["load_slit"] = tk.Button(button_frame, text="Load Slit List", command=self.load_slits)
        self.buttons["load_slit"].grid(row=15, column=2, sticky=TK_STICKY_ALL)
        tk.Label(button_frame, text="Current Slit List").grid(row=16, column=0, sticky=TK_STICKY_ALL)
        self.str_filename_slits = tk.StringVar()
        l = tk.Label(button_frame, textvariable=self.str_filename_slits, bg="grey", anchor="w")
        l.grid(row=16, column=1, columnspan=2, sticky=TK_STICKY_ALL)

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
        tk.Label(hadamard_conf_frame, text="Slit Width:", anchor="w").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.slit_width = tk.IntVar(self, 3)
        box = tk.Entry(hadamard_conf_frame, textvariable=self.slit_width, width=5)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Length:", anchor="w").grid(row=3, column=3, sticky=TK_STICKY_ALL)
        self.slit_length = tk.IntVar(self, 256)
        box = tk.Entry(hadamard_conf_frame, textvariable=self.slit_length, width=5)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=4, sticky=TK_STICKY_ALL)

        # Field Centre
        tk.Label(hadamard_conf_frame, text="Field Centre:", anchor="w").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Xo", anchor="w").grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.slit_xc = tk.IntVar(self, 540)
        tk.Entry(hadamard_conf_frame, textvariable=self.slit_xc, width=5).grid(row=4, column=2, sticky=TK_STICKY_ALL)
        tk.Label(hadamard_conf_frame, text="Yo", anchor="w").grid(row=4, column=3, sticky=TK_STICKY_ALL)
        self.slit_yc = tk.IntVar(self, 1045)
        tk.Entry(hadamard_conf_frame, textvariable=self.slit_yc, width=5).grid(row=4, column=4, sticky=TK_STICKY_ALL)

        # Field Width
        tk.Label(hadamard_conf_frame, text="Width:", anchor="w").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.field_width = tk.IntVar(self, 21)
        txt = tk.Entry(hadamard_conf_frame,  textvariable=self.field_width, bg="red", fg="white", font=BIGFONT_15)
        txt.grid(row=5, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        
        # Generate
        self.buttons["gen_frame"] = tk.Button(hadamard_conf_frame, text="GENERATE", bg='#A877BA', font=BIGFONT, 
                                              command=self.generate_hts)
        self.buttons["gen_frame"].grid(row=6, column=0, columnspan=3, sticky=TK_STICKY_ALL)

        # Name / Rename
        tk.Label(hadamard_conf_frame, text="Name:").grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.mask_name = tk.StringVar(self, "")
        tk.Label(hadamard_conf_frame, textvariable=self.mask_name).grid(row=8, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        rename_button_text = "Rename '{}' to:".format(self.mask_name.get())
        self.buttons["rename"] = tk.Button(hadamard_conf_frame, text=rename_button_text, command=self.rename_masks_file)
        self.buttons["rename"].grid(row=9, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.rename_value = tk.StringVar(self, "")
        e = tk.Entry(hadamard_conf_frame, textvariable=self.rename_value)
        e.grid(row=9, column=2, columnspan=3, sticky=TK_STICKY_ALL)

        # Ra/Dec
        radec_frame = tk.LabelFrame(hadamard_frame, text="Generate from RA/DEC")
        radec_frame.grid(row=4, column=0, rowspan=2, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="Target RA:", anchor="w").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.target_ra = tk.DoubleVar(self, 1.234567)
        e = tk.Entry(radec_frame, textvariable=self.target_ra, width=10)
        e.grid(row=0, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="(decimal degrees)").grid(row=0, column=3, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="Target DEC:", anchor="w").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.target_dec = tk.DoubleVar(self, 1.234567)
        e = tk.Entry(radec_frame, textvariable=self.target_ra, width=10)
        e.grid(row=1, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        tk.Label(radec_frame, text="(decimal degrees)").grid(row=1, column=3, sticky=TK_STICKY_ALL)
        self.buttons["gen_radec"] = tk.Button(radec_frame, text="GENERATE", bg='#A877BA', font=BIGFONT_20, 
                                              command=self.generate_hts_from_radec)
        self.buttons["gen_radec"].grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self._set_buttons()


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
        self._set_buttons()


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
        self._set_buttons()


    def calculate_field_width(self, event=None):
        """ calculate_field_width """
        self.field_width.set(self.slit_width.get() * self.order)


    def set_SH_matrix(self, event=None):
        """ set_SH_matrix """
        if self.SHMatrix_Checked.get() == "S":
            self.order = self.Sorders[1]
            self.order_menu.set_menu(self.order, *self.Sorders)
            self.mask_arrays = np.arange(0, self.order)
        else:
            self.order = self.Horders[1]
            self.order_menu.set_menu(self.order, self.Horders)
            a = tuple(['a'+str(i), 'b'+str(i)] for i in range(1, 4))
            self.mask_arrays = [inner for outer in zip(*a) for inner in outer]
        self.calculate_field_width()
        self._set_buttons()
        self.logger.debug("Selected Order is {}".format(self.order))
        self.logger.debug("Mask Arrays are: {}".format(self.mask_arrays))


    def generate_hts(self):
        """ HTS_generate """
        DMD_size = self.DMD.dmd_size
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
        self._set_buttons()


    def dmd_initialize(self):
        """ dmd_initialize """
        self.DMD.initialize()
        self.DMD._open()
        self._set_slit_image("current_dmd_state.png", "initial state")
        self.str_map_filename.set("none")
        self.initialized = True
        self._set_buttons()


    def dmd_whiteout(self):
        """ 
        sets all mirrors "ON" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "OFF"
        """
        self.DMD.apply_blackout()
        self._set_slit_image("current_dmd_state.png", "whiteout")
        self._set_buttons()


    def dmd_blackout(self):
        """ 
        sets all mirrors "OFF" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "ON"
        """
        self.DMD.apply_whiteout()
        self._set_slit_image("current_dmd_state.png", "blackout")
        self._set_buttons()


    def dmd_checkerboard(self):
        """ dmd_checkerboard """
        self.DMD.apply_checkerboard()
        self._set_slit_image("current_dmd_state.png", "checkerboard")
        self._set_buttons()


    def dmd_invert(self):
        """ dmd_invert """
        self.DMD.apply_invert()
        if "inverted" in self.str_map_filename.get():
            state_name = self.str_map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.str_map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)
        self._set_buttons()


    def dmd_antinvert(self):
        """ dmd_antinvert """
        self.DMD.apply_antinvert()
        if "inverted" in self.str_map_filename.get():
            state_name = self.str_map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.str_map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)
        self._set_buttons()


    def browse_map(self):
        """ BrowseMapFiles """
        self.str_map_filename.set("")
        filename = askopenfilename(initialdir=get_data_file("dmd.csv.maps"), title="Select a File",
                                   filetypes=(("Text files", "*.csv"), ("all files", "*.*")))
        try:
            os.startfile(filename)
        except AttributeError:
            subprocess.call(['open', filename])
        self.str_map_filename.set(Path(filename).name)
        self._set_buttons()


    def load_map(self):
        """ LoadMap """
        self.str_map_filename.set("")
        self.str_filename_slits.set("")
        filename = askopenfilename(initialdir=get_data_file("dmd.csv.maps"), title="Select a File",
                                   filetypes=(("Text files", "*.csv"), ("all files", "*.*")))
        file_path = Path(filename)
        self.logger.info("Loading Map {}".format(filename))
        self.str_map_filename.set(file_path.name)
        self.main_fits_header.set_param("dmdmap", file_path.name)
        map_list = self._load_map(file_path)
        dmd_shape = self._make_dmd_array(map_list)
        self.DMD.apply_shape(dmd_shape)

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
        self._set_buttons()


    def load_slits(self):
        """ LoadSlits """
        self.string_var_filename.set("")
        self.str_filename_slits.set("")
        filename_slits = askopenfilename(initialdir=get_data_file("dmd.csv.slits"), title="Select a File",
                                         filetypes=(("Text files", "*.csv"), ("all files", "*.*")))
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
        self.DMD.apply_shape(slit_shape)
        self._set_slit_image("current_dmd_state.png", file_path.name[:-4])
        self._set_buttons()


    def add_slit(self):
        """
        # 1. read the current filename
        # 2. open the .csv file
        # 3. add the slit
        """
        # 1. read the current filename
        filename_in_text = self.str_map_filename.get()
        if filename_in_text[-4:] != ".csv":
            filename_in_text += ".csv"
        self.map_filename = get_data_file("dmd.csv.maps", filename_in_text)
        map_list = self._load_map(self.map_filename)
        row = [str(x) for x in [self.x0.get(), self.x1.get(), self.y0.get(), self.y1.get(), 0]]
        map_list.append(row)
        self.map = map_list
        self._set_buttons()


    def save_map(self):
        """ SaveMap """
        self.logger.info("Saving current DMD map")
        filename_in_text = self.str_map_filename.get()
        
        # If there is no filename defined, create one based on current date
        if (len(filename_in_text) == 0) or (filename_in_text == "none"):
            self.logger.error("Attempted to save nonexistent map")
            filename_in_text = "map_custom_{}.csv".formate(datetime.now().strftime("%Y%m%d"))
            self.logger.info("Creating custom map file {}".format(filename_in_text))
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)
        pandas_map = pd.DataFrame(self.map)
        pandas_map.to_csv(self.map_filename, index=False, header=None)
        self._set_buttons()
        self.logger.info("Map {} saved".format(filename_in_text))


    def push_current_map(self):
        """ Push to the DMD the file in Current DMD Map Textbox """
        self.logger.info("Pushing map to DMD")
        filename_in_text = self.str_map_filename.get()
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = get_data_file("dmd.scv.maps", filename_in_text)
        map_list = self._load_map(self.map_filename)
        dmd_shape = self._make_dmd_array(map_list)
        self.DMD.apply_shape(dmd_shape)
        self._set_slit_image("current_dmd_state.png", "Current Map")
        self._set_buttons()


    def _set_slit_image(self, image_file, image_name):
        """
        Set the slit image (centre frame) to the given file, which represents a DMD
        mirror configuration
        """
        with Image.open(get_data_file("dmd", image_file)) as image_map:
            image_scaled = image_map.resize((300, 270))
            tk_image = ImageTk.PhotoImage(image_scaled)
            label1 = tk.Label(self.canvas, image=tk_image)
            label1.image = tk_image
            label1.grid(row=0, column=0)
        self.str_map_filename.set(image_name)


    def _set_buttons(self):
        """Set buttons to enabled or disabled based on DMD state"""
        self.buttons["rename"].config(text="Rename '{}' to:".format(self.mask_name))
        for button in self.buttons:
            if button == "initialize":
                if self.initialized:
                    self.buttons[button]['state'] = "disabled"
                else:
                    self.buttons[button]['state'] = "normal"
            elif button in ["gen_frame", "gen_radec"]:
                if self.initialized:
                    self.buttons[button]['state'] = "normal"
                else:
                    self.buttons[button]['state'] = "disabled"
            else:
                if self.initialized:
                    if button in ["push_map", "add_slit"]:
                        if self.str_map_filename.get() in ['', 'none']:
                            self.buttons[button]['state'] = "disabled"
                        else:
                            self.buttons[button]['state'] = "normal"
                    elif button == "rename":
                        if self.mask_name in ["", "none"]:
                            self.buttons[button]['state'] = "disabled"
                        else:
                            self.buttons[button]['state'] = "normal"
                    else:
                        self.buttons[button]['state'] = "normal"
                else:
                    self.buttons[button]['state'] = "disabled"


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
