#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 28 10:28:03 2022

@author: robberto
"""
from matplotlib import pyplot as plt
from PIL import Image
import numpy as np

class DMD_map():
    
    def __init__(self):
        #start creating a frame of 0's 
        self.x_size = 2048   #DMD size x
        self.y_size = 1080   #DMD size y
        self.map = np.zeros((self.x_size,self.y_size)).astype(int)  

    def SAMOS_FOV(self):
        #The FoV seen by the camera is set to 1; edges to be refined.
        self.x0_field = 484   #1024 - 1080/2 
        self.x1_field = 1564  #1024 + 1080/2 
        self.y0_field = 0
        self.y1_field = 1080
        self.map[self.x0_field:self.x1_field+1, self.y0_field:self.y1_field+1]=1
   
    def draw_box(self,x0,x1,y0,y1):
        #general method to create a box (a slit) at a certain point in the SAMOS_FOV (smaller square!)
        x0+=self.x0_field
        x1+=self.x0_field
        y0+=self.y0_field
        y1+=self.y0_field
        self.map[x0:x1+1,y0:y1+1] = 0
        
    def draw_grid(self,dx,dy,Dx,Dy):
        #general method to create a centered grid of points (dx,dx = 1,1 to set 3x3) spaced Dx,DY e.g. 100,100
        Npoints_x  = (self.x1_field - self.x0_field) // Dx 
        Npoints_y  = (self.y1_field - self.y0_field) // Dy       
        for i in range(Npoints_x+1):
            x_i = int(self.x_size/2 + Dx * (-Npoints_x/2+i)) - self.x0_field
            for j in range(Npoints_y+1):
#                print(j,Npoints_y)
                y_j = int(self.y_size/2 + Dy * (-Npoints_y/2+j)) - self.y0_field
                print(i,j,x_i,y_j)
                self.draw_box(x_i-dx,x_i+dx,y_j-dy,y_j+dy)
        
    def invert_map(self):
        #invert the map, leaving the outer area at zero
        #we need to decide what we like better for the spectroscopic channel....
       self.map[self.x0_field:self.x1_field+1, self.y0_field:self.y1_field+1] = \
                abs(self.map[self.x0_field:self.x1_field+1, self.y0_field:self.y1_field+1]-1)     
        
    def save_map(self,filename):
       #save .png file, fix the directory
       im = Image.fromarray(self.map.astype(np.uint8))
       im.save(filename) 
 
       print(self.map[30:50,940])
       plt.clf()
       plt.imshow(im, vmin=0, vmax=1)
       plt.colorbar()
       plt.savefig("/Users/robberto/Desktop/DMD_map_view.png")
       
    def load_map(self,filename):
        #to be written, if we ever need it.
        pass     
    
    
DMD = DMD_map()
DMD.SAMOS_FOV()
#DMD.draw_box(500,550,200,250)
DMD.draw_grid(5,5,100,100)
DMD.invert_map()
filename = "/Users/robberto/Desktop/DMD_map_load.png"
DMD.save_map(filename)
