"""
SAMOS SAMI tk Frame Class
"""
from datetime import datetime
from functools import partial

from astropy.coordinates import SkyCoord

import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.dialogs.dialogs import Messagebox as mbox
from ttkbootstrap.style import Bootstyle as tbs
from tkinter.scrolledtext import ScrolledText

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class SAMIPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMI", **kwargs)
        self.initialized = False
        self.labels = {}

        # Initialization Button
        w = ttk.Button(self.main_frame, text="Initialize", command=self.initialize, bootstyle="success")
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", False)]

        # Top Frame
        frame = ttk.LabelFrame(self.main_frame, text="Legend")
        frame.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        w = ttk.Label(frame, anchor="w", text="Value has not been sent to SAMI", bootstyle="warning", width=40)
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Label(frame, anchor="e", text="Value has successfully been sent to SAMI", bootstyle="success", width=40)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)

        # Left Frame
        frame = ttk.LabelFrame(self.main_frame, text="FP Commands")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        # FP Position
        ttk.Label(frame, text="FP Position:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.fp_pos = self.make_db_var(tk.StringVar, "sami_fp_pos", "UNKNOWN", callback=partial(self.mark_invalid, "fp_pos"))
        self.labels["fp_pos"] = ttk.Label(frame, textvariable=self.fp_pos, bootstyle="warning")
        self.labels["fp_pos"].grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # FP Absolute Move
        ttk.Label(frame, text="Absolute Move").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.fp_abs = self.make_db_var(tk.IntVar, "sami_fp_absolute_move_set", 0, callback=partial(self.mark_invalid, "fp_absolute"))
        self.labels["fp_absolute"] = ttk.Entry(frame, textvariable=self.fp_abs, bootstyle="warning")
        self.labels["fp_absolute"].grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["fp_absolute"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Move", command=self.move_abs, bootstyle="success")
        w.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # FP Relative Move
        ttk.Label(frame, text="Relative Move").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.fp_rel = self.make_db_var(tk.IntVar, "sami_fp_relative_move_set", 0, callback=partial(self.mark_invalid, "fp_relative"))
        self.labels["fp_relative"] = ttk.Entry(frame, textvariable=self.fp_rel, bootstyle="warning")
        self.labels["fp_relative"].grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["fp_relative"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Move", command=self.move_rel, bootstyle="success")
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Take Exposure
        frame = ttk.LabelFrame(self.main_frame, text="Take Exposures")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Take Exposure Button
        w = ttk.Button(frame, text="TAKE EXPOSURE", command=self.take_exposure, bootstyle="success")
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Right Frame
        frame = ttk.LabelFrame(self.main_frame, text="DHE Settings")
        frame.grid(row=2, column=1, rowspan=2, sticky=TK_STICKY_ALL)
        # Exposure Time
        ttk.Label(frame, text="Exposure Time:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.exptime = self.make_db_var(tk.IntVar, "sami_exptime_set", 10, callback=partial(self.mark_invalid, "exp_exptime"))
        self.labels["exp_exptime"] = ttk.Entry(frame, textvariable=self.exptime, bootstyle="warning")
        self.labels["exp_exptime"].grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["exp_exptime"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_exptime, bootstyle="success")
        w.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Number of Images
        ttk.Label(frame, text="Number of Images:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.n_images = self.make_db_var(tk.IntVar, "sami_n_exposures_set", 1, callback=partial(self.mark_invalid, "exp_expnum"))
        self.labels["exp_expnum"] = ttk.Entry(frame, textvariable=self.n_images, bootstyle="warning")
        self.labels["exp_expnum"].grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["exp_expnum"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_n_images, bootstyle="success")
        w.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Basename
        ttk.Label(frame, text="Base Image Name:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.basename = self.make_db_var(tk.StringVar, "POTN_Base_Name", "", callback=partial(self.mark_invalid, "exp_basename"))
        self.labels["exp_basename"] = ttk.Entry(frame, textvariable=self.basename, bootstyle="warning")
        self.labels["exp_basename"].grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["exp_basename"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_basename, bootstyle="success")
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Image Object
        ttk.Label(frame, text="Object Name:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.objname = self.make_db_var(tk.StringVar, "POTN_Target", "", callback=partial(self.mark_invalid, "exp_target"))
        self.labels["exp_target"] = ttk.Entry(frame, textvariable=self.objname, bootstyle="warning")
        self.labels["exp_target"].grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["exp_target"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_objname, bootstyle="success")
        w.grid(row=3, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        # Image Comment
        ttk.Label(frame, text="Image Comment:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.comment = self.make_db_var(tk.StringVar, "POTN_Comment", "", callback=partial(self.mark_invalid, "exp_comment"))
        self.labels["exp_comment"] = ttk.Entry(frame, textvariable=self.comment, bootstyle="warning")
        self.labels["exp_comment"].grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["exp_comment"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set", command=self.set_comment, bootstyle="success")
        w.grid(row=4, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Bottom Status Log
        self.text_area = ScrolledText(self.main_frame, wrap=tk.WORD, width=53, height=25, font=("Times New Roman", 15))
        self.text_area.grid(row=4, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.set_enabled()


    @check_enabled
    def initialize(self):
        self.initialized = True


    @check_enabled
    def mark_invalid(self, component):
        self.labels[component].configure(bootstyle="warning")

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
            self.labels["fp_pos"].configure(bootstyle="success")
            self.labels["fp_relative"].configure(bootstyle="warning")
            self.labels["fp_absolute"].configure(bootstyle="success")
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
            message = f"ERROR: Relative move {move} from {location} goes outside the valid range [0, 4095]"
            mbox.show_error(message, title="Move Position Error", parent=self)
            self._log(f"ERROR: Invalid move position {location + move}")
            return
        self._log(f"Sending 'sami fp moveoff {move}'")
        reply = self.SAMI.move("relative", move)
        if reply == "DONE":
            # Success
            self.fp_pos.set(f"{location + move}")
            self.labels["fp_pos"].configure(bootstyle="success")
            self.labels["fp_relative"].configure(bootstyle="success")
            self.labels["fp_absolute"].configure(bootstyle="warning")
        self._log(f"Received {reply}")


    @check_enabled
    def set_exptime(self):
        self._log(f"Setting Exposure Time")
        exptime = self.exptime.get()
        self._log(f"Sending 'sami dhe set obs.exptime {exptime}'")
        reply = self.SAMI.dhe("obs.exptime", exptime)
        if reply == "DONE":
            self.labels["exp_exptime"].configure(bootstyle="success")
        self._log(f"Received {reply}")


    @check_enabled
    def set_n_images(self):
        self._log(f"Setting Number of Images")
        n_images = self.n_images.get()
        self._log(f"Sending 'sami dhe set obs.nimages {n_images}'")
        reply = self.SAMI.dhe("obs.nimages", n_images)
        if reply == "DONE":
            self.labels["exp_expnum"].configure(bootstyle="success")
        self._log(f"Received {reply}")


    @check_enabled
    def set_basename(self):
        self._log(f"Setting Image Base Name")
        basename = self.basename.get()
        self._log(f"Sending 'sami dhe set image.basename {basename}'")
        reply = self.SAMI.dhe("image.basename", basename)
        if reply == "DONE":
            self.labels["exp_basename"].configure(bootstyle="success")
        self._log(f"Received {reply}")


    @check_enabled
    def set_objname(self):
        self._log(f"Setting Object Name")
        objname = self.objname.get()
        self._log(f"Sending 'sami dhe set image.title {objname}'")
        reply = self.SAMI.dhe("image.title", objname)
        if reply == "DONE":
            # Success
            self.labels["exp_target"].configure(bootstyle="success")
        self._log(f"Received {reply}")


    @check_enabled
    def set_comment(self):
        self._log(f"Setting Image Comment")
        comment = self.comment.get()
        self._log(f"Sending 'sami dhe set image.comment {comment}'")
        reply = self.SAMI.dhe("image.comment", comment)
        if reply == "DONE":
            # Success
            self.labels["exp_comment"].configure(bootstyle="success")
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
