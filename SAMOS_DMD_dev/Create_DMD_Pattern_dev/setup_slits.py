

import numpy as np
import pandas as pd
from astropy.table import Table, Column, QTable
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.gaia import Gaia 
from astroquery.vizier import Vizier
import math

from ginga.util.iqcalc import IQCalc

from astropy.stats import mad_std, sigma_clipped_stats
from photutils.detection import IRAFStarFinder, DAOStarFinder
from skimage import util



import ap_region_massimoshacked as apreg
from regions import PixCoord, RectanglePixelRegion




def single_source_detector(image, fwhm, threshold):

	daofind = DAOStarFinder(fwhm=fwhm,threshold=threshold, brightest=1)
	daosources = daofind(image).to_pandas()

	x_guess, y_guess = daosources.loc[0,["xcentroid", "ycentroid"]]
	daosource = daosources.iloc[0]
	#print(x_guess, y_guess)
	#print(daosource)
	print(x_guess, y_guess)

	iqcalc = IQCalc()

	xc, yc = iqcalc.find_bright_peaks(data=image)[0]
	radius = image.shape[1]/2.
	#print(iqcalc.get_fwhm(x=xc,y=yc,radius=radius,data=image))
	fwhm_x, fwhm_y, xcent, ycent, fwhm_x_dict, fwhm_y_dict = iqcalc.get_fwhm(x=xc,y=yc,radius=radius,data=image)

	source_df = pd.DataFrame(data=np.array([[xcent, ycent, fwhm_x, fwhm_y]]),
							columns=["xcentroid", "ycentroid", "fwhm_x", "fwhm_y"])

	print(source_df)
	return source_df



def write_DMD_pattern(slit_table, save_pattern=False, pattern_name='pattern.png'):

	"""
	The columns used from the input table should be 
	object
	RA
	DEC
	dmd_xc
	dmd_yc
	dmd_x0
	dmd_y0
	dmd_x1
	dmd_y1

	First makes sure that the spectra won't overlap, so it saves the indices of 
	objects for which a different pattern needs to be made.
	I will make a loop that does it automatically.

	Pattern name can be user input from the GUI.
	"""
	slit_table = slit_table.sort_values(by="dmd_x0").reset_index(drop=True)

	left_mirs = []
	right_mirs = []
	upper_mirs = []
	lower_mirs = []
	dmd_dx0s = [] 
	dmd_dy0s = []
	dmd_dx1s = []
	dmd_dy1s = []
	good_index = []

	redo_index = []
	dmd_slits = []
	j = 0
	slit_num = 0
	for i in slit_table.index.values:
		if i==0:
			print('accepting first target', i)
			good_index.append(i)
			ra, dec = slit_table.loc[i, ['RA', 'DEC']].values
			coords0 = SkyCoord(90, 20,unit='deg')
			

			dmd_xc, dmd_yc = slit_table.loc[i, ["dmd_xc", "dmd_yc"]]
			dmd_x0, dmd_y0 = slit_table.loc[i, ["dmd_x0", "dmd_y0"]]
			dmd_x1, dmd_y1 = slit_table.loc[i, ["dmd_x1", "dmd_y1"]]


			print("append slit {}".format(i))
			left_mirs.append(dmd_x0)
			right_mirs.append(dmd_x1)
			upper_mirs.append(dmd_y0)
			lower_mirs.append(dmd_y1)
			

			dx0 = np.abs(dmd_xc-dmd_x0)
			dy0 = np.abs(dmd_yc-dmd_y0)
			dx1 = np.abs(dmd_x1-dmd_xc)
			dy1 = np.abs(dmd_y1-dmd_yc)

			dmd_dx0s.append(dx0)
			dmd_dy0s.append(dy0)
			dmd_dx1s.append(dx1)
			dmd_dy1s.append(dy1)
		
			sl = DMDSlit(ra=ra,dec=dec, xc=dmd_xc, yc=dmd_yc, x0=dmd_x0, x1=dmd_x1, 
					 y0=dmd_y0, y1=dmd_y1, slit_n=slit_num)
			

			dmd_slits.append(sl)
			slit_num+=1
		
		if j-i >= 1: 
			continue

		j=i+1

		if len(slit_table)<2:

			pcols = ["target", "ra", "dec", "dmd_xc", "dmd_yc", "dmd_dx0", "dmd_dy0", "dmd_dx1", "dmd_dy1"]
			pdata = np.vstack((slit_table.loc[i, 'object'],
					  slit_table.loc[i, 'RA'], slit_table.loc[i, 'DEC'],
					  slit_table.dmd_xc.values, slit_table.dmd_yc.values, np.array(dmd_dx0s), np.array(dmd_dy0s), 
					  np.array(dmd_dx1s), np.array(dmd_dy1s))).T


			pattern_table = pd.DataFrame(data=pdata, columns=pcols)
			return pattern_table, redo_index, bin_pattern

		if j<len(slit_table):
			#print(i, j)
			#continue

			while ((slit_table.iloc[j]['dmd_x0'] > slit_table.iloc[i]['dmd_x1']) & (j<len(slit_table)-1)):
									### '>' because images from Strasbourg decrease in RA from left to right.
				print('skipping target', j)
				#print(target_table.iloc[j]['slit_edges_left'], target_table.iloc[i]['slit_edges_right'])
				redo_index.append(j)
				j+=1
			
			print('accepting target', j)
			print('\n')
			good_index.append(j)


			ra, dec = slit_table.loc[j, ['RA', 'DEC']].values
			coords0 = SkyCoord(90, 20,unit='deg')


			dmd_xc, dmd_yc = slit_table.loc[j, ["dmd_xc", "dmd_yc"]]
			dmd_x0, dmd_y0 = slit_table.loc[j, ["dmd_x0", "dmd_y0"]]
			dmd_x1, dmd_y1 = slit_table.loc[j, ["dmd_x1", "dmd_y1"]]


			print("append slit {}".format(j))
			left_mirs.append(dmd_x0)
			right_mirs.append(dmd_x1)
			upper_mirs.append(dmd_y0)
			lower_mirs.append(dmd_y1)
			

			dx0 = np.abs(dmd_xc-dmd_x0)
			dy0 = np.abs(dmd_yc-dmd_y0)
			dx1 = np.abs(dmd_x1-dmd_xc)
			dy1 = np.abs(dmd_y1-dmd_yc)

			dmd_dx0s.append(dx0)
			dmd_dy0s.append(dy0)
			dmd_dx1s.append(dx1)
			dmd_dy1s.append(dy1)
		
			sl = DMDSlit(ra=ra,dec=dec, xc=dmd_xc, yc=dmd_yc, x0=dmd_x0, x1=dmd_x1, 
					 y0=dmd_y0, y1=dmd_y1, slit_n=slit_num)
			

			dmd_slits.append(sl)
			slit_num+=1


	pcols = ["target", "ra", "dec", "dmd_xc", "dmd_yc", "dmd_dx0", "dmd_dy0", "dmd_dx1", "dmd_dy1"]
	pdata = np.vstack((slit_table.loc[good_index, 'object'].values,
					  slit_table.loc[good_index, 'RA'].values, slit_table.loc[good_index, 'DEC'].values,
					  slit_table.loc[good_index, 'dmd_xc'], slit_table.loc[good_index, 'dmd_yc'], 
					  np.array(dmd_dx0s), np.array(dmd_dy0s), 
					  np.array(dmd_dx1s), np.array(dmd_dy1s))).T


	pattern_table = pd.DataFrame(data=pdata, columns=pcols)

	#### this line creates the actual png image which can be uploaded to the DMD ###
	bin_pattern = create_DMD_shape(pattern_table, save_pattern=save_pattern, pattern_save_name=pattern_name)

	return pattern_table, redo_index, bin_pattern

from PIL import Image
def create_DMD_shape(table, save_pattern=False, pattern_save_name='pattern.png',inverted=False):



    xoffset = 0#np.full(len(table.index),int(0))
    yoffset = np.full(len(table.index),int(2048/4))
    y1 = (np.around(table['dmd_yc'].values.astype(float))-np.floor(table['dmd_dy0'].values.astype(float))).astype(int) + yoffset
    y2 = (np.around(table['dmd_yc'].values.astype(float))+np.ceil(table['dmd_dy1'].values.astype(float))).astype(int) + yoffset
    x1 = (np.around(table['dmd_xc'].values.astype(float))-np.floor(table['dmd_dx0'].values.astype(float))).astype(int) + xoffset
    x2 = (np.around(table['dmd_xc'].values.astype(float))+np.ceil(table['dmd_dx1'].values.astype(float))).astype(int) + xoffset
    if inverted:
        dmd_shape = np.zeros((2048,1080))
        for i in table.index:
            dmd_shape[y1[i]:y2[i],x1[i]:x2[i]]=1
    else:
        dmd_shape = np.ones((2048,1080)) # This is the size of the DC2K
        for i in table.index:
            dmd_shape[y1[i]:y2[i],x1[i]:x2[i]]=0
    dmd_shape = np.uint8(dmd_shape) #test_shape.astype(np.uint8)

    print(pattern_save_name)
    if save_pattern:
    
        im_pattern = Image.fromarray(dmd_shape)
        im_pattern.save(pattern_save_name)
    
    return dmd_shape


class DMDSlit:

	def __init__(self, ra, dec, xc, yc, x0, y0, x1, y1, 
				slit_n=None):
		
		
		self.ra = ra  # ra [deg] of slit target center
		self.dec = dec # dec [deg] of slit target center
		
		x1 = x1-1
		y1 = y1-1

		self.x0 = x0
		self.y0 = y0
		self.x1 = x1
		self.y1 = y1

		dx = x1-x0
		dy = y1-y0

		self.dx = dx
		self.dy = dy

		
		dx = x1-x0
		dy = y1-y0
		
		
		xc = x0+math.floor(dx/2)
		dx0 = xc-x0
		dx1 = x1-xc

	
		yc = y0+math.floor((dy/2))
		dy0 = yc-y0
		dy1 = y1-yc


		self.xc = xc   #ra position in DMD mirrors
		self.yc = yc   #dec position in DMD mirrors
		self.dx0 = dx0 # left edge  : number of mirrors left of center
		self.dy0 = dy0 # lower edge : number of mirros below center
		self.dx1 = dx1 # right edge : number of mirrors right of center
		self.dy1 = dy1 # upper edge : number of mirrors above center

		

		#default slit width (y-direction) is 2 mirrors 
		self.slit_n = slit_n #slit number if slit is part of DMD pattern



