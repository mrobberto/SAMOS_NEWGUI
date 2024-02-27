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

from samos.system.SAMOS_Functions import Class_SAMOS_Functions as SF
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *


class ConfigPage(ttk.Frame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(container)
        self.logger = logging.getLogger("samos")
        self.DMD = kwargs['DMD']

        self.PAR = SAMOS_Parameters()
        
        self.fits_dir = get_fits_dir()

        self.left_frame = tk.Frame(self, background="dark gray", width=600, height=500)
        self.left_frame.place(x=0, y=0)
        self.right_frame = tk.Frame(self, background="dark gray", width=400, height=500)
        self.right_frame.place(x=585, y=0)

        # Set up directories frame
        frame = tk.LabelFrame(self.left_frame, text="Directories", font=BIGFONT)
        frame.place(x=4, y=4, anchor="nw", width=592, height=225)

        tk.Label(frame, text=self.PAR.dir_dict['dir_Motors']).place(x=4, y=10)
        tk.Label(frame, text=self.PAR.dir_dict['dir_CCD']).place(x=4, y=35)
        tk.Label(frame, text=self.PAR.dir_dict['dir_DMD']).place(x=4, y=60)
        tk.Label(frame, text=self.PAR.dir_dict['dir_SOAR']).place(x=4, y=85)
        tk.Label(frame, text=self.PAR.dir_dict['dir_SAMI']).place(x=4, y=110)
        tk.Label(frame, text=self.PAR.dir_dict['dir_Astrom']).place(x=4, y=135)
        tk.Label(frame, text=self.PAR.dir_dict['dir_system']).place(x=4, y=160)

        self.dir_Motors = tk.StringVar()
        self.dir_Motors.set(self.PAR.dir_dict['dir_Motors'])
        tk.Entry(frame, width=25, textvariable=self.dir_Motors).place(x=140, y=10)
        self.dir_CCD = tk.StringVar()
        self.dir_CCD.set(self.PAR.dir_dict['dir_CCD'])
        tk.Entry(frame, width=25, textvariable=self.dir_CCD).place(x=140, y=35)
        self.dir_DMD = tk.StringVar()
        self.dir_DMD.set(self.PAR.dir_dict['dir_DMD'])
        tk.Entry(frame, width=25, textvariable=self.dir_DMD).place(x=140, y=60)
        self.dir_SOAR = tk.StringVar()
        self.dir_SOAR.set(self.PAR.dir_dict['dir_SOAR'])
        tk.Entry(frame, width=25, textvariable=self.dir_SOAR).place(x=140, y=85)
        self.dir_SAMI = tk.StringVar()
        self.dir_SAMI.set(self.PAR.dir_dict['dir_SAMI'])
        tk.Entry(frame, width=25, textvariable=self.dir_SAMI).place(x=140, y=110)
        self.dir_Astrom = tk.StringVar()
        self.dir_Astrom.set(self.PAR.dir_dict['dir_Astrom'])
        tk.Entry(frame, width=25, textvariable=self.dir_Astrom).place(x=140, y=135)
        self.dir_system = tk.StringVar()
        self.dir_system.set(self.PAR.dir_dict['dir_system'])
        tk.Entry(frame, width=25, textvariable=self.dir_system).place(x=140, y=160)

        tk.Button(frame, text="Load Current", relief="raised", command=self.load_dir_user, font=BIGFONT).place(x=380, y=10)
        tk.Button(frame, text="Save Current", relief="raised", command=self.save_dir_user, font=BIGFONT).place(x=380, y=50)
        tk.Button(frame, text="Load Default", relief="raised", command=self.load_dir_default, font=BIGFONT).place(x=380, y=90)

        # Set up servers frame
        frame = tk.LabelFrame(self.left_frame, text="Servers", font=BIGFONT)
        frame.place(x=4, y=234, anchor="nw", width=592, height=200)

        tk.Radiobutton(frame, text='Inside', variable=self.PAR.inoutvar, value='inside', 
                       command=self.load_IP_default).place(x=20, y=0)
        tk.Radiobutton(frame, text='Outside (with VPN)', variable=self.PAR.inoutvar, 
                       value='outside', command=self.load_IP_default).place(x=150, y=0)

        tk.Label(frame, text="SAMOS Motors").place(x=4, y=35)
        tk.Label(frame, text="CCD").place(x=4, y=60)
        tk.Label(frame, text="DMD").place(x=4, y=85)
        tk.Label(frame, text="SOAR Telescope").place(x=4, y=110)
        tk.Label(frame, text="SOAR SAMI").place(x=4, y=135)

        self.IP_Motors = tk.StringVar()
        self.IP_Motors.set(self.PAR.IP_dict['IP_Motors'])
        tk.Entry(frame, width=20, textvariable=self.IP_Motors).place(x=120, y=35)
        self.IP_CCD = tk.StringVar()
        self.IP_CCD.set(self.PAR.IP_dict['IP_CCD'])
        tk.Entry(frame, width=20, textvariable=self.IP_CCD).place(x=120, y=60)
        self.IP_DMD = tk.StringVar()
        self.IP_DMD.set(self.PAR.IP_dict['IP_DMD'])
        tk.Entry(frame, width=20, textvariable=self.IP_DMD).place(x=120, y=85)
        self.IP_SOAR = tk.StringVar()
        self.IP_SOAR.set(self.PAR.IP_dict['IP_SOAR'])
        tk.Entry(frame, width=20, textvariable=self.IP_SOAR).place(x=120, y=110)
        self.IP_SAMI = tk.StringVar()
        self.IP_SAMI.set(self.PAR.IP_dict['IP_SAMI'])
        tk.Entry(frame, width=20, textvariable=self.IP_SAMI).place(x=120, y=135)

        self.IP_Motors_on_button = tk.Button(frame, image=self.PAR.Image_off, bd=0, 
                                             command=self.Motors_switch).place(x=320, y=39)
        self.CCD_on_button = tk.Button(frame, image=self.PAR.Image_off, bd=0, command=self.CCD_switch).place(x=320, y=64)
        self.DMD_on_button = tk.Button(frame, image=self.PAR.Image_off, bd=0, command=self.DMD_switch).place(x=320, y=89)
        self.SOAR_Tel_on_button = tk.Button(frame, image=self.PAR.Image_off, bd=0, 
                                            command=self.SOAR_switch).place(x=320, y=113)
        self.SOAR_SAMI_on_button = tk.Button(frame, image=self.PAR.Image_off, bd=0, 
                                             command=self.SAMI_switch).place(x=320, y=139)


        # Other entries
        frame = tk.LabelFrame(self.right_frame, text="Observer Data", font=BIGFONT)
        frame.place(x=4, y=4, width=392, height=225)

        tk.Label(frame, text="Telescope").place(x=4, y=10)
        self.Telescope = tk.StringVar()
        self.Telescope.set(self.PAR.PotN['Telescope'])
        tk.Entry(frame, width=20, textvariable=self.Telescope).place(x=140, y=10)

        tk.Label(frame, text="Program ID").place(x=4, y=35)
        self.Program_ID = tk.StringVar()
        self.Program_ID.set(self.PAR.PotN['Program ID'])
        tk.Entry(frame, width=20, textvariable=self.Program_ID).place(x=140, y=35)

        tk.Label(frame, text="Proposal Title").place(x=4, y=60)
        self.Proposal_Title = tk.StringVar()
        self.Proposal_Title.set(self.PAR.PotN['Proposal Title'])
        tk.Entry(frame, width=20, textvariable=self.Proposal_Title).place(x=140, y=60)

        tk.Label(frame, text="Principal Investigator").place(x=4, y=85)
        self.Principal_Investigator = tk.StringVar()
        self.Principal_Investigator.set(self.PAR.PotN['Principal Investigator'])
        tk.Entry(frame, width=20, textvariable=self.Principal_Investigator).place(x=140, y=85)

        tk.Label(frame, text="Observer").place(x=4, y=110)
        self.Observer = tk.StringVar()
        self.Observer.set(self.PAR.PotN['Observer'])
        tk.Entry(frame, width=20, textvariable=self.Observer).place(x=140, y=110)

        self.TO_var = tk.StringVar()
        self.TO_var.set(self.PAR.PotN['Telescope Operator'])
        tk.Label(frame, text="Telescope Operator ").place(x=4, y=135)
        tk.Entry(frame, width=20, textvariable=self.TO_var).place(x=140, y=135)

        # Initialize
        frame = tk.LabelFrame(self.right_frame, text="Logbook", font=BIGFONT)
        frame.place(x=4, y=234, width=392, height=96)
        tk.Button(frame, text="Initialize Logbook", relief="raised", command=self.LogBookstartup).place(x=4, y=20)
        

    def LogBookstartup(self):
        SF.create_log_file(
            Telescope=self.Telescope.get(),
            ProgramID=self.Program_ID.get(),
            ProposalTitle=self.Proposal_Title.get(),
            PI=self.Principal_Investigator.get(), 
            Observer=self.Observer.get(),
            Operator=self.TO_var.get()
        )
        self.PAR.logbook_exist = True
    
    def startup(self):
        self.logger.info("CONFIG_GUI: entering startup.")
        self.load_IP_default()
        self.IP_echo()
        
        if self.PAR.IP_status_dict['IP_DMD'] == True:
            IP = self.PAR.IP_dict['IP_DMD']
            [host, port] = IP.split(":")
            self.DMD.initialize(address=host, port=int(port))
        if self.PAR.IP_status_dict['IP_Motors'] == True:
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
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = get_data_file("system", "IP_addresses_default_inside.csv")
        else:
            ip_file = get_data_file("system", "IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(dir_SYSTEM, "IP_addresses_default.csv")
        shutil.copy(ip_file, ip_file_default)
        return self._load_ip(ip_file)


    def load_IP_default(self):
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = get_data_file("system", "IP_addresses_default_inside.csv")
        else:
            ip_file = get_data_file("system", "IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(dir_SYSTEM, "IP_addresses_default.csv")
        shutil.copy(ip_file, ip_file_default)
        return self._load_ip(ip_file_default)


    def save_IP_user(self):
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = get_data_file("system", "IP_addresses_default_inside.csv")
        else:
            ip_file = get_data_file("system", "IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(dir_SYSTEM, "IP_addresses_default.csv")
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
        """ MOTORS alive? """
        print("\n Checking Motors status")
        IP = self.PAR.IP_dict['IP_Motors']
        [host, port] = IP.split(":")
        PCM.initialize(address=host, port=int(port))
        answer = PCM.echo_client()
        # print("\n Motors return:>", answer,"<")
        if answer != "no connection":
            print("Motors are on")
            self.IP_Motors_on_button.config(image=self.PAR.Image_on)
            print('echo from server:')
            self.PAR.IP_status_dict['IP_Motors'] = True
            # PCM.power_on()

        else:
            print("Motors are off\n")
            self.IP_Motors_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_Motors'] = False


        # CCD alive?
        print("\n Checking CCD status")
        url_name = "http://"+os.path.join(self.PAR.IP_dict['IP_CCD'])  # +'/'
        answer = (CCD.get_url_as_string(url_name))[:6]  # expect <HTML>
        print("CCD returns:>", answer, "<")
        if str(answer) == '<HTML>':
            print("CCD is on")
            self.CCD_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_CCD'] = True
        else:
            print("\nCCD is off\n")
            self.CCD_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_CCD'] = False

        # DMD alive?
        print("\n Checking DMD status")
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        self.DMD.initialize(address=host, port=int(port))
        answer = self.DMD._open()
        if answer != "no DMD":
            print("\n DMD is on")
            self.DMD_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_DMD'] = True
        else:
            print("\n DMD is off")
            self.DMD_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_DMD'] = False

        self.save_IP_status()
        return self.PAR.IP_dict


    # Define our switch functions
    def Motors_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_Motors']:
            self.IP_Motors_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_Motors'] = False
            PCM.power_off()
        else:
            self.IP_Motors_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_Motors'] = True
            self.save_IP_status()
            PCM.IP_host = self.IP_Motors
            PCM.power_on()
        self.save_IP_status()
        print(self.PAR.IP_status_dict)


    def CCD_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_CCD']:
            self.CCD_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_CCD'] = False
        else:
            self.CCD_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_CCD'] = True
        self.save_IP_status()
        print(self.PAR.IP_status_dict)


    def DMD_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_DMD']:
            self.DMD_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_DMD'] = False
        else:
            self.DMD_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_DMD'] = True
        self.save_IP_status()
        print(self.PAR.IP_status_dict)


    def SOAR_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_SOAR']:
            self.SOAR_Tel_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_SOAR'] = False
        else:
            self.SOAR_Tel_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_SOAR'] = True
        self.save_IP_status()
        print(self.PAR.IP_status_dict)


    def SAMI_switch(self):
        """ Determine is on or off """
        if self.PAR.IP_status_dict['IP_SAMI']:
            self.SOAR_SAMI_on_button.config(image=self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_SAMI'] = False
        else:
            self.SOAR_SAMI_on_button.config(image=self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_SAMI'] = True
        self.save_IP_status()
        print(self.PAR.IP_status_dict)


    def client_exit(self):
        """ to be written """
        print("complete")
        # self.master.destroy()


    def create_menubar(self, parent):
        # the size of the window is controlled when the menu is loaded
        parent.geometry("1000x520")
        parent.title("SAMOS Configuration")

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame("DMDPage"))
        filemenu.add_command(label="Recalibrate CCD2DMD", command=lambda: parent.show_frame("CCD2DMDPage"))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame("MotorsPage"))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame("CCDPage"))
        filemenu.add_command(label="SOAR TCS", command=lambda: parent.show_frame("SOARPage"))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame("MainPage"))
        filemenu.add_separator()
        filemenu.add_command(label="ETC", command=lambda: parent.show_frame("ETCPage"))
        filemenu.add_command(label="Exit", command=parent.quit)

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame("GSPage"))        
        help_menu.add_separator()

        return menubar
    

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
        
        for system in self.systems[:-2]:
            key = "IP_{}".format(system)
            self.PAR.IP_dict[key] = dict_from_csv[key]
            getattr(self, key).set(dict_from_csv[key])

        return self.PAR.IP_dict


    SYSTEMS = ["Motors", "CCD", "DMD", "SOAR", "SAMI", "Astrom", "system"]
