"""
SAMOS CCD tk Frame Class
"""
import logging

import tkinter as tk
from tkinter import ttk

from samos.tk_utilities.utils import about_box
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


class CCDPage(ttk.Frame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(container)
        self.logger = logging.getLogger("samos")
        self.logger.debug('Initializing CCD control frame')

        # Define Our Images
        self.on_png = tk.PhotoImage(file=get_data_file("tk.icons", "on_small.png"))
        self.off_png = tk.PhotoImage(file=get_data_file("tk.icons", "off_small.png"))

        # Label for the full frame
        tk.Label(self, text="CCD Page", font=('Times', '20')).pack(pady=0, padx=0)

        # Set up main frame
        main_frame = tk.Frame(self, background="cyan")
        main_frame.place(x=0, y=0, anchor="nw", width=950, height=590)

        # CCD Setup Panel
        ccd_frame = tk.LabelFrame(main_frame, text="Camera Setup", font=BIGFONT)
        ccd_frame.pack(fill="both", expand="yes")

        # CAMERA ON/OFF SWITCH
        self.camera_is_on = False
        self.label_camera = tk.Label(ccd_frame, text=self.cam, fg="grey", font=BIGFONT)
        self.label_camera.place(x=4, y=8)
        self.button_camera = tk.Button(ccd_frame, image=self.cimg, bd=0, command=self.toggle_camera)
        self.button_camera.place(x=180, y=0)

        # COOLER ON/OFF SWITCH
        self.cooler_is_on = False
        self.label_cooler = tk.Label(ccd_frame, text=self.cool, fg="grey", font=BIGFONT)
        self.label_cooler.place(x=4, y=58)
        self.button_cooler = tk.Button(ccd_frame, image=self.coolimg, bd=0, command=self.toggle_cooler)
        self.button_cooler.place(x=180, y=50)

        # COOLER TEMPERATURE SETUP AND VALUE
        tk.Label(ccd_frame, text="CCD Temperature Sepoint (C)").place(x=4, y=98)
        self.Tset = tk.StringVar()
        self.Tset.set("-90")
        entry_Tset = tk.Entry(ccd_frame, textvariable=self.Tset, width=5, bd=3)
        entry_Tset.place(x=200, y=96)
        tk.Label(ccd_frame, text="Current CCD Temperature (K)").place(x=4, y=128)
        self.Tdet = tk.IntVar()
        tk.Label(ccd_frame, textvariable=self.Tdet, font=('Arial', 16), borderwidth=3, relief="sunken", 
                 bg="green", fg="white", text=str(273)).place(x=200, y=126)
        self.Tdet.set(273)


    def toggle_camera(self):
        if self.camera_is_on:
            self.camera_is_on = False
        else:
            self.camera_is_on = True
        self.button_camera.config(image=self.cimg)
        self.label_camera.config(text=self.cam, fg="grey")


    def toggle_cooler(self):
        if self.cooler_is_on:
            self.cooler_is_on = False
        else:
            self.cooler_is_on = True
        self.button_cooler.config(image=self.cool_img)
        self.label_cooler.config(text=self.cool, fg="green")


    def create_menubar(self, parent):
        parent.geometry("900x600")
        parent.title("SAMOS CCD Controller")

        menubar = tk.Menu(parent, bd=3, relief=tk.RAISED, activebackground="#80B9DC")

        # Filemenu
        filemenu = tk.Menu(menubar, tearoff=0, relief=tk.RAISED, activebackground="#026AA9")
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Config", command=lambda: parent.show_frame("ConfigPage"))
        filemenu.add_command(label="DMD", command=lambda: parent.show_frame("DMDPage"))
        filemenu.add_command(label="Recalibrate CCD2DMD", command=lambda: parent.show_frame("CCD2DMDPage"))
        filemenu.add_command(label="Motors", command=lambda: parent.show_frame("MotorsPage"))
        filemenu.add_command(label="CCD", command=lambda: parent.show_frame("CCDPage"))
        filemenu.add_command(label="SOAR TCS", command=lambda: parent.show_frame("SOARPage"))
        filemenu.add_command(label="MainPage", command=lambda: parent.show_frame("MainPage"))
        filemenu.add_separator()
        filemenu.add_command(label="ETC", command=lambda: parent.show_frame("ETCPage"))
        filemenu.add_command(label="Exit", command=parent.quit)

        # help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=about_box)
        help_menu.add_command(label="Guide Star", command=lambda: parent.show_frame("GSPage"))        
        help_menu.add_separator()

        return menubar
    
    
    @property
    def cam(self):
        """
        This property holds valid text for the camera button based on its current state.
        """
        if self.camera_is_on:
            return "Camera is ON"
        return "Camera is OFF"
    
    
    @property
    def cimg(self):
        """
        This property points to the appropriate image for the camera button given the 
        camera state
        """
        if self.camera_is_on:
            return self.on_png
        return self.off_png


    @property
    def cool(self):
        """
        This property holds valid text for the cooler button based on its current state.
        """
        if self.cooler_is_on:
            return "Cooler is ON"
        return "Cooler is OFF"
    
    
    @property
    def coolimg(self):
        """
        This property points to the appropriate image for the cooler button given the 
        cooler state
        """
        if self.cooler_is_on:
            return self.on_png
        return self.off_png
