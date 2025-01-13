"""
SAMOS Configuration tk Frame Class
"""
import csv
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil
import yaml

import tkinter as tk
import ttkbootstrap as ttk
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class ConfigPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS Configuration", **kwargs)
        self.logger.info("Setting up config page")

        # Set up directories frame
        frame = ttk.LabelFrame(self.main_frame, text="Files", borderwidth=2)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.files_loc = self.make_db_var(tk.StringVar, "config_files_storage_location", "module")
        self.custom_files_path = self.make_db_var(tk.StringVar, "config_custom_files_location", "")
        ttk.Label(frame, text="Store files:", anchor=tk.W).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Radiobutton(frame, text="In Module", variable=self.files_loc, value="module", command=self.set_files_base)
        b.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Radiobutton(frame, text="Home Directory", variable=self.files_loc, value="home", command=self.set_files_base)
        b.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Radiobutton(frame, text="Working Directory", variable=self.files_loc, value="cwd", command=self.set_files_base)
        b.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Radiobutton(frame, text="Custom Location", variable=self.files_loc, value="custom", command=self.set_files_base)
        b.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, textvariable=self.custom_files_path).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="Nightly Files Location:", anchor=tk.W).grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.nightly_files_dir = self.make_db_var(tk.StringVar, "config_nightly_files_dir", "")
        tk.Label(frame, textvariable=self.nightly_files_dir, width=75).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Set up servers frame
        frame = ttk.LabelFrame(self.main_frame, text="Servers", borderwidth=2)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.ip_loc = self.make_db_var(tk.StringVar, "config_ip_status", "disconnected")
        b = tk.Radiobutton(frame, text='Connected', variable=self.ip_loc, value='connected')
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text='Disconnected', variable=self.ip_loc, value='disconnected')
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)

        # Hardware Labels
        ttk.Label(frame, text="PCM").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="CCD").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="DMD").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="SOAR Telescope").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="SOAR SAMI").grid(row=5, column=0, sticky=TK_STICKY_ALL)

        # Status Indicator Frame
        self.status_box = tk.Canvas(frame, background="gray", width=50)
        self.status_box.grid(row=1, column=1, rowspan=5, sticky=TK_STICKY_ALL)
        self.status_box.create_oval(10, 10, 40, 40, fill=INDICATOR_LIGHT_PENDING_COLOR, outline=None, tags=["pcm_ind"])
        self.status_box.create_oval(10, 48, 40, 78, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["ccd_ind"], outline=None)
        self.status_box.create_oval(10, 86, 40, 116, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["dmd_ind"], outline=None)
        self.status_box.create_oval(10, 124, 40, 154, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["soar_ind"], outline=None)
        self.status_box.create_oval(10, 162, 40, 192, fill=INDICATOR_LIGHT_PENDING_COLOR, tags=["sami_ind"], outline=None)
        # Register the frame with PAR
        self.PAR.add_status_indicator(self.status_box, self.update_status_box)

        self.IP_PCM = self.make_db_var(tk.StringVar, "config_ip_pcm", "172.16.0.128:1000")
        tk.Entry(frame, width=20, textvariable=self.IP_PCM).grid(row=1, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_CCD = self.make_db_var(tk.StringVar, "config_ip_ccd", "172.16.0.245:80")
        tk.Entry(frame, width=20, textvariable=self.IP_CCD).grid(row=2, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_DMD = self.make_db_var(tk.StringVar, "config_ip_dmd", "172.16.0.141:8888")
        tk.Entry(frame, width=20, textvariable=self.IP_DMD).grid(row=3, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SOAR = self.make_db_var(tk.StringVar, "config_ip_soar", "139.220.15.2:40050")
        tk.Entry(frame, width=20, textvariable=self.IP_SOAR).grid(row=4, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SAMI = self.make_db_var(tk.StringVar, "config_ip_sami", "139.229.15:63")
        tk.Entry(frame, width=20, textvariable=self.IP_SAMI).grid(row=5, column=2, columnspan=2, sticky=TK_STICKY_ALL)

        b = ttk.Button(frame, text="Initialize Components", command=self.startup, bootstyle="success")
        b.grid(row=6, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # Observer Data
        frame = ttk.LabelFrame(self.main_frame, text="Observer Data", borderwidth=2)
        frame.grid(row=0, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        # Telescope
        ttk.Label(frame, text="Telescope").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.Telescope = self.make_db_var(tk.StringVar, "POTN_Telescope", "")
        ttk.Entry(frame, width=20, textvariable=self.Telescope).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # Program ID
        ttk.Label(frame, text="Program ID").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.Program_ID = self.make_db_var(tk.StringVar, "POTN_Program", "")
        ttk.Entry(frame, width=20, textvariable=self.Program_ID).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Proposal Title
        ttk.Label(frame, text="Proposal Title").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.Proposal_Title = self.make_db_var(tk.StringVar, "POTN_Title", "")
        ttk.Entry(frame, width=20, textvariable=self.Proposal_Title).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        # Principal Investigator
        ttk.Label(frame, text="Principal Investigator").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.Principal_Investigator = self.make_db_var(tk.StringVar, "POTN_PI", "")
        ttk.Entry(frame, width=20, textvariable=self.Principal_Investigator).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        # Observer
        ttk.Label(frame, text="Observer").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.Observer = self.make_db_var(tk.StringVar, "POTN_Observer", "")
        ttk.Entry(frame, width=20, textvariable=self.Observer).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        # TO
        ttk.Label(frame, text="Telescope Operator ").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.Telescope_Operator = self.make_db_var(tk.StringVar, "POTN_Telescope_Operator", "")
        ttk.Entry(frame, width=20, textvariable=self.Telescope_Operator).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Initialize
        frame = ttk.LabelFrame(self.main_frame, text="Logbook", borderwidth=2)
        frame.grid(row=1, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.init_logbook_button = ttk.Button(frame, text="Initialize Logbook", command=self.LogBookstartup)
        self.init_logbook_label = ttk.Label(frame, text="Logbook File:")
        self.logbook_location = self.make_db_var(tk.StringVar, "config_logbook_path", "")
        self.logbook_location_label = ttk.Label(frame, textvariable=self.logbook_location)
        if Path(self.logbook_location.get()).is_file():
            self.init_logbook_label.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.logbook_location_label.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        else:
            self.init_logbook_button.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Settings
        frame = ttk.LabelFrame(self.main_frame, text="Settings", borderwidth=2)
        frame.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.logger.info("Finished setting up config page. Starting initial widget check.")
        self.set_enabled()
        self.logger.info("Finished initial widget check.")


    @check_enabled
    def set_files_base(self):
        self.logger.info(f"Set files to be stored in {self.files_loc.get()}")
        if (self.files_loc.get() == "custom"):
            custom_path = Path(self.custom_files_path.get())
            self.logger.info(f"\tCustom files location is '{self.custom_files_path.get()}'")
            self.logger.info(f"\tAs a path, this is '{custom_path}'")
            self.logger.info(f"\tIs it a directory: {custom_path.is_dir()}")
            self.logger.info(f"\tDoes it exist: {custom_path.exists()}")
            if (not custom_path.is_dir()) or (not custom_path.exists()) or (self.custom_files_path.get() == ""):
                initial_dir = Path.cwd()
                title = "Select a Location to store files"
                custom_loc = tk.filedialog.askdirectory(initialdir=initial_dir, title=title)
                self.custom_files_path.set(custom_loc)


    @check_enabled
    def LogBookstartup(self):
        self.PAR.create_log_file()


    @check_enabled
    def startup(self):
        self.logger.info("CONFIG_GUI: entering startup.")
        if self.ip_loc.get() == "connected":
            self.PCM.initialize_motors()
            self.PCM.power_on()
            self.CCD.initialize_ccd()
            self.DMD.initialize()
            self.DMD._open()
            self.SOAR.echo_client()
        else:
            self.logger.info("Disconnected. Doing nothing.")
        self.update_status_box()
        self.logger.info("CONFIG_GUI: startup complete.")


    def update_status_box(self):
        if self.PCM.is_on:
            self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_ON_COLOR)
            if self.PCM.filter_moving or self.PCM.grism_moving:
                self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_PENDING_COLOR)
        else:
            self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.CCD.ccd_on:
            self.status_box.itemconfig("ccd_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("ccd_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.DMD.is_on:
            self.status_box.itemconfig("dmd_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("dmd_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        if self.SOAR.is_on:
            self.status_box.itemconfig("soar_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("soar_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
        sami_status = False
        if sami_status:
            self.status_box.itemconfig("sami_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("sami_ind", fill=INDICATOR_LIGHT_OFF_COLOR)


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        if Path(self.logbook_location.get()).is_file():
            self.init_logbook_button.grid_forget()
            self.init_logbook_label.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.logbook_location_label.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        else:
            self.init_logbook_button.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.init_logbook_label.grid_forget()
            self.logbook_location_label.grid_forget()            
