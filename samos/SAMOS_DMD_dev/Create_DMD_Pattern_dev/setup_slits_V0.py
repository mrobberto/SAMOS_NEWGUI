

import numpy as np
import pandas as pd
from astropy.table import Table, Column, QTable
from astropy.coordinates import SkyCoord
import astropy.units as u
from astroquery.gaia import Gaia 
from astroquery.vizier import Vizier
import math


class DMDSlit:

	def __init__(self, ra, dec, x0, y0, x1, y1, 
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



def DMD_Pattern_from_SlitList(target_table, wcs=None, ra_center=None, dec_center=None, slit_xsize=7, slit_ysize=3, pos_angle=0.):

	"""
	Given slit sizes/widths, and a list of targets, create a pattern 
	where source spectra won't overlap each other. 

	Input:
			target_table  - Table with targets.  Must have columns for RA and DEC in J2000d
			wcs           - WCS for transforming target coordinates to pixel/mirror  coordinate.  Default 
							is to create WCS for DMD directly.  Otherwise, can go from CCD pixels.
			slit_xsize    - int or array of ints representing length (in mirrors) of slit(s) in x-direction
			slit_ysize    - int or array ints representing the width (in mirrors) of slit(s) in y-direction.
		
	"""

	if len(target_table)>1:
		print("length > 1")
		target_table = target_table.sort_values(by="ra", ascending=False)


	if wcs is None:
		# or is it 3.1???  
		scale = 3.095*60./1080 # 3.095 arcmin fov projected over 1080x1080 mirrors

		mx_center = 540 #center x mirror of 1080x1080 array
		my_center = 540
		wcs = create_wcs(pixscale1=scale,pixscale2=scale, pos_angle=0., 
						naxis1=1080, naxis2=1080, crval1=ra_center, crval2=dec_center,
						crpix1=mx_center,crpix2=my_center)
	else:
		scale = np.abs(wcs.pixel_scale_matrix[0,0])*3600

	if (ra_center is None) and (dec_center is None):
		ra_center = (np.max(target_table['ra'])-np.min(target_table['ra'])) /2. + np.min(target_table['ra'])
		dec_center = (np.max(target_table['dec'])-np.min(target_table['dec'])) /2. + np.min(target_table['dec'])
	
	
	
	
	from astropy.wcs.utils import skycoord_to_pixel as sky2dmd

	
	slit_ra_centers = target_table['ra']
	slit_dec_centers = target_table['dec']


	half_slit_xsize = slit_xsize/2.
	half_slit_ysize = slit_ysize/2. 

	# I am referencing images from Strasburg and Aladin to write this. 
	# Those images are oriented such that RA decreases from left to right, 
	# which is why the input table and the left and right slit eges below 
	# are also sorted in order of decreasing RA.

	slit_edges_left = slit_ra_centers + (half_slit_xsize*scale / 3600.) #put into degrees bc that is unit of RA list
	slit_edges_right = slit_ra_centers - (half_slit_xsize*scale / 3600.) 

	
	slit_edges_top = slit_dec_centers + (half_slit_ysize*scale / 3600.)
	#print("tops",slit_edges_top)
	slit_edges_bottom = slit_dec_centers - (half_slit_ysize*scale / 3600.)

	#print(dmd_scale, slit_ra_centers,slit_edges_left)
	target_table['slit_edges_left'] = slit_edges_left
	target_table['slit_edges_right'] = slit_edges_right
	target_table['slit_edges_top'] = slit_edges_top
	target_table['slit_edges_bottom'] = slit_edges_bottom

	#center of mass of the targets system
	centerfield = (min(slit_edges_left)+max(slit_edges_left)) / 2.
	centerfield_dec = (min(slit_edges_bottom)+max(slit_edges_bottom)) / 2.
	#print("center_field ra,dec",centerfield,centerfield_dec)
	#range in mirrors of the targets
	range_mirrors = (max(slit_edges_left)-min(slit_edges_left))*3600./scale

	good_index = []
	mir_x = []
	mir_y = []
	mir_right = []
	mir_left = []
	mir_top = []
	mir_bottom = []
	dmd_slits = []
	j=0 
	slit_num = 0
	for i in range(len(target_table)-1):

		if i==0:
			print('accepting first target', i)
			good_index.append(i)
			ra, dec = target_table.loc[i, ['ra', 'dec']].values
			coords0 = SkyCoord(ra, dec,unit='deg')
			

			#print(coords0)
			dmd_coords = sky2dmd(coords=coords0, wcs=wcs) # center of target coords in dmd coords.
			dmd_xc, dmd_yc = dmd_coords
			try:
				half_slx = half_slit_xsize[i]
				half_sly = half_slit_ysize[i]
			except:
				half_slx = half_slit_xsize
				half_sly = half_slit_ysize
			ml = dmd_xc-half_slx
			mr = dmd_xc+half_slx
			mt = dmd_yc+half_sly
			mb = dmd_yc-half_sly

			print("append slit {}".format(i))
			mir_left.append(ml)
			mir_right.append(mr)
			mir_top.append(mt)
			mir_bottom.append(mb)
			mir_x.append(dmd_xc)
			mir_y.append(dmd_yc)

			dx1 = dmd_xc - ml 
			dx2 = mr - dmd_xc
			dy1 = mt - dmd_yc
			dy2 = dmd_yc - mb

		
			sl = DMDSlit(ra=ra,dec=dec, x=dmd_xc, y=dmd_yc, dx1=dx1, dx2=dx2, 
					 dy1=dy1, dy2=dy2, slit_n=slit_num)
			

			dmd_slits.append(sl)
			slit_num+=1
		
		if j-i >= 1: 
			continue

		j=i+1


		while ((target_table.iloc[j]['slit_edges_left'] > target_table.iloc[i]['slit_edges_right']) & (j<len(target_table)-1)):
								### '>' because images from Strasbourg decrease in RA from left to right.
			print('skipping target', j)
			#print(target_table.iloc[j]['slit_edges_left'], target_table.iloc[i]['slit_edges_right'])

			j+=1
		
		print('accepting target', j)
		print('\n')
		good_index.append(j)


		ra, dec = target_table.loc[j, ['ra', 'dec']].values
		coords0 = SkyCoord(ra, dec,unit='deg')

		dmd_xc, dmd_yc = sky2dmd(coords0, wcs) # center of target coords in dmd coords.

		try:
			half_slx = half_slit_xsize[j]
			half_sly = half_slit_ysize[j]
		except:
			half_slx = half_slit_xsize
			half_sly = half_slit_ysize
		ml = dmd_xc-half_slx
		mr = dmd_xc+half_slx
		mt = dmd_yc+half_sly
		mb = dmd_yc-half_sly

		print("append slit {}".format(j))
		mir_left.append(ml)
		mir_right.append(mr)
		mir_top.append(mt)
		mir_bottom.append(mb)
		mir_x.append(dmd_xc)
		mir_y.append(dmd_yc)
		

		dx1 = dmd_xc - ml 
		dx2 = mr - dmd_xc
		dy1 = mt - dmd_yc
		dy2 = dmd_yc - mb


	
		sl = DMDSlit(ra=ra,dec=dec, x=dmd_xc, y=dmd_yc, dx1=dx1, dx2=dx2, 
				 dy1=dy1, dy2=dy2, slit_n=slit_num)
		



		dmd_slits.append(sl)
		slit_num+=1
		
	dx1 = np.asarray(mir_x)-np.asarray(mir_left)
	dx2 = np.asarray(mir_right)-np.asarray(mir_x)
	dy1 = np.asarray(mir_top)-np.asarray(mir_y)
	dy2 = np.asarray(mir_y)-np.asarray(mir_bottom)

	pcols = ["target", "ra", "dec", "x", "y", "dx1", "dy1", "dx2", "dy2"]
	pdata = np.vstack((target_table.loc[good_index, 'DESIGNATION'].values,
					  target_table.loc[good_index, 'ra'].values, target_table.loc[good_index, 'dec'].values,
					  np.asarray(mir_x), np.asarray(mir_y), dx1, dy1, dx2, dy2)).T


	pattern_table = pd.DataFrame(data=pdata, columns=pcols)

	return pattern_table, dmd_slits, good_index