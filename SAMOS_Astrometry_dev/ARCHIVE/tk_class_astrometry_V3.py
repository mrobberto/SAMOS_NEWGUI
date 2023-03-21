#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec 30 10:49:37 2021

@author: robberto
"""
import tkinter as tk
from ginga.tkw.ImageViewTk import ImageViewCanvas
from ginga.AstroImage import AstroImage
from ginga.util import io_fits
from ginga.util.loader import load_data
from ginga.misc import log


class Astrometry(tk.Toplevel):     #the astrometry class inherits from the tk.Toplevel widget
#    def __init__(self, master=None):
    def __init__(self, master=None):  #__init__ constructor method. 
        #>>> AM = Astrometry(master) would be an instance of the class Astrometry that you can call with its functions, e.g.
        #>>> AM.show_Simbad()
    
        logger = log.get_logger("example1", log_stderr=True)
        self.logger = logger
        
        super().__init__(master = master) 
        #super() recalls and includes the __init__() of the master class (tk.Topelevel), so one can use that stuff there without copying the code.
        
        
        self.title("Astrometry")
        self.geometry("900x600")
        label = tk.Label(self, text ="This is the Astrometry Window")
        label.pack()

  
#       
        self.frame0l = tk.Frame(self,background="cyan")#, width=300, height=300)
        self.frame0l.place(x=0, y=0, anchor="nw", width=890, height=590)

# =============================================================================
#      ENTER COORDINATES
# 
# =============================================================================
        labelframe_EnterCoordinates =  tk.LabelFrame(self.frame0l, text="Enter Coordinates", 
                                                     width=300,height=140,
                                                     font=("Arial", 24))
        labelframe_EnterCoordinates.place(x=5,y=5)

        label_EnterRA =  tk.Label(labelframe_EnterCoordinates, text="RA")
        label_EnterRA.place(x=4,y=10)
        self.string_RA = tk.StringVar(value="00:00:00.0")
        entry_RA = tk.Entry(labelframe_EnterCoordinates, width=11,  bd =3, textvariable=self.string_RA)
        entry_RA.place(x=40, y=8)
        label_RA_template =  tk.Label(labelframe_EnterCoordinates, text="(HH:MM:SS.x)")
        label_RA_template.place(x=150,y=10)

        label_EnterDEC =  tk.Label(labelframe_EnterCoordinates, text="DEC")
        label_EnterDEC.place(x=4,y=40)
        self.string_DEC= tk.StringVar(value="+00:00:00.00")
        entry_DEC = tk.Entry(labelframe_EnterCoordinates, width=11,  bd =3, textvariable=self.string_DEC)
        entry_DEC.place(x=40, y=38)
        label_DEC_template =  tk.Label(labelframe_EnterCoordinates, text="(\u00b1DD:MM:SS.xx)")
        label_DEC_template.place(x=150,y=40)

        label_EnterEpoch =  tk.Label(labelframe_EnterCoordinates, text="Epoch")
        label_EnterEpoch.place(x=4,y=70)
        self.string_Epoch= tk.StringVar(value="2000.0")
        entry_Epoch = tk.Entry(labelframe_EnterCoordinates, width=6,  bd =3, textvariable=self.string_Epoch)
        entry_Epoch.place(x=40, y=68)
        label_Epoch_template =  tk.Label(labelframe_EnterCoordinates, text="e.g. 2000.0")
        label_Epoch_template.place(x=110,y=70)
  
        
# =============================================================================
#      QUERY SIMBAD
# 
# =============================================================================
        labelframe_Query_Simbad =  tk.LabelFrame(self.frame0l, text="Query Simbad", 
                                                     width=300,height=140,
                                                     font=("Arial", 24))
        labelframe_Query_Simbad.place(x=5,y=150)

        button_Query_Simbad =  tk.Button(labelframe_Query_Simbad, text="Query Simbad", bd=3, command=self.Query_Simbad)
        button_Query_Simbad.place(x=5,y=5)


        button_Show_Simbad =  tk.Button(labelframe_Query_Simbad, text="Show Simbad", bd=3, command=self.Show_Simbad)
        button_Show_Simbad.place(x=5,y=35)


        self.label_SelectSurvey = tk.Label(labelframe_Query_Simbad, text="Survey")
        self.label_SelectSurvey.place(x=100, y=35)
#        # Dropdown menu options
        Survey_options = [
             "DSS",
             "CDS/P/DSS2/red",
             "SDSS",
             "PanSTARRS",
             "2MASS",
             "GALEX",
             "AIIWISE"]
#        # datatype of menu text
        self.Survey_selected = tk.StringVar()
#        # initial menu text
        self.Survey_selected.set(Survey_options[0])
#        # Create Dropdown menu
        self.menu_Survey = tk.OptionMenu(labelframe_Query_Simbad, self.Survey_selected ,  *Survey_options)
        self.menu_Survey.place(x=160, y=35)

        print(self.Survey_selected.get())

        
        self.readout_Simbad = tk.Label(self.frame0l, text='')
# =============================================================================
#      QUERY Gaia
# 
# =============================================================================
        labelframe_Query_Gaia =  tk.LabelFrame(self.frame0l, text="Query Gaia", 
                                                     width=300,height=140,
                                                     font=("Arial", 24))
        labelframe_Query_Gaia.place(x=5,y=300)

        button_Query_Gaia =  tk.Button(labelframe_Query_Gaia, text="Query Gaia", bd=3, command=self.Query_Gaia)
        button_Query_Gaia.place(x=5,y=5)


# =============================================================================
# #           LAST TWO LINES
# =============================================================================

        self.hbox = tk.Frame(self.frame0l)
        self.hbox.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
#        self.hbox.place(x=0,y=560)
   
        self.readout_Simbad = tk.Label(self.frame0l, text='tbd')
        self.readout_Simbad.pack(side=tk.BOTTOM, fill=tk.X, expand=0)
#        self.readout_Simbad.place(x=0,y=530)


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
            canvas = tk.Canvas(self.frame0l, bg="grey", height=528, width=516)
#            canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            canvas.place(x=310,y=5)
                  
            fi = ImageViewCanvas(logger)
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

            fi.set_bg(0.2, 0.2, 0.2)
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

    def receive_radec(self,radec):
        self.string_RA.set(radec[0])
        self.string_DEC.set(radec[1])

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
        coord = SkyCoord(self.string_RA.get()+'  '+self.string_DEC.get(),unit=(u.hourangle, u.deg), frame='fk5') 
#        coord = SkyCoord('16 14 20.30000000 -19 06 48.1000000', unit=(u.hourangle, u.deg), frame='fk5') 
        query_results = Simbad.query_region(coord)                                                      
        print(query_results)
    
    # =============================================================================
    # Download an image centered on the first object in the results 
    # 
    # =============================================================================
        from urllib.parse import urlencode
        from astropy.io import fits
        object_main_id = query_results[0]['MAIN_ID']#.decode('ascii')
        object_coords = SkyCoord(ra=query_results['RA'], dec=query_results['DEC'], 
                                 unit=(u.hourangle, u.deg), frame='icrs')
        query_params = { 
             'hips': self.Survey_selected.get(), #'DSS', #
             'object': object_main_id, 
             'ra': object_coords[0].ra.value, 
             'dec': object_coords[0].dec.value, 
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
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.gaia import Gaia

        coord = SkyCoord(ra=self.string_RA.get(), dec=self.string_DEC.get(), unit=(u.hourangle, u.deg), frame='icrs')
        width = u.Quantity(0.1, u.deg)
        height = u.Quantity(0.1, u.deg)
        r = Gaia.query_object_async(coordinate=coord, width=width, height=height)
        r.pprint()
        ra_Gaia = r['ra']
        dec_Gaia = r['dec']
        mag_Gaia = r['phot_g_mean_mag']
        print(ra_Gaia,dec_Gaia,mag_Gaia)
        self.Gaia_RADECtoXY(ra_Gaia,dec_Gaia)

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
        print(x_Gaia,y_Gaia)    
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
        print('done')
    
 