#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  8 12:53:57 2023

@author: samos_dev

example of sunken buttons from https://stackoverflow.com/questions/53401582/change-buttons-relief-on-click-using-tkinter

"""

from tkinter import * 
#from tkinter.ttk import *
from PIL import Image,ImageTk
import os

cwd = os.getcwd()

# creating tkinter window
root = Tk()
  
# Adding widgets to the root window
#Label(root, text = 'GeeksforGeeks', font =(
#  'Verdana', 15)).pack(side = TOP, pady = 10)
  
# Creating a photoimage object to use image
UpArrow = Image.open(cwd+"/Green-Up-Arrow.png")
resized_image= UpArrow.resize((64,64), Image.ANTIALIAS)
UpArrow_small= ImageTk.PhotoImage(resized_image)
UpArrow.close()

LeftArrow = Image.open(cwd+"/Green-Left-Arrow.png")
resized_image= LeftArrow.resize((64,64), Image.ANTIALIAS)
LeftArrow_small= ImageTk.PhotoImage(resized_image)
LeftArrow.close()

DownArrow = Image.open(cwd+"/Green-Down-Arrow.png")
resized_image= DownArrow.resize((64,64), Image.ANTIALIAS)
DownArrow_small= ImageTk.PhotoImage(resized_image)
DownArrow.close()

RightArrow = Image.open(cwd+"/Green-Right-Arrow.png")
resized_image= RightArrow.resize((64,64), Image.ANTIALIAS)
RightArrow_small= ImageTk.PhotoImage(resized_image)
RightArrow.close()

Arrows = [UpArrow_small,LeftArrow_small,DownArrow_small,RightArrow_small]
# here, image option is used to
# set image on button
tags = ('N','E','S','W')
active = None
buttons=[]
for j,i in enumerate(tags): 
    buttons.append(Button(root, text=i, image = Arrows[j], command=lambda x=j: button_pressed(x,active)))
    buttons[-1].grid(column=0, row=j)

def button_pressed(idx,active):
    if active is not None:
        buttons[active].configure(relief='groove')
    buttons[idx].configure(relief='sunken')
    active = idx      


root.mainloop()
