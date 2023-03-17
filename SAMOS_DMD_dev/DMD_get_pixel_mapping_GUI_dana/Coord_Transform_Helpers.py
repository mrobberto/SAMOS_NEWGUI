import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec


import astropy
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.wcs.utils import fit_wcs_from_points
from astropy.nddata import CCDData
from astropy.nddata import StdDevUncertainty
from astropy import wcs as astropy_wcs
from astropy import constants as const
from astropy.stats import mad_std, sigma_clipped_stats
from astropy.nddata import CCDData
from astropy.visualization import hist
from astropy.visualization import quantity_support,astropy_mpl_style, simple_norm

from photutils.detection import IRAFStarFinder, DAOStarFinder


plt.rcParams.update({'font.size': 20})
plt.rcParams.update({'xtick.labelsize': 12})
plt.rcParams.update({'ytick.labelsize': 12})
plt.rcParams.update({'axes.titlesize': 15})


def show_fits(ccds,gspec=(1,1),figsize=(5,5),ax_titles=None, fontdict={"fontsize":15},**kwargs):

    """
    Show fits images, single or multiple

    ccds     : image CCDData array or list of CCDData arrays
    
    gspec    : shape of grid spec for axes (if displaying multiple images)

    figsize  : size of figure

    ax_titles : title(s) of axis (axes) (optional, must be same length as ccds list)

    """

    nrows,ncols = gspec

    fig = plt.figure(figsize=figsize)
    gs = GridSpec(nrows=nrows,ncols=ncols,figure=fig,hspace=0.5, wspace=0.5)

    if (nrows==1 or ncols==1) and (type(ccds)!=list): 
            ccds = [ccds]

    if all([type(i)==astropy.nddata.ccddata.CCDData for i in ccds]):
        imdat = [i.data for i in ccds]

    elif all([type(i)==np.ndarray for i in ccds]):
        imdat = ccds

    im_num = 0
    axes = []
    for i in range(gs.nrows):

        for j in range(gs.ncols):
        
            this_ax = fig.add_subplot(gs[i,j])

            this_imdat = imdat[im_num]

            this_norm = simple_norm(data=this_imdat, stretch="log")
            this_img = this_ax.imshow(this_imdat, cmap='gray', origin='lower',
                  norm=this_norm, interpolation='none')

            this_cbar = plt.colorbar(this_img, ax=this_ax, shrink=0.7, format="%.0e")
            this_cbar.ax.tick_params(labelsize=10)

            if ax_titles is not None:

                if type(ax_titles)==list:

                    this_ax.set_title(ax_titles[im_num], y=1.05, fontdict=fontdict)

            axes.append(this_ax)
            im_num+=1
    return fig

def iraf_gridsource_find(ccd,expected_sources,**kwargs):

    iraffind = IRAFStarFinder(brightest=expected_sources,**kwargs)

    irafsources = iraffind(ccd)

    for col in irafsources.colnames:

        irafsources[col].info.format = "%.8f"

    #print(np.sqrt(expected_sources))
    sorted_irafsources = sort_iraf_source_table(irafsources.to_pandas(),numcols=int(np.sqrt(expected_sources)))

    return sorted_irafsources, irafsources

def sort_iraf_source_table(pd_iraf_sources,numcols=11):

    ix_sorted_inds = None

    sorted_coords_full_arr = None

    cols_list = np.array(list(range(numcols)))

    j = -1 # column counter for each row
    this_row_x = [] # list of 11 columns in current row
    this_row_y = []
    this_ix_inds = []
    passed_rows = 0
    pd_iraf_sources = pd_iraf_sources.sort_values(by="ycentroid").reset_index()
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
            #print(this_row_coords)
        
            if sorted_coords_full_arr is None:
                
                sorted_coords_full_arr = this_row_coords
                ix_sorted_inds = sorted_ix_inds
            else:
                sorted_coords_full_arr = np.vstack((sorted_coords_full_arr,this_row_coords))
                ix_sorted_inds = np.hstack((ix_sorted_inds,sorted_ix_inds))
            

            this_row_x, this_row_y = [],[]
            this_ix_inds = []
            #print(sorted_coords_full_arr)
            #print("rows passed",passed_rows)
            j = -1 #reset column counter
            passed_rows+=1 # quick log of rows passed

    return pd_iraf_sources.reindex(ix_sorted_inds).reset_index(drop=True)

from PIL import Image
def create_test_shape(table, save_pattern=False, pattern_save_name='pattern.png',inverted=False):

    xoffset = 0#np.full(len(table.index),int(0))
    yoffset = np.full(len(table.index),int(2048/4))
    y1 = (np.around(table['y'].values.astype(float))-np.floor(table['dy1'].values.astype(float))).astype(int) + yoffset
    y2 = (np.around(table['y'].values.astype(float))+np.ceil(table['dy2'].values.astype(float))).astype(int) + yoffset
    x1 = (np.around(table['x'].values.astype(float))-np.floor(table['dx1'].values.astype(float))).astype(int) + xoffset
    x2 = (np.around(table['x'].values.astype(float))+np.ceil(table['dx2'].values.astype(float))).astype(int) + xoffset
    if inverted:
        test_shape = np.zeros((2048,1080))
        for i in table.index:
            test_shape[y1[i]:y2[i],x1[i]:x2[i]]=1
    else:
        test_shape = np.ones((2048,1080)) # This is the size of the DC2K
        for i in table.index:
            test_shape[y1[i]:y2[i],x1[i]:x2[i]]=0
    test_shape = np.uint8(test_shape) #test_shape.astype(np.uint8)
    
    if save_pattern:
    
        im_pattern = Image.fromarray(test_shape)
        im_pattern.save(pattern_save_name)
    
    return test_shape



def make_grid_pattern(pt_width, pt_height, pt_distance):
    
    dmd_arr = np.ones((1080,1080))
    columns = ["SlitNum", "x", "y", "dx1", "dy1", "dx2", "dy2"]
    table_dat = []
    
    slit_n = 0
    for row in range(dmd_arr.shape[0])[::pt_distance]:
    
        for col in range(dmd_arr.shape[1])[::pt_distance]:
        
            row_dat = [slit_n, col, row, 0, 0, pt_width, pt_height]

            table_dat.append(row_dat)
        
            slit_n+=1
    pattern = pd.DataFrame(data=np.array(table_dat), columns=columns)

    return pattern




class AFFtest:

    def __init__(self, DMD_PIX_df):

        self.patsrc_df = DMD_PIX_df


    def fit_wcs_with_sip(self,sip_degree,plot_hists=True):

        dmd_coords = self.patsrc_df[['x','y']].values
        ccd_coords = self.patsrc_df[['xcentroid','ycentroid']].values

        dmd_sky_coords = SkyCoord(dmd_coords[:,0]*u.arcsecond,dmd_coords[:,1]*u.arcsecond,unit='deg') 
        ccd_sky_coords = SkyCoord(ccd_coords[:,0]*u.arcsecond,ccd_coords[:,1]*u.arcsecond,unit='deg')


        # get WCS for ccd pixel coords to dmd mirror coords
        ccd_to_dmd_wcs = fit_wcs_from_points(xy=ccd_coords.T,
                world_coords=dmd_sky_coords,sip_degree=sip_degree)

        # get WCS for dmd mirror coords to ccd pixel coords
        dmd_to_ccd_wcs = fit_wcs_from_points(xy=dmd_coords.T,
                world_coords=ccd_sky_coords,sip_degree=sip_degree)
        
        
        ccd_x_ra_in_arr = np.array([i.ra.degree for i in ccd_sky_coords])
        ccd_y_dec_in_arr = np.array([i.dec.degree for i in ccd_sky_coords])

        dmd_x_ra_in_arr = np.array([i.ra.degree for i in dmd_sky_coords])
        dmd_y_dec_in_arr = np.array([i.dec.degree for i in dmd_sky_coords])

        ccd_x_pix_in_arr = ccd_coords[:,0]
        ccd_y_pix_in_arr = ccd_coords[:,1]

        dmd_x_mir_in_arr = dmd_coords[:,0]
        dmd_y_mir_in_arr = dmd_coords[:,1]
        
        wcs_conversion_df_cols1 = ["dmd_x_ra_in", "dmd_y_dec_in",
                  "dmd_x_mir_in", "dmd_y_mir_in", 
                  "ccd_x_pix_out","ccd_y_pix_out",
                  "ccd_x_pix_in", "ccd_y_pix_in", 
                  "dmd_x_mir_out", "dmd_y_mir_out",
                  "dmd_x_ra_out", "dmd_y_dec_out"]


        #stop = True
        #if stop:
        #    return ccd_to_dmd_wcs, dmd_to_ccd_wcs

        dmd_x_sky_out_arr, dmd_y_sky_out_arr = ccd_to_dmd_wcs.all_pix2world(ccd_x_pix_in_arr,  ccd_y_pix_in_arr, 0)

        ccd_x_pix_out_arr, ccd_y_pix_out_arr = ccd_to_dmd_wcs.all_world2pix(dmd_x_ra_in_arr,dmd_y_dec_in_arr, 0)


        #dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600

        CCD2DMD_wcs_conv_data = np.column_stack([dmd_x_ra_in_arr, dmd_y_dec_in_arr, 
                          dmd_x_mir_in_arr, dmd_y_mir_in_arr,
                          ccd_x_pix_out_arr, ccd_y_pix_out_arr,
                          ccd_x_pix_in_arr, ccd_y_pix_in_arr,
                          dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600,
                          dmd_x_sky_out_arr, dmd_y_sky_out_arr])


        CCD2DMD_wcs_conv_df = pd.DataFrame(data=CCD2DMD_wcs_conv_data,columns=wcs_conversion_df_cols1)


        delta_dmdx_in_out = np.abs(CCD2DMD_wcs_conv_df[["dmd_x_mir_in"]].values-CCD2DMD_wcs_conv_df[["dmd_x_mir_out"]].values)
        delta_dmdy_in_out = np.abs(CCD2DMD_wcs_conv_df[["dmd_y_mir_in"]].values-CCD2DMD_wcs_conv_df[["dmd_y_mir_out"]].values)

        delta_ccdx_in_out = np.abs(CCD2DMD_wcs_conv_df[["ccd_x_pix_in"]].values-CCD2DMD_wcs_conv_df[["ccd_x_pix_out"]].values)
        delta_ccdy_in_out = np.abs(CCD2DMD_wcs_conv_df[["ccd_y_pix_in"]].values-CCD2DMD_wcs_conv_df[["ccd_y_pix_out"]].values)

        CCD2DMD_wcs_conv_df["delta_dmdx_in_out"] = delta_dmdx_in_out
        CCD2DMD_wcs_conv_df["delta_dmdy_in_out"] = delta_dmdy_in_out
        CCD2DMD_wcs_conv_df["delta_ccdx_in_out"] = delta_ccdx_in_out
        CCD2DMD_wcs_conv_df["delta_ccdy_in_out"] = delta_ccdy_in_out


        wcs_conversion_df_cols2 = ["ccd_x_ra_in", "ccd_y_dec_in",
                   "ccd_x_pix_in", "ccd_y_pix_in",
                   "dmd_x_mir_out", "dmd_y_mir_out",
                   "dmd_x_mir_in", "dmd_y_mir_in", 
                   "ccd_x_pix_out","ccd_y_pix_out",
                   "ccd_x_ra_out", "ccd_y_dec_out"]

        ccd_x_sky_out_arr, ccd_y_sky_out_arr = dmd_to_ccd_wcs.all_pix2world(dmd_x_mir_in_arr,  dmd_y_mir_in_arr, 0)

        dmd_x_mir_out_arr, dmd_y_mir_out_arr = dmd_to_ccd_wcs.all_world2pix(ccd_x_ra_in_arr,ccd_y_dec_in_arr, 0)


        #dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600

        DMD2CCD_wcs_conv_data = np.column_stack([ccd_x_ra_in_arr, ccd_y_dec_in_arr, 
                              ccd_x_pix_in_arr, ccd_y_pix_in_arr,
                              dmd_x_mir_out_arr, dmd_y_mir_out_arr,
                              dmd_x_mir_in_arr, dmd_y_mir_in_arr,
                              ccd_x_sky_out_arr*3600, ccd_y_sky_out_arr*3600,
                             ccd_x_sky_out_arr, ccd_y_sky_out_arr])

        #print(wcs_conversion_df_cols2)
        DMD2CCD_wcs_conv_df = pd.DataFrame(data=DMD2CCD_wcs_conv_data,columns=wcs_conversion_df_cols2)



        delta_dmdx_in_out = np.abs(DMD2CCD_wcs_conv_df[["dmd_x_mir_in"]].values-DMD2CCD_wcs_conv_df[["dmd_x_mir_out"]].values)
        delta_dmdy_in_out = np.abs(DMD2CCD_wcs_conv_df[["dmd_y_mir_in"]].values-DMD2CCD_wcs_conv_df[["dmd_y_mir_out"]].values)

        delta_ccdx_in_out = np.abs(DMD2CCD_wcs_conv_df[["ccd_x_pix_in"]].values-DMD2CCD_wcs_conv_df[["ccd_x_pix_out"]].values)
        delta_ccdy_in_out = np.abs(DMD2CCD_wcs_conv_df[["ccd_y_pix_in"]].values-DMD2CCD_wcs_conv_df[["ccd_y_pix_out"]].values)

        DMD2CCD_wcs_conv_df["delta_dmdx_in_out"] = delta_dmdx_in_out
        DMD2CCD_wcs_conv_df["delta_dmdy_in_out"] = delta_dmdy_in_out
        DMD2CCD_wcs_conv_df["delta_ccdx_in_out"] = delta_ccdx_in_out
        DMD2CCD_wcs_conv_df["delta_ccdy_in_out"] = delta_ccdy_in_out

        #print(DMD2CCD_wcs_conv_df.columns)
        
        self.ccd_to_dmd_wcs = ccd_to_dmd_wcs
        self.CCD2DMD_wcs_conv_df = CCD2DMD_wcs_conv_df
        CCD2DMD_wcs_conv_df.to_csv('MapResults/ccd2dmd_wcs_conversion_df.csv',index=False)
        self.dmd_to_ccd_wcs = dmd_to_ccd_wcs 
        self.DMD2CCD_wcs_conv_df = DMD2CCD_wcs_conv_df
        DMD2CCD_wcs_conv_df.to_csv('MapResults/dmd2ccd_wcs_conversion_df.csv',index=False)


        if plot_hists:
        
            fig1_hists = plt.figure(figsize=(10,10))
            gs1_hists = GridSpec(figure=fig1_hists,nrows=2,ncols=2,hspace=0.3)
            ax1a_hists = fig1_hists.add_subplot(gs1_hists[0,0])
            ax1b_hists = fig1_hists.add_subplot(gs1_hists[0,1],sharex=ax1a_hists,sharey=ax1a_hists)

            ax2a_hists = fig1_hists.add_subplot(gs1_hists[1,0],sharex=ax1a_hists,sharey=ax1a_hists)
            ax2b_hists = fig1_hists.add_subplot(gs1_hists[1,1],sharex=ax1a_hists,sharey=ax1a_hists)




            ax1a_hists.hist(CCD2DMD_wcs_conv_df[["delta_dmdx_in_out"]],bins=10,label="ccd2dmd_wcs",alpha=0.8,edgecolor='b',
                linewidth=1.3)


            ax1a_hists.hist(DMD2CCD_wcs_conv_df[["delta_dmdx_in_out"]],bins=10,label="dmd2ccd_wcs_inv", alpha=1,edgecolor='red',
                linestyle='--',hatch="/",fill=False,linewidth=1.3)

            ax1a_hists.legend(fontsize=12)
            ax1a_hists.set_title(r"$\Delta$ (DMD$_{X,known}$,DMD$_{X,out}$)")


            ax1b_hists.hist(CCD2DMD_wcs_conv_df[["delta_dmdy_in_out"]],bins=10,label="ccd2dmd_wcs",alpha=0.8,edgecolor='b',
                linewidth=1.3)


            ax1b_hists.hist(DMD2CCD_wcs_conv_df[["delta_dmdy_in_out"]],bins=10,label="dmd2ccd_wcs_inv", alpha=1,edgecolor='red',
                linestyle='--',hatch="/",fill=False,linewidth=1.3)

            ax1b_hists.legend(fontsize=12)

            ax1b_hists.set_title(r"$\Delta$ (DMD$_{Y,known}$,DMD$_{Y,out}$)")




            ax2a_hists.hist(DMD2CCD_wcs_conv_df[["delta_ccdx_in_out"]],bins=10,label="dmd2ccd_wcs",alpha=0.8,edgecolor='b',
                linewidth=1.3)


            ax2a_hists.hist(CCD2DMD_wcs_conv_df[["delta_ccdx_in_out"]],bins=10,label="ccd2dmd_wcs_inv", alpha=1,edgecolor='red',
                linestyle='--',hatch="/",fill=False,linewidth=1.3)

            ax2a_hists.legend(fontsize=12)

            ax2a_hists.set_title(r"$\Delta$ (CCD$_{X,known}$,CCD$_{X,out}$)")


            ax2b_hists.hist(DMD2CCD_wcs_conv_df[["delta_ccdy_in_out"]],bins=10,label="dmd2ccd_wcs",alpha=0.8,edgecolor='b',
                linewidth=1.3)


            ax2b_hists.hist(CCD2DMD_wcs_conv_df[["delta_ccdy_in_out"]],bins=10,label="ccd2dmd_wcs_inv", alpha=1,edgecolor='red',
                linestyle='--',hatch="/",fill=False,linewidth=1.3)

            ax2b_hists.legend(fontsize=12)

            ax2b_hists.set_title(r"$\Delta$ (CCD$_{Y,known}$,CCD$_{Y,out}$)")

            fig1_hists.suptitle("WCS results for SIP order = {}".format(sip_degree), fontsize=20,y=0.95)


    

    def get_average_offsets_grouped(self, sip_wcs_df, show_plot=False):


        mir_in_xcols = list(set(sip_wcs_df.dmd_x_mir_in.values))
        mir_in_yrows = list(set(sip_wcs_df.dmd_y_mir_in.values))


        row_dfs = [sip_wcs_df.where(sip_wcs_df.dmd_y_mir_in==ry).dropna(how='all') for ry in mir_in_yrows]
        col_dfs = [sip_wcs_df.where(sip_wcs_df.dmd_x_mir_in==rx).dropna(how='all') for rx in mir_in_xcols]

        self.avg_delta_xmir_by_yrow = [np.mean(rowdf.delta_dmdx_in_out.values) for rowdf in row_dfs]
        self.avg_delta_ymir_by_yrow = [np.mean(rowdf.delta_dmdy_in_out.values) for rowdf in row_dfs]

        self.med_delta_xmir_by_yrow = [np.median(rowdf.delta_dmdx_in_out.values) for rowdf in row_dfs]
        self.med_delta_ymir_by_yrow = [np.median(rowdf.delta_dmdy_in_out.values) for rowdf in row_dfs]


        self.avg_delta_xmir_by_xcol = [np.mean(coldf.delta_dmdx_in_out.values) for coldf in col_dfs]
        self.avg_delta_ymir_by_xcol = [np.mean(coldf.delta_dmdy_in_out.values) for coldf in col_dfs]

        self.med_delta_xmir_by_xcol = [np.median(coldf.delta_dmdx_in_out.values) for coldf in col_dfs]
        self.med_delta_ymir_by_xcol = [np.median(coldf.delta_dmdy_in_out.values) for coldf in col_dfs]


        self.avg_delta_xpix_by_yrow = [np.mean(rowdf.delta_ccdx_in_out.values) for rowdf in row_dfs]
        self.avg_delta_ypix_by_yrow = [np.mean(rowdf.delta_ccdy_in_out.values) for rowdf in row_dfs]

        self.med_delta_xpix_by_yrow = [np.median(rowdf.delta_ccdx_in_out.values) for rowdf in row_dfs]
        self.med_delta_ypix_by_yrow = [np.median(rowdf.delta_ccdy_in_out.values) for rowdf in row_dfs]


        self.avg_delta_xpix_by_xcol = [np.mean(coldf.delta_ccdx_in_out.values) for coldf in col_dfs]
        self.avg_delta_ypix_by_xcol = [np.mean(coldf.delta_ccdy_in_out.values) for coldf in col_dfs]

        self.med_delta_xpix_by_xcol = [np.median(coldf.delta_ccdx_in_out.values) for coldf in col_dfs]
        self.med_delta_ypix_by_xcol = [np.median(coldf.delta_ccdy_in_out.values) for coldf in col_dfs]


    def plot_offsets_by_group(self,sip_wcs_df,avg=True):


        fig = plt.figure(figsize=(8,8))
        gs = GridSpec(nrows=2,ncols=2)


        ax1 = fig.add_subplot(gs[0,0])
        ax2 = fig.add_subplot(gs[1,0],sharey=ax1,sharex=ax1)

        x_cols_mir_in = list(set(sip_wcs_df.dmd_x_mir_in.values))
        y_rows_mir_in = list(set(sip_wcs_df.dmd_y_mir_in.values))
        
        #ax1.scatter(self.x_cols_mir)
        
        if avg:

            ax1_title = "X offset averages by row"



def check_wcs_output_from_sip_degree(sip_degree, dmd_coords, dmd_sky_coords, ccd_coords, ccd_sky_coords,
                    plot_hists=True):
    
    
    # get WCS for ccd pixel coords to dmd mirror coords
    ccd_to_dmd_wcs = fit_wcs_from_points(xy=ccd_coords.T,
            world_coords=dmd_sky_coords,sip_degree=sip_degree)

    # get WCS for dmd mirror coords to ccd pixel coords
    dmd_to_ccd_wcs = fit_wcs_from_points(xy=dmd_coords.T,
            world_coords=ccd_sky_coords,sip_degree=sip_degree)


    ccd_x_ra_in_arr = np.array([i.ra.degree for i in ccd_sky_coords])
    ccd_y_dec_in_arr = np.array([i.dec.degree for i in ccd_sky_coords])

    dmd_x_ra_in_arr = np.array([i.ra.degree for i in dmd_sky_coords])
    dmd_y_dec_in_arr = np.array([i.dec.degree for i in dmd_sky_coords])

    ccd_x_pix_in_arr = ccd_coords[:,0]
    ccd_y_pix_in_arr = ccd_coords[:,1]

    dmd_x_mir_in_arr = dmd_coords[:,0]
    dmd_y_mir_in_arr = dmd_coords[:,1]

    wcs_conversion_df_cols1 = ["dmd_x_ra_in", "dmd_y_dec_in",
              "dmd_x_mir_in", "dmd_y_mir_in", 
              "ccd_x_pix_out","ccd_y_pix_out",
              "ccd_x_pix_in", "ccd_y_pix_in", 
              "dmd_x_mir_out", "dmd_y_mir_out",
              "dmd_x_ra_out", "dmd_y_dec_out"]

    dmd_x_sky_out_arr, dmd_y_sky_out_arr = ccd_to_dmd_wcs.all_pix2world(ccd_x_pix_in_arr,  ccd_y_pix_in_arr, 0)

    print(len(dmd_x_ra_in_arr),len(dmd_y_dec_in_arr),len(ccd_x_pix_in_arr),len(ccd_y_pix_in_arr))
    ccd_x_pix_out_arr, ccd_y_pix_out_arr = ccd_to_dmd_wcs.all_world2pix(dmd_x_ra_in_arr,dmd_y_dec_in_arr, 0)


    #dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600

    CCD2DMD_wcs_conv_data = np.column_stack([dmd_x_ra_in_arr, dmd_y_dec_in_arr, 
                      dmd_x_mir_in_arr, dmd_y_mir_in_arr,
                      ccd_x_pix_out_arr, ccd_y_pix_out_arr,
                      ccd_x_pix_in_arr, ccd_y_pix_in_arr,
                      dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600,
                      dmd_x_sky_out_arr, dmd_y_sky_out_arr])


    CCD2DMD_wcs_conv_df = pd.DataFrame(data=CCD2DMD_wcs_conv_data,columns=wcs_conversion_df_cols1)


    delta_dmdx_in_out = np.abs(CCD2DMD_wcs_conv_df[["dmd_x_mir_in"]].values-CCD2DMD_wcs_conv_df[["dmd_x_mir_out"]].values)
    delta_dmdy_in_out = np.abs(CCD2DMD_wcs_conv_df[["dmd_y_mir_in"]].values-CCD2DMD_wcs_conv_df[["dmd_y_mir_out"]].values)

    delta_ccdx_in_out = np.abs(CCD2DMD_wcs_conv_df[["ccd_x_pix_in"]].values-CCD2DMD_wcs_conv_df[["ccd_x_pix_out"]].values)
    delta_ccdy_in_out = np.abs(CCD2DMD_wcs_conv_df[["ccd_y_pix_in"]].values-CCD2DMD_wcs_conv_df[["ccd_y_pix_out"]].values)

    CCD2DMD_wcs_conv_df["delta_dmdx_in_out"] = delta_dmdx_in_out
    CCD2DMD_wcs_conv_df["delta_dmdy_in_out"] = delta_dmdy_in_out
    CCD2DMD_wcs_conv_df["delta_ccdx_in_out"] = delta_ccdx_in_out
    CCD2DMD_wcs_conv_df["delta_ccdy_in_out"] = delta_ccdy_in_out


    wcs_conversion_df_cols2 = ["ccd_x_ra_in", "ccd_y_dec_in",
               "ccd_x_pix_in", "ccd_y_pix_in",
               "dmd_x_mir_out", "dmd_y_mir_out",
               "dmd_x_mir_in", "dmd_y_mir_in", 
               "ccd_x_pix_out","ccd_y_pix_out",
               "ccd_x_ra_out", "ccd_y_dec_out"]

    ccd_x_sky_out_arr, ccd_y_sky_out_arr = dmd_to_ccd_wcs.all_pix2world(dmd_x_mir_in_arr,  dmd_y_mir_in_arr, 0)

    dmd_x_mir_out_arr, dmd_y_mir_out_arr = dmd_to_ccd_wcs.all_world2pix(ccd_x_ra_in_arr,ccd_y_dec_in_arr, 0)


    #dmd_x_sky_out_arr*3600, dmd_y_sky_out_arr*3600

    DMD2CCD_wcs_conv_data = np.column_stack([ccd_x_ra_in_arr, ccd_y_dec_in_arr, 
                          ccd_x_pix_in_arr, ccd_y_pix_in_arr,
                          dmd_x_mir_out_arr, dmd_y_mir_out_arr,
                          dmd_x_mir_in_arr, dmd_y_mir_in_arr,
                          ccd_x_sky_out_arr*3600, ccd_y_sky_out_arr*3600,
                         ccd_x_sky_out_arr, ccd_y_sky_out_arr])

    #print(wcs_conversion_df_cols2)
    DMD2CCD_wcs_conv_df = pd.DataFrame(data=DMD2CCD_wcs_conv_data,columns=wcs_conversion_df_cols2)



    delta_dmdx_in_out = np.abs(DMD2CCD_wcs_conv_df[["dmd_x_mir_in"]].values-DMD2CCD_wcs_conv_df[["dmd_x_mir_out"]].values)
    delta_dmdy_in_out = np.abs(DMD2CCD_wcs_conv_df[["dmd_y_mir_in"]].values-DMD2CCD_wcs_conv_df[["dmd_y_mir_out"]].values)

    delta_ccdx_in_out = np.abs(DMD2CCD_wcs_conv_df[["ccd_x_pix_in"]].values-DMD2CCD_wcs_conv_df[["ccd_x_pix_out"]].values)
    delta_ccdy_in_out = np.abs(DMD2CCD_wcs_conv_df[["ccd_y_pix_in"]].values-DMD2CCD_wcs_conv_df[["ccd_y_pix_out"]].values)

    DMD2CCD_wcs_conv_df["delta_dmdx_in_out"] = delta_dmdx_in_out
    DMD2CCD_wcs_conv_df["delta_dmdy_in_out"] = delta_dmdy_in_out
    DMD2CCD_wcs_conv_df["delta_ccdx_in_out"] = delta_ccdx_in_out
    DMD2CCD_wcs_conv_df["delta_ccdy_in_out"] = delta_ccdy_in_out

    #print(DMD2CCD_wcs_conv_df.columns)
    
    if plot_hists:
    
        fig1_hists = plt.figure(figsize=(10,10))
        gs1_hists = GridSpec(figure=fig1_hists,nrows=2,ncols=2,hspace=0.3)
        ax1a_hists = fig1_hists.add_subplot(gs1_hists[0,0])
        ax1b_hists = fig1_hists.add_subplot(gs1_hists[0,1],sharex=ax1a_hists,sharey=ax1a_hists)

        ax2a_hists = fig1_hists.add_subplot(gs1_hists[1,0],sharex=ax1a_hists,sharey=ax1a_hists)
        ax2b_hists = fig1_hists.add_subplot(gs1_hists[1,1],sharex=ax1a_hists,sharey=ax1a_hists)




        ax1a_hists.hist(CCD2DMD_wcs_conv_df[["delta_dmdx_in_out"]],bins=10,label="ccd2dmd_wcs",alpha=0.8,edgecolor='b',
            linewidth=1.3)


        ax1a_hists.hist(DMD2CCD_wcs_conv_df[["delta_dmdx_in_out"]],bins=10,label="dmd2ccd_wcs", alpha=1,edgecolor='red',
            linestyle='--',hatch="/",fill=False,linewidth=1.3)

        ax1a_hists.legend()
        ax1a_hists.set_title(r"$\Delta$ (DMD$_{X,in}$,DMD$_{X,out}$)")


        ax1b_hists.hist(CCD2DMD_wcs_conv_df[["delta_dmdy_in_out"]],bins=10,label="ccd2dmd_wcs",alpha=0.8,edgecolor='b',
            linewidth=1.3)


        ax1b_hists.hist(DMD2CCD_wcs_conv_df[["delta_dmdy_in_out"]],bins=10,label="dmd2ccd_wcs", alpha=1,edgecolor='red',
            linestyle='--',hatch="/",fill=False,linewidth=1.3)

        ax1b_hists.legend()

        ax1b_hists.set_title(r"$\Delta$ (DMD$_{Y,in}$,DMD$_{Y,out}$)")




        ax2a_hists.hist(CCD2DMD_wcs_conv_df[["delta_ccdx_in_out"]],bins=10,label="ccd2dmd_wcs",alpha=0.8,edgecolor='b',
            linewidth=1.3)


        ax2a_hists.hist(DMD2CCD_wcs_conv_df[["delta_ccdx_in_out"]],bins=10,label="dmd2ccd_wcs", alpha=1,edgecolor='red',
            linestyle='--',hatch="/",fill=False,linewidth=1.3)

        ax2a_hists.legend()

        ax2a_hists.set_title(r"$\Delta$ (CCD$_{X,in}$,CCD$_{X,out}$)")


        ax2b_hists.hist(CCD2DMD_wcs_conv_df[["delta_ccdy_in_out"]],bins=10,label="ccd2dmd_wcs",alpha=0.8,edgecolor='b',
            linewidth=1.3)


        ax2b_hists.hist(DMD2CCD_wcs_conv_df[["delta_ccdy_in_out"]],bins=10,label="dmd2ccd_wcs", alpha=1,edgecolor='red',
            linestyle='--',hatch="/",fill=False,linewidth=1.3)

        ax2b_hists.legend()

        ax2b_hists.set_title(r"$\Delta$ (CCD$_{Y,in}$,CCD$_{Y,out}$)")

        fig1_hists.suptitle("WCS results for SIP order = {}".format(sip_degree), fontsize=20,y=0.95)

    return ccd_to_dmd_wcs, CCD2DMD_wcs_conv_df, dmd_to_ccd_wcs, DMD2CCD_wcs_conv_df

