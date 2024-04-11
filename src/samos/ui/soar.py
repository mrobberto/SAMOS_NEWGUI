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

from astropy.coordinates import SkyCoord
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
from customtkinter import CTkSwitch

from samos.ccd import CCD
from samos.dmd.pixel_mapping import Coord_Transform_Helpers as CTH
from samos.dmd.convert.CONVERT_class import CONVERT
from samos.dmd.pattern_helpers.Class_DMDGroup import DMDGroup
from samos.dmd import DigitalMicroMirrorDevice
from samos.soar.Class_SOAR import Class_SOAR
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

        # Left Frame
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Offset
        w = ttk.Button(frame, text="Get Offset", command=partial(self.tcs_offset, "STATUS"))
        w.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.offset = tk.StringVar(self, "E 0.00 N 0.00")
        w = ttk.Entry(frame, textvariable=self.offset, width=12)
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Move to Offset", command=partial(self.tcs_offset, "MOVE"))
        w.grid(row=1, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Focus
        w = ttk.Button(frame, text="Get Focus", command=partial(self.tcs_focus, "STATUS"))
        w.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.focus = tk.DoubleVar(self, 0.)
        w = ttk.Entry(frame, textvariable=self.focus, width=12)
        w.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        focus_options = ["Relative", "Absolute"]
        self.focus_option = tk.StringVar(self, focus_options[0])
        w = ttk.OptionMenu(frame, self.focus_option, *focus_options)
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Change Focus", command=partial(self.tcs_focus, "MOVE"))
        w.grid(row=2, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # CLM
        w = ttk.Button(frame, text="Get CLM", command=partial(self.tcs_clm, "STATUS"))
        w.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.clm = tk.StringVar(self, "IN")
        w = customtkinter.CTkSwitch(frame, textvariable=self.clm, command=partial(self.tcs_clm, "SET"), 
                                    variable=self.clm, onvalue="IN", offvalue="OUT")
        w.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Guider
        w = ttk.Button(frame, text="Get Guider", command=partial(self.tcs_guider, "STATUS"))
        w.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.guider = tk.StringVar(self, "DISABLED")
        w = customtkinter.CTkSwitch(frame, textvariable=self.guider, command=partial(self.tcs_guider, "SET"), 
                                    variable=self.guider, onvalue="ENABLED", offvalue="DISABLED")
        w.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Whitespot
        self.whitespot = tk.StringVar(self, "OFF")
        self.whitespot_pct = tk.DoubleVar(self, 50)
        w = ttk.Button(frame, text="Get Whitespot", command=partial(self.tcs_whitespot, "STATUS"))
        w.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = customtkinter.CTkSwitch(frame, textvariable=self.whitespot, command=partial(self.tcs_whitespot, "SET"), 
                                    variable=self.whitespot, onvalue="ON", offvalue="OFF")
        w.grid(row=5, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        ttk.Label(frame, text="Whitespot %:").grid(row=5, column=2, sticky=TK_STICKY_ALL)
        w = ttk.Entry(frame, textvariable=self.whitespot_pct, width=4)
        w.grid(row=5, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set Whitespot Intensity", command=partial(self.tcs_whitespot, "SET"))
        w.grid(row=5, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # ADC
        adc_options = ["IN", "PARK", "TRACK"]
        self.adc = tk.StringVar(self, adc_options[1])
        self.adc_pct = tk.DoubleVar(self, 0.)
        w = ttk.Button(frame, text="Get ADC", command=partial(self.tcs_adc, "STATUS"))
        w.grid(row=6, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.OptionMenu(frame, self.adc, self.adc.get(), *adc_options, command=partial(self.tcs_adc, "SET"))
        w.grid(row=6, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        ttk.Label(frame, text="ADC %:").grid(row=6, column=2, sticky=TK_STICKY_ALL)
        w = ttk.Entry(frame, textvariable=self.adc_pct, width=4)
        w.grid(row=6, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set ADC %", command=partial(self.tcs_adc, "SET"))
        w.grid(row=5, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # IPA
        self.ipa = tk.DoubleVar(self, 0.)
        w = ttk.Button(frame, text="Get IPA", command=partial(self.tcs_ipa, "STATUS"))
        w.grid(row=7, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Entry(frame, textvariable=self.ipa, width=20)
        w.grid(row=7, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set IPA", command=partial(self.tcs_ipa, "SET"))
        w.grid(row=7, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Instrument
        self.instrument = tk.StringVar(self, "SAM")
        w = ttk.Button(frame, text="Get Instrument", command=partial(self.tcs_instrument, "STATUS"))
        w.grid(row=8, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Entry(frame, textvariable=self.instrument, width=20)
        w.grid(row=8, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set Instrument", command=partial(self.tcs_instrument, "MOVE"))
        w.grid(row=8, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Target and Slew
        frame = ttk.LabelFrame(self.main_frame, text="Target:")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.ra = tk.StringVar(self, "")
        ttk.Label(frame, text="RA:", justify=tk.LEFT).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Entry(frame, textvariable=self.ra, width=11)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.dec = tk.StringVar(self, "")
        ttk.Label(frame, text="DEC:", justify=tk.LEFT).grid(row=0, column=2, sticky=TK_STICKY_ALL)
        w = ttk.Entry(frame, textvariable=self.dec, width=11)
        w.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.epoch = tk.StringVar(self, "2000.0")
        ttk.Label(frame, text="Epoch:", justify=tk.LEFT).grid(row=0, column=4, sticky=TK_STICKY_ALL)
        w = ttk.Entry(frame, textvariable=self.epoch, width=6)
        w.grid(row=0, column=5, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="STATUS", command=partial(self.tcs_target, "STATUS"))
        w.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="MOVE", command=partial(self.tcs_target, "MOVE"))
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="MOUNT", command=partial(self.tcs_target, "MOUNT"))
        w.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="STOP", command=partial(self.tcs_target, "STOP"))
        w.grid(row=1, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Right Frame
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=1, column=1, rowspan=2, sticky=TK_STICKY_ALL)
        # Lamps - there are 12 lamps, with 9 and 12 having dimmers.
        self.lamp_vars = {}
        self.lamp_dimmer_vars = {}
        for i in range(12):
            self.lamp_vars[i+1] = tk.StringVar(self, "OFF")
            w = ttk.Button(frame, text="Get Lamp {}".format(i+1), command=partial(self.tcs_lamp, "STATUS", i+1))
            w.grid(row=i, column=0, sticky=TK_STICKY_ALL)
            self.check_widgets[w] = [("condition", self, "initialized", True)]
            w = CTkSwitch(frame, textvariable=self.lamp_vars[i+1], command=partial(self.tcs_lamp, "SET", i+1),
                          variable=self.lamp_vars[i+1], onvalue="ON", offvalue="OFF", border_width=2)
            w.grid(row=i, column=1, sticky=TK_STICKY_ALL)
            self.check_widgets[w] = [("condition", self, "initialized", True)]
            if (i == 8) or (i == 11):
                # Add dimmer
                self.lamp_dimmer_vars[i+1] = tk.DoubleVar(self, 50)
                ttk.Label(frame, text="Dimmer Intensity %:").grid(row=i, column=2, sticky=TK_STICKY_ALL)
                w = ttk.Entry(frame, textvariable=self.lamp_dimmer_vars[i+1], width=4)
                w.grid(row=i, column=3, sticky=TK_STICKY_ALL)
                self.check_widgets[w] = [("condition", self, "initialized", True)]
                w = ttk.Button(frame, text="Set Lamp Intensity", command=partial(self.tcs_lamp, "SET", i+1))
                w.grid(row=i, column=4, sticky=TK_STICKY_ALL)
                self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Info Buttons
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="INFO", command=partial(self.tcs_info, "INFO"))
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="INFOX", command=partial(self.tcs_info, "INFOX"))
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="GINFO", command=partial(self.tcs_info, "GINFO"))
        w.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="SINFO", command=partial(self.tcs_info, "SINFO"))
        w.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="ROTPOS", command=partial(self.tcs_info, "ROTPOS"))
        w.grid(row=0, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="INFOA", command=partial(self.tcs_info, "INFOA"))
        w.grid(row=0, column=5, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Custom Command
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Custom Command:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.custom_command = tk.StringVar(self, "")
        w = ttk.Entry(frame, textvariable=self.custom_command)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="SEND", command=self.tcs_custom)
        w.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Bottom Status Log
        self.text_area = ScrolledText(self.main_frame, wrap=tk.WORD, width=53, height=25, font=("Times New Roman", 15))
        self.text_area.grid(row=4, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.set_enabled()


    def tcs_custom(self):
        self._log(f"Sending {self.custom_command.get()}")
        reply = self.SOAR.send_to_tcs(self.custom_command.get())
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


    def tcs_offset(self, event):
        """
        This command send an offset motion request to the TCS.
        The offset is given in units of arcseconds, and must be preceded by one of the direction characters N, S, E and W.
        """
        if event == "MOVE":
            offset = self.offset.get()
        else:
            offset = ""
        self._log(f"Sent OFFSET {event} {offset}")
        reply = SOAR.offset(event, offset)
        self._log(f"Received {reply}")


    def tcs_focus(self, event):
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
        if event != "STATUS":
            offset = self.focus.get()
        else:
            offset = ""
        self._log(f"Sent FOCUS {event} {offset}")
        reply = SOAR.focus(event, offset)
        self._log(f"Received {reply}")


    def tcs_clm(self, event):
        """ This command requests actions to the comparison lamps mirror mechanism. """
        self._log(f"Sent CLM {event}")
        reply = SOAR.clm(event)
        self._log(f"Received {reply}")


    def tcs_guider(self, event):
        """ This command enable or disable the guider device. """
        self._log(f"Sent Guider {event}")
        reply = SOAR.guider(event)
        self._log(f"Received {reply}")


    def tcs_whitespot(self, message):
        """ This command enable or disable the Whitespot device. """
        event = self.whitespot.get()
        if message == "STATUS":
            event = "STATUS"
        pct = self.whitespot_pct.get()
        if event != "ON":
            pct = 0.
        self._log(f"Sent Whitespot {event} {pct}")
        reply = SOAR.whitespot(event, pct)
        self._log(f"Received {reply}")


    def tcs_lamp(self, message, lamp_number):
        """
        This command turns on or off the calibration lamps. Where “LN” is the location of the lamp (1 to 12).
        There are two position that have dimmers, position L9 and L12, therefore, a percentage must be added.
        """
        if message == "STATUS":
            event = "STATUS"
            location = lamp_number
        else:
            event = self.lamp_vars[lamp_number].get()
            location = lamp_number
            if (event == "ON") and ((lamp_number == 9) or (lamp_number == 12)):
                location += " {}".format(self.lamp_dimmer_vars[lamp_number]).get()
        self._log(f"Sent LAMP {event} to {location}")
        reply = SOAR.lamp_id(event, location)
        self._log(f"Received {reply}")


    def tcs_adc(self, event):
        message = self.adc.get()
        percentage = self.adc_pct.get()
        if message != "IN":
            percentage = ''
        self._log(f"Sent ADC {message} {percentage}")
        reply = SOAR.adc(message, percentage)
        self._log(f"Received {reply}")


    def tcs_ipa(self, event):
        """
        This command set a new instrument position angle to the TCS.
        The IPA is given in units of degrees.
        """
        if event == "SET":
            offset = self.ipa.get()
        else:
            offset = ""
        self._log("Sent IPA {event} {offset}")
        reply = SOAR.ipa(event, offset)
        self._log(f"Received {reply}")


    def tcs_instrument(self, event):
        """
        This command selects the instrument in use
        """
        if event == "SET":
            value = self.instrument.get()
        else:
            value = ""
        self._log(f"Sent Instrument {event} {value}")
        reply = SOAR.instrument(event, offset)
        self._log(f"Received {reply}")


    def tcs_target(self, event):
        """
        This command send a new position request to the TCS.
        The target is given in units of RA (HH:MM:SS.SS), DEC (DD:MM:SS.SS) and EPOCH (year).
        This command involves the movement of mount, dome, rotator, adc and optics.
        If it is required to know only the state of the mount, use option "MOUNT"
        """
        coord = SkyCoord(ra=self.ra.get(), dec=self.dec.get(), equinox=self.epoch.get())
        radec = coord.to_string(style='hmsdms')
        if event != "MOVE":
            radec = ""
        self._log(f"Sent Target {event} {radec}")
        reply = SOAR.target(event, RADEC)
        self._log(f"Received {reply}")


    def tcs_info(self, message):
        """
        This command returns various lists of parameters, dependin on the choice:
        """
        self._log(f"Sending {message}")
        reply = SOAR.info_whatever(message)
        self._log(f"Received {reply}")


    def _log(self, message):
        self.logger.info("Adding '{}' to log".format(message))
        self.text_area.insert(tk.END, f"{datetime.now()}: {message}\n")
        self.text_area.yview(tk.END)
