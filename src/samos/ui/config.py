"""
SAMOS Configuration tk Frame Class
"""
import csv
from datetime import datetime
import logging
import os
from pathlib import Path
import shutil

import tkinter as tk
from tkinter import ttk

from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class ConfigPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS Configuration", **kwargs)

        # Set up directories frame
        frame = ttk.LabelFrame(self.main_frame, text="Files", borderwidth=2)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        initial_files_location = "module"
        if "SAMOS_FILES_LOCATION" in os.environ:
            initial_files_location = os.environ["SAMOS_FILES_LOCATION"]
        self.files_loc = tk.StringVar(self, initial_files_location)
        custom_files_initial = ""
        if "SAMOS_CUSTOM_FILES_LOCATION" in os.environ:
            custom_files_initial = os.environ["SAMOS_CUSTOM_FILES_LOCATION"]
        self.custom_files_path = tk.StringVar(self, custom_files_initial)
        ttk.Label(frame, text="Store files:", anchor=tk.W).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="In Module", variable=self.files_loc, value="module", command=self.set_files_base,
                            anchor=tk.W)
        b.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Home Directory", variable=self.files_loc, value="home", command=self.set_files_base,
                            anchor=tk.W)
        b.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Working Directory", variable=self.files_loc, value="cwd", command=self.set_files_base,
                            anchor=tk.W)
        b.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Custom Location", variable=self.files_loc, value="custom", command=self.set_files_base,
                            anchor=tk.W)
        b.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, textvariable=self.custom_files_path).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="Nightly Files Location:", anchor=tk.W).grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.nightly_files_dir = tk.StringVar(self, get_fits_dir())
        tk.Label(frame, textvariable=self.nightly_files_dir, width=75).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Set up servers frame
        frame = ttk.LabelFrame(self.main_frame, text="Servers", borderwidth=2)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.ip_loc = tk.StringVar(self, "inside")
        b = tk.Radiobutton(frame, text='Inside', variable=self.ip_loc, value='inside', command=self.load_IP_default)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text='Outside (with VPN)', variable=self.ip_loc, value='outside', command=self.load_IP_default)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text='SIMULATED', fg='red', variable=self.ip_loc, value='simulated', command=self.load_IP_default)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)

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

        self.IP_PCM = tk.StringVar(self, self.PAR.IP_dict['IP_PCM'])
        tk.Entry(frame, width=20, textvariable=self.IP_PCM).grid(row=1, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_CCD = tk.StringVar(self, self.PAR.IP_dict['IP_CCD'])
        tk.Entry(frame, width=20, textvariable=self.IP_CCD).grid(row=2, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_DMD = tk.StringVar(self, self.PAR.IP_dict['IP_DMD'])
        tk.Entry(frame, width=20, textvariable=self.IP_DMD).grid(row=3, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SOAR = tk.StringVar(self, self.PAR.IP_dict['IP_SOAR'])
        tk.Entry(frame, width=20, textvariable=self.IP_SOAR).grid(row=4, column=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SAMI = tk.StringVar(self, self.PAR.IP_dict['IP_SAMI'])
        tk.Entry(frame, width=20, textvariable=self.IP_SAMI).grid(row=5, column=2, columnspan=2, sticky=TK_STICKY_ALL)

        b = ttk.Button(frame, text="Initialize Components", command=self.startup)
        b.grid(row=6, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # Other entries
        frame = ttk.LabelFrame(self.main_frame, text="Observer Data", borderwidth=2)
        frame.grid(row=0, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)

        ttk.Label(frame, text="Telescope").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.Telescope = tk.StringVar()
        self.Telescope.set(self.PAR.PotN['Telescope'])
        tk.Entry(frame, width=20, textvariable=self.Telescope).grid(row=0, column=1, sticky=TK_STICKY_ALL)

        ttk.Label(frame, text="Program ID").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.Program_ID = tk.StringVar()
        self.Program_ID.set(self.PAR.PotN['Program ID'])
        tk.Entry(frame, width=20, textvariable=self.Program_ID).grid(row=1, column=1, sticky=TK_STICKY_ALL)

        ttk.Label(frame, text="Proposal Title").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.Proposal_Title = tk.StringVar()
        self.Proposal_Title.set(self.PAR.PotN['Proposal Title'])
        tk.Entry(frame, width=20, textvariable=self.Proposal_Title).grid(row=2, column=1, sticky=TK_STICKY_ALL)

        ttk.Label(frame, text="Principal Investigator").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.Principal_Investigator = tk.StringVar()
        self.Principal_Investigator.set(self.PAR.PotN['Principal Investigator'])
        tk.Entry(frame, width=20, textvariable=self.Principal_Investigator).grid(row=3, column=1, sticky=TK_STICKY_ALL)

        ttk.Label(frame, text="Observer").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.Observer = tk.StringVar()
        self.Observer.set(self.PAR.PotN['Observer'])
        tk.Entry(frame, width=20, textvariable=self.Observer).grid(row=4, column=1, sticky=TK_STICKY_ALL)

        ttk.Label(frame, text="Telescope Operator ").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.TO_var = tk.StringVar()
        self.TO_var.set(self.PAR.PotN['Telescope Operator'])
        tk.Entry(frame, width=20, textvariable=self.TO_var).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Initialize
        frame = ttk.LabelFrame(self.main_frame, text="Logbook", borderwidth=2)
        frame.grid(row=1, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        b = ttk.Button(frame, text="Initialize Logbook", command=self.LogBookstartup)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)


    def set_files_base(self):
        os.environ["SAMOS_FILES_LOCATION"] = self.files_loc.get()
        if self.files_loc.get() == "custom" and (not Path(self.custom_files_path.get()).is_dir()):
            custom_loc = ttk.filedialog.askdirectory(initialdir=Path.cwd(), title="Select a Location to store files")
            self.custom_files_path.set(custom_loc)
            os.environ["SAMOS_CUSTOM_FILES_LOCATION"] = custom_loc
        self.nightly_files_dir.set(get_fits_dir())


    def LogBookstartup(self):
        self.PAR.PotN['Program ID'] = self.Program_ID.get()
        self.PAR.PotN['Observer'] = self.Observer.get()
        self.PAR.PotN['Telescope Operator'] = self.TO_var.get()
        self.PAR.PotN['Telescope'] = self.Telescope.get()
        self.PAR.PotN['PI'] = self.Principal_Investigator.get()
        self.PAR.PotN['ProposalTitle'] = self.Proposal_Title.get()
        self.PAR.update_PotN()
        self.PAR.create_log_file()


    @check_enabled
    def startup(self):
        self.logger.info("CONFIG_GUI: entering startup.")
        self.PCM.initialize_motors()
        self.PCM.power_on()
        self.CCD.initialize_ccd()
        self.DMD.initialize()
        self.DMD._open()
        self.SOAR.echo_client()
        self.update_status_box()
        self.logger.info("CONFIG_GUI: startup complete.")


    @check_enabled
    def load_IP_user(self):
        if self.ip_loc.get() == 'inside':
            ip_file = get_data_file("system", "IP_addresses_user_inside.csv")
        elif self.ip_loc.get() == 'outside':
            ip_file = get_data_file("system", "IP_addresses_user_outside.csv")
        elif self.ip_loc.get() == 'simulated':
            ip_file = get_data_file("system", "IP_addresses_SIMULATED.csv")
        ip_file_default = get_data_file("system", "IP_addresses_default.csv")
        shutil.copy(ip_file, ip_file_default)
        return self._load_ip(ip_file)


    @check_enabled
    def load_IP_default(self):
        if self.ip_loc.get() == 'inside':
            ip_file = get_data_file("system", "IP_addresses_default_inside.csv")
        elif self.ip_loc.get() == 'outside':
            ip_file = get_data_file("system", "IP_addresses_default_outside.csv")
        elif self.ip_loc.get() == 'simulated':
            ip_file = get_data_file("system", "IP_addresses_SIMULATED.csv")
        ip_file_default = get_data_file("system", "IP_addresses_default.csv")
        shutil.copy(ip_file, ip_file_default)
        return self._load_ip(ip_file_default)


    def save_IP_user(self):
        if self.ip_loc.get() == 'inside':
            ip_file = get_data_file("system", "IP_addresses_user_inside.csv")
        elif self.ip_loc.get() == 'outside':
            ip_file = get_data_file("system", "IP_addresses_user_outside.csv")
        elif self.ip_loc.get() == 'simulated':
            self.logger.error("ERROR: simulated IP addresses should not be changed!")
            return
        ip_file_default = get_data_file("system", "IP_addresses_default.csv")
        shutil.copy(ip_file, ip_file_default)
        
        with open(ip_file, "w") as outf:
            with csv.writer(outf) as w:
                for key in self.PAR.ip_dict:
                    w.writerow([key, self.PAR.ip_dict[key]])
        self.save_IP_status()


    def update_status_box(self):
        if self.PCM.is_on:
            self.PAR.IP_status_dict['IP_PCM'] = True
            self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_ON_COLOR)
            if self.PCM.filter_moving or self.PCM.grism_moving:
                self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_PENDING_COLOR)
        else:
            self.status_box.itemconfig("pcm_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
            self.PAR.IP_status_dict['IP_PCM'] = False
        if self.CCD.ccd_on:
            self.PAR.IP_status_dict['IP_CCD'] = True
            self.status_box.itemconfig("ccd_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("ccd_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
            self.PAR.IP_status_dict['IP_CCD'] = False
        if self.DMD.is_on:
            self.PAR.IP_status_dict['IP_DMD'] = True
            self.status_box.itemconfig("dmd_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("dmd_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
            self.PAR.IP_status_dict['IP_DMD'] = False
        if self.SOAR.is_on:
            self.PAR.IP_status_dict['IP_SOAR'] = True
            self.status_box.itemconfig("soar_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("soar_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
            self.PAR.IP_status_dict['IP_SOAR'] = False
        sami_status = False
        if sami_status:
            self.PAR.IP_status_dict['IP_SAMI'] = True
            self.status_box.itemconfig("sami_ind", fill=INDICATOR_LIGHT_ON_COLOR)
        else:
            self.status_box.itemconfig("sami_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
            self.PAR.IP_status_dict['IP_SAMI'] = False


    def _load_ip(self, data_file):
        with open(data_file, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        
        for system in self.SYSTEMS:
            key = "IP_{}".format(system)
            self.PAR.IP_dict[key] = dict_from_csv[key]
            getattr(self, key).set(dict_from_csv[key])
        
        if self.ip_loc.get() == "simulated":
            self.parent.initialize_simulator()
        else:
            self.parent.destroy_simulator()

        return self.PAR.IP_dict


    SYSTEMS = ["PCM", "CCD", "DMD", "SOAR", "SAMI"]
