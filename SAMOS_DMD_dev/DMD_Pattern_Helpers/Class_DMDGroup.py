#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 10 11:07:25 2023

@author: samos_dev
"""

import numpy as np
import os
import pandas as pd



class DMDGroup:
    
    """
    Series of DMD patterns that correspond to a field of view.
    When slits will produce overlapping spectra in a main FOV, 
    envoke this class to create a series of DMD patterns with no overlap.
    """
    
    def __init__(self, dmd_slitview_df, regfile = None):
        
        self.regfile = regfile
        self.RA_FOV = None
        self.DEC_FOV = None
        self.X_FOV = None
        self.Y_FOV = None
        self.Slit_Patterns = None
        
        self.slitDF = dmd_slitview_df.sort_values(by="dmd_y1",ascending=False)
        
        if regfile is not None:
            
            reg_fname = os.path.split(regfile)[1].strip(".reg")
            
            if "RADEC" in regfile:
                
                radec_text_ind = regfile.index("RADEC")+6
                
                radec_text = regfile[radec_text_ind:].strip(".reg")
                
                self.RA_FOV = float(radec_text[0])
                self.DEC_FOV = float(radec_text[1])
        
        elif not self.slitDF.RA.isnull().values.any():
            
            
            ra_center = (np.max(self.slitDF['RA'])-np.min(self.slitDF['RA']))/2. + np.min(self.slitDF['RA'])
            dec_center = (np.max(self.slitDF['DEC'])-np.min(self.slitDF['DEC']))/2. + np.min(self.slitDF['DEC'])
            self.RA_FOV = ra_center
            self.DEC_FOV = dec_center
                                

        
        x_center = (np.max(self.slitDF['dmd_xc'])-np.min(self.slitDF['dmd_xc']))/2. + np.min(self.slitDF['dmd_xc'])
        y_center = (np.max(self.slitDF['dmd_yc'])-np.min(self.slitDF['dmd_yc']))/2. + np.min(self.slitDF['dmd_yc'])
        
        self.X_FOV = x_center
        self.Y_FOV = y_center
        
        
    def pass_through_current_slits(self, input_df):
        
        
        
        input_df = input_df.sort_values(by="dmd_y1", ascending=False).reset_index(drop=True)
        
    
        good_inds = []

        dmd_slit_rows = []
        j=0 
        slit_num = 0
        first_ind = input_df.index.values[0]
        
        
        for i in input_df.index.values:

            if i==first_ind:
                print('accepting first target', i)
                good_inds.append(i)
                #ra, dec = input_df.loc[i, ['RA', 'DEC']].values
                #coords0 = SkyCoord(ra, dec,unit='deg')
                

                #print(coords0)
                #dmd_coords = sky2dmd(coords=coords0, wcs=wcs) # center of target coords in dmd coords.
                dmd_xc, dmd_yc = input_df.loc[i, ["dmd_xc", "dmd_yc"]]


                print("append slit {}".format(i))

                dmd_slit_rows.append(i)
                slit_num+=1
            
            if j-i >= 1: 
                continue
            
            if i==input_df.index.values[-1]:
                continue

            j=i+1

            jrow = input_df.loc[j]
            comp_rows = input_df.loc[good_inds].values
            jrows = np.full(comp_rows.shape, jrow)
            
            #map the function to all rows
            #all_good = np.array(list(map(self.check_any_overlap, np.full(comp_rows.shape, input_df.loc[j]), comp_rows)))
            #check if this row also overlaps with any of the previously accepted rows
            # if no overlap, return True
            #is_good = self.check_any_overlap(input_df.loc[j], input_df.loc[i])
            #print(len(input_df))
            while ((not self.check_any_overlap(np.array(input_df.loc[j]), np.array(input_df.loc[i]))) & (j<len(input_df)-1) & \
                   (not all(np.array(list(map(self.check_any_overlap, 
                                              np.full(input_df.loc[good_inds].values.shape, input_df.loc[j]), 
                                              input_df.loc[good_inds].values)))))):
            #while ((not is_good) & (j<len(input_df)-1) & (not all(all_good))):
                print('skipping target', j)

                j+=1
                
            is_good =  ((self.check_any_overlap(input_df.loc[j], input_df.loc[i])) & \
                   (all(np.array(list(map(self.check_any_overlap, 
                                              np.full(input_df.loc[good_inds].values.shape, input_df.loc[j]), 
                                              input_df.loc[good_inds].values))))))
            
            if j<len(input_df)-1:
                print('accepting target', j)
                print('\n')
                good_inds.append(j)
                
            
            elif is_good:
                print('accepting target', j)
                print('\n')
                good_inds.append(j)


       
            print("append slit {}".format(j))
        
            dmd_slit_rows.append(j)
            slit_num+=1
            i = j
        
        good_pattern_df = input_df.loc[good_inds]
        
        redo_pattern_df = input_df.drop(index=good_inds)
        if 0 in redo_pattern_df.object.values:
            print(input_df)
        
        
        return good_pattern_df, redo_pattern_df
    
    def check_any_overlap(self, row, comp_row):
        # force row and comp_row to be np_array to avoid occasional issues when they arrive as pandas table
       # row = np.array(row)
       # comp_row = np.array(row)
        row_y0 = int(row[-3])
        row_y1 = int(row[-1])
        
        comp_row_y0 = int(comp_row[-3])
        comp_row_y1 = int(comp_row[-1])
        
        row_vals = set(range(row_y0, row_y1))
        comp_row_vals = set(range(comp_row_y0, comp_row_y1))
        
        #print(len(row_vals.intersection(comp_row_vals)))
        #print(row)
        #print(comp_row)
        
        if len(row_vals.intersection(comp_row_vals))>0:
            # if pixel overlap, return false
            
            return False
        else:
            #print("true, no intersection", row_vals.intersection(comp_row_vals))
            #print("row1", row_y0, row_y1)
            #print("row2", comp_row_y0, comp_row_y1)
            return True
        
        
                
        
    def pass_through_current_slits_two_sided(self, input_df):
        
        
        input_df = input_df.sort_values(by='dmd_y0',ascending=False).reset_index(drop=True)
        
        slit_xsizes = input_df.dmd_x1.values - input_df.dmd_x0.values
        slit_ysizes = input_df.dmd_y1.values - input_df.dmd_y0.values
        
        half_slit_xsizes = slit_xsizes/2.
        half_slit_ysizes = slit_ysizes/2.
        
        slit_edges_left = input_df.dmd_x0.values
        slit_edges_right = input_df.dmd_x1.values
        slit_edges_top = input_df.dmd_y1.values
        slit_edges_bottom = input_df.dmd_y0.values
        
        #center of mass of the targets system
        centerfield_x = (min(slit_edges_left)+max(slit_edges_left)) / 2.
        centerfield_y = (min(slit_edges_bottom)+max(slit_edges_bottom)) / 2.
        
        range_mirrors = (max(slit_edges_top)-min(slit_edges_bottom))
    
    
        good_inds = []
        good_inds_l = []
        dmd_slit_rows = []
        j=0 
        slit_num = 0
        first_ind = input_df.index.values[0]
        
        k = 0
        l_ind = len(input_df)
        for i in input_df.index.values:
            k += 1
            l_ind -= 1
            if i==first_ind:
                print('accepting first target', i)
                good_inds.append(i)

                dmd_xc, dmd_yc = input_df.loc[i, ["dmd_xc", "dmd_yc"]]


                print("append slit {}".format(i))

                dmd_slit_rows.append(i)
                slit_num+=1
            
            if j-i >= 1: 
                continue
            
            if i==input_df.index.values[-1]:
                continue

            j=i+1
            mid_index_ind = int(np.floor(len(input_df)/2))
            mid = input_df.index.values[mid_index_ind]
            
            #j = input_df.index.values[int(len(input_df))-k]
            
            while ((input_df.iloc[j]['dmd_y1'] > input_df.iloc[i]['dmd_y0']) & (j<len(input_df)-1)):
                print('skipping target', j)
                #print(input_df.iloc[j]['slit_edges_left'], input_df.iloc[i]['slit_edges_right'])

                j+=1
                
            print('accepting target', j)
            print('\n')
            
            if j not in good_inds_l:
                good_inds.extend([j])
            
            l = input_df.index.values[l_ind]
            
            if (input_df.iloc[l]['dmd_y1'] < input_df.iloc[i]['dmd_y0']) & (l not in good_inds):
                
                if l<len(input_df)-1:
                    
                    if input_df.iloc[l]['dmd_y0'] > input_df.iloc[l+1]['dmd_y1']:
                        
                        #print(l)
                        good_inds_l.append(l)
                else:
                    good_inds_l.append(l)

           
            print("append slit {}".format(j))
            
            dmd_slit_rows.append(j)
            slit_num+=1
            i = j+1
        
        good_inds.extend(good_inds_l)
        good_pattern_df = input_df.loc[good_inds]
        
        redo_pattern_df = input_df.drop(index=good_inds)
        
        return good_pattern_df, redo_pattern_df
    
    

                
               
    
    
    
    
    
    
    
    
    
    
    