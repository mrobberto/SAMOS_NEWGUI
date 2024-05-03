"""
SAMOS SAMI tk Frame Class
"""
from datetime import datetime
from functools import partial

from astropy.coordinates import SkyCoord

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import Messagebox as mbox
from tkinter.scrolledtext import ScrolledText

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class SAMIPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMI", **kwargs)
        self.initialized = False

        # Initialization Button
        w = ttk.Button(self.main_frame, text="Initialize", command=self.initialize, bootstyle="success")
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", False)]

        # Left Frame
        frame = ttk.LabelFrame(self.main_frame, text="FP Commands")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # FP Position
        ttk.Label(frame, text="FP Position:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.fp_pos = tk.StringVar(self, "UNKNOWN")
        ttk.Label(frame, textvariable=self.fp_pos).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # FP Absolute Move
        ttk.Label(frame, text="Absolute Move").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.fp_abs = tk.IntVar(self, 0)
        w = ttk.Entry(frame, textvariable=self.fp_abs)
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Move", command=self.move_abs, bootstyle="success")
        w.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # FP Relative Move
        ttk.Label(frame, text="Relative Move").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.fp_rel = tk.IntVar(self, 0)
        w = ttk.Entry(frame, textvariable=self.fp_rel)
        w.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Move", command=self.move_rel, bootstyle="success")
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Take Exposure
        frame = ttk.LabelFrame(self.main_frame, text="Take Exposures")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        # Take Exposure Button
        w = ttk.Button(frame, text="TAKE EXPOSURE", command=self.take_exposure, bootstyle="success")
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Right Frame
        frame = ttk.LabelFrame(self.main_frame, text="DHE Settings")
        frame.grid(row=1, column=1, rowspan=2, sticky=TK_STICKY_ALL)
        # Exposure Time
        ttk.Label(frame, text="Exposure Time:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.exptime = tk.IntVar(self, 10)
        w = ttk.Entry(frame, textvariable=self.exptime)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_exptime, bootstyle="success")
        w.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Number of Images
        ttk.Label(frame, text="Number of Images:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.n_images = tk.IntVar(self, 1)
        w = ttk.Entry(frame, textvariable=self.n_images)
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_n_images, bootstyle="success")
        w.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Basename
        ttk.Label(frame, text="Base Image Name:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.basename = tk.StringVar(self, "")
        w = ttk.Entry(frame, textvariable=self.basename)
        w.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_basename, bootstyle="success")
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Image Object
        ttk.Label(frame, text="Object Name:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.objname = tk.StringVar(self, "")
        w = ttk.Entry(frame, textvariable=self.objname)
        w.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_objname, bootstyle="success")
        w.grid(row=3, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Image Comment
        ttk.Label(frame, text="Image Comment:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.comment = tk.StringVar(self, "")
        w = ttk.Entry(frame, textvariable=self.comment)
        w.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_comment, bootstyle="success")
        w.grid(row=4, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Bottom Status Log
        self.text_area = ScrolledText(self.main_frame, wrap=tk.WORD, width=53, height=25, font=("Times New Roman", 15))
        self.text_area.grid(row=3, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.set_enabled()


    @check_enabled
    def initialize(self):
        self.initialized = True


    @check_enabled
    def move_abs(self):
        self._log(f"Commanding Absolute Move")
        location = self.fp_abs.get()
        if (location < 0) or (location > 4095):
            mbox.show_error(f"ERROR: Move location {location} not in the valid range [0, 4095]", title="Move Position Error", parent=self)
            self._log(f"ERROR: Invalid move position {location}")
            return
        self._log(f"Sending 'sami fp moveabs {location}'")
        reply = self.SAMI.move("absolute", location)
        if reply == "DONE":
            # Success
            self.fp_pos.set(f"{location}")
        self._log(f"Received {reply}")


    @check_enabled
    def move_rel(self):
        self._log(f"Commanding Relative Move")
        if self.fp_pos.get() == "UNKNOWN":
            mbox.show_error(f"ERROR: Cannot send relative move when absolute location is unknown", title="Move Position Error", parent=self)
            self._log(f"ERROR: Relative move when absolute")
            return
        move = self.fp_rel.get()
        location = int(self.fp_pos.get())
        if (location + move < 0) or (location + move > 4095):
            mbox.show_error(f"ERROR: Relative move {move} from {location} goes outside the valid range [0, 4095]", title="Move Position Error", parent=self)
            self._log(f"ERROR: Invalid move position {location + move}")
            return
        self._log(f"Sending 'sami fp moveoff {move}'")
        reply = self.SAMI.move("relative", move)
        if reply == "DONE":
            # Success
            self.fp_pos.set(f"{location + move}")
        self._log(f"Received {reply}")


    @check_enabled
    def set_exptime(self):
        self._log(f"Setting Exposure Time")
        exptime = self.exptime.get()
        self._log(f"Sending 'sami dhe set obs.exptime {exptime}'")
        reply = self.SAMI.dhe("obs.exptime", exptime)
        self._log(f"Received {reply}")


    @check_enabled
    def set_n_images(self):
        self._log(f"Setting Number of Images")
        n_images = self.n_images.get()
        self._log(f"Sending 'sami dhe set obs.nimages {n_images}'")
        reply = self.SAMI.dhe("obs.nimages", n_images)
        self._log(f"Received {reply}")


    @check_enabled
    def set_basename(self):
        self._log(f"Setting Image Base Name")
        basename = self.basename.get()
        self._log(f"Sending 'sami dhe set image.basename {basename}'")
        reply = self.SAMI.dhe("image.basename", basename)
        self._log(f"Received {reply}")


    @check_enabled
    def set_objname(self):
        self._log(f"Setting Object Name")
        objname = self.objname.get()
        self._log(f"Sending 'sami dhe set image.title {objname}'")
        reply = self.SAMI.dhe("image.title", objname)
        if reply == "DONE":
            # Success
            self.PAR.PotN["Object Name"] = objname
        self._log(f"Received {reply}")


    @check_enabled
    def set_comment(self):
        self._log(f"Setting Image Comment")
        comment = self.comment.get()
        self._log(f"Sending 'sami dhe set image.title {objname}'")
        reply = self.SAMI.dhe("image.comment", comment)
        if reply == "DONE":
            # Success
            self.PAR.PotN["Comments"] = comment
        self._log(f"Received {reply}")


    @check_enabled
    def take_exposure(self):
        self._log(f"Taking Exposure")
        self._log(f"Sending 'sami dhe expose'")
        reply = self.SAMI.expose(self)
        self._log(f"Received {reply}")


    def _log(self, message):
        self.logger.info("Adding '{}' to log".format(message))
        self.text_area.insert(tk.END, f"{datetime.now()}: {message}\n")
        self.text_area.yview(tk.END)
