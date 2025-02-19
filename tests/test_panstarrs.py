#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 23:16:23 2023

@author: robberto
"""

from astropy.io import ascii
import numpy as np
from samos.astrometry-guide_stars import PanSTARRSGuideStar as PS_dr2cat
PS_dr2 = PS_dr2cat()


"""
Use metadata query to get information on available columns
This query works for any of the tables in the API (mean, stack, detection).
"""

meta = PS_dr2.ps_metadata("mean","dr2")
print(meta)

"""Simple positional query
Search mean object table with nDetections > 1.

This searches the mean object catalog for objects within 50 arcsec of M87 (RA=187.706, Dec=12.391 in degrees). Note that the results are restricted to objects with nDetections>1, where nDetections is the total number of times the object was detected on the single-epoch images in any filter at any time. Objects with nDetections=1 tend to be artifacts, so this is a quick way to eliminate most spurious objects from the catalog.
"""
ra = 187.706
dec = 12.391
radius = 50.0/3600.0
constraints = {'nDetections.gt':1}

# strip blanks and weed out blank and commented-out values
columns = """objID,raMean,decMean,nDetections,ng,nr,ni,nz,ny,
    gMeanPSFMag,rMeanPSFMag,iMeanPSFMag,zMeanPSFMag,yMeanPSFMag""".split(',')
columns = [x.strip() for x in columns]
columns = [x for x in columns if x and not x.startswith('#')]
results = PS_dr2.ps_cone(ra,dec,radius,release='dr2',columns=columns,verbose=True,**constraints)
# print first few lines
lines = results.split('\n')
print(len(lines),"rows in results -- first 5 rows:")
print('\n'.join(lines[:6]))
"""
https://catalogs.mast.stsci.edu/api/v0.1/panstarrs/dr2/mean.csv?nDetections.gt=1&ra=187.706&dec=12.391&radius=0.013888888888888888&columns=%5BobjID%2CraMean%2CdecMean%2CnDetections%2Cng%2Cnr%2Cni%2Cnz%2Cny%2CgMeanPSFMag%2CrMeanPSFMag%2CiMeanPSFMag%2CzMeanPSFMag%2CyMeanPSFMag%5D
47 rows in results -- first 5 rows:
objID,raMean,decMean,nDetections,ng,nr,ni,nz,ny,gMeanPSFMag,rMeanPSFMag,iMeanPSFMag,zMeanPSFMag,yMeanPSFMag
122881877112164157,187.71126262,12.40316813,2,0,0,2,0,0,-999.0,-999.0,19.040800094604492,-999.0,-999.0
122881877105204765,187.71049731,12.4035168,2,0,0,2,0,0,-999.0,-999.0,19.13680076599121,-999.0,-999.0
122881877095525205,187.70951703,12.40389466,2,0,0,2,0,0,-999.0,-999.0,18.8612003326416,-999.0,-999.0
122881877085143466,187.7085017546712,12.402395900723272,37,9,11,7,7,3,18.826099395751953,18.006799697875977,17.76689910888672,17.875099182128906,17.68120002746582
122851877124637737,187.7124557950916,12.38104290416518,50,9,10,15,9,7,19.32469940185547,18.029600143432617,17.798799514770508,17.930400848388672,17.508899688720703
"""

"""
Convert the results to an astropy table
The CSV results string is easily converted to an astropy table. This table is easily manipulated to extract information on individual columns or rows.
"""
tab = ascii.read(results)
# improve the format
for filter in 'grizy':
    col = filter+'MeanPSFMag'
    try:
        tab[col].format = ".4f"
        tab[col][tab[col] == -999.0] = np.nan
    except KeyError:
        print("{} not found".format(col))
print(tab)
