"""
Exposure window, to handle progress bars and (non-blocking) repeat calls to read data from
the CCD device interface.

Author:
    - Brian York
"""
from astropy.io import fits
import logging
import numpy as np
import time

import tkinter as tk
import ttkbootstrap as ttk
from tkinter.scrolledtext import ScrolledText

from samos.utilities.constants import *


class TextHandler(logging.Handler):
    # This class allows you to log to a Tkinter Text or ScrolledText widget
    # Adapted from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06

    def __init__(self, text):
        # run the regular Handler __init__
        logging.Handler.__init__(self)
        # Store a reference to the Text it will log to
        self.text = text

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text.configure(state='normal')
            self.text.insert(tk.END, msg + '\n')
            self.text.configure(state='disabled')
            # Autoscroll to the bottom
            self.text.yview(tk.END)
        # This is necessary because we can't modify the Text from other threads
        self.text.after(0, append)


class LoggingWindow(ttk.Toplevel):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.main_frame = ttk.Frame(self)
        self.main_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.text = ScrolledText(self.main_frame, state='disabled')
        self.text.configure(font='TkFixedFont')
        self.text.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.text_handler = TextHandler(self.text)
        self.geometry('800x600')

    def destroy(self):
        self.withdraw()
