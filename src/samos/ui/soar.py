"""
SAMOS SOAR tk Frame Class
"""
import copy
import csv
from datetime import datetime
from functools import partial
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
from tkinter.scrolledtext import ScrolledText
import customtkinter

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

from .common_frame import SAMOSFrame, check_enabled


class SOARPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SOAR", **kwargs)
        self.initialized = False

        # Initialization Button
        w = ttk.Button(self.main_frame, text="Initialize", command=self.way)
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Offset
        w = ttk.Button(self.main_frame, text="Get Offset", command=partial(self.Offset_option_TCS, ""))
        w.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.offset = tk.StringVar(self, "E 0.00 N 0.00")
        w = ttk.Entry(self.main_frame, textvariable=self.offset, width=12)
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(self.main_frame, text="Move to Offset", command=partial(self.Offset_option_TCS, "MOVE"))
        w.grid(row=1, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Focus
        w = ttk.Button(self.main_frame, text="Get Focus", command=partial(self.Focus_option_TCS, "STATUS"))
        w.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.focus = tk.DoubleVar(self, 0.)
        w = ttk.Entry(self.main_frame, textvariable=self.focus, width=12)
        w.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        focus_options = ["Relative", "Absolute"]
        self.focus_option = tk.StringVar(self, focus_options[0])
        w = ttk.OptionMenu(self.main_frame, self.focus_option, *focus_options)
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(self.main_frame, text="Change Focus", command=partial(self.Focus_option_TCS, "MOVE"))
        w.grid(row=2, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # CLM
        w = ttk.Button(self.main_frame, text="Get CLM", command=partial(self.CLM_option_TCS, "STATUS"))
        w.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.clm = tk.StringVar(self, "IN")
        w = customtkinter.CTkSwitch(self.main_frame, textvariable=self.clm, command=partial(self.CLM_option_TCS, "SET"), 
                                    variable=self.clm, onvalue="IN", offvalue="OUT")
        w.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Guider
        w = ttk.Button(self.main_frame, text="Get Guider", command=partial(self.Guider_option_TCS, "STATUS"))
        w.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.guider = tk.StringVar(self, "DISABLED")
        w = customtkinter.CTkSwitch(self.main_frame, textvariable=self.guider, command=partial(self.Guider_option_TCS, "SET"), 
                                    variable=self.guider, onvalue="ENABLED", offvalue="DISABLED")
        w.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Whitespot


        self.Whitespot_status = tk.StringVar()
        # initializing the choice, i.e. Python
        self.Whitespot_status.set("OFF")
        status = ["ON", "OFF"]
        ttk.Label(self.main_frame,
                 text="Whitespot % :",
                 justify=tk.LEFT).place(x=4, y=190)
        self.Whitespot_percentage = tk.StringVar()
        self.Whitespot_percentage.set("50")
        entry_Whitespot_percentage = ttk.Entry(
            self.main_frame, textvariable=self.Whitespot_percentage, width=4)
        entry_Whitespot_percentage.place(x=130, y=186)
        button_Whitespot_Enable = ttk.Radiobutton(self.main_frame,
                   text=status[0],
                   variable=self.Whitespot_status,
                   command=partial(self.Whitespot_option_TCS, status[0]),
                   value="ON").place(x=200, y=190)
        button_Whitespot_Disable = ttk.Radiobutton(self.main_frame,
                   text=status[1],
                   variable=self.Whitespot_status,
                   command=partial(self.Whitespot_option_TCS, status[1]),
                   value="OFF").place(x=300, y=190)
        button_Whitespot_STATUS = ttk.Button(
            self.main_frame, text="STATUS", command=partial(self.Whitespot_option_TCS, "STATUS"))
        button_Whitespot_STATUS.place(x=400, y=190)

        self.Lamp_LN_status = tk.StringVar()
        self.Lamp_LN_status.set("OFF")  # initializing the choice, i.e. Python
        status = ["ON", "OFF"]
        ttk.Label(self.main_frame,
                 text="Lamp L# %:",
                 justify=tk.LEFT).place(x=4, y=220)
        self.Lamp_number = tk.StringVar()
        self.Lamp_percentage = tk.StringVar()
        self.Lamp_number.set("L2")
        self.Lamp_percentage.set("50")
        entry_Lamp_number = ttk.Entry(
                self.main_frame, textvariable=self.Lamp_number,  width=4)
        entry_Lamp_number.place(x=90, y=216)
        entry_Lamp_percentage = ttk.Entry(
                self.main_frame, textvariable=self.Lamp_percentage, width=4)
        entry_Lamp_percentage.place(x=130, y=216)
        button_Lamp_Enable = ttk.Radiobutton(self.main_frame,
                text=status[0],
                variable=self.Lamp_LN_status,
                command=partial(self.Lamp_LN_option_TCS, status[0]),
                           value="ON").place(x=200, y=220)
        button_Lamp_Disable = ttk.Radiobutton(self.main_frame,
                           text=status[1],
                           variable=self.Lamp_LN_status,
                           command=partial(self.Lamp_LN_option_TCS, status[1]),
                           value="OFF").place(x=300, y=220)
        button_Lamp_STATUS = ttk.Button(
                    self.main_frame, text="STATUS", command=partial(self.Lamp_LN_option_TCS, "STATUS"))
        button_Lamp_STATUS.place(x=400, y=220)

        ttk.Label(self.main_frame,
                 text="ADC %:",
                 justify=tk.LEFT).place(x=4, y=250)
#        button_ADC_MOVE = ttk.Button(
#            self.main_frame, text="ADC MOVE %", command=partial(self.ADC_option_TCS, "MOVE"))
#        button_ADC_MOVE.place(x=4, y=250)
        self.ADC_MOVE_msg = tk.StringVar()
        self.ADC_MOVE_msg.set("0.0")
        entry_ADC_MOVE = ttk.Entry(
            self.main_frame, textvariable=self.ADC_MOVE_msg, width=4)
        entry_ADC_MOVE.place(x=130, y=248)
        self.v_ADC = tk.StringVar()
        self.v_ADC.set("PARK")
        ADC_status = ["IN", "PARK", "TRACK"]
        button_ADC_IN = ttk.Radiobutton(self.main_frame,
                   text=ADC_status[0],
                   variable=self.v_ADC,
                   # self.ADC_option_TCS,
                   command=partial(self.ADC_option_TCS, ADC_status[0]),
                   value="IN").place(x=200, y=250)
        button_ADC_PARK = ttk.Radiobutton(self.main_frame,
                   text=ADC_status[1],
                   variable=self.v_ADC,
                   # self.ADC_option_TCS,
                   command=partial(self.ADC_option_TCS, ADC_status[1]),
                   value="PARK").place(x=250, y=250)
        button_ADC_TRACK = ttk.Radiobutton(self.main_frame,
                   text=ADC_status[2],
                   variable=self.v_ADC,
                   # self.ADC_option_TCS,
                   command=partial(self.ADC_option_TCS, ADC_status[2]),
                   value="TRACK").place(x=320, y=250)
        button_CLM_STATUS = ttk.Button(
            self.main_frame, text="STATUS", command=partial(self.ADC_option_TCS, "STATUS"))
        button_CLM_STATUS.place(x=400, y=248)

        ttk.Label(self.main_frame,
                 text="IPA:",
                 justify=tk.LEFT).place(x=4, y=280)
        button_IPA_MOVE = ttk.Button(
            self.main_frame, text="MOVE", command=partial(self.IPA_option_TCS, "MOVE"))
        button_IPA_MOVE.place(x=60, y=276)
        self.IPA_MOVE_msg = tk.StringVar()
        self.IPA_MOVE_msg.set("0.0")
        entry_IPA_MOVE = ttk.Entry(
            self.main_frame, textvariable=self.IPA_MOVE_msg, width=20)
        entry_IPA_MOVE.place(x=200, y=278)
        button_IPA_STATUS = ttk.Button(
            self.main_frame, text="STATUS", command=partial(self.IPA_option_TCS, "STATUS"))
        button_IPA_STATUS.place(x=400, y=280)

        ttk.Label(self.main_frame,
                 text="Instrument:",
                 justify=tk.LEFT).place(x=4, y=310)
        button_Instrument_MOVE = ttk.Button(
            self.main_frame, text="MOVE", command=partial(self.Instrument_option_TCS, "MOVE"))
        button_Instrument_MOVE.place(x=100, y=306)
        self.Instrument_MOVE_msg = tk.StringVar()
        self.Instrument_MOVE_msg.set("SAM")
        entry_Instrument_MOVE = ttk.Entry(
            self.main_frame, textvariable=self.Instrument_MOVE_msg, width=20)
        entry_Instrument_MOVE.place(x=200, y=308)
        button_Instrument_STATUS = ttk.Button(
            self.main_frame, text="STATUS", command=partial(self.Instrument_option_TCS, "STATUS"))
        button_Instrument_STATUS.place(x=400, y=310)

        ttk.Label(self.main_frame,
                 text="Target:",
                 justify=tk.LEFT).place(x=4, y=370)
        ttk.Label(self.main_frame,
                 text="RA:",
                 justify=tk.LEFT).place(x=70, y=370)
        self.Target_RA_msg = tk.StringVar()
        self.Target_RA_msg.set("07:43:48.40")
        entry_Target_RA = ttk.Entry(
            self.main_frame, textvariable=self.Target_RA_msg, width=11)
        entry_Target_RA.place(x=105, y=366)
        ttk.Label(self.main_frame,
                 text="DEC:",
                 justify=tk.LEFT).place(x=235, y=370)
        self.Target_DEC_msg = tk.StringVar()
        self.Target_DEC_msg.set("-28:57:18.00")
        entry_Target_DEC = ttk.Entry(
            self.main_frame, textvariable=self.Target_DEC_msg, width=11)
        entry_Target_DEC.place(x=280, y=366)
        ttk.Label(self.main_frame,
                 text="Epoch:",
                 justify=tk.LEFT).place(x=70, y=400)
        self.Target_EPOCH_msg = tk.StringVar()
        self.Target_EPOCH_msg.set("2000.0")
        entry_Target_EPOCH = ttk.Entry(
            self.main_frame, textvariable=self.Target_EPOCH_msg, width=6)
        entry_Target_EPOCH.place(x=127, y=396)
        self.Target_variable = tk.StringVar()
        self.Target_variable.set("MOVE")
        Target_options = ["MOVE", "MOUNT", "STOP"]
        button_Target_MOVE = ttk.Radiobutton(self.main_frame,
                   text=Target_options[0],
                   variable=self.Target_variable,
                   command=partial(self.Target_option_TCS, Target_options[0]),
                   value="MOVE").place(x=180, y=430)
        button_Target_MOUNT = ttk.Radiobutton(self.main_frame,
                   text=Target_options[1],
                   variable=self.Target_variable,
                   command=partial(self.Target_option_TCS, Target_options[1]),
                   value="MOUNT").place(x=250, y=430)
        button_Target_STOP = ttk.Radiobutton(self.main_frame,
                   text=Target_options[2],
                   variable=self.Target_variable,
                   command=partial(self.Target_option_TCS, Target_options[2]),
                   value="STOP").place(x=330, y=430)
        button_Focus_STATUS = ttk.Button(
            self.main_frame, text="STATUS", command=partial(self.Target_option_TCS, "STATUS"))
        button_Focus_STATUS.place(x=400, y=428)

        label_INFO = ttk.Button(self.main_frame, text="INFO",
            command=partial(self.Handle_Infox, "INFO"))
        label_INFO.place(x=600, y=4)
        label_INFOx = ttk.Button(
            self.main_frame, text="INFOX",
            command=partial(self.Handle_Infox, "INFOX"))
        label_INFOx.place(x=675, y=4)
        label_GINFO = ttk.Button(
            self.main_frame, text="GINFO",
            command=partial(self.Handle_Infox, "GINFO"))
        label_GINFO.place(x=750, y=4)
        label_SINFO = ttk.Button(
            self.main_frame, text="SINFO",
            command=partial(self.Handle_Infox, "SINFO"))
        label_SINFO.place(x=825, y=4)
        label_ROTPOS = ttk.Button(
            self.main_frame, text="ROTPOS",
            command=partial(self.Handle_Infox, "ROTPOS"))
        label_ROTPOS.place(x=900, y=4)
        label_INFOA = ttk.Button(
            self.main_frame, text="INFOA",
            command=partial(self.Handle_Infox, "INFOA"))
        label_INFOA.place(x=975, y=4)

        '''
        self.INFOxxx_msg=tk.StringVar()
        self.INFOxxx_msg.set("")
        entry_INFOxxx = ttk.Text(self.main_frame,  height=20, width=50,  bd =3)
        scroll = ttk.Scrollbar(self.main_frame)
        entry_INFOxxx.configure(yscrollcommand=scroll.set)
        entry_INFOxxx.place(x=600, y=40)
        scroll.config(command=entry_INFOxxx.yview)
        scroll.place(side=tk.RIGHT, fill=tk.Y)
        entry_INFOxxx.insert(tk.END, "lorem ipsum")
        '''
        self.text_area = ScrolledText(self.main_frame, wrap=tk.WORD,
                                                      width=53, height=25,
                                                      font=("Times New Roman", 15))
        self.text_area.grid(row=20, column=0, columnspan=6, sticky=TK_STICKY_ALL)


    def Send_to_TCS(self):
        self._log(f"Sending {self.Send_to_TCS_msg.get()}")
        reply = self.SOAR.send_to_TCS(self.Send_to_TCS_msg.get())
        self._log(f"Received {reply}")


    def way(self):
        """ 
        (Who are you?) This command returns an identification string

        For example
            WAY
            DONE SOAR 4.2m
        """
        self._log("Sent WAY")
        reply = self.SOAR.send_to_tcs("WAY")
        self._log(f"Received {reply}")


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


    def _log(self, message):
        self.logger.info("Adding '{}' to log".format(message))
        self.text_area.insert(tk.END, f"{datetime.now()}: {message}\n")
        self.text_area.yview(tk.END)
