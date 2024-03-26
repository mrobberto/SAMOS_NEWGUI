"""
SAMOS Guide Star tk Frame Class
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
from tkinter import ttk
from tkinter.filedialog import askopenfilename

from samos.utilities import get_data_file, get_temporary_dir, get_fits_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame
from .gs_query_frame import GSQueryFrame


class GSPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Guide Star", **kwargs)
        self.main_fits_header.create_main_params_dict()
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        self.loaded_regfile = None
        self.fits_dir = get_fits_dir()

        # FITS manager
        frame = tk.LabelFrame(self.main_frame, text="FITS Manager", background="pink")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        # RA, DEC Entry box
        self.ra = tk.DoubleVar(self, 150.17110)
        tk.Label(frame, text="RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.ra).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.dec = tk.DoubleVar(self, -54.79004)
        tk.Label(frame, text="Dec:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.dec).grid(row=1, column=1, sticky=TK_STICKY_ALL)

        # QUERY Server
        self.gs_query_frame = GSQueryFrame(self.main_frame, self.ra, self.dec, self.run_query, self.logger)
        self.gs_query_frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)

        # GINGA DISPLAY
        frame = tk.LabelFrame(self.main_frame, text="Survey Image", relief=tk.RAISED)
        frame.grid(row=0, column=1, rowspan=4, sticky=TK_STICKY_ALL)
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
        self.drawing_canvas.set_drawtype('box', color='red')
        self.drawing_canvas.register_for_cursor_drawing(self.fits_image)
        self.drawing_canvas.add_callback('pick-up', self.pick_cb, 'up')
        self.drawing_canvas.set_draw_mode('pick')
        self.drawing_canvas.ui_set_active(True)
        self.fits_image.get_canvas().add(self.drawing_canvas)
        self.drawtypes = self.drawing_canvas.get_drawtypes()
        self.drawtypes.sort()
        self.fits_image.set_window_size(1028, 1044)
        self.readout = tk.Label(frame, text='')
        self.readout.grid(row=1, column=0, sticky=TK_STICKY_ALL)

        # Guide Star Pickup Frame
        frame = tk.LabelFrame(self.main_frame, text="Guide Star Pickup", font=BIGFONT)
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Low Mag (bright end)
        self.low_mag = tk.IntVar(self, 11)
        tk.Label(frame, text="Low Mag:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        s = tk.Spinbox(frame, increment=1, textvariable=self.low_mag, from_=0, to=25)
        s.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # High mag (faint end)
        tk.Label(frame, text="High Mag:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.high_mag = tk.IntVar(self, 13)
        s = tk.Spinbox(frame, increment=1, textvariable=self.high_mag, from_=0, to=25)
        s.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # SLIT POINTER ENABLED
        self.guide_star_pickup_enabled = tk.IntVar(self, 1)
        b = tk.Button(frame, text="Pick Guide Star", command=self.pick_guide_star)
        b.grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        # Candidate Guide Star Co-ordinates
        self.gs_ra = tk.DoubleVar(self, self.ra.get())
        tk.Label(frame, text="RA:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_ra).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.gs_dec = tk.DoubleVar(self, self.dec.get())
        tk.Label(frame, text="Dec:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_dec).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        # X Shift
        self.gs_xshift = tk.DoubleVar(self, 0.)
        tk.Label(frame, text="X Shift (mm)").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_xshift).grid(row=5, column=1, sticky=TK_STICKY_ALL)
        # Y Shift
        self.gs_yshift = tk.DoubleVar(self, -0.)
        tk.Label(frame, text="Y Shift (mm)").grid(row=6, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_yshift).grid(row=6, column=1, sticky=TK_STICKY_ALL)
        # Magnitude
        self.gs_mag = tk.DoubleVar(self, 0.0)
        tk.Label(frame, text="Magnitude:").grid(row=7, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.gs_mag).grid(row=7, column=1, sticky=TK_STICKY_ALL)
        b = tk.Button(frame, text="Accept Guide Star", command=self.send_RADEC_to_SOAR)
        b.grid(row=8, column=0, columnspan=2, sticky=TK_STICKY_ALL)

        # Ginga Tools Box
        frame = tk.LabelFrame(self.main_frame, text="Image Tools", font=BIGFONT)
        frame.grid(row=4, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.drawtypes = self.drawing_canvas.get_drawtypes()
        # W Draw (?)
        wdrawtype = tk.Entry(frame)
        wdrawtype.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        wdrawtype.insert(0, 'box')
        wdrawtype.bind("<Return>", self.set_drawparams)
        self.wdrawtype = wdrawtype
        # Draw Colour
        wdrawcolor = ttk.Combobox(frame, values=self.drawcolors, style="TCombobox")
        wdrawcolor.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        color_index = self.drawcolors.index('red')
        wdrawcolor.current(color_index)
        wdrawcolor.bind("<<ComboboxSelected>>", self.set_drawparams)
        self.wdrawcolor = wdrawcolor
        # Draw Fill
        self.vfill = tk.IntVar(self, 0)
        tk.Checkbutton(frame, text="Fill", variable=self.vfill).grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.walpha = tk.DoubleVar(self, 1.0)
        tk.Label(frame, text="Alpha:").grid(row=0, column=3, sticky=TK_STICKY_ALL)
        e = tk.Entry(frame, textvariable=self.walpha)
        e.grid(row=0, column=4, sticky=TK_STICKY_ALL)
        e.bind("<Return>", self.set_drawparams)
        # Buttons
        tk.Button(frame, text="Slits Only", command=self.slits_only).grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Clear Canvas", command=self.clear_canvas).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Save Canvas", command=self.save_canvas).grid(row=1, column=2, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Open Canvas", command=self.open_canvas).grid(row=1, column=3, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Save Image", command=self.save_gs).grid(row=1, column=4, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="Load Image", command=self.load_gs).grid(row=1, column=5, sticky=TK_STICKY_ALL)


    def set_drawparams(self, evt):
        kind = self.wdrawtype.get()
        color = self.wdrawcolor.get()
        alpha = self.walpha.get()
        fill = self.vfill.get() != 0
        params = {'color': color, 'alpha': alpha}
        if kind in ('circle', 'rectangle', 'polygon', 'triangle', 'righttriangle', 'ellipse', 'square', 'box'):
            params['fill'] = fill
            params['fillalpha'] = alpha
        self.drawing_canvas.set_drawtype(kind, **params)


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
            r.write(get_fits_dir() / "current_regions.reg", format='ds9')


    def clear_canvas(self):
        self.drawing_canvas.delete_all_objects(redraw=True)


    def send_RADEC_to_SOAR(self):
        self.logger.warning("send_RADEC_to_SOAR has not been implemented!")


    def run_query(self, catalog):
        self.catalog = catalog
        self.clear_canvas()
        self.logger.info("Setting local canvas")
        self.data_GS = self.catalog.image[0].data
        self.logger.info("Setting local header information")
        self.header_GS = self.catalog.image[0].header
        self.logger.info("Creating Local Image")
        self.image = AstroImage()
        self.image.load_hdu(self.catalog.image[0])
        self.fits_image.set_image(self.image)
        self.fits_image.rotate(self.PAR.Ginga_PA)
        self.table_full = self.catalog.table
        self.table_full.pprint_include_names = ('id', 'ra', 'dec', 'star_mag')


    def pick_guide_star(self):
        self.logger.info("Selecting Guide Star")
        self.clear_canvas()

        # Filter table by low and high magnitudes
        low_mag = self.low_mag.get()
        high_mag = self.high_mag.get()
        self.logger.info("Looking for stars with {} < mag < {}".format(low_mag, high_mag))
        self.logger.info("Initial table has {} sources".format(len(self.table_full)))
        self.table = self.table_full[(self.table_full['star_mag'] > low_mag) & (self.table_full['star_mag'] < high_mag)]
        self.logger.info("Final table has {} sources".format(len(self.table)))

        # For each remaining source, either reject it (for wrong location) or label it for potential selection
        image = self.fits_image.get_image()
        rows_to_drop = []
        gs_regions = Regions()
        Text = self.drawing_canvas.get_draw_class('Text')
        x_low, x_high = self.data_GS.shape[0]//4, 3*self.data_GS.shape[0]//4
        y_low, y_high = self.data_GS.shape[1]//4, 3*self.data_GS.shape[1]//4
        for row in self.table:
            x, y = image.radectopix(row['ra'], row['dec'], format='str', coords='fits')
            if ((x > x_low) and (x < x_high) and (y > y_low) and (y < y_high)):
                self.logger.info("Dropping source {} because too close to centre".format(row['id']))
                # Can't use a star in the very central region
                rows_to_drop.append(row['id'])
            elif ((x < 0) or (x > self.data_GS.shape[0]) or (y < 0) or (y > self.data_GS.shape[1])):
                self.logger.info("Dropping source {} because out of frame".format(row['id']))
                # Can't use a star that's outside the frame
                rows_to_drop.append(row['id'])
            else:
                self.logger.info("Adding source {} to potential guide star list".format(row['id']))
                region = CirclePixelRegion(center=PixCoord(x, y), radius=10)
                gs_regions.append(region)
                obj = r2g(region)
                obj.color = "red"
                obj.pickable = True
                obj.add_callback('pick-up', self.pick_cb, 'down')
                self.logger.info("Adding source with ID {}".format(row["id"]))
                self.drawing_canvas.add(obj, tag=f'@{row["id"]}')
                star_label = Text(x=x+5, y=y+5, text=f'{row["id"]}', color="red")
                star_label.fontsize = 25
                self.drawing_canvas.add(star_label)
        for object_id in rows_to_drop:
            self.table = self.table[self.table['id'] != object_id]
        self.logger.info("{} candidate guide stars".format(len(self.table)))
        self.logger.info("{}".format(self.table))

        #DRAW  THE YELLOW AREA OF SISI
        width, height = self.data_GS.shape[0]//2, self.data_GS.shape[1]//2
        box_region = RectanglePixelRegion(center=PixCoord(x=width, y=height), width=width, height=height, angle=0*u.deg)  
        obj = r2g(box_region)
        obj.color = "green"
        self.drawing_canvas.add(obj)


    def open_canvas(self):
        if hasattr(self, 'catalog') and (self.catalog.saved_regions is not None):
            self.clear_canvas()
            for region in enumerate(self.catalog.saved_regions):
                self.drawing_canvas.add(r2g(region))


    def slits_only(self):
        """ erase all objects in the canvas except slits (boxes) """
        # We want to remove everything but boxes
        kinds = ['point', 'circle', 'rectangle', 'polygon', 'triangle', 'righttriangle', 'ellipse', 'square']
        if CM.CompoundMixin.is_compound(self.drawing_canvas.objects):
            to_remove = CM.CompoundMixin.get_objects_by_kinds(self.drawing_canvas, kinds)
            CM.CompoundMixin.delete_objects(self.drawing_canvas, list(to_remove))


    def pick_cb(self, obj, canvas, event, pt, ptype):
        self.logger.info(f"User picked {ptype} with {obj.kind} at ({pt[0]:.2f}, {pt[1]:.2f})")

        try:
            self.logger.info("Clearing existing selection (if there is one)")
            canvas.get_object_by_tag(self.selected_obj_tag).color = 'red'
            canvas.clear_selected()
            print('unselect previous obj tag')
        except Exception as e:
            self.logger.info("No existing selection found")

        # Add selection
        canvas.select_add(obj.tag)
        self.selected_obj_tag = obj.tag
        obj.color = 'green'
        canvas.set_draw_mode('draw')
        canvas.set_draw_mode('pick')
        self.object_id = obj.tag.strip('@')
        self.logger.info("Selected source has ID {}".format(self.object_id))

        if ptype == 'up' or ptype == 'down':
            self.logger.info("Searching for object {} in table".format(self.object_id))
            row = self.table[self.table['id'] == self.object_id]
            self.logger.info("{}".format(row))
            self.gs_ra.set(row['ra'].value[0])
            self.gs_dec.set(row['dec'].value[0])
            delta_ra = (row['ra'].value[0] - self.ra.get()) * u.deg
            delta_ra_mm = delta_ra.to(u.arcsec) / SOAR_ARCS_MM_SCALE
            self.gs_xshift.set(delta_ra_mm.value)
            delta_dec = (row['dec'].value[0] - self.dec.get()) * u.deg
            delta_dec_mm = delta_dec.to(u.arcsec) / SOAR_ARCS_MM_SCALE
            self.gs_yshift.set(delta_dec_mm.value)
            self.gs_mag.set(row['star_mag'].value[0])
        return True


    def load_gs(self):
        gs_file = askopenfilename(initialdir=get_fits_dir(), title="Select Guide Star FITS File", 
                                  filetypes=(("FITS files", "*.fits"), ("all files", "*.*")))
        with fits.open(gs_file) as in_file:
            if "CAT_TYPE" not in in_file[0].header:
                self.logger.error("Tried to open guide star file not created by SAMOS!")
                raise ValueError("{} is not a valid Guide Star File!".format(gs_file))
            cat_type = in_file[0].header["CAT_TYPE"]
        if cat_type not in self.catalogs:
            self.logger.error("Invalid catalog type {}".format(cat_type))
            raise ValueError("Invalid Catalog type {}".format(cat_type))
        self.clear_canvas()
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
