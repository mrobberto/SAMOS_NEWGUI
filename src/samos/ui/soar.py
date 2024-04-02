"""
SAMOS SOAR tk Frame Class
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
from samos.motors import PCM
from samos.soar.Class_SOAR import Class_SOAR
from samos.astrometry.tk_class_astrometry_V5 import Astrometry
from samos.hadamard.generate_DMD_patterns_samos import make_S_matrix_masks, make_H_matrix_masks
from samos.system import WriteFITSHead as WFH
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters
from samos.system.SlitTableViewer import SlitTableView as STView
from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


class SOARPage(ttk.Frame):
    """ to be written """

    def __init__(self, parent, container, **kwargs):
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

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame("GSPage"))        
        help_menu.add_separator()

        return menubar
