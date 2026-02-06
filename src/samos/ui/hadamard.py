"""
SAMOS Hadamard Generation tk Frame Class
"""
import numpy as np
from astropy.io import fits
from astropy import units as u
from ginga.AstroImage import AstroImage
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
from ginga.util.loader import load_data
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions


from ginga.util import iqcalc
import tkinter as tk
import ttkbootstrap as ttk
from tkinter.filedialog import askopenfilename

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *
from samos.utilities.utils import ccd_to_dmd, dmd_to_ccd
from samos.ui.main_page import MainPage

from .common_frame import SAMOSFrame
from .gs_query_frame import GSQueryFrame
from .hadamard_subframe import HadamardGenerator


class HadamardPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Hadamard", **kwargs)
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        self.loaded_regfile = None
        self.select_mode = False

        left_frame = ttk.Frame(self.main_frame)
        left_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        left_frame.grid_columnconfigure(0, weight=1)

        main_frame = ttk.Frame(self.main_frame)
        main_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # FITS manager
        frame = ttk.LabelFrame(left_frame, text="Coordinates")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        # RA, DEC Entry box
        self.ra = self.make_db_var(tk.DoubleVar, "hadamard_ra", 150.17110)
        ttk.Label(frame, text="RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.ra).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.dec = self.make_db_var(tk.DoubleVar, "hadamard_dec", -54.79004)
        ttk.Label(frame, text="Dec:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.dec).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Load from Current Image", command=self.load_ra_dec)
        w.grid(row=2, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

        # QUERY Server
        self.gs_query_frame = GSQueryFrame(
            self,
            left_frame,
            self.run_query,
            "hadamard_ra",
            "hadamard_dec",
            **self.samos_classes
        )
        self.gs_query_frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.gs_query_frame.grid_rowconfigure(0, weight=0)
        self.gs_query_frame.grid_columnconfigure(0, weight=1)

        # Hadamard Sub-frame
        self.hadamard_conf_frame = HadamardGenerator(self, left_frame, **kwargs)
        self.hadamard_conf_frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.hadamard_conf_frame.grid_rowconfigure(0, weight=0)
        self.hadamard_conf_frame.grid_columnconfigure(0, weight=1)

        frame = ttk.LabelFrame(left_frame, text="Image Controls")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        frame.grid_columnconfigure(0, weight=1)
        w = ttk.Button(frame, text="Select Hadamard Centre", command=self.set_hadamard_now)
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Clear Display", command=self.clear_all)
        w.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Draw Hadamard Slits", command=self.draw_hadamard)
        w.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Load FITS File", command=self.load_fits)
        w.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        """
        # GINGA DISPLAY
        frame = ttk.LabelFrame(main_frame, text="Display", relief=tk.RAISED)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        frame.rowconfigure(0, minsize=800, weight=1)
        frame.columnconfigure(0, minsize=800, weight=1)
        self.ginga_canvas = tk.Canvas(frame, bg="grey", height=800, width=800)
        self.ginga_canvas.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.fits_image = CanvasView(self.logger)
        self.fits_image.set_widget(self.ginga_canvas)
        self.fits_image.enable_autocuts('on')
        self.fits_image.set_autocut_params('zscale')
        self.fits_image.enable_autozoom('on')
        self.fits_image.set_enter_focus(True)
        self.fits_image.set_bg(0.2, 0.2, 0.2)
        self.fits_image.ui_set_active(True)
        self.fits_image.show_pan_mark(True)
        self.fits_image.show_mode_indicator(True, corner='ur')
        self.fits_image.get_bindings().enable_all(True)
        self.drawing_canvas = self.canvas_types.DrawingCanvas()
        self.drawing_canvas.enable_draw(True)
        self.drawing_canvas.enable_edit(True)
        self.drawing_canvas.set_drawtype('crosshair', color='red')
        self.drawing_canvas.register_for_cursor_drawing(self.fits_image)
        self.drawing_canvas.add_callback('draw-event', self.draw_cb)
        self.drawing_canvas.set_draw_mode('pick')
        self.drawing_canvas.ui_set_active(True)
        self.fits_image.get_canvas().add(self.drawing_canvas)
        self.drawtypes = self.drawing_canvas.get_drawtypes()
        self.drawtypes.sort()
        self.current_object = None
        self.fits_image.set_window_size(1028, 1044)
        self.readout = ttk.Label(frame, text='')
        self.readout.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        frame.grid_rowconfigure(1, weight=0)
        """
        # FITS file markup canvas
        canvas = tk.Canvas(self.main_frame, bg="grey", width=528, height=516)
        canvas.grid(row=0, column=1, rowspan=8, columnspan=8, sticky=TK_STICKY_ALL, padx=5, pady=5)
        fi = CanvasView(self.logger)
        fi.set_widget(canvas)
        fi.enable_autocuts('on')
        fi.set_autocut_params('zscale')
        #fi.set_callback('cursor-changed', self.cursor_cb)
        fi.enable_autozoom('on')
        fi.set_enter_focus(True)
        fi.set_bg(0.2, 0.2, 0.2)
        fi.ui_set_active(True)
        fi.show_pan_mark(True)
        fi.show_mode_indicator(True, corner='ur')
        self.canvas = self.canvas_types.DrawingCanvas()
        self.canvas = self.canvas_types.DrawingCanvas()
        self.canvas.enable_draw(True)
        self.canvas.enable_edit(True)
        #self.canvas.set_drawtype(self.draw_type.get(), color='red')
        self.canvas.register_for_cursor_drawing(fi)
        self.canvas.add_callback('draw-event', self.draw_cb)
        self.canvas.add_callback('cursor-up', self.set_hadamard_now)
        self.canvas.set_draw_mode('draw')
        self.canvas.ui_set_active(True)
        fi.get_canvas().add(self.canvas)
        self.drawtypes = self.canvas.get_drawtypes()
        self.drawtypes.sort()
        self.fits_image = fi
        bd = fi.get_bindings()
        bd.enable_all(True)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)


    def load_ra_dec(self):
        """
        Load RA and DEC values from current image centre WCS
        """
        loaded_file = tk.filedialog.askopenfilename(
            title="Select a File",
            filetypes=(("fits files", "*.fits"), ("all files","*.*"))
        )
        self.fits_image_ql  = loaded_file
        self.Display(loaded_file)        
        return
        #pass

    def Display(self, imagefile):
        """
        Display the raw image arrived  from SAMI, still with the original Spectral Instruments FITS header""

        Parameters
        ----------
        imagefile : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        self.AstroImage = load_data(imagefile, logger=self.logger)
        self.fits_image.set_image(self.AstroImage)
        self.fits_image_ql = imagefile
        self.toggle_compass(show=False)
        
        
    def set_hadamard_now(self, canvas, PointEvent, x0, y0):
        """
        Set Hadamard X/Y by clicking on the canvas
        """
        self.logger.info(f"User inspecting target on canvas/n")
        
        #grab the pixel coordinates of the click
        coords = PixCoord(x0,y0)
        
        #create a region centered on that coordinates
        region = RectanglePixelRegion(center=coords, width=21, height=21, angle=0*u.deg)
        
        #conver to ginga object (type box)
        obj = r2g(region)
        
        #add to the canvas
        canvas.add(obj)
        """
        self.logger.info("Selecting Hadamard Centre")
        self.select_mode = True
        self.coords = PixCoord(x0,y0)
        print(self.coords)
        self.hadamard_conf_frame.slit_xc = self.coords[0]
        self.hadamard_conf_frame.slit_yc = self.coords[1]
        """

    def clear_all(self):
        """
        Clear the frame image and any slits
        """
        self.drawing_canvas.delete_all_objects(redraw=True)
        self.ginga_canvas.delete_all_objects(redraw=True)


    def draw_hadamard(self):
        """
        Draw the Hadamard slits on the canvas
        """
        pass


    def load_fits(self):
        """
        Load a FITS file into the display
        """
        fits_path = askopenfilename(
            initialdir=self.PAR.output_dir,
            title="Select a File",
            filetypes=(("FITS files", "*.fits"), ("all files", "*.*"))
        )
        with fits.open(fits_path) as in_file:
            self._display_image(in_file[0])


    def save_canvas(self):
        """
        Here we're converting the canvas objects into astropy regions, and saving them as 
        a FITS table, which is stored in the current catalog object (if available).
        """
        r = Regions()
        for canvas_object in self.drawing_canvas.get_objects():
            r.append(g2r(canvas_object))
        if hasattr(self, "catalog"):
            self.catalog.saved_regions = r
        else:
            r.write(self.PAR.fits_dir / "current_regions.reg", format='ds9')


    def run_query(self, catalog):
        self.catalog = catalog
        self.clear_all()
        self.logger.info("Setting local canvas")
        self.data_GS = self.catalog.image[0].data
        self.logger.info("Setting local header information")
        self.header_GS = self.catalog.image[0].header
        self.logger.info("Creating Local Image")
        self._display_image(self.catalog.image[0])
        self.table_full = self.catalog.table
        self.table_full.pprint_include_names = ('id', 'ra', 'dec', 'star_mag')

    def cursor_cb(self, viewer, button, data_x, data_y):
        """
        This gets called when the data position relative to the cursor changes.
        """
        # Start by checking if there's even an image to look at.
        #if viewer.get_image() is None:
        #    return

        # Get the value under the data coordinates
        try:
            # We report the value across the pixel, even though the coords
            # change halfway across the pixel
            value = viewer.get_data(int(data_x + viewer.data_off), int(data_y + viewer.data_off))
            value = f"{value:8g}"
        except Exception as e:
            value = "Invalid"

        fits_x = int(np.floor(data_x) + 1)
        fits_y = int(np.floor(data_y) + 1)
        text = f"FITS: ({fits_x:4d}, {fits_y:4d}). Value = {value}"
  


        dmd_x, dmd_y = ccd_to_dmd(fits_x, fits_y, self.PAR.dmd_wcs)
        dmd_x = int(np.floor(dmd_x))
        dmd_y = int(np.floor(dmd_y))
        text = f"DMD: ({dmd_x:7d}, {dmd_y:7d}). " + text
        print(text)



    def draw_cb(self, canvas, tag):
        self.logger.info(f"User drew {tag} on {canvas}")
        self.canvas.set_draw_mode("draw")
        
        obj = canvas.get_object_by_tag(tag)
        if not self.select_mode:
            canvas.delete_object(obj)
            return

        try:
            image = self.fits_image.get_image()
            x, y = obj.get_center_pt()
            self.logger.info(f"User selected {x}, {y}")
            self.hadamard_conf_frame.slit_xc.set(x)
            self.hadamard_conf_frame.slit_yc.set(y)
#             ra, dec = image.pixtoradec(x, y)
#             self.logger.info(f"User selected {ra}, {dec}")
            if self.current_object is not None:
                canvas.delete_object(self.current_object)
            self.current_object = obj
        except Exception as e:
            self.logger.error(f"Unable to select point because {e}")
            self.logger.exception(e)
            return


    def load_gs(self):
        title = "Select Guide Star FITS File"
        filetypes = (("FITS files", "*.fits"), ("all files", "*.*"))
        gs_file = askopenfilename(
            initialdir=self.PAR.fits_dir, title=title, filetypes=filetypes)
        with fits.open(gs_file) as in_file:
            if "CAT_TYPE" not in in_file[0].header:
                self.logger.error("Tried to open guide star file not created by SAMOS!")
                raise ValueError("{} is not a valid Guide Star File!".format(gs_file))
            cat_type = in_file[0].header["CAT_TYPE"]
        if cat_type not in self.catalogs:
            self.logger.error("Invalid catalog type {}".format(cat_type))
            raise ValueError("Invalid Catalog type {}".format(cat_type))
        self.clear_all()
        self.catalog = self.catalogs[cat_type].initFromFits(gs_file, self.logger)
        self.data_GS = self.catalog.image[0].data
        self.header_GS = self.catalog.image[0].header
        self.image = AstroImage()
        self.image.load_hdu(self.catalog.image[0])
        self.fits_image.set_image(self.image)
        self.fits_image.rotate(self.PAR.Ginga_PA)
        self.table_full = self.catalog.table
        self.table_full.pprint_include_names = ('id', 'ra', 'dec', 'star_mag')


    def save_gs(self):
        self.catalog.save("guidestar_{}.fits".format(self.catalog.catalog))


    def _display_image(self, hdu):
        """
        Display the provided HDU on the canvas
        """
        self.image = AstroImage()
        self.image.load_hdu(hdu)
        self.fits_image.set_image(self.image)
        self.fits_image.rotate(self.PAR.Ginga_PA)
