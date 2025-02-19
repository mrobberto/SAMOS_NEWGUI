#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
We have been given a pair of classes (SCL in scl.py, and SoarTCS in soar_tcs.py) that
define the python method of talking to SOAR. The SCL class is a low-level connection
interface that is used by SoarTCS. As far as I can tell from the code, you should use the
SoarTCS class exclusively, and let it take care of the details in SCL.

Note that the SoarTCS class assumes that SOAR is available to be connected to. As such,
this class (which provides a wrapper to SoarTCS that understands SAMOS) will not create a
SoarTCS object *unless* the internet status is set to connected.

The SOAR class provides an `update_connection()` function that will add a SoarTCS object,
if none has been defined, if the current SAMOS status is connected. If you set the SAMOS
software to "connected" when you know you're not *actually* connected, that's on you.
"""
import numpy as np
import os
from pathlib import Path
import socket
import sys

from .soar_tcs import SoarTCS


class SOAR:
    def __init__(self, db, par, logger):
        self.db = db
        self.PAR = par
        self.logger = logger
        self.is_on = False
        self._soar = None
        self.update_connection()


    def update_connection(self):
        self.set_ip()
        if self.PAR.is_connected:
            if self._soar is None:
                try:
                    self._soar = SoarTCS(self.SOAR_IP, self.SOAR_PORT, self.logger)
                except Exception as e:
                    self.logger.error(f"Status is connected but unable to create SOAR interface")
                    self.logger.exception(e)


    def set_ip(self):
        ip_soar = self.db.get_value("config_ip_soar", default="127.0.0.1:9898")
        try:
            ip_port = ip_soar.split(":")
            self.SOAR_IP = ip_port[0]
            self.SOAR_PORT = int(ip_port[1])
        except IndexError as e:
            # Probably means this isn't a valid IP address. Set to loopback.
            self.SOAR_IP = "127.0.0.1"
            self.SOAR_PORT = 9898


    def echo_client(self):
        return self._soar_command("infoa")


    def send_to_tcs(self, command):
        return self._soar_command(command)


    def way(self):
        return self._soar_command("way")


    def offset(self, ra=0., dec=0.):
        return self._soar_command("offset", {"offset_ra": ra, "offset_dec": dec})


    def focus(self, param, value):
        return self._soar_command("focus", value, move_type=param)


    def clm(self, param):
        return self._soar_command("clm", param)


    def guider(self, param):
        return self._soar_command("guider", param)


    def whitespot(self, param, percentage):
        return self._soar_command("whitespot", percentage, turn_on=(param == "ON"))


    def lamp_id(self, param, location, percentage):
        return self._soar_command("lamp", location, state=param, percentage=percentage)


    def adc(self, param, percent):
        return self._soar_command("adc", percent, park=(param == "PARK"))


    def target(self, ra=0., dec=0., epoch=2000., ra_rate=0., dec_rate=0.):
        target_dict = {
            "ra": ra,
            "dec": dec,
            "epoch": epoch,
            "ra_rate": ra_rate,
            "dec_rate": dec_rate
        }
        return self._soar_command("target_move", target_dict)


    def ipa(self, angle=0.):
        return self._soar_command("ipa", angle)


    def instrument(self, instrument="GOODMAN"):
        return self._soar_command("instrument", instrument)


    def get_soar_status(self, key):
        if self._soar is None:
            return "DISCONNECTED"
        info_dict = self._soar.info
        if key in self._soar.info:
            return self._soar.info[key]
        return f"UNKNOWN INFO VALUE {key}"


    def _soar_command(self, message, *args, **kwargs):
        if not self.PAR.is_connected:
            return ["DISCONNECTED"]
        if self._soar is None:
            return ["NO SOAR OBJECT"]
        if hasattr(self._soar, message):
            result = getattr(self._soar, message)(*args, **kwargs)
            output = [f"Output from {message}"]
            if isinstance(result, dict):
                for item in result:
                    output.append(f"{item} = {result[item]}")
            else:
                output.append(result)
        return [f"UNKNOWN MESSAGE {message}"]
