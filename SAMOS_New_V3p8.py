 """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
Created on Tue Feb 25 13:21:00 2023

"""
from sys import platform
from SAMOS_DMD_dev.DMD_get_pixel_mapping_GUI_dana import Coord_Transform_Helpers as CTH
from SAMOS_DMD_dev.CONVERT.CONVERT_class import CONVERT
from SAMOS_DMD_dev.DMD_Pattern_Helpers.Class_DMDGroup import DMDGroup
from SAMOS_DMD_dev.Class_DMD_dev import DigitalMicroMirrorDevice
from SAMOS_MOTORS_dev.Class_PCM import Class_PCM
from SAMOS_SOAR_dev.Class_SOAR import Class_SOAR
from SAMOS_CCD_dev.Class_CCD_dev import Class_Camera
# from SAMOS_CCD_dev.Class_CCD_dev import Class_Camera
from SAMOS_Astrometry_dev.skymapper_interrogate import skymapper_interrogate
from SAMOS_Astrometry_dev.tk_class_astrometry_V5 import Astrometry
from SAMOS_Astrometry_dev.PanStarrs.Class_ps1image import PanStarrs as PS_image
from SAMOS_Astrometry_dev.PanStarrs.Class_ps1_dr2_catalog import PS_DR2_Catalog as PS_table
from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF
from SAMOS_system_dev.SlitTableViewer import SlitTableView as STView
from SAMOS_ETC.SAMOS_SPECTRAL_ETC import ETC_Spectral_Page as ETCPage
import SAMOS_system_dev.utils as U
import SAMOS_system_dev.WriteFITSHead as WFH

from SAMOS_system_dev.SAMOS_Parameters_out import SAMOS_Parameters


import re  # re module of the standard library handles strings, e.g. use re.search() to extract substrings
# , PointPixelRegion, RegionVisual
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion
from astroquery.simbad import Simbad
# from SAMOS_MOTORS_dev.Class_PCM import Class_PCM
import time

# from SAMOS_Astrometry_dev.skymapper_interrogate_fLoad VOTABLE import skymapper_interrogate_VOTABLE
import glob
import pathlib
import math
import numpy
from regions import Regions
import aplpy
import twirl
from matplotlib import pyplot as plt
from urllib.parse import urlencode
from astropy.wcs.utils import fit_wcs_from_points
from astroquery.gaia import Gaia
from ginga.util import iqcalc
from ginga.AstroImage import AstroImage
from ginga.util import ap_region
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.util.loader import load_data
from ginga.misc import log
import ginga.colors as gcolors
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
import subprocess
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import csv
import tkinter as tk

# from tkinter import *
# import tkinter as tk  #small t for Python 3f
from tkinter import ttk
from tkinter import messagebox

# import filedialog module
from tkinter import filedialog
# from tkinter.filedialog import askopenfilename
# from tkinter.filedialog import asksaveasfile

from astropy.coordinates import SkyCoord, FK4  # , ICRS, Galactic, FK5
from astropy import units as u
from astropy.io import fits, ascii
from astropy.stats import sigma_clipped_stats, SigmaClip
import astropy.wcs as wcs


from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder


import shutil
import copy
# from esutil import htm

from PIL import Image, ImageTk  # , ImageOps
from Hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks

import os
import sys
cwd = os.getcwd()
print(cwd)


# define the local directory, absolute so it is not messed up when this is called

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)
sys.path.append(parent_dir)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# Import classes
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# load the functions

PCM = Class_PCM()

# at the moment the Class Camera must be called with a few parameters...
params = {'Exposure Time': 0, 'CCD Temperature': 2300,
          'Trigger Mode': 4, 'NofFrames': 1}
# Trigger Mode = 4: light
# Trigger Mode = 5: dark
CCD = Class_Camera(dict_params=params)


# Import the DMD class
DMD = DigitalMicroMirrorDevice()  # config_id='pass')

# Instantiate the PanStarrs class
PSima = PS_image()
PStab = PS_table()


"""
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfile

import sys
# sys.path.append('/opt/anaconda3/envs/samos_env/lib/python3.10/site-packages')

import os
from os.path import exists as file_exists
import time
from argparse import ArgumentParser

import threading
import pandas as pd
"""
# for image display
img = AstroImage()
iq = iqcalc.IQCalc()


# from astropy import units as u
# from astropy.io import fits


# from astropy.nddata import block_reduce

# import regions

# Needed to run ConvertSIlly by C. Loomis

# import sewpy   #to run sextractor wrapper

STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'
# #===#===#===#===#===#===#===#===#=====d#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===
#
# from Astrometry import tk_class_astrometry
# Astrometry = tk_class_astrometry
#
# Astrometry.return_from_astrometry()
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

# from pathlib import Path
# define the local directory, absolute so it is not messed up when this is called
# path = Path(__file__).parent.absolute()
# local_dir = str(path.absolute())
# sys.path.append(local_dir)


dir_Astrometry = os.path.join(local_dir, "SAMOS_Astrometry_dev")
dir_CCD = os.path.join(local_dir, "SAMOS_CCD_dev")
dir_DMD = os.path.join(local_dir, "SAMOS_DMD_dev")
dir_MOTORS = os.path.join(local_dir, "SAMOS_MOTORS_dev")
dir_SOAR = os.path.join(local_dir, "SAMOS_SOAR_dev")
dir_CONFIG = os.path.join(local_dir, "SAMOS_CONFIG_dev")
dir_SYSTEM = os.path.join(local_dir, "SAMOS_system_dev")

os.sys.path.append(local_dir)
os.sys.path.append(dir_Astrometry)
os.sys.path.append(dir_CCD)
os.sys.path.append(dir_DMD)
os.sys.path.append(dir_MOTORS)
os.sys.path.append(dir_SOAR)
os.sys.path.append(dir_CONFIG)
os.sys.path.append(dir_SYSTEM)


# from SAMOS_CONFIG_dev.CONFIG_GUI import Config

# print(Config.return_directories)

"""
from SAMOS_CCD_dev.GUI_CCD_dev import GUI_CCD
from SAMOS_CCD_dev.Class_CCD_dev import Class_Camera as CCD


from SAMOS_MOTORS_dev.SAMOS_MOTORS_GUI_dev  import Window as SM_GUI
"""
Motors = Class_PCM()
SOAR = Class_SOAR()
"""
from SAMOS_DMD_dev.SAMOS_DMD_GUI_dev import GUI_DMD
# from SAMOS_DMD_dev.Class_DMD import DigitalMicroMirrorDevice as DMD
from SAMOS_DMD_dev.Class_DMD_dev import DigitalMicroMirrorDevice
"""
convert = CONVERT()

main_fits_header = WFH.FITSHead()
"""
DMD = DigitalMicroMirrorDevice()#config_id='pass')

from SAMOS_SOAR_dev.tk_class_SOAR_V0 import SOAR as SOAR

from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF


# from ginga.misc import widgets
# import PCM_module_GUI as Motors

"""

indicator_light_on_color = "#08F903"
indicator_light_off_color = "#194A18"
indicator_light_pending_color = "#F707D3"
# text format for writing new info to header. Global var
param_entry_format = '[Entry {}]\nType={}\nKeyword={}\nValue="{}"\nComment="{}\n"'

r_ulim, g_llim, b_llim = 0.3, 0.6, 0.6
bright_blues = [c for c in gcolors.color_list if (gcolors.color_dict[c][0] <= r_ulim and
                                                  gcolors.color_dict[c][1] >= g_llim and
                                                  gcolors.color_dict[c][2] >= b_llim or
                                                  c == 'blueviolet' or c == 'cadetblue1')]
r_llim, g_ulim, b_ulim = 0.6, 0.5, 0.6
bright_reds = [c for c in gcolors.color_list if (gcolors.color_dict[c][0] >= r_llim and
                                                 gcolors.color_dict[c][1] <= g_ulim and
                                                 gcolors.color_dict[c][2] <= b_ulim)]
r_ulim, g_ullim, b_ulim = 0.5, 0.5, 0.6
bright_greens = [c for c in gcolors.color_list if (gcolors.color_dict[c][0] <= r_ulim and
                                                   gcolors.color_dict[c][1] >= g_llim and
                                                   gcolors.color_dict[c][2] <= b_ulim)]

nice_colors_list = bright_blues
nice_colors_list.extend(bright_reds)
nice_colors_list.extend(bright_greens)


class App(tk.Tk):
    """ to be written """

    def __init__(self):
        """ to be written """
        super().__init__()

        # Setting up Initial Things
        self.title("SAMOS Control System")
        self.geometry("1100x500")
        self.resizable(True, True)
        # self.iconphoto(False, tk.PhotoImage(file="assets/title_icon.png"))

        # Creating a container
        container = tk.Frame(self, bg="#8AA7A9", width=1100)
        container.pack(side="top", fill="both", expand=True,)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        # Initialize Frames
        self.frames = {}
        self.ConfigPage = ConfigPage
        self.DMDPage = DMDPage
        self.CCD2DMD_RecalPage = CCD2DMD_RecalPage
        self.Motors = Motors
        self.SOAR_Page = SOAR_Page
        self.CCDPage = CCDPage
        self.MainPage = MainPage
        self.ETCPage = ETCPage
        self.GuideStarPage = GuideStarPage

        # Defining Frames and Packing it
        for F in {ConfigPage, DMDPage, CCD2DMD_RecalPage, Motors, CCDPage, SOAR_Page, MainPage, ETCPage, GuideStarPage}:
            frame = F(self, container)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(ConfigPage)

    def show_frame(self, cont):
        """ to be written """
        frame = self.frames[cont]
        menubar = frame.create_menubar(self)
        self.configure(menu=menubar)
        frame.tkraise()  # This line will put the frame on front


# ---------------------------------------- Config PAGE FRAME / CONTAINER ------------------------------------------------------------------------

class ConfigPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """

        super().__init__(container)

 #       self.PAR = SAM_Par_module.SAMOS_Parameters()
        self.PAR = SAMOS_Parameters()

        if platform == "win32":
            self.bigfont = ("Arial", 12, 'bold')
            self.bigfont_20 = ("Arial", 12, 'bold')
            self.bigfont_15 = ("Arial", 10, 'bold')
        else:
            self.bigfont = ("Arial", 24)
            self.bigfont_20 = ("Arial", 20)
            self.bigfont_15 = ("Arial", 15)
        # label = tk.Label(self, text="Config Page", font=('Times', '20'))
        # label.pack(pady=0,padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        # parameters that you want to send through the Frame class
#        tk.Frame.__init__(self, master)

        # reference to the master widget, which is the "parent" tk window, since we instance
        # at the end   >app = Config(parent)
#        self.master = master

        # with that, we want to then run init_window, which doesn't yet exist
#        self.init_Config()

        # path = Path(__file__).parent.absolute()
#        parent_dir = str(path.parent)

        # self.cwd = local_dir
        # self.parent_dir = parent_dir

    # Creation of init_window
#    def init_Config(self):
#        print(parent_dir)

        # Keep track of the button state on/off
 #       self.Motors_is_on = True
        # Define Our Images

        """
        self.Image_on = tk.PhotoImage(file = local_dir+"/Images/on.png")
        self.Image_off = tk.PhotoImage(file = local_dir+"/Images/off.png")
        """

        """
        self.dir_dict = {'dir_Motors': '/SAMOS_MOTORS_dev',
                         'dir_CCD'   : '/SAMOS_CCD_dev',
                         'dir_DMD'   : '/SAMOS_DMD_dev',
                         'dir_SOAR'  : '/SAMOS_SOAR_dev',
                         'dir_SAMI'  : '/SAMOS_SAMI_dev',
                         'dir_Astrom': '/SAMOS_Astrometry_dev',
                         'dir_system': '/SAMOS_system_dev',
                        }
        """

        """
        self.IP_dict =  {'IP_Motors': '128.220.146.254:8889',
                         'IP_CCD'   : '128.220.146.254:8900',
                         'IP_DMD'   : '128.220.146.254:8888',
                         'IP_SOAR'  : 'TBD',
                         'IP_SAMI'  : 'TBD',
                        }
        """

        """
        self.IP_status_dict = {'IP_Motors':False,
                               'IP_CCD'   :False,
                               'IP_DMD'   :False,
                               'IP_SOAR'  :False,
                               'IP_SAMI'   :False,
                              }
        """
        # changing the title of our master widget
        # master.title("SAMOS- Config Window")

        self.frame0l = tk.Frame(
            self, background="dark gray", width=600, height=500)
        self.frame0l.place(x=0, y=0)  # , anchor="nw", width=20, height=145)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Directories
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.labelframe_Servers = tk.LabelFrame(
            self.frame0l, text="Directories", font=self.bigfont)  # ("Arial", 24))
        self.labelframe_Servers.place(
            x=4, y=4, anchor="nw", width=592, height=225)

# 2. Directories and Files
# 2.1 SAMOS Motors parameter files
# 2.2 SAMOS CCD parameter files
# 2.3 SAMOS DMD parameter files
# 2.4 SOAR Telescope parameter files
# 2.5 SOAR SAMI parameter files
# 2.6 SAMOS Astrometry
# 2.7 SAMOS system Window

        Label1 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_Motors'])
        Label1.place(x=4, y=10)
        self.update()
        Label2 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_CCD'])
        Label2.place(x=4, y=35)
        Label3 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_DMD'])
        Label3.place(x=4, y=60)
        Label1 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_SOAR'])
        Label1.place(x=4, y=85)
        Label2 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_SAMI'])
        Label2.place(x=4, y=110)
        Label1 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_Astrom'])
        Label1.place(x=4, y=135)
        Label2 = tk.Label(self.labelframe_Servers,
                          text=self.PAR.dir_dict['dir_system'])
        Label2.place(x=4, y=160)

        self.dir_Motors = tk.StringVar()
        self.dir_Motors.set(self.PAR.dir_dict['dir_Motors'])
        Entry_dir_Motors = tk.Entry(
            self.labelframe_Servers, width=25, textvariable=self.dir_Motors)
        Entry_dir_Motors.place(x=140, y=10)
        self.dir_CCD = tk.StringVar()
        self.dir_CCD.set(self.PAR.dir_dict['dir_CCD'])
        Entry2 = tk.Entry(self.labelframe_Servers, width=25,
                          textvariable=self.dir_CCD)
        Entry2.place(x=140, y=35)
        self.dir_DMD = tk.StringVar()
        self.dir_DMD.set(self.PAR.dir_dict['dir_DMD'])
        Entry3 = tk.Entry(self.labelframe_Servers, width=25,
                          textvariable=self.dir_DMD)
        Entry3.place(x=140, y=60)
        self.dir_SOAR = tk.StringVar()
        self.dir_SOAR.set(self.PAR.dir_dict['dir_SOAR'])
        Entry4 = tk.Entry(self.labelframe_Servers, width=25,
                          textvariable=self.dir_SOAR)
        Entry4.place(x=140, y=85)
        self.dir_SAMI = tk.StringVar()
        self.dir_SAMI.set(self.PAR.dir_dict['dir_SAMI'])
        Entry5 = tk.Entry(self.labelframe_Servers, width=25,
                          textvariable=self.dir_SAMI)
        Entry5.place(x=140, y=110)
        self.dir_Astrom = tk.StringVar()
        self.dir_Astrom.set(self.PAR.dir_dict['dir_Astrom'])
        Entry5 = tk.Entry(self.labelframe_Servers, width=25,
                          textvariable=self.dir_Astrom)
        Entry5.place(x=140, y=135)
        self.dir_system = tk.StringVar()
        self.dir_system.set(self.PAR.dir_dict['dir_system'])
        Entry5 = tk.Entry(self.labelframe_Servers, width=25,
                          textvariable=self.dir_system)
        Entry5.place(x=140, y=160)

        Button_dir_Current = tk.Button(self.labelframe_Servers, text="Load Current",
                                       relief="raised", command=self.load_dir_user, font=self.bigfont)  # ("Arial", 24))
        Button_dir_Current.place(x=380, y=10)
        Button_dir_Save = tk.Button(self.labelframe_Servers, text="Save Current",
                                    relief="raised", command=self.save_dir_user, font=self.bigfont)  # ("Arial", 24))
        Button_dir_Save.place(x=380, y=50)
        Button_dir_Load = tk.Button(self.labelframe_Servers, text="Load Default",
                                    relief="raised", command=self.load_dir_default, font=self.bigfont)  # ("Arial", 24))
        Button_dir_Load.place(x=380, y=90)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Servers
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.labelframe_Servers = tk.LabelFrame(
            self.frame0l, text="Servers", font=self.bigfont)  # ("Arial", 24))
        self.labelframe_Servers.place(
            x=4, y=234, anchor="nw", width=592, height=200)

        """
        self.inoutvar=tk.StringVar()
        self.inoutvar.set("outside")
        """

        r1 = tk.Radiobutton(self.labelframe_Servers, text='Inside',
                            variable=self.PAR.inoutvar, value='inside', command=self.load_IP_default)
        r1.place(x=20, y=0)
        r2 = tk.Radiobutton(self.labelframe_Servers, text='Outside (with VPN)',
                            variable=self.PAR.inoutvar, value='outside', command=self.load_IP_default)
        r2.place(x=150, y=0)

# 1. Server addresses
# 1.1 SAMOS Motors
# 1.2 SAMOS CCD
# 1.3 SAMOS DMD controller
# 1.4 SOAR Telescope
# 1.5 SOAR SAMI
        Label1 = tk.Label(self.labelframe_Servers, text="SAMOS Motors")
        Label1.place(x=4, y=35)
        Label2 = tk.Label(self.labelframe_Servers, text="CCD")
        Label2.place(x=4, y=60)
        Label3 = tk.Label(self.labelframe_Servers, text="DMD")
        Label3.place(x=4, y=85)
        Label1 = tk.Label(self.labelframe_Servers, text="SOAR Telescope")
        Label1.place(x=4, y=110)
        Label2 = tk.Label(self.labelframe_Servers, text="SOAR SAMI")
        Label2.place(x=4, y=135)

        # print(self.PAR.IP_dict)

        self.IP_Motors = tk.StringVar()
        self.IP_Motors.set(self.PAR.IP_dict['IP_Motors'])
        Entry_IP_Motors = tk.Entry(
            self.labelframe_Servers, width=20, textvariable=self.IP_Motors)
        Entry_IP_Motors.place(x=120, y=35)
        self.IP_CCD = tk.StringVar()
        self.IP_CCD.set(self.PAR.IP_dict['IP_CCD'])
        Entry2 = tk.Entry(self.labelframe_Servers, width=20,
                          textvariable=self.IP_CCD)
        Entry2.place(x=120, y=60)
        self.IP_DMD = tk.StringVar()
        self.IP_DMD.set(self.PAR.IP_dict['IP_DMD'])
        Entry3 = tk.Entry(self.labelframe_Servers, width=20,
                          textvariable=self.IP_DMD)
        Entry3.place(x=120, y=85)
        self.IP_SOAR = tk.StringVar()
        self.IP_SOAR.set(self.PAR.IP_dict['IP_SOAR'])
        Entry4 = tk.Entry(self.labelframe_Servers, width=20,
                          textvariable=self.IP_SOAR)
        Entry4.place(x=120, y=110)
        self.IP_SAMI = tk.StringVar()
        self.IP_SAMI.set(self.PAR.IP_dict['IP_SAMI'])
        Entry5 = tk.Entry(self.labelframe_Servers, width=20,
                          textvariable=self.IP_SAMI)
        Entry5.place(x=120, y=135)

 #       self.Image_on = Image.open("/Users/robberto/Box/@Massimo/_Python/SAMOS_GUI_dev/SAMOS_CONFIG_dev/Images/on.jpg")
#        self.python_image = ImageTk.PhotoImage(self.image)
        # self.Label(self, image=self.python_image).pack()

#        ttk.Label(self,image=self.Image_on).pack()
        # Create A Button
        self.IP_Motors_on_button = tk.Button(
            self.labelframe_Servers, image=self.PAR.Image_off, bd=0, command=self.Motors_switch)
        self.IP_Motors_on_button.place(x=320, y=39)
        self.CCD_on_button = tk.Button(
            self.labelframe_Servers, image=self.PAR.Image_off, bd=0, command=self.CCD_switch)
        self.CCD_on_button.place(x=320, y=64)
        self.DMD_on_button = tk.Button(
            self.labelframe_Servers, image=self.PAR.Image_off, bd=0, command=self.DMD_switch)
        self.DMD_on_button.place(x=320, y=89)
        self.SOAR_Tel_on_button = tk.Button(
            self.labelframe_Servers, image=self.PAR.Image_off, bd=0, command=self.SOAR_switch)
        self.SOAR_Tel_on_button.place(x=320, y=113)
        self.SOAR_SAMI_on_button = tk.Button(
            self.labelframe_Servers, image=self.PAR.Image_off, bd=0, command=self.SAMI_switch)
        self.SOAR_SAMI_on_button.place(x=320, y=139)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    OTHER INFO
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.frame0r = tk.Frame(
            self, background="dark gray", width=400, height=500)
        self.frame0r.place(x=585, y=0)  # , anchor="nw", width=20, height=145)

        self.labelframe_Others = tk.LabelFrame(
            self.frame0r, text="Observer Data", font=self.bigfont)
        self.labelframe_Others.place(
            x=4, y=4, anchor="nw", width=392, height=225)

        Label1 = tk.Label(self.labelframe_Others, text="Telescope")
        Label1.place(x=4, y=10)
        self.Telescope = tk.StringVar()
        self.Telescope.set(self.PAR.PotN['Telescope'])
        Entry_IP_Telescope = tk.Entry(
            self.labelframe_Others, width=20, textvariable=self.Telescope)
        Entry_IP_Telescope.place(x=140, y=10)

        Label1 = tk.Label(self.labelframe_Others, text="Program ID")
        Label1.place(x=4, y=35)
        self.Program_ID = tk.StringVar()
        self.Program_ID.set(self.PAR.PotN['Program ID'])
        Entry_Program_ID = tk.Entry(
            self.labelframe_Others, width=20, textvariable=self.Program_ID)
        Entry_Program_ID.place(x=140, y=35)

        Label1 = tk.Label(self.labelframe_Others, text="Proposal Title")
        Label1.place(x=4, y=60)
        self.Proposal_Title = tk.StringVar()
        self.Proposal_Title.set(self.PAR.PotN['Proposal Title'])
        Entry_Proposal_Title = tk.Entry(
            self.labelframe_Others, width=20, textvariable=self.Proposal_Title)
        Entry_Proposal_Title.place(x=140, y=60)

        Label1 = tk.Label(self.labelframe_Others, text="Principal Investigator")
        Label1.place(x=4, y=85)
        self.Principal_Investigator = tk.StringVar()
        self.Principal_Investigator.set(self.PAR.PotN['Principal Investigator'])
        Entry_Principal_Investigator = tk.Entry(
            self.labelframe_Others, width=20, textvariable=self.Principal_Investigator)
        Entry_Principal_Investigator.place(x=140, y=85)

        Label1 = tk.Label(self.labelframe_Others, text="Observer")
        Label1.place(x=4, y=110)
        self.Observer = tk.StringVar()
        self.Observer.set(self.PAR.PotN['Observer'])
        Entry_Observer = tk.Entry(
            self.labelframe_Others, width=20, textvariable=self.Observer)
        Entry_Observer.place(x=140, y=110)

        self.TO_var = tk.StringVar()
        self.TO_var.set(self.PAR.PotN['Telescope Operator'])
        TO_label = tk.Label(self.labelframe_Others, text="Telescope Operator ")
        TO_label.place(x=4, y=135)
        TO_entry = tk.Entry(self.labelframe_Others, width=20,
                            textvariable=self.TO_var)
        TO_entry.place(x=140, y=135)



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Initialize
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Initialize_frame = tk.Frame(self.frame0l)
        self.Initialize_frame.place(
            x=4, y=440, anchor="nw", width=592, height=48)
        Initialize_Button = tk.Button(self.Initialize_frame, text="Initialize",
                                      relief="raised", command=self.startup, font=self.bigfont)  # ("Arial", 24))
        Initialize_Button.place(x=230, y=5)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #   FUNCTIONS ....
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    def startup(self):
        """ to be written """
        print("CONFIG_GUI: entering startup()\n")
        self.load_IP_default()
        self.IP_echo()
        SF.create_fits_folder()

        if self.PAR.IP_status_dict['IP_DMD'] == True:
            IP = self.PAR.IP_dict['IP_DMD']
            [host, port] = IP.split(":")
            DMD.initialize(address=host, port=int(port))
            # PCM.power_on()
            # PCM.check_if_power_is_on()
        if self.PAR.IP_status_dict['IP_Motors'] == True:
            PCM.power_on()
            # PCM.check_if_power_is_on()
        print("\n*** CONFIG_GUI: exiting startup() ***\n")

    # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    # create directoy to store the data
    # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        def create_fits_folder(self):
            """ to be written """

            today = datetime.now()

            # name of the directory
            self.fits_dir = os.path.join(
                parent_dir, "SISI_images","SAMOS_" + today.strftime('%Y%m%d'))

            isdir = os.path.isdir(self.fits_dir)
            if isdir == False:
                os.mkdir(self.fits_dir)

            fits_directory_file = open(
                os.path.join(dir_SYSTEM, "fits_current_dir_name.txt"), "w")
            fits_directory_file.write(self.fits_dir)
            fits_directory_file.close()

    def load_dir_default(self):
        """ to be written """
        dict_from_csv = {}

        # with open(self.parent_dir+"/SAMOS_system_dev/dirlist_default.csv", mode='r') as inp:
        with open(os.path.join(dir_SYSTEM, "dirlist_default.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        inp.close()

        self.dir_Motors.set(dict_from_csv['dir_Motors'])
        self.dir_CCD.set(dict_from_csv['dir_CCD'])
        self.dir_DMD.set(dict_from_csv['dir_DMD'])
        self.dir_SOAR.set(dict_from_csv['dir_SOAR'])
        self.dir_SAMI.set(dict_from_csv['dir_SAMI'])
        self.dir_Astrom.set(dict_from_csv['dir_Astrom'])
        self.dir_system.set(dict_from_csv['dir_system'])

        self.PAR.dir_dict['dir_Motors'] = dict_from_csv['dir_Motors']
        self.PAR.dir_dict['dir_CCD'] = dict_from_csv['dir_CCD']
        self.PAR.dir_dict['dir_DMD'] = dict_from_csv['dir_DMD']
        self.PAR.dir_dict['dir_SOAR'] = dict_from_csv['dir_SOAR']
        self.PAR.dir_dict['dir_SAMI'] = dict_from_csv['dir_SAMI']
        self.PAR.dir_dict['dir_Astrom'] = dict_from_csv['dir_Astrom']
        self.PAR.dir_dict['dir_system'] = dict_from_csv['dir_system']

 #       self.destroy()
 #       tk.Frame.__init__(self)
#       self.__init__()

        return self.PAR.dir_dict

    def load_dir_user(self):
        """ to be written """
        dict_from_csv = {}

        with open(os.path.join(dir_SYSTEM, "dirlist_user.csv"), mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}

        inp.close()
        self.dir_Motors.set(dict_from_csv['dir_Motors'])
        self.dir_CCD.set(dict_from_csv['dir_CCD'])
        self.dir_DMD.set(dict_from_csv['dir_DMD'])
        self.dir_SOAR.set(dict_from_csv['dir_SOAR'])
        self.dir_SAMI.set(dict_from_csv['dir_SAMI'])
        self.dir_Astrom.set(dict_from_csv['dir_Astrom'])
        self.dir_system.set(dict_from_csv['dir_system'])

        self.PAR.dir_dict['dir_Motors'] = dict_from_csv['dir_Motors']
        self.PAR.dir_dict['dir_CCD'] = dict_from_csv['dir_CCD']
        self.PAR.dir_dict['dir_DMD'] = dict_from_csv['dir_DMD']
        self.PAR.dir_dict['dir_SOAR'] = dict_from_csv['dir_SOAR']
        self.PAR.dir_dict['dir_SAMI'] = dict_from_csv['dir_SAMI']
        self.PAR.dir_dict['dir_Astrom'] = dict_from_csv['dir_Astrom']
        self.PAR.dir_dict['dir_system'] = dict_from_csv['dir_system']

        return self.PAR.dir_dict

    def save_dir_user(self):
        """ define a dictionary with key value pairs
        dict = {'dir_Motors' : self.dir_Motors.get(),
                'dir_CCD' :  self.dir_CCD.get(),
                'dir_DMD' :  self.dir_DMD.get(),
                'dir_SOAR':  self.dir_SOAR.get(),
                'dir_SAMI': self.dir_SAMI.get(),
                'dir_Astrom':  self.dir_Astrom.get(),
                'dir_system': self.dir_system.get()}
        """
        self.PAR.dir_dict['dir_Motors'] = self.dir_Motors.get()
        self.PAR.dir_dict['dir_CCD'] = self.dir_CCD.get()
        self.PAR.dir_dict['dir_DMD'] = self.dir_DMD.get()
        self.PAR.dir_dict['dir_SOAR'] = self.dir_SOAR.get()
        self.PAR.dir_dict['dir_SAMI'] = self.dir_SAMI.get()
        self.PAR.dir_dict['dir_Astrom'] = self.dir_Astrom.get()
        self.PAR.dir_dict['dir_system'] = self.dir_system.get()

        # open file for writing, "w" is writing
        file_dirlist = open(os.path.join(dir_SYSTEM, "dirlist_user.csv"), "w")
        w = csv.writer(file_dirlist)
        print(os.path.join(dir_SYSTEM, "dirlist_user.csv"))
        file_dirlist.close()

        # loop over dictionary keys and values
        for key, val in self.PAR.dir_dict.items():

            # write every key and value to file
            w.writerow([key, val])

    def load_IP_user(self):
        """ to be written """
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = os.path.join(
                dir_SYSTEM, "IP_addresses_default_inside.csv")
        else:
            ip_file = os.path.join(
                dir_SYSTEM, "IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(dir_SYSTEM, "IP_addresses_default.csv")
        if platform == "win32":
            os.system('copy {} {}'.format(ip_file, ip_file_default))
        else:
            os.system('cp {} {}'.format(ip_file, ip_file_default))
            
        with open(ip_file, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        inp.close()

        self.PAR.IP_dict['IP_Motors'] = dict_from_csv['IP_Motors']
        self.PAR.IP_dict['IP_CCD'] = dict_from_csv['IP_CCD']
        self.PAR.IP_dict['IP_DMD'] = dict_from_csv['IP_DMD']
        self.PAR.IP_dict['IP_SOAR'] = dict_from_csv['IP_SOAR']
        self.PAR.IP_dict['IP_SAMI'] = dict_from_csv['IP_SAMI']

        self.IP_Motors.set(dict_from_csv['IP_Motors'])
        self.IP_CCD.set(dict_from_csv['IP_CCD'])
        self.IP_DMD.set(dict_from_csv['IP_DMD'])
        self.IP_SOAR.set(dict_from_csv['IP_SOAR'])
        self.IP_SAMI.set(dict_from_csv['IP_SAMI'])

        return self.PAR.IP_dict

    def save_IP_user(self):
        """ to be written """

        # define a dictionary with key value pairs
 #       dict = {'IP_Motors' : self.IP_Motors.get(), 'IP_CCD' :  self.IP_CCD.get(), 'IP_DMD' :  self.IP_DMD.get(), 'IP_SOAR':  self.IP_SOAR.get(), 'IP_SAMI': self.IP_SAMI.get()}


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         self.PAR.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
#         self.PAR.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
#         self.PAR.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
#         self.PAR.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
#         self.PAR.IP_dict['IP_SAMI']=dict_from_csv['IP__SOAR_SAMI']
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# open file for writing, "w" is writing

        if self.PAR.inoutvar.get() == 'inside':
            ip_file = os.path.join(
                dir_SYSTEM, "IP_addresses_default_inside.csv")
        else:
            ip_file = os.path.join(
                dir_SYSTEM, "IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(dir_SYSTEM, "IP_addresses_default.csv")
        if platform == "win32":
            os.system('copy {} {}'.format(ip_file, ip_file_default))
        else:
            os.system('cp {} {}'.format(ip_file, ip_file_default))

        print(ip_file)
        w = csv.writer(open(ip_file, "w"))

        # loop over dictionary keys and values
        for key, val in self.PAR.IP_dict.items():

            # write every key and value to file
            w.writerow([key, val])
        w.close()

        self.save_IP_status()

    def load_IP_default(self):
        """ to be written """

        if self.PAR.inoutvar.get() == 'inside':
            ip_file = os.path.join(
                dir_SYSTEM, "IP_addresses_default_inside.csv")
        else:
            ip_file = os.path.join(
                dir_SYSTEM, "IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(dir_SYSTEM, "IP_addresses_default.csv")
        if platform == "win32":
            os.system('copy {} {}'.format(ip_file, ip_file_default))
        else:
            os.system('cp {} {}'.format(ip_file, ip_file_default))

        dict_from_csv = {}
        with open(ip_file_default, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]: rows[1] for rows in reader}
        inp.close()

        self.PAR.IP_dict['IP_Motors'] = dict_from_csv['IP_Motors']
        self.PAR.IP_dict['IP_CCD'] = dict_from_csv['IP_CCD']
        self.PAR.IP_dict['IP_DMD'] = dict_from_csv['IP_DMD']
        self.PAR.IP_dict['IP_SOAR'] = dict_from_csv['IP_SOAR']
        self.PAR.IP_dict['IP_SAMI'] = dict_from_csv['IP_SAMI']

        self.IP_Motors.set(dict_from_csv['IP_Motors'])
        self.IP_CCD.set(dict_from_csv['IP_CCD'])
        self.IP_DMD.set(dict_from_csv['IP_DMD'])
        self.IP_SOAR.set(dict_from_csv['IP_SOAR'])
        self.IP_SAMI.set(dict_from_csv['IP_SAMI'])

        # if PCM.MOTORS_onoff == 1:
        # self.IP_echo()

    def save_IP_status(self):
        """ to be written """
        file_IPstatus = open(os.path.join(
            dir_SYSTEM, "IP_status_dict.csv"), "w")
        w = csv.writer(file_IPstatus)

        # loop over dictionary keys and values
        for key, val in self.PAR.IP_status_dict.items():

            # write every key and value to file
            w.writerow([key, val])
        file_IPstatus.close()

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
        DMD.initialize(address=host, port=int(port))
        answer = DMD._open()
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
#            SF.read_IP_initial_status()
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
        """ to be written """

        # the size of the window is controlled when the menu is loaded
        parent.geometry("1000x500")

        parent.title("SAMOS Configuration")

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED,
                           activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(
            label="Recalibrate CCD2DMD", command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
# ---------------------------------------- DMD PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class DMDPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """

        super().__init__(container)

        label = tk.Label(self, text="DMD Page", font=('Times', '20'))
        label.pack(pady=0, padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        # super() recalls and includes the __init__() of the master class (tk.Topelevel), so one can use that stuff there without copying the code.
        if platform == "win32":
            self.bigfont = ("Arial", 12, 'bold')
            self.bigfont_20 = ("Arial", 12, 'bold')
            self.bigfont_15 = ("Arial", 10, 'bold')
        else:
            self.bigfont = ("Arial", 24)
            self.bigfont_20 = ("Arial", 20)
            self.bigfont_15 = ("Arial", 15)

        # reference to the master widget, which is the tk window
        # self.master = master

        # DMD.initialize()

        # changing the title of our master widget
        # self.title("IDG - DMD module driver")
        # Creation of init_window
        # self.geometry("610x407")
        # label = tk.Label(self, text ="DMD Control Window")
        # label.pack()
#
        # self.frame0l = tk.Frame(self,background="green")
        # self.frame0l.place(x=0, y=0, anchor="nw", width=390, height=320)

        # self.Echo_String = StringVar()
        # self.check_if_power_is_on()

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Startup Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.frame_startup = tk.Frame(self, background="light gray")
        self.frame_startup.place(x=4, y=4, anchor="nw", width=290, height=396)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       DMD Initialize
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # dmd.initialize()
        button_Initialize = tk.Button(
            self.frame_startup, text="Initialize", bd=3, command=self.dmd_initialize)
        button_Initialize.place(x=4, y=4)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       Load Basic Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        button_Whiteout = tk.Button(
            self.frame_startup, text="Blackout", bd=3, command=self.dmd_blackout)
        button_Whiteout.place(x=4, y=34)
        button_Blackout = tk.Button(
            self.frame_startup, text="Whiteout", bd=3, command=self.dmd_whiteout)
        button_Blackout.place(x=140, y=34)
        button_Checkerboard = tk.Button(
            self.frame_startup, text="Checkerboard", bd=3, command=self.dmd_checkerboard)
        button_Checkerboard.place(x=4, y=64)
        button_Invert = tk.Button(
            self.frame_startup, text="Invert", bd=3, command=self.dmd_invert)
        button_Invert.place(x=4, y=94)
        button_antInvert = tk.Button(
            self.frame_startup, text="AntInvert", bd=3, command=self.dmd_antinvert)
        button_antInvert.place(x=140, y=94)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       Load Custom Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        button_edit = tk.Button(self.frame_startup,
                                text="Edit DMD Map",
                                command=self.BrowseMapFiles)
        button_edit.place(x=4, y=140)

        button_load_map = tk.Button(self.frame_startup,
                                    text="Load DMD Map",
                                    command=self.LoadMap)
        button_load_map.place(x=140, y=140)

        label_filename = tk.Label(self.frame_startup, text="Current DMD Map")
        label_filename.place(x=4, y=170)
        self.str_map_filename = tk.StringVar()
        self.textbox_filename = tk.Text(self.frame_startup, height=1, width=22)
        self.textbox_filename.place(x=120, y=170)

        """ Define custom slit """

        label_x0 = tk.Label(self.frame_startup, text="x0")
        label_x0.place(x=5, y=200)
        self.x0 = tk.IntVar()
        self.x0.set(540)
        self.entry_x0 = tk.Entry(
            self.frame_startup, width=4, textvariable=self.x0)
        self.entry_x0.place(x=30, y=198)

        label_x1 = tk.Label(self.frame_startup, text="x1")
        label_x1.place(x=85, y=200)
        self.x1 = tk.IntVar()
        self.x1.set(540)
        entry_x1 = tk.Entry(self.frame_startup, width=4, textvariable=self.x1)
        entry_x1.place(x=110, y=198)

        label_y0 = tk.Label(self.frame_startup, text="y0")
        label_y0.place(x=150, y=200)
        self.y0 = tk.IntVar()
        self.y0.set(1024)
        entry_y0 = tk.Entry(self.frame_startup, width=4, textvariable=self.y0)
        entry_y0.place(x=175, y=198)


        label_y1 = tk.Label(self.frame_startup, text="y1")
        label_y1.place(x=210, y=200)
        self.y1 = tk.IntVar()
        self.y1.set(1024)
        entry_y1 = tk.Entry(self.frame_startup, width=4, textvariable=self.y1)
        entry_y1.place(x=235, y=198)

        button_add_slit = tk.Button(self.frame_startup,
                                    text="Add",
                                    command=self.AddSlit)
        button_add_slit.place(x=4, y=260)

        button_save_map = tk.Button(self.frame_startup,
                                    text="Save",
                                    command=self.SaveMap)
        button_save_map.place(x=104, y=260)

        button_push_slit = tk.Button(self.frame_startup,
                                     text="Push",
                                     command=self.PushCurrentMap)
        button_push_slit.place(x=204, y=260)


        """ Load Slit Table """
        button_load_slits = tk.Button(self.frame_startup,
                                      text="Load Slit List",
                                      command=self.LoadSlits)
        button_load_slits.place(x=140, y=320)

        # gridfnam = tk.StringVar()
        label_filename_slits = tk.Label(
            self.frame_startup, text="Current Slit List")
        label_filename_slits.place(x=4, y=350)
        # params["gridfnam"] = gridfnam
        # print(gridfnam)
        self.str_filename_slits = tk.StringVar()
        self.textbox_filename_slits = tk.Text(
            self.frame_startup, height=1, width=20)
        self.textbox_filename_slits.place(x=120, y=350)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       Display Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        self.canvas = tk.Canvas(self, width=300, height=270, bg="dark gray")
        self.canvas.place(x=300, y=4)
        """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       HADAMARD Patterns
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        """
        self.Hadamard_frame = tk.Frame(self, width=300, height=400, bg="gray")
        self.Hadamard_frame.place(x=605, y=4)
        self.HadamardConf_LabelFrame = tk.LabelFrame(
            self.Hadamard_frame, width=292, height=392, text="Hadamard Configuration")
        self.HadamardConf_LabelFrame.place(x=4, y=4)

        """ Type of Matrix: S or H?"""
# ===#====
        self.SHMatrix_Checked = tk.StringVar(None, "S")
        btn1 = tk.Radiobutton(self.HadamardConf_LabelFrame, text="S Matrix", padx=20,
                              variable=self.SHMatrix_Checked, value="S", command=self.set_SH_matrix)
        btn2 = tk.Radiobutton(self.HadamardConf_LabelFrame, text="H Matrix", padx=20,
                              variable=self.SHMatrix_Checked, value="H", command=self.set_SH_matrix)
# >>>>>>> Stashed changes
        btn1.place(x=4, y=5)
        btn2.place(x=4, y=30)  # 150, y=20)

        """ Order of H Matrix?"""
        label_order = tk.Label(self.HadamardConf_LabelFrame,
                               text="Order: ", bd=4)  # , font=("Arial", 24))
# <<<#<<<< Updated upstream
        label_order.place(x=140, y=14)

        """ Order of S Matrix?"""
# >>>>>>> Stashed changes
        self.Sorders = (3, 7, 11, 15, 19, 23, 31, 35, 43,
                        47, 63, 71, 79, 83, 103, 127, 255)
        self.Sorder = tk.IntVar()
        self.Sorder.set(self.Sorders[1])
        self.order = self.Sorder.get()
        self.Sorder_menu = tk.OptionMenu(
            self.HadamardConf_LabelFrame, self.Sorder, *self.Sorders, command=self.set_SH_matrix)
# <<<#<<<< Updated upstream
        self.Sorder_menu.place(x=190, y=15)

        """ Order of H Matrix?"""
        self.Horders = (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
        self.Horder = tk.IntVar()
        self.Horder.set(self.Horders[1])
        self.order = self.Sorder.get()
        self.Horder_menu = tk.OptionMenu(
            self.HadamardConf_LabelFrame, self.Horder, *self.Horders, command=self.set_SH_matrix)
        self.Horder_menu.place(x=1090, y=29)
# =======
        self.Sorder_menu.place(x=190, y=19)
        #

        """ Slit Width?"""
        label_width = tk.Label(self.HadamardConf_LabelFrame,
                               text="Slit Width: ", bd=4)  # , font=("Arial", 24))
        label_width.place(x=4, y=74)
        self.entrybox_width = tk.Entry(self.HadamardConf_LabelFrame, width=3)
        self.entrybox_width.bind("<Return>", self.calculate_field_width)
        self.entrybox_width.insert(0, "3")
        self.entrybox_width.place(x=80, y=73)

        """ Slit Length?"""
        label_length = tk.Label(
            self.HadamardConf_LabelFrame, text="Length:", bd=4)  # , font=("Arial", 24))
        label_length.place(x=154, y=74)
        self.entrybox_length = tk.Entry(self.HadamardConf_LabelFrame, width=4)
        self.entrybox_length.bind("<Return>", self.calculate_field_width)
        self.entrybox_length.insert(0, "256")
        self.entrybox_length.place(x=230, y=73)

        """ Center Field?"""
        label_center_x = tk.Label(
            self.HadamardConf_LabelFrame, text="Center: Xo", bd=4)  # , font=("Arial", 24))
        label_center_x.place(x=4, y=111)
        self.entrybox_center_x = tk.Entry(
            self.HadamardConf_LabelFrame, width=4)
        self.entrybox_center_x.insert(0, "540")
        self.entrybox_center_x.place(x=80, y=110)
        # , font=("Arial", 24))
        label_center_y = tk.Label(
            self.HadamardConf_LabelFrame, text="Center: Yo", bd=4)
        label_center_y.place(x=154, y=111)
        self.entrybox_center_y = tk.Entry(
            self.HadamardConf_LabelFrame, width=5)
        self.entrybox_center_y.insert(0, "1024")
        self.entrybox_center_y.place(x=230, y=110)

        """ Field With?"""
        label_field_width = tk.Label(
            self.HadamardConf_LabelFrame, text="Width:", bd=4)  # , font=("Arial", 24))
        label_field_width.place(x=4, y=148)
        self.field_width_ = tk.StringVar()
        self.field_width_.set("21")
        self.textbox_field_width = tk.Text(
            self.HadamardConf_LabelFrame,  height=1, width=4, bg="red", fg="white", font=self.bigfont_15)
        self.textbox_field_width.place(x=70, y=150)
        self.textbox_field_width.insert(tk.INSERT, "21")

        """ GENERATE """
        self.button_Generate = tk.Button(self.HadamardConf_LabelFrame, text="GENERATE", bd=3, bg='#A877BA', font=self.bigfont,
                                         command=self.HTS_generate)
        self.button_Generate.place(x=70, y=150)  # 80)
        self.textbox_masknames = tk.Text(
            self.HadamardConf_LabelFrame, height=1, width=37)
        self.textbox_masknames.place(x=4, y=190)  # 220)

        """ Rename?"""
        button_save_masks = tk.Label(self.HadamardConf_LabelFrame,
                                     text="Rename:")
        button_save_masks.place(x=4, y=213)  # 243)
        self.entrybox_newmasknames = tk.Entry(
            self.HadamardConf_LabelFrame, width=25)
        self.entrybox_newmasknames.bind("<Return>", self.rename_masks_file)
        self.entrybox_newmasknames.place(x=70, y=213)  # 243)

        self.Hadamard_RADEC_frame = tk.Frame(
            self.HadamardConf_LabelFrame, width=280, height=125, bg="gray")
        self.Hadamard_RADEC_frame.place(x=0, y=245)  # 275)
        """ Target RADEC?"""
        label_target_RA = tk.Label(
            self.Hadamard_RADEC_frame, text="Target RA:", bd=4)  # , font=("Arial", 24))
        label_target_RA.place(x=4, y=4)
        self.entrybox_target_RA = tk.Entry(
            self.Hadamard_RADEC_frame, width=14)
        self.entrybox_target_RA.insert(0, "01.234567")
        self.entrybox_target_RA.place(x=80, y=4)

        label_target_DEC = tk.Label(
            self.Hadamard_RADEC_frame, text="Target DEC:", bd=4)  # , font=("Arial", 24))
        label_target_DEC.place(x=4, y=34)
        self.entrybox_target_DEC = tk.Entry(
            self.Hadamard_RADEC_frame, width=14)
        self.entrybox_target_DEC.insert(0, "01.234567")
        self.entrybox_target_DEC.place(x=80, y=34)

        """ GENERATE FROM RADEC"""
        self.button_Generate_from_RADEC = tk.Button(self.Hadamard_RADEC_frame, text="GENERATE FROM RADEC", bd=3, bg='#A877BA', font=self.bigfont_20,
                                                    command=self.HTS_generate_from_RADEC)
        self.button_Generate_from_RADEC.place(x=10, y=64)

    def HTS_generate_from_RADEC(self):
        """ Generates HTS mask centered on RADEC coordinates
            - requires WCS (check on existence has to be written)
            - no check on the RADEC being inside the field (to be written)
            - RADEC format in decimal degrees (no HH:MM:SS, dd:mm:ss)
        """
        # get AR and DEC from input fields
        dec_HTS_center = float(self.entrybox_target_DEC.get())
        ra_HTS_center = float(self.entrybox_target_RA.get())

        # convert radec->pixels using WCS
        # from https://gist.github.com/barentsen/548f88ef38f645276fccea1481c76fc3
        ad = np.array([[ra_HTS_center, dec_HTS_center]]).astype(float)
        x_CCD_HTS_center, y_CCD_HTS_center = WCS_global.all_world2pix(ad, 0)[0]

        # convert pixels -> DMD mirrors
        x_DMD_HTS_center, y_DMD_HTS_center = convert.CCD2DMD(
            int(x_CCD_HTS_center), int(y_CCD_HTS_center))

        # refresh entrybox field
        self.entrybox_center_x.delete(0, tk.END)
        self.entrybox_center_x.insert(0, int(x_DMD_HTS_center))
        self.entrybox_center_y.delete(0, tk.END)
        self.entrybox_center_y.insert(0, int(y_DMD_HTS_center))

        # generate mask
        self.HTS_generate()
        """
        """" Check mask  ? """
        """
        label_check = tk.Label(self.HadamardConf_LabelFrame,
                               text="Check Mask Nr.: ", bd=4)  # , font=("Arial", 24))
        label_check.place(x=4, y=270)
        self.mask_arrays = np.arange(0,self.order)
        self.mask_checked = tk.StringVar()
        self.mask_checked.set(0)
#        self.mask_check_menu = tk.OptionMenu(
#            self.HadamardConf_LabelFrame, self.mask_checked, *self.mask_arrays, command=self.check_mask)
        self.mask_check_menu = ttk.Combobox(self.HadamardConf_LabelFrame, width =4,
                                            textvariable=self.mask_checked, style="TCombobox")
        self.mask_check_menu.bind("<<ComboboxSelected>>", self.check_mask)
        self.mask_check_menu['values'] = list(self.mask_arrays)
        self.mask_check_menu.place(x=120, y=271)
        """

        """ Load Masks?"""
        """
        button_load_masks = tk.Button(self.HadamardConf_LabelFrame,
                                            text="Load masks:",
                                            command=self.load_masks_file)
        button_load_masks.place(x=4, y=321)
        label_filename_masks = tk.Label(
            self.HadamardConf_LabelFrame, text="Loaded Mask Set:")
        label_filename_masks.place(x=4, y=349)
        # self.str_filename_masks = tk.StringVar()
        self.textbox_filename_masks = tk.Text(
            self.HadamardConf_LabelFrame, height=1, width=22)
        self.textbox_filename_masks.place(x=120, y=350)
        """
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
    """
    def load_masks_file(self):
        """""""load_masks_file """""""
        self.textbox_filename_masks.delete('1.0', tk.END)
        filename_masks = filedialog.askopenfilename(initialdir=os.path.join(local_dir,"Hadamard","mask_sets"),
                                        title="Select a File",
                                        filetypes=(("Text files",
                                                      "*.bmp"),
                                                     ("all files",
                                                      "*.*")))
        head, tail = os.path.split(filename_masks)
        self.textbox_filename_masks.insert(tk.END, tail)
        self.textbox_masknames.delete("1.0", tk.END)
        self.entrybox_newmasknames.delete(0, tk.END)
        self.entrybox_newmasknames.insert(tk.INSERT,str(tail[0:tail.rfind("_")]))
        #
        # actually load the masks!
        # to be written
        # im =np.asarray(Image.open(local_dir+"/Hadamard/mask_sets/" + maskfile_bmp), dtype='int')
        pass
    """

    def rename_masks_file(self, event=None):
        """ rename the mask file, only the part starting with 'mask' """

        oldfilename_masks = self.textbox_masknames.get("1.0", tk.END)

        # => find all positions of the '_' string in the filename
        i_ = [x for x, v in enumerate(oldfilename_masks) if v == '_']
        old_string = oldfilename_masks[i_[0]+1:i_[1]]
        # second = oldfilename_masks[i_[1]]

        old = str(oldfilename_masks[0:i_[-1]])
        new_string = self.entrybox_newmasknames.get()
        file_names = os.path.join(
            local_dir, "Hadamard", "mask_sets", old+"*.bmp")
        files = sorted(glob.glob(file_names))
        for ifile in range(len(files)):
            path, tail = os.path.split(files[ifile])
            oldName = files[ifile]
            newName = os.path.join(path, tail.replace(old_string, new_string))
            os.rename(oldName, newName)
        self.textbox_masknames.delete("1.0", tk.END)
        self.textbox_masknames.insert(
            tk.END, oldfilename_masks[0:-1].replace(old_string, new_string))
        self.entrybox_newmasknames.delete(0, tk.END)

    """
    def check_mask(self, event=None):
        """""" to be written """""""
        maskname = self.textbox_masknames.get("1.0",tk.END)
        basename = str(maskname[0:maskname.rfind("_")])
        maskfile = basename + "_" + self.mask_checked.get()
        maskfile_bmp = maskfile + ".bmp"
        maskfile_png = maskfile + ".png"
        image_mask = Image.open(os.path.join(
            local_dir,"Hadamard","mask_sets",maskfile_bmp))
        im =np.asarray(Image.open(os.path.join(
            local_dir,"Hadamard","mask_sets",maskfile_bmp)), dtype='int')
        # im.resize((512,270)).save(local_dir+"/Hadamslitard/mask_sets/" + maskfile_png)
        plt.clf()
        shape_rotated = np.rot90(im, k=1, axes=(0, 1))
        plt.imshow(shape_rotated, vmin=0, vmax=1)
        plt.savefig(os.path.join(
            local_dir,"Hadamard","mask_sets", maskfile_png))
        plt.close()  #needed to overwrite!
        image_map = Image.open(os.path.join(
            local_dir,"Hadamard","mask_sets", maskfile_png))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()

        """

    def calculate_field_width(self, event=None):
        """ calculate_field_width """
        self.textbox_field_width.delete("1.0", tk.END)
        self.field_width = int(self.entrybox_width.get()) * self.order
        self.textbox_field_width.insert(tk.INSERT, str(self.field_width))

    def set_SH_matrix(self, event=None):
        """ set_SH_matrix """
        if self.SHMatrix_Checked.get() == "S":
            self.Sorder_menu.place(x=190, y=19)
            self.Horder_menu.place(x=1900, y=19)
            self.order = self.Sorder.get()
            self.mask_arrays = np.arange(0, self.order)
        else:
            self.Sorder_menu.place(x=1900, y=19)
            self.Horder_menu.place(x=190, y=19)
            self.order = self.Horder.get()
            a = tuple(['a'+str(i), 'b'+str(i)] for i in range(1, 4))
            self.mask_arrays = [inner for outer in zip(*a) for inner in outer]
        self.calculate_field_width()
        print(self.order)
        print(self.mask_arrays)
        #self.mask_check_menu['values'] = list(self.mask_arrays)
        # self.mask_check_menu['menu'].delete(0, 'end')
        # for choice in self.mask_arrays:
        #    self.mask_check_menu['menu'].add_command(label=choice, command=tk._setit(self.mask_checked,self.mask_arrays))

    def HTS_generate(self):
        """ HTS_generate """
        DMD_size = (1080, 2048)
        matrix_type = self.SHMatrix_Checked.get()  # Two options, H or S
        # e.g. 15 Order of the hadamard matrix (or S matrix)
        order = self.order
        """note the flipping of xy when we talk to the DMD"""
        Xo, Yo = int(self.entrybox_center_y.get()), int(
            self.entrybox_center_x.get())
        # DMD_size[1]/2, DMD_size[0]/2   # Coordinates on the DMD to center the Hadamard matrix around

        # 4 # Slit width in number of micromirrors
        slit_width = int(self.entrybox_width.get())
        # 4 # Slit length in number of micromirrors
        slit_length = int(self.entrybox_length.get())

        # folder = 'C:/Users/Kate/Documents/hadamard/mask_sets/' # Change path to fit user needs

#        folder = os.path.join(local_dir,'Hadamard','mask_sets',os.path.sep)
        # above line was not allowing to write data
        folder = os.path.join(local_dir, 'Hadamard', 'mask_sets/')
        if matrix_type == 'S':
            mask_set, matrix = make_S_matrix_masks(
                order, DMD_size, slit_width, slit_length, Xo, Yo, folder)  # mask_set.shape (1080,2048,7)
#            name = 'S'+str(order)+'_'+str(slit_width)+'w_mask_1-'+str(order)+'.bmp'
            name = 'S'+str(order)+'_mask_'+str(slit_width) + \
                'w_' + "{:03d}".format(order) + '.bmp'
        if matrix_type == 'H':
            mask_set_a, mask_set_b, matrix = make_H_matrix_masks(
                order, DMD_size, slit_width, slit_length, Xo, Yo, folder)
#            name = str(matrix_type)+str(order)+'_'+str(slit_width)+'w_mask_ab1-'+str(order)+'.bmp'
            name = str(matrix_type)+str(order)+'_mask_' + \
                str(slit_width) + 'w_ab_' + "{:03d}".format(order) + '.bmp'
        self.textbox_masknames.delete("1.0", tk.END)
        self.textbox_masknames.insert(tk.INSERT, str(name))
        self.entrybox_newmasknames.delete(0, tk.END)
        self.entrybox_newmasknames.insert(
            tk.INSERT, str(name[0:name.rfind("_")]))
        # self.textbox_filename_masks.delete("1.0", tk.END)
        # self.textbox_filename_masks.insert(tk.INSERT,str(name))


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#         # Exit
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        quitButton = tk.Button(self, text="Exit",command=self.client_exit)
#        quitButton.place(x=180, y=350)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# echo client()
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


    def dmd_initialize(self):
        """ dmd_initialize """
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("none")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "none")

    def dmd_whiteout(self):
        """ sets all mirrors "ON" as seen by the imaging channel
            from the point of view of the DMD with its current orientation, all mirrors are "OFF" """
        DMD.apply_blackout()
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "whiteout_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("whiteout")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "whiteout")

    def dmd_blackout(self):
        """ sets all mirrors "OFF" as seen by the imaging channel
            from the point of view of the DMD with its current orientation, all mirrors are "ON" """
        DMD.apply_whiteout()
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "blackout_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("blackoutout")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "blackout")

    def dmd_checkerboard(self):
        """ dmd_checkerboard """
        DMD.apply_checkerboard()
        # global img
        shutil.copy(os.path.join(dir_DMD, "checkerboard.png"),
                    os.path.join(dir_DMD, "current_dmd_state.png"))
        time.sleep(1)
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        self.str_map_filename.set("checkerboard")
        self.textbox_filename.delete("1.0", "end")
        self.textbox_filename.insert(tk.INSERT, "checkerboard")

    def dmd_invert(self):
        """ dmd_invert """
        DMD.apply_invert()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        # image=image_map.convert("L")
        # image_invert = ImageOps.invert(image)
        # image_invert.save(dir_DMD+ "/current_dmd_state.png")
        # global img
        # img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
        # self.img= ImageTk.PhotoImage(image_invert)
        # Add image to the Canvas Items
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()
        # self.str_map_filename.set("checkerboard")
        self.textbox_filename.insert(tk.INSERT, " inverted ")


#        # global img
#        img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
#        #Add image to the Canvas Items
#        self.canvas.create_image(104,128,image=img)

    def dmd_antinvert(self):
        """ dmd_antinvert """
        DMD.apply_antinvert()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()

    def BrowseMapFiles(self):
        """ BrowseMapFiles """
        self.textbox_filename.delete('1.0', tk.END)
        filename = filedialog.askopenfilename(initialdir=os.path.join(dir_DMD, "DMD_csv", "maps"),
                                              title="Select a File",
                                              filetypes=(("Text files",
                                                          "*.csv"),
                                                         ("all files",
                                                          "*.*")))
        if platform != "win32":
            subprocess.call(['open', '-a', 'TextEdit', filename])
        else:        
            cmd = 'start "excel" "%s"' %(filename)
            os.system(cmd)
            #"D:\\SAMOS_NEWGUI\\SAMOS_DMD_dev\\DMD_csv\\maps\\ThinCentralSlit.csv"')
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)
        self.str_map_filename.set(tail)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load DMD map file
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def LoadMap(self):
        """ LoadMap """
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename = filedialog.askopenfilename(initialdir=os.path.join(dir_DMD, "DMD_csv", "maps"),
                                              title="Select a File",
                                              filetypes=(("Text files",
                                                          "*.csv"),
                                                         ("all files",
                                                          "*.*")))
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)

        main_fits_header.set_param("dmdmap", tail)

        myList = []

        with open(filename, 'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        # print(myList)
        file.close()

        for i in range(len(myList)):
            print("Row " + str(i) + ": " + str(myList[i]))

        test_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]), int(
                myList[i][2]):int(myList[i][3])] = int(myList[i][4])

        try:
            DMD.apply_shape(test_shape)
        except:
            print("DMD non connected")

        """ CREATE THE astropy regions file in PIXEL UNITS """

        # 1. instantiate the convert class
        c = CONVERT()

        f = open(os.path.join(local_dir, 'SAMOS_regions',
                 'pixels', tail[:-3]+'reg'), 'w')

        # 2. loop over the lines to create ds9 region files
        header = "# Region file format: DS9 astropy/regions\nglobal edit=1 width=1 font=Sans Serif fill=0 color=red\nimage"
        f.write(header + '\n')
        for i in range(len(myList)):
            x0, y0 = c.DMD2CCD(float(myList[i][0]), float(myList[i][2]))
            x1, y1 = c.DMD2CCD(float(myList[i][1]), float(myList[i][3]))
            xc = (x0 + x1)/2.
            yc = (y0 + y1)/2.
            dx = x1-x0
            dy = y1-y0
            output_string = "box("+str(xc)+","+str(yc) + \
                ","+str(dx)+","+str(dy)+",0)"
            print(output_string)
            f.write(output_string + '\n')
        f.close()

        self.m = MainPage(None, None)
        self.m.textbox_filename_regfile_xyAP.insert(tk.END, tail[:-3]+'reg')
        # Create a photoimage object of the image in the path
        # Load an image in the script
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104, 128, image=self.img)
        image_map.close()

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load Slit file
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def LoadSlits(self):
        """ LoadSlits """
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename_slits = filedialog.askopenfilename(initialdir=os.path.join(dir_DMD, "DMD_csv", "slits"),
                                                    title="Select a File",
                                                    filetypes=(("Text files",
                                                                "*.csv"),
                                                               ("all files",
                                                                "*.*")))
        head, tail = os.path.split(filename_slits)
        self.textbox_filename_slits.insert(tk.END, tail)
        main_fits_header.set_param("dmdmap", tail)
        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index), int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        self.slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in table.index:
            self.slit_shape[x1[i]:x2[i], y1[i]:y2[i]] = 0
        DMD.apply_shape(self.slit_shape)

        # Create a photoimage object of the image in the path
        # Load the image
        # global img
        # self.img = None
#        image_map = Image.open(local_dir + "/current_dmd_state.png")
#        self.img= ImageTk.PhotoImage(image_map)
#         image_map.close()
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas, image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
        image_map.close()

        # Add image to the Canvas Items
        # print('img =', self.img)
        # self.canvas.create_image(104,128,image=self.img)

    def AddSlit(self):
        """
        # 1. read the current filename
        # 2. open the .csv file
        # 3. add the slit
        """

        # 1. read the current filename
        filename_in_text = self.textbox_filename.get("1.0",'end-1c')
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = os.path.join(
            dir_DMD, "DMD_csv", "maps", filename_in_text)
        
        myList = []
        # 2. that's just a string! check if file exists to load what you already inherited
        if os.path.isfile(self.map_filename) == True: 
            with open(self.map_filename, 'r') as file:
                myFile = csv.reader(file)
                for row in myFile:
                    myList.append(row)
            file.close()
 
        # 3. add the slit
        # set the four corners of the aperture
#        row = [str(int(self.x0.get())), str(int(self.y0.get())), str(
#            int(self.x1.get())), str(int(self.y1.get())), "0"]
        row = [str(int(self.x0.get())), str(int(self.x1.get())), str(
            int(self.y0.get())), str(int(self.y1.get())), "0"]
        myList.append(row)
        self.map = myList

    def SaveMap(self):
        """ SaveMap """
        print("Saving Map")
        filename_in_text = self.textbox_filename.get("1.0",'end-1c')
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = os.path.join(
            dir_DMD, "DMD_csv", "maps", filename_in_text)
        pandas_map = pd.DataFrame(self.map)
        pandas_map.to_csv(self.map_filename, index=False, header=None)
        print("Map Saved")
        
    def PushCurrentMap(self):
        """ Push to the DMD the file in Current DMD Map Textbox """

        filename_in_text = self.textbox_filename.get("1.0",'end-1c')
        if filename_in_text[-4:] != ".csv":
            filename_in_text.append(".csv")
        self.map_filename = os.path.join(
            dir_DMD, "DMD_csv", "maps", filename_in_text)

        myList = []
        with open(self.map_filename, 'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        file.close()

        # for i in range(len(myList)):
        #    print("Row " + str(i) + ": " + str(myList[i]))

        test_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]), int(
                myList[i][2]):int(myList[i][3])] = int(myList[i][4])

        DMD.apply_shape(test_shape)

        # Create a photoimage object of the image in the path
        # Load an image in the script
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104, 128, image=self.img)
        image_map.close()

    def enter_command(self):
        """ enter_command """
        print('command entered:', self.Command_string.get())
        # convert StringVar to string
        t = DMD.send_command_string(self.Command_string.get())
        self.Echo_String.set(t)
        print(t)

#    def client_exit(self):
#        print("destroy")
#        self.destroy()

    def create_menubar(self, parent):
        """ create_menubar """
        parent.geometry("910x407")
        if platform == "win32":
            parent.geometry("910x425")
        parent.title("SAMOS DMD Controller")
        self.PAR = SAMOS_Parameters()
        # MainPage class expects 2 arguments. They may be None.
        self.Main = MainPage(None, None)

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
# ---------------------------------------- MOTORS PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class Motors(tk.Frame):
    """ Motors """

    def __init__(self, parent, container):
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
#        data = ascii.read(local_dir+'/IDG_filter_positions.txt')
#        print(data)

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
#        data = ascii.read(local_dir+'/IDG_Filter_positions.txt')
#        print(data)

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
        if platform == "win32":
            parent.geometry("500x400")

        parent.title("SAMOS Motor Controller")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
# ---------------------------------------- CCD PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class CCDPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """
        super().__init__(container)

        label = tk.Label(self, text="CCD Page", font=('Times', '20'))
        label.pack(pady=0, padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        if platform == "win32":
            self.bigfont = ("Arial", 12, 'bold')
            self.bigfont_20 = ("Arial", 12, 'bold')
            self.bigfont_15 = ("Arial", 10, 'bold')
        else:
            self.bigfont = ("Arial", 24)
            self.bigfont_20 = ("Arial", 20)
            self.bigfont_15 = ("Arial", 15)

        # , width=300, height=300)
        self.frame0l = tk.Frame(self, background="cyan")
        self.frame0l.place(x=0, y=0, anchor="nw", width=950, height=590)

        """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    ACQUIRE IMAGE Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        #, width=400, height=800)
        self.frame2l = tk.Frame(self.frame0l,background="dark turquoise")
        self.frame2l.place(x=0, y=4, anchor="nw", width=420, height=300)



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#       CONTROL OF SCIENCE AND REFERENCE FILES
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

#        root = tk.Tk()
#        root.title("Tab Widget")
        tabControl = ttk.Notebook(self.frame2l)

        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        tab4 = ttk.Frame(tabControl)
        tab5 = ttk.Frame(tabControl)

        tabControl.add(tab1, text ='Image')
        tabControl.add(tab2, text ='Bias')
        tabControl.add(tab3, text ='Dark')
        tabControl.add(tab4, text ='Flat')
        tabControl.add(tab5, text ='Buffer')
        tabControl.pack(expand = 1, fill ="both")

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      SCIENCE
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        labelframe_Acquire =  tk.LabelFrame(
            tab1, text="Acquire Image", font=("Arial", 24))
        labelframe_Acquire.pack(fill="both", expand="yes")
#        labelframe_Grating.place(x=4, y=10)

        label_ExpTime =  tk.Label(labelframe_Acquire, text="Exp. Time (s)")
        label_ExpTime.place(x=4,y=10)
        self.ExpTime=tk.StringVar()
        self.ExpTime.set("0.01")
        entry_ExpTime = tk.Entry(
            labelframe_Acquire, textvariable=self.ExpTime, width=5,  bd =3)
        entry_ExpTime.place(x=100, y=10)

        label_ObjectName =  tk.Label(labelframe_Acquire, text="Object Name:")
        label_ObjectName.place(x=4,y=30)
        entry_ObjectName = tk.Entry(labelframe_Acquire, width=11,  bd =3)
        entry_ObjectName.place(x=100, y=30)

        label_Comment =  tk.Label(labelframe_Acquire, text="Comment:")
        label_Comment.place(x=4,y=50)
#        scrollbar = tk.Scrollbar(orient="horizontal")
        # , xscrollcommand=scrollbar.set)
        entry_Comment = tk.Entry(labelframe_Acquire, width=11,  bd =3)
        entry_Comment.place(x=100, y=50)

        button_ExpStart=  tk.Button(
            labelframe_Acquire, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
                                         #  command=self.expose)
        button_ExpStart.place(x=50,y=75)



        label_Display =  tk.Label(
            labelframe_Acquire, text="Correct for Display:")
        label_Display.place(x=4,y=120)
        subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(
            labelframe_Acquire, text='Bias',variable=subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=140)
        subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(
            labelframe_Acquire, text='Dark',variable=subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60,y=140)
        divide_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(
            labelframe_Acquire, text='Flat',variable=divide_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120,y=140)
        subtract_Buffer = tk.IntVar()
        check_Buffer = tk.Checkbutton(
            labelframe_Acquire, text='Buffer',variable=subtract_Buffer, onvalue=1, offvalue=0)
        check_Buffer.place(x=180,y=140)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      BIAS
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Bias =  tk.LabelFrame(tab2, text="Bias",
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Bias.pack(fill="both", expand="yes")

#        labelframe_Bias.place(x=5,y=5)
        label_Bias_ExpT =  tk.Label(labelframe_Bias, text="Exposure time (s):")
        label_Bias_ExpT.place(x=4,y=10)
        self.Bias_ExpT = tk.StringVar(value="0.00")
        entry_Bias_ExpT = tk.Entry(
            labelframe_Bias, width=6,  bd =3, textvariable=self.Bias_ExpT)
        entry_Bias_ExpT.place(x=120, y=6)

        label_Bias_NofFrames =  tk.Label(
            labelframe_Bias, text="Nr. of Frames:")
        label_Bias_NofFrames.place(x=4,y=40)
        self.Bias_NofFrames = tk.StringVar(value="10")
        entry_Bias_NofFrames = tk.Entry(
            labelframe_Bias, width=5,  bd =3, textvariable=self.Bias_NofFrames)
        entry_Bias_NofFrames.place(x=100, y=38)


        self.var_Bias_saveall = tk.IntVar()
        r1_Bias_saveall = tk.Radiobutton(
            labelframe_Bias, text = "Save single frames", variable=self.var_Bias_saveall, value=1)
        r1_Bias_saveall.place(x=150, y=38)

        label_Bias_MasterFile =  tk.Label(
            labelframe_Bias, text="Master Bias File:")
        label_Bias_MasterFile.place(x=4,y=70)
        self.Bias_MasterFile = tk.StringVar(value="Bias")
        entry_Bias_MasterFile = tk.Entry(
            labelframe_Bias, width=11,  bd =3, textvariable=self.Bias_MasterFile)
        entry_Bias_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(
            labelframe_Bias, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)

#        root.mainloop()





# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      Dark
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Dark =  tk.LabelFrame(tab3, text="Dark",
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Dark.pack(fill="both", expand="yes")

        label_Dark_ExpT =  tk.Label(labelframe_Dark, text="Exposure time (s):")
        label_Dark_ExpT.place(x=4,y=10)
        self.Dark_ExpT = tk.StringVar(value="0.00")
        entry_Dark_ExpT = tk.Entry(
            labelframe_Dark, width=6,  bd =3, textvariable=self.Dark_ExpT)
        entry_Dark_ExpT.place(x=120, y=6)

        label_Dark_NofFrames =  tk.Label(
            labelframe_Dark, text="Nr. of Frames:")
        label_Dark_NofFrames.place(x=4,y=40)
        self.Dark_NofFrames = tk.StringVar(value="10")
        entry_Dark_NofFrames = tk.Entry(
            labelframe_Dark, width=5,  bd =3, textvariable=self.Dark_NofFrames)
        entry_Dark_NofFrames.place(x=100, y=38)


        var_Dark_saveall = tk.IntVar()
        r1_Dark_saveall = tk.Radiobutton(
            labelframe_Dark, text = "Save single frames", variable=var_Dark_saveall, value=1)
        r1_Dark_saveall.place(x=150, y=38)

        label_Dark_MasterFile =  tk.Label(
            labelframe_Dark, text="Master Dark File:")
        label_Dark_MasterFile.place(x=4,y=70)
        self.Dark_MasterFile = tk.StringVar(value="Dark")
        entry_Dark_MasterFile = tk.Entry(
            labelframe_Dark, width=11,  bd =3, textvariable=self.Dark_MasterFile)
        entry_Dark_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(
            labelframe_Dark, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      Flat
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Flat =  tk.LabelFrame(tab4, text="Flat",
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Flat.pack(fill="both", expand="yes")

        label_Flat_ExpT =  tk.Label(labelframe_Flat, text="Exposure time (s):")
        label_Flat_ExpT.place(x=4,y=10)
        self.Flat_ExpT = tk.StringVar(value="0.00")
        entry_Flat_ExpT = tk.Entry(
            labelframe_Flat, width=6,  bd =3, textvariable=self.Flat_ExpT)
        entry_Flat_ExpT.place(x=120, y=6)

        label_Flat_NofFrames =  tk.Label(
            labelframe_Flat, text="Nr. of Frames:")
        label_Flat_NofFrames.place(x=4,y=40)
        self.Flat_NofFrames = tk.StringVar(value="10")
        entry_Flat_NofFrames = tk.Entry(
            labelframe_Flat, width=5,  bd =3, textvariable=self.Flat_NofFrames)
        entry_Flat_NofFrames.place(x=100, y=38)


        var_Flat_saveall = tk.IntVar()
        r1_Flat_saveall = tk.Radiobutton(
            labelframe_Flat, text = "Save single frames", variable=var_Flat_saveall, value=1)
        r1_Flat_saveall.place(x=150, y=38)

        label_Flat_MasterFile =  tk.Label(
            labelframe_Flat, text="Master Flat File:")
        label_Flat_MasterFile.place(x=4,y=70)
        self.Flat_MasterFile = tk.StringVar(value="Flat")
        entry_Flat_MasterFile = tk.Entry(
            labelframe_Flat, width=11,  bd =3, textvariable=self.Flat_MasterFile)
        entry_Flat_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(
            labelframe_Flat, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)




# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      Buffer
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Buffer =  tk.LabelFrame(tab5, text="Buffer",
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Buffer.pack(fill="both", expand="yes")

        label_Buffer_ExpT =  tk.Label(
            labelframe_Buffer, text="Exposure time (s):")
        label_Buffer_ExpT.place(x=4,y=10)
        self.Buffer_ExpT = tk.StringVar(value="0.00")
        entry_Buffer_ExpT = tk.Entry(
            labelframe_Buffer, width=6,  bd =3, textvariable=self.Buffer_ExpT)
        entry_Buffer_ExpT.place(x=120, y=6)

        label_Buffer_NofFrames =  tk.Label(
            labelframe_Buffer, text="Nr. of Frames:")
        label_Buffer_NofFrames.place(x=4,y=40)
        self.Buffer_NofFrames = tk.StringVar(value="10")
        entry_Buffer_NofFrames = tk.Entry(
            labelframe_Buffer, width=5,  bd =3, textvariable=self.Buffer_NofFrames)
        entry_Buffer_NofFrames.place(x=100, y=38)


        var_Buffer_saveall = tk.IntVar()
        r1_Buffer_saveall = tk.Radiobutton(
            labelframe_Buffer, text = "Save single frames", variable=var_Buffer_saveall, value=1)
        r1_Buffer_saveall.place(x=150, y=38)

        label_Buffer_MasterFile =  tk.Label(
            labelframe_Buffer, text="Master Buffer File:")
        label_Buffer_MasterFile.place(x=4,y=70)
        self.Buffer_MasterFile = tk.StringVar(value="Buffer")
        entry_Buffer_MasterFile = tk.Entry(
            labelframe_Buffer, width=11,  bd =3, textvariable=self.Buffer_MasterFile)
        entry_Buffer_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(
            labelframe_Buffer, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)


        """


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      CCD Setup panel
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        # , width=400, height=800)
        self.frame2r = tk.Frame(self.frame0l, background="#4A7A8C")
#        self.frame2r.place(x=430, y=4, anchor="nw", width=360, height=400)
        self.frame2r.place(x=4, y=4, anchor="nw", width=360, height=400)
        labelframe_Setup = tk.LabelFrame(
            self.frame2r, text="Camera Setup", font=self.bigfont)
        labelframe_Setup.pack(fill="both", expand="yes")

#        #camera_is_open = tk.IntVar()
#        button_open_camera= tk.Button(labelframe_Setup, text='Open Camera')
        # command = open_close_camera)
#        button_open_camera.place(x=4, y=104)

#        button_cooler_on= tk.Button(labelframe_Setup, text='Cooler on')
        # command = open_close_camera)
#        button_cooler_on.place(x=4, y=124)

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
        # CAMERA ON/OFF SWITCH
        self.camera_is_on = False
        self.label_camera_ON = tk.Label(labelframe_Setup,
                                        text="The Camera is off",
                                        fg="grey",
                                        font=self.bigfont)
        self.label_camera_ON.place(x=4, y=8)

        # Define Our Images
        self.on_png = tk.PhotoImage(file=os.path.join(
            local_dir, "tk_utilities", "on.png"))
        self.off_png = tk.PhotoImage(file=os.path.join(
            local_dir, "tk_utilities", "off.png"))
        self.button_open_camera = tk.Button(
            labelframe_Setup, image=self.off_png, bd=0, command=self.turn_camera_ON)
        # command = open_close_camera)
        self.button_open_camera.place(x=180, y=0)

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
        # COOLER ON/OFF SWITCH
        self.cooler_is_on = False
        self.label_cooler_ON = tk.Label(labelframe_Setup,
                                        text="The Cooler is off",
                                        fg="grey",
                                        font=self.bigfont)
        self.label_cooler_ON.place(x=4, y=58)

        # Define Our Images
        self.button_open_cooler = tk.Button(
            labelframe_Setup, image=self.off_png, bd=0, command=self.turn_cooler_ON)
        # command = open_close_camera)
        self.button_open_cooler.place(x=180, y=50)
 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
        # COOLER TEMPERATURE SETUP AND VALUE
        label_Tset = tk.Label(
            labelframe_Setup, text="CCD Temperature Sepoint (C)")
        label_Tset.place(x=4, y=98)
        self.Tset = tk.StringVar()
        self.Tset.set("-90")
        entry_Tset = tk.Entry(labelframe_Setup,
                              textvariable=self.Tset, width=5,
                              # font=('Arial',16),
                              bd=3)
        entry_Tset.place(x=200, y=96)
        #
        label_Tdet = tk.Label(
            labelframe_Setup, text="Current CCD Temperature (K)")
        label_Tdet.place(x=4, y=128)
        self.Tdet = tk.IntVar()
        label_show_Tdet = tk.Label(labelframe_Setup,
                                   textvariable=self.Tdet,
                                   font=('Arial', 16),
                                   borderwidth=3,
                                   relief="sunken",
                                   bg="green", fg="white",
                                   text=str(273))
        label_show_Tdet.place(x=200, y=126)
        self.Tdet.set(273)

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
    def turn_camera_ON(self):
        """ to be written """
        # global camera_is_on

        # Determine is on or off
        if self.camera_is_on:
            self.button_open_camera.config(image=self.off_png)
            self.label_camera_ON.config(text="The Camera is Off", fg="grey")
            self.camera_is_on = False
        else:
            self.button_open_camera.config(image=self.on_png)
            self.label_camera_ON.config(text="The Camera is On", fg="green")
            self.camera_is_on = True

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
    def turn_cooler_ON(self):
        """ to be written """
        # global camera_is_on

        # Determine is on or off
        if self.cooler_is_on:
            self.button_open_cooler.config(image=self.off_png)
            self.label_cooler_ON.config(text="The Cooler is Off", fg="grey")
            self.cooler_is_on = False
        else:
            self.button_open_cooler.config(image=self.on_png)
            self.label_cooler_ON.config(text="The Cooler is On", fg="green")
            self.cooler_is_on = True

        """
        #        labelframe_Grating.place(x=4, y=10)

        params = {'Exposure Time':100,'CCD Temperature':2300,'Trigger Mode': 4}
        # Trigger Mode = 4: light
        # Trigger Mode = 4: dark

        Camera= Class_Camera(dict_params=params)


        Camera.expose()
        # Camera.Cooler("1")

        # Camera.dict_params['Exposure Time']=10

        # Camera.set_CCD_temp(2030)    #(273-80) * 10

        # Status = Camera.status()
        # print(Status)
        # url_name = 'http://128.220.146.254:8900/'
        """


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      SHOW SIMBAD IMAGE
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    """
    def Show_Simbad(self):
            # """""" to be written """""""
            self.frame_DisplaySimbad = tk.Frame(
                self.frame0l,background="pink")#, width=400, height=800)
            self.frame_DisplaySimbad.place(
                x=310, y=5, anchor="nw", width=528, height=516)

            # img = AstroImage()
#            img = io_fits.load_file(self.image.filename())

            # ginga needs a logger.
            # If you don't want to log anything you can create a null logger by
            # using null=True in this call instead of log_stderr=True
            # logger = log.get_logger("example1", log_stderr=True, level=40)
            logger = log.get_logger("example1",log_stderr=True, level=40)

#            fv = FitsViewer()
#            top = fv.get_widget()

#            ImageViewCanvas.fitsimage.set_image(img)
            canvas = tk.Canvas(self.frame0l, bg="grey", height=516, width=528)
#            canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            canvas.place(x=310,y=5)

            fi = CanvasView(logger)
            fi.set_widget(canvas)
#            fi.set_image(img)
#            self.fitsimage.set_image(img)

            # fi.set_redraw_lag(0.0)
            fi.enable_autocuts('on')
            fi.set_autocut_params('zscale')
            fi.enable_autozoom('on')
            fi.enable_draw(False)
            # tk seems to not take focus with a click
            fi.set_enter_focus(True)
            fi.set_callback('cursor-changed', self.cursor_cb)

            # 'button-press' is found in Mixins.py
            fi.set_callback('button-press', self. button_click)

            # 'drag-drop' is found in Mixins.py
            # fi.set_callback('drag-drop', self. draw_cb)

           # fi.set_bg(0.2, 0.2, 0.2)
            fi.ui_set_active(True)
            fi.show_pan_mark(True)
#            fi.set_image(img)
            self.fitsimage = fi


            bd = fi.get_bindings()
            bd.enable_all(True)

            # canvas that we will draw on
            DrawingCanvas = fi.getDrawClass('drawingcanvas')
            canvas = DrawingCanvas()
            canvas.enable_draw(True)
            # canvas.enable_edit(True)
            canvas.set_drawtype('rectangle', color='blue')
            canvas.set_surface(fi)
            self.canvas = canvas
            # add canvas to view
            fi.add(canvas)
            canvas.ui_set_active(True)

            fi.configure(516,528)
          #  fi.set_window_size(514,522)

            # self.fitsimage.set_image(img)
#            self.root.title(filepath)
            self.load_file()



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#             self.readout_Simbad = tk.Label(self.frame0l, text='tbd')
# #            self.readout_Simbad.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
#             self.readout_Simbad.place(x=0,y=530)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


            self.drawtypes = fi.get_drawtypes()
            # wdrawtype = ttk.Combobox(self, values=self.drawtypes,
            # command=self.set_drawparams)
            # index = self.drawtypes.index('ruler')
            # wdrawtype.current(index)
            wdrawtype = tk.Entry(self.hbox, width=12)
            wdrawtype.insert(0, 'rectangle')
            wdrawtype.bind("<Return>", self.set_drawparams)
            self.wdrawtype = wdrawtype

            # wdrawcolor = ttk.Combobox(self, values=self.drawcolors,
            #                           command=self.set_drawparams)
            # index = self.drawcolors.index('blue')
            # wdrawcolor.current(index)
            wdrawcolor = tk.Entry(self.hbox, width=12)
            wdrawcolor.insert(0, 'blue')
            wdrawcolor.bind("<Return>", self.set_drawparams)
            self.wdrawcolor = wdrawcolor

            self.vfill = tk.IntVar()
            wfill = tk.Checkbutton(self.hbox, text="Fill", variable=self.vfill)
            self.wfill = wfill

            walpha = tk.Entry(self.hbox, width=12)
            walpha.insert(0, '1.0')
            walpha.bind("<Return>", self.set_drawparams)
            self.walpha = walpha

            wclear = tk.Button(self.hbox, text="Clear Canvas",
                                    command=self.clear_canvas)
#            wopen = tk.Button(self.hbox, text="Open File",
#                                   command=self.open_file)
            wquit = tk.Button(self.hbox, text="Quit",
                                   command=lambda: self.quit())
            for w in (wquit, wclear, walpha, tk.Label(self.hbox, text='Alpha:'),
                      wfill, wdrawcolor, wdrawtype):#, wopen):
                w.pack(side=tk.RIGHT)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         top = fv.get_widget()
#
#         if len(args) > 0:
#            fv.load_file(args[0])
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def cursor_cb(self, viewer, button, data_x, data_y):
        """"""This gets called when the data position relative to the cursor
        changes.
        """""""
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))

        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
        except Exception as e:
            self.logger.warning("Bad coordinate conversion: %s" % (
                str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'

        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s" % (
            ra_txt, dec_txt, fits_x, fits_y, value)
#        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s Button %s" % (
#            ra_txt, dec_txt, fits_x, fits_y, value, button)
        self.readout_Simbad.config(text=text)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         labelframe_SolveAstrometry =  tk.LabelFrame(self.frame0l, text="Solve Astrometry", font=("Arial", 24))
#         labelframe_SolveAstrometry.pack(fill="both", expand="yes")
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    def load_file(self):
        """"""" to be written """""""
        image = load_data('./newtable.fits', logger=self.logger)
#        image = load_data(filepath, logger=self.logger)
        self.fitsimage.set_image(image)


    def get_widget(self):
        """""" to be written """"""
        return self.root

    # this is a function called by main to pass parameters
    def receive_radec(self,radec,radec_list,xy_list):
        """""" to be written """"""
        self.string_RA_center.set(radec[0])
        self.string_DEC_center.set(radec[1])
        self.string_RA_list = radec_list[0]
        self.string_DEC_list = radec_list[1]
        self.xy = xy_list

    def set_drawparams(self, evt):
        """""" to be written """"""
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  # 'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)


    def clear_canvas(self):
        """""" to be written """"""
        obj_tags = list(self.canvas.tags.keys())
        print(obj_tags)
        for tag in obj_tags:
            if self.SlitTabView is not None:
                if tag in self.SlitTabView.slit_obj_tags:
                    obj_ind = self.SlitTabView.slit_obj_tags.index(tag)
                    self.SlitTabView.stab.delete_row(obj_ind)
                    del self.SlitTabView.slit_obj_tags[obj_ind]
                self.SlitTabView.slitDF = self.SlitTabView.slitDF[0:0]


        self.canvas.delete_all_objects(redraw=True)


#
    def return_from_astrometry(self):
        """""" to be written """"""
        return "voila"

    def button_click(self, viewer, button, data_x, data_y):
        """""" to be written """"""
        print('pass', data_x, data_y)
        value = viewer.get_data(int(data_x + viewer.data_off),
                                int(data_y + viewer.data_off))
        print(value)
        # create crosshair
        tag = '_$nonpan_mark'
        radius = 10
        tf = 'True'
        color='red'
        canvas = viewer.get_private_canvas()
        try:
            mark = canvas.get_object_by_tag(tag)
            if not tf:
                canvas.delete_object_by_tag(tag)
            else:
                mark.color = color

        except KeyError:
            if tf:
                Point = canvas.get_draw_class('point')
                canvas.add(Point(data_x-264, data_y-258, radius, style='plus', color=color,
                                 coord='cartesian'),
                           redraw=True)#False)

        canvas.update_canvas(whence=3)

#        value = viewer.pick_hover(self, event, data_x, data_y, viewerpass)
        # If button is clicked, run this method and open window 2

    def    (self):
        """""" to be written """"""
        coord = SkyCoord(self.string_RA_center.get(
        )+'  '+self.string_DEC_center.get(),unit=(u.hourangle, u.deg), frame='fk5')
#        coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5')
        query_results = Simbad.query_region(coord)
        print(query_results)

    # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    # Download an image centered on the coordinates passed by the main window
    #
    # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
        object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'],
                                 unit=(u.hourangle, u.deg), frame='icrs')
        c = SkyCoord(self.string_RA_center.get(),
                     self.string_DEC_center.get(), unit=(u.hourangle, u.deg))
        query_params = {
             'hips': self.Survey_selected.get(), #'DSS', #
             # 'object': object_main_id,
             # Download an image centef on the first object in the results
             # 'ra': object_coords[0].ra.value,
             # 'dec': object_coords[0].dec.value,
             'ra': c.ra.value,
             'dec': c.dec.value,
             'fov': (3.5 * u.arcmin).to(u.deg).value,
             'width': 528,
             'height': 516
             }

        url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'
        hdul = fits.open(url)
        # Downloading http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=DSS&object=%5BT64%5D++7&ra=243.58457533549102&dec=-19.11336493196987&fov=0.03333333333333333&width=500&height=500
        # |#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====| 504k/504k (100.00%)         0s
        hdul.info()
#        hdul.info()
        # Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
        # No.    Name      Ver    Type      Cards   Dimensions   Format
        #  0  PRIMARY       1 PrimaryHDU      22   (500, 500)   int16
        print(hdul[0].header)
        # SIMPLE  =                    T / conforms to FITS standard
        # BITPIX  =                   16 / array data type
        # NAXIS   =                    2 / number of array dimensions
        # NAXIS1  =                  500
        # NAXIS2  =                  500
        # WCSAXES =                    2 / Number of coordinate axes
        # CRPIX1  =                250.0 / Pixel coordinate of reference point
        # CRPIX2  =                250.0 / Pixel coordinate of reference point
        # CDELT1  = -6.6666668547014E-05 / [deg] Coordinate increment at reference point
        # CDELT2  =  6.6666668547014E-05 / [deg] Coordinate increment at reference point
        # CUNIT1  = 'deg'                / Units of coordinate increment and value
        # CUNIT2  = 'deg'                / Units of coordinate increment and value
        # CTYPE1  = 'RA---TAN'           / Right ascension, gnomonic projection
        # CTYPE2  = 'DEC--TAN'           / Declination, gnomonic projection
        # CRVAL1  =           243.584534 / [deg] Coordinate value at reference point
        # CRVAL2  =         -19.11335065 / [deg] Coordinate value at reference point
        # LONPOLE =                180.0 / [deg] Native longitude of celestial pole
        # LATPOLE =         -19.11335065 / [deg] Native latitude of celestial pole
        # RADESYS = 'ICRS'               / Equatorial coordinate system
        # HISTORY Generated by CDS hips2fits service - See http://alasky.u-strasbg.fr/hips
        # HISTORY -image-services/hips2fits for details
        # HISTORY From HiPS CDS/P/DSS2/NIR (DSS2 NIR (XI+IS))
        self.image = hdul
        hdul.writeto('./newtable.fits',overwrite=True)
        hdul.close()


        gc = aplpy.FITSFigure(hdul)
        gc.show_grayscale()
    # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    # INFO: Auto-setting vmin to  2.560e+03 [aplpy.core]
    # INFO: Auto-setting vmax to  1.513e+04 [aplpy.core]
    # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        gc.show_markers(object_coords.ra, object_coords.dec, edgecolor='red',
                     marker='s', s=50**2)
        gc.save('plot.png')


    def Query_Gaia(self):
        """""" to be written """"""
        # Gaia coords are 2016.0

        coord = SkyCoord(ra=self.string_RA_center.get(
        ), dec=self.string_DEC_center.get(), unit=(u.hourangle, u.deg), frame='icrs')
        width = u.Quantity(0.1, u.deg)
        height = u.Quantity(0.1, u.deg)
        Gaia.ROW_LIMIT=200
        r = Gaia.query_object_async(
            coordinate=coord, width=width, height=height)
        r.pprint()
        self.ra_Gaia = r['ra']
        self.dec_Gaia = r['dec']
        mag_Gaia = r['phot_g_mean_mag']
        print(self.ra_Gaia,self.dec_Gaia,mag_Gaia)
        print(len(self.ra_Gaia))
        self.Gaia_RADECtoXY(self.ra_Gaia,self.dec_Gaia)

    def Gaia_RADECtoXY(self, ra_Gaia, dec_Gaia):
        """""" to be written """"""
        viewer=self.fitsimage
        image = viewer.get_image()
        x_Gaia = []
        y_Gaia = []
        i=0
        for i in range(len(ra_Gaia)):
            x, y = image.radectopix(
                ra_Gaia[i], dec_Gaia[i], format='str', coords='fits')
            x_Gaia.append(x)
            y_Gaia.append(y)
        print("GAIA: Converted RADEC to XY for display")
        self.plot_gaia(x_Gaia, y_Gaia)


    def plot_gaia(self,x_Gaia,y_Gaia):
        """""" to be written """"""

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        viewer=self.fitsimage
#         if image is None:
#                 # No image loaded
#             return
#         x_Gaia, y_Gaia = image.radectopix(RA, DEC, format='str', coords='fits')
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # create crosshair
        tag = '_$pan_mark'
        radius = 10
        color='red'
        canvas = viewer.get_private_canvas()
        print(x_Gaia, y_Gaia)
        mark = canvas.get_object_by_tag(tag)
        mark.color = color
        Point = canvas.get_draw_class('point')
        i=0
        for i in range(len(x_Gaia)):
            canvas.add(Point(x_Gaia[i]-264, y_Gaia[i]-258, radius, style='plus', color=color,
                             coord='cartesian'),
                       redraw=True)#False)

        canvas.update_canvas(whence=3)
        print('plotted all', len(x_Gaia), 'sources')
        print(self.string_RA_list,self.string_DEC_list)
        self.Cross_Match()

    def Cross_Match(self):
        """""" to be written """"""

        print(self.ra_Gaia,self.dec_Gaia,self.string_RA_list,self.string_DEC_list)
        # ----------
        # from https://mail.python.org/pipermail/astropy/2012-May/001761.html
        h = htm.HTM()
        maxrad=5.0/3600.0
        m1,m2,radius = h.match( np.array(self.ra_Gaia), np.array(self.dec_Gaia), np.array(
            self.string_RA_list),np.array(self.string_DEC_list), maxrad)
        # ----------
        print(m1,m2)
        print((np.array(self.ra_Gaia)[m1]-np.array(self.string_RA_list)[m2])*3600)
        print((np.array(self.dec_Gaia)[m1]-np.array(self.string_DEC_list)[m2])*3600)
        g = [np.array(self.ra_Gaia)[m1],np.array(self.dec_Gaia)[m1]]
        # s = [np.array(self.string_RA_list)[m2],np.array(self.string_DEC_list)[m2]]
        # Gaia_pairs = np.reshape(g,(2,44))
        src = []
        for i in range(len(g[0])):
            src.append([g[0][i],g[1][i]])

        # ----------
        # create wcs
        # FROM https://docs.astropy.org/en/stable/api/astropy.wcs.utils.fit_wcs_from_points.html
        # xy   #   x & y pixel coordinates  (numpy.ndarray, numpy.ndarray) tuple
        # coords = g
        # These come from Gaia, epoch 2015.5
        world_coords  = SkyCoord(src, frame=FK4, unit=(
            u.deg, u.deg), obstime="J2015.5")
        xy  = ( (self.xy[0])[m2], (self.xy[1])[m2] )
        wcs = fit_wcs_from_points(
            xy, world_coords, proj_point='center',projection='TAN',sip_degree=3)
        # ----------
        # update fits file header
        # from https://docs.astropy.org/en/stable/wcs/example_create_imaging.html

        # Three pixel coordinates of interest.
        # The pixel coordinates are pairs of [X, Y].
        # The "origin" argument indicates whether the input coordinates
        # are 0-based (as in Numpy arrays) or
        # 1-based (as in the FITS convention, for example coordinates
        # coming from DS9).
        pixcrd = np.array([[0, 0], [24, 38], [45, 98]], dtype=np.float64)

        # Convert pixel coordinates to world coordinates.
        # The second argument is "origin" -- in this case we're declaring we
        # have 0-based (Numpy-like) coordinates.
        world = wcs.wcs_pix2world(pixcrd, 0)
        print(world)

        # Convert the same coordinates back to pixel coordinates.
        pixcrd2 = wcs.wcs_world2pix(world, 0)
        print(pixcrd2)

        # Now, write out the WCS object as a FITS header
        header = wcs.to_header()

        # header is an astropy.io.fits.Header object.  We can use it to create a new
        # PrimaryHDU and write it to a file.
        hdu = fits.PrimaryHDU(header=header)

        # Save to FITS file
        hdu.writeto('test.fits')
    """

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("900x600")
        parent.title("SAMOS CCD Controller")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
# ---------------------------------------- REDO Pix <-> DMD Mapping  ------------------------------------------------------------------------
#
#############################################################################################################################################

Coordinate transformation from DMD to Pixels (and vice versa) may need to be recalculated
User will have to take an exposure of a grid pattern, then go through steps to create a
new FITS file with the "WCS" transformation, which will be used in the CONVERT class
"""
# will rename/relocate the CTH class once this works


class CCD2DMD_RecalPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """
        super().__init__(container)

    # =============================================================================
    #
    #  #    FITS Files Label Frame
    #
    # =============================================================================
        self.fits_hdu = None
        self.sources_table = None
        self.dmd_table = None
        self.DMD_PIX_df = None
        self.afftest = None
        self.coord_text = None

        logger = log.get_logger("example2", options=None)
        self.logger = logger
        vbox_l = tk.Frame(self, relief=tk.RAISED)
        vbox_l.pack(side=tk.LEFT)
        vbox_l.place(x=5, y=0, anchor="nw", width=220, height=550)
        self.vb_l = vbox_l

        # , width=400, height=800)
        self.frame0l = tk.Frame(
            self.vb_l, background="#9D76A4", relief=tk.RAISED)
        self.frame0l.place(x=4, y=0, anchor="nw", width=220, height=250)

        self.wdir = "./"
        filelist = os.listdir(self.wdir)

        self.file_browse_button = tk.Button(self.frame0l, text="Open Grid FITS File",
                                            bg="#9D76A4", command=self.browse_grid_fits_files)
        # browse_files.pack(side=tk.TOP)
        self.file_browse_button.pack()

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=250, y=0, anchor="nw")  # , width=500, height=800)
        # self.vb = vbox

#        canvas = tk.Canvas(vbox, bg="grey", height=514, width=522)
        canvas = tk.Canvas(vbox, bg="grey", height=516, width=528)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # => ImageViewTk -- a backend for Ginga using a Tk canvas widget
        fi = CanvasView(logger)

        # => Call this method with the Tkinter canvas that will be used for the display.
        fi.set_widget(canvas)
        # fi.set_redraw_lag(0.0)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        # fi.enable_draw(False)
        # tk seems to not take focus with a click
        fi.set_enter_focus(True)
        # fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        self.dmd_pattern_text = " "
        self.dmd_pattern_label = tk.Label(self, text=self.dmd_pattern_text)
        self.dmd_pattern_label.pack()
        self.dmd_pattern_label.place(x=520, y=545, anchor="s")

        vbox_c = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox_c.pack(side=tk.BOTTOM)
        vbox_c.place(x=60, y=545, anchor="nw")  # , width=500, height=800)
        import tksheet

        tk_grid_sources_table = tksheet.Sheet(vbox_c, width=900, height=300,
                                              column_width=60)  # tk_sources_table.headers()
        tk_grid_sources_table.grid()

        self.tk_grid_sources_table = tk_grid_sources_table
 # =============================================================================
 #
 #  #    Buttions for Source Extraction
 #      -Enter in number of sources to find in image.
 #      -Enter in approx FWHM for sources.
 #      -Initialize Coordinate transformation.
 #      -Enter SIP value and run coordinate WCS fit.
 #
 # =============================================================================

        self.source_find_button = tk.Button(self.frame0l, text="Run IRAFStarFinder",
                                            bg="#9D76A4", state="disabled", command=self.irafstarfind)
        # self.source_find_button.place(x=4)
        # self.frame1l.create_window(102,120,window=self.source_find_button)
        self.source_find_button.pack(anchor="n", padx=4, pady=15)
        # self.source_find_button.place(x=4, y=20)

        self.run_coord_transf_button = tk.Button(self.frame0l, text="Initialize Coord Transform", bg="#9D76A4", state="disabled",
                                                 command=self.run_coord_transf)
        self.run_coord_transf_button.pack(padx=15, pady=5)
        # self.run_coord_transf_button.place(x=4, y=40)

    def cursor_cb(self, event):
        """ to be written """
        if self.fits_hdu is None:
            return

        x, y = event.xdata, event.ydata

        self.coord_text = '({},{})'.format(x, y)
        self.coord_label["text"] = (self.coord_text)

    def browse_grid_fits_files(self):
        """ to be written """

        filename = tk.filedialog.askopenfilename(initialdir=self.PAR.QL_images, filetypes=[("FITS files", "*fits")],
                                                 title="Select a FITS File", parent=self.frame0l)

        if filename == '':
            print('no grid file selected')
            return

        self.AstroImage = load_data(filename, logger=self.logger)

        self.fitsimage.set_image(self.AstroImage)

        # self.source_find_button["state"] = "active"
        # self.source_fwhm_entry["state"] = "normal"
        # self.source_find_entry["state"] = "normal"

        self.fits_header = self.AstroImage.as_hdu().header
        self.grid_pattern_name = self.fits_header["DMDMAP"]
        dmd_pattern_text = "DMD Pattern: {}".format(self.grid_pattern_name)
        self.dmd_pattern_label["text"] = dmd_pattern_text

        self.grid_pattern_fullPath = os.path.join(
            "SAMOS_DMD_dev", "DMD_csv", "slits", "{}".format(self.grid_pattern_name))
        dmd_table = pd.read_csv(self.grid_pattern_fullPath)
        # .sort_values(by="y", ascending=False).reset_index(drop=True)
        self.dmd_table = dmd_table

        # self.rotate_dmd_table_180()
        self.source_find_button["state"] = "active"
        self.run_coord_transf_button["state"] = "active"

    def rotate_dmd_table_180(self):

        numcols = int(np.sqrt(self.dmd_table.shape[0]))
        rot_dmd_tab = self.dmd_table.sort_values(
            by="y", ascending=False).reset_index(drop=True)
        j = -1

        stacked_x_rows = []

        inds = rot_dmd_tab.index.values[::11]
        for ind in range(len(inds)):

            i = inds[ind]

            # print(sorted_row)
            if i == inds[-1]:
                sorted_row = rot_dmd_tab.iloc[i:].copy(
                ).sort_values(by="x", ascending=False)
                stacked_x_rows.extend(sorted_row.x.values)
                break

            next_ind = inds[ind+1]
            sorted_row = rot_dmd_tab.iloc[i:i +
                                          numcols].copy().sort_values(by="x", ascending=False)

            stacked_x_rows.extend(sorted_row.x.values)

        rot_dmd_tab["x"] = np.array(stacked_x_rows)
        print(rot_dmd_tab)
        # self.dmd_table = rot_dmd_tab.copy()

    def irafstarfind(self):  # expected_sources=53**2,fwhm=5):
        """ to be written """

        fwhm = 5  # float(self.source_fwhm_entry.get())

        ccd = self.AstroImage.as_nddata().data
        # bright columns on left and right side of CCD that we don't want to be included in the starfinder.
        # set them to be the average of surrounding columns
        colcorr_ccd = ccd.copy()
        for col in range(1010, 1025):
            colcorr_ccd[:, col] = np.average(
                (np.average(ccd[:, 1000:1009], axis=1), np.average(ccd[:, 1020:], axis=1)), axis=0)

        for col in range(20, 40):
            colcorr_ccd[:, col] = np.average(
                (np.average(ccd[:, 0:20], axis=1), np.average(ccd[:, 40:50], axis=1)), axis=0)

        ccd = colcorr_ccd.copy()

        # print(ccd.header)
        mean_ccd, median_ccd, std_ccd = sigma_clipped_stats(ccd, sigma=4.0)

        expected_sources = self.dmd_table.shape[0]
        # print(std_ccd)
        xpixels, ypixels = [], []
        for i in self.dmd_table.index.values:

            dmd_x, dmd_y = self.dmd_table.loc[i, ["x", "y"]].values
            pix_x, pix_y = convert.DMD2CCD(dmd_x, dmd_y)
            xpixels.append(pix_x)
            ypixels.append(pix_y)

#        xypixels = np.vstack((np.array(xpixels),np.array(ypixels))).T
        xypixels = np.vstack((np.array(ypixels), np.array(xpixels))).T

        # sources_table, unsorted_sources = CTH.iraf_gridsource_find(ccd,expected_sources=expected_sources,fwhm=fwhm,
        #                                                           threshold=3*std_ccd)# xycoords=xypixels, exclude_border=True)

        sources_table, unsorted_sources = CTH.iraf_gridsource_find(ccd, expected_sources=expected_sources, fwhm=fwhm,
                                                                   threshold=3*std_ccd)  # exclude_border=True)

        iraf_positions = np.transpose(
            (sources_table['xcentroid'], sources_table['ycentroid']))

        self.sources_table = sources_table.round(3)

        DMD_PIX_df = pd.concat((self.dmd_table, self.sources_table), axis=1)

        dup_ind_col_drop = DMD_PIX_df.columns.values[0]
        DMD_PIX_df = DMD_PIX_df.drop(columns=dup_ind_col_drop)
        print(DMD_PIX_df)
        print(DMD_PIX_df.columns)

        self.DMD_PIX_df = DMD_PIX_df
        self.tk_grid_sources_table.headers(newheaders=DMD_PIX_df.columns.values,
                                           show_headers_if_not_sheet=True,
                                           redraw=True)

        for i in DMD_PIX_df.index.values:

            row = DMD_PIX_df.iloc[i]
            self.tk_grid_sources_table.insert_row(values=row, redraw=True)

            x_c, y_c = row[["xcentroid", "ycentroid"]].values
            reg = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)),
                                       width=40, height=40,
                                       angle=0*u.deg)

            self.fitsimage.canvas.add(r2g(reg))
            # and we convert it to ginga.

    def run_coord_transf(self):

        self.afftest = CTH.AFFtest(self.DMD_PIX_df)
        self.afftest.fit_wcs_with_sip(3)

        new_hdr = self.fits_header.copy()
        imwcs = self.afftest.ccd_to_dmd_wcs.to_header(relax=True)

        imwcs.rename_keyword("PC1_1", "CD1_1")
        imwcs.rename_keyword("PC1_2", "CD1_2")
        imwcs.rename_keyword("PC2_1", "CD2_1")
        imwcs.rename_keyword("PC2_2", "CD2_2")

        for key in list(imwcs.keys()):
            new_hdr.set(key, imwcs[key])

        new_hdu = fits.PrimaryHDU(data=self.AstroImage.as_nddata().data,
                                  header=new_hdr)

        img_Mapping_fpath = os.path.join("SAMOS_DMD_dev", "CONVERT",
                        "DMD_Mapping_WCS.fits")
        prev_Mapping_fname = os.path.join("SAMOS_DMD_dev", "CONVERT",
                                          "DMD_Mapping_WCS_prev.fits")
        # change name of previous FITS file with the coordinate transformation
        # to save it just in case recalibration went wrong.
        os.rename(img_Mapping_fpath, prev_Mapping_fname)
        # will change this file to CONVERT/DMD_Mapping_WCS.fits once confident it works
        new_hdu.writeto(img_Mapping_fpath, overwrite=True)

        print("New transform FITS file created")

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("910x650")
        parent.title("SAMOS Recalibrate CCD2DMD Transformation")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
# ---------------------------------------- SOAR TCS PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class SOAR_Page(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """
        super().__init__(container)

        # label = tk.Label(self, text="SOAR TCS 1", font=('Times', '20'))
        # label.pack(pady=0,padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        # , width=300, height=300)
        self.frame0l = tk.Frame(self, background="light gray")
        self.frame0l.place(x=0, y=0, anchor="nw", width=1100, height=500)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      TCS Controls
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        button_WAY = tk.Button(
            self.frame0l, text="Who are you?", command=self.WAY)
        button_WAY.place(x=4, y=40)

        from functools import partial
        tk.Label(self.frame0l,
                 text="Offset:",
                 justify=tk.LEFT,
                 padx=2).place(x=4, y=70)
        self.OFFSET_MOVE_msg = tk.StringVar()
        self.OFFSET_MOVE_msg.set("E 0.00 N 0.00")
        entry_OFFSET_MOVE = tk.Entry(
            self.frame0l, textvariable=self.OFFSET_MOVE_msg, width=12,  bd=3)
        entry_OFFSET_MOVE.place(x=60, y=68)
        button_OFFSET_MOVE = tk.Button(
            self.frame0l, text="MOVE", command=partial(self.Offset_option_TCS, "MOVE"))
        button_OFFSET_MOVE.place(x=200, y=70)
        button_OFFSET_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.Offset_option_TCS, "STATUS"))
        button_OFFSET_STATUS.place(x=400, y=70)

        tk.Label(self.frame0l,
                 text="Focus:",
                 justify=tk.LEFT,
                 padx=2).place(x=4, y=100)
        self.Focus_option_msg = tk.StringVar()
        self.Focus_option_msg.set("0")
        entry_Focus_option = tk.Entry(
            self.frame0l, textvariable=self.Focus_option_msg, width=5,  bd=3)
        entry_Focus_option.place(x=60, y=98)
        self.Focus_variable = tk.StringVar()
        self.Focus_variable.set("MOVEREL")
        Focus_options = ["MOVEREL", "MOVEABS"]
        button_Focus_MOVEREL = tk.Radiobutton(self.frame0l,
                   text=Focus_options[0],
                   padx=2,
                   variable=self.Focus_variable,
                   command=partial(self.Focus_option_TCS, Focus_options[0]),
                   value="MOVEREL").place(x=200, y=100)
        button_Focus_MOVEABS = tk.Radiobutton(self.frame0l,
                   text=Focus_options[1],
                   padx=2,
                   variable=self.Focus_variable,
                   command=partial(self.Focus_option_TCS, Focus_options[1]),
                   value="MOVEABS").place(x=300, y=100)
        button_Focus_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.Focus_option_TCS, "STATUS"))
        button_Focus_STATUS.place(x=400, y=100)

        self.v = tk.StringVar()
        self.v.set("OUT")  # initializing the choice, i.e. Python
        status = ["IN", "OUT"]
        tk.Label(self.frame0l,
                 text="CLM:",
                 justify=tk.LEFT,
                 padx=20).place(x=4, y=130)
        button_CLM_IN = tk.Radiobutton(self.frame0l,
                   text=status[0],
                   padx=20,
                   variable=self.v,
                   command=partial(self.CLM_option_TCS, status[0]),
                   value="IN").place(x=200, y=130)
        button_CLM_OUT = tk.Radiobutton(self.frame0l,
                   text=status[1],
                   padx=20,
                   variable=self.v,
                   command=partial(self.CLM_option_TCS, status[1]),
                   value="OUT").place(x=300, y=130)
        button_CLM_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.CLM_option_TCS, "STATUS"))
        button_CLM_STATUS.place(x=400, y=130)

        self.Guider_status = tk.StringVar()
        # initializing the choice, i.e. Python
        self.Guider_status.set("DISABLE")
        status = ["ENABLE", "DISABLE"]
        tk.Label(self.frame0l,
                 text="Guider:",
                 justify=tk.LEFT,
                 padx=20).place(x=4, y=160)
        button_Guider_Enable = tk.Radiobutton(self.frame0l,
                   text=status[0],
                   padx=5,
                   variable=self.Guider_status,
                   command=partial(self.Guider_option_TCS, status[0]),
                   value="ENABLE").place(x=200, y=160)
        button_Guider_Disable = tk.Radiobutton(self.frame0l,
                   text=status[1],
                   padx=5,
                   variable=self.Guider_status,
                   command=partial(self.Guider_option_TCS, status[1]),
                   value="DISABLE").place(x=300, y=160)
        button_Guider_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.Guider_option_TCS, "STATUS"))
        button_Guider_STATUS.place(x=400, y=160)

        self.Whitespot_status = tk.StringVar()
        # initializing the choice, i.e. Python
        self.Whitespot_status.set("OFF")
        status = ["ON", "OFF"]
        tk.Label(self.frame0l,
                 text="Whitespot % :",
                 justify=tk.LEFT,
                 padx=10).place(x=4, y=190)
        self.Whitespot_percentage = tk.StringVar()
        self.Whitespot_percentage.set("50")
        entry_Whitespot_percentage = tk.Entry(
            self.frame0l, textvariable=self.Whitespot_percentage, width=4,  bd=3)
        entry_Whitespot_percentage.place(x=130, y=186)
        button_Whitespot_Enable = tk.Radiobutton(self.frame0l,
                   text=status[0],
                   padx=5,
                   variable=self.Whitespot_status,
                   command=partial(self.Whitespot_option_TCS, status[0]),
                   value="ON").place(x=200, y=190)
        button_Whitespot_Disable = tk.Radiobutton(self.frame0l,
                   text=status[1],
                   padx=5,
                   variable=self.Whitespot_status,
                   command=partial(self.Whitespot_option_TCS, status[1]),
                   value="OFF").place(x=300, y=190)
        button_Whitespot_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.Whitespot_option_TCS, "STATUS"))
        button_Whitespot_STATUS.place(x=400, y=190)

        self.Lamp_LN_status = tk.StringVar()
        self.Lamp_LN_status.set("OFF")  # initializing the choice, i.e. Python
        status = ["ON", "OFF"]
        tk.Label(self.frame0l,
                 text="Lamp L# %:",
                 justify=tk.LEFT,
                 padx=2).place(x=4, y=220)
        self.Lamp_number = tk.StringVar()
        self.Lamp_percentage = tk.StringVar()
        self.Lamp_number.set("L2")
        self.Lamp_percentage.set("50")
        entry_Lamp_number = tk.Entry(
                self.frame0l, textvariable=self.Lamp_number,  width=4,  bd=3)
        entry_Lamp_number.place(x=90, y=216)
        entry_Lamp_percentage = tk.Entry(
                self.frame0l, textvariable=self.Lamp_percentage, width=4,  bd=3)
        entry_Lamp_percentage.place(x=130, y=216)
        button_Lamp_Enable = tk.Radiobutton(self.frame0l,
                text=status[0],
                padx=5,
                variable=self.Lamp_LN_status,
                command=partial(self.Lamp_LN_option_TCS, status[0]),
                           value="ON").place(x=200, y=220)
        button_Lamp_Disable = tk.Radiobutton(self.frame0l,
                           text=status[1],
                           padx=5,
                           variable=self.Lamp_LN_status,
                           command=partial(self.Lamp_LN_option_TCS, status[1]),
                           value="OFF").place(x=300, y=220)
        button_Lamp_STATUS = tk.Button(
                    self.frame0l, text="STATUS", command=partial(self.Lamp_LN_option_TCS, "STATUS"))
        button_Lamp_STATUS.place(x=400, y=220)

        tk.Label(self.frame0l,
                 text="ADC %:",
                 justify=tk.LEFT,
                 padx=2).place(x=4, y=250)
#        button_ADC_MOVE = tk.Button(
#            self.frame0l, text="ADC MOVE %", command=partial(self.ADC_option_TCS, "MOVE"))
#        button_ADC_MOVE.place(x=4, y=250)
        self.ADC_MOVE_msg = tk.StringVar()
        self.ADC_MOVE_msg.set("0.0")
        entry_ADC_MOVE = tk.Entry(
            self.frame0l, textvariable=self.ADC_MOVE_msg, width=4,  bd=3)
        entry_ADC_MOVE.place(x=130, y=248)
        self.v_ADC = tk.StringVar()
        self.v_ADC.set("PARK")
        ADC_status = ["IN", "PARK", "TRACK"]
        button_ADC_IN = tk.Radiobutton(self.frame0l,
                   text=ADC_status[0],
                   padx=2,
                   variable=self.v_ADC,
                   # self.ADC_option_TCS,
                   command=partial(self.ADC_option_TCS, ADC_status[0]),
                   value="IN").place(x=200, y=250)
        button_ADC_PARK = tk.Radiobutton(self.frame0l,
                   text=ADC_status[1],
                   padx=2,
                   variable=self.v_ADC,
                   # self.ADC_option_TCS,
                   command=partial(self.ADC_option_TCS, ADC_status[1]),
                   value="PARK").place(x=250, y=250)
        button_ADC_TRACK = tk.Radiobutton(self.frame0l,
                   text=ADC_status[2],
                   padx=2,
                   variable=self.v_ADC,
                   # self.ADC_option_TCS,
                   command=partial(self.ADC_option_TCS, ADC_status[2]),
                   value="TRACK").place(x=320, y=250)
        button_CLM_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.ADC_option_TCS, "STATUS"))
        button_CLM_STATUS.place(x=400, y=248)

        tk.Label(self.frame0l,
                 text="IPA:",
                 justify=tk.LEFT,
                 padx=8).place(x=4, y=280)
        button_IPA_MOVE = tk.Button(
            self.frame0l, text="MOVE", command=partial(self.IPA_option_TCS, "MOVE"))
        button_IPA_MOVE.place(x=60, y=276)
        self.IPA_MOVE_msg = tk.StringVar()
        self.IPA_MOVE_msg.set("0.0")
        entry_IPA_MOVE = tk.Entry(
            self.frame0l, textvariable=self.IPA_MOVE_msg, width=20,  bd=3)
        entry_IPA_MOVE.place(x=200, y=278)
        button_IPA_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.IPA_option_TCS, "STATUS"))
        button_IPA_STATUS.place(x=400, y=280)

        tk.Label(self.frame0l,
                 text="Instrument:",
                 justify=tk.LEFT,
                 padx=8).place(x=4, y=310)
        button_Instrument_MOVE = tk.Button(
            self.frame0l, text="MOVE", command=partial(self.Instrument_option_TCS, "MOVE"))
        button_Instrument_MOVE.place(x=100, y=306)
        self.Instrument_MOVE_msg = tk.StringVar()
        self.Instrument_MOVE_msg.set("SAM")
        entry_Instrument_MOVE = tk.Entry(
            self.frame0l, textvariable=self.Instrument_MOVE_msg, width=20,  bd=3)
        entry_Instrument_MOVE.place(x=200, y=308)
        button_Instrument_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.Instrument_option_TCS, "STATUS"))
        button_Instrument_STATUS.place(x=400, y=310)

        tk.Label(self.frame0l,
                 text="Target:",
                 justify=tk.LEFT,
                 padx=2).place(x=4, y=370)
        tk.Label(self.frame0l,
                 text="RA:",
                 justify=tk.LEFT,
                 padx=2).place(x=70, y=370)
        self.Target_RA_msg = tk.StringVar()
        self.Target_RA_msg.set("07:43:48.40")
        entry_Target_RA = tk.Entry(
            self.frame0l, textvariable=self.Target_RA_msg, width=11,  bd=3)
        entry_Target_RA.place(x=105, y=366)
        tk.Label(self.frame0l,
                 text="DEC:",
                 justify=tk.LEFT,
                 padx=2).place(x=235, y=370)
        self.Target_DEC_msg = tk.StringVar()
        self.Target_DEC_msg.set("-28:57:18.00")
        entry_Target_DEC = tk.Entry(
            self.frame0l, textvariable=self.Target_DEC_msg, width=11,  bd=3)
        entry_Target_DEC.place(x=280, y=366)
        tk.Label(self.frame0l,
                 text="Epoch:",
                 justify=tk.LEFT,
                 padx=2).place(x=70, y=400)
        self.Target_EPOCH_msg = tk.StringVar()
        self.Target_EPOCH_msg.set("2000.0")
        entry_Target_EPOCH = tk.Entry(
            self.frame0l, textvariable=self.Target_EPOCH_msg, width=6,  bd=3)
        entry_Target_EPOCH.place(x=127, y=396)
        self.Target_variable = tk.StringVar()
        self.Target_variable.set("MOVE")
        Target_options = ["MOVE", "MOUNT", "STOP"]
        button_Target_MOVE = tk.Radiobutton(self.frame0l,
                   text=Target_options[0],
                   padx=0,
                   variable=self.Target_variable,
                   command=partial(self.Target_option_TCS, Target_options[0]),
                   value="MOVE").place(x=180, y=430)
        button_Target_MOUNT = tk.Radiobutton(self.frame0l,
                   text=Target_options[1],
                   padx=0,
                   variable=self.Target_variable,
                   command=partial(self.Target_option_TCS, Target_options[1]),
                   value="MOUNT").place(x=250, y=430)
        button_Target_STOP = tk.Radiobutton(self.frame0l,
                   text=Target_options[2],
                   padx=0,
                   variable=self.Target_variable,
                   command=partial(self.Target_option_TCS, Target_options[2]),
                   value="STOP").place(x=330, y=430)
        button_Focus_STATUS = tk.Button(
            self.frame0l, text="STATUS", command=partial(self.Target_option_TCS, "STATUS"))
        button_Focus_STATUS.place(x=400, y=428)

        label_INFO = tk.Button(self.frame0l, text="INFO",
            command=partial(self.Handle_Infox, "INFO"))
        label_INFO.place(x=600, y=4)
        label_INFOx = tk.Button(
            self.frame0l, text="INFOX",
            command=partial(self.Handle_Infox, "INFOX"))
        label_INFOx.place(x=675, y=4)
        label_GINFO = tk.Button(
            self.frame0l, text="GINFO",
            command=partial(self.Handle_Infox, "GINFO"))
        label_GINFO.place(x=750, y=4)
        label_SINFO = tk.Button(
            self.frame0l, text="SINFO",
            command=partial(self.Handle_Infox, "SINFO"))
        label_SINFO.place(x=825, y=4)
        label_ROTPOS = tk.Button(
            self.frame0l, text="ROTPOS",
            command=partial(self.Handle_Infox, "ROTPOS"))
        label_ROTPOS.place(x=900, y=4)
        label_INFOA = tk.Button(
            self.frame0l, text="INFOA",
            command=partial(self.Handle_Infox, "INFOA"))
        label_INFOA.place(x=975, y=4)

        '''
        self.INFOxxx_msg=tk.StringVar()
        self.INFOxxx_msg.set("")
        entry_INFOxxx = tk.Text(self.frame0l,  height=20, width=50,  bd =3)
        scroll = tk.Scrollbar(self.frame0l)
        entry_INFOxxx.configure(yscrollcommand=scroll.set)
        entry_INFOxxx.place(x=600, y=40)
        scroll.config(command=entry_INFOxxx.yview)
        scroll.place(side=tk.RIGHT, fill=tk.Y)
        entry_INFOxxx.insert(tk.END, "lorem ipsum")
        '''
        from tkinter import scrolledtext
        self.text_area = tk.scrolledtext.ScrolledText(self.frame0l, wrap=tk.WORD,
                                                      width=53, height=25,
                                                      font=("Times New Roman", 15))
        self.text_area.grid(column=0, row=2, pady=40, padx=600)
######################################

    def Send_to_TCS(self):
        """ to be written """
        self.Send_to_TCS_msg.set("you should write something here")
        message = self.Send_to_TCS_msg.get()
        msg_back = SOAR.send_to_TCS(message)
        self.text_area.insert(tk.END, 'sent: \n>'+message +
                              '\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def WAY(self):
        """ (Who are you?) This command returns an identification string

        For example
            WAY
            DONE SOAR 4.2m
        """
        message = "WAY"
        # self.WAY_msg.set(message)
        msg_back = SOAR.send_to_TCS(message)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Offset_option_TCS(self, event):
        """
        This command send an offset motion request to the TCS.
        The offset is given in units of arcseconds, and must be preceded by one of the direction characters N, S, E and W.
        """
        if event == "MOVE":
            offset = self.OFFSET_MOVE_msg.get()
        else:
            offset = ""
        msg_back = SOAR.offset(event, offset)
        message = "OFFSET " + event + " " + offset
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)
#        self.Offset_option_msg.set("you selected "+self.Offset_option_selected.get())
        pass

    def Focus_option_TCS(self, event):
        """
        This command requests actions to the focus mechanism associated with the secondary mirror (M2).

        Parameters
        ----------
        event : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        event = event.replace("Focus ", "")
        if event != "STATUS":
            offset = self.Focus_option_msg.get()
        else:
            offset = ""
        message = "FOCUS " + event + " " + offset
        msg_back = SOAR.focus(event, offset)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def CLM_option_TCS(self, event):
        """ This command requests actions to the comparison lamps mirror mechanism. """
        message = "CLM " + event
        msg_back = SOAR.clm(event)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Guider_option_TCS(self, event):
        """ This command enable or disable the guider device. """
        # event = self.Guider_status.get()
        message = "GUIDER " + event
        msg_back = SOAR.guider(event)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Whitespot_option_TCS(self, message):
        """ This command enable or disable the Whitespot device. """
        percentage = self.Whitespot_percentage.get()
        if message != 'ON':
            percentage = ''
        msg_back = SOAR.whitespot(message, percentage)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              "WHITESPOT " + message + ' ' + percentage + '\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Lamp_LN_option_TCS(self, status):
        """
        This command turns on or off the calibration lamps. Where “LN” is the location of the lamp (1 to 12).
        There are two position that have dimmers, position L9 and L12, therefore, a percentage must be added.
        """
        lamp_nr = self.Lamp_number.get()
        percentage = ''
        if ((status == "ON") and ((lamp_nr == 'L9') or (lamp_nr == 'L12'))):
            percentage = self.Lamp_percentage.get()
        location = lamp_nr + ' ' + percentage
        message = "LAMP " + status + ' ' + location
        msg_back = SOAR.lamp_id(status, location)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def ADC_option_TCS(self, message):
        """ This command enable or disable the Whitespot device. """
        percentage = self.ADC_MOVE_msg.get()
        if message != "IN":
            percentage = ''
        msg_back = SOAR.adc(message, percentage)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              "ADC " + message + ' ' + percentage + '\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def IPA_option_TCS(self, event):
        """
        This command set a new instrument position angle to the TCS.
        The IPA is given in units of degrees.
        """
        if event == "MOVE":
            offset = self.IPA_MOVE_msg.get()
        else:
            offset = ""
        msg_back = SOAR.ipa(event, offset)
        message = "IPA " + event + " " + offset
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Instrument_option_TCS(self, event):
        """
        This command selects the instrument in use
        """
        if event == "MOVE":
            offset = self.Instrument_MOVE_msg.get()
        else:
            offset = ""
        msg_back = SOAR.instrument(event, offset)
        message = "INSTRUMENT " + event + " " + offset
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Target_option_TCS(self, event):
        """
        This command send a new position request to the TCS.
        The target is given in units of RA (HH:MM:SS.SS), DEC (DD:MM:SS.SS) and EPOCH (year).
        This command involves the movement of mount, dome, rotator, adc and optics.
        If it is required to know only the state of the mount, use option "MOUNT"
        """
        RA = self.Target_RA_msg.get()
        DEC = self.Target_DEC_msg.get()
        EPOCH = self.Target_EPOCH_msg.get()
        RADEC = "RA="+RA+" DEC="+DEC+" EPOCH="+EPOCH
        if event != "MOVE":
            RADEC = ''
        msg_back = SOAR.target(event, RADEC)
        message = "TARGET " + event + ' ' + RADEC
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message + '\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def Handle_Infox(self, message):
        """
        This command returns various lists of parameters, dependin on the choice:
        """
        msg_back = SOAR.info_whatever(message)
        self.text_area.insert(tk.END, '\nsent: \n>' +
                              message+'\nreceived: \n>'+str(msg_back))
        self.text_area.yview(tk.END)

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("1100x500")
        parent.title("SOAR TCS")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
        filemenu.add_command(label="Exit", command=parent.quit)

#        # ETC menu
#        ETC_menu = tk.Menu(menubar, tearoff=0)
#        menubar.add_cascade(label="ETC", menu=ETC_menu)
#        ETC_menu.add_command(label="Spectropscopy", command=parent.show_frame(parent.ETC))
#        ETC_menu.add_command(label="Imaging", command=U.about)
#        ETC_menu.add_separator()

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
# ---------------------------------------- MAIN PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class MainPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """
        super().__init__(container)

        #self.DMDPage = DMDPage
        self.PAR = SAMOS_Parameters()
        self.ConfP = ConfigPage(parent,container)

        self.container = container
        
        self.initialize_slit_table()

        logger = log.get_logger("example2", options=None)
        self.logger = logger

        label = tk.Label(self, text="Main Page", font=('Times', '20'))
        label.pack(pady=0, padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        if platform == "win32":
            self.bigfont = ("Arial", 12, 'bold')
            self.bigfont_20 = ("Arial", 12, 'bold')
            self.bigfont_15 = ("Arial", 10, 'bold')
        else:
            self.bigfont = ("Arial", 24)
            self.bigfont_20 = ("Arial", 20)
            self.bigfont_15 = ("Arial", 15)

        # keep track of the entry number for header keys that need to be added
        # will be used to write "OtherParameters.txt"
        self.extra_header_params = 0
        # keep string of entries to write to a file after acquisition.
        self.header_entry_string = ''
        main_fits_header.create_main_params_dict()
        self.wcs = None
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        #self.SlitTabView = None
        self.loaded_regfile = None
        today = datetime.now()
        self.fits_dir = os.path.join(
            parent_dir, "SISI_images", "SAMOS_" + today.strftime('%Y%m%d'))



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    OBSERVER/NIGHT INFO Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.wcs_exist = None

        self.frame_ObsInf = tk.Frame(self, background="cyan")
        self.frame_ObsInf.place(x=10, y=0, anchor="nw", width=420, height=150)

        labelframe_ObsInf = tk.LabelFrame(self.frame_ObsInf, text="Observer Information",
                                          font=self.bigfont)
        labelframe_ObsInf.pack(fill="both", expand="yes")

        # name_scroll = tk.Scrollbar(labelframe_ObsInf)
        # name_scroll.pack(side=tk.BOTTOM, fill=tk.Y)
        self.names_var = tk.StringVar()
        self.names_var.set(self.PAR.PotN['Observer'])
        name_label = tk.Label(labelframe_ObsInf, text="Observer Name(s): ")
        name_label.place(x=30, y=4)
        name_entry = tk.Entry(labelframe_ObsInf, width=25, bd=3,
                              textvariable=self.names_var)
        # xscrollcommand=name_scroll)
        name_entry.place(x=150, y=4)

        self.program_var = tk.StringVar()
        self.program_var.set(self.PAR.PotN['Program ID'])
        program_label = tk.Label(labelframe_ObsInf, text="Program ID: ")
        program_label.place(x=71, y=35)
        program_entry = tk.Entry(labelframe_ObsInf, width=25, bd=3,
                                 textvariable=self.program_var)
        program_entry.place(x=150, y=35)

        self.TO_var = tk.StringVar()
        self.TO_var.set(self.PAR.PotN['Telescope Operator'])
        TO_label = tk.Label(labelframe_ObsInf, text="Telescope Operator(s): ")
        TO_label.place(x=4, y=66)
        TO_entry = tk.Entry(labelframe_ObsInf, width=25,
                            bd=3, textvariable=self.TO_var)
        TO_entry.place(x=150, y=66)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    FILTER STATUS Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame0l = tk.Frame(self, background="cyan")
        self.frame0l.place(x=10, y=155, anchor="nw", width=220, height=110)

        labelframe_Filters = tk.LabelFrame(self.frame0l, text="Filter Status",
                                           font=self.bigfont)  # ("Arial", 24))
        labelframe_Filters.pack(fill="both", expand="yes")


#        label_FW1 =  tk.Label(labelframe_Filters, text="Filters")
#        label_FW1.place(x=4,y=10)

        all_dirs = SF.read_dir_user()
        filter_data = ascii.read(os.path.join(
            local_dir, all_dirs['dir_system'], 'SAMOS_Filter_positions.txt'))
        filter_names = list(filter_data[0:12]['Filter'])
        self.filter_data = filter_data
        # print(filter_names)

        self.FW_filter = tk.StringVar()
        # initial menu text
        self.FW_filter.set(filter_names[2])

        # Create Dropdown menu
        self.optionmenu_FW = tk.OptionMenu(
            labelframe_Filters, self.FW_filter, *filter_names)
        self.optionmenu_FW.place(x=5, y=8)
        self.optionmenu_FW.config(bg="white", fg="black")
        button_SetFW = tk.Button(
            labelframe_Filters, text="Set Filter", bd=3, command=self.set_filter)
        button_SetFW.place(x=110, y=4)

#        self.Current_Filter = tk.StringVar()
#        self.Current_Filter.set(self.FW1_filter.get())
        self.Label_Current_Filter = tk.Text(labelframe_Filters, font=(
            'Georgia 20'), width=8, height=1, bg='white', fg='green')
        # self.Label_Current_Filter.insert(tk.END,"",#self.FW1_Filter)
        self.Label_Current_Filter.insert(tk.END, self.FW_filter.get())
        self.Label_Current_Filter.place(x=30, y=45)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         entry_FW1 = tk.Entry(labelframe_Filters, width=11,  bd =3)
#         entry_FW1.place(x=100, y=10)
# # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         label_FW1_template =  tk.Label(labelframe_Filters, text="HH:MM:SS.xx")
#         label_FW1_template.place(x=200,y=10)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         label_FW2 =  tk.Label(labelframe_Filters, text="FW 2")
#         label_FW2.place(x=4,y=40)
#         # Dropdown menu options
#         FW2_options = [
#             "[OIII]",
#             "Ha",
#             "[SII]",
#             "blank",
#             "open"
#         ]
#         # datatype of menu text
#         self.FW2_filter = tk.StringVar()
#         # initial menu text
#         self.FW2_filter.set(FW2_options[4])
#         # Create Dropdown menu
#         self.optionmenu_FW2 = tk.OptionMenu(labelframe_Filters, self.FW2_filter, *FW2_options)
#         self.optionmenu_FW2.place(x=40, y=38)
#         button_SetFW2 =  tk.Button(labelframe_Filters, text="Set FW2", bd=3)
#         button_SetFW2.place(x=125,y=34)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         entry_FW2 = tk.Entry(labelframe_Filters, width=11, bd =3)
#         entry_FW2.place(x=100, y=40)
# # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         label_FW1_template =  tk.Label(labelframe_Filters, text="2213DD:MM:SS.xx")
#         label_FW1_template.place(x=200,y=10)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        button_HomeFW1 =  tk.Button(labelframe_Filters, text="Home FW1", bd=3)
#        button_HomeFW1.place(x=4,y=70)
#        button_HomeFW2 =  tk.Button(labelframe_Filters, text="Home FW2", bd=3)
#        button_HomeFW2.place(x=105,y=70)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    GRISM STATUS Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame1l = tk.Frame(self, background="cyan")
        self.frame1l.place(x=220, y=155, anchor="nw", width=220, height=110)

        labelframe_Grating = tk.LabelFrame(
            self.frame1l, text="Grism Status", font=self.bigfont)  # ("Arial", 24))
        labelframe_Grating.pack(fill="both", expand="yes")
#        labelframe_Grating.place(x=4, y=10)

        all_dirs = SF.read_dir_user()
        Grating_data = ascii.read(os.path.join(
            local_dir, all_dirs['dir_system'], 'SAMOS_Filter_positions.txt'))
        self.Grating_names = list(Grating_data[12:18]['Filter'])
        self.Grating_positions = list(Grating_data[12:18]['Position'])
#        print(Grating_names)
#
        self.Grating_Optioned = tk.StringVar()
        # initial menu text
        index = 2
        self.Grating_Optioned.set(self.Grating_names[index])
        # Create Dropdown menu
        self.optionmenu_GR = tk.OptionMenu(
            labelframe_Grating, self.Grating_Optioned, *self.Grating_names)
        self.optionmenu_GR.place(x=5, y=8)
        self.optionmenu_GR.config(bg="white", fg="black")
        button_SetGR = tk.Button(
            labelframe_Grating, text="Set Grism", bd=3, width=7, command=self.set_grating)
        button_SetGR.place(x=110, y=4)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         self.Grating_int = tk.IntVar()
#         self.Grating_int.set(2)
#         self.optionmenu_GR = tk.OptionMenu(labelframe_Grating, self.Grating_int, *self.Grating_names)
#         self.optionmenu_GR.place(x=5, y=8)
#         button_SetGR =  tk.Button(labelframe_Grating, text="Set Grating", bd=3, command=self.set_grating)
#         button_SetGR.place(x=110,y=4)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Label_Current_Grating = tk.Text(labelframe_Grating, font=(
            'Georgia 20'), width=8, height=1, bg='white', fg='green')
        # self.Label_Current_Filter.insert(tk.END,"",#self.FW1_Filter)
        self.Label_Current_Grating.insert(tk.END, self.Grating_names[index])
        self.Label_Current_Grating.place(x=30, y=45)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         # Dropdown menu options
#         options = [
#             "Low Blue",
#             "Low Red",
#             "High Blue",
#             "High Red"
#         ]
#         # datatype of menu text
#         self.grating = tk.StringVar()
#         # initial menu text
#         self.grating.set(options[2])
#         # Create Dropdown menu
#         self.optionmenu_grating = tk.OptionMenu(labelframe_Grating, self.grating, *options)
#         self.optionmenu_grating.place(x=4, y=0)
#
#         button_HomeGrating=  tk.Button(labelframe_Grating, text="Home Grating", bd=3)
#         button_HomeGrating.place(x=4,y=35)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         label_FW1 =  tk.Label(labelframe_Filters, text="Grism")
#         label_FW1.place(x=4,y=10)
#         entry_FW1 = tk.Entry(labelframe_Filters, width=5,  bd =3)
#         entry_FW1.place(x=100, y=10)
#         label_FW2 =  tk.Label(labelframe_Filters, text="Filter Wheel 2")
#         label_FW2.place(x=4,y=40)
#         entry_FW2 = tk.Entry(labelframe_Filters, width=5, bd =3)
#         entry_FW2.place(x=100, y=40)
#
#         button_HomeFW1 =  tk.Button(labelframe_Filters, text="Home FW1", bd=3)
#         button_HomeFW1.place(x=0,y=70)
#         button_HomeFW2 =  tk.Button(labelframe_Filters, text="Home FW2", bd=3)
#         button_HomeFW2.place(x=105,y=70)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         self.frame0r = tk.Frame(self,background="cyan")#, width=400, height=800)
#         self.frame0r.place(x=601, y=0, anchor="nw", width=500, height=800)
#
#
#         vbox = tk.Frame(self.frame0l, relief=tk.RAISED, borderwidth=1)
#         vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#       CCD SETUP
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        self.frame_CCDInf = tk.Frame(self, background="cyan")
        self.frame_CCDInf.place(
            x=10, y=265, anchor="nw", width=430, height=330)
        labelframe_CCDInf = tk.LabelFrame(
            self.frame_CCDInf, text="CCD Setup", font=self.bigfont)
        labelframe_CCDInf.pack(fill="both", expand="yes")


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Configure IMAGE Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame2l = tk.Frame(self.frame_CCDInf, background="cyan")
        self.frame2l.place(x=4, y=30, anchor="nw", width=422, height=150)

#        root = tk.Tk()
#        root.title("Tab Widget")

        tabstyle = ttk.Style()

        tabstyle.configure("TNotebook.Tab", darkcolor="dark gray", lightcolor="black",
                           foreground="black")

        tabControl = ttk.Notebook(self.frame2l, padding=0, style="TNotebook")

        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        tab4 = ttk.Frame(tabControl)
        tab5 = ttk.Frame(tabControl)

        tabControl.add(tab1, text='Science')
        tabControl.add(tab2, text='Bias')
        tabControl.add(tab3, text='Dark')
        tabControl.add(tab4, text='Flat')
        tabControl.add(tab5, text='Buffer')
        tabControl.pack(expand=1, fill="both")
        self.var_acq_type = tk.StringVar()
        self.tabControl = tabControl
        self.tabControl.bind("<<NotebookTabChanged>>", self.change_acq_type)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      SCIENCE
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Acquire = tk.LabelFrame(
                                            tab1, 
                                            text="Science", 
                                            font=self.bigfont)
        labelframe_Acquire.place(x=2, y=5, anchor="nw", width=420, height=90)

        label_ObjectName = tk.Label(labelframe_Acquire, text="Object Name:")
        label_ObjectName.place(x=4, y=2)
        self.ObjectName = tk.StringVar()
        self.ObjectName.set(self.PAR.PotN['Object Name'])
        entry_ObjectName = tk.Entry(labelframe_Acquire, width=16,  bd=3,
                                    textvariable=self.ObjectName)
        entry_ObjectName.place(x=100, y=0)
        #start keeping memory of the opbject name to handle WCS changes
        self.Previous_ObjectName = self.ObjectName.get()


        self.Light_NofFrames = tk.IntVar()
        self.Light_NofFrames.set(1)
        label_Light_NofFrames = tk.Label(
            labelframe_Acquire, text="Nr. of Frames:")
        label_Light_NofFrames.place(x=220, y=2)
        entry_Light_NofFrames = tk.Entry(labelframe_Acquire, textvariable=self.Light_NofFrames,
                                         width=3, bd=3)
        entry_Light_NofFrames.place(x=315, y=0)

        label_Comment = tk.Label(labelframe_Acquire, text="Comments:")
        label_Comment.place(x=4, y=35)
        self.Comment = tk.StringVar()
        self.Comment.set(self.PAR.PotN['Comment'])
        self.entry_Comment = tk.Entry(labelframe_Acquire, width=20,  bd=3, 
                                      textvariable=self.Comment)
        self.entry_Comment.place(x=100, y=33)

        self.var_Light_saveall = tk.IntVar()
        r1_Light_saveall = tk.Checkbutton(labelframe_Acquire, text="Save single frames",
                                          variable=self.var_Light_saveall, onvalue=1, offvalue=0)
        r1_Light_saveall.place(x=250, y=35)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      BIAS
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Bias = tk.LabelFrame(tab2,
                                        text="Bias",
                                        font=self.bigfont)
        labelframe_Bias.place(x=2, y=5, anchor="nw", width=420, height=90)

        label_Bias_MasterFile = tk.Label(labelframe_Bias, text="Master Bias:")
        label_Bias_MasterFile.place(x=4, y=2)
        self.Bias_MasterFile = tk.StringVar(value="Bias")
        entry_Bias_MasterFile = tk.Entry(
            labelframe_Bias, width=8,  bd=3, textvariable=self.Bias_MasterFile)
        entry_Bias_MasterFile.place(x=100, y=0)

        label_Bias_NofFrames = tk.Label(labelframe_Bias, text="Nr. of Frames:")
        label_Bias_NofFrames.place(x=220, y=2)
        self.Bias_NofFrames = tk.StringVar(value="1")
        entry_Bias_NofFrames = tk.Entry(
            labelframe_Bias, width=3,  bd=3, textvariable=self.Bias_NofFrames)
        entry_Bias_NofFrames.place(x=315, y=0)

        label_Comment = tk.Label(labelframe_Bias, text="Comments:")
        label_Comment.place(x=4, y=35)
        self.BiasComment = tk.StringVar()
        self.BiasComment.set(self.PAR.PotN['Comment'])
        self.entry_BiasComment = tk.Entry(labelframe_Bias, width=20,  bd=3, 
                                          textvariable=self.BiasComment)
        self.entry_BiasComment.place(x=100, y=33)


        self.var_Bias_saveall = tk.IntVar()
        r1_Bias_saveall = tk.Checkbutton(labelframe_Bias, text="Save single frames",
                                          variable=self.var_Bias_saveall, onvalue=1, offvalue=0)
        r1_Bias_saveall.place(x=250, y=35)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      Dark
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Dark = tk.LabelFrame(tab3, text="Dark",
                                    #    width=300, height=170,
                                        font=self.bigfont)
        labelframe_Dark.place(x=2, y=5, anchor="nw", width=420, height=90)

        label_Dark_MasterFile = tk.Label(labelframe_Dark, text="Master Dark:")
        label_Dark_MasterFile.place(x=4, y=2)
        self.Dark_MasterFile = tk.StringVar(value="Dark")
        entry_Dark_MasterFile = tk.Entry(
            labelframe_Dark, width=8,  bd=3, textvariable=self.Dark_MasterFile)
        entry_Dark_MasterFile.place(x=100, y=0)

        label_Comment = tk.Label(labelframe_Dark, text="Comments:")
        label_Comment.place(x=4, y=35)
        self.DarkComment = tk.StringVar()
        self.DarkComment.set(self.PAR.PotN['Comment'])
        self.entry_DarkComment = tk.Entry(labelframe_Dark, width=20,  bd=3, 
                                          textvariable = self.DarkComment)
        self.entry_DarkComment.place(x=100, y=33)

        label_Dark_NofFrames = tk.Label(labelframe_Dark, text="Nr. of Frames:")
        label_Dark_NofFrames.place(x=220, y=2)
        self.Dark_NofFrames = tk.StringVar(value="1")
        entry_Dark_NofFrames = tk.Entry(
            labelframe_Dark, width=3,  bd=3, textvariable=self.Dark_NofFrames)
        entry_Dark_NofFrames.place(x=315, y=0)

        self.var_Dark_saveall = tk.IntVar()
        r1_Dark_saveall = tk.Checkbutton(labelframe_Dark, text="Save single frames",
                                          variable=self.var_Dark_saveall, onvalue=1, offvalue=0)
        r1_Dark_saveall.place(x=250, y=35)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      Flat
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Flat = tk.LabelFrame(tab4, text="Flat",
                                       # width=300, height=170,
                                        font=self.bigfont)
        labelframe_Flat.place(x=2, y=5, anchor="nw", width=420, height=90)

        label_Flat_MasterFile = tk.Label(
            labelframe_Flat, text="Master Flat File:")
        label_Flat_MasterFile.place(x=4, y=2)
        self.Flat_MasterFile = tk.StringVar(value="Flat")
        entry_Flat_MasterFile = tk.Entry(
            labelframe_Flat, width=8,  bd=3, textvariable=self.Flat_MasterFile)
        entry_Flat_MasterFile.place(x=100, y=0)

        label_Comment = tk.Label(labelframe_Flat, text="Comments:")
        label_Comment.place(x=4, y=35)
        self.FlatComment = tk.StringVar()
        self.FlatComment.set(self.PAR.PotN['Comment'])
        self.entry_FlatComment = tk.Entry(labelframe_Flat, width=20,  bd=3, 
                                          textvariable=self.FlatComment)
        self.entry_FlatComment.place(x=100, y=33)

#        label_Flat_ExpT =  tk.Label(labelframe_Flat, text="Exposure time (s):")
#        #label_Flat_ExpT.place(x=4,y=10)
#        self.Flat_ExpT = tk.StringVar(value="0.00")
#        entry_Flat_ExpT = tk.Entry(labelframe_Flat, width=6,  bd =3, textvariable=self.Flat_ExpT)
#        #entry_Flat_ExpT.place(x=120, y=6)

        label_Flat_NofFrames = tk.Label(labelframe_Flat, text="Nr. of Frames:")
        label_Flat_NofFrames.place(x=220, y=2)
        self.Flat_NofFrames = tk.StringVar(value="1")
        entry_Flat_NofFrames = tk.Entry(
            labelframe_Flat, width=3,  bd=3, textvariable=self.Flat_NofFrames)
        entry_Flat_NofFrames.place(x=315, y=0)

        self.var_Flat_saveall = tk.IntVar()
#        r1_Flat_saveall = tk.Radiobutton(
#            labelframe_Flat, text="Save single frames", variable=self.var_Flat_saveall, value=1)
        r1_Flat_saveall = tk.Checkbutton(labelframe_Flat, text="Save single frames",
                                          variable=self.var_Flat_saveall, onvalue=1, offvalue=0)
        r1_Flat_saveall.place(x=250, y=35)

#        button_ExpStart = tk.Button(labelframe_Flat, text="START", bd=3, bg='#0052cc', font=self.bigfont,
#                                    command=self.expose_flat)
#        button_ExpStart.place(x=75, y=95)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      Buffer
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Buffer = tk.LabelFrame(tab5, text="Buffer",
                                         # width=300, height=180,
                                          font=self.bigfont)
        labelframe_Buffer.place(x=2, y=5, anchor="nw", width=420, height=90)

        label_Buffer_MasterFile = tk.Label(
            labelframe_Buffer, text="Master Buffer File:")
        label_Buffer_MasterFile.place(x=4, y=2)
        self.Buffer_MasterFile = tk.StringVar(value="Buffer")
        entry_Buffer_MasterFile = tk.Entry(
            labelframe_Buffer, width=8,  bd=3, textvariable=self.Buffer_MasterFile)
        entry_Buffer_MasterFile.place(x=100, y=0)

        label_Comment = tk.Label(labelframe_Buffer, text="Comments:")
        label_Comment.place(x=4, y=35)
        self.BufferComment = tk.StringVar()
        self.BufferComment.set(self.PAR.PotN['Comment'])
        self.entry_BufferComment = tk.Entry(labelframe_Buffer, width=20,  bd=3, 
                                            textvariable = self.BufferComment)
        self.entry_BufferComment.place(x=100, y=33)


#        label_Buffer_ExpT =  tk.Label(labelframe_Buffer, text="Exposure time (s):")
#        #label_Buffer_ExpT.place(x=4,y=10)
#        self.Buffer_ExpT = tk.StringVar(value="0.00")
#        entry_Buffer_ExpT = tk.Entry(labelframe_Buffer, width=6,  bd =3, textvariable=self.Buffer_ExpT)
#        #entry_Buffer_ExpT.place(x=120, y=6)

        label_Buffer_NofFrames = tk.Label(
            labelframe_Buffer, text="Nr. of Frames:")
        label_Buffer_NofFrames.place(x=220, y=2)
        self.Buffer_NofFrames = tk.StringVar(value="1")
        entry_Buffer_NofFrames = tk.Entry(
            labelframe_Buffer, width=5,  bd=3, textvariable=self.Buffer_NofFrames)
        entry_Buffer_NofFrames.place(x=315, y=0)

        self.var_Buffer_saveall = tk.IntVar()
#        r1_Buffer_saveall = tk.Radiobutton(
#            labelframe_Buffer, text="Save single frames", variable=self.var_Buffer_saveall, value=1)
        r1_Buffer_saveall = tk.Checkbutton(labelframe_Buffer, text="Save single frames",
                                          variable=self.var_Buffer_saveall, onvalue=1, offvalue=0)
        r1_Buffer_saveall.place(x=250, y=35)

#        button_ExpStart = tk.Button(labelframe_Buffer, text="START", bd=3, bg='#0052cc', font=self.bigfont,
#                                    command=self.expose_buffer)
        # button_ExpStart.place(x=75,y=95)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

#       ACQUISITION PANEL
# Begin exposure with progress bars

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        self.AcquisitionFrame = tk.Frame(
            self.frame_CCDInf, background="dark gray")
        self.AcquisitionFrame.place(x=5, y=150, width=420, height=172)

        labelframe_ExposeBegin = tk.LabelFrame(self.AcquisitionFrame, text="Acquisition",
                                               font=self.bigfont)
        labelframe_ExposeBegin.pack(fill="both", expand="yes")

        label_out_fname = tk.Label(
            labelframe_ExposeBegin, text="Base Filename:")
        label_out_fname.place(x=4, y=15)
        self.out_fname = tk.StringVar()
        self.out_fname.set(self.PAR.PotN['Base Filename'])
        entry_out_fname = tk.Entry(labelframe_ExposeBegin, textvariable=self.out_fname,
                                   width=8, bd=3)
        entry_out_fname.place(x=100, y=13)

        # set exposure time
        label_ExpTime = tk.Label(labelframe_ExposeBegin, text="Exp. Time (s):")
        label_ExpTime.place(x=4, y=55)
        self.ExpTimeSet = tk.StringVar()
        self.ExpTimeSet.set("0.01")
        entry_ExpTime = tk.Entry(
            labelframe_ExposeBegin, textvariable=self.ExpTimeSet, width=5,  bd=3)
        entry_ExpTime.place(x=100, y=53)

        
        # Select Acquisition Type
        #label_Display = tk.Label(labelframe_ExposeBegin, text="Image Type:")
        #label_Display.place(x=205, y=0)
        #self.var_acq_type = tk.StringVar()
        #tab_selected = self.tabControl.tab(self.tabControl.select(), "text")

        #self.var_acq_type.set(tab_selected)
        #self.acq_type_select = ttk.Combobox(labelframe_ExposeBegin, width=8,
        #                                    textvariable=self.var_acq_type,
        #                                    style="TCombobox")
        #self.acq_type_select["values"] = [
        #    "Science", "Bias", "Dark", "Flat", "Buffer"]
        #self.acq_type_select["state"] = "readonly"
        #self.acq_type_select.place(x=295, y=0)
        
        
        # label each file name incrementally to keep track
        self.out_fnumber = tk.IntVar()

        import fnmatch
        if not os.path.exists(self.fits_dir):
            next_file_number = 1

        else:
            # current_files = [os.path.join(self.fits_dir,f) for f in os.listdir(self.fits_dir) if not fnmatch.fnmatch(f, "SAMOS_*fits")]
            current_files = glob.glob(os.path.join(
                self.fits_dir, "*_"+"[0-9]"*4+".fits"))
            if len(current_files) == 0:
                next_file_number = 1
            else:
                last_file = max(current_files, key=os.path.getctime)
                last_file = os.path.split(last_file)[1]
                # set number of next exposure to be after the number of the most recently saved image
                next_file_number = int(
                    last_file.strip(".fits").split("_")[-1])+1
        out_int = "{:04n}".format(next_file_number)

        self.out_fnumber.set(out_int)
        label_out_fnumber = tk.Label(labelframe_ExposeBegin, text="Exp. #")
        label_out_fnumber.place(x=160, y=55)
        entry_out_fnumber = tk.Spinbox(labelframe_ExposeBegin,
                                       textvariable=self.out_fnumber, width=4,
                                       increment=1, from_=0, to=1000, format="%04.0f")
        # command=self.change_out_fnumber)
        entry_out_fnumber.place(x=205, y=53)
        self.entry_out_fnumber = entry_out_fnumber
        # To begin the exposure
        button_ExpStart = tk.Button(labelframe_ExposeBegin, text="START", bd=3,
                                    bg='#0052cc', font=self.bigfont,
                                    command=self.start_an_exposure)
        button_ExpStart.place(x=285, y=25)

        #### Include progress bars for exposure and readout. ####
        # Most of this so we can update the label during an exposure.
        s_expose = ttk.Style(labelframe_Acquire)
        # add the label to the progressbar style
        s_expose.layout('text.Horizontal.TProgressbar',
                        [('Horizontal.Progressbar.trough',
                          {'children': [('Horizontal.Progressbar.pbar',
                                         {'side': 'left', 'sticky': 'ns'})],
                           'sticky': 'nswe'}),
                            ('Horizontal.Progressbar.label', {'sticky': 'nswe'})])

        # change the text of the progressbar,
        # the trailing spaces are here to properly center the text
        s_expose.configure("text.Horizontal.TProgressbar",
                           text="Expose 0 %      ", anchor='center',
                           background="magenta", foreground="black", troughcolor="gray")

        self.var_perc_exp_done = tk.IntVar()
        self.exp_progbar = ttk.Progressbar(labelframe_ExposeBegin, orient='horizontal',
                                           variable=self.var_perc_exp_done,
                                           length=130, style="text.Horizontal.TProgressbar")
        self.exp_progbar.place(x=280, y=80)
        # need to save the style so it can be configured later during exposure/readout
        self.exp_progbar_style = s_expose

        s_readout = ttk.Style(labelframe_Acquire)
        s_readout.layout('text.Horizontal.RProgressbar',
                         [('Horizontal.Progressbar.trough',
                           {'children': [('Horizontal.Progressbar.pbar',
                                          {'side': 'left', 'sticky': 'ns'})],
                            'sticky': 'nswe'}),
                             ('Horizontal.Progressbar.label', {'sticky': 'nswe'})])

        s_readout.configure("text.Horizontal.RProgressbar",
                            text="Readout 0 %      ", anchor='center',
                            background="cyan", troughcolor="gray", foreground="black")

        self.var_perc_read_done = tk.IntVar()
        self.readout_progbar = ttk.Progressbar(labelframe_ExposeBegin, orient='horizontal',
                                               variable=self.var_perc_read_done,
                                               length=130, style="text.Horizontal.RProgressbar")
        self.readout_progbar.place(x=280, y=110)
        # need to save the style so it can be configured later during exposure/readout
        self.readout_progbar_style = s_readout

        label_Display = tk.Label(
            labelframe_ExposeBegin, text="Correct for Quick Look:")
        label_Display.place(x=4, y=95)
        self.subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(
            labelframe_ExposeBegin, text='Bias', variable=self.subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=115)
        self.subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(
            labelframe_ExposeBegin, text='Dark', variable=self.subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60, y=115)
        self.divide_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(
            labelframe_ExposeBegin, text='Flat', variable=self.divide_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120, y=115)
        self.subtract_Buffer = tk.IntVar()
        check_Buffer = tk.Checkbutton(
            labelframe_ExposeBegin, text='Buffer', variable=self.subtract_Buffer, onvalue=1, offvalue=0)
        check_Buffer.place(x=180, y=115)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    FITS manager
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame_FITSmanager = tk.Frame(self, background="pink")
        self.frame_FITSmanager.place(
            x=10, y=600, anchor="nw", width=430, height=210)

        labelframe_FITSmanager = tk.LabelFrame(
            self.frame_FITSmanager, text="FITS manager", font=self.bigfont)
        labelframe_FITSmanager.pack(fill="both", expand="yes")

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#
#
#         label_FW1 =  tk.Label(labelframe_Filters, text="Filter Wheel 1")
#         label_FW1.place(x=4,y=10)
#         entry_FW1 = tk.Entry(labelframe_Filters, width=5,  bd =3)
#         entry_FW1.place(x=100, y=10)
#         label_FW2 =  tk.Label(labelframe_Filters, text="Filter Wheel 2")
#         label_FW2.place(x=4,y=40)
#         entry_FW2 = tk.Entry(labelframe_Filters, width=5, bd =3)
#         entry_FW2.place(x=100, y=40)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        button_FITS_Load = tk.Button(labelframe_FITSmanager, text="Load existing file", bd=3,
                                     command=self.load_existing_file)
        button_FITS_Load.place(x=0, y=0)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#       RA, DEC Entry box
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.string_RA = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA.set("150.17110")  # NGC 3105
        label_RA = tk.Label(labelframe_FITSmanager, text='RA:',  bd=3)
        self.entry_RA = tk.Entry(
            labelframe_FITSmanager, width=11,  bd=3, textvariable=self.string_RA)
        label_RA.place(x=150, y=-1)
        self.entry_RA.place(x=190, y=-5)

        """ DEC Entry box"""
        self.string_DEC = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC.set("-54.79004")  # NGC 3105
        label_DEC = tk.Label(labelframe_FITSmanager, text='Dec:',  bd=3)
        self.entry_DEC = tk.Entry(
            labelframe_FITSmanager, width=11,  bd=3, textvariable=self.string_DEC)
        label_DEC.place(x=150, y=20)
        self.entry_DEC.place(x=190, y=20)
        
        button_RADEC_to_SOAR = tk.Button(labelframe_FITSmanager, text="Send to SOAR", bd=3,
                             command=self.send_RADEC_to_SOAR)
        button_RADEC_to_SOAR.place(x=300, y=8)

# =============================================================================
#      QUERY Server
#
# =============================================================================
        labelframe_Query_Survey = tk.LabelFrame(labelframe_FITSmanager, text="Query Image Server",
                                                width=420, height=140,
                                                font=self.bigfont)
        labelframe_Query_Survey.place(x=5, y=45)


        self.label_SelectSurvey = tk.Label(
            labelframe_Query_Survey, text="Survey")
        self.label_SelectSurvey.place(x=5, y=5)
#        # Dropdown menu options
        Survey_options = [
            "SkyMapper",
#            "SDSS",
#            "PanSTARRS/DR1/", #SIMBAD - 
#            "DSS",          #SIMBAD - 
#            "DSS2/red",     #SIMBAD - 
#            "CDS/P/AKARI/FIS/N160", #SIMBAD - 
#            "2MASS/J",      #SIMBAD -  
#            "GALEX",        # SIMBAD - 
            "AllWISE/W3"]   # SIMBAD - 
#        # datatype of menu text
        self.Survey_selected = tk.StringVar()
#        # initial menu text
        self.Survey_selected.set(Survey_options[0])
#        # Create Dropdown menu
        self.menu_Survey = tk.OptionMenu(
            labelframe_Query_Survey, self.Survey_selected,  *Survey_options)
        # add bar to split menu, see
        # https://stackoverflow.com/questions/55621073/add-a-separator-to-an-option-menu-in-python-with-tkinter
        self.menu_Survey['menu'].insert_separator(3)
        self.menu_Survey.place(x=55, y=4)

#        self.readout_Simbad = tk.Label(self.frame0l, text='')


#        """ SkyMapper Query """
#        #button_skymapper_query = tk.Button(labelframe_FITSmanager, text="SkyMapper Query", bd=1,
#        #                                   command=self.SkyMapper_query)
#        #button_skymapper_query.place(x=190, y=65)
#
#        """ SkyMapper or SDSS query"""
#        griz_Survey_options = [
#            "SkyMapper Query",
#            "SDSS Query"]
#        # datatype of menu text
#        self.griz_Survey_selected = tk.StringVar()
#        # initial menu text
#        self.griz_Survey_selected.set(griz_Survey_options[0])
#        # Create Dropdown menu
#        self.griz_menu_Survey = tk.OptionMenu(
#            labelframe_FITSmanager, self.griz_Survey_selected,  *griz_Survey_options)
#        self.griz_menu_Survey.place(x=190, y=65)

        
        
        """ Filter Entry box"""
        self.string_Filter = tk.StringVar()
        self.string_Filter.set("i")
        label_Filter = tk.Label(labelframe_Query_Survey, text='Filter:',  bd=3)
        entry_Filter = tk.Entry(labelframe_Query_Survey,
                                width=2,  bd=3, textvariable=self.string_Filter)
        label_Filter.place(x=195, y=5)
        entry_Filter.place(x=240, y=4)
        
        """ QUERY BUTTON"""
        button_Query_Survey = tk.Button(
            labelframe_Query_Survey, text="Query", bd=3, command=self.Query_Survey)
        button_Query_Survey.place(x=300, y=5)


        """ Nr. of Stars Entry box"""
        label_nrofstars = tk.Label(
            labelframe_Query_Survey, text="Nr. of stars:")
        label_nrofstars.place(x=5, y=36)
        self.nrofstars = tk.IntVar()
        entry_nrofstars = tk.Entry(
            labelframe_Query_Survey, width=3,  bd=3, textvariable=self.nrofstars)
        entry_nrofstars.place(x=80, y=35)
        self.nrofstars.set('25')

        """ twirl Astrometry"""
        button_twirl_Astrometry = tk.Button(labelframe_Query_Survey, text="twirl WCS", bd=3,
                                            command=self.twirl_Astrometry)
        button_twirl_Astrometry.place(x=125, y=35)
        
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#       RA, DEC cente display
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.string_RA_cntr = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA_cntr.set(self.string_RA.get())  # NGC 3105
        label_RA_cntr = tk.Label(labelframe_Query_Survey, text='CNTR RA:',  bd=3)
        self.entry_RA_cntr = tk.Entry(
            labelframe_Query_Survey, width=11,  bd=3, textvariable=self.string_RA_cntr)
        label_RA_cntr.place(x=5, y=65)
        self.entry_RA_cntr.place(x=80,y=65)
        
        self.string_RA_cntr_mm = tk.StringVar()
        self.string_RA_cntr_mm.set(0)
        label_RA_cntr_mm = tk.Label(labelframe_Query_Survey, text='X(mm):',  bd=3)
        self.entry_RA_cntr_mm = tk.Entry(
            labelframe_Query_Survey, width=5,  bd=3, textvariable=self.string_RA_cntr_mm)
        label_RA_cntr_mm.place(x=150, y=65)
        self.entry_RA_cntr_mm.place(x=200, y=65)

        """ DEC Entry box"""
        self.string_DEC_cntr = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC_cntr.set(self.string_DEC.get())  # NGC 3105
        label_DEC_cntr = tk.Label(labelframe_Query_Survey, text='CNTR Dec:',  bd=3)
        self.entry_DEC_cntr = tk.Entry(
            labelframe_Query_Survey, width=11,  bd=3, textvariable=self.string_DEC_cntr)
        label_DEC_cntr.place(x=5, y=90)
        self.entry_DEC_cntr.place(x=80, y=90)
        
        self.string_DEC_cntr_mm = tk.StringVar()
        self.string_DEC_cntr_mm.set(0)
        label_DEC_cntr_mm = tk.Label(labelframe_Query_Survey, text='Y(mm):',  bd=3)
        self.entry_DEC_cntr_mm = tk.Entry(
            labelframe_Query_Survey, width=5,  bd=3, textvariable=self.string_DEC_cntr_mm)
        label_DEC_cntr_mm.place(x=150, y=90)
        self.entry_DEC_cntr_mm.place(x=200, y=90)
        
        button_RADEC_to_SOAR = tk.Button(labelframe_Query_Survey, text="Send to Guider", bd=3,
                             command=self.send_RADEC_to_SOAR)
        button_RADEC_to_SOAR.place(x=270, y=70)
        
        
        

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        button_Astrometry =  tk.Button(labelframe_FITSmanager, text="Astrometry", bd=3,
#                                            command=Astrometry)
#                                            command=self.load_Astrometry)
#        button_Astrometry.place(x=0,y=110)

#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# GINGA DISPLAY
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=450, y=0, anchor="nw")  # , width=500, height=800)
        # self.vb = vbox

#        canvas = tk.Canvas(vbox, bg="grey", height=514, width=522)
        canvas = tk.Canvas(vbox, bg="grey", height=516, width=528)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # => ImageViewTk -- a backend for Ginga using a Tk canvas widget
        fi = CanvasView(logger)
        # => Call this method with the Tkinter canvas that will be used for the display.
        fi.set_widget(canvas)
        # fi.set_redraw_lag(0.0)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        # fi.enable_draw(False)
        # tk seems to not take focus with a click
        fi.set_enter_focus(True)
        fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        canvas = self.canvas_types.DrawingCanvas()
        canvas.enable_draw(True)
        canvas.enable_edit(True)
        canvas.set_drawtype('box', color='red')
#        canvas.set_drawtype('point', color='red')
        canvas.register_for_cursor_drawing(fi)
        canvas.add_callback('draw-event', self.draw_cb)
        canvas.set_draw_mode('draw')
        # without this call, you can only draw with the right mouse button
        # using the default user interface bindings
        # canvas.register_for_cursor_drawing(fi)

        canvas.ui_set_active(True)
        self.canvas = canvas


#        # add canvas to viewers default canvas
        fi.get_canvas().add(canvas)

        self.drawtypes = canvas.get_drawtypes()
        self.drawtypes.sort()

#        fi.configure(516, 528) #height, width
        fi.set_window_size(514, 522)

        self.readout = tk.Label(vbox, text='')
        self.readout.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
        # self.readout.place()

        """
        HORIZONTAL BOX AT THE BOTTOM WITH ORIGINAL GINGA TOOLS
        """

        hbox = tk.Frame(self)
        hbox.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.drawtypes = canvas.get_drawtypes()
        # wdrawtype = ttk.Combobox(self, values=self.drawtypes,
        # command=self.set_drawparams)
        # index = self.drawtypes.index('ruler')
        # wdrawtype.current(index)
        wdrawtype = tk.Entry(hbox, width=12)
        wdrawtype.insert(0, 'box')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype

        wdrawcolor = ttk.Combobox(
            hbox, values=self.drawcolors, style="TCombobox")  # ,
        #                           command=self.set_drawparams)
        index = self.drawcolors.index('red')
        wdrawcolor.current(index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        # wdrawcolor = tk.Entry(hbox, width=12)
        # wdrawcolor.insert(0, 'blue')
        # wdrawcolor.bind("<Return>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor

        self.vfill = tk.IntVar()
        wfill = tk.Checkbutton(hbox, text="Fill", variable=self.vfill)
        self.wfill = wfill

        walpha = tk.Entry(hbox, width=12)
        walpha.insert(0, '1.0')
        walpha.bind("<Return>", self.set_drawparams)
        self.walpha = walpha

        wrun = tk.Button(hbox, text="Slits Only",
                         command=self.slits_only)
        wclear = tk.Button(hbox, text="Clear Canvas",
                           command=self.clear_canvas)
        wsave = tk.Button(hbox, text="Save Canvas",
                          command=self.save_canvas)
        wopen = tk.Button(hbox, text="Open File",
                          command=self.open_file)
        # pressing quit button freezes application and forces kernel restart.
        wquit = tk.Button(hbox, text="Quit",
                          #command=lambda: self.quit(self))
                          command=self.MASTER_quit)

        for w in (wquit, wsave, wclear, wrun, walpha, tk.Label(hbox, text='Alpha:'),
                  #                  wfill, wdrawcolor, wslit, wdrawtype, wopen):
                  wfill, wdrawcolor, wdrawtype, wopen):
            w.pack(side=tk.RIGHT)

        # mode = self.canvas.get_draw_mode() #initially set to draw by line >canvas.set_draw_mode('draw')


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    Motor/Telescope Indicator Frame
#         Circles that light green or magenta
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        self.canvas_Indicator = tk.Canvas(self, background="gray")
        self.canvas_Indicator.place(x=60, y=810, width=310, height=85)

        self.canvas_Indicator.create_oval(20, 20, 60, 60, fill=indicator_light_on_color,
                                          outline=None, tags=["filter_ind"])
        self.canvas_Indicator.create_text(40, 70, text="Filters")
        self.canvas_Indicator.create_oval(100, 20, 140, 60, fill=indicator_light_on_color,
                                          tags=["grism_ind"], outline=None)
        self.canvas_Indicator.create_text(120, 70, text="Grisms")

        # indicator for mirror and SOAR TCS applicable at telescope
        self.canvas_Indicator.create_oval(170, 20, 210, 60, fill=indicator_light_off_color, tags=["mirror_ind"],
                                          outline=None)
        self.canvas_Indicator.create_text(190, 70, text="Mirror")
        self.canvas_Indicator.create_oval(240, 20, 280, 60, fill=indicator_light_off_color, tags=["tcs_ind"],
                                          outline=None)
        self.canvas_Indicator.create_text(260, 70, text="TCS")

        # connect canvas_Indicator to the PCM class so it can tell
        # the objects what color to be
        # might not be necessary to chane color in PCM class but keeping it here for now
        PCM.canvas_Indicator = self.canvas_Indicator

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    SLIT Configuration Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame_SlitConf = tk.Frame(self, background="gray")
        self.frame_SlitConf.place(
            x=460, y=610, anchor="nw", width=500, height=250)
        labelframe_SlitConf = tk.LabelFrame(self.frame_SlitConf, text="Slit Configuration",
                                            font=self.bigfont)
        labelframe_SlitConf.pack(fill="both", expand="yes")

        self.Draw_Edit_Pick_Checked = tk.StringVar(None, "draw")
        btn1 = tk.Radiobutton(labelframe_SlitConf, text="Draw", padx=6, pady=1,
                              variable=self.Draw_Edit_Pick_Checked, value="draw", command=self.set_mode_cb)
        # btn1.pack(anchor='ne')
        btn1.place(x=220, y=25)
        btn2 = tk.Radiobutton(labelframe_SlitConf, text="Edit", padx=10, pady=1,
                              variable=self.Draw_Edit_Pick_Checked, value="edit", command=self.set_mode_cb)
        btn2.place(x=220, y=50)  # pack(anchor='ne')
        btn3 = tk.Radiobutton(labelframe_SlitConf, text="Delete", padx=9, pady=1,
                              variable=self.Draw_Edit_Pick_Checked, value="pick", command=self.set_mode_cb)
        btn3.place(x=220, y=75)  # pack(anchor='ne')
    

#        self.deleteChecked = tk.IntVar()
#        btn4 = tk.Checkbutton(labelframe_SlitConf, text="Delete Picked", padx=5, pady=1,
#                              variable=self.deleteChecked)
#        btn4.place(x=280, y=75)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    SLIT WIDTH in mirrors, dispersion direction (affects Resolving power)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        label_slit_w = tk.Label(labelframe_SlitConf,
                                text="Slit width (mirrors)")
        label_slit_w.place(x=4, y=4)
        self.slit_w = tk.IntVar(value=3)
        self.textbox_slit_w = tk.Entry(
            labelframe_SlitConf, textvariable=self.slit_w, width=4)
        # self.textbox_slit_w.place(x=130,y=5)

        width_adjust_btn = tk.Spinbox(labelframe_SlitConf,
                                      command=self.slit_width_length_adjust, increment=1,
                                      textvariable=self.slit_w, width=5,
                                      from_=0, to=1080)
        width_adjust_btn.place(x=130, y=4)
        width_adjust_btn.bind("<Return>", self.slit_width_length_adjust)
        self.width_adjust_btn = width_adjust_btn


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    SLIT LENGTH in mirror, cross-dispersion (affets sky subtraction)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        label_slit_l = tk.Label(labelframe_SlitConf,
                                text="Slit length (mirrors)")
        label_slit_l.place(x=4, y=29)
        self.slit_l = tk.IntVar()
        self.slit_l.set(9)
        self.textbox_slit_l = tk.Entry(
            labelframe_SlitConf, textvariable=self.slit_l, width=4)
        # self.textbox_slit_l.place(x=130,y=30)

        length_adjust_btn = tk.Spinbox(labelframe_SlitConf,
                                       command=self.slit_width_length_adjust, increment=1,
                                       textvariable=self.slit_l, width=5,
                                       from_=0, to=1080)
        length_adjust_btn.place(x=130, y=30)
        length_adjust_btn.bind("<Return>", self.slit_width_length_adjust)
        self.length_adjust_btn = length_adjust_btn

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    SLIT POINTER ENABLED
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.CentroidPickup_ChkBox_Enabled = tk.IntVar()
        wslit = tk.Checkbutton(labelframe_SlitConf, text="Source Pickup",
                               variable=self.CentroidPickup_ChkBox_Enabled, command=self.set_slit_drawtype)
        wslit.place(x=220, y=0)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    SHOW TRACES ENABLED
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # self.traces = tk.IntVar()
        traces_button = tk.Button(
            labelframe_SlitConf, text="Show Traces", command=self.show_traces)
        traces_button.place(x=330, y=-3)

        remove_traces_button = tk.Button(
            labelframe_SlitConf, text="Remove Traces", command=self.remove_traces, padx=0, pady=0)
        remove_traces_button.place(x=330, y=24)
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    View Slit Table
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        view_slit_tab_button = tk.Button(
            labelframe_SlitConf, text="View Slit Table", command=self.show_slit_table, padx=0, pady=0)
        view_slit_tab_button.place(x=330, y=51)
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    Find Stars
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        button_find_stars = tk.Button(labelframe_SlitConf, text="Find stars", bd=3,
                                            command=self.find_stars, state='active', padx=0, pady=0)#'disabled')
        button_find_stars.place(x=330, y=78)
        self.button_find_stars = button_find_stars
        

        #### check overlapping slits and create a series of new DMD patterns with slits that do not overlap #####

        labelframe_PatternSeries = tk.LabelFrame(labelframe_SlitConf, text="Create Pattern Series with No Overlapping Slits",
                                                 font=self.bigfont_15, height=110, width=385)
        labelframe_PatternSeries.place(x=4, y=105)
        # labelframe_PatternSeries.pack(fill="both", expand="yes")

        overlapping_slits_btn = tk.Button(labelframe_PatternSeries, text="Generate Patterns", command=self.create_pattern_series_from_traces,
                                          padx=0, pady=0)
        overlapping_slits_btn.place(x=4, y=4)

        self.base_pattern_name_var = tk.StringVar()
        self.base_pattern_name_var.set("Base Pattern Name")

        base_pattern_name_entry = tk.Entry(labelframe_PatternSeries, width=15,
                                           textvariable=self.base_pattern_name_var, foreground="gray")
        base_pattern_name_entry.place(x=150, y=4, height=25)
        base_pattern_name_entry.bind(
            "<KeyPress>", self.set_pattern_entry_text_color)
        self.base_pattern_name_entry = base_pattern_name_entry

        self.selected_dmd_pattern = tk.StringVar()
        self.pattern_group_dropdown = ttk.Combobox(labelframe_PatternSeries, width=25,
                                                   textvariable=self.selected_dmd_pattern, style="TCombobox")
        self.pattern_group_dropdown.bind(
            "<<ComboboxSelected>>", self.selected_dmd_group_pattern)
        self.pattern_group_dropdown.place(x=4, y=35, width=200)

        save_this_sub_pattern_btn = tk.Button(labelframe_PatternSeries, text="Save Displayed Pattern",
                                              command=self.save_selected_sub_pattern,
                                              padx=0, pady=0)
        save_this_sub_pattern_btn.place(x=205, y=32)
        save_all_sub_patterns_btn = tk.Button(labelframe_PatternSeries,
                                              text="Save All Patterns",
                                              command=self.save_all_sub_patterns, padx=0, pady=0)
        save_all_sub_patterns_btn.place(x=4, y=60)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    Apply to All
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # self.apply_to_all = tk.IntVar()
        apply_to_all_button = tk.Button(
            labelframe_SlitConf, text="Apply to All", command=self.apply_to_all)
        apply_to_all_button.place(x=4, y=55)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #   ORTHONORMAL ENABLED
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.Orthonormal_ChkBox_Enabled = tk.IntVar()
        Orthonormal_checkbox = tk.Checkbutton(
                               labelframe_SlitConf, text="Orthonormal",
                               variable=self.Orthonormal_ChkBox_Enabled)
        Orthonormal_checkbox.place(x=100, y=55)


        """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    DMD Handler Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        #, width=400, height=800)
        self.frame0r = tk.Frame(self,background="cyan")
        self.frame0r.place(x=1270, y=10, anchor="nw", width=360, height=120)

        labelframe_DMD =  tk.LabelFrame(
            self.frame0r, text="DMD", font=("Arial", 24))
        labelframe_DMD.pack(fill="both", expand="yes")

         # 1) Set the x size of the default slit
         # 2) Set the y size of the default slit
         # 3) save slit pattern to file
         # 4) save and push slit pattern
         # 5) load slit pattern
         # 6) shift slit pattern
         # 7) analyze point source
         # 8) remove slit

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
         # 3) write slit pattern
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        regfname_entry = tk.Entry(labelframe_DMD)
        regfname_entry.place(x=0,y=25, width=150)
        # default text is greyed out
        regfname_entry.config(fg='grey',bg='white')
        regfname_entry.insert(tk.END,"enter pattern name")
        regfname_entry.bind("<FocusIn>", self.regfname_handle_focus_in)
        # regfname_entry.bind("<FocusOut>", self.regfname_handle_focus_out)
        self.regfname_entry = regfname_entry
        # click in entry box deletes default text and allows entry of new text
        button_write_slits =  tk.Button(
            labelframe_DMD, text="SAVE: Slits -> .reg file", bd=3, command=self.write_slits)
        button_write_slits.place(x=155,y=25)


        button_load_ds9regfile_xyAP =  tk.Button(
            labelframe_DMD, text="LOAD: .reg file -> Slits", bd=3, command=self.load_ds9regfile_xyAP)
        button_load_ds9regfile_xyAP.place(x=155,y=50)

        button_push_slits =  tk.Button(labelframe_DMD, text="Slits -> DMD", bd=3, font=(
            "Arial", 24),  relief=tk.RAISED, command=self.push_slits)
        button_push_slits.place(x=80,y=85)
        """

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # 4)# LOAD BUTTONS
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        """
        button_load_map = tk.Button(labelframe_DMD,
                        text = "Load DMD Map",
                        command = self.LoadMap)
        button_load_map.place(x=4,y=162)

        label_filename = tk.Label(labelframe_DMD, text="Current DMD Map")
        label_filename.place(x=4,y=190)
        self.str_map_filename = tk.StringVar()
        self.textbox_filename = tk.Text(labelframe_DMD, height = 1, width = 22)
        self.textbox_filename.place(x=120,y=190)
        """

        """
        button_load_slits = tk.Button(labelframe_DMD,
                       text = "Load Slit Grid",
                       command = self.LoadSlits)
        button_load_slits.place(x=4,y=222)

        label_filename_slits = tk.Label(
            labelframe_DMD, text="Current Slit Grid")
        label_filename_slits.place(x=4,y=250)
        self.str_map_filename_slits = tk.StringVar()
        self.textbox_filename_slits = tk.Text(
            labelframe_DMD, height = 1, width = 22)
        self.textbox_filename_slits.place(x=120,y=250)
        """

        """
        button_save_slittable = tk.Button(labelframe_DMD,
                       text = "Save Slit Table",
                       command = self.Save_slittable)
        button_save_slittable.place(x=4,y=282)

        label_filename_slittable = tk.Label(
            labelframe_DMD, text="Saved Slit Table")
        label_filename_slittable.place(x=4,y=310)
        self.str_map_filename_slittable = tk.StringVar()
        self.textbox_filename_slittable= tk.Text(
            labelframe_DMD, height = 1, width = 22)
        self.textbox_filename_slittable.place(x=120,y=310)
        """

        """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    DMD Handler Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        """
        self.frame1r = tk.Frame(self)  # , width=400, height=800)
        self.frame1r.place(x=1000, y=5, anchor="nw", width=380, height=860)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    RADEC module
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_Sky = tk.LabelFrame(self.frame1r,
                                       text="Sky (RA,Dec) regions",
                                       font=self.bigfont_20, bg="#8AA7A9")
#        labelframe_Sky.pack(fill="both", expand="yes")
        labelframe_Sky.place(x=0, y=0, width=380, height=250)

        button_load_regfile_RADEC = tk.Button(labelframe_Sky,
                                              text="load (RA,Dec) regions from ds9/radec .reg file",
                                              command=self.load_regfile_RADEC)
        button_load_regfile_RADEC.place(x=4, y=4)

        label_filename_regfile_RADEC = tk.Label(labelframe_Sky,
                                                text="Loaded Region File in RADEC units:",
                                                bg="#8AA7A9")
        label_filename_regfile_RADEC.place(x=4, y=34)
        self.str_filename_regfile_RADEC = tk.StringVar()
        self.textbox_filename_regfile_RADEC = tk.Text(
            labelframe_Sky, height=1, width=48)
        self.textbox_filename_regfile_RADEC.place(x=4, y=55)

        button_push_RADEC = tk.Button(labelframe_Sky,
                                      text="get center/point (RA,Dec) from filename ",
                                      command=self.push_RADEC)
        button_push_RADEC.place(x=54, y=90)

        label_workflow = tk.Label(
            labelframe_Sky, text="Point, take an image and twirl WCS from GAIA...", bg="#8AA7A9")
        label_workflow.place(x=4, y=120)

        button_regions_RADEC2pixel = tk.Button(labelframe_Sky,
                                               text="display ds9/radec regions -> Ginga",
                                               command=self.display_ds9ad_Ginga)
        button_regions_RADEC2pixel.place(x=4, y=145)

        button_regions_RADEC_save = tk.Button(labelframe_Sky,
                                              text="write Ginga regions -> ds9/radec .reg file",
                                              command=self.write_GingaRegions_ds9adFile)
        button_regions_RADEC_save.place(x=4, y=175)

        """
        button_regions_RADEC_save= tk.Button(labelframe_Sky,
                                            text = "save (RA,Dec) regions -> astropy XY.reg file",
                        command = self.save_RADECregions_AstropyXYRegFile)
        button_regions_RADEC_save.place(x=4,y=211)
        """
 # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
 #  #    CCD  module
 # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_CCD = tk.LabelFrame(self.frame1r,
                                       text="CCD (x,y) regions", font=self.bigfont_20, bg="#00CED1")
#        labelframe_CCD.pack(fill="both", expand="yes")
        labelframe_CCD.place(x=0, y=251, width=380, height=159)

        button_load_ds9regfile_xyAP = tk.Button(labelframe_CCD,
                                                text="load (x,y) regions from ds9/xy .reg file",
                                                command=self.load_ds9regfile_xyAP)
        button_load_ds9regfile_xyAP.place(x=4, y=4)

        label_filename_regfile_xyAP = tk.Label(labelframe_CCD,
                                               text="Loaded Region File in CCD units:",
                                               bg="#00CED1")
        label_filename_regfile_xyAP.place(x=4, y=34)
        self.str_filename_regfile_xyAP = tk.StringVar()
        self.textbox_filename_regfile_xyAP = tk.Text(
            labelframe_CCD, height=1, width=48)
        self.textbox_filename_regfile_xyAP.place(x=4, y=55)

        """
        button_push_CCD = tk.Button(labelframe_CCD,
                        text = "get pointing RA,DEC from filename",
                        command = self.push_CCD)
        button_push_CCD.place(x=54,y=90)
        """

        """
        label_workflow = tk.Label(
            labelframe_CCD, text="Point, take an image and twirl WCS from GAIA...", bg="#00CED1")
        label_workflow.place(x=4,y=130)
        """

        # button_regions_CCD2RADEC = tk.Button(labelframe_CCD,
        #                                text = "convert Ginga x,y regions -> ds9/radec regions",
        #                                command = self.convert_GAxy_APad)
        # button_regions_CCD2RADEC.place(x=4,y=121)

        """
        button_regions_CCD2pixel = tk.Button(labelframe_CCD,
                                        text = "convert (x,y) regions -> slits",
                                        command = self.convert_regions_xyAP2xyGA)
        button_regions_CCD2pixel.place(x=4,y=151)
        """

        # button_regions_draw = tk.Button(labelframe_CCD,
        #                                text = "DRAW",
        #                                command = self.draw_slits)
        # button_regions_draw.place(x=250,y=151)

        button_regions_CCD_save = tk.Button(labelframe_CCD,
                                            text="save (x,y) regions -> ds9/xy .reg file",
                                            command=self.save_regions_xy2xyfile)
        button_regions_CCD_save.place(x=4, y=90)

 # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
 #  #    DMD  module
 # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_DMD = tk.LabelFrame(
            self.frame1r, text="DMD slits", font=self.bigfont_20, bg="#20B2AA")
#        labelframe_DMD.pack(fill="both", expand="yes")
        labelframe_DMD.place(x=0, y=410, width=380, height=260)

        """
        button_load_regfile_DMD = tk.Button(labelframe_DMD,
                        text = "load targets DMD from .reg file",
                        command = self.load_regfile_DMD)
        button_load_regfile_DMD.place(x=4,y=4)

        label_filename_regfile_DMD = tk.Label(
            labelframe_DMD, text="Loaded Region File in DMD units:", bg="#20B2AA")
        label_filename_regfile_DMD.place(x=4,y=34)
        self.str_filename_regfile_DMD = tk.StringVar()
        self.textbox_filename_regfile_DMD= tk.Text(
            labelframe_DMD, height = 1, width = 48)
        self.textbox_filename_regfile_DMD.place(x=4,y=55)

        button_push_DMD = tk.Button(labelframe_DMD,
                        text = "get pointing RA,DEC from filename",
                        command = self.push_DMD)
        button_push_DMD.place(x=54,y=90)

        label_workflow = tk.Label(
            labelframe_DMD, text="Point, take an image and twirl WCS from GAIA...", bg="#20B2AA")
        label_workflow.place(x=4,y=130)
        """

        button_push_slits = tk.Button(labelframe_DMD, text="Current Slit Regions -> DMD", bd=3, font=self.bigfont,  relief=tk.RAISED,
                                      command=self.push_slit_shape)
        button_push_slits.place(x=20, y=4)
#        button_push_slits.place(x=20,y=125)

        button_save_slittable = tk.Button(labelframe_DMD,
                                          text="Save Slit List to .csv",
                                          command=self.Save_slittable)
        button_save_slittable.place(x=4, y=54)
#        button_save_slittable.place(x=4,y=175)

        label_filename_slittable = tk.Label(labelframe_DMD,
                                            text="Saved Slit List .csv file",
                                            bg="#20B2AA")  # 00CED1")
#        label_filename_slittable.place(x=4,y=205)
        label_filename_slittable.place(x=4, y=84)

        self.str_filename_slittable = tk.StringVar()
        self.textbox_filename_slittable = tk.Text(
            labelframe_DMD, height=1, width=25)
#        self.textbox_filename_slittable.place(x=147,y=206)
        self.textbox_filename_slittable.place(x=147, y=85)

        button_load_slits = tk.Button(labelframe_DMD,
                                      text="Load & Push Slit .csv List",
                                      command=self.load_regfile_csv)
#        button_load_slits.place(x=4,y=4)
        button_load_slits.place(x=4, y=125)

        label_filename_slits = tk.Label(
            labelframe_DMD, text="Current Slit List", bg="#20B2AA")
#        label_filename_slits.place(x=4,y=34)
        label_filename_slits.place(x=4, y=154)
        self.str_filename_slits = tk.StringVar()
        self.textbox_filename_slits = tk.Text(
            labelframe_DMD, height=1, width=22)
#        self.textbox_filename_slits.place(x=120,y=34)
        self.textbox_filename_slits.place(x=120, y=155)

        button_regions_DMD2pixel = tk.Button(labelframe_DMD,
                                             text="convert slit regions -> (x,y) pixels",
                                             command=self.convert_regions_slit2xyAP)
#        button_regions_DMD2pixel.place(x=4,y=84)
        button_regions_DMD2pixel.place(x=4, y=185)

        """
        button_regions_DMD_save= tk.Button(labelframe_DMD,
                                             text = "save Regions RA,DEC -> astropy .reg file",
                         command = self.save_regions_DMD_AstropyReg)
        button_regions_DMD_save.place(x=4,y=181)
        """

 # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
 #  #    HTS module
 # #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        labelframe_HTS = tk.LabelFrame(
            self.frame1r, text="HTS", font=self.bigfont_20, bg="#98F5FF")
#        labelframe_HTM.pack(fill="both", expand="yes")
        labelframe_HTS.place(x=0, y=700, width=380, height=150)

        """ Load Mask"""
        button_load_masks_HTS = tk.Button(labelframe_HTS,
                                          text="Load mask:",
                                          command=self.load_masks_file_HTS)
        button_load_masks_HTS.place(x=4, y=5)

        label_filename_masks_HTS = tk.Label(
            labelframe_HTS, text="Loaded Mask:")
        label_filename_masks_HTS.place(x=4, y=30)
        # self.str_filename_masks = tk.StringVar()
        self.textbox_filename_masks_HTS = tk.Text(
            labelframe_HTS, height=1, width=22)
        self.textbox_filename_masks_HTS.place(x=120, y=31)

        """ Pust Mask"""
        button_push_masks_HTS = tk.Button(labelframe_HTS,
                                          text="Push mask:",
                                          command=self.push_masks_file_HTS)
        button_push_masks_HTS.place(x=4, y=60)

        label_filename_masks_HTS_pushed = tk.Label(
            labelframe_HTS, text="Pushed Mask:")
        label_filename_masks_HTS_pushed.place(x=4, y=85)
        # self.str_filename_masks = tk.StringVar()
        self.textbox_filename_masks_HTS_pushed = tk.Text(
            labelframe_HTS, height=1, width=22)
        self.textbox_filename_masks_HTS_pushed.place(x=120, y=86)

        """ NExt Mask"""
        button_next_masks_HTS = tk.Button(labelframe_HTS,
                                          text="NEXT",
                                          command=self.next_masks_file_HTS)
        button_next_masks_HTS.place(x=290, y=83)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load AP Region file in RADEC
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#    def save_regions_DMD_AstropyReg(self):
#        """ to be written """
#        pass

#    def push_DMD(self):
#        """ to be written """
#        pass

    def load_regfile_csv(self):
        """ to be written """
        self.LoadSlits()
        pass

    def save_regions_xy2xyfile(self):
        """ Save (x,y) Astropy Regions to .reg file """
        """ converting Ginga Regions to AP/radec Regions
            - collects/compound all Ginga Regions in RRR_xyGA
            - convert to AP/xy   (aka RRR_xyAP)
            - write to AP/xy .region file
                => requires WCS
        """

        print("saving (x,y) Astropy Regions to .reg file")
        file = filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                        defaultextension=".reg",
                                        initialdir=os.path.join(local_dir, "SAMOS_regions", "pixels"))
        # 1. Collect all
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        # 2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        # 3. Write astropy regions, pixels
        self.RRR_xyAP.write(file.name, overwrite=True)
        print("(x,y) Astropy Regions to .reg file:\n", file.name)

#    def push_CCD(self):
#        """ to be written """
#        pass

#    def change_out_fnumber(self):
#        """
#        Returns
#        -------
#        Incremental change in Exposure number to be appended to the end of filenames.
#
#        """
#        return

    def write_GingaRegions_ds9adFile(self):
        """ collect all Ginga regions and save to a ds9/ad .reg file
            - collect all Ginga xy Regions in a AP/ad list
                uses convert_GAxy_APad()
            - wites the AP/ad on file list as set of ds9/ad region files
        """
        if "RRR_RADec" not in dir(self):
            print("There are no (RA,Dec) regions to be written on file")
            return
        else:
            print("saving (RA,DEC) Astropy Regions to .reg file")
            file = filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                            defaultextension=".reg",
                                            initialdir=os.path.join(local_dir, "SAMOS_regions", "RADEC"))
        # we want to scoop all objects on the canvas
        # obj_all = CM.CompoundMixin.get_objects(self.canvas)
            self.RRR_RADec = self.convert_GAxy_APad()
            print("\ncollected all Ginga xy Regions in a AP/ad list (aka RRR_RADec")
            self.RRR_RADec.write(file.name, overwrite=True)
            print("saved  AP/ad list to ds/ad region file file:\n", file.name)
            print(
                "\ncollected all Ginga xy Regions to ads/ad region file file:\n", file.name)

    """
    def save_RADECregions_AstropyXYRegFile(self):
        print("saving (x,y) Astropy Regions to .reg file")
        self.display_ds9ad_GingaAP()
        file = filedialog.asksaveasfile(filetypes = [("txt file", ".reg")],
                                        defaultextension = ".reg",
                                        initialdir=local_dir+"/SAMOS_regions/pixels")
        self.RRR_xyAP.write(file.name, overwrite=True)
    """

    def display_ds9ad_Ginga(self):
        """ converting ds9/radec Regions to AP/radec Regions
            - open ds9/radec region file and convert to AP/xy (aka RRR_xyAP)
                -> requires WCS
            - convert AP/xy to Ginga/xy (aka RRR_xyGA)
            - convert AP/xy to AP/ad (aka RRR_RADec)
        """
        print("displaying ds9/radec Regions on Ginga\n")
        # requires wcs: class AStrometry
        if 'wcs' not in dir(self):
            print("missing self.wcs. No operation performed \n")
            return
        self.RRR_xyAP = Astrometry.APRegion_RAD2pix(
            self.filename_regfile_RADEC, self.wcs)
        print("\nopened ds9/radec region file and converted to AP/xy (aka RRR_xyAP)\n => used current WCS")

        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("\nconverted AP/xy to Ginga/xy (aka RRR_xyGA)")

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP, self.wcs)
        print("converted AP/xy to APradec (aka RRR_RADec)")
        self.SlitTabView.load_table_from_regfile_RADEC(regs_RADEC=self.RRR_RADec,
                                                       img_wcs=self.wcs)
        print("displayed APradec regions on Ginga display")

        # return self.RRR_xyAP

    def convert_GAxy_APad(self):
        """ converting Ginga Regions to AP/radec Regions
            - collects/compound all Ginga Regions in RRR_xyGA
            - convert tho AP/xy   (aka RRR_xyAP)
            - convert to AP/radec (aka RRR_RADec)
                => requires WCS
        """
        print("converting Ginga Regions to AP/radec Regions")
        # requires wcs: class AStrometry
        if 'wcs' not in dir(self):
            print("missing self.wcs. No operation performed \n")
            return
        # 1. Collect all objects in ginga canvas
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("\ncollected/compounded all Ginga Regions in RRR_GAxy")
        # 2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        print("converted GA/xy to AP/xy   (aka RRR_xyAP)")
        # 3. convert to RADEC using wcs
        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP, self.wcs)
        print("converted AP/xy converted to AP/ad (aka RRR_RADec")
        print("\nCompleted conversion Ginga Regions to AP/radec Regions ")
        return self.RRR_RADec

    def draw_slits(self):

        # all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        # color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas, color="red")
        # [print("draw-slits obj tags ", obj.tag) for obj in all_ginga_objects]
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)

    """
    def convert_regions_xyAP2slit(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        # color in RED all the regions loaded from .reg file
        # requires Dana wcs
        # returns .csv map file
        pass
    """

    def convert_regions_slit2xyAP(self):
        """ to be written """
        # requires Dana wcs
        # returns RRR_xyAP
        pass

    def convert_regions_xyAP2xyGA(self):
        """ converting (x,y) Astropy Regions to (x,y) Ginga Regions """
        print("converting (x,y) Astropy Regions to (x,y) Ginga Regions")

        # cleanup, keep only the slits
        self.slits_only()

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        # [CM.CompoundMixin.add_object(self.canvas,r2g(reg)) for reg in self.RRR_xyAP]
        for reg in range(len(self.RRR_xyAP)):
            this_reg = self.RRR_xyAP[reg]
            this_obj = r2g(this_reg)
            this_obj.pickable = True
            this_obj.add_callback('pick-down', self.pick_cb, 'down')
            this_obj.add_callback('pick-up', self.pick_cb, 'up')

            this_obj.add_callback('pick-key', self.pick_cb, 'key')
            self.canvas.add(this_obj)
            # ap_region.add_region(self.canvas, this_reg)
            if reg < 10 or reg == len(self.RRR_xyAP)-1:
                print("reg number {} tag: {}".format(reg, this_obj.tag))
            self.SlitTabView.slit_obj_tags.append(this_obj.tag)
        # [print("cm object tags", obj.tag) for obj in self.canvas.get_objects()]
        # uses r2g
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("(x,y) Astropy regions converted to (x,y) Ginga regions\nRRR_xyGA created")
        return self.RRR_xyGA
        # self.RRR_xyGA is a self.canvas.objects

    def convert_regions_xyGA2xyAP(self):
        """ converting (x,y) Ginga Regions to (x,y) Astropy Regions """
        print("converting (x,y) Ginga Regions to (x,y) Astropy Regions")
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        list_all_ginga_objects = list(all_ginga_objects)
        if len(list_all_ginga_objects) != 0:
            self.RRR_xyAP = Regions([g2r(list_all_ginga_objects[0])])
            for i in range(1, len(list_all_ginga_objects)):
                self.RRR_xyAP.append(g2r(list_all_ginga_objects[i]))
        return self.RRR_xyAP
        print("(x,y) Ginga regions converted to (x,y) Astropy regions")
        
    def push_RADEC(self):
        """ to be written """
        self.string_RA = tk.StringVar(self, self.RA_regCNTR)
        self.string_DEC = tk.StringVar(self, self.DEC_regCNTR)
        self.entry_RA.delete(0, tk.END)
        self.entry_DEC.delete(0, tk.END)
        self.entry_RA.insert(0, self.RA_regCNTR)
        self.entry_DEC.insert(0, self.DEC_regCNTR)
        print("RADEC loaded")

    def load_regfile_RADEC(self):
        """ read (RA,DEC) Regions from .reg file
        - open ds9/ad file and read the regions files creating a AP/ad list of regions (aka RRR_RADec)
        - extract center RA, Dec
        """
        print("read ds9/ad .reg file to create AP/ad regions (aka RRR_RADec")
        self.textbox_filename_regfile_RADEC.delete('1.0', tk.END)
#        self.textbox_filename_slits.delete('1.0', tk.END)
        self.filename_regfile_RADEC = filedialog.askopenfilename(initialdir=os.path.join(local_dir, "SAMOS_regions", "RADEC"),
                                                                 title="Select a File",
                                                                 filetypes=(("Text files",
                                                                             "*.reg"),
                                                                            ("all files",
                                                                             "*.*")))
        self.loaded_regfile = os.path.split(self.filename_regfile_RADEC)[1]
        # First read the file and set the regions in original RADEC units
        self.RRR_RADec = Regions.read(
            self.filename_regfile_RADEC, format='ds9')
        filtered_duplicates_regions = []
        for reg in self.RRR_RADec:
            if reg not in filtered_duplicates_regions:
                filtered_duplicates_regions.append(reg)

        self.RRR_RADec = filtered_duplicates_regions
        #
        # Then extract the clean filename to get RA and DEC of the central point
        head, tail = os.path.split(self.filename_regfile_RADEC)
        self.textbox_filename_regfile_RADEC.insert(tk.END, tail)
        
        # find the opject t name reading all characters up to the first "_"
        self.target_name = tail[0:tail.find("_")] 
        
        #write the object name in the Science tab
        self.ObjectName.set(self.target_name)        
                
        # the filename must carry the RADEC coordinates are "RADEC_". Find this string...
        s = re.search(r'RADEC=', tail)
        # extract RADEC
        RADEC = tail[s.end():-4]
        RA_cut = (re.findall('.*-', RADEC))
        # and RA, DEC as strings at disposal
        self.RA_regCNTR = RA_cut[0][:-1]
        self.DEC_regCNTR = (re.findall('-.*', RADEC))[0]
        # we return the filename
        print("(RA,DEC) Regions loaded from .reg file")

        return self.filename_regfile_RADEC

    def load_ds9regfile_xyAP(self):
        """ read (x,y) Astropy  Regions from ds9 .reg file
            - open ds9 .reg file in pixels units
            - extract the clean filename to get RA and DEC of the central point
            - create AP.xy regions (aka RRR_xyAP)
            - visualize xyAP regions on GINGA display\n
                => WCS solution needed
            - convert xyAP regions to GINGA regions (aka RRR_xyGA)
        """
        print("\n Load ds9/xy reg. file")
        reg = filedialog.askopenfilename(filetypes=[("region files", "*.reg")],
                                         initialdir=os.path.join(local_dir, 'SAMOS_regions', 'pixels'))
        print("reading (x,y) Astropy region file")
        if isinstance(reg, tuple):
            regfileName = reg[0]
        else:
            regfileName = str(reg)
        # if len(regfileName) != 0:

        # Then
        head, tail = os.path.split(regfileName)
        self.loaded_regfile = regfileName
        self.textbox_filename_regfile_xyAP.insert(tk.END, tail)

        self.RRR_xyAP = Regions.read(regfileName, format='ds9')
        print("created AP.xy regions (aka RRR_xyAP)")
        filtered_duplicates_regions = []
        for reg in self.RRR_xyAP:
            if reg not in filtered_duplicates_regions:
                filtered_duplicates_regions.append(reg)

        self.RRR_xyAP = filtered_duplicates_regions
        print("eliminated duplicated regions")

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        self.SlitTabView.load_table_from_regfile_CCD(regs_CCD=self.RRR_xyAP,
                                                     img_wcs=self.wcs)
        # if the image has a wcs, it will be used to get sky coords
        print("xyAP regions visualized on GINGA display\n   => WCS solution needed")

        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("convert xyAP regions to GINGA regions (aka RRR_xyGA)")
        # [print("first 10 xyAP obj tags ", obj.tag) for obj in self.canvas.get_objects()[:10]]

        # [print("last 10 xyAP obj tags ", obj.tag) for obj in self.canvas.get_objects()[-10:]]
        print("number of regions: ", len(self.canvas.get_objects()))
        # self.display_region_file()
        print("ds9/xy regions loaded in Ginga")
        # regfile = open(regfileName, "r")

    """
    def display_region_file(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        # color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas,color="red")
    """
    """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# DONE WITH THE FIELDS
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    """

    def regfname_handle_focus_out(self, _):
        """ to be written """

        current_text = self.regfname_entry.get()
        if current_text.strip(" ") == "":
            # self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg='grey')
            self.regfname_entry.config(bg='white')
            self.regfname_entry.insert(0, "enter pattern name")

    def regfname_handle_focus_in(self, _):
        """ to be written """

        current_text = self.regfname_entry.get()
        if current_text == "enter pattern name":

            self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg="black")

    def write_slits(self):
        """ to be written """
        # when writing a new DMD pattern, put it in the designated directory
        # don't want to clutter working dir.
        # At SOAR, this should be cleared out every night for the next observer
        created_patterns_path = path / Path("Astropy Regions/")
        pattern_name = self.regfname_entry.get()
        # check if pattern name has been proposed
        if (pattern_name.strip(" ") == "") or (pattern_name == "enter pattern name"):
            # if there is no pattern name provided, use a default based on
            # number of patterns already present
            num_patterns_thus_far = len(os.listdir(created_patterns_path))
            pattern_name = "pattern_reg{}.reg".format(num_patterns_thus_far)

        pattern_path = created_patterns_path / Path(pattern_name)

        # create astropy regions and save them after checking that there is something to save...
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas,'rectangle')
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'box')

        list_slits = list(slits)
        if len(list_slits) != 0:
            RRR = Regions([g2r(list_slits[0])])
            for i in range(1, len(list_slits)):
                RRR.append(g2r(list_slits[i]))
        RRR.write(str(pattern_path)+'.reg', overwrite=True)
        print("\nSlits written to region file\n")

    def collect_slit_shape(self):
        """
        collect selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)

        try:
            pattern_list_index = self.pattern_group_dropdown.current()
            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects = [self.canvas.get_object_by_tag(
                tag) for tag in current_pattern_tags]
        except:
            pass

        # counter = 0
        self.slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for obj in objects:
            print(obj)
          
            # force Orthonormal orientation if checkbox is set
            # This function is called if a checkbox forces the slits to be Orthonormal on the DMD. 
            # This is intended to havoid having slightly diagonal slits when the position angle of the image is not exactly 
            # oriented with the celestial coordinates
            if self.Orthonormal_ChkBox_Enabled.get() == 1:
                obj.rot_deg = 0.0
                
            ccd_x0, ccd_y0, ccd_x1, ccd_y1 = obj.get_llur()
            # first case: figures that have no extensions (i.e. points): do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1, y1 = convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1, y1] = 0
            elif self.CentroidPickup_ChkBox_Enabled.get() == 1 and obj.kind == 'point':
                x1, y1 = convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.floor(x1)), int(np.floor(y1))
                x2, y2 = convert.CCD2DMD(ccd_x1, ccd_y1)
                x2, y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))

                # dmd_corners[:][1] = corners[:][1]+500
                ####
                # x1 = round(dmd_corners[0][0])
                # y1 = round(dmd_corners[0][1])+400
                # x2 = round(dmd_corners[2][0])
                # y2 = round(dmd_corners[2][1])+400
                """
                # 3 load the slit pattern
                data_box = self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]), len(good_box[1]))
                """ paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_x):  # scanning multiple rows means each steps moves up along the y axis
                    # the indices of the y values pertinent to that x
                    iy = np.where(good_box_x == i)
                    iymin = min(iy[0])  # the smallest y index
                    iymax = max(iy[0])  # last largest y index
                    cx0 = ccd_x0 + i  # so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cy0 = ccd_y0 + good_box_y[iymin]
                    cy1 = ccd_y0 + good_box_y[iymax]
                    # get the lower value of the column at the x position,
                    x1, y1 = convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = convert.CCD2DMD(cx0, cy1)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y2+1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y2+1,x1-2:x1] = 1
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """ paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_y):  # scanning multiple rows means each steps moves up along the y axis
                    # the indices of the y values pertinent to that x
                    ix = np.where(good_box_y == i)
                    ixmin = min(ix[0])  # the smallest y index
                    ixmax = max(ix[0])  # last largest y index
                    cy0 = ccd_y0 + i  # so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cx0 = ccd_x0 + good_box_x[ixmin]
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    # get the lower value of the column at the x position,
                    x1, y1 = convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = convert.CCD2DMD(cx1, cy0)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y1,x1-2:x1] = 1
                """
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """
       #     self.slit_shape[x1:x2,y1:y2]=0
#        IP = self.PAR.IP_dict['IP_DMD']
#        [host,port] = IP.split(":")
#        DMD.initialize(address=host, port=int(port))
#        DMD._open()
#        DMD.apply_shape(self.slit_shape)

    def push_slit_shape(self):
        """
        push selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        
        # if someone forgot to remove the tracese, we do it here for safety
        self.remove_traces()
        self.collect_slit_shape()

        """# 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)

        try:

            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects =[self.canvas.get_object_by_tag(
                tag) for tag in current_pattern_tags]
        except:
            pass

        # counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            print(obj)
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()

            # first case: figures that have no extensions: do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1,y1]=0
            elif  self.CentroidPickup_ChkBox_Enabled.get() != 0 and obj.kind == 'point':
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """"""
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))

                # dmd_corners[:][1] = corners[:][1]+500
                ####
                # x1 = round(dmd_corners[0][0])
                # y1 = round(dmd_corners[0][1])+400
                # x2 = round(dmd_corners[2][0])
                # y2 = round(dmd_corners[2][1])+400
                """"""
                # 3 load the slit pattern
                data_box=self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]),len(good_box[1]))
                """""" paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion""""""
                for i in np.unique(good_box_x):  #scanning multiple rows means each steps moves up along the y axis
                    #the indices of the y values pertinent to that x
                    iy = np.where(good_box_x == i)
                    iymin = min(iy[0])   #the smallest y index
                    iymax = max(iy[0])   #last largest y index
                    cx0 = ccd_x0 + i     #so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cy0 = ccd_y0 + good_box_y[iymin]
                    cy1 = ccd_y0 + good_box_y[iymax]
                    #get the lower value of the column at the x position,
                    x1,y1 = convert.CCD2DMD(cx0,cy0)
                    x1,y1 = int(np.round(x1)), int(np.round(y1))
                    x2,y2 = convert.CCD2DMD(cx0,cy1)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y2+1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y2+1,x1-2:x1] = 1
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """""" paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion """"""
                for i in np.unique(good_box_y):  #scanning multiple rows means each steps moves up along the y axis
                    #the indices of the y values pertinent to that x
                    ix = np.where(good_box_y == i)
                    ixmin = min(ix[0])   #the smallest y index
                    ixmax = max(ix[0])   #last largest y index
                    cy0 = ccd_y0 + i     #so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cx0 = ccd_x0 + good_box_x[ixmin]
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    #get the lower value of the column at the x position,
                    x1,y1 = convert.CCD2DMD(cx0,cy0)
                    x1,y1 = int(np.round(x1)), int(np.round(y1))
                    x2,y2 = convert.CCD2DMD(cx1,cy0)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y1,x1-2:x1] = 1
                """"""
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """"""
       #     self.slit_shape[x1:x2,y1:y2]=0
#        IP = self.PAR.IP_dict['IP_DMD']
#        [host,port] = IP.split(":")
#        DMD.initialize(address=host, port=int(port))
#        DMD._open()
#        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()
        """
        
        self.push_slits()
        print("check")
                

    def push_slits(self):
        """ Actual push of the slit_shape to the DMD """
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()

    """
    def push_slits(self):
        # push selected slits to DMD pattern
        # Export all Ginga objects to Astropy region
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        # counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()

            x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            # dmd_corners[:][1] = corners[:][1]+500
            ####
            # x1 = round(dmd_corners[0][0])
            # y1 = round(dmd_corners[0][1])+400
            # x2 = round(dmd_corners[2][0])
            # y2 = round(dmd_corners[2][1])+400
        # 3 load the slit pattern
            self.slit_shape[x1:x2,y1:y2]=0
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))

#        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()

        print("check")


    def get_IP(self,device='DMD'):
        v=pd.read_csv("SAMOS_system_dev/IP_addresses_default.csv",header=None)
        if device == 'DMD':
            return(v[2][1])

        IPs = Config.load_IP_user(self)
        # print(IPs)
    """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#     def open_Astrometry(self):
#         btn = tk.Button(master,
#              text ="Click to open a new window",
#              command = openNewWindow)
#         btn.pack(pady = 10)ƒ
#         return self.Astrometry(master)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def set_filter(self):
        """ to be written """
        print(self.FW_filter.get())
        print('moving to filter:', self.FW_filter.get())
#        self.Current_Filter.set(self.FW_filter.get())
        filter = self.FW_filter.get()
        main_fits_header.set_param("filter", filter)
        filter_pos_ind = list(self.filter_data["Filter"]).index(filter)
        filter_pos = list(self.filter_data["Position"])[filter_pos_ind]
        main_fits_header.set_param("filtpos", filter_pos)
        print(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
        t = PCM.move_filter_wheel(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_on_color)
        self.canvas_Indicator.update()

        # self.Echo_String.set(t)
        print(t)

        self.Label_Current_Filter.delete("1.0", "end")
        self.Label_Current_Filter.insert(tk.END, self.FW_filter.get())

        self.extra_header_params += 1
        entry_string = param_entry_format.format(self.extra_header_params, 'String', 'FILTER',
                                                 filter, 'Selected filter')
        self.header_entry_string += entry_string

    def set_grating(self):
        print(self.Grating_names, self.Grating_Optioned.get())
        i_selected = self.Grating_names.index(self.Grating_Optioned.get())
        print(i_selected)
#        Grating_Position_Optioned
        GR_pos = self.Grating_positions[i_selected]
        print(GR_pos)
        main_fits_header.set_param("grating", GR_pos)
 #       print('moving to grating',Grating_Position_Optioned)
#        self.Current_Filter.set(self.FW1_filter.get())
#        grating = str(Grating_Position_Optioned)
#        print(grating)
#        t = PCM.move_grism_rails(grating)
#        GR_pos = self.selected_GR_pos.get()
#        print(type(GR_pos),type(str(GR_pos)),type("GR_B1"))
        self.canvas_Indicator.itemconfig(
            "grism_ind", fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
        t = PCM.move_grism_rails(GR_pos)
        self.canvas_Indicator.itemconfig(
            "grism_ind", fill=indicator_light_on_color)
        self.canvas_Indicator.update()

#        self.Echo_String.set(t)
        print(t)
        # self.Label_Current_Filter.insert(tk.END,"",#self.FW1_Filter)
        self.Label_Current_Grating.delete("1.0", "end")
        self.Label_Current_Grating.insert(tk.END, self.Grating_Optioned.get())

        self.extra_header_params += 1
        entry_string = param_entry_format.format(self.extra_header_params, 'String', 'GRISM',
                                                 i_selected, 'Grism position')
        self.header_entry_string += entry_string

        print(entry_string)

    def get_widget(self):
        """ to be written """
        return self.root

    def set_drawparams(self, evt):
        """ to be written """
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  # 'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def save_canvas(self):
        """ to be written """
        regs = ap_region.export_regions_canvas(self.canvas, logger=self.logger)
        # self.canvas.save_all_objects()

    def clear_canvas(self):
        """ to be written """
        # CM.CompoundMixin.delete_all_objects(self.canvas)#,redraw=True)
        obj_tags = list(self.canvas.tags.keys())
        # print(obj_tags)
        for tag in obj_tags:
            if self.SlitTabView is not None:
                if tag in self.SlitTabView.slit_obj_tags:
                    obj_ind = self.SlitTabView.slit_obj_tags.index(tag)
                    # self.SlitTabView.stab.delete_row(int(tag.strip("@")))
                    del self.SlitTabView.slit_obj_tags[obj_ind]
                self.SlitTabView.slitDF = self.SlitTabView.slitDF[0:0]

                # if not self.slit_window.winfo_exists():
                #    self.SlitTabView.recover_window()
        self.canvas.delete_all_objects(redraw=True)

# ConvertSIlly courtesy of C. Loomis
    def convertSIlly(self, fname, outname=None):
        """ to be written """
        FITSblock = 2880

    # If no output file given, just prepend "fixed"
        if outname is None:
            fname = pathlib.Path(fname)
            dd = fname.parent
            outname = pathlib.Path(fname.parent, 'fixed'+fname.name)

        with open(fname, "rb") as in_f:
            buf = in_f.read()
        in_f.close()
    # Two fixes:
    # Header cards:
        buf = buf.replace(b'SIMPLE  =                    F',
                          b'SIMPLE  =                    T')
        buf = buf.replace(b'BITPIX  =                  -16',
                          b'BITPIX  =                   16')
        buf = buf.replace(b"INSTRUME= Spectral Instruments, Inc. 850-406 camera  ",
                          b"INSTRUME= 'Spectral Instruments, Inc. 850-406 camera'")

    # Pad to full FITS block:
        blocks = len(buf) / FITSblock
        pad = round((math.ceil(blocks) - blocks) * FITSblock)
        buf = buf + (b'\0' * pad)

        with open(outname, "wb+") as out_f:
            out_f.write(buf)

##################################
#
#      EXPOSURE STARTS HERE
#
##################################

    def start_an_exposure(self):
        """ 
        This is the landing procedure after the START button has been pressed
        """
        self.update_PotN()
        self.obj_type = self.var_acq_type.get()
        self.start_combo_obj_number = int(self.entry_out_fnumber.get())
        # if a set of images, save the number suffix of the first
        # image in the set
        if self.obj_type == "Science":
            self.expose_light()
        elif self.obj_type == "Bias":
            self.expose_bias()
        elif self.obj_type == "Flat":
            self.expose_flat()
        elif self.obj_type == "Dark":
            self.expose_dark()
        elif self.obj_type == "Buffer":
            self.expose_buffer()

   
    def update_PotN(self):
        """
        Updates the parameters of the night variables and files for logging the observations
        """
        import json
#       How do we capture a parameter in another class/form?
        self.PAR.PotN['Telescope'] = self.ConfP.Telescope.get() #ConfigPage.Telescope.get()
        self.PAR.PotN['Program ID'] = self.program_var.get() 
        self.PAR.PotN['Proposal Title'] = self.ConfP.Proposal_Title.get()#ConfigPage.Telescope.get()
        self.PAR.PotN['Principal Investigator'] = self.ConfP.Principal_Investigator.get() #ConfigPage.Telescope.get()
        # For the parameters redefinied here it is easy: capture them...
        self.PAR.PotN['Observer'] = self.names_var.get()
        self.PAR.PotN['Telescope Operator'] = self.TO_var.get()
        self.PAR.PotN['Object Name'] = self.ObjectName.get()
        self.PAR.PotN['Comment'] = self.Comment.get()
        self.PAR.PotN['Bias Comment'] = self.BiasComment.get()
        self.PAR.PotN['Dark Comment'] = self.DarkComment.get()
        self.PAR.PotN['Flat Comment'] = self.FlatComment.get()
        self.PAR.PotN['Buffer Comment'] = self.FlatComment.get()
        self.PAR.PotN['Base Filename'] = self.out_fname.get()
        
        # ..open the json file and read all...
        PotN_file = os.path.join(local_dir,'SAMOS_system_dev','Parameters_of_the_night.txt')
        with open(PotN_file, "r") as jsonFile:
            data = json.load(jsonFile)
        #... change what has to be changed...
        data["Observer"] = self.PAR.PotN['Observer'] 
        data["Program ID"] = self.PAR.PotN['Program ID'] 
        data["Proposal Title"] = self.PAR.PotN['Proposal Title'] 
        data["Principal Investigator"] = self.PAR.PotN['Principal Investigator'] 
        data["Telescope Operator"] = self.PAR.PotN['Telescope Operator'] 
        data["Object Name"] = self.PAR.PotN['Object Name'] 
        data["Comment"] = self.PAR.PotN['Comment'] 
        data["Bias Comment"] = self.PAR.PotN['Bias Comment'] 
        data["Dark Comment"] = self.PAR.PotN['Dark Comment'] 
        data["Flat Comment"] = self.PAR.PotN['Flat Comment'] 
        data["Buffer Comment"] = self.PAR.PotN['Buffer Comment'] 
        data["Base Filename"] = self.PAR.PotN['Base Filename'] 
        # ... write the json file
        with open(PotN_file, "w") as jsonFile:
            json.dump(data, jsonFile)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Expose_light
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    def expose_light(self):
        """ to be written """
        self.image_type = "sci"
        ExpTime_ms = float(self.ExpTimeSet.get())*1000
        params = {'Exposure Time': ExpTime_ms, 'CCD Temperature': 2300,
                  'Trigger Mode': 4, 'NofFrames': int(self.Light_NofFrames.get())}

        #are we observing a new target? BCS we may haave lost the WCS solution
        if self.ObjectName.get() !=  self.Previous_ObjectName:
            # yes,  we changed the target
            # therefore we lost the WCS solution
            self.wcs = None
            WCS_global = None
            self.Previous_ObjectName = self.ObjectName.get()

        newfiles = self.expose(params)
        self.handle_light(newfiles)
        # handle multiple files
        superfile = self.combine_files(newfiles)
        self.handle_QuickLook(superfile)
        print("science file created")

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Expose_bias
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    def expose_bias(self):
        """ 
        Sets trigger mode = 5 to tell the SI camera that the shutter has to stay closed
        """
        self.image_type = "bias"
        ExpTime_ms = 0  # float(self.Bias_ExpT.get())*1000
        save_Exp_time = self.ExpTimeSet.get()
        self.ExpTimeSet.set("0")
        params = {'Exposure Time': ExpTime_ms, 'CCD Temperature': 2300,
                  'Trigger Mode': 5, 'NofFrames': int(self.Bias_NofFrames.get())}
        
        # cleanup the directory to remove setimage_ files that may be refreshed
        #self.cleanup_files()
        newfiles = self.expose(params)
        self.handle_bias(newfiles)
        superfile = self.combine_files(newfiles)
        shutil.copy(superfile, os.path.join(self.PAR.QL_images,"superbias.fits"))
        self.handle_QuickLook(superfile)
        self.ExpTimeSet.set(save_Exp_time)
        print("Superbias file created")


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Expose_dark
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


    def expose_dark(self):
        """ 
        Sets trigger mode = 5 to tell the SI camera that the shutter has to stay closed
        """
        self.image_type = "dark"
        ExpTime_ms = float(self.ExpTimeSet.get())*1000
        params = {'Exposure Time': ExpTime_ms, 'CCD Temperature': 2300,
                  'Trigger Mode': 5, 'NofFrames': int(self.Dark_NofFrames.get())}
        
        
        #by default we subtract the bias to create a superbias_s.fits file
        #that will be needed for the quick look
        self.subtract_Bias.set(1)
        
        newfiles = self.expose(params)
        self.handle_dark(newfiles)
        superfile = self.combine_files(newfiles)
        self.handle_QuickLook(superfile)
        print("Superdark_s file created")
        
                
        #by default we subtract the bias to create a superbias_s.fits file
        #that will be needed for the quick look.
        #Here wer RETURN to NO BIAS SUBTRACTION
        self.subtract_Bias.set(0)



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Expose_flat
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


    def expose_flat(self):
        """ to be written """
        self.image_type = "flat"
        ExpTime_ms = float(self.ExpTimeSet.get())*1000
        params = {'Exposure Time': ExpTime_ms, 'CCD Temperature': 2300,
                  'Trigger Mode': 4, 'NofFrames': int(self.Flat_NofFrames.get())}
        #by default we subtract the bias to create a superbias_s.fits file
        #that will be needed for the quick look
        self.subtract_Bias.set(1)
        self.subtract_Dark.set(1)
               
        newfiles = self.expose(params)
        self.handle_flat(newfiles)
        superfile = self.combine_files(newfiles)
        self.handle_QuickLook(superfile)
        print("Superflat file created")

        #by default we subtract the bias to create a superbias_s.fits file
        #that will be needed for the quick look
        self.subtract_Bias.set(0)
        self.subtract_Dark.set(0)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Expose_buffer
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    def expose_buffer(self):
        """ to be written """
        self.image_type = "buff"
        ExpTime_ms = float(self.ExpTimeSet.get())*1000
        params = {'Exposure Time': ExpTime_ms, 'CCD Temperature': 2300,
                  'Trigger Mode': 4, 'NofFrames': int(self.Buffer_NofFrames.get())}

        newfiles = self.expose(params)
        self.handle_buffer(newfiles)
        superfiles = self.combine_files(newfiles)        
        shutil.copy(superfiles, os.path.join(self.PAR.QL_images,"superbuffer.fits"))
        self.handle_QuickLook(superfiles)
        print("Buffer file created")
        # Camera= CCD(dict_params=params)
        
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Expose
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def expose(self, params):
        """ handle the file acquired by the SISI camera"""

        # Prepare the exposure parameers
        # ExpTime_ms = float(self.ExpTime.get())*1000
        # params = {'Exposure Time':ExpTime_ms,'CCD Temperature':2300, 'Trigger Mode': 4}

        # Camera= CCD(dict_params=params)
        #
        # START WITH DEFINITIONS
        self.current_night_dir_filenames = []
        Camera = Class_Camera(dict_params=params)
        Camera.exp_progbar = self.exp_progbar
        Camera.exp_progbar_style = self.exp_progbar_style
        Camera.var_exp = self.var_perc_exp_done
        Camera.read_progbar = self.readout_progbar
        Camera.read_progbar_style = self.readout_progbar_style
        Camera.var_read = self.var_perc_read_done


        # Expose
        IP = self.PAR.IP_dict['IP_CCD']
        [host, port] = IP.split(":")
#        PCM.initialize(address=host, port=int(port))
        imtype = self.image_type
        if self.image_type == "sci":
            imtype = "sci_{}".format(self.FW_filter.get())
            self.obj_type = "SCI"
        elif self.image_type == "bias":
            imtype = "bias"
            self.obj_type = "BIAS"
        elif self.image_type == "buff":
            imtype = "Buff"
            self.obj_type = "BUFF"
        elif self.image_type == "flat":
            imtype = "flat_{}".format(self.FW_filter.get())
            self.obj_type = "FLAT"
        elif self.image_type == "dark":
            self.obj_type = "DARK"
#            imtype = "dark_{}s".format(self.ExpTime.get())
            imtype = "dark_{}s".format(float(self.ExpTimeSet.get())) # e.g. 'dark_0.01s'

        #PREPARE THE FILENAME OF THE IMAGE
        #Remove spaces from Base Filename string
        if self.out_fname.get().strip() == "":
            basename = self.out_fname.get()
        basename = "_"+self.out_fname.get()
        out_fname = os.path.join(self.fits_dir, imtype+basename)   # e,g, '/Users/samos_dev/GitHub/SISI_images/SAMOS_20231003/dark_0.01s_771nm'
        # new_fname = "{}_{:04n}.fits".format(basename,int(self.entry_out_fnumber.get()))

        # these extra 2 parameters in Camera.expose are to save copies of the
        # file to the ObsNight directory
        newfiles = Camera.expose(night_dir_basename=out_fname,
                      start_fnumber=self.entry_out_fnumber)  # host, port=int(port))
        self.reset_progress_bars()
        
        # THE LAST ARRIVED FILE is latest_file
#        fits_dir = SF.read_fits_folder()
#        print(fits_dir)
#        list_of_files = glob.glob(
#             os.path.join(fits_dir,"*.fits") )  
#        latest_file = max(list_of_files, key=os.path.getctime)
#        print(latest_file)
#        self.fullpath_FITSfilename = latest_file # self.fits_image
        
        return newfiles


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Handle files: sets or single?
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


    def handle_light(self,newfiles):
        """

        Parameters
        ----------
        newfiles : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
#        Camera = Class_Camera(dict_params=params)
        for fname in newfiles:
            
            #FIX THE HEADERS
            hdul = fits.open(fname)
            data = hdul[0].data
            original_header = hdul[0].header

            expTime = params['Exposure Time']/1000
            main_fits_header.set_param("expTime", expTime)

            main_fits_header.set_param("filter", self.FW_filter.get())
    #        main_fits_header.set_param("filtpos", self.selected_FW_pos.get())

            main_fits_header.set_param("grating", self.Grating_Optioned.get())

            main_fits_header.set_param(
                "filename", os.path.split(fname)[1])
            main_fits_header.set_param(
                "filedir", os.path.split(fname)[0])

            main_fits_header.set_param("observers", self.names_var.get())
            main_fits_header.set_param("programID", self.program_var.get())
            main_fits_header.set_param("telOperators", self.TO_var.get())
            main_fits_header.set_param("objname", self.ObjectName.get())
            main_fits_header.set_param("obstype", self.obj_type)
            # reset some parameters that may have been changed from previous exposures.
            main_fits_header.set_param("combined", "F")
            main_fits_header.set_param("ncombined", 0)
            main_fits_header.create_fits_header(original_header)
            if self.wcs_exist is True:
                main_fits_header.add_astrometric_fits_keywords(original_header)
    
            # ADD THE DMD MAP HEADER, IF ANY
            try:
                # main_fits_header.set_param("gridfnam", params["DMDMAP"])
                print("DMDMAP is ", main_fits_header.dmdmap)
            except:
                print("no slit grid loaded")   
            #try:
            #    DMD.current_dmd_shape
            #except NameError:
            #    DMD.current_dmd_shape = None
            #if DMD.current_dmd_shape is not None:
            #    dmd_hdu = self.create_dmd_pattern_hdu(
            #        main_fits_header.output_header)
            #    hdul.append(dmd_hdu)
            try:
                dmd_hdu = self.create_dmd_pattern_hdu(
                    main_fits_header.output_header)
                hdul.append(dmd_hdu)
            except:
                print("no DMD mask")
            
            
            print(main_fits_header.output_header)
    
            # QUICK LOOK IMAGE     
            self.fits_image = os.path.join(
                 self.PAR.QL_images, "newimage.fits")
            
            # update header for new filename/filepath
            main_fits_header.create_fits_header(main_fits_header.output_header)
            hdul[0].header = main_fits_header.output_header
            hdulist = fits.HDUList(hdus=[hdul[0]])
            hdul.close()
    
            # self.Display(fits_image_converted)
            self.fitsimage.rotate(self.PAR.Ginga_PA)  
            self.Display(self.fits_image)                   # '/Users/samos_dev/GitHub/SAMOS_NEWGUI/SAMOS_QL_images/newimage.fit'

            #create fits header for final image
            main_fits_header.create_fits_header(main_fits_header.output_header)

            #update the final image
            #fits.writeto(fname, data,
            #                header=main_fits_header.output_header, overwrite=True)

            # 
            self.most_recent_img_fullpath = fname  # e.g. dark_0s_Test_0004.fits
            print("Saved new file as {}".format(fname))
            # self.entry_out_fnumber.invoke("buttonup")
            hdulist.close()

#            print("Cleanup: deleting original fits file")
#            CCD.delete_fitsfile()



    def handle_bias(self,newfiles):
        """

        Parameters
        ----------
        newfiles : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
#        Camera = Class_Camera(dict_params=params)
        for fname in newfiles:
            
            #FIX THE HEADERS
            hdul = fits.open(fname)
            data = hdul[0].data
            original_header = hdul[0].header

            expTime = params['Exposure Time']/1000
            main_fits_header.set_param("expTime", expTime)

            main_fits_header.set_param(
                "filename", os.path.split(fname)[1])
            main_fits_header.set_param(
                "filedir", os.path.split(fname)[0])

            main_fits_header.set_param("observers", self.names_var.get())
            main_fits_header.set_param("programID", self.program_var.get())
            main_fits_header.set_param("telOperators", self.TO_var.get())
            main_fits_header.set_param("objname", self.ObjectName.get())
            main_fits_header.set_param("obstype", self.obj_type)
            # reset some parameters that may have been changed from previous exposures.
            main_fits_header.set_param("combined", "F")
            main_fits_header.set_param("ncombined", 0)
            main_fits_header.create_fits_header(original_header)
    
            
            
            print(main_fits_header.output_header)
    
            # QUICK LOOK IMAGE     
            self.fits_image = os.path.join(
                 self.PAR.QL_images, "newimage.fits")
            
            # update header for new filename/filepath
            main_fits_header.create_fits_header(main_fits_header.output_header)
            hdul[0].header = main_fits_header.output_header
            hdulist = fits.HDUList(hdus=[hdul[0]])
            hdul.close()
    
            # self.Display(fits_image_converted)
            self.fitsimage.rotate(self.PAR.Ginga_PA)  
            self.Display(self.fits_image)                   # '/Users/samos_dev/GitHub/SAMOS_NEWGUI/SAMOS_QL_images/newimage.fit'
            #create fits header for final image
            main_fits_header.create_fits_header(main_fits_header.output_header)

            #update the final image
            #fits.writeto(fname, data,
            #                header=main_fits_header.output_header, overwrite=True)

            # 
            self.most_recent_img_fullpath = fname  # e.g. dark_0s_Test_0004.fits
            print("Saved new file as {}".format(fname))
            # self.entry_out_fnumber.invoke("buttonup")
            hdulist.close()

#            print("Cleanup: deleting original fits file")
#            CCD.delete_fitsfile()

    def handle_dark(self,newfiles):
        """

        Parameters
        ----------
        newfiles : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
#        Camera = Class_Camera(dict_params=params)
        superdark_s = np.zeros( (1032,1056) )
        for fname in newfiles:
            
            #FIX THE HEADERS
            hdul = fits.open(fname)
            data = hdul[0].data
            original_header = hdul[0].header

            expTime = params['Exposure Time']/1000
            main_fits_header.set_param("expTime", expTime)

            main_fits_header.set_param(
                "filename", os.path.split(fname)[1])
            main_fits_header.set_param(
                "filedir", os.path.split(fname)[0])

            main_fits_header.set_param("observers", self.names_var.get())
            main_fits_header.set_param("programID", self.program_var.get())
            main_fits_header.set_param("telOperators", self.TO_var.get())
            main_fits_header.set_param("objname", self.ObjectName.get())
            main_fits_header.set_param("obstype", self.obj_type)
            # reset some parameters that may have been changed from previous exposures.
            main_fits_header.set_param("combined", "F")
            main_fits_header.set_param("ncombined", 0)
            main_fits_header.create_fits_header(original_header)
    
            print(main_fits_header.output_header)
    
            # QUICK LOOK IMAGE     
            self.fits_image = os.path.join(
                 self.PAR.QL_images, "newimage.fits")
            
            # update header for new filename/filepath
            main_fits_header.create_fits_header(main_fits_header.output_header)
            hdul[0].header = main_fits_header.output_header
            hdulist = fits.HDUList(hdus=[hdul[0]])
            hdul.close()
    
            # self.Display(fits_image_converted)
            self.fitsimage.rotate(self.PAR.Ginga_PA)  
            self.Display(self.fits_image)                   # '/Users/samos_dev/GitHub/SAMOS_NEWGUI/SAMOS_QL_images/newimage.fit'

            #create fits header for final image
            main_fits_header.create_fits_header(main_fits_header.output_header)

            #update the final image
            #fits.writeto(fname, data,
            #                header=main_fits_header.output_header, overwrite=True)

            # 
            self.most_recent_img_fullpath = fname  # e.g. dark_0s_Test_0004.fits
            print("Saved new file as {}".format(fname))
            # self.entry_out_fnumber.invoke("buttonup")
            hdulist.close()
            
            #  PART 2: CREATE SUPERDARK_S

            """ 
            We need to handle the dark because it may have been taken for an exposure time
            different than the one used for the science image
            """
               
            #EXTRACT THE EXPOSURE TIME(S)
        # ... with a given exposure time
            exptime = original_header['PARAM2']
#                hdu_dark.close()

            # if a bias file has also been taken...
            # make sure to use the bias that was taken for this observation run
            bias_file = os.path.join(
                            self.PAR.QL_images, "superbias.fits")
            try:
                #bias_file = glob.glob(
                #    os.path.join(self.fits_dir,"superbias.fits"))[0]
                hdu_bias = fits.open(bias_file)
                bias = hdu_bias[0].data
                hdu_bias.close()
            except IndexError:
                bias = np.zeros_like(data)
            if self.subtract_Bias.get() == 1:
                dark_bias = data-bias
                main_fits_header.output_header.set(
                    "MSTRBIAS", bias_file, "Master Bias file if corrected")
            else:
                dark_bias = data
                
            superdark_s += dark_bias

        dark_bias / len(newfiles)
        dark_sec = dark_bias / (exptime/1000)
        hdr_out = copy.deepcopy(main_fits_header.output_header)
        hdr_out['EXPTIME'] = 1  #set the exposure time of this file to 1s

        dir_hdul1 = os.path.join(
            self.PAR.QL_images, "superdark_s.fits")
        fits.writeto(dir_hdul1, dark_sec, hdr_out, overwrite=True)

        
    def handle_flat(self, newfiles):
        """

        Parameters
        ----------
        newfiles : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
#        Camera = Class_Camera(dict_params=params)
        running_flat = np.zeros( (1032,1056) )
        for fname in newfiles:
            
            #FIX THE HEADERS
            hdul = fits.open(fname)
            data = hdul[0].data
            original_header = hdul[0].header

            expTime = params['Exposure Time']/1000
            main_fits_header.set_param("expTime", expTime)
            main_fits_header.set_param("filter", self.FW_filter.get())
    #        main_fits_header.set_param("filtpos", self.selected_FW_pos.get())

            main_fits_header.set_param(
                "filename", os.path.split(fname)[1])
            main_fits_header.set_param(
                "filedir", os.path.split(fname)[0])

            main_fits_header.set_param("observers", self.names_var.get())
            main_fits_header.set_param("programID", self.program_var.get())
            main_fits_header.set_param("telOperators", self.TO_var.get())
            main_fits_header.set_param("objname", self.ObjectName.get())
            main_fits_header.set_param("obstype", self.obj_type)
            # reset some parameters that may have been changed from previous exposures.
            main_fits_header.set_param("combined", "F")
            main_fits_header.set_param("ncombined", 0)
            main_fits_header.create_fits_header(original_header)
    
            print(main_fits_header.output_header)
    
            # QUICK LOOK IMAGE     
            self.fits_image = os.path.join(
                 self.PAR.QL_images, "newimage.fits")
            
            # update header for new filename/filepath
            main_fits_header.create_fits_header(main_fits_header.output_header)
            hdul[0].header = main_fits_header.output_header
            hdulist = fits.HDUList(hdus=[hdul[0]])
            hdul.close()
    
            # self.Display(fits_image_converted)
            self.fitsimage.rotate(self.PAR.Ginga_PA)  
            self.Display(self.fits_image)                   # '/Users/samos_dev/GitHub/SAMOS_NEWGUI/SAMOS_QL_images/newimage.fit'

            #create fits header for final image
            main_fits_header.create_fits_header(main_fits_header.output_header)

            #update the final image
            #fits.writeto(fname, data,
            #                header=main_fits_header.output_header, overwrite=True)

            # 
            self.most_recent_img_fullpath = fname  # e.g. dark_0s_Test_0004.fits
            print("Saved new file as {}".format(fname))
            # self.entry_out_fnumber.invoke("buttonup")
            hdulist.close()
            
            #  PART 2: CREATE SUPERFLAT
            """ 
            we need to handle the flat because it may have been taken 
            for a filter different than the one of the science image 
            """

            # if a bias file has also been taken...
            # make sure to use the bias that was taken for this observation run
            dark_s_file = os.path.join(
                            self.PAR.QL_images, "superdark_s.fits")

            try:
                bias_file = glob.glob(
                    os.path.join(self.PAR.QL_images,"superbias.fits"))[0]
                hdu_bias = fits.open(bias_file)
                bias = hdu_bias[0].data
                hdu_bias.close()
            except IndexError:
                bias = np.zeros_like(flat)

            try:
                dark_s_file = glob.glob(
                    os.path.join(self.PAR.QL_images,"superdark_s.fits"))[0]
                hdu_dark_s = fits.open(dark_s_file)
                dark_s = hdu_dark_s[0].data
                hdu_dark_s.close()
            except IndexError:
                dark_s = np.zeros_like(flat)

            # the bias must be subtracted from the flat
            if self.subtract_Bias.get() == 1:
                flat_bias = data-bias
                main_fits_header.output_header.set(
                    "MSTRBIAS", bias_file, "Master Bias file if corrected")   
            else:
                flat_bias = flat

            if self.subtract_Dark.get() == 1:
                # the dark current rate is multiplied by the exposure time of te flat
                # and subtracted off if requested
                # PARAM2 exposure time is in ms, so /1000 to get it in seconds
                # Also scale the dark if exposure times are different.
                dark = dark_s * float(self.ExpTimeSet.get())
                main_fits_header.output_header.set(
                    "MSTRDARK", dark_s_file, "Master Dark file if corrected")
                flat_dark = flat_bias - dark
            else:
                flat_dark = flat_bias

            # finally the flat is normalized to median=1
            running_flat += flat_dark

        median_running_flat = np.median(running_flat)
        superflat = running_flat / median_running_flat 

        hdr_out = copy.deepcopy(main_fits_header.output_header)


        dir_hdul1 = os.path.join(
            self.PAR.QL_images, "superflat_"+self.FW_filter.get()+".fits")
#        hdulist.writeto(os.path.join(local_dir,"SAMOS_QL_images","superflat_"+self.FW_filter.get()+"_norm.fits"),overwrite=True)
        # fits.writeto( os.path.join(local_dir,"SAMOS_QL_images","superflat_"+self.FW_filter.get()+"_norm.fits"),flat_norm,hdr,overwrite=True)

#        main_fits_header.create_fits_header(hdr)
        pr_hdu = fits.PrimaryHDU(superflat, main_fits_header.output_header)
        hdulist1 = fits.HDUList(hdus=[pr_hdu])


        hdulist1.writeto(dir_hdul1, overwrite=True)
#        hdulist2.writeto(dir_hdul2, overwrite=True)

    def handle_buffer(self,newfiles):
        """

        Parameters
        ----------
        newfiles : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
#        Camera = Class_Camera(dict_params=params)
        for fname in newfiles:
            
            #FIX THE HEADERS
            hdul = fits.open(fname)
            data = hdul[0].data
            original_header = hdul[0].header

            expTime = params['Exposure Time']/1000
            main_fits_header.set_param("expTime", expTime)
            main_fits_header.set_param("filter", self.FW_filter.get())

            main_fits_header.set_param(
                "filename", os.path.split(fname)[1])
            main_fits_header.set_param(
                "filedir", os.path.split(fname)[0])

            main_fits_header.set_param("observers", self.names_var.get())
            main_fits_header.set_param("programID", self.program_var.get())
            main_fits_header.set_param("telOperators", self.TO_var.get())
            main_fits_header.set_param("objname", self.ObjectName.get())
            main_fits_header.set_param("obstype", self.obj_type)
            # reset some parameters that may have been changed from previous exposures.
            main_fits_header.set_param("combined", "F")
            main_fits_header.set_param("ncombined", 0)
            main_fits_header.create_fits_header(original_header)
    
           
            
            print(main_fits_header.output_header)
    
            # QUICK LOOK IMAGE     
            self.fits_image = os.path.join(
                 self.PAR.QL_images, "newimage.fits")
            
            # update header for new filename/filepath
            main_fits_header.create_fits_header(main_fits_header.output_header)
            hdul[0].header = main_fits_header.output_header
            hdulist = fits.HDUList(hdus=[hdul[0]])
            hdul.close()
    
            # self.Display(fits_image_converted)
            self.fitsimage.rotate(self.PAR.Ginga_PA)  
            self.Display(self.fits_image)                   # '/Users/samos_dev/GitHub/SAMOS_NEWGUI/SAMOS_QL_images/newimage.fit'
            #create fits header for final image
            main_fits_header.create_fits_header(main_fits_header.output_header)

            #update the final image
            #fits.writeto(fname, data,
            #                header=main_fits_header.output_header, overwrite=True)

            # 
            self.most_recent_img_fullpath = fname  # e.g. dark_0s_Test_0004.fits
            print("Saved new file as {}".format(fname))
            # self.entry_out_fnumber.invoke("buttonup")
            hdulist.close()

#            print("Cleanup: deleting original fits file")
#            CCD.delete_fitsfile()


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# # Handle files: sets or single?
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def combine_files(self,files):
        """
         this procedure runs after CCD.expose()
         to handle the decision of saving all single files or just the averages
         """
        # We may have received just one (setimage_0.fit) or multiple images; 
        # we start building the list of filename        
        #files = glob.glob(
        #    os.path.join(self.PAR.QL_images, "setimage_*.fit") )
        
        #files = self.current_night_dir_filenames           #e.g. files: =>  '/Users/samos_dev/GitHub/SISI_images/SAMOS_20231003/dark_0.01s_771nm_0033.fits'
        
        #nothing to combine if there is only one new file
        if len(files) == 1:
            superfile = files[0]
            return superfile
        
        superfile_cube = np.zeros((1032, 1056, len(files)))  # note y,x,z
        
        img_number = self.start_combo_obj_number-1

        #create a header for the dmd pattern 
        dmd_hdu = None
        if DMD.current_dmd_shape is not None:
            dmd_hdu = self.create_dmd_pattern_hdu(
                                main_fits_header.output_header)
        #loop through the files    
        for i in range(len(files)):
            img_number += 1
            print(files[i])
            with fits.open(files[i]) as hdu:

                # search string for image
                # glob.glob(night_dir_fname_search)[0]
                #night_dir_fname = files[i]              # e.g. night_dir_fname: => '/Users/samos_dev/GitHub/SISI_images/SAMOS_20231003/dark_0.01s_771nm_0033.fits'

                #night_hdulist = fits.open(night_dir_fname)
                #night_hdulist[0].header = main_fits_header.output_header
                hdu[0].header = main_fits_header.output_header
                if dmd_hdu is not None:
                    hdu.append(dmd_hdu)
                    
                # store the data array in the supercube
                superfile_cube[:, :, i] = hdu[0].data
                superfile_header = hdu[0].header
                
                # do you want to save the running file?
                # YES
                if self.var_Light_saveall.get() == 1 or \
                   self.var_Bias_saveall.get() == 1 or \
                   self.var_Dark_saveall.get() == 1 or \
                   self.var_Flat_saveall.get() == 1 or \
                   self.var_Buffer_saveall.get() == 1:
                   # save every single frame
                   # os.rename(files[i], os.path.join(
                   #     self.PAR.QL_images+self.image_type+"_"+self.FW_filter.get()+'_'+str(i)+".fits"))
                    # os.rename(files[i],os.path.join(self.fits_dir,self.image_type+"_"+self.FW_filter.get()+'_'+str(i)+".fits"))
                    # self.entry_out_fnumber.invoke("buttonup")
                    # night_hdulist.writeto(night_dir_fname, overwrite=True)
                    # night_hdulist.close()
                    hdu_copy = copy.deepcopy(hdu)
                    hdu.close()
                    os.remove(files[i])
                    hdu_copy.writeto(files[i], overwrite=True)
                    hdu_copy.close()
                #NO
                else: #close and kill the running file
                    hdu.close()
                    os.remove(files[i])
                    # also remove the file that was put in the Night directory
                    #try:
                    #    os.remove(os.path.join(self.fits_dir, files[i]))
                    #except FileNotFoundError:
                    #    pass
            #superfile_header = hdu[0].header
            #hdu.close()             
        #  => HERE WE DO THE COADD OF THE DATA            
        superfile_data = superfile_cube.mean(axis=2)
        
        #superfile_header = hdu[0].header
        
        
        if self.image_type == "sci":
            self.obj_type = "SCI"
        elif self.image_type == "buff":
            self.obj_type = "BUFF"
        elif self.image_type == "bias":
            self.obj_type = "BIAS"
        elif self.image_type == "dark":
            self.obj_type = "DARK"
        elif self.image_type == "flat":
            self.obj_type = "FLAT"

        #ADD FILTERNAME if we are COADDING science or flat images        
        if self.image_type == "sci" or self.image_type == "flat":
            superfile_dirname = os.path.join(
                self.PAR.QL_images, self.image_type+"_"+self.FW_filter.get()+"_coadd.fits")
            # fits.writeto(,superfile_data,supefrfile_header,overwrite=True)
        else: 
            superfile_dirname = os.path.join(
                self.PAR.QL_images, self.image_type+"_coadd.fits")   # e.g. superfile_name:  => '/Users/samos_dev/GitHub/SAMOS_NEWGUI/SAMOS_QL_images/dark_coadd.fits'

        # save combined file in Night directory
        # self.entry_out_fnumber.invoke("buttonup")
        second_superfile_name0 = os.path.split(superfile_dirname)[1][:-11]  
        if self.image_type == "dark":
            second_superfile_name0 = second_superfile_name0 + \
                "_{}s".format(self.ExpTimeSet.get())  # e,g, second_superfile_name0: => 'dark_0.01s'
        
        #remove spaces from basename, and add a "_
        if self.out_fname.get().strip(" ") == "":
            basename = self.out_fname.get()
        basename = "_"+self.out_fname.get()

        """
        we don't want to use here the current file counter int(self.entry_out_fnumber.get())
        because it has been already pushed up by +1 count
        Therefore, we read it and take down 1 count for the supersci file
        """
        current_counter = int(self.entry_out_fnumber.get())
        previous_counter = current_counter - 1

        second_superfile_name = "{}{}_{:04n}_coadd.fits".format(second_superfile_name0, basename,
                                                        #int(self.entry_out_fnumber.get()))
                                                        previous_counter)
        second_superfile_dirname = os.path.join(
            self.fits_dir, second_superfile_name) # e.g. '/Users/samos_dev/GitHub/SISI_images/SAMOS_20231003/dark_0.01s_771nm_0038_coadd.fits'
        main_fits_header.set_param("filedir", self.fits_dir)
        main_fits_header.set_param("filename", second_superfile_dirname)
        main_fits_header.set_param("combined", "T")
        main_fits_header.set_param("ncombined", len(files))
        main_fits_header.set_param("obstype", self.obj_type)
        main_fits_header.create_fits_header(superfile_header)
        print(second_superfile_dirname)

        #super_hdu1 = fits.PrimaryHDU(superfile_data, superfile_header)
        super_hdu2 = fits.PrimaryHDU(superfile_data, main_fits_header.output_header)

        #hdulist1 = fits.HDUList(hdus=[super_hdu1])
        # second file with updated fits header
        hdulist2 = fits.HDUList(hdus=[super_hdu2])
        if dmd_hdu is not None:
        #    hdulist1.append(dmd_hdu)
            hdulist2.append(dmd_hdu)

        #hdulist1.writeto(superfile_dirname, overwrite=True)
        hdulist2.writeto(second_superfile_dirname, overwrite=True)
        # fits.writeto(superfile_name,superfile_data,superfile_header,overwrite=True)
        # fits.writeto(os.path.join(self.fits_dir,second_superfile_name),superfile,
        #             main_fits_header.output_header,overwrite=True)
        # self.entry_out_fnumber.invoke("buttonup")
        combined_file = second_superfile_dirname
        return combined_file

    def cleanup_files(self):
        """ to be written """
        file_names = os.path.join(
            self.PAR.QL_images, self.image_type+"_*.fits")
        files = glob.glob(file_names)
        for i in range(len(files)):
            os.remove(files[i])


    def handle_QuickLook(self,QLfile):
        """ handle_light frame for Quick Look display, applying bias, dark and flat if necessary """
        # last received image
#        light_file = os.path.join(self.PAR.QL_images, "newimage.fit")
        light_file = QLfile
        


        # last saved buffer
        buffer_file = os.path.join(
            self.PAR.QL_images, "superbuffer.fits")
        
        

        hdu_light = fits.open(light_file)
        light = hdu_light[0].data
        hdu_light.close()

#        hdu_bias = fits.open(bias_file)
#        bias = hdu_bias[0].data
#        hdu_bias.close()
#       Revised version by Dana below where we first check for a superbias

#        hdu_dark_s = fits.open(dark_s_file)
#        dark_s = hdu_dark_s[0].data
#        hdu_dark_s.close()
#       Revised version by Dana below where we check for a superdark

#        hdu_flat = fits.open(flat_file)
#        flat = hdu_flat[0].data
#        hdu_flat.close()
#       Revised version by Dana below where we check for a superdark


        hdr = hdu_light[0].header
        exptime = hdr['PARAM2']
        # this exptime is in ms

# HANDLE BIAS SUBTRACTION, IF REQUESTED
        if self.subtract_Bias.get() == 1:
            # last bias taken
#            bias_file = os.path.join(
#                self.PAR.QL_images, "superbias.fits")
            try:
                bias_file = glob.glob(os.path.join(self.PAR.QL_images,"superbias.fits"))[0]
                hdu_bias = fits.open(bias_file)
                bias = hdu_bias[0].data
                hdu_bias.close()
            except IndexError:
                bias = np.zeros_like(light)
                bias_file = ''
            light_bias = light-bias
            main_fits_header.output_header.set(
                "MSTRBIAS", bias_file, "Master Bias file if corrected")
        else:
            light_bias = light

# HANDLE DARK SUBTRACTION, IF REQUESTED
        if self.subtract_Dark.get() == 1:
            # last dark taken, normalized to count/s
#            dark_s_file = os.path.join(
#                self.PAR.QL_images, "superdark_s.fits")
            try:
                dark_s_files = glob.glob(
                    os.path.join(self.PAR.QL_images,"superdark_s.fits"))[0]
                if len(dark_s_files) > 1:
                    dark_s_file = self.find_closest_dark()
                elif len(dark_s_files) == 1:
                    dark_s_file = dark_s_files[0]
                hdu_dark_s = fits.open(dark_s_file)
                dark_s = hdu_dark_s[0].data
                hdu_dark_s.close()
            except (IndexError, ValueError):
                dark_s = np.zeros_like(light)
                dark_s_file = ''
            # if different exposure times between Light and Dark, scale the dark
            light_bias_dark = light_bias - dark_s * \
                (float(self.ExpTimeSet.get())/(exptime*1000))
            main_fits_header.output_header.set(
                "MSTRDARK", dark_s_file, "Master Dark file if corrected")
        else:
            light_bias_dark = light_bias

# HANDLE FLAT DIVISION, IF REQUESTED
        if self.divide_Flat.get() == 1:
            try:
                flat_file = glob.glob(
                    os.path.join(self.PAR.QL_images,"superflat_{}*.fits").format(self.FW_filter.get()))[0]
                hdu_flat = fits.open(flat_file)
                flat = hdu_flat[0].data
                hdu_flat.close()
                print("found flat file ", flat_file)
            except IndexError:
                flat = np.zeros_like(light) + 1  #set flat field to 1
                flat_file = ''
                print("\n*** No Flat file found for the current bandpass *** \n FLAT CORRECTION NOT PERFORMED \n ")
            light_bias_dark_flat = np.divide(light_bias_dark, flat)
            main_fits_header.output_header.set(
                "MSTRFLAT", flat_file, "Master Flat file if corrected")
        else:
            light_bias_dark_flat = light_bias_dark

# HANDLE BUFFER SUBTRACTION, IF REQUESTED
        if self.subtract_Buffer.get() == 1:
#            hdu_buffer = fits.open(buffer_file)
#            buffer = hdu_buffer[0].data
#            hdu_buffer.close()
            try:
                buffer_file = glob.glob(
                    os.path.join(self.PAR.QL_images,"superbuffer.fits"))[0]
                hdu_buffer = fits.open(buffer_file)
                buffer = hdu_buffer[0].data
                hdu_buffer.close()
            except IndexError:
                buffer = np.zeros_like(light)
                buffer_file = ''
            light_bias_dark_flat_buffer = light_bias_dark_flat - buffer
            main_fits_header.output_header.set(
                "MSTRFLAT", buffer_file, "Master Flat file if corrected")
        else:
            light_bias_dark_flat_buffer = light_bias_dark_flat

        fits_image = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
 
        if self.image_type == "sci":
            self.obj_type = "SCI"
            # I am adding the QL suffix to indicate that this is an image processed for QL
            imtype = "Sci_{}".format(self.FW_filter.get())
        elif self.image_type == "bias":
            self.obj_type = "BIAS"
            imtype = "bias"
        elif self.image_type == "buff":
            self.obj_type = "BUFF"
            imtype = "buff"
        elif self.image_type == "flat":
            self.obj_type = "FLAT"
            imtype = "flat_{}".format(self.FW_filter.get())
        elif self.image_type == "dark":
            #            imtype = "dark_{}s".format(self.ExpTime.get())
            self.obj_type = "DARK"
            imtype = "dark_{}s".format(self.ExpTimeSet.get())

#        if self.out_fname.get().strip(" ") == "":
#            basename = self.out_fname.get()
#        else:
#            basename = "_"+self.out_fname.get()
#        out_fname = os.path.join(self.fits_dir, imtype+basename)

#        main_fits_header.set_param("obstype", self.obj_type)
#        main_fits_header.set_param("filterpos", self.selected_FW_pos.get())

        main_fits_header.create_fits_header(hdr)

        """
        The following will be implemented when SAMOS is at SOAR.
        It adds the TCS info to the header.

        # take the output info and return as a dictionary
        TCS_dict = Class_SOAR_Page.SOAR_Page.infoa()
        main_fits_header.output_header.update(TCS_dict)
        """
        
        #
        pr_hdu = fits.PrimaryHDU(
            light_bias_dark_flat_buffer, main_fits_header.output_header)
        hdulist = fits.HDUList([pr_hdu])
        dmd_hdu = None
        if DMD.current_dmd_shape is not None:
            dmd_hdu = self.create_dmd_pattern_hdu(
                main_fits_header.output_header)
            hdulist.append(dmd_hdu)

        #hdulist.writeto(fits_image, overwrite=True)

        main_fits_header.create_fits_header(main_fits_header.output_header)
#        if self.subtract_Buffer.get() == 1:
#            light_buffer = light-buffer
#            hdulist = fits.HDUList(
#                [fits.PrimaryHDU(light_buffer, main_fits_header.output_header)])
#            if dmd_hdu is not None:
#                hdulist.append(dmd_hdu)
#            # fits.writeto(fits_image,light_buffer,
#            #             main_fits_header.output_header,overwrite=True)
#            hdulist.writeto(fits_image, overwrite=True)
#            self.Display(fits_image)
        # WRITES TO => newimage_ql.fits
        fits.writeto(fits_image,light_bias_dark_flat_buffer,
                     main_fits_header.output_header,overwrite=True)
        self.fitsimage.rotate(self.PAR.Ginga_PA)  
        self.Display(fits_image)
        
            

#        hdulist.writeto(fits_image, overwrite=True)

        # Save a copy of the image to store in the Obs Night Directory under
        # a more informative filename
        #fname = self.current_night_dir_filenames[-1]
        fname = QLfile
        #
        # ADD the QL Prefix to indicate that this file has been processed for Quick Look
        path, file = os.path.split(fname)
        QL_file = file[:-5] + '_QL.fits'
#        QL_fname = os.path.join(self.PAR.QL_images, QL_file)
        QL_fname = os.path.join(path,"QL_images", QL_file)
        # done
        #
#        main_fits_header.set_param("filedir", self.fits_dir)
        data_dir = self.fits_dir.replace(parent_dir,"")
        main_fits_header.set_param("filedir", data_dir)
        #main_fits_header.set_param("filename", fname)
        file_name = fname.replace(self.fits_dir,"")[1:]
        main_fits_header.set_param("filename", fname)
        
        main_fits_header.set_param("obstype", self.obj_type)

        main_fits_header.create_fits_header(main_fits_header.output_header)
        hdulist[0].header = main_fits_header.output_header
        hdulist.writeto(QL_fname, overwrite=True)
#        fits.writeto(full_fpath, light_dark_bias, main_fits_header.output_header,
#                     overwrite=True)

#        self.entry_out_fnumber.invoke("buttonup")
        


    def change_acq_type(self, event):
        """
        When the acquisition tab is changed
        """

        image_type = self.tabControl.tab(self.tabControl.select(), "text")
        self.var_acq_type.set(image_type)

    def find_closest_dark(self):
        """
        In any of the self.handle_IMG methods, when the exposure time of the
        image you want to correct does not match any superdark,
        find the one with the closest exposure time.

        Returns
        -------
        Filename (and inc. path) for closest superdark.

        """
        superdark_list = glob.glob(os.path.join(
            self.fits_dir, "superdark_*.fits"))
        superdark_times = np.array([os.path.split(darkf)[1].split(
            "_")[1].strip("s") for darkf in superdark_list]).astype(float)
        i = np.argmin(np.abs(superdark_times-float(self.ExpTimeSet.get())))

        return superdark_list[i]


    def create_dmd_pattern_hdu(self, primary_header):
        """
        If the DMD has a loaded pattern, create an image extension
        to add to the output file.
        """
        main_fits_header.set_param("extensions", True)
        dmd_hdu = fits.ImageHDU(DMD.current_dmd_shape)
        # check if pattern is DMD map or a grid pattern
        dmd_hdu.header["FILENAME"] = primary_header["FILENAME"]
        dmd_hdu.header["FILEDIR"] = primary_header["FILEDIR"]

        if 'unavail' in primary_header["DMDMAP"]:
            dmd_hdu.header["DMDMAP"] = primary_header["DMDMAP"]

        elif 'unavail' in primary_header["GRIDFNAM"]:
            dmd_hdu.header["GRIDFNAM"] = primary_header["GRIDFNAM"]

        main_fits_header.create_fits_header(primary_header)
        return dmd_hdu

    def Display(self, imagefile):
        """ to be written """
#        image = load_data(fits_image_converted, logger=self.logger)

        # AstroImage object of ginga.AstroImage module
        self.AstroImage = load_data(imagefile, logger=self.logger)

        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)

    def reset_progress_bars(self):

        self.exp_progbar["value"] = 0
        self.var_perc_exp_done.set(0)
        self.exp_progbar_style.configure('text.Horizontal.TProgressbar',
                                         text='Expose {:g} %'.format(self.var_perc_exp_done.get()))
        self.readout_progbar["value"] = 0
        self.var_perc_read_done.set(0)
        self.readout_progbar_style.configure('text.Horizontal.RProgressbar',
                                             text='Readout {:g} %'.format(self.var_perc_read_done.get()))

    def load_existing_file(self):
        """ to be written """
        FITSfiledir = os.path.join(self.PAR.QL_images)
        self.last_fits_file_dialog = filedialog.askopenfilename(initialdir=self.fits_dir,                                                          title="Select a File",
                                                                 filetypes=(("fits files",
                                                                             "*.fits"),
                                                                            ("all files",
                                                                             "*.*")))
        self.fits_image_ql  = self.last_fits_file_dialog

        #self.fullpath_FITSfilename = os.path.join(
        #    self.fits_dir, self.loaded_fits_file)
        # './fits_image/newimage_ql.fits'
        self.AstroImage = load_data(
            self.last_fits_file_dialog, logger=self.logger)
        # AstroImage object of ginga.AstroImage module

        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)
#        self.root.title(self.fullpath_FITSfilename)

        #return self.filename_regfile_RADEC

    def send_RADEC_to_SOAR(self):
        pass

    def Query_Survey(self):
        """ to be written """
        self.clear_canvas()
        from astroquery.hips2fits import hips2fits
        Survey = self.Survey_selected.get()

        if Survey == "SkyMapper":
            try:
                self.SkyMapper_query()
                #GuideStarPage.SkyMapper_query_GuideStar(self)
            except:
                print("\n Sky mapper image server is down \n")
            return

        elif Survey == "SDSS":
            self.SDSS_query()
            return
            
          

        elif Survey == "PanSTARRS/DR1/":
            try:
                self.PanStarrs_query()
            except:
                print("\n PanStarrs image server is down \n")
            return

        else:
            print("Survey selected: ",Survey,'\n')
            """
            coord = SkyCoord(self.string_RA.get()+'  ' +
                         self.string_DEC.get(), unit=(u.deg, u.deg), frame='fk5')
            # coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5')

            query_results = Simbad.query_region(coord)
            
            if query_results is None:
                print('\n no objects found at that RA,Dec; try again elsewhere\n')
                ra_center = self.string_RA.get()
                dec_center = self.string_DEC.get()
            else:
                print('\n SIMBAD OBJECTS: \n',query_results)
            """
        # =============================================================================
        # Download an image centered on the coordinates passed by the main window
        #
        # =============================================================================
            # object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
            #object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'],
            #                         #                                 unit=(u.deg, u.deg), frame='icrs')
            #                         unit=(u.hourangle, u.deg), frame='icrs')
            c = SkyCoord(self.string_RA.get(),
                         self.string_DEC.get(), unit=(u.deg, u.deg))
     # FROM      https://astroquery.readthedocs.io/en/latest/hips2fits/hips2fits.html
            """
             query_params = {
                 'hips': self.Survey_selected.get(), #'DSS', #
                 # 'object': object_main_id,
                 # Download an image centef on the first object in the results
                 # 'ra': object_coords[0].ra.value,
                 # 'dec': object_coords[0].dec.value,
                 'ra': c.ra.value,
                 'dec': c.dec.value,
                 'fov': (3.5 * u.arcmin).to(u.deg).value,
                 'width': 1056#528,
                 'height': 1032#516
                 }
            url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'
            hdul = fits.open(url)
            """
            query_params = {"NAXIS1": 1056,
                            "NAXIS2": 1032,
                            "WCSAXES": 2,
                            "CRPIX1": 528,
                            "CRPIX2": 516,
                            "CDELT1": self.PAR.SISI_PixelScale/3600,
                            "CDELT2": self.PAR.SISI_PixelScale/3600,
                            "CUNIT1": "deg",
                            "CUNIT2": "deg",
                            "CTYPE1": "RA---TAN",
                            "CTYPE2": "DEC--TAN",
                            "CRVAL1": c.ra.value,
                            "CRVAL2": c.dec.value}
            query_wcs = wcs.WCS(query_params)
            hips = self.Survey_selected.get()
            hdul = hips2fits.query_with_wcs(hips=hips,
                                            wcs=query_wcs,
                                            get_query_payload=False,
                                            format='fits')
    
            # Downloading http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=DSS&object=%5BT64%5D++7&ra=243.58457533549102&dec=-19.113364937196987&fov=0.03333333333333333&width=500&height=500
            # |==============================================================| 504k/504k (100.00%)         0s
            hdul.info()
            # Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
            # No.    Name      Ver    Type      Cards   Dimensions   Format
            #  0  PRIMARY       1 PrimaryHDU      22   (500, 500)   int16
            print(hdul[0].header)
            
            #to make this robust, we neeed to add a couple of parameters to the FITS header
            #(something like this may be needed by the other surveys...)
            hdul[0].header["FILENAME"] = Survey + "_" + self.string_RA.get() +"_" + self.string_DEC.get() + ".fits"

            self.image = hdul
            hdul.writeto(os.path.join(dir_Astrometry,
                         'newtable.fits'), overwrite=True)
    
            img = AstroImage()
            Posx = self.string_RA.get()
            Posy = self.string_DEC.get()
            filt = self.string_Filter.get()
            data = hdul[0].data[:, ::-1]
            try:
                image_data = Image.fromarray(data)
            except:
                print("\n  No image returned, exiting \n")
                return
            # img_res = image_data.resize(size=(1032,1056))
            img_res = image_data
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec
    
    #            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
     #           hdu.writeto(rebinned_filename,overwrite=True)
     
            self.button_find_stars['state'] = 'active'

                   
            print('\n', self.hdu_res.header)
            self.fitsimage.set_image(img)
            self.AstroImage = img
    #        self.fullpath_FITSfilename = filepath.name
            hdul.close()
            self.fits_image_ql = os.path.join(
                self.PAR.QL_images, "newimage_ql.fits")
            fits.writeto(self.fits_image_ql, self.hdu_res.data,
                         header=self.hdu_res.header, overwrite=True)

        # self.root.title(filepath)

    """
    Inject image from SkyMapper to create a WCS solution using twirl
    """
    def SkyMapper_query(self):
        """ get image from SkyMapper """

        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, 1058, 1032, filt)
        # filepath = skymapper_interrogate_VOTABLE(Posx, Posy, filt)
        with fits.open(filepath.name) as hdu_in:
            #            img.load_hdu(hdu_in[0])
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(1032, 1056))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec

            output_header = copy.deepcopy(hdu_in[0].header)
            main_fits_header.add_astrometric_fits_keywords(self.hdu_res.header)
#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)
            output_header['RA'] = ra
            output_header['DEC'] = dec
            output_header['NAXIS1'] = float(1056)
            output_header['NAXIS2'] = float(1032)
            output_header['CRVAL1'] = float(ra)
            output_header['CRVAL2'] = float(dec)
            output_header['CRPIX1'] = float(528)
            output_header['CRPIX2'] = float(516)
            
            self.wcs =wcs.WCS(output_header)
            self.wcs_exist = True        
            
            img.load_hdu(self.hdu_res)

            self.fitsimage.set_image(img)
            self.AstroImage = img
            self.fullpath_FITSfilename = filepath.name
        hdu_in.close()
        
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, self.hdu_res.data,
##                     header=self.hdu_res.header, overwrite=True)
                     header=output_header, overwrite=True)

        self.fitsimage.rotate(self.PAR.Ginga_PA)  
        self.Display(self.fits_image_ql)
        self.button_find_stars['state'] = 'active'
        self.wcs_exist = True
 
    
 
    def SkyMapper_query_old(self):
        """ get image from SkyMapper """

        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, 1058, 1032, filt)
        # filepath = skymapper_interrogate_VOTABLE(Posx, Posy, filt)
        """
        hdu_in = fits.open(filepath.name)
            #            img.load_hdu(hdu_in[0])
            
        data = hdu_in[0].data
        header = hdu_in[0].header
        hdu_in.close()
        
        #for debug, write onfile the fits file returned by skymapper
        """
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        os.remove(self.fits_image_ql)
        shutil.move(filepath.name,self.fits_image_ql)  
        #fits.writeto(self.fits_image_ql, data,
        #                 header=header, overwrite=True)
        self.fits_image.rotate(self.PAR.Ginga_PA)  
        self.Display(self.fits_image_ql)
        
            
        """
        with fits.open(filepath.name) as hdu_in:
            #            img.load_hdu(hdu_in[0])
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(1032, 1056))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec

            output_header = copy.deepcopy(hdu_in[0].header)
            main_fits_header.add_astrometric_fits_keywords(self.hdu_res.header)
#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)
            output_header['RA'] = ra
            output_header['DEC'] = dec
            output_header['NAXIS1'] = float(1056)
            output_header['NAXIS2'] = float(1032)
            output_header['CRVAL1'] = float(ra)
            output_header['CRVAL2'] = float(dec)
            output_header['CRPIX1'] = float(528)
            output_header['CRPIX2'] = float(516)
            
            self.wcs =wcs.WCS(output_header)
            self.wcs_exist = True        
            
            img.load_hdu(self.hdu_res)

            self.fitsimage.set_image(img)
            self.AstroImage = img
            self.fullpath_FITSfilename = filepath.name
        hdu_in.close()
        
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, self.hdu_res.data,
##                     header=self.hdu_res.header, overwrite=True)
                     header=output_header, overwrite=True)
        self.Display(self.fits_image_ql)
        self.button_find_stars['state'] = 'active'
        self.wcs_exist = True
        """
        
        
    def SDSS_query(self):
        """ get image from SDSS 
            Follow https://github.com/behrouzz/sdss
        """

#        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        
        from astropy import units as u
        from astropy import coordinates as coords
        from astroquery.sdss import SDSS

        pos = coords.SkyCoord(Posx,Posy, unit=(u.deg, u.deg))
        #pos = coords.SkyCoord(RA_HMS +' ' + DEG_HMS,frame='icrs')
        #xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)
        # we search a large area around the target position
        xid = SDSS.query_region(pos, radius='150 arcsec', spectro=True)
        print(xid)
        if xid is None:
            #messagebox.showinfo(title='INFO', message='Not in SDSS')
            print("\n\n\n**** FIELD NOT IN SDSS *****\n\n\n")
            return
        else:
            self.SDSS_stars = np.transpose([xid['ra'],xid['dec']])
            
        
        im = SDSS.get_images(matches=xid, band=filt)
        hdu_0 = im[0]
        data = hdu_0[0].data
        header = hdu_0[0].header
        
        #or pick up the best tile?
    
        
        #fits.writeto(os.path.join(cwd,'input_file.fits'), data, header, overwrite=True)

        from scipy import ndimage
        data_rotated = ndimage.rotate(data, 270, reshape=True)

        
        header_rotated = copy.deepcopy(header)
        tmp = header['NAXIS1'] ; header_rotated['NAXIS2'] = tmp
        tmp = header['NAXIS2'] ; header_rotated['NAXIS1'] = tmp
        tmp = header['CRPIX1'] ; header_rotated['CRPIX2'] = tmp
        tmp = header['CRPIX2'] ; header_rotated['CRPIX1'] = tmp
        tmp = header['CD1_1'] ; header_rotated['CD1_2'] = tmp
        tmp = header['CD1_2'] ; header_rotated['CD1_1'] = -tmp
        tmp = header['CD2_1'] ; header_rotated['CD2_2'] = tmp
        tmp = header['CD2_2'] ; header_rotated['CD2_1'] = -tmp
        
#        fits.writeto(os.path.join(cwd,'output_file.fits'), data_rotated, header_rotated, overwrite=True)
#
        # Resize image
        SDSS_NaturalScale = 0.396127 # arcsec/pix from https://skyserver.sdss.org/dr12/en/tools/chart/chartinfo.aspx
        SAMOS_SISIScale = self.PAR.SISI_PixelScale #arcesc/pix, from 1/6" * 1.125
        FoV_SAMOS_X = 1032 * SAMOS_SISIScale #arcsec
        FoV_SAMOS_Y = 1056 * SAMOS_SISIScale #arcsec
        FoV_SDSS_Xpix = np.round(FoV_SAMOS_X/SDSS_NaturalScale)  # 488
        FoV_SDSS_Ypix = np.round(FoV_SAMOS_Y/SDSS_NaturalScale)  # 500

        #get target xy coordinatex on      
        from astropy.wcs import WCS
        w = WCS(header_rotated)
        xc, yc = np.round(w.world_to_pixel(pos))       
        data_rotated_framed  = np.zeros( (3048,2489) )
        pedestal = 500
        data_rotated_framed[pedestal:pedestal+2048, pedestal:pedestal+1489] = data_rotated

        #SDSS_cutout
        #SDSS_cutout = data_rotated[ int(xc-FoV_SDSS_Xpix/2) : int(xc+FoV_SDSS_Xpix/2),  
        #                            int(yc-FoV_SDSS_Ypix/2) : int(yc+FoV_SDSS_Ypix/2) ]
        SDSS_cutout = data_rotated_framed[ pedestal+int(yc-FoV_SDSS_Ypix/2) : pedestal+int(yc+FoV_SDSS_Ypix/2),  
                                            pedestal+int(xc-FoV_SDSS_Xpix/2) : pedestal+int(xc+FoV_SDSS_Xpix/2) ]
        
#       with fits.open(fits_file) as hdu_in:
            #            img.load_hdu(hdu_in[0])
#            data = hdu_in[0].data
        image_data = Image.fromarray(SDSS_cutout)
        img_res = image_data.resize(size=(1032, 1056))
        self.hdu_res = fits.PrimaryHDU(img_res)
        
        # ra, dec in degrees
        ra = Posx
        dec = Posy
        self.hdu_res.header['RA'] = ra
        self.hdu_res.header['DEC'] = dec
        
        img.load_hdu(self.hdu_res)

        self.fitsimage.set_image(img)
        self.AstroImage = img
        #self.fullpath_FITSfilename = os.path.join(cwd,fits_file)#filepath.name
        #hdu_in.close()
        self.button_find_stars['state'] = 'active'
        
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, self.hdu_res.data,
                     header=self.hdu_res.header, overwrite=True)     
        
           
            
           
    def twirl_Astrometry(self):
        """ to be written """

        self.wcs = None
        self.fitsimage.rotate(self.PAR.Ginga_PA)  
        self.Display(self.fits_image_ql)
        # self.load_file()   #for ging

        hdu_Main = fits.open(self.fits_image_ql)  # for this function to work
        hdu = hdu_Main[0]
        header = hdu.header
        data = hdu.data
        hdu_Main.close()
        
        # not all headers use ra,dec
        try:
            ra, dec = header["RA"], header["DEC"]
        except:
            mywcs = wcs.WCS(header)
            ra, dec = mywcs.all_pix2world([[data.shape[0]/2,data.shape[1]/2]], 0)[0]
        print(ra,dec)
        
        
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        shape = data.shape
        #pixel = self.PAR.SISI_PixelScale * u.arcsec
        fov = 0.05#np.max(shape)*pixel.to(u.deg).value 

        # Let's find some stars and display the image

        self.canvas.delete_all_objects(redraw=True)
        #check first if it exist, as we may have not yet queried SDSS        
        try:  
            if self.SDSS_stars is None:  #if it exist but is none, we just check the current image
                stars = twirl.find_peaks(data)[0:self.nrofstars.get()]
            else: #if it exist, we are coming from SDSS and therefore we use the SDSS stars
                import copy
                stars = copy.deepcopy(self.SDSS_stars)
                SDSS_stars = None  #and immediately delete them so we are free for the next searh
        except:  #if self.SDSS has never been created, we go to the basic search
             stars = twirl.find_peaks(data)[0:self.nrofstars.get()]

#        plt.figure(figsize=(8,8))
#        med = np.median(data)
#        plt.imshow(data, cmap="Greys_r", vmax=np.std(data)*5 + med, vmin=med)
#        plt.plot(*stars.T, "o", fillstyle="none", c="w", ms=12)

        from regions import PixCoord, CirclePixelRegion
#        xs=stars[0,0]
#        ys=stars[0,1]
#        center_pix = PixCoord(x=xs, y=ys)
        radius_pix = 7

#        this_region = CirclePixelRegion(center_pix, radius_pix)

        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                   for x, y in stars]  # [(1, 2), (3, 4)]]
        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
            obj.color="red"
        # add_region(self.canvas, obj, tag="twirlstars", draw=True)
            self.canvas.add(obj)

        # we can now compute the WCS
        gaias = twirl.gaia_radecs(center, fov, limit=self.nrofstars.get())
        
#        stars_sorted = np.flip(np.sort(stars,axis=0))
#        gaias_sorted = np.sort(gaias,axis=0)
        #stars_sorted = np.sort(stars,axis=0)
        #gaias_sorted = np.flip(np.sort(gaias,axis=0))
        self.wcs = twirl.compute_wcs(stars, gaias)#,tolerance=0.1)

        global WCS_global   #used for HTS
        WCS_global = self.wcs

        # Lets check the WCS solution

#        plt.figure(figsize=(8,8))
        radius_pix = 21
        gaia_pixel = np.array(SkyCoord(gaias, unit="deg").to_pixel(self.wcs)).T
        regions_gaia = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                        for x, y in gaia_pixel]  # [(1, 2), (3, 4)]]
        regs_gaia = Regions(regions_gaia)
        for reg in regs_gaia:
            obj = r2g(reg)
            obj.color = "green"
        # add_region(self.canvas, obj, tag="twirlstars", redraw=True)
            self.canvas.add(obj)

        print(self.wcs)
        
        if self.wcs is None:
            self.wcs_exist = False
            print("\n WCS solution not found, returning\n")
            return
        else:
            self.wcs_exist = True            
            print("\n WCS solution found!\n")
            
        hdu_wcs = self.wcs.to_fits()

        if self.loaded_regfile is not None:
            hdu_wcs[0].header.set(
                "dmdmap", os.path.split(self.loaded_regfile)[1])

        hdu_wcs[0].data = data  # add data to fits file
        self.wcs_filename = os.path.join(
            ".", "SAMOS_Astrometry_dev", "WCS_"+str(ra)+"_"+str(dec)+".fits")
        hdu_wcs[0].writeto(self.wcs_filename, overwrite=True)

        self.fitsimage.rotate(self.PAR.Ginga_PA)  
        self.Display(self.wcs_filename)
        self.button_find_stars['state'] = 'active'
        
        self.wcs_exist = True
        
        #calculate the offset in mm between pointed and actual position for the GS
        mywcs = wcs.WCS(header)
        ra_cntr, dec_cntr = mywcs.all_pix2world([[data.shape[0]/2,data.shape[1]/2]], 0)[0]
        print(ra,dec)

        self.string_RA_cntr.set(ra)
        self.string_DEC_cntr.set(dec)
        Delta_RA = float(ra) - float(self.string_RA.get()) 
        Delta_DEC = float(dec) - float(self.string_DEC.get()) 
        Delta_RA_mm = round(Delta_RA * 3600 / self.PAR.SOAR_arcs_mm_scale,3)
        Delta_DEC_mm = round(Delta_DEC * 3600 / self.PAR.SOAR_arcs_mm_scale,3)
        self.string_RA_cntr_mm.set(Delta_RA_mm)
        self.string_DEC_cntr_mm.set(Delta_DEC_mm)
        
        #
        # > to read:
        # hdu = fits_open(self.wcs_filename)
        # hdr = hdu[0].header
        # import astropy.wcs as apwcs
        # wcs = apwcs.WCS(hdu[('sci',1)].header)
        

    def find_stars(self):
        """ to be written """

        self.fitsimage.rotate(self.PAR.Ginga_PA)  
        self.Display(self.fits_image_ql)
        
        self.set_slit_drawtype()
        # self.load_file()   #for ging

        hdu = fits.open(self.fits_image_ql)  # for this function to work
        
        header = hdu[0].header
        data = hdu[0].data
        hdu.close()
        ra, dec = header["RA"], header["DEC"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]

        # image shape and pixel size in "
        shape = data.shape
        pixel = self.PAR.SISI_PixelScale * u.arcsec
        fov = np.max(shape)*pixel.to(u.deg).value

        # Let's find some stars and display the image

        self.canvas.delete_all_objects(redraw=True)
        threshold = 0.1
        stars = twirl.find_peaks(data, threshold)[0:self.nrofstars.get()]

#        plt.figure(figsize=(8,8))
        med = np.median(data)
#        plt.imshow(data, cmap="Greys_r", vmax=np.std(data)*5 + med, vmin=med)
#        plt.plot(*stars.T, "o", fillstyle="none", c="w", ms=12)

        from regions import PixCoord, CirclePixelRegion
#        xs=stars[0,0]
#        ys=stars[0,1]
#        center_pix = PixCoord(x=xs, y=ys)
        radius_pix = 20

#        this_region = CirclePixelRegion(center_pix, radius_pix)

#        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
        regions = [RectanglePixelRegion(center=PixCoord(x=round(x), y=round(y)),
                           width=self.slit_w.get(), height=self.slit_l.get(),
                           angle=0*u.deg)
                   for x, y in stars]  # [(1, 2), (3, 4)]]

        if self.SlitTabView is None:
            self.initialize_slit_table()

        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
        # add_region(self.canvas, obj, tag="twirlstars", draw=True)
            self.canvas.add(obj)

            obj.pickable = True
            obj.add_callback('pick-up', self.pick_cb, 'up')
            # obj.add_callback('pick-down', self.pick_cb, 'down')
            obj.add_callback('edited', self.edit_cb)

            self.SlitTabView.add_slit_obj(reg, obj.tag, self.fitsimage)
    
        self.draw_slits()
        pass


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#     def start_the_loop(self):
#         while self.stop_it == 0:
#             threading.Timer(1.0, self.load_manager_last_file).start()
#
#     def load_manager_last_file(self):
#         FITSfiledir = './fits_image/'
#         self.fullpath_FITSfilename = FITSfiledir + (os.listdir(FITSfiledir))[0]
#         print(self.fullpath_FITSfilename)
#
#     def stop_the_loop(self):
#         self.stop_it == 1
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#         image = load_data(self.fullpath_FITSfilename, logger=self.logger)
#         self.fitsimage.set_image(image)
#         self.root.title(self.fullpath_FITSfilename)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def load_file(self):
        """ to be written """
        self.AstroImage = load_data(
            self.fullpath_FITSfilename, logger=self.logger)
        self.canvas.set_image(self.AstroImage)
        self.root.title(self.fullpath_FITSfilename)

    def open_file(self):
        """ to be written """
        filename = filedialog.askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        # self.load_file()
        self.AstroImage = load_data(filename, logger=self.logger)
        self.fitsimage.set_image(self.AstroImage)

        if self.AstroImage.wcs.wcs.has_celestial:
            self.wcs = self.AstroImage.wcs.wcs

    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'point')
        print(list(points))

        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'point')
        list_point = list(points)
        CM.CompoundMixin.delete_objects(self.canvas, list_point)
        self.canvas.objects  # check that the points are gone

        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas, ['point', 'circle',
                                                                     'rectangle', 'polygon',
                                                                     'triangle', 'righttriangle',
                                                                     'ellipse', 'square'])
        list_points = list(points)
        CM.CompoundMixin.delete_objects(self.canvas, list_points)
        self.canvas.objects  # check that the points are gone

        """
        # Find approximate bright peaks in a sub-area
        from ginga.util import iqcalc
        iq = iqcalc.IQCalc()
    
        r = self.canvas.objects[0]
        img_data = self.AstroImage.get_data()
        data_box = self.AstroImage.cutout_shape(r)
        
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        px,py=round(peaks[0][0]+r.x1),round(peaks[0][1]+r.y2)
        print(px,py)   #image coordinates
        print(img_data[px,py]) #actual counts
     
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)       
        # how many did we find with standard thresholding, etc.
        # see params for find_bright_peaks() and evaluate_peaks() for details
        print(len(objs))
        # example of what is returned
        o1 = objs[0]
        print(o1)
           
        # pixel coords are for cutout, so add back in origin of cutout
        #  to get full data coords RA, DEC of first object
        x1, y1, x2, y2 = r.get_llur()
        self.img.pixtoradec(x1+o1.objx, y1+o1.objy)
          
        # Draw circles around all objects
        Circle = self.canvas.get_draw_class('circle')
        for obj in objs:
            x, y = x1+obj.objx, y1+obj.objy
            if r.contains(x, y):
                self.canvas.add(Circle(x, y, radius=10, color='yellow'))
        
        # set pan and zoom to center
        self.fitsimage.set_pan((x1+x2)/2, (y1+y2)/2)
        self.fitsimage.scale_to(0.75, 0.75)
        
        r_all = self.canvas.objects[:]
        print(r_all)
        
        
        EXERCISE COMPOUNDMIXING CLASS
        r_all is a CompountMixing object, see class ginga.canvas.CompoundMixin.CompoundMixin
         https://ginga.readthedocs.io/en/stable/_modules/ginga/canvas/CompoundMixin.html#CompoundMixin.get_objects_by_kinds        
              
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        print(list(points))
        
        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        list_point=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_point)
        self.canvas.objects   #check that the points are gone
           
        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas,['point','circle',
                                                                    'rectangle', 'polygon', 
                                                                    'triangle', 'righttriangle', 
                                                                    'ellipse', 'square'])
        list_points=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_points)
        self.canvas.objects   #check that the points are gone
    
        # drawing an object can be done rather easily
        # first take an object fromt the list and change something
        objects=CM.CompoundMixin.get_objects(self.canvas)
        o0=objects[0]
        o0.y1=40
        o0.height=100
        o0.width=70
        o0.color='lightblue'
        CM.CompoundMixin.draw(self.canvas,self.canvas.viewer)
        
        END OF THE COMPOUNDMIXING EXCERCISE
        # ===#===#===#===#===#===#===#===#===#===#===#====        

        # region = 'fk5;circle(290.96388,14.019167,843.31194")'
        # astropy_region = pyregion.parse(region)
        # astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])
        # print(astropy_region)
         
        # List all regions that we have created
        # n_objects = len(self.canvas.objects)
        # for i_obj in range(n_objects):
        #   astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj])
        #   print(astropy_region) 
           
        # create a list of astropy regions, so we export a .reg file
        # first put the initial region in square brackets, argument of Regions to initiate the list
        RRR=Regions([ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])])
        # then append to the list adding all other regions
        for i_obj in range(1,len(self.canvas.objects)):
           RRR.append(ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj]))
           print(RRR) 
 
        # write the regions to file
        # this does not seem to work...
        RRR.write('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9',overwrite=True)
       
        # reading back the ds9 regions in ginga
        pyregions = Regions.read('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9')
        n_regions = len(pyregions)
        for i in range(n_regions):
            pyregion = pyregions[i]
            pyregion.width=7
            pyregion.width=3
            ap_region.add_region(self.canvas,pyregion)

        print("yay!")            
        
        # Export all Ginga objects to Astropy region
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        counter = 0
        for obj in objects:
            if counter == 0:
                astropy_regions=[g2r(obj)]  #here we create the first astropy region and the Regions list []
            else:
                astropy_regions.append(g2r(obj)) #will with the other slits 
            counter += 1
        regs = Regions(astropy_regions)     #convert to astropy-Regions
        regs.write('my_regions.reg',overwrite=True)   #write to file
        
        # 2, Extract the slits and convert pixel->DMD values
        
        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        
        # create initial DMD slit mask
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        
        regions = Regions.read('my_regions.reg')


        for i in range(len(regions)):
            reg = regions[i]
            corners = reg.corners
            # convert CCD corners to DMD corners here
            # TBD
            # dmd_corners=[] 
            # for j in range(len(corners)):
            x1,y1 = convert.CCD2DMD(corners[0][0], corners[0][1])
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(corners[2][0], corners[2][1])
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            # dmd_corners[:][1] = corners[:][1]+500
            ####   
            # x1 = round(dmd_corners[0][0])
            # y1 = round(dmd_corners[0][1])+400
            # x2 = round(dmd_corners[2][0])
            # y2 = round(dmd_corners[2][1])+400
        # 3 load the slit pattern   
            self.slit_shape[x1:x2,y1:y2]=0
        DMD.apply_shape(self.slit_shape)  
        # DMD.apply_invert()   

        
        print("check")
        """

    def cursor_cb(self, viewer, button, data_x, data_y):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            value = int(round(value, 0))
        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        dmd_x, dmd_y = convert.CCD2DMD(fits_x, fits_y)

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
            ra_deg, dec_deg = image.pixtoradec(fits_x, fits_y)
            self.ra_center, self.dec_center = image.pixtoradec(528, 516,
                                                               format='str', coords='fits')

        except Exception as e:
            # self.logger.warning("Bad coordinate conversion: %s" % (
            #    str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'
            ra_deg = 'BAD WCS'
            dec_deg = 'BAD WCS'
        coords_text = "RA: %s  DEC: %s \n" % (ra_txt, dec_txt)
#        coords_text_DEG = "RA: %s  DEC: %s \n"%(str(ra_deg), str(dec_deg))
        coords_text_DEG = "RA: %.9s DEC %.9s\n" % (str(ra_deg), str(dec_deg))
#        dmd_text = "DMD_X: %.2f  DMD_Y: %.2f \n"%(dmd_x, dmd_y)
#        dmd_text = "DMD_X: %i  DMD_Y: %i \n"%(np.round(dmd_x), round(dmd_y))
        dmd_text = "DMD_X: %i  DMD_Y: %i \n" % (
            np.floor(dmd_x), np.floor(dmd_y))
        text = "X: %i  Y: %i  Value: %s" % (
            np.floor(fits_x), np.floor(fits_y), value)

        text = coords_text + coords_text_DEG + dmd_text + text
        self.readout.config(text=text)

    def MASTER_quit(self):
        #self.ConfP.destroy()
        self.destroy()
        return True

######

    def set_slit_drawtype(self):
        self.wdrawtype.delete(0, tk.END)
        mode = self.Draw_Edit_Pick_Checked.set("draw")
        self.set_mode_cb()
        if self.CentroidPickup_ChkBox_Enabled.get() == 1:
            self.wdrawtype.insert(0, "point")
        else:
            self.wdrawtype.insert(0, "box")
#            self.Draw_Edit_Pick_Checked.set("None")
        print("drawtype changed to ", self.wdrawtype.get())
#        parameters = []
#        parameters['color'] = 'red'
        self.canvas.set_drawtype(self.wdrawtype.get())#,**parameters)
            

    def set_mode_cb(self):
        """ to be written """
        mode = self.Draw_Edit_Pick_Checked.get()
        
        #we turn off here the SourcePickup_ChkBox 
        if mode != "draw":
            self.CentroidPickup_ChkBox_Enabled.set(0)
            
#        self.logger.info("canvas mode changed (%s) %s" % (mode))
        self.logger.info("canvas mode changed (%s)" % (mode))
        try: #all object painted red, should not be true for the traces
            for obj in self.canvas.objects:
                obj.color = 'red'
        except:
            pass

        self.canvas.set_draw_mode(mode)

    def draw_cb(self, canvas, tag):
        """ to be written """
        obj = canvas.get_object_by_tag(tag)
        
#        obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.pickable = True
        obj.add_callback('pick-key', self.pick_cb, 'key')

        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        # obj.add_callback('pick-hover', self.pick_cb, 'hover')
        # obj.add_callback('pick-enter', self.pick_cb, 'enter')
        # obj.add_callback('pick-leave', self.pick_cb, 'leave')
        
        obj.add_callback('edited', self.edit_cb)
        # obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        kind = self.wdrawtype.get()
        print("kind: ", kind)
        
        # =============
        #CASE A)
        #this case should never run. 
        #If we have enabled the slit pickup mode, the ob.kind is "point" 
        if kind == "box" and self.CentroidPickup_ChkBox_Enabled.get() == 1:
            if self.SlitTabView is None:
                self.initialize_slit_table()
            try:
                kind == "box"
                # the ginga object, a box, is converted to an astropy region
                r = g2r(obj)

            except ValueError:
                # if you just click instead of drawing a box, call the slit_handler
                print("box")
                obj.kind = "box"

            new_obj = self.slit_handler(obj)
            r = g2r(new_obj)
            tag = new_obj.tag
            obj = new_obj

            self.SlitTabView.add_slit_obj(r, tag, self.fitsimage)
            # self.SlitTabView.slit_obj_tags.append(tag)

        # =============
        #CASE B)
        # Pick up mode. obj.kind should always be point.
        elif self.CentroidPickup_ChkBox_Enabled.get() == 1 and kind == 'point':  # or kind == 'box':

            #this case requires more sophisticated operations, hence a dedicated function            
            self.slit_handler(obj)

        # =============
        # CASE C)
        # a box is drawn but centroid is not searched, just drawn... 
        elif kind == "box" and self.CentroidPickup_ChkBox_Enabled.get() == 0:
            
            #if table does not exist, create it (this should not happen as table previously created)
            if self.SlitTabView is None:
                self.initialize_slit_table()
            
            # the ginga object, a box, is converted to an astropy region
            r = g2r(obj)
            
            # the astropy object is added to the table
            self.SlitTabView.add_slit_obj(r, tag, self.fitsimage)
            # self.SlitTabView.slit_obj_tags.append(tag)

            
            

    def slit_handler(self, obj):
        """ to be written """
        print('ready to associate a slit to ')
        print(obj.kind)
        img_data = self.AstroImage.get_data()

        #we are still a bit paranoid....
        if obj.kind == 'point':
            
            # Search centroid: Start creating box
            x_c = obj.points[0][0]-1  # really needed?
            y_c = obj.points[0][1]-1
            
            # create area to search, use astropy and convert to ginga (historic reasons...)
            r = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)),
                                     width=40, height=40,
                                     angle=0*u.deg)
            # and we convert it to ginga.
            obj = r2g(r)
            # Note: r as an Astropy region is a RECTANGLE
            #      obj is a Ginga region type BOX
            # obj = r2g(r)
            
            # the Ginga Box object can be added to the canvas
            self.canvas.add(obj)
        
        # time to do the math; collect the pixels in the Ginga box
        data_box = self.AstroImage.cutout_shape(obj)

        # we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.canvas, obj)

  #      obj = self.canvas.get_draw_class('rectangle')
  #      obj(x1=x_c-20,y1=y_c-20,x2=x_c+20,y2=y_c+20,
  #                      width=100,
  #                      height=30,
  #                      angle = 0*u.deg)
  #      data_box = self.img.cutout_shape(obj)
       
        # find the peak within the Ginga box
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        x1 = obj.x-obj.xradius
        y1 = obj.y-obj.yradius
        px, py = round(peaks[0][0]+x1), round(peaks[0][1]+y1)
        print('peak found at: ', px, py)  # image coordinates
        print('with counts: ', img_data[px, py])  # actual counts
        
        # GINGA MAGIC!!! 
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)
        # from ginga.readthedocs.io
        """
        Each result contains the following keys:

           * ``objx``, ``objy``: Fitted centroid from :meth:`get_fwhm`.
           * ``pos``: A measure of distance from the center of the image.
           * ``oid_x``, ``oid_y``: Center-of-mass centroid from :meth:`centroid`.
           * ``fwhm_x``, ``fwhm_y``: Fitted FWHM from :meth:`get_fwhm`.
           * ``fwhm``: Overall measure of fwhm as a single value.
           * ``fwhm_radius``: Input FWHM radius.
           * ``brightness``: Average peak value based on :meth:`get_fwhm` fits.
           * ``elipse``: A measure of ellipticity.
           * ``x``, ``y``: Input indices of the peak.
           * ``skylevel``: Sky level estimated from median of data array and
             ``skylevel_magnification`` and ``skylevel_offset`` attributes.
           * ``background``: Median of the input array.
           * ``ensquared_energy_fn``: Function of ensquared energy for different pixel radii.
           * ``encircled_energy_fn``: Function of encircled energy for different pixel radii.

        """
        print('full evaluation: ', objs)
        print('fitted centroid: ', objs[0].objx, objs[0].objy)
        print('FWHM: ', objs[0].fwhm)
        print('peak value: ', objs[0].brightness)
        print('sky level: ', objs[0].skylevel)
        print('median of area: ', objs[0].background)
        print("the four vertex of the rectangle are, in pixel coord:")
        x1, y1, x2, y2 = obj.get_llur()
        print(x1, y1, x2, y2)
        print("the RADEC of the fitted centroid are, in decimal degrees:")
        print(self.AstroImage.pixtoradec(objs[0].objx, objs[0].objy))
#        slit_w=3
#        slit_l=9
#        self.canvas.add(slit_box(x1=objs[0].objx+x1-slit_w,y1=objs[0].objy+y1-slit_h,x2=objs[0].objx+x1+slit_w,y2=objs[0].objy+y1+slit_h,
#                        width=100,
#                        height=30,
#                        angle = 0*u.deg))

        #enogh with astronomy;
        # having found the centroid, we need to draw the slit
        slit_box = self.canvas.get_draw_class('box')
        xradius = self.slit_w.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        yradius = self.slit_l.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        new_slit_tag = self.canvas.add(slit_box(x=objs[0].objx+x1,
                                                y=objs[0].objy+y1,
                                                xradius=xradius,
                                                yradius=yradius,
                                                color='red',
                                                alpha=0.8,
                                                fill=False,
                                                angle=5*u.deg,
                                                pickable=True))
        #sing a victory song...
        print("slit added")

        # some final stuff that must be here for some reason... to be reviewed?
        obj = self.canvas.get_object_by_tag(new_slit_tag)
        # obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.add_callback('edited', self.edit_cb)
        # self.cleanup_kind('point')
        # ssself.cleanup_kind('box')
        return self.canvas.objects[-1]

    def show_traces(self):
        """ Show Traces """
        # if self.traces == 1:
        img_data = self.AstroImage.get_data()

        # keep only the slits/boxes
        self.slits_only()

        # we should hanve only boxes/slits
        objects = CM.CompoundMixin.get_objects(self.canvas)
        self.trace_boxes_objlist = []
        for i in range(len(objects)):

            if objects[i].alpha == 0:
                continue

            o0 = objects[i]
            x_c = o0.x  # really needed?
            y_c = o0.y
            height_ = 2*o0.yradius
            width_ = 1024
            alpha_ = 0.3
            color_ = 'green'
            # create area to search, using astropy instead of ginga (still unclear how you do it with ginga)
            Rectangle = self.canvas.get_draw_class('rectangle')
#            r = Rectangle(center=PixCoord(x=round(x_c), y=round(y_c)),
#                                        width=width_, height=height_,
#                                        angle = 0*u.deg)
            r = Rectangle(x1=round(x_c)-1024, y1=round(y_c)-o0.yradius, x2=round(x_c)+1024, y2=round(y_c)+o0.yradius,
                          angle=0*u.deg, color='yellow', fill=1, fillalpha=0.5)
            self.canvas.add(r)
            CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)
            self.trace_boxes_objlist.append(r)
            # create box

    def remove_traces(self):
        """ 
        Use "try:/except:"
        We may call this function just to make sure that the field is clean, so
        we do not need to assume that the traces have been created
        """
        try: 
            self.trace_boxes_objlist
            if len(self.trace_boxes_objlist) > 0:
                CM.CompoundMixin.delete_objects(
                    self.canvas, self.trace_boxes_objlist)
                self.trace_boxes_objlist = []
        except:
            return
        
    def save_all_sub_patterns(self):

        pattern_dirname = os.path.join(self.fits_dir, "SubPatterns")

        if not os.path.exists(pattern_dirname):
            os.mkdir(pattern_dirname)

        for i in range(len(self.pattern_series)):

            pattern = self.pattern_series[i]
            pattern_name = self.sub_pattern_names[i]
            print(i)
            if self.wcs.has_celestial:

                pattern_data_rows = pattern.values
                sky_regions = Regions(
                    list(map(self.create_astropy_RectangleSkyRegion, pattern_data_rows)))
                new_regfname = os.path.join(
                    pattern_dirname, pattern_name, ".reg")
                sky_regions.write(new_regfname, overwrite=True, format="ds9")

        pass

    def save_selected_sub_pattern(self):

        pattern_list_index = self.pattern_group_dropdown.current()

        # print(self.pattern_series[pattern_list_index])
        current_pattern = self.pattern_series[pattern_list_index]

        pattern_name = self.pattern_group_dropdown.get()

        pattern_dirname = os.path.join(self.fits_dir, "SubPatterns")
        if not os.path.exists(pattern_dirname):
            os.mkdir(pattern_dirname)
        if self.wcs.has_celestial:
            pattern_data_rows = current_pattern.values

            sky_regions = Regions(
                list(map(self.create_astropy_RectangleSkyRegion, pattern_data_rows)))
            new_regfname = os.path.join(pattern_dirname, pattern_name, ".reg")
            sky_regions.write(new_regfname, overwrite=True, format="ds9")

    def create_astropy_RectangleSkyRegion(self, pattern_row):
        # given
        ra, dec = pattern_row[1:3]
        x0, y0 = pattern_row[5:7]
        x1, y1 = pattern_row[7:9]

        ra_width = (x1-x0)*self.wcs.proj_plane_pixel_scales()[0].value
        dec_length = (y1-y0)*self.wcs.proj_plane_pixel_scales()[0].value

        center = SkyCoord(ra, dec, unit=(u.deg, u.deg), frame="fk5")
        sky_region = RectangleSkyRegion(
            center=center, width=ra_width*u.deg, height=dec_length*u.arcsec, )

        return sky_region

    def set_pattern_entry_text_color(self, event):

        if self.base_pattern_name_entry.get() != "Base Pattern Name":

            # self.base_pattern_name_entry.foreground="black"
            self.base_pattern_name_entry.config(fg="black")

    def create_pattern_series_from_traces(self):
        """

        Input: Primary DMD pattern that is shown in the display.

        Returns
        -------
        Series of patterns from a main FOV pattern where each new pattern
        contains slits with no risk of overlapping spectra.
        """
        self.remove_traces()
        self.slits_only()

        print(self.base_pattern_name_entry.get())

        self.DMD_Group = DMDGroup(
            dmd_slitview_df=self.SlitTabView.slitDF, regfile=self.loaded_regfile)

        good_patterns = [self.SlitTabView.slitDF]

        redo_pattern = self.SlitTabView.slitDF.copy()
        base_name = self.base_pattern_name_entry.get()
        if (base_name != "Base Pattern Name" and base_name.strip(" ") != ""):
            basename = "{}".format(base_name.replace(" ", "_"))
        else:
            basename = "Pattern"

        pattern_name_txt = "{}_{}"
        self.pattern_group_dropdown["values"] = "MainPattern"
        self.sub_pattern_names = ["MainPattern"]
        pattern_num = 0
        while len(redo_pattern) > 0:
            pattern_num += 1
            good_pattern, redo_pattern = self.DMD_Group.pass_through_current_slits(
                redo_pattern)
            # good_pattern, redo_pattern = self.DMD_Group.pass_through_current_slits_two_sided(redo_pattern)
            good_patterns.append(good_pattern)
            pattern_name = pattern_name_txt.format(basename, pattern_num)
            self.sub_pattern_names.append(pattern_name)
            self.pattern_group_dropdown["values"] += (pattern_name,)

        self.pattern_series = good_patterns

        # self.all_slit_tags = self.canvas.get_tags()
        self.all_slit_objects = [self.canvas.get_object_by_tag(
            tag) for tag in self.SlitTabView.slit_obj_tags]

        import random
        random.seed(138578028235)

        drawcolors = nice_colors_list

        for pattern in self.pattern_series[1:]:
            c = random.choice(drawcolors)
            drawcolors.remove(c)
            tags = ["@{}".format(int(obj_num))
                    for obj_num in pattern.object.values]
            print(tags)
            # obj_inds = [self.all_slit_tags.index(tag) for tag in tags]

            for tag in tags:
                # print(c)
                obj = self.canvas.get_object_by_tag(tag)
                obj.color = c
                obj.alpha = 1

    def selected_dmd_group_pattern(self, event):

        self.slits_only()
        print(self.pattern_group_dropdown.get())
        pattern_list_index = self.pattern_group_dropdown.current()

        print(self.pattern_series[pattern_list_index])
        current_pattern = self.pattern_series[pattern_list_index]

        current_pattern_tags = [
            "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

        for tag in current_pattern_tags:
            obj_ind = self.SlitTabView.slit_obj_tags.index(tag)

            obj = self.canvas.get_object_by_tag(tag)
            obj.alpha = 1

            self.canvas.redraw()

        hide_pattern_tags = [
            tag for tag in self.SlitTabView.slit_obj_tags if tag not in current_pattern_tags]

        for tag in hide_pattern_tags:

            obj = self.canvas.get_object_by_tag(tag)

            obj.alpha = 0

            self.canvas.redraw()

        print(current_pattern_tags)

    def apply_to_all(self):
        """ apply the default slit width/length to all slits """

        # cleanup, keep only the slits
        self.slits_only()

        # do the change
        xr = float(self.slit_w.get())/2.
        yr = float(self.slit_l.get())/2.
        CM.CompoundMixin.set_attr_all(self.canvas, xradius=xr, yradius=yr)

        # display

#        CM.CompoundMixin.draw(self.canvas,self.canvas.viewer)
        self.canvas.redraw()

        # update slit table/df
        updated_objs = CM.CompoundMixin.get_objects(self.canvas)

        # way faster than looping
        viewer_list = np.full(len(updated_objs), self.canvas.viewer)
        np.array(
            list(map(self.SlitTabView.update_table_from_obj, updated_objs, viewer_list)))

        """ 
        # cleanup, keep only the slits
        self.slits_only()
 
        # do the change
        xr = float(self.slit_w.get())/2.
        yr = float(self.slit_l.get())/2.
        CM.CompoundMixin.set_attr_all(self.canvas, xradius=xr, yradius=yr)
         
        # display
        CM.CompoundMixin.draw(self.canvas,self.canvas.viewer)
        """

    def get_dmd_coords_of_picked_slit(self, picked_slit):
        """ get_dmd_coords_of_picked_slit """

        x0, y0, x1, y1 = picked_slit.get_llur()
        fits_x0 = x0+1
        fits_y0 = y0+1
        fits_x1 = x1+1
        fits_y1 = y1+1

        fits_xc, fits_yc = picked_slit.get_center_pt()+1

        dmd_xc, dmd_yc = convert.CCD2DMD(fits_xc, fits_yc)
        dmd_x0, dmd_y0 = convert.CCD2DMD(fits_x0, fits_y0)
        dmd_x1, dmd_y1 = convert.CCD2DMD(fits_x1, fits_y1)

        dmd_width = int(np.ceil(dmd_x1-dmd_x0))
        dmd_length = int(np.ceil(dmd_y1-dmd_y0))

        return dmd_xc, dmd_yc, dmd_x0, dmd_y0, dmd_x1, dmd_y1, dmd_width, dmd_length

    def slit_width_length_adjust(self, event=None):
        """ to be written """
        try:
            picked_slit = self.canvas.get_object_by_tag(self.selected_obj_tag)

            current_dmd_width = int(self.width_adjust_btn.get())
            current_dmd_length = int(self.length_adjust_btn.get())

            half_current_dmd_width = int(current_dmd_width)/2
            half_current_dmd_length = int(current_dmd_length)/2

            fits_xc, fits_yc = picked_slit.get_center_pt()
            dmd_xc, dmd_yc = convert.CCD2DMD(fits_xc+1, fits_yc+1)

            dmd_x0 = dmd_xc-half_current_dmd_width
            dmd_y0 = dmd_yc-half_current_dmd_length
            dmd_x1 = dmd_xc+half_current_dmd_width
            dmd_y1 = dmd_yc+half_current_dmd_length

            fits_x0, fits_y0 = convert.DMD2CCD(dmd_x0-1, dmd_y0-1)
            fits_x1, fits_y1 = convert.DMD2CCD(dmd_x1-1, dmd_y1-1)

            fits_length = np.ceil(fits_y1-fits_y0)
            fits_width = np.ceil(fits_x1-fits_x0)

            picked_slit.xradius = fits_width/2
            picked_slit.yradius = fits_length/2

            self.canvas.set_draw_mode('draw')  # stupid but necessary to show
            # which object is selected
            self.canvas.set_draw_mode('pick')

            # update the cells in the table.
            obj_ind = list(self.SlitTabView.stab.get_column_data(
                0)).index(self.selected_obj_tag.strip("@"))

            imcoords_txt_fmt = "{:.2f}"

            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=5, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_x0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=6, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_y0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=7, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_x1))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=8, redraw=True,
                                                value=imcoords_txt_fmt.format(fits_y1))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=11, redraw=True,
                                                value=int(dmd_x0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=12, redraw=True,
                                                value=int(dmd_y0))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=13, redraw=True,
                                                value=int(dmd_x1))
            self.SlitTabView.stab.set_cell_data(r=obj_ind, c=14, redraw=True,
                                                value=int(dmd_y1))

        except AttributeError:
            print("Must first pick a slit to adjust width/length!!")
        pass
    
    def delete_obj_cb(self, obj, canvas, event, pt, ptype):
        try:
            if event.key == 'd':
                # print(event.key)
                canvas.delete_object(obj)
                print("start tab len", len(
                    self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.delete_row(self.tab_row_ind)
                print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.redraw()
                self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
                    index=self.obj_ind)
                # del self.SlitTabView.slit_obj_tags[self.obj_ind]
                self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
                canvas.clear_selected()

                try:

                    for si in range(len(self.pattern_series)):

                        sub = self.pattern_series[si]

                        tag = int(obj.tag.strip("@"))

                        if tag in sub.object.values:
                            sub_ind = sub.where(sub.object == tag).dropna(
                                how="all").index.values[0]
                            sub = sub.drop(index=sub_ind)

                            self.pattern_series[si] = sub

                except:
                    print("try again")

        except:
            pass

    def pick_cb(self, obj, canvas, event, pt, ptype):
        """ to be written """

        print("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        self.logger.info("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))

        try:
            canvas.get_object_by_tag(self.selected_obj_tag).color = 'red'
            canvas.clear_selected()
            print('unselect previous obj tag')
        except:
            pass

        canvas.select_add(obj.tag)
        self.selected_obj_tag = obj.tag
        obj.color = 'green'

        canvas.set_draw_mode('draw')  # stupid but necessary to show
        # which object is selected
        # this took me a solid 3 hours to figure out
        canvas.set_draw_mode('pick')

        self.obj_ind = int(obj.tag.strip('@'))-1
        try:
            self.tab_row_ind = self.SlitTabView.stab.get_column_data(
                0).index(obj.tag.strip('@'))
            dmd_x0, dmd_x1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
                'dmd_x0', 'dmd_x1']].astype(int)
            dmd_y0, dmd_y1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
                'dmd_y0', 'dmd_y1']].astype(int)
            dmd_width = int(dmd_x1-dmd_x0)
            dmd_length = int(dmd_y1-dmd_y0)

            self.slit_w.set(dmd_width)
            self.slit_l.set(dmd_length)
        except:
            pass

        if ptype == 'up' or ptype == 'down':
            
            print("picked object with tag {}".format(obj.tag))
            #if self.deleteChecked.get():#event.key == 'd':
            canvas.delete_object(obj)
            try:
                self.SlitTabView.stab.select_row(row=self.tab_row_ind)          
                print("start tab len", len(
                    self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.delete_row(self.tab_row_ind)
                print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
                self.SlitTabView.stab.redraw()
                self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
                    index=self.obj_ind)
                # del self.SlitTabView.slit_obj_tags[self.obj_ind]
                self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
                canvas.clear_selected()

                try:

                    for si in range(len(self.pattern_series)):

                        sub = self.pattern_series[si]

                        tag = int(obj.tag.strip("@"))

                        if tag in sub.object.values:
                            sub_ind = sub.where(sub.object == tag).dropna(
                                how="all").index.values[0]
                            sub = sub.drop(index=sub_ind)

                            self.pattern_series[si] = sub

                except:
                    print("try again")

            except:
                print("No slit table created yet.")

        return True

    def edit_cb(self, obj):
        """ to be written """
        self.logger.info("object %s has been edited" % (obj.kind))
        tab_row_ind = list(self.SlitTabView.stab.get_column_data(
            0)).index(int(obj.tag.strip("@")))
        self.SlitTabView.stab.select_row(row=tab_row_ind, redraw=True)
        # update slit table data to reflect the new edits
        self.SlitTabView.update_table_row_from_obj(obj, self.fitsimage)
        return True

    def cleanup_kind(self, kind):
        """  
        REMOVE only a specific type of object
        self.cleanup_kind('point')
        self.cleanup_kind('box') 
        """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        # points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        found = CM.CompoundMixin.get_objects_by_kind(self.canvas, str(kind))
        list_found = list(found)
        CM.CompoundMixin.delete_objects(self.canvas, list_found)
        self.canvas.objects  # check that the points are gone

    def push_objects_to_slits(self):
        """ to be written """
        # 1) print all the objects as a astropy region file
        # 2) edit the file into a dmd file
        # 3) load the dmd file
        print("check")


######
#    def donothing(self):
#        """ to be written """
#        pass

######

    def initialize_slit_table(self):
        global slit_window
        slit_window = tk.Toplevel()
        slit_window.title("Slit Table")
        # Creation of init_window
        slit_window.geometry("700x407")
        self.slit_window = slit_window
        self.SlitTabView = STView(self.slit_window, self.container)
        self.slit_window.withdraw()

    def show_slit_table(self):
        """ to be written """

        try:
            # self.SlitTabView.show_tab()
            self.slit_window.deiconify()
        except AttributeError:
            print("no slits to show")

        except:
            # need to remake the table viewing window if it is destroyed
            if not self.slit_window.winfo_exists():

                # preserve the slit data frame so it is republished in the new window
                current_slitDF = self.SlitTabView.slitDF

                self.initialize_slit_table()
                self.SlitTabView.slitDF = current_slitDF
                # re-add the table rows
                if not self.SlitTabView.slitDF.empty:
                    self.SlitTabView.recover_window()
            self.slit_window.deiconify()


######
#    def load_Astrometry(self):
#        """ to be written """
#        # => send center and list coodinates to Astrometry, and start Astrometry!
#        Astrometry().receive_radec([self.ra_center,self.dec_center],[self.ra_list,self.dec_list],self.xy_list)


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load DMD map file
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def LoadMap(self):
        """ to be written """
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename = filedialog.askopenfilename(initialdir=os.path.join(dir_DMD, "DMD_csv", "maps"),
                                              title="Select a File",
                                              filetypes=(("Text files",
                                                          "*.csv"),
                                                         ("all files",
                                                          "*.*")))
        head, tail = os.path.split(filename)
        self.textbox_filename_slits.insert(tk.END, tail)

        myList = []

        with open(filename, 'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        # print(myList)

        for i in range(len(myList)):
            print("Row " + str(i) + ": " + str(myList[i]))

        test_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]), int(
                myList[i][2]):int(myList[i][3])] = int(myList[i][4])

        DMD.apply_shape(test_shape)

        # Create a photoimage object of the image in the path
        # Load an image in the script
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104, 128, image=self.img)
        image_map.close()


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load Slit file
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def LoadSlits(self):
        """ to be written """
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename_slits = filedialog.askopenfilename(initialdir=os.path.join(dir_DMD, "DMD_csv", "slits"),
                                                    title="Select a File",
                                                    filetypes=(("Text files",
                                                                "*.csv"),
                                                               ("all files",
                                                                "*.*")))
        head, tail = os.path.split(filename_slits)
        self.textbox_filename_slits.insert(tk.END, tail)

        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index), int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        self.slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for i in table.index:
            self.slit_shape[x1[i]:x2[i], y1[i]:y2[i]] = 0

        self.push_slits()
        # IP = self.PAR.IP_dict['IP_DMD']
        # [host,port] = IP.split(":")
        # DMD.initialize(address=host, port=int(port))
        # DMD._open()
        # DMD.apply_shape(self.slit_shape)

        # Create a photoimage object of the image in the path
        # Load the image
        # global img
        image_map = Image.open(os.path.join(dir_DMD, "current_dmd_state.png"))
        self.img = ImageTk.PhotoImage(image_map)
        image_map.close()
        # Add image to the Canvas Items
        # print('img =', self.img)
        # self.canvas.create_image(104,128,image=self.img)

    def Save_slittable(self):
        """ to be written """
        if "slit_shape" not in dir(self):
            print("No DMD pattern has been created yet.")
            return
        file = filedialog.asksaveasfile(filetypes=[("csv file", ".csv")],
                                        defaultextension=".csv",
                                        initialdir=os.path.join(
                                            dir_DMD, "DMD_csv", "slits"),
                                        initialfile=self.filename_regfile_RADEC[0:-4]+".csv")
        pandas_slit_shape = pd.DataFrame(self.slit_shape)
        pandas_slit_shape.to_csv(file.name)

# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
#  
#  THREE HADAMARD ROUTINES BEFORE CLOSING
#
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&
# &&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&

    def load_masks_file_HTS(self):
        """load_masks_file for upload on DMD"""
        self.textbox_filename_masks_HTS.delete('1.0', tk.END)
        filename_masks = filedialog.askopenfilename(initialdir=os.path.join(local_dir, "Hadamard", "mask_sets"),
                                                    title="Select a File",
                                                    filetypes=(("Text files",
                                                                "*.bmp"),
                                                               ("all files",
                                                                "*.*")))
        self.head_HTS, self.tail_HTS = os.path.split(filename_masks)
        self.textbox_filename_masks_HTS.insert(tk.END, self.tail_HTS)
        # self.textbox_masknames_HTS.delete("1.0", tk.END)
        # self.entrybox_newmasknames.delete(0, tk.END)
        # self.entrybox_newmasknames.insert(tk.INSERT,str(tail[0:tail.rfind("_")]))

    def push_masks_file_HTS(self):

        # %% Open a file and check that the code worked
        # name = 'H128_3w_mask_a1.bmp'
        # name = 'H16_4w_mask_a1.bmp'
        # name = 'S83_4w_mask_34.bmp'
        # name = 'S11_3w_mask_9.bmp'
        try:
            im = np.asarray(Image.open(os.path.join(
                self.head_HTS, self.tail_HTS)), dtype='int')
        # plt.imshow(im, cmap='gray')
        except:
            messagebox.showinfo(title='INFO', message='No mask')
            return
        DMD.initialize()
        DMD.apply_shape(im)
        # DMD.apply_invert()   #INVERT to push the pattern to SAMI, comment to see the mask on SISI

        self.textbox_filename_masks_HTS_pushed.delete("1.0", tk.END)
        self.textbox_filename_masks_HTS_pushed.insert(tk.END, self.tail_HTS)

    def next_masks_file_HTS(self):
        """look at the currently loaded mask and push the next one to the DMD"""

        # => find all positions of the '_' string in the filename
        i_ = [x for x, v in enumerate(self.tail_HTS) if v == '_']

        # identify order, "signature ("a", "b", or "_" for H and S matrices) and counter of the current mask
        order = self.tail_HTS[1:i_[0]]
        ab_ = self.tail_HTS[i_[-1]-1]
        counter = self.tail_HTS[i_[-1]+1:i_[-1]+4]

        # if we have reached the last mask and we are not in Hmask_a, exit with message
        if ((int(counter) == int(order)) and (ab_ != 'a')):
            print("exit")
            messagebox.showinfo(title='INFO', message='No mask')
            return

        # increment and set as the current mask:
        str1 = self.tail_HTS
        list1 = list(str1)
        if ab_ == 'a':  # Hmask_a goes to Hmask_b
            list1[i_[-1]-1] = 'b'
        elif ab_ == 'b':  # Hmask_b goes to Hmask_a with increment of counter
            list1[i_[-1]-1] = 'a'
            counter_plus1 = "{:03d}".format(int(counter)+1)
            list1[i_[-1]+1:i_[-1]+4] = list(counter_plus1)
        else:  # Smask increment of counter
            counter_plus1 = "{:03d}".format(int(counter)+1)
            list1[i_[-1]+1:i_[-1]+4] = list(counter_plus1)
        self.tail_HTS = ''.join(list1)

        # Push to the DMD
        self.push_masks_file_HTS()

    """
    Generic File Writer
    02/21/23 mr - to be tested!
    """
    def save(file_type):
        """ to be written """
        if file_type == None:
            files = [('All Files', '*.*')]
        elif file_type == 'py':
            files = [('Python Files', '*.py')]
        elif file_type == 'txt':
            files == ('Text Document', '*.txt')
        elif file_type == 'csv':
            files == ('DMD grid', '*.csv')
        file = filedialog.asksaveasfile(
            filetypes=files, defaultextension=files)

        # btn = ttk.Button(self, text = 'Save', command = lambda : save())

    def create_menubar(self, parent):
        """ to be written """
        
        parent.geometry("1400x900")  # was ("1280x900")
        if platform == "win32":
            parent.geometry("1400x920")
        parent.title("SAMOS Main Page")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar


















"""
#############################################################################################################################################
#
# ---------------------------------------- GUIDESTAR PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class GuideStarPage(tk.Frame):
    """ to be written """

    def __init__(self, parent, container):
        """ to be written """
        super().__init__(container)

        #self.DMDPage = DMDPage
        self.PAR = SAMOS_Parameters()
        self.ConfP = ConfigPage(parent,container)

        self.container = container
        

        logger = log.get_logger("example2", options=None)
        self.logger = logger

        label = tk.Label(self, text="Main Page", font=('Times', '20'))
        label.pack(pady=0, padx=0)

        # ADD CODE HERE TO DESIGN THIS PAGE
        if platform == "win32":
            self.bigfont = ("Arial", 12, 'bold')
            self.bigfont_20 = ("Arial", 12, 'bold')
            self.bigfont_15 = ("Arial", 10, 'bold')
        else:
            self.bigfont = ("Arial", 24)
            self.bigfont_20 = ("Arial", 20)
            self.bigfont_15 = ("Arial", 15)

        # keep track of the entry number for header keys that need to be added
        # will be used to write "OtherParameters.txt"
        self.extra_header_params = 0
        # keep string of entries to write to a file after acquisition.
        self.header_entry_string = ''
        main_fits_header.create_main_params_dict()
        self.wcs = None
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        #self.SlitTabView = None
        self.loaded_regfile = None
        today = datetime.now()
        self.fits_dir = os.path.join(
            parent_dir, "SISI_images", "SAMOS_" + today.strftime('%Y%m%d'))



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    OBSERVER/NIGHT INFO Label Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.wcs_exist = None





# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #    FITS manager
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame_FITSmanager = tk.Frame(self, background="pink")
        self.frame_FITSmanager.place(
            x=10, y=10, anchor="nw", width=420, height=190)

        labelframe_FITSmanager = tk.LabelFrame(
            self.frame_FITSmanager, text="FITS manager", font=self.bigfont)
        labelframe_FITSmanager.pack(fill="both", expand="yes")

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#
#
#         label_FW1 =  tk.Label(labelframe_Filters, text="Filter Wheel 1")
#         label_FW1.place(x=4,y=10)
#         entry_FW1 = tk.Entry(labelframe_Filters, width=5,  bd =3)
#         entry_FW1.place(x=100, y=10)
#         label_FW2 =  tk.Label(labelframe_Filters, text="Filter Wheel 2")
#         label_FW2.place(x=4,y=40)
#         entry_FW2 = tk.Entry(labelframe_Filters, width=5, bd =3)
#         entry_FW2.place(x=100, y=40)
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

#        button_FITS_Load = tk.Button(labelframe_FITSmanager, text="Load existing file", bd=3,
#                                     command=self.load_existing_file)
#        button_FITS_Load.place(x=0, y=0)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#       RA, DEC Entry box
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.string_RA = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA.set("150.17110")  # NGC 3105
        label_RA = tk.Label(labelframe_FITSmanager, text="RA:",  bd=3)
        self.entry_RA = tk.Entry(
            labelframe_FITSmanager, width=11,  bd=3, textvariable=self.string_RA)
        label_RA.place(x=150, y=1)
        self.entry_RA.place(x=190, y=-5)

        """ DEC Entry box"""
        self.string_DEC = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC.set("-54.79004")  # NGC 3105
        label_DEC = tk.Label(labelframe_FITSmanager, text="Dec:",  bd=3)
        self.entry_DEC = tk.Entry(
            labelframe_FITSmanager, width=11,  bd=3, textvariable=self.string_DEC)
        label_DEC.place(x=150, y=20)
        self.entry_DEC.place(x=190, y=20)
        
        """
        button_RADEC_to_SOAR = tk.Button(labelframe_FITSmanager, text="Send to SOAR", bd=3,
                             command=self.send_RADEC_to_SOAR)
        button_RADEC_to_SOAR.place(x=300, y=8)
        """
        
        
# =============================================================================
#      QUERY Server
#
# =============================================================================
        labelframe_Query_Survey = tk.LabelFrame(labelframe_FITSmanager, text="Query Image Server",
                                                width=400, height=110,
                                                font=self.bigfont)
        labelframe_Query_Survey.place(x=5, y=45)


        self.label_SelectSurvey = tk.Label(
            labelframe_Query_Survey, text="Survey")
        self.label_SelectSurvey.place(x=5, y=5)
#        # Dropdown menu options
        Survey_options = [
            "SkyMapper",
            "SDSS",
            "PanSTARRS/DR1/", #SIMBAD - 
            "DSS",          #SIMBAD - 
            "DSS2/red",     #SIMBAD - 
            "CDS/P/AKARI/FIS/N160", #SIMBAD - 
            "2MASS/J",      #SIMBAD -  
            "GALEX",        # SIMBAD - 
            "AllWISE/W3"]   # SIMBAD - 
#        # datatype of menu text
        self.Survey_selected = tk.StringVar()
#        # initial menu text
        self.Survey_selected.set(Survey_options[0])
#        # Create Dropdown menu
        self.menu_Survey = tk.OptionMenu(
            labelframe_Query_Survey, self.Survey_selected,  *Survey_options)
        # add bar to split menu, see
        # https://stackoverflow.com/questions/55621073/add-a-separator-to-an-option-menu-in-python-with-tkinter
        self.menu_Survey['menu'].insert_separator(3)
        self.menu_Survey.place(x=65, y=3)

#        self.readout_Simbad = tk.Label(self.frame0l, text='')


#        """ SkyMapper Query """
#        #button_skymapper_query = tk.Button(labelframe_FITSmanager, text="SkyMapper Query", bd=1,
#        #                                   command=self.SkyMapper_query)
#        #button_skymapper_query.place(x=190, y=65)
#
#        """ SkyMapper or SDSS query"""
#        griz_Survey_options = [
#            "SkyMapper Query",
#            "SDSS Query"]
#        # datatype of menu text
#        self.griz_Survey_selected = tk.StringVar()
#        # initial menu text
#        self.griz_Survey_selected.set(griz_Survey_options[0])
#        # Create Dropdown menu
#        self.griz_menu_Survey = tk.OptionMenu(
#            labelframe_FITSmanager, self.griz_Survey_selected,  *griz_Survey_options)
#        self.griz_menu_Survey.place(x=190, y=65)

        
        
        """ Filter Entry box"""
        self.string_Filter = tk.StringVar()
        self.string_Filter.set("i")
        label_Filter = tk.Label(labelframe_Query_Survey, text='Filter:',  bd=3)
        entry_Filter = tk.Entry(labelframe_Query_Survey,
                                width=2,  bd=3, textvariable=self.string_Filter)
        label_Filter.place(x=195, y=5)
        entry_Filter.place(x=240, y=3)
        
        """ QUERY BUTTON"""
        button_Query_Survey = tk.Button(
            labelframe_Query_Survey, text="Query", bd=3, command=self.Query_Survey)
        button_Query_Survey.place(x=300, y=3)


        """ Nr. of Stars Entry box"""
        """
        label_nrofstars = tk.Label(
            labelframe_Query_Survey, text="Nr. of stars:")
        label_nrofstars.place(x=5, y=36)
        self.nrofstars = tk.IntVar()
        entry_nrofstars = tk.Entry(
            labelframe_Query_Survey, width=3,  bd=3, textvariable=self.nrofstars)
        entry_nrofstars.place(x=80, y=35)
        self.nrofstars.set('25')
        """
        
        
        """ twirl Astrometry"""
        """
        button_twirl_Astrometry = tk.Button(labelframe_Query_Survey, text="twirl WCS", bd=3,
                                            command=self.twirl_Astrometry)
        button_twirl_Astrometry.place(x=120, y=35)
        """
        
        """ find stars"""
        """
        button_find_stars = tk.Button(labelframe_Query_Survey, text="Find stars", bd=3,
                                            command=self.find_stars, state='active')#'disabled')
        button_find_stars.place(x=220, y=35)
        self.button_find_stars = button_find_stars
        """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#        button_Astrometry =  tk.Button(labelframe_FITSmanager, text="Astrometry", bd=3,
#                                            command=Astrometry)
#                                            command=self.load_Astrometry)
#        button_Astrometry.place(x=0,y=110)

#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# GINGA DISPLAY
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=450, y=0, anchor="nw")  # , width=500, height=800)
        # self.vb = vbox

#        canvas = tk.Canvas(vbox, bg="grey", height=514, width=522)
        canvas = tk.Canvas(vbox, bg="grey", height=800, width=800)#1032, width=1056)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # => ImageViewTk -- a backend for Ginga using a Tk canvas widget
        fi = CanvasView(logger)
        # => Call this method with the Tkinter canvas that will be used for the display.
        fi.set_widget(canvas)
        # fi.set_redraw_lag(0.0)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        # fi.enable_draw(False)
        # tk seems to not take focus with a click
        fi.set_enter_focus(True)
        fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        canvas = self.canvas_types.DrawingCanvas()
        canvas.enable_draw(True)
        canvas.enable_edit(True)
        canvas.set_drawtype('box', color='red')
#        canvas.set_drawtype('point', color='red')
        canvas.register_for_cursor_drawing(fi)
#        canvas.add_callback('draw-event', self.draw_cb)
#        canvas.set_draw_mode('draw')
        canvas.add_callback('pick-up', self.pick_cb,'up')
        canvas.set_draw_mode('pick')
        # without this call, you can only draw with the right mouse button
        # using the default user interface bindings
        # canvas.register_for_cursor_drawing(fi)

        canvas.ui_set_active(True)
        self.canvas = canvas


#        # add canvas to viewers default canvas
        fi.get_canvas().add(canvas)

        self.drawtypes = canvas.get_drawtypes()
        self.drawtypes.sort()

#        fi.configure(516, 528) #height, width
        fi.set_window_size(1028, 1044)

        self.readout = tk.Label(vbox, text='')
        self.readout.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
        # self.readout.place()





# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
#  #   Guide Star Pickup Frame
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        # , width=400, height=800)
        self.frame_SlitConf = tk.Frame(self, background="gray")
        self.frame_SlitConf.place(
            x=10, y=210, anchor="nw", width=420, height=180)
        labelframe_SlitConf = tk.LabelFrame(self.frame_SlitConf, text="Guide Star Pickup",
                                            font=self.bigfont)
        labelframe_SlitConf.pack(fill="both", expand="yes")
        
        """
        self.Draw_Edit_Pick_Checked = tk.StringVar(None, "draw")
        btn1 = tk.Radiobutton(labelframe_SlitConf, text="Draw", padx=6, pady=1,
                              variable=self.Draw_Edit_Pick_Checked, value="draw", command=self.set_mode_cb)
        # btn1.pack(anchor='ne')
        btn1.place(x=220, y=25)
        btn2 = tk.Radiobutton(labelframe_SlitConf, text="Edit", padx=10, pady=1,
                              variable=self.Draw_Edit_Pick_Checked, value="edit", command=self.set_mode_cb)
        btn2.place(x=220, y=50)  # pack(anchor='ne')
        btn3 = tk.Radiobutton(labelframe_SlitConf, text="Delete", padx=9, pady=1,
                              variable=self.Draw_Edit_Pick_Checked, value="pick", command=self.set_mode_cb)
        btn3.place(x=220, y=75)  # pack(anchor='ne')
        """

#        self.deleteChecked = tk.IntVar()
#        btn4 = tk.Checkbutton(labelframe_SlitConf, text="Delete Picked", padx=5, pady=1,
#                              variable=self.deleteChecked)
#        btn4.place(x=280, y=75)

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    Low Mag (bright end)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        label_low_mag = tk.Label(labelframe_SlitConf,
                                text="low mag")
        label_low_mag.place(x=4, y=4)
        self.low_mag = tk.IntVar()
        self.low_mag.set(11)
        self.textbox_low_mag = tk.Entry(
            labelframe_SlitConf, textvariable=self.low_mag, width=4)
        # self.textbox_low_mag.place(x=130,y=5)

        low_mag_SpinBox = tk.Spinbox(labelframe_SlitConf,
                                      command=self.check_valid_mags, increment=1,
                                      textvariable=self.low_mag, width=5,
                                      from_=0, to=25)
        low_mag_SpinBox.place(x=100, y=4)
        low_mag_SpinBox.bind("<Return>", self.check_valid_mags)
        #self.low mag = low mag


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    High mag (faint end)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        label_high_mag = tk.Label(labelframe_SlitConf,
                                text="high mag")
        label_high_mag.place(x=4, y=29)
        self.high_mag = tk.IntVar()
        self.high_mag.set(13)
        self.textbox_high_mag = tk.Entry(
            labelframe_SlitConf, textvariable=self.high_mag, width=4)
        # self.textbox_high_mag.place(x=130,y=30)

        high_mag_SpinBox = tk.Spinbox(labelframe_SlitConf,
                                       command=self.check_valid_mags, increment=1,
                                       textvariable=self.high_mag, width=5,
                                       from_=0, to=25)
        high_mag_SpinBox.place(x=100, y=30)
        high_mag_SpinBox.bind("<Return>", self.check_valid_mags)
        #self.high_mag = high mag

# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    SLIT POINTER ENABLED
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        self.GuideStarPickup_ChkBox_Enabled = tk.IntVar()
        self.GuideStarPickup_ChkBox_Enabled.set(1)
        
        GS_pickb = tk.Button(labelframe_SlitConf, text="Pick Guide Star",
                               command=self.Pick_GuideStar)
        GS_pickb.place(x=220, y=0)
                
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#  #    RADEC OF CANDIDATE GUIDE STAR
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
        """ RA Entry box"""
        self.string_RA_GS = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA_GS.set("150.17110")  # NGC 3105
        Label_RA_GS = tk.Label(labelframe_SlitConf, text='RA:',  bd=3)
        Entry_RA_GS = tk.Entry(
            labelframe_SlitConf, width=9,  bd=3, textvariable=self.string_RA_GS)
        Label_RA_GS.place(x=5, y=51)
        Entry_RA_GS.place(x=45, y=51)

        """ DEC Entry box"""
        self.string_DEC_GS = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC_GS.set("-54.79004")  # NGC 3105
        Label_DEC_GS = tk.Label(labelframe_SlitConf, text='Dec:',  bd=3)
        Entry_DEC_GS = tk.Entry(
            labelframe_SlitConf, width=9,  bd=3, textvariable=self.string_DEC_GS)
        Label_DEC_GS.place(x=5, y=71)
        Entry_DEC_GS.place(x=45, y=71)
        
        """ X shift"""
        self.string_Xmm_GS = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_Xmm_GS.set("150.17110")  # NGC 3105
        Label_Xmm_GS = tk.Label(labelframe_SlitConf, text='X(mm)',  bd=3)
        Entry_Xmm_GS = tk.Entry(
            labelframe_SlitConf, width=9,  bd=3, textvariable=self.string_Xmm_GS)
        Label_Xmm_GS.place(x=145, y=51)
        Entry_Xmm_GS.place(x=195, y=51)

        """ Y shift"""
        self.string_Ymm_GS = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_Ymm_GS.set("-54.79004")  # NGC 3105
        Label_Ymm_GS = tk.Label(labelframe_SlitConf, text='Y(mm)',  bd=3)
        Entry_Ymm_GS = tk.Entry(
            labelframe_SlitConf, width=9,  bd=3, textvariable=self.string_Ymm_GS)
        Label_Ymm_GS.place(x=145, y=71)
        Entry_Ymm_GS.place(x=195, y=71)

        """ magnitude"""
        self.string_mag_GS = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
#        self.string_mag_GS.set("-54.79004")  # NGC 3105
        Label_mag_GS = tk.Label(labelframe_SlitConf, text='Mag',  bd=3)
        Entry_mag_GS = tk.Entry(
            labelframe_SlitConf, width=5,  bd=3, textvariable=self.string_mag_GS)
        Label_mag_GS.place(x=295, y=65)
        Entry_mag_GS.place(x=340, y=64)


        button_RADEC_to_SOAR = tk.Button(labelframe_SlitConf, text="Accept Guide Star", bd=3,
                             command=self.send_RADEC_to_SOAR)
        button_RADEC_to_SOAR.place(x=5, y=100)




        """
        HORIZONTAL BOX AT THE BOTTOM WITH ORIGINAL GINGA TOOLS
        """

        hbox = tk.Frame(self)
        hbox.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.drawtypes = canvas.get_drawtypes()
        # wdrawtype = ttk.Combobox(self, values=self.drawtypes,
        # command=self.set_drawparams)
        # index = self.drawtypes.index('ruler')
        # wdrawtype.current(index)
        wdrawtype = tk.Entry(hbox, width=12)
        wdrawtype.insert(0, 'box')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype

        wdrawcolor = ttk.Combobox(
            hbox, values=self.drawcolors, style="TCombobox")  # ,
        #                           command=self.set_drawparams)
        index = self.drawcolors.index('red')
        wdrawcolor.current(index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        # wdrawcolor = tk.Entry(hbox, width=12)
        # wdrawcolor.insert(0, 'blue')
        # wdrawcolor.bind("<Return>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor

        self.vfill = tk.IntVar()
        wfill = tk.Checkbutton(hbox, text="Fill", variable=self.vfill)
        self.wfill = wfill

        walpha = tk.Entry(hbox, width=12)
        walpha.insert(0, '1.0')
        walpha.bind("<Return>", self.set_drawparams)
        self.walpha = walpha

        wrun = tk.Button(hbox, text="Slits Only",
                         command=self.slits_only)
        wclear = tk.Button(hbox, text="Clear Canvas",
                           command=self.clear_canvas)
        wsave = tk.Button(hbox, text="Save Canvas",
                          command=self.save_canvas)
        wopen = tk.Button(hbox, text="Open File",
                          command=self.open_file)
        # pressing quit button freezes application and forces kernel restart.
        wquit = tk.Button(hbox, text="Quit",
                          #command=lambda: self.quit(self))
                          command=self.MASTER_quit)

        for w in (wquit, wsave, wclear, wrun, walpha, tk.Label(hbox, text='Alpha:'),
                  #                  wfill, wdrawcolor, wslit, wdrawtype, wopen):
                  wfill, wdrawcolor, wdrawtype, wopen):
            w.pack(side=tk.RIGHT)

        # mode = self.canvas.get_draw_mode() #initially set to draw by line >canvas.set_draw_mode('draw')


        



# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#
# Load AP Region file in RADEC
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#    def save_regions_DMD_AstropyReg(self):
#        """ to be written """
#        pass

#    def push_DMD(self):
#        """ to be written """
#        pass

        """
    def load_regfile_csv(self):
        """
        """ to be written """
        """
        self.LoadSlits()
        pass
        """
        
        
        """
    def save_regions_xy2xyfile(self):
        """    
        """ Save (x,y) Astropy Regions to .reg file """
        """ converting Ginga Regions to AP/radec Regions
            - collects/compound all Ginga Regions in RRR_xyGA
            - convert to AP/xy   (aka RRR_xyAP)
            - write to AP/xy .region file
                => requires WCS
        """
        """
        print("saving (x,y) Astropy Regions to .reg file")
        file = filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                        defaultextension=".reg",
                                        initialdir=os.path.join(local_dir, "SAMOS_regions", "pixels"))
        # 1. Collect all
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        # 2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        # 3. Write astropy regions, pixels
        self.RRR_xyAP.write(file.name, overwrite=True)
        print("(x,y) Astropy Regions to .reg file:\n", file.name)
        """

#    def push_CCD(self):
#        """ to be written """
#        pass

#    def change_out_fnumber(self):
#        """
#        Returns
#        -------
#        Incremental change in Exposure number to be appended to the end of filenames.
#
#        """
#        return
    
        """
    def write_GingaRegions_ds9adFile(self):
        """
        """ collect all Ginga regions and save to a ds9/ad .reg file
            - collect all Ginga xy Regions in a AP/ad list
                uses convert_GAxy_APad()
            - wites the AP/ad on file list as set of ds9/ad region files
        """
        
        """
        if "RRR_RADec" not in dir(self):
            print("There are no (RA,Dec) regions to be written on file")
            return
        else:
            print("saving (RA,DEC) Astropy Regions to .reg file")
            file = filedialog.asksaveasfile(filetypes=[("txt file", ".reg")],
                                            defaultextension=".reg",
                                            initialdir=os.path.join(local_dir, "SAMOS_regions", "RADEC"))
        # we want to scoop all objects on the canvas
        # obj_all = CM.CompoundMixin.get_objects(self.canvas)
            self.RRR_RADec = self.convert_GAxy_APad()
            print("\ncollected all Ginga xy Regions in a AP/ad list (aka RRR_RADec")
            self.RRR_RADec.write(file.name, overwrite=True)
            print("saved  AP/ad list to ds/ad region file file:\n", file.name)
            print(
                "\ncollected all Ginga xy Regions to ads/ad region file file:\n", file.name)
        """    

        """
    def save_RADECregions_AstropyXYRegFile(self):
        print("saving (x,y) Astropy Regions to .reg file")
        self.display_ds9ad_GingaAP()
        file = filedialog.asksaveasfile(filetypes = [("txt file", ".reg")],
                                        defaultextension = ".reg",
                                        initialdir=local_dir+"/SAMOS_regions/pixels")
        self.RRR_xyAP.write(file.name, overwrite=True)
        """
    
        """
    def display_ds9ad_Ginga(self):
        """    
        """ converting ds9/radec Regions to AP/radec Regions
            - open ds9/radec region file and convert to AP/xy (aka RRR_xyAP)
                -> requires WCS
            - convert AP/xy to Ginga/xy (aka RRR_xyGA)
            - convert AP/xy to AP/ad (aka RRR_RADec)
        """
        
        """
        print("displaying ds9/radec Regions on Ginga\n")
        # requires wcs: class AStrometry
        if 'wcs' not in dir(self):
            print("missing self.wcs. No operation performed \n")
            return
        self.RRR_xyAP = Astrometry.APRegion_RAD2pix(
            self.filename_regfile_RADEC, self.wcs)
        print("\nopened ds9/radec region file and converted to AP/xy (aka RRR_xyAP)\n => used current WCS")

        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("\nconverted AP/xy to Ginga/xy (aka RRR_xyGA)")

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP, self.wcs)
        print("converted AP/xy to APradec (aka RRR_RADec)")
        self.SlitTabView.load_table_from_regfile_RADEC(regs_RADEC=self.RRR_RADec,
                                                       img_wcs=self.wcs)
        print("displayed APradec regions on Ginga display")

        # return self.RRR_xyAP
        """

        """
    def convert_GAxy_APad(self):
        """
        """ converting Ginga Regions to AP/radec Regions
            - collects/compound all Ginga Regions in RRR_xyGA
            - convert tho AP/xy   (aka RRR_xyAP)
            - convert to AP/radec (aka RRR_RADec)
                => requires WCS
        """
        
        """
        print("converting Ginga Regions to AP/radec Regions")
        # requires wcs: class AStrometry
        if 'wcs' not in dir(self):
            print("missing self.wcs. No operation performed \n")
            return
        # 1. Collect all objects in ginga canvas
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("\ncollected/compounded all Ginga Regions in RRR_GAxy")
        # 2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        print("converted GA/xy to AP/xy   (aka RRR_xyAP)")
        # 3. convert to RADEC using wcs
        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP, self.wcs)
        print("converted AP/xy converted to AP/ad (aka RRR_RADec")
        print("\nCompleted conversion Ginga Regions to AP/radec Regions ")
        return self.RRR_RADec
        """

        """
    def draw_slits(self):
        """
        """
        # all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        # color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas, color="red")
        # [print("draw-slits obj tags ", obj.tag) for obj in all_ginga_objects]
        CM.CompoundMixin.draw(self.canvas, self.canvas.viewer)
        """
        """
    def convert_regions_xyAP2slit(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        # color in RED all the regions loaded from .reg file
        # requires Dana wcs
        # returns .csv map file
        pass
        """

        """
    def convert_regions_slit2xyAP(self):
        """
        """ to be written """
        """
        # requires Dana wcs
        # returns RRR_xyAP
        pass
        """

        """
    def convert_regions_xyAP2xyGA(self):
        """
        """ converting (x,y) Astropy Regions to (x,y) Ginga Regions """
        """
        print("converting (x,y) Astropy Regions to (x,y) Ginga Regions")

        # cleanup, keep only the slits
        self.slits_only()

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        # [CM.CompoundMixin.add_object(self.canvas,r2g(reg)) for reg in self.RRR_xyAP]
        for reg in range(len(self.RRR_xyAP)):
            this_reg = self.RRR_xyAP[reg]
            this_obj = r2g(this_reg)
            this_obj.pickable = True
            this_obj.add_callback('pick-down', self.pick_cb, 'down')
            this_obj.add_callback('pick-up', self.pick_cb, 'up')

            this_obj.add_callback('pick-key', self.pick_cb, 'key')
            self.canvas.add(this_obj)
            # ap_region.add_region(self.canvas, this_reg)
            if reg < 10 or reg == len(self.RRR_xyAP)-1:
                print("reg number {} tag: {}".format(reg, this_obj.tag))
            self.SlitTabView.slit_obj_tags.append(this_obj.tag)
        # [print("cm object tags", obj.tag) for obj in self.canvas.get_objects()]
        # uses r2g
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("(x,y) Astropy regions converted to (x,y) Ginga regions\nRRR_xyGA created")
        return self.RRR_xyGA
        # self.RRR_xyGA is a self.canvas.objects
        """

        """
     def convert_regions_xyGA2xyAP(self):
         """    
        """ converting (x,y) Ginga Regions to (x,y) Astropy Regions """
        """
        print("converting (x,y) Ginga Regions to (x,y) Astropy Regions")
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        list_all_ginga_objects = list(all_ginga_objects)
        if len(list_all_ginga_objects) != 0:
            self.RRR_xyAP = Regions([g2r(list_all_ginga_objects[0])])
            for i in range(1, len(list_all_ginga_objects)):
                self.RRR_xyAP.append(g2r(list_all_ginga_objects[i]))
        return self.RRR_xyAP
        print("(x,y) Ginga regions converted to (x,y) Astropy regions")
        """
        """    
    def push_RADEC(self):
        """
        """ to be written """
        """
        self.string_RA = tk.StringVar(self, self.RA_regCNTR)
        self.string_DEC = tk.StringVar(self, self.DEC_regCNTR)
        self.entry_RA.delete(0, tk.END)
        self.entry_DEC.delete(0, tk.END)
        self.entry_RA.insert(0, self.RA_regCNTR)
        self.entry_DEC.insert(0, self.DEC_regCNTR)
        print("RADEC loaded")
        """

        """
    def load_regfile_RADEC(self):
        """
        """ read (RA,DEC) Regions from .reg file
        - open ds9/ad file and read the regions files creating a AP/ad list of regions (aka RRR_RADec)
        - extract center RA, Dec
        """
        """
        print("read ds9/ad .reg file to create AP/ad regions (aka RRR_RADec")
        self.textbox_filename_regfile_RADEC.delete('1.0', tk.END)
#        self.textbox_filename_slits.delete('1.0', tk.END)
        self.filename_regfile_RADEC = filedialog.askopenfilename(initialdir=os.path.join(local_dir, "SAMOS_regions", "RADEC"),
                                                                 title="Select a File",
                                                                 filetypes=(("Text files",
                                                                             "*.reg"),
                                                                            ("all files",
                                                                             "*.*")))
        self.loaded_regfile = os.path.split(self.filename_regfile_RADEC)[1]
        # First read the file and set the regions in original RADEC units
        self.RRR_RADec = Regions.read(
            self.filename_regfile_RADEC, format='ds9')
        filtered_duplicates_regions = []
        for reg in self.RRR_RADec:
            if reg not in filtered_duplicates_regions:
                filtered_duplicates_regions.append(reg)

        self.RRR_RADec = filtered_duplicates_regions
        #
        # Then extract the clean filename to get RA and DEC of the central point
        head, tail = os.path.split(self.filename_regfile_RADEC)
        self.textbox_filename_regfile_RADEC.insert(tk.END, tail)
        
        # find the opject t name reading all characters up to the first "_"
        self.target_name = tail[0:tail.find("_")] 
        
        #write the object name in the Science tab
        self.ObjectName.set(self.target_name)        
                
        # the filename must carry the RADEC coordinates are "RADEC_". Find this string...
        s = re.search(r'RADEC=', tail)
        # extract RADEC
        RADEC = tail[s.end():-4]
        RA_cut = (re.findall('.*-', RADEC))
        # and RA, DEC as strings at disposal
        self.RA_regCNTR = RA_cut[0][:-1]
        self.DEC_regCNTR = (re.findall('-.*', RADEC))[0]
        # we return the filename
        print("(RA,DEC) Regions loaded from .reg file")

        return self.filename_regfile_RADEC
        """

        """
    def load_ds9regfile_xyAP(self):
        """
        """ read (x,y) Astropy  Regions from ds9 .reg file
            - open ds9 .reg file in pixels units
            - extract the clean filename to get RA and DEC of the central point
            - create AP.xy regions (aka RRR_xyAP)
            - visualize xyAP regions on GINGA display\n
                => WCS solution needed
            - convert xyAP regions to GINGA regions (aka RRR_xyGA)
        """
        
        """
        print("\n Load ds9/xy reg. file")
        reg = filedialog.askopenfilename(filetypes=[("region files", "*.reg")],
                                         initialdir=os.path.join(local_dir, 'SAMOS_regions', 'pixels'))
        print("reading (x,y) Astropy region file")
        if isinstance(reg, tuple):
            regfileName = reg[0]
        else:
            regfileName = str(reg)
        # if len(regfileName) != 0:

        # Then
        head, tail = os.path.split(regfileName)
        self.loaded_regfile = regfileName
        self.textbox_filename_regfile_xyAP.insert(tk.END, tail)

        self.RRR_xyAP = Regions.read(regfileName, format='ds9')
        print("created AP.xy regions (aka RRR_xyAP)")
        filtered_duplicates_regions = []
        for reg in self.RRR_xyAP:
            if reg not in filtered_duplicates_regions:
                filtered_duplicates_regions.append(reg)

        self.RRR_xyAP = filtered_duplicates_regions
        print("eliminated duplicated regions")

        if self.SlitTabView is None:
            # self.SlitTabView = STView()
            self.initialize_slit_table()

        self.SlitTabView.load_table_from_regfile_CCD(regs_CCD=self.RRR_xyAP,
                                                     img_wcs=self.wcs)
        # if the image has a wcs, it will be used to get sky coords
        print("xyAP regions visualized on GINGA display\n   => WCS solution needed")

        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("convert xyAP regions to GINGA regions (aka RRR_xyGA)")
        # [print("first 10 xyAP obj tags ", obj.tag) for obj in self.canvas.get_objects()[:10]]

        # [print("last 10 xyAP obj tags ", obj.tag) for obj in self.canvas.get_objects()[-10:]]
        print("number of regions: ", len(self.canvas.get_objects()))
        # self.display_region_file()
        print("ds9/xy regions loaded in Ginga")
        # regfile = open(regfileName, "r")
        """
    """
    def display_region_file(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        # color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas,color="red")
    """
    """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
# DONE WITH THE FIELDS
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
    """
    
    def regfname_handle_focus_out(self, _):
        """ to be written """

        current_text = self.regfname_entry.get()
        if current_text.strip(" ") == "":
            # self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg='grey')
            self.regfname_entry.config(bg='white')
            self.regfname_entry.insert(0, "enter pattern name")

    def regfname_handle_focus_in(self, _):
        """ to be written """

        current_text = self.regfname_entry.get()
        if current_text == "enter pattern name":

            self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg="black")

    def write_slits(self):
        """ to be written """
        # when writing a new DMD pattern, put it in the designated directory
        # don't want to clutter working dir.
        # At SOAR, this should be cleared out every night for the next observer
        created_patterns_path = path / Path("Astropy Regions/")
        pattern_name = self.regfname_entry.get()
        # check if pattern name has been proposed
        if (pattern_name.strip(" ") == "") or (pattern_name == "enter pattern name"):
            # if there is no pattern name provided, use a default based on
            # number of patterns already present
            num_patterns_thus_far = len(os.listdir(created_patterns_path))
            pattern_name = "pattern_reg{}.reg".format(num_patterns_thus_far)

        pattern_path = created_patterns_path / Path(pattern_name)

        # create astropy regions and save them after checking that there is something to save...
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas,'rectangle')
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'box')

        list_slits = list(slits)
        if len(list_slits) != 0:
            RRR = Regions([g2r(list_slits[0])])
            for i in range(1, len(list_slits)):
                RRR.append(g2r(list_slits[i]))
        RRR.write(str(pattern_path)+'.reg', overwrite=True)
        print("\nSlits written to region file\n")

    def collect_slit_shape(self):
        """
        collect selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)

        try:
            pattern_list_index = self.pattern_group_dropdown.current()
            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects = [self.canvas.get_object_by_tag(
                tag) for tag in current_pattern_tags]
        except:
            pass

        # counter = 0
        self.slit_shape = np.ones((1080, 2048))  # This is the size of the DC2K
        for obj in objects:
            print(obj)
          
            # force Orthonormal orientation if checkbox is set
            # This function is called if a checkbox forces the slits to be Orthonormal on the DMD. 
            # This is intended to havoid having slightly diagonal slits when the position angle of the image is not exactly 
            # oriented with the celestial coordinates
            if self.Orthonormal_ChkBox_Enabled.get() == 1:
                obj.rot_deg = 0.0
                
            ccd_x0, ccd_y0, ccd_x1, ccd_y1 = obj.get_llur()
            # first case: figures that have no extensions (i.e. points): do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1, y1 = convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1, y1] = 0
            elif self.GuideStarPickup_ChkBox_Enabled.get() == 1 and obj.kind == 'point':
                x1, y1 = convert.CCD2DMD(ccd_x0, ccd_y0)
                x1, y1 = int(np.floor(x1)), int(np.floor(y1))
                x2, y2 = convert.CCD2DMD(ccd_x1, ccd_y1)
                x2, y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))

                # dmd_corners[:][1] = corners[:][1]+500
                ####
                # x1 = round(dmd_corners[0][0])
                # y1 = round(dmd_corners[0][1])+400
                # x2 = round(dmd_corners[2][0])
                # y2 = round(dmd_corners[2][1])+400
                """
                # 3 load the slit pattern
                data_box = self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]), len(good_box[1]))
                """ paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_x):  # scanning multiple rows means each steps moves up along the y axis
                    # the indices of the y values pertinent to that x
                    iy = np.where(good_box_x == i)
                    iymin = min(iy[0])  # the smallest y index
                    iymax = max(iy[0])  # last largest y index
                    cx0 = ccd_x0 + i  # so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cy0 = ccd_y0 + good_box_y[iymin]
                    cy1 = ccd_y0 + good_box_y[iymax]
                    # get the lower value of the column at the x position,
                    x1, y1 = convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = convert.CCD2DMD(cx0, cy1)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y2+1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y2+1,x1-2:x1] = 1
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """ paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_y):  # scanning multiple rows means each steps moves up along the y axis
                    # the indices of the y values pertinent to that x
                    ix = np.where(good_box_y == i)
                    ixmin = min(ix[0])  # the smallest y index
                    ixmax = max(ix[0])  # last largest y index
                    cy0 = ccd_y0 + i  # so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cx0 = ccd_x0 + good_box_x[ixmin]
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    # get the lower value of the column at the x position,
                    x1, y1 = convert.CCD2DMD(cx0, cy0)
                    x1, y1 = int(np.round(x1)), int(np.round(y1))
                    x2, y2 = convert.CCD2DMD(cx1, cy0)    # and the higher
                    x2, y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1, x2, y1, y2)
                    self.slit_shape[x1-2:x2+1, y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1, y1-2:y1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y1,x1-2:x1] = 1
                """
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """
       #     self.slit_shape[x1:x2,y1:y2]=0
#        IP = self.PAR.IP_dict['IP_DMD']
#        [host,port] = IP.split(":")
#        DMD.initialize(address=host, port=int(port))
#        DMD._open()
#        DMD.apply_shape(self.slit_shape)

    def push_slit_shape(self):
        """
        push selected slits to DMD pattern
        Export all Ginga objects to Astropy region
        """
        
        # if someone forgot to remove the tracese, we do it here for safety
        self.remove_traces()
        self.collect_slit_shape()

        """# 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)

        try:

            print(self.pattern_series[pattern_list_index])
            current_pattern = self.pattern_series[pattern_list_index]
            current_pattern_tags = [
                "@{}".format(int(obj_num)) for obj_num in current_pattern.object.values]

            objects =[self.canvas.get_object_by_tag(
                tag) for tag in current_pattern_tags]
        except:
            pass

        # counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            print(obj)
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()

            # first case: figures that have no extensions: do nothing
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1,y1]=0
            elif  self.GuideStarPickup_ChkBox_Enabled.get() != 0 and obj.kind == 'point':
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """"""
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))

                # dmd_corners[:][1] = corners[:][1]+500
                ####
                # x1 = round(dmd_corners[0][0])
                # y1 = round(dmd_corners[0][1])+400
                # x2 = round(dmd_corners[2][0])
                # y2 = round(dmd_corners[2][1])+400
                """"""
                # 3 load the slit pattern
                data_box=self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]),len(good_box[1]))
                """""" paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion""""""
                for i in np.unique(good_box_x):  #scanning multiple rows means each steps moves up along the y axis
                    #the indices of the y values pertinent to that x
                    iy = np.where(good_box_x == i)
                    iymin = min(iy[0])   #the smallest y index
                    iymax = max(iy[0])   #last largest y index
                    cx0 = ccd_x0 + i     #so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cy0 = ccd_y0 + good_box_y[iymin]
                    cy1 = ccd_y0 + good_box_y[iymax]
                    #get the lower value of the column at the x position,
                    x1,y1 = convert.CCD2DMD(cx0,cy0)
                    x1,y1 = int(np.round(x1)), int(np.round(y1))
                    x2,y2 = convert.CCD2DMD(cx0,cy1)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y2+1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y2+1,x1-2:x1] = 1
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """""" paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion """"""
                for i in np.unique(good_box_y):  #scanning multiple rows means each steps moves up along the y axis
                    #the indices of the y values pertinent to that x
                    ix = np.where(good_box_y == i)
                    ixmin = min(ix[0])   #the smallest y index
                    ixmax = max(ix[0])   #last largest y index
                    cy0 = ccd_y0 + i     #so for this x position
                    # we have these CCD columns limits, counted on the x axis
                    cx0 = ccd_x0 + good_box_x[ixmin]
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    #get the lower value of the column at the x position,
                    x1,y1 = convert.CCD2DMD(cx0,cy0)
                    x1,y1 = int(np.round(x1)), int(np.round(y1))
                    x2,y2 = convert.CCD2DMD(cx1,cy0)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y1] = 1
#                    self.slit_shape[y1-2:y2+1,x1-2:x2+1] = 0
#                    self.slit_shape[y1-2:y1,x1-2:x1] = 1
                """"""
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """"""
       #     self.slit_shape[x1:x2,y1:y2]=0
#        IP = self.PAR.IP_dict['IP_DMD']
#        [host,port] = IP.split(":")
#        DMD.initialize(address=host, port=int(port))
#        DMD._open()
#        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()
        """
        
        self.push_slits()
        print("check")
                

    def push_slits(self):
        """ Actual push of the slit_shape to the DMD """
        IP = self.PAR.IP_dict['IP_DMD']
        [host, port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()

    """
    def push_slits(self):
        # push selected slits to DMD pattern
        # Export all Ginga objects to Astropy region
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        # counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()

            x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            # dmd_corners[:][1] = corners[:][1]+500
            ####
            # x1 = round(dmd_corners[0][0])
            # y1 = round(dmd_corners[0][1])+400
            # x2 = round(dmd_corners[2][0])
            # y2 = round(dmd_corners[2][1])+400
        # 3 load the slit pattern
            self.slit_shape[x1:x2,y1:y2]=0
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))

#        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        # DMD.apply_invert()

        print("check")


    def get_IP(self,device='DMD'):
        v=pd.read_csv("SAMOS_system_dev/IP_addresses_default.csv",header=None)
        if device == 'DMD':
            return(v[2][1])

        IPs = Config.load_IP_user(self)
        # print(IPs)
    """
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#     def open_Astrometry(self):
#         btn = tk.Button(master,
#              text ="Click to open a new window",
#              command = openNewWindow)
#         btn.pack(pady = 10)ƒ
#         return self.Astrometry(master)
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def set_filter(self):
        """ to be written """
        print(self.FW_filter.get())
        print('moving to filter:', self.FW_filter.get())
#        self.Current_Filter.set(self.FW_filter.get())
        filter = self.FW_filter.get()
        main_fits_header.set_param("filter", filter)
        filter_pos_ind = list(self.filter_data["Filter"]).index(filter)
        filter_pos = list(self.filter_data["Position"])[filter_pos_ind]
        main_fits_header.set_param("filtpos", filter_pos)
        print(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
        t = PCM.move_filter_wheel(filter)
        self.canvas_Indicator.itemconfig(
            "filter_ind", fill=indicator_light_on_color)
        self.canvas_Indicator.update()

        # self.Echo_String.set(t)
        print(t)

        self.Label_Current_Filter.delete("1.0", "end")
        self.Label_Current_Filter.insert(tk.END, self.FW_filter.get())

        self.extra_header_params += 1
        entry_string = param_entry_format.format(self.extra_header_params, 'String', 'FILTER',
                                                 filter, 'Selected filter')
        self.header_entry_string += entry_string

 
    def get_widget(self):
        """ to be written """
        return self.root

    def set_drawparams(self, evt):
        """ to be written """
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  # 'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def save_canvas(self):
        """ to be written """
        regs = ap_region.export_regions_canvas(self.canvas, logger=self.logger)
        # self.canvas.save_all_objects()

    def clear_canvas(self):
        """ to be written """
        # CM.CompoundMixin.delete_all_objects(self.canvas)#,redraw=True)
        obj_tags = list(self.canvas.tags.keys())
        # print(obj_tags)
        #for tag in obj_tags:
        #    if self.SlitTabView is not None:
        #        if tag in self.SlitTabView.slit_obj_tags:
        #            obj_ind = self.SlitTabView.slit_obj_tags.index(tag)
        #            # self.SlitTabView.stab.delete_row(int(tag.strip("@")))
        #            del self.SlitTabView.slit_obj_tags[obj_ind]
        #        self.SlitTabView.slitDF = self.SlitTabView.slitDF[0:0]

                # if not self.low_magindow.winfo_exists():
                #    self.SlitTabView.recover_window()
        self.canvas.delete_all_objects(redraw=True)


   
    def update_PotN(self):
        """
        Updates the parameters of the night variables and files for logging the observations
        """
        import json
#       How do we capture a parameter in another class/form?
        self.PAR.PotN['Telescope'] = self.ConfP.Telescope.get() #ConfigPage.Telescope.get()
        self.PAR.PotN['Program ID'] = self.program_var.get() 
        self.PAR.PotN['Proposal Title'] = self.ConfP.Proposal_Title.get()#ConfigPage.Telescope.get()
        self.PAR.PotN['Principal Investigator'] = self.ConfP.Principal_Investigator.get() #ConfigPage.Telescope.get()
        # For the parameters redefinied here it is easy: capture them...
        self.PAR.PotN['Observer'] = self.names_var.get()
        self.PAR.PotN['Telescope Operator'] = self.TO_var.get()
        self.PAR.PotN['Object Name'] = self.ObjectName.get()
        self.PAR.PotN['Comment'] = self.Comment.get()
        self.PAR.PotN['Bias Comment'] = self.BiasComment.get()
        self.PAR.PotN['Dark Comment'] = self.DarkComment.get()
        self.PAR.PotN['Flat Comment'] = self.FlatComment.get()
        self.PAR.PotN['Buffer Comment'] = self.FlatComment.get()
        self.PAR.PotN['Base Filename'] = self.out_fname.get()
        
        # ..open the json file and read all...
        PotN_file = os.path.join(local_dir,'SAMOS_system_dev','Parameters_of_the_night.txt')
        with open(PotN_file, "r") as jsonFile:
            data = json.load(jsonFile)
        #... change what has to be changed...
        data["Observer"] = self.PAR.PotN['Observer'] 
        data["Program ID"] = self.PAR.PotN['Program ID'] 
        data["Proposal Title"] = self.PAR.PotN['Proposal Title'] 
        data["Principal Investigator"] = self.PAR.PotN['Principal Investigator'] 
        data["Telescope Operator"] = self.PAR.PotN['Telescope Operator'] 
        data["Object Name"] = self.PAR.PotN['Object Name'] 
        data["Comment"] = self.PAR.PotN['Comment'] 
        data["Bias Comment"] = self.PAR.PotN['Bias Comment'] 
        data["Dark Comment"] = self.PAR.PotN['Dark Comment'] 
        data["Flat Comment"] = self.PAR.PotN['Flat Comment'] 
        data["Buffer Comment"] = self.PAR.PotN['Buffer Comment'] 
        data["Base Filename"] = self.PAR.PotN['Base Filename'] 
        # ... write the json file
        with open(PotN_file, "w") as jsonFile:
            json.dump(data, jsonFile)


    def Display(self, imagefile):
        """ to be written """
#        image = load_data(fits_image_converted, logger=self.logger)

        # AstroImage object of ginga.AstroImage module
        self.AstroImage = load_data(imagefile, logger=self.logger)

        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)

    def reset_progress_bars(self):

        self.exp_progbar["value"] = 0
        self.var_perc_exp_done.set(0)
        self.exp_progbar_style.configure('text.Horizontal.TProgressbar',
                                         text='Expose {:g} %'.format(self.var_perc_exp_done.get()))
        self.readout_progbar["value"] = 0
        self.var_perc_read_done.set(0)
        self.readout_progbar_style.configure('text.Horizontal.RProgressbar',
                                             text='Readout {:g} %'.format(self.var_perc_read_done.get()))

    def load_existing_file(self):
        """ to be written """
        FITSfiledir = os.path.join(self.PAR.QL_images)
        self.last_fits_file_dialog = filedialog.askopenfilename(initialdir=self.fits_dir,                                                          title="Select a File",
                                                                 filetypes=(("fits files",
                                                                             "*.fits"),
                                                                            ("all files",
                                                                             "*.*")))
        self.fits_image_ql  = self.last_fits_file_dialog

        #self.fullpath_FITSfilename = os.path.join(
        #    self.fits_dir, self.loaded_fits_file)
        # './fits_image/newimage_ql.fits'
        self.AstroImage = load_data(
            self.last_fits_file_dialog, logger=self.logger)
        # AstroImage object of ginga.AstroImage module

        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)
#        self.root.title(self.fullpath_FITSfilename)

        #return self.filename_regfile_RADEC

    def send_RADEC_to_SOAR(self):
        pass

    def Query_Survey(self):
        """ to be written """
        #cleanup the canfas
        CM.CompoundMixin.delete_all_objects(self.canvas)#,redraw=True)
        self.clear_canvas()

        from astroquery.hips2fits import hips2fits
        Survey = self.Survey_selected.get()

        if Survey == "SkyMapper":
            try:
                self.SkyMapper_query_GuideStar()
            except:
                print("\n Sky mapper image server is down \n")
            return

        elif Survey == "SDSS":
            self.SDSS_query()
            return
    
        elif Survey == "PanSTARRS/DR1/":
            print("\n Quering PanSTARRS/DR1")
            self.PanStarrs_query_GuideStars()

        else:
            Survey = Survey+self.string_Filter.get()
            """    
            print("Survey selected: ",Survey,'\n')
            coord = SkyCoord(self.string_RA.get()+'  ' +
                         self.string_DEC.get(), unit=(u.deg, u.deg), frame='fk5')
            # coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5')

            query_results = Simbad.query_region(coord)
            
            if query_results is None:
                print('\n no objects found at that RA,Dec; try again elsewhere\n')
                ra_center = self.string_RA.get()
                dec_center = self.string_DEC.get()
            else:
                print('\n SIMBAD OBJECTS: \n',query_results)
            """
        # =============================================================================
        # Download an image centered on the coordinates passed by the main window
        #
        # =============================================================================
            # object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
            #object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'],
            #                         #                                 unit=(u.deg, u.deg), frame='icrs')
            #                         unit=(u.hourangle, u.deg), frame='icrs')
            c = SkyCoord(self.string_RA.get(),
                         self.string_DEC.get(), unit=(u.deg, u.deg))
     # FROM      https://astroquery.readthedocs.io/en/latest/hips2fits/hips2fits.html
            """
             query_params = {
                 'hips': self.Survey_selected.get(), #'DSS', #
                 # 'object': object_main_id,
                 # Download an image centef on the first object in the results
                 # 'ra': object_coords[0].ra.value,
                 # 'dec': object_coords[0].dec.value,
                 'ra': c.ra.value,
                 'dec': c.dec.value,
                 'fov': (3.5 * u.arcmin).to(u.deg).value,
                 'width': 1056#528,
                 'height': 1032#516
                 }
            url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}'
            hdul = fits.open(url)
            """
            query_params = {"NAXIS1": 1056,
                            "NAXIS2": 1032,
                            "WCSAXES": 2,
                            "CRPIX1": 1056,
                            "CRPIX2": 1032,
                            "CDELT1": self.PAR.SISI_PixelScale/3600,
                            "CDELT2": self.PAR.SISI_PixelScale/3600,
                            "CUNIT1": "deg",
                            "CUNIT2": "deg",
                            "CTYPE1": "RA---TAN",
                            "CTYPE2": "DEC--TAN",
                            "CRVAL1": c.ra.value,
                            "CRVAL2": c.dec.value}
            query_wcs = wcs.WCS(query_params)
            hips = self.Survey_selected.get()
            hdul = hips2fits.query_with_wcs(hips=hips,
                                            wcs=query_wcs,
                                            get_query_payload=False,
                                            format='fits')
    
            # Downloading http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=DSS&object=%5BT64%5D++7&ra=243.58457533549102&dec=-19.113364937196987&fov=0.03333333333333333&width=500&height=500
            # |==============================================================| 504k/504k (100.00%)         0s
            hdul.info()
            # Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
            # No.    Name      Ver    Type      Cards   Dimensions   Format
            #  0  PRIMARY       1 PrimaryHDU      22   (500, 500)   int16
            print(hdul[0].header)
            
            #to make this robust, we neeed to add a couple of parameters to the FITS header
            #(something like this may be needed by the other surveys...)
            hdul[0].header["FILENAME"] = Survey + "_" + self.string_RA.get() +"_" + self.string_DEC.get() + ".fits"

            self.image = hdul
            hdul.writeto(os.path.join(dir_Astrometry,
                         'newtable.fits'), overwrite=True)
    
            img = AstroImage()
            Posx = self.string_RA.get()
            Posy = self.string_DEC.get()
            filt = self.string_Filter.get()
            data = hdul[0].data[:, ::-1]
            try:
                image_data = Image.fromarray(data)
            except:
                print("\n  No image returned, exiting \n")
                return
            # img_res = image_data.resize(size=(1032,1056))
            img_res = image_data
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec
    
    #            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
     #           hdu.writeto(rebinned_filename,overwrite=True)
     
            #self.button_find_stars['state'] = 'active'

            img.load_hdu(self.hdu_res)
            print('\n', self.hdu_res.header)
            self.fitsimage.set_image(img)
            self.AstroImage = img
    #        self.fullpath_FITSfilename = filepath.name
            hdul.close()
            self.fits_image_ql = os.path.join(
                self.PAR.QL_images, "newimage_ql.fits")
            fits.writeto(self.fits_image_ql, self.hdu_res.data,
                         header=self.hdu_res.header, overwrite=True)

        # self.root.title(filepath)

    """
    Inject image from SkyMapper to create a WCS solution using twirl
    """
    def SkyMapper_query_GuideStar(self):
        """ get image from SkyMapper """

        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        
        SOAR_EFL = 68176.3    # mm
        SAMI_GUIDE_SCALE = 206265 / SOAR_EFL   # arcsec/mmm
        SAMI_GUIDE_FoV_mm = 100 # mm
        SAMI_GUIDE_FoV_arcsec = SAMI_GUIDE_FoV_mm * SAMI_GUIDE_SCALE    # arcsec [mm * arcsec/mm 
        SAMI_GUIDE_FoV_SISIpix = round(SAMI_GUIDE_FoV_arcsec / self.PAR.SISI_PixelScale)   

        filepath = skymapper_interrogate(Posx, Posy, SAMI_GUIDE_FoV_SISIpix , SAMI_GUIDE_FoV_SISIpix , filt)
        # filepath = skymapper_interrogate_VOTABLE(Posx, Posy, filt)
        with fits.open(filepath.name) as hdu_in:
            #            img.load_hdu(hdu_in[0])
            
            self.data_GS = hdu_in[0].data
            self.header_GS = hdu_in[0].header
            
            #for debug, write onfile the fits file returned by skymapper
            SkyMapperProduced = os.path.join(self.PAR.QL_images, "SkyMapperProduced.fits")
            fits.writeto(SkyMapperProduced, self.data_GS,
                         header=self.header_GS, overwrite=True)            
        self.fitsimage.rotate(self.PAR.Ginga_PA)    
        self.Display(SkyMapperProduced)
        
        """
        TABLE CONSTRUCTION
        """
        import urllib.request
        string = "https://skymapper.anu.edu.au/sm-cone/public/query?"
        string += "RA=" + Posx + "&"
        string += "DEC=" + Posy + "&"
        string += "SR=0.06&RESPONSEFORMAT=CSV"
        
        import tempfile
        with urllib.request.urlopen(string,timeout=30) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
        self.table_full = pd.read_csv(tmp_file.name)
        #rename the magnitudes using the general band names
        self.table_full = self.table_full.rename(columns={"g_psf": "g_band","r_psf": "r_band","i_psf": "i_band","z_psf": "z_band","raj2000":"RA","dej2000":"DEC"})
        
        
        
    def Pick_GuideStar(self):        
        """ to be written, but it seems rather obvious"""
        CM.CompoundMixin.delete_all_objects(self.canvas)#,redraw=True)
        self.clear_canvas()
        filt = self.string_Filter.get()
        if filt == "g":
            self.table_full['star_mag'] = self.table_full['g_band']
        elif filt == "r":
            self.table_full['star_mag'] = self.table_full['r_band']
        elif filt == "i":
            self.table_full['star_mag'] = self.table_full['i_band']
        elif filt == "z":
            self.table_full['star_mag'] = self.table_full['z_band']
        self.table = self.table_full[ (self.table_full['star_mag']>self.low_mag.get()) & (self.table_full['star_mag']<self.high_mag.get()) ]
        
        viewer=self.fitsimage
        image = viewer.get_image()
        x_SkyMap = [] 
        y_SkyMap = []
        i=0
        nstar = self.table.shape[0]
        i_drop=[]
        for i in range(nstar):
            x, y = image.radectopix(self.table.RA.iloc[i], self.table.DEC.iloc[i], format='str', coords='fits')
            #CHECK IF THE STAR IS OUTSIDE THE CENTRAL REGION
            if  ( (x>round(self.data_GS.shape[0]/4)) and (x<round(self.data_GS.shape[0]*3/4)) and (y>round(self.data_GS.shape[0]/4)) and (y<round(self.data_GS.shape[0]*3/4)) ):
                i_drop.append(self.table.index[i])
                continue
            elif  ( (x<0) or (x>round(self.data_GS.shape[0])) or (y<0) or (y>round(self.data_GS.shape[0])) ):
                i_drop.append(self.table.index[i])
                continue
            print(i,self.table.RA.iloc[i], self.table.DEC.iloc[i],x,y)
            x_SkyMap.append(x)
            y_SkyMap.append(y)
        self.table = self.table.drop(i_drop)
        
        print("Converted RADEC to XY for display")   
        
        
        # Draw circles around all objects
        radius_pix=10
        regions = [CirclePixelRegion(center=PixCoord(x,y), radius=radius_pix)
                        for x, y in np.transpose([x_SkyMap,y_SkyMap])]  # [(1, 2), (3, 4)]]
        regs = Regions(regions)
        i_tag = 0
        for reg in regs:
            obj = r2g(reg)
            obj.color = "red"
            obj.pickable = True
            obj.add_callback('pick-up', self.pick_cb, 'down')
            obj.tag = '@'+str(i_tag)
            i_tag += 1
            self.canvas.add(obj)
        self.circle_tags = list(self.canvas.tags.keys())    
        print(self.circle_tags)


        # LABELS NEXT TO all objects
        Text = self.canvas.get_draw_class('Text')
        z = np.transpose([x_SkyMap,y_SkyMap])
        x = z[:,0]+5
        y = z[:,1]+5
        for i in range(len(x)):
                print(x[i],y[i])
                string=Text(x=x[i], y=y[i],text=str(i),color='red')
                string.fontsize=25
                self.canvas.add(string)
        
        #DRAW  THE YELLOW AREA OF SISI
        box_region = RectanglePixelRegion(center=PixCoord(x=round(self.data_GS.shape[0]/2), y=round(self.data_GS.shape[1]/2)),
                          width=round(self.data_GS.shape[0]/2), height=round(self.data_GS.shape[1]/2),
                          angle=0*u.deg)  
        #regs = Regions(box_region)
        #regs.append(box_region)
        obj = r2g(box_region)
        obj.color = "green"

        # FINAL PLOT        
        #for reg in regs:
        #    obj = r2g(reg)
            #obj.color = "red"
            #obj.fill=True
            #obj.alpha=0.01
            #obj.alpha = "0.5"
        # add_region(self.canvas, obj, tag="twirlstars", redraw=True)
        self.canvas.add(obj)
        print("done")

        
        
    def SDSS_query(self):

#        img = AstroImage()
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt = self.string_Filter.get()
        
        from astropy import units as u
        from astropy import coordinates as coords
        from astroquery.sdss import SDSS
        from astropy.nddata import Cutout2D


        pos = coords.SkyCoord(Posx,Posy, unit=(u.deg, u.deg))
        #xid = SDSS.query_region(pos, radius='10 arcsec', spectro=True)
        #print(xid)
        #if xid is None:
        #    print("\n\n\n**** FIELD NOT IN SDSS *****\n\n\n")
        #    return
        #else:
        #    self.SDSS_stars = np.transpose([xid['ra'],xid['dec']])
            
        
        im = SDSS.get_images(coordinates=pos, radius='170 arcsec', band=filt)
        number_of_nans=758*758
        for i in range(len(im)):
            hdu = im[i]
            data = hdu[0].data
            header = hdu[0].header
            """
            2D Cutout Images
            https://docs.astropy.org/en/stable/nddata/utils.html
            """
            w = wcs.WCS(header)
            xc, yc = np.round(w.world_to_pixel(pos))   
            position = (xc, yc)
            SDSS_pixel_scale = 0.396 #arcsec_pix - https://classic.sdss.org/dr3/instruments/imager/
            size = np.round((300/SDSS_pixel_scale, 300/SDSS_pixel_scale))     # pixels
            try:
                cutout = Cutout2D(data, position, size, wcs=w,mode='partial')
            except:
                continue
            if np.count_nonzero(np.isnan(cutout.data)) < number_of_nans:
                number_of_nans = np.count_nonzero(np.isnan(cutout.data))
                best_data = cutout.data
                best_header = copy.deepcopy(header)
                d=dict(cutout.wcs.to_header())
                best_header.update(d)
        
        #always needd for Pick Guide Stars
        self.data_GS = best_data
        self.header_GS = best_header

        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, best_data,
                     header=best_header, overwrite=True)    

        #hdu = fits.open(self.fits_image_ql)
        #img.load_hdu(hdu)
        #self.fitsimage.set_image(img)
        #self.AstroImage = img
        
        self.fitsimage.rotate(90)
        
        self.Display(self.fits_image_ql)
        
        
        """
        TABLE CONSTRUCTION
        """
        
        result = SDSS.query_region(pos,fields={'ra','dec','psfMag_g','psfMag_r','psfMag_i','psfMag_z'},radius=180*u.arcsec)
        
        self.table_full = result.to_pandas()
        #rename the magnitudes using the general band names;
        self.table_full = self.table_full.rename(columns={"ra":"RA", "dec":"DEC", "psfMag_g": "g_band", "psfMag_r":"r_band", "psfMag_i":"i_band", "psfMag_z":"z_band"})
        
        # not that elegant, but this is how  we convert the table to a pandas table
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            shutil.copyfileobj(result, tmp_file)
        self.table_full = pd.read_csv(tmp_file.name)        
   

        
    def PanStarrs_query_GuideStars(self):
        
        #get ra,dec and set image size
        ra = float(self.string_RA.get())
        dec = float(self.string_DEC.get())
        if dec < -30:
            print("\n Declination outside the PanStarrs survey \n")
            return
        
        filter = self.string_Filter.get()
        size = int(300 / 0.25)   # create an image 5'x5'
        
        #get the pan star image
        fitsurl = PSima.geturl(ra, dec, size=size, filters=filter, format="fits")
        fh = fits.open(fitsurl[0])
        fim = fh[0].data
        
        #also a couple of variables for the Pick_GuideStar
        self.data_GS = fh[0].data
        self.header_GS = fh[0].header
        
        # replace NaN values with zero for display
        fim[numpy.isnan(fim)] = 0.0
        self.fits_image_ql = os.path.join(
            self.PAR.QL_images, "newimage_ql.fits")
        fits.writeto(self.fits_image_ql, fim,
                     header=fh[0].header, overwrite=True)    
        
        self.Display(self.fits_image_ql)
        self.fitsimage.rotate(self.PAR.Ginga_PA)
 
    
        """
        TABLE CONSTRUCTION
        """
        
        """Simple positional query
        Search mean object table with nDetections > 1.

        This searches the mean object catalog for objects within 212 arcsec of radec). 
        Note that the results are restricted to objects with nDetections>1, 
        where nDetections is the total number of times the object was detected on the single-epoch images 
        in any filter at any time. Objects with nDetections=1 tend to be artifacts, so this is a quick way 
        to eliminate most spurious objects from the catalog.
        """
        radius = 212.0/3600.0
        constraints = {'nDetections.gt':1}
        # strip blanks and weed out blank and commented-out values
        columns = """objID,raMean,decMean,nDetections,ng,nr,ni,nz,ny,
            gMeanPSFMag,rMeanPSFMag,iMeanPSFMag,zMeanPSFMag,yMeanPSFMag""".split(',')
        columns = [x.strip() for x in columns]
        columns = [x for x in columns if x and not x.startswith('#')]
        results = PStab.ps1cone(ra,dec,radius,release='dr2',columns=columns,verbose=True,**constraints)
        
        tab = ascii.read(results)
        # improve the format
        for filter in 'grizy':
            col = filter+'MeanPSFMag'
            try:
                tab[col].format = ".4f"
                tab[col][tab[col] == -999.0] = np.nan
            except KeyError:
                print("{} not found".format(col))
        print(tab)
        self.table_full = tab.to_pandas()
        self.table_full = self.table_full.rename(columns={"gMeanPSFMag": "g_band","rMeanPSFMag": "r_band","iMeanPSFMag": "i_band","zMeanPSFMag": "z_band","raMean":"RA", "decMean":"DEC"})


       
  
    def load_file(self):
        """ to be written """
        self.AstroImage = load_data(
            self.fullpath_FITSfilename, logger=self.logger)
        self.canvas.set_image(self.AstroImage)
        self.root.title(self.fullpath_FITSfilename)

    def open_file(self):
        """ to be written """
        filename = filedialog.askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        # self.load_file()
        self.AstroImage = load_data(filename, logger=self.logger)
        self.fitsimage.set_image(self.AstroImage)

        if self.AstroImage.wcs.wcs.has_celestial:
            self.wcs = self.AstroImage.wcs.wcs

    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'point')
        print(list(points))

        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas, 'point')
        list_point = list(points)
        CM.CompoundMixin.delete_objects(self.canvas, list_point)
        self.canvas.objects  # check that the points are gone

        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas, ['point', 'circle',
                                                                     'rectangle', 'polygon',
                                                                     'triangle', 'righttriangle',
                                                                     'ellipse', 'square'])
        list_points = list(points)
        CM.CompoundMixin.delete_objects(self.canvas, list_points)
        self.canvas.objects  # check that the points are gone

        """
        # Find approximate bright peaks in a sub-area
        from ginga.util import iqcalc
        iq = iqcalc.IQCalc()
    
        r = self.canvas.objects[0]
        img_data = self.AstroImage.get_data()
        data_box = self.AstroImage.cutout_shape(r)
        
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        px,py=round(peaks[0][0]+r.x1),round(peaks[0][1]+r.y2)
        print(px,py)   #image coordinates
        print(img_data[px,py]) #actual counts
     
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)       
        # how many did we find with standard thresholding, etc.
        # see params for find_bright_peaks() and evaluate_peaks() for details
        print(len(objs))
        # example of what is returned
        o1 = objs[0]
        print(o1)
           
        # pixel coords are for cutout, so add back in origin of cutout
        #  to get full data coords RA, DEC of first object
        x1, y1, x2, y2 = r.get_llur()
        self.img.pixtoradec(x1+o1.objx, y1+o1.objy)
          
        # Draw circles around all objects
        Circle = self.canvas.get_draw_class('circle')
        for obj in objs:
            x, y = x1+obj.objx, y1+obj.objy
            if r.contains(x, y):
                self.canvas.add(Circle(x, y, radius=10, color='yellow'))
        
        # set pan and zoom to center
        self.fitsimage.set_pan((x1+x2)/2, (y1+y2)/2)
        self.fitsimage.scale_to(0.75, 0.75)
        
        r_all = self.canvas.objects[:]
        print(r_all)
        
        
        EXERCISE COMPOUNDMIXING CLASS
        r_all is a CompountMixing object, see class ginga.canvas.CompoundMixin.CompoundMixin
         https://ginga.readthedocs.io/en/stable/_modules/ginga/canvas/CompoundMixin.html#CompoundMixin.get_objects_by_kinds        
              
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        print(list(points))
        
        # we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        list_point=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_point)
        self.canvas.objects   #check that the points are gone
           
        # we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas,['point','circle',
                                                                    'rectangle', 'polygon', 
                                                                    'triangle', 'righttriangle', 
                                                                    'ellipse', 'square'])
        list_points=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_points)
        self.canvas.objects   #check that the points are gone
    
        # drawing an object can be done rather easily
        # first take an object fromt the list and change something
        objects=CM.CompoundMixin.get_objects(self.canvas)
        o0=objects[0]
        o0.y1=40
        o0.height=100
        o0.width=70
        o0.color='lightblue'
        CM.CompoundMixin.draw(self.canvas,self.canvas.viewer)
        
        END OF THE COMPOUNDMIXING EXCERCISE
        # ===#===#===#===#===#===#===#===#===#===#===#====        

        # region = 'fk5;circle(290.96388,14.019167,843.31194")'
        # astropy_region = pyregion.parse(region)
        # astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])
        # print(astropy_region)
         
        # List all regions that we have created
        # n_objects = len(self.canvas.objects)
        # for i_obj in range(n_objects):
        #   astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj])
        #   print(astropy_region) 
           
        # create a list of astropy regions, so we export a .reg file
        # first put the initial region in square brackets, argument of Regions to initiate the list
        RRR=Regions([ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])])
        # then append to the list adding all other regions
        for i_obj in range(1,len(self.canvas.objects)):
           RRR.append(ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj]))
           print(RRR) 
 
        # write the regions to file
        # this does not seem to work...
        RRR.write('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9',overwrite=True)
       
        # reading back the ds9 regions in ginga
        pyregions = Regions.read('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9')
        n_regions = len(pyregions)
        for i in range(n_regions):
            pyregion = pyregions[i]
            pyregion.width=7
            pyregion.width=3
            ap_region.add_region(self.canvas,pyregion)

        print("yay!")            
        
        # Export all Ginga objects to Astropy region
        # 1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        counter = 0
        for obj in objects:
            if counter == 0:
                astropy_regions=[g2r(obj)]  #here we create the first astropy region and the Regions list []
            else:
                astropy_regions.append(g2r(obj)) #will with the other slits 
            counter += 1
        regs = Regions(astropy_regions)     #convert to astropy-Regions
        regs.write('my_regions.reg',overwrite=True)   #write to file
        
        # 2, Extract the slits and convert pixel->DMD values
        
        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        
        # create initial DMD slit mask
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        
        regions = Regions.read('my_regions.reg')


        for i in range(len(regions)):
            reg = regions[i]
            corners = reg.corners
            # convert CCD corners to DMD corners here
            # TBD
            # dmd_corners=[] 
            # for j in range(len(corners)):
            x1,y1 = convert.CCD2DMD(corners[0][0], corners[0][1])
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(corners[2][0], corners[2][1])
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            # dmd_corners[:][1] = corners[:][1]+500
            ####   
            # x1 = round(dmd_corners[0][0])
            # y1 = round(dmd_corners[0][1])+400
            # x2 = round(dmd_corners[2][0])
            # y2 = round(dmd_corners[2][1])+400
        # 3 load the slit pattern   
            self.slit_shape[x1:x2,y1:y2]=0
        DMD.apply_shape(self.slit_shape)  
        # DMD.apply_invert()   

        
        print("check")
        """

    def cursor_cb(self, viewer, button, data_x, data_y):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))
            value = int(round(value, 0))
        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        dmd_x, dmd_y = convert.CCD2DMD(fits_x, fits_y)

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
            ra_deg, dec_deg = image.pixtoradec(fits_x, fits_y)
            self.ra_center, self.dec_center = image.pixtoradec(1056, 1032,
                                                               format='str', coords='fits')
            Delta_Xmm = ( ra_deg - float(self.string_RA.get()) ) * 3600 / self.PAR.SOAR_arcs_mm_scale
            Delta_Ymm = ( dec_deg - float(self.string_DEC.get()) ) * 3600 / self.PAR.SOAR_arcs_mm_scale

        except Exception as e:
            # self.logger.warning("Bad coordinate conversion: %s" % (
            #    str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'
            ra_deg = 'BAD WCS'
            dec_deg = 'BAD WCS'
        coords_text = "RA: %s  DEC: %s \n" % (ra_txt, dec_txt)
#        coords_text_DEG = "RA: %s  DEC: %s \n"%(str(ra_deg), str(dec_deg))
        coords_text_DEG = "RA: %.9s DEC %.9s\n" % (str(ra_deg), str(dec_deg))
#        dmd_text = "DMD_X: %.2f  DMD_Y: %.2f \n"%(dmd_x, dmd_y)
#        dmd_text = "DMD_X: %i  DMD_Y: %i \n"%(np.round(dmd_x), round(dmd_y))
#        dmd_text = "DMD_X: %i  DMD_Y: %i \n" % (
#            np.floor(dmd_x), np.floor(dmd_y))
        mmm_text = "Dx(mm): %.3s  Dy(mm): %.3s \n" % (
            np.floor(Delta_Xmm), np.floor(Delta_Ymm))
        text = "X: %i  Y: %i  Value: %s" % (
            np.floor(fits_x), np.floor(fits_y), value)

        text = coords_text + coords_text_DEG + mmm_text + text
        self.readout.config(text=text)

    def MASTER_quit(self):
        #self.ConfP.destroy()
        self.destroy()
        return True

######

    def Pickup_GuideStar(self):
        self.wdrawtype.delete(0, tk.END)
        mode = self.Draw_Edit_Pick_Checked.set("draw")
        self.set_mode_cb()
        if self.GuideStarPickup_ChkBox_Enabled.get() == 1:
            self.wdrawtype.insert(0, "point")
        else:
            self.wdrawtype.insert(0, "box")
#            self.Draw_Edit_Pick_Checked.set("None")
        print("drawtype changed to ", self.wdrawtype.get())
#        parameters = []
#        parameters['color'] = 'red'
        self.canvas.set_drawtype(self.wdrawtype.get())#,**parameters)
            

    def set_mode_cb(self):
        """ to be written """
        mode = self.Draw_Edit_Pick_Checked.get()
        
        #we turn off here the SourcePickup_ChkBox 
        if mode != "draw":
            self.GuideStarPickup_ChkBox_Enabled.set(0)
            
#        self.logger.info("canvas mode changed (%s) %s" % (mode))
        self.logger.info("canvas mode changed (%s)" % (mode))
        try: #all object painted red, should not be true for the traces
            for obj in self.canvas.objects:
                obj.color = 'red'
        except:
            pass

        self.canvas.set_draw_mode(mode)


    def draw_cb(self, canvas, tag):
        """ to be written """
        self.Pickup_GuideStar()
        obj = canvas.get_object_by_tag(tag)
        
#        obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.pickable = True
        obj.add_callback('pick-key', self.pick_cb, 'key')

        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        # obj.add_callback('pick-hover', self.pick_cb, 'hover')
        # obj.add_callback('pick-enter', self.pick_cb, 'enter')
        # obj.add_callback('pick-leave', self.pick_cb, 'leave')
        
        obj.add_callback('edited', self.edit_cb)
        # obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        kind = self.wdrawtype.get()
        print("kind: ", kind)
        
        # Pick up mode. obj.kind should always be point.
            #this case requires more sophisticated operations, hence a dedicated function            
        self.slit_handler(obj)


    def slit_handler(self, obj):
        print('ready to associate a slit to ')
        print(obj.kind)
        img_data = self.AstroImage.get_data()

        #we are still a bit paranoid....
        if obj.kind == 'point':
            
            # Search centroid: Start creating box
            x_c = obj.points[0][0]-1  # really needed?
            y_c = obj.points[0][1]-1
            
            # create area to search, use astropy and convert to ginga (historic reasons...)
            r = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)),
                                     width=40, height=40,
                                     angle=0*u.deg)
            # and we convert it to ginga.
            obj = r2g(r)
            # Note: r as an Astropy region is a RECTANGLE
            #      obj is a Ginga region type BOX
            # obj = r2g(r)
            
            # the Ginga Box object can be added to the canvas
            self.canvas.add(obj)
        
        # time to do the math; collect the pixels in the Ginga box
        data_box = self.AstroImage.cutout_shape(obj)

        # we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.canvas, obj)

  #      obj = self.canvas.get_draw_class('rectangle')
  #      obj(x1=x_c-20,y1=y_c-20,x2=x_c+20,y2=y_c+20,
  #                      width=100,
  #                      height=30,
  #                      angle = 0*u.deg)
  #      data_box = self.img.cutout_shape(obj)
       
        # find the peak within the Ginga box
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        x1 = obj.x-obj.xradius
        y1 = obj.y-obj.yradius
        px, py = round(peaks[0][0]+x1), round(peaks[0][1]+y1)
        print('peak found at: ', px, py)  # image coordinates
        print('with counts: ', img_data[px, py])  # actual counts
        
        # GINGA MAGIC!!! 
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)
        # from ginga.readthedocs.io
        
        
        """
        Each result contains the following keys:

           * ``objx``, ``objy``: Fitted centroid from :meth:`get_fwhm`.
           * ``pos``: A measure of distance from the center of the image.
           * ``oid_x``, ``oid_y``: Center-of-mass centroid from :meth:`centroid`.
           * ``fwhm_x``, ``fwhm_y``: Fitted FWHM from :meth:`get_fwhm`.
           * ``fwhm``: Overall measure of fwhm as a single value.
           * ``fwhm_radius``: Input FWHM radius.
           * ``brightness``: Average peak value based on :meth:`get_fwhm` fits.
           * ``elipse``: A measure of ellipticity.
           * ``x``, ``y``: Input indices of the peak.
           * ``skylevel``: Sky level estimated from median of data array and
             ``skylevel_magnification`` and ``skylevel_offset`` attributes.
           * ``background``: Median of the input array.
           * ``ensquared_energy_fn``: Function of ensquared energy for different pixel radii.
           * ``encircled_energy_fn``: Function of encircled energy for different pixel radii.

        """
        """
        print('full evaluation: ', objs)
        print('fitted centroid: ', objs[0].objx, objs[0].objy)
        print('FWHM: ', objs[0].fwhm)
        print('peak value: ', objs[0].brightness)
        print('sky level: ', objs[0].skylevel)
        print('median of area: ', objs[0].background)
        print("the four vertex of the rectangle are, in pixel coord:")
        x1, y1, x2, y2 = obj.get_llur()
        print(x1, y1, x2, y2)
        print("the RADEC of the fitted centroid are, in decimal degrees:")
        print(self.AstroImage.pixtoradec(objs[0].objx, objs[0].objy))
#        slit_w=3
#        slit_l=9
#        self.canvas.add(slit_box(x1=objs[0].objx+x1-slit_w,y1=objs[0].objy+y1-slit_h,x2=objs[0].objx+x1+slit_w,y2=objs[0].objy+y1+slit_h,
#                        width=100,
#                        height=30,
#                        angle = 0*u.deg))

        #enogh with astronomy;
        # having found the centroid, we need to draw the slit
        slit_box = self.canvas.get_draw_class('box')
        xradius = self.low_mag.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        yradius = self.high_mag.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        new_slit_tag = self.canvas.add(slit_box(x=objs[0].objx+x1,
                                                y=objs[0].objy+y1,
                                                xradius=xradius,
                                                yradius=yradius,
                                                color='red',
                                                alpha=0.8,
                                                fill=False,
                                                angle=5*u.deg,
                                                pickable=True))
        #sing a victory song...
        print("slit added")

        # some final stuff that must be here for some reason... to be reviewed?
        """
        
        """
        #obj = self.canvas.get_object_by_tag(new_slit_tag)
        # obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        obj.add_callback('pick-move', self.pick_cb, 'move')
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.add_callback('edited', self.edit_cb)
        # self.cleanup_kind('point')
        # ssself.cleanup_kind('box')
        return self.canvas.objects[-1]

             # create box
        """     

        """
    def create_astropy_RectangleSkyRegion(self, pattern_row):
        # given
        ra, dec = pattern_row[1:3]
        x0, y0 = pattern_row[5:7]
        x1, y1 = pattern_row[7:9]

        ra_width = (x1-x0)*self.wcs.proj_plane_pixel_scales()[0].value
        dec_length = (y1-y0)*self.wcs.proj_plane_pixel_scales()[0].value

        center = SkyCoord(ra, dec, unit=(u.deg, u.deg), frame="fk5")
        sky_region = RectangleSkyRegion(
            center=center, width=ra_width*u.deg, height=dec_length*u.arcsec, )

        return sky_region
        """
        
        """
    def set_pattern_entry_text_color(self, event):

        if self.base_pattern_name_entry.get() != "Base Pattern Name":

            # self.base_pattern_name_entry.foreground="black"
            self.base_pattern_name_entry.config(fg="black")
        """    


        """
    def get_dmd_coords_of_picked_slit(self, picked_slit):
        """
        """ get_dmd_coords_of_picked_slit """
        """
        x0, y0, x1, y1 = picked_slit.get_llur()
        fits_x0 = x0+1
        fits_y0 = y0+1
        fits_x1 = x1+1
        fits_y1 = y1+1

        fits_xc, fits_yc = picked_slit.get_center_pt()+1

        dmd_xc, dmd_yc = convert.CCD2DMD(fits_xc, fits_yc)
        dmd_x0, dmd_y0 = convert.CCD2DMD(fits_x0, fits_y0)
        dmd_x1, dmd_y1 = convert.CCD2DMD(fits_x1, fits_y1)

        dmd_width = int(np.ceil(dmd_x1-dmd_x0))
        dmd_length = int(np.ceil(dmd_y1-dmd_y0))

        return dmd_xc, dmd_yc, dmd_x0, dmd_y0, dmd_x1, dmd_y1, dmd_width, dmd_length
        """
        
    def check_valid_mags(self, event=None):
        """ to be written """
        pass
    
        """
    def delete_obj_cb(self, obj, canvas, event, pt, ptype):
        try:
            if event.key == 'd':
                # print(event.key)
                canvas.delete_object(obj)
                #print("start tab len", len(
                #    self.SlitTabView.stab.get_sheet_data()))
                #self.SlitTabView.stab.delete_row(self.tab_row_ind)
                #print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
                #self.SlitTabView.stab.redraw()
                #self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
                #    index=self.obj_ind)
                # del self.SlitTabView.slit_obj_tags[self.obj_ind]
                #self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
                canvas.clear_selected()

                try:

                    for si in range(len(self.pattern_series)):

                        sub = self.pattern_series[si]

                        tag = int(obj.tag.strip("@"))

                        if tag in sub.object.values:
                            sub_ind = sub.where(sub.object == tag).dropna(
                                how="all").index.values[0]
                            sub = sub.drop(index=sub_ind)

                            self.pattern_series[si] = sub

                except:
                    print("try again")

        except:
            pass
        """
    def pick_cb(self, obj, canvas, event, pt, ptype):
        """ to be written """

        print("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        self.logger.info("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))

        try:
            canvas.get_object_by_tag(self.selected_obj_tag).color = 'red'
            canvas.clear_selected()
            print('unselect previous obj tag')
        except:
            pass

        canvas.select_add(obj.tag)
        self.selected_obj_tag = obj.tag
        obj.color = 'green'

        canvas.set_draw_mode('draw')  # stupid but necessary to show
        # which object is selected
        # this took me a solid 3 hours to figure out
        canvas.set_draw_mode('pick')

        self.obj_ind = int(obj.tag.strip('@'))-1
        #try:
            #self.tab_row_ind = self.SlitTabView.stab.get_column_data(
            #    0).index(obj.tag.strip('@'))
            #dmd_x0, dmd_x1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
            #    'dmd_x0', 'dmd_x1']].astype(int)
            #dmd_y0, dmd_y1 = self.SlitTabView.slitDF.loc[self.obj_ind, [
            #    'dmd_y0', 'dmd_y1']].astype(int)
         #   dmd_width = int(dmd_x1-dmd_x0)
         #   dmd_length = int(dmd_y1-dmd_y0)

         #   self.low_mag.set(dmd_width)
         #   self.high_mag.set(dmd_length)
         #except:
         #   pass

        if ptype == 'up' or ptype == 'down':
            
            print("picked object with index",format(obj.tag))
            
            # the obj.tas continuously incremented; we keep track of the current set in the self.circe_tags variable
            # and the first element of the self.circle_tags is subtracted off so we start from index = 0 for pandas
            index = int(obj.tag[1:]) - int(self.circle_tags[0][1:]) 
            
            #print(self.table.iloc[index])
            self.string_RA_GS.set(self.table['RA'].iloc[index])
            self.string_DEC_GS.set(self.table['DEC'].iloc[index])
            Delta_RA = float(self.table['RA'].iloc[index]) - float(self.string_RA.get()) 
            Delta_DEC = float(self.table['DEC'].iloc[index]) - float(self.string_DEC.get()) 
            Delta_RA_mm = round(Delta_RA * 3600 / self.PAR.SOAR_arcs_mm_scale,3)
            Delta_DEC_mm = round(Delta_DEC * 3600 / self.PAR.SOAR_arcs_mm_scale,3)
            self.string_Xmm_GS.set(Delta_RA_mm)
            self.string_Ymm_GS.set(Delta_DEC_mm)
            
            #print the magntude of the selected star
#            print(self.star_mag)
            self.string_mag_GS.set(round(self.table.star_mag.iloc[index],3))
            
            #if self.deleteChecked.get():#event.key == 'd':
            # canvas.delete_object(obj)
            #try:
            #    self.SlitTabView.stab.select_row(row=self.tab_row_ind)          
            #    print("start tab len", len(
            #        self.SlitTabView.stab.get_sheet_data()))
            #    self.SlitTabView.stab.delete_row(self.tab_row_ind)
            #    print("end tab len", len(self.SlitTabView.stab.get_sheet_data()))
            #    self.SlitTabView.stab.redraw()
            #    self.SlitTabView.slitDF = self.SlitTabView.slitDF.drop(
            #        index=self.obj_ind)
            #    # del self.SlitTabView.slit_obj_tags[self.obj_ind]
            #    self.SlitTabView.slit_obj_tags.remove(self.selected_obj_tag)
            #     canvas.clear_selected()

            #    try:
            #    
            #        for si in range(len(self.pattern_series)):

            #           sub = self.pattern_series[si]

            #            tag = int(obj.tag.strip("@"))

            #            if tag in sub.object.values:
            #                sub_ind = sub.where(sub.object == tag).dropna(
            #                    how="all").index.values[0]
            #                sub = sub.drop(index=sub_ind)

            #                self.pattern_series[si] = sub

            #    except:
            #        print("try again")

            #except:
            #    print("No slit table created yet.")

        return True
        

    def edit_cb(self, obj):
        """ to be written """
        self.logger.info("object %s has been edited" % (obj.kind))
        #tab_row_ind = list(self.SlitTabView.stab.get_column_data(
        #    0)).index(int(obj.tag.strip("@")))
        #self.SlitTabView.stab.select_row(row=tab_row_ind, redraw=True)
        # update slit table data to reflect the new edits
        #self.SlitTabView.update_table_row_from_obj(obj, self.fitsimage)
        return True

        """
    def cleanup_kind(self, kind):
        """
        """  
        REMOVE only a specific type of object
        self.cleanup_kind('point')
        self.cleanup_kind('box') 
        """
        """
        # check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        # we can find out what are the "points" objects
        # points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        found = CM.CompoundMixin.get_objects_by_kind(self.canvas, str(kind))
        list_found = list(found)
        CM.CompoundMixin.delete_objects(self.canvas, list_found)
        self.canvas.objects  # check that the points are gone
        """




    def save(file_type):
        """ to be written """
        pass
        """
        if file_type == None:
            files = [('All Files', '*.*')]
        elif file_type == 'py':
            files = [('Python Files', '*.py')]
        elif file_type == 'txt':
            files == ('Text Document', '*.txt')
        elif file_type == 'csv':
            files == ('DMD grid', '*.csv')
        file = filedialog.asksaveasfile(
            filetypes=files, defaultextension=files)

        # btn = ttk.Button(self, text = 'Save', command = lambda : save())
        """
        
    def create_menubar(self, parent):
        """ to be written """
        
        #parent is the local form
        parent.geometry("1290x920")  #was ("1400x900")  # was("1280x900")
        if platform == "win32":
            parent.geometry("1260x930") # was "1400x920")
        parent.title("SAMOS Main Page")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED,
                          activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0,
                           relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(
            label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(
            label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Recalibrate CCD2DMD",
                             command=lambda: parent.show_frame(parent.CCD2DMD_RecalPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOAR_Page))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
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
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GuideStarPage))        
        help_menu.add_separator()

        return menubar







if __name__ == "__main__":
    app = App()
    # set a style for the application so it works on various desktop themes
    # ttk.Style().theme_use("clam")
    combostyle = ttk.Style()
    combostyle.configure("TCombobox", fieldbackground="dark gray",
                         foreground="black", background="white")
    app.mainloop()

    # IF you find this useful >> Claps on Medium >> Stars on Github >> Subscription on youtube will help me
