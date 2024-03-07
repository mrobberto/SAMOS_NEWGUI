"""
SAMOS ETC tk Frame Class
"""
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from pathlib import Path
import yaml

from astropy import units as u

import tkinter as tk
from tkinter import ttk

from samos.etc import ETC
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame


class ETCPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SAMOS ETC", **kwargs)
        
        left_frame = tk.Frame(self.main_frame, background="bisque")
        left_frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        right_frame = tk.Frame(self.main_frame, background="gray")
        right_frame.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        
        # Top Left Frame:
        frame = tk.LabelFrame(left_frame, text="ETC Options", background="light gray", relief=tk.RIDGE)
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        # Grating
        tk.Label(frame, text="Grating:", anchor="w").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        bandpass_options = ["Low Red", "Low Blue", "High Red", "High Blue"]
        self.bandpass = tk.StringVar(self, bandpass_options[2])
        ttk.OptionMenu(frame, self.bandpass, *bandpass_options).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # Slit Width
        tk.Label(frame, text="Slit Width:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        slit_options = [0.17, 0.33, 0.5, 0.67, 0.88, 1.00, 1.17, 1.33, 1.5, 1.67, 1.88, 2.00]
        self.slit_width = tk.DoubleVar(self, slit_options[2])
        ttk.OptionMenu(frame, self.slit_width,  *slit_options).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="arcsec").grid(row=2, column=2, sticky=TK_STICKY_ALL)
        # Number of Exposures
        tk.Label(frame, text="# of Exposures").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.n_exp = tk.IntVar(self, 2)
        tk.Entry(frame, textvariable=self.n_exp).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        # Seeing
        tk.Label(frame, text="Seeing FWHM:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.seeing_fwhm = tk.DoubleVar(self, 0.4)
        tk.Entry(frame, textvariable=self.seeing_fwhm).grid(row=4, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="arcsec").grid(row=4, column=2, sticky=TK_STICKY_ALL)
        # Use Adaptive Optics?
        tk.Label(frame, text="Use GLAO?").grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.ao_value = tk.StringVar(self, "SAM")
        b = tk.Radiobutton(frame, text="SAM", value="SAM", variable=self.ao_value)
        b.grid(row=6, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Natural Seeing", value="Natural Seeing", variable=self.ao_value)
        b.grid(row=6, column=2, sticky=TK_STICKY_ALL)
        # Flux or Magnitude
        tk.Label(frame, text="Flux Mode:").grid(row=7, column=0, sticky=TK_STICKY_ALL)
        self.flux_mode = tk.StringVar(self, "magnitude")
        b = tk.Radiobutton(frame, text="Line Flux", value="flux", variable=self.flux_mode)
        b.grid(row=7, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Magnitude", value="magnitude", variable=self.flux_mode)
        b.grid(row=7, column=2, sticky=TK_STICKY_ALL)
        
        # Second Left Frame
        frame = tk.LabelFrame(left_frame, text="Emission Line Source", background="light gray")
        frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        # Line Flux
        tk.Label(frame, text="Line Flux:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.line_flux = tk.DoubleVar(self, 9.0)
        tk.Entry(frame, textvariable=self.line_flux).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="(1E-17 erg/Hz/s/cm\u00b2)").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # Central Wavelength
        tk.Label(frame, text="Central Wavelength:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.line_cenwave = tk.IntVar(self, 6563)
        tk.Entry(frame, textvariable=self.line_cenwave).grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.line_cenwave_units = tk.StringVar(self, "angstroms")
        b = tk.Radiobutton(frame, text="(angstroms)", value="angstroms", variable=self.line_cenwave_units)
        b.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="(microns)", value="microns", variable=self.line_cenwave_units)
        b.grid(row=1, column=3, sticky=TK_STICKY_ALL)
        # Redshift
        tk.Label(frame, text="Redshift:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.line_redshift = tk.DoubleVar(self, 0.0)
        tk.Entry(frame, textvariable=self.line_redshift).grid(row=2, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="Redshifted Wavelength:").grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.line_redshifted_wl = tk.DoubleVar(self, self.line_cenwave.get()*self.line_redshift.get())
        tk.Label(frame, textvariable=self.line_redshifted_wl).grid(row=2, column=3, sticky=TK_STICKY_ALL)
        # Source FWHM
        tk.Label(frame, text="Source FWHM:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.line_fwhm = tk.DoubleVar(self, 30.)
        tk.Entry(frame, textvariable=self.line_fwhm).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        tk.Label(frame, text="(km/s)").grid(row=3, column=2, sticky=TK_STICKY_ALL)
        self.flux_config_frame = frame

        # Third Left Frame
        frame = tk.LabelFrame(left_frame, text="Spectrum Source", background="light gray")
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        # Magnitude
        tk.Label(frame, text="Magnitude:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.spec_mag = tk.DoubleVar(self, 18.6)
        tk.Entry(frame, textvariable=self.spec_mag).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.spec_mag_units = tk.StringVar(self, "AB")
        b = tk.Radiobutton(frame, text="AB", value="AB", variable=self.spec_mag_units, command=self.config_mag_type)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Vega", value="Vega", variable=self.spec_mag_units, command=self.config_mag_type)
        b.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.ab_options = ["u_SDSS", "g_SDSS", "r_SDSS", "i_SDSS", "z_SDSS", "Y_VISTA", "J_VISTA", "H_VISTA", "K_VISTA"]
        self.vega_options = ["U", "B", "V", "R", "I", "Y", "J", "H", "Ks", "K"]
        self.spec_mag_band = tk.StringVar(self, self.ab_options[2])
        self.mag_bands = ttk.OptionMenu(frame, self.spec_mag_band, *self.ab_options)
        self.mag_bands.grid(row=0, column=4, sticky=TK_STICKY_ALL)
        # Spectrum
        tk.Label(frame, text="Spectrum:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.spec_options = ["Flat F_nu", "User Spectrum"]
        self.spec_type = tk.StringVar(self, self.spec_options[0])
        self.spec_dropdown = ttk.OptionMenu(frame, self.spec_type, *self.spec_options, command=self.load_spectrum)
        self.spec_dropdown.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        # User Spectrum
        user_spec_frame = tk.LabelFrame(frame, text="User Spectrum:")
        tk.Label(user_spec_frame, text="File:").grid(row=0, column=0, rowspan=4, columnspan=5, sticky=TK_STICKY_ALL)
        self.spec_path = None
        self.spec_file = tk.StringVar(self, "")
        tk.Entry(user_spec_frame, textvariable=self.spec_file).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        tk.Label(user_spec_frame, text="Flux Type:").grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.spec_fluxunit = tk.StringVar(self, "F_lam")
        b = tk.Radiobutton(user_spec_frame, text="F_lam", value="F_lam", variable=self.spec_fluxunit)
        b.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(user_spec_frame, text="F_nu", value="F_nu", variable=self.spec_fluxunit)
        b.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        tk.Label(user_spec_frame, text="Wavelength Units:").grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.spec_waveunit = tk.StringVar(self, "angstroms")
        b = tk.Radiobutton(user_spec_frame, text="Angstroms", value="angstroms", variable=self.spec_waveunit)
        b.grid(row=2, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(user_spec_frame, text="Microns", value="microns", variable=self.spec_waveunit)
        b.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        tk.Label(user_spec_frame, text="Redshift:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.spec_redshift = tk.DoubleVar(self, 0.0)
        tk.Entry(user_spec_frame, textvariable=self.spec_redshift).grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.mag_config_frame = frame

        # Fourth Left Frame
        frame = tk.LabelFrame(left_frame, text="Calculation Options", bg="light gray")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        # Calculation Type
        tk.Label(frame, text="Calculation Type:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.calculation_type = tk.StringVar(self, "calc_exptime")
        b = tk.Radiobutton(frame, text="Calculate Time from SNR", value="calc_exptime", variable=self.calculation_type)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Calculate SNR from Time", value="calc_snr", variable=self.calculation_type)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # Exptime
        subframe = tk.Frame(frame, bg="light gray")
        subframe.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        tk.Label(subframe, text="Exposure Time:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.calc_exptime = tk.DoubleVar(self, 1000.)
        tk.Entry(subframe, textvariable=self.calc_exptime).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        tk.Label(subframe, text="(s)").grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.calc_exptime_frame = subframe
        # SNR
        subframe = tk.Frame(frame, bg="light gray")
        subframe.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        tk.Label(subframe, text="SNR:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.calc_snr = tk.DoubleVar(self, 10.)
        tk.Entry(subframe, textvariable=self.calc_snr).grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.calc_snr_frame = subframe

        # Fifth Left Frame
        frame = tk.LabelFrame(left_frame, text="Optional Inputs", bg="light gray")
        frame.grid(row=4, column=0, sticky=TK_STICKY_ALL)
        # Airmass and Water Vapor
        tk.Label(frame, text="Use custom values for:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.custom_airmass = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Airmass", variable=self.custom_airmass, onvalue=1, offvalue=0,
                           command=self.config_airmass_water)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.custom_water = tk.IntVar(self, 0)
        b = tk.Checkbutton(frame, text="Water Vapour", variable=self.custom_water, onvalue=1, offvalue=0, 
                           command=self.config_airmass_water)
        b.grid(row=0, column=2, sticky=TK_STICKY_ALL)
        # Airmass
        subframe = tk.Frame(frame, bg="light gray")
        subframe.grid(row=1, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        tk.Label(subframe, text="Airmass:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.airmass_options = [1.0, 1.5, 2.0]
        self.airmass = tk.DoubleVar(self, self.airmass_options[0])
        self.airmass_select = ttk.OptionMenu(subframe, self.airmass, *self.airmass_options)
        self.airmass_select.configure(state="disabled")
        self.airmass_select.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.airmass_frame = subframe
        # Water Vapour
        subframe = tk.Frame(frame, bg="light gray")
        subframe.grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        tk.Label(subframe, text='Water Vapour:').grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.water_options = [1.0, 1.6, 3.0, 5.0]
        self.water = tk.DoubleVar(self, self.water_options[1])
        self.water_select = ttk.OptionMenu(subframe, self.water, *self.water_options)
        self.water_select.configure(state="disabled")
        self.water_select.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.water_frame = subframe

        # Calculate Frame
        frame = tk.LabelFrame(left_frame, text="Run", bg="light gray")
        frame.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        tk.Button(frame, text="CALCULATE", command=self.run_calculation).grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # First right frame
        frame = tk.LabelFrame(right_frame, text="Output", bg="light gray")
        frame.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        # Header text
        self.header_text = tk.StringVar(self, "")
        t = tk.Label(frame, textvariable=self.header_text, background="light gray")
        t.grid(row=0, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        # Frame to hold matplotlib canvas
        self.plot_frame = tk.Frame(frame, width=490, height=245)
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
        tk.Label(frame, text="Choose Plot:").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.plot_type = tk.StringVar(self, "plot_obs")
        b = tk.Radiobutton(frame, text="Plot Observation", value="plot_obs", variable=self.plot_type,
                           command=self.plot_obs)
        b.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="Plot Signal to Noise", value="plot_snr", variable=self.plot_type,
                           command=self.plot_snr)
        b.grid(row=3, column=2, sticky=TK_STICKY_ALL)
        # Wavelength Range
        tk.Label(frame, text="Wavelength Range:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.wl_type = tk.StringVar(self, "default")
        b = tk.Radiobutton(frame, text="Default", value="default", variable=self.wl_type, command=self.config_wave_type)
        b.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        b = tk.Radiobutton(frame, text="User-Selected", value="user", variable=self.wl_type, command=self.config_wave_type)
        b.grid(row=4, column=2, sticky=TK_STICKY_ALL)
        # Chosen Wavelength Range
        subframe = tk.Frame(frame)
        subframe.grid(row=5, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        self.lambda_min = tk.DoubleVar(self)
        tk.Entry(subframe, textvariable=self.lambda_min).grid(row=00, column=0, sticky=TK_STICKY_ALL)
        tk.Label(subframe, text=" to ").grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.lambda_max = tk.DoubleVar(self)
        tk.Entry(subframe, textvariable=self.lambda_max).grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.lambda_options = ["microns", "angstroms"]
        self.lambda_unit = tk.StringVar(self, "microns")
        self.lambda_select = ttk.OptionMenu(subframe, self.lambda_unit, *self.lambda_options)
        self.lambda_select.configure(state="disabled")
        self.lambda_select.grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.custom_wl_frame = subframe
        # Refresh Plot
        tk.Button(frame, text="Refresh Plot", command=self.refresh_plot).grid(row=6, column=0, sticky=TK_STICKY_ALL)

        # Save Frame
        frame = tk.LabelFrame(right_frame, text="Save to File", bg="light gray")
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
        tk.Button(frame, text="Save", command=self.print_to_file, relief=tk.RAISED).grid(row=2, column=0, sticky=TK_STICKY_ALL)

        # Run initial setup
        self.initial_setup()


    def initial_setup(self):
        self.config_flux_mode()
        self.config_calc_type()


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
            "total_exptime": self.calc_exptime.get(),
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


    def config_flux_mode(self):
        if self.flux_mode.get() == "magnitude":
            self._set_frame(self.mag_config_frame, "normal", "magnitude mode")
            self._set_frame(self.flux_config_frame, "disabled", "flux mode")
        elif self.flux_mode.get() == "flux":
            self._set_frame(self.mag_config_frame, "disabled", "magnitude mode")
            self._set_frame(self.flux_config_frame, "normal", "flux mode")
        else:
            self.logger.error("Invalid Flux Mode {}".format(self.flux_mode.get()))


    def config_airmass_water(self):
        if self.custom_airmass.get():
            self._set_frame(self.airmass_frame, "disabled", "custom airmass")
        else:
            self._set_frame(self.airmass_frame, "normal", "custom airmass")
        if self.custom_water.get():
            self._set_frame(self.water_frame, "disabled", "custom water vapour")
        else:
            self._set_frame(self.water_frame, "normal", "custom water vapour")


    def config_calc_type(self):
        if self.calculation_type.get() == 'calc_exptime':
            self._set_frame(self.calc_exptime_frame, "normal", "calculate exptime")
            self._set_frame(self.calc_snr_frame, "disabled", "calculate snr")
        elif self.calculation_type.get() == 'calc_snr':
            self._set_frame(self.calc_exptime_frame, "disabled", "calculate exptime")
            self._set_frame(self.calc_snr_frame, "normal", "calculate snr")
        else:
            self.logger.error("Invalid Calculation Type {}".format(self.flux_mode.get()))


    def config_wave_type(self):
        if self.wl_type.get() == "default":
            self._set_frame(self.custom_wl_frame, "disabled", "custom wavelength")
        elif self.wl_type.get() == "user":
            self._set_frame(self.custom_wl_frame, "normal", "custom wavelength")
        else:
            self.logger.error("Invalid Wavelength Mode {}".format(self.flux_mode.get()))


    def _set_frame(self, frame, state, name):
        for child in frame.winfo_children():
            try:
                child.configure(state=state)
            except Exception as e:
                self.logger.error("Attempting to set state={} for {} child {} produced {}".format(name, state, child, e))
