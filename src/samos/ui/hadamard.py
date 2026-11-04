"""
SAMOS Hadamard Generation tk Frame Class
"""
import numpy as np
import os
from pathlib import Path
from datetime import datetime, timezone
# SC3_HTS_SELECT_EDIT_V8: editable approved boxes and FITS pointing fields.
# SC3_HTS_DISPLAYFIX_V2: show latest accessible SAMI FITS and constrain image area.
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
from samos.hadamard.multi_region import build_sequence, save_sequence  # SC3_HTS_MULTIBOX_V1


class HadamardPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Hadamard", **kwargs)
        self.canvas_types = get_canvas_types()
        self.drawcolors = colors.get_colors()
        self.loaded_regfile = None
        self.select_mode = False
        self.hts_centers = []  # APPROVED CCD centers, zero-based
        self.hts_lengths = []  # one DMD x-axis length per approved region
        self.hts_modes = []  # 'hadamard' or 'slitlet_scan', one per region
        self.hts_fixed = []  # fixed monitoring MOS slits (center, length, width)
        self.hts_approval_order = []  # undo chronological approval
        self.hts_pending_mode = None
        self.hts_pending_width = None
        self.hts_pending_length = None
        self.hts_pending_center = None
        self.hts_pending_box = None
        self.hts_confirmed = False
        self.hts_confirmed_signature = None
        self.hts_source_path = None
        self.hts_recent_dir = None
        # SC3_HTS_SELECT_EDIT_V8: stable IDs across edits/deletions.
        self.hts_scan_ids = []
        self.hts_fixed_ids = []
        self.hts_next_id = 1
        self.hts_selected = None      # ('scan'/'fixed', stable ID)
        self.hts_pending_origin = None  # selected existing region, or None for new
        self.hts_select_mode = False

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
        self.ra = self.make_db_var(tk.StringVar, "hadamard_ra", "150.171100")
        ttk.Label(frame, text="RA:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.ra).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.dec = self.make_db_var(tk.StringVar, "hadamard_dec", "-54.790040")
        ttk.Label(frame, text="Dec:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Entry(frame, textvariable=self.dec).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        w = ttk.Button(frame, text="Load from Current Image", command=self.load_ra_dec)
        w.grid(row=2, column=0, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.hts_coords_status = tk.StringVar(value='RA/Dec: enter survey-query center')
        ttk.Label(frame, textvariable=self.hts_coords_status,
                  wraplength=320).grid(row=3, column=0, columnspan=2,
                                       sticky=TK_STICKY_ALL)
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
        # Hadamard-only diagnostics; preserves the existing survey providers.
        self.gs_query_frame.run_query = self.hts_query_survey

        # Hadamard Sub-frame
        self.hadamard_conf_frame = HadamardGenerator(self, left_frame, **kwargs)
        self.hadamard_conf_frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.hadamard_conf_frame.grid_rowconfigure(0, weight=0)
        self.hadamard_conf_frame.grid_columnconfigure(0, weight=1)

        frame = ttk.LabelFrame(left_frame, text="Image Controls")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        frame.grid_columnconfigure(0, weight=1)
        # SC3_HTS_SELECT_EDIT_V8: explicit select, edit, approve and delete.
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)
        buttons = (
            ('New HTS Box', self.set_hadamard_now),
            ('New Slitlet Scan Box', self.hts_new_scan_box),
            ('New Fixed MOS Slit', self.hts_new_fixed_slit),
            ('Select / Edit Box', self.hts_select_box),
            ('Approve Box', self.hts_approve_box),
            ('Undo Box (Delete Selected)', self.hts_undo),
            ('Refresh Boxes', self.draw_hadamard),
            ('Clear Regions', self.hts_clear_confirm),
            ('Load FITS File', self.load_fits),
            ('Generate Masks (Offline)', self.generate_multi_hts),
        )
        for pos,(caption,callback) in enumerate(buttons):
            ttk.Button(frame, text=caption, command=callback).grid(
                row=pos//2, column=pos%2, padx=2, pady=2,
                sticky=TK_STICKY_ALL)
        fixed_options = ttk.Frame(frame)
        fixed_options.grid(row=5, column=0, columnspan=2,
                           sticky=TK_STICKY_ALL)
        self.hts_fixed_length_var = tk.IntVar(value=9)
        self.hts_fixed_width_var = tk.IntVar(value=3)
        ttk.Label(fixed_options,text='Fixed X (mirrors):').pack(side='left')
        tk.Entry(fixed_options,width=5,textvariable=self.hts_fixed_length_var).pack(side='left')
        ttk.Label(fixed_options,text='Y:').pack(side='left')
        tk.Entry(fixed_options,width=5,textvariable=self.hts_fixed_width_var).pack(side='left')
        self.hts_status = tk.StringVar(value='No regions selected')
        ttk.Label(frame,textvariable=self.hts_status,wraplength=450).grid(
            row=6,column=0,columnspan=2,sticky=TK_STICKY_ALL)

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
        # A conservative size: Ginga scales the image to the viewer, not its raw pixel dimensions.
        # Keep space for the controls on smaller remote-desktop windows.
        viewer_width = min(460, max(320, self.winfo_screenwidth() - 750))
        viewer_height = min(430, max(280, self.winfo_screenheight() - 320))
        # SC3_HTS_DISPLAYFIX_V3: fixed physical viewport, no grid stretching.
        # SC3_HTS_DISPLAYFIX_V4: use available screen space, with sensible caps.
        # Left controls take roughly 620 px on the current Mac layout.  The
        # viewer is ~700x600 on a 1400x1000 screen, but shrinks on smaller ones.
        # SC3_HTS_VIEWER_LARGE_V6: maximize usable right-side viewport.
        # Leave space for the controls and the macOS menu/title bars.
        viewer_width = max(440, min(1100, self.winfo_screenwidth() - 590))
        viewer_height = max(400, min(950, self.winfo_screenheight() - 165))
        viewer_holder = ttk.Frame(self.main_frame, width=viewer_width,
                                  height=viewer_height + 32)
        viewer_holder.grid(row=0, column=1, rowspan=8, columnspan=8,
                           sticky='nw', padx=5, pady=5)
        viewer_holder.grid_propagate(False)
        # Identifies the image in use even after box-selection status changes.
        self.hts_image_filename = tk.StringVar(value='Image: (none loaded)')
        ttk.Label(viewer_holder, textvariable=self.hts_image_filename,
                  anchor='w', font=('TkDefaultFont', 11, 'bold')).pack(
                      side='top', fill='x', padx=3, pady=(0, 3))
        canvas = tk.Canvas(viewer_holder, bg='grey', width=viewer_width,
                           height=viewer_height, highlightthickness=0,
                           borderwidth=0)
        canvas.pack(side='top', fill='both', expand=True)
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
        self.canvas.enable_draw(True)
        self.canvas.enable_edit(True)
        self.canvas.set_surface(fi)  # SC3_HTS_EDIT_BOXES_V6: required by Ginga EDIT mode
        self.canvas.easymove = True
        #self.canvas.set_drawtype(self.draw_type.get(), color='red')
        self.canvas.register_for_cursor_drawing(fi)
        self.canvas.add_callback('draw-event', self.draw_cb)
        self.canvas.add_callback('edit-event', self.hts_edit_cb)
        self.canvas.add_callback('cursor-up', self.hts_canvas_pick)
        self.canvas.set_draw_mode('pick')
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


    def _hts_sami_search_roots(self):
        """Only locally accessible directories; remote SAMI paths require mounting/copying."""
        roots=[]
        explicit=os.environ.get('SAMOS_SAMI_IMAGE_DIR', '').strip()
        if explicit:
            roots.append(Path(explicit).expanduser())
        for attr in ('fits_dir', 'output_dir'):
            value=getattr(self.PAR,attr,None)
            if value:
                roots.append(Path(value).expanduser())
        roots.append(Path('/home2/images'))
        distinct=[]
        for p in roots:
            if p.is_dir() and p.resolve() not in distinct:
                distinct.append(p.resolve())
        return distinct

    def _hts_latest_sami_fits(self):
        """Find the newest readable FITS file in known observing directories.

        Search root and immediate/date child directories only. A file on remote
        soarhrc is invisible until its directory is mounted or copied locally.
        """
        latest=None
        for root in self._hts_sami_search_roots():
            dirs=[root]
            try:
                dirs += [p for p in root.iterdir() if p.is_dir() and
                         (p.name.isdigit() or p.name.lower() in ('sami','images','fits'))]
            except OSError:
                continue
            for folder in dirs:
                try:
                    for p in folder.iterdir():
                        if p.is_file() and p.suffix.lower() in ('.fits','.fit','.fts'):
                            stat=p.stat()
                            if latest is None or stat.st_mtime_ns>latest[0]:
                                latest=(stat.st_mtime_ns,p)
                except (OSError,PermissionError):
                    continue
        return latest[1] if latest else None

    def load_ra_dec(self):
        """Latest accessible exposure, or chooser in that directory if absent."""
        from tkinter import messagebox
        roots = self._hts_sami_search_roots()
        newest = self._hts_latest_sami_fits()
        if newest is None:
            messagebox.showwarning('No recent FITS',
                'No FITS image found automatically. A file browser will open '
                'in the configured image directory so you can select an exposure.',
                parent=self)
            initial = roots[0] if roots else Path(getattr(self.PAR,'fits_dir',Path.home()))
        else:
            initial = newest.parent
        chosen = askopenfilename(
            initialdir=str(initial),
            initialfile=newest.name if newest is not None else None,
            title='Select current SAMI FITS image',
            filetypes=(('FITS images','*.fits *.fit *.fts'),('All files','*.*')),
            parent=self)
        if not chosen:
            return
        try:
            self.Display(chosen)
            self.hts_source_path=str(Path(chosen).resolve())
            self.hts_recent_dir=str(Path(chosen).resolve().parent)
            self.clear_all()
            self.hts_status.set('FITS loaded: '+Path(chosen).name+'; 0 boxes')
            self.logger.info('HTS current FITS displayed: %s',chosen)
        except Exception as exc:
            self.logger.exception('HTS FITS selection/display failed')
            messagebox.showerror('Cannot display FITS image',str(exc),parent=self)

    def hts_query_survey(self):
        """Same survey clients as shared GSQueryFrame, but expose actual errors."""
        from tkinter import messagebox
        q=self.gs_query_frame
        survey=q.survey_selected.get()
        try:
            survey_key=q.SURVEY_MAP[survey]
            ra=float(self.ra.get())
            dec=float(self.dec.get())
            band=q.survey_filter.get().strip()
            self.logger.info('HTS survey request: %s band %s at RA %.6f Dec %.6f',
                             survey, band, ra, dec)
            catalog=q.catalogs[survey_key](ra,dec,band,self.PAR,self.logger)
            catalog.run_query()
            if not getattr(catalog,'image',None):
                raise RuntimeError('Survey returned no FITS image')
            self.run_query(catalog)
            q.catalog=catalog
        except Exception as exc:
            self.logger.exception('HTS survey query failed: %s',survey)
            messagebox.showerror('Survey query failed',
                f'{survey} ({band}) could not be displayed.\n\n'
                f'{type(exc).__name__}: {exc}\n\n'
                'Check survey availability, coordinates and filter. '
                'You may also load a downloaded survey FITS with Load FITS File.',
                parent=self)

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
        self.hts_image_filename.set('FITS: ' + Path(imagefile).name)
        self._hts_set_radec_from_header(self.AstroImage.as_hdu().header,
                                        self.AstroImage.get_size())
        # The historical method calls toggle_compass which is not guaranteed
        # to exist on all SAMOS GUI versions; Ginga already displays the FITS.
        if hasattr(self, 'toggle_compass'):
            self.toggle_compass(show=False)
        
        
    # SC3_HTS_RADEC_HEADER_V8: FITS pointing metadata is separate from
    # the fixed CCD-DMD instrumental calibration; no WCS is modified here.
    def _hts_set_radec_from_header(self, header, image_size=None):
        """Populate survey-query fields from explicit FITS pointing or sky WCS.

        Missing coordinates clear both entries rather than retaining a stale
        pointing from a previously displayed image.
        """
        def parse_coord(value, is_ra):
            from astropy.coordinates import Angle
            if value is None or str(value).strip().upper() in ('', 'UNAVAIL','NONE'):
                raise ValueError('missing angle')
            v=str(value).strip()
            if ':' in v or any(k in v.lower() for k in ('h','m','s')):
                return float(Angle(v,unit=u.hourangle if is_ra else u.deg).degree)
            return float(v)
        pairs=(('RA','DEC'),('OBJRA','OBJDEC'),('TELRA','TELDEC'),
               ('OBSRA','OBSDEC'))
        coords=None
        for a,b in pairs:
            if a in header and b in header:
                try:
                    ra=parse_coord(header[a],True)
                    dec=parse_coord(header[b],False)
                    if np.isfinite([ra,dec]).all() and -90<=dec<=90:
                        coords=(ra%360.0,dec,a+'/'+b)
                        break
                except (TypeError,ValueError):
                    continue
        if coords is None:
            try:
                from astropy.wcs import WCS
                w=WCS(header).celestial
                if w.has_celestial:
                    if image_size is None:
                        nx=float(header['NAXIS1']);ny=float(header['NAXIS2'])
                    else:
                        nx,ny=map(float,image_size)
                    ra,dec=w.all_pix2world((nx-1)/2,(ny-1)/2,0)
                    if np.isfinite([ra,dec]).all() and -90<=float(dec)<=90:
                        coords=(float(ra)%360.0,float(dec),'celestial FITS WCS')
            except Exception:
                pass
        if coords is None:
            self.ra.set('')
            self.dec.set('')
            self.hts_coords_status.set('RA/Dec unavailable in FITS; enter center for survey query')
        else:
            ra,dec,origin=coords
            self.ra.set(f'{ra:.8f}')
            self.dec.set(f'{dec:.8f}')
            self.hts_coords_status.set(f'RA/Dec from {origin} (degrees)')

    # SC3_HTS_FIXED_AND_SLITLET_V7: editable scan regions + stationary MOS slitlets.
    def _hts_signature(self):
        conf = self.hadamard_conf_frame
        return (str(conf.sh_select.get()), int(conf.order.get()),
                int(conf.slit_width.get()), int(conf.slit_length.get()),
                tuple((float(x), float(y), int(length), mode)
                      for (x,y),length,mode in zip(self.hts_centers,
                                                   self.hts_lengths,self.hts_modes)),
                tuple((float(v['center'][0]),float(v['center'][1]),
                       int(v['length']),int(v['width'])) for v in self.hts_fixed))

    def _hts_shape(self, length=None):
        conf = self.hadamard_conf_frame
        width = int(conf.order.get()) * int(conf.slit_width.get())
        length = int(conf.slit_length.get()) if length is None else int(length)
        if not 1 <= length <= 1080 or not 1 <= width <= 2048:
            raise ValueError('Invalid scan rectangle dimensions')
        return length,width

    def _hts_dmd_xy(self, ccd_x, ccd_y):
        if self.PAR.dmd_wcs is None:
            raise ValueError('Gold CCD-DMD WCS is not loaded')
        wx, wy = self.PAR.dmd_wcs.all_pix2world(float(ccd_x),float(ccd_y),0)
        xy = np.asarray([wx,wy],dtype=float) * 3600.0
        if not np.isfinite(xy).all():
            raise ValueError('Non-finite DMD coordinates')
        return xy

    def _hts_geometry(self, ccd_x, ccd_y, length, width):
        """Exact native DMD rectangle and corresponding projected CCD corners."""
        length,width = int(length),int(width)
        if length < 1 or width < 1:
            raise ValueError('Region size must be positive')
        dx,dy = np.rint(self._hts_dmd_xy(ccd_x,ccd_y)).astype(int)
        x0, y0 = int(dx-length//2),int(dy-width//2)
        bounds = (x0,y0,x0+length,y0+width)
        corners = [(x0,y0),(x0+length,y0),(x0+length,y0+width),(x0,y0+width)]
        wx = np.asarray([a for a,b in corners],dtype=float) / 3600.0
        wy = np.asarray([b for a,b in corners],dtype=float) / 3600.0
        xx,yy = self.PAR.dmd_wcs.all_world2pix(wx,wy,0)
        points = list(zip(np.asarray(xx,float).tolist(),np.asarray(yy,float).tolist()))
        if not np.isfinite(np.asarray(points)).all():
            raise ValueError('Invalid projection of region corners')
        return bounds,points

    def _hts_box_geometry(self, ccd_x, ccd_y, length=None):
        length,width = self._hts_shape(length)
        return self._hts_geometry(ccd_x,ccd_y,length,width)

    def _hts_edit_scale(self, ccd_x, ccd_y):
        """Projected CCD radii/angle per DMD mirror, at this region center."""
        dmd_xy = self._hts_dmd_xy(ccd_x,ccd_y)
        xw = np.array([dmd_xy[0]-1,dmd_xy[0]+1,dmd_xy[0]]) / 3600.0
        yw = np.array([dmd_xy[1],dmd_xy[1],dmd_xy[1]+2]) / 3600.0
        xx,yy = self.PAR.dmd_wcs.all_world2pix(xw,yw,0)
        xx,yy = np.asarray(xx,float),np.asarray(yy,float)
        vx = np.array([xx[1]-xx[0],yy[1]-yy[0]])/2.0
        vy = np.array([xx[2]-xx[0],yy[2]-yy[0]])/2.0
        sx,sy = float(np.hypot(*vx)),float(np.hypot(*vy))
        angle = float(np.degrees(np.arctan2(vx[1],vx[0])))
        if not np.isfinite([sx,sy,angle]).all() or min(sx,sy) <= 0:
            raise ValueError('Invalid DMD-to-CCD local scale')
        return sx,sy,angle

    @staticmethod
    def _hts_overlap(a,b):
        return max(a[0],b[0]) < min(a[2],b[2]) and max(a[1],b[1]) < min(a[3],b[3])

    @staticmethod
    def _hts_within_dmd(b):
        return 0 <= b[0] < b[2] <= 1080 and 0 <= b[1] < b[3] <= 2048

    def _hts_validate_centers(self, centers, lengths=None, fixed_slits=None):
        if lengths is None:
            lengths = [int(self.hadamard_conf_frame.slit_length.get())]*len(centers)
        if len(lengths) != len(centers):
            raise ValueError('Scan region center/length mismatch')
        fixed_slits = self.hts_fixed if fixed_slits is None else fixed_slits
        entries=[]
        scan_bounds=[]
        for i,((x,y),length) in enumerate(zip(centers,lengths),1):
            b,_ = self._hts_box_geometry(x,y,length)
            if not self._hts_within_dmd(b):
                raise ValueError(f'Scan box {i} outside DMD: {b}')
            scan_bounds.append(b)
            entries.append(('scan',i,b))
        for i,v in enumerate(fixed_slits,1):
            b,_ = self._hts_geometry(*v['center'],v['length'],v['width'])
            if not self._hts_within_dmd(b):
                raise ValueError(f'Fixed slit {i} outside DMD: {b}')
            entries.append(('fixed',i,b))
        for i,(label,n,a) in enumerate(entries):
            for other_label,other_n,b in entries[:i]:
                if self._hts_overlap(a,b):
                    raise ValueError(f'{label} {n} overlaps {other_label} {other_n}')
        return scan_bounds

    def _hts_pending_from_canvas(self):
        obj = self.hts_pending_box
        if obj is None:
            return self.hts_pending_center
        cx,cy = tuple(map(float,obj.get_center_pt()))
        if not np.isfinite([cx,cy]).all():
            raise ValueError('Invalid editable box center')
        sx,sy,_ = self._hts_edit_scale(cx,cy)
        length = int(np.rint(2*abs(float(obj.xradius))/sx))
        self.hts_pending_length = max(1,min(1080,length))
        if self.hts_pending_mode == 'fixed_slit':
            width = int(np.rint(2*abs(float(obj.yradius))/sy))
            self.hts_pending_width = max(1,min(2048,width))
        else:
            self.hts_pending_width = self._hts_shape()[1]  # encoded width is fixed
            # If Ginga's Y resize handles were dragged, immediately restore
            # the coded height and the correct instrument-plane orientation.
            obj.yradius = sy * self.hts_pending_width / 2.0
            obj.rot_deg = self._hts_edit_scale(cx,cy)[2]
        self.hts_pending_center = (cx,cy)
        return self.hts_pending_center

    def _hts_begin_region(self, mode):
        from tkinter import messagebox
        if self.fits_image.get_image() is None:
            messagebox.showwarning('Load image','Load a FITS or survey image first.',parent=self)
            return
        if self.hts_pending_center is not None:
            messagebox.showwarning('Pending box','Approve or undo the current editable box first.',parent=self)
            return
        self.hts_confirmed = False
        self.hts_confirmed_signature = None
        try:
            image = self.fits_image.get_image()
            try:
                imw,imh = image.get_size()
            except AttributeError:
                imh,imw = image.get_data().shape[:2]
            cx,cy = (imw-1)/2.0,(imh-1)/2.0
            if mode == 'fixed_slit':
                length = int(self.hts_fixed_length_var.get())
                width = int(self.hts_fixed_width_var.get())
                self._hts_geometry(cx,cy,length,width)
            else:
                length,width = self._hts_shape()
                self._hts_box_geometry(cx,cy,length)
            self.hts_pending_center=(cx,cy)
            self.hts_pending_length=length
            self.hts_pending_width=width
            self.hts_pending_mode=mode
            self.hts_pending_origin=None
            self.hts_selected=None
            self.hts_select_mode=False
            self.draw_hadamard()
        except Exception as exc:
            self.hts_pending_center=None
            self.hts_pending_length=None
            self.hts_pending_width=None
            self.hts_pending_mode=None
            self.logger.exception('New scan/slit box failed')
            messagebox.showerror('Create region failed',str(exc),parent=self)

    def set_hadamard_now(self):
        self._hts_begin_region('hadamard')

    def hts_new_scan_box(self):
        self._hts_begin_region('slitlet_scan')

    def hts_new_fixed_slit(self):
        self._hts_begin_region('fixed_slit')

    def hts_select_box(self):
        """Enter click-to-reopen mode, including boxes already approved."""
        from tkinter import messagebox
        if self.hts_pending_center is not None:
            messagebox.showinfo('Editing','Approve or delete the active box first.',parent=self)
            return
        if not (self.hts_centers or self.hts_fixed):
            messagebox.showinfo('No boxes','Create a box first.',parent=self)
            return
        self.hts_select_mode=True
        self.canvas.set_draw_mode('pick')
        self.hts_status.set('Select / Edit: click an approved colored region')

    def hts_canvas_pick(self, canvas, *args):
        """Ginga cursor-up supplies (button, data_x, data_y) in CCD pixels."""
        if not self.hts_select_mode or self.hts_pending_center is not None or len(args)<3:
            return
        try:
            px,py=map(float,args[-2:])
            dx,dy=self._hts_dmd_xy(px,py)
            matches=[]
            for i,((cx,cy),length) in enumerate(zip(self.hts_centers,self.hts_lengths)):
                b,_=self._hts_box_geometry(cx,cy,length)
                if b[0]<=dx<b[2] and b[1]<=dy<b[3]:
                    matches.append(('scan',i))
            for i,slit in enumerate(self.hts_fixed):
                b,_=self._hts_geometry(*slit['center'],slit['length'],slit['width'])
                if b[0]<=dx<b[2] and b[1]<=dy<b[3]:
                    matches.append(('fixed',i))
            if matches:
                self._hts_edit_existing(*matches[-1])
            else:
                self.hts_status.set('No region at click; click inside an approved box')
        except Exception as exc:
            self.logger.exception('HTS selecting existing box failed')
            self.hts_status.set('Selection error: '+str(exc))

    def _hts_edit_existing(self, kind, index):
        """Open existing region in editable Ginga Box; keep its stable ID."""
        if self.hts_pending_center is not None:
            raise ValueError('Another region is currently being edited')
        if kind=='scan':
            self.hts_pending_center=tuple(self.hts_centers[index])
            self.hts_pending_length=int(self.hts_lengths[index])
            self.hts_pending_width=self._hts_shape()[1]
            self.hts_pending_mode=self.hts_modes[index]
            stable_id=self.hts_scan_ids[index]
        else:
            entry=self.hts_fixed[index]
            self.hts_pending_center=tuple(entry['center'])
            self.hts_pending_length=int(entry['length'])
            self.hts_pending_width=int(entry['width'])
            self.hts_pending_mode='fixed_slit'
            stable_id=self.hts_fixed_ids[index]
        self.hts_pending_origin=(kind,stable_id)
        self.hts_selected=(kind,stable_id)
        self.hts_select_mode=False
        self.hts_confirmed=False
        self.hts_confirmed_signature=None
        self.draw_hadamard()

    def _hts_lookup(self, kind, stable_id):
        ids=self.hts_scan_ids if kind=='scan' else self.hts_fixed_ids
        return ids.index(stable_id)

    def hts_edit_cb(self, canvas, obj):
        if obj is not self.hts_pending_box:
            return
        try:
            self._hts_pending_from_canvas()
            self.draw_hadamard()
        except Exception as exc:
            self.logger.exception('Ginga HTS region editing failed')
            self.hts_status.set('Region edit failed: '+str(exc))

    def draw_hadamard(self):
        """Editable active rectangle, approved color-coded immutable polygons."""
        from tkinter import messagebox
        colors={'hadamard':'yellow','slitlet_scan':'orange','fixed_slit':'cyan'}
        try:
            if self.hts_pending_box is not None:
                self._hts_pending_from_canvas()
            self.canvas.set_draw_mode('pick')
            self.canvas.clear_selected()
            self.canvas.delete_all_objects(redraw=False)
            self.hts_pending_box=None
            for i,((x,y),length,mode,stable_id) in enumerate(zip(
                    self.hts_centers,self.hts_lengths,self.hts_modes,self.hts_scan_ids)):
                if self.hts_pending_origin == ('scan',stable_id):
                    continue
                _,pts = self._hts_box_geometry(x,y,length)
                color=colors[mode]
                obj=self.canvas_types.Polygon(pts,color=color,linewidth=2)
                obj.editable=False
                self.canvas.add(obj,redraw=False)
                label=('H' if mode=='hadamard' else 'L')+str(stable_id)
                self.canvas.add(self.canvas_types.Text(float(pts[0][0]),float(pts[0][1]),
                         text=label,color=color,fontsize=12),redraw=False)
            for i,slit in enumerate(self.hts_fixed):
                stable_id=self.hts_fixed_ids[i]
                if self.hts_pending_origin == ('fixed',stable_id):
                    continue
                _,pts=self._hts_geometry(*slit['center'],slit['length'],slit['width'])
                obj=self.canvas_types.Polygon(pts,color='cyan',linewidth=2)
                obj.editable=False
                self.canvas.add(obj,redraw=False)
                self.canvas.add(self.canvas_types.Text(float(pts[0][0]),float(pts[0][1]),
                      text='F'+str(stable_id),color='cyan',fontsize=12),redraw=False)
            if self.hts_pending_center is not None:
                cx,cy=self.hts_pending_center
                length=int(self.hts_pending_length)
                width=(int(self.hts_pending_width) if self.hts_pending_mode=='fixed_slit'
                       else self._hts_shape()[1])
                sx,sy,angle=self._hts_edit_scale(cx,cy)
                editbox=self.canvas_types.Box(float(cx),float(cy),
                        sx*length/2.0,sy*width/2.0,rot_deg=angle,
                        color=colors[self.hts_pending_mode],linewidth=3)
                editbox.editable=True
                self.canvas.add(editbox,redraw=False)
                self.hts_pending_box=editbox
                self.canvas.set_draw_mode('edit')
                self.canvas.edit_select(editbox)
                text=('Resize X and Y' if self.hts_pending_mode=='fixed_slit'
                      else 'Move / resize X')
                self.hts_status.set(f'{len(self.hts_centers)} scan boxes, '
                    f'{len(self.hts_fixed)} fixed slits; {text}, then Approve Box')
            else:
                if self.hts_confirmed and self.hts_confirmed_signature!=self._hts_signature():
                    self.hts_confirmed=False
                    self.hts_confirmed_signature=None
                state='CONFIRMED' if self.hts_confirmed else 'not confirmed'
                self.hts_status.set(f'{len(self.hts_centers)} scan boxes, '
                     f'{len(self.hts_fixed)} fixed slits; {state}')
            self.canvas.update_canvas()
        except Exception as exc:
            self.logger.exception('HTS region display failed')
            messagebox.showerror('HTS display error',str(exc),parent=self)

    def hts_approve_box(self):
        from tkinter import messagebox
        if self.hts_pending_center is None:
            messagebox.showinfo('No active box','Create or select a box first.',parent=self)
            return
        try:
            center=self._hts_pending_from_canvas()
            length=int(self.hts_pending_length)
            mode=self.hts_pending_mode
            origin=self.hts_pending_origin
            if origin is None:
                stable_id=self.hts_next_id
            else:
                stable_id=origin[1]
            # Validate edited geometry against the other regions, excluding
            # its own previous footprint (otherwise it self-collides).
            scan_centers=list(self.hts_centers)
            scan_lengths=list(self.hts_lengths)
            fixed=list(self.hts_fixed)
            if origin is not None:
                old_kind,old_id=origin
                idx=self._hts_lookup(old_kind,old_id)
                if old_kind=='scan':
                    scan_centers.pop(idx);scan_lengths.pop(idx)
                else:
                    fixed.pop(idx)
            if mode=='fixed_slit':
                entry={'center':center,'length':length,'width':int(self.hts_pending_width)}
                self._hts_validate_centers(scan_centers,scan_lengths,fixed+[entry])
            else:
                self._hts_validate_centers(scan_centers+[center],scan_lengths+[length],fixed)
            if origin is None:
                self.hts_next_id+=1
                if mode=='fixed_slit':
                    self.hts_fixed.append(entry)
                    self.hts_fixed_ids.append(stable_id)
                else:
                    self.hts_centers.append(center)
                    self.hts_lengths.append(length)
                    self.hts_modes.append(mode)
                    self.hts_scan_ids.append(stable_id)
            else:
                kind,_=origin
                idx=self._hts_lookup(kind,stable_id)
                if kind=='fixed':
                    self.hts_fixed[idx]=entry
                else:
                    self.hts_centers[idx]=center
                    self.hts_lengths[idx]=length
        except Exception as exc:
            self.logger.exception('HTS box approval failed')
            messagebox.showerror('Cannot approve box',str(exc),parent=self)
            return
        self.hts_selected=('fixed' if mode=='fixed_slit' else 'scan',stable_id)
        self.hts_pending_center=None
        self.hts_pending_length=None
        self.hts_pending_width=None
        self.hts_pending_mode=None
        self.hts_pending_box=None
        self.hts_pending_origin=None
        self.hts_select_mode=False
        self.hts_confirmed=False
        self.hts_confirmed_signature=None
        self.draw_hadamard()

    def hts_undo(self):
        """Delete selected region only, never implicitly the most recent other box."""
        from tkinter import messagebox
        selection=self.hts_pending_origin or self.hts_selected
        # New pending box has no approved region to delete.
        self._hts_cancelled_pending = bool(self.hts_pending_center is not None and
                                           self.hts_pending_origin is None)
        if self._hts_cancelled_pending:
            selection=None
            self.hts_pending_center=None
        if selection is None and self.hts_pending_center is None:
            if self.hts_selected is None and self.hts_pending_mode is None:
                # An active new box is allowed to be cancelled.  An idle
                # page with nothing selected should leave all regions intact.
                if not getattr(self,'_hts_cancelled_pending',False):
                    messagebox.showinfo('No box selected',
                        'Choose Select / Edit Box and click a region to delete it.',parent=self)
                    return
        if selection is not None:
            kind,stable_id=selection
            idx=self._hts_lookup(kind,stable_id)
            if kind=='fixed':
                self.hts_fixed.pop(idx);self.hts_fixed_ids.pop(idx)
            else:
                self.hts_centers.pop(idx);self.hts_lengths.pop(idx)
                self.hts_modes.pop(idx);self.hts_scan_ids.pop(idx)
        self.hts_pending_center=None
        self.hts_pending_length=None
        self.hts_pending_width=None
        self.hts_pending_mode=None
        self.hts_pending_box=None
        self.hts_pending_origin=None
        self.hts_selected=None
        self.hts_select_mode=False
        self.hts_confirmed=False
        self.hts_confirmed_signature=None
        self._hts_cancelled_pending=False
        self.draw_hadamard()

    def hts_clear_confirm(self):
        from tkinter import messagebox
        if self.hts_centers or self.hts_fixed or self.hts_pending_center is not None:
            if not messagebox.askyesno('Clear all regions',
                 'Remove ALL approved and editable scan/slit regions?',parent=self):
                return
        self.clear_all()

    def clear_all(self):
        """Clear both scan and monitoring slit regions; preserve loaded FITS."""
        self.hts_centers.clear()
        self.hts_lengths.clear()
        self.hts_modes.clear()
        self.hts_fixed.clear()
        self.hts_scan_ids.clear()
        self.hts_fixed_ids.clear()
        self.hts_approval_order.clear()
        self.hts_selected=None
        self.hts_pending_origin=None
        self.hts_select_mode=False
        self.hts_pending_center=None
        self.hts_pending_length=None
        self.hts_pending_width=None
        self.hts_pending_mode=None
        self.hts_pending_box=None
        self.hts_confirmed=False
        self.hts_confirmed_signature=None
        self.canvas.set_draw_mode('pick')
        self.canvas.clear_selected()
        self.canvas.delete_all_objects(redraw=True)
        self.hts_status.set('0 scan boxes, 0 fixed slits; not confirmed')

    def hts_confirm_regions(self):
        from tkinter import messagebox
        if self.hts_pending_center is not None:
            messagebox.showwarning('Pending region','Approve or undo the editable region first.',parent=self)
            return
        if not self.hts_centers:
            messagebox.showwarning('No scan boxes',
                 'Approve at least one Hadamard or Slitlet Scan box.',parent=self)
            return
        try:
            self._hts_validate_centers(self.hts_centers,self.hts_lengths)
            if self.hadamard_conf_frame.sh_select.get()=='H' and 'slitlet_scan' in self.hts_modes:
                raise ValueError('Slitlet Scan requires S-matrix mode in this version')
            signature=self._hts_signature()
        except Exception as exc:
            messagebox.showerror('Cannot confirm regions',str(exc),parent=self)
            return
        self.hts_confirmed=True
        self.hts_confirmed_signature=signature
        self.draw_hadamard()
        messagebox.showinfo('Regions confirmed',
             f'{len(self.hts_centers)} scanning boxes, '
             f'{len(self.hts_fixed)} fixed monitoring slits confirmed.\n'
             'Generate Multi-Box HTS (Offline) to compose the sequence.',parent=self)

    def _hts_dmd_centers(self):
        if not self.hts_centers:
            raise ValueError('Approve at least one scanning box')
        xy=np.asarray(self.hts_centers,dtype=float)
        wx,wy=self.PAR.dmd_wcs.all_pix2world(xy[:,0],xy[:,1],0)
        coords=np.column_stack([np.asarray(wx,float)*3600.0,
                                np.asarray(wy,float)*3600.0])
        if not np.isfinite(coords).all():
            raise ValueError('Non-finite DMD scan centers')
        return coords

    def _hts_dmd_fixed(self):
        result=[]
        for slit in self.hts_fixed:
            x,y=self._hts_dmd_xy(*slit['center'])
            result.append({'dmd_center':[float(x),float(y)],
                           'length':int(slit['length']),
                           'width':int(slit['width'])})
        return result

    def generate_multi_hts(self):
        """Write offline-only masks; never call DMD.apply_shape()."""
        from tkinter import messagebox
        from datetime import datetime, timezone
        from pathlib import Path
        import hashlib
        try:
            if self.hts_pending_center is not None:
                raise ValueError('Approve or delete the active box first')
            if not self.hts_centers:
                raise ValueError('Approve at least one HTS or Slitlet Scan box')
            self._hts_validate_centers(self.hts_centers,self.hts_lengths,
                                       self.hts_fixed)
            if (self.hadamard_conf_frame.sh_select.get()=='H' and
                    'slitlet_scan' in self.hts_modes):
                raise ValueError('Slitlet Scan requires S-matrix mode')
            centers = self._hts_dmd_centers()
            conf = self.hadamard_conf_frame
            kind = conf.sh_select.get()
            order = int(conf.order.get())
            width = int(conf.slit_width.get())
            length = int(conf.slit_length.get())
            arrays, meta = build_sequence(centers,kind,order,width,length,
                       slit_lengths=self.hts_lengths,scan_modes=self.hts_modes,
                       fixed_slits=self._hts_dmd_fixed())
            meta['fixed_ccd_centers_zero_based'] = [
                list(v['center']) for v in self.hts_fixed]
            meta['scan_region_ids'] = list(self.hts_scan_ids)
            meta['fixed_region_ids'] = list(self.hts_fixed_ids)
            # Do not write an enormous set until the user accepts summary.
            n = len(arrays)
            if not messagebox.askyesno('Generate offline HTS sequence',
                 f'{len(centers)} scan boxes + {len(self.hts_fixed)} fixed slits, {kind}{order}; {n} full-field masks\n'
                 'No hardware commands will be sent. Continue?', parent=self):
                return
            # SC3_HTS_SEQUENCE_SIBLING_V9: keep HTS_sequences beside legacy mask_sets.
            archive = Path(get_data_file('hadamard.mask_sets')).parent / 'HTS_sequences'
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            folder = archive / f'hts_{kind}{order}_N{len(centers)}_{stamp}'
            gold_path = Path(get_data_file('dmd.convert','DMD_Mapping_WCS.fits'))
            gold_sha = hashlib.sha256(gold_path.read_bytes()).hexdigest()
            save_sequence(folder, arrays, meta,
                ccd_centers=[list(x) for x in self.hts_centers],
                image_path=self.hts_source_path, calibration_sha256=gold_sha)
            self.hts_status.set(f'Saved {n} OFFLINE masks in {folder.name}')
            messagebox.showinfo('HTS saved (not loaded)',
                f'Saved {n} masks and manifest to\n{folder}\n\n'
                'These masks have NOT been sent to the DMD.', parent=self)
        except Exception as exc:
            self.logger.exception('Multi-region HTS generation failed')
            messagebox.showerror('HTS generation failed',str(exc),parent=self)

    def load_fits(self):
        """Display FITS; discard previous region selections to prevent mismatches."""
        fits_path = askopenfilename(
            initialdir=self.hts_recent_dir or self.PAR.output_dir,
            title='Select a FITS image for HTS planning',
            filetypes=(('FITS files','*.fits *.fit *.fts'),('all files','*.*')))
        if not fits_path:
            return
        with fits.open(fits_path) as hdus:
            self._display_image(hdus[0])
            hdr = hdus[0].header.copy()
        self._hts_set_radec_from_header(hdr,self.image.get_size())
        self.hts_source_path = str(Path(fits_path).resolve())
        self.hts_recent_dir = str(Path(fits_path).resolve().parent)
        self.hts_image_filename.set('FITS: ' + Path(fits_path).name)
        self.clear_all()

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
        self.hts_source_path = 'SURVEY_QUERY'  # survey image is not a local FITS filename
        try:
            label = str(self.gs_query_frame.survey_selected.get())
            band = str(self.gs_query_frame.survey_filter.get()).strip()
            self.hts_image_filename.set(f'Survey: {label}  |  Filter: {band}')
        except Exception:
            self.hts_image_filename.set('Survey: image-server FITS')
        self.hts_coords_status.set('RA/Dec: survey query center (degrees)')
        self.hts_status.set('Survey query image displayed; 0 boxes')
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
        self.hts_image_filename.set('Guide-star FITS: ' + Path(gs_file).name)
        self._hts_set_radec_from_header(self.image.as_hdu().header, self.image.get_size())
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
