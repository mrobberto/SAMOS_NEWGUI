#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 15:49:14 2025

@author: robberto
"""
from astroquery.simbad import Simbad 
from astroquery.vizier import Vizier
from astropy.coordinates import SkyCoord
#SkyCoord = SkyCoord()
import astropy.units as u
#import astropy.coordinates as coord
import os as os
import numpy as np
import pyvo as vo
from regions import RectangleSkyRegion, Regions

#SETUP THE DIRECTORY
cwd = os.getcwd()
parent_dir = os.path.abspath(os.path.join(cwd, os.pardir))



class Catalogs():
    Target_name = ""
    dir_name = ""
    radec_center =""
        
    def resolve_target_name_SIMBAD(self, Target_name_SIMBAD):
        """
        Parameters
        ----------
        Target_name_SIMBAD : TYPE
            DESCRIPTION.

        Returns
        -------
        self.Pos  TYPE : astropy SkyCoord, in deg, deg
            DESCRIPTION.

        """
 
        Target_name = Target_name_SIMBAD
        
        result_table = Simbad.query_object(Target_name)
 
        if result_table is None:
            print("> SIMBAD target name NOT found")
            return
        else:
            print("> SIMBAD target found")    
            print("> SIMBAD table:\n",result_table,'\n')
            ra = result_table['RA']
            dec = result_table['DEC']
            radec = SkyCoord(ra,dec,unit=(u.hourangle,u.deg), frame='icrs')[0]
            ra_deg = radec.ra.value ;# print(Posx.dtype)
            dec_deg = radec.dec.value;# print(Posy.dtype)
                
    
            print(ra_deg,dec_deg)
            self.Pos = SkyCoord(ra=ra_deg, dec=dec_deg, unit='deg')
                
            #print(radec_center.ra.value[0],radec_center.dec.value[0])
            #print(Posx)
            return self.Pos
           # dir_name = os.path.join(parent_dir, Target_name)
           # if not os.path.exists(dir_name):
           #     os.makedirs(dir_name)
           #     filename = Target_name+"_slits.reg"
           
           
    def query_region_Vizier_GAIA3(self, ra_DD, dec_DD, radius = 3):
        """
        

        Parameters
        ----------
        ra_DD : TYPE
            DESCRIPTION.
        dec_DD : TYPE
            DESCRIPTION.
        radius : TYPE, optional
            DESCRIPTION. The default is 3.

        Returns
        -------
        r : TYPE
            DESCRIPTION.

        """
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.gaia import Gaia
        
        Gaia.ROW_LIMIT = -1  # Ensure the default row limit.
        coord = SkyCoord(ra=ra_DD, dec=dec_DD, unit=(u.deg, u.deg), frame='icrs')
        j = Gaia.cone_search_async(coord, radius=u.Quantity(radius, u.arcmin))
        #INFO: Query finished. [astroquery.utils.tap.core]
        r = j.get_results()
        r.rename_column('phot_g_mean_mag', 'Gmag')
        r.rename_column('ra', 'RA')
        r.rename_column('dec', 'DEC')
        r.pprint()    
        return r
           

    def query_region_Vizier_table(self, ra_DD, dec_DD, radius = 3, table='II/246/out'):
        """
        Parameters
        ----------
        table: TYPE string
            DESCRIPTION: table to download, default 2MASS
        ra_DD : TYPE
            DESCRIPTION.
        dec_DD : TYPE
            DESCRIPTION.
        radius : TYPE, optional
            DESCRIPTION. The default is 2.
        Glim : TYPE, optional
            DESCRIPTION. The default is 19.

        Returns
        -------
        tablelist : TYPE
        
        DESCRIPTION.
        Query the VizieR web service for the specific published table/catalog, returning
        a table with all Gaia sources within a certain circular "radius", 
        down to a limit magnitude "Glim"
        
        from: https://astroquery.readthedocs.io/en/latest/vizier/vizier.html

        """
        center = SkyCoord( ra_DD, dec_DD, unit=(u.deg, u.deg),
                    frame='fk5')
        print(center)
        Vizier.ROW_LIMIT = -1
        tablelist = Vizier.query_region(center, catalog="II/246",
                                        radius=radius*u.arcmin)
                                        #table)
        return tablelist
    

    def get_2Mass_image(self,radec_center):
        # Lookup and define a service for 2MASS images
        
        # Start at STScI VAO Registry at https://vao.stsci.edu/keyword-search/
        # Limit by Publisher "NASA/IPAC Infrared Science Archive" and Capability Type "Simple Image Access Protocol" then search on "2MASS"
        # Locate the SIA URL https://irsa.ipac.caltech.edu/cgi-bin/2MASS/IM/nph-im_sia?type=at&ds=asky&
        #import pyvo as vo
        twomass_service = vo.dal.SIAService("https://irsa.ipac.caltech.edu/cgi-bin/2MASS/IM/nph-im_sia?type=at&ds=asky&")

        # Search the service
        # Search for images covering within 1 arcsecond of the star
        Pos=radec_center
        im_table = twomass_service.search(pos=Pos, size=1.0*u.arcsec)

        # for debug
        # Examine the table of images that is returned
        im_table.to_table()

        # Locate and download an image of interest
        #There are multiple images, we want to take the one that is centered closed to our target to get full field coverage
        #calculate the distances from tall the center images
        Posx = radec_center.ra.value ; print(Posx.dtype)
        Posy = radec_center.dec.value; print(Posy.dtype)
        d_from_center= np.sqrt( ( (im_table['center_ra']-Posx)/np.cos(im_table['center_dec']*u.deg))**2 +
                                (im_table['center_dec']-Posy)**2 )
        #check:
        print(d_from_center)


        #loop over the images to get the first one with the minimum distance
       # mini = d_from_center[0]
       # i_mini = 0
       # for i in range(len(im_table)):
       # #    print(i,d_from_center[i],mini)
       #     if d_from_center[i] < mini:
       #         mini = d_from_center[i]
       #         i_mini=i
                
        i_mini = int(np.argmin(d_from_center))      
        #print(i_mini)
        #print(im_table[i_mini].getdataurl())

        # Download the image and open it in Astropy
        from astropy.utils.data import download_file
        from astropy.io import fits
        fname = download_file(im_table[i_mini].getdataurl(), cache=True)
        image1 = fits.open(fname)
        filter=image1[0].header['FILTER']

        # Extract a cutout of 180"x180"
        from astropy.wcs import WCS
        wcs = WCS(image1[0].header)
        from astropy.nddata import Cutout2D
        cutout = Cutout2D(image1[0].data, Pos, (180, 180), wcs=wcs)
        #cutout.writeto(dir_name+"/Target_Field_2MASSradec_center[0].to_string()+".fits",overwrite=True)
        wcs = cutout.wcs

        # Put the cutout image in the FITS HDU
        # Update the FITS header with the cutout WCS
        hdu = fits.PrimaryHDU(data=cutout.data)
        hdu.header.update(cutout.wcs.to_header())
        hdu.data = cutout.data

        # Write the cutout to a new FITS file
        import os as os
        Target_name="NGC 3105"
        dir_name = os.path.join(parent_dir, Target_name)
        os.makedirs(dir_name, exist_ok=True)
        cutout_filename = dir_name+"/"+Target_name+"_2Mass_"+filter+"_"+radec_center.to_string()+".fits"
        hdu.writeto(cutout_filename, overwrite=True)


        #plot it...
        import matplotlib.pyplot as plt
        fig = plt.figure()
        # Create an ImageNormalize object using a SqrtStretch object
        vmin=np.nanmin(cutout.data)
        vmax=np.nanmax(cutout.data)
        from astropy.visualization import (MinMaxInterval, SqrtStretch, ImageNormalize)
        norm = ImageNormalize(vmin=vmin, vmax=vmax, stretch=SqrtStretch())
        ax = fig.add_subplot(1, 1, 1, projection=wcs)
        #ax.imshow(cutout.data, cmap='gray_r', origin='lower', norm=norm)
        im = ax.imshow(cutout.data, origin='lower', norm=norm)
        ax.scatter(Posx,Posy, transform=ax.get_transform('fk5'), s=500, edgecolor='red', facecolor='none')
        fig.colorbar(im)
        
        return ax,wcs
                    

    def Save_table_2_Astropy_slitregions(self,Target_name, ra,dec,it,Slit_Length_pix,Slit_Width_pix, pdtab, dir_name=None, filename=None):

    
        #sort by RA:
        #pdtab = pdtab.sort_values(by='RA')
    
        #print(pdtab['RA'],pdtab['DEC'])
        #pdtab = SimbadTable.to_pandas()
        # Determine the RADEC offset in degrees
        RA_Center = ra#np.mean(pdtab['RA'])
        DEC_Center = dec#np.mean(pdtab['DEC'])
    #    RA_Offsets = AstropyTable['RA'] - RA_Center
    #    DEC_Offsets = AstropyTable['DEC'] - DEC_Center
    #    print(np.c_[RA_Offsets[0:5], DEC_Offsets[0:5]]) #in degrees
        
        positions=[]
        for i in range(len(pdtab['RA'])):
            positions.append( (pdtab['RA'].iloc[i],pdtab['DEC'].iloc[i]) )
    
        coords =[SkyCoord(x,y, unit=(u.deg,u.deg), frame='fk5').to_string('decimal') for x,y in positions]
        #print(coords)
        
    #    RA_i=[]
    #    DEC_i=[]
    #    for i in range(len(coords)):
    #        ra,dec= coords[i].split(' ')
    #        RA_i.append(float(ra))
    #        DEC_i.append(float(dec))
    #    #print(RA_i,"\n",DEC_i)           
    #    RA_Center = np.mean(RA_i)
    #    DEC_Center = np.mean(DEC_i)
    #    #print(RA_Center, DEC_Center)
    
    
    ### HERE IS THE LINE THAT CHANGES WITH THE ORIENTATION OF THE GRATINGS
    ### WAS                                    
    #                                    width=0.18*Slit_Width_pix * u.arcsec, height=0.18* Slit_Length_pix * u.arcsec,
    ### IS                                    
        apregions = [RectangleSkyRegion(center=SkyCoord(x,y, unit=(u.deg, u.deg), frame='fk5'),#unit='deg', frame='fk5'),
                                      width=0.18*Slit_Length_pix* u.arcsec, height=0.18* Slit_Width_pix * u.arcsec,
                                      angle=0 * u.deg) for x,y in positions]
        slits = Regions(apregions)
        #print(slits[0])
    
        if filename is None:
            filename = Target_name+"-T"+"{:02d}".format(it)+"_RADEC="+str(round(RA_Center,7))+ '{0:+}'.format(round(DEC_Center,7))
    #    filename = Target+"_RADEC="+str(round(RA_Center,7))+ '{0:+}'.format(round(DEC_Center,7))+".reg"
    #    '{0:+} number'.format(1)
        os.path.join(dir_name,filename+".reg")
        slits.write(os.path.join(dir_name,filename+".reg"),overwrite=True, format='ds9')
        pdtab.to_csv(os.path.join(dir_name,filename+".csv"))
         
        print("\nSlits written to region file\n",filename)
        return slits  
    

        
    
    
    def query_region_SkyMapper(self, ra_DD, dec_DD, radius = 3):
        
        """
        SkyMapper TABLE CONSTRUCTION
        """
        #import urllib.request
        #import shutil
        string = "https://skymapper.anu.edu.au/sm-cone/public/query?"
        string += "RA=" + str(ra_DD) + "&"
        string += "DEC=" + str(dec_DD) + "&"
        string += "SR="+str(radius/60)+"&RESPONSEFORMAT=CSV"  #radius
        
        import urllib.request
        import tempfile
        import shutil
        import pandas as pd
        with urllib.request.urlopen(string,timeout=30) as response:
            with tempfile.NamedTemporaryFile(delete=False) as tmp_tblfile:
                shutil.copyfileobj(response, tmp_tblfile)
        skymapper_pandas_full = pd.read_csv(tmp_tblfile.name)
        #rename the magnitudes using the general band names
        skymapper_pandas_full = skymapper_pandas_full.rename(columns={"g_psf": "g_band","r_psf": "r_band","i_psf": "i_band","z_psf": "z_band","raj2000":"RA","dej2000":"DEC"})
        #return table_full
        
        print(skymapper_pandas_full)
        #Check
        print("there are ",len(skymapper_pandas_full)," sources")    

        return skymapper_pandas_full
    
    
       

    """
    ROUTINES BELOW NOT USED AT THE MOMENT
    """    
        

    def resolve_target_coordinates_SIMBAD(self, ra_DD, dec_DD):
        """
        

        Parameters
        ----------
        ra_DD : TYPE
            DESCRIPTION.
        dec_DD : TYPE
            DESCRIPTION.

        Returns
        -------
        table_1 : TYPE
        
        DESCRIPTION.

        """
        table_1 = Simbad.query_region(SkyCoord( ra_DD, dec_DD, unit=(u.deg, u.deg),
                   frame='fk5'), radius=180 * u.arcsec)
        return table_1
    


    def extract_astropy_table(self, Target_name_SIMBAD):
        Target_name = Target_name_SIMBAD
        
        result_table = Simbad.query_object(Target_name)
        if result_table is None:
            print("> SIMBAD target name NOT found")
            return
        else:
            print("> SIMBAD target found")   
            print(result_table.colnames)
            print(result_table)
        #    return
            ra = result_table['RA']
            dec = result_table['DEC']
            radec_center = SkyCoord(ra,dec,unit=(u.hourangle,u.deg), frame='icrs')[0]
            Posx = radec_center.ra.value ;# print(Posx.dtype)
            Posy = radec_center.dec.value;# print(Posy.dtype)
            print("> SIMBAD table:\n",result_table,'\n')
                
            #print(radec_center.ra.value)    
    
            ra = radec_center.ra.value ; #print(Posx.dtype)
            dec = radec_center.dec.value; #print(Posy.dtype)
            #print(ra,dec)
            self.Pos = SkyCoord(ra=Posx, dec=Posy, unit='deg')
                
            #print(radec_center.ra.value[0],radec_center.dec.value[0])
            #print(Posx)
            return self.Pos
            
    def skymapper_interrogate(self,POSx=189.99763, POSy=-11.62305, RA_Size=1058, DEC_Size=1032, filter='r'):
        POS = str(POSx)+","+str(POSy)   #"189.99763,-11.62305"
       # Sizex = np.round(0.18 / 3600 * RA_Size, 6)
       # Sizey = np.round(0.18 / 3600 * DEC_Size, 6)
        Sizex = 0.18 / 3600 * RA_Size
        Sizey = 0.18 / 3600 * DEC_Size
        SIZE = str(Sizex) + "," + str(Sizey)  #"0.05,0.1"
        FILTERS  = filter  #"g"#"g,r,i"
        string0= 'https://api.skymapper.nci.org.au/public/siap/dr2/'
        string = string0 + "query?"
        string += 'POS=' + POS + '&'
        string += 'SIZE=' + '0.05' + '&'   # first call to find the plate we use a small 5'x5' field
        string += 'BAND=' + FILTERS + '&'
        string += 'FORMAT=image/fits&INTERSECT=covers'#'&MJD_END=56970'#'&RESPONSEFORMAT=CSV'
        
        import urllib.request
        with urllib.request.urlopen(string,timeout=30) as response:
           html = response.read()
        #print(html)
        
        #v=pd.read_csv(html)
        v=html.decode('UTF-8')
        
        #entrypoint  = v.find("\nSkyMapper")   #use this if &RESPONSEFORMAT=CSV' works
        #image_number = v[entrypoint+13:entrypoint+30]
     
        entrypoint = []
        import re
        [entrypoint.append(m.start()) for m in re.finditer(">SkyMapper_", v)] 
    
        min_d = 100.
        i_min_d = 0
        best_image = ""
    
        for i in range(len(entrypoint)):
        #    entrypoint_old  = v.find(">SkyMapper_")
            image_number = v[entrypoint[i]+13:entrypoint[i]+30]
            #print("a",entrypoint,image_number)
            
            string = string0 + "get_image?"
            string += 'IMAGE='+image_number + '&'
            string += 'SIZE=' + SIZE + '&'
            string += 'POS=' + POS + '&'
            string += 'BAND=' + FILTERS + '&'
            string += 'FORMAT=fits'
    
            Sizex = 0.18 / 3600 * 1058
            Sizey = 0.18 / 3600 * 1038
            SIZE_SAMOS = str(Sizex) + "," + str(Sizey)  #"0.05,0.1"
            string_SAMOS = string0 + "get_image?"
            string_SAMOS += 'IMAGE='+image_number + '&'
            string_SAMOS += 'SIZE=' + SIZE_SAMOS + '&'
            string_SAMOS += 'POS=' + POS + '&'
            string_SAMOS += 'BAND=' + FILTERS + '&'
            string_SAMOS += 'FORMAT=fits'
            
            #print(string)
            #print(string_SAMOS)
            
            #https://api.skymapper.nci.org.au/public/siap/dr2/get_image?IMAGE=20140425124821-10&SIZE=0.05,0.1&POS=189.99763,-11.62305&BAND=g&FORMAT=fits
            #https://api.skymapper.nci.org.au/public/siap/dr2/get_image?IMAGE=20140425124821-10&SIZE=0.0833&POS=189.99763,-11.62305&FORMAT=png
            #string='https://api.skymapper.nci.org.au/public/siap/dr2/query?POS=150.17110,-54.79004&SIZE=0.052899999999999996,0.05159999999999999&BAND=i&FORMAT=image/fits&INTERSECT=covers&MJD_END=56970'
            """
            #Fetching URLs
            #FROM https://docs.python.org/3/howto/urllib2.html
            """
            import tempfile
            import shutil
            with urllib.request.urlopen(string,timeout=30) as response:
                #print("a")
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                #    print("b")
                    shutil.copyfileobj(response, tmp_file)
            with open(tmp_file.name) as html:
                #print("c")
                pass
                
            with urllib.request.urlopen(string_SAMOS,timeout=30) as response_SAMOS:
                #print("d")
                with tempfile.NamedTemporaryFile(delete=False) as tmp_file_SAMOS:
                #    print("e")
                    shutil.copyfileobj(response_SAMOS, tmp_file_SAMOS)
            with open(tmp_file_SAMOS.name) as html:
                #print("f")
            
                pass
            from astropy.wcs import WCS
            from astropy.io import fits
            hdu_in = fits.open(tmp_file.name)
            header = hdu_in[0].header
            #print(header)
            NAXIS1 = header['NAXIS1']
            NAXIS2 = header['NAXIS2']
            #import astropy.wcs as wcs
            #mywcs = wcs.WCS(header)
            mywcs = WCS(header)
            ra_center_skymapper, dec_center_skymapper = mywcs.all_pix2world([[NAXIS1/2,NAXIS2/2]], 0)[0]
            # Locate and download an image of interest
            #There are multiple images, we want to take the one that is centered closed to our target to get full field coverage
            #calculate the distances from tall the center images
            print(ra_center_skymapper,POSx,np.cos(dec_center_skymapper*u.deg),dec_center_skymapper,POSy)
            d_from_center= np.sqrt( ( (ra_center_skymapper-POSx)/np.cos(dec_center_skymapper*u.deg))**2 +
                            (dec_center_skymapper-POSy)**2 )
            #check:
            #print(d_from_center)
            #print(best_image)
            if d_from_center < min_d:
                min_d = d_from_center
                i_min_d=i
                best_image=tmp_file
                best_image_SAMOS = tmp_file_SAMOS
                print(best_image_SAMOS)
    
    
            #data = hdu_in[0].data
            
            #import astropy.wcs as wcs
            #mywcs = wcs.WCS(header)
            #ra, dec = mywcs.all_pix2world([[data.shape[0]/2,data.shape[1]/2]], 0)[0]
            #header['RA'] = ra
            #header['DEC'] = dec
            #fits.writeto(tmp_file, data, header=header, overwrite=True)
        #print(best_image.name)
        #print(best_image_SAMOS.name)
        self.SkyMapper_query(best_image_SAMOS,POSx,POSy)
        if ((RA_Size == 1058) and (DEC_Size == 1032)) or ((RA_Size == 2560) and (DEC_Size == 2560)):
            return(best_image)
        elif np.absolute(header['NAXIS1'] - header['NAXIS2']) <= 1:
            return(best_image)
            
    #    from astropy.io import fits
    #    hdu = fits.open(tmp_file.name)[0]
    #    image = hdu.data
    #    header = hdu.header
    #    return(hdu)
    """
        Inject image from SkyMapper to create a WCS solution using twirl
        """
    
    def SkyMapper_query(self,filepath,POSx,POSy):
        print("enter here")
        """ get image from SkyMapper """
        #print("aa",filepath.name)
    
        #img = AstroImage()
        #Posx = str(radec_center.ra.value[0])
        #Posy = str(radec_center.dec.value[0])
        #filt ="g"
        #filepath = skymapper_interrogate(Posx, Posy, 1058, 1032, filt)
        # filepath = skymapper_interrogate_VOTABLE(Posx, Posy, filt)'
        
        from astropy.io import fits
        hdu_in = fits.open(filepath.name)
        #            img.load_hdu(hdu_in[0])
        data = hdu_in[0].data
        from PIL import Image
        image_data = Image.fromarray(data)
        img_res = image_data.resize(size=(1032, 1056))
        hdu_res = fits.PrimaryHDU(img_res)
            # ra, dec in degrees
        
        #ra = str(Posx)
        #dec = str(Posy)
        #hdu_res.header['RA'] = str(Posx)
        #hdu_res.header['DEC'] = Posy
        
        import copy
        output_header = copy.deepcopy(hdu_res.header) # copy.deepcopy(hdu_in[0].header)
            #main_fits_header.add_astrometric_fits_keywords(hdu_res.header)
            #            rebinned_filename = "./SkyMapper_g_20140408104645-29_150.171-54.790_1056x1032.fits"
            #           hdu.writeto(rebinned_filename,overwrite=True)
            
        #    output_header['RA'] = ra
        #    output_header['DEC'] = dec
        output_header['WCSAXES'] = 2 #/ Number of coordinate axes       
        output_header['NAXIS1'] = float(1056)
        output_header['NAXIS2'] = float(1032)
        output_header['CRVAL1'] = str(POSx)
        output_header['CRVAL2'] = POSy
        output_header['CRPIX1'] = float(528)
        output_header['CRPIX2'] = float(516)
        output_header['CDELT1'] = -0.18 / 3600
        output_header['CDELT2'] = 0.18 / 3600
        output_header['CUNIT1'] = 'deg'
        output_header['CUNIT2'] = 'deg'
        output_header['CTYPE1']  = 'RA---SIN'          # / Right ascension, orthographic/synthesis project
        output_header['CTYPE2']  = 'DEC--SIN'          # / Declination, orthographic/synthesis projection
        output_header['RADESYS'] = 'FK5'               # / Equatorial coordinate system                   
        output_header['EQUINOX'] = 2000.0 #/ [yr] Equinox of equatorial coordinates
            
            
        filter=hdu_in[0].header['FILTER']
            
            #import astropy.wcs as wcs
            #wcs =wcs.WCS(output_header)      
    
            #img.load_hdu(hdu_res)
    
            #self.fitsimage.set_image(img)
            #self.AstroImage = img
            #self.fullpath_FITSfilename = filepath.name
        hdu_in.close()
    
        fits_image_ql = os.path.join(dir_name, Target_name+"_SkyMapper_"+filter+"_"+radec_center.to_string()+".fits")
        fits.writeto(fits_image_ql, hdu_res.data,
                         ##                     header=self.hdu_res.header, overwrite=True)
                         header=output_header, overwrite=True)

        #self.fitsimage.rotate(self.PAR.Ginga_PA)  
        #self.Display(self.fits_image_ql)
        #self.button_find_stars['state'] = 'active'
        #self.wcs_exist = True        