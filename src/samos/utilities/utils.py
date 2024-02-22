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
import os
import sys

from pathlib import Path


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
