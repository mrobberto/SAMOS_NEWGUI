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
import time

from astropy import wcs
import pandas as pd
from PIL import Image, ImageTk, ImageOps

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs import Messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from samos.hadamard.patterns import make_S_matrix_masks, make_H_matrix_masks
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.utils import ccd_to_dmd, dmd_to_ccd
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled
from .hadamard_subframe import HadamardGenerator


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

        w = ttk.Button(frame, text="Blackout -> SAMI", command=self.dmd_blackout, bootstyle="success")
        w.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        w = ttk.Button(frame, text="Whiteout -> SISI", command=self.dmd_whiteout, bootstyle="success")
        w.grid(row=3, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        w = ttk.Button(frame, text="Checkerboard",command=self.dmd_checkerboard, bootstyle="success")
        w.grid(row=3, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
#        self.check_widgets[w] = [("condition", self, "initialized", True), ("condition", self.DMD, "extended_patterns", True)]
        #the line above was preventing the activation of the checkerboard button, so I reinstate the vanilla line.    
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        
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
        w = ttk.Button(frame, text="Push", command=self.push_slits, bootstyle="success")
        w.grid(row=1, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Save", command=self.save_slits)
        w.grid(row=1, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        # Create New Slit List
        w = ttk.Button(frame, text="New Slit List", command=self.create_slits)
        w.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        # Load Slit List
        w = ttk.Button(frame, text="Load Slit List", command=self.load_slits)
        w.grid(row=2, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="Current Slit List:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, textvariable=self.slits_filename, anchor="w").grid(row=3, column=1, columnspan=2, sticky=TK_STICKY_ALL)

        # Canvas display for DMD pattern
        self.canvas = tk.Canvas(display_frame, width=300, height=270, bg="dark gray")
        self.canvas.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Inline read-only library preview. Do not confuse it with the live DMD state.
        ttk.Button(display_frame, text="Preview Pixel Mask (.reg/.jpg) — NO SEND",
                   command=self._open_pixel_mask_browser).grid(
                       row=1, column=0, padx=3, pady=5, sticky=TK_STICKY_ALL)
        ttk.Button(display_frame, text="Return to DMD Display",
                   command=self._restore_pixel_mask_display).grid(
                       row=2, column=0, padx=3, pady=2, sticky=TK_STICKY_ALL)
        self._pixel_mask_preview_status = tk.StringVar(self, value="DMD display; no pixel-mask preview selected")
        ttk.Label(display_frame, textvariable=self._pixel_mask_preview_status,
                  wraplength=310, anchor="w", justify="left").grid(
                      row=3, column=0, padx=3, pady=3, sticky="w")
        # The left display is the DMD/SAMI selection mask, not a SISI pixel map.
        # This legend does not imply optical verification of the mirror positions.
        ttk.Label(display_frame,
                  text="DMD mirror view: white = to SAMI; black = to SISI. "
                       "Commanded pattern, not an optical readback.",
                  wraplength=310, anchor="w", justify="left").grid(
                      row=4, column=0, padx=3, pady=2, sticky="w")

        """ 
        # Hadamard Sub-frame
        """
        self.hadamard_conf_frame = HadamardGenerator(self, hadamard_frame, **kwargs)
        self.hadamard_conf_frame.grid(row=0, column=0, rowspan=4, sticky=TK_STICKY_ALL)

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



    def _open_pixel_mask_browser(self):
        """Preview a SISI .reg/.jpg in the EXISTING page canvas; no hardware calls."""
        from tkinter import messagebox
        from samos.ui.dmd_mask_inline_preview import (
            default_pixel_root, jpeg_for_selection, letterboxed_preview)
        root = default_pixel_root(__file__)
        initial_dir = getattr(self, "_pixel_mask_preview_lastdir", root)
        if not Path(initial_dir).is_dir():
            initial_dir = root
        chosen = askopenfilename(
            parent=self,
            initialdir=str(initial_dir),
            title="Preview SISI pixel mask (no DMD send)",
            filetypes=(("SISI pixel masks", "*.reg"),
                       ("JPEG previews", "*.jpg *.jpeg"),
                       ("All files", "*.*")))
        if not chosen:
            return
        selected = Path(chosen)
        try:
            preview = jpeg_for_selection(selected)
            with Image.open(preview) as picture:
                fitted = letterboxed_preview(picture)
            new_photo = ImageTk.PhotoImage(fitted, master=self.canvas)
        except (OSError, ValueError) as exc:
            messagebox.showwarning("Pixel mask preview", str(exc), parent=self)
            return
        # Overlay only the image; retain underlying live-DMD display widgets.
        # This is a preview, NOT a DMD command and NOT a mask-selection action.
        self._restore_pixel_mask_display()
        label = tk.Label(self.canvas, image=new_photo, bg="black", bd=0,
                         highlightthickness=0)
        label.image = new_photo
        label.grid(row=0, column=0)
        label.lift()
        self._pixel_mask_preview_label = label
        self._pixel_mask_preview_photo = new_photo
        self._pixel_mask_preview_lastdir = selected.parent
        try:
            shown = str(selected.relative_to(root))
        except ValueError:
            shown = selected.name
        self._pixel_mask_preview_status.set(
            "PREVIEW ONLY — {} (no DMD command)".format(shown))

    def _restore_pixel_mask_display(self):
        """Remove the JPEG overlay without changing the DMD controller or map."""
        label = getattr(self, "_pixel_mask_preview_label", None)
        if label is not None:
            try:
                label.destroy()
            except tk.TclError:
                pass
        self._pixel_mask_preview_label = None
        self._pixel_mask_preview_photo = None
        self._pixel_mask_preview_status.set(
            "DMD display restored (no hardware command)")

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
            title = "ERROR: No valid WCS!"
            message = "ERROR: SAMOS has no valid WCS.\nUnable to set mask from RA/DEC."
            Messagebox.ok(message, title=title)
            return
        x_CCD_HTS_center, y_CCD_HTS_center = self.PAR.wcs.all_world2pix(ad, 0)[0]

        # convert pixels -> DMD mirrors
        x_DMD_HTS_center, y_DMD_HTS_center = ccd_to_dmd(x_CCD_HTS_center, y_CCD_HTS_center, self.PAR.dmd_wcs)

        # refresh entrybox field
        self.hadamard_conf_frame.slit_xc.set(int(x_DMD_HTS_center))
        self.hadamard_conf_frame.slit_yc.set(int(y_DMD_HTS_center))

        # generate mask
        self.hadamard_conf_frame.generate_hts()


    @check_enabled
    def dmd_initialize(self):
        """ dmd_initialize """
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
        self.DMD.apply_blackout()
        self._set_slit_image("current_dmd_state.png", "whiteout")


    @check_enabled
    def dmd_blackout(self):
        """ 
        sets all mirrors "OFF" as seen by the imaging channel. From the point of view of 
        the DMD with its current orientation, all mirrors are "ON"
        """
        self.DMD.apply_whiteout()
        self._set_slit_image("current_dmd_state.png", "blackout")


    @check_enabled
    def dmd_checkerboard(self):
        """ dmd_checkerboard """
        self.DMD.apply_checkerboard()
        self._set_slit_image("current_dmd_state.png", "checkerboard")


    @check_enabled
    def dmd_invert(self):
        """ dmd_invert """
        self.DMD.apply_invert()
        if "inverted" in self.map_filename.get():
            state_name = self.map_filename.get().replace(" inverted", "")
        else:
            state_name = "{} inverted".format(self.map_filename.get())
        self._set_slit_image("current_dmd_state.png", state_name)


    @check_enabled
    def dmd_antinvert(self):
        """ dmd_antinvert """
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
        """Load a custom DMD mask and write its SISI-coordinate DS9 region file.

        The DMD WCS is constructed ONCE per load. Previously it was rebuilt
        twice for every slit rectangle, repeatedly opening the same FITS file.
        Hardware commands and region geometry are unchanged.
        """
        self.map_filename.set("none")
        self.map_filename_path = None
        self.slits_filename.set("")
        self.slits_filename_path = None
        filename = askopenfilename(
            initialdir=get_data_file("dmd.csv.maps"),
            title="Select a File",
            filetypes=(("Text files", "*.csv"), ("all files", "*.*"))
        )
        if not filename:
            return

        t_total = time.perf_counter()
        self.map_filename_path = Path(filename)
        self.logger.info("Loading Map {}".format(self.map_filename_path))
        self.map_filename.set(self.map_filename_path.name)
        self.main_fits_header.set_param("dmdmap", self.map_filename_path.name)

        t_stage = time.perf_counter()
        map_list = self._load_map(self.map_filename_path)
        dmd_shape = self._make_dmd_array(map_list)
        self.logger.info("DMD timing: CSV read + array preparation %.3f s",
                         time.perf_counter() - t_stage)

        t_stage = time.perf_counter()
        self.DMD.apply_shape(dmd_shape)
        self.logger.info("DMD timing: apply_shape (encoding + DMD commands + PNG) %.3f s",
                         time.perf_counter() - t_stage)

        # Preserve the original per-corner transformations and DS9 format.
        # Accessing PAR.dmd_wcs opens DMD_Mapping_WCS.fits and constructs an
        # Astropy WCS, so it must not happen inside the rectangle loop.
        t_stage = time.perf_counter()
        dmd_wcs = self.PAR.dmd_wcs
        self.logger.info("DMD timing: WCS construction %.3f s",
                         time.perf_counter() - t_stage)

        t_stage = time.perf_counter()
        self.logger.info("Creating Regions file")
        region_path = get_data_file("regions.pixels")
        new_region_file = region_path / self.map_filename_path.name.replace(".csv", ".reg")
        self.logger.info("Writing DMD map to %s", new_region_file)
        with open(new_region_file, 'w') as f:
            f.write("# Region file format: DS9 astropy/regions\n")
            f.write("global edit=1 width=1 font=Sans Serif fill=0 color=red\n")
            f.write("image\n")
            for row in map_list:
                x0, y0 = dmd_to_ccd(row[0], row[2], dmd_wcs)
                x1, y1 = dmd_to_ccd(row[1], row[3], dmd_wcs)
                xc, yc = (x0 + x1)/2., (y0 + y1)/2.
                dx, dy = x1 - x0, y1 - y0
                output = f"box({xc},{yc},{dx},{dy},0)"
                self.logger.debug(output)
                f.write(f"{output}\n")
        self.logger.info("DMD timing: DS9 region generation (%d rectangles) %.3f s",
                         len(map_list), time.perf_counter() - t_stage)

        self.map_filename.set(new_region_file.name)
        # ***** DEPENDENCY *****
        # main_page = self.parent.frames['MainPage']
        # main_page.str_filename_regfile_xyAP.set(new_region_file.name)
        # ***** DEPENDENCY *****
        t_stage = time.perf_counter()
        self._set_slit_image("current_dmd_state.png", new_region_file.name[:-4])
        self.logger.info("DMD timing: GUI preview refresh %.3f s",
                         time.perf_counter() - t_stage)
        self.logger.info("DMD timing: total load_map %.3f s",
                         time.perf_counter() - t_total)


    @check_enabled
    def create_slits(self):
        self.map_filename.set("none")
        self.map_filename_path = None
        title = "Create a new Slits file"
        self.slits_filename_path = Path(asksaveasfilename(initialdir=self.PAR.fits_dir, title=title))
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
        self.logger.info("Starting to create map from file")
        for index, row in table.iterrows():
            self.logger.info(f"\tRow is {row['x']} {row['y']} {row['dx1']} {row['dx2']} {row['dy1']} {row['dy2']}")
            xoffset = 0
            yoffset = 2048 // 4
            y0 = round(row['x']) - np.floor(row['dx1']).astype(int) + yoffset
            y1 = round(row['x']) + np.floor(row['dx2']).astype(int) + yoffset
            x0 = round(row['y']) - np.floor(row['dy1']).astype(int) + xoffset
            x1 = round(row['y']) + np.floor(row['dy2']).astype(int) + xoffset
            self.logger.info(f"\tAdding [{x0}, {x1}, {y0}, {y1}, 0] to map")
            self.map.append([x0, x1, y0, y1, 0])
        self.logger.info(f"Finished.")
        self.logger.info(f"Map is {self.map}")


    @check_enabled
    def push_slits(self):
        dmd_shape = self._make_dmd_array(self.map)
        self.DMD.apply_shape(dmd_shape)
        self._set_slit_image("current_dmd_state.png", self.slits_filename.get()[:-4])


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
            filename_in_text += ".csv"
        self.map_filename_path = get_data_file("dmd.scv.maps", filename_in_text)
        map_list = self._load_map(self.map_filename_path)
        dmd_shape = self._make_dmd_array(map_list)
        self.DMD.apply_shape(dmd_shape)
        self._set_slit_image("current_dmd_state.png", "Current Map")


    def _set_slit_image(self, image_file, image_name):
        """Refresh the mirror-coordinate DMD display (not the SISI preview).

        Reuse the existing Tk label instead of stacking a fresh widget after
        every DMD command. The separate SISI pixel-mask overlay is unchanged.
        """
        t_start = time.perf_counter()
        label = getattr(self, "_dmd_image_label", None)
        if label is None or not label.winfo_exists():
            label = ttk.Label(self.canvas)
            self._dmd_image_label = label
            label.grid(row=0, column=0)
        # This file is a display artifact, not proof of the mirror positions.
        # If an RC1.1 archive lacks it (as happened at SOAR), do not allow
        # a missing/corrupt PNG to abort the GUI's DMD initialization callback.
        try:
            with Image.open(get_data_file("dmd", image_file)) as image_map:
                image_scaled = image_map.resize((300, 270))
        except (OSError, ValueError) as exc:
            self.logger.warning(
                "DMD display image unavailable (%s): %s. "
                "No mirror-state readback has been performed.", image_file, exc)
            label.configure(image="", text="DMD display unavailable\n"
                                          "Missing or unreadable PNG\n"
                                          "Not a mirror-state readback")
            label.image = None
        else:
            tk_image = ImageTk.PhotoImage(image_scaled)
            label.configure(image=tk_image, text="")
            label.image = tk_image
        self.map_filename.set(image_name)
        self.map_filename_path = image_file
        self.logger.info("DMD timing: PNG read/resize + Tk image %.3f s",
                         time.perf_counter() - t_start)


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
