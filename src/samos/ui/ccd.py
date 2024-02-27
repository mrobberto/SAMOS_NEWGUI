"""
SAMOS CCD tk Frame Class
"""
import logging

import tkinter as tk
from tkinter import ttk

from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


class CCDPage(tk.Frame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(container)
        self.logger = logging.getLogger("samos")
        self.logger.debug('Initializing CCD control frame')

        tk.Label(self, text="CCD Page", font=('Times', '20')).pack(pady=0, padx=0)

        left_frame = tk.Frame(self, background="cyan").place(x=0, y=0, anchor="nw", width=950, height=590)

        # CCD Setup Panel
        frame2r = tk.Frame(left_frame, background="#4A7A8C").place(x=4, y=4, anchor="nw", width=360, height=400)
        setup_frame = tk.LabelFrame(frame2r, text="Camera Setup", font=BIGFONT).pack(fill="both", expand="yes")

        # CAMERA ON/OFF SWITCH
        self.camera_is_on = False
        self.label_camera_ON = tk.Label(setup_frame, text="The Camera is off", fg="grey", font=BIGFONT).place(x=4, y=8)

        # Define Our Images
        self.on_png = tk.PhotoImage(file=get_data_file("tk.icons", "on_small.png"))
        self.off_png = tk.PhotoImage(file=get_data_file("tk.icons", "off_small.png"))
        self.button_open_camera = tk.Button(
            setup_frame, image=self.off_png, bd=0, command=self.turn_camera_ON)
        # command = open_close_camera)
        self.button_open_camera.place(x=180, y=0)

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
        # COOLER ON/OFF SWITCH
        self.cooler_is_on = False
        self.label_cooler_ON = tk.Label(setup_frame,
                                        text="The Cooler is off",
                                        fg="grey",
                                        font=BIGFONT)
        self.label_cooler_ON.place(x=4, y=58)

        # Define Our Images
        self.button_open_cooler = tk.Button(
            setup_frame, image=self.off_png, bd=0, command=self.turn_cooler_ON)
        # command = open_close_camera)
        self.button_open_cooler.place(x=180, y=50)
 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
        # COOLER TEMPERATURE SETUP AND VALUE
        label_Tset = tk.Label(
            setup_frame, text="CCD Temperature Sepoint (C)")
        label_Tset.place(x=4, y=98)
        self.Tset = tk.StringVar()
        self.Tset.set("-90")
        entry_Tset = tk.Entry(setup_frame,
                              textvariable=self.Tset, width=5,
                              # font=('Arial',16),
                              bd=3)
        entry_Tset.place(x=200, y=96)
        #
        label_Tdet = tk.Label(
            setup_frame, text="Current CCD Temperature (K)")
        label_Tdet.place(x=4, y=128)
        self.Tdet = tk.IntVar()
        label_show_Tdet = tk.Label(setup_frame,
                                   textvariable=self.Tdet,
                                   font=('Arial', 16),
                                   borderwidth=3,
                                   relief="sunken",
                                   bg="green", fg="white",
                                   text=str(273))
        label_show_Tdet.place(x=200, y=126)
        self.Tdet.set(273)

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
    def turn_camera_ON(self):
        """ to be written """
        # global camera_is_on

        # Determine is on or off
        if self.camera_is_on:
            self.button_open_camera.config(image=self.off_png)
            self.label_camera_ON.config(text="The Camera is Off", fg="grey")
            self.camera_is_on = False
        else:
            self.button_open_camera.config(image=self.on_png)
            self.label_camera_ON.config(text="The Camera is On", fg="green")
            self.camera_is_on = True

 # ===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===##===#===#===
    def turn_cooler_ON(self):
        """ to be written """
        # global camera_is_on

        # Determine is on or off
        if self.cooler_is_on:
            self.button_open_cooler.config(image=self.off_png)
            self.label_cooler_ON.config(text="The Cooler is Off", fg="grey")
            self.cooler_is_on = False
        else:
            self.button_open_cooler.config(image=self.on_png)
            self.label_cooler_ON.config(text="The Cooler is On", fg="green")
            self.cooler_is_on = True


# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====
#      SHOW SIMBAD IMAGE
#
# #===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#===#=====

    def create_menubar(self, parent):
        """ to be written """
        parent.geometry("900x600")
        parent.title("SAMOS CCD Controller")

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
                             command=lambda: parent.show_frame(parent.CCD2DMDPage))
        filemenu.add_command(
            label="Motors", command=lambda: parent.show_frame(parent.MotorsPage))
        filemenu.add_command(
            label="CCD", command=lambda: parent.show_frame(parent.CCDPage))
        filemenu.add_command(
            label="SOAR TCS", command=lambda: parent.show_frame(parent.SOARPage))
        filemenu.add_command(
            label="MainPage", command=lambda: parent.show_frame(parent.MainPage))
        filemenu.add_command(
            label="Close", command=lambda: parent.show_frame(parent.ConfigPage))
        filemenu.add_separator()
        filemenu.add_command(
            label="ETC", command=lambda: parent.show_frame(parent.ETCPage))
        filemenu.add_command(label="Exit", command=parent.quit)

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame(parent.GSPage))        
        help_menu.add_separator()

        return menubar
