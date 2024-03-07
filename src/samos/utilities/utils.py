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
from datetime import datetime
import os
from pathlib import Path
import sys

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
    
    if "SAMOS_OUTPUTS" in os.environ:
        base_dir = Path(os.environ["SAMOS_OUTPUTS"])
    elif "SAMOS_STORE_TO_CWD" in os.environ:
        base_dir = Path(os.getcwd())
    else:
        base_dir = get_temporary_dir()
    
    fits_dir = base_dir / "SISI_images" / "SAMOS_{}".format(today.strftime('%Y%m%d'))
    fits_dir.mkdir(parents=True, exist_ok=True)
    
    fits_directory_file = get_temporary_dir() / "fits_current_dir_name.txt"
    with open(fits_directory_file, "w") as outf:
        outf.write("{}".format(fits_dir))
    
    return fits_dir


def grid_sall(widget, sticky=TK_STICKY_ALL, **kwargs):
    """
    Effectively makes the default sticky value ALL
    """
    widget.grid(widget, sticky=sticky, **kwargs)
