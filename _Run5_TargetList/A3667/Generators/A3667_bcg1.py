#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 15:41:54 2025

@author: robberto
"""
    
    

#ignore boring runtime warnings
import warnings
warnings.filterwarnings('ignore', category=RuntimeWarning)

#import ipyaladin.aladin_widget as ipyal
#from ipyaladin import Aladin
#from ipywidgets import Layout#, Box, widgets
import pandas as pd
#from astroquery.simbad import Simbad
import astropy.units as u
#from astropy import coordinates#, units as u, wcs

from astroquery.vizier import Vizier
from astroquery.mast import Catalogs
#from astropy.io.votable import parse
from astropy.table import Table, Column
import numpy as np
import matplotlib.pyplot as plt
import copy

from regions import RectangleSkyRegion, Regions
from astropy.coordinates import SkyCoord
from astropy import coordinates
from astropy import units as u

#from astropy import units as u
import os as os
#import matplotlib.pyplot as plt
#import matplotlib.transforms as transforms
#from matplotlib.patches import Rectangle
    
#from astropy.wcs import WCS
#from astropy.io import fits
#from astropy.utils.data import get_pkg_data_filename
#from astropy import units as u
#from astropy.visualization.wcsaxes import Quadrangle
from astropy.coordinates import SkyOffsetFrame, ICRS
#from astropy.coordinates import SkyCoord

from astropy.time import Time
#from astropy.io import fits

import astropy.coordinates as coord
from astroquery.gaia import Gaia
#import urllib.request
#import shutil
#import tempfile
#import re

from regions import PixCoord

#import pyvo as vo
#from astropy.utils.data import download_file
#from astropy.nddata import Cutout2D

#from gammapy.maps import RegionGeom

from ClassCatalogs import Catalogs

import warnings; warnings.filterwarnings("ignore")

"""
INSTANTIATE THE CLASS HANDLING THE CATALOGS
"""
Cat = Catalogs()


"""
DECLARE THE TARGETNAME
"""
Simbad_name = "Abell 3667"
Target_name = "Abell3667-mergeer-neqr-bcg1" #"Simbad_Name"

Target_name = "".join(Target_name.split())  #REMOVE AL WHITE SPACES
Cat.Target_name = Target_name

"""
SETUP THE DIRECTORY
"""
cwd = os.getcwd()
parent_dir = os.path.abspath(os.path.join(cwd, os.pardir))

dir_name = os.path.join(parent_dir, Target_name)
if not os.path.exists(dir_name):
    os.makedirs(dir_name)
Cat.dir_name  = dir_name
Cat.dir_name = Target_name#"Abell3667-small-group"

"""
#Extract RADEC of target, known by Name
"""
#Get the SIMBAD Coordinates of the Target
print(Cat.resolve_target_name_SIMBAD(Simbad_name).ra.value)
#ra_center = Cat.resolve_target_name_SIMBAD(Simbad_name).ra.value
#dec_center = Cat.resolve_target_name_SIMBAD(Simbad_name).dec.value

#ra_center = 303.108538 * u.deg
#dec_center = -56.8072455 * u.deg
ra_center = 303.253612	 * u.deg
dec_center = -56.8145572 * u.deg
#ra_center = 303.0308726	 * u.deg
#dec_center = -56.80049103 * u.deg


radec_center = coord.SkyCoord(ra_center,dec_center,unit=(u.deg,u.deg), frame='icrs')
Cat.radec_center = radec_center
print(radec_center)


#Cat.extract_astropy_table(Target_name)

#CHECK: Extract GAIA sources 
#Vizier.ROW_LIMIT=100
Gaia.ROW_LIMIT = -1 
Gaia = Cat.query_region_Vizier_GAIA3(ra_center,dec_center,2)
print(Gaia.colnames)
print(Gaia['Gmag'])
print(Gaia['DEC'])

#CHECK: Extract generic table (e.g. 2MASS sources) 
#table=""
#TwoMass = Cat.query_region_Vizier_table(ra_center,dec_center,2)  #missing table, defauld to 2mass
#TwoMass = TwoMass[0]
#print(TwoMass.colnames)
#print(TwoMass['Kmag'])


#OTHER CHECKS...
#Extract Astropy tablefrom your own catalog on disk#%%script false --no-raise-error
#

#catfile = '../a3667_samos_targets/bcg1_infalling_group.csv'
catfile = '../a3667_samos_targets/supertable2.csv'
pandacat = pd.read_csv(catfile)
#check...
pandacat.head()

# If needed, you can rename columns
#pandacat.set_index('Entry')
#check...
#pandacat.head()
pandacat = pandacat.rename(columns={'ra': 'RA', 'dec': 'DEC'})

#to create an astropy table, use
main_ap_table = Table.from_pandas(pandacat)

#mytable = Table.from_pandas(pandacat)
#print(mytable[0:5])
#table_4 = Table.from_pandas(pandacat_4)
"""

#Create an astropy table from my file + Vizier X-match
"""
#The X-match output table is a VOTable. Must handled with care, Pandas seems to work.

#Routine is required to read VOTable => Pandas
#def votable_to_pandas(votable_file):
#    votable = parse(votable_file)
#    table = votable.get_first_table().to_table(use_names_over_ids=True)
#    return table.to_pandas()

#here we go...
#catfile = './M42/Slimtable.csv.vot'
#pandacat_4  = votable_to_pandas(catfile)
#pandacat_4.head()
"""
#to create an astropy table, use
table_4 = Table.from_pandas(pandacat_4)
print(table_4[0:5])
"""

#We have shown 4 methods and created 4 tables: table_1, table_2 table_3, table_4
#"""
##SELECT A TABLE TO WORK WITH
#"""
#WE SELECT GAIA DR2 CATALOG PROVIDED BY VIZIER
#main_ap_table = table_4

"""
#SORT TABLE BY RIGHT ASCENSIONN
"""
#main_ap_table.sort('RA')
#print(main_ap_table)




"""
#Get the sources within 180"x180" FoV
"""
# Create a deep copy of the table to save the one selected 
main_ap_table_infield = copy.deepcopy(main_ap_table)

#Define a rectangular astropy region 180" x 180"
rr=RectangleSkyRegion(radec_center,180*u.arcsec,180*u.arcsec)

#To use the .contain method, we need a WCS. To get something on sky, 
#we get the WCS from 2MASS.
#We follow here the example on https://irsa.ipac.caltech.edu/docs/program_interface/sia_2mass_allsky.html
ax,wcs = Cat.get_2Mass_image(Target_name, radec_center)


#SELECT SOURCES FALLING INSIDE THE 180"x180" region
#get the RADEC of all sources in the table
all_RADEC = SkyCoord(ra=main_ap_table['RA'], dec=main_ap_table['DEC'], unit='deg')
print("We start with a table containing", len(all_RADEC)," targets")
main_ap_table_infield['in_field']='OUT'
#
for i in range(len(main_ap_table)):
#    print(len(main_ap_table_infield))
    print(all_RADEC[i])
    if rr.contains(all_RADEC[i],wcs):
        main_ap_table_infield['in_field'][i]='IN'
        #print(i,"yes")
        ax.scatter(all_RADEC[i].ra, all_RADEC[i].dec, transform=ax.get_transform('fk5'), s=500, edgecolor='red', facecolor='none')
    else:
#X        main_ap_table_infield['RA']==np.nan
        #print(i,"no")
        continue
#X  bad = np.logical_or.reduce([np.isnan(col) for col in main_ap_table_infield.itercols()])
#X  print(bad)
mask = np.logical_or.reduce([c == 'OUT' for c in main_ap_table_infield.columns.values()])
#print(mask)
main_ap_table_infield = main_ap_table_infield[~mask]
#print("", len(all_RADEC)," targets")
print("...and we end up with",len(main_ap_table_infield)," sources")


#Query region skymapper
#skymapper_pandas_full = Cat.query_region_SkyMapper(ra_center, dec_center, radius = 2)
#print(skymapper_pandas_full)

#and both catalogs can be matched...
#TO BE DONE

"""
WE work with Pandas table, and prepare for the weigths/priority sorting

main_pdtable = main_ap_table_infield.to_pandas()
main_pdtable["Weigth"]=0


def divide_array(arr):
    arr_out = arr
    n = len(arr)
    if n == 0:
      return {}
    groups = {}
    group_size = n // 5
    remainder = n % 5

    start = 0
    for i in range(1, 6):
        end = start + group_size
        indexes_i = list(range(start, end))
        arr_out[indexes_i] = i
#        arr_out[start:end] = i
        #groups[i] = arr[start:end]
        #arr_out.loc[arr_out[groups[i]]] = i
        start = end
    arr_out[end:]=i    
    return arr_out


#We need to find a good parameter for initial, tentative sorting
column_names = main_pdtable.columns
print(column_names)
sorting_param  = 'Weigth'
main_pdtable = copy.deepcopy(main_pdtable.sort_values(by=[sorting_param]))
print(main_pdtable)

arr=np.array(main_pdtable["Weigth"])
grouped_array = divide_array(arr)
print(grouped_array)
main_pdtable["Weigth"] = grouped_array
main_pdtable.to_csv(os.path.join(dir_name,"table_to_be_ranked_w.csv"))
print(main_pdtable)


Now you may open the table_to_be_ranked.csv and edit to set different weigths
> for example, open the file in Excel, sort by Gmag and divide 
the targets in 5 groups assigning 1 to the top 20%, 2 to the 20-40% etc. 
then save adding the _w suffix before the .csv



main_pdtable_w = pd.read_csv(dir_name+"/table_to_be_ranked_w.csv")

"""

main_pdtable_w = main_ap_table_infield.to_pandas()
#we MUST sort again the table, weigth first, then RA as we disperse the specrra along DEC

main_pdtable_ranked  = main_pdtable_w.sort_values(by=['Weigth','RA'],ascending=[True, False])
main_pdtable_ranked.reset_index(drop=True, inplace=True)
main_pdtable_ranked['mask'] = -1
main_pdtable_ranked


"""SET THE DEFAULT SLIT SIZES: FUNDAMENTAL!
"""
Slit_Width_pix = 3 #pixels; this affect the resolution of the spectra
Slit_Length_pix = 9 #pixels; this affects the total nr. of spectra in a dense field


"""
ITERATIVE SOLUTION, STARTING FROM the top priority (weigth = 1)
We set a hard limit of 5 masks, can be refined
"""
dataframe_collection = {}

#SET HOW MANY TARGETS WE WANT TO CONSIDER
Max_nr_of_targets = min(1000,len(main_pdtable_ranked))

Nr_of_region_files = 5

for k in range(Nr_of_region_files): #k is the iterator labeling the region files
    #main_pdtable_ranked_Weigth1 = main_pdtable_ranked[(main_pdtable_ranked['Weigth'] == 1) & (main_pdtable_ranked['mask'] == -1)]
    #print(len(main_pdtable_ranked_Weigth1)) #69 sources with Weigth 1 entering the loop

    # we will do n_trials randomized to get the best combo
    n_trials = 20
    
    random_seed = 42
    np.random.seed(random_seed)
    
    best_rank1 = 0
    best_total = 0

    
    #loop on the trials
    for i in range(n_trials):
        rank1 = []
        total = []
        
        #make a copy of the big input table
        main_pdtable_ranked_internal = copy.deepcopy(main_pdtable_ranked) #e.g. 346 elements
        
        
        
        #print('\nstarting with these masks data:')
        #print('nr of 0',len(main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==0]))   
        #print('nr of 1',len(main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==1]))
        #print('nr of 2',len(main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==2]))
        #print(main_pdtable_ranked)
        
        N_ones = len(main_pdtable_ranked_internal[(main_pdtable_ranked_internal['Weigth'] == 1) & (main_pdtable_ranked_internal['mask'] == -1)])
        #print('N_ones = ', N_ones)
        df = main_pdtable_ranked_internal[(main_pdtable_ranked_internal['Weigth'] == 1) & (main_pdtable_ranked_internal['mask'] == -1)].sample(frac=1)
        #print('df = ', df)
        main_pdtable_ranked_internal = main_pdtable_ranked_internal.sort_values(by=['Weigth','mask'],ascending=[True, True])
        main_pdtable_ranked_internal[:N_ones]=df
        #print(main_pdtable_ranked_internal)
        #print('nr of 0',len(main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==0]))   
        #print('nr of 1',len(main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==1]))
        #print('nr of 2',len(main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==2]))
      
        xc = (main_pdtable_ranked_internal['RA']-ra_center)*3600*6 * np.cos(main_pdtable_ranked_internal['DEC']*np.pi/180.)    #distance in pixel from the center field
        xc = xc.astype(int)
        yc = ((main_pdtable_ranked_internal['DEC']-dec_center)*3600*6).astype(int) 
        length=4000
        spacing = 2 #pixel
        #adding two extra pixels spacing to make sure that there are at least two pixels...
        source_separation = (Slit_Length_pix + spacing+2) #e.g. 9 pixel slit length, + 2 spacing =  11 pixels separation center to center

        #POPULATE FRAME
# _|       fullarray = np.zeros((1100,4096))
        fullarray = np.zeros((4096,1100))
        count0=0
        listone=[]
        for j in range(Max_nr_of_targets):  #len(main_pdtable_ranked_internal):
            
            #print(j)#,main_pdtable_ranked_internal.at[j,'index'])
            
            #if main_pdtable_ranked_internal.at[j,'Entry'] == 104:
            #    count0 = count0+1
            #    #print(count0,main_pdtable_ranked_internal.at[j,'index'])
            #    listone.append(main_pdtable_ranked_internal.at[j,'Entry'])
            #    print(listone)
            if main_pdtable_ranked_internal.at[j,'mask'] != -1:
                 #print(main_pdtable_ranked_internal.iloc[j]['mask'])
                 #print('skipping source j: ', j,' because main_pdtable_ranked_internal.at[j,mask] =',main_pdtable_ranked_internal.at[j,'mask'])
                 #print(main_pdtable_ranked_internal.iloc[j]['mask'])
                 continue                
            #print(j,yc[j],xc[j]) 
#_|             

            if np.abs(xc[j]) > 544:
                continue
            # On the RA side we are working in pixels of the SISI camera
            x0 = (xc[j]-int(source_separation/2)+550)
            x1 = (xc[j]+int(source_separation/2)+551)
            #OIn the DEC side we don't care... let's assume SAMI 4K long
            y0 = (yc[j]-int(length/2)+2048)
            y1 = (yc[j]+int(length/2)+2048)
            
            x0 = max(x0,0)
            x1 = min(x1,1100)
            y0 = max(y0,0)
            y1 = min(y1,4096)
            length = y1-y0
#_|            print('\ny0,y1,x0,x1: ',y0,y1,x0,x1)

#_|            array = np.zeros((1100,4096))
            array = np.zeros((4096,1100))                    #    [4096,1100]
#            print('array.shape: ',array.shape)
#_|            rectangle = np.ones((source_separation, length))
            rectangle = np.ones((length,source_separation))
#            print('rectangle.shape: ',rectangle.shape)                           #     [2000,11]
#            print('array[y0:y1,x0:x1].shape: ',array[y0:y1,x0:x1].shape) 
            
            array[y0:y1,x0:x1] = rectangle 
#x            print('fullarray.shape: ',fullarray.shape)
            fullarray += array
            if np.max(fullarray) > 1:   #there is OVERLAP: UNDO!
                fullarray -= array #undo
                
            else: #NO OVERLAP: GOOD"
                #remove the oversized rectangle
                fullarray -= array
                #set the new rectangle with the appropriate slit size
                innerrectangle = np.ones((length,source_separation-4))
                #inject the new smaller rectangle in the 
                array = np.zeros((4096,1100)) 
                array[y0:y1,x0+2:x1-2] = innerrectangle
                fullarray += array
                #keep track of the TARGETS
                if main_pdtable_ranked_internal.iloc[j]['Weigth'] == 1:
                    rank1.append(j)
                #keep track of the total (FILLERS included)    
                total.append(j)   
                #promote the source to the current k-th mask
                #print('current mask:',main_pdtable_ranked_internal.at[j,'mask'])
                main_pdtable_ranked_internal.at[j,'mask'] = k
                #print('new   mask = ',main_pdtable_ranked_internal.at[j,'mask'])
                #print('check        ',main_pdtable_ranked_internal.at[j,'mask'])
                #df.at[1, 'B'] = 10
                #df[df['A'] > 2]['B']
        #
        print('iteration   #total    #rank1     best_total    best_rank1')
        #print(f"i={i:.2f}, {(len(total)):.3f}, {(len(rank1)):.3f}, {(best total):.3f}, {(best rank1):.3f}")
        print(i,len(total),len(rank1),best_total,best_rank1) 

        #plt.imshow(fullarray, cmap='hot')
        #plt.colorbar()
        #plt.show()
        
        #do we want to keep this iteration?
        if (len(rank1) >= best_rank1) and (len(total) >= best_total):
            print("Keeping",i,len(total),len(rank1),best_total,best_rank1)
            best_rank1 = len(rank1)
            best_total = len(total)
            target_list_out = copy.deepcopy(main_pdtable_ranked_internal)
            target_list_out.loc[main_pdtable_ranked_internal['mask']==k,'mask']=k
            #print('i_best = ', i)
            
            print('best at trial',i,':')
            print('nr in mask 0',len(target_list_out[target_list_out['mask']==0]))   
            print('nr in mask 1',len(target_list_out[target_list_out['mask']==1]))   
            print('nr in mask 2',len(target_list_out[target_list_out['mask']==2]))           
            print('nr in mask 3',len(target_list_out[target_list_out['mask']==3]))           
            print('nr in mask 4',len(target_list_out[target_list_out['mask']==4]))           
    print('end of trial:')        
    #print('nr in mask 0',len(target_list_out[target_list_out['mask']==0]))   
    #print('nr in mask 1',len(target_list_out[target_list_out['mask']==1]))   
    #print('nr in mask 2',len(target_list_out[target_list_out['mask']==2]))           

    print('nr in mask 0',len(target_list_out[target_list_out['mask']==0]))   
    print('nr in mask 1',len(target_list_out[target_list_out['mask']==1]))   
    print('nr in mask 2',len(target_list_out[target_list_out['mask']==2]))           
    print('nr in mask 3',len(target_list_out[target_list_out['mask']==3]))           
    print('nr in mask 4',len(target_list_out[target_list_out['mask']==4]))  
    
    #Overwrite the main table with the new k/mask value; 
    # we are going to loop on to the next mask (k-value) and this table will be copied at the beginning of each i-trial 
    main_pdtable_ranked= target_list_out.sort_values(by='RA')
    #print(len(main_pdtable_ranked[main_pdtable_ranked_internal['mask']==0]))   
    #print(len(main_pdtable_ranked[main_pdtable_ranked_internal['mask']==1]))

    #SORT BY RA. From south (down) to north (up)
    #we reuse main_pdtable_ranked_internal
    main_pdtable_ranked_internal = target_list_out[target_list_out['mask']==k]
    main_pdtable_ranked_internal  = main_pdtable_ranked_internal.sort_values(by=['RA'],ascending=[True])

    #SAVE .csv TABLE FILES
    #main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==k].to_csv(dir_name+"/table_ranked_"+str(k)+".csv")
    #target_list_out.to_csv(dir_name+"/table_out.csv")

    dataframe_collection[k] = main_pdtable_ranked_internal[main_pdtable_ranked_internal['mask']==k]
    
    #target_list_out_Weigth1 = target_list_out[target_list_out['Weigth'] == 1]
    #target_list_out_Weigth2 = target_list_out[target_list_out['Weigth'] != 1]
    
    
    plt.imshow(fullarray, cmap='hot')
    #plt.colorbar()
    plt.show()


"""
SAVE the list of selected targets as Simbad regions file¶
"""
#filename = Target_name+"_slits.reg"
#os.path.join(dir_name,filename+".reg")
#filename=""

#RUN
Nr_of_tables = len(dataframe_collection)
print(Nr_of_tables)
RegionFiles_directory_path = os.path.join(dir_name,'RegionFiles','RADEC')
os.makedirs(RegionFiles_directory_path, exist_ok=True)
for it in range(Nr_of_tables):
     slits = Cat.Save_table_2_Astropy_slitregions(Target_name,ra_center,dec_center,it,Slit_Length_pix,Slit_Width_pix,dataframe_collection[it], RegionFiles_directory_path)   
#    print(RegionFiles_directory_path,filename)

"""
GRAPHICS
"""

#Select a table in the collection
it = 0

# Determine the RADEC offset in degrees
#RA_Center = np.mean(dataframe_collection[it]['RA'])
#DEC_Center = np.mean(dataframe_collection[it]['DEC'])
RA_Offsets = dataframe_collection[it]['RA'] - ra_center
DEC_Offsets = dataframe_collection[it]['DEC'] - dec_center
print(np.c_[RA_Offsets[0:5], DEC_Offsets[0:5]]) #in degrees

# Determine the RADEC offset in arcsec
RA_Offsets *= 3600
DEC_Offsets *= 3600
print(np.c_[RA_Offsets[0:5], DEC_Offsets[0:5]])   #in arcsec

#Determine the RADEC position in SAMOS CCD pixels [1024,1024]
IM_CCD_Scale = 0.18
#
RA_Offsets_IMpix = RA_Offsets / IM_CCD_Scale # in pixels
DEC_Offsets_IMpix = DEC_Offsets / IM_CCD_Scale
print(np.c_[RA_Offsets_IMpix[0:5], DEC_Offsets_IMpix[0:5]])   #in pixels



# Display sources in SAMOS Spectral Inst. CCD coordinates
plt.figure(figsize=(10,10))
plt.plot(RA_Offsets_IMpix, DEC_Offsets_IMpix, 'ro')
plt.axis([-512, 512, -512, 512])
plt.show()

# OFFsets in in SAMI pixels (SAMOS-SP Channel)
SP_CCD_Scale = 0.133
#
RA_Offsets_SPpix = RA_Offsets / SP_CCD_Scale # in pixels
DEC_Offsets_SPpix = DEC_Offsets / SP_CCD_Scale
print(np.c_[RA_Offsets_SPpix[0:5], DEC_Offsets_SPpix[0:5]])

# OFFsets in in SpecIns pixels (SAMOS-IM Channel)
IM_CCD_Scale = 0.17578125 #180/1024
#
RA_Offsets_IMpix = RA_Offsets / IM_CCD_Scale # in pixels
DEC_Offsets_IMpix = DEC_Offsets / IM_CCD_Scale
print(np.c_[RA_Offsets_IMpix[0:5], DEC_Offsets_IMpix[0:5]])

plt.figure(figsize=(5,15))
plt.plot(RA_Offsets_SPpix, DEC_Offsets_SPpix, 'ro')
plt.axis([-750, 750,-2048, 2048])
rectangle = plt.Rectangle((-675,-675),1350, 1350, fc='blue',ec="red")
plt.gca().add_patch(rectangle)
for i in range(len(RA_Offsets_IMpix)):
#    print(RA_Offsets_IMpix.iloc[i])
#    print(np.round(RA_Offsets_IMpix.iloc[i]-1),np.round(DEC_Offsets_IMpix.iloc[i]-1000,3, np.round(DEC_Offsets_IMpix.iloc[i]+1000))
#    xy = (RA_Offsets_SPpix.iloc[i]-1000,np.round(DEC_Offsets_SPpix.iloc[i]))
    xy = (np.round(RA_Offsets_SPpix.iloc[i])-5,DEC_Offsets_SPpix.iloc[i]-1000)
    print(xy)
#    rectangle = plt.Rectangle(xy ,3300,9, fc='green',ec="green")
    rectangle = plt.Rectangle(xy ,9,2000, fc='green',ec="green")
    plt.gca().add_patch(rectangle)

"""
PHOTOMETRY
"""
# SOUTHERN HEMISPHERE, use SkyMapper
if dec_center <= 0:
    SkyMapper_phot_pandas = Cat.query_region_SkyMapper(ra_center, dec_center, radius = 2)
    SkyMapper_phot_pandas.to_csv(dir_name+"/"+Target_name+"-SkyMapper_in_field_"+radec_center.to_string()+".csv")

if dec_center > 0:
#    from astroquery.mast import Observations
#    from astropy.coordinates import SkyCoord
#    import astropy.units as u

    # Define the coordinates of the search center
    coord = coordinates.SkyCoord(ra_center * u.deg, dec_center * u.deg, frame='icrs')

    # Define the search radius
    radius = 120 * u.arcsec

    # Query the Pan-STARRS mean object catalog
    PanSTARRS = Catalogs.query_region(coord, radius=radius, catalog="PanSTARRS", table="mean")

    # Print the results
    print(PanSTARRS)
    PanSTARRS_phot_pandas = pd.DataFrame(np.squeeze(PanSTARRS))
    PanSTARRS_phot_pandas.to_csv(dir_name+"/"+Target_name+"-PanSTARRS_in_field_"+radec_center.to_string()+".csv")

"""
ASTROMETRY
"""

#width of the field in "tangent arcminutes"
#The 3'x3' field corresponds to RA range that depends on the DEC. 
#If the Width is DRA=3' arcmin at the equator, at the source this corresponds to DRA=3/cos(delta).  
"""
dra = 3.3/np.cos(dec_center*u.deg)
print(dra.value)

from astroquery.gaia import Gaia
Gaia.ROW_LIMIT = -1
Gaia.MAIN_GAIA_TABLE = "gaiadr3.gaia_source"  # Reselect Data Release 3, default
#from astropy.coordinates import SkyCoord


coord = SkyCoord(ra=ra_center, dec=dec_center, unit=(u.degree, u.degree), frame='icrs')
width = u.Quantity(dra.value, u.arcmin)
height = u.Quantity(3.3, u.arcmin)
r_Gaia = Gaia.query_object_async(coordinate=radec_center, width=width, height=height)
#INFO: Query finished. [astroquery.utils.tap.core]
r_Gaia.pprint(max_lines=12, max_width=130)
"""
r_Gaia = Cat.query_region_Vizier_GAIA3(ra_center,dec_center,2)
r_Gaia.rename_column('SOURCE_ID', 'MainID')
print("\n\n FOUND ", len(r_Gaia), " GAIA DR3 SOURCES")

# FIX The GAIA COORDINATES TO THE EPOCH OF OBSERVATION
#from astropy.coordinates import SkyCoord, Distance, Galactic
print(str(ra_center),str(dec_center))

r_coord = SkyCoord(
    ra=r_Gaia['RA'], 
    dec=r_Gaia['DEC'],
    #distance=Distance(parallax=r_Gaia['parallax']),
    #pm_ra = r_Gaia['pmra'],
    pm_ra_cosdec =  np.array(r_Gaia['pmra'].filled(0))* u.mas/u.yr,
    #pm_dec =r_Gaia['pmdec'],
    pm_dec = np.array(r_Gaia['pmdec'].filled(0))* u.mas/u.yr,

    obstime=Time(r_Gaia['ref_epoch'], format='jyear'))

print(Time.now())
    
r_coord_today  = r_coord.apply_space_motion(
                new_obstime=Time.now())# Time('J1950'))
r_Gaia['ra_now']=r_coord_today.ra.deg
r_Gaia['dec_now']=r_coord_today.dec.deg

gaia_pdtable = r_Gaia.to_pandas()
gaia_pdtable['placement']='out'


region_sky = RectangleSkyRegion(center=radec_center,
                                    width=0.05 * u.deg, height=0.05 * u.deg)#     
region_sky_pixel=region_sky.to_pixel(wcs)

for i_star in range(len(r_Gaia['RA'])):
    gaia_coord=SkyCoord(ICRS(float(r_Gaia['RA'][i_star])*u.deg, float(r_Gaia['DEC'][i_star])*u.deg))
    if region_sky_pixel.contains(PixCoord.from_sky(gaia_coord,wcs)):
                print(i_star,"GAIA SOURCE IS IN SAMOS FOV")
                gaia_pdtable.loc[i_star,'placement'] = 'in_field'

gaia_infield = gaia_pdtable[gaia_pdtable['placement']=='in_field']
g0 = gaia_infield[["MainID","ra_now","dec_now","Gmag"]].sort_values(by="Gmag")
print(g0.dropna(inplace = True))
g0.to_csv(dir_name+"/"+Target_name+"-GAIA_in_field_"+radec_center.to_string()+".csv")


