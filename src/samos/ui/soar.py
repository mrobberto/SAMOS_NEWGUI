"""
SAMOS SOAR tk Frame Class
"""
from datetime import datetime
from functools import partial

from astropy.coordinates import SkyCoord

import tkinter as tk
import ttkbootstrap as ttk
from tkinter.scrolledtext import ScrolledText

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class SOARPage(SAMOSFrame):
    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "SOAR", **kwargs)
        self.labels = {}
        self.label_text = {}
        self.initialized = False

        # Initialization Button
        w = ttk.Button(self.main_frame, text="Initialize", command=self.way)
        w.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)

        # Top Frame
        frame = ttk.LabelFrame(self.main_frame, text="Legend")
        frame.grid(row=1, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        w = ttk.Label(frame, anchor="w", text="Value has not been sent to SAMI", bootstyle="warning", width=40)
        w.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        w = ttk.Label(frame, anchor="e", text="Value has successfully been sent to SAMI", bootstyle="success", width=40)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)

        # Left Frame
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=2, column=0, sticky=TK_STICKY_ALL)

        # Offset
        w = ttk.Button(frame, text="Get Offset", command=partial(self.tcs_offset, "STATUS"), bootstyle="info")
        w.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.offset_ra = self.make_db_var(tk.DoubleVar, "soar_offset_ra_set", 0., callback=partial(self.mark_invalid, "offset_ra"))
        self.offset_dec = self.make_db_var(tk.DoubleVar, "soar_offset_dec_set", 0., callback=partial(self.mark_invalid, "offset_dec"))
        w = ttk.Label(frame, text="Offset RA:")
        w.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.labels['offset_ra'] = ttk.Entry(frame, textvariable=self.offset_ra, width=12, bootstyle="warning")
        self.labels['offset_ra'].grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels['offset_ra']] = [("condition", self, "initialized", True)]
        w = ttk.Label(frame, text="Offset DEC:")
        w.grid(row=1, column=3, sticky=TK_STICKY_ALL)
        self.labels['offset_dec'] = ttk.Entry(frame, textvariable=self.offset_dec, width=12, bootstyle="warning")
        self.labels['offset_dec'].grid(row=1, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels['offset_dec']] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Move to Offset", command=partial(self.tcs_offset, "MOVE"), bootstyle="success")
        w.grid(row=1, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Focus
        w = ttk.Button(frame, text="Get Focus", command=partial(self.tcs_focus, "STATUS"), bootstyle="info")
        w.grid(row=2, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.focus = self.make_db_var(tk.IntVar, "soar_focus_set", 0, callback=partial(self.mark_invalid, "focus"))
        self.labels["focus"] = ttk.Entry(frame, textvariable=self.focus, width=12, bootstyle="warning")
        self.labels["focus"].grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["focus"]] = [("condition", self, "initialized", True)]
        focus_options = ["Relative", "Absolute"]
        self.focus_option = self.make_db_var(tk.StringVar, "soar_focus_move_type_set", "Relative")
        w = ttk.OptionMenu(frame, self.focus_option, None, *focus_options)
        w.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Change Focus", command=partial(self.tcs_focus, "MOVE"), bootstyle="success")
        w.grid(row=2, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # CLM
        w = ttk.Button(frame, text="Get CLM", command=partial(self.tcs_clm, "STATUS"), bootstyle="info")
        w.grid(row=3, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.clm = self.make_db_var(tk.StringVar, "soar_clm_set", "IN", callback=partial(self.mark_invalid, "clm"))
        self.labels["clm"] = ttk.Checkbutton(
            frame,
            textvariable=self.clm,
            command=partial(self.tcs_clm, "SET"),
            variable=self.clm,
            onvalue="IN",
            offvalue="OUT",
            bootstyle="round-toggle-warning"
        )
        self.labels["clm"].grid(row=3, column=1, padx=5, sticky=TK_STICKY_ALL)
        self.label_text["clm"] = "round-toggle-"
        self.check_widgets[self.labels["clm"]] = [("condition", self, "initialized", True)]

        # Guider
        w = ttk.Button(frame, text="Get Guider", command=partial(self.tcs_guider, "STATUS"), bootstyle="info")
        w.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.guider = self.make_db_var(tk.StringVar, "soar_guider_set", "DISABLED", callback=partial(self.mark_invalid, "guider"))
        self.labels["guider"] = ttk.Checkbutton(
            frame,
            textvariable=self.guider,
            command=partial(self.tcs_guider, "SET"),
            variable=self.guider,
            onvalue="ENABLED",
            offvalue="DISABLED",
            bootstyle="round-toggle-warning"
        )
        self.labels["guider"].grid(row=4, column=1, padx=5, sticky=TK_STICKY_ALL)
        self.label_text["guider"] = "round-toggle-"
        self.check_widgets[self.labels["guider"]] = [("condition", self, "initialized", True)]

        # Whitespot
        self.whitespot = self.make_db_var(
            tk.StringVar,
            "soar_whitespot_set",
            "OFF",
            callback=partial(self.mark_invalid, "whitespot")
        )
        self.whitespot_pct = self.make_db_var(
            tk.DoubleVar,
            "soar_whitespot_pct_set",
            50.,
            callback=partial(self.mark_invalid, "whitespot_pct")
        )
        w = ttk.Button(frame, text="Get Whitespot", command=partial(self.tcs_whitespot, "STATUS"), bootstyle="info")
        w.grid(row=5, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.labels["whitespot"] = ttk.Checkbutton(
            frame,
            textvariable=self.whitespot,
            command=partial(self.tcs_whitespot, "SET"),
            variable=self.whitespot,
            onvalue="ON",
            offvalue="OFF",
            bootstyle="round-toggle-warning"
        )
        self.labels["whitespot"].grid(row=5, column=1, padx=5, sticky=TK_STICKY_ALL)
        self.label_text["whitespot"] = "round-toggle-"
        self.check_widgets[self.labels["whitespot"]] = [("condition", self, "initialized", True)]
        ttk.Label(frame, text="Whitespot %:").grid(row=5, column=2, sticky=TK_STICKY_ALL)
        self.labels["whitespot_pct"] = ttk.Entry(frame, textvariable=self.whitespot_pct, width=4, bootstyle="warning")
        self.labels["whitespot_pct"].grid(row=5, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["whitespot_pct"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set Whitespot Intensity", command=partial(self.tcs_whitespot, "SET"), bootstyle="success")
        w.grid(row=5, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # ADC
        self.adc_options = ["IN", "PARK", "TRACK"]
        self.adc = self.make_db_var(tk.StringVar, "soar_adc_set", self.adc_options[1], callback=partial(self.mark_invalid, "adc"))
        self.adc_pct = self.make_db_var(tk.DoubleVar, "soar_adc_pct_set", 0., callback=partial(self.mark_invalid, "adc_pct"))
        w = ttk.Button(frame, text="Get ADC", command=partial(self.tcs_adc, "STATUS"), bootstyle="info")
        w.grid(row=6, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.labels["adc"] = ttk.OptionMenu(frame, self.adc, None, *self.adc_options, command=partial(self.tcs_adc, "SET"), bootstyle="warning")
        self.labels["adc"].grid(row=6, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["adc"]] = [("condition", self, "initialized", True)]
        ttk.Label(frame, text="ADC %:").grid(row=6, column=2, sticky=TK_STICKY_ALL)
        self.labels["adc_pct"] = ttk.Entry(frame, textvariable=self.adc_pct, width=4, bootstyle="warning")
        self.labels["adc_pct"].grid(row=6, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["adc_pct"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set ADC %", command=partial(self.tcs_adc, "SET"), bootstyle="success")
        w.grid(row=6, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # IPA
        self.ipa = self.make_db_var(tk.DoubleVar, "soar_position_angle_set", 0., callback=partial(self.mark_invalid, "ipa"))
        w = ttk.Button(frame, text="Get IPA", command=partial(self.tcs_ipa, "STATUS"), bootstyle="info")
        w.grid(row=7, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.labels["ipa"] = ttk.Entry(frame, textvariable=self.ipa, width=20, bootstyle="warning")
        self.labels["ipa"].grid(row=7, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["ipa"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set IPA", command=partial(self.tcs_ipa, "SET"), bootstyle="success")
        w.grid(row=7, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Instrument
        self.instrument = self.make_db_var(tk.StringVar, "soar_instrument_set", "SAM", callback=partial(self.mark_invalid, "instrument"))
        w = ttk.Button(frame, text="Get Instrument", command=partial(self.tcs_instrument, "STATUS"), bootstyle="info")
        w.grid(row=8, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        self.labels["instrument"] = ttk.Entry(frame, textvariable=self.instrument, width=20, bootstyle="warning")
        self.labels["instrument"].grid(row=8, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["instrument"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="Set Instrument", command=partial(self.tcs_instrument, "MOVE"), bootstyle="success")
        w.grid(row=8, column=5, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Target and Slew
        frame = ttk.LabelFrame(self.main_frame, text="Target:")
        frame.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.ra = self.make_db_var(tk.DoubleVar, "target_ra", 0., callback=partial(self.mark_invalid, "target_ra"))
        ttk.Label(frame, text="RA:", justify=tk.LEFT).grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.labels["target_ra"] = ttk.Entry(frame, textvariable=self.ra, width=11, bootstyle="warning")
        self.labels["target_ra"].grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["target_ra"]] = [("condition", self, "initialized", True)]
        self.dec = self.make_db_var(tk.DoubleVar, "target_dec", 0., callback=partial(self.mark_invalid, "target_dec"))
        ttk.Label(frame, text="DEC:", justify=tk.LEFT).grid(row=0, column=2, sticky=TK_STICKY_ALL)
        self.labels["target_dec"] = ttk.Entry(frame, textvariable=self.dec, width=11, bootstyle="warning")
        self.labels["target_dec"].grid(row=0, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["target_dec"]] = [("condition", self, "initialized", True)]
        self.epoch = self.make_db_var(tk.DoubleVar, "target_epoch", 2000.0, callback=partial(self.mark_invalid, "target_epoch"))
        ttk.Label(frame, text="Epoch:", justify=tk.LEFT).grid(row=0, column=4, sticky=TK_STICKY_ALL)
        self.labels["target_epoch"] = ttk.Entry(frame, textvariable=self.epoch, width=6, bootstyle="warning")
        self.labels["target_epoch"].grid(row=0, column=5, sticky=TK_STICKY_ALL)
        self.check_widgets[self.labels["target_epoch"]] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="STATUS", command=partial(self.tcs_target, "STATUS"), bootstyle="info")
        w.grid(row=1, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="MOVE", command=partial(self.tcs_target, "MOVE"), bootstyle="success")
        w.grid(row=1, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="MOUNT", command=partial(self.tcs_target, "MOUNT"), bootstyle="success")
        w.grid(row=1, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="STOP", command=partial(self.tcs_target, "STOP"), bootstyle="warning")
        w.grid(row=1, column=3, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Right Frame
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=2, column=1, rowspan=2, sticky=TK_STICKY_ALL)
        # Lamps - there are 12 lamps, with 9 and 12 having dimmers.
        self.lamp_vars = {}
        self.lamp_dimmer_vars = {}
        for i in range(12):
            lamp_name = f"lamp_{i+1}"
            self.lamp_vars[i+1] = self.make_db_var(
                tk.StringVar,
                f"soar_lamp_{i+1}_set",
                "OFF",
                callback=partial(self.mark_invalid, lamp_name)
            )
            w = ttk.Button(frame, text="Get Lamp {}".format(i+1), command=partial(self.tcs_lamp, "STATUS", i+1), bootstyle="info")
            w.grid(row=i, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
            self.check_widgets[w] = [("condition", self, "initialized", True)]
            self.labels[lamp_name] = ttk.Checkbutton(
                frame,
                textvariable=self.lamp_vars[i+1],
                command=partial(self.tcs_lamp, "SET", i+1), 
                variable=self.lamp_vars[i+1],
                onvalue="ON",
                offvalue="OFF",
                bootstyle="round-toggle-warning"
            )
            self.labels[lamp_name].grid(row=i, column=1, padx=5, sticky=TK_STICKY_ALL)
            self.label_text[lamp_name] = "round-toggle-"
            self.check_widgets[self.labels[lamp_name]] = [("condition", self, "initialized", True)]
            if (i == 8) or (i == 11):
                # Add dimmer
                dimmer_name = f"lamp_dimmer_{i+1}"
                self.lamp_dimmer_vars[i+1] = self.make_db_var(
                    tk.DoubleVar,
                    f"soar_lamp_dimmer_{i+1}_set",
                    50.,
                    callback=partial(self.mark_invalid, dimmer_name)
                )
                ttk.Label(frame, text="Dimmer Intensity %:").grid(row=i, column=2, sticky=TK_STICKY_ALL)
                self.labels[dimmer_name] = ttk.Entry(frame, textvariable=self.lamp_dimmer_vars[i+1], width=4, bootstyle="warning")
                self.labels[dimmer_name].grid(row=i, column=3, sticky=TK_STICKY_ALL)
                self.check_widgets[self.labels[dimmer_name]] = [("condition", self, "initialized", True)]
                w = ttk.Button(frame, text="Set Lamp Intensity", command=partial(self.tcs_lamp, "SET", i+1), bootstyle="success")
                w.grid(row=i, column=4, padx=2, pady=2, sticky=TK_STICKY_ALL)
                self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Custom Command
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Custom Command:").grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.custom_command = tk.StringVar(self, "")
        w = ttk.Entry(frame, textvariable=self.custom_command)
        w.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]
        w = ttk.Button(frame, text="SEND", command=self.tcs_custom, bootstyle="success")
        w.grid(row=0, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[w] = [("condition", self, "initialized", True)]

        # Bottom Status Log
        self.text_area = ScrolledText(self.main_frame, wrap=tk.WORD, width=53, height=25, font=("Times New Roman", 15))
        self.text_area.grid(row=5, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        self.set_enabled()


    @check_enabled
    def mark_invalid(self, component):
        comp_str = self.label_text.get(component, "")
        self.labels[component].configure(bootstyle=f"{comp_str}warning")

    @check_enabled
    def tcs_custom(self):
        self._log(f"Sending {self.custom_command.get()}")
        reply = self.SOAR.send_to_tcs(self.custom_command.get())
        self._log(f"Received {reply}")


    @check_enabled
    def way(self):
        """ 
        (Who are you?) This command returns an identification string

        For example
            WAY
            DONE SOAR 4.2m
        """
        self._log("Sent WAY")
        reply = self.SOAR.send_to_tcs("WAY")
        self.initialized = True
        self._log(f"Received {reply}")


    @check_enabled
    def tcs_offset(self, event):
        """
        This command send an offset motion request to the TCS.
        The offset is given in units of arcseconds, and must be preceded by one of the direction characters N, S, E and W.
        """
        if event == "STATUS":
            offset_ra = self.SOAR.get_soar_status("offset_ra")
            self._log(f"Received {offset_ra} as RA offset status")
            if isinstance(offset_ra, float):
                self.offset_ra.set(offset_ra)
                self.labels["offset_ra"].configure(bootstyle="success")
            offset_dec = self.SOAR.get_soar_status("offset_dec")
            if isinstance(offset_dec, float):
                self.offset_dec.set(offset_dec)
                self.labels["offset_dec"].configure(bootstyle="success")
            self._log(f"Received {offset_dec} as DEC offset status")
        else:
            reply = self.SOAR.offset(ra=self.offset_ra.get(), dec=self.offset_dec.get())
            if "DONE" in reply:
                self.labels["offset_ra"].configure(bootstyle="success")
                self.labels["offset_dec"].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_focus(self, event):
        """
        This command requests actions to the focus mechanism associated with the secondary mirror (M2).

        Parameters
        ----------
        event : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        if event == "STATUS":
            focus = self.SOAR.get_soar_status("focus")
            self._log(f"Received {focus} as focus value")
            if isinstance(focus, int):
                self.focus.set(focus)
                self.labels["focus"].configure(bootstyle="success")
        else:
            offset = self.focus.get()
            event = self.focus_option.get().lower()
            self._log(f"Sending FOCUS {event} {offset}")
            reply = self.SOAR.focus(event, offset)
            if "successfully" in reply:
                self.labels["focus"].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_clm(self, event):
        """ This command requests actions to the comparison lamps mirror mechanism. """
        if event == "STATUS":
            clm_state = self.SOAR.get_soar_status("clm")
            self._log(f"Received {clm_state} as clm value")
            if isinstance(clm_state, str) and clm_state.upper() in ["IN", "OUT"]:
                self.clm.set(clm_state.upper())
                self.labels["clm"].configure(bootstyle="round-toggle-success")
        else:
            self._log(f"Sending CLM {event}")
            reply = self.SOAR.clm(event)
            if "successfully" in reply:
                self.labels["clm"].configure(bootstyle="round-toggle-success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_guider(self, event):
        """ This command enable or disable the guider device. """
        if event == "STATUS":
            guider_state = self.SOAR.get_soar_status("guider")
            self._log(f"Received {guider_state} as guider value")
            if isinstance(guider_state, str) and guider_state.upper() in ["ENABLED", "DISABLED"]:
                self.guider.set(guider_state.upper())
                self.labels["guider"].configure(bootstyle="round-toggle-success")
        else:
            self._log(f"Sending Guider {event}")
            reply = self.SOAR.guider(event)
            if "successfully" in reply:
                self.labels["guider"].configure(bootstyle="round-toggle-success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_whitespot(self, event):
        """ This command enable or disable the Whitespot device. """
        if event == "STATUS":
            whitespot_state = self.SOAR.get_soar_status("whitespot")
            self._log(f"Received {whitespot_state} as whitespot value")
            if isinstance(whitespot_state, float):
                if whitespot_state == 0.:
                    self.whitespot.set("OFF")
                else:
                    self.whitespot.set("ON")
                self.labels["whitespot"].configure(bootstyle="round-toggle-success")
                self.whitespot_pct.set(whitespot_state)
                self.labels["whitespot_pct"].configure(bootstyle="success")
        else:
            whitespot_state = self.whitespot.get()
            if whitespot_state == "OFF":
                self.whitespot_pct.set(0.)
            self._log(f"Sending Whitespot {whitespot_state}")
            reply = self.SOAR.whitespot(whitespot_state, self.whitespot_pct.get())
            if "successfully" in reply:
                self.labels["whitespot"].configure(bootstyle="round-toggle-success")
                self.labels["whitespot_pct"].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_lamp(self, event, lamp_number):
        """
        This command turns on or off the calibration lamps. Where “LN” is the location of the lamp (1 to 12).
        There are two position that have dimmers, position L9 and L12, therefore, a percentage must be added.
        """
        if event == "STATUS":
            lamp_state = self.SOAR.get_soar_status(f"lamp_{lamp_number}")
            self._log(f"Received {lamp_state} for lamp {lamp_number}")
            if isinstance(lamp_state, str) and lamp_state in ["ON", "OFF"]:
                self.lamp_vars[lamp_number].set(lamp_state)
                self.labels[f"lamp_{lamp_number}"].configure(bootstyle="round-toggle-success")
            if lamp_number in self.lamp_dimmer_vars:
                lamp_dimmer_state = self.SOAR.get_soar_status(f"lamp_dimmer_{lamp_number}")
                self._log(f"Received {lamp_dimmer_state} for lamp {lamp_number}")
                if isinstance(lamp_dimmer_state, float):
                    self.lamp_dimmer_vars[lamp_number].set(lamp_dimmer_state)
                    self.labels[f"lamp_dimmer_{lamp_number}"].configure(bootstyle="success")
        else:
            lamp_value = self.lamp_vars[lamp_number].get()
            lamp_dimmer = 0.
            if lamp_number in self.lamp_dimmer_vars:
                lamp_dimmer = self.lamp_dimmer_vars[lamp_number].get()
            self._log(f"Sending Lamp {lamp_number} {lamp_value} with dimmer {lamp_dimmer}")
            reply = self.SOAR.lamp_id(lamp_value, lamp_number, lamp_dimmer)
            if "successfully" in reply or "not needed" in reply:
                self.labels[f"lamp_{lamp_number}"].configure(bootstyle="round-toggle-success")
                if lamp_number in lamp_dimmer_vars:
                    self.lamp_dimmer_vars[lamp_number].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_adc(self, event, option=None):
        if event == "STATUS":
            adc_state = self.SOAR.get_soar_status("adc").upper()
            self._log(f"Received {adc_state} as adc value")
            if isinstance(adc_state, str) and adc_state in self.adc_options:
                self.adc.set(adc_state)
                self.labels["adc"].configure(bootstyle="success")
            adc_pct = self.SOAR.get_soar_status("adc_pct")
            self._log(f"Received {adc_pct} as adc percentage")
            if isinstance(adc_pct, float):
                self.adc_pct.set(adc_pct)
                self.labels["adc_pct"].configure(bootstyle="success")
        else:
            adc_state = self.adc.get()
            adc_pct = self.adc_pct.get()
            self._log(f"Sending adc {adc_state} {adc_pct}")
            reply = self.SOAR.adc(adc_state, adc_pct)
            if "successfully" in reply:
                self.labels["adc"].configure(bootstyle="success")
                self.labels["adc_pct"].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_ipa(self, event):
        """
        This command set a new instrument position angle to the TCS.
        The IPA is given in units of degrees.
        """
        if event == "STATUS":
            ipa_state = self.SOAR.get_soar_status("ipa")
            self._log(f"Received {ipa_state} as ipa value")
            if isinstance(ipa_state, float):
                self.ipa.set(ipa_state)
                self.labels["ipa"].configure(bootstyle="success")
        else:
            self._log(f"Sending IPA {event}")
            reply = self.SOAR.ipa(self.ipa.get())
            if "successfully" in reply:
                self.labels["ipa"].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_instrument(self, event):
        """
        This command selects the instrument in use
        """
        if event == "STATUS":
            instrument_state = self.SOAR.get_soar_status("instrument")
            self._log(f"Received {instrument_state} as instrument value")
            self.instrument.set(instrument_state)
            self.labels["instrument"].configure(bootstyle="success")
        else:
            instrument_state = self.instrument.get()
            self._log(f"Sending Instrument {instrument_state}")
            reply = self.SOAR.instrument(instrument_state)
            if "successfully" in reply:
                self.labels["instrument"].configure(bootstyle="success")
            self._log(f"Received {reply}")


    @check_enabled
    def tcs_target(self, event):
        """
        This command send a new position request to the TCS.
        The target is given in units of RA (HH:MM:SS.SS), DEC (DD:MM:SS.SS) and EPOCH (year).
        This command involves the movement of mount, dome, rotator, adc and optics.
        If it is required to know only the state of the mount, use option "MOUNT"
        """
        if event == "STATUS":
            for item in ["ra", "dec", "epoch"]:
                name = f"target_{item}"
                value = self.SOAR.get_soar_status(name)
                self._log(f"Received {value} as Target {item.upper()} value")
                if isinstance(value, float):
                    getattr(self, name).set(value)
                    self.labels[name].configure(bootstyle="success")
        else:
            ra = self.target_ra.get()
            dec = self.target_dec.get()
            epoch = self.target_epoch.get()
            self._log(f"Sending target (ra, dec, epoch) = ({ra}, {dec}, {epoch})")
            reply = self.SOAR.target(ra=ra, dec=dec, epoch=epoch)
            if reply:
                for item in ["ra", "dec", "epoch"]:
                    name = f"target_{item}"
                    self.labels[name].configure(bootstyle="success")
            self._log(f"Received {reply}")


    def _log(self, message):
        self.logger.info("Adding '{}' to log".format(message))
        self.text_area.insert(tk.END, f"{datetime.now()}: {message}\n")
        self.text_area.yview(tk.END)
