#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 30 10:49:37 2021

@author: robberto
"""
import tkinter as tk
from tkinter import ttk

#for image display
from ginga.tkw.ImageViewTk import CanvasView
from ginga.misc import log

from samos.utilities import get_data_file

import os
cwd = os.getcwd()
print(cwd)


#absolute path of this file
dir_path = os.path.dirname(os.path.realpath(__file__))


class GUI_CCD(tk.Toplevel):     #the GUI_CCD class inherits from the tk.Toplevel widget
    def __init__(self, master=None):  #__init__ constructor method. 
    
#        logger = log.get_logger("example2", log_stderr=True)
#        self.logger = logger
        
        super().__init__(master = master) 
        #super() recalls and includes the __init__() of the master class (tk.Topelevel), so one can use that stuff there without copying the code.
        
        
        self.title("CCD Setup")
        self.geometry("900x600")
        label = tk.Label(self, text ="This is the CCD Window")
        label.pack()

  
#       
        self.frame0l = tk.Frame(self,background="cyan")#, width=300, height=300)
        self.frame0l.place(x=0, y=0, anchor="nw", width=950, height=590)

# =============================================================================
#         
#  #    ACQUIRE IMAGE Frame
#         
# =============================================================================
        self.frame2l = tk.Frame(self.frame0l,background="dark turquoise")#, width=400, height=800)
        self.frame2l.place(x=4, y=4, anchor="nw", width=420, height=400)
        
        
  
# =============================================================================
#       CONTROL OF SCIENCE AND REFERENCE FILES
# 
# =============================================================================

#        root = tk.Tk()
#        root.title("Tab Widget")
        tabControl = ttk.Notebook(self.frame2l)
  
        tab1 = ttk.Frame(tabControl)
        tab2 = ttk.Frame(tabControl)
        tab3 = ttk.Frame(tabControl)
        tab4 = ttk.Frame(tabControl)
        tab5 = ttk.Frame(tabControl)
  
        tabControl.add(tab1, text ='Image')
        tabControl.add(tab2, text ='Bias')
        tabControl.add(tab3, text ='Dark')
        tabControl.add(tab4, text ='Flat')
        tabControl.add(tab5, text ='Buffer')
        tabControl.pack(expand = 1, fill ="both")
  
# =============================================================================
#      SCIENCE
# =============================================================================

        labelframe_Acquire =  tk.LabelFrame(tab1, text="Acquire Image", font=("Arial", 24))
        labelframe_Acquire.pack(fill="both", expand="yes")
#        labelframe_Grating.place(x=4, y=10)

        label_ExpTime =  tk.Label(labelframe_Acquire, text="Exp. Time (s)")
        label_ExpTime.place(x=4,y=10)
        self.ExpTime=tk.StringVar()
        self.ExpTime.set("0.01")
        entry_ExpTime = tk.Entry(labelframe_Acquire, textvariable=self.ExpTime, width=5,  bd =3)
        entry_ExpTime.place(x=100, y=10)

        label_ObjectName =  tk.Label(labelframe_Acquire, text="Object Name:")
        label_ObjectName.place(x=4,y=30)
        entry_ObjectName = tk.Entry(labelframe_Acquire, width=11,  bd =3)
        entry_ObjectName.place(x=100, y=30)

        label_Comment =  tk.Label(labelframe_Acquire, text="Comment:")
        label_Comment.place(x=4,y=50)
#        scrollbar = tk.Scrollbar(orient="horizontal")
        entry_Comment = tk.Entry(labelframe_Acquire, width=11,  bd =3)# , xscrollcommand=scrollbar.set)
        entry_Comment.place(x=100, y=50)

        button_ExpStart=  tk.Button(labelframe_Acquire, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
                                         #  command=self.expose)
        button_ExpStart.place(x=50,y=75)


# =============================================================================
#      BIAS
# =============================================================================
        labelframe_Bias =  tk.LabelFrame(tab2, text="Bias", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Bias.pack(fill="both", expand="yes")

#        labelframe_Bias.place(x=5,y=5)
        label_Bias_ExpT =  tk.Label(labelframe_Bias, text="Exposure time (s):")
        label_Bias_ExpT.place(x=4,y=10)
        self.Bias_ExpT = tk.StringVar(value="0.00")
        entry_Bias_ExpT = tk.Entry(labelframe_Bias, width=6,  bd =3, textvariable=self.Bias_ExpT)
        entry_Bias_ExpT.place(x=120, y=6)
        
        label_Bias_NofFrames =  tk.Label(labelframe_Bias, text="Nr. of Frames:")
        label_Bias_NofFrames.place(x=4,y=40)
        self.Bias_NofFrames = tk.StringVar(value="10")
        entry_Bias_NofFrames = tk.Entry(labelframe_Bias, width=5,  bd =3, textvariable=self.Bias_NofFrames)
        entry_Bias_NofFrames.place(x=100, y=38)
        
        
        var_Bias_saveall = tk.IntVar()
        r1_Bias_saveall = tk.Radiobutton(labelframe_Bias, text = "Save single frames", variable=var_Bias_saveall, value=1)
        r1_Bias_saveall.place(x=150, y=38)

        label_Bias_MasterFile =  tk.Label(labelframe_Bias, text="Master Bias File:")
        label_Bias_MasterFile.place(x=4,y=70)
        self.Bias_MasterFile = tk.StringVar(value="Bias")
        entry_Bias_MasterFile = tk.Entry(labelframe_Bias, width=11,  bd =3, textvariable=self.Bias_MasterFile)
        entry_Bias_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Bias, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)
  
#        root.mainloop()  




        
# =============================================================================
#      Dark
# =============================================================================
        labelframe_Dark =  tk.LabelFrame(tab3, text="Dark", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Dark.pack(fill="both", expand="yes")

        label_Dark_ExpT =  tk.Label(labelframe_Dark, text="Exposure time (s):")
        label_Dark_ExpT.place(x=4,y=10)
        self.Dark_ExpT = tk.StringVar(value="0.00")
        entry_Dark_ExpT = tk.Entry(labelframe_Dark, width=6,  bd =3, textvariable=self.Dark_ExpT)
        entry_Dark_ExpT.place(x=120, y=6)
        
        label_Dark_NofFrames =  tk.Label(labelframe_Dark, text="Nr. of Frames:")
        label_Dark_NofFrames.place(x=4,y=40)
        self.Dark_NofFrames = tk.StringVar(value="10")
        entry_Dark_NofFrames = tk.Entry(labelframe_Dark, width=5,  bd =3, textvariable=self.Dark_NofFrames)
        entry_Dark_NofFrames.place(x=100, y=38)
        
        
        var_Dark_saveall = tk.IntVar()
        r1_Dark_saveall = tk.Radiobutton(labelframe_Dark, text = "Save single frames", variable=var_Dark_saveall, value=1)
        r1_Dark_saveall.place(x=150, y=38)

        label_Dark_MasterFile =  tk.Label(labelframe_Dark, text="Master Dark File:")
        label_Dark_MasterFile.place(x=4,y=70)
        self.Dark_MasterFile = tk.StringVar(value="Dark")
        entry_Dark_MasterFile = tk.Entry(labelframe_Dark, width=11,  bd =3, textvariable=self.Dark_MasterFile)
        entry_Dark_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Dark, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)

# =============================================================================
#      Flat
# =============================================================================
        labelframe_Flat =  tk.LabelFrame(tab4, text="Flat", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Flat.pack(fill="both", expand="yes")

        label_Flat_ExpT =  tk.Label(labelframe_Flat, text="Exposure time (s):")
        label_Flat_ExpT.place(x=4,y=10)
        self.Flat_ExpT = tk.StringVar(value="0.00")
        entry_Flat_ExpT = tk.Entry(labelframe_Flat, width=6,  bd =3, textvariable=self.Flat_ExpT)
        entry_Flat_ExpT.place(x=120, y=6)
        
        label_Flat_NofFrames =  tk.Label(labelframe_Flat, text="Nr. of Frames:")
        label_Flat_NofFrames.place(x=4,y=40)
        self.Flat_NofFrames = tk.StringVar(value="10")
        entry_Flat_NofFrames = tk.Entry(labelframe_Flat, width=5,  bd =3, textvariable=self.Flat_NofFrames)
        entry_Flat_NofFrames.place(x=100, y=38)
        
        
        var_Flat_saveall = tk.IntVar()
        r1_Flat_saveall = tk.Radiobutton(labelframe_Flat, text = "Save single frames", variable=var_Flat_saveall, value=1)
        r1_Flat_saveall.place(x=150, y=38)

        label_Flat_MasterFile =  tk.Label(labelframe_Flat, text="Master Flat File:")
        label_Flat_MasterFile.place(x=4,y=70)
        self.Flat_MasterFile = tk.StringVar(value="Flat")
        entry_Flat_MasterFile = tk.Entry(labelframe_Flat, width=11,  bd =3, textvariable=self.Flat_MasterFile)
        entry_Flat_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Flat, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)



        label_Display =  tk.Label(labelframe_Acquire, text="Subtract for Display:")
        label_Display.place(x=4,y=120)
        subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(labelframe_Acquire, text='Bias',variable=subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=140)
        subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(labelframe_Acquire, text='Dark',variable=subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60,y=140)
        subtract_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(labelframe_Acquire, text='Flat',variable=subtract_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120,y=140)
        subtract_Buffer = tk.IntVar()
        check_Buffer = tk.Checkbutton(labelframe_Acquire, text='Buffer',variable=subtract_Buffer, onvalue=1, offvalue=0)
        check_Buffer.place(x=180,y=140)

# =============================================================================
#      Buffer
# =============================================================================
        labelframe_Buffer =  tk.LabelFrame(tab5, text="Buffer", 
                                                     width=300, height=170,
                                                     font=("Arial", 24))
        labelframe_Buffer.pack(fill="both", expand="yes")

        label_Buffer_ExpT =  tk.Label(labelframe_Buffer, text="Exposure time (s):")
        label_Buffer_ExpT.place(x=4,y=10)
        self.Buffer_ExpT = tk.StringVar(value="0.00")
        entry_Buffer_ExpT = tk.Entry(labelframe_Buffer, width=6,  bd =3, textvariable=self.Buffer_ExpT)
        entry_Buffer_ExpT.place(x=120, y=6)
        
        label_Buffer_NofFrames =  tk.Label(labelframe_Buffer, text="Nr. of Frames:")
        label_Buffer_NofFrames.place(x=4,y=40)
        self.Buffer_NofFrames = tk.StringVar(value="10")
        entry_Buffer_NofFrames = tk.Entry(labelframe_Buffer, width=5,  bd =3, textvariable=self.Buffer_NofFrames)
        entry_Buffer_NofFrames.place(x=100, y=38)
        
        
        var_Buffer_saveall = tk.IntVar()
        r1_Buffer_saveall = tk.Radiobutton(labelframe_Buffer, text = "Save single frames", variable=var_Buffer_saveall, value=1)
        r1_Buffer_saveall.place(x=150, y=38)

        label_Buffer_MasterFile =  tk.Label(labelframe_Buffer, text="Master Buffer File:")
        label_Buffer_MasterFile.place(x=4,y=70)
        self.Buffer_MasterFile = tk.StringVar(value="Buffer")
        entry_Buffer_MasterFile = tk.Entry(labelframe_Buffer, width=11,  bd =3, textvariable=self.Buffer_MasterFile)
        entry_Buffer_MasterFile.place(x=120, y=68)

        button_ExpStart=  tk.Button(labelframe_Buffer, text="START", bd=3, bg='#0052cc',font=("Arial", 24))#,
#                                          command=expose)
        button_ExpStart.place(x=75,y=95)



        label_Display =  tk.Label(labelframe_Acquire, text="Subtract for Display:")
        label_Display.place(x=4,y=120)
        subtract_Bias = tk.IntVar()
        check_Bias = tk.Checkbutton(labelframe_Acquire, text='Bias',variable=subtract_Bias, onvalue=1, offvalue=0)
        check_Bias.place(x=4, y=140)
        subtract_Dark = tk.IntVar()
        check_Dark = tk.Checkbutton(labelframe_Acquire, text='Dark',variable=subtract_Dark, onvalue=1, offvalue=0)
        check_Dark.place(x=60,y=140)
        subtract_Flat = tk.IntVar()
        check_Flat = tk.Checkbutton(labelframe_Acquire, text='Flat',variable=subtract_Flat, onvalue=1, offvalue=0)
        check_Flat.place(x=120,y=140)
        subtract_Buffer = tk.IntVar()
        check_Buffer = tk.Checkbutton(labelframe_Acquire, text='Buffer',variable=subtract_Buffer, onvalue=1, offvalue=0)
        check_Buffer.place(x=180,y=140)

# =============================================================================
#      CCD Setup panel
# 
# =============================================================================

        self.frame2r = tk.Frame(self.frame0l,background="#4A7A8C")#, width=400, height=800)
        self.frame2r.place(x=430, y=4, anchor="nw", width=360, height=400)
        labelframe_Setup =  tk.LabelFrame(self.frame2r, text="Camera Seup", font=("Arial", 24))
        labelframe_Setup.pack(fill="both", expand="yes")
        
#        #camera_is_open = tk.IntVar()
#        button_open_camera= tk.Button(labelframe_Setup, text='Open Camera')
                                                        #command = open_close_camera)
#        button_open_camera.place(x=4, y=104)
        
#        button_cooler_on= tk.Button(labelframe_Setup, text='Cooler on')
                                                        #command = open_close_camera)
#        button_cooler_on.place(x=4, y=124)
        
 #=========#=========#=========#=========#=========#=========#=========       
        # CAMERA ON/OFF SWITCH
        self.camera_is_on = False
        self.label_camera_ON = tk.Label(labelframe_Setup,
                         text = "The Camera is off",
                         fg = "grey",
                         font = ("Helvetica", 20))
        self.label_camera_ON.place(x=4,y=8)
        
        # Define Our Images
        self.on_png = tk.PhotoImage(file = get_data_file("tk.icons", "on_small.png"))
        self.off_png = tk.PhotoImage(file = get_data_file("tk.icons", "off.png"))
        self.button_open_camera= tk.Button(labelframe_Setup, image=self.off_png, bd=0, command=self.turn_camera_ON)
                                                        #command = open_close_camera)
        self.button_open_camera.place(x=180, y=0)

 #=========#=========#=========#=========#=========#=========#=========       
        # COOLER ON/OFF SWITCH
        self.cooler_is_on = False
        self.label_cooler_ON = tk.Label(labelframe_Setup,
                         text = "The Cooler is off",
                         fg = "grey",
                         font = ("Helvetica", 20))
        self.label_cooler_ON.place(x=4,y=58)
        
        # Define Our Images
        self.button_open_cooler= tk.Button(labelframe_Setup, image=self.off_png, bd=0, command=self.turn_cooler_ON)
                                                        #command = open_close_camera)
        self.button_open_cooler.place(x=180, y=50)
 #=========#=========#=========#=========#=========#=========#=========       
        # COOLER TEMPERATURE SETUP AND VALUE
        label_Tset =  tk.Label(labelframe_Setup, text="CCD Temperature Sepoint (C)")
        label_Tset.place(x=4,y=98)
        self.Tset = tk.StringVar()
        self.Tset.set("-90")
        entry_Tset = tk.Entry(labelframe_Setup, 
                              textvariable=self.Tset, width=5,
                              #font=('Arial',16),
                              bd =3)
        entry_Tset.place(x=200, y=96)
        #
        label_Tdet = tk.Label(labelframe_Setup, text="Current CCD Temperature (K)")
        label_Tdet.place(x=4,y=128)
        self.Tdet = tk.IntVar()
        label_show_Tdet = tk.Label(labelframe_Setup, 
                                   textvariable=self.Tdet,
                                   font=('Arial',16),
                                   borderwidth=3,
                                   relief="sunken",
                                   bg="green",fg="white",
                                   text=str(273))
        label_show_Tdet.place(x=200,y=126)
        self.Tdet.set(273)
            
 #=========#=========#=========#=========#=========#=========#=========       
    def turn_camera_ON(self):
        #global camera_is_on
         
        # Determine is on or off
        if self.camera_is_on:
            self.button_open_camera.config(image = self.off_png)
            self.label_camera_ON.config(text = "The Camera is Off",fg = "grey")
            self.camera_is_on = False
        else:
            self.button_open_camera.config(image = self.on_png)
            self.label_camera_ON.config(text = "The Camera is On", fg = "green")
            self.camera_is_on = True

 #=========#=========#=========#=========#=========#=========#=========       
    def turn_cooler_ON(self):
        #global camera_is_on
         
        # Determine is on or off
        if self.cooler_is_on:
            self.button_open_cooler.config(image = self.off_png)
            self.label_cooler_ON.config(text = "The Cooler is Off",fg = "grey")
            self.cooler_is_on = False
        else:
            self.button_open_cooler.config(image = self.on_png)
            self.label_cooler_ON.config(text = "The Cooler is On", fg = "green")
            self.cooler_is_on = True

        """ 
        #        labelframe_Grating.place(x=4, y=10)

        params = {'Exposure Time':100,'CCD Temperature':2300,'Trigger Mode': 4}
        #Trigger Mode = 4: light
        #Trigger Mode = 4: dark

        Camera= Class_Camera(dict_params=params)


        Camera.expose()
        #Camera.Cooler("1") 

        #Camera.dict_params['Exposure Time']=10

        #Camera.set_CCD_temp(2030)    #(273-80) * 10

        #Status = Camera.status()
        #print(Status)
        #url_name = 'http://128.220.146.254:8900/'
        """
 


# =============================================================================
#      SHOW SIMBAD IMAGE
# 
# =============================================================================

    def Show_Simbad(self):
            self.frame_DisplaySimbad = tk.Frame(self.frame0l,background="pink")#, width=400, height=800)
            self.frame_DisplaySimbad.place(x=310, y=5, anchor="nw", width=528, height=516) 
            
            #img = AstroImage()
#            img = io_fits.load_file(self.image.filename())
    
            # ginga needs a logger.
            # If you don't want to log anything you can create a null logger by
            # using null=True in this call instead of log_stderr=True
            #logger = log.get_logger("example1", log_stderr=True, level=40)
            logger = log.get_logger("example1",log_stderr=True, level=40)
 
#            fv = FitsViewer()
#            top = fv.get_widget()
            
#            ImageViewCanvas.fitsimage.set_image(img)
            canvas = tk.Canvas(self.frame0l, bg="grey", height=516, width=528)
#            canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            canvas.place(x=310,y=5)
                  
            fi = CanvasView(logger)
            fi.set_widget(canvas)
#            fi.set_image(img) 
#            self.fitsimage.set_image(img)

            #fi.set_redraw_lag(0.0)
            fi.enable_autocuts('on')
            fi.set_autocut_params('zscale')
            fi.enable_autozoom('on')
            fi.enable_draw(False)
            # tk seems to not take focus with a click
            fi.set_enter_focus(True)
            fi.set_callback('cursor-changed', self.cursor_cb)
            
            #'button-press' is found in Mixins.py
            fi.set_callback('button-press', self. button_click)  
            
            #'drag-drop' is found in Mixins.py
            #fi.set_callback('drag-drop', self. draw_cb)   

           # fi.set_bg(0.2, 0.2, 0.2)
            fi.ui_set_active(True)
            fi.show_pan_mark(True)
#            fi.set_image(img)
            self.fitsimage = fi
            
            
            bd = fi.get_bindings()
            bd.enable_all(True)
    
            # canvas that we will draw on
            DrawingCanvas = fi.getDrawClass('drawingcanvas')
            canvas = DrawingCanvas()
            canvas.enable_draw(True)
            #canvas.enable_edit(True)
            canvas.set_drawtype('rectangle', color='blue')
            canvas.set_surface(fi)
            self.canvas = canvas
            # add canvas to view
            fi.add(canvas)
            canvas.ui_set_active(True)
     
            fi.configure(516,528)
          #  fi.set_window_size(514,522)
            
            #self.fitsimage.set_image(img)
#            self.root.title(filepath)
            self.load_file()
     

     
# =============================================================================
#             self.readout_Simbad = tk.Label(self.frame0l, text='tbd')
# #            self.readout_Simbad.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
#             self.readout_Simbad.place(x=0,y=530)
#      
# =============================================================================


            self.drawtypes = fi.get_drawtypes()
            ## wdrawtype = ttk.Combobox(root, values=self.drawtypes,
            ##                          command=self.set_drawparams)
            ## index = self.drawtypes.index('ruler')
            ## wdrawtype.current(index)
            wdrawtype = tk.Entry(self.hbox, width=12)
            wdrawtype.insert(0, 'rectangle')
            wdrawtype.bind("<Return>", self.set_drawparams)
            self.wdrawtype = wdrawtype
     
            # wdrawcolor = ttk.Combobox(root, values=self.drawcolors,
            #                           command=self.set_drawparams)
            # index = self.drawcolors.index('blue')
            # wdrawcolor.current(index)
            wdrawcolor = tk.Entry(self.hbox, width=12)
            wdrawcolor.insert(0, 'blue')
            wdrawcolor.bind("<Return>", self.set_drawparams)
            self.wdrawcolor = wdrawcolor
    
            self.vfill = tk.IntVar()
            wfill = tk.Checkbutton(self.hbox, text="Fill", variable=self.vfill)
            self.wfill = wfill
    
            walpha = tk.Entry(self.hbox, width=12)
            walpha.insert(0, '1.0')
            walpha.bind("<Return>", self.set_drawparams)
            self.walpha = walpha
    
            wclear = tk.Button(self.hbox, text="Clear Canvas",
                                    command=self.clear_canvas)
#            wopen = tk.Button(self.hbox, text="Open File",
#                                   command=self.open_file)
            wquit = tk.Button(self.hbox, text="Quit",
                                   command=lambda: self.quit())
            for w in (wquit, wclear, walpha, tk.Label(self.hbox, text='Alpha:'),
                      wfill, wdrawcolor, wdrawtype):#, wopen):
                w.pack(side=tk.RIGHT)
            
# =============================================================================
#         top = fv.get_widget()
# 
#         if len(args) > 0:
#            fv.load_file(args[0])
# 
# =============================================================================

    def cursor_cb(self, viewer, button, data_x, data_y):
        """This gets called when the data position relative to the cursor
        changes.
        """
        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off),
                                    int(data_y + viewer.data_off))

        except Exception:
            value = None

        fits_x, fits_y = data_x + 1, data_y + 1

        # Calculate WCS RA
        try:
            # NOTE: image function operates on DATA space coords
            image = viewer.get_image()
            if image is None:
                # No image loaded
                return
            ra_txt, dec_txt = image.pixtoradec(fits_x, fits_y,
                                               format='str', coords='fits')
        except Exception as e:
            self.logger.warning("Bad coordinate conversion: %s" % (
                str(e)))
            ra_txt = 'BAD WCS'
            dec_txt = 'BAD WCS'

        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s" % (
            ra_txt, dec_txt, fits_x, fits_y, value)
#        text = "RA: %s  DEC: %s  X: %.2f  Y: %.2f  Value: %s Button %s" % (
#            ra_txt, dec_txt, fits_x, fits_y, value, button) 
        self.readout_Simbad.config(text=text)


# =============================================================================
#         labelframe_SolveAstrometry =  tk.LabelFrame(self.frame0l, text="Solve Astrometry", font=("Arial", 24))
#         labelframe_SolveAstrometry.pack(fill="both", expand="yes")
#         
# =============================================================================
    def load_file(self):
        image = load_data('./newtable.fits', logger=self.logger)
#        image = load_data(filepath, logger=self.logger)
        self.fitsimage.set_image(image)


    def get_widget(self):
       return self.root

    ### this is a function called by main to pass parameters 
    def receive_radec(self,radec,radec_list,xy_list): 
        self.string_RA_center.set(radec[0])
        self.string_DEC_center.set(radec[1])
        self.string_RA_list = radec_list[0]
        self.string_DEC_list = radec_list[1]
        self.xy = xy_list

    def set_drawparams(self, evt):
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = float(self.walpha.get())
        fill = self.vfill.get() != 0

        params = {'color': color,
                  'alpha': alpha,
                  #'cap': 'ball',
                  }
        if kind in ('circle', 'rectangle', 'polygon', 'triangle',
                    'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha

        self.canvas.set_drawtype(kind, **params)


    def clear_canvas(self):
        self.canvas.deleteAllObjects()

#    
    def return_from_astrometry(self):
        return "voila"

    def button_click(self, viewer, button, data_x, data_y):
        print('pass', data_x, data_y)
        value = viewer.get_data(int(data_x + viewer.data_off),
                                int(data_y + viewer.data_off))
        print(value)
        # create crosshair
        tag = '_$nonpan_mark'
        radius = 10
        tf = 'True'
        color='red'
        canvas = viewer.get_private_canvas()
        try:
            mark = canvas.get_object_by_tag(tag)
            if not tf:
                canvas.delete_object_by_tag(tag)
            else:
                mark.color = color
    
        except KeyError:
            if tf:
                Point = canvas.get_draw_class('point')
                canvas.add(Point(data_x-264, data_y-258, radius, style='plus', color=color,
                                 coord='cartesian'),
                           redraw=True)#False)
    
        canvas.update_canvas(whence=3)

#        value = viewer.pick_hover(self, event, data_x, data_y, viewerpass)
        # If button is clicked, run this method and open window 2
            
    def Query_Simbad(self):
        from astroquery.simbad import Simbad                                                            
        from astropy.coordinates import SkyCoord
        from astropy import units as u
        coord = SkyCoord(self.string_RA_center.get()+'  '+self.string_DEC_center.get(),unit=(u.hourangle, u.deg), frame='fk5') 
#        coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5') 
        query_results = Simbad.query_region(coord)                                                      
        print(query_results)
    
    # =============================================================================
    # Download an image centered on the coordinates passed by the main window
    # 
    # =============================================================================
        from urllib.parse import urlencode
        from astropy.io import fits
        object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
        object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'], 
                                 unit=(u.hourangle, u.deg), frame='icrs')
        c = SkyCoord(self.string_RA_center.get(),self.string_DEC_center.get(), unit=(u.hourangle, u.deg))
        query_params = { 
             'hips': self.Survey_selected.get(), #'DSS', #
             #'object': object_main_id, 
             # Download an image centered on the first object in the results 
             #'ra': object_coords[0].ra.value, 
             #'dec': object_coords[0].dec.value, 
             'ra': c.ra.value, 
             'dec': c.dec.value,
             'fov': (3.5 * u.arcmin).to(u.deg).value, 
             'width': 528, 
             'height': 516 
             }                                                                                               
        
        url = f'http://alasky.u-strasbg.fr/hips-image-services/hips2fits?{urlencode(query_params)}' 
        hdul = fits.open(url)                                                                           
        # Downloading http://alasky.u-strasbg.fr/hips-image-services/hips2fits?hips=DSS&object=%5BT64%5D++7&ra=243.58457533549102&dec=-19.113364937196987&fov=0.03333333333333333&width=500&height=500
        #|==============================================================| 504k/504k (100.00%)         0s
        hdul.info()
        hdul.info()                                                                                     
        #Filename: /path/to/.astropy/cache/download/py3/ef660443b43c65e573ab96af03510e19
        #No.    Name      Ver    Type      Cards   Dimensions   Format
        #  0  PRIMARY       1 PrimaryHDU      22   (500, 500)   int16   
        print(hdul[0].header)                                                                                  
        # SIMPLE  =                    T / conforms to FITS standard                      
        # BITPIX  =                   16 / array data type                                
        # NAXIS   =                    2 / number of array dimensions                     
        # NAXIS1  =                  500                                                  
        # NAXIS2  =                  500                                                  
        # WCSAXES =                    2 / Number of coordinate axes                      
        # CRPIX1  =                250.0 / Pixel coordinate of reference point            
        # CRPIX2  =                250.0 / Pixel coordinate of reference point            
        # CDELT1  = -6.6666668547014E-05 / [deg] Coordinate increment at reference point  
        # CDELT2  =  6.6666668547014E-05 / [deg] Coordinate increment at reference point  
        # CUNIT1  = 'deg'                / Units of coordinate increment and value        
        # CUNIT2  = 'deg'                / Units of coordinate increment and value        
        # CTYPE1  = 'RA---TAN'           / Right ascension, gnomonic projection           
        # CTYPE2  = 'DEC--TAN'           / Declination, gnomonic projection               
        # CRVAL1  =           243.584534 / [deg] Coordinate value at reference point      
        # CRVAL2  =         -19.11335065 / [deg] Coordinate value at reference point      
        # LONPOLE =                180.0 / [deg] Native longitude of celestial pole       
        # LATPOLE =         -19.11335065 / [deg] Native latitude of celestial pole        
        # RADESYS = 'ICRS'               / Equatorial coordinate system                   
        # HISTORY Generated by CDS hips2fits service - See http://alasky.u-strasbg.fr/hips
        # HISTORY -image-services/hips2fits for details                                   
        # HISTORY From HiPS CDS/P/DSS2/NIR (DSS2 NIR (XI+IS))    
        self.image = hdul                                    
        hdul.writeto('./newtable.fits',overwrite=True)
        
    
                
        import aplpy
        from astropy.nddata import block_reduce
        gc = aplpy.FITSFigure(hdul)                                                                     
        gc.show_grayscale()                                                                             
    # =============================================================================
    # INFO: Auto-setting vmin to  2.560e+03 [aplpy.core]
    # INFO: Auto-setting vmax to  1.513e+04 [aplpy.core]
    # =============================================================================
        gc.show_markers(object_coords.ra, object_coords.dec, edgecolor='red',
                     marker='s', s=50**2)         
        gc.save('plot.png')
        
        
    def Query_Gaia(self):
        #Gaia coords are 2016.0
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.gaia import Gaia

        coord = SkyCoord(ra=self.string_RA_center.get(), dec=self.string_DEC_center.get(), unit=(u.hourangle, u.deg), frame='icrs')
        width = u.Quantity(0.1, u.deg)
        height = u.Quantity(0.1, u.deg)
        Gaia.ROW_LIMIT=200
        r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
        r.pprint()
        self.ra_Gaia = r['ra']
        self.dec_Gaia = r['dec']
        mag_Gaia = r['phot_g_mean_mag']
        print(self.ra_Gaia,self.dec_Gaia,mag_Gaia)
        print(len(self.ra_Gaia))
        self.Gaia_RADECtoXY(self.ra_Gaia,self.dec_Gaia)

    def Gaia_RADECtoXY(self, ra_Gaia, dec_Gaia):
        viewer=self.fitsimage
        image = viewer.get_image()
        x_Gaia = [] 
        y_Gaia = []
        i=0
        for i in range(len(ra_Gaia)):
            x, y = image.radectopix(ra_Gaia[i], dec_Gaia[i], format='str', coords='fits')
            x_Gaia.append(x)
            y_Gaia.append(y)
        print("GAIA: Converted RADEC to XY for display")    
        self.plot_gaia(x_Gaia, y_Gaia)

            
    def plot_gaia(self,x_Gaia,y_Gaia):
# =============================================================================
        viewer=self.fitsimage
#         if image is None:
#                 # No image loaded
#             return
#         x_Gaia, y_Gaia = image.radectopix(RA, DEC, format='str', coords='fits')
# 
# =============================================================================
        # create crosshair
        tag = '_$pan_mark'
        radius = 10
        color='red'
        canvas = viewer.get_private_canvas()
        print(x_Gaia, y_Gaia)
        mark = canvas.get_object_by_tag(tag)
        mark.color = color  
        Point = canvas.get_draw_class('point')
        i=0
        for i in range(len(x_Gaia)):
            canvas.add(Point(x_Gaia[i]-264, y_Gaia[i]-258, radius, style='plus', color=color,
                             coord='cartesian'),
                       redraw=True)#False)
    
        canvas.update_canvas(whence=3)
        print('plotted all', len(x_Gaia), 'sources')
        print(self.string_RA_list,self.string_DEC_list)
        self.Cross_Match()
        
    def Cross_Match(self):
        import numpy as np
        print(self.ra_Gaia,self.dec_Gaia,self.string_RA_list,self.string_DEC_list)
        ####----------
        ### from https://mail.python.org/pipermail/astropy/2012-May/001761.html
        from esutil import htm
        h = htm.HTM()
        maxrad=5.0/3600.0 
        m1,m2,radius = h.match( np.array(self.ra_Gaia), np.array(self.dec_Gaia), np.array(self.string_RA_list),np.array(self.string_DEC_list), maxrad)
        ####----------
        print(m1,m2)
        print((np.array(self.ra_Gaia)[m1]-np.array(self.string_RA_list)[m2])*3600)
        print((np.array(self.dec_Gaia)[m1]-np.array(self.string_DEC_list)[m2])*3600)
        g = [np.array(self.ra_Gaia)[m1],np.array(self.dec_Gaia)[m1]]
        s = [np.array(self.string_RA_list)[m2],np.array(self.string_DEC_list)[m2]]
        Gaia_pairs = np.reshape(g,(2,44))
        src = []
        for i in range(len(g[0])):
            src.append([g[0][i],g[1][i]])
            
        ####----------
        #create wcs
        #FROM https://docs.astropy.org/en/stable/api/astropy.wcs.utils.fit_wcs_from_points.html
        #xy   #   x & y pixel coordinates  (numpy.ndarray, numpy.ndarray) tuple
        coords = g
        #These come from Gaia, epoch 2015.5
        from astropy.coordinates import SkyCoord  # High-level coordinates
        from astropy.coordinates import ICRS, Galactic, FK4, FK5  # Low-level frames
        import astropy.units as u
        world_coords  = SkyCoord(src, frame=FK4, unit=(u.deg, u.deg), obstime="J2015.5")  
        from astropy.wcs.utils import fit_wcs_from_points
        xy  = ( (self.xy[0])[m2], (self.xy[1])[m2] ) 
        wcs = fit_wcs_from_points( xy, world_coords, proj_point='center',projection='TAN',sip_degree=3) 
        ####----------
        ### update fits file header
        ### from https://docs.astropy.org/en/stable/wcs/example_create_imaging.html
        
        # Three pixel coordinates of interest.
        # The pixel coordinates are pairs of [X, Y].
        # The "origin" argument indicates whether the input coordinates
        # are 0-based (as in Numpy arrays) or
        # 1-based (as in the FITS convention, for example coordinates
        # coming from DS9).
        pixcrd = np.array([[0, 0], [24, 38], [45, 98]], dtype=np.float64)
        
        # Convert pixel coordinates to world coordinates.
        # The second argument is "origin" -- in this case we're declaring we
        # have 0-based (Numpy-like) coordinates.    
        world = w.wcs_pix2world(pixcrd, 0)
        print(world)
 
        # Convert the same coordinates back to pixel coordinates.
        pixcrd2 = wcs.wcs_world2pix(world, 0)
        print(pixcrd2)
 
        # Now, write out the WCS object as a FITS header
        header = wcs.to_header()    

        # header is an astropy.io.fits.Header object.  We can use it to create a new
        # PrimaryHDU and write it to a file.
        from astropy.io import fits
        hdu = fits.PrimaryHDU(header=header)

        # Save to FITS file
        hdu.writeto('test.fits')

#Root window created. 
#Here, that would be the only window, but you can later have windows within windows.
#root = GUI_CCD()

#size of the window
#root.geometry("400x330")

#Then we actually create the instance.
#app = Tk.Window(root)    

#Finally, show it and begin the mainloop.
#root.mainloop()


