#! /usr/bin/env python
#
# example1_tk.py -- Simple, configurable FITS viewer.
#
# This is open-source software licensed under a BSD license.
# Please see the file LICENSE.txt for details.
#
import sys
import csv
from pathlib import Path
#define the local directory, absolute so it is not messed up when this is called
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())



import logging

from ginga.tkw.ImageViewTk import CanvasView
from ginga.util.loader import load_data

import tkinter as Tkinter
from tkinter.filedialog import askopenfilename

from skymapper_interrogate import skymapper_interrogate

STD_FORMAT = '%(asctime)s | %(levelname)1.1s | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s'


class SkyMapperLoader(object):

    def __init__(self, logger):

        self.logger = logger
        root = Tkinter.Tk()
        root.title("SkyMapper loader")
        self.root = root

        vbox = Tkinter.Frame(root, relief=Tkinter.RAISED, borderwidth=1)
        vbox.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=1)

        canvas2 = Tkinter.Canvas(vbox, bg="grey", height=512, width=512)
        canvas2.pack(side=Tkinter.TOP, fill=Tkinter.BOTH, expand=1)

        fi2 = CanvasView(logger)
        fi2.set_widget(canvas2)
        fi2.enable_autocuts('on')
        fi2.set_autocut_params('zscale')
        fi2.enable_autozoom('on')
        fi2.enable_auto_orient(True)
        fi2.set_bg(0.2, 0.2, 0.2)
        fi2.ui_set_active(True)
        # tk seems to not take focus with a click
        fi2.set_enter_focus(True)
        fi2.show_pan_mark(True)
        fi2.show_mode_indicator(True, corner='ur')
        self.fitsimage = fi2

        bd = fi2.get_bindings()
        bd.enable_pan(True)
        bd.enable_zoom(True)
        bd.enable_cuts(True)
        bd.enable_flip(True)
        bd.enable_cmap(True)
        bd.enable_rotate(True)

        fi2.configure(512, 512)

        hbox = Tkinter.Frame(root)
        hbox.pack(side=Tkinter.BOTTOM, fill=Tkinter.X, expand=0)

        self.string_RA = Tkinter.StringVar()
        self.string_RA.set("189.99763")
        label_RA = Tkinter.Label(hbox, text='RA:',  bd =3)
        entry_RA = Tkinter.Entry(hbox, width=11,  bd =3, textvariable = self.string_RA)
        
        self.string_DEC = Tkinter.StringVar()
        self.string_DEC.set("-11.62305")
        label_DEC = Tkinter.Label(hbox, text='Dec:',  bd =3)
        entry_DEC = Tkinter.Entry(hbox, width=11,  bd =3, textvariable = self.string_DEC)
        
        self.string_Filter = Tkinter.StringVar()
        self.string_Filter.set("i")
        label_Filter = Tkinter.Label(hbox, text='Filter:',  bd =3)
        entry_Filter = Tkinter.Entry(hbox, width=3,  bd =3,textvariable = self.string_Filter)

        wquery = Tkinter.Button(hbox, text="Query",
                               command=self.SkyMapper_query)

        wsave = Tkinter.Button(hbox, text="Save File",
                               command=self.save_file)
        wquit = Tkinter.Button(hbox, text="Quit",
                               command=lambda: self.quit(root))
        
        for w in (label_RA, entry_RA, label_DEC, entry_DEC, label_Filter, entry_Filter, wquery, wsave, wquit):
            w.pack(side=Tkinter.LEFT)

    def get_widget(self):
        return self.root

    def SkyMapper_query(self):
        from ginga.AstroImage import AstroImage
        from PIL import Image
        img = AstroImage()
        from astropy.io import fits
        Posx = self.string_RA.get()
        Posy = self.string_DEC.get()
        filt= self.string_Filter.get()
        filepath = skymapper_interrogate(Posx, Posy, filt)       
        with fits.open(filepath.name) as hdu_in:
#            img.load_hdu(hdu_in[0])
            data = hdu_in[0].data
            image_data = Image.fromarray(data)
            img_res = image_data.resize(size=(1032,1056))
            self.hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
            ra = Posx
            dec = Posy
            self.hdu_res.header['RA'] = ra
            self.hdu_res.header['DEC'] = dec

#            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
 #           hdu.writeto(rebinned_filename,overwrite=True)

            img.load_hdu(self.hdu_res)       

            self.fitsimage.set_image(img)
        
        #self.root.title(filepath)


    def save_file(self):
        from astropy.io import fits 
        fits.writeto("../fits_image/newimage_ff.fits",self.hdu_res.data,header=self.hdu_res.header,overwrite=True) 

    def open_file(self):
        filename = askopenfilename(filetypes=[("allfiles", "*"),
                                              ("fitsfiles", "*.fits")])
        self.load_file(filename)

    def quit(self, root):
        root.quit()
        root.destroy()
        return True


def main(options, args):

    logger = logging.getLogger("example1")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(STD_FORMAT)
    stderrHdlr = logging.StreamHandler()
    stderrHdlr.setFormatter(fmt)
    logger.addHandler(stderrHdlr)

    fv = SkyMapperLoader(logger)
    top = fv.get_widget()

    if len(args) > 0:
        fv.load_file(args[0])

    top.mainloop()


if __name__ == '__main__':
    main(None, sys.argv[1:])

# END
