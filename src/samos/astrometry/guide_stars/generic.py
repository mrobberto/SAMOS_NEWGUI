"""
Defines Base guide star class for common interface and functionality
"""
from astropy import units as u
from astropy import coordinates as coords
from astropy.io import fits
from astropy.nddata import Cutout2D
from astropy.table import QTable
from astroquery.hips2fits import hips2fits
from copy import deepcopy
import numpy as np
from regions import Regions

from samos.utilities.constants import *

from .base import GuideStar


class GenericGuideStar(GuideStar):
    def __init__(self, ra, dec, band, survey, logger):
        super().__init__(ra, dec, band, survey, logger)
        self.selected_survey = survey


    def run_query(self):
        """
        Base class. Do whatever is needed to run a query and retrieve results.
        """
        pos = coords.SkyCoord(self.ra, self.dec, unit=(u.deg, u.deg))
        query_params = self.QUERY_PARAMS | {"CRVAL1": pos.ra.value, "CRVAL2": pos.dec.value}
        query_wcs = wcs.WCS(query_params)
        hdul = hips2fits.query_with_wcs(hips=survey, wcs=query_wcs, get_query_payload=False, format='fits')
        hdul[0].header["FILENAME"] = f"{self.survey}_{self.ra}_{self.dec}.fits"

        # We need to do an axis flip?
        data = hdul[0].data[:, ::-1]
        self.fits_image = fits.PrimaryHDU(data=data)
        self.fits_image.header.update(dict(query_wcs.to_header()))

        # NOTE that we're not setting the source table here?

    VALID_BANDS = ['g', 'r', 'i', 'z']
    QUERY_PARAMS = {
        "NAXIS1": 1056,
        "NAXIS2": 1032,
        "WCSAXES": 2,
        "CRPIX1": 1056,
        "CRPIX2": 1032,
        "CDELT1": SISI_PIXEL_SCALE.to(u.deg/u.pix).value,
        "CDELT2": SISI_PIXEL_SCALE.to(u.deg/u.pix).value,
        "CUNIT1": "deg",
        "CUNIT2": "deg",
        "CTYPE1": "RA---TAN",
        "CTYPE2": "DEC--TAN",
    }
