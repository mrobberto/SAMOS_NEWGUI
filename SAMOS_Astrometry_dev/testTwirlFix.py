import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.nddata import CCDData
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder

from astropy.coordinates import SkyCoord

from photutils.background import Background2D, MedianBackground


def find_stars(ccd):

    data = ccd.data
    mean, median, std = sigma_clipped_stats(data, sigma=3.0)
    daofind = DAOStarFinder(fwhm=5.0, threshold=3.*std)

    sources = daofind(data - median)
    for col in sources.colnames:
        if col not in ('id', 'npix'):
            sources[col].info.format = '%.2f'  # for consistent table output
    sources.pprint(max_width=76)
    
    return sources