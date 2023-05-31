#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 16 08:56:51 2021

@author: robberto

05.31.2023: removed background colors from buttons as they don't look good on windows
"""


#FROM https://pythonprogramming.net/python-3-tkinter-basics-tutorial/
#========================================================================

import tkinter as tk
# Used for styling the GUI
#from tkinter import ttk
# import filedialog module
from tkinter import filedialog

from PIL import Image,ImageTk,ImageOps

import os,sys
import shutil
#from astropy.io import ascii
import time

import numpy as np
import pandas as pd

from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute()) #  .../SAMOS_DMD_dev
parent_dir = str(path.parent)  
sys.path.append(parent_dir)

SF_path = parent_dir+"/SAMOS_system_dev"
os.sys.path.append(SF_path)




from Class_DMD_dev import DigitalMicroMirrorDevice
DMD = DigitalMicroMirrorDevice()


#Here, we are creating our class, Window, and inheriting from the Frame class. 
#Frame is a class from the tkinter module. (see Lib/tkinter/__init__)

#class GUI_DMD(tk.Tk):#tk.Toplevel):  #this is a sublclass of whatver is Toplevel
class GUI_DMD(tk.Toplevel):  #this is a sublclass of whatver is Toplevel

    #The __init__ function is called every time an object is created from a class#
    #The master parameter, defaulted None is the parent widget that will be passed 
    #to the new instance of Window when it is initialized
    def __init__(self):#, master=None):
        
 
        super().__init__()#master = master) 
        #super() recalls and includes the __init__() of the master class (tk.Topelevel), so one can use that stuff there without copying the code.
  
        #reference to the master widget, which is the tk window                 
        #self.master = master 
  
        DMD.initialize()

        # changing the title of our master widget      
        self.title("IDG - DMD module driver")
        #Creation of init_window
        self.geometry("610x407")
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
        button_Initialize =  tk.Button(self.frame_startup, text="Initialize", bd=3, command=self.dmd_initialize) # bg='#0052cc'
        button_Initialize.place(x=4,y=4)

# ==========================================================================
#       Load Basic Patterns
# =============================================================================
        button_Blackout =  tk.Button(self.frame_startup, text="Blackout", bd=3, command=self.dmd_blackout) # bg='#0052cc',
        button_Blackout.place(x=4,y=34)
        button_Whiteout =  tk.Button(self.frame_startup, text="Whiteout", bd=3, command=self.dmd_whiteout) #bg='#0052cc',
        button_Whiteout.place(x=4,y=64)
        button_Checkerboard =  tk.Button(self.frame_startup, text="Checkerboard", bd=3, command=self.dmd_checkerboard) #bg='#0052cc',
        button_Checkerboard.place(x=4,y=94)
        button_Invert =  tk.Button(self.frame_startup, text="Invert", bd=3, command=self.dmd_invert) #bg='#0052cc',
        button_Invert.place(x=4,y=124)

        button_antInvert =  tk.Button(self.frame_startup, text="AntInvert", bd=3, command=self.dmd_antinvert) #bg='#0052cc',
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
        DMD.initialize()
        DMD._open()
        image_map = Image.open(local_dir + "/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)
        self.canvas.create_image(104,128,image=self.img)
              
        
    def dmd_blackout(self):
        DMD.apply_blackout()
        # global img
        image_map = Image.open(local_dir + "/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)
        #Add image to the Canvas Items
        self.canvas.create_image(104,128,image=self.img)

    def dmd_whiteout(self):
        DMD.apply_whiteout()
        # global img
        image_map = Image.open(local_dir + "/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)
        #Add image to the Canvas Items
        self.canvas.create_image(104,128,image=self.img)

    def dmd_checkerboard(self):
        DMD.apply_checkerboard()
        # global img
        shutil.copy(local_dir + "/checkerboard.png",local_dir + "/current_dmd_state.png")
        time.sleep(1)
        image_map = Image.open(local_dir + "/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)
        #Add image to the Canvas Items
        self.canvas.create_image(104,128,image=self.img)

    def dmd_invert(self):
        DMD.apply_invert()
        image_map = Image.open(local_dir + "/current_dmd_state.png")
        image=image_map.convert("L")
        image_invert = ImageOps.invert(image)
        image_invert.save(local_dir + "/current_dmd_state.png")
        # global img
        #img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
        self.img= ImageTk.PhotoImage(image_invert)
        #Add image to the Canvas Items
        self.canvas.create_image(104,128,image=self.img)
             
#        # global img
#        img= ImageTk.PhotoImage(Image.open(local_dir + "/current_dmd_state.png"))
#        #Add image to the Canvas Items
#        self.canvas.create_image(104,128,image=img)

    def dmd_antinvert(self):
        DMD.apply_antinvert()
        image_map = Image.open(local_dir + "/current_dmd_state.png")
        self.img= ImageTk.PhotoImage(image_map)
        #Add image to the Canvas Items
        self.canvas.create_image(104,128,image=self.img)
             
    def browseFiles(self):
        filename = filedialog.askopenfilename(initialdir = local_dir+"/DMD_maps_csv",
                                          title = "Select a File",
                                          filetypes = (("Text files",
                                                        "*.csv"),
                                                       ("all files",
                                                        "*.*")))
        import subprocess
        subprocess.call(['open', '-a','TextEdit', filename])
        
        
# =============================================================================
#
# Load DMD map file
#
# =============================================================================

    def LoadMap(self):
        self.textbox_filename.delete('1.0', tk.END)
        self.textbox_filename_slits.delete('1.0', tk.END)
        filename = filedialog.askopenfilename(initialdir = local_dir+"/DMD_maps_csv",
                                        title = "Select a File",
                                        filetypes = (("Text files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*")))
        head, tail = os.path.split(filename)
        self.textbox_filename.insert(tk.END, tail)
        
        import csv
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
        image_map = Image.open(local_dir + "/current_dmd_state.png")
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
        filename_slits = filedialog.askopenfilename(initialdir = local_dir+"/DMD_maps_csv",
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
        slit_shape = np.ones((1080,2048)) # This is the size of the DC2K
        for i in table.index:
           slit_shape[x1[i]:x2[i],y1[i]:y2[i]]=0
        DMD.apply_shape(slit_shape)
        
        # Create a photoimage object of the image in the path
        #Load the image
        # global img
        #self.img = None
#        image_map = Image.open(local_dir + "/current_dmd_state.png")
#        self.img= ImageTk.PhotoImage(image_map)
#         image_map.close()
        image_map = Image.open(local_dir + "/current_dmd_state.png")        
        test = ImageTk.PhotoImage(image_map)
        label1 = tk.Label(self.canvas,image=test)
        label1.image = test
        # Position image
        label1.place(x=-100, y=0)



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
        

#Root window created. 
#Here, that would be the only window, but you can later have windows within windows.
root = GUI_DMD()

#size of the window
#root.geometry("400x330")

#Then we actually create the instance.
#app = Tk.Window(root)    

#Finally, show it and begin the mainloop.
root.mainloop()
