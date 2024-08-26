"""
Defines Base guide star class for common interface and functionality
"""
from astropy import units as u
from astropy.io import fits
from astropy.table import QTable
from copy import deepcopy
import numpy as np
from regions import Regions

from samos.utilities import get_fits_dir
from samos.utilities.constants import *


class GuideStar():
    def __init__(self, ra, dec, band, catalog, logger):
        self.logger = logger
        self.catalog = catalog
        self.ra = ra
        self.dec = dec
        if band not in self.VALID_BANDS:
            self.logger.error("Invalid band {} for {} catalog".format(band, self.catalog))
            raise ValueError("Invalid band {} for {} catalog".format(band, self.catalog))
        self.band = band

        self.fits_image = None
        self.star_table = None
        self.saved_regions = None


    @classmethod
    def initFromFits(cls, fits_file, logger):
        """
        Creates a new catalog object from a FITS file saved by a catalog object.
        """
        with open(fits_file) as hdu:
            ra = hdu[0].header.get("CAT_RA", 0.)
            dec = hdu[0].header.get("CAT_DEC", 0.)
            band = hdu[0].header.get("CAT_BAND", 0.)
            cat = cls(ra, dec, band, logger)
            cat._from_hdu(hdu)
        return cat


    def run_query(self):
        """
        Base class. Do whatever is needed to run a query and retrieve results.
        """
        pass


    @property
    def image(self):
        """
        Base function to store the FITS image
        """
        return self.fits_image


    @property
    def table(self):
        """
        Base function to store the object table
        """
        return self.star_table


    def save(self, out_file):
        """
        Create a FITS file with the catalog image as the first extension, and the 
        catalog table as the second extension
        """
        hdul = self._to_hdu()
        hdul.writeto(get_fits_dir() / out_file)


    def load(self, fits_file):
        """
        Load a FITS file and turn it into a catalog image and catalog table.
        """
        with fits.open(fits_file) as hdu:
            self._from_hdu(hdu)


    def _to_hdu(self):
        output_columns = ["ra", "dec", "star_mag"]

        primary_header = deepcopy(self.fits_image[0].header)
        primary_header["CAT_TYPE"] = self.catalog
        primary_header["CAT_RA"] = self.ra
        primary_header["CAT_DEC"] = self.dec
        primary_header["CAT_BAND"] = self.band
        primary_hdu = fits.PrimaryHDU(header=primary_header, data=None)
        image_hdu = fits.ImageHDU(data=self.fits_image[0].data, header=self.fits_image[0].header)
        table_hdu = fits.BinTableHDU.from_columns(self.star_table[column] for column in output_columns)
        regions_string = self.saved_regions.serialize(format='ds9')
        # Get maximum length in the region array
        max_len = max([len(x) for x in regions_string.split('\n')])
        # Convert into a numpy array of strings
        region_array = np.array(regions_string.split('\n'))
        region_col = fits.Column(name='regions', format=f"{max_len}A", array=region_array)
        regions_hdu = fits.BinTableHDU.from_columns([region_col])
        hdul = fits.HDUList([primary_hdu, image_hdu, table_hdu, regions_hdu])
        return hdul


    def _from_hdu(self, hdu):
        if "CAT_TYPE" not in hdu[0].header:
            self.logger.error("Invalid input FITS file – no CAT_TYPE field in primary header!")
            raise ValueError("SAMOS {} Guide Star output file must have CAT_TYPE in primary header!".format(self.catalog))
        elif hdu[0].header["CAT_TYPE"] != self.catalog:
            self.logger.error("{} catalog asked to open file saved by {}".format(self.catalog, hdu[0].header["CAT_TYPE"]))
            raise ValueError("{} catalog can't open {} file type!".format(self.catalog, hdu[0].header["CAT_TYPE"]))
        self.fits_image = fits.ImageHDU(header=input_file[1].header, data=input_file[1].data)
        self.star_table = QTable.read(hdu, format='fits', hdu=2)
        self.saved_regions = Regions.parse('\n'.join(hdu[3].data['regions']), format='ds9')


    VALID_BANDS = []
