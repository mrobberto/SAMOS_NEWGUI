"""
SAMOS Hadamard Generation tk Frame Class
"""
from astropy.io import fits
from astropy import units as u
from ginga.AstroImage import AstroImage
from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from ginga import colors
from ginga.canvas import CompoundMixin as CM
from ginga.canvas.CanvasObject import get_canvas_types
from ginga.tkw.ImageViewTk import CanvasView
from regions import PixCoord, CirclePixelRegion, RectanglePixelRegion, RectangleSkyRegion, Regions

import tkinter as tk
import ttkbootstrap as ttk
from tkinter.filedialog import askopenfilename

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

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
        w = ttk.Button(frame, text="Select Hadamard Centre", command=self.set_hadamard)
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Clear Display", command=self.clear_all)
        w.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Draw Hadamard Slits", command=self.draw_hadamard)
        w.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Load FITS File", command=self.load_fits)
        w.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # GINGA DISPLAY
        frame = ttk.LabelFrame(main_frame, text="Image", relief=tk.RAISED)
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

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)


    def load_ra_dec(self):
        """
        Load RA and DEC values from current image centre WCS
        """
        pass


    def set_hadamard(self):
        """
        Set Hadamard X/Y by clicking on the canvas
        """
        self.logger.info("Selecting Hadamard Centre")
        self.select_mode = True


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


    def draw_cb(self, canvas, tag):
        self.logger.info(f"User drew {tag} on {canvas}")
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
