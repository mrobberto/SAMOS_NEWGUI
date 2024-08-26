"""
Defines Base guide star class for common interface and functionality
"""
from astropy import units as u
from astropy.io import ascii, fits
from astropy.table import QTable
from copy import deepcopy
import numpy as np
import pandas as pd
import re
import shutil
from tempfile import NamedTemporaryFile
import urllib.request

from samos.utilities import get_fits_dir, get_temporary_dir
from samos.utilities.constants import *

from .base import GuideStar


class SkyMapperGuideStar(GuideStar):
    def __init__(self, ra, dec, band, logger):
        super().__init__(ra, dec, band, "skymapper", logger)


    def run_query(self):
        """
        Do whatever is needed to run a query and retrieve results.
        """
        output_files = self.skymapper_interrogate(ra_size=SAMI_GUIDE_FOV_SISIPIX.value, dec_size=SAMI_GUIDE_FOV_SISIPIX.value)
        
        with fits.open(output_files[0]) as hdu:
            self.fits_image = deepcopy(hdu)
        
        url = "https://skymapper.anu.edu.au/sm-cone/public/query?RA={}&DEC={}&SR=0.06&RESPONSEFORMAT=CSV"
        query_url = url.format(self.ra, self.dec)
        with urllib.request.urlopen(query_url, timeout=30) as response:
            with open(get_fits_dir() / "skymapper_table.csv", "wb") as csv_file:
                shutil.copyfileobj(response, csv_file)
        self.star_table = ascii.read(get_fits_dir() / "skymapper_table.csv", format="csv")
        self.star_table["{}_psf".format(self.band)].name = "star_mag"
        self.star_table["raj2000"].name = "ra"
        self.star_table["dej2000"].name = "dec"
        self.star_table['id'] = ["{}".format(x) for x in range(len(self.star_table))]


    def skymapper_interrogate(self, ra_size=1058, dec_size=1032):
        """
        Query the skymapper.nci.org.au website for information on the supplied location. 
        If there are any matching images, further query skymapper to retrieve those 
        images, save them to a temporary location, and return paths to their location.

        Parameters
        ----------
        ra_size : int, default=1058
            Size of field in the RA direction (arcseconds). Default is magic.
        dec_size : int, default=1032
            Size of field in the DEC direction (arcseconds). Default is magic.

        Returns
        -------
        out_files : list
            List of file paths
        """
        pixel_scale = 0.18 * u.arcsec / u.pix
        out_dir = get_temporary_dir()

        # Handle formatting of values to proper units
        ra = self.ra * u.deg
        dec = self.dec * u.deg
        size_ra = (ra_size * u.pixel * pixel_scale).to(u.deg)
        size_dec = (dec_size * u.pixel * pixel_scale).to(u.deg)

        query = self.BASE_URL + "query?POS={},{}&SIZE={},{}&BAND={}&FORMAT=image/fits&INTERSECT=covers"
        query_url = query.format(ra.value, dec.value, size_ra.value, size_dec.value, self.band)

        self.logger.debug("Query URL is {}".format(query))

        with urllib.request.urlopen(query_url, timeout=30) as response:
           html = response.read()

        v=html.decode('utf-8')

        entrypoint = []
        [entrypoint.append(m.start()) for m in re.finditer(">SkyMapper_", v)]

        out_files = []
        for i in range(len(entrypoint)):
            image_number = v[entrypoint[i]+13:entrypoint[i]+30]

            image_url = self.BASE_URL + "get_image?IMAGE={}&SIZE={},{}&POS={},{}&BAND={}&FORMAT=fits"
            image_query = image_url.format(image_number, size_ra.value, size_dec.value, ra.value, dec.value, self.band)
            self.logger.info("Retrieving image at {}".format(image_query))

            out_file = out_dir / f"{image_number}.fits"

            # Fetching URLs
            with urllib.request.urlopen(image_query, timeout=30) as response:
                with open(out_file, 'wb') as of:
                    shutil.copyfileobj(response, of)

            with fits.open(out_file) as hdu_in:
                header = hdu_in[0].header

            if np.absolute(header['NAXIS1'] - header['NAXIS2']) > 1.:
                if  (ra_size != 1058) or (dec_size != 1032):
                    logger.error("Bad Image Size")
                    continue

            out_files.append(out_file)
        return out_files


    VALID_BANDS = ['u', 'v', 'g', 'r', 'i', 'z']
    BASE_URL = "https://api.skymapper.nci.org.au/public/siap/dr2/"
