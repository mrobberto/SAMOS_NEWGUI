"""
SAMOS Sub-frame for generating Hadamard matrices
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
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.utils import ccd_to_dmd, dmd_to_ccd
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class HadamardGenerator(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Hadamard", **kwargs)
        self.initialized = False
        self.map = None
        self.logger.info("Initializing Hadamard Generator Page")

        # Matrix Type and order
        self.sh_select = self.make_db_var(tk.StringVar, "dmd_hadamard_matrix_type", "S")
        w = ttk.Radiobutton(
            self.main_frame,
            text="S Matrix",
            variable=self.sh_select,
            value="S",
            command=self.set_SH_matrix
        )
        w.grid(row=0, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        w = ttk.Radiobutton(
            self.main_frame,
            text="H Matrix",
            variable=self.sh_select,
            value="H",
            command=self.set_SH_matrix
        )
        w.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        w = ttk.Label(self.main_frame, text="Order: ")
        w.grid(row=0, column=2, rowspan=2, sticky=TK_STICKY_ALL)
        self.orders = {
            "S": (3, 7, 11, 15, 19, 23, 31, 35, 43, 47, 63, 71, 79, 83, 103, 127, 255),
            "H": (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
        }
        starting_order = self.orders[self.sh_select.get()][1]
        self.order = self.make_db_var(tk.IntVar, "dmd_hadamard_order", starting_order)
        self.order_menu = ttk.OptionMenu(
            self.main_frame,
            self.order,
            None,
            *self.orders[self.sh_select.get()],
            command=self.set_SH_matrix
        )
        self.order_menu.grid(row=0, column=3, rowspan=2, sticky=TK_STICKY_ALL)

        # Slit Dimensions
        w = ttk.Label(self.main_frame, text="Slit Width:", anchor="w")
        w.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.slit_width = self.make_db_var(tk.IntVar, "dmd_hadamard_width", 3)
        box = tk.Entry(self.main_frame, textvariable=self.slit_width, width=5)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        w = ttk.Label(self.main_frame, text="Length:", anchor="w")
        w.grid(row=3, column=3, sticky=TK_STICKY_ALL)
        self.slit_length = self.make_db_var(tk.IntVar, "dmd_hadamard_length", 256)
        box = tk.Entry(self.main_frame, textvariable=self.slit_length, width=5)
        box.bind("<Return>", self.calculate_field_width)
        box.grid(row=3, column=4, sticky=TK_STICKY_ALL)

        # Field Centre
        w = ttk.Label(self.main_frame, text="Field Centre:", anchor="w")
        w.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Label(self.main_frame, text="Xo", anchor="w")
        w.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.slit_xc = self.make_db_var(tk.IntVar, "dmd_hadamard_xc", 540)
        w = tk.Entry(self.main_frame, textvariable=self.slit_xc, width=5)
        w.grid(row=4, column=2, sticky=TK_STICKY_ALL)
        w = ttk.Label(self.main_frame, text="Yo", anchor="w")
        w.grid(row=4, column=3, sticky=TK_STICKY_ALL)
        self.slit_yc = self.make_db_var(tk.IntVar, "dmd_hadamard_yc", 1045)
        w = tk.Entry(self.main_frame, textvariable=self.slit_yc, width=5)
        w.grid(row=4, column=4, sticky=TK_STICKY_ALL)

        # Field Width
        w = ttk.Label(self.main_frame, text="Width:", anchor="w")
        w.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.field_width = self.make_db_var(tk.IntVar, "dmd_hadamard_field_width", 21)
        txt = tk.Entry(
            self.main_frame,
            textvariable=self.field_width,
            bg="red",
            fg="white",
            font=BIGFONT_15
        )
        txt.grid(row=5, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        
        # Generate
        w = ttk.Button(self.main_frame, text="GENERATE", command=self.generate_hts)
        w.grid(row=6, column=0, padx=2, pady=2, columnspan=3, sticky=TK_STICKY_ALL)

        # Name / Rename
        w = ttk.Label(self.main_frame, text="Name:")
        w.grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.mask_name = self.make_db_var(tk.StringVar, "dmd_hadamard_mask_name", "")
        w = tk.Label(self.main_frame, textvariable=self.mask_name)
        w.grid(row=8, column=1, columnspan=4, sticky=TK_STICKY_ALL)
        rename_button_text = "Rename '{}' to:".format(self.mask_name.get())
        self.rename_button = ttk.Button(
            self.main_frame,
            text=rename_button_text,
            command=self.rename_masks_file
        )
        self.rename_button.grid(
            row=9,
            column=0,
            padx=2,
            pady=2,
            columnspan=2,
            sticky=TK_STICKY_ALL
        )
        self.rename_value = self.make_db_var(
            tk.StringVar,
            "dmd_hadamard_mask_rename_value",
            "",
            callback=self.update_hadamard_mask_name
        )
        e = tk.Entry(self.main_frame, textvariable=self.rename_value)
        e.grid(row=9, column=2, columnspan=3, sticky=TK_STICKY_ALL)


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


    def update_hadamard_mask_name(self):
        """ Rename mask renaming button when mask name is updated """
        mask_name = self.rename_value.get()
        self.rename_button.configure(text=f"Rename '{mask_name}' to:")


    def calculate_field_width(self, event=None):
        """ calculate_field_width """
        self.field_width.set(self.slit_width.get() * self.order.get())


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
            mask_set, matrix = make_S_matrix_masks(
                order,
                DMD_size,
                slit_width,
                slit_length,
                Xo,
                Yo,
                folder
            )
            name = f'S{order}_mask_{slit_width}w_{order:03d}.bmp'
        if matrix_type == 'H':
            mask_set_a, mask_set_b, matrix = make_H_matrix_masks(
                order,
                DMD_size,
                slit_width,
                slit_length,
                Xo,
                Yo,
                folder
            )
            name = f"H{order}_mask_{slit_width}w_ab_{order:03d}.bmp"
        self.mask_name.set(name)
        self.rename_value.set("")


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        self.rename_button.config(text=f"Rename '{self.mask_name.get()}' to:")
