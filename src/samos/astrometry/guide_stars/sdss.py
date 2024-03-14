"""
Defines Base guide star class for common interface and functionality
"""
from astropy import units as u
from astropy import coordinates as coords
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.table import QTable
from astroquery.sdss import SDSS
from copy import deepcopy
import numpy as np
from regions import Regions

from samos.utilities import get_fits_dir
from samos.utilities.constants import *

from .base import GuideStar


class SDSSGuideStar(GuideStar):
    def __init__(self, ra, dec, band, logger):
        super().__init__(ra, dec, band, "sdss", logger)


    def run_query(self):
        """
        Base class. Do whatever is needed to run a query and retrieve results.
        """
        pos = coords.SkyCoord(self.ra, self.dec, unit=(u.deg, u.deg))
        image_array = SDSS.get_images(coordinates=pod, radius='170 arcsec', band=self.band)
        number_of_nans = 758*758
        for image in image_array:
            data = image[0].data
            header = image[0].header
            w = wcs.WCS(header)
            xc, yc = np.round(w.world_to_pixel(pos))
            position = (xc, yc)
            size = np.round((300/SDSS_PIXEL_SCALE.value, 300/SDSS_PIXEL_SCALE.value))
            try:
                cutout = Cutout2D(data, position, size, wcs=w, mode='partial')
            except Exception as e:
                # whatever the exception, all we want to do is skip this file
                continue
            if np.count_nonzero(np.isnan(cutout.data)) < number_of_nans:
                number_of_nans = np.count_nonzero(np.isnan(cutout.data))
                best_data = deepcopy(cutout.data)
                best_header = deepcopy(header)
                best_header.update(dict(cutout.wcs.to_header()))
        self.fits_image = fits.ImageHDU(header=best_header, data=best_data)

        self.star_table = SDSS.query_region(pos, fields={'ra', 'dec', f'psfMAG_{self.band}'}, radius=180*u.arcsec)
        self.star_table['id'] = ["{}".format(x) for x in range(len(self.star_table))]
        self.star_table[f'psfMAG_{self.band}'].name = "star_mag"


    VALID_BANDS = ['g', 'r', 'i', 'z']
