#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 16 08:56:51 2021

@author: robberto
"""


#FROM https://pythonprogramming.net/python-3-tkinter-basics-tutorial/
#========================================================================

#import tkinter as tk
import tkinter as tk  #small t for Python 3
from tkinter import ttk
from PIL import Image, ImageTk

import os, sys
import csv
from pathlib import Path
import time 
from datetime import datetime

#define the local directory, absolute so it is not messed up when this is called

path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   

#load the functions
from samos.utilities import get_data_file
from samos.system.SAMOS_Functions import Class_SAMOS_Functions as SF
# =============================================================================
# Import classes
# 
# =============================================================================
from  samos.motors.Class_PCM import Class_PCM 
PCM = Class_PCM()

#at the moment the Class Camera must be called with a few parameters...
from  samos.ccd.Class_CCD import Class_Camera
params = {'Exposure Time':0,'CCD Temperature':2300,'Trigger Mode': 4}
        #Trigger Mode = 4: light
        #Trigger Mode = 5: dark
CCD = Class_Camera(dict_params=params)

#Import the DMD class
from samos.dmd.Class_DMD_dev import DigitalMicroMirrorDevice
dmd = DigitalMicroMirrorDevice()#config_id='pass') 



# =============================================================================
#Here, we are creating our class, Window, and inheriting from the Frame class. 
#Frame is a class from the tkinter module. (see Lib/tkinter/__init__)

class Config(tk.Frame):

    # Define the settings upon initialization. Here you can specify
    def __init__(self, master=None):
        
        # parameters that you want to send through the Frame class
        tk.Frame.__init__(self, master)   

        #reference to the master widget, which is the "root" tk window, since we instance
        #at the end   >app = Config(root)                 
        self.master = master

        #with that, we want to then run init_window, which doesn't yet exist
#        self.init_Config()


        path = Path(__file__).parent.absolute()
#        parent_dir = str(path.parent)      
 
        self.cwd = local_dir       
        self.parent_dir = parent_dir        
       
        
    #Creation of init_window
#    def init_Config(self):
#        print(parent_dir)

        # Keep track of the button state on/off
 #       self.Motors_is_on = True
        # Define Our Images 
        self.Image_on = tk.PhotoImage(file = get_data_file("tk.icons", "on_small.png"))
        self.Image_off = tk.PhotoImage(file = get_data_file("tk.icons", "off_small.png")) 
        
        self.dir_dict = {'dir_Motors': '/motors',
                         'dir_CCD'   : '/ccd',
                         'dir_DMD'   : '/dmd',
                         'dir_SOAR'  : '/soar',
                         'dir_SAMI'  : '/SAMOS_SAMI_dev',
                         'dir_Astrom': '/astrometry',
                         'dir_system': '/system',
                        }
        
       
        self.IP_dict =  {'IP_Motors': '128.220.146.254:8889',
                         'IP_CCD'   : '128.220.146.254:8900',
                         'IP_DMD'   : '128.220.146.254:8888',
                         'IP_SOAR'  : 'TBD',
                         'IP_SAMI'  : 'TBD',
                        } 
        
        self.IP_status_dict = {'IP_Motors':False,
                               'IP_CCD'   :False,
                               'IP_DMD'   :False,
                               'IP_SOAR'  :False,
                               'IP_SAMI'   :False,
                              }
        # changing the title of our master widget      
        master.title("SAMOS- Config Window")

        self.frame0l = tk.Frame(root,background="dark gray", width=600, height=500)
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

        Label1 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_Motors'])
        Label1.place(x=4, y=10)
        Label2 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_CCD'])
        Label2.place(x=4, y=35)
        Label3 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_DMD'])
        Label3.place(x=4, y=60)
        Label1 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_SOAR'])
        Label1.place(x=4, y=85)
        Label2 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_SAMI'])
        Label2.place(x=4, y=110)
        Label1 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_Astrom'])
        Label1.place(x=4, y=135)
        Label2 = tk.Label(self.labelframe_Servers, text = self.dir_dict['dir_system'])
        Label2.place(x=4, y=160)
        
        self.dir_Motors = tk.StringVar()
        self.dir_Motors.set(self.dir_dict['dir_Motors'])
        Entry_dir_Motors = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_Motors)
        Entry_dir_Motors.place(x=140, y=10)
        self.dir_CCD= tk.StringVar()
        self.dir_CCD.set(self.dir_dict['dir_CCD'])
        Entry2 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_CCD)
        Entry2.place(x=140, y=35)
        self.dir_DMD= tk.StringVar()
        self.dir_DMD.set(self.dir_dict['dir_DMD'])
        Entry3 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_DMD)
        Entry3.place(x=140, y=60)
        self.dir_SOAR = tk.StringVar()
        self.dir_SOAR.set(self.dir_dict['dir_SOAR'])
        Entry4 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_SOAR)
        Entry4.place(x=140, y=85)
        self.dir_SAMI = tk.StringVar()
        self.dir_SAMI.set(self.dir_dict['dir_SAMI'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_SAMI)
        Entry5.place(x=140, y=110)
        self.dir_Astrom = tk.StringVar()
        self.dir_Astrom.set(self.dir_dict['dir_Astrom'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=25, textvariable = self.dir_Astrom)
        Entry5.place(x=140, y=135)
        self.dir_system = tk.StringVar()
        self.dir_system.set(self.dir_dict['dir_system'])
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
        

        self.inoutvar=tk.StringVar()
        self.inoutvar.set("outside")
        r1 = tk.Radiobutton(self.labelframe_Servers, text='Inside', variable=self.inoutvar, value='inside', command=self.load_IP_default)
        r1.place(x=20,y=0)
        r2 = tk.Radiobutton(self.labelframe_Servers, text='Outside', variable=self.inoutvar, value='outside', command=self.load_IP_default)
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
        
        #print(self.IP_dict)
        
        self.IP_Motors = tk.StringVar()
        self.IP_Motors.set(self.IP_dict['IP_Motors'])
        Entry_IP_Motors = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_Motors)
        Entry_IP_Motors.place(x=120, y=35)
        self.IP_CCD= tk.StringVar()
        self.IP_CCD.set(self.IP_dict['IP_CCD'])
        Entry2 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_CCD)
        Entry2.place(x=120, y=60)
        self.IP_DMD= tk.StringVar()
        self.IP_DMD.set(self.IP_dict['IP_DMD'])
        Entry3 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_DMD)
        Entry3.place(x=120, y=85)
        self.IP_SOAR = tk.StringVar()
        self.IP_SOAR.set(self.IP_dict['IP_SOAR'])
        Entry4 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_SOAR)
        Entry4.place(x=120, y=110)
        self.IP_SAMI = tk.StringVar()
        self.IP_SAMI.set(self.IP_dict['IP_SAMI'])
        Entry5 = tk.Entry(self.labelframe_Servers,width=20, textvariable = self.IP_SAMI)
        Entry5.place(x=120, y=135)

#        self.python_image = ImageTk.PhotoImage(self.image)
        #self.Label(self, image=self.python_image).pack()

#        ttk.Label(self,image=self.Image_on).pack()
         # Create A Button
        self.IP_Motors_on_button = tk.Button(self.labelframe_Servers, image = self.Image_off, bd = 0, command = self.Motors_switch)
        self.IP_Motors_on_button.place(x=320,y=39) 
        self.CCD_on_button = tk.Button(self.labelframe_Servers, image = self.Image_off, bd = 0, command = self.CCD_switch)
        self.CCD_on_button.place(x=320,y=64) 
        self.DMD_on_button = tk.Button(self.labelframe_Servers, image = self.Image_off, bd = 0, command = self.DMD_switch)
        self.DMD_on_button.place(x=320,y=89) 
        self.SOAR_Tel_on_button = tk.Button(self.labelframe_Servers, image = self.Image_off, bd = 0, command = self.SOAR_switch)
        self.SOAR_Tel_on_button.place(x=320,y=113) 
        self.SOAR_SAMI_on_button = tk.Button(self.labelframe_Servers, image = self.Image_off, bd = 0, command = self.SAMI_switch)
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
        self.frame0r = tk.Frame(root,background="dark gray", width=400, height=500)
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
#  #    Exit
#         
# =============================================================================
        self.Exit_frame =  tk.Frame(self.frame0l)
        self.Exit_frame.place(x=4, y=440, anchor="nw", width=592, height=48)
        Exit_Button = tk.Button(self.Exit_frame, text ="Exit", relief="raised", command = self.client_exit, font=("Arial",24)) 
        Exit_Button.place(x=230, y=5)

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
        print("CONFIG_GUI: exiting startup()\n")
        




    def load_dir_default(self):
        dict_from_csv = {}

        with open(get_data_file("system", "dirlist_default.csv")) as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        self.dir_Motors.set(dict_from_csv['dir_Motors'])
        self.dir_CCD.set(dict_from_csv['dir_CCD'])
        self.dir_DMD.set(dict_from_csv['dir_DMD'])
        self.dir_SOAR.set(dict_from_csv['dir_SOAR'])
        self.dir_SAMI.set(dict_from_csv['dir_SAMI'])
        self.dir_Astrom.set(dict_from_csv['dir_Astrom'])
        self.dir_system.set(dict_from_csv['dir_system'])
        
        self.dir_dict['dir_Motors'] = dict_from_csv['dir_Motors']
        self.dir_dict['dir_CCD'] = dict_from_csv['dir_CCD']
        self.dir_dict['dir_DMD'] = dict_from_csv['dir_DMD']
        self.dir_dict['dir_SOAR'] = dict_from_csv['dir_SOAR']
        self.dir_dict['dir_SAMI'] = dict_from_csv['dir_SAMI']
        self.dir_dict['dir_Astrom'] = dict_from_csv['dir_Astrom']
        self.dir_dict['dir_system'] = dict_from_csv['dir_system']
        
 #       self.destroy()
 #       tk.Frame.__init__(self)   
#       self.__init__()

        return self.dir_dict
        

    def load_dir_user(self):
        dict_from_csv = {}

        with open( get_data_file("system", "dirlist_user.csv")) as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        self.dir_Motors.set(dict_from_csv['dir_Motors'])
        self.dir_CCD.set(dict_from_csv['dir_CCD'])
        self.dir_DMD.set(dict_from_csv['dir_DMD'])
        self.dir_SOAR.set(dict_from_csv['dir_SOAR'])
        self.dir_SAMI.set(dict_from_csv['dir_SAMI'])
        self.dir_Astrom.set(dict_from_csv['dir_Astrom'])
        self.dir_system.set(dict_from_csv['dir_system'])
        
        self.dir_dict['dir_Motors'] = dict_from_csv['dir_Motors']
        self.dir_dict['dir_CCD'] = dict_from_csv['dir_CCD']
        self.dir_dict['dir_DMD'] = dict_from_csv['dir_DMD']
        self.dir_dict['dir_SOAR'] = dict_from_csv['dir_SOAR']
        self.dir_dict['dir_SAMI'] = dict_from_csv['dir_SAMI']
        self.dir_dict['dir_Astrom'] = dict_from_csv['dir_Astrom']
        self.dir_dict['dir_system'] = dict_from_csv['dir_system']
        
        return self.dir_dict

    def save_dir_user(self):

        # define a dictionary with key value pairs
#        dict = {'dir_Motors' : self.dir_Motors.get(), 
#                'dir_CCD' :  self.dir_CCD.get(), 
#                'dir_DMD' :  self.dir_DMD.get(), 
#                'dir_SOAR':  self.dir_SOAR.get(), 
#                'dir_SAMI': self.dir_SAMI.get(),
#                'dir_Astrom':  self.dir_Astrom.get(), 
#                'dir_system': self.dir_system.get()}
        self.dir_dict['dir_Motors'] = self.dir_Motors.get()
        self.dir_dict['dir_CCD'] = self.dir_CCD.get()
        self.dir_dict['dir_DMD'] = self.dir_DMD.get()
        self.dir_dict['dir_SOAR'] = self.dir_SOAR.get()
        self.dir_dict['dir_SAMI'] = self.dir_SAMI.get()
        self.dir_dict['dir_Astrom'] = self.dir_Astrom.get()
        self.dir_dict['dir_system'] = self.dir_system.get()
        
        # open file for writing, "w" is writing
        w = csv.writer(open(get_data_file("system", "dirlist_user.csv"), "w"))

        # loop over dictionary keys and values
        for key, val in self.dir_dict.items():

            # write every key and value to file
            w.writerow([key, val])
           

    def load_IP_user(self):
        local_path = get_data_file("system")
        if self.inoutvar.get() == 'inside':
            ip_file = os.path.join(local_path,"IP_addresses_default_inside.csv")
        else:
            ip_file = os.path.join(local_path,"IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(local_path , "IP_addresses_default.csv")    
        os.system('cp {} {}'.format(ip_file,ip_file_default))  
        
        with open(ip_file, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        self.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
        self.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
        self.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
        self.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
        self.IP_dict['IP_SAMI']=dict_from_csv['IP_SAMI']

        self.IP_Motors.set(dict_from_csv['IP_Motors'])
        self.IP_CCD.set(dict_from_csv['IP_CCD'])
        self.IP_DMD.set(dict_from_csv['IP_DMD'])
        self.IP_SOAR.set(dict_from_csv['IP_SOAR'])
        self.IP_SAMI.set(dict_from_csv['IP_SAMI'])
        


        return self.IP_dict

    def save_IP_user(self):

        # define a dictionary with key value pairs
 #       dict = {'IP_Motors' : self.IP_Motors.get(), 'IP_CCD' :  self.IP_CCD.get(), 'IP_DMD' :  self.IP_DMD.get(), 'IP_SOAR':  self.IP_SOAR.get(), 'IP_SAMI': self.IP_SAMI.get()}


# =============================================================================
#         self.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
#         self.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
#         self.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
#         self.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
#         self.IP_dict['IP_SAMI']=dict_from_csv['IP__SOAR_SAMI']
#         
# =============================================================================
# open file for writing, "w" is writing
        local_path = get_data_file("system")
        if self.inoutvar.get() == 'inside':
            ip_file = os.path.join(local_path,"IP_addresses_default_inside.csv")
        else:
            ip_file = os.path.join(local_path,"IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(local_path, "IP_addresses_default.csv")
        os.system('cp {} {}'.format(ip_file,ip_file_default))  
        
        w = csv.writer(open(ip_file, "w"))
        print(ip_file)

        # loop over dictionary keys and values
        for key, val in self.IP_dict.items():

            # write every key and value to file
            w.writerow([key, val])            
 
        self.save_IP_status()    
        
        
        
    def load_IP_default(self):
        
        local_path = get_data_file("system")
        if self.inoutvar.get() == 'inside':
            ip_file = os.path.join(local_path,"IP_addresses_default_inside.csv")
        else:
            ip_file = os.path.join(local_path,"IP_addresses_default_outside.csv")
        ip_file_default = os.path.join(local_path, "IP_addresses_default.csv" )   
        os.system('cp {} {}'.format(ip_file,ip_file_default))  

        dict_from_csv = {}      
        with open(ip_file, mode='r') as inp:
            reader = csv.reader(inp)
            dict_from_csv = {rows[0]:rows[1] for rows in reader}

        self.IP_dict['IP_Motors']=dict_from_csv['IP_Motors']
        self.IP_dict['IP_CCD']=dict_from_csv['IP_CCD']
        self.IP_dict['IP_DMD']=dict_from_csv['IP_DMD']
        self.IP_dict['IP_SOAR']=dict_from_csv['IP_SOAR']
        self.IP_dict['IP_SAMI']=dict_from_csv['IP_SAMI']

        self.IP_Motors.set(dict_from_csv['IP_Motors'])
        self.IP_CCD.set(dict_from_csv['IP_CCD'])
        self.IP_DMD.set(dict_from_csv['IP_DMD'])
        self.IP_SOAR.set(dict_from_csv['IP_SOAR'])
        self.IP_SAMI.set(dict_from_csv['IP_SAMI']) 
        
        #if PCM.MOTORS_onoff == 1:
        self.IP_echo()
        


    def save_IP_status(self):

        w = csv.writer(open(get_data_file("system", "IP_status_dict.csv"), "w"))

        # loop over dictionary keys and values
        for key, val in self.IP_status_dict.items():

            # write every key and value to file
            w.writerow([key, val])               


    def IP_echo(self):                   
#MOTORS alive?
        print("\n Checking Motors status")
        PCM.initialize(address=self.IP_dict['IP_Motors'][0:-5], port=int(self.IP_dict['IP_Motors'][-4:]))
        answer = PCM.echo_client()
        #print("\n Motors return:>", answer,"<")
        if answer != "no connection":
            print("Motors are on")
            self.IP_Motors_on_button.config(image = self.Image_on)
            print('echo from server:')
            PCM.power_on()

        else:
            print("Motors are off\n")
            self.IP_Motors_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_Motors'] = False    
         

#CCD alive?
        print("\n Checking CCD status")
        url_name = "http://"+self.IP_dict['IP_CCD']+'/'
        answer = (CCD.get_url_as_string(url_name))[:6]   #expect <HTML>
        print("CCD returns:>", answer,"<")
        if str(answer) == '<HTML>':
            print("CCD is on")
            self.CCD_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_CCD'] = True   
        else:
            print("\nCCD is off\n")
            self.CCD_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_CCD'] = False  
            
#DMD alive?
        print("\n Checking DMD status")
        dmd.initialize(address=self.IP_dict['IP_DMD'][0:-5], port=int(self.IP_dict['IP_DMD'][-4:]))
        answer = dmd._open()
        if answer != "no DMD":
            print("\n DMD is on")
            self.DMD_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_DMD'] = True   
        else:
            print("\n DMD is off")
            self.DMD_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_DMD'] = False    


        self.save_IP_status()    
        return self.IP_dict
    
    # Define our switch functions
    def Motors_switch(self):
        # Determine is on or off
        if self.IP_status_dict['IP_Motors']:
            self.IP_Motors_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_Motors'] = False
            PCM.power_off()
        else:           
            self.IP_Motors_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_Motors'] = True
#            SF.read_IP_initial_status()
            self.save_IP_status()
            PCM.IP_host = self.IP_Motors
            PCM.power_on()
        self.save_IP_status()    
        print(self.IP_status_dict)        
    
    def CCD_switch(self):         
        # Determine is on or off
        if self.IP_status_dict['IP_CCD']:
            self.CCD_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_CCD'] = False
        else:           
            self.CCD_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_CCD'] = True        
        self.save_IP_status()    
        print(self.IP_status_dict)        
    

    def DMD_switch(self):         
        # Determine is on or off
        if self.IP_status_dict['IP_DMD']:
            self.DMD_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_DMD'] = False
        else:           
            self.DMD_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_DMD'] = True          
        self.save_IP_status()    
        print(self.IP_status_dict)        
    
    def SOAR_switch(self):         
        # Determine is on or off
        if self.IP_status_dict['IP_SOAR']:
            self.SOAR_Tel_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_SOAR'] = False
        else:           
            self.SOAR_Tel_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_SOAR']= True            
        self.save_IP_status()    
        print(self.IP_status_dict)        

    def SAMI_switch(self):         
        # Determine is on or off
        if self.IP_status_dict['IP_SAMI']:
            self.SOAR_SAMI_on_button.config(image = self.Image_off)
            self.IP_status_dict['IP_SAMI'] = False
        else:           
            self.SOAR_SAMI_on_button.config(image = self.Image_on)
            self.IP_status_dict['IP_SAMI'] = True    
        self.save_IP_status()    
        print(self.IP_status_dict)        
    

# =============================================================================
#     def return_directories(self):
#         a = self.dir_dict
#         print('returning',a)
#         return a
# 
#     def return_switch_status(self):
#         return self.IP_status_dict
# 
#     def return_IP_addresses(self):
#         return self.IP_dict
# 
# =============================================================================
    def client_exit(self):
        print("complete")
        self.master.destroy() 
       

#Root window created. 
#Here, that would be the only window, but you can later have windows within windows.
root = tk.Tk()

#size of the window
root.geometry("1000x500")   


#Then we actually create the instance.
app = Config(root)

app.startup()

#Finally, show it and begin the mainloop.
root.mainloop()

