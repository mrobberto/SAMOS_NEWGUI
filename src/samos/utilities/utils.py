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
from platformdirs import user_config_dir
import sys

from ginga.util.ap_region import ginga_canvas_object_to_astropy_region as g2r
from ginga.util.ap_region import astropy_region_to_ginga_canvas_object as r2g
from regions import Regions

from .constants import *


def get_config_dir(app_name="SAMOS"):
    """
    Gets a (platform-correct) place to store preferences
    """
    pref_dir = user_config_dir(app_name)
    pref_path = Path(pref_dir)
    pref_path.mkdir(parents=True, exist_ok=True)
    return pref_path


def get_data_file(mod_path, filename=None, must_exist=True):
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
    
    if (not file_path.exists()) and (must_exist):
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


def ccd_to_dmd(ccd_x, ccd_y, wcs):
#    dmd_x, dmd_y = wcs.pixel_to_world(ccd_x, ccd_y)
    dmd_x = wcs.pixel_to_world(ccd_x, ccd_y).ra.value
    dmd_y = wcs.pixel_to_world(ccd_x, ccd_y).dec.value
    
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
