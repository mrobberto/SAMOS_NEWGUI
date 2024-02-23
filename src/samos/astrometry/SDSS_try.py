#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 25 17:35:59 2023

@author: samos_dev

from : https://github.com/behrouzz/sdss
"""
import copy
import os

from astropy import coordinates as coords
from astropy import units as u
from astropy.io import fits
from astroquery.sdss import SDSS
from scipy import ndimage

from samos.utilities import get_tmp_dir()


if __name__ == "__main__":
    out_dir = get_tmp_dir()

    ra = 179.689293428354
    dec = -0.454379056007667
    # *****
    # Should we have frame='icrs' as another argument below?
    pos = coords.SkyCoord(str(ra),str(dec), unit=(u.deg, u.deg))
    xid = SDSS.query_region(pos, radius='5 arcsec', spectro=True)
    print(xid)

    im = SDSS.get_images(matches=xid, band='g')

    hdu_0 = im[0]
    data = hdu_0[0].data
    header = hdu_0[0].header
    fits.writeto(os.path.join(cwd,'input_file.fits'), data, header, overwrite=True)

    data_rotated = ndimage.rotate(data, 270, reshape=True)

    header_rotated = copy.deepcopy(header)

    # *****
    # Is there a reason that tmp is being created here? It seems like, now that 
    # header_rotated is being deepcopied, it shouldn't be needed.
    tmp = header['NAXIS1'] ; header_rotated['NAXIS2'] = tmp
    tmp = header['NAXIS2'] ; header_rotated['NAXIS1'] = tmp
    tmp = header['CRPIX1'] ; header_rotated['CRPIX2'] = tmp
    tmp = header['CRPIX2'] ; header_rotated['CRPIX1'] = tmp
    tmp = header['CD1_1'] ; header_rotated['CD1_2'] = tmp
    tmp = header['CD1_2'] ; header_rotated['CD1_1'] = -tmp
    tmp = header['CD2_1'] ; header_rotated['CD2_2'] = tmp
    tmp = header['CD2_2'] ; header_rotated['CD2_1'] = -tmp

    fits.writeto(out_dir / 'output_file.fits', data_rotated, header_rotated, overwrite=True)

