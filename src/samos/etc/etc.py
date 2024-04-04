"""
This file contains the SAMOS ETC computation (as separate from the ETC UI tab which is
located at samos.ui.etc).
"""
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path
import yaml

from astropy import constants as c
from astropy import units as u
import pandas as pd
from scipy import interpolate

import tkinter as tk
from tkinter import ttk

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *


class ETC:

    def __init__(self, parameters, logger):
        self.params = parameters
        self.read_throughput_files()
        self.read_AB_filters()
        self.printed = {}


    def read_throughput_files(self):
        # SAMOS
        samos_throughputs = get_data_file('etc.filters', 'samos.yaml')
        with open(samos_throughputs) as in_file:
            samos = yaml.safe_load(in_file)

        for item in ['lowred', 'lowblue', 'highred', 'highblue']:
            wave_array = np.array(samos[item]['wave'], dtype=np.float32) * u.Unit(samos[item]['waveunit'])
            flux_array = np.array(samos[item]['throughput'], dtype=np.float32) * samos[item]['throughput_scale']
            setattr(self, f'samos_{item}_wave', wave_array)
            setattr(self, f'samos_{item}_flux', flux_array)

        # SAMI
        sami_throughputs = get_data_file('etc.filters', 'sami.yaml')
        with open(sami_throughputs) as in_file:
            sami = yaml.safe_load(in_file)

        for item in ['ccd', 'window']:
            wave_array = np.array(sami[item]['wave'], dtype=np.float32) * u.Unit(sami[item]['waveunit'])
            flux_array = np.array(sami[item]['throughput'], dtype=np.float32) * sami[item]['throughput_scale']
            setattr(self, f'sami_{item}_wave', wave_array)
            setattr(self, f'sami_{item}_flux', flux_array)
        
        # Treat actual CCD throughput as being CCD * window
        self.sami_ccd_flux *= self.sami_window_flux
        
        #SAM throuhgput: from A. Tokovinin, private communicaiton
        self.sam_throughput = 0.9  


    def read_AB_filters(self):
        filter_path = get_data_file("etc", "filters")
        AB_filter = self.params["spec_mag_band"]
        if AB_filter  == 'u_SDSS':
            df = pd.read_csv(filter_path / 'u_SDSS.res', delimiter='\s+', header=None)
        if AB_filter  == 'g_SDSS':
            df = pd.read_csv(filter_path / 'g_SDSS.res', delimiter='\s+', header=None)
        if AB_filter  == 'r_SDSS':
            df = pd.read_csv(filter_path / 'r_SDSS.res', delimiter='\s+', header=None)
        if AB_filter  == 'i_SDSS':
            df = pd.read_csv(filter_path / 'i_SDSS.res', delimiter='\s+', header=None)
        if AB_filter  == 'z_SDSS':
            df = pd.read_csv(filter_path / 'z_SDSS.res', delimiter='\s+', header=None)
        if AB_filter  == 'Y_VISTA':
            df = pd.read_csv(filter_path / 'Y_uv.res', delimiter='\s+', comment='#', header=None)
        if AB_filter  == 'J_VISTA':
            df = pd.read_csv(filter_path / 'J_uv.res', delimiter='\s+', comment='#', header=None)
        if AB_filter  == 'H_VISTA':
            df = pd.read_csv(filter_path / 'H_uv.res', delimiter='\s+', comment='#', header=None)
        if AB_filter  == 'K_VISTA':
            df = pd.read_csv(filter_path / 'K_uv.res', delimiter='\s+', comment='#', header=None)
        return df.to_numpy() 


    def read_spectrum(self):
        if "Pickles_1998" in str(self.spec_path):
            # Pickles model
            df = pd.read_csv(self.spec_path, delimiter='\s+', header=None)
            df = df.to_numpy()
            wl_A = df[:,0]
            userspec_wl_um =  ((df[:,0]).flatten() / 10000.0) * u.um
            userspec_Flam =  ((df[:,1]).flatten()) * u.erg / u.s / (u.cm * u.cm) / u.angstrom
            userspec_Fnu = userspec_Flam * c.c / (userspec_wl_um.to(u.angstrom) * userspec_wl_um.to(u.angstrom))
        elif "BT-Settl" in str(self.spec_path):
            # Stellar Models: Allard Spectra
            t_lwr = Table.read(self.spec_path, format='fits')
            wl = t_lwr['wl_A'] * u.angstrom
            wl = wl[np.where((wl >= 3E2) & (wl <= 3E6))]
            Flam = 10**(t_lwr['Flam']-8) * u.erg / u.s / (u.cm * u.cm) / u.angstrom
            Flam = Flam[np.where((wl >= 3E2) & (wl <= 3E6))]
            userspec_wl_um = wl.to(u.um)
            userspec_Fnu = userspec_Flam * c.c / (userspec_wl_um.to(u.angstrom) * userspec_wl_um.to(u.angstrom))
        else:
            df = pd.read_csv(self.spec_path, delimiter='\s+', header=None)
            df = df.to_numpy()
            wl = df[2:,0]
            Fl = df[2:,1]
            if self.params["line_cenwave_units"] == 'angstroms':
                wl = wl * u.angstrom
            else:
                wl = wl * u.um
            if self.params["spec_fluxunit"] == 'F_lam':
                userspec_Flam = Fl * u.erg / u.s / (u.cm * u.cm) / u.angstrom
                userspec_Fnu = userspec_Flam * c.c / (wl.to(u.angstrom) * wl.to(u.angstrom))
            else:    
                userspec_Fnu = Fl * u.erg / u.s / (u.cm * u.cm)
            userspec_wl_um = wl.to(u.um)

        self.user_Wave = userspec_wl_um
        self.user_Flux = userspec_Fnu


    def Moffat4(self, FWHM, beta):
        """
        The purpose of Moffat4 is to mimic what output would look like based on the
        inherent flaws of optics of telescope
        
        The basic process is to convert everything to velocity, make a gaussian kernel and
        convolve it with the rest of the function, then convert back to wavelength
        
        beta is the Moffat parameter, FWHM is in arcseconds.
        """
        FWHM = FWHM.to(u.arcsec).value
        xc = 512
        yc = 512
        rows, cols = (xc, yc)
        dist_circle = np.zeros((xc,yc), dtype=np.float64)
        for i in range(rows):
            for j in range(cols):
                dist_circle[i,j] = np.sqrt( (i-xc/2)**2 + (j-yc/2)**2 )

        FWHM_75 = FWHM * 75.
        # Well-known relation, e.g. from http://pixinsight.com/doc/tools/DynamicPSF/DynamicPSF.html
        # or Patat 2011 http://www.aanda.org/articles/aa/full_html/2011/03/aa15537-10/aa15537-10.html    
        alpha = FWHM_75 / (2. * np.sqrt(2.**(1. / beta) - 1.))
        # Got this analytic form Patat et al. or http://en.wikipedia.org/wiki/Moffat_distribution
        PSF_Moffat4 = (beta - 1) / (np.pi * alpha**2) / (1. + dist_circle**2 / alpha**2)**beta     
        return PSF_Moffat4.astype(np.float32)


    def DMDslit4(self, Nslit_X, Nslit_Y):
        """
        1 DMD side is typically 10 micron size = 166.6 mas
        The gap is 0.6 micron wide, i.e. 10 mas (exactly!).

        We sample the gap with 3 pixels: 1 pixel = 0.2 micron = 3.33mas. The grid is 
        therefore made of:

            3-pixel-wide gap
            50-pixel-wide mirror sides

        1" is therefore 300 pixels.

        If we work with images of 2048x2048 pixels, we have 6.82" fields; enough for a 
        decent long slit.
        """
        Nslit_X = Nslit_X.value
        Nslit_Y = Nslit_Y.value
        rows, cols = 512, 512
        slit4 = np.ones((rows, cols), dtype=np.float64)

        Xparity = np.fmod(Nslit_X / 2, 1)
        if Xparity != 0:
              slit4[:256 - int(Nslit_X * 8), :] = 0 
              slit4[256 + int(Nslit_X * 8):, :] = 0
        else:          
              slit4[:256 - int(Nslit_X / 2 * 13), :] = 0 
              slit4[256 + int(Nslit_X / 2 * 13):, :] = 0

        Yparity = np.fmod(Nslit_Y / 2, 1)
        if Yparity != 0:
              slit4[:, :256 - int(Nslit_Y * 8)] = 0 
              slit4[:, 256 + int(Nslit_Y * 8):] = 0
        else: 
              slit4[:, :256-int(Nslit_Y / 2 * 7)] = 0 
              slit4[:, 256+int(Nslit_Y / 2 * 7):] = 0
        return slit4


    def slit_loss(self, FWHM, beta, Nslit_X, Nslit_Y):
        PSF_in = self.Moffat4(FWHM, beta)
        slit = self.DMDslit4(Nslit_X, Nslit_Y)
        PSF_out = np.multiply(PSF_in, slit)
        slit_loss = np.sum(PSF_out)
        return slit_loss


    def degrade_resolution(self, wavelengths, flux, center_wave, spec_res, disp, px_tot):    
        wavelengths = wavelengths.to(u.um)
        center_wave = center_wave.to(u.um)
        spec_res = spec_res.value
        c_kms = c.c.to(u.km / u.s)
        
        # Number of pixels to be output - 50%  more than are on the detector to cover the K band for MOSFIRE  
        Npix_spec = int(np.round(px_tot.value * 3./2.))

        # make "velocity" grid centered at the central wavelength of the band sampled at 1 km/s, 
        # from -300,000 to 300,000 Km/s
        vel_array = np.arange(-300000, 300001) * u.km / u.s

        # the array of wavelengths coming in input is converted to velocity difference vs. central wavelength, in km/s
        in_vel = (wavelengths / center_wave - 1) * c_kms

        # if the array of wavelengths too wide we can get non-physical velocities: kill them and their relative
        # input flux array create vectors in velocity space, picking realistic values (keeping good indices)
        scalar_in_vel = in_vel.value
        scalar_vel_array = vel_array.value
        good_vel_range = np.where((scalar_in_vel > np.min(scalar_vel_array)) & (scalar_in_vel < np.max(scalar_vel_array)))
        in_vel_short = in_vel[good_vel_range]
        in_flux_short = flux[good_vel_range]

        # these new arrays of rel. velocities from the center_wave, and relative fluxes, are calculated starting
        # from the wavelengths and therefore are not uniformly sampled. Interpolate to equally spaced km/s, up to
        # 600000 points
        f = interpolate.interp1d(in_vel_short, in_flux_short, fill_value="extrapolate")   
        interp_flux = f(scalar_vel_array)

        # Now we need to blur this highly dispersed spectrum with the response of the slit, in km/s.
        # - sigma  = the resolution of the spectrograph in km/s, expressed as sigma of the Gaussian response.
        # - it is Delta_lam/lam = Delta_v/c = FWHM/c = 2SQRT(2log2)/c, since
        # - FWHM = 2*SQRT(2*log2) x sigma = 2.35 x sigma.
        # - Therefore, since FWHM/c = Dlambda/lambda = 1/R, we have sigma*2.35 = c/R, i.e. 
        sigma = c_kms / spec_res / (2 * np.sqrt(2 * np.log(2)))

        # Now make a smaller velocity array with the same velocity "resolution" as the steps in vel, above
        n = np.round(8. * sigma.value)
        
        # make sure that n is odd so there is a well defined central velocity...
        if (n % 2 == 0): 
            n = n + 1

        # create an array of n values in the range [-4*sigma,+4*sigma] in km/s,
        # e.g. from -509km/s to +509km/s in this case   
        vel_kernel = (np.arange(n) - np.floor(n / 2.0)) * u.km / u.s

        # create a normalized gaussian (unit area) with width=sigma
        gauss_kernel = (1 / (np.sqrt(2 * np.pi) * sigma)) * np.exp(-0.5 * vel_kernel**2.0 / sigma**2.0)

        # convolve flux with gaussian kernel
        convol_flux = np.convolve(interp_flux, gauss_kernel.value , mode="same") 
        convol_wave = center_wave * (vel_array / c_kms + 1.0)

        # and the real pixel scale 
        real_wave = (np.arange(Npix_spec)*u.pix * disp).to(u.um)
        real_wave = real_wave - real_wave[int(np.round(Npix_spec/2.))]
        real_wave = real_wave + center_wave

        # interpolate transmission onto the pixel scale of the detector
        out = {"lam": real_wave, "flux": np.interp(real_wave, convol_wave.to(u.um), convol_flux)}
        return(out)


    def plot_obs(self):
        struct = self.spec_struct
        
        wave_grid = struct['wave']
        sn_index = struct['plot_index']
        filt_index = struct['filt_index']
        tpSpecObs = struct['tp']
        fltSpecObs = struct['filt']
        tranSpecObs = struct['tran']
        bkSpecObs = struct['bk']
        signalSpecObs = struct['signal']
        noiseSpecObs = struct['noise']
        snSpecObs = struct['sn']
        center = struct['center']
        time = struct['time']
        lineF = struct['line_flux']
        line_width = struct["line_width"]

        # Plot Chosen line/spectrum
        if (self.params['wl_type'] == "default") and (self.params["flux_mode"] == "magnitude"):
            index = np.where(fltSpecObs > 0.05)
            xrange = [np.floor(min(wave_grid[index] * 100)) / 100., np.ceil(max(wave_grid[index] * 100)) / 100.]
            x = wave_grid
            y = fltSpecObs * time / max(fltSpecObs * time)
        elif (self.params['wl_type'] == "default") and (self.params["flux_mode"] == "flux"):
            index = np.where(abs(wave_grid - center) < .01)
            xrange = [np.floor(min(wave_grid[index] * 100)) / 100., np.ceil(max(wave_grid[index] * 100)) / 100.]
            x = wave_grid
            y = signalSpecObs / max(signalSpecObs)     
        elif (self.params['wl_type'] == "user") and (self.params["flux_mode"] == "magnitude"):
            xrange = [self.params['wl_min'].to(u.um), self.params['wl_max'].to(u.um)]
            index = np.where((wave_grid > xrange[0]) & (wave_grid < xrange[1]))
            x = wave_grid
            y = fltSpecObs * time / max(fltSpecObs * time)
        elif (self.params['wl_type'] == "user") and (self.params["flux_mode"] == "flux"):
            xrange = [self.params['wl_min'].to(u.um), self.params['wl_max'].to(u.um)]
            index = np.where((wave_grid > xrange[0]) & (wave_grid < xrange[1]))
            x = wave_grid
            y = signalSpecObs / max(signalSpecObs)

        fig = plt.Figure(figsize=(6, 6))
        a = fig.add_subplot(111)
        fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
        a.plot(x[index], y[index], color='white')
        a.axis(xmin=xrange[0].value, xmax=xrange[1].value)
        a.set_xlabel("Wavelength (micron)", fontsize=12)
        a.set_ylabel("Transmission", fontsize=12)

        # Plot atmospheric trasparency
        line_tran, = a.plot(x[index], tranSpecObs[index], 'm-', label='tran')
        # Plot throughput
        line_tp, = a.plot(x[index], tpSpecObs[index], 'g-', label="tp")

        # Plot sky and background
        a.plot(x[index], np.sqrt(bkSpecObs[index]) / (2 * max(signalSpecObs[index])), 'r-', label='sky res')

        # Plot signal
        a.plot(x[index], signalSpecObs[index] / (2  *max(signalSpecObs[index])), 'b-', label='science')

        a.legend(bbox_to_anchor=(0.7, 0.97), loc='upper left', borderaxespad=0.02)

        a2 = a.twinx()
        a2.set_ylabel('photons/pixel')
        a2.axis(ymin=0, ymax=2 * max(signalSpecObs[index].value))
        
        self.printed["transmission"] = tranSpecObs[index]
        self.printed["background"] = bkSpecObs[index]
        self.printed["throughput"] = tpSpecObs[index]
        self.printed["signal"] = signalSpecObs[index]
        self.printed["wavegrid"] = wave_grid[index]
        self.printed["noise"] = noiseSpecObs[index]
        self.printed["snr"] = snSpecObs[index]

        return fig


    def plot_snr(self):
        struct=self.spec_struct

        wave_grid = struct['wave']
        sn_index = struct['plot_index']
        noiseSpecObs = struct['noise']
        snSpecObs = struct['sn']
        tpSpecObs = struct['tp']
        filt_index = struct['filt_index']
        signalSpecObs = struct['signal']
        bkSpecObs = struct['bk']
        tranSpecObs = struct['tran']
        center = struct['center']
        time = struct['time']
        fltSpecObs = struct['filt']
        lineF = struct['line_flux']
        line_width = struct["line_width"]

        fig = plt.Figure(figsize=(6,6))
        host = fig.add_subplot(111)
        fig.subplots_adjust(top=0.98, bottom=0.18, left=0.12, right=0.86) 
        par1 = host.twinx()
        host.set_xlim( (x[index])[0], (x[index])[-1] ) 
        host.set_ylim(0, 1.3 * max(snSpecObs))
        par1.set_ylim(0, 2 * max(signalSpecObs[index]))

        host.set_xlabel("Wavelength (micron)", fontsize=12)
        host.set_ylabel("S/N per pixel")
        par1.set_ylabel("photons/pixel")

        color1 = "green"
        color2 = "blue"
        color3 = "red"

        p1, = host.plot(wave_grid[index], snSpecObs[index], color=color1, label="S/N")
        p2, = par1.plot(wave_grid[index], signalSpecObs[index], color=color2, label="signal")
        p3, = par1.plot(wave_grid[index], noiseSpecObs[index], color=color3, label="noise")

        lns = [p1, p2, p3]
        host.legend(handles=lns, loc='best')
        
        self.printed["transmission"] = tranSpecObs[index]
        self.printed["background"] = bkSpecObs[index]
        self.printed["throughput"] = tpSpecObs[index]
        self.printed["signal"] = signalSpecObs[index]
        self.printed["wavegrid"] = wave_grid[index]
        self.printed["noise"] = noiseSpecObs[index]
        self.printed["snr"] = snSpecObs[index]

        return fig


    def print_to_file(self):
        return self.printed


    def run_calculation(self):
        WaterVapor_Value = self.params["WaterVapour"]
        band = self.params["bandpass"]
        slit_width = self.params["slit"]  # slit width in arcsec
        nExp = self.params["n_exp"]
        theta = self.params["source_fwhm"]  # source angular extent in arcsec
        Nreads = 1
        lineWl = self.params["line_cenwave"].to(u.um)
        FWHM = self.params["line_fwhm"] # in km/s
        z_line = self.params["line_redshift"]
        mag = self.params["spec_mag"]
        z_spec = self.params["spec_redshift"]
        Vega_band = self.params["spec_mag_band"]
        SN = self.params["total_snr"]
        time = self.params["total_exptime"]
        lineF = self.params['line_flux']
        
        line_width  = FWHM  # initial value, prevents crash when using magnitudes (i.e. no line width)

        # if the number of exposures is greater than 1, assume two dither positions
        if (nExp > 1):
            dither = 2.0
        else: 
            dither = 1.0

        # the location of the code and the data spectra
        sky_path = get_data_file("etc.Paranal_sky_VIS")
 
        # MOSIFRE Linearity Limits
        #          2.15 e/ADU gain
        #          1% non linearity 26K ADU= 55900 electrons
        #          5% non linearity 37K ADUs = 79550 e-
        #          saturation 43K ADUs = 92450 e-
        sat_limit = 92450       #to be revised

        # 1. Throughput: 
        # 1.1 Mirror coating
        # 0) Metals for telescope optics (and possibly other mirrors)
        # Al from National Bureau of Standards, certainly optimistic
        #lambda[nm], transmission
        Al_reflectivity = np.loadtxt(get_data_file("etc.coating_throughput", "Al_reflectance_NBS.txt"), dtype=np.float32)
        Al_reflectivity_Wave = (Al_reflectivity[:,0] * u.nm).to(u.um)
        Al_reflectivity_Flux = Al_reflectivity[:,1]

        if band == "Low Red":
            SAMOS_throughput_Wave = self.samos_lowred_wave
            SAMOS_throughput_Flux = self.samos_lowred_flux     
        elif band == "Low Blue":
            SAMOS_throughput_Wave = self.samos_lowblue_wave
            SAMOS_throughput_Flux = self.samos_lowblue_flux     
        elif band == "High Red":
            SAMOS_throughput_Wave = self.samos_highred_wave
            SAMOS_throughput_Flux = self.samos_highred_flux     
        elif band == "High Blue":
            SAMOS_throughput_Wave = self.samos_highred_wave
            SAMOS_throughput_Flux = self.samos_highred_flux     

        filt_wave = SAMOS_throughput_Wave.to(u.um)
        filt = SAMOS_throughput_Flux 

        # if the magnitude is entered in Vega, change it to AB.
        # conversions for J,H,Ks from Blanton et al 2005
        # K from ccs
        # Y from CFHT WIRCam
        if ( (self.params["flux_mode"] == 'magnitude') and (self.params["spec_mag_units"] == "Vega")):                                                                            
            if Vega_band == 'U': 
                mag=mag+0.79
            elif Vega_band == 'B':
                mag=mag-0.09 
            elif Vega_band == 'V':
                mag=mag+0.02 
            elif Vega_band == 'R':
                mag=mag+0.21 
            elif Vega_band == 'I':
                mag=mag+0.45
            elif Vega_band== 'Y': 
                mag=mag+0.66
            elif Vega_band == 'J':
                mag=mag+0.91 
            elif Vega_band == 'H':
                mag=mag+1.39 
            elif Vega_band == 'K':
                mag=mag+1.95 
            elif Vega_band == 'Ks':
                mag=mag+1.85

        # CONSTANTS
        # the speed of light in cm/s
        c_kms = c.c.to(u.km/u.s)
        logc = np.log10(c.c.to(u.cm/u.s).value)

        # planck's constant in erg*s
        logh = np.log10(c.h.to(u.erg * u.s).value)

        # in log(erg cm)
        loghc = logc + logh
    
        f_nu_AB = 48.59

        # SOAR and SAMOS CONSTANTS
        #area of the telescope in cm^2
        AT = ((400 * u.cm / 2.)**2 * np.pi)

        #slit width used in arcsec to measure R_theta
        # SAMOS DMD scale is 0.1667". Nominal slit width is 2 mirrors
        slit_W = 0.1667 * 2 * u.arcsec

        #spatial pixel scale in arcseconds/pixel
        # spatial pixel scale [arcsec/px] - Sample 2 mirrors with 2.25 CCD pixels
        pix_scale = 0.1875375 * u.arcsec / u.pix

        #dispersion pixel size
        pix_disp = 0.24 * u.um / u.pix

        #Number of pixels in dispersion direction on the detector
        tot_Npix = 4096 * u.pix

        #Detector readnoise in electrons/pix CDS (correlated double sampling)
        det_RN = 5. * u.electron / u.pix  # SAMI, TBC

        #number of elements
        Nelement = 1  # superseeded by SAMOS throughput files.
    
        #number of SAM mirrors, silver coated
        N_SAM_mirrors = 3
    
        #number of windows
        Nwindow = 1.  # superseeded by SAMOS throughput files.

        # SLIT LOSSES
        if self.params["glao"] == "SAM":
            # ;appropriate from SAM, e-mail from Tokovinin; set =3 for VLT/FORS1 and =100 for a Gaussian profile
            beta = 3.
        else:
            beta = 10. 

        # SKY CONSTANTS
        # read in the atmospheric transparency from Gemini Observatory: 
        # Lord, S. D., 1992, NASA Technical Memorandum 103957
        # default is 1.6mm water vapor column
        # airmass=1
    
        #1.3 Atmospheric Transmission
        sky_transmission = np.loadtxt(sky_path / "GenericTransmission_VIS.txt", skiprows=1)
        sky_transmission_Wave = (sky_transmission[:,0].astype(float) * u.angstrom).to(u.um)
        sky_transmission_Flux = sky_transmission[:,1].astype(float)

        sky_spectrum = np.loadtxt(sky_path / "UVES_Fluxed_SkyALL.txt") #lambda [A]; [erg/sec/cm2/A/arcsec2]
        sky_spectrum_Wave = (sky_spectrum[:,0] * u.angstrom).to(u.um)
        sky_spectrum_Flux = sky_spectrum[:,1] * u.erg / u.s / (u.cm * u.cm) / u.angstrom / (u.arcsec * u.arcsec)
        sky_spectrum_Flux *= sky_spectrum_Wave.to(u.cm) / (c.c.to(u.cm/u.s) * c.h.to(u.erg*u.s))
        sky_spectrum_Flux = sky_spectrum_Flux.to(1 / u.s / (u.cm * u.cm) / u.angstrom / (u.arcsec * u.arcsec))

        # MOSIFRE Throughput
        #     ;elem_AR = elment AR per surface
        #     ;ref_mir = mirror reflectance
        #     ;win_AR = window AR per surface
        #     ;grat_eff: grating effciency
        #     ;fil_tran: filter transmission
        #     ;qe: quantum efficiency
        #     ;disp: dispersion in angstroms/pixel
        #     ;cent: central wavelength in micron
        #     ;background in magnitudes per arcsecond^2
        #     ;f_not: log of magnitude zero point in erg/s/cm^2/micron
        #     ;dark current in electrons per second
        #     ;rt: R-theta product: multiply by slit width to get resolution
        #     ;SMRef: SOAR Mirror reflectance (placeholder only, as it is included in Silver throughput)
        HighRedstat = {
#             "elem_AR" :0.99, 
#             "ref_mir" :0.98, 
#             "win_AR": 0.988, 
#             "grat_eff": 0.72,
#             "fil_trans": 0.93, 
#             "qe": 0.88, 
#             "disp": 2.170, 
#             "lambda": 2.2, 
#             "background": 16, 
#             "f_not": np.log10(3.8)-7, 
            "dark": 0.005 * u.electron / (u.s * u.pix),
#             "rt": 3620.0*slit_width, 
#             "SMRef":1.00 
            "disp": (7000.-5988.) * u.angstrom / (2876.0 * u.pix),  # dispersion [angstrom/px]
            "lambda": 0.6472 * u.um,   # central wavelength [microns]
            "rt" : 8111. * 0.1667 * 2 * u.arcsec  # instrument["slit_W"] 
            }
    
        LowRedstat={
#             "elem_AR": 0.992, 
#             "ref_mir": 0.985, 
#             "win_AR": 0.985,  
#             "grat_efF": 0.65, 
#             "fil_trans": 0.95, 
#             "qe": 0.88, 
#             "disp": 1.629, 
#             "lambda": 1.65, 
#             "background": 16.6, 
#             "f_not": np.log10(1.08)-6, 
            "dark": 0.005 * u.electron / (u.s * u.pix),
#             "rt": 3660.0*slit_width, 
#             "SMRef": 1.00
            "disp":  (6000.-4000.) * u.angstrom / (2875.0 * u.pix),  # dispersion [angstrom/px]
            "lambda":  0.7712 * u.um,   # central wavelength [microns]
            "rt" : 2791. * 0.1667 * 2* u.arcsec  # instrument["slit_W"] 
            }
    
        HighBluestat={ 
#             "elem_AR": 0.985, 
#             "ref_mir": 0.98, 
#             "win_AR": 0.985, 
#             "grat_eff": 0.8,
#             "fil_trans": 0.9, 
#             "qe": 0.8, 
#             "disp": 1.303, 
#             "lambda": 1.25, 
#             "background": 16.8, 
#             "f_not": np.log10(2.90)-6, 
            "dark": 0.005 * u.electron / (u.s * u.pix),
#             "rt":3310.0*slit_width, 
#             "SMRef": 1.00
            "disp":(5139.-4504.) * u.angstrom / (2876.0 * u.pix),  # dispersion [angstrom/px]
            "lambda":0.4803 * u.um,  # central wavelength [microns]
            "rt": 9601. * 0.1667 * 2* u.arcsec  # instrument["slit_W"] 
            }
    
        LowBluestat={
#             "elem_AR": 0.985, 
#             "ref_mir": 0.98, 
#             "win_AR": 0.985, 
#             "grat_eff": 0.8,
#             "fil_trans": 0.9, 
#             "qe": 0.8, 
#             "disp": 1.086, 
#             "lambda": 1.05, 
#             "background": 17.3, 
#             "f_not": np.log10(7.45)-6, 
            "dark": 0.005 * u.electron / (u.s * u.pix),
#             "rt": 3380.0*slit_width, 
#             "SMRef": 1.00 
            "disp": (9500.-6000.) * u.angstrom / (2874.0 * u.pix),  # dispersion [angstrom/px]
            "lambda": 0.4965 * u.um,  # central wavelength [microns]
            "rt": 3137. * 0.1667 * 2* u.arcsec  # instrument["slit_W"] 
            }

        if (band == 'Low Blue'):
            stat=LowBluestat
        if (band == 'High Blue'):
            stat=HighBluestat 
        if (band == 'Low Red'): 
            stat=LowRedstat
        if (band == 'High Red'):
            stat=HighRedstat

        # figure out the THROUGHPUT
        tp_wave = SAMOS_throughput_Wave 
        throughput = SAMOS_throughput_Flux 

        # number of Keck Mirrors (Primary and Secondary)
        N_SOAR_mirrors = 3

        # the total throughput is the instrument throughput times the reflectance of the 
        # keck primary and secondary
        #    throughput=throughput*stat["SMRef"]**(NKmir)
        th_SOAR_Wave = Al_reflectivity_Wave 
        th_SOAR_Flux = Al_reflectivity_Flux**(N_SOAR_mirrors)

        # real FWHM resolution
        R = stat["rt"]/slit_width

        # slit width in pixels along the dispersion direction
        swp = slit_width / pix_disp

        # spectral coverage in micron)
        cov = tot_Npix * (stat["disp"].to(u.um / u.pix))

        # Using a specific line flux
        if self.params["flux_mode"] == 'flux':
            # figure out the relavant wavelength range
            center = lineWl.to(u.um) * (1 + z_line)

            # resolution at the central wavelength in micron
            res = center / R

            # the width of the spectral line before going through the spectrograph
            real_width = center * FWHM / c.c.to(u.angstrom/u.s)

            # the line width in micron that would be observed
            line_width = np.sqrt(real_width**2 + res**2)
        else:
            # we are calculating for a broad band flux: 
            center = stat["lambda"].to(u.um)

            # resolution at the central wavelength in micron
            res = center / R

        # convolve the filter with bandpass resolution
        bandpass_degrade = self.degrade_resolution(wavelengths=filt_wave, flux=filt, center_wave=stat["lambda"], 
                                                   spec_res=R, disp=stat["disp"], px_tot=tot_Npix)

        # normalize the spectrum to find the relevant portions
        fltSpecObsNorm = np.array(bandpass_degrade["flux"]) / max(np.array(bandpass_degrade["flux"]))
        band_index = np.where( (bandpass_degrade["lam"] >= filt_wave[0]) & (bandpass_degrade["lam"] <= filt_wave[-1]) )
        fltSpecObs = np.array(bandpass_degrade["flux"][band_index])
        
        # a tighter selection of the indexes with high throuhgput for the S/N
        filt_index = np.where(fltSpecObs > 0.05)
        wave_grid = bandpass_degrade["lam"][band_index]

        th_SOAR_degrade = self.degrade_resolution(wavelengths=th_SOAR_Wave, flux=th_SOAR_Flux, center_wave=stat["lambda"],
                                                  spec_res=R, disp=stat["disp"], px_tot=tot_Npix)
        th_SOAR_degrade_Flux = th_SOAR_degrade["flux"][band_index]

        # convolve the atm_Transmission spectrum with the resolution
        atmtrans_degrade = self.degrade_resolution(wavelengths=sky_transmission_Wave, flux=sky_transmission_Flux, 
                                                   center_wave=stat["lambda"],  spec_res=R, disp=stat["disp"], 
                                                   px_tot=tot_Npix)
        tranSpecObs = np.array(atmtrans_degrade["flux"][band_index])

        # convolve the throughput spectrum with the resolution
        throughput_degrade = self.degrade_resolution(wavelengths=tp_wave, flux=throughput, center_wave=stat["lambda"],  
                                                     spec_res=R, disp=stat["disp"], px_tot=tot_Npix)
        tpSpecObs = np.array(throughput_degrade["flux"][band_index])
        tpSpecObs = np.where(tpSpecObs < 0, 0, tpSpecObs)

        SAMI_throughput_degrade = self.degrade_resolution(wavelengths=self.sami_ccd_wave, flux=self.sami_ccd_flux,
                                                          center_wave=stat["lambda"], spec_res=R, disp=stat["disp"], 
                                                          px_tot=tot_Npix)
        SAMISpecObs = np.array(SAMI_throughput_degrade["flux"][band_index])

        # convolve the background spectrum with the resolution
        # background in phot/sec/arcsec^2/nm/m^2
        bg = sky_spectrum_Flux.to(1 / u.s / (u.arcsec*u.arcsec) / u.nm / (u.m * u.m))
        background_degrade = self.degrade_resolution(wavelengths=sky_spectrum_Wave, flux=sky_spectrum_Flux,
                                                     center_wave=stat["lambda"], spec_res=R, disp=stat["disp"], 
                                                     px_tot=tot_Npix)
        #for now - sent the filt_index to be the NONzero_index
        raw_bkSpecObs = background_degrade["flux"][band_index]  #2251
        raw_bkSpecObs = np.where(raw_bkSpecObs < 0, 0, raw_bkSpecObs) * (1 / u.s / (u.arcsec*u.arcsec) / u.nm / (u.m * u.m))

        # Create "SAM throughput" by extending the constant throughput value to all wavelengths
        sam_throughput = np.full(len(band_index), self.sam_throughput)

        # Final THROGHPUT    
        # Atmosphere x SOAR Telescope x SAM-AO x SAMOS x SAMI    
        tpSpecObs = tranSpecObs * th_SOAR_degrade_Flux * sam_throughput * tpSpecObs * SAMISpecObs

        # Using a specific line flux
        if self.params["flux_mode"] == 'flux':
            # the location inside the FWHM of the line
            line_index = np.where(abs(wave_grid - center) < 0.5 * line_width)
            # the area used to calcclate the S/N
            sn_index = line_index

            # now send the background spectrum through the telescope by multiplying the 
            # throughput, the slit_width, the angular extent (theta), the area of the
            # telescope, and the pixel scale in nm. This gives phot/sec/pixel
            bkSpecObs = raw_bkSpecObs * tpSpecObs * slit_width * theta * (AT * 10.**(-4)) * (stat["disp"]/10.0)
            bkSpecObs = bkSpecObs.value

            # determine the average background within the FWHM of the line in photons per 
            # second per arcsec^2 per nm per m^2
            mkBkgd = np.mean(sky_spectrum_Flux[np.where(abs(sky_spectrum_Wave - center) <= 0.5 * line_width)])

            # What does this correspond to in AB mags/arcsec^2
            # - go to erg/s/cm^2/Hz
            # - 10^-4 for m^2 to cm^2
            # - 10^3 for micron to nm
            # - lam^2/c to covert from d(lam) to d(nu) (per Hz instead of per nm)
            # - hc/lam to convert photons to ergs
            # ***** CAN THIS BE DONE WITH UNITS?
            mag_back = -2.5 * (np.log10(mkBkgd * center) -4 + 3 + logh) - f_nu_AB

            # the signal in electrons per second that will hit the telsecope as it hits 
            # the atmosphere (ie need to multiply by the throughput and the atmospheric 
            # transparency
            signalATM = lineF * 10**(-17 - loghc - 4) * center * AT

            # the width of the line in sigma - not FWHM in micron
            sigma = line_width / (2 * np.sqrt(2 * np.log(2)))

            # a spectrum version of the signal
            # hot per second per pixel (without atm or telescope) ie total(signal_spec/signal) 
            # with equal resolution of wave_grid / stat.disp in micron
            signal_spec = signalATM * (1 / (np.sqrt(2 * np.pi) * sigma))
            signal_spec *= np.exp(-0.5 * (wave_grid - center)**2 / sigma**2) * stat["disp"]/10.**4

            # the spectrum of the signal as detected
            sig_rateSpecObs = (signal_spec * tpSpecObs * tranSpecObs).value

            # SLIT LOSSES
            Nslit_X = round(self.params["slit"] / 0.1667*u.arcsec)
            Nslit_Y = round(theta * 2 / 0.1667*u.arcsec)
            slit_loss = self.slit_loss(theta, beta, Nslit_X, Nslit_Y)            
            sig_rateSpecObs = sig_rateSpecObs * slit_loss

            # the number of pixels in the spectral direction
            nPixSpec = (line_width * 10000.0) / stat["disp"]

            # the spatial pixel scale
            nPixSpatial = theta / pix_scale

            # The number of pixels per FWHM observed
            Npix= nPixSpec * nPixSpatial
        else:
            # we are calculating for a broad band flux
            # the area used to calculate the S/N
            sn_index = filt_index
            bg_spec = raw_bkSpecObs.to(1/(u.um * u.s * (u.arcsec * u.arcsec) * (u.m * u.m)))
            mag_back = -2.5 * (np.log10(np.mean(bg_spec.value) * center.value) - 4 + 3 + logh) - f_nu_AB

            # now send the background spectrum through the telescope by multiplying the 
            # throughput, the slit_width, the angular extent, the area of the telescope, 
            # and the pixel scale in nm. This gives phot/sec/pixel
            bkSpecObs = raw_bkSpecObs * tpSpecObs * slit_width * theta * (AT.to(u.m * u.m)) * (stat["disp"].to(u.nm / u.pix))

            if self.params["spec_type"] == "User spectrum": 
                # using the user input spectrum
                self.read_spectrum()

                #Redshift is applied only to the wavelenghts
                self.user_Wave = self.user_Wave*(1 + z_spec) * u.Unit(params["spec_waveunit"])

                # does the user spectrum cover the full band pass and are the wavelengths in micron?
                if ((min(self.user_Wave) > min(filt_wave)) or (max(self.user_Wave) < max(filt_wave))):
                    warning = "The read-in spectrum from {} does not span the full wavelength "
                    warning += "coverage of the {} band, or is not in the proper format. The "
                    warning += "correct format is erg/s/cm2 in two-column format with a space "
                    warning += "or comma as the delimiter. Also please check that you have "
                    warning += "chosen the correct wavelength units."
                    ttk.messagebox.showarning(title='Check spectrum', message=warning.format(self.source_filename, band))

                # convolve with the resolution of mosfire
                userSig_degrade = self.degrade_resolution(wavelengths=self.user_Wave, flux=self.user_Flux, 
                                                          center_wave=stat["lambda"], spec_res=R, disp=stat["disp"], 
                                                          px_tot=tot_Npix)
                userSig = np.array(userSig_degrade["flux"][band_index])

                # multiply by the normalized filter transmission        
                filt_shape = fltSpecObs / max(fltSpecObs)
                userSig = userSig * filt_shape

                if self.params["spec_mag_units"] == 'AB':
                    df = self.read_ABfilters()
                    wl_um = df[:,0] / 10000.0   #in micron
                    tp   = df[:,1]
                    good_index  = np.where(tp > 0.05)
                    AB_filter_degrade = self.degrade_resolution(wavelengths=wl_um, flux=tp, 
                                                                center_wave=np.mean(wl_um), spec_res=R, 
                                                                disp=stat["disp"], px_tot=tot_Npix)
                    AB_filter_degrade = np.array(AB_filter_degrade["flux"])
                    Source_filter_degrade = self.degrade_resolution(wavelengths=wl_um, flux=self.user_Flux,
                                                                    center_wave=np.mean(wl_um), spec_res=R, 
                                                                    disp=stat["disp"], px_tot=tot_Npix)
                    Source_filter_degrade = np.array(Source_filter_degrade["flux"])
                    Source_filter_degrade = Source_filter_degrade * AB_filter_degrade
                    # make the total match the broad band magnitude
                    scale = 10.0**(-0.4 * (mag + f_nu_AB)) / np.mean(Source_filter_degrade)
                else:
                    # multiply by the normalized filter transmission        
                    filt_shape = fltSpecObs / max(fltSpecObs)
                    userSig = userSig * filt_shape
                    # make the total match the broad band magnitude
                    scale = 10.0**(-0.4 * (mag + f_nu_AB)) / np.mean(userSig)

                # raw fv spec
                raw_fv_sig_spec = userSig * scale

                # convert to flux hitting the primary in flux hitting the primary in
                # - phot/sec/micron (if the earth had no atmosphere)
                # - phot/sec/micron = fnu * AT / lam / h
                signal_spec = raw_fv_sig_spec * 10.**(-1 * logh) * AT / wave_grid
            else:
                # using a flat F_nu spec (DEFAULT)
                # fv=10^((-2/5)*MagAB-48.59) (erg/s/cm^2/Hz)
                # Convert to flam: flam=fv*c/lam^2 (erg/s/cm^2/micron)
                # covert to photons: phot/sec/micron = fnu * AT / lam / h
                # flux hitting the primary in phot/sec/micron (if the earth had no atmosphere)
                flux_value = 10.**(-0.4 * (mag.value + f_nu_AB))*(u.erg / u.s / (u.cm * u.cm) / u.Hz)
                signal_spec = ((flux_value * AT / (c.h * wave_grid))).to(1 / u.s / u.um)

            # multiply by the atmospheric transparency
            signal_spec = signal_spec * tranSpecObs

            # now put it through the throughput of the telescope (phot/sec/micron)
            sig_rateSpecObs = signal_spec * tpSpecObs

            # SLIT LOSSES
            Nslit_X = round((self.params["slit"] / (0.1667*(u.arcsec / u.pix))).value) * u.pix
            nsy = theta * 2 / (0.1667*(u.arcsec / u.pix))
            Nslit_Y = round((theta * 2 / (0.1667*(u.arcsec / u.pix))).value) * u.pix
            slit_loss = self.slit_loss(theta, beta, Nslit_X, Nslit_Y)
            sig_rateSpecObs = sig_rateSpecObs * slit_loss

            # now for phot/sec/pix multiply by micron/pix
            sig_rateSpecObs = sig_rateSpecObs * (stat["disp"] / 10000.0)

            # number of pixels per resolution element in the spectral direction
            nPixSpec = (res * 10000.0) /stat["disp"]

            # the spatial pixel scale
            nPixSpatial = theta / pix_scale

            # The number of pixels per FWHM observed
            Npix = nPixSpec * nPixSpatial     

        if self.params["calc_type"] == 'calc_exptime':
            # Determine EXP TIME ...
            # differentiate between total exposure time and amount of time of individual exposures
            # if calulating with a line flux, assume S/N over the line. Otherwise, S/N per spectral pixel
            if self.params["flux_mode"] == 'flux':
                qa = -nPixSpec * sig_rateSpecObs**2 / SN**2 
            else:
                qa = -sig_rateSpecObs**2 / SN**2
            qb = dither * bkSpecObs + dither * stat["dark"] * nPixSpatial.value / u.electron + sig_rateSpecObs
            qc = dither * det_RN.value**2 / Nreads * nPixSpatial.value * nExp
            timeSpec = (((-qb - np.sqrt(qb**2 - 4 * qa * qc)) / (2 * qa)) / u.pix).decompose()
            time = np.median(timeSpec[sn_index])
        else:
            # Determine SNR
            pass


        # Determine the signal to noise
        # - noise contributions
        # - poisson of background
        # - poisson of dark current
        # - poisson of the signal
        # - read noise

        # the noise per slit length in the spatial direction and per pixel in the spectral direction
        # the noise spectrum:
        # - Poisson of the dark
        # - current, signal, and background + the read noise"
        signal_rate = (sig_rateSpecObs * u.pix).decompose()
        dark_rate = ((bkSpecObs + stat["dark"] / u.electron * nPixSpatial.value) * u.pix).decompose()
        readnoise_per_exp = ((det_RN * u.pix / u.electron)**2 / Nreads * nPixSpatial.value * nExp).decompose()
        noiseSpecObs = np.sqrt(signal_rate * time + dither * (dark_rate * time + readnoise_per_exp))
        signalSpecObs =  sig_rateSpecObs * time
        snSpecObs = signalSpecObs / noiseSpecObs
        stn = np.mean(np.sqrt(nPixSpec) * snSpecObs[sn_index])

        # the electron per pixel spectrum
        eppSpec = noiseSpecObs**2 / nPixSpatial

        # the mean instrument+telescope throughput in the same band pass
        tp = np.mean(tpSpecObs[sn_index])

        # maximum electron per pixel
        max_epp = np.max(eppSpec[sn_index]) / nExp
        max_epp_scalar = int(np.round(max_epp.value, 0))

        # if calulating a line flux, S/N per FWHM ie S/N in the line
        if self.params["flux_mode"] == 'flux':

            # over the line (per FWHM)
            stn = np.mean(np.sqrt(nPixSpec) * snSpecObs[sn_index])

            # signal in e/FWHM
            signal = np.mean(sig_rateSpecObs[sn_index]) * nPixSpec * time

            # sky background in e/sec/FWHM
            background = np.mean(bkSpecObs[sn_index]) * nPixSpec * time

            # Read noise for multiple reads, electrons per FWHM
            RN = det_RN / np.sqrt(Nreads) * np.sqrt(Npix) * np.sqrt(nExp)

            # noise per FWHM
            noise = np.mean(noiseSpecObs[sn_index]) * np.sqrt(nPixSpec)

            # e-
            dark = stat["dark"] * Npix * time
        else:
            # we are computing S/N per pixel for a continuum source

            # per spectral pixel
            stn = np.median(snSpecObs[sn_index])

            # signal in e/(spectral pixel)
            signal = np.median(sig_rateSpecObs[sn_index]) * time

            # sky background in e/(spectral pixel)
            background = np.median(bkSpecObs[sn_index]) * time

            # Read noise for multiple reads, electrons per spectral pixel
            RN = det_RN / np.sqrt(Nreads) * np.sqrt(nPixSpatial) * np.sqrt(nExp)

            # noise per spectral pixel
            noise = np.median(noiseSpecObs[sn_index])

            # e- per spectral pixel
            dark = stat["dark"] * nPixSpatial * time

        # display the results
        summary_struct = {}
        summary_struct["quant"] = ['Wavelength', 'Resolution','Dispersion', 'Throughput', 'Signal', 'Sky Background', 
                                   'Sky brightness', 'Dark Current', 'Read Noise', 'Total Noise','S/N', 
                                   'Total Exposure Time', 'Max e- per pixel']

        if (self.params["flux_mode"] == "flux") and (lineWl > 0):
            summary_struct["unit"] = ['micron','FWHM in angstrom', 'angstrom/pixel', '',  'electrons per FWHM', 
                                      'electrons per FWHM', 'AB mag per sq. arcsec', 'electrons per FWHM', 
                                      'electrons per FWHM', 'electrons per FWHM', 'per observed FWHM', 
                                      'seconds', 'electrons per pixel per exp']                                     
        else:
            summary_struct["unit"] = ['micron','angstrom', 'angstrom/pixel', '',  'electrons per spectral pixel',
                                      'electrons per spectral pixel', 'AB mag per sq. arcsec', 
                                      'electrons per spectral pixel', 'electrons per spectral pixel', 
                                      'electrons per spectral pixel', 'per spectral pixel', 'seconds', 
                                      'electrons per pixel']
        if max_epp_scalar >= 1e10:
            max_epp_string = "> 1e10"
        else:
            max_epp_string = max_epp_scalar
            
        #checking if the signal is saturating the detector
        if max_epp_scalar > sat_limit:
            ttk.messagebox.showerror(title="Saturated Exposure", message="Detector saturated!\n\nTry to increase Nexp.")

        summary_struct["value"] = [np.round(center,4), np.round(res * 1e4,1), np.round(stat['disp'],2),
                                   np.round(tp,2), np.round(signal,2), np.round(background,2),
                                   np.round(mag_back,2), np.round(dark,2), np.round(RN,2),
                                   np.round(noise,2), np.round(stn,2), np.round(time,2), max_epp_string]

        ## Actual output containing the spectrum (for graphing purposes) --------------
        self.spec_struct = {}
        self.spec_struct["wave"] = wave_grid
        self.spec_struct["center"] = center
        self.spec_struct["plot_index"] = sn_index
        self.spec_struct["filt_index"] = filt_index[0]
        self.spec_struct["tp"] = tpSpecObs
        self.spec_struct["filt"] = fltSpecObs
        self.spec_struct["tran"] = tranSpecObs
        self.spec_struct["bk"] = bkSpecObs * time
        self.spec_struct["signal"] = signalSpecObs
        self.spec_struct["noise"] = noiseSpecObs
        self.spec_struct["sn"] = snSpecObs
        self.spec_struct["line_flux"] = self.params["line_flux"]
        self.spec_struct["time"] = time
        self.spec_struct["line_width"] = line_width

        if self.params["calc_type"] ==  'calc_exptime':
            result_str = "Calculation for a signal to noise ratio of {} ".format(np.round(stn, 3))
        elif self.params["calc_type"] ==  'calc_snr':
            result_str = "Calculation for a {} s total integration time ".format(self.params["total_exptime"])
        result_str += "through a {} arcsecond slit in {} band".format(self.params["slit"], self.params["bandpass"])

        return summary_struct, result_str
