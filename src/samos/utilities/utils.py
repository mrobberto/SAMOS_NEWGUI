"""
This module defines various utility functions, for loading/retrieving configuration data,
generating a path to find data files, etc.

Authors
-------

    - Brian York (york@stsci.edu)

Use
---

    This module is intended to be imported and its individual functions used on their own.

Dependencies
------------
    
    None.
"""
from astropy.coordinates import SkyCoord
from astropy import units as u
from datetime import datetime
import os
from pathlib import Path
import sys

from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from regions import Regions

from .constants import *


def get_data_file(mod_path, filename=None):
    """
    Returns the path to a data file given the calling module and the name of the file. 
    Raises a FileNotFoundError if the data file requested is not actually present at the 
    derived path.
    
    Parameters
    ----------
    mod_path : str
        Dotted module separators, e.g. samos.hadamard, that are converted into a path by 
        converting the dots to directory separators.
    filename : str, default None
        The name of the data file. If None, then this gets a path in the data directory 
        rather than a single file.
    
    Returns
    -------
    file_path : pathlib.Path
        Path to the file
    """
    # Start out by the general path to the data directory
    file_path = Path(__file__).parent.parent.absolute() / "data"
    
    for subpath in mod_path.split("."):
        if subpath != "samos":
            file_path = file_path / subpath
    if filename is not None:
        file_path = file_path / filename
    
    if not file_path.exists():
        raise FileNotFoundError("File {} does not exist".format(file_path))
    return file_path


def get_temporary_dir():
    """
    Return a Path to a directory for storing temporary files that shouldn't be included 
    by either github or the package installer.
    
    Returns
    -------
    dir_path : pathlib.Path
        Path to the directory
    """
    dir_path = Path(__file__).parent.parent.absolute() / "data" / "tmp"
    return dir_path


def get_fits_dir():
    """
    Returns a Path to a directory for storing FITS files (generally exposure outputs).
    Operates by the following rules:
    
    - If there is a "SAMOS_OUTPUTS" environment variable, store files there.
    - If there is a "SAMOS_STORE_TO_CWD" environment variable, store files in cwd
    - Store files in the SAMOS data.temporary directory
    
    In addition, makes sure that the directory *exists*, creates a daily directory 
    within the general FITS directory, and ensures that *that* directory exists.
    
    Returns
    -------
    fits_dir : pathlib.Path
        Path to today's FITS file output directory
    """
    today = datetime.now()
    
    if "SAMOS_FILES_LOCATION" in os.environ:
        if os.environ["SAMOS_FILES_LOCATION"] == "module":
            base_dir = get_temporary_dir()
        elif os.environ["SAMOS_FILES_LOCATION"] == "home":
            base_dir = Path.home()
        elif os.environ["SAMOS_FILES_LOCATION"] == "cwd":
            base_dir = Path.cwd()
        elif os.environ["SAMOS_FILES_LOCATION"] == "custom":
            if "SAMOS_CUSTOM_FILES_LOCATION" in os.environ:
                base_dir = Path(os.environ["SAMOS_CUSTOM_FILES_LOCATION"])
            else:
                base_dir = get_temporary_dir()
        else:
            base_dir = Path(os.environ["SAMOS_FILES_LOCATION"])
    else:
        base_dir = get_temporary_dir()
    
    fits_dir = base_dir / "SISI_images" / "SAMOS_{}".format(today.strftime('%Y%m%d'))
    fits_dir.mkdir(parents=True, exist_ok=True)
    
    fits_directory_file = get_temporary_dir() / "fits_current_dir_name.txt"
    with open(fits_directory_file, "w") as outf:
        outf.write("{}".format(fits_dir))
    
    return fits_dir


def ccd_to_dmd(ccd_x, ccd_y, wcs):
    dmd_x, dmd_y = wcs.pixel_to_world(ccd_x, ccd_y)
    return (dmd_x * 3600., dmd_y*3600. + CCD_DMD_Y_OFFSET)


def dmd_to_ccd(dmd_x, dmd_y, wcs):
    dmd_y -= CCD_DMD_Y_OFFSET
    dmd_coord = SkyCoord(dmd_x, dmd_y, unit=u.arcsec)
    ccd_x, ccd_y = wcs.world_to_pixel(dmd_coord)
    return ccd_x, ccd_y


# Contains a naive way of turning a slit array into a CSV file, included here because it's
# not actually used that I can see, but I want to keep it available for the moment.
#     def push_objects_to_slits(self):
#         self.logger.info("Creating DMD slit file")
#         save_file = ttk.filedialog.asksaveasfile(filetypes=[("txt file", ".pix")],
#                                                 defaultextension=".pix",
#                                                 initialdir=get_data_file("dmd.scv.maps"))
#         self.logger.info("Collecting current slits")
#         slit_shape = self.collect_slit_shape()
#         self.logger.info("Creating Slit Map file")
#         with open(save_file, "wt") as dmd_file:
#             for row_index in range(slit_shape.shape[0]):
#                 if not np.all(slit_shape[row_index]):
#                     # There are at least some zeros in this row
#                     column = 0
#                     gathering = False
#                     start_column = -1
#                     while column < slit_shape.shape[1]:
#                         if not gathering:
#                             while (column < slit_shape.shape[1]) and (slit_shape[row_index][column] == 1):
#                                 column += 1
#                             if slit_shape[row_index][column] == 0:
#                                 gathering = True
#                                 start_column = column
#                         else:
#                             while (column < slit_shape.shape[1]) and (slit_shape[row_index][column] == 0):
#                                 column += 1
#                             if (column == slit_shape[1]) or (slit_shape[row_index][column] == 1):
#                                 dmd_file.write(f"{start_column},{column},{row_index},{row_index},0\n")
#                                 gathering = False
