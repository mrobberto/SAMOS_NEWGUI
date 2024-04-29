from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.wcs.utils import fit_wcs_from_points
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import pandas as pd
from photutils.detection import IRAFStarFinder


def iraf_gridsource_find(ccd, expected_sources, **kwargs):
    iraffind = IRAFStarFinder(brightest=expected_sources, **kwargs)
    irafsources = iraffind(ccd)
    for col in irafsources.colnames:
        irafsources[col].info.format = "%.8f"
    sorted_irafsources = sort_iraf_source_table(irafsources.to_pandas(), numcols=int(np.sqrt(expected_sources)))
    return sorted_irafsources, irafsources


def sort_iraf_source_table(pd_iraf_sources, numcols=11):
    ix_sorted_inds = None
    sorted_coords_full_arr = None
    cols_list = np.arange(numcols)

    j = -1 # column counter for each row
    this_row_x = [] # list of 11 columns in current row
    this_row_y = []
    this_ix_inds = []
    passed_rows = 0
    pd_iraf_sources = pd_iraf_sources.sort_values(by="ycentroid").reset_index()
    print(pd_iraf_sources)
    for i in pd_iraf_sources.index.values:
        j+=1
        x,y = pd_iraf_sources.loc[i,["xcentroid","ycentroid"]]

        this_row_x.append(x)
        this_row_y.append(y)
        this_ix_inds.append(i)
        if j==numcols-1:
            this_row_x = np.array(this_row_x)
            this_row_y = np.array(this_row_y)
            this_ix_inds = np.array(this_ix_inds)

            this_row_sort_xinds = np.argsort(this_row_x)

            sorted_row_x = this_row_x[this_row_sort_xinds]
            sorted_row_y = this_row_y[this_row_sort_xinds]
            sorted_ix_inds = this_ix_inds[this_row_sort_xinds]

            this_row_coords = np.column_stack((sorted_row_x,sorted_row_y))
        
            if sorted_coords_full_arr is None:
                sorted_coords_full_arr = this_row_coords
                ix_sorted_inds = sorted_ix_inds
            else:
                sorted_coords_full_arr = np.vstack((sorted_coords_full_arr,this_row_coords))
                ix_sorted_inds = np.hstack((ix_sorted_inds,sorted_ix_inds))

            this_row_x, this_row_y = [],[]
            this_ix_inds = []
            j = -1 #reset column counter
            passed_rows+=1 # quick log of rows passed
    return pd_iraf_sources.reindex(ix_sorted_inds).reset_index(drop=True)


def fit_wcs_with_sip(sip_degree, pattern_source_df, plot_hists=True):
    dmd_coords = pattern_source_df[['x','y']].values
    ccd_coords = pattern_source_df[['xcentroid','ycentroid']].values

    dmd_sky_coords = SkyCoord(dmd_coords[:,0]*u.arcsecond, dmd_coords[:,1]*u.arcsecond, unit='deg') 
    ccd_sky_coords = SkyCoord(ccd_coords[:,0]*u.arcsecond, ccd_coords[:,1]*u.arcsecond, unit='deg')

    # get WCS for ccd pixel coords to dmd mirror coords
    ccd_to_dmd_wcs = fit_wcs_from_points(xy=ccd_coords.T, world_coords=dmd_sky_coords, sip_degree=sip_degree)

    # get WCS for dmd mirror coords to ccd pixel coords
    dmd_to_ccd_wcs = fit_wcs_from_points(xy=dmd_coords.T, world_coords=ccd_sky_coords, sip_degree=sip_degree)

    ccd_x_ra_in_arr = np.array([i.ra.degree for i in ccd_sky_coords])
    ccd_y_dec_in_arr = np.array([i.dec.degree for i in ccd_sky_coords])

    dmd_x_ra_in_arr = np.array([i.ra.degree for i in dmd_sky_coords])
    dmd_y_dec_in_arr = np.array([i.dec.degree for i in dmd_sky_coords])

    ccd_x_pix_in_arr = ccd_coords[:,0]
    ccd_y_pix_in_arr = ccd_coords[:,1]

    dmd_x_mir_in_arr = dmd_coords[:,0]
    dmd_y_mir_in_arr = dmd_coords[:,1]
    
    wcs_conversion_df_cols1 = ["dmd_x_ra_in", "dmd_y_dec_in", "dmd_x_mir_in", "dmd_y_mir_in", "ccd_x_pix_out","ccd_y_pix_out",
                               "ccd_x_pix_in", "ccd_y_pix_in", "dmd_x_mir_out", "dmd_y_mir_out", "dmd_x_ra_out", "dmd_y_dec_out"]

    dmd_x_sky_out_arr, dmd_y_sky_out_arr = ccd_to_dmd_wcs.all_pix2world(ccd_x_pix_in_arr,  ccd_y_pix_in_arr, 0)
    ccd_x_pix_out_arr, ccd_y_pix_out_arr = ccd_to_dmd_wcs.all_world2pix(dmd_x_ra_in_arr,dmd_y_dec_in_arr, 0)

    CCD2DMD_wcs_conv_data = np.column_stack([dmd_x_ra_in_arr, dmd_y_dec_in_arr, dmd_x_mir_in_arr, dmd_y_mir_in_arr,
                                             ccd_x_pix_out_arr, ccd_y_pix_out_arr, ccd_x_pix_in_arr, ccd_y_pix_in_arr,
                                             dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600, dmd_x_sky_out_arr, dmd_y_sky_out_arr])

    CCD2DMD_wcs_conv_df = pd.DataFrame(data=CCD2DMD_wcs_conv_data, columns=wcs_conversion_df_cols1)

    delta_dmdx_in_out = np.abs(CCD2DMD_wcs_conv_df[["dmd_x_mir_in"]].values - CCD2DMD_wcs_conv_df[["dmd_x_mir_out"]].values)
    delta_dmdy_in_out = np.abs(CCD2DMD_wcs_conv_df[["dmd_y_mir_in"]].values - CCD2DMD_wcs_conv_df[["dmd_y_mir_out"]].values)

    delta_ccdx_in_out = np.abs(CCD2DMD_wcs_conv_df[["ccd_x_pix_in"]].values - CCD2DMD_wcs_conv_df[["ccd_x_pix_out"]].values)
    delta_ccdy_in_out = np.abs(CCD2DMD_wcs_conv_df[["ccd_y_pix_in"]].values - CCD2DMD_wcs_conv_df[["ccd_y_pix_out"]].values)

    CCD2DMD_wcs_conv_df["delta_dmdx_in_out"] = delta_dmdx_in_out
    CCD2DMD_wcs_conv_df["delta_dmdy_in_out"] = delta_dmdy_in_out
    CCD2DMD_wcs_conv_df["delta_ccdx_in_out"] = delta_ccdx_in_out
    CCD2DMD_wcs_conv_df["delta_ccdy_in_out"] = delta_ccdy_in_out

    wcs_conversion_df_cols2 = ["ccd_x_ra_in", "ccd_y_dec_in", "ccd_x_pix_in", "ccd_y_pix_in", "dmd_x_mir_out", "dmd_y_mir_out",
                               "dmd_x_mir_in", "dmd_y_mir_in", "ccd_x_pix_out","ccd_y_pix_out", "ccd_x_ra_out", "ccd_y_dec_out"]

    ccd_x_sky_out_arr, ccd_y_sky_out_arr = dmd_to_ccd_wcs.all_pix2world(dmd_x_mir_in_arr,  dmd_y_mir_in_arr, 0)

    dmd_x_mir_out_arr, dmd_y_mir_out_arr = dmd_to_ccd_wcs.all_world2pix(ccd_x_ra_in_arr,ccd_y_dec_in_arr, 0)

    DMD2CCD_wcs_conv_data = np.column_stack([ccd_x_ra_in_arr, ccd_y_dec_in_arr, ccd_x_pix_in_arr, ccd_y_pix_in_arr,
                                             dmd_x_mir_out_arr, dmd_y_mir_out_arr, dmd_x_mir_in_arr, dmd_y_mir_in_arr,
                                             ccd_x_sky_out_arr*3600, ccd_y_sky_out_arr*3600, ccd_x_sky_out_arr, ccd_y_sky_out_arr])

    DMD2CCD_wcs_conv_df = pd.DataFrame(data=DMD2CCD_wcs_conv_data,columns=wcs_conversion_df_cols2)

    delta_dmdx_in_out = np.abs(DMD2CCD_wcs_conv_df[["dmd_x_mir_in"]].values-DMD2CCD_wcs_conv_df[["dmd_x_mir_out"]].values)
    delta_dmdy_in_out = np.abs(DMD2CCD_wcs_conv_df[["dmd_y_mir_in"]].values-DMD2CCD_wcs_conv_df[["dmd_y_mir_out"]].values)

    delta_ccdx_in_out = np.abs(DMD2CCD_wcs_conv_df[["ccd_x_pix_in"]].values-DMD2CCD_wcs_conv_df[["ccd_x_pix_out"]].values)
    delta_ccdy_in_out = np.abs(DMD2CCD_wcs_conv_df[["ccd_y_pix_in"]].values-DMD2CCD_wcs_conv_df[["ccd_y_pix_out"]].values)

    DMD2CCD_wcs_conv_df["delta_dmdx_in_out"] = delta_dmdx_in_out
    DMD2CCD_wcs_conv_df["delta_dmdy_in_out"] = delta_dmdy_in_out
    DMD2CCD_wcs_conv_df["delta_ccdx_in_out"] = delta_ccdx_in_out
    DMD2CCD_wcs_conv_df["delta_ccdy_in_out"] = delta_ccdy_in_out

    if plot_hists:
        fig1_hists = plt.figure(figsize=(10,10))
        gs1_hists = GridSpec(figure=fig1_hists,nrows=2,ncols=2,hspace=0.3)
        ax1a_hists = fig1_hists.add_subplot(gs1_hists[0,0])
        ax1b_hists = fig1_hists.add_subplot(gs1_hists[0,1],sharex=ax1a_hists,sharey=ax1a_hists)
        ax2a_hists = fig1_hists.add_subplot(gs1_hists[1,0],sharex=ax1a_hists,sharey=ax1a_hists)
        ax2b_hists = fig1_hists.add_subplot(gs1_hists[1,1],sharex=ax1a_hists,sharey=ax1a_hists)
        
        ax_list = [ax1a_hists, ax1b_hists, ax2a_hists, ax2b_hists]
        key_list = ["dmdx", "dmdy", "ccdx", "ccdy"]
        label_list = [("ccd2dmd", "dmd2ccd"), ("ccd2dmd", "dmd2ccd"), ("dmd2ccd", "ccd2dmd"), ("dmd2ccd", "ccd2dmd")]
        for ax, key, label in zip(ax_list, key_list, label_list):
            data = CCD2DMD_wcs_conv_df[[f"delta_{key}_in_out"]]
            l0, l1 = f"{label[0]}_wcs", f"{label[1]}_wcs_inv"
            ax.hist(data, bins=10, label=l0, alpha=0.8, edgecolor='b', linewidth=1.3)
            ax.hist(data, bins=10, label=l1, alpha=1, edgecolor='red', linestyle='--', hatch="/", fill=False, linewidth=1.3)
            ax.legend(fontsize=12)

        ax1a_hists.set_title(r"$\Delta$ (DMD$_{X,known}$,DMD$_{X,out}$)")
        ax1b_hists.set_title(r"$\Delta$ (DMD$_{Y,known}$,DMD$_{Y,out}$)")
        ax2a_hists.set_title(r"$\Delta$ (CCD$_{X,known}$,CCD$_{X,out}$)")
        ax2b_hists.set_title(r"$\Delta$ (CCD$_{Y,known}$,CCD$_{Y,out}$)")
        fig1_hists.suptitle("WCS results for SIP order = {}".format(sip_degree), fontsize=20,y=0.95)

    return ccd_to_dmd_wcs


class DMDGroup:    
    """
    Series of DMD patterns that correspond to a field of view.
    When slits will produce overlapping spectra in a main FOV, 
    envoke this class to create a series of DMD patterns with no overlap.
    """
    def __init__(self, dmd_slitview_df, logger, regfile=None):
        self.regfile = regfile
        self.logger = logger
        self.RA_FOV = None
        self.DEC_FOV = None
        self.X_FOV = None
        self.Y_FOV = None
        self.Slit_Patterns = None
        
        self.slitDF = dmd_slitview_df.sort_values(by="dmd_y1", ascending=False)
        
        if regfile is not None:
            reg_fname = regfile.name.strip(".reg")
            if "RADEC" in str(regfile):
                radec_text_ind = str(regfile).index("RADEC")+6
                radec_text = regfile[radec_text_ind:].strip(".reg")
                self.RA_FOV = float(radec_text[0])
                self.DEC_FOV = float(radec_text[1])
        elif not self.slitDF.RA.isnull().values.any():
            ra_center = (np.max(self.slitDF['RA']) - np.min(self.slitDF['RA'])) / 2. + np.min(self.slitDF['RA'])
            dec_center = (np.max(self.slitDF['DEC']) - np.min(self.slitDF['DEC'])) / 2. + np.min(self.slitDF['DEC'])
            self.RA_FOV = ra_center
            self.DEC_FOV = dec_center
        
        x_center = (np.max(self.slitDF['dmd_xc']) - np.min(self.slitDF['dmd_xc'])) / 2. + np.min(self.slitDF['dmd_xc'])
        y_center = (np.max(self.slitDF['dmd_yc']) - np.min(self.slitDF['dmd_yc'])) / 2. + np.min(self.slitDF['dmd_yc'])
        
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
            if i == first_ind:
                self.logger.info(f"Accepting first target {i}")
                good_inds.append(i)
                dmd_xc, dmd_yc = input_df.loc[i, ["dmd_xc", "dmd_yc"]]
                self.logger.info(f"Append slit {i}")
                dmd_slit_rows.append(i)
                slit_num += 1
            if j - i >= 1:
                continue
            if i == input_df.index.values[-1]:
                continue
            j = i + 1
            jrow = input_df.loc[j]
            comp_rows = input_df.loc[good_inds].values
            jrows = np.full(comp_rows.shape, jrow)
            
            while ((not self.check_any_overlap(np.array(input_df.loc[j]), np.array(input_df.loc[i]))) & (j<len(input_df)-1) & \
                   (not all(np.array(list(map(self.check_any_overlap, np.full(input_df.loc[good_inds].values.shape, input_df.loc[j]), 
                                              input_df.loc[good_inds].values)))))):
                self.logger.info(f"Skipping target {j}")
                j += 1

            is_good = ((self.check_any_overlap(input_df.loc[j], input_df.loc[i])) & \
                       (all(np.array(list(map(self.check_any_overlap, np.full(input_df.loc[good_inds].values.shape, input_df.loc[j]), 
                                              input_df.loc[good_inds].values))))))
            
            if j < len(input_df) - 1:
                self.logger.info(f"Accepting Target {j}")
                good_inds.append(j)
            elif is_good:
                self.logger.info(f"Accepting Target {j}")
                good_inds.append(j)
            self.logger.info(f"Append slit {j}")
            dmd_slit_rows.append(j)
            slit_num += 1
            i = j
        
        good_pattern_df = input_df.loc[good_inds]
        redo_pattern_df = input_df.drop(index=good_inds)
        if 0 in redo_pattern_df.object.values:
            self.logger.info(f"{input_df}")
        
        return good_pattern_df, redo_pattern_df


    def check_any_overlap(self, row, comp_row):
        row_y0 = int(row[-3])
        row_y1 = int(row[-1])
        
        comp_row_y0 = int(comp_row[-3])
        comp_row_y1 = int(comp_row[-1])
        
        row_vals = set(range(row_y0, row_y1))
        comp_row_vals = set(range(comp_row_y0, comp_row_y1))
        
        if len(row_vals.intersection(comp_row_vals)) > 0:
            return False
        else:
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
            if i == first_ind:
                self.logger.info(f"Accepting first target {i}")
                good_inds.append(i)
                dmd_xc, dmd_yc = input_df.loc[i, ["dmd_xc", "dmd_yc"]]
                self.logger.info(f"Append slit {i}")
                dmd_slit_rows.append(i)
                slit_num += 1
            if j-i >= 1:
                continue
            if i == input_df.index.values[-1]:
                continue

            j = i + 1
            mid_index_ind = int(np.floor(len(input_df) / 2))
            mid = input_df.index.values[mid_index_ind]
            
            while ((input_df.iloc[j]['dmd_y1'] > input_df.iloc[i]['dmd_y0']) & (j<len(input_df)-1)):
                self.logger.info(f"Skipping target {j}")
                j += 1

            self.logger.info(f"Accepting Target {j}")
            if j not in good_inds_l:
                good_inds.extend([j])
            
            l = input_df.index.values[l_ind]

            if (input_df.iloc[l]['dmd_y1'] < input_df.iloc[i]['dmd_y0']) & (l not in good_inds):
                if l < len(input_df) - 1:
                    if input_df.iloc[l]['dmd_y0'] > input_df.iloc[l + 1]['dmd_y1']:
                        good_inds_l.append(l)
                else:
                    good_inds_l.append(l)
            
            self.logger.info(f"Append slit {j}")
            dmd_slit_rows.append(j)
            slit_num += 1
            i = j + 1
        
        good_inds.extend(good_inds_l)
        good_pattern_df = input_df.loc[good_inds]
        
        redo_pattern_df = input_df.drop(index=good_inds)
        
        return good_pattern_df, redo_pattern_df
