"""
SAMOS ETC tk Frame Class
"""
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pathlib import Path
import yaml

from astropy import units as u

import tkinter as tk
import ttkbootstrap as ttk
from samos.etc import ETC
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class ETCPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS ETC", **kwargs)
        
        left_frame = ttk.Frame(self.main_frame)
        left_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        right_frame = ttk.Frame(self.main_frame)
        right_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        # Top Left Frame:
        frame = ttk.LabelFrame(left_frame, text="ETC Options", relief=tk.RIDGE)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        # Grating
        ttk.Label(frame, text="Grating:", anchor="w").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        bandpass_options = ["Low Red", "Low Blue", "High Red", "High Blue"]
        self.bandpass = tk.StringVar(self, bandpass_options[2])
        ttk.OptionMenu(frame, self.bandpass, *bandpass_options).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Slit Width
        ttk.Label(frame, text="Slit Width:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        slit_options = [0.17, 0.33, 0.5, 0.67, 0.88, 1.00, 1.17, 1.33, 1.5, 1.67, 1.88, 2.00]
        self.slit_width = tk.DoubleVar(self, slit_options[2])
        ttk.OptionMenu(frame, self.slit_width,  *slit_options).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="arcsec").grid(row=2, column=2, sticky=TK_STICKY_ALL)
        # Number of Exposures
        ttk.Label(frame, text="# of Exposures").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.n_exp = tk.IntVar(self, 2)
        tk.Entry(frame, textvariable=self.n_exp).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        # Seeing
        ttk.Label(frame, text="Seeing FWHM:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.seeing_fwhm = tk.DoubleVar(self, 0.4)
        tk.Entry(frame, textvariable=self.seeing_fwhm).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        ttk.Label(frame, text="arcsec").grid(row=4, column=2, sticky=TK_STICKY_ALL)
        # Use Adaptive Optics?
        ttk.Label(frame, text="Use GLAO?").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.ao_value = tk.StringVar(self, "SAM")
        b = tk.Radiobutton(frame, text="SAM", value="SAM", variable=self.ao_value)
        b.grid(row=6, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Natural Seeing", value="Natural Seeing", variable=self.ao_value)
        b.grid(row=6, column=2, sticky=TK_STICKY_ALL)
        # Flux or Magnitude
        ttk.Label(frame, text="Flux Mode:").grid(row=7, column=0, sticky=TK_STICKY_ALL)
        self.flux_mode = tk.StringVar(self, "magnitude")
        b = tk.Radiobutton(frame, text="Line Flux", value="flux", variable=self.flux_mode, command=self.set_enabled)
        b.grid(row=7, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Magnitude", value="magnitude", variable=self.flux_mode, command=self.set_enabled)
        b.grid(row=7, column=2, sticky=TK_STICKY_ALL)
        
        # Flux Configuration Frame
        frame = ttk.LabelFrame(left_frame, text="Emission Line Source")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Line Flux
        ttk.Label(frame, text="Line Flux:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.line_flux = tk.DoubleVar(self, 9.0)
        w = tk.Entry(frame, textvariable=self.line_flux)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "flux")]
        ttk.Label(frame, text="(1E-17 erg/Hz/s/cm\u00b2)").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # Central Wavelength
        ttk.Label(frame, text="Central Wavelength:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.line_cenwave = tk.IntVar(self, 6563)
        w = tk.Entry(frame, textvariable=self.line_cenwave)
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "flux")]
        self.line_cenwave_units = tk.StringVar(self, "angstroms")
        b = tk.Radiobutton(frame, text="(angstroms)", value="angstroms", variable=self.line_cenwave_units)
        b.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "flux")]
        b = tk.Radiobutton(frame, text="(microns)", value="microns", variable=self.line_cenwave_units)
        b.grid(row=1, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "flux")]
        # Redshift
        ttk.Label(frame, text="Redshift:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.line_redshift = tk.DoubleVar(self, 0.0)
        w = tk.Entry(frame, textvariable=self.line_redshift)
        w.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "flux")]
        ttk.Label(frame, text="Redshifted Wavelength:").grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.line_redshifted_wl = tk.DoubleVar(self, self.line_cenwave.get()*self.line_redshift.get())
        tk.Label(frame, textvariable=self.line_redshifted_wl).grid(row=2, column=3, sticky=TK_STICKY_ALL)
        # Source FWHM
        ttk.Label(frame, text="Source FWHM:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.line_fwhm = tk.DoubleVar(self, 30.)
        w = tk.Entry(frame, textvariable=self.line_fwhm)
        w.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "flux")]
        ttk.Label(frame, text="(km/s)").grid(row=3, column=2, sticky=TK_STICKY_ALL)

        # Magnitude Configuration Frame
        frame = ttk.LabelFrame(left_frame, text="Spectrum Source")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        # Magnitude
        ttk.Label(frame, text="Magnitude:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.spec_mag = tk.DoubleVar(self, 18.6)
        w = tk.Entry(frame, textvariable=self.spec_mag)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "magnitude")]
        self.spec_mag_units = tk.StringVar(self, "AB")
        b = tk.Radiobutton(frame, text="AB", value="AB", variable=self.spec_mag_units, command=self.config_mag_type)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "magnitude")]
        b = tk.Radiobutton(frame, text="Vega", value="Vega", variable=self.spec_mag_units, command=self.config_mag_type)
        b.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "magnitude")]
        self.ab_options = ["u_SDSS", "g_SDSS", "r_SDSS", "i_SDSS", "z_SDSS", "Y_VISTA", "J_VISTA", "H_VISTA", "K_VISTA"]
        self.vega_options = ["U", "B", "V", "R", "I", "Y", "J", "H", "Ks", "K"]
        self.spec_mag_band = tk.StringVar(self, self.ab_options[2])
        self.mag_bands = ttk.OptionMenu(frame, self.spec_mag_band, *self.ab_options)
        self.mag_bands.grid(row=0, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[self.mag_bands] = [("tkvar", self.flux_mode, "magnitude")]
        # Spectrum
        ttk.Label(frame, text="Spectrum:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.spec_options = ["Flat F_nu", "User Spectrum"]
        self.spec_type = tk.StringVar(self, self.spec_options[0])
        self.spec_dropdown = ttk.OptionMenu(frame, self.spec_type, *self.spec_options, command=self.load_spectrum)
        self.spec_dropdown.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.spec_dropdown] = [("tkvar", self.flux_mode, "magnitude")]
        # User Spectrum
        user_spec_frame = ttk.LabelFrame(frame, text="User Spectrum:")
        ttk.Label(user_spec_frame, text="File:").grid(row=0, column=0, rowspan=4, columnspan=5, sticky=TK_STICKY_ALL)
        self.spec_path = None
        self.spec_file = tk.StringVar(self, "")
        w = tk.Entry(user_spec_frame, textvariable=self.spec_file)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "magnitude")]
        ttk.Label(user_spec_frame, text="Flux Type:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.spec_fluxunit = tk.StringVar(self, "F_lam")
        b = tk.Radiobutton(user_spec_frame, text="F_lam", value="F_lam", variable=self.spec_fluxunit)
        b.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "magnitude")]
        b = tk.Radiobutton(user_spec_frame, text="F_nu", value="F_nu", variable=self.spec_fluxunit)
        b.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "magnitude")]
        ttk.Label(user_spec_frame, text="Wavelength Units:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.spec_waveunit = tk.StringVar(self, "angstroms")
        b = tk.Radiobutton(user_spec_frame, text="Angstroms", value="angstroms", variable=self.spec_waveunit)
        b.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "magnitude")]
        b = tk.Radiobutton(user_spec_frame, text="Microns", value="microns", variable=self.spec_waveunit)
        b.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("tkvar", self.flux_mode, "magnitude")]
        ttk.Label(user_spec_frame, text="Redshift:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.spec_redshift = tk.DoubleVar(self, 0.0)
        w = tk.Entry(user_spec_frame, textvariable=self.spec_redshift)
        w.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.flux_mode, "magnitude")]

        # Calculation Type
        frame = ttk.LabelFrame(left_frame, text="Calculation Options")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Calculation Type
        ttk.Label(frame, text="Calculation Type:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.calculation_type = tk.StringVar(self, "calc_exptime")
        b = tk.Radiobutton(frame, text="Calculate Time from SNR", value="calc_exptime", variable=self.calculation_type, 
                           command=self.set_enabled)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Calculate SNR from Time", value="calc_snr", variable=self.calculation_type,
                           command=self.set_enabled)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        # Exptime
        subframe = ttk.Frame(frame)
        subframe.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(subframe, text="Exposure Time:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.calc_exptime = tk.DoubleVar(self, 1000.)
        w = tk.Entry(subframe, textvariable=self.calc_exptime)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.calculation_type, "calc_snr")]
        ttk.Label(subframe, text="(s)").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # SNR
        subframe = ttk.Frame(frame)
        subframe.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        ttk.Label(subframe, text="SNR:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.calc_snr = tk.DoubleVar(self, 10.)
        w = tk.Entry(subframe, textvariable=self.calc_snr)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.calculation_type, "calc_exptime")]

        # Custom airmass and water vapour
        frame = ttk.LabelFrame(left_frame, text="Optional Inputs")
        frame.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        # Airmass and Water Vapor
        ttk.Label(frame, text="Use custom values for:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.custom_airmass = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Airmass", variable=self.custom_airmass, onvalue=1, offvalue=0,
                            command=self.set_enabled)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.custom_water = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Water Vapour", variable=self.custom_water, onvalue=1, offvalue=0, 
                            command=self.set_enabled)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # Airmass
        subframe = ttk.Frame(frame)
        subframe.grid(row=1, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        ttk.Label(subframe, text="Airmass:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.airmass_options = [1.0, 1.5, 2.0]
        self.airmass = tk.DoubleVar(self, self.airmass_options[0])
        self.airmass_select = ttk.OptionMenu(subframe, self.airmass, *self.airmass_options)
        self.airmass_select.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.airmass_select] = [("tkvar", self.custom_airmass, 1)]
        # Water Vapour
        subframe = ttk.Frame(frame)
        subframe.grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        ttk.Label(subframe, text='Water Vapour:').grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.water_options = [1.0, 1.6, 3.0, 5.0]
        self.water = tk.DoubleVar(self, self.water_options[1])
        self.water_select = ttk.OptionMenu(subframe, self.water, *self.water_options)
        self.water_select.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.water_select] = [("tkvar", self.custom_water, 1)]

        # Calculate Frame
        frame = ttk.LabelFrame(left_frame, text="Run")
        frame.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        b = ttk.Button(frame, text="CALCULATE", command=self.run_calculation)
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # First right frame
        frame = ttk.LabelFrame(right_frame, text="Output")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        # Header text
        self.header_text = tk.StringVar(self, "")
        t = tk.Label(frame, textvariable=self.header_text)
        t.grid(row=0, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        # Frame to hold matplotlib canvas
        self.plot_frame = ttk.Frame(frame, width=490, height=245)
        self.plot_frame.grid(row=1, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.plot_frame.rowconfigure(0, minsize=500, weight=1)
        self.plot_frame.columnconfigure(0, minsize=250, weight=1)
        # Results View
        self.view = ttk.Treeview(frame)
        self.view.grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.view['columns']= ('Parameter', 'Value', 'Units')
        self.view.column("#0", width=0,  stretch=tk.NO)
        self.view.column("Parameter", anchor=tk.CENTER, width=150)
        self.view.column("Value", anchor=tk.CENTER, width=100)
        self.view.column("Units", anchor=tk.CENTER, width=235)
        self.view.heading("#0", text="", anchor=tk.CENTER)
        self.view.heading("Parameter", text="Parameter", anchor=tk.CENTER)
        self.view.heading("Value", text="Value", anchor=tk.CENTER)
        self.view.heading("Units", text="Units", anchor=tk.CENTER)
        # Choose Plot
        ttk.Label(frame, text="Choose Plot:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.plot_type = tk.StringVar(self, "plot_obs")
        b = tk.Radiobutton(frame, text="Plot Observation", value="plot_obs", variable=self.plot_type,
                           command=self.plot_obs)
        b.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Plot Signal to Noise", value="plot_snr", variable=self.plot_type,
                           command=self.plot_snr)
        b.grid(row=3, column=2, sticky=TK_STICKY_ALL)
        # Wavelength Range
        ttk.Label(frame, text="Wavelength Range:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.wl_type = tk.StringVar(self, "default")
        b = tk.Radiobutton(frame, text="Default", value="default", variable=self.wl_type, command=self.set_enabled)
        b.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="User-Selected", value="user", variable=self.wl_type, command=self.set_enabled)
        b.grid(row=4, column=2, sticky=TK_STICKY_ALL)
        # Chosen Wavelength Range
        subframe = ttk.Frame(frame)
        subframe.grid(row=5, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.lambda_min = tk.DoubleVar(self)
        w = tk.Entry(subframe, textvariable=self.lambda_min)
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.wl_type, "user")]
        ttk.Label(subframe, text=" to ").grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.lambda_max = tk.DoubleVar(self)
        w = tk.Entry(subframe, textvariable=self.lambda_max)
        w.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("tkvar", self.wl_type, "user")]
        self.lambda_options = ["microns", "angstroms"]
        self.lambda_unit = tk.StringVar(self, "microns")
        self.lambda_select = ttk.OptionMenu(subframe, self.lambda_unit, *self.lambda_options)
        self.lambda_select.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[self.lambda_select] = [("tkvar", self.wl_type, "user")]
        # Refresh Plot
        ttk.Button(frame, text="Refresh Plot", command=self.refresh_plot).grid(row=6, column=0, sticky=TK_STICKY_ALL)

        # Save Frame
        frame = ttk.LabelFrame(right_frame, text="Save to File")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Options
        self.save_throughput = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Throughput", variable=self.save_throughput, onvalue=1, offvalue=0)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.save_transmission = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Transmission", variable=self.save_transmission, onvalue=1, offvalue=0)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.save_background = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Background", variable=self.save_background, onvalue=1, offvalue=0)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.save_signal = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Signal", variable=self.save_signal, onvalue=1, offvalue=0)
        b.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.save_noise = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Noise", variable=self.save_noise, onvalue=1, offvalue=0)
        b.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.save_snr = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Signal to Noise", variable=self.save_snr, onvalue=1, offvalue=0)
        b.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.save_buttons = {
            "throughput": self.save_throughput,
            "transmission": self.save_transmission,
            "background": self.save_background,
            "signal": self.save_signal,
            "noise": self.save_noise,
            "snr": self.save_snr,
        }
        # Button
        ttk.Button(frame, text="Save", command=self.print_to_file).grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.set_enabled()


    def refresh_plot(self):
        if self.plot_type.get() == "plot_obs":
            self.plot_obs()
        else:
            self.plot_snr()


    @property
    def parameters_dict(self):
        if self.line_cenwave_units.get() == "angstroms":
            cenwave = self.line_cenwave.get() * u.angstrom
        else:
            cenwave = self.line_cenwave.get() * u.um
        if self.lambda_unit.get() == "angstroms":
            wl_min = self.lambda_min.get() * u.angstrom
            wl_max = self.lambda_max.get() * u.angstrom
        else:
            wl_min = self.lambda_min.get() * u.um
            wl_max = self.lambda_max.get() * u.um

        all_parameters = {
            "bandpass": self.bandpass.get(),
            "slit": self.slit_width.get() * u.arcsec,
            "n_exp": self.n_exp.get(),
            "source_fwhm": self.seeing_fwhm.get() * u.arcsec,
            "flux_mode": self.flux_mode.get(),
            "line_flux": self.line_flux.get() * 1.e-17 * u.erg / u.s / (u.cm * u.cm) / u.Hz,
            "line_cenwave": cenwave,
            "line_cenwave_units": self.line_cenwave_units.get(),
            "line_redshift": self.line_redshift.get(),
            "line_fwhm": self.line_fwhm.get() * u.km / u.s,
            "spec_mag": self.spec_mag.get() * u.mag,
            "spec_mag_units": self.spec_mag_units.get(),  # ['AB', 'Vega']
            "spec_mag_band": self.spec_mag_band.get(),
            "spec_type": self.spec_type.get(),
            "spec_path": self.spec_path,
            "flux_units": self.spec_fluxunit.get(),
            "spec_redshift": self.spec_redshift.get(),
            "spec_waveunit": self.spec_waveunit.get(),
            "calc_type": self.calculation_type.get(),
            "total_exptime": self.calc_exptime.get() * u.s,
            "total_snr": self.calc_snr.get(),
            "custom_airmass": self.custom_airmass.get(),
            "custom_watervapour": self.custom_water.get(),
            "Airmass": self.airmass.get(),
            "WaterVapour": self.water.get(),
            "wl_type": self.wl_type.get(),
            "wl_min": wl_min,
            "wl_max": wl_max,
            "wl_unit": self.lambda_unit.get(),
            "glao": self.ao_value.get()
        }
        return all_parameters


    def load_spectrum(self):
        if self.spec_type.get() == "User Spectrum":
            filetypes = (('text files', '*.txt'), ('text files', '*.dat'), ('text files', '*.fits'), ('All files', '*.*'))
            spec_path = fd.askopenfilename(title='Select Spectrum File', initialdir=get_data_file("etc.templates"),
                                           filetypes=filetypes)
            self.spec_path = Path(spec_path)
            self.spec_file.set(self.spec_path.name)


    def plot_obs(self):
        if not hasattr(self, 'ETC'):
            self.logger.error("Can't plot a calculation if none has been run!")
            return
        fig = self.ETC.plot_obs()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky=TK_STICKY_ALL)
        canvas.draw()


    def plot_snr(self):
        if not hasattr(self, 'ETC'):
            self.logger.error("Can't plot a calculation if none has been run!")
            return
        fig = self.ETC.plot_snr()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.get_tk_widget().grid(row=0, column=0, sticky=TK_STICKY_ALL)
        canvas.draw()


    def print_to_file(self):
        if not hasattr(self, 'ETC'):
            self.ETC = ETC(self.parameters_dict)
        printed_values = self.etc.print_to_file()
        results_path = get_temporary_dir()
        for key in self.save_buttons:
            if self.save_buttons[key].get():
                output_values = np.transpose([printed_values["wavegrid"], printed_values[key]])
                np.savetxt(results_path / "{}.txt".format(key), output_values, fmt='%.3f, %.3f')


    def run_calculation(self):
        self.ETC = ETC(self.parameters_dict, self.logger)
        summary, result = self.ETC.run_calculation()

        for item in self.view.get_children():
            self.view.delete(item)

        for i in range(len(summary["quant"])):
            view_values = (summary["quant"][i], summary["value"][i], summary["unit"][i])
            self.view.insert(parent='', index='end', iid=i, text='', values=view_values)

        self.lambda_min.set(self.ETC.spec_struct["wave"][0])
        self.lambda_max.set(self.ETC.spec_struct["wave"][-1])
        
        if self.plot_type.get() == "plot_obs":
            self.plot_obs()
        else:
            self.plot_snr()


    def config_mag_type(self):
        if self.spec_mag_units.get() == 'AB':
            self.spec_mag_band.set(self.ab_options[2])
            self.mag_bands.set_menu(self.spec_mag_band, *self.ab_options)
        else:
            self.spec_mag_band.set(self.vega_options[2])
            self.mag_bands.set_menu(self.spec_mag_band, *self.vega_options)
