#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 16 08:56:51 2021

@author: robberto
"""

# Import the library tkinter
from tkinter import *
import tkinter as tk
from tkinter import messagebox  # needed for python3.x
from tkinter import filedialog as fd
from tkinter import ttk

import os
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from astropy.table import Table
from scipy import interpolate
import math as math

from SAMOS_system_dev.SAMOS_Parameters_out import SAMOS_Parameters
#import SAMOS_system_dev.utils as U

import sys
from sys import platform

class ETC_Spectral_Page(Frame):

#    def __init__(self, win):
    def __init__(self, parent, container):
        super().__init__(container)
        
        self.homedir = os.getcwd()+'/SAMOS_ETC'

        # Constructing the left/right frames
        # , width=400, height=800)
        root = self
        self.frame0l = Frame(root, background="bisque")
        self.frame0l.place(x=0, y=0, anchor="nw", width=500, height=720)
        #root.geometry("1000x720")   


        # Displaying the frame1 in row 0 and column 0
        # frame0l.geometry("400x800")
        # frame0l.grid(row=0, column=0)

        # Constructing the first frame, frame1
        # , width=400, height=800)
        self.frame0r = Frame(root, background="gray")
        # Displaying the frame1 in row 0 and column 0
        self.frame0r.place(x=501, y=0, anchor="nw", width=500, height=720)

        #######################################################################
        # Constructing the first frame, frame1
        self.frame1 = Frame(self.frame0l, bg="light gray",
                            relief=RIDGE)  # , padx=15, pady=15)
        # Displaying the frame1 in row 0 and column 0
        self.frame1.place(x=2, y=2, width=496, height=180)

        self.w = Canvas(self.frame1, width=496, height=180)
        self.w.create_rectangle(8, 5, 488, 38, outline='blue')
        # w.create_rectangle(50, 50, 100, 100, fill="red", outline = 'blue')
        self.w.pack()

        self.label_Atmosferic_Window = Label(
            self.frame1, text="Grating")
        self.label_Atmosferic_Window.place(x=10, y=10)
        #####

        # Constructing the button b1 in frame1
        # Dropdown menu options
        options = [
            "Low Red",
            "Low Blue",
            "High Red",
            "High Blue"
        ]
        # datatype of menu text
        self.bandpass = StringVar()

        # initial menu text
        self.bandpass.set(options[2])

        # Create Dropdown menu
        self.drop = OptionMenu(self.frame1, self.bandpass, *options)
        self.drop.place(x=73, y=6)

        # b1 = Button(frame1, text="Ks")

        # Displaying the button b1
        # b1.pack()

        #####
        self.w.create_rectangle(8, 38, 488, 98, outline='blue')

        ### SLIT WIDTH ###
        ##################
        self.label_SlitWidth = Label(self.frame1, text="Slit Width")
        self.label_SlitWidth.place(x=10, y=40)
#        # Dropdown menu options
        slit_options = [
             '0.17',
             '0.33',
             '0.5',
             '0.67',
             '0.88',
             '1.00',
             '1.17',
             '1.33',
             '1.5',
             '1.67',
             '1.88',
             '2.00'
        ]
#        # datatype of menu text
        self.slit_selected = StringVar()
#
#        # initial menu text
        self.slit_selected.set(slit_options[2])
#
#        # Create Dropdown menu
#        self.slit_drop = OptionMenu(self.frame1 , self.slit_selected , slit_options[2], *slit_options)
        self.slit_drop = OptionMenu(self.frame1 , self.slit_selected ,  *slit_options)
        self.slit_drop.place(x=110, y=39)
        self.label_arcsec1 = Label(self.frame1, text="arcsec")
        self.label_arcsec1.place(x=180, y=40)


# =============================================================================
#         init_SlitWidth = StringVar()
#         init_SlitWidth.set("0.7")
#         self.Entry_SlitWidth = Entry(
#             self.frame1, width=4, textvariable=init_SlitWidth)
#         self.Entry_SlitWidth.place(x=110, y=37)
#         self.label_arcsec1 = Label(self.frame1, text="arcsec")
#         self.label_arcsec1.place(x=180, y=40)
# 
# =============================================================================
        ### NR. OF EXPOSURES ###
        ########################
        self.label_NExp = Label(self.frame1, text="Nr. of Exp")
        self.label_NExp.place(x=325, y=40)
        init_Nexp = StringVar()
        init_Nexp.set("2")
        self.Entry_NofExp = Entry(self.frame1, width=4, textvariable=init_Nexp)
        self.Entry_NofExp.place(x=400, y=40)

        ### ANGULAR EXTENT ###
        ######################
        self.label_AngularExtent = Label(self.frame1, text="Seeing FWHM")
        self.label_AngularExtent.place(x=10, y=74)
        init_AngExt = StringVar()
        init_AngExt.set("0.4")
        self.Entry_AngularExtent = Entry(
            self.frame1, width=4, textvariable=init_AngExt)
        self.Entry_AngularExtent.place(x=110, y=71)
        self.label_arcsec1 = Label(self.frame1, text="arcsec")
        self.label_arcsec1.place(x=155, y=74)

#######################################################################################################################
        ### USE AOS ###
#######################################################################################################################
        self.label_GLAO = Label(self.frame1, text="GLAO?")
        self.label_GLAO.place(x=255, y=70)
        self.selected_GLAO = StringVar(value='SAM')
        modes = ['SAM', 'Natural Seeing']
        counter = 0
        for mode in modes:
            self.r_GLAO = Radiobutton(
                self.frame1,
                text=mode,
                value=mode,
                variable=self.selected_GLAO
            )
            self.r_GLAO.place(x=300+counter*60, y=69)
            counter += 1

# =============================================================================
#         ### FOWLER PAIRS ###
#         ####################
#         self.label_FowlerSampling = Label(self.frame1, text="Fowler Pairs")
#         self.label_FowlerSampling.place(x=320, y=70)
#         init_Fowler = StringVar()
#         init_Fowler.set("16")
#         self.Entry_NrFowlerPairs = Entry(
#             self.frame1, width=4, textvariable=init_Fowler)
#         self.Entry_NrFowlerPairs.place(x=400, y=67)
# 
# =============================================================================
        #####
        self.w.create_rectangle(8, 108, 488, 170, outline='blue')

# =============================================================================
#         self.selected_MagnitudeSystem = StringVar(value='Vega')
#         modes = ['AB', 'Vega']
#         counter = 0
#         for mode in modes:
#             self.r_ABORVEGA = Radiobutton(
#                 self.frame2b,
#                 text=mode,
#                 value=mode,
#                 variable=self.selected_MagnitudeSystem
#             )
#             self.r_ABORVEGA.place(x=120+counter*40, y=18)
#             counter += 1
# 
# =============================================================================
#######################################################################################################################
        ### USE FLUX OR MAGNITUDES ###
#######################################################################################################################
        self.label_FluxORmag = Label(self.frame1, text="Use Line Flux or magnitude?")
        self.label_FluxORmag.place(x=20, y=115)
        self.selected_FluxORmag = StringVar(value='Use magnitude')
        modes = ['Use Line Flux', 'Use magnitude']
        counter = 0
        for mode in modes:
            self.r_FluxORmag = Radiobutton(
                self.frame1,
                text=mode,
                value=mode,
                variable=self.selected_FluxORmag,
                command=self.hide_FluxORmag
            )
            self.r_FluxORmag.place(x=20+counter*120, y=140)
            counter += 1


#######################################################################################################################
#######################################################################################################################

        # Constructing the second frame, frame2
        # , padx=15, pady=15)
        self.frame2 = Frame(self.frame0l, bg="light gray")
        # Displaying the frame2
        self.frame2.place(x=2, y=178, width=496, height=140)

        self.w = Canvas(self.frame2, width=496, height=140)
        self. w.create_rectangle(8, 8, 488, 132, outline='blue')
        self.w.pack()

        ### LINE FLUX ###
        #################
        self.label_LineFlux = Label(self.frame2, text="Line Flux")
        self.label_LineFlux.place(x=10, y=13)
        init_LineFlux = StringVar()
        init_LineFlux.set("9.0")
        self.Entry_LineFlux = Entry(self.frame2, width=4, textvariable=init_LineFlux)
        self.Entry_LineFlux.place(x=72, y=10)
        self.label_LineFluxUnits = Label(
            self.frame2, text="x 1E-17 erg/s/cm\u00b2")
        self.label_LineFluxUnits.place(x=120, y=13)

        ### CENTRAL WAVELENGTH ###
        ##########################
        self.label_CentralWl = Label(self.frame2, text="Central Wavelength")
        self.label_CentralWl.place(x=10, y=43)
        init_CentralWl = StringVar()
        init_CentralWl.set("6563")
        self.Entry_CentralWl = Entry(
            self.frame2, width=4, textvariable=init_CentralWl)
        self.Entry_CentralWl.place(x=142, y=40)
        self.selected_LineWlUnits = StringVar(value='Angstrom')
        modes = ['Angstrom', 'micron']
        counter = 0
        for mode in modes:
            self.r_LineWlUnits = Radiobutton(
                self.frame2,
                text=mode,
                value=mode,
                variable=self.selected_LineWlUnits
            )
            self.r_LineWlUnits.place(x=200+counter*100, y=43)
            counter += 1  

        ### REDSHIFT ###
        ################
        self.label_LineRedshift = Label(self.frame2, text="Redshift")
        self.label_LineRedshift.place(x=10, y=70)
        init_LineRedshift = StringVar()
        init_LineRedshift.set("0.0")
        self.Entry_LineRedshift = Entry(
            self.frame2, width=5, textvariable=init_LineRedshift)
        self.Entry_LineRedshift.place(x=72, y=67)
        
        
       # self.Button_checkRedshiftedWl = Button(self.frame2,text="check", 
       #                                       relief=RAISED, command=self.check_RedshiftedWavelength)
       # self.Button_checkRedshiftedWl.place(x=210,y=67)

        ### REDSHIFTED WAVELENGTH ###
        ################
        self.label_RedshiftAdopted = Label(self.frame2, text="Redshit adopted")
        self.label_RedshiftAdopted.place(x=280, y=70)
        init_RedshiftAdopted = StringVar()
        RWL = float(init_LineRedshift.get() ) # 6563*(1+float(init_LineRedshift.get()))
        RWL_string = str(RWL)
        init_RedshiftAdopted.set(RWL)# "{:7.2f}".format=(RWL))
        self.Entry_RedshiftAdopted = Entry(
            self.frame2, width=5, textvariable=init_RedshiftAdopted)
        self.Entry_RedshiftAdopted.place(x=422, y=67)

        ### SOURCE WFHM ###
        ###################
        self.label_FWHM = Label(self.frame2, text="Source FWHM")
        self.label_FWHM.place(x=10, y=103)
        init_FWHM = StringVar()
        init_FWHM.set("30")
        self.Entry_FWHM = Entry(self.frame2, width=4, textvariable=init_FWHM)
        self.Entry_FWHM.place(x=102, y=100)
        self.label_FWHM = Label(self.frame2, text="km/s")
        self.label_FWHM.place(x=145, y=103)


##############################################################################################################
##############################################################################################################

        # Constructing the third frame, frame2b
        # , padx=15, pady=15)
        self.frame2b = Frame(self.frame0l, bg="light gray")
        # Displaying the frame3
        self.frame2b.place(x=2, y=312, width=496, height=120)

        self.w = Canvas(self.frame2b, width=496, height=120)
        self.w.create_rectangle(8, 8, 488, 113, outline='blue')
        self.w.pack()


#        self.w.create_rectangle(8, 8, 488, 90, outline = 'blue')
      #####
       # self.w.create_rectangle(8, 128, 488, 260, outline = 'blue')

        ### MAGNITUDE ###
        ######################
        self.label_Magnitude = Label(self.frame2b, text="Magnitude")
        self.label_Magnitude.place(x=10, y=18)
        init_SourceMagnitude = StringVar()
        init_SourceMagnitude.set("18.6")
        self.Entry_Magnitude = Entry(self.frame2b, width=5, textvariable=init_SourceMagnitude)
        self.Entry_Magnitude.place(x=78, y=15)
        self.selected_MagnitudeSystem = StringVar(value='Vega')
        modes = ['AB', 'Vega']
        counter = 0
        for mode in modes:
            self.r_ABORVEGA = Radiobutton(
                self.frame2b,
                text=mode,
                value=mode,
                variable=self.selected_MagnitudeSystem,
#                command = self.hide_Vegamag
                command = self.shift_ABorVegamag
            )
            self.r_ABORVEGA.place(x=120+counter*40, y=18)
            counter += 1

      
        # Dropdown menu options
        VegaMag_options = [
            "U",
            "B",
            "V",
            "R",
            "I",
            "Y",
            "J",
            "H",
            "Ks",
            "K"
        ]
        # datatype of menu text
        self.Vega_band = StringVar()
        # initial menu text
        self.Vega_band.set(VegaMag_options[2])        
        # Create Dropdown menu
        self.menu_Vega_band = OptionMenu(self.frame2b, self.Vega_band, *VegaMag_options)
        self.menu_Vega_band.place(x=220, y=18)
       
        # Dropdown menu options
        ABMag_options = [
            "u_SDSS",
            "g_SDSS",
            "r_SDSS",
            "i_SDSS",
            "z_SDSS",
            "Y_VISTA",
            "J_VISTA",
            "H_VISTA",
            "K_VISTA"
        ]
        # datatype of menu text
        self.AB_band = StringVar()
        # initial menu text
        self.AB_band.set(ABMag_options[2])        
        # Create Dropdown menu
        self.menu_AB_band = OptionMenu(self.frame2b, self.AB_band, *ABMag_options)
        self.menu_AB_band.place(x=2200, y=18)



        ### Type of spectrum  ###
        #########################
        self.label_TypeOfSpectrum = Label(self.frame2b, text="Spectrum")
        self.label_TypeOfSpectrum.place(x=290, y=18)
        # Dropdown menu
        options = [
            "Flat F_nu",
            "My own spectrum",
        ]
        self.TypeOfSpectrum = StringVar()
        self.TypeOfSpectrum.set(options[0])
        # Create Dropdown menu
        self.drop_TypeOfSpectrum = OptionMenu(
            self.frame2b, self.TypeOfSpectrum, *options, command=self.select_SourceSpectrum)
        self.drop_TypeOfSpectrum.place(x=347, y=18)
        self.drop_TypeOfSpectrum.config(width=10)

        ### FILENAME ###
        ################
        self.label_Filename = Label(self.frame2b, text="Filename")
        self.label_Filename.place(x=10, y=53)
        self.Entry_Filename = Entry(self.frame2b, width=30)
        self.Entry_Filename.place(x=70, y=50)
 
        # Dropdown menu
        ###############
        self.buttons_FlamORFnu_index = {}
        self.selected_FlamORFnu = StringVar(value='F_lam')
        modes = ['F_lam', 'F_nu']
        counter = 0
        for mode in modes:
            self.r_FlamORFnu = Radiobutton(
                self.frame2b,
                text=mode,
                value=mode,
                variable=self.selected_FlamORFnu,
            )
            self.r_FlamORFnu.place(x=350+counter*70, y=53)
            counter += 1
            self.buttons_FlamORFnu_index[mode]=self.selected_FlamORFnu


        ### WAVELENGTH UNIT ###
        ################
        self.label_SpectrumWlUnits = Label(self.frame2b, text="Wavelength Unit")
        self.label_SpectrumWlUnits.place(x=10, y=83)
        self.selected_SpectrumWlUnits = StringVar(value='Angstrom')
        modes = ['Angstrom', 'Micron']
        counter = 0
        for mode in modes:
            self.r_SpectrumWlUnits = Radiobutton(
                self.frame2b,
                text=mode,
                value=mode,
                variable=self.selected_SpectrumWlUnits
            )
            self.r_SpectrumWlUnits.place(x=120+counter*90, y=83)
            counter += 1
            
        ### MAGNITUDE REDSHIFT ###
        ################
        self.label_MagnitudeRedshift = Label(self.frame2b, text="Redshift")
        self.label_MagnitudeRedshift.place(x=350, y=83)
        init_MagnitudeRedshift = StringVar()
        init_MagnitudeRedshift.set("0.0")
        self.Entry_MagnitudeRedshift = Entry(
            self.frame2b, width=4, textvariable=init_MagnitudeRedshift)
        self.Entry_MagnitudeRedshift.place(x=412, y=80)
            


########################################################################################################
########################################################################################################

        # Constructing frame Exp Time vs SNR
        # , padx=15, pady=15)
        self.frame4 = Frame(self.frame0l, bg="light gray")
        # Displaying the frame2
        self.frame4.place(x=2, y=430, width=496, height=110)

        self.w = Canvas(self.frame4, width=496, height=110)
        self.w.create_rectangle(8, 8, 488, 102, outline='blue')
        self.w.pack()

        self.w.create_rectangle(8, 8, 488, 64, outline='blue')
        ### ExpTimeORSNR ###
        ####################
        self.label_ExpTimeORSNR = Label(
            self.frame4, text="Input an exposure time or a desired Signal to Noise ratio")
        self.label_ExpTimeORSNR.place(x=10, y=12)
        self.selected_ExpTimeORSNR = StringVar()
        modes = ['Determine Exposure Time', 'Determine Signal to Noise']
        counter = 0
        for mode in modes:
            self.r_ExpTimeORSNR = Radiobutton(
                self.frame4,
                text=mode,
                value=mode,
                variable=self.selected_ExpTimeORSNR,
                command=self.hide_ExpTimeORSNR
            )
            self.r_ExpTimeORSNR.place(x=10+counter*235, y=35)
            counter += 1
        #self.selected_ExpTimeORSNR.set('Determine Exposure Time')

        self.w.create_rectangle(8, 64, 238, 102, outline='blue')
        
        ### TOTAL EXPOSURE TIME ###
        ###########################
        self.label_TotalExpTime = Label(self.frame4, text="Total Exposure Time")
        self.label_TotalExpTime.place(x=10, y=73)
        init_TotalExpTime = StringVar()
        init_TotalExpTime.set("1000")
        self.Entry_TotalExpTime = Entry(self.frame4, width=7, textvariable=init_TotalExpTime)
        self.Entry_TotalExpTime.place(x=145, y=70)
        self.label_s = Label(self.frame4, text="s")
        self.label_s.place(x=220, y=73)

        ### DESIRED SNR ###
        ###########################
        self.label_DesiredSNR = Label(self.frame4, text="Desired SNR")
        self.label_DesiredSNR.place(x=280, y=73)
        init_SNR = StringVar()
        init_SNR.set("10")
        self.Entry_DesiredSNR = Entry(self.frame4, width=7, textvariable=init_SNR)
        self.Entry_DesiredSNR.place(x=360, y=70)


##############################################################################################################
##############################################################################################################

        # Constructing the fifth frame, frame5

        # , padx=15, pady=15)
        self.frame5 = Frame(self.frame0l, bg="light gray")
        self.frame5.place(x=2, y=535, width=496, height=65)

        self.w5 = Canvas(self.frame5, width=496, height=65)
        self.w5.create_rectangle(8, 8, 488, 59, outline='blue')
        self.w5.pack()

  #      self.w.create_rectangle(8, 8, 488, 62, outline = 'blue')

        ### OPTIONAL INPUT ###
        ######################
        self.label_AirmassANDWaterVapor = Label(
            self.frame5, text="Optional Input: Airmass and Water Vapour")
        self.label_AirmassANDWaterVapor.place(x=10, y=12)
        self.selected_AirmassORWaterVapor = StringVar()
        selfmodes_AirmassORWaterVapor = [
            'Use Default', 'Airmass and Water Vapor Column']
        counter = 0
        for mode in selfmodes_AirmassORWaterVapor:
            self.radio_AirmassORWaterVapor = Radiobutton(
                self.frame5,
                text=mode,
                value=mode,
                variable=self.selected_AirmassORWaterVapor,
                command=self.hide_AirmassORWaterVapor
            )
            self.radio_AirmassORWaterVapor.place(x=10+counter*115, y=35)
            counter += 1
        self.selected_AirmassORWaterVapor.set('Use Default')

        # , padx=15, pady=15)
        self.frame5b = Frame(self.frame0l, bg="light gray")
        self.frame5b.place(x=2, y=594, width=496, height=120)
   #     self.w.create_rectangle(8, 62, 228, 112, outline = 'blue')

        self.w5b = Canvas(self.frame5b, width=496, height=120)
        self.w5b.create_rectangle(8, 3, 488, 52, outline='blue')
        self.w5b.pack()

        ### AIRMASS ###
        ###############
        self.label_Airmass = Label(self.frame5b, text="Airmass")
        self.label_Airmass.place(x=80, y=5)
        self.selected_Airmass = StringVar()
        self.modes_Airmass = ['1.0', '1.5', '2.0']
        counter = 0
        for mode in self.modes_Airmass:
            self.radio_Airmass = Radiobutton(
                self.frame5b,
                text=mode,
                value=mode,
                variable=self.selected_Airmass,
#                command = self.hide
            )
            self.radio_Airmass.place(x=10+counter*50, y=25)
            counter += 1
        self.selected_Airmass.set('1.0')

        self.w5b.create_rectangle(8, 3, 244, 52, outline='blue')

        ### Water Vapor ###
        ###################
        self.label_WaterVapor = Label(self.frame5b, text="Water Vapor (mm)")
        self.label_WaterVapor.place(x=300, y=5)
        self.selected_WaterVapor = StringVar()
        self.modes_WaterVapor = ['1.0', '1.6', '3.0', '5.0']
        counter = 0
        for mode in self.modes_WaterVapor:
            self.radio_WaterVapor = Radiobutton(
                self.frame5b,
                text=mode,
                value=mode,
                variable=self.selected_WaterVapor
                # command = self.hide_AirmassORWaterVapor
            )
#       radio_WaterVapor_1p0 =  Radiobutton(self.frame5, text=modes[0], value=modes[0], variable=self.selected_WaterVapor,
#           state = 'disabled',
#           #command = self.hide_AirmassORWaterVapor
#       )
            self.radio_WaterVapor.place(x=250+counter*50, y=25)
            counter += 1
        self.selected_WaterVapor.set('1.6')

######################################################################

# =============================================================================
# # =============================================================================
# #         # Constructing the last frame
# #         # , padx=15, pady=15)
# # =============================================================================
        self.frame6 = Frame(self.frame0l, bg="light gray")
        # Dislaying the self.frame2
        self.frame6.place(x=2, y=650, width=496, height=70)

        self.w = Canvas(self.frame6, width=496, height=69)
        self.w.create_rectangle(8, 8, 488, 61, outline='blue')
        self.w.pack()

        ### CALCULATE OR EXIT ###
        #########################
        self.button_Calculate = Button(self.frame6, text="Calculate", command=self.XTcalc)
        self.button_Calculate.place(x=150, y=20)
        # , command=root_exit)
        self.button_Exit = Button(self.frame6, text="Exit", command=self.root_exit)
        self.button_Exit.place(x=250, y=20)

        self.initial_setup()
        
        


# =============================================================================
#         #########################
#         ### OUTPUT FRAME ###
#         #########################
# 
# =============================================================================
        self.frame_out = Frame(self.frame0r, bg="light gray")
        self.frame_out.place(x=2, y=2, width=500, height=720)

        self.w = Canvas(self.frame_out, width=496, height=714)
        self.w.create_rectangle(8, 8, 488, 46, outline='blue')
        self.w.pack()

    
        self.text_SAMOS_Header = Text(self.frame_out, width=66, height=2, background='light gray')
        if platform == "win32":
            self.text_SAMOS_Header = Text(self.frame_out, width=59, height=2, background='light gray')
        #self.text_SAMOS_Header.insert(INSERT, text)
        self.text_SAMOS_Header.place(x=12, y=10)
        

        self.set = ttk.Treeview(self.frame_out)
        self.set.place(x=2, y=50, width=490, height=280)

        self.set['columns']= ('Parameter', 'Value','Units')
        self.set.column("#0", width=0,  stretch=NO)
        self.set.column("Parameter",anchor=CENTER, width=150)
        self.set.column("Value",anchor=CENTER, width=100)
        self.set.column("Units",anchor=CENTER, width=235)
# 
        self.set.heading("#0",text="",anchor=CENTER)
        self.set.heading("Parameter",text="Parameter",anchor=CENTER)
        self.set.heading("Value",text="Value",anchor=CENTER)
        self.set.heading("Units",text="Units",anchor=CENTER)
# 
#        self.set.insert(parent='',index='end',iid=0,text='',values=('101','john','Gold'))
#        self.set.insert(parent='',index='end',iid=1,text='',values=('102','jack',"Silver"))
#        self.set.insert(parent='',index='end',iid=2,text='',values=('103','joy','Bronze'))
# 
# =============================================================================

# =============================================================================
#         ##################################
#         ###  PLOT OBSERVATIONS OR SNR? ###
#         ##################################
# 
# =============================================================================
        self.w.create_rectangle(8, 336, 492, 367, outline='blue')
 
        self.selected_PlotObsORSNR = StringVar(value='Plot Observations')
        modes = ['Plot Observations', 'Plot Signal to Noise']
        commands=[self.plot_obs,self.plot_snr]
        counter = 0
        for mode in modes:
            self.r_PlotObsORSNR = Radiobutton(
                self.frame_out,
                text=mode,
                value=mode,
                variable=self.selected_PlotObsORSNR,
                command=commands[counter]
            )
            self.r_PlotObsORSNR.place(x=12+counter*200, y=340)
            counter += 1


# =============================================================================
#         ##################################
#         ###  PLOT DEFAULT WL OR USER SPECIFIED?  ###
#         ##################################
# 
# =============================================================================
        self.w.create_rectangle(8, 371, 492, 402, outline='blue')
 
        self.label_PlotWavelengthRange  = Label(self.frame_out, text="Wl range")
        self.label_PlotWavelengthRange.place(x=12, y=375)
        self.selected_PlotWavelengthRange = StringVar(value='Default')
        modes = ['Default', 'User set']
        counter = 0
        for mode in modes:
            self.r_PlotWavelengthRange = Radiobutton(
                self.frame_out,
                text=mode,
                value=mode,
                variable=self.selected_PlotWavelengthRange,
                command = self.hide_PlotWithUserSpecifiedWavelengths
            )
            self.r_PlotWavelengthRange.place(x=75+counter*75, y=375)
            counter += 1

# =============================================================================
#         wl_0 = StringVar()
#         wl_1 = StringVar()
#         wl_range=self.bandpass.get()
#         wl_0.set(wl_range[0])
#         wl_1.set(wl_range[-1])
# 
# =============================================================================
        self.Entry_lambdamin= Entry(self.frame_out, width=6)
        self.Entry_lambdamin.place(x=235, y=372)
        self.Entry_lambdamin.configure(state='disabled')

        self.label_2dash = Label(self.frame_out, text="--")
        self.label_2dash.place(x=290, y=375)
        self.label_2dash.configure(state='disabled')

        self.Entry_lambdamax= Entry(self.frame_out, width=6)
        self.Entry_lambdamax.place(x=305, y=372)
        self.Entry_lambdamax.configure(state='disabled')

        self.label_lambdamicron = Label(self.frame_out, text="micron")
        self.label_lambdamicron.place(x=340, y=375)
        self.label_lambdamicron.configure(state='disabled')
        
        self.Button_RefreshPlot = Button(self.frame_out,text="Refresh", command=self.RefreshPlot)
        self.Button_RefreshPlot.place(x=400,y=372)                                 


# =============================================================================
# # =============================================================================
# # Last set of buttons for the printout  
# # 
# # =============================================================================
#         Results_path = homedir + '/Mosfire_Results/'
# =============================================================================

        self.w.create_rectangle(8, 655, 492, 710, outline='blue')

        self.button_PrintToFile = Button(self.frame_out, text="Print to file", command=self.PrintToFile, relief=RAISED) 
        self.button_PrintToFile.place(x=10, y=670)        

        self.buttons = {}
        text_buttons=["Throughput", "Transmission", "Background", "Signal", "Noise", "S/N"] 
        offset = [0,1,2,0,1,2]
        counter = 0
        for name in text_buttons:
            self.button_var = IntVar()
            self.button_var.set(0)
            self.cb = Checkbutton(self.frame_out, text=name, variable=self.button_var)
            self.cb.place(x=130+120*offset[counter], y= 663+20*int(counter/3))
            self.buttons[name]=self.button_var
            counter = counter+1


# =============================================================================
#         for name in os.listdir(filedir):
#             if name.endswith('.py') or name.endswith('.pyc'):
#                 if name not in ("____.py", "_____.pyc"):
#                     var = tk.IntVar() 
#                     var.set(0)
#                     cb.pack()
#                     buttons.append((var,name))
# 
# =============================================================================




    def RefreshPlot(self):
        if self.selected_PlotObsORSNR.get() == "Plot Observations":
            self.plot_obs()
        else:
            self.plot_snr()
          
            
        ######################################################################

    def initial_setup(self):
        self.selected_FluxORmag.set('Use magnitude')
        self.hide_FluxORmag()
        self.selected_AirmassORWaterVapor.set('Use Default')
#        self.hide_AirmassORWaterVapor()
#        self.selected_ExpTimeORSNR.set('Desired SNR')
        self.hide_ExpTimeORSNR()
        self.selected_ExpTimeORSNR.set('Determine Signal to Noise')
        self.read_throughput_files()
#        self.selected_PlotObsORSNR.set('Plot Observations') 
# =============================================================================
#         wl_range=spec_struct["wave"] 
#         #for the output window, set the lambdamin/max of the bandpass
#         wl_0 = wl_range[0]
#         wl_1 = wl_range[-1]
#         self.Entry_lambdamin.set(str(wl_0))
#         self.Entry_lambdamax.set(str(wl_1))
#         
# =============================================================================

    # collect all parameters and put it in a dictionary

    def collect_all_parameters(self):
        all_parameters = {
            "bandpass": self.bandpass.get(),
#            "slit": self.Entry_SlitWidth.get(),
            "slit": self.slit_selected.get(),
            "NrOfExp": self.Entry_NofExp.get(),
            "AngularExt": self.Entry_AngularExtent.get(),
#            "NrFowlerPairs": self.Entry_NrFowlerPairs.get(),
            "FluxORMag": self.selected_FluxORmag.get(), #['Line Flux', 'magnitude']
            "LineFlux": self.Entry_LineFlux.get(),  # 1E-17 units
            "CentralWl": self.Entry_CentralWl.get(),
            "LineWlUnits": self.selected_LineWlUnits.get(),
            "LineRedshift": self.Entry_LineRedshift.get(),
            "FWHM": self.Entry_FWHM.get(),
            "SourceMagnitude": self.Entry_Magnitude.get(),
            "Magnitude System": self.selected_MagnitudeSystem.get(), #['AB', 'Vega']
            "Vega_band": self.Vega_band.get(),
            "AB_band": self.AB_band.get(),
            "TypeOfSpectrum": self.TypeOfSpectrum.get(),
            "Filename": self.Entry_Filename.get(),
            "FluxUnits": self.selected_FlamORFnu.get(),
            "MagnitudeRedshift": self.Entry_MagnitudeRedshift.get(),
            "SpectrumWlUnits": self.selected_SpectrumWlUnits.get(),
            "ExpTimeORSNR": self.selected_ExpTimeORSNR.get(),
            "TotalExpTime": self.Entry_TotalExpTime.get(),
            "DesiredSNR": self.Entry_DesiredSNR.get(),
            "AirmassORWaterVapor": self.selected_AirmassORWaterVapor.get(),
            "Airmass": self.selected_Airmass.get(),
            "WaterVapor": self.selected_WaterVapor.get()
        }
        return(all_parameters)

    def read_throughput_files(self):
        # From SAMOS_throughput_20210608.xlsx
        # Note: Production mimimums used for grating efficiencies, dewar windows and detector efficiency excluded, 92% DMD fill factor, and 80% DMD diffraction efficiency applied to FRED data to get throughput
        SAMOS_LowRed_Jack_wl = np.array([600,  625,  650,  675,  700,  725,  750,  775,  800,  825,  850,  875,  900,  925,  950]) * 1E-3 #;nm->[micron]
        SAMOS_LowRed_Jack_th = np.array([23.8, 26.8, 29.2, 31.1, 31.5, 30.9, 30.5,    28.9, 27.2, 25.3, 23.9, 22.2, 19.7, 17.4, 15.5]) * 1E-2
        SAMOS_LowRed_throughput = np.transpose(np.array([SAMOS_LowRed_Jack_wl,SAMOS_LowRed_Jack_th]))
        self.SAMOS_LowRed_throughput_Wave = SAMOS_LowRed_throughput[:,0].astype(float) 
        self.SAMOS_LowRed_throughput_Flux = SAMOS_LowRed_throughput[:,1].astype(float)
        
        SAMOS_LowBlue_Jack_wl = np.array([400, 450, 500, 550, 600, 700, 770, 850, 950]) * 1E-3 #;nm->[micron]
        SAMOS_LowBlue_Jack_th = np.array([25.0,    33.3,38.4,39.6,38.4,36.3,33.2,30.1,28.4]) * 1E-2
        SAMOS_LowBlue_throughput = np.transpose(np.array([SAMOS_LowBlue_Jack_wl,SAMOS_LowBlue_Jack_th]))
        self.SAMOS_LowBlue_throughput_Wave = SAMOS_LowBlue_throughput[:,0].astype(float)
        self.SAMOS_LowBlue_throughput_Flux = SAMOS_LowBlue_throughput[:,1].astype(float)
        
        SAMOS_HighRed_Jack_wl = np.array([600, 610, 620,   630,    640,    650,   660,    670,    680,    690,    700 ]) * 1E-3 #;nm->[micron]
        SAMOS_HighRed_Jack_th = np.array([31.7,    34.1,36.0,    37.2,    37.9,    37.7,    37.0,    35.2,    33.3,    30.8,    28.1]) * 1E-2
        SAMOS_HighRed_throughput = np.transpose(np.array([SAMOS_HighRed_Jack_wl,SAMOS_HighRed_Jack_th]))
        self.SAMOS_HighRed_throughput_Wave = SAMOS_HighRed_throughput[:,0].astype(float)
        self.SAMOS_HighRed_throughput_Flux = SAMOS_HighRed_throughput[:,1].astype(float)
        
        SAMOS_HighBlue_Jack_wl = np.array([448, 45,    460,470,480,490,500,510,516]) * 1E-3 #;nm->[micron]
        SAMOS_HighBlue_Jack_th = np.array([34.7, 35.4, 39.5, 41.4, 41.4,40.9, 38.4,35.4,33.8]) * 1E-2
        SAMOS_HighBlue_throughput = np.transpose(np.array([SAMOS_HighBlue_Jack_wl,SAMOS_HighBlue_Jack_th]))
        self.SAMOS_HighBlue_throughput_Wave = SAMOS_HighBlue_throughput[:,0].astype(float)
        self.SAMOS_HighBlue_throughput_Flux = SAMOS_HighBlue_throughput[:,1].astype(float)

        #adding SAMI from same file
        SAMI_CCD_Jack_wl = np.array(np.array([400, 450, 500, 550, 600, 700, 770, 850, 950]) )* 1E-3 #;nm->[micron]) * 1E-3 #;nm->[micron]
        SAMI_window_Jack_th = np.array([0.980,    0.990,    0.990,    0.990,    0.990,    0.990,    0.990,    0.990,    0.980])
        SAMI_CCD_Jack_th    = np.array([0.810,    0.850,    0.840,    0.820,    0.780,    0.710,    0.600,    0.400,    0.140])
        SAMI_WinCDD_Jack_th = SAMI_window_Jack_th  * SAMI_CCD_Jack_th
        SAMI_CCD_throughput = np.transpose(np.array([SAMI_CCD_Jack_wl,SAMI_WinCDD_Jack_th]))
        self.SAMI_CCD_throughput_Wave = SAMI_CCD_throughput[:,0].astype(float)
        self.SAMI_CCD_throughput_Flux = SAMI_CCD_throughput[:,1].astype(float)
        
        #SAM throuhgput: from A. Tokovinin, private communicaiton
        self.SAM_th = 0.9  
      
        
    def hide_FluxORmag(self):
        print(self.selected_FluxORmag.get())
        if self.selected_FluxORmag.get() == 'Use magnitude':
             for child in self.frame2.winfo_children():
                 try:
                     if child.widgetName != 'frame':  # frame has no state, so skip
                         child.configure(state='disabled')
                 except Exception as e:
                     print(e)
             for child in self.frame2b.winfo_children():
                 try:
                     if child.widgetName != 'frame':  # frame has no state, so skip
                         child.configure(state='normal')
                 except Exception as e:
                     print(e)
        if self.selected_FluxORmag.get() == 'Use Line Flux':
             for child in self.frame2.winfo_children():
                 try:
                     if child.widgetName != 'frame':  # frame has no state, so skip
                         child.configure(state='normal')
                 except Exception as e:
                     print(e)
             for child in self.frame2b.winfo_children():
                 try:
                     if child.widgetName != 'frame':  # frame has no state, so skip
                         child.configure(state='disabled')
                 except Exception as e:
                     print(e)
 
    def hide_Vegamag(self):
        if self.selected_MagnitudeSystem.get() == 'AB':
            self.menu_Vega_band.configure(state='disabled')               
        else:
            self.menu_Vega_band.configure(state='normal')               


    def shift_ABorVegamag(self):
        if self.selected_MagnitudeSystem.get() == 'AB':
            self.menu_Vega_band.place(x=2200, y=18)
            self.menu_AB_band.place(x=220, y=18)
        else:
            self.menu_Vega_band.place(x=220, y=18)
            self.menu_AB_band.place(x=2200, y=18)

    
    def read_ABfilters(self):
#        homedir = os.getcwd() 
        filter_path = self.homedir + '/Filters/'
        AB_filter = self.AB_band.get()
        if AB_filter  == 'u_SDSS':
            df = pd.read_csv(filter_path+'u_SDSS.res.txt', delimiter='\s+', header=None)
        if AB_filter  == 'g_SDSS':
            df = pd.read_csv(filter_path+'g_SDSS.res.txt', delimiter='\s+', header=None)
        if AB_filter  == 'r_SDSS':
            df = pd.read_csv(filter_path+'r_SDSS.res.txt', delimiter='\s+', header=None)
        if AB_filter  == 'i_SDSS':
            df = pd.read_csv(filter_path+'i_SDSS.res.txt', delimiter='\s+', header=None)
        if AB_filter  == 'z_SDSS':
            df = pd.read_csv(filter_path+'z_SDSS.res.txt', delimiter='\s+', header=None)
        if AB_filter  == 'Y_VISTA':
            df = pd.read_csv(filter_path+'Y_uv.res.txt', delimiter='\s+', comment='#', header=None)
        if AB_filter  == 'J_VISTA':
            df = pd.read_csv(filter_path+'J_uv.res.txt', delimiter='\s+', comment='#', header=None)
        if AB_filter  == 'H_VISTA':
            df = pd.read_csv(filter_path+'H_uv.res.txt', delimiter='\s+', comment='#', header=None)
        if AB_filter  == 'K_VISTA':
            df = pd.read_csv(filter_path+'K_uv.res.txt', delimiter='\s+', comment='#', header=None)
#        wl_A = df[0]
#        tp   = df[1]
        return df.to_numpy() 


    def hide_AirmassORWaterVapor(self):
        if self.selected_AirmassORWaterVapor.get() == 'Use Default':
              for child in self.frame5b.winfo_children():
                  try:
                      if child.widgetName != 'frame':  # frame has no state, so skip
                          child.configure(state='disabled')
                  except Exception as e:
                      print(e)
        else:
              for child in self.frame5b.winfo_children():
                  try:
                      if child.widgetName != 'frame':  # frame has no state, so skip
                          child.configure(state='normal')
                  except Exception as e:
                      print(e)

    def hide_ExpTimeORSNR(self):
        if self.selected_ExpTimeORSNR.get() == 'Determine Exposure Time':
            self.label_TotalExpTime.configure(state='disabled')
            self.Entry_TotalExpTime.configure(state='disabled')
            self.label_s.configure(state='disabled')
            ### HIDE SNR ###
            ###########################
            self.label_DesiredSNR.configure(state='normal')
            self.Entry_DesiredSNR.configure(state='normal')
        else:
            self.label_TotalExpTime.configure(state='normal')
            self.Entry_TotalExpTime.configure(state='normal')
            self.label_s.configure(state='normal')
            ### HIDE SNR ###
            ###########################
            self.label_DesiredSNR.configure(state='disabled')
            self.Entry_DesiredSNR.configure(state='disabled')

    def hide_PlotWithUserSpecifiedWavelengths(self):
        if self.selected_PlotWavelengthRange.get() == 'Default':
            self.Entry_lambdamin.configure(state='disabled')
            self.label_2dash.configure(state='disabled')
            self.Entry_lambdamax.configure(state='disabled')
            self.label_lambdamicron.configure(state='disabled')
        else:
            self.Entry_lambdamin.configure(state='normal')
            self.label_2dash.configure(state='normal')
            self.Entry_lambdamax.configure(state='normal')
            self.label_lambdamicron.configure(state='normal')


    def validate(self, all_parameters):
        #validate nr of exposures
        if all_parameters["NrOfExp"].isdigit() == False:
           messagebox.showerror(title=None,message="Nr. of Exp must be an integer > 0")
        elif int(all_parameters["NrOfExp"]) < 1:   
           messagebox.showerror(title=None,message="Nr. of Exp must be an integer > 0")
        # validate line flux
        if all_parameters["FluxORMag"] == 'Use Line Flux':
           if float(all_parameters["LineFlux"]) <= 0:
             messagebox.showerror(title=None, message="Line Flux must be  > 0")
           if float(all_parameters["CentralWl"]) <= 0:
             messagebox.showerror(
                 title=None, message="Central Wavelength must be  > 0")

#    def check_RedshiftedWavelength(self): 
#        print('pippo')
#        CentralWl = float(self.Entry_CentralWl.get())
#        Redshift =  float(self.Entry_Redshift.get())
#        RedshiftedWavelength = CentralWl * (1+Redshift)
#        RedshiftedWavelength_string = "{:.2f}".format(RedshiftedWavelength)
#        print(CentralWl, Redshift, RedshiftedWavelength, RedshiftedWavelength_string)
#        self.Entry_RedshiftAdopted.insert(END,RedshiftedWavelength_string)

 #       # validate redshift
 #       if float(all_parameters["Redshift"]) < 0:
 #          messagebox.showerror(title=None, message="Redshift must be  >= 0")
         
# =============================================================================
# =============================================================================
#          ;make the structure into something useful
# =============================================================================



    def select_SourceSpectrum(self,arg1):
        if arg1 == 'My own spectrum':
# =============================================================================
#             self.label_Filename.configure(state='normal')
#             self.Entry_Filename.configure(state='normal')
#             self.r_FlamORFnu.configure(state='normal',value='F_lam')
#             self.r_FlamORFnu.configure(state='normal',value='F_nu')
#             self.label_SpectrumWlUnits.configure(state='normal')
#             self.r_SpectrumWlUnits.configure(state='normal')
#             self.label_MagnitudeRedshift.configure(state='normal')
#             self.Entry_MagnitudeRedshift.configure(state='normal')
# 
# =============================================================================
            self.source_filename = StringVar()
            filetypes = (
                ('text files', '*.txt'),
                ('text files', '*.dat'),
                ('text files', '*.fits'),
                ('All files', '*.*')
                )
            self.source_fullpathfilename = fd.askopenfilename(
                title='Open a file',
                initialdir = os.getcwd()+'/templates/',
                filetypes=filetypes)            
            full_path = os.path.dirname(self.source_fullpathfilename)
            self.selected_directory = full_path.replace(os.getcwd()+'/templates/','')   #e.g.'Pickles_1998
            self.selected_file = self.source_fullpathfilename.replace(os.getcwd()+'/templates/','') #e.g. '
            self.Entry_Filename.insert(END,self.selected_file)
            
# =============================================================================
#  =============================================================================
# # =============================================================================
# #
# =============================================================================
    def read_SourceSpectrum(self):
        logc=np.log10(29979245800.)  
        if self.selected_directory == 'Pickles_1998':
            df = pd.read_csv(self.source_fullpathfilename, delimiter='\s+', header=None)
            df = df.to_numpy()
            wl_A = df[:,0]
            userspec_wl_um =  (df[:,0]).flatten() / 10000.0   # we work with wl in micron
            userspec_Flam =  (df[:,1]).flatten()
            userspec_Fnu = userspec_Flam *10**logc / (userspec_wl_um*1E-4)**2
#            print('stop here')
#            if all_parameters["TypeOfSpectrum"] ==  "My own spectrum":
    ##          print(self.source_filename)

# =============================================================================
#       #B) Stellar Models: Allard Spectra
        if self.selected_directory == 'BT-Settl-CIFSST2011bc/SPECTRA':
              t_lwr = Table.read(self.source_fullpathfilename,format='fits')#,names=['WAVE','FLUX','dFLUX'])
#             #
              wl = t_lwr['wl_A'] # angstrom
              wl_range = (wl >= 3E2) & (wl <= 3E6) 
              wl = wl[wl_range]
#             
              Flam = 10**(t_lwr['Flam']-8)   #Flam = erg/cm2/s/A , from README.rtf file of Allard.
              Flam = Flam[wl_range]
#             
              userspec_wl_um = wl / 10000.0  
              userspec_Fnu = Flam * 10**logc / (wl*1E-4)**2
# =============================================================================
# =============================================================================
        if self.selected_directory == 'others':
# #             #
              df = pd.read_csv(self.source_fullpathfilename, delimiter='\s+', header=None)
              df = df.to_numpy()
              wl = df[2:,0]
              Fl = df[2:,1]
              if self.selected_LineWlUnits.get() == 'Angstrom':
                   wl_A = wl  #
                   userspec_wl_um = wl_A /10000.0
              else:
                   usersepc_wl_um = wl                  
              if self.selected_FlamORFnu.get() == 'F_lam':
                   Flam =Fl
                   userspec_Fnu = Fl * 10**logc / (userspec_wl_um*1E-4)**2
              else:    
                   userspec_Fnu = Fl
# # =============================================================================
# =============================================================================
        self.user_Wave = userspec_wl_um#A
        self.user_Flux = userspec_Fnu#lam
        return 
# ====== =======================================================================
#         else:
#          ### FILENAME ###
#          ################
#             print('disable all')
#             self.label_Filename.configure(state='disabled')
#             self.Entry_Filename.configure(state='disabled')
#             self.r_FlamORFnu.configure(state='disabled',value='F_lam')
#             self.r_FlamORFnu.configure(state='disabled',value='F_nu')
#             self.label_SpectrumWlUnits.configure(state='disabled')
#             self.r_SpectrumWlUnits.configure(state='disabled')
#             self.label_MagnitudeRedshift.configure(state='disabled')
#             self.Entry_MagnitudeRedshift.configure(state='disabled')
# 
# =============================================================================
#purpose is to mimic what output would look like based on the inherent flaws of optics of telescope
#basic process: convert everything to velocity, make a gaussian kernal and convolve it with the rest of the function, 
#               then convert back to wavelength

 

    def Moffat4(self,FWHM,beta):# ;eta is the Moffat parameter, FWHM in arcsec
# =============================================================================
#     ;examples:
#     ;a) to display the PSF, FWHM=0.8"
#     ;IDL> show3,moffat(0.5)/max(moffat(0.5))  
#     ;b) to find the encircled energy over a long slit of 0.8", FWHM=0.45"
#     ;slit=0.8 & print,total((moffat(0.45))[320-(slit/2.*100):320+(slit/2.*100-1),*])
#     
#     ;==========================================================================
#     dist_circle, circle, 2048 ;ancillary for Moffat below - will result in a 2048x2048 image with source centered at (1024-1)/2 = (511.5,511.5), i.e. peaks at the pixel center  
# =============================================================================
        xc=512
        yc=512
        rows, cols = (xc, yc)
        dist_circle=np.zeros((xc,yc))
        for i in range(rows):
            for j in range(cols):
                dist_circle[i,j] = np.sqrt( (i-xc/2)**2 + (j-yc/2)**2 )
    #    ;beta = 2.    ;appropriate from SAM, e-mail from Tokovinin; set =3 for VLT/FORS1 and =100 for a Gaussian profile
        FWHM_75=FWHM*75.   #;use 0.0033*4 =0.0122" pixels
        alpha = FWHM_75 / (2.*np.sqrt(2.**(1./beta)-1.))  # ; well known relation, e.g. from http://pixinsight.com/doc/tools/DynamicPSF/DynamicPSF.html
                                                           # ; or Patat 2011 http://www.aanda.org/articles/aa/full_html/2011/03/aa15537-10/aa15537-10.html    
    #    ;got this analytic form Patat et al. or http://en.wikipedia.org/wiki/Moffat_distribution
        PSF_Moffat4 = (beta-1)/(np.pi*alpha**2)/(1.+dist_circle**2/alpha**2)**beta     
        return PSF_Moffat4
# =============================================================================
# =============================================================================


    def DMDslit4(self,Nslit_X,Nslit_Y):
# =============================================================================
#         ;1DMD side is typically 10micron size = 166.6mas.
#         ;the gap is 0.6micron wide, i.e. 10mas (exactly!).
#         ;we sample the gap with 3 pixels: 1 pixel=0.2micron=3.33mas. The grid is therefore made of 
#         ; 3pixel wide gap
#         ; 50pixel wide mirror sides
#         ; 1" is therefore 300pixels. 
#         ;if we work with images of 2048x2048 pixels, we have 6.82" fields; enough for a decent long slit.
#         ;therefore
# =============================================================================
#        slit=fltarr(2048,2048)+1
        rows, cols = (512, 512)
        slit4=[]#np.zeros(shape=(rows,cols))
        for i in range(rows):
            col = []
            for j in range(cols):
                col.append(1)
            slit4.append(col)
        slit4=np.array(slit4)
        
 #       edges = np.arange(1,50*51,52)
        Xparity = np.fmod(Nslit_X/2,1)
# =============================================================================
# =============================================================================
        if Xparity != 0:
              slit4[0:256-int(Nslit_X*8), :] = 0 
              slit4[256+int(Nslit_X*8):,:] = 0
        else:          
              slit4[0:256-int(Nslit_X/2*13), :] = 0 
              slit4[256+int(Nslit_X/2*13):,:] = 0
#
        Yparity = np.fmod(Nslit_Y/2,1)
        if Yparity != 0:
              slit4[:,0:256-int(Nslit_Y*8)] = 0 
              slit4[:,256+int(Nslit_Y*8):] = 0
        else: 
              slit4[:,0:256-int(Nslit_Y/2*7)] = 0 
              slit4[:,256+int(Nslit_Y/2*7):] = 0
# 
# =============================================================================
        return slit4


# =============================================================================
# # =============================================================================
# # =============================================================================
# 
# =============================================================================
    def slit_loss(self,FWHM,beta,Nslit_X,Nslit_Y):
       PSF_in = self.Moffat4(FWHM,beta)
       slit = self.DMDslit4(Nslit_X,Nslit_Y)
       PSF_out = np.multiply(PSF_in,slit)
       slit_loss=np.sum(PSF_out)   #sum(PSF_in-PSF_out)/sum(PSF_in)
       return slit_loss

# =============================================================================




    def degrade_resolution(self, wavelengths, flux, center_wave, spec_res, disp, px_tot):    
    #0.40471199999999996 1.34252 4096
# =============================================================================
#       Number of pixels to be output - 50%  more than are on the detector to cover the K band for MOSFIRE  
        Npix_spec = px_tot * 3./2.  # if px_tot=4096, this is 6144 pixels
#     
# =============================================================================
#       the log of speed of light in cm/s
        logc=np.log10(29979245800.)  
#     
# =============================================================================
#       make "velocity" grid centered at the central wavelength of the band
#       sampled at 1 km/s, from -300,000 to 300,000 Km/s
        vel=(np.arange(600001)-300000) # big array of integers....   [km/s]
#     
# =============================================================================
#       the array of wavelengths coming in input is converted to velocity difference vs. central wavelength, in km/s
        in_vel=(wavelengths/center_wave-1)*10.**(1*logc-5) 
#     
# =============================================================================
#       if the array of wavelengths too wide
#       we can get non-physical velocities: kill them and their relative input flux array
#       create vectors in velocity space, picking realistic values (keeping good indices)
        in_vel_short = in_vel[ np.where( (in_vel > vel[0]) & (in_vel < vel[600000]) )[0] ]
        in_flux_short = flux[ np.where( (in_vel > vel[0]) & (in_vel < vel[600000]) )[0] ] 
#     
# =============================================================================
#       these new arrays of rel. velocities from the center_wave, and relative fluxes, are n
#       calculated starting from the wavelengths and therefore are not uniformly sampled...
#       interpolate to equally spaced km/s, up to 600000 points

#        interp_flux = np.interp(vel, in_vel_short, in_flux_short, fill_value = "extrapolate")   
        f = interpolate.interp1d(in_vel_short, in_flux_short, fill_value = "extrapolate")   
        interp_flux = f(vel)
        
#     
# =============================================================================
#       now we need to blur this highly dispersed spectrum with the response of the slit, in km/s.
#       sigma  = the resolution of the spectrograph in km/s, expressed as sigma of the Gaussian response.
#       it is Delta_lam/lam = Delta_v/c = FWHM/c = 2SQRT(2log2)/c, since
#       FWHM = 2*SQRT(2*log2) x sigma = 2.35 x sigma.
#       Therefore, since FWHM/c = Dlambda/lambda = 1/R, we have sigma*2.35 = c/R, i.e. 
        sigma = (10.**(logc-5)/spec_res)/(2*np.sqrt(2*np.log(2))) 
#     
# =============================================================================
#       Now make a smaller velocity array with the same velocity "resolution" as the steps in vel, above
        n = np.round(8.*sigma) # e.g. 1018km/s  if sigma=127.31km/s 
        # make sure that n is odd so there is a well defined central velocity...
        if (n % 2 == 0): 
            n = n + 1   #i.e. n=1019
#       create an array of n values in the range [-4*sigma,+4*sigma] in km/s, e.g. from -509km/s to +509km/s in this case   
        vel_kernel = np.arange(n) - np.floor(n/2.0) 
#     
# =============================================================================
#       create a normalized gaussian (unit area) with width=sigma
        gauss_kernel = (1/(np.sqrt(2*np.pi)*sigma)) * np.exp(-0.5*vel_kernel**2.0/sigma**2.0)
#     
# =============================================================================
#       convolve flux with gaussian kernel
        convol_flux = np.convolve(interp_flux, gauss_kernel , mode="same") 
        convol_wave = center_wave * (vel*10.**(-1*logc+5.0) + 1.0 ) # [micron] weirdly spaced, as derived from km/s
#     
# =============================================================================
#       and the real pixel scale 
        real_wave = np.arange(Npix_spec) * disp * 10.**(-4.)     #6000pix * 10A/pix * 1E-4mic/A  => [micron]
        real_wave = real_wave - real_wave[int(np.round(Npix_spec/2.))]   
        real_wave = real_wave + center_wave # [pixel]    print(real_wave)
#     
# =============================================================================
#       interpolate onto the pixel scale of the detector
        out_wave = real_wave
        out_flux = np.interp(real_wave , convol_wave, convol_flux)
        
        out = {"lam": out_wave, #[micron]
              "flux": out_flux} #same unit in input e.g. erg/cm2/s/micron
        
        return(out)
    
# =============================================================================
# =============================================================================
    
                            
         

# =============================================================================
# =============================================================================

    def plot_obs(self) :
        
        struct=self.spec_struct
        
# =============================================================================
# =============================================================================
#          ;make the structure into something useful
# =============================================================================
        wave_grid  = struct['wave']
        sn_index   = struct['plot_index']
        filt_index = struct['filt_index']
        tpSpecObs  = struct['tp']
        fltSpecObs = struct['filt']
        tranSpecObs= struct['tran']
        bkSpecObs  = struct['bk']
        signalSpecObs = struct['signal']
        noiseSpecObs=struct['noise']
        snSpecObs  = struct['sn']
        center     = struct['center']
        time       = struct['time']
        lineF      = struct['LineFlux']
        line_width = struct["line_width"]

     
        if ( (self.selected_PlotWavelengthRange.get() == 'Default') & (self.selected_FluxORmag.get() == 'Use magnitude') ):
#              xrange = np.array([ float(self.wl_0), float(self.wl_1) ]) 
              index=np.where(fltSpecObs > 0.05)
              xrange=[np.floor(min(wave_grid[index]*100))/100.,np.ceil(max(wave_grid[index]*100))/100. ]
              
              x = wave_grid
              y = fltSpecObs * time/max(fltSpecObs*time)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot(111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 

              a.plot(x[index], y[index],color='white')
              a.axis(xmin=xrange[0],xmax=xrange[1])
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        if ( (self.selected_PlotWavelengthRange.get() == 'Default') & (self.selected_FluxORmag.get() == 'Use Line Flux') ):
#              if ((len(xrange) == 1) and (xrange[0].item == 0)):
              index=np.where(abs(wave_grid-center) < .01)
              xrange=[np.floor(min(wave_grid[index]*100))/100.,np.ceil(max(wave_grid[index]*100))/100. ]
#              else:
                   # index=np.where((wave_grid < max(xrange)) & (wave_grid > min(xrange)))
#                    index = np.where(abs(wave_grid - center) < 10*line_width)[0]                  
                   # index = index[0]
       
              x = wave_grid
              y = signalSpecObs/max(signalSpecObs)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot()#111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
              
              a.plot(x[index], y[index],color='white') #no lines shown              
              #a.axis(xmin=xrange[0],xmax=xrange[1])
              a.axis(xmin=min(x[index]), xmax=max(x[index]))
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        if ( (self.selected_PlotWavelengthRange.get() == 'User set') & (self.selected_FluxORmag.get() == 'Use magnitude') ):
# 
              xrange = np.array([ float(self.Entry_lambdamin.get()), float(self.Entry_lambdamax.get())]) 
              index = np.where( (wave_grid > xrange[0]) & (wave_grid < xrange[1]) )
        
              x = wave_grid
              y = fltSpecObs * time/max(fltSpecObs*time)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot(111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 

              a.plot(x[index], y[index],color='white')
              a.axis(xmin=xrange[0],xmax=xrange[1])
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        if ( (self.selected_PlotWavelengthRange.get() == 'User set') & (self.selected_FluxORmag.get() == 'Use Line Flux') ):
              
#              if ((len(xrange) == 1) and (xrange[0].item == 0)):
              xrange = np.array([ float(self.Entry_lambdamin.get()), float(self.Entry_lambdamax.get())]) 
              index = np.where( (wave_grid > xrange[0]) & (wave_grid < xrange[1]) )
       
              x = wave_grid
              y = signalSpecObs/max(signalSpecObs)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot()#111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
              
              a.plot(x[index], y[index],color='white') #no lines shown              
              #a.axis(xmin=xrange[0],xmax=xrange[1])
              a.axis(xmin=min(x[index]), xmax=max(x[index]))
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)
              


# =============================================================================
#   ;*************************************
#   ;*************************************
#   ; plot the atmosphere and the throughput
#   ;*************************************
#   ;*************************************
#   
# =============================================================================
# =============================================================================
#   ;atmospheric trasparency
# =============================================================================
#               oplot, wave_grid, tranSpecObs, color=purple, thick=2
        line_tran, = a.plot(x[index], tranSpecObs[index],'m-',label='tran')
     
#   
# =============================================================================
# =============================================================================
#   ;throughput
# =============================================================================
#               oplot, wave_grid, tpSpecObs, color=green, thick=2
        line_tp, = a.plot(x[index], tpSpecObs[index],'g-',label="tp")

# =============================================================================
# =============================================================================
  
    
# =============================================================================
#   ;*************************************
#   ;*************************************
#   ; plot the sky and background spec
#   ;*************************************
#   ;*************************************
#   
# =============================================================================
# =============================================================================
#   ;instrumentally broadened night sky lines
# =============================================================================
        a.plot(x[index], np.sqrt(bkSpecObs[index])/(2*max(signalSpecObs[index])),'r-',label='sky res')
# #     
# =============================================================================
# =============================================================================
#   ;signal
# =============================================================================
        a.plot(x[index], signalSpecObs[index]/(2*max(signalSpecObs[index])),'b-',label='science')
#
# =============================================================================
        a.legend(bbox_to_anchor=(0.7, 0.97),
                        loc='upper left', borderaxespad=0.02)
        #a.legend(loc='best')
        self.printed_atmtrans = tranSpecObs[index]
        self.printed_background = bkSpecObs[index]     
        self.printed_throughput = tpSpecObs[index]
        self.printed_signal = signalSpecObs[index]
        self.printed_wavegrid = wave_grid[index]
        self.printed_noise = noiseSpecObs[index]
        self.printed_snr = snSpecObs[index]

# =============================================================================
# =============================================================================
#     
        a2 = a.twinx()
        #ax2.plot(t, s2, 'r.')
        a2.set_ylabel('photons/pixel')
        a2.axis(ymin=0, ymax=2*max(signalSpecObs[index]))
# =============================================================================

        canvas = FigureCanvasTkAgg(fig, master=self.frame_out)
        canvas.get_tk_widget().place(x=2, y=410, width=490, height=245)#pack()
        canvas.draw()

# =============================================================================
# # =============================================================================
# # # =============================================================================
# # # 
         
    def plot_snr(self):

        struct=self.spec_struct
        
        
# =============================================================================
# =============================================================================
#          ;make the structure into something useful
# =============================================================================
        wave_grid  = struct['wave']
        sn_index   = struct['plot_index']
        noiseSpecObs=struct['noise']
        snSpecObs  = struct['sn']
        tpSpecObs  = struct['tp']
        filt_index = struct['filt_index']
        signalSpecObs = struct['signal']
        bkSpecObs  = struct['bk']
        tranSpecObs= struct['tran']
        center     = struct['center']
        time       = struct['time']
        fltSpecObs = struct['filt']
        lineF      = struct['LineFlux']
        line_width = struct["line_width"]

     
        if ( (self.selected_PlotWavelengthRange.get() == 'Default') & (self.selected_FluxORmag.get() == 'Use magnitude') ):
#              xrange = np.array([ float(self.wl_0), float(self.wl_1) ]) 
              index=np.where(fltSpecObs > 0.05)
              xrange=[np.floor(min(wave_grid[index]*100))/100.,np.ceil(max(wave_grid[index]*100))/100. ]
              
              x = wave_grid
              y = fltSpecObs * time/max(fltSpecObs*time)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot(111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 

              a.plot(x[index], y[index],color='white')
              a.axis(xmin=xrange[0],xmax=xrange[1])
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        if ( (self.selected_PlotWavelengthRange.get() == 'Default') & (self.selected_FluxORmag.get() == 'Use Line Flux') ):
#              if ((len(xrange) == 1) and (xrange[0].item == 0)):
              index=np.where(abs(wave_grid-center) < .01)
              xrange=[np.floor(min(wave_grid[index]*100))/100.,np.ceil(max(wave_grid[index]*100))/100. ]
#              else:
                   # index=np.where((wave_grid < max(xrange)) & (wave_grid > min(xrange)))
#                    index = np.where(abs(wave_grid - center) < 10*line_width)[0]                  
                   # index = index[0]
       
              x = wave_grid
              y = signalSpecObs/max(signalSpecObs)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot()#111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
              
              a.plot(x[index], y[index],color='white') #no lines shown              
              #a.axis(xmin=xrange[0],xmax=xrange[1])
              a.axis(xmin=min(x[index]), xmax=max(x[index]))
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        if ( (self.selected_PlotWavelengthRange.get() == 'User set') & (self.selected_FluxORmag.get() == 'Use magnitude') ): 
              xrange = np.array([ float(self.Entry_lambdamin.get()), float(self.Entry_lambdamax.get())]) 
              index = np.where( (wave_grid > xrange[0]) & (wave_grid < xrange[1]) )
        
              x = wave_grid
              y = fltSpecObs * time/max(fltSpecObs*time)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot(111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 

              a.plot(x[index], y[index],color='white')
              a.axis(xmin=xrange[0],xmax=xrange[1])
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        if ( (self.selected_PlotWavelengthRange.get() == 'User set') & (self.selected_FluxORmag.get() == 'Use Line Flux') ):
              
#              if ((len(xrange) == 1) and (xrange[0].item == 0)):
              xrange = np.array([ float(self.Entry_lambdamin.get()), float(self.Entry_lambdamax.get())]) 
              index = np.where( (wave_grid > xrange[0]) & (wave_grid < xrange[1]) )
       
              x = wave_grid
              y = signalSpecObs/max(signalSpecObs)     
              fig = Figure(figsize=(6,6))
              a = fig.add_subplot()#111)
              fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
              
              a.plot(x[index], y[index],color='white') #no lines shown              
              #a.axis(xmin=xrange[0],xmax=xrange[1])
              a.axis(xmin=min(x[index]), xmax=max(x[index]))
              a.set_xlabel("Wavelength (micron)", fontsize=12)
              a.set_ylabel("Transmission", fontsize=12)

        import matplotlib.pyplot as plt 
        
        fig = Figure(figsize=(6,6))
        host = fig.add_subplot()#111)
        fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
        #fig, host = plt.subplots(figsize=(6,6)) # (width, height) in inches
        par1 = host.twinx()
        host.set_xlim( (x[index])[0], (x[index])[-1] ) 
        host.set_ylim(0, 1.3*max(snSpecObs))
        par1.set_ylim(0, 2*max(signalSpecObs[index]))

        host.set_xlabel("Wavelength (micron)", fontsize=12)
        host.set_ylabel("S/N per pixel")
        par1.set_ylabel("photons/pixel")

        color1 = "green" # plt.cm.viridis(0)
        color2 = "blue"  # plt.cm.viridis(0.5)
        color3 = "red"   # plt.cm.viridis(.9)

        p1, = host.plot( wave_grid[index], snSpecObs[index], color=color1, label="S/N")
        p2, = par1.plot( wave_grid[index], signalSpecObs[index], color=color2, label="signal")
        p3, = par1.plot( wave_grid[index], noiseSpecObs[index], color=color3, label="noise")

        lns = [p1, p2, p3]
        host.legend(handles=lns, loc='best')

#        fig.tight_layout()
            
        canvas = FigureCanvasTkAgg(fig, master=self.frame_out)
        canvas.get_tk_widget().place(x=2, y=410, width=490, height=245)#pack()
        canvas.draw()
        self.printed_atmtrans = tranSpecObs[index]
        self.printed_background = bkSpecObs[index]     
        self.printed_throughput = tpSpecObs[index]
        self.printed_signal = signalSpecObs[index]
        self.printed_wavegrid = wave_grid[index]
        self.printed_noise = noiseSpecObs[index]
        self.printed_snr = snSpecObs[index]

       

# =============================================================================
    def PrintToFile(self):
        values = [(ingredient, var.get()) for ingredient, var in  self.buttons.items()]
        if ( (values[0])[1] ) == 1:
            np.savetxt(self.results_path+'Throughput.txt', np.transpose([self.printed_wavegrid,self.printed_throughput]),fmt='%.3f, %.3f')
        if ( (values[1])[1] ) == 1:
            np.savetxt(self.results_path+'Transmission.txt', np.transpose([self.printed_wavegrid,self.printed_atmtrans]),fmt='%.3f, %.3f')
        if ( (values[2])[1] ) == 1:
            np.savetxt(self.results_path+'Background.txt', np.transpose([self.printed_wavegrid,self.printed_background]),fmt='%.3f, %.3f')
        if ( (values[3])[1] ) == 1:
            np.savetxt(self.results_path+'Signal.txt', np.transpose([self.printed_wavegrid,self.printed_signal]),fmt='%.3f, %.3f')
        if ( (values[4])[1] ) == 1:
            np.savetxt(self.results_path+'Noise.txt', np.transpose([self.printed_wavegrid,self.printed_noise]),fmt='%.3f, %.3f')
        if ( (values[5])[1] ) == 1:
            np.savetxt(self.results_path+'SNR.txt', np.transpose([self.printed_wavegrid,self.printed_snr]),fmt='%.3f, %.3f')


# =============================================================================
# # =============================================================================
# # =============================================================================
# =============================================================================



    def XTcalc(self):
        all_parameters = self.collect_all_parameters()
        WaterVapor_Value = self.selected_WaterVapor.get()
        all_parameters = self.collect_all_parameters()
        ready_to_go = self.validate(all_parameters)
        
        self.button_Calculate = Button(self.frame6, text="Calculate", command=self.XTcalc)

        self.button_Calculate.config(text="Processing...")
# =============================================================================
# =============================================================================
# # Convert all_parameters entries to more manageable entities
#
        band = all_parameters["bandpass"]
        slit_width = float(all_parameters["slit"])         #slit width in arcsec
        nExp = float(all_parameters["NrOfExp"])
        theta = float(all_parameters["AngularExt"])  #source angular extent in arcsec 
        Nreads = 1   #int(all_parameters["NrFowlerPairs"])
        lineWl = float(all_parameters["CentralWl"])   #Central Wl (in AA or micron)
        FWHM = float(all_parameters["FWHM"])
        z_line = float(all_parameters["LineRedshift"])
        mag =float(all_parameters["SourceMagnitude"])   
        z_spec = float(all_parameters["MagnitudeRedshift"])
        Vega_band = all_parameters["Vega_band"]
        SN = float(all_parameters["DesiredSNR"])
        time = float(all_parameters["TotalExpTime"])
        lineF = float(all_parameters['LineFlux'])
        
        line_width  = FWHM  #initial value, prevents crash when using magnitudes (i.e. no line width)
        
        print(self.slit_selected.get())
# =============================================================================
# =============================================================================
#       put everything in micron
#
        if ( (all_parameters["FluxORMag"] == "Use Line Flux") and (all_parameters["LineWlUnits"] == "Angstrom")):
           lineWl=lineWl/10000.0
#   
# =============================================================================
# =============================================================================
#   if the number of exposures is greater than 1, assume two dither positions
#
        if (nExp >1 ) :
           dither=2.0
        else: 
           dither=1.0   

# =============================================================================
# =============================================================================
#          the location of the code and the data spectra
#
        #homedir = os.getcwd() #+ '/XTcalc_dir'
       # mos_path = homedir + '/mosfire/'
        sky_path = self.homedir + '/Paranal_sky_VIS/'
        #tp_path = homedir + '/MosfireSpecEff/'
        #bk_path = homedir + '/MosfireSkySpec/'
        self.results_path = self.homedir + '/SAMOS_Results/'
 
# =============================================================================
# =============================================================================
#          MOSIFRE Linearity Limits
#
#          2.15 e/ADU gain
#          1% non linearity 26K ADU= 55900 electrons
#          5% non linearity 37K ADUs = 79550 e-
#          saturation 43K ADUs = 92450 e-
# # =============================================================================
# =============================================================================
#         one_per_limit = 55900   #to be revised
#         five_per_limit = 79550  #to be revised
        sat_limit = 92450       #to be revised
# =============================================================================
# 



# =============================================================================
# # 1. Throughput: 
# ################
# 
# =============================================================================
#1.1 Mirror coating
#==============================================================================
#0) Metals for telescope optics (and possibly other mirrors)
# Al from National Bureau of Standards, certainly optimistic
        Al_reflectivity = np.loadtxt(os.path.join(self.homedir,"coating_throughput","Al_reflectance_NBS.txt")) #lambda[nm], transmission
        Al_reflectivity[:,0] =  Al_reflectivity[:,0] * 1E-3 #nm -< [micron]
        Al_reflectivity_Wave = Al_reflectivity[:,0].astype(float)
        Al_reflectivity_Flux = Al_reflectivity[:,1].astype(float)
#Al_reflectivity.shape #(25,2)


# =============================================================================
# #New Values from Jack P. 3/12/2021
# =============================================================================
# =============================================================================
#         SAMOS_LowRed_Jack_wl = np.array([600, 625, 650, 675, 700, 725, 750, 775, 800, 825, 850, 875, 900, 925, 950]) * 1E-3 #;nm->[micron]
#         SAMOS_LowRed_Jack_th = np.array([29.2, 32.8, 35.7, 38.0, 38.5, 37.8, 37.3, 35.3, 33.2, 31.0, 29.2, 27.2, 24.1, 21.3, 18.9]) * 1E-2
#         SAMOS_LowRed_throughput = np.transpose(np.array([SAMOS_LowRed_Jack_wl,SAMOS_LowRed_Jack_th]))
#         SAMOS_LowRed_throughput_Wave = SAMOS_LowRed_throughput[:,0].astype(float)
#         SAMOS_LowRed_throughput_Flux = SAMOS_LowRed_throughput[:,1].astype(float)
#         
#         SAMOS_LowBlue_Jack_wl = np.array([400, 450, 500, 550, 600, 700, 770, 850, 950]) * 1E-3 #;nm->[micron]
#         SAMOS_LowBlue_Jack_th = np.array([30.5, 40.7, 46.9, 48.4, 47.0, 44.4, 40.6, 36.8, 34.8]) * 1E-2
#         SAMOS_LowBlue_throughput = np.transpose(np.array([SAMOS_LowBlue_Jack_wl,SAMOS_LowBlue_Jack_th]))
#         SAMOS_LowBlue_throughput_Wave = SAMOS_LowBlue_throughput[:,0].astype(float)
#         SAMOS_LowBlue_throughput_Flux = SAMOS_LowBlue_throughput[:,1].astype(float)
#         
#         SAMOS_HighRed_Jack_wl = np.array([600, 610, 620, 630, 640, 650, 660, 670, 680, 690, 700]) * 1E-3 #;nm->[micron]
#         SAMOS_HighRed_Jack_th = np.array([31.0, 33.6, 35.7, 37.1, 38.2, 38.4, 37.9, 36.5, 34.8, 32.4, 29.8]) * 1E-2
#         SAMOS_HighRed_throughput = np.transpose(np.array([SAMOS_HighRed_Jack_wl,SAMOS_HighRed_Jack_th]))
#         SAMOS_HighRed_throughput_Wave = SAMOS_HighRed_throughput[:,0].astype(float)
#         SAMOS_HighRed_throughput_Flux = SAMOS_HighRed_throughput[:,1].astype(float)
#         
#         SAMOS_HighBlue_Jack_wl = np.array([448, 45,    460,470,480,490,500,510,516]) * 1E-3 #;nm->[micron]
#         SAMOS_HighBlue_Jack_th = np.array([34.7, 35.4, 39.5, 41.4, 41.4,40.9, 38.4,35.4,33.8]) * 1E-2
#         SAMOS_HighBlue_throughput = np.transpose(np.array([SAMOS_HighBlue_Jack_wl,SAMOS_HighBlue_Jack_th]))
#         SAMOS_HighBlue_throughput_Wave = SAMOS_HighBlue_throughput[:,0].astype(float)
#         SAMOS_HighBlue_throughput_Flux = SAMOS_HighBlue_throughput[:,1].astype(float)
# 
# =============================================================================
        if band == "Low Red":
            SAMOS_throughput_Wave = self.SAMOS_LowRed_throughput_Wave
            SAMOS_throughput_Flux = self.SAMOS_LowRed_throughput_Flux     
        if band == "Low Blue":
            SAMOS_throughput_Wave = self.SAMOS_LowBlue_throughput_Wave
            SAMOS_throughput_Flux = self.SAMOS_LowBlue_throughput_Flux     
        if band == "High Red":
            SAMOS_throughput_Wave = self.SAMOS_HighRed_throughput_Wave
            SAMOS_throughput_Flux = self.SAMOS_HighRed_throughput_Flux     
        if band == "High Blue":
            SAMOS_throughput_Wave = self.SAMOS_HighBlue_throughput_Wave
            SAMOS_throughput_Flux = self.SAMOS_HighBlue_throughput_Flux     

        filt_wave = SAMOS_throughput_Wave 
        filt = SAMOS_throughput_Flux 

# =============================================================================
#          MOSIFRE Filters
#   
# =============================================================================
# 
#  ;read in the filter curve - wavlegth in microns
#  readcol, mos_path+'mosfire_'+band+'.txt', filt_wave, filt, format='f,f', /silent
# =============================================================================
#         filter_bandpass = np.loadtxt(mos_path+"mosfire_"+band+".txt")
#         filt_wave = filter_bandpass[:,0].astype(float)
#         filt = filter_bandpass[:,1].astype(float)
#         # just to be sure the wavelengths are increasing....
#         if filt_wave[0] > filt_wave[-1]:   
#             filt_wave = np.flip(filt_wave)
#             filt = np.flip(filt)
#  
# =============================================================================
# 
# =============================================================================
#         SOURCE SPECTRUM ENTERED BY THE USER?
#   
# =============================================================================
# 
# =============================================================================
#         if all_parameters["TypeOfSpectrum"] ==  "My own spectrum":
# ##          print(self.source_filename)
#             source_spectrum = np.loadtxt(self.source_fullpathfilename))
#  #           self.user_Wave = source_spectrum[:,0].astype(float)
#  #           self.user_Flux = source_spectrum[:,1].astype(float)
#             messagebox.showinfo(
#                 title='Check Flux Units!',
#                 message='wl[0] = '+str(user_Wave[0]) + '     Flux[0] = ' + str(self.user_Flux[0])
#                 )
#             
#             #MOSFIRE wants spectra in micron
# # =============================================================================
#             if all_parameters["SpectrumWlUnits"] == "Angstrom": 
#                 user_Wave = user_Wave/10000.0
#     
#             #Redshift is applied only to the wavelenghts
# # =============================================================================
#             user_Wave=user_Wave*(1+z)
#    
# # does the user spectrum cover the full band pass and are the wavelengths in micron?
# # =============================================================================
#             if ((min(user_Wave) > min(filt_wave)) or (max(user_Wave) < max(filt_wave))):
#             #ok=0
# #                warning = StringVar()
#                 warning = 'The read-in spectrum from ' + str(self.source_filename) \
#                       + 'does not span the full wavelength coverage of the ', band,' band ' \
#                       + 'or is not in the proper format. The correct format is ' \
#                       + 'observed-frame wavelength in micron or Angstroms and flux in ' \
#                       + 'erg/s/cm2 in two column format with a space or comma ' \
#                       + 'as the delimiter. Also please check that you have choosen the correct ' \
#                       + 'wavelength units on the GUI.'
#                 messagebox.showinfo(
#                     title='Check spectrum',
#                     message=warning
#                     )
# #              (PUT HERE AN INSTRUCTION TO RETURN?) 
# =============================================================================
        
# =============================================================================
# if the magnitude is entered in Vega, change it to AB.
# conversions for J,H,Ks from Blanton et al 2005
# K from ccs
# Y from CFHT WIRCam
#
# =============================================================================   
        if ( (all_parameters["FluxORMag"] == 'Use magnitude') and (all_parameters["Magnitude System"] == "Vega")):                                                                            
           if Vega_band == 'U': 
               mag=mag+0.79
           elif Vega_band == 'B':
               mag=mag-0.09 
           elif Vega_band == 'V':
               mag=mag+0.02 
           elif Vega_band == 'R':
               mag=mag+0.21 
           elif Vega_band == 'I':
               mag=mag+0.45
           elif Vega_band== 'Y': 
               mag=mag+0.66
           elif Vega_band == 'J':
               mag=mag+0.91 
           elif Vega_band == 'H':
               mag=mag+1.39 
           elif Vega_band == 'K':
               mag=mag+1.95 
           elif Vega_band == 'Ks':
               mag=mag+1.85
        
        
# =============================================================================
# *************************************
# *************************************
#          CONSTANTS
# *************************************
# *************************************
#     
# =============================================================================
    #the speed of light in cm/s
        logc = np.log10(29979245800.)
    
    #planck's constant in erg*s
        logh = np.log10(6.626068)-27
    
    #in log(erg cm)
        loghc = logc+logh
    
        f_nu_AB=48.59
    
# =============================================================================
# *************************************
# *************************************
#      SOAR and SAMOS CONSTANTS
# *************************************
# *************************************
#     
# =============================================================================
    #area of the telescope in cm^2
        AT=((400/2.)**2 * np.pi)
    
    #slit width used in arcsec to measure R_theta
        slit_W=0.1667*2,    # SAMOS DMD scale is 0.1667". Nominal slit width is 2 mirrors
    
    #spatial pixel scale in arcseconds/pixel
        pix_scale=0.1875375  #0.1667*1.125,    # spatial pixel scale [arcsec/px] - Sample 2 mirrors with 2.25 CCD pixels
    
    #dispersion pixel size
        pix_disp=0.24
    
    #Number of pixels in dispersion direction on the detector
        tot_Npix=4096.
    
    #Detector readnoise in electrons/pix CDS (correlated double sampling)
        det_RN=5.  #SAMI, TBC
    
    #number of elements
        Nelement=1 #superseeded by SAMOS throughput files.
    
    #number of SAM mirrors, silver coated
        N_SAM_mirrors=3.
    
    #number of windows
        Nwindow=1. #superseeded by SAMOS throughput files.
    
    
# =============================================================================
# *************************************
# *************************************
#          SKY CONSTANTS
# *************************************
# *************************************
# =============================================================================

# =============================================================================
# read in the atmospheric transparency
# From Gemini Observatory: Lord, S. D., 1992, NASA Technical Memorandum 103957
# default is 1.6mm water vapor column
# airmass=1
#      
# =============================================================================
# =============================================================================
#         vp = str( int( float(all_parameters["WaterVapor"])*10) )  # "1.0" => "10..."
#         am = str( int( float(all_parameters["Airmass"])*10) )
#         if all_parameters["AirmassORWaterVapor"] != "Use Default":
#             transpec='mktrans_zm_'+vp+'_'+am+'.dat'            
#             sky_spec='mk_skybg_zm_' + vp +'_'+ am +'_ph.dat'
#         else: # => DEFAULT
#             transpec='mktrans_zm_16_10.dat'  
#             sky_spec='mk_skybg_zm_16_10_ph.dat'
#         sky_transmission = np.loadtxt(sky_path+transpec)
#         sky_transmission_Wave = sky_transmission[:,0].astype(float)   #wl in micron, ok
#         sky_transmission_Flux = sky_transmission[:,1].astype(float)   # throughput 0-1, ok
# 
# =============================================================================
    
        #1.3 Atmospheric Transmission
        #==============================================================================
        sky_transmission = np.loadtxt(os.path.join(sky_path,"GenericTransmission_VIS.txt"),skiprows=1) #lambda[micron], transmission
        sky_transmission[:,0] = sky_transmission[:,0] *1E-4 # A => [micron]
        sky_transmission_Wave = sky_transmission[:,0].astype(float)
        sky_transmission_Flux = sky_transmission[:,1].astype(float)
#
        loghc = -15.701922659
        sky_spectrum = np.loadtxt(os.path.join(sky_path, "UVES_Fluxed_SkyALL.txt")) #lambda [A]; [erg/sec/cm2/A/arcsec2]
        sky_spectrum[:,0] = sky_spectrum[:,0] * 1E-4 #A -> [micron]
        sky_spectrum[:,1] = sky_spectrum[:,1] * (10.**(-loghc) * sky_spectrum[:,0] * 1E-4) # erg/sec/cm2/A/arcsec2 => [ph/sec/cm2/A/arcsec2]
        sky_spectrum[:,1] = sky_spectrum[:,1] * 1E4 * 1E-1  # [ph/sec/cm2/nm/arcsec2] => ph/sec/m2/nm/arcsec2
        sky_spectrum[:,1] = sky_spectrum[:,1] * 1E3 # ph/sec/m2/nm/arcsec2 => [ph/sec/m2/micron/arcsec2
        sky_spectrum_Wave = sky_spectrum[:,0].astype(float)
        sky_spectrum_Flux = sky_spectrum[:,1].astype(float)
        
# =============================================================================
#         # Infrared spectrum at MK or CP
#         sky_spectrum = np.loadtxt(sky_path+sky_spec)
#         sky_spectrum_Wave = sky_spectrum[:,0].astype(float)   #wl in Angstrom, bad...
#         sky_spectrum_Wave = sky_spectrum_Wave/1000            #wl in micron, GOOD
#         sky_spectrum_Flux = sky_spectrum[:,1].astype(float)   # throughput 0-1, ok
#         #unuts are  photons/sec/arcsec^2/nm/m^2
# 
# =============================================================================
        #MOSFIRE USES DIFFERENT BACKGROUND SPECTRA    
#        sky_spectrum = np.loadtxt(sky_path+band+'sky_cal_pA.sav.dat')
#        sky_spectrum_Wave = sky_spectrum[:,0].astype(float)   #wl in Angstrom, bad...
#        sky_spectrum_Flux = sky_spectrum[:,1].astype(float)   # throughput 0-1, ok

        # lam = sky_spectrum_Wave   #consistent with IDL
        #mksky = sky_spectrum_Flux 
                
        
# =============================================================================
#     *************************************
#     *************************************
#            MOSIFRE Throughput
#     *************************************
#     *************************************
#     
#     ;elem_AR = elment AR per surface
#     ;ref_mir = mirror reflectance
#     ;win_AR = window AR per surface
#     ;grat_eff: grating effciency
#     ;fil_tran: filter transmission
#     ;qe: quantum efficiency
#     ;disp: dispersion in angstroms/pixel
#     ;cent: central wavelength in micron
#     ;background in magnitudes per arcsecond^2
#     ;f_not: log of magnitude zero point in erg/s/cm^2/micron
#     ;dark current in electrons per second
#     ;rt: R-theta product: multiply by slit width to get resolution
#     ;SMRef: SOAR Mirror reflectance (placeholder only, as it is included in Silver throughput)
#     
# =============================================================================
    
        HighRedstat={
# =============================================================================
#             "elem_AR" :0.99, 
#             "ref_mir" :0.98, 
#             "win_AR": 0.988, 
#             "grat_eff": 0.72,
#             "fil_trans": 0.93, 
#             "qe": 0.88, 
#             "disp": 2.170, 
#             "lambda": 2.2, 
#             "background": 16, 
#             "f_not": np.log10(3.8)-7, 
            "dark": 0.005, 
#             "rt": 3620.0*slit_width, 
#             "SMRef":1.00 
# =============================================================================
            "disp": (7000.-5988.)/2876.0,    # dispersion [angstrom/px]
            "lambda": 0.6472,                # central wavelength [microns]
            "rt" : 8111. * 0.1667*2        # instrument["slit_W"] 
            }
    
        LowRedstat={
# =============================================================================
#             "elem_AR": 0.992, 
#             "ref_mir": 0.985, 
#             "win_AR": 0.985,  
#             "grat_efF": 0.65, 
#             "fil_trans": 0.95, 
#             "qe": 0.88, 
#             "disp": 1.629, 
#             "lambda": 1.65, 
#             "background": 16.6, 
#             "f_not": np.log10(1.08)-6, 
            "dark": 0.005, 
#             "rt": 3660.0*slit_width, 
#             "SMRef": 1.00
# =============================================================================
            "disp":  (6000.-4000.)/2875.0,    # dispersion [angstrom/px]
            "lambda":  0.7712,                # central wavelength [microns]
            "rt" : 2791. * 0.1667*2,       # instrument["slit_W"] 
            }
    
        HighBluestat={ 
# =============================================================================
#             "elem_AR": 0.985, 
#             "ref_mir": 0.98, 
#             "win_AR": 0.985, 
#             "grat_eff": 0.8,
#             "fil_trans": 0.9, 
#             "qe": 0.8, 
#             "disp": 1.303, 
#             "lambda": 1.25, 
#             "background": 16.8, 
#             "f_not": np.log10(2.90)-6, 
            "dark": 0.005, 
#             "rt":3310.0*slit_width, 
#             "SMRef": 1.00
# =============================================================================
            "disp":(5139.-4504.)/2876.0,    # dispersion [angstrom/px]
            "lambda":0.4803,                # central wavelength [microns]
            "rt": 9601. * 0.1667*2,        # instrument["slit_W"] 
            }
    
        LowBluestat={
# =============================================================================
#             "elem_AR": 0.985, 
#             "ref_mir": 0.98, 
#             "win_AR": 0.985, 
#             "grat_eff": 0.8,
#             "fil_trans": 0.9, 
#             "qe": 0.8, 
#             "disp": 1.086, 
#             "lambda": 1.05, 
#             "background": 17.3, 
#             "f_not": np.log10(7.45)-6, 
            "dark": 0.005, 
#             "rt": 3380.0*slit_width, 
#             "SMRef": 1.00 
# =============================================================================
            "disp": (9500.-6000.)/2874.0,    # dispersion [angstrom/px]
            "lambda": 0.4965,        # central wavelength [microns]
            "rt": 3137. * 0.1667*2,        # instrument["slit_W"] 


            }
    
# =============================================================================
        if (band == 'Low Blue'):
            stat=LowBluestat
        if (band == 'High Blue'):
            stat=HighBluestat 
        if (band == 'Low Red'): 
            stat=LowRedstat
        if (band == 'High Red'):
            stat=HighRedstat

    
# =============================================================================
# **************************
#     figure out the THROUGHPUT
# **************************
#     
# =============================================================================
# read in the throughput spectrum UPDATED 6/26/2012
# =============================================================================
# =============================================================================
#         throughput_table = np.loadtxt(tp_path+ band + 'eff.sm.dat')
#         tp_wave = throughput_table[:,0].astype(float)      #wl in Angstrom, bad...
#         tp_wave = tp_wave/10000           #wl in micron, GOOD
#         throughput = throughput_table[:,1].astype(float)      # throughput 0-1, ok
#         throughput[throughput<0] = 0     #set to zero possible negative values
# 
# =============================================================================

        tp_wave = SAMOS_throughput_Wave 
        throughput = SAMOS_throughput_Flux 

# =============================================================================
# number of Keck Mirrors (Primary and Secondary)
        N_SOAR_mirrors = 3
# =============================================================================
    
# =============================================================================
#     the total throughput is the instrument throughput
#     times the reflectance of the keck primary and secondary
#        throughput=throughput*stat["SMRef"]**(NKmir)
        th_SOAR_Wave = Al_reflectivity_Wave 
        th_SOAR_Flux = Al_reflectivity_Flux **(N_SOAR_mirrors)
##     
# =============================================================================
    
# =============================================================================
#     real FWHM resolution
        R=stat["rt"]/slit_width
#     
# =============================================================================

# =============================================================================
#     slit width in pixels along the dispersion direction
        swp=slit_width/pix_disp
#     
# =============================================================================

# =============================================================================
#     spectral coverage in micron)
        cov=tot_Npix*(stat["disp"]/10000.)
#    
# =============================================================================



# =============================================================================
# *************************************
# *************************************
#      Using a specific line flux
# *************************************
# *************************************
        #=> 9 Begin User Set line Flux
        if all_parameters["FluxORMag"] == 'Use Line Flux':
   
# =============================================================================
# =============================================================================
#          figure out the relavant wavelength range
#       
#           the observed line wavelength in micron
            center = lineWl * (1+z_line)   #lineWl*(1+z)
 
# =============================================================================
#             filter_limit_0 = min(filt_wave[np.where(filt>0.05)])
#             filter_limit_1 = max(filt_wave[np.where(filt>0.05)])
#             if ( (center < filter_limit_0) or (center > filter_limit_1 ) ):
#                messagebox.showerror(
#                  title=None, message="Central Wavelength " + str(center ) + " is out of bandpass \n changing redshift to match bandpass center")
#                center = 0.5 * (filter_limit_0 + filter_limit_1)
#                z_line = center/lineWl - 1   #new redshift
#                z_line = round(z_line,3)
#                self.Entry_LineRedshift.delete(0,END)
#                self.Entry_LineRedshift.insert(0,str(z_line))
#             self.Entry_RedshiftAdopted.delete(0,END)
#             self.Entry_RedshiftAdopted.insert(0,str(z_line))
#             #stat["lambda"] = center
# =============================================================================
               #self.root_exit() 
               
# =============================================================================         
# =============================================================================
#           resolution at the central wavelength in micron
            res = center/R
#       
# =============================================================================
#           the width of the spectral line before going through the spectrograph
            real_width = center*FWHM*10**(-logc+5)
#       
# =============================================================================
#     
#           the line width in micron that would be observed
            line_width = np.sqrt(real_width**2+res**2)
#       
# =============================================================================      
        #<= 9 END User Set line Flux
        #=> 9 Begin BROAD BAND FILTERS
        else: #   BROAD BAND FILTERS
    
# =============================================================================
# *********************************************
# *********************************************
#      we are calculating for a broad band flux: 
# *********************************************
# *********************************************
            center=stat["lambda"]
      
# =============================================================================
#       resolution at the central wavelength in micron
            res=center/R
#
# =============================================================================
        #<= 9 END BROAD BAND FILTERS
# =============================================================================



# =============================================================================
# # =============================================================================
# #
# #          DEGRADE RESOLUTION
# # 
# #     convolve the filter with bandpass resolution
# # =============================================================================
# # =============================================================================
# =============================================================================
# =============================================================================
        bandpass_degrade = self.degrade_resolution(wavelengths=np.array(filt_wave), 
                                    flux=np.array(filt), 
                                    center_wave=stat["lambda"], 
                                    spec_res=R, 
                                    disp = stat["disp"],
                                    px_tot = tot_Npix)
        
#       normalize the spectrum to find the relevant portions
        fltSpecObsNorm = np.array(bandpass_degrade["flux"])/max(np.array(bandpass_degrade["flux"]))
  
#        band_index = np.where(fltSpecObsNorm > 0.01)[0]
        band_index = np.where( (bandpass_degrade["lam"] >= filt_wave[0]) & (bandpass_degrade["lam"] <= filt_wave[-1]) )
        
        fltSpecObs = np.array(bandpass_degrade["flux"][band_index])
        
#       a tighter selection of the indexes with high throuhgput for the S/N
        filt_index=np.where(fltSpecObs > 0.05)[0]
        
        wave_grid = np.array(bandpass_degrade["lam"][band_index])
# 
# =============================================================================

# =============================================================================
# =============================================================================
        
        th_SOAR_degrade = self.degrade_resolution(wavelengths=th_SOAR_Wave, 
                                    flux = th_SOAR_Flux, 
                                    center_wave=stat["lambda"], 
                                    spec_res=R, 
                                    disp = stat["disp"],
                                    px_tot = tot_Npix)
#        th_tel_degrade_SpecObs = np.array(bandpass_degrade["flux"][band_index])
#        th_SOAR_degrade_Wave = th_SOAR_degrade["lam"][band_index]
        th_SOAR_degrade_Flux = th_SOAR_degrade["flux"][band_index]

# =============================================================================
# =============================================================================
#       the relavant portion of the spectrum
#        bandpass_index = np.where(fltSpecObs > 0.1)[0]
#        fltSpecObs=fltSpecObs[bandpass_index]
# =============================================================================
# =============================================================================
# #    
# =============================================================================
# =============================================================================
#       convolve the atm_Transmission spectrum with the resolution
#       mosfire_resolution, tran_lam, trans, stat.lambda, R, stat.disp, out_wave=wave_grid, out_flux=tranSpecObs
#
        atmtrans_degrade = self.degrade_resolution(wavelengths=sky_transmission_Wave, 
                                        flux= sky_transmission_Flux, 
                                        center_wave=stat["lambda"],  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
        tranSpecObs = np.array(atmtrans_degrade["flux"][band_index])   #2251 values     
# =============================================================================
# =============================================================================
#       convolve the throughput spectrum with the resolution
#
#        good = np.logical_and(tp_wave >= wave_grid[0],tp_wave <= wave_grid[-1])
#       tp_wave_selected = tp_wave#[good]
#        throughput_selected = throughput#[good]
        throughput_degrade = self.degrade_resolution(wavelengths=tp_wave,#_selected, 
                                        flux=throughput,#,_selected, 
                                        center_wave=stat["lambda"],  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
        tpSpecObs = np.array(throughput_degrade["flux"][band_index])  #2251 values
        v = tpSpecObs
        v2 = [0 if i < 0 else i for i in v]
        tpSpecObs = np.array(v2)


        SAMI_throughput_degrade = self.degrade_resolution(wavelengths=self.SAMI_CCD_throughput_Wave,#_selected, 
                                        flux=self.SAMI_CCD_throughput_Flux,#,_selected, 
                                        center_wave=stat["lambda"],  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
        SAMISpecObs = np.array(SAMI_throughput_degrade["flux"][band_index])  #2251 values
#        v = tpSpecObs
#        v2 = [0 if i < 0 else i for i in v]
#        tpSpecObs = np.array(v2)


# =============================================================================
# =============================================================================
#       convolve the background spectrum with the resolution
#
# =============================================================================
#        ;background in phot/sec/arcsec^2/nm/m^2
#        mosfire_resolution, lam, mksky, stat.lambda, R, stat.disp, out_wave=wave_grid, out_flux=raw_bkSpecObs
#        good = np.logical_and(sky_spectrum_Wave >= wave_grid[0],sky_spectrum_Wave <= wave_grid[-1])

        #sky_spectrum_Flux = sky_spectrum_Flux/(0.7*pix_scale*10.**(loghc+4.0))*sky_spectrum_Wave*10**(4.+1.)
 
#        sky_spectrum_Wave_selected = sky_spectrum_Wave#[good]
#        sky_spectrum_Flux_selected = sky_spectrum_Flux#[good]
        background_degrade = self.degrade_resolution(wavelengths=sky_spectrum_Wave,#_selected, 
                                        flux=sky_spectrum_Flux,#_selected, 
                                        center_wave=stat["lambda"],  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
        #for now - sent the filt_index to be the NONzero_index
        background_degrade["flux"][background_degrade["flux"]<0]=0
        raw_bkSpecObs  = background_degrade["flux"][band_index]  #2251
        #filt_index = np.where(raw_bkSpecObs>0)[0]
        #filt_index = band_index  #used later, to keep consistency...
 
    
 
# =============================================================================
# # =============================================================================
# #      Final THROGHPUT    
# #  
#        Atmosphere x SOAR Telescope x SAM-AO x SAMOS x SAMI    
# # =============================================================================
        tpSpecObs = tranSpecObs * th_SOAR_degrade_Flux * np.full(len(band_index),self.SAM_th) * tpSpecObs * SAMISpecObs                     
#  
# =============================================================================

# =============================================================================
# =============================================================================


# 
# =============================================================================
#     *************************************
#     *************************************
#     ;     Using a specific line flux
#     *************************************
#     *************************************
        #=> 9: USE LINE FLUX       
        if all_parameters["FluxORMag"] == 'Use Line Flux':
# =============================================================================
# =============================================================================
#     
#           the location inside the FWHM of the line
            line_index = np.where(abs(wave_grid - center) < 0.5*line_width)[0]
#       
# =============================================================================
#           the area used to calcclate the S/N
            sn_index=line_index
#       
# =============================================================================
# =============================================================================
#           ;now send the background spectrum through the telescope by
#           ;multiplying the throughput, the
#           ;slit_width, the angular extent (theta), the area of the
#           ;telescope, and the pixel scale in nm
#       
#           ;this gives phot/sec/pixel
            bkSpecObs = raw_bkSpecObs * tpSpecObs * slit_width *theta * (AT*10.**(-4)) * (stat["disp"]/10.0)
# =============================================================================
# =============================================================================
#       
#           ;determine the average background
#           ;within the FWHM of the line
#           ;in photons per second per arcsec^2 per nm per m^2
            mkBkgd=np.mean(sky_spectrum_Flux[np.where(abs(sky_spectrum_Wave - center) <= 0.5*line_width)])
#       
# =============================================================================
# =============================================================================
#       ;fv_back=mkBkgd*(center)^2*10^(-4+3-4-c)
#       
#       ;what does this correspond to in AB mags/arcsec^2
#       
#       ;go to erg/s/cm^2/Hz
#       ;10^-4 for m^2 to cm^2
#       ;10^3 for micron to nm
#       ;lam^2/c to covert from d(lam) to d(nu) (per Hz instead of per nm)
#       ;hc/lam to convert photons to ergs
            mag_back=-2.5*(np.log10(mkBkgd*center)-4+3+logh)-f_nu_AB
#       
# =============================================================================
# =============================================================================
#       ; the signal in electrons per second that will hit the telsecope
#       ; as it hits the atmosphere (ie need
#       ; to multiply by the throughput and
#       ; the atmospheric transparency
            signalATM = lineF * 10**(-17-loghc-4) * center * AT
#       
# =============================================================================
# =============================================================================
#       ;the width of the line in sigma - not FWHM
#       ;in micron
            sigma=line_width/(2*np.sqrt(2*np.log(2)))
#       
# =============================================================================
# =============================================================================
#       ;a spectrum version of the signal
#       ;phot per second per pixel (without atm or telescope)
#       ; ie total(signal_spec/signal) with
#       ; equal resolution of wave_grid /
#       ; stat.disp in micron
            signal_spec=signalATM*(1/(np.sqrt(2*np.pi)*sigma))*np.exp(-0.5*(wave_grid-center)**2/sigma**2)*stat["disp"]/10.**4
#       
# =============================================================================
# =============================================================================
#       ; the spectrum of the signal as detected
            sig_rateSpecObs=signal_spec * tpSpecObs * tranSpecObs
#       
#
# =============================================================================
# =============================================================================
# # #       SLIT LOSSES
# # =============================================================================
# =============================================================================
            if self.selected_GLAO.get() == "SAM": 
               beta = 3.   # ;appropriate from SAM, e-mail from Tokovinin; set =3 for VLT/FORS1 and =100 for a Gaussian profile
            else:
               beta = 10. 
            Nslit_X = round(float(self.slit_selected.get())/0.1667)
            Nslit_Y = round(theta*2/0.1667)
            #print(Nslit_X,Nslit_Y)
            slit_loss = self.slit_loss(theta,beta,Nslit_X,Nslit_Y)            
            #print(slit_loss)
            sig_rateSpecObs = sig_rateSpecObs * slit_loss

# =============================================================================
# =============================================================================
#       ; the number of pixels in the spectral direction
            nPixSpec = (line_width*10000.0)/stat["disp"]
#       
# =============================================================================
# =============================================================================
#       ;the spatial pixel scale
            nPixSpatial=theta/pix_scale
#       
# =============================================================================
# =============================================================================
#       ;The number of pixels per FWHM observed
            Npix= nPixSpec * nPixSpatial

# =============================================================================
        #<= 9: END USE LINE FLUX       
        #=> 9: BEGIN USE BROAD BAND    
# =============================================================================
        else: #use 
# =============================================================================
#       ;*************************************
#       ;*************************************
#       ; we are calculating for a broad band flux
#       ;*************************************
#       ;*************************************
#       
# =============================================================================
# =============================================================================
#       ; the area used to calculate the S/N
            sn_index=filt_index
#       
            mag_back=-2.5*(np.log10(np.mean(raw_bkSpecObs)*center)-4+3+logh)-f_nu_AB
#       
# =============================================================================
# =============================================================================
#       ;now send the background spectrum through the telescope by
#       ;multiplying the throughput, the
#       ;slit_width, the angular extent, the area of the
#       ;telescope, and the pixel scale in nm
#       
#       ;this gives phot/sec/pixel
            bkSpecObs = raw_bkSpecObs * tpSpecObs * slit_width * theta * (AT*10.0**(-4)) * (stat["disp"]/10.0)#       ;     bkSpecObs = raw_bkSpecObs * tpSpecObs * (0.5)^2 * (AT*10.^(-4)) * (stat.disp/10.0)
# =============================================================================
      
# =============================================================================
#       ;*************************************
#       ;*************************************
#       ; using the user input spectrum
#       ;*************************************
#       ;*************************************
       
             #=> 13: BEGIN USER SPECTRUM    

            if all_parameters["TypeOfSpectrum"] == "My own spectrum": 
# =============================================================================
# =============================================================================
                self.read_SourceSpectrum()
                #Redshift is applied only to the wavelenghts

# =============================================================================
                self.user_Wave=self.user_Wave*(1+z_spec)
# does the user spectrum cover the full band pass and are the wavelengths in micron?
# =============================================================================
                if ((min(self.user_Wave) > min(filt_wave)) or (max(self.user_Wave) < max(filt_wave))):
            #ok=0
#                warning = StringVar()
                    warning = 'The read-in spectrum from ' + str(self.source_filename) \
                      + 'does not span the full wavelength coverage of the ', band,' band ' \
                      + 'or is not in the proper format. The correct format is ' \
                      + 'observed-frame wavelength in micron or Angstroms and flux in ' \
                      + 'erg/s/cm2 in two column format with a space or comma ' \
                      + 'as the delimiter. Also please check that you have choosen the correct ' \
                      + 'wavelength units on the GUI.'
                    messagebox.showinfo(
                     title='Check spectrum',
                     message=warning
                    )
     
#         ;convolve with the resolution of mosfire
#         mosfire_resolution,  userWave, userFlux, stat.lambda, R, stat.disp, $
#           out_wave=user_wave_grid, out_flux=userSig
#         userSig=userSig[band_index]
                userSig_degrade = self.degrade_resolution(wavelengths=self.user_Wave, 
                                        flux= self.user_Flux, 
                                        center_wave=stat["lambda"],  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
                userSig = np.array(userSig_degrade["flux"][band_index])   #2251 values

#         
# =============================================================================
# =============================================================================
#         ;multiply by the normalized filter transmission        
                filt_shape = fltSpecObs/max(fltSpecObs)
                userSig = userSig*filt_shape

#         
# =============================================================================
# =============================================================================
                if self.selected_MagnitudeSystem.get() == 'AB':
                  df = self.read_ABfilters()
                  wl_um = df[:,0] / 10000.0   #in micron
                  tp   = df[:,1]
                  good_index  = np.where(tp > 0.05)
                  AB_filter_degrade = self.degrade_resolution(wavelengths=wl_um,#[good_index], 
                                        flux= tp,#[good_index],  
                                        center_wave=np.mean(wl_um),#[good_index]),  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
                  AB_filter_degrade = np.array(AB_filter_degrade["flux"])#[good_index])   #2251 values
                  Source_filter_degrade = self.degrade_resolution(wavelengths=wl_um, #[good_index], 
                                        flux= self.user_Flux, #[good_index],  
                                        center_wave=np.mean(wl_um),#[good_index]),  
                                        spec_res=R, 
                                        disp = stat["disp"], 
                                        px_tot = tot_Npix)
                  Source_filter_degrade = np.array(Source_filter_degrade["flux"])#[good_index])   #2251 values
                  Source_filter_degrade = Source_filter_degrade * AB_filter_degrade
#         ;make the total match the broad band magnitude
                  scale=10.0**(-0.4*(mag+f_nu_AB))/np.mean(Source_filter_degrade)
                else:
#         ;multiply by the normalized filter transmission        
                  filt_shape = fltSpecObs/max(fltSpecObs)
                  userSig = userSig*filt_shape#         
#         ;make the total match the broad band magnitude
                  scale=10.0**(-0.4*(mag+f_nu_AB))/np.mean(userSig)
# =============================================================================
# =============================================================================
#         ;raw fv spec
                raw_fv_sig_spec = userSig*scale
#         
# =============================================================================       
# =============================================================================
#         ;convert to flux hitting the primary in flux hitting the primary in
#         ;phot/sec/micron (if the earth had no atmosphere)
#         ;phot/sec/micron = fnu * AT / lam / h
                signal_spec=raw_fv_sig_spec*10.**(-1*logh)*AT / wave_grid
#         
# =============================================================================        
# =============================================================================
#         ;*************************************
#         ;*************************************
#         ; using a flat F_nu spec (DEFAULT)
#         ;*************************************
#         ;*************************************
            else:
#              
# =============================================================================
# =============================================================================
             
#         ;fv=10^((-2/5)*MagAB-48.59) (erg/s/cm^2/Hz)
#         ;convert to flam: flam=fv*c/lam^2 (erg/s/cm^2/micron)
#         ;covert to photons: phot/sec/micron = fnu * AT / lam / h
#         
#         ;flux hitting the primary in
#         ;phot/sec/micron (if the earth had no atmosphere)
              signal_spec=10.0**(-0.4*(mag+f_nu_AB)-logh) * AT / wave_grid
#         
# =============================================================================
#        ; newSpec=10.0^(-0.4*(mag[0]+f_nu_AB)) * wave_grid/wave_grid
        
            
# =============================================================================
#       ;multiply by the atmospheric transparency
            signal_spec=signal_spec * tranSpecObs
#       
# =============================================================================
# =============================================================================
#       ; now put it through the throughput of the telescope
#       ; phot/sec/micron
            sig_rateSpecObs= signal_spec * tpSpecObs
#       
#
# =============================================================================
# =============================================================================
# # #       SLIT LOSSES
# # =============================================================================
# =============================================================================
#           beta = 2.   # ;appropriate from SAM, e-mail from Tokovinin; set =3 for VLT/FORS1 and =100 for a Gaussian profile
            if self.selected_GLAO.get() == "SAM": 
               beta = 3.   # ;appropriate from SAM, e-mail from Tokovinin; set =3 for VLT/FORS1 and =100 for a Gaussian profile
            else:
               beta = 10. 
            Nslit_X = round(float(self.slit_selected.get())/0.1667)
            Nslit_Y = round(theta*2/0.1667)
           #print(Nslit_X,Nslit_Y)
            slit_loss = self.slit_loss(theta,beta,Nslit_X,Nslit_Y)            
           #print(slit_loss)
            sig_rateSpecObs = sig_rateSpecObs * slit_loss

# =============================================================================
# =============================================================================
#       ; now for phot/sec/pix multiply by micron/pix
            sig_rateSpecObs=sig_rateSpecObs * (stat["disp"]/10000.0)
#       
# =============================================================================
# =============================================================================
#       ;number of pixels per resolution element in the spectral direction
            nPixSpec = (res*10000.0)/stat["disp"]
#       
# =============================================================================
# =============================================================================
#       ;the spatial pixel scale
            nPixSpatial=theta/pix_scale
#       
# =============================================================================
# =============================================================================
#       ;The number of pixels per FWHM observed
            Npix= nPixSpec * nPixSpatial     
# =============================================================================
      
      
# =============================================================================
#         ;*************************************
#         ;*************************************
#         ; Determine EXP TIME ...
#         ;*************************************
#         ;*************************************         

        if all_parameters["ExpTimeORSNR"] == 'Determine Exposure Time':
    
# =============================================================================    
# =============================================================================
#       ; differentiate between total exposure time
#       ; and amount of time of individual exposures
#       
#       ;     ; figure out how long it takes
#       ;     qb=bkSpecObs + stat.dark*nPixSpatial + sig_rateSpecObs
#       ;     qa=-nPixSpec * sig_rateSpecObs^2/SN[0]^2
#       ;     qc=det_RN^2/Nreads*nPixSpatial
#       
#       ; figure out how long it takes
#       
#       ;if calulating with a line flux, assume S/N over the line
#       ; other wise, S/N per spectral pixel
           if all_parameters["FluxORMag"] == 'Use Line Flux':
              qa=-nPixSpec * sig_rateSpecObs**2/SN**2 
           else:
              qa=-sig_rateSpecObs**2/SN**2
#       
# =============================================================================
           qb = dither*bkSpecObs + dither*stat["dark"]*nPixSpatial + sig_rateSpecObs
           qc = dither*det_RN**2/Nreads*nPixSpatial*nExp
      
           timeSpec=(-qb -np. sqrt( qb**2 - 4*qa*qc ))/(2*qa)
      
           time=np.median(timeSpec[sn_index])
      
           time=float(time)
      
# =============================================================================
# =============================================================================
# #    ; Determine the signal to noise
# #     
# =============================================================================
#     ; noise contributions
#     ; poisson of background
#     ; poisson of dark current
#     ; poisson of the signal
#     ; read noise
#     
# =============================================================================    
# =============================================================================
#     ;the noise per slit length in the spatial direction
#     ; and per pixel in the spectral direction
#     
#     ; the noise spectrum:
#     ; Poisson of the dark
#     ; current, signal, and background + the read noise"
#     
        noiseSpecObs = np.sqrt( sig_rateSpecObs*time + dither*( (bkSpecObs +stat["dark"]*nPixSpatial)*time + det_RN**2/Nreads*nPixSpatial*nExp))
#       
# =============================================================================     
#    ;  noiseSpecObs = sqrt((bkSpecObs +stat.dark*nPixSpatial + sig_rateSpecObs)*time[0] +det_RN^2/Nreads*nPixSpatial)
    
        signalSpecObs =  sig_rateSpecObs * time
    
        snSpecObs = signalSpecObs / noiseSpecObs
    
        stn = np.mean(np.sqrt(nPixSpec) * snSpecObs[sn_index])
    
# =============================================================================
#     ;the electron per pixel spectrum
        eppSpec=noiseSpecObs**2/nPixSpatial
#     
# =============================================================================

# =============================================================================
#     ;*************************************
#     ;*************************************
#     ;       values to be printed
#     ;*************************************
#     ;*************************************
#     
# =============================================================================
# =============================================================================
#     ;the mean instrument+telescope throughput in the same band pass
#        tp = np.mean( np.array(tpSpecObs)[sn_index.astype(int)])
        tp = np.mean(tpSpecObs[sn_index])
#     
# =============================================================================
# =============================================================================
#     ;maximum electron per pixel
        max_epp=int(np.round(max(eppSpec[sn_index]/nExp),0))
#     
# =============================================================================
# =============================================================================
#     
#     ;if calulating a line flux, S/N per FWHM
#     ;ie S/N in the line
#     
        if all_parameters["FluxORMag"] == 'Use Line Flux':
#     
# =============================================================================
# =============================================================================
#       ;over the line (per FWHM)
           stn = np.mean(np.sqrt(nPixSpec) * snSpecObs[sn_index])
#       
# =============================================================================
# =============================================================================
#       ;signal in e/FWHM
           signal = np.mean(sig_rateSpecObs[sn_index])*nPixSpec*time
#       
# =============================================================================
# =============================================================================
#       ;sky background in e/sec/FWHM
           background = np.mean(bkSpecObs[sn_index])*nPixSpec*time
#       
# =============================================================================
# =============================================================================
#       ;Read noise for multiple reads, electrons per FWHM
           RN=det_RN/np.sqrt(Nreads)*np.sqrt(Npix)*np.sqrt(nExp)
#       
# =============================================================================
# =============================================================================
#       ;noise per FWHM
           noise=np.mean(noiseSpecObs[sn_index])*np.sqrt(nPixSpec)
#       
# =============================================================================
# =============================================================================
#       ;e-
           dark=stat["dark"]*Npix*time
#       
# =============================================================================
      
# =============================================================================
#         ;*************************************
#         ;*************************************
#         ; ...Determine SNR
#         ;*************************************
#         ;*************************************         
      
        else:

# =============================================================================
# =============================================================================
#       ;we are computing S/N per pixel for a continuum source
#       
#       ;per spectral pixel
           stn = np.median(snSpecObs[sn_index])
#       
# =============================================================================
# =============================================================================
#       ;signal in e/(spectral pixel)
           signal = np.median(sig_rateSpecObs[sn_index])*time
#       
# =============================================================================
# =============================================================================
#       ;sky background in e/(spectral pixel)
           background = np.median(bkSpecObs[sn_index])*time
#       
# =============================================================================
# =============================================================================
#       ;Read noise for multiple reads, electrons per spectral pixel
           RN=det_RN/np.sqrt(Nreads)*np.sqrt(nPixSpatial)*np.sqrt(nExp)
#       
# =============================================================================
# =============================================================================
#       ;noise per spectral pixel
           noise=np.median(noiseSpecObs[sn_index])
#       
# =============================================================================
# =============================================================================
#       ;e- per spectral pixel
           dark=stat["dark"]*nPixSpatial*time
#       
# =============================================================================
    
    
     
# =============================================================================
#     ;*************************************
#     ;*************************************
#     ;      display the results
#     ;*************************************
#     ;*************************************
#     
# =============================================================================
    
        GUI = True
        if GUI == True:
            #Summary of results, in dictionary 
            summary_struct = dict()
            summary_struct["quant"] = ['Wavelength', 'Resolution','Dispersion', 'Throughput', 'Signal', 'Sky Background', 
                                       'Sky brightness', 'Dark Current', 'Read Noise', 'Total Noise','S/N', 
                                       'Total Exposure Time', 'Max e- per pixel']

            if ( (all_parameters["FluxORMag"] == "Line Flux") and (lineWl > 0) ):
                summary_struct["unit"] = ['micron','FWHM in angstrom', 'angstrom/pixel', '',  'electrons per FWHM', 
                                          'electrons per FWHM', 'AB mag per sq. arcsec', 'electrons per FWHM', 
                                          'electrons per FWHM', 
                                          'electrons per FWHM',
                                          'per observed FWHM', 'seconds', 'electrons per pixel per exp']                                     
            else:
                summary_struct["unit"] = ['micron','angstrom', 'angstrom/pixel', '',  'electrons per spectral pixel',
                                              'electrons per spectral pixel', 'AB mag per sq. arcsec', 'electrons per spectral pixel', 
                                              'electrons per spectral pixel', 'electrons per spectral pixel',
                                              'per spectral pixel', 'seconds', 'electrons per pixel']


            if max_epp >= 1e10:
                max_epp_string = "> 1e10"
            else:
                max_epp_string = max_epp
                
                #checking if the signal is saturating the detector
            if max_epp > sat_limit:
                messagebox.showerror(title=None,message="Detector saturated! \n\n     Try to increase Nexp...")
#                print("Detector Saturated!")
# =============================================================================
#     #
#     #for IR detector do a check on the non linearity thresholds
#     #---------------------------------------------------------------
#     #elif (max_epp > telescope["five_per_limit"]) & (max_epp < instrument["sat_limit"]):
#     #    print("Detector in >5 percent unlinear regime")
#     #elif (max_epp > telescope["one_per_limit"]) & (max_epp < instrument["five_per_limit"]):
#     #    print("Detector in 1 - 5 percent nonlinear regime")
            else:
                pass
# 
# =============================================================================
    
            summary_struct["value"] = [np.round(center,4),#stat["lambda"],4),
                    np.round(res * 1e4,1),
                    np.round(stat['disp'],2),
                    np.round(tp,2),         #avg_throughput,
                    np.round(signal,2),      #signal_print,
                    np.round(background,2),             #background_print,
                    np.round(mag_back,2),      #bkg_mag,
                    np.round(dark,2),          #dark_print,
                    np.round(RN,2),            #RN_print,6),
                    np.round(noise,2),         #noise_print,6),
                    np.round(stn,2),
                    np.round(time,2),          #exp_time,6),
                    max_epp_string
                    ]


    ## Actual output containing the spectrum (for graphing purposes) --------------
            self.spec_struct = dict()
        
            self.spec_struct["wave"] = wave_grid #background_degrade["lam"]
            self.spec_struct["center"] = center#stat["lambda"]
            self.spec_struct["plot_index"] = sn_index
            self.spec_struct["filt_index"] = filt_index
            self.spec_struct["tp"] = tpSpecObs #throughput_degrade["flux"]
            self.spec_struct["filt"] = fltSpecObs #bandpass_degrade["flux"]
            self.spec_struct["tran"] = tranSpecObs
        #    spec_struct["bk"] = background_degrade["flux"]
            self.spec_struct["bk"] = bkSpecObs * time  #background_final * exp_time # [electrons/pixel]
        #    spec_struct["sig"] = signal_spectrum # phot/sec/micron #not needed
            self.spec_struct["signal"] =   signalSpecObs # signal_final # electrons/pixel -> signal_space * exp_time
            self.spec_struct["noise"] = noiseSpecObs  # noise 
            self.spec_struct["sn"] = snSpecObs   #  SNR
            self.spec_struct["LineFlux"] = all_parameters["LineFlux"]
            self.spec_struct["time"] = time
            
            self.spec_struct["line_width"] = line_width

      
        
        
        
# =============================================================================
#           widget_control, GUI.table, set_value=out_struct
#           
#           ;turn the max e- per pixel red if the detector has saturated
#           color_bkgrd=fltarr(3,13*3)+255
#           if (max_epp gt sat_limit) then color_bkgrd[1:2,36:38]=0 else $
#             if (max_epp gt five_per_limit) then begin
#             color_bkgrd[2,36:38]=0
#             color_bkgrd[1,36:38]=140
#           endif else $
#             if (max_epp gt one_per_limit) then color_bkgrd[2,36:38]=0
#             
#           widget_control, GUI.table, BACKGROUND_COLOR=color_bkgrd
#           
            self.text_SAMOS_Header.delete('1.0',END)
            if all_parameters["ExpTimeORSNR"] ==  'Determine Exposure Time':
#               Longstring=             "*****************************************\n" 
#                Longstring=Longstring + "             MOSFIRE XTCalc              \n"
#                Longstring=Longstring + "*****************************************\n" 
                # Longstring=#Longstring + 
                #Longstring=Longstring + "*****************************************\n" 
                Longstring = "Calculation for a signal to noise ratio of " + str(np.round(stn,3)) +"\n"
                Longstring=Longstring + "through a "+all_parameters["slit"]+" arcsecond slit in "+ all_parameters["bandpass"]+" band"
                self.text_SAMOS_Header.insert(INSERT,Longstring)
            if all_parameters["ExpTimeORSNR"] ==  'Determine Signal to Noise':
#                Longstring2=             "*****************************************\n" 
#                Longstring2=Longstring2 + "             MOSFIRE XTCalc              \n"
#                Longstring2=Longstring2 + "*****************************************\n" 
                #Longstring2=#Longstring2 + 
                Longstring2="Calculation for a " + all_parameters["TotalExpTime"] + " s total integration time \n"
                Longstring2=Longstring2 + "through a "+all_parameters["slit"]+" arcsecond slit in "+ all_parameters["bandpass"]+" band"
                self.text_SAMOS_Header.insert(INSERT,Longstring2)
                

#           endif else begin
#             Longstring=["*****************************************",$
#               "             MOSFIRE XTCalc              ",$
#               "*****************************************",$
#               String(Format='("Calculation for a ",(f0.2)," second integration ")', time),$
#               String(Format='("through a ",(f0.1)," arcsecond slit in ",(A)," band")',slit_width,band)]
#           endelse   
#                
# =============================================================================
            for item in self.set.get_children():
                self.set.delete(item) 
# =============================================================================
#             self.set.insert(parent='',index='end',iid=4,text='',values=('1010','john','Gold'))
# #            self.set.insert(parent='',index='end',iid=1,text='',values=('1020','jack',"Silver"))
# #            self.set.insert(parent='',index='end',iid=2,text='',values=('1030','joy','Bronze'))       
#             for each in  summary_struct["quant"]:
#                 print(each)
#                 
#             #Create list of 'id's
#             listOfEntriesInTreeView=treeview.get_children()
# 
#             for each in listOfEntriesInTreeView:
#                 print(treeview.item(each)['values'][col])  #e.g. prints data in clicked cell
#                 treeview.detach(each) #e.g. detaches entry from treeview
#                 
# =============================================================================
            for i in  range(len(summary_struct["quant"])):
                self.set.insert(parent='',index='end',iid=i,text='',
                                values=(summary_struct["quant"][i],
                                        summary_struct["value"][i],
                                        summary_struct["unit"][i]) )  
                
                
# =============================================================================
#             #x= np.array ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
#             #v= np.array ([16,16.31925,17.6394,16.003,17.2861,17.3131,19.1259,18.9694,22.0003,22.81226])
#             #p= np.array ([16.23697,     17.31653,     17.22094,     17.68631,     17.73641 ,    18.6368,
#             #            19.32125,     19.31756 ,    21.20247  ,   22.41444   ,  22.11718  ,   22.12453])
# 
#             x=spec_struct["wave"] 
#             y=spec_struct["plot_index"]           
#             fig = Figure(figsize=(6,6))
#             a = fig.add_subplot(111)
#             #a.scatter(x,v,color='red')
#             a.plot(x, y,color='blue')
#             a.invert_yaxis()
# 
#            # a.set_title ("Estimation Grid", fontsize=16)
#             a.set_ylabel("transmission", fontsize=14)
#             a.set_xlabel("Wavelength (micron)", fontsize=14)
# 
#             canvas = FigureCanvasTkAgg(fig, master=self.frame_out)
#             canvas.get_tk_widget().place(x=2, y=450, width=490, height=250)#pack()
#             canvas.draw()
#     
# =============================================================================
    

# =============================================================================
            self.Entry_lambdamin.configure(state='normal')
            self.Entry_lambdamax.configure(state='normal')
            if self.selected_PlotWavelengthRange.get() == 'Default':
                self.Entry_lambdamin.delete(0, END)
                self.Entry_lambdamax.delete(0, END)
                self.wl_0 = wave_grid[0] # background_degrade["lam"][0]
                self.wl_0 = f"{self.wl_0:,{'.3f'}}"
                self.wl_1 = wave_grid[-1] #background_degrade["lam"][-1]
                self.wl_1 = f"{self.wl_1:,{'.3f'}}"
#            self.Entry_lambdamin.insert(0,self.wl_0) 
#            self.Entry_lambdamax.insert(0,self.wl_1) 
                index = np.where(abs(wave_grid - center) < 10*line_width)[0]
                lambdamin = f"{min(wave_grid[index]):,{'.3f'}}"
                lambdamax = f"{max(wave_grid[index]):,{'.3f'}}"
            else: 
                lambdamin  = float(self.Entry_lambdamin.get())
                lambdamax  = float(self.Entry_lambdamax.get())
                self.Entry_lambdamin.delete(0, END)
                self.Entry_lambdamax.delete(0, END)
            self.Entry_lambdamin.insert(0,lambdamin) 
            self.Entry_lambdamax.insert(0,lambdamax) 
            self.Entry_lambdamin.configure(state='disabled')
            self.Entry_lambdamax.configure(state='disabled')
            
# 
# =============================================================================
            if self.selected_PlotObsORSNR.get() == "Plot Observations":
#               print( "Plot Observations")
               self.plot_obs()
            else:
               self.plot_snr()
               
        self.button_Calculate.config(text="Calculate")
        print('calculation completed')    

 
    def root_exit(self):
       root.quit()#destroy() 
# 
# =============================================================================

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("1000x740")
        parent.title("SAMOS Specroscopic ETC at SOAR")
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
        help_menu.add_separator()

        return menubar


# Create a GUI root
#root = Tk()
#mywin=MainWindow(root)
        
# Give a title to your self
#root.title("XTCak=lk")
# size of the window
#root.geometry("1000x720")   
        
# Make the loop for displaying root
#root.mainloop()
