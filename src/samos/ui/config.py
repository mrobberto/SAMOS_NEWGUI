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

from .common_frame import SAMOSFrame


class ConfigPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS Configuration", **kwargs)

        # Set up directories frame
        frame = tk.LabelFrame(self.main_frame, text="Files", font=BIGFONT, borderwidth=2)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        initial_files_location = "module"
        if "SAMOS_FILES_LOCATION" in os.environ:
            initial_files_location = os.environ["SAMOS_FILES_LOCATION"]
        self.files_loc = tk.StringVar(self, initial_files_location)
        custom_files_initial = ""
        if "SAMOS_CUSTOM_FILES_LOCATION" in os.environ:
            custom_files_initial = os.environ["SAMOS_CUSTOM_FILES_LOCATION"]
        self.custom_files_path = tk.StringVar(self, custom_files_initial)
        tk.Label(frame, text="Store files:", anchor=tk.W).grid(row=0, column=0, sticky=TK_STICKY_ALL)
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
        tk.Label(frame, textvariable=self.custom_files_path).grid(row=5, column=0, sticky=TK_STICKY_ALL)

        # Set up servers frame
        frame = tk.LabelFrame(self.main_frame, text="Servers", font=BIGFONT, borderwidth=2)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL, padx=3, pady=3)

        self.ip_loc = tk.StringVar(self, "inside")
        b = tk.Radiobutton(frame, text='Inside', variable=self.ip_loc, value='inside', command=self.load_IP_default)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text='Outside (with VPN)', variable=self.ip_loc, value='outside', command=self.load_IP_default)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text='SIMULATED', fg='red', variable=self.ip_loc, value='simulated', command=self.load_IP_default)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)

        tk.Label(frame, text="PCM").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="CCD").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="DMD").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="SOAR Telescope").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="SOAR SAMI").grid(row=5, column=0, sticky=TK_STICKY_ALL)

        self.IP_PCM = tk.StringVar()
        self.IP_PCM.set(self.PAR.IP_dict['IP_PCM'])
        tk.Entry(frame, width=20, textvariable=self.IP_PCM).grid(row=1, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_CCD = tk.StringVar()
        self.IP_CCD.set(self.PAR.IP_dict['IP_CCD'])
        tk.Entry(frame, width=20, textvariable=self.IP_CCD).grid(row=2, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_DMD = tk.StringVar()
        self.IP_DMD.set(self.PAR.IP_dict['IP_DMD'])
        tk.Entry(frame, width=20, textvariable=self.IP_DMD).grid(row=3, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SOAR = tk.StringVar()
        self.IP_SOAR.set(self.PAR.IP_dict['IP_SOAR'])
        tk.Entry(frame, width=20, textvariable=self.IP_SOAR).grid(row=4, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.IP_SAMI = tk.StringVar()
        self.IP_SAMI.set(self.PAR.IP_dict['IP_SAMI'])
        tk.Entry(frame, width=20, textvariable=self.IP_SAMI).grid(row=5, column=1, columnspan=2, sticky=TK_STICKY_ALL)

        self.IP_Motors_on_button = tk.Button(frame, image=self.off_sm, bd=0, command=self.Motors_switch)
        self.IP_Motors_on_button.grid(row=1, column=3, sticky=TK_STICKY_ALL)
        self.CCD_on_button = tk.Button(frame, image=self.off_sm, bd=0, command=self.CCD_switch)
        self.CCD_on_button.grid(row=2, column=3, sticky=TK_STICKY_ALL)
        self.DMD_on_button = tk.Button(frame, image=self.off_sm, bd=0, command=self.DMD_switch)
        self.DMD_on_button.grid(row=3, column=3, sticky=TK_STICKY_ALL)
        self.SOAR_Tel_on_button = tk.Button(frame, image=self.off_sm, bd=0, command=self.SOAR_switch)
        self.SOAR_Tel_on_button.grid(row=4, column=3, sticky=TK_STICKY_ALL)
        self.SOAR_SAMI_on_button = tk.Button(frame, image=self.off_sm, bd=0, command=self.SAMI_switch)
        self.SOAR_SAMI_on_button.grid(row=5, column=3, sticky=TK_STICKY_ALL)

        # Other entries
        frame = tk.LabelFrame(self.main_frame, text="Observer Data", font=BIGFONT, borderwidth=2)
        frame.grid(row=0, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)

        tk.Label(frame, text="Telescope").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.Telescope = tk.StringVar()
        self.Telescope.set(self.PAR.PotN['Telescope'])
        tk.Entry(frame, width=20, textvariable=self.Telescope).grid(row=0, column=1, sticky=TK_STICKY_ALL)

        tk.Label(frame, text="Program ID").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.Program_ID = tk.StringVar()
        self.Program_ID.set(self.PAR.PotN['Program ID'])
        tk.Entry(frame, width=20, textvariable=self.Program_ID).grid(row=1, column=1, sticky=TK_STICKY_ALL)

        tk.Label(frame, text="Proposal Title").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.Proposal_Title = tk.StringVar()
        self.Proposal_Title.set(self.PAR.PotN['Proposal Title'])
        tk.Entry(frame, width=20, textvariable=self.Proposal_Title).grid(row=2, column=1, sticky=TK_STICKY_ALL)

        tk.Label(frame, text="Principal Investigator").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.Principal_Investigator = tk.StringVar()
        self.Principal_Investigator.set(self.PAR.PotN['Principal Investigator'])
        tk.Entry(frame, width=20, textvariable=self.Principal_Investigator).grid(row=3, column=1, sticky=TK_STICKY_ALL)

        tk.Label(frame, text="Observer").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.Observer = tk.StringVar()
        self.Observer.set(self.PAR.PotN['Observer'])
        tk.Entry(frame, width=20, textvariable=self.Observer).grid(row=4, column=1, sticky=TK_STICKY_ALL)

        tk.Label(frame, text="Telescope Operator ").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.TO_var = tk.StringVar()
        self.TO_var.set(self.PAR.PotN['Telescope Operator'])
        tk.Entry(frame, width=20, textvariable=self.TO_var).grid(row=5, column=1, sticky=TK_STICKY_ALL)

        # Initialize
        frame = tk.LabelFrame(self.main_frame, text="Logbook", font=BIGFONT, borderwidth=2)
        frame.grid(row=1, column=1, sticky=TK_STICKY_ALL, padx=3, pady=3)
        b = tk.Button(frame, text="Initialize Logbook", relief="raised", command=self.LogBookstartup)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)


    def set_files_base(self):
        os.environ["SAMOS_FILES_LOCATION"] = self.files_loc.get()
        if self.files_loc.get() == "custom" and (not Path(self.custom_files_path.get()).is_dir()):
            custom_loc = tk.filedialog.askdirectory(initialdir=Path.cwd(), title="Select a Location to store files")
            self.custom_files_path.set(custom_loc)
            os.environ["SAMOS_CUSTOM_FILES_LOCATION"] = custom_loc


    def LogBookstartup(self):
        self.PAR.PotN['Program ID'] = self.Program_ID.get()
        self.PAR.PotN['Observer'] = self.Observer.get()
        self.PAR.PotN['Telescope Operator'] = self.TO_var.get()
        self.PAR.PotN['Telescope'] = self.Telescope.get()
        self.PAR.PotN['PI'] = self.Principal_Investigator.get()
        self.PAR.PotN['ProposalTitle'] = self.Proposal_Title.get()
        self.PAR.update_PotN()
        self.PAR.create_log_file()


    def startup(self):
        self.logger.info("CONFIG_GUI: entering startup.")
        self.load_IP_default()
        self.IP_echo()
        
        if self.PAR.IP_status_dict['IP_DMD'] == True:
            IP = self.PAR.IP_dict['IP_DMD']
            [host, port] = IP.split(":")
            self.DMD.initialize(address=host, port=int(port))
        if self.PAR.IP_status_dict['IP_PCM'] == True:
            PCM.power_on()
        self.logger.info("CONFIG_GUI: startup complete.")


    def load_dir_default(self):
        return self._load_dir("dirlist_default.csv")


    def load_dir_user(self):
        return self._load_dir("dirlist_user.csv")


    def save_dir_user(self):
        with open(get_data_file("system", "dirlist_user.csv"), "w") as file_dirlist:
            with csv.writer(file_dirlist) as w:
                for system in self.SYSTEMS:
                    key = "dir_{}".format(system)
                    w.writerow([key, getattr(self, key)])
                    self.PAR.dir_dict[key] = getattr(self, key)


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


    def save_IP_status(self):
        with open(get_data_file("system", "IP_status_dict.csv"), "w") as outf:
            with csv.writer(outf) as w:
                for key, val in self.PAR.IP_status_dict.items():
                    w.writerow([key, val])


    def IP_echo(self):
        # Motors Alive?
        self.logger.info("Checking Motor Status")
        IP = self.PAR.IP_dict['IP_PCM']
        [host, port] = IP.split(":")
        PCM.initialize(address=host, port=int(port))
        answer = PCM.echo_client()
        if answer != "no connection":
            self.logger.info("Motors are on")
            self.IP_Motors_on_button.config(image=self.on_sm)
            self.logger.info('echo from server:')
            self.PAR.IP_status_dict['IP_PCM'] = True
            # PCM.power_on()

        else:
            self.logger.warning("Motors are off")
            self.IP_Motors_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_PCM'] = False


        # CCD alive?
        self.logger.info("Checking CCD status")
        url_name = "http://"+os.path.join(self.PAR.IP_dict['IP_CCD'])  # +'/'
        answer = (CCD.get_url_as_string(url_name))[:6]  # expect <HTML>
        self.logger.info("CCD returns: '''{}'''".format(answer))
        if str(answer) == '<HTML>':
            self.logger.info("CCD is on")
            self.CCD_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_CCD'] = True
        else:
            self.logger.warning("CCD is off\n")
            self.CCD_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_CCD'] = False

        # DMD alive?
        self.logger.info("Checking DMD status")
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        self.DMD.initialize(address=host, port=int(port))
        answer = self.DMD._open()
        if answer != "no DMD":
            self.logger.info("DMD is on")
            self.DMD_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_DMD'] = True
        else:
            self.logger.warning("DMD is off")
            self.DMD_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_DMD'] = False

        self.save_IP_status()
        return self.PAR.IP_dict


    # Define our switch functions
    def Motors_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_PCM']:
            self.IP_Motors_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_PCM'] = False
            PCM.power_off()
        else:
            self.IP_Motors_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_PCM'] = True
            self.save_IP_status()
            PCM.IP_host = self.IP_PCM.get()
            PCM.power_on()
        self.save_IP_status()
        self.logger.info("SAMOS IP: {}".format(self.PAR.IP_status_dict))


    def CCD_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_CCD']:
            self.CCD_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_CCD'] = False
        else:
            self.CCD_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_CCD'] = True
        self.save_IP_status()
        self.logger.info("SAMOS IP: {}".format(self.PAR.IP_status_dict))


    def DMD_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_DMD']:
            self.DMD_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_DMD'] = False
        else:
            self.DMD_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_DMD'] = True
        self.save_IP_status()
        self.logger.info("SAMOS IP: {}".format(self.PAR.IP_status_dict))


    def SOAR_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_SOAR']:
            self.SOAR_Tel_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_SOAR'] = False
        else:
            self.SOAR_Tel_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_SOAR'] = True
        self.save_IP_status()
        self.logger.info("SAMOS IP: {}".format(self.PAR.IP_status_dict))


    def SAMI_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_SAMI']:
            self.SOAR_SAMI_on_button.config(image=self.off_sm)
            self.PAR.IP_status_dict['IP_SAMI'] = False
        else:
            self.SOAR_SAMI_on_button.config(image=self.on_sm)
            self.PAR.IP_status_dict['IP_SAMI'] = True
        self.save_IP_status()
        self.logger.info("SAMOS IP: {}".format(self.PAR.IP_status_dict))
    

    def _load_dir(self, data_file):
        dict_from_csv = {}

        with open(get_data_file("system", data_file)) as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        
        for system in self.SYSTEMS:
            key = "dir_{}".format(system)
            setattr(self, key, dict_from_csv[key])
            self.PAR.dir_dict[key] = dict_from_csv[key]

        return self.PAR.dir_dict
    
    
    def _load_ip(self, data_file):
        with open(data_file, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        
        for system in self.SYSTEMS[:-2]:
            key = "IP_{}".format(system)
            self.PAR.IP_dict[key] = dict_from_csv[key]
            getattr(self, key).set(dict_from_csv[key])
        
        if self.ip_loc.get() == "simulated":
            self.parent.initialize_simulator()
        else:
            self.parent.destroy_simulator()

        return self.PAR.IP_dict


    SYSTEMS = ["PCM", "CCD", "DMD", "SOAR", "SAMI", "Astrom", "system"]
