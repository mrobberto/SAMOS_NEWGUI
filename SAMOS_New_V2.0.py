#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 25 13:21:00 2023
03.03.203- V2.0
    - added the capability of drawing generic shapes, 
03.01.2023 - V1.1
    - Major redesign of the SLit handling part, created the 3 color column on the right side
      following the data flow. 
    - Minor reorg, but notice the new structure of the .csv maps/slit pattern under DMD_dev

02.28.2023 - V1.0
    - Added Slit Configuration Frame with fields to enter slit width and lenght
    - Moved Slit Pointer check
    - Added in paraemters the DMD2PIXEL scale of 0.892. To be used for the conversion
    - Slit loaded from file  appear in red
    
02.27.2023 
    - cleaned first jupyter notebook to create target list using ipyaladin interactive
    - region file in RADEC must be copieed to directory /regions/RADEC
    - putton "load .red RADEC" allows to lod the region file in RADEC. File name format is rather rigid
    - coordinates of the center are extracted searching filename between "RADEC="  and ".reg"
    - observations is assumed to be done at this point: use sSkyMapper Query for test
    - after twirl vs. GAIA and WCS header created, convert the RADEC region file to a pixel region file
    - the regions (slits) appear on the display!  
TO DO: "Run Code" erases everything, should leave the slits untouched.

02.26.2023 First committ to share with Dana
=======
- V7. Created a button for saving the Stil Table made by Dana, to be completeed.
      moved folder "asset" to archive
      Fixed when Convertsilly correction is done, overwrites newimage.fit
- V6. Set inoutvar in Parameters class and looks ok from home!
- V5. All initial definitions of IP addresses and status are ow in Parameters class 
- V4. Self.Image_on/off are now coming from Parameters: self.PAR.Image_on/off
- V3. Added SAMOS_Parameters() class
      Display CCD image from home   
- V2. Cleaned the startup sequence removing a bunch of print() messages
"""
import tkinter as tk
#from tkinter import *
#import tkinter as tk  #small t for Python 3f
from tkinter import ttk
#import filedialog module
from tkinter import filedialog
#from tkinter.filedialog import askopenfilename
#from tkinter.filedialog import asksaveasfile

from astropy import units as u
from astropy.io import fits, ascii
from astropy.stats import sigma_clipped_stats, SigmaClip
import astropy.wcs as wcs

from photutils.background import Background2D, MedianBackground
from photutils.detection import DAOStarFinder


import utils as U
import shutil
#from esutil import htm

from PIL import Image, ImageTk#, ImageOps


import os, sys
cwd = os.getcwd()
print(cwd)

import csv
from pathlib import Path
import time 
from datetime import datetime

import numpy as np
import pandas as pd

import subprocess

#define the local directory, absolute so it is not messed up when this is called

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   
sys.path.append(parent_dir)

# =============================================================================
# Import classes
# 
# =============================================================================
#load the functions
from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF

from  SAMOS_MOTORS_dev.Class_PCM import Class_PCM 
PCM = Class_PCM()

#at the moment the Class Camera must be called with a few parameters...
from  SAMOS_CCD_dev.Class_CCD import Class_Camera
params = {'Exposure Time':0,'CCD Temperature':2300,'Trigger Mode': 4}
        #Trigger Mode = 4: light
        #Trigger Mode = 5: dark
CCD = Class_Camera(dict_params=params)

#Import the DMD class
from SAMOS_DMD_dev.Class_DMD_dev import DigitalMicroMirrorDevice
DMD = DigitalMicroMirrorDevice()#config_id='pass') 




"""
import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfile

import sys
#sys.path.append('/opt/anaconda3/envs/samos_env/lib/python3.10/site-packages')

import os
from os.path import exists as file_exists
import time
from argparse import ArgumentParser
    
import threading
import pandas as pd
"""
#for image display
from ginga.tkw.ImageViewTk import CanvasView
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.canvas import CompoundMixin as CM
from ginga.misc import log
from ginga.util.loader import load_data
from ginga import colors
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util import ap_region
from ginga.AstroImage import AstroImage
img = AstroImage()
from ginga.util import iqcalc
iq = iqcalc.IQCalc()


from astroquery.gaia import Gaia
from astroquery.simbad import Simbad                                                            
from astropy.coordinates import SkyCoord, FK4#, ICRS, Galactic, FK5 
#from astropy import units as u
#from astropy.io import fits
from astropy.wcs.utils import fit_wcs_from_points
from urllib.parse import urlencode
from matplotlib import pyplot as plt
import twirl


#import aplpy
#from astropy.nddata import block_reduce

#import regions
from regions import Regions
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion#, PointPixelRegion, RegionVisual

### Needed to run ConvertSIlly by C. Loomis
import math
import pathlib
import glob
import re #re module of the standard library handles strings, e.g. use re.search() to extract substrings

#import sewpy   #to run sextractor wrapper

STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'
# =============================d================================================
# 
# from Astrometry import tk_class_astrometry
# Astrometry = tk_class_astrometry
# 
# Astrometry.return_from_astrometry()
# 
# =============================================================================

#from pathlib import Path
##define the local directory, absolute so it is not messed up when this is called
#path = Path(__file__).parent.absolute()
#local_dir = str(path.absolute())
#sys.path.append(local_dir)


dir_Astrometry = local_dir+"/SAMOS_Astrometry_dev"
dir_CCD = local_dir+"/SAMOS_CCD_dev"
dir_DMD = local_dir+"/SAMOS_DMD_dev"
dir_MOTORS = local_dir+"/SAMOS_MOTORS_dev"
dir_SOAR = local_dir+"/SAMOS_SOAR_dev"
dir_CONFIG = local_dir+"/SAMOS_CONFIG_dev"
dir_SYSTEM = local_dir+"/SAMOS_system_dev"

os.sys.path.append(local_dir)
os.sys.path.append(dir_Astrometry)
os.sys.path.append(dir_CCD)
os.sys.path.append(dir_DMD)
os.sys.path.append(dir_MOTORS)
os.sys.path.append(dir_SOAR)
os.sys.path.append(dir_CONFIG)
os.sys.path.append(dir_SYSTEM)


#from SAMOS_CONFIG_dev.CONFIG_GUI import Config

#print(Config.return_directories)

from SAMOS_Astrometry_dev.tk_class_astrometry_V4 import Astrometry
from SAMOS_Astrometry_dev.skymapper_interrogate import skymapper_interrogate
"""
from SAMOS_CCD_dev.GUI_CCD_dev import GUI_CCD
from SAMOS_CCD_dev.Class_CCD_dev import Class_Camera as CCD


from SAMOS_MOTORS_dev.SAMOS_MOTORS_GUI_dev  import Window as SM_GUI
"""
from SAMOS_MOTORS_dev.Class_PCM  import Class_PCM 
Motors  = Class_PCM()
"""
from SAMOS_DMD_dev.SAMOS_DMD_GUI_dev import GUI_DMD 
#from SAMOS_DMD_dev.Class_DMD import DigitalMicroMirrorDevice as DMD
from SAMOS_DMD_dev.Class_DMD_dev import DigitalMicroMirrorDevice
"""
from SAMOS_DMD_dev.CONVERT.CONVERT_class import CONVERT 
convert = CONVERT()

from SlitTableViewer import SlitTableView as STView


"""
DMD = DigitalMicroMirrorDevice()#config_id='pass') 

from SAMOS_SOAR_dev.tk_class_SOAR_V0 import SOAR as SOAR

from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF


#from ginga.misc import widgets 
#import PCM_module_GUI as Motors

"""
#text format for writing new info to header. Global var
param_entry_format = '[Entry {}]\nType={}\nKeyword={}\nValue="{}"\nComment="{}\n"'



class App(tk.Tk):
    def __init__(self):
        super().__init__()

        ## Setting up Initial Things
        self.title("SAMOS Tkinter Restructuring")
        self.geometry("1000x500")
        self.resizable(True, True)
        #self.iconphoto(False, tk.PhotoImage(file="assets/title_icon.png"))
    
        ## Creating a container
        container = tk.Frame(self, bg="#8AA7A9")
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)


        ## Initialize Frames
        self.frames = {}
        self.ConfigPage = ConfigPage
        self.DMDPage = DMDPage
        self.Motors = Motors
        self.CCDPage = CCDPage
        self.MainPage = MainPage

        ## Defining Frames and Packing it
        for F in {ConfigPage, DMDPage, Motors, CCDPage, MainPage}:
            frame = F(self, container)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")    
           
        self.show_frame(ConfigPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        menubar = frame.create_menubar(self)
        self.configure(menu=menubar)
        frame.tkraise()                         ## This line will put the frame on front
 



#---------------------------------------- Config PAGE FRAME / CONTAINER ------------------------------------------------------------------------

class ConfigPage(tk.Frame):
    def __init__(self, parent, container):
        super().__init__(container)

        self.PAR = SAMOS_Parameters()        
        #label = tk.Label(self, text="Config Page", font=('Times', '20'))
        #label.pack(pady=0,padx=0)

        ## ADD CODE HERE TO DESIGN THIS PAGE
        # parameters that you want to send through the Frame class
#        tk.Frame.__init__(self, master)   

        #reference to the master widget, which is the "parent" tk window, since we instance
        #at the end   >app = Config(parent)                 
#        self.master = master

        #with that, we want to then run init_window, which doesn't yet exist
#        self.init_Config()
        

        #path = Path(__file__).parent.absolute()
#        parent_dir = str(path.parent)      
        
        #self.cwd = local_dir       
        #self.parent_dir = parent_dir        
        
        
    #Creation of init_window
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
        #master.title("SAMOS- Config Window")
        
        self.frame0l = tk.Frame(self,background="dark gray", width=600, height=500)
        self.frame0l.place(x=0, y=0)#, anchor="nw", width=20, height=145)
        

# =============================================================================
#         
#  #    Directories
#         
# =============================================================================
        self.labelframe_Servers =  tk.LabelFrame(self.frame0l, text="Directories", font=("Arial", 24))
        self.labelframe_Servers.place(x=4, y=4, anchor="nw", width=592, height=225)
  
# 2. Directories and Files
# 2.1 SAMOS Motors parameter files
# 2.2 SAMOS CCD parameter files
# 2.3 SAMOS DMD parameter files
# 2.4 SOAR Telescope parameter files
# 2.5 SOAR SAMI parameter files
# 2.6 SAMOS Astrometry
# 2.7 SAMOS system Window

        Label1 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_Motors'])
        Label1.place(x=4, y=10)
        self.update()
        Label2 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_CCD'])
        Label2.place(x=4, y=35)
        Label3 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_DMD'])
        Label3.place(x=4, y=60)
        Label1 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_SOAR'])
        Label1.place(x=4, y=85)
        Label2 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_SAMI'])
        Label2.place(x=4, y=110)
        Label1 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_Astrom'])
        Label1.place(x=4, y=135)
        Label2 = tk.Label(self.labelframe_Servers, text = self.PAR.dir_dict['dir_system'])
        Label2.place(x=4, y=160)
        
        self.dir_Motors = tk.StringVar()
        self.dir_Motors.set(self.PAR.dir_dict['dir_Motors'])
        Entry_dir_Motors = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_Motors)
        Entry_dir_Motors.place(x=140, y=10)
        self.dir_CCD= tk.StringVar()
        self.dir_CCD.set(self.PAR.dir_dict['dir_CCD'])
        Entry2 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_CCD)
        Entry2.place(x=140, y=35)
        self.dir_DMD= tk.StringVar()
        self.dir_DMD.set(self.PAR.dir_dict['dir_DMD'])
        Entry3 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_DMD)
        Entry3.place(x=140, y=60)
        self.dir_SOAR = tk.StringVar()
        self.dir_SOAR.set(self.PAR.dir_dict['dir_SOAR'])
        Entry4 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_SOAR)
        Entry4.place(x=140, y=85)
        self.dir_SAMI = tk.StringVar()
        self.dir_SAMI.set(self.PAR.dir_dict['dir_SAMI'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_SAMI)
        Entry5.place(x=140, y=110)
        self.dir_Astrom = tk.StringVar()
        self.dir_Astrom.set(self.PAR.dir_dict['dir_Astrom'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_Astrom)
        Entry5.place(x=140, y=135)
        self.dir_system = tk.StringVar()
        self.dir_system.set(self.PAR.dir_dict['dir_system'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_system)
        Entry5.place(x=140, y=160)

        Button_dir_Current = tk.Button(self.labelframe_Servers, text ="Load Current", relief="raised", command = self.load_dir_user, font=("Arial", 24))
        Button_dir_Current.place(x=380, y=10)
        Button_dir_Save = tk.Button(self.labelframe_Servers, text ="Save Current", relief="raised", command = self.save_dir_user, font=("Arial", 24))
        Button_dir_Save.place(x=380, y=50)
        Button_dir_Load= tk.Button(self.labelframe_Servers, text ="Load Default", relief="raised", command = self.load_dir_default, font=("Arial", 24))
        Button_dir_Load.place(x=380, y=90)
        
# =============================================================================
#         
#  #    Servers
#         
# =============================================================================
        self.labelframe_Servers =  tk.LabelFrame(self.frame0l, text="Servers", font=("Arial", 24))
        self.labelframe_Servers.place(x=4, y=234, anchor="nw", width=592, height=200)
        

        """
        self.inoutvar=tk.StringVar()
        self.inoutvar.set("outside")
        """
        
        r1 = tk.Radiobutton(self.labelframe_Servers, text='Inside', variable=self.PAR.inoutvar, value='inside', command=self.load_IP_default)
        r1.place(x=20,y=0)
        r2 = tk.Radiobutton(self.labelframe_Servers, text='Outside', variable=self.PAR.inoutvar, value='outside', command=self.load_IP_default)
        r2.place(x=150,y=0)

# 1. Server addresses
# 1.1 SAMOS Motors
# 1.2 SAMOS CCD
# 1.3 SAMOS DMD controller
# 1.4 SOAR Telescope
# 1.5 SOAR SAMI
        Label1 = tk.Label(self.labelframe_Servers, text = "SAMOS Motors")
        Label1.place(x=4, y=35)
        Label2 = tk.Label(self.labelframe_Servers, text = "CCD")
        Label2.place(x=4, y=60)
        Label3 = tk.Label(self.labelframe_Servers, text = "DMD")
        Label3.place(x=4, y=85)
        Label1 = tk.Label(self.labelframe_Servers, text = "SOAR Telescope")
        Label1.place(x=4, y=110)
        Label2 = tk.Label(self.labelframe_Servers, text = "SOAR SAMI")
        Label2.place(x=4, y=135)
        
        #print(self.PAR.IP_dict)
        
        self.IP_Motors = tk.StringVar()
        self.IP_Motors.set(self.PAR.IP_dict['IP_Motors'])
        Entry_IP_Motors = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_Motors)
        Entry_IP_Motors.place(x=120, y=35)
        self.IP_CCD= tk.StringVar()
        self.IP_CCD.set(self.PAR.IP_dict['IP_CCD'])
        Entry2 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_CCD)
        Entry2.place(x=120, y=60)
        self.IP_DMD= tk.StringVar()
        self.IP_DMD.set(self.PAR.IP_dict['IP_DMD'])
        Entry3 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_DMD)
        Entry3.place(x=120, y=85)
        self.IP_SOAR = tk.StringVar()
        self.IP_SOAR.set(self.PAR.IP_dict['IP_SOAR'])
        Entry4 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_SOAR)
        Entry4.place(x=120, y=110)
        self.IP_SAMI = tk.StringVar()
        self.IP_SAMI.set(self.PAR.IP_dict['IP_SAMI'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_SAMI)
        Entry5.place(x=120, y=135)

 #       self.Image_on = Image.open("/Users/robberto/Box/@Massimo/_Python/SAMOS_GUI_dev/SAMOS_CONFIG_dev/Images/on.jpg")
#        self.python_image = ImageTk.PhotoImage(self.image)
        #self.Label(self, image=self.python_image).pack()

#        ttk.Label(self,image=self.Image_on).pack()
         # Create A Button
        self.IP_Motors_on_button = tk.Button(self.labelframe_Servers, image = self.PAR.Image_off, bd = 0, command = self.Motors_switch)
        self.IP_Motors_on_button.place(x=320,y=39) 
        self.CCD_on_button = tk.Button(self.labelframe_Servers, image = self.PAR.Image_off, bd = 0, command = self.CCD_switch)
        self.CCD_on_button.place(x=320,y=64) 
        self.DMD_on_button = tk.Button(self.labelframe_Servers, image = self.PAR.Image_off, bd = 0, command = self.DMD_switch)
        self.DMD_on_button.place(x=320,y=89) 
        self.SOAR_Tel_on_button = tk.Button(self.labelframe_Servers, image = self.PAR.Image_off, bd = 0, command = self.SOAR_switch)
        self.SOAR_Tel_on_button.place(x=320,y=113) 
        self.SOAR_SAMI_on_button = tk.Button(self.labelframe_Servers, image = self.PAR.Image_off, bd = 0, command = self.SAMI_switch)
        self.SOAR_SAMI_on_button.place(x=320,y=139) 

        
       # Button_IP_Load_Current = tk.Button(self.labelframe_Servers, text ="Load Current", relief="raised", command = self.load_IP_user, font=("Arial", 24))
       # Button_IP_Load_Current.place(x=380, y=10)
       # Button_IP_Save_Current = tk.Button(self.labelframe_Servers, text ="Save Current", relief="raised", command = self.save_IP_user, font=("Arial", 24))
       # Button_IP_Save_Current.place(x=380, y=50)
       # Button_IP_Load_Default = tk.Button(self.labelframe_Servers, text ="Load Default", relief="raised", command = self.load_IP_default, font=("Arial", 24))
       # Button_IP_Load_Default.place(x=380, y=90)
 
# =============================================================================
#         
#  #    OTHER INFO
#         
# =============================================================================
        self.frame0r = tk.Frame(self,background="dark gray", width=400, height=500)
        self.frame0r.place(x=585, y=0)#, anchor="nw", width=20, height=145)
 

        self.labelframe_Others =  tk.LabelFrame(self.frame0r, text="Others", font=("Arial", 24))
        self.labelframe_Others.place(x=4, y=4, anchor="nw", width=392, height=225)
  
        Label1 = tk.Label(self.labelframe_Others, text = "Observer")
        Label1.place(x=4, y=10)
        self.Observer = tk.StringVar()
        self.Observer.set('Observer')
        Entry_IP_Observer = tk.Entry(self.labelframe_Others,width=20, textvariable = self.Observer)
        Entry_IP_Observer.place(x=120, y=10)


 

# =============================================================================
#         
#  #    Initialize
#         
# =============================================================================
        self.Initialize_frame =  tk.Frame(self.frame0l)
        self.Initialize_frame.place(x=4, y=440, anchor="nw", width=592, height=48)
        Initialize_Button = tk.Button(self.Initialize_frame, text ="Initialize", relief="raised", command = self.startup, font=("Arial",24)) 
        Initialize_Button.place(x=230, y=5)

# =============================================================================
# =============================================================================
#         
#  #   FUNCTIONS ....
#         
# =============================================================================
# =============================================================================
    def startup(self):
        print("CONFIG_GUI: entering startup()\n")
        self.load_IP_default()
        self.IP_echo()
        SF.create_fits_folder()
        
        if self.PAR.IP_status_dict['IP_DMD'] == True:  
            IP = self.PAR.IP_dict['IP_DMD']
            [host,port] = IP.split(":")
            DMD.initialize(address=host, port=int(port))
            #PCM.power_on()
            #PCM.check_if_power_is_on()
        if self.PAR.IP_status_dict['IP_Motors'] == True:  
            PCM.power_on()
            #PCM.check_if_power_is_on()
        print("\n*** CONFIG_GUI: exiting startup() ***\n")
        
    
    # =============================================================================
    # create directoy to store the data
    # =============================================================================
        def create_fits_folder(self) :       
    
            today = datetime.now()
            
            #name of the directory    
            self.fits_dir = self.local_dir + "/SAMOS_" + today.strftime('%Y%m%d')
            
            isdir = os.path.isdir(self.fits_dir)
            if isdir == False:  
                os.mkdir(self.fits_dir)
                
            fits_directory_file = open(dir_SYSTEM + "/fits_current_dir_name.txt", "w")
            fits_directory_file.write(self.fits_dir)
            fits_directory_file.close()    
    




    def load_dir_default(self):
        dict_from_csv = {}


        #with open(self.parent_dir+"/SAMOS_system_dev/dirlist_default.csv", mode='r') as inp:
        with open(dir_SYSTEM + "/dirlist_default.csv", mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

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
        dict_from_csv = {}

        with open(dir_SYSTEM + "/dirlist_user.csv", mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

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

        # define a dictionary with key value pairs
#        dict = {'dir_Motors' : self.dir_Motors.get(), 
#                'dir_CCD' :  self.dir_CCD.get(), 
#                'dir_DMD' :  self.dir_DMD.get(), 
#                'dir_SOAR':  self.dir_SOAR.get(), 
#                'dir_SAMI': self.dir_SAMI.get(),
#                'dir_Astrom':  self.dir_Astrom.get(), 
#                'dir_system': self.dir_system.get()}
        self.PAR.dir_dict['dir_Motors'] = self.dir_Motors.get()
        self.PAR.dir_dict['dir_CCD'] = self.dir_CCD.get()
        self.PAR.dir_dict['dir_DMD'] = self.dir_DMD.get()
        self.PAR.dir_dict['dir_SOAR'] = self.dir_SOAR.get()
        self.PAR.dir_dict['dir_SAMI'] = self.dir_SAMI.get()
        self.PAR.dir_dict['dir_Astrom'] = self.dir_Astrom.get()
        self.PAR.dir_dict['dir_system'] = self.dir_system.get()
        
        # open file for writing, "w" is writing
        w = csv.writer(open(dir_SYSTEM + "/dirlist_user.csv", "w"))
        print(dir_SYSTEM + "/dirlist_user.csv")

        # loop over dictionary keys and values
        for key, val in self.PAR.dir_dict.items():

            # write every key and value to file
            w.writerow([key, val])
           

    def load_IP_user(self):
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = dir_SYSTEM + "/IP_addresses_default_inside.csv"
        else:
            ip_file = dir_SYSTEM + "/IP_addresses_default_outside.csv"
        ip_file_default = dir_SYSTEM + "/IP_addresses_default.csv"    
        os.system('cp {} {}'.format(ip_file,ip_file_default))  
        
        with open(ip_file, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        self.PAR.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
        self.PAR.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
        self.PAR.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
        self.PAR.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
        self.PAR.IP_dict['IP_SAMI']=dict_from_csv['IP_SAMI']

        self.IP_Motors.set(dict_from_csv['IP_Motors'])
        self.IP_CCD.set(dict_from_csv['IP_CCD'])
        self.IP_DMD.set(dict_from_csv['IP_DMD'])
        self.IP_SOAR.set(dict_from_csv['IP_SOAR'])
        self.IP_SAMI.set(dict_from_csv['IP_SAMI'])
        


        return self.PAR.IP_dict

    def save_IP_user(self):

        # define a dictionary with key value pairs
 #       dict = {'IP_Motors' : self.IP_Motors.get(), 'IP_CCD' :  self.IP_CCD.get(), 'IP_DMD' :  self.IP_DMD.get(), 'IP_SOAR':  self.IP_SOAR.get(), 'IP_SAMI': self.IP_SAMI.get()}


# =============================================================================
#         self.PAR.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
#         self.PAR.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
#         self.PAR.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
#         self.PAR.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
#         self.PAR.IP_dict['IP_SAMI']=dict_from_csv['IP__SOAR_SAMI']
#         
# =============================================================================
# open file for writing, "w" is writing
       
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = dir_SYSTEM + "/IP_addresses_default_inside.csv"
        else:
            ip_file = dir_SYSTEM + "/IP_addresses_default_outside.csv"
        ip_file_default = dir_SYSTEM + "/IP_addresses_default.csv"    
        os.system('cp {} {}'.format(ip_file,ip_file_default))  
        
        w = csv.writer(open(ip_file, "w"))
        print(ip_file)

        # loop over dictionary keys and values
        for key, val in self.PAR.IP_dict.items():

            # write every key and value to file
            w.writerow([key, val])            
 
        self.save_IP_status()    
        
        
        
    def load_IP_default(self):
        
        if self.PAR.inoutvar.get() == 'inside':
            ip_file = dir_SYSTEM + "/IP_addresses_default_inside.csv"
        else:
            ip_file = dir_SYSTEM + "/IP_addresses_default_outside.csv"
        ip_file_default = dir_SYSTEM + "/IP_addresses_default.csv"    
        os.system('cp {} {}'.format(ip_file,ip_file_default))  

        dict_from_csv = {}      
        with open(ip_file_default, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        self.PAR.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
        self.PAR.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
        self.PAR.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
        self.PAR.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
        self.PAR.IP_dict['IP_SAMI']=dict_from_csv['IP_SAMI']

        self.IP_Motors.set(dict_from_csv['IP_Motors'])
        self.IP_CCD.set(dict_from_csv['IP_CCD'])
        self.IP_DMD.set(dict_from_csv['IP_DMD'])
        self.IP_SOAR.set(dict_from_csv['IP_SOAR'])
        self.IP_SAMI.set(dict_from_csv['IP_SAMI']) 
        
        #if PCM.MOTORS_onoff == 1:
        #self.IP_echo()
        


    def save_IP_status(self):

        w = csv.writer(open(dir_SYSTEM + "/IP_status_dict.csv", "w"))

        # loop over dictionary keys and values
        for key, val in self.PAR.IP_status_dict.items():

            # write every key and value to file
            w.writerow([key, val])               


    def IP_echo(self):                   
#MOTORS alive?
        print("\n Checking Motors status")
        IP = self.PAR.IP_dict['IP_Motors']
        [host,port] = IP.split(":")
        PCM.initialize(address=host, port=int(port))
        answer = PCM.echo_client()
        #print("\n Motors return:>", answer,"<")
        if answer != "no connection":
            print("Motors are on")
            self.IP_Motors_on_button.config(image = self.PAR.Image_on)
            print('echo from server:')
            self.PAR.IP_status_dict['IP_Motors'] = True  
            #PCM.power_on()

        else:
            print("Motors are off\n")
            self.IP_Motors_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_Motors'] = False    
         

#CCD alive?
        print("\n Checking CCD status")
        url_name = "http://"+self.PAR.IP_dict['IP_CCD']+'/'
        answer = (CCD.get_url_as_string(url_name))[:6]   #expect <HTML>
        print("CCD returns:>", answer,"<")
        if str(answer) == '<HTML>':
            print("CCD is on")
            self.CCD_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_CCD'] = True   
        else:
            print("\nCCD is off\n")
            self.CCD_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_CCD'] = False  
            
#DMD alive?
        print("\n Checking DMD status")
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        answer = DMD._open()
        if answer != "no DMD":
            print("\n DMD is on")
            self.DMD_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_DMD'] = True   
        else:
            print("\n DMD is off")
            self.DMD_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_DMD'] = False    


        self.save_IP_status()    
        return self.PAR.IP_dict
    
    # Define our switch functions
    def Motors_switch(self):
        # Determine is on or off
        if self.PAR.IP_status_dict['IP_Motors']:
            self.IP_Motors_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_Motors'] = False
            PCM.power_off()
        else:           
            self.IP_Motors_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_Motors'] = True
#            SF.read_IP_initial_status()
            self.save_IP_status()
            PCM.IP_host = self.IP_Motors
            PCM.power_on()
        self.save_IP_status()    
        print(self.PAR.IP_status_dict)        
    
    def CCD_switch(self):         
        # Determine is on or off
        if self.PAR.IP_status_dict['IP_CCD']:
            self.CCD_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_CCD'] = False
        else:           
            self.CCD_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_CCD'] = True        
        self.save_IP_status()    
        print(self.PAR.IP_status_dict)        
    

    def DMD_switch(self):         
        # Determine is on or off
        if self.PAR.IP_status_dict['IP_DMD']:
            self.DMD_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_DMD'] = False
        else:           
            self.DMD_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_DMD'] = True          
        self.save_IP_status()    
        print(self.PAR.IP_status_dict)        
    
    def SOAR_switch(self):         
        # Determine is on or off
        if self.PAR.IP_status_dict['IP_SOAR']:
            self.SOAR_Tel_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_SOAR'] = False
        else:           
            self.SOAR_Tel_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_SOAR']= True            
        self.save_IP_status()    
        print(self.PAR.IP_status_dict)        

    def SAMI_switch(self):         
        # Determine is on or off
        if self.PAR.IP_status_dict['IP_SAMI']:
            self.SOAR_SAMI_on_button.config(image = self.PAR.Image_off)
            self.PAR.IP_status_dict['IP_SAMI'] = False
        else:           
            self.SOAR_SAMI_on_button.config(image = self.PAR.Image_on)
            self.PAR.IP_status_dict['IP_SAMI'] = True    
        self.save_IP_status()    
        print(self.PAR.IP_status_dict)                

    def client_exit(self):
        print("complete")
        #self.master.destroy()         
    
    def create_menubar(self, parent):
        #the size of the window is controlled when the menu is loaded
        parent.geometry("1000x500")  
        parent.title("SAMOS Configuration")

        
        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")
        
        ## Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)  

        """
        ## proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """
        
        ## help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
#---------------------------------------- DMD PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class DMDPage(tk.Frame):
    def __init__(self, parent, container):
        super().__init__(container)

        label = tk.Label(self, text="DMD Page", font=('Times', '20'))
        label.pack(pady=0,padx=0)
        

        ## ADD CODE HERE TO DESIGN THIS PAGE
        #super() recalls and includes the __init__() of the master class (tk.Topelevel), so one can use that stuff there without copying the code.
  
        #reference to the master widget, which is the tk window                 
        #self.master = master 
  
        #DMD.initialize()

        # changing the title of our master widget      
        #self.title("IDG - DMD module driver")
        #Creation of init_window
        #self.geometry("610x407")
        #label = tk.Label(self, text ="DMD Control Window")
        #label.pack()
#       
        #self.frame0l = tk.Frame(self,background="green")
        #self.frame0l.place(x=0, y=0, anchor="nw", width=390, height=320)

        #self.Echo_String = StringVar()         
        #self.check_if_power_is_on()

# =============================================================================
#         
#  #    Startup Frame
#         
# =============================================================================
        self.frame_startup = tk.Frame(self,background="light gray")
        self.frame_startup.place(x=4, y=4, anchor="nw", width=290, height=400)

# =============================================================================
#       DMD Initialize
# =============================================================================
        #dmd.initialize()
        button_Initialize =  tk.Button(self.frame_startup, text="Initialize", bd=3, bg='#0052cc',command=self.dmd_initialize)
        button_Initialize.place(x=4,y=4)

# ==========================================================================
#       Load Basic Patterns
# =============================================================================
        button_Blackout =  tk.Button(self.frame_startup, text="Blackout", bd=3, bg='#0052cc',command=self.dmd_blackout)
        button_Blackout.place(x=4,y=34)
        button_Whiteout =  tk.Button(self.frame_startup, text="Whiteout", bd=3, bg='#0052cc',command=self.dmd_whiteout)
        button_Whiteout.place(x=4,y=64)
        button_Checkerboard =  tk.Button(self.frame_startup, text="Checkerboard", bd=3, bg='#0052cc',command=self.dmd_checkerboard)
        button_Checkerboard.place(x=4,y=94)
        button_Invert =  tk.Button(self.frame_startup, text="Invert", bd=3, bg='#0052cc',command=self.dmd_invert)
        button_Invert.place(x=4,y=124)

        button_antInvert =  tk.Button(self.frame_startup, text="AntInvert", bd=3, bg='#0052cc',command=self.dmd_antinvert)
        button_antInvert.place(x=140,y=124)
  
# ==========================================================================
#       Load Custom Patterns
# =============================================================================
    
        button_edit = tk.Button(self.frame_startup,
                        text = "Edit DMD File",
                        command = self.browseFiles)
        button_edit.place(x=4,y=164)

        button_load_map = tk.Button(self.frame_startup,
                        text = "Load DMD Map",
                        command = self.LoadMap)
        button_load_map.place(x=4,y=212)

        label_filename = tk.Label(self.frame_startup, text="Current DMD Map")
        label_filename.place(x=4,y=240)
        self.str_filename = tk.StringVar() 
        self.textbox_filename = tk.Text(self.frame_startup, height = 1, width = 22)      
        self.textbox_filename.place(x=120,y=240)

        button_load_slits = tk.Button(self.frame_startup,
                       text = "Load Slit Grid",
                       command = self.LoadSlits)
        button_load_slits.place(x=4,y=272)

        label_filename_slits = tk.Label(self.frame_startup, text="Current Slit Grid")
        label_filename_slits.place(x=4,y=300)
        self.str_filename_slits = tk.StringVar() 
        self.textbox_filename_slits = tk.Text(self.frame_startup, height = 1, width = 22)      
        self.textbox_filename_slits.place(x=120,y=300)

   

# ==========================================================================
#       Display Patterns
# =============================================================================

        self.canvas = tk.Canvas(self, width = 300, height = 270, bg="dark gray") 
        self.canvas.place(x=300,y=4)

# =============================================================================
# 
#         # Exit
# =============================================================================
        quitButton = tk.Button(self, text="Exit",command=self.client_exit)
        quitButton.place(x=180, y=350)


# =============================================================================
#
# echo client()
#
# =============================================================================
    def dmd_initialize(self):
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
              
        
    def dmd_blackout(self):
        DMD.apply_blackout()
        # global img
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)

    def dmd_whiteout(self):
        DMD.apply_whiteout()
        # global img
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)

    def dmd_checkerboard(self):
        DMD.apply_checkerboard()
        # global img
        shutil.copy(dir_DMD + "/checkerboard.png",dir_DMD + "/current_dmd_state.png")
        time.sleep(1)
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)

    def dmd_invert(self):
        DMD.apply_invert()
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        #image=image_map.convert("L")
        #image_invert = ImageOps.invert(image)
        #image_invert.save(dir_DMD+ "/current_dmd_state.png")
        # global img
        #img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
        #self.img= ImageTk.PhotoImage(image_invert)
        #Add image to the Canvas Items
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)

             
#        # global img
#        img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
#        #Add image to the Canvas Items
#        self.canvas.create_image(104,128,image=img)

    def dmd_antinvert(self):
        DMD.apply_antinvert()
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)
            
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = dir_DMD+"/DMD_maps_csv",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.csv"),
                                                       ("all files",
                                                        "*.*")))
        subprocess.call(['open', '-a','TextEdit', filename])
        
        
# =============================================================================
#
# Load DMD map file
#
# =============================================================================

    def LoadMap(self):
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename = filedialog.askopenfilename(initialdir = dir_DMD+"/DMD_maps_csv",
                                        title = "Select a File",
                                        filetypes = (("Text files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*")))
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)
        
        myList = []

        with open (filename,'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        #print(myList)         
        
        for i in range(len(myList)):
            print("Row " + str(i) + ": " + str(myList[i]))
        
        test_shape = np.ones((1080,2048)) # This is the size of the DC2K    
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]),int(myList[i][2]):int(myList[i][3])] = int(myList[i][4])
        
        DMD.apply_shape(test_shape)    

        # Create a photoimage object of the image in the path
        #Load an image in the script
        # global img
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104,128,image=self.img)

        
# =============================================================================
#
# Load Slit file
#
# =============================================================================
        
    def LoadSlits(self):
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename_slits = filedialog.askopenfilename(initialdir = dir_DMD+"/DMD_maps_csv",
                                        title = "Select a File",
                                        filetypes = (("Text files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*")))
        head, tail = os.path.split(filename_slits)
        self.textbox_filename_slits.insert(tk.END, tail)

        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index),int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for i in table.index:
           self.slit_shape[x1[i]:x2[i],y1[i]:y2[i]]=0
        DMD.apply_shape(self.slit_shape)
        
        # Create a photoimage object of the image in the path
        #Load the image
        # global img
        #self.img = None
#        image_map = Image.open(local_dir + "/current_dmd_state.png")
#        self.img= ImageTk.PhotoImage(image_map)
#         image_map.close()
        image_map = Image.open(dir_DMD + "/current_dmd_state.png")        
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)


    def save_slittable(self):
        pass

        #Add image to the Canvas Items
        #print('img =', self.img)
        #self.canvas.create_image(104,128,image=self.img)
     
    def enter_command(self):       
        print('command entered:',self.Command_string.get())         
        t = DMD.send_command_string(self.Command_string.get()) #convert StringVar to string
        self.Echo_String.set(t)
        print(t)
        
    def client_exit(self):
        print("destroy")
        self.destroy()         

    def create_menubar(self, parent):
        parent.geometry("610x407")
        parent.title("SAMOS DMD Controller")
        self.PAR = SAMOS_Parameters()
        
        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")

        ## Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame(parent.MainPage))        
        filemenu.add_command(label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)  

        """
        ## proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """
        
        ## help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
#---------------------------------------- MOTORS PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class Motors(tk.Frame):
    def __init__(self, parent, container):
        super().__init__(container)

        #label = tk.Label(self, text="Motors Page", font=('Times', '20'))
        #label.pack(pady=0,padx=0)

        ## ADD CODE HERE TO DESIGN THIS PAGE
        self.Echo_String = tk.StringVar()         
        #self.check_if_power_is_on()

# =============================================================================
#         
#         #Get echo from Server 
# =============================================================================
        Button_Echo_From_Server = tk.Button(self, text="Echo from server",command=self.call_echo_PCM, relief=tk.RAISED)
        # placing the button on my window
        Button_Echo_From_Server.place(x=10,y=10)
        self.Echo_String = tk.StringVar()        
        Label_Echo_Text = tk.Label(self,textvariable=self.Echo_String,width=15,bg='white')
        Label_Echo_Text.place(x=160,y=13)
        
# =============================================================================
#         
#        # Power on/odd 
# =============================================================================
        self.is_on = False
        if self.is_on == False:
            text = "Turn power ON"
            color = "green"
        else: 
            text = "Turn power OFF"
            color = "red"
        self.Button_Power_OnOff = tk.Button(self, text=text,command=self.power_switch, relief=tk.RAISED,fg = color)
        self.Button_Power_OnOff.place(x=10,y=40)

# =============================================================================
#         All port statusPower on/odd 
# =============================================================================
        self.Button_All_Ports_Status = tk.Button(self, text="All ports status",command=self.all_ports_status, relief=tk.RAISED)
        self.Button_All_Ports_Status.place(x=200,y=40)
  
# =============================================================================
#         Select FW or GR    
# =============================================================================
        self.r1_v = tk.IntVar()
        
        r1 = tk.Radiobutton(self, text='FW1', variable=self.r1_v, value=1, command=self.Choose_FWorGR)
        r1.place(x=10,y=70) 
        
        r2 = tk.Radiobutton(self, text='FW2', variable=self.r1_v, value=2, command=self.Choose_FWorGR)
        r2.place(x=70,y=70)  
        
        r3 = tk.Radiobutton(self, text='GR_A', variable=self.r1_v, value=3, command=self.Choose_FWorGR)
        r3.place(x=130,y=70) 

        r3 = tk.Radiobutton(self, text='GR_B', variable=self.r1_v, value=4, command=self.Choose_FWorGR)
        r3.place(x=190,y=70) 
   
        #start with FW1 
        self.r1_v.set(1)
        self.Choose_FWorGR()
# =============================================================================
#       home
# =============================================================================
        self.Button_home = tk.Button(self, text="send to home",command=self.home, relief=tk.RAISED)
        self.Button_home.place(x=10,y=100)

# =============================================================================
#        Initialize
# =============================================================================
        self.Button_Initialize = tk.Button(self, text="Initialize Filter Wheels",command=self.FW_initialize, relief=tk.RAISED)
        self.Button_Initialize.place(x=200,y=100)
  
# =============================================================================
#        Query current step counts
# =============================================================================
        self.Button_Initialize = tk.Button(self, text="Current steps",command=self.query_current_step_counts, relief=tk.RAISED)
        self.Button_Initialize.place(x=10,y=130)

    
# =============================================================================
#         
#         #Move to step.... 
# =============================================================================
        Button_Move_to_step = tk.Button(self, text="Move to step",command=self.move_to_step, relief=tk.RAISED)
        Button_Move_to_step.place(x=10,y=160)
        self.Target_step = tk.StringVar()        
        Label_Target_step = tk.Entry(self,textvariable=self.Target_step,width=6,bg='white')
        Label_Target_step.place(x=140,y=163)
        Button_Stop = tk.Button(self, text="Stop",command=self.stop, relief=tk.RAISED)
        Button_Stop.place(x=260,y=160)
    
# =============================================================================
#         
#         #Move to FW_position.... 
# =============================================================================
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
        self.menu_FW_pos = tk.OptionMenu(self, self.selected_FW_pos,  *FW_pos_options)
        self.menu_FW_pos.place(x=120, y=193)
        Button_Move_to_FW_pos = tk.Button(self, text="FW Position",command=self.FW_move_to_position, relief=tk.RAISED)
        Button_Move_to_FW_pos.place(x=10,y=190)

# =============================================================================
#         
#         #Move to Filter.... 
# =============================================================================
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
        self.menu_filters = tk.OptionMenu(self, self.selected_filter,  *filter_options)
        self.menu_filters.place(x=300, y=193)
        Button_Move_to_filter = tk.Button(self, text="Filter",command=self.FW_move_to_filter, relief=tk.RAISED)
        Button_Move_to_filter.place(x=230,y=190)

# =============================================================================
#         
#         #Move to GR_position.... 
# =============================================================================
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
        self.menu_GR_pos = tk.OptionMenu(self, self.selected_GR_pos,  *GR_pos_options)
        self.menu_GR_pos.place(x=120, y=223)
        Button_Move_to_GR_pos = tk.Button(self, text="GR Position",command=self.GR_move_to_position, relief=tk.RAISED)
        Button_Move_to_GR_pos.place(x=10,y=220)

# =============================================================================
#         
#         #Enter command
# =============================================================================
        Button_Enter_Command = tk.Button(self, text="Enter Command: ",command=self.enter_command, relief=tk.RAISED)
        Button_Enter_Command.place(x=10,y=250)
        self.Command_string = tk.StringVar()        
        Text_Command_string = tk.Entry(self,textvariable=self.Command_string,width=15,bg='white')
        Text_Command_string.place(x=180,y=252)
        Label_Command_string_header = tk.Label(self,text=" ~@,9600_8N1T2000,+")
        Label_Command_string_header.place(x=10,y=280)
        Label_Command_string_Example = tk.Label(self,text=" (e.g. /1e1R\\n)")
        Label_Command_string_Example.place(x=165,y=280)


# =============================================================================
# 
#         # Exit
# =============================================================================
        quitButton = tk.Button(self, text="Exit",command=self.client_exit)
        quitButton.place(x=280, y=300)
        
        
        
    def get_widget(self):
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
        print('echo from server:')
        t = PCM.echo_client()
        self.Echo_String.set(t)
        print(t)

    def power_switch(self):     
    # Determine is on or off
        if self.is_on:  #True, power is on => turning off, prepare for turn on agaim
            t=PCM.power_off()
            self.is_on = False
            self.Button_Power_OnOff.config(text="Turn power On",fg = "green")
        else:            
            t=PCM.power_on()
            self.is_on = True
            self.Button_Power_OnOff.config(text="Turn power Off",fg = "red")
        self.Echo_String.set(t)
        print("Power switched to ", t)
    
    def all_ports_status(self):       
        print('all ports status:')
        t = PCM.all_ports_status()
        self.Echo_String.set(t)
        print(t)
        
    def Choose_FWorGR(self):
        if self.r1_v.get() == 1: 
            unit = 'FW1',
        if self.r1_v.get() == 2: 
            unit = 'FW2',
        if self.r1_v.get() == 3: 
            unit= 'GR_A',
        if self.r1_v.get() == 4: 
            unit = 'GR_B',
        self.FWorGR = unit[0]    #returns a list...
        print(self.FWorGR)    

    def FW_initialize(self):       
        print('Initialize:')
        t = PCM.initialize_filter_wheel("FW1")
        t = PCM.initialize_filter_wheel("FW2")
        self.Echo_String.set(t)
        print(t)

    def stop_the_motors(self):       
        print('Stop the motor:')
        t = PCM.motors_stop()
        self.Echo_String.set(t)

    def query_current_step_counts(self):       
        print('Current step counts:')
        t = PCM.query_current_step_counts(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def home(self):       
        print('home:')
        t = PCM.home_FWorGR_wheel(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def move_to_step(self):       
        print('moving to step:')
        t = PCM.go_to_step(self.FWorGR,self.Target_step.get())
        self.Echo_String.set(t)
        print(t)

    def stop(self):       
        print('moving to step:')
        t = PCM.stop_filter_wheel(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def FW_move_to_position(self):       
        print('moving to FW position:',self.selected_FW_pos.get()) 
        FW_pos = self.selected_FW_pos.get()
        t = PCM.move_FW_pos_wheel(FW_pos)
        self.Echo_String.set(t)
        print(t)
        
    def FW_move_to_filter(self):       
        print('moving to filter:',self.selected_filter.get()) 
        filter = self.selected_filter.get()
        t = PCM.move_filter_wheel(filter)
        self.Echo_String.set(t)
        print(t)

    def GR_move_to_position(self):       
        print('moving to GR_position:') 
        GR_pos = self.selected_GR_pos.get()
        t = PCM.move_grism_rails(GR_pos)
        self.Echo_String.set(t)
        print(t)

    def enter_command(self):       
        print('command entered:',self.Command_string.get())         
        t = PCM.send_command_string(self.Command_string.get()) #convert StringVar to string
        self.Echo_String.set(t)
        print(t)
        
    def client_exit(self):
        print("destroy")
        self.destroy() 

    def create_menubar(self, parent):
        parent.geometry("400x330")
        parent.title("SAMOS Motor Controller")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")

        ## Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)  

        """
        ## proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """

        ## help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_separator()

        return menubar


"""
#############################################################################################################################################
#
#---------------------------------------- CCD PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""


class CCDPage(tk.Frame):
    def __init__(self, parent, container):
        super().__init__(container)

        label = tk.Label(self, text="CCD Page", font=('Times', '20'))
        label.pack(pady=0,padx=0)

        ## ADD CODE HERE TO DESIGN THIS PAGE
        self.frame0l = tk.Frame(self,background="cyan")#, width=300, height=300)
        self.frame0l.place(x=0, y=0, anchor="nw", width=950, height=590)

# =============================================================================
#         
#  #    ACQUIRE IMAGE Frame
#         
# =============================================================================
        self.frame2l = tk.Frame(self.frame0l,background="dark turquoise")#, width=400, height=800)
        self.frame2l.place(x=4, y=4, anchor="nw", width=420, height=400)
        
        
  
# =============================================================================
#       CONTROL OF SCIENCE AND REFERENCE FILES
# 
# =============================================================================

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
  
# =============================================================================
#      SCIENCE
# =============================================================================

        labelframe_Acquire =  tk.LabelFrame(tab1, text="Acquire Image", font=("Arial", 24))
        labelframe_Acquire.pack(fill="both", expand="yes")
#        labelframe_Grating.place(x=4, y=10)

        label_ExpTime =  tk.Label(labelframe_Acquire, text="Exp. Time (s)")
        label_ExpTime.place(x=4,y=10)
        self.ExpTime=tk.StringVar()
        self.ExpTime.set("0.01")
        entry_ExpTime = tk.Entry(labelframe_Acquire, textvariable=self.ExpTime, width=5,  bd =3)
        entry_ExpTime.place(x=100, y=10)

        label_ObjectName =  tk.Label(labelframe_Acquire, text="Object Name:")
        label_ObjectName.place(x=4,y=30)
        entry_ObjectName = tk.Entry(labelframe_Acquire, width=11,  bd =3)
        entry_ObjectName.place(x=100, y=30)

        label_Comment =  tk.Label(labelframe_Acquire, text="Comment:")
        label_Comment.place(x=4,y=50)
#        scrollbar = tk.Scrollbar(orient="horizontal")
        entry_Comment = tk.Entry(labelframe_Acquire, width=11,  bd =3)# , xscrollcommand=scrollbar.set)
        entry_Comment.place(x=100, y=50)

        button_ExpStart=  tk.Button(labelframe_Acquire, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
                                         #  command=self.expose)
        button_ExpStart.place(x=50,y=75)


# =============================================================================
#      BIAS
# =============================================================================
        labelframe_Bias =  tk.LabelFrame(tab2, text="Bias", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Bias.pack(fill="both", expand="yes")

#        labelframe_Bias.place(x=5,y=5)
        label_Bias_ExpT =  tk.Label(labelframe_Bias, text="Exposure time (s):")
        label_Bias_ExpT.place(x=4,y=10)
        self.Bias_ExpT = tk.StringVar(value="0.00")
        entry_Bias_ExpT = tk.Entry(labelframe_Bias, width=6,  bd =3, textvariable=self.Bias_ExpT)
        entry_Bias_ExpT.place(x=120, y=6)
        
        label_Bias_NofFrames =  tk.Label(labelframe_Bias, text="Nr. of Frames:")
        label_Bias_NofFrames.place(x=4,y=40)
        self.Bias_NofFrames = tk.StringVar(value="10")
        entry_Bias_NofFrames = tk.Entry(labelframe_Bias, width=5,  bd =3, textvariable=self.Bias_NofFrames)
        entry_Bias_NofFrames.place(x=100, y=38)
        
        
        var_Bias_saveall = tk.IntVar()
        r1_Bias_saveall = tk.Radiobutton(labelframe_Bias, text = "Save single frames", variable=var_Bias_saveall, value=1)
        r1_Bias_saveall.place(x=150, y=38)

        label_Bias_MasterFile =  tk.Label(labelframe_Bias, text="Master Bias File:")
        label_Bias_MasterFile.place(x=4,y=70)
        self.Bias_MasterFile = tk.StringVar(value="Bias")
        entry_Bias_MasterFile = tk.Entry(labelframe_Bias, width=11,  bd =3, textvariable=self.Bias_MasterFile)
        entry_Bias_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Bias, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)
  
#        root.mainloop()  




        
# =============================================================================
#      Dark
# =============================================================================
        labelframe_Dark =  tk.LabelFrame(tab3, text="Dark", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Dark.pack(fill="both", expand="yes")

        label_Dark_ExpT =  tk.Label(labelframe_Dark, text="Exposure time (s):")
        label_Dark_ExpT.place(x=4,y=10)
        self.Dark_ExpT = tk.StringVar(value="0.00")
        entry_Dark_ExpT = tk.Entry(labelframe_Dark, width=6,  bd =3, textvariable=self.Dark_ExpT)
        entry_Dark_ExpT.place(x=120, y=6)
        
        label_Dark_NofFrames =  tk.Label(labelframe_Dark, text="Nr. of Frames:")
        label_Dark_NofFrames.place(x=4,y=40)
        self.Dark_NofFrames = tk.StringVar(value="10")
        entry_Dark_NofFrames = tk.Entry(labelframe_Dark, width=5,  bd =3, textvariable=self.Dark_NofFrames)
        entry_Dark_NofFrames.place(x=100, y=38)
        
        
        var_Dark_saveall = tk.IntVar()
        r1_Dark_saveall = tk.Radiobutton(labelframe_Dark, text = "Save single frames", variable=var_Dark_saveall, value=1)
        r1_Dark_saveall.place(x=150, y=38)

        label_Dark_MasterFile =  tk.Label(labelframe_Dark, text="Master Dark File:")
        label_Dark_MasterFile.place(x=4,y=70)
        self.Dark_MasterFile = tk.StringVar(value="Dark")
        entry_Dark_MasterFile = tk.Entry(labelframe_Dark, width=11,  bd =3, textvariable=self.Dark_MasterFile)
        entry_Dark_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Dark, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)

# =============================================================================
#      Flat
# =============================================================================
        labelframe_Flat =  tk.LabelFrame(tab4, text="Flat", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Flat.pack(fill="both", expand="yes")

        label_Flat_ExpT =  tk.Label(labelframe_Flat, text="Exposure time (s):")
        label_Flat_ExpT.place(x=4,y=10)
        self.Flat_ExpT = tk.StringVar(value="0.00")
        entry_Flat_ExpT = tk.Entry(labelframe_Flat, width=6,  bd =3, textvariable=self.Flat_ExpT)
        entry_Flat_ExpT.place(x=120, y=6)
        
        label_Flat_NofFrames =  tk.Label(labelframe_Flat, text="Nr. of Frames:")
        label_Flat_NofFrames.place(x=4,y=40)
        self.Flat_NofFrames = tk.StringVar(value="10")
        entry_Flat_NofFrames = tk.Entry(labelframe_Flat, width=5,  bd =3, textvariable=self.Flat_NofFrames)
        entry_Flat_NofFrames.place(x=100, y=38)
        
        
        var_Flat_saveall = tk.IntVar()
        r1_Flat_saveall = tk.Radiobutton(labelframe_Flat, text = "Save single frames", variable=var_Flat_saveall, value=1)
        r1_Flat_saveall.place(x=150, y=38)

        label_Flat_MasterFile =  tk.Label(labelframe_Flat, text="Master Flat File:")
        label_Flat_MasterFile.place(x=4,y=70)
        self.Flat_MasterFile = tk.StringVar(value="Flat")
        entry_Flat_MasterFile = tk.Entry(labelframe_Flat, width=11,  bd =3, textvariable=self.Flat_MasterFile)
        entry_Flat_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Flat, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)



        label_Display =  tk.Label(labelframe_Acquire, text="Subtract for Display:")
        label_Display.place(x=4,y=120)
        subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(labelframe_Acquire, text='Bias',variable=subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=140)
        subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(labelframe_Acquire, text='Dark',variable=subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60,y=140)
        subtract_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(labelframe_Acquire, text='Flat',variable=subtract_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120,y=140)
        subtract_Buffer = tk.IntVar()
        check_Buffer = tk.Checkbutton(labelframe_Acquire, text='Buffer',variable=subtract_Buffer, onvalue=1, offvalue=0)
        check_Buffer.place(x=180,y=140)

# =============================================================================
#      Buffer
# =============================================================================
        labelframe_Buffer =  tk.LabelFrame(tab5, text="Buffer", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Buffer.pack(fill="both", expand="yes")

        label_Buffer_ExpT =  tk.Label(labelframe_Buffer, text="Exposure time (s):")
        label_Buffer_ExpT.place(x=4,y=10)
        self.Buffer_ExpT = tk.StringVar(value="0.00")
        entry_Buffer_ExpT = tk.Entry(labelframe_Buffer, width=6,  bd =3, textvariable=self.Buffer_ExpT)
        entry_Buffer_ExpT.place(x=120, y=6)
        
        label_Buffer_NofFrames =  tk.Label(labelframe_Buffer, text="Nr. of Frames:")
        label_Buffer_NofFrames.place(x=4,y=40)
        self.Buffer_NofFrames = tk.StringVar(value="10")
        entry_Buffer_NofFrames = tk.Entry(labelframe_Buffer, width=5,  bd =3, textvariable=self.Buffer_NofFrames)
        entry_Buffer_NofFrames.place(x=100, y=38)
        
        
        var_Buffer_saveall = tk.IntVar()
        r1_Buffer_saveall = tk.Radiobutton(labelframe_Buffer, text = "Save single frames", variable=var_Buffer_saveall, value=1)
        r1_Buffer_saveall.place(x=150, y=38)

        label_Buffer_MasterFile =  tk.Label(labelframe_Buffer, text="Master Buffer File:")
        label_Buffer_MasterFile.place(x=4,y=70)
        self.Buffer_MasterFile = tk.StringVar(value="Buffer")
        entry_Buffer_MasterFile = tk.Entry(labelframe_Buffer, width=11,  bd =3, textvariable=self.Buffer_MasterFile)
        entry_Buffer_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Buffer, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)



        label_Display =  tk.Label(labelframe_Acquire, text="Subtract for Display:")
        label_Display.place(x=4,y=120)
        subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(labelframe_Acquire, text='Bias',variable=subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=140)
        subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(labelframe_Acquire, text='Dark',variable=subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60,y=140)
        subtract_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(labelframe_Acquire, text='Flat',variable=subtract_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120,y=140)
        subtract_Buffer = tk.IntVar()
        check_Buffer = tk.Checkbutton(labelframe_Acquire, text='Buffer',variable=subtract_Buffer, onvalue=1, offvalue=0)
        check_Buffer.place(x=180,y=140)

# =============================================================================
#      CCD Setup panel
# 
# =============================================================================

        self.frame2r = tk.Frame(self.frame0l,background="#4A7A8C")#, width=400, height=800)
        self.frame2r.place(x=430, y=4, anchor="nw", width=360, height=400)
        labelframe_Setup =  tk.LabelFrame(self.frame2r, text="Camera Seup", font=("Arial", 24))
        labelframe_Setup.pack(fill="both", expand="yes")
        
#        #camera_is_open = tk.IntVar()
#        button_open_camera= tk.Button(labelframe_Setup, text='Open Camera')
                                                        #command = open_close_camera)
#        button_open_camera.place(x=4, y=104)
        
#        button_cooler_on= tk.Button(labelframe_Setup, text='Cooler on')
                                                        #command = open_close_camera)
#        button_cooler_on.place(x=4, y=124)
        
 #=========#=========#=========#=========#=========#=========#=========       
        # CAMERA ON/OFF SWITCH
        self.camera_is_on = False
        self.label_camera_ON = tk.Label(labelframe_Setup,
                         text = "The Camera is off",
                         fg = "grey",
                         font = ("Helvetica", 20))
        self.label_camera_ON.place(x=4,y=8)
        
        # Define Our Images
        self.on_png = tk.PhotoImage(file = local_dir + "/tk_utilities/on.png")
        self.off_png = tk.PhotoImage(file =local_dir + "/tk_utilities/off.png")
        self.button_open_camera= tk.Button(labelframe_Setup, image=self.off_png, bd=0, command=self.turn_camera_ON)
                                                        #command = open_close_camera)
        self.button_open_camera.place(x=180, y=0)

 #=========#=========#=========#=========#=========#=========#=========       
        # COOLER ON/OFF SWITCH
        self.cooler_is_on = False
        self.label_cooler_ON = tk.Label(labelframe_Setup,
                         text = "The Cooler is off",
                         fg = "grey",
                         font = ("Helvetica", 20))
        self.label_cooler_ON.place(x=4,y=58)
        
        # Define Our Images
        self.button_open_cooler= tk.Button(labelframe_Setup, image=self.off_png, bd=0, command=self.turn_cooler_ON)
                                                        #command = open_close_camera)
        self.button_open_cooler.place(x=180, y=50)
 #=========#=========#=========#=========#=========#=========#=========       
        # COOLER TEMPERATURE SETUP AND VALUE
        label_Tset =  tk.Label(labelframe_Setup, text="CCD Temperature Sepoint (C)")
        label_Tset.place(x=4,y=98)
        self.Tset = tk.StringVar()
        self.Tset.set("-90")
        entry_Tset = tk.Entry(labelframe_Setup, 
                              textvariable=self.Tset, width=5,
                              #font=('Arial',16),
                              bd =3)
        entry_Tset.place(x=200, y=96)
        #
        label_Tdet = tk.Label(labelframe_Setup, text="Current CCD Temperature (K)")
        label_Tdet.place(x=4,y=128)
        self.Tdet = tk.IntVar()
        label_show_Tdet = tk.Label(labelframe_Setup, 
                                   textvariable=self.Tdet,
                                   font=('Arial',16),
                                   borderwidth=3,
                                   relief="sunken",
                                   bg="green",fg="white",
                                   text=str(273))
        label_show_Tdet.place(x=200,y=126)
        self.Tdet.set(273)
            
 #=========#=========#=========#=========#=========#=========#=========       
    def turn_camera_ON(self):
        #global camera_is_on
         
        # Determine is on or off
        if self.camera_is_on:
            self.button_open_camera.config(image = self.off_png)
            self.label_camera_ON.config(text = "The Camera is Off",fg = "grey")
            self.camera_is_on = False
        else:
            self.button_open_camera.config(image = self.on_png)
            self.label_camera_ON.config(text = "The Camera is On", fg = "green")
            self.camera_is_on = True

 #=========#=========#=========#=========#=========#=========#=========       
    def turn_cooler_ON(self):
        #global camera_is_on
         
        # Determine is on or off
        if self.cooler_is_on:
            self.button_open_cooler.config(image = self.off_png)
            self.label_cooler_ON.config(text = "The Cooler is Off",fg = "grey")
            self.cooler_is_on = False
        else:
            self.button_open_cooler.config(image = self.on_png)
            self.label_cooler_ON.config(text = "The Cooler is On", fg = "green")
            self.cooler_is_on = True

        """ 
        #        labelframe_Grating.place(x=4, y=10)

        params = {'Exposure Time':100,'CCD Temperature':2300,'Trigger Mode': 4}
        #Trigger Mode = 4: light
        #Trigger Mode = 4: dark

        Camera= Class_Camera(dict_params=params)


        Camera.expose()
        #Camera.Cooler("1") 

        #Camera.dict_params['Exposure Time']=10

        #Camera.set_CCD_temp(2030)    #(273-80) * 10

        #Status = Camera.status()
        #print(Status)
        #url_name = 'http://128.220.146.254:8900/'
        """
 


# =============================================================================
#      SHOW SIMBAD IMAGE
# 
# =============================================================================

    def Show_Simbad(self):
            self.frame_DisplaySimbad = tk.Frame(self.frame0l,background="pink")#, width=400, height=800)
            self.frame_DisplaySimbad.place(x=310, y=5, anchor="nw", width=528, height=516) 
            
            #img = AstroImage()
#            img = io_fits.load_file(self.image.filename())
    
            # ginga needs a logger.
            # If you don't want to log anything you can create a null logger by
            # using null=True in this call instead of log_stderr=True
            #logger = log.get_logger("example1", log_stderr=True, level=40)
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

            #fi.set_redraw_lag(0.0)
            fi.enable_autocuts('on')
            fi.set_autocut_params('zscale')
            fi.enable_autozoom('on')
            fi.enable_draw(False)
            # tk seems to not take focus with a click
            fi.set_enter_focus(True)
            fi.set_callback('cursor-changed', self.cursor_cb)
            
            #'button-press' is found in Mixins.py
            fi.set_callback('button-press', self. button_click)  
            
            #'drag-drop' is found in Mixins.py
            #fi.set_callback('drag-drop', self. draw_cb)   

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
            #canvas.enable_edit(True)
            canvas.set_drawtype('rectangle', color='blue')
            canvas.set_surface(fi)
            self.canvas = canvas
            # add canvas to view
            fi.add(canvas)
            canvas.ui_set_active(True)
     
            fi.configure(516,528)
          #  fi.set_window_size(514,522)
            
            #self.fitsimage.set_image(img)
#            self.root.title(filepath)
            self.load_file()
     

     
# =============================================================================
#             self.readout_Simbad = tk.Label(self.frame0l, text='tbd')
# #            self.readout_Simbad.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
#             self.readout_Simbad.place(x=0,y=530)
#      
# =============================================================================


            self.drawtypes = fi.get_drawtypes()
            ## wdrawtype = ttk.Combobox(self, values=self.drawtypes,
            ##                          command=self.set_drawparams)
            ## index = self.drawtypes.index('ruler')
            ## wdrawtype.current(index)
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
            
# =============================================================================
#         top = fv.get_widget()
# 
#         if len(args) > 0:
#            fv.load_file(args[0])
# 
# =============================================================================

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


# =============================================================================
#         labelframe_SolveAstrometry =  tk.LabelFrame(self.frame0l, text="Solve Astrometry", font=("Arial", 24))
#         labelframe_SolveAstrometry.pack(fill="both", expand="yes")
#         
# =============================================================================
    def load_file(self):
        image = load_data('./newtable.fits', logger=self.logger)
#        image = load_data(filepath, logger=self.logger)
        self.fitsimage.set_image(image)


    def get_widget(self):
       return self.root

    ### this is a function called by main to pass parameters 
    def receive_radec(self,radec,radec_list,xy_list): 
        self.string_RA_center.set(radec[0])
        self.string_DEC_center.set(radec[1])
        self.string_RA_list = radec_list[0]
        self.string_DEC_list = radec_list[1]
        self.xy = xy_list

    def set_drawparams(self, evt):
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  #'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)


    def clear_canvas(self):
        self.canvas.delete_all_objects(redraw=True)

#    
    def return_from_astrometry(self):
        return "voila"

    def button_click(self, viewer, button, data_x, data_y):
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
            
    def Query_Simbad(self):
        coord = SkyCoord(self.string_RA_center.get()+'  '+self.string_DEC_center.get(),unit=(u.hourangle, u.deg), frame='fk5') 
#        coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5') 
        query_results = Simbad.query_region(coord)                                                      
        print(query_results)
    
    # =============================================================================
    # Download an image centered on the coordinates passed by the main window
    # 
    # =============================================================================
        #object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
        object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'], 
                                 unit=(u.hourangle, u.deg), frame='icrs')
        c = SkyCoord(self.string_RA_center.get(),self.string_DEC_center.get(), unit=(u.hourangle, u.deg))
        query_params = { 
             'hips': self.Survey_selected.get(), #'DSS', #
             #'object': object_main_id, 
             # Download an image centef on the first object in the results 
             #'ra': object_coords[0].ra.value, 
             #'dec': object_coords[0].dec.value, 
             'ra': c.ra.value, 
             'dec': c.dec.value,
             'fov': (3.5 * u.arcmin).to(u.deg).value, 
             'width': 528, 
             'height': 516 
             }                                                                                               
        
        url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}' 
        hdul = fits.open(url)                                                                           
        # Downloading http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=DSS&object=%5BT64%5D++7&ra=243.58457533549102&dec=-19.11336493196987&fov=0.03333333333333333&width=500&height=500
        #|==============================================================| 504k/504k (100.00%)         0s
        hdul.info()
        hdul.info()                                                                                     
        #Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
        #No.    Name      Ver    Type      Cards   Dimensions   Format
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
        
    
                
        gc = aplpy.FITSFigure(hdul)                                                                     
        gc.show_grayscale()                                                                             
    # =============================================================================
    # INFO: Auto-setting vmin to  2.560e+03 [aplpy.core]
    # INFO: Auto-setting vmax to  1.513e+04 [aplpy.core]
    # =============================================================================
        gc.show_markers(object_coords.ra, object_coords.dec, edgecolor='red',
                     marker='s', s=50**2)         
        gc.save('plot.png')
        
        
    def Query_Gaia(self):
        #Gaia coords are 2016.0

        coord = SkyCoord(ra=self.string_RA_center.get(), dec=self.string_DEC_center.get(), unit=(u.hourangle, u.deg), frame='icrs')
        width = u.Quantity(0.1, u.deg)
        height = u.Quantity(0.1, u.deg)
        Gaia.ROW_LIMIT=200
        r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
        r.pprint()
        self.ra_Gaia = r['ra']
        self.dec_Gaia = r['dec']
        mag_Gaia = r['phot_g_mean_mag']
        print(self.ra_Gaia,self.dec_Gaia,mag_Gaia)
        print(len(self.ra_Gaia))
        self.Gaia_RADECtoXY(self.ra_Gaia,self.dec_Gaia)

    def Gaia_RADECtoXY(self, ra_Gaia, dec_Gaia):
        viewer=self.fitsimage
        image = viewer.get_image()
        x_Gaia = [] 
        y_Gaia = []
        i=0
        for i in range(len(ra_Gaia)):
            x, y = image.radectopix(ra_Gaia[i], dec_Gaia[i], format='str', coords='fits')
            x_Gaia.append(x)
            y_Gaia.append(y)
        print("GAIA: Converted RADEC to XY for display")    
        self.plot_gaia(x_Gaia, y_Gaia)

            
    def plot_gaia(self,x_Gaia,y_Gaia):
# =============================================================================
        viewer=self.fitsimage
#         if image is None:
#                 # No image loaded
#             return
#         x_Gaia, y_Gaia = image.radectopix(RA, DEC, format='str', coords='fits')
# 
# =============================================================================
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
        print(self.ra_Gaia,self.dec_Gaia,self.string_RA_list,self.string_DEC_list)
        ####----------
        ### from https://mail.python.org/pipermail/astropy/2012-May/001761.html
        h = htm.HTM()
        maxrad=5.0/3600.0 
        m1,m2,radius = h.match( np.array(self.ra_Gaia), np.array(self.dec_Gaia), np.array(self.string_RA_list),np.array(self.string_DEC_list), maxrad)
        ####----------
        print(m1,m2)
        print((np.array(self.ra_Gaia)[m1]-np.array(self.string_RA_list)[m2])*3600)
        print((np.array(self.dec_Gaia)[m1]-np.array(self.string_DEC_list)[m2])*3600)
        g = [np.array(self.ra_Gaia)[m1],np.array(self.dec_Gaia)[m1]]
        #s = [np.array(self.string_RA_list)[m2],np.array(self.string_DEC_list)[m2]]
        #Gaia_pairs = np.reshape(g,(2,44))
        src = []
        for i in range(len(g[0])):
            src.append([g[0][i],g[1][i]])
            
        ####----------
        #create wcs
        #FROM https://docs.astropy.org/en/stable/api/astropy.wcs.utils.fit_wcs_from_points.html
        #xy   #   x & y pixel coordinates  (numpy.ndarray, numpy.ndarray) tuple
        #coords = g
        #These come from Gaia, epoch 2015.5
        world_coords  = SkyCoord(src, frame=FK4, unit=(u.deg, u.deg), obstime="J2015.5")  
        xy  = ( (self.xy[0])[m2], (self.xy[1])[m2] ) 
        wcs = fit_wcs_from_points( xy, world_coords, proj_point='center',projection='TAN',sip_degree=3) 
        ####----------
        ### update fits file header
        ### from https://docs.astropy.org/en/stable/wcs/example_create_imaging.html
        
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

    def create_menubar(self, parent):
        parent.geometry("900x600")
        parent.title("SAMOS CCD Controller")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")

        ## Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)  

        """
        ## proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """

        ## help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_separator()

        return menubar

"""
#############################################################################################################################################
#
#---------------------------------------- MAIN PAGE FRAME / CONTAINER ------------------------------------------------------------------------
#
#############################################################################################################################################
"""

class MainPage(tk.Frame):
    def __init__(self, parent, container):
        super().__init__(container)
        
        logger = log.get_logger("example2", options=None)
        self.logger = logger

        label = tk.Label(self, text="Main Page", font=('Times', '20'))
        label.pack(pady=0,padx=0)

        ## ADD CODE HERE TO DESIGN THIS PAGE

        # keep track of the entry number for header keys that need to be added
        # will be used to write "OtherParameters.txt" 
        self.extra_header_params = 0
        self.header_entry_string = '' #keep string of entries to write to a file after acquisition.

        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        self.SlitTabView = None
        
# =============================================================================
#         
#  #    FILTER STATUS Label Frame
#         
# =============================================================================
        self.frame0l = tk.Frame(self,background="cyan")#, width=400, height=800)
        self.frame0l.place(x=4, y=0, anchor="nw", width=220, height=110)
 
        labelframe_Filters =  tk.LabelFrame(self.frame0l, text="Filter Status", font=("Arial", 24))
        labelframe_Filters.pack(fill="both", expand="yes")
          

#        label_FW1 =  tk.Label(labelframe_Filters, text="Filters")
#        label_FW1.place(x=4,y=10)

        all_dirs = SF.read_dir_user()
        filter_data= ascii.read(local_dir+all_dirs['dir_system']+'/SAMOS_Filter_positions.txt')
        filter_names = list(filter_data[0:9]['Filter'])
        #print(filter_names)

        self.FW1_filter = tk.StringVar() 
        # initial menu text
        self.FW1_filter.set(filter_names[2])
        # Create Dropdown menu
        self.optionmenu_FW1 = tk.OptionMenu(labelframe_Filters, self.FW1_filter, *filter_names)
        self.optionmenu_FW1.place(x=5, y=8)
        button_SetFW1 =  tk.Button(labelframe_Filters, text="Set Filter", bd=3, command=self.set_filter)
        button_SetFW1.place(x=110,y=4)
        
#        self.Current_Filter = tk.StringVar()
#        self.Current_Filter.set(self.FW1_filter.get())
        self.Label_Current_Filter = tk.Text(labelframe_Filters,font=('Georgia 20'),width=8,height=1,bg='white', fg='green')
        #self.Label_Current_Filter.insert(tk.END,"",#self.FW1_Filter)
        self.Label_Current_Filter.insert(tk.END,self.FW1_filter.get())
        self.Label_Current_Filter.place(x=30,y=45)



# =============================================================================
#         entry_FW1 = tk.Entry(labelframe_Filters, width=11,  bd =3)
#         entry_FW1.place(x=100, y=10)
# # =============================================================================
# =============================================================================
#         label_FW1_template =  tk.Label(labelframe_Filters, text="HH:MM:SS.xx")
#         label_FW1_template.place(x=200,y=10)
#         
# =============================================================================
# =============================================================================
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
# =============================================================================

# =============================================================================
#         entry_FW2 = tk.Entry(labelframe_Filters, width=11, bd =3)
#         entry_FW2.place(x=100, y=40)
# # =============================================================================
# =============================================================================
#         label_FW1_template =  tk.Label(labelframe_Filters, text="2213DD:MM:SS.xx")
#         label_FW1_template.place(x=200,y=10)
#         
# =============================================================================
#        button_HomeFW1 =  tk.Button(labelframe_Filters, text="Home FW1", bd=3)
#        button_HomeFW1.place(x=4,y=70)
#        button_HomeFW2 =  tk.Button(labelframe_Filters, text="Home FW2", bd=3)
#        button_HomeFW2.place(x=105,y=70)

# =============================================================================
#         
#  #    GRISM STATUS Label Frame
#         
# =============================================================================
        self.frame1l = tk.Frame(self,background="cyan")#, width=400, height=800)
        self.frame1l.place(x=4, y=120, anchor="nw", width=220, height=110)

        labelframe_Grating =  tk.LabelFrame(self.frame1l, text="Grism Status", font=("Arial", 24))
        labelframe_Grating.pack(fill="both", expand="yes")
#        labelframe_Grating.place(x=4, y=10)
         
        all_dirs = SF.read_dir_user()
        Grating_data= ascii.read(local_dir+all_dirs['dir_system']+'/SAMOS_Filter_positions.txt')
        self.Grating_names = list(Grating_data[14:18]['Filter'])
        self.Grating_positions= list(Grating_data[14:18]['Position'])
#        print(Grating_names)
#
        self.Grating_Optioned = tk.StringVar() 
        # initial menu text
        index=2
        self.Grating_Optioned.set(self.Grating_names[index])
        # Create Dropdown menu
        self.optionmenu_GR = tk.OptionMenu(labelframe_Grating, self.Grating_Optioned, *self.Grating_names)
        self.optionmenu_GR.place(x=5, y=8)
        button_SetGR =  tk.Button(labelframe_Grating, text="Set Grating", bd=3, command=self.set_grating)
        button_SetGR.place(x=110,y=4)


# =============================================================================
#         self.Grating_int = tk.IntVar() 
#         self.Grating_int.set(2)  
#         self.optionmenu_GR = tk.OptionMenu(labelframe_Grating, self.Grating_int, *self.Grating_names)
#         self.optionmenu_GR.place(x=5, y=8)
#         button_SetGR =  tk.Button(labelframe_Grating, text="Set Grating", bd=3, command=self.set_grating)
#         button_SetGR.place(x=110,y=4)
# 
# =============================================================================
        self.Label_Current_Grating = tk.Text(labelframe_Grating,font=('Georgia 20'),width=8,height=1,bg='white', fg='green')
        #self.Label_Current_Filter.insert(tk.END,"",#self.FW1_Filter)
        self.Label_Current_Grating.insert(tk.END,self.Grating_names[index])
        self.Label_Current_Grating.place(x=30,y=45)

        
# =============================================================================
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
# =============================================================================
# =============================================================================

# =============================================================================
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
# =============================================================================
#         self.frame0r = tk.Frame(self,background="cyan")#, width=400, height=800)
#         self.frame0r.place(x=601, y=0, anchor="nw", width=500, height=800)
#         
#         
#         vbox = tk.Frame(self.frame0l, relief=tk.RAISED, borderwidth=1)
#         vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
# =============================================================================


# =============================================================================
#         
#  #    ACQUIRE IMAGE Label Frame
#         
# =============================================================================
        self.frame2l = tk.Frame(self,background="cyan")#, width=400, height=800)
        self.frame2l.place(x=0, y=240, anchor="nw", width=370, height=280)

#        root = tk.Tk()
#        root.title("Tab Widget")
        tabControl = ttk.Notebook(self.frame2l)
  
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        tab4 = ttk.Frame(tabControl)
  
        tabControl.add(tab1, text ='Image')
        tabControl.add(tab2, text ='Bias')
        tabControl.add(tab3, text ='Dark')
        tabControl.add(tab4, text ='Flat')
        tabControl.pack(expand = 1, fill ="both")
  
# =============================================================================
#      SCIENCE
# =============================================================================

        labelframe_Acquire =  tk.LabelFrame(tab1, text="Acquire Image", font=("Arial", 24))
        labelframe_Acquire.pack(fill="both", expand="yes")
#        labelframe_Grating.place(x=4, y=10)

        label_ExpTime =  tk.Label(labelframe_Acquire, text="Exp. Time (s)")
        label_ExpTime.place(x=4,y=10)
        self.Light_ExpT=tk.StringVar()
        self.Light_ExpT.set("0.01")
        entry_ExpTime = tk.Entry(labelframe_Acquire, textvariable=self.Light_ExpT, width=5,  bd =3)
        entry_ExpTime.place(x=100, y=10)

        label_ObjectName =  tk.Label(labelframe_Acquire, text="Object Name:")
        label_ObjectName.place(x=4,y=40)
        entry_ObjectName = tk.Entry(labelframe_Acquire, width=11,  bd =3)
        entry_ObjectName.place(x=100, y=38)

        label_Comment =  tk.Label(labelframe_Acquire, text="Comment:")
        label_Comment.place(x=4,y=70)
#        scrollbar = tk.Scrollbar(orient="horizontal")
        entry_Comment = tk.Entry(labelframe_Acquire, width=11,  bd =3)# , xscrollcommand=scrollbar.set)
        entry_Comment.place(x=100, y=68)

        button_ExpStart=  tk.Button(labelframe_Acquire, text="READ", bd=3, bg='#0052cc',font=("Arial", 24),
                                         command=self.expose_light)
        button_ExpStart.place(x=75,y=95)

        label_Display =  tk.Label(labelframe_Acquire, text="Subtract for Display:")
        label_Display.place(x=4,y=135)
        self.subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(labelframe_Acquire, text='Bias',variable=self.subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=155)
        self.subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(labelframe_Acquire, text='Dark',variable=self.subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60,y=155)
        self.subtract_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(labelframe_Acquire, text='Flat',variable=self.subtract_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120,y=155)

# =============================================================================
#      BIAS
# =============================================================================
        labelframe_Bias =  tk.LabelFrame(tab2, text="Bias", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Bias.pack(fill="both", expand="yes")

#        labelframe_Bias.place(x=5,y=5)
        label_Bias_ExpT =  tk.Label(labelframe_Bias, text="Exposure time (s):")
        label_Bias_ExpT.place(x=4,y=10)
        self.Bias_ExpT = tk.StringVar(value="0.00")
        entry_Bias_ExpT = tk.Entry(labelframe_Bias, width=6,  bd =3, textvariable=self.Bias_ExpT)
        entry_Bias_ExpT.place(x=120, y=6)
        
        label_Bias_NofFrames =  tk.Label(labelframe_Bias, text="Nr. of Frames:")
        label_Bias_NofFrames.place(x=4,y=40)
        self.Bias_NofFrames = tk.StringVar(value="10")
        entry_Bias_NofFrames = tk.Entry(labelframe_Bias, width=5,  bd =3, textvariable=self.Bias_NofFrames)
        entry_Bias_NofFrames.place(x=100, y=38)
        
        
        self.var_Bias_saveall = tk.IntVar()
        r1_Bias_saveall = tk.Radiobutton(labelframe_Bias, text = "Save single frames", variable=self.var_Bias_saveall, value=1)
        r1_Bias_saveall.place(x=160, y=38)

        label_Bias_MasterFile =  tk.Label(labelframe_Bias, text="Master Bias File:")
        label_Bias_MasterFile.place(x=4,y=70)
        self.Bias_MasterFile = tk.StringVar(value="Bias")
        entry_Bias_MasterFile = tk.Entry(labelframe_Bias, width=11,  bd =3, textvariable=self.Bias_MasterFile)
        entry_Bias_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Bias, text="START", bd=3, bg='#0052cc',font=("Arial", 24),
                                          command=self.expose_bias)
        button_ExpStart.place(x=75,y=95)
  
#        root.mainloop()  




        
# =============================================================================
#      Dark
# =============================================================================
        labelframe_Dark =  tk.LabelFrame(tab3, text="Dark", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Dark.pack(fill="both", expand="yes")

        label_Dark_ExpT =  tk.Label(labelframe_Dark, text="Exposure time (s):")
        label_Dark_ExpT.place(x=4,y=10)
        self.Dark_ExpT = tk.StringVar(value="0.00")
        entry_Dark_ExpT = tk.Entry(labelframe_Dark, width=6,  bd =3, textvariable=self.Dark_ExpT)
        entry_Dark_ExpT.place(x=120, y=6)
        
        label_Dark_NofFrames =  tk.Label(labelframe_Dark, text="Nr. of Frames:")
        label_Dark_NofFrames.place(x=4,y=40)
        self.Dark_NofFrames = tk.StringVar(value="10")
        entry_Dark_NofFrames = tk.Entry(labelframe_Dark, width=5,  bd =3, textvariable=self.Dark_NofFrames)
        entry_Dark_NofFrames.place(x=100, y=38)
        
        
        self.var_Dark_saveall = tk.IntVar()
        r1_Dark_saveall = tk.Radiobutton(labelframe_Dark, text = "Save single frames", variable=self.var_Dark_saveall, value=1)
        r1_Dark_saveall.place(x=160, y=38)

        label_Dark_MasterFile =  tk.Label(labelframe_Dark, text="Master Dark File:")
        label_Dark_MasterFile.place(x=4,y=70)
        self.Dark_MasterFile = tk.StringVar(value="Dark")
        entry_Dark_MasterFile = tk.Entry(labelframe_Dark, width=11,  bd =3, textvariable=self.Dark_MasterFile)
        entry_Dark_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Dark, text="START", bd=3, bg='#0052cc',font=("Arial", 24),
                                          command=self.expose_dark)
        button_ExpStart.place(x=75,y=95)

# =============================================================================
#      Flat
# =============================================================================
        labelframe_Flat =  tk.LabelFrame(tab4, text="Flat", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Flat.pack(fill="both", expand="yes")

        label_Flat_ExpT =  tk.Label(labelframe_Flat, text="Exposure time (s):")
        label_Flat_ExpT.place(x=4,y=10)
        self.Flat_ExpT = tk.StringVar(value="0.00")
        entry_Flat_ExpT = tk.Entry(labelframe_Flat, width=6,  bd =3, textvariable=self.Flat_ExpT)
        entry_Flat_ExpT.place(x=120, y=6)
        
        label_Flat_NofFrames =  tk.Label(labelframe_Flat, text="Nr. of Frames:")
        label_Flat_NofFrames.place(x=4,y=40)
        self.Flat_NofFrames = tk.StringVar(value="10")
        entry_Flat_NofFrames = tk.Entry(labelframe_Flat, width=5,  bd =3, textvariable=self.Flat_NofFrames)
        entry_Flat_NofFrames.place(x=100, y=38)
        
        
        self.var_Flat_saveall = tk.IntVar()
        r1_Flat_saveall = tk.Radiobutton(labelframe_Flat, text = "Save single frames", variable=self.var_Flat_saveall, value=1)
        r1_Flat_saveall.place(x=160, y=38)

        label_Flat_MasterFile =  tk.Label(labelframe_Flat, text="Master Flat File:")
        label_Flat_MasterFile.place(x=4,y=70)
        self.Flat_MasterFile = tk.StringVar(value="Flat")
        entry_Flat_MasterFile = tk.Entry(labelframe_Flat, width=11,  bd =3, textvariable=self.Flat_MasterFile)
        entry_Flat_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Flat, text="START", bd=3, bg='#0052cc',font=("Arial", 24),
                                          command=self.expose_flat)
        button_ExpStart.place(x=75,y=95)



        
        
# =============================================================================
#         
#  #    FITS manager
#         
# =============================================================================
        self.frame_FITSmanager = tk.Frame(self,background="pink")#, width=400, height=800)
        self.frame_FITSmanager.place(x=0, y=500, anchor="nw", width=400, height=250)

        labelframe_FITSmanager =  tk.LabelFrame(self.frame_FITSmanager, text="FITS manager", font=("Arial", 24))
        labelframe_FITSmanager.pack(fill="both", expand="yes")

# =============================================================================
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
# =============================================================================
 
        button_FITS_Load =  tk.Button(labelframe_FITSmanager, text="FITS Load", bd=3, 
                                           command=self.load_last_file)
        button_FITS_Load.place(x=0,y=25)
        
        self.string_RA = tk.StringVar()
#        self.string_RA.set("189.99763")  #Sombrero
        self.string_RA.set("150.17110")  #NGC 3105
        label_RA = tk.Label(labelframe_FITSmanager, text='RA:',  bd =3)
        self.entry_RA = tk.Entry(labelframe_FITSmanager, width=11,  bd =3, textvariable = self.string_RA)
        label_RA.place(x=190,y=5)
        self.entry_RA.place(x=230,y=5)
        
        self.string_DEC = tk.StringVar()
#        self.string_DEC.set("-11.62305")#Sombrero
        self.string_DEC.set("-54.79004") #NGC 3105
        label_DEC = tk.Label(labelframe_FITSmanager, text='Dec:',  bd =3)
        self.entry_DEC = tk.Entry(labelframe_FITSmanager, width=11,  bd =3, textvariable = self.string_DEC)
        label_DEC.place(x=290,y=30)
        self.entry_DEC.place(x=230,y=30)
        
        self.string_Filter = tk.StringVar()
        self.string_Filter.set("i")
        label_Filter = tk.Label(labelframe_FITSmanager, text='Filter:',  bd =3)
        entry_Filter = tk.Entry(labelframe_FITSmanager, width=3,  bd =3,textvariable = self.string_Filter)
        label_Filter.place(x=190,y=55)
        entry_Filter.place(x=230,y=55)

        button_skymapper_query =  tk.Button(labelframe_FITSmanager, text="SkyMapper Query", bd=3, 
                                           command=self.SkyMapper_query)
        button_skymapper_query.place(x=190,y=80)
        
        button_skymapper_save =  tk.Button(labelframe_FITSmanager, text="SkyMapper Save", bd=3, 
                                           command=self.SkyMapper_save)
        button_skymapper_save.place(x=190,y=105)
        
        button_twirl_Astrometry =  tk.Button(labelframe_FITSmanager, text="twirl_Astrometry", bd=3, 
#                                            command=Astrometry)
                                            command=self.twirl_Astrometry)
        button_twirl_Astrometry.place(x=190,y=130)
        
        #self.stop_it = 0
        
        button_FITS_start =  tk.Button(labelframe_FITSmanager, text="FITS start", bd=3, 
                                           command=self.check_for_file_existence)#start_the_loop)
        button_FITS_start.place(x=0,y=50)

# =============================================================================
        button_Astrometry =  tk.Button(labelframe_FITSmanager, text="Astrometry", bd=3, 
#                                            command=Astrometry)
                                            command=self.load_Astrometry)
        button_Astrometry.place(x=0,y=110)

# 
# =============================================================================
        button_run_Sextractor =  tk.Button(labelframe_FITSmanager, text="run DaoFind", bd=3, 
                                            command=self.run_DaoFind)
        button_run_Sextractor.place(x=0,y=80)
        label_sigma =  tk.Label(labelframe_FITSmanager, text="sigma")
        label_sigma.place(x=120,y=82)
        self.sigma=tk.StringVar()
        entry_sigma = tk.Entry(labelframe_FITSmanager, width=3,  bd =3, textvariable=self.sigma)
        entry_sigma.place(x=160, y=80)
        self.sigma.set('25')


# 
# =============================================================================
        button_show_slits =  tk.Button(labelframe_FITSmanager, text="Show slits", bd=3, 
#                                            command=Astrometry)
                                            command=self.show_slits)
        button_show_slits.place(x=0,y=140)

# =============================================================================
#
# GINGA DISPLAY
#
# =============================================================================

        vbox = tk.Frame(self, relief=tk.RAISED, borderwidth=1)
#        vbox.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        vbox.pack(side=tk.TOP)
        vbox.place(x=350, y=0, anchor="nw")#, width=500, height=800)
        #self.vb = vbox

#        canvas = tk.Canvas(vbox, bg="grey", height=514, width=522)
        canvas = tk.Canvas(vbox, bg="grey", height=516, width=528)
        canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        fi = CanvasView(logger) #=> ImageViewTk -- a backend for Ginga using a Tk canvas widget
        fi.set_widget(canvas)  #=> Call this method with the Tkinter canvas that will be used for the display.
        #fi.set_redraw_lag(0.0)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        fi.enable_autozoom('on')
        #fi.enable_draw(False)
        # tk seems to not take focus with a click
        fi.set_enter_focus(True)
        fi.set_callback('cursor-changed', self.cursor_cb)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        # add little mode indicator that shows keyboard modal states
        fi.show_mode_indicator(True, corner = 'ur')
        self.fitsimage = fi

        bd = fi.get_bindings()
        bd.enable_all(True)

        # canvas that we will draw on
#        DrawingCanvas = fi.getDrawClasses('drawingcanvas')
        canvas = self.canvas_types.DrawingCanvas()
        canvas.enable_draw(True)
        canvas.enable_edit(True)
        canvas.set_drawtype('point', color='red')
        canvas.register_for_cursor_drawing(fi)
        canvas.add_callback('draw-event', self.draw_cb)
        canvas.set_draw_mode('draw')

        # without this call, you can only draw with the right mouse button
        # using the default user interface bindings
        #canvas.register_for_cursor_drawing(fi)

        canvas.set_surface(fi)
        canvas.ui_set_active(True)
        self.canvas = canvas


#        # add canvas to viewers default canvas
        fi.get_canvas().add(canvas)

        self.drawtypes = canvas.get_drawtypes()
        self.drawtypes.sort()

#        fi.configure(516, 528) #height, width
        fi.set_window_size(514,522)
        
        """
        HORIZONTAL BOX AT THE BOTTOM WITH ORIGINAL GINGA TOOLS
        """

        hbox = tk.Frame(self)
        hbox.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.readout = tk.Label(self, text='')
        self.readout.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.drawtypes = canvas.get_drawtypes()
        ## wdrawtype = ttk.Combobox(self, values=self.drawtypes,
        ##                         command=self.set_drawparams)
        ## index = self.drawtypes.index('ruler')
        ## wdrawtype.current(index)
        wdrawtype = tk.Entry(hbox, width=12)
        wdrawtype.insert(0, 'point')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype

        #self.vslit = tk.IntVar()
        #wslit = tk.Checkbutton(hbox, text="Slit", variable=self.vslit)
        #self.wslit = wslit

        wdrawcolor = ttk.Combobox(hbox, values=self.drawcolors)#,
        #                           command=self.set_drawparams)
        index = self.drawcolors.index('lightblue')
        wdrawcolor.current(index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        #wdrawcolor = tk.Entry(hbox, width=12)
        #wdrawcolor.insert(0, 'blue')
        #wdrawcolor.bind("<Return>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor

        self.vfill = tk.IntVar()
        wfill = tk.Checkbutton(hbox, text="Fill", variable=self.vfill)
        self.wfill = wfill

        walpha = tk.Entry(hbox, width=12)
        walpha.insert(0, '1.0')
        walpha.bind("<Return>", self.set_drawparams)
        self.walpha = walpha

        wrun = tk.Button(hbox, text="Run code",
                                command=self.run_code)
        wclear = tk.Button(hbox, text="Clear Canvas",
                                command=self.clear_canvas)
        wsave = tk.Button(hbox, text="Save Canvas",
                                command=self.save_canvas)
        wopen = tk.Button(hbox, text="Open File",
                               command=self.open_file)
                # pressing quit button freezes application and forces kernel restart.
        wquit = tk.Button(hbox, text="Quit",
                               command=lambda: self.quit(self))

        for w in (wquit, wsave, wclear, wrun, walpha, tk.Label(hbox, text='Alpha:'),
#                  wfill, wdrawcolor, wslit, wdrawtype, wopen):
                  wfill, wdrawcolor, wdrawtype, wopen):
            w.pack(side=tk.RIGHT)
 

        #mode = self.canvas.get_draw_mode() #initially set to draw by line >canvas.set_draw_mode('draw')
        hbox1 = tk.Frame(hbox)
        hbox1.pack(side=tk.BOTTOM, fill=tk.X, expand=0)

        self.setChecked = tk.StringVar(None,"draw")
        btn1 = tk.Radiobutton(hbox1,text="Draw",padx=20,variable=self.setChecked,value="draw", command=self.set_mode_cb).pack(anchor=tk.SW)
        btn2 = tk.Radiobutton(hbox1,text="Edit",padx=20,variable=self.setChecked,value="edit", command=self.set_mode_cb).pack(anchor=tk.SW)
        btn3 = tk.Radiobutton(hbox1,text="Pick",padx=20,variable=self.setChecked,value="pick", command=self.set_mode_cb).pack(anchor=tk.SW)
 
# =============================================================================
#         
#  #    SLIT Configuration Frame
#         
# =============================================================================
        self.frame_SlitConf = tk.Frame(self,background="gray")#, width=400, height=800)
        self.frame_SlitConf.place(x=400, y=600, anchor="nw", width=360, height=150)
        labelframe_SlitConf =  tk.LabelFrame(self.frame_SlitConf, text="Slit Configuration", font=("Arial", 24))
        labelframe_SlitConf.pack(fill="both", expand="yes")

# =============================================================================
#  #    SLIT WIDTH in mirrors, dispersion direction (affects Resolving power)
# =============================================================================        
        label_slit_w = tk.Label(labelframe_SlitConf, text="Slit width (mirrors)")
        label_slit_w.place(x=4,y=4)
        self.slit_w = tk.IntVar(value=3) 
        self.textbox_slit_w = tk.Entry(labelframe_SlitConf, textvariable=self.slit_w, width = 4)      
        self.textbox_slit_w.place(x=130,y=5)

# =============================================================================
#  #    SLIT LENGTH in mirror, cross-dispersion (affets sky subtraction) 
# =============================================================================        
        label_slit_l = tk.Label(labelframe_SlitConf, text="Slit length (mirrors)")
        label_slit_l.place(x=4,y=29)
        self.slit_l = tk.IntVar() 
        self.slit_l.set(9)
        self.textbox_slit_l = tk.Entry(labelframe_SlitConf, textvariable=self.slit_l, width = 4)      
        self.textbox_slit_l.place(x=130,y=30)

# =============================================================================
#  #    SLIT POINTER ENABLED
# =============================================================================        
        self.vslit = tk.IntVar()
        wslit = tk.Checkbutton(labelframe_SlitConf, text="Slit Pointer", variable=self.vslit)
        wslit.place(x=180, y=4)
        
        """
# =============================================================================
#         
#  #    DMD Handler Label Frame
#         
# =============================================================================
        self.frame0r = tk.Frame(self,background="cyan")#, width=400, height=800)
        self.frame0r.place(x=1270, y=10, anchor="nw", width=360, height=120)
 
        labelframe_DMD =  tk.LabelFrame(self.frame0r, text="DMD", font=("Arial", 24))
        labelframe_DMD.pack(fill="both", expand="yes")
 
         #1) Set the x size of the default slit
         #2) Set the y size of the default slit
         #3) save slit pattern to file 
         #4) save and push slit pattern
         #5) load slit pattern
         #6) shift slit pattern
         #7) analyze point source
         #8) remove slit
 
# =============================================================================
         #3) write slit pattern
# =============================================================================
        regfname_entry = tk.Entry(labelframe_DMD)
        regfname_entry.place(x=0,y=25, width=150)
        regfname_entry.config(fg='grey',bg='white') # default text is greyed out
        regfname_entry.insert(tk.END,"enter pattern name")
        regfname_entry.bind("<FocusIn>", self.regfname_handle_focus_in) 
        #regfname_entry.bind("<FocusOut>", self.regfname_handle_focus_out)
        self.regfname_entry = regfname_entry
        # click in entry box deletes default text and allows entry of new text
        button_write_slits =  tk.Button(labelframe_DMD, text="SAVE: Slits -> .reg file", bd=3, command=self.write_slits)
        button_write_slits.place(x=155,y=25)      
        
        
        button_load_regfile_xyAP =  tk.Button(labelframe_DMD, text="LOAD: .reg file -> Slits", bd=3, command=self.load_regfile_xyAP)
        button_load_regfile_xyAP.place(x=155,y=50)
        
        button_push_slits =  tk.Button(labelframe_DMD, text="Slits -> DMD", bd=3, font=("Arial", 24),  relief=tk.RAISED, command=self.push_slits)
        button_push_slits.place(x=80,y=85)
        """

# =============================================================================
         #4)# LOAD BUTTONS
# =============================================================================
        """
        button_load_map = tk.Button(labelframe_DMD,
                        text = "Load DMD Map",
                        command = self.LoadMap)
        button_load_map.place(x=4,y=162)

        label_filename = tk.Label(labelframe_DMD, text="Current DMD Map")
        label_filename.place(x=4,y=190)
        self.str_filename = tk.StringVar() 
        self.textbox_filename = tk.Text(labelframe_DMD, height = 1, width = 22)      
        self.textbox_filename.place(x=120,y=190)
        """
        
        """
        button_load_slits = tk.Button(labelframe_DMD,
                       text = "Load Slit Grid",
                       command = self.LoadSlits)
        button_load_slits.place(x=4,y=222)

        label_filename_slits = tk.Label(labelframe_DMD, text="Current Slit Grid")
        label_filename_slits.place(x=4,y=250)
        self.str_filename_slits = tk.StringVar() 
        self.textbox_filename_slits = tk.Text(labelframe_DMD, height = 1, width = 22)      
        self.textbox_filename_slits.place(x=120,y=250)
        """

        """
        button_save_slittable = tk.Button(labelframe_DMD,
                       text = "Save Slit Table",
                       command = self.Save_slittable)
        button_save_slittable.place(x=4,y=282)
        
        label_filename_slittable = tk.Label(labelframe_DMD, text="Saved Slit Table")
        label_filename_slittable.place(x=4,y=310)
        self.str_filename_slittable = tk.StringVar() 
        self.textbox_filename_slittable= tk.Text(labelframe_DMD, height = 1, width = 22)      
        self.textbox_filename_slittable.place(x=120,y=310)
        """


        
        """   
# =============================================================================
#         
#  #    DMD Handler Label Frame
#         
# =============================================================================
        """        
        self.frame1r = tk.Frame(self)#, width=400, height=800)
        self.frame1r.place(x=900, y=5, anchor="nw", width=360, height=800)
 
# =============================================================================         
#  #    RADEC module
# =============================================================================
        labelframe_Sky =  tk.LabelFrame(self.frame1r, 
                                        text="Sky (RA,Dec) regions", 
                                        font=("Arial", 20), bg="#8AA7A9")
        labelframe_Sky.pack(fill="both", expand="yes")
        
        button_load_regfile_RADEC = tk.Button(labelframe_Sky,
                                         text = "load (RA,Dec) regions from astropy .reg file", 
                                         command = self.load_regfile_RADEC)
        button_load_regfile_RADEC.place(x=4,y=4)
        
        label_filename_regfile_RADEC = tk.Label(labelframe_Sky, 
                                         text="Loaded Region File in RADEC units:", 
                                         bg="#8AA7A9")
        label_filename_regfile_RADEC.place(x=4,y=34)
        self.str_filename_regfile_RADEC = tk.StringVar() 
        self.textbox_filename_regfile_RADEC= tk.Text(labelframe_Sky, height = 1, width = 48)      
        self.textbox_filename_regfile_RADEC.place(x=4,y=55)

        button_push_RADEC = tk.Button(labelframe_Sky,
                                          text = "get center/point (RA,Dec) from filename",
                                          command = self.push_RADEC)
        button_push_RADEC.place(x=54,y=90)

        label_workflow = tk.Label(labelframe_Sky, text="Point, take an image and twirl WCS from GAIA...", bg="#8AA7A9")
        label_workflow.place(x=4,y=130)

        button_regions_RADEC2pixel = tk.Button(labelframe_Sky,
                                           text = "convert (RA,Dec) regions -> (x,y) regions",
                                           command = self.convert_regions_RADEC2xy)
        button_regions_RADEC2pixel.place(x=4,y=151)

        button_regions_RADEC_save= tk.Button(labelframe_Sky,
                                            text = "save (RA,Dec) regions -> astropy RADEC.reg file",
                                            command = self.save_RADECregions_AstropyRADECRegFile)
        button_regions_RADEC_save.place(x=4,y=181)

        """
        button_regions_RADEC_save= tk.Button(labelframe_Sky,
                                            text = "save (RA,Dec) regions -> astropy XY.reg file",
                        command = self.save_RADECregions_AstropyXYRegFile)
        button_regions_RADEC_save.place(x=4,y=211)
        """
 # =============================================================================         
 #  #    CCD  module
 # =============================================================================
        labelframe_CCD =  tk.LabelFrame(self.frame1r, 
                                        text="CCD (x,y) regions", font=("Arial", 20), bg="#00CED1")
        labelframe_CCD.pack(fill="both", expand="yes")
         
        button_load_regfile_xyAP = tk.Button(labelframe_CCD,
                                        text = "load (x,y) regions from .reg file", 
                                        command = self.load_regfile_xyAP)
        button_load_regfile_xyAP.place(x=4,y=4)
         
        label_filename_regfile_xyAP = tk.Label(labelframe_CCD, 
                                        text="Loaded Region File in CCD units:", 
                                        bg="#00CED1")
        label_filename_regfile_xyAP.place(x=4,y=34)
        self.str_filename_regfile_xyAP = tk.StringVar() 
        self.textbox_filename_regfile_xyAP= tk.Text(labelframe_CCD, height = 1, width = 48)      
        self.textbox_filename_regfile_xyAP.place(x=4,y=55)

        """
        button_push_CCD = tk.Button(labelframe_CCD,
                        text = "get pointing RA,DEC from filename",
                        command = self.push_CCD)
        button_push_CCD.place(x=54,y=90)
        """
        
        """
        label_workflow = tk.Label(labelframe_CCD, text="Point, take an image and twirl WCS from GAIA...", bg="#00CED1")
        label_workflow.place(x=4,y=130)
        """
        
        button_regions_CCD2RADEC = tk.Button(labelframe_CCD,
                                        text = "convert (x,y) regions -> (RA,Dec) regions",
                                        command = self.convert_regions_xy2RADEC)
        button_regions_CCD2RADEC.place(x=4,y=121)

        
        """
        button_regions_CCD2pixel = tk.Button(labelframe_CCD,
                                        text = "convert (x,y) regions -> slits",
                                        command = self.convert_regions_xyAP2xyGA)
        button_regions_CCD2pixel.place(x=4,y=151)
        """
        
        button_regions_draw = tk.Button(labelframe_CCD,
                                        text = "DRAW",
                                        command = self.draw_slits)
        button_regions_draw.place(x=250,y=151)

        button_regions_CCD_save= tk.Button(labelframe_CCD,
                                        text = "save (x,y) regions -> astropy .reg file",
                                        command = self.save_regions_xy2xyfile)
        button_regions_CCD_save.place(x=4,y=181)
       
 # =============================================================================         
 #  #    DMD  module
 # =============================================================================
        labelframe_DMD =  tk.LabelFrame(self.frame1r, text="DMD slits", font=("Arial", 20), bg="#20B2AA")
        labelframe_DMD.pack(fill="both", expand="yes")
         
        """
        button_load_regfile_DMD = tk.Button(labelframe_DMD,
                        text = "load targets DMD from .reg file", 
                        command = self.load_regfile_DMD)
        button_load_regfile_DMD.place(x=4,y=4)
        
        label_filename_regfile_DMD = tk.Label(labelframe_DMD, text="Loaded Region File in DMD units:", bg="#20B2AA")
        label_filename_regfile_DMD.place(x=4,y=34)
        self.str_filename_regfile_DMD = tk.StringVar() 
        self.textbox_filename_regfile_DMD= tk.Text(labelframe_DMD, height = 1, width = 48)      
        self.textbox_filename_regfile_DMD.place(x=4,y=55)

        button_push_DMD = tk.Button(labelframe_DMD,
                        text = "get pointing RA,DEC from filename",
                        command = self.push_DMD)
        button_push_DMD.place(x=54,y=90)

        label_workflow = tk.Label(labelframe_DMD, text="Point, take an image and twirl WCS from GAIA...", bg="#20B2AA")
        label_workflow.place(x=4,y=130)
        """
        button_load_slits = tk.Button(labelframe_DMD,
                       text = "Load Slit .csv table",
                       command = self.load_regfile_csv)
        button_load_slits.place(x=4,y=4)

        label_filename_slits = tk.Label(labelframe_DMD, text="Current Slit Grid", bg="#20B2AA")
        label_filename_slits.place(x=4,y=34)
        self.str_filename_slits = tk.StringVar() 
        self.textbox_filename_slits = tk.Text(labelframe_DMD, height = 1, width = 22)      
        self.textbox_filename_slits.place(x=120,y=34)

        
        button_regions_DMD2pixel = tk.Button(labelframe_DMD,
                                            text = "convert slits -> (x,y) pixels",
                        command = self.convert_regions_slit2xyAP)
        button_regions_DMD2pixel.place(x=4,y=84)

        """
        button_regions_DMD_save= tk.Button(labelframe_DMD,
                                             text = "save Regions RA,DEC -> astropy .reg file",
                         command = self.save_regions_DMD_AstropyReg)
        button_regions_DMD_save.place(x=4,y=181)
        """
        button_push_slits =  tk.Button(labelframe_DMD, text="Slits -> DMD", bd=3, font=("Arial", 24),  relief=tk.RAISED, 
                                       command=self.push_slits)
        button_push_slits.place(x=80,y=125)

        
        button_save_slittable = tk.Button(labelframe_DMD,
                       text = "Save Slit .csv table",
                       command = self.Save_slittable)
        button_save_slittable.place(x=4,y=181)
        
        label_filename_slittable = tk.Label(labelframe_DMD, text="Saved Slit .csv table")
        label_filename_slittable.place(x=4,y=210)
        self.str_filename_slittable = tk.StringVar() 
        self.textbox_filename_slittable= tk.Text(labelframe_DMD, height = 1, width = 22)      
        self.textbox_filename_slittable.place(x=120,y=210)

        
        
       

     
# =============================================================================
#
# Load AP Region file in RADEC
#
# =============================================================================
    def save_regions_DMD_AstropyReg(self): 
        pass
    
 
    def push_DMD(self):
        pass

    def load_regfile_csv(self):
        pass

    def save_regions_xy2xyfile(self):
        print("saving (x,y) Astropy Regions to .reg file")
        file = filedialog.asksaveasfile(filetypes = [("txt file", ".reg")], 
                                        defaultextension = ".reg",
                                        initialdir=local_dir+"/SAMOS_regions/pixels")
        #1. Collect all
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        #2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        #3. Write astropy regions, pixels
        self.RRR_xyAP.write(file.name, overwrite=True)
        print("(x,y) Astropy Regions to .reg file:\n",file.name)

    def push_CCD(self):
        pass
        
        
    def save_RADECregions_AstropyRADECRegFile(self): 
        if "RRR_RADec" not in dir(self):
            print("There are no (RA,Dec) regions to be written on file")
            return
        else:
            print("saving (RA,DEC) Astropy Regions to .reg file")
            file = filedialog.asksaveasfile(filetypes = [("txt file", ".reg")], 
                                        defaultextension = ".reg",
                                        initialdir=local_dir+"/SAMOS_regions/RADEC")
        #we want to scoop all objects on the canvas
        #obj_all = CM.CompoundMixin.get_objects(self.canvas)
            self.RRR_RADec = self.convert_regions_xy2RADEC()
            self.RRR_RADec.write(file.name, overwrite=True)
            print("saved  (RA,DEC) Astropy Regions to .reg file:\n",file.name)


    """
    def save_RADECregions_AstropyXYRegFile(self): 
        print("saving (x,y) Astropy Regions to .reg file")
        self.convert_regions_RADEC2xyAP()
        file = filedialog.asksaveasfile(filetypes = [("txt file", ".reg")], 
                                        defaultextension = ".reg",
                                        initialdir=local_dir+"/SAMOS_regions/pixels")
        self.RRR_xyAP.write(file.name, overwrite=True)
    """    


    def convert_regions_RADEC2xy(self): 
        print("converting (RA,DEC) Astropy Regions to (x,y) Astropy Regions")
        #requires wcs: class AStrometry
        if 'wcs' not in dir(self): 
            print("missing self.wcs. No operation performed \n")
            return
        self.RRR_xyAP  = Astrometry.APRegion_RAD2pix(self.filename_regfile_RADEC,self.wcs)
        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        print("RADec regions converted to xy regions\nRRR_xyAP created")
        #return self.RRR_xyAP
  
    def convert_regions_xy2RADEC(self):
        print("converting (x,y) Astropy Regions to (RA,DEC) Astropy Regions")
        #requires wcs: class AStrometry
        if 'wcs' not in dir(self): 
            print("missing self.wcs. No operation performed \n")
            return
        #1. Collect all
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        #2. convert to Astropy, pixels
        self.RRR_xyAP = self.convert_regions_xyGA2xyAP()
        #3. convert to RADEC using wcs
        self.RRR_RADec = Astrometry.APRegion_pix2RAD(self.RRR_xyAP,self.wcs)
        print("(x,y) Astropy regions converted to (RA,DEC) Astropy regions")
        return self.RRR_RADec

    def draw_slits(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        #color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas,color="red")
    
    """
    def convert_regions_xyAP2slit(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        #color in RED all the regions loaded from .reg file
        #requires Dana wcs
        #returns .csv map file 
        pass
    """

    def convert_regions_slit2xyAP(self):
        #requires Dana wcs
        #returns RRR_xyAP
        pass
    
    def convert_regions_xyAP2xyGA(self):
        print("converting (x,y) Astropy Regions to (x,y) Ginga Regions")
        [CM.CompoundMixin.add_object(self.canvas,r2g(reg)) for reg in self.RRR_xyAP]
        #uses r2g
        self.RRR_xyGA = CM.CompoundMixin.get_objects(self.canvas)
        print("(x,y) Astropy regions converted to (x,y) Ginga regions\nRRR_xyGA created")
        return self.RRR_xyGA
        #self.RRR_xyGA is a self.canvas.objects
       
     
    def convert_regions_xyGA2xyAP(self):
        print("converting (x,y) Ginga Regions to (x,y) Astropy Regions")
        all_ginga_objects = CM.CompoundMixin.get_objects(self.canvas)
        list_all_ginga_objects = list(all_ginga_objects)
        if len(list_all_ginga_objects) != 0:
            self.RRR_xyAP=Regions([g2r(list_all_ginga_objects[0])])
            for i in range(1,len(list_all_ginga_objects)):
                self.RRR_xyAP.append(g2r(list_all_ginga_objects[i]))
        return self.RRR_xyAP
        print("(x,y) Ginga regions converted to (x,y) Astropy regions")
        

    def push_RADEC(self):
        self.string_RA  = tk.StringVar(self,self.RA_regCNTR)
        self.string_DEC  = tk.StringVar(self,self.DEC_regCNTR)
        self.entry_RA.delete(0, tk.END)
        self.entry_DEC.delete(0, tk.END)
        self.entry_RA.insert(0, self.RA_regCNTR)
        self.entry_DEC.insert(0, self.DEC_regCNTR)
        print("RADEC loaded")

    def load_regfile_RADEC(self):
        print("reading (RA,DEC) Regions from .reg file")        
        self.textbox_filename_regfile_RADEC.delete('1.0', tk.END)
#        self.textbox_filename_slits.delete('1.0', tk.END)
        self.filename_regfile_RADEC = filedialog.askopenfilename(initialdir = local_dir +"/SAMOS_regions/RADEC",
                                        title = "Select a File",
                                        filetypes = (("Text files",
                                                      "*.reg"),
                                                     ("all files",
                                                      "*.*")))
        #First read the file and set the regions in original RADEC units
        self.RRR_RADec = Regions.read(self.filename_regfile_RADEC, format='ds9')
        #
        #Then extract the clean filename to get RA and DEC of the central point
        head, tail = os.path.split(self.filename_regfile_RADEC)
        self.textbox_filename_regfile_RADEC.insert(tk.END, tail)
        #the filename must carry the RADEC coordinates are "RADEC_". Find this string...
        s=re.search(r'RADEC=',tail)
        #extract RADEC
        RADEC = tail[s.end():-4]
        RA_cut=(re.findall('.*-',RADEC))
        #and RA, DEC as strings at disposal 
        self.RA_regCNTR = RA_cut[0][:-1]
        self.DEC_regCNTR = (re.findall('-.*',RADEC))[0]
        #we return the filename
        print("(RA,DEC) Regions loaded from .reg file")        
        return self.filename_regfile_RADEC
        
    def load_regfile_xyAP(self):
        print("reading (x,y) Astropy Regions from .reg file")                
        reg = filedialog.askopenfilename(filetypes=[("region files", "*.reg")],
                                         initialdir=local_dir+'/SAMOS_regions/pixels')
        print("reading (x,y) Astropy region file")
        if isinstance(reg, tuple):
            regfileName = reg[0]
        else:
            regfileName = str(reg)
        #if len(regfileName) != 0:
        
        #Then extract the clean filename to get RA and DEC of the central point
        head, tail = os.path.split(regfileName)
        self.textbox_filename_regfile_xyAP.insert(tk.END, tail)
            
        self.RRR_xyAP = Regions.read(regfileName, format='ds9')
        
        self.RRR_xyGA = self.convert_regions_xyAP2xyGA()
        #self.display_region_file()
        print("(x,y) Astropy Regions loaded from .reg file")        
        #regfile = open(regfileName, "r")
        
    """
    def display_region_file(self):
        [ap_region.add_region(self.canvas, reg) for reg in self.RRR_xyAP]
        #color in RED all the regions loaded from .reg file
        CM.CompoundMixin.set_attr_all(self.canvas,color="red")
    """    
    """
# =============================================================================
# DONE WITH THE FIELDS
# =============================================================================
    """

    def regfname_handle_focus_out(self,_):
        
        current_text = self.regfname_entry.get()
        if current_text.strip(" ") == "":
            #self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg='grey')
            self.regfname_entry.config(bg='white')
            self.regfname_entry.insert(0, "enter pattern name")


    def regfname_handle_focus_in(self,_):
        
        current_text = self.regfname_entry.get()
        if current_text == "enter pattern name":
            
            self.regfname_entry.delete(0, tk.END)
            self.regfname_entry.config(fg="black")


    def write_slits(self):
        # when writing a new DMD pattern, put it in the designated directory
        # don't want to clutter working dir.
        # At SOAR, this should be cleared out every night for the next observer
        created_patterns_path = path / Path("Astropy Regions/")
        pattern_name = self.regfname_entry.get()
        #check if pattern name has been proposed
        if (pattern_name.strip(" ") == "") or (pattern_name == "enter pattern name"):
            # if there is no pattern name provided, use a default based on 
            # number of patterns already present
            num_patterns_thus_far = len(os.listdir(created_patterns_path))
            pattern_name = "pattern_reg{}.reg".format(num_patterns_thus_far)
            
        pattern_path = created_patterns_path / Path(pattern_name)
        
        #create astropy regions and save them after checking that there is something to save...
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas,'rectangle')
        """
        slits = CM.CompoundMixin.get_objects_by_kind(self.canvas,'box')
        
        
        list_slits = list(slits)
        if len(list_slits) != 0:
            RRR=Regions([g2r(list_slits[0])])
            for i in range(1,len(list_slits)):
                RRR.append(g2r(list_slits[i]))
        RRR.write(str(pattern_path)+'.reg', overwrite=True)
        print("\nSlits written to region file\n")


    
    
    def push_slits(self):
        # push selected slits to DMD pattern
        #Export all Ginga objects to Astropy region
        #1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        #counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
     
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()
                
             
            if ((ccd_x0 == ccd_x1) and (ccd_y0 == ccd_y1)):
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.round(x1)), int(np.round(y1))
                self.slit_shape[x1,y1]=0
            elif  self.vslit.get() != 0 and obj.kind == 'point':
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            else:
                print("generic aperture")
                """
                x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
                x1,y1 = int(np.floor(x1)), int(np.floor(y1))
                x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
                x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
                
                #dmd_corners[:][1] = corners[:][1]+500
                ####   
                #x1 = round(dmd_corners[0][0])
                #y1 = round(dmd_corners[0][1])+400
                #x2 = round(dmd_corners[2][0])
                #y2 = round(dmd_corners[2][1])+400
                """      
                #3 load the slit pattern  
                data_box=self.AstroImage.cutout_shape(obj)
                good_box = data_box.nonzero()
                good_box_x = good_box[1]
                good_box_y = good_box[0]
                print(len(good_box[0]),len(good_box[1]))
                """ paint black the vertical columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_x):  #scanning multiple rows means each steps moves up along the y axis
                    iy = np.where(good_box_x == i) #the indices of the y values pertinent to that x 
                    iymin = min(iy[0])   #the smallest y index 
                    iymax = max(iy[0])   #last largest y index
                    cx0 = ccd_x0 + i     #so for this x position
                    cy0 = ccd_y0 + good_box_y[iymin] # we have these CCD columns limits, counted on the x axis
                    cy1 = ccd_y0 + good_box_y[iymax]
                    x1,y1 = convert.CCD2DMD(cx0,cy0)    #get the lower value of the column at the x position, 
                    x1,y1 = int(np.round(x1)), int(np.round(y1))  
                    x2,y2 = convert.CCD2DMD(cx0,cy1)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y2+1] = 1                    
#                    self.slit_shape[y1:y2+1,x1:x2+1] = 0
                """ paint black the horizontal columns, avoids rounding error in the pixel->dmd sub-int conversion"""
                for i in np.unique(good_box_y):  #scanning multiple rows means each steps moves up along the y axis
                    ix = np.where(good_box_y == i) #the indices of the y values pertinent to that x 
                    ixmin = min(ix[0])   #the smallest y index 
                    ixmax = max(ix[0])   #last largest y index
                    cy0 = ccd_y0 + i     #so for this x position
                    cx0 = ccd_x0 + good_box_x[ixmin] # we have these CCD columns limits, counted on the x axis
                    cx1 = ccd_x0 + good_box_x[ixmax]
                    x1,y1 = convert.CCD2DMD(cx0,cy0)    #get the lower value of the column at the x position, 
                    x1,y1 = int(np.round(x1)), int(np.round(y1))  
                    x2,y2 = convert.CCD2DMD(cx1,cy0)    # and the higher
                    x2,y2 = int(np.round(x2)), int(np.round(y2))
                    print(x1,x2,y1,y2)
                    self.slit_shape[x1-2:x2+1,y1-2:y2+1] = 0
                    self.slit_shape[x1-2:x1,y1-2:y1] = 1                    
                """
                for i in range(len(good_box[0])):
                x = ccd_x0 + good_box[i]
                y = ccd_y0 + good_box[i]
                x1,y1 = convert.CCD2DMD(x,y)
                self.slit_shape[x1,y1]=0
                """
       #     self.slit_shape[x1:x2,y1:y2]=0
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        DMD.apply_shape(self.slit_shape)  
        #DMD.apply_invert()   
       
        print("check")
            
    """
    def push_slits(self):
        # push selected slits to DMD pattern
        #Export all Ginga objects to Astropy region
        #1. list of ginga objects
        objects = CM.CompoundMixin.get_objects(self.canvas)
        #counter = 0
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for obj in objects:
            ccd_x0,ccd_y0,ccd_x1,ccd_y1 = obj.get_llur()
    
            x1,y1 = convert.CCD2DMD(ccd_x0,ccd_y0)
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(ccd_x1,ccd_y1)
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            #dmd_corners[:][1] = corners[:][1]+500
            ####   
            #x1 = round(dmd_corners[0][0])
            #y1 = round(dmd_corners[0][1])+400
            #x2 = round(dmd_corners[2][0])
            #y2 = round(dmd_corners[2][1])+400
        #3 load the slit pattern   
            self.slit_shape[x1:x2,y1:y2]=0
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))

#        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        DMD.apply_shape(self.slit_shape)  
        #DMD.apply_invert()   
       
        print("check")
    
 
    def get_IP(self,device='DMD'): 
        v=pd.read_csv("SAMOS_system_dev/IP_addresses_default.csv",header=None)
        if device == 'DMD':
            return(v[2][1])    

        IPs = Config.load_IP_user(self)
        #print(IPs)
    """    
# =============================================================================
#     def open_Astrometry(self):
#         btn = tk.Button(master,
#              text ="Click to open a new window",
#              command = openNewWindow)
#         btn.pack(pady = 10)ƒ
#         return self.Astrometry(master)
# ============================================================================= 

    def set_filter(self):
        print(self.FW1_filter.get())
        print('moving to filter:',self.FW1_filter.get()) 
#        self.Current_Filter.set(self.FW1_filter.get())
        filter = self.FW1_filter.get()
        print(filter)
        t = PCM.move_filter_wheel(filter)
        #self.Echo_String.set(t)
        print(t)
 
        self.Label_Current_Filter.delete("1.0","end")
        self.Label_Current_Filter.insert(tk.END,self.FW1_filter.get())
        
        self.extra_header_params+=1
        entry_string = param_entry_format.format(self.extra_header_params,'String','FILTER',
                                                 filter,'Selected filter')
        self.header_entry_string+=entry_string
        
    def set_grating(self):
        print(self.Grating_names,self.Grating_Optioned.get())
        i_selected = self.Grating_names.index(self.Grating_Optioned.get())
        print(i_selected) 
#        Grating_Position_Optioned 
        GR_pos = self.Grating_positions[i_selected]
        print(GR_pos)
 #       print('moving to grating',Grating_Position_Optioned) 
#        self.Current_Filter.set(self.FW1_filter.get())
#        grating = str(Grating_Position_Optioned)
#        print(grating)
#        t = PCM.move_grism_rails(grating)
#        GR_pos = self.selected_GR_pos.get()
#        print(type(GR_pos),type(str(GR_pos)),type("GR_B1")) 
        t = PCM.move_grism_rails(GR_pos)
#        self.Echo_String.set(t)
        print(t)
        #self.Label_Current_Filter.insert(tk.END,"",#self.FW1_Filter)
        self.Label_Current_Grating.delete("1.0","end")
        self.Label_Current_Grating.insert(tk.END,self.Grating_Optioned.get())
       
        
        self.extra_header_params+=1
        entry_string = param_entry_format.format(self.extra_header_params,'String','GRISM',
                                                  i_selected,'Grism position')
        self.header_entry_string+=entry_string
        
        print(entry_string)
        
    def get_widget(self):
        return self.root

    def set_drawparams(self, evt):
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  #'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)

    def save_canvas(self):
        regs = ap_region.export_regions_canvas(self.canvas, logger=self.logger)
        #self.canvas.save_all_objects()

    def clear_canvas(self):
        #CM.CompoundMixin.delete_all_objects(self.canvas)#,redraw=True)
        self.canvas.delete_all_objects(redraw=True)

#ConvertSIlly courtesy of C. Loomis
    def convertSIlly(self,fname, outname=None):
        FITSblock = 2880

    # If no output file given, just prepend "fixed"
        if outname is None:
            fname = pathlib.Path(fname)
            dd = fname.parent
            outname = pathlib.Path(fname.parent, 'fixed'+fname.name)
    
        with open(fname, "rb") as in_f:
            buf = in_f.read()

    # Two fixes:
    # Header cards:
        buf = buf.replace(b'SIMPLE  =                    F', b'SIMPLE  =                    T')
        buf = buf.replace(b'BITPIX  =                  -16', b'BITPIX  =                   16')
        buf = buf.replace(b"INSTRUME= Spectral Instruments, Inc. 850-406 camera  ", b"INSTRUME= 'Spectral Instruments, Inc. 850-406 camera'")
    
    # Pad to full FITS block:
        blocks = len(buf) / FITSblock
        pad = round((math.ceil(blocks) - blocks) * FITSblock)
        buf = buf + (b'\0' * pad)
    
        with open(outname, "wb+") as out_f:
            out_f.write(buf)

# =============================================================================
# # Expose_light
# 
# =============================================================================
    def expose_light(self):
        self.image_type = "science"
        ExpTime_ms = float(self.Light_ExpT.get())*1000
        params = {'Exposure Time':ExpTime_ms,'CCD Temperature':2300, 'Trigger Mode': 4, 'NofFrames': 1}
        self.expose(params)
#        self.combine_files()
        self.handle_light()
        print("science file created")

# =============================================================================
# # Expose_bias
# 
# =============================================================================
    def expose_bias(self):
        self.image_type = "bias"
        ExpTime_ms = float(self.Bias_ExpT.get())*1000
        params = {'Exposure Time':ExpTime_ms,'CCD Temperature':2300, 'Trigger Mode': 5, 'NofFrames': int(self.Bias_NofFrames.get())}
        #cleanup the directory to remove setimage_ files that may be refreshed
        self.cleanup_files()
        self.expose(params)
        self.combine_files()
        print("Superbias file created")
        
                       
# =============================================================================
# # Expose_dark
# 
# =============================================================================
    def expose_dark(self):
        self.image_type = "dark"
        ExpTime_ms = float(self.Dark_ExpT.get())*1000
        params = {'Exposure Time':ExpTime_ms,'CCD Temperature':2300, 'Trigger Mode': 5, 'NofFrames': int(self.Dark_NofFrames.get())}
        self.expose(params)
        self.combine_files()
        self.handle_dark()
        print("Superdark file created")


# =============================================================================
# # Expose_flat
# 
# =============================================================================
    def expose_flat(self):
        self.image_type = "flat"
        ExpTime_ms = float(self.Flat_ExpT.get())*1000
        params = {'Exposure Time':ExpTime_ms,'CCD Temperature':2300, 'Trigger Mode': 4, 'NofFrames': int(self.Flat_NofFrames.get())}
        self.expose(params)
        self.combine_files()
        self.handle_flat()
        print("Superflat file created")
        #Camera= CCD(dict_params=params)

# =============================================================================
# # Handle files: sets or single?
# 
# =============================================================================
    def combine_files(self):
        #this procedure runs after the CCD.expose()
        #to handle the decision of saving all single files or just the averages
        file_names = local_dir+"/fits_image/setimage_*.fit"
        files = glob.glob(file_names)
        superfile_cube = np.zeros((1032,1056,len(files)))   #note y,x,z
        for i in range(len(files)):
            print(files[i])
            with fits.open(files[i]) as hdu:
                superfile_cube[:,:,i] = hdu[0].data
                if self.var_Bias_saveall.get() == 1 or \
                   self.var_Dark_saveall.get() == 1 or \
                   self.var_Flat_saveall.get() == 1:
                   #save every single frame
                    os.rename(files[i],local_dir+"/fits_image/"+self.image_type+"_"+str(i)+".fits")
                else: 
                    os.remove(files[i])
        superfile = superfile_cube.mean(axis=2)        
        superfile_header = hdu[0].header
        fits.writeto(local_dir+"/fits_image/super"+self.image_type+".fits",superfile,superfile_header,overwrite=True)
            
    def cleanup_files(self):
        file_names = local_dir+"/fits_image/"+self.image_type+"_*.fits"
        files = glob.glob(file_names)
        for i in range(len(files)):
             os.remove(files[i])
        
    def handle_dark(self):
        dark_file = local_dir+"/fits_image/superdark.fits"
        bias_file = local_dir+"/fits_image/superbias.fits"
        hdu_dark = fits.open(dark_file)
        dark = hdu_dark[0].data
        hdu_bias = fits.open(bias_file)
        bias = hdu_bias[0].data
        
        if self.subtract_Bias.get() == 1:
            dark_bias = dark-bias
        else:    
            dark_bias = dark
        
        hdr = hdu_dark[0].header
        exptime = hdr['PARAM2']
        dark_sec = dark_bias / exptime
        hdr_out = hdr
        hdr_out['PARAM2']=1
        fits.writeto(local_dir+"/fits_image/superdark_s.fits",dark_sec,hdr_out,overwrite=True)

    def handle_flat(self):
        flat_file = local_dir+"/fits_image/superflat.fits"
        dark_s_file = local_dir+"/fits_image/superdark_s.fits"
        bias_file = local_dir+"/fits_image/superbias.fits"
        hdu_flat = fits.open(flat_file)
        flat = hdu_flat[0].data
        hdu_bias = fits.open(bias_file)
        bias = hdu_bias[0].data
        if self.subtract_Bias.get() == 1:
            flat_bias = flat-bias
        else:    
            flat_bias = flat

        hdr = hdu_flat[0].header
        exptime = hdr['PARAM2']
        hdu_dark_s = fits.open(dark_s_file)
        dark_s = hdu_dark_s[0].data
        dark = dark_s * exptime
        if self.subtract_Dark.get() == 1:
            flat_dark = flat-dark
            flat_dark = flat - dark
        else:    
            flat_dark = flat
        flat_norm = flat_dark / np.median(flat_dark)
        fits.writeto(local_dir+"/fits_image/superflat_norm.fits",flat_norm,hdr,overwrite=True)
        
    def handle_light(self):
        light_file = local_dir+"/fits_image/newimage.fit"
        flat_file = local_dir+"/fits_image/superflat_norm.fits"
        dark_s_file = local_dir+"/fits_image/superdark_s.fits"
        bias_file = local_dir+"/fits_image/superbias.fits"
        
        hdu_light = fits.open(light_file)
        light = hdu_light[0].data
        
        hdu_bias = fits.open(bias_file)
        bias = hdu_bias[0].data
        
        hdu_dark_s = fits.open(dark_s_file)
        dark_s = hdu_dark_s[0].data
        
        hdu_flat = fits.open(flat_file)
        flat = hdu_flat[0].data

        hdr = hdu_light[0].header
        exptime = hdr['PARAM2']

        if self.subtract_Bias.get() == 1:
            light_bias = light-bias
        else:    
            light_bias = light
            
        if self.subtract_Dark.get() == 1:
            light_dark = light_bias - dark_s * exptime
        else:    
            light_dark = light_bias

        if self.subtract_Flat.get() == 1:
            light_dark_bias = np.divide(light_dark, flat) 
        else:    
            light_dark_bias = light_dark
        fits_image = local_dir+"/fits_image/newimage_ff.fits"    
        fits.writeto(fits_image,light_dark_bias,hdr,overwrite=True)
        self.Display(fits_image)
       

# =============================================================================
# # Expose
# 
# =============================================================================

    def expose(self,params):
        
        #Prepare the exposure parameers
        #ExpTime_ms = float(self.ExpTime.get())*1000
        #params = {'Exposure Time':ExpTime_ms,'CCD Temperature':2300, 'Trigger Mode': 4}
        
        #Camera= CCD(dict_params=params)
        Camera = Class_Camera(dict_params=params)
        
        self.this_param_file = open("{}/Parameters.txt".format(os.getcwd()),"w")
        
        self.this_param_file.write(self.header_entry_string)
        self.this_param_file.close()
        #Expose
        IP = self.PAR.IP_dict['IP_CCD']
        [host,port] = IP.split(":")
#        PCM.initialize(address=host, port=int(port))
        Camera.expose(host, port=int(port))
        
        #Fix the fit header from U16 to I16, creating a new image
        #create proper working directory
        work_dir = os.getcwd()

        ##fits_image = "/Users/robberto/Box/@Massimo/_Python/SAMOS_GUI_dev/fits_image/newimage_fixed.fit"
        #fits_image = "{}/fits_image/newimage_fixed.fit".format(work_dir)
        self.fits_image = "{}/fits_image/newimage.fit".format(work_dir)
        fits_image_converted = local_dir+"/fits_image/newimage_fixed.fit"                     
        #fits_image_converted = "{}/fits_image/newimage_fixed.fit".format(work_dir)                       
        self.convertSIlly(self.fits_image,fits_image_converted)
        
        #copy the cleaned file to newimage.fit
        shutil.copy(fits_image_converted,self.fits_image)
        
        self.Display(fits_image_converted)
        
        #To do: cancel the original image.= If the canera is active; otherwise leave it.
        #Hence, we need a general switch to activate if the camera is running.
        #Hence, we may need a general login window.
        
        #self.Display(self.fits_image)

    def Display(self,imagefile): 
#        image = load_data(fits_image_converted, logger=self.logger)

        # AstroImage object of ginga.AstroImage module
        self.AstroImage = load_data(imagefile, logger=self.logger)
      
        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)

       
        

    def load_last_file(self):
        FITSfiledir = './fits_image/'
        self.fullpath_FITSfilename = FITSfiledir + (os.listdir(FITSfiledir))[0] 
            # './fits_image/cutout_rebined_resized.fits'
        self.AstroImage = load_data(self.fullpath_FITSfilename, logger=self.logger)
        # AstroImage object of ginga.AstroImage module
        
        # passes the image to the viewer through the set_image() method
        self.fitsimage.set_image(self.AstroImage)
        self.root.title(self.fullpath_FITSfilename)


    """ 
    TEST
    Inject image from SkyMapper to create a WCS solution
    using twirl
    """
    def SkyMapper_query(self):
        from ginga.AstroImage import AstroImage
        from PIL import Image
        img = AstroImage()
        from astropy.io import fits
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, filt)       
        with fits.open(filepath.name) as hdu_in:
#            img.load_hdu(hdu_in[0])
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(1032,1056))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec

#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)

            img.load_hdu(self.hdu_res)       

            self.fitsimage.set_image(img)
        
        #self.root.title(filepath)
    
    def SkyMapper_save(self):
        from astropy.io import fits 
        work_dir = os.getcwd()
        self.fits_image_ff = "{}/fits_image/newimage_ff.fits".format(work_dir)
        fits.writeto(self.fits_image_ff,self.hdu_res.data,header=self.hdu_res.header,overwrite=True) 
        print("SAVED:  ",self.fits_image_ff)
    
    def twirl_Astrometry(self):
        from astropy.io import fits
        import numpy as np
        from astropy import units as u
        from astropy.coordinates import SkyCoord
        from matplotlib import pyplot as plt
        import twirl
        
        self.Display(self.fits_image_ff)
        #self.load_file()   #for ging
        
        hdu=fits.open(self.fits_image_ff)[0]  #for this function to work
        
        header = hdu.header 
        data = hdu.data
        
        ra, dec = header["RA"], header["DEC"]
        center = SkyCoord(ra, dec, unit=["deg", "deg"])
        center = [center.ra.value, center.dec.value]
        
        # image shape and pixel size in "
        shape = data.shape
        pixel = 0.18 * u.arcsec
        fov = np.max(shape)*pixel.to(u.deg).value
        
        # Let's find some stars and display the image
        
        self.canvas.delete_all_objects(redraw=True)
        
        stars = twirl.find_peaks(data)[0:25]
        
#        plt.figure(figsize=(8,8))
        med = np.median(data)
#        plt.imshow(data, cmap="Greys_r", vmax=np.std(data)*5 + med, vmin=med)
#        plt.plot(*stars.T, "o", fillstyle="none", c="w", ms=12)

        from regions import PixCoord, CirclePixelRegion
#        xs=stars[0,0]
#        ys=stars[0,1]
#        center_pix = PixCoord(x=xs, y=ys)
        radius_pix = 42
#        region = CirclePixelRegion(center_pix, radius_pix)
        
        regions = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                for x, y in stars]  #[(1, 2), (3, 4)]]
        regs = Regions(regions)
        for reg in regs:
            obj = r2g(reg)
        #add_region(self.canvas, obj, tag="twirlstars", draw=True)
            self.canvas.add(obj)
        
        # we can now compute the WCS
        gaias = twirl.gaia_radecs(center, fov, limit=25)
        self.wcs = twirl._compute_wcs(stars, gaias)
        
        
        # Lets check the WCS solution 
        
#        plt.figure(figsize=(8,8))
        radius_pix = 25
        gaia_pixel = np.array(SkyCoord(gaias, unit="deg").to_pixel(self.wcs)).T
        regions_gaia = [CirclePixelRegion(center=PixCoord(x, y), radius=radius_pix)
                for x, y in gaia_pixel]  #[(1, 2), (3, 4)]]
        regs_gaia = Regions(regions_gaia)
        for reg in regs_gaia:
            obj = r2g(reg)
            obj.color="red"
        #add_region(self.canvas, obj, tag="twirlstars", redraw=True)
            self.canvas.add(obj)
        
        print(self.wcs)
        hdu_wcs = self.wcs.to_fits()
        self.wcs_filename = "./SAMOS_Astrometry_dev/" + "WCS_"+ra+"_"+dec+".fits"
        hdu_wcs[0].writeto(self.wcs_filename,overwrite=True)
        #
        #> to read:
        #hdu = fits_open(self.wcs_filename)
        #hdr = hdu[0].header
        #import astropy.wcs as apwcs
        #wcs = apwcs.WCS(hdu[('sci',1)].header)
        #hdu.close()
        
 
        
        

        
# =============================================================================
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
# =============================================================================
    def check_for_file_existence(self):
        FITSfiledir = './fits_image/'
        while len(os.listdir(FITSfiledir)) == 0:
            print('nothing here')
            time.sleep(1)
        time.sleep(1) #one second to complete data transfer
        self.load_last_file()
        print('and move fits file')
        

# =============================================================================
#         image = load_data(self.fullpath_FITSfilename, logger=self.logger)
#         self.fitsimage.set_image(image)
#         self.root.title(self.fullpath_FITSfilename)
# 
# =============================================================================



    def load_file(self):
        self.AstroImage = load_data(self.fullpath_FITSfilename, logger=self.logger)
        self.canvas.set_image(self.AstroImage)
        self.root.title(self.fullpath_FITSfilename)

    def open_file(self):
        filename = filedialog.askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        self.load_file(filename)

    def run_code(self):
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
        """      
        #check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        #we can find out what are the "points" objects
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        print(list(points))
        
        #we can remove what we don't like, e.g. points
        points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        list_point=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_point)
        self.canvas.objects   #check that the points are gone
           
        #we can remove both points and boxes
        points = CM.CompoundMixin.get_objects_by_kinds(self.canvas,['point','circle',
                                                                    'rectangle', 'polygon', 
                                                                    'triangle', 'righttriangle', 
                                                                    'ellipse', 'square'])
        list_points=list(points)
        CM.CompoundMixin.delete_objects(self.canvas,list_points)
        self.canvas.objects   #check that the points are gone
        """
        #drawing an object can be done rather easily
        #first take an object fromt the list and change something
        objects=CM.CompoundMixin.get_objects(self.canvas)
        o0=objects[0]
        o0.y1=40
        o0.height=100
        o0.width=70
        o0.color='lightblue'
        CM.CompoundMixin.draw(self.canvas,self.canvas.viewer)
        
        END OF THE COMPOUNDMIXING EXCERCISE
        #=====================================        

        # region = 'fk5;circle(290.96388,14.019167,843.31194")'
        # astropy_region = pyregion.parse(region)
        #astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])
        #print(astropy_region)
         
        #List all regions that we have created
        #n_objects = len(self.canvas.objects)
        #for i_obj in range(n_objects):
        #   astropy_region=ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj])
        #   print(astropy_region) 
           
        #create a list of astropy regions, so we export a .reg file
        #first put the initial region in square brackets, argument of Regions to initiate the list
        RRR=Regions([ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[0])])
        #then append to the list adding all other regions
        for i_obj in range(1,len(self.canvas.objects)):
           RRR.append(ap_region.ginga_canvas_object_to_astropy_region(self.canvas.objects[i_obj]))
           print(RRR) 
 
        #write the regions to file
        #this does not seem to work...
        RRR.write('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9',overwrite=True)
       
        #reading back the ds9 regions in ginga
        pyregions = Regions.read('/Users/SAMOS_dev/Desktop/new_regions.reg', format='ds9')
        n_regions = len(pyregions)
        for i in range(n_regions):
            pyregion = pyregions[i]
            pyregion.width=7
            pyregion.width=3
            ap_region.add_region(self.canvas,pyregion)

        print("yay!")            
        
        #Export all Ginga objects to Astropy region
        #1. list of ginga objects
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
        
        #2, Extract the slits and convert pixel->DMD values
        
        DMD.initialize(address=self.PAR.IP_dict['IP_DMD'][0:-5], port=int(self.PAR.IP_dict['IP_DMD'][-4:]))
        DMD._open()
        
        #create initial DMD slit mask
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        
        regions = Regions.read('my_regions.reg')


        for i in range(len(regions)):
            reg = regions[i]
            corners = reg.corners
            #convert CCD corners to DMD corners here
            #TBD
            #dmd_corners=[] 
            #for j in range(len(corners)):
            x1,y1 = convert.CCD2DMD(corners[0][0], corners[0][1])
            x1,y1 = int(np.floor(x1)), int(np.floor(y1))
            x2,y2 = convert.CCD2DMD(corners[2][0], corners[2][1])
            x2,y2 = int(np.ceil(x2)), int(np.ceil(y2))
            #dmd_corners[:][1] = corners[:][1]+500
            ####   
            #x1 = round(dmd_corners[0][0])
            #y1 = round(dmd_corners[0][1])+400
            #x2 = round(dmd_corners[2][0])
            #y2 = round(dmd_corners[2][1])+400
        #3 load the slit pattern   
            self.slit_shape[x1:x2,y1:y2]=0
        DMD.apply_shape(self.slit_shape)  
        #DMD.apply_invert()   

        
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
            self.ra_center, self.dec_center = image.pixtoradec(528, 516,
                                               format='str', coords='fits')

        except Exception as e:
            #self.logger.warning("Bad coordinate conversion: %s" % (
            #    str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'
        coords_text = "RA: %s  DEC: %s \n"%(ra_txt, dec_txt)
#        dmd_text = "DMD_X: %.2f  DMD_Y: %.2f \n"%(dmd_x, dmd_y)
        dmd_text = "DMD_X: %i  DMD_Y: %i \n"%(np.round(dmd_x), round(dmd_y))
        text = "X: %.2f  Y: %.2f  Value: %s" % (
            fits_x, fits_y, value)
        
        text = coords_text + dmd_text + text
        self.readout.config(text=text)

    def quit(self,root):
        root.destroy()
        return True

######
    def set_mode_cb(self):
        mode = self.setChecked.get()
#        self.logger.info("canvas mode changed (%s) %s" % (mode))
        self.logger.info("canvas mode changed (%s)" % (mode))
        self.canvas.set_draw_mode(mode)

    def draw_cb(self, canvas, tag):
        obj = canvas.get_object_by_tag(tag)
        obj.add_callback('pick-down', self.pick_cb, 'down')
        obj.add_callback('pick-up', self.pick_cb, 'up')
        #obj.add_callback('pick-move', self.pick_cb, 'move')
        #obj.add_callback('pick-hover', self.pick_cb, 'hover')
        #obj.add_callback('pick-enter', self.pick_cb, 'enter')
        #obj.add_callback('pick-leave', self.pick_cb, 'leave')
        obj.add_callback('pick-key', self.pick_cb, 'key')
        obj.pickable = True
        obj.add_callback('edited', self.edit_cb)
        #obj.add_callback('pick-key',self.delete_obj_cb, 'key')
        kind = self.wdrawtype.get()
        print("kind: ", kind)
        if self.vslit.get() != 0 and kind == 'point':
            true_kind='Slit'
            print("It is a slit")
#            print("Handle the rectangle as a slit")
            if self.SlitTabView is None:
                self.SlitTabView = STView() 
                
            self.slit_handler(obj)
        

        
        
    def slit_handler(self, point):
        print('ready to associate a slit to ')
        print(point)
        img_data = self.AstroImage.get_data()
        #create box
        x_c = point.points[0][0]-1#really needed?
        y_c = point.points[0][1]-1
        #create area to search, using astropy instead of ginga (still unclear how you do it with ginga)
        r = RectanglePixelRegion(center=PixCoord(x=round(x_c), y=round(y_c)),
                                        width=40, height=40,
                                        angle = 0*u.deg)
        # and we convert it to ginga.
        #Note: r as an Astropy region is a RECTANGLE
        #      obj is a Ginga region type BOX
        obj = r2g(r)
        #this retuns a Box object 
        self.canvas.add(obj)
        data_box = self.AstroImage.cutout_shape(obj)
        
        #we can now remove the "pointer" object
        CM.CompoundMixin.delete_object(self.canvas,obj)

    #      obj = self.canvas.get_draw_class('rectangle')
  #      obj(x1=x_c-20,y1=y_c-20,x2=x_c+20,y2=y_c+20,
  #                      width=100,
  #                      height=30,
  #                      angle = 0*u.deg)
  #      data_box = self.img.cutout_shape(obj)
        peaks = iq.find_bright_peaks(data_box)
        print(peaks[:20])  # subarea coordinates
        x1=obj.x-obj.xradius
        y1=obj.y-obj.yradius
        px,py=round(peaks[0][0]+x1),round(peaks[0][1]+y1)
        print('peak found at: ', px,py)   #image coordinates
        print('with counts: ',img_data[px,py]) #actual counts
        # evaluate peaks to get FWHM, center of each peak, etc.
        objs = iq.evaluate_peaks(peaks, data_box)       
        #from ginga.readthedocs.io
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
        print('full evaluation: ',objs)
        print('fitted centroid: ', objs[0].objx,objs[0].objy) 
        print('FWHM: ', objs[0].fwhm) 
        print('peak value: ',objs[0].brightness)
        print('sky level: ',objs[0].skylevel)
        print('median of area: ',objs[0].background)
        print("the four vertex of the rectangle are, in pixel coord:")
        x1, y1, x2, y2 = obj.get_llur()
        print("the RADEC of the fitted centroid are, in decimal degrees:")
        print(self.AstroImage.pixtoradec(objs[0].objx,objs[0].objy))
        slit_box = self.canvas.get_draw_class('rectangle')
        slit_w=3
#        slit_l=9
#        self.canvas.add(slit_box(x1=objs[0].objx+x1-slit_w,y1=objs[0].objy+y1-slit_h,x2=objs[0].objx+x1+slit_w,y2=objs[0].objy+y1+slit_h,
#                        width=100,
#                        height=30,
#                        angle = 0*u.deg))
        
        slit_box = self.canvas.get_draw_class('box')
        xradius = self.slit_l.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        yradius = self.slit_w.get() * 0.5 * self.PAR.scale_DMD2PIXEL
        obj.fill = 1
        self.canvas.add(slit_box(x=objs[0].objx+x1, 
                                 y=objs[0].objy+y1, 
                                 xradius = xradius,
                                 yradius = yradius,
                                 color = 'red',
                                 alpha = 0.8,
                                 fill = True,
                                 angle=5*u.deg))

        self.SlitTabView.add_slit_obj(r, self.fitsimage)
        print("slit added")

        #self.cleanup_kind('point')
        #ssself.cleanup_kind('box')


    def pick_cb(self, obj, canvas, event, pt, ptype):
        
        print("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        self.logger.info("pick event '%s' with obj %s at (%.2f, %.2f)" % (
            ptype, obj.kind, pt[0], pt[1]))
        
        try:
            if event.key=='d':
                canvas.delete_object(obj)
        except:
            pass
        return True
    
    def edit_cb(self, obj):
        self.logger.info("object %s has been edited" % (obj.kind))

        return True

    def cleanup_kind(self,kind):
        #check that we have created a compostition of objects:
        CM.CompoundMixin.is_compound(self.canvas.objects)     # True

        #we can find out what are the "points" objects
        #points = CM.CompoundMixin.get_objects_by_kind(self.canvas,'point')
        found = CM.CompoundMixin.get_objects_by_kind(self.canvas,str(kind))
        list_found=list(found)
        CM.CompoundMixin.delete_objects(self.canvas,list_found)
        self.canvas.objects   #check that the points are gone

    def push_objects_to_slits(self):
        #1) print all the objects as a astropy region file
        #2) edit the file into a dmd file
        #3) load the dmd file
        print("check")





######
    def donothing(self):
        pass

######
    def show_slit_table(self):
        self.SlitTabView = STView()
        
######
    def load_Astrometry(self):
        #=> send center and list coodinates to Astrometry, and start Astrometry!
        Astrometry().receive_radec([self.ra_center,self.dec_center],[self.ra_list,self.dec_list],self.xy_list)


######
    def load_Motors_module_GUI(self):
        #calls class "Motors" in tk_class_motors_V1.py; starts the gui and initialize
        #SM_GUI()
#        Motors()        
        pass

######
    def load_DMD_module_GUI(self):
        #GUI_DMD()       
        pass

######
    def load_CCD_module_GUI(self):
        #GUI_CCD().receive_radec([self.ra_center,self.dec_center],[self.ra_list,self.dec_list],self.xy_list)       
        pass

######
    def load_SOAR_module_GUI(self):
        #SOAR()       
        pass

######
    def load_CONFIG_GUI(self):
        #print(Config.load_IP_user(self))       
        pass

######
# from https://sewpy.readthedocs.io/en/latest/
    def run_DaoFind(self):
        self.fullpath_FITSfilename
        ### here is the daophot part of the procedure
        hdu = fits.open(self.fullpath_FITSfilename, logger=self.logger)

        ### read the wcs to get radec from the pixels
        ### see https://docs.astropy.org/en/stable/api/astropy.wcs.WCS.html#astropy.wcs.WCS.pixel_to_world_values
        w = wcs.WCS(hdu[('sci',1)].header, hdu)

        data = hdu[0].data
        hdu.close()   #good practice
        
        #1d background estimate
        sigma = float(self.sigma.get())
        print(sigma)
        mean, median, std = sigma_clipped_stats(data, sigma=sigma)
        print((mean, median, std))  
        
        #2d background estimate
        # FROM https://photutils.readthedocs.io/en/stable/background.html
        sigma_clip = SigmaClip(sigma=3.)
        bkg_estimator = MedianBackground()
        bkg = Background2D(data, (50, 50), filter_size=(3, 3), sigma_clip=sigma_clip, bkg_estimator=bkg_estimator)
        median = bkg.background    

        plt.imshow(bkg.background, origin='lower', cmap='Greys_r', interpolation='nearest')
        
        
        daofind = DAOStarFinder(fwhm=3.0, threshold=3.*std)  
        sources = daofind(data - median)  
        for col in sources.colnames:  
            sources[col].info.format = '%.8g'  # for consistent table output
        print(sources)  
        
# =============================================================================
#         self.display_Daofind(sources)
# =============================================================================
#
        #### back to ginga
        self.fitsimage.set_image(self.AstroImage)
            # passes the image to the viewer through the set_image() method

#        image = load_data(self.fullpath_FITSfilename, logger=self.logger)
        viewer=self.fitsimage#.set_image(image)   #ImageViewCanvas object of ginga.tkw.ImageViewTk module
        canvas = viewer.get_private_canvas() #ImageViewCanvas object of ginga.tkw.ImageViewTk module
        canvas.delete_all_objects(redraw=True)
        canvas.show_pan_mark(True)
        x = sources['xcentroid']
        y = sources['ycentroid']
        
        ### get radec
        ### see https://docs.astropy.org/en/stable/api/astropy.wcs.WCS.html#astropy.wcs.WCS.pixel_to_world_values
        self.ra_list, self.dec_list = w.all_pix2world(x, y, 1)  # we send this to astrometry for cross-matching sources
        self.xy_list = (x,y)   # we send this to astrometry to build the new wcs
        #

        #tag = '_$pan_mark'
        radius = 10
        color='green'
#        canvas = viewer.get_private_canvas()
#        viewer.initialize_private_canvas(canvas)
#        mark = canvas.get_object_by_tag(tag)
#        mark.color = color  
        Point = canvas.get_draw_class('point')
 #       canvas.set.drawtype('cross',color='green')
#        self.canvas.redraw(whence=3)
        i=0
        for i in range(len(x)):
 #           x[0]=886
#            y[0]=938
#            canvas.add(Point(x[i]/2.-258, y[i]/2-264, radius, style='plus', color=color,                             
#            canvas.add(Point( (x[i]/2.-264)*1.01, (y[i]/2-258)*1.01, radius, style='plus', color=color,                             
#            canvas.add(Point( (x[i]/2.-264.5), (y[i]/2-258.5), radius, style='plus', color=color,                             
            canvas.add(Point( (x[i]-526)/2., (y[i]-514)/2., radius, style='plus', color=color,                             
                             coord='cartesian'),
                       redraw=True)#False)
            print(x[i], y[i],x[i]/2.-264, y[i]/2.-258)
#            print(x[i], y[i],x[i]/2.-258, y[i]/2.2-258)
        canvas.update_canvas(whence=3)
        print('done')

    def show_slits(self):
        #### back to ginga
        self.fitsimage.set_image(self.AstroImage)
            # passes the image to the viewer through the set_image() method

#        image = load_data(self.fullpath_FITSfilename, logger=self.logger)
        viewer=self.fitsimage#.set_image(image)   #ImageViewCanvas object of ginga.tkw.ImageViewTk module
        canvas = viewer.get_private_canvas() #ImageViewCanvas object of ginga.tkw.ImageViewTk module
        canvas.delete_all_objects(redraw=True)
        canvas.show_pan_mark(True)
        x = [10,110,210,310,410,510,610,710]#sources['xcentroid']
        y = [10,110,210,310,410,510,610,710]#)sources['ycentroid']
        Dx = [7,7,  7,  7,  7,  7,  7,  7]
        Dy = [3,3,  3,  3,  3,  3,  3,  3]
        #tag = '_$pan_mark'
        radius = 1
        #color='green'
#        canvas = viewer.get_private_canvas()
#        viewer.initialize_private_canvas(canvas)
#        mark = canvas.get_object_by_tag(tag)
#        mark.color = color  
        Point = canvas.get_draw_class('point')
 #       canvas.set.drawtype('cross',color='green')
#        self.canvas.redraw(whence=3)
        i=0
        for i in range(len(x)):
            x[0]=886
            y[0]=938
#            canvas.add(Point(x[i]/2.-258, y[i]/2-264, radius, style='plus', color=color,                             
#            canvas.add(Point( (x[i]/2.-264)*1.01, (y[i]/2-258)*1.01, radius, style='plus', color=color,                             
#            canvas.add(Point( (x[i]/2.-264.5), (y[i]/2-258.5), radius, style='plus', color=color,                             
            for ix in range(Dx[i]):
                for iy in range(Dy[i]):
                    xp = ((x[i] + (ix-int(Dx[i]/2)))-526)/2.
                    yp = ((y[i] + (iy-int(Dy[i]/2)))-514)/2.
#                    canvas.add(Point( (x[i]-526)/2., (y[i]-514)/2., radius, style='square', color='black',                             
                    canvas.add(Point( xp, yp, radius, style='square', color='black',                             
                             coord='cartesian'),
                       redraw=True)#False)
            print(x[i], y[i],x[i]/2.-264, y[i]/2.-258)
#            print(x[i], y[i],x[i]/2.-258, y[i]/2.2-258)
        canvas.update_canvas(whence=3)
        print('done')
    




# =============================================================================
#
# Load DMD map file
#
# =============================================================================

    def LoadMap(self):
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename = filedialog.askopenfilename(initialdir = dir_DMD+"/DMD_maps_csv",
                                        title = "Select a File",
                                        filetypes = (("Text files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*")))
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)
        

        myList = []

        with open (filename,'r') as file:
            myFile = csv.reader(file)
            for row in myFile:
                myList.append(row)
        #print(myList)         
        
        for i in range(len(myList)):
            print("Row " + str(i) + ": " + str(myList[i]))
        
        test_shape = np.ones((1080,2048)) # This is the size of the DC2K    
        for i in range(len(myList)):
            test_shape[int(myList[i][0]):int(myList[i][1]),int(myList[i][2]):int(myList[i][3])] = int(myList[i][4])
        
        DMD.apply_shape(test_shape)    

        # Create a photoimage object of the image in the path
        #Load an image in the script
        # global img
        image_map = Image.open("/Users/samos_dev/GitHub/SAMOS_GUI_Python/SAMOS_DMD_dev/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)

        print('img =', self.img)
        self.canvas.create_image(104,128,image=self.img)

        
# =============================================================================
#
# Load Slit file
#
# =============================================================================
        
    def LoadSlits(self):
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename_slits = filedialog.askopenfilename(initialdir = dir_DMD +"/DMD_maps_csv",
                                        title = "Select a File",
                                        filetypes = (("Text files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*")))
        head, tail = os.path.split(filename_slits)
        self.textbox_filename_slits.insert(tk.END, tail)

        table = pd.read_csv(filename_slits)
        xoffset = 0
        yoffset = np.full(len(table.index),int(2048/4))
        y1 = (round(table['x'])-np.floor(table['dx1'])).astype(int) + yoffset
        y2 = (round(table['x'])+np.ceil(table['dx2'])).astype(int) + yoffset
        x1 = (round(table['y'])-np.floor(table['dy1'])).astype(int) + xoffset
        x2 = (round(table['y'])+np.ceil(table['dy2'])).astype(int) + xoffset
        self.slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for i in table.index:
           self.slit_shape[x1[i]:x2[i],y1[i]:y2[i]]=0
        IP = self.PAR.IP_dict['IP_DMD']
        [host,port] = IP.split(":")
        DMD.initialize(address=host, port=int(port))
        DMD._open()
        DMD.apply_shape(self.slit_shape)
        
        # Create a photoimage object of the image in the path
        #Load the image
        # global img
        image_map = Image.open("/Users/samos_dev/GitHub/SAMOS_GUI_Python/SAMOS_DMD_dev/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)

        #Add image to the Canvas Items
        print('img =', self.img)
        self.canvas.create_image(104,128,image=self.img)


    def Save_slittable(self):
        if "slit_shape" not in dir(self):
            print("No DMD pattern has been created yet.")
            return
        file = filedialog.asksaveasfile(filetypes = [("csv file", ".csv")], 
                                        defaultextension = ".csv",
                                        initialdir=local_dir+"/SAMOS_DMD_dev/DMD_csv/slits",
                                        initialfile = self.filename_regfile_RADEC[0:-4]+".csv")
        pandas_slit_shape = pd.DataFrame(self.slit_shape)
        pandas_slit_shape.to_csv(file.name)
        
        
    
    """
    Generic File Writer
    02/21/23 mr - to be tested!
    """
    def save(file_type):
        if file_type == None:
            files = [('All Files', '*.*')] 
        elif file_type == 'py':
            files = [('Python Files', '*.py')]
        elif file_type == 'txt':
            files == ('Text Document', '*.txt')
        elif file_type == 'csv':   
            files == ('DMD grid', '*.csv')
        file = filedialog.asksaveasfile(filetypes = files, defaultextension = files)
      
        #btn = ttk.Button(self, text = 'Save', command = lambda : save())        
        

    def create_menubar(self, parent):
        parent.geometry("1280x900")
#        parent.geometry("1680x900")
        parent.title("SAMOS Main Page")
        self.PAR = SAMOS_Parameters()

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")

        ## Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame(parent.DMDPage))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame(parent.Motors))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=parent.quit)  

        """
        ## proccessing menu
        processing_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Validation", menu=processing_menu)
        processing_menu.add_command(label="validate")
        processing_menu.add_separator()
        """

        ## help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=U.about)
        help_menu.add_separator()

        return menubar


class SAMOS_Parameters():
    def __init__(self):
        
        self.Image_on = tk.PhotoImage(file=local_dir+"/Images/on.png")
        self.Image_off = tk.PhotoImage(file=local_dir+"/Images/off.png")
        
        self.dir_dict = {'dir_Motors': '/SAMOS_MOTORS_dev',
                         'dir_CCD'   : '/SAMOS_CCD_dev',
                         'dir_DMD'   : '/SAMOS_DMD_dev',
                         'dir_SOAR'  : '/SAMOS_SOAR_dev',
                         'dir_SAMI'  : '/SAMOS_SAMI_dev',
                         'dir_Astrom': '/SAMOS_Astrometry_dev',
                         'dir_system': '/SAMOS_system_dev',
                        }
        
        """ Default IP address imported for all forms"""
        ip_file_default = dir_SYSTEM + "/IP_addresses_default.csv"           
        with open(ip_file_default, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}
        self.IP_dict = {}
        self.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
        self.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
        self.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
        self.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
        self.IP_dict['IP_SAMI']=dict_from_csv['IP_SAMI']

        self.IP_status_dict = {'IP_Motors':False,
                               'IP_CCD'   :False,
                               'IP_DMD'   :False,
                               'IP_SOAR'  :False,
                               'IP_SAMI'   :False,
                              }
        """ REMOVED
        self.IP_dict =  {'IP_Motors': '128.220.146.254:8889',
                         'IP_CCD'   : '128.220.146.254:8900',
                         'IP_DMD'   : '128.220.146.254:8888',
                         'IP_SOAR'  : 'TBD',
                         'IP_SAMI'  : 'TBD',
                        } 
        """

        self.inoutvar=tk.StringVar()
        self.inoutvar.set("outside") 
        
        self.scale_DMD2PIXEL = 0.892   #mirros to pixel as per e-mail by RB  Jan 207, 2023


if __name__ == "__main__":
    app = App()
    app.mainloop()

    ## IF you find this useful >> Claps on Medium >> Stars on Github >> Subscription on youtube will help me

