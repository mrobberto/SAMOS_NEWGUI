"""
SAMOS Motors tk Frame Class
"""
import copy
import csv
from datetime import datetime
import glob
import logging
from matplotlib import pyplot as plt
import numpy as np
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import twirl
from urllib.parse import urlencode

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
from PIL import Image, ImageTk
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
from tkinter import ttk

from samos.ccd import CCD
from samos.dmd.pixel_mapping import Coord_Transform_Helpers as CTH
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.pattern_helpers.Class_DMDGroup import DMDGroup
from samos.dmd import DigitalMicroMirrorDevice
from samos.motors.Class_PCM import Class_PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.astrometry.tk_class_astrometry_V5 import Astrometry
from samos.hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks
from samos.system import WriteFITSHead as WFH
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.system.SlitTableViewer import SlitTableView as STView
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


class MotorsPage(ttk.Frame):
    """ Motors """

    def __init__(self, parent, container, **kwargs):
        """ to be written """

        super().__init__(container)

        # label = tk.Label(self, text="Motors Page", font=('Times', '20'))
        # label.pack(pady=0,padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        self.Echo_String = tk.StringVar()
        # self.check_if_power_is_on()

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         #Get echo from Server
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        Button_Echo_From_Server = tk.Button(
            self, text="Echo from server", command=self.call_echo_PCM, relief=tk.RAISED)
        # placing the button on my window
        Button_Echo_From_Server.place(x=10, y=10)
        self.Echo_String = tk.StringVar()
        Label_Echo_Text = tk.Label(
            self, textvariable=self.Echo_String, width=15, bg='white')
        Label_Echo_Text.place(x=160, y=13)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#        # Power on/odd
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.is_on = False
        if self.is_on == False:
            text = "Turn power ON"
            color = "green"
        else:
            text = "Turn power OFF"
            color = "red"
        self.Button_Power_OnOff = tk.Button(
            self, text=text, command=self.power_switch, relief=tk.RAISED, fg=color)
        self.Button_Power_OnOff.place(x=10, y=40)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         All port statusPower on/odd
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Button_All_Ports_Status = tk.Button(
            self, text="All ports status", command=self.all_ports_status, relief=tk.RAISED)
        self.Button_All_Ports_Status.place(x=200, y=40)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         Select FW or GR
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.r1_v = tk.IntVar()

        r1 = tk.Radiobutton(self, text='FW1', variable=self.r1_v,
                            value=1, command=self.Choose_FWorGR)
        r1.place(x=10, y=70)

        r2 = tk.Radiobutton(self, text='FW2', variable=self.r1_v,
                            value=2, command=self.Choose_FWorGR)
        r2.place(x=70, y=70)

        r3 = tk.Radiobutton(self, text='GR_A', variable=self.r1_v,
                            value=3, command=self.Choose_FWorGR)
        r3.place(x=130, y=70)

        r3 = tk.Radiobutton(self, text='GR_B', variable=self.r1_v,
                            value=4, command=self.Choose_FWorGR)
        r3.place(x=190, y=70)

        # start with FW1
        self.r1_v.set(1)
        self.Choose_FWorGR()
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       home
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Button_home = tk.Button(
            self, text="send to home", command=self.home, relief=tk.RAISED)
        self.Button_home.place(x=10, y=100)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        Initialize
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Button_Initialize = tk.Button(
            self, text="Initialize Filter Wheels", command=self.FW_initialize, relief=tk.RAISED)
        self.Button_Initialize.place(x=200, y=100)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        Query current step counts
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Button_Initialize = tk.Button(
            self, text="Current steps", command=self.query_current_step_counts, relief=tk.RAISED)
        self.Button_Initialize.place(x=10, y=130)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         #Move to step....
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        Button_Move_to_step = tk.Button(
            self, text="Move to step", command=self.move_to_step, relief=tk.RAISED)
        Button_Move_to_step.place(x=10, y=160)
        self.Target_step = tk.StringVar()
        Label_Target_step = tk.Entry(
            self, textvariable=self.Target_step, width=6, bg='white')
        Label_Target_step.place(x=140, y=163)
        Button_Stop = tk.Button(
            self, text="Stop", command=self.stop, relief=tk.RAISED)
        Button_Stop.place(x=260, y=160)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         #Move to FW_position....
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        FW_pos_options = [
            "A1",
            "A2",
            "A3",
            "A4",
            "A5",
            "A6",
            "B1",
            "B2",
            "B3",
            "B4",
            "B5",
            "B6",
        ]

#        # datatype of menu text
        self.selected_FW_pos = tk.StringVar()
#        # initial menu text
        self.selected_FW_pos.set(FW_pos_options[0])
#        # Create Dropdown menu
        self.menu_FW_pos = tk.OptionMenu(
            self, self.selected_FW_pos,  *FW_pos_options)
        self.menu_FW_pos.place(x=120, y=193)
        Button_Move_to_FW_pos = tk.Button(
            self, text="FW Position", command=self.FW_move_to_position, relief=tk.RAISED)
        Button_Move_to_FW_pos.place(x=10, y=190)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         #Move to Filter....
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        filter_options = [
            "open",
            "SLOAN-g",
            "SLOAN-r",
            "SLOAN-i",
            "SLOAN-z",
            "Ha",
            "O[III]",
            "S[II]",
        ]

#        # datatype of menu text
        self.selected_filter = tk.StringVar()
#        # initial menu text
        self.selected_filter.set(filter_options[0])
#        # Create Dropdown menu
        self.menu_filters = tk.OptionMenu(
            self, self.selected_filter,  *filter_options)
        self.menu_filters.place(x=300, y=193)
        Button_Move_to_filter = tk.Button(
            self, text="Filter", command=self.FW_move_to_filter, relief=tk.RAISED)
        Button_Move_to_filter.place(x=230, y=190)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         #Move to GR_position....
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        GR_pos_options = [
            "GR_A1",
            "GR_A2",
            "GR_B1",
            "GR_B2",
        ]
#        # datatype of menu text
        self.selected_GR_pos = tk.StringVar()
#        # initial menu text
        self.selected_GR_pos.set(GR_pos_options[0])
#        # Create Dropdown menu
        self.menu_GR_pos = tk.OptionMenu(
            self, self.selected_GR_pos,  *GR_pos_options)
        self.menu_GR_pos.place(x=120, y=223)
        Button_Move_to_GR_pos = tk.Button(
            self, text="GR Position", command=self.GR_move_to_position, relief=tk.RAISED)
        Button_Move_to_GR_pos.place(x=10, y=220)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         #Enter command
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        Button_Enter_Command = tk.Button(
            self, text="Enter Command: ", command=self.enter_command, relief=tk.RAISED)
        Button_Enter_Command.place(x=10, y=250)
        self.Command_string = tk.StringVar()
        Text_Command_string = tk.Entry(
            self, textvariable=self.Command_string, width=15, bg='white')
        Text_Command_string.place(x=180, y=252)
        Label_Command_string_header = tk.Label(
            self, text=" ~@,9600_8N1T2000,+")
        Label_Command_string_header.place(x=10, y=280)
        Label_Command_string_Example = tk.Label(self, text=" (e.g. /1e1R\\n)")
        Label_Command_string_Example.place(x=165, y=280)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         # Exit
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        quitButton = tk.Button(self, text="Exit", command=self.client_exit)
        quitButton.place(x=280, y=300)

    def get_widget(self):
        """ get_widget """
        return self.root

    """
    def check_if_power_is_on(self):
        print('at startup, get echo from server:')
        t = PCM.echo_client()
        self.Echo_String.set(t)
        if t!= None:
            print(t[2:13])
            if t[2:13] == "NO RESPONSE":
                self.is_on = False
                self.Echo_String.set(t[2:13])
            else:
                self.is_on = True
                self.Echo_String.set(t)
        else:
            print("No echo from the server")
    """

    def call_echo_PCM(self):
        """ call_echo_PCM """
        print('echo from server:')
        t = PCM.echo_client()
        self.Echo_String.set(t)
        print(t)

    def power_switch(self):
        """ power_switch """
    # Determine is on or off
        if self.is_on:  # True, power is on => turning off, prepare for turn on agaim
            t = PCM.power_off()
            self.is_on = False
            self.Button_Power_OnOff.config(text="Turn power On", fg="green")
        else:
            t = PCM.power_on()
            self.is_on = True
            self.Button_Power_OnOff.config(text="Turn power Off", fg="red")
        self.Echo_String.set(t)
        print("Power switched to ", t)

    def all_ports_status(self):
        """ all_ports_status """
        print('all ports status:')
        t = PCM.all_ports_status()
        self.Echo_String.set(t)
        print(t)

    def Choose_FWorGR(self):
        """ Choose_FWorGR """
        if self.r1_v.get() == 1:
            unit = 'FW1',
        if self.r1_v.get() == 2:
            unit = 'FW2',
        if self.r1_v.get() == 3:
            unit = 'GR_A',
        if self.r1_v.get() == 4:
            unit = 'GR_B',
        self.FWorGR = unit[0]  # returns a list...
        print(self.FWorGR)

    def FW_initialize(self):
        """ to be written """

        print('Initialize:')
        t = PCM.initialize_filter_wheel("FW1")
        t = PCM.initialize_filter_wheel("FW2")
        self.Echo_String.set(t)
        print(t)

    def stop_the_motors(self):
        """ to be written """
        print('Stop the motor:')
        t = PCM.motors_stop()
        self.Echo_String.set(t)

    def query_current_step_counts(self):
        """ to be written """
        print('Current step counts:')
        t = PCM.query_current_step_counts(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def home(self):
        """ to be written """
        print('home:')
        t = PCM.home_FWorGR_wheel(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def move_to_step(self):
        """ to be written """
        print('moving to step:')

        t = PCM.go_to_step(self.FWorGR, self.Target_step.get())
        self.Echo_String.set(t)
        print(t)

    def stop(self):
        """ to be written """
        print('moving to step:')
        t = PCM.stop_filter_wheel(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def FW_move_to_position(self):
        """ to be written """
        print('moving to FW position:', self.selected_FW_pos.get())
        FW_pos = self.selected_FW_pos.get()
        t = PCM.move_FW_pos_wheel(FW_pos)
        self.Echo_String.set(t)
        main_fits_header.set_param("filterpos", FW_pos)
        print(t)

    def FW_move_to_filter(self):
        """ to be written """
        print('moving to filter:', self.selected_filter.get())
        filter = self.selected_filter.get()
        t = PCM.move_filter_wheel(filter)
        self.Echo_String.set(t)
        main_fits_header.set_param("filters", filter)
        print(t)

    def GR_move_to_position(self):
        """ to be written """
        print('moving to GR_position:')
        GR_pos = self.selected_GR_pos.get()
        t = PCM.move_grism_rails(GR_pos)
        self.Echo_String.set(t)

        print(t)

    def enter_command(self):
        """ to be written """
        print('command entered:', self.Command_string.get())
        # convert StringVar to string
        t = PCM.send_command_string(self.Command_string.get())
        self.Echo_String.set(t)
        print(t)

    def client_exit(self):
        """ to be written """
        print("destroy")
        self.destroy()

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("400x330")
        if sys.platform == "win32":
            parent.geometry("500x400")

        parent.title("SAMOS Motor Controller")

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame("DMDPage"))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame("CCD2DMDPage"))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame("MotorsPage"))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame("CCDPage"))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame("SOARPage"))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame("MainPage"))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame("ETCPage"))
        filemenu.add_command(label="Exit", command=parent.quit)

        """
        # proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame("GSPage"))        
        help_menu.add_separator()

        return menubar
