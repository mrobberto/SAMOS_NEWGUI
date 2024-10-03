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
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class ConfigPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS Configuration", **kwargs)
        self.logger.info("Setting up config page")
        self.prefs_dict = {}
        try:
            prefs_file = get_data_file("system", "preferences.yaml")
            with open(prefs_file, 'r') as inf:
                self.prefs_dict = yaml.safe_load(inf)
        except FileNotFoundError as e:
            self.logger.warning("No preferences file found")

        # Set up directories frame
        frame = ttk.LabelFrame(self.main_frame, text="Files", borderwidth=2)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        initial_files_location = "module"
        custom_files_initial = ""
        if "SAMOS_FILES_LOCATION" in os.environ:
            initial_files_location = os.environ["SAMOS_FILES_LOCATION"]
            if initial_files_location == "custom" and "SAMOS_CUSTOM_FILES_LOCATION" in os.environ:
                custom_files_initial = os.environ["SAMOS_CUSTOM_FILES_LOCATION"]
        if "files_location" in self.prefs_dict:
            initial_files_location = self.prefs_dict["files_location"]
            os.environ["SAMOS_FILES_LOCATION"] = self.prefs_dict["files_location"]
            if (initial_files_location == "custom") and ("custom_files_location" in self.prefs_dict):
                custom_files_initial = self.prefs_dict["custom_files_location"]
                os.environ["SAMOS_CUSTOM_FILES_LOCATION"] = self.prefs_dict["custom_files_location"]
        self.files_loc = tk.StringVar(self, initial_files_location)
        self.custom_files_path = tk.StringVar(self, custom_files_initial)
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
        self.nightly_files_dir = tk.StringVar(self, get_fits_dir())
        tk.Label(frame, textvariable=self.nightly_files_dir, width=75).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Set up servers frame
        frame = ttk.LabelFrame(self.main_frame, text="Servers", borderwidth=2)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        initial_ip_loc = "inside"
        if "ip_loc" in self.prefs_dict:
            initial_ip_loc = self.prefs_dict["ip_loc"]
        self.ip_loc = tk.StringVar(self, initial_ip_loc)
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

        b = ttk.Button(frame, text="Initialize Components", command=self.startup, bootstyle="success")
        b.grid(row=6, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # Observer Data
        frame = ttk.LabelFrame(self.main_frame, text="Observer Data", borderwidth=2)
        frame.grid(row=0, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        # Telescope
        ttk.Label(frame, text="Telescope").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.Telescope = tk.StringVar(self, self.PAR.PotN['Telescope'])
        ttk.Entry(frame, width=20, textvariable=self.Telescope).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # Program ID
        ttk.Label(frame, text="Program ID").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.Program_ID = tk.StringVar(self, self.PAR.PotN['Program ID'])
        ttk.Entry(frame, width=20, textvariable=self.Program_ID).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Proposal Title
        ttk.Label(frame, text="Proposal Title").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.Proposal_Title = tk.StringVar(self, self.PAR.PotN['Proposal Title'])
        ttk.Entry(frame, width=20, textvariable=self.Proposal_Title).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        # Principal Investigator
        ttk.Label(frame, text="Principal Investigator").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.Principal_Investigator = tk.StringVar(self, self.PAR.PotN['Principal Investigator'])
        ttk.Entry(frame, width=20, textvariable=self.Principal_Investigator).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        # Observer
        ttk.Label(frame, text="Observer").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.Observer = tk.StringVar(self, self.PAR.PotN['Observer'])
        ttk.Entry(frame, width=20, textvariable=self.Observer).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        # TO
        ttk.Label(frame, text="Telescope Operator ").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.Telescope_Operator = tk.StringVar(self, self.PAR.PotN['Telescope Operator'])
        ttk.Entry(frame, width=20, textvariable=self.Telescope_Operator).grid(row=5, column=1, sticky=TK_STICKY_ALL)
        # Save        
        w = ttk.Button(frame, text="Save Changes", command=self.save_potn_changes)
        w.grid(row=6, column=0, sticky=TK_STICKY_ALL)

        # Initialize
        frame = ttk.LabelFrame(self.main_frame, text="Logbook", borderwidth=2)
        frame.grid(row=1, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        self.init_logbook_button = ttk.Button(frame, text="Initialize Logbook", command=self.LogBookstartup)
        self.init_logbook_label = ttk.Label(frame, text="Logbook File:")
        self.logbook_location = tk.StringVar(self, self.PAR.logfile_name)
        self.logbook_location_label = ttk.Label(frame, textvariable=self.logbook_location)
        if self.PAR.logbook_exists:
            self.init_logbook_label.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.logbook_location_label.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        else:
            self.init_logbook_button.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.logger.info("Finished setting up config page. Starting initial widget check.")
        self.set_enabled()
        self.logger.info("Finished initial widget check.")

        # Settings
        frame = ttk.LabelFrame(self.main_frame, text="Settings", borderwidth=2)
        frame.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL, padx=3, pady=3)

        # Flip the X axis when loading images
        self.flip_x_on_open = tk.BooleanVar(self, self.PAR.flip_x_on_open)
        b = ttk.Checkbutton(frame, command=self.set_image_flip, text="Flip Images on Open", variable=self.flip_x_on_open, onvalue=True, offvalue=False)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)


    @check_enabled
    def set_files_base(self):
        self.old_files_loc = os.environ.get("SAMOS_FILES_LOCATION", "unknown")
        os.environ["SAMOS_FILES_LOCATION"] = self.files_loc.get()
        self.prefs_dict["files_location"] = self.files_loc.get()
        if (self.files_loc.get() == "custom"):
            custom_loc = self.prefs_dict["custom_files_location"]
            if (self.old_files_loc != "custom"):
                initial_dir = Path.cwd()
                if Path(self.custom_files_path.get()).is_dir():
                    initial_dir = Path(self.custom_files_path.get())
                custom_loc = tk.filedialog.askdirectory(initialdir=initial_dir, title="Select a Location to store files")
            self.custom_files_path.set(custom_loc)
            os.environ["SAMOS_CUSTOM_FILES_LOCATION"] = custom_loc
            self.prefs_dict["custom_files_location"] = custom_loc
        prefs_file = get_data_file("system") / "preferences.yaml"
        with open(prefs_file, "w") as outf:
            yaml.dump(self.prefs_dict, outf, default_flow_style=False)
        self.nightly_files_dir.set(get_fits_dir())


    @check_enabled
    def set_image_flip(self):
        self.PAR.flip_x_on_open = self.flip_x_on_open.get()


    def save_potn_changes(self):
        self.PAR.PotN['Telescope'] = self.Telescope.get().strip()
        self.PAR.PotN['Program ID'] = self.Program_ID.get().strip()
        self.PAR.PotN['Proposal Title'] = self.Proposal_Title.get().strip()
        self.PAR.PotN['Principal Investigator'] = self.Principal_Investigator.get().strip()
        self.PAR.PotN['Observer'] = self.Observer.get().strip()
        self.PAR.PotN['Telescope Operator'] = self.Telescope_Operator.get().strip()
        self.PAR.update_PotN()


    @check_enabled
    def LogBookstartup(self):
        self.save_potn_changes()
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
        self.prefs_dict["ip_loc"] = self.ip_loc.get()
        prefs_file = get_data_file("system") / "preferences.yaml"
        with open(prefs_file, "w") as outf:
            yaml.dump(self.prefs_dict, outf, default_flow_style=False)
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


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        self.flip_x_on_open.set(self.PAR.flip_x_on_open)
        if self.PAR.logbook_exists:
            self.init_logbook_button.grid_forget()
            self.init_logbook_label.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.logbook_location_label.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        else:
            self.init_logbook_button.grid(row=0, column=0, sticky=TK_STICKY_ALL)
            self.init_logbook_label.grid_forget()
            self.logbook_location_label.grid_forget()            


    SYSTEMS = ["PCM", "CCD", "DMD", "SOAR", "SAMI"]
