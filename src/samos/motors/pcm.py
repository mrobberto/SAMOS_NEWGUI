#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 28 08:11:18 2021

Module to work with the IDG PCM controller and EZHR Stepper module controller.

# Documented Notes:

All commands that you want to send to the EZHR motor controllers must be preceded with:
`~@,9600_8N1T2000,`

    - `~` is the character that all messages to the PCM start with. 
    - `@` means push the message to the RS485 bus. 
    - `9600_8N1T2000` means use 9600 baud, 8 data bits, no parity, 1 stop bit, with a 2000
       millisecond timeout for a response message.

All the commands you send to the EZHR start with a drive number: /1, /2, /3 etc.

When you send a command like `~@,9600_8N1T2000,/3e1R` you are asking drive 3 (/3) to
execute stored procedure 1 (e1). The R last the end tells it to run the command.

Every command returns a response packet. The format of the packet is detailed in the EZHR
instructions. See page 23 of the EZHR manual.

You can also query the drive at anytime. Query commands start with a `?` and do not need
an R at the end. The command to query the current step count is `?0`, and the command to
query the limit switches is `?4`. For example: `~@,9600_8N1T2000,/3?4` asks drive 3 (/3)
to return the position switch status (?4). Query commands are on page 9 of the manual.

You should query the status of the motor controller to see if it has stopped moving, then
query the step count, and the position sensor status, to make sure it went to where you
thought it should go to.

With the grisms you must send one drive home, and make sure it is home by checking its
status before  moving the other drive.

# AND FOR SUPPORT...

    - CALL ME from 8AM to 10PM +1(443) 299 7810
    - TEXT ME anytime +1(443) 299 7810
    - FB MESSENGER ME… Facebook.com/limey.steve.5 ...Use the video or audio chat option - 
      it rings on my cell.
    - FACETIME ME +1(443)299 7810

# FOR TESTING TCP COMMUNICATION ON LOCALHOST (see instuction below)
> echo_server() 
> echo_client()

# PCM procedures
> PCM_power_on()
> all_port_status()
> initialize_filter_wheel(FW)
> stored_filter_wheel_procedures()
> home_filter_wheel(FW)
> move_filter_wheel(position)
> query_current_step_counts(FW)
> timed_query_current_count_monitor(FW)
> initialize_grism_rails()
> stored_grism_rails_procedures()
> home_grism_rails(GR)
> fast_home_grism_rails(GR)
> move_grism_rails(position)

# To use/test
>>> from samos.motors import PCM
>>> PCM = PCM(parameters_object, logger, canvas_object)
>>> PCM.echo_client()
>>>     Received b'NL11111111'
>>> PCM.params()
>>>     {'Host': '10.0.0.179', 'PORT': 1000}
>>> PCM.params['Host']
@author: m. robberto
"""
from astropy.io import ascii
from astropy.table import Table
import functools
import numpy as np
import os
from pathlib import Path
import socket
import sys
import time 

from samos.utilities import get_data_file
from samos.utilities.constants import *


def motor_move(indicators):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.indicator is not None:
                for item in indicators:
                    self.indicator.itemconfig(f"{item}_ind", fill=INDICATOR_LIGHT_PENDING_COLOR)
                    self.indicator.update()
            result = func(self, *args, **kwargs)
            if self.indicator is not None:
                for item in indicators:
                    self.indicator.itemconfig(f"{item}_ind", fill=INDICATOR_LIGHT_ON_COLOR)
                    self.indicator.update()
            return result
        return wrapper
    return decorator


class PCM():
    def __init__(self, par, logger, canvas_Indicator=None):
        self.PAR = par
        self.logger = logger
        self.set_ip()
        self.is_on = False
        self.fw1_positions = {}
        self.fw1_commands = {}
        self.fw2_positions = {}
        self.fw2_commands = {}
        self.gra_positions = {}
        self.gra_commands = {}
        self.grb_positions = {}
        self.grb_commands = {}

        # Configure socket wait
        socket.setdefaulttimeout(3)
        
        # reference to indicator lights in main GUI
        self.canvas_Indicator = canvas_Indicator

        data = ascii.read(get_data_file("motors", 'IDG_Filter_positions.txt'))
        for i, name in enumerate(["A1", "A2", "A3", "A4", "A5", "A6"]):
            self.fw1_positions[name] = data['Counts'][i]
            self.fw1_commands[name] = bytearray("1e{}R".format(i+1), 'utf8')
        for i, name in enumerate(["B1", "B2", "B3", "B4", "B5", "B6"]):
            self.fw1_positions[name] = data['Counts'][i+6]
            self.fw1_commands[name] = bytearray("2e{}R".format(i+1), "utf8")
        self.gra_positions["GR_H1"] = data['Counts'][12]
        self.gra_positions["GR_A1"] = data['Counts'][14]
        self.gra_positions["GR_A2"] = data['Counts'][16]
        self.grb_positions["GR_H2"] = data['Counts'][13]
        self.grb_positions["GR_B1"] = data['Counts'][15]
        self.grb_positions["GR_B2"] = data['Counts'][17]
        self.gra_commands["GR_H1"] = b"3e0R"
        self.gra_commands["GR_A1"] = b"3e1R"
        self.gra_commands["GR_A2"] = b"3e2R"
        self.grb_commands["GR_H2"] = b"4e0R"
        self.grb_commands["GR_B1"] = b"4e1R"
        self.grb_commands["GR_B2"] = b"4e2R"


    def initialize_motors(self):
        self.set_ip()
        self.check_if_power_is_on()
        if self.canvas_Indicator is not None:
            if self.is_on:
                self.logger.info("Motors connected!")
                self.canvas_Indicator.itemconfig("grism_ind", fill=INDICATOR_LIGHT_ON_COLOR)
                self.canvas_Indicator.itemconfig("filter_ind", fill=INDICATOR_LIGHT_ON_COLOR)
            else:
                self.logger.info("Motors not connected!")
                self.canvas_Indicator.itemconfig("grism_ind", fill=INDICATOR_LIGHT_OFF_COLOR)
                self.canvas_Indicator.itemconfig("filter_ind", fill=INDICATOR_LIGHT_OFF_COLOR)


    def initialize_indicator(self, indicator):
        if self.canvas_Indicator is not None:
            self.logger.warning("Overwriting existing indicator widget with a new one!")
        self.canvas_Indicator = indicator


    def set_ip(self):
        """
        Called when the configured IP addresses change
        """
        self.IP_Host = self.PAR.IP_dict['IP_PCM'].split(":")[0]
        self.IP_Port = int(self.PAR.IP_dict['IP_PCM'].split(":")[1])


    def check_if_power_is_on(self):
        self.logger.info("Checking Power Status")
        reply = self._send(b'~se,all,on\n')
        if reply is not None:
            if "NO RESPONSE" in reply:
                self.logger.info("Motor power is off")
                self.is_on = False
                return False
            self.is_on = True
            self.logger.info("Motors replied {}".format(reply))
            return True
        self.logger.warning("No reply from Motors")
        return False


    def echo_client(self):
        self.logger.info("Sending PCM echo")
        return self._send(b'~se,all,on\n')


    def power_on(self):
        self.logger.info("Sending PCM power on signal")
        return self._send(b'~se,all,on\n')


    def power_off(self):
        self.logger.info("Sending PCM power off signal")
        return self._send(b'~se,all,off\n')


    def send_command_string(self, string):
        self.logger.info("Sending PCM command string {}".format(string))
        return self._send(bytearray("~@,9600_8N1T2000,{}\n".format(string)), 'utf8')


    def filter_sensor_status(self, FW):
        self.logger.info("Getting status from {}".format(FW))
        if FW == "FW1":
            return self.send_command_string("/1?0")
        elif FW == "FW2":
            return self.send_command_string("/2?0")
        self.logger.error("Received request for sensor status for unknown component {}".format(FW))


    def all_ports_status(self):
        self.logger.info("Getting status of all power ports")
        return self._send(b"~ge,all\n")


    def initialize_filter_wheel(self, FW):
        self.logger.warning("Initializing PCM Filter Wheel {}".format(FW))
        self.logger.warning("This should only need to be done before first use or after replacing a drive.")
        #   Here are filter wheel commands to send to the PCM. The stored procedures only 
        # need to be sent once in the lifetime of the drive. You should have the ability
        # to send these, but will not have to unless we replaced a drive.
        #   The operating commands allow you to choose a particular filter by asking the
        # drive to execute a stored procedure. This should be integrated into your code.
        # You also ought to query the wheels to make sure they are where you think they
        # are.
        #   Note: all procedures include the command to route the drive packet via the PCM
        # so it should be really simple to integrate.
        # BTW the camera is not facing the filter wheel.

        # FILTER WHEEL STORED PROCEDURES: 
        #   These need to be sent to the motor controllers the first time they are used.
        # i.e if you replace a motor controller you should reinitialize with these
        # commands…

        if FW == "FW1":
            # WHEEL 1
            # Initial drive settings (velocity, steps ratio, current), plus homing routine
            # — this runs automatically on power up.
            return self.send_command_string(b"/1s0m23l23h0j32n2f1v2500V5000Z100000R")
        elif FW == "FW2":
            # WHEEL 2
            # Initial drive settings (velocity, steps ratio, current), plus homing routine
            # — this runs automatically on power up.
            return self.send_command_string(b"/2s0m23l23h0j32n2f1v2500V5000Z100000R")
        self.logger.error("Received request to initialize unknown component {}".format(FW))


    def stored_filter_wheel_procedures(self):
        """
        FILTER WHEEL STORED PROCEDURES - These need to be sent to the motor controllers
        the first time they are used… i.e if you replace a motor controller you should
        reinitialize with these commands…
        """
        self.logger.warning("Re-initializing Filter Wheels.")
        self.logger.warning("This should only need to be done before first use or after replacing a controller.")

        self.logger.info("Initializing Wheel 1")
        self.logger.info("Initializing A1")
        result = self.send_command_string(b"/1s1n0A46667R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A2")
        result = self.send_command_string(b"/1s2n0A62222R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A3")
        result = self.send_command_string(b"/1s3n0A77778R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A4")
        result = self.send_command_string(b"/1s4n0A0R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A5")
        result = self.send_command_string(b"/1s5n0A15555R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A6")
        result = self.send_command_string(b"/1s6n0A31111R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing Wheel 2")
        self.logger.info("Initializing B1")
        result = self.send_command_string(b"/2s1n0A46667R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B2")
        result = self.send_command_string(b"/2s2n0A62222R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B3")
        result = self.send_command_string(b"/2s3n0A77778R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B4")
        result = self.send_command_string(b"/2s4n0A0R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B5")
        result = self.send_command_string(b"/2s5n0A15555R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B6")
        result = self.send_command_string(b"/2s6n0A31111R")
        self.logger.info("Result was {}".format(result))


    @motor_move(["filter", "grism"])
    def return_wheel_home(self, wheel):
        """
        Homing is automatic on power-up, or can be forced with the following commands.
        """
        self.logger.info("Returning {} to home position".format(wheel))
        if wheel == "FW1":
            return self.send_command_string(b"/1e0R")
        elif wheel == "FW2":
            return self.send_command_string(b"/2e0R")
        elif wheel == "GR_A":
            return self.send_command_string(b"/3e10R")
        elif wheel == "GR_B":
            return self.send_command_string(b"/4e10R")
        self.logger.error("Received command to home unknown component {}".format(wheel))


    @motor_move(["filter", "grism"])
    def go_to_step(self, wheel, step):
        self.logger.info("Commanding {} to {}".format(wheel, step))
        if wheel == "FW1":
            return self.send_command_string(bytearray("/1A{}R".format(step), "utf8"))
        elif wheel == "FW2":
            return self.send_command_string(bytearray("/2A{}R".format(step), "utf8"))
        elif wheel == "GR_A":
            return self.send_command_string(bytearray("/3A{}R".format(step), "utf8"))
        elif wheel == "GR_B":
            return self.send_command_string(bytearray("/4A{}R".format(step), "utf8"))
        self.logger.error("Received command to set unknown component {} to {}".format(wheel, step))


    def current_filter_step(self, wheel):
        self.logger.info("Getting step counts for {}".format(wheel))
        if wheel == "FW1":
            return self.send_command_string(b"/1?0")
        elif wheel == "FW2":
            return self.send_command_string(b"/2?0")
        elif wheel == "GR_A":
            return self.send_command_string(b"/3?0")
        elif wheel == "GR_B":
            return self.send_command_string(b"/4?0")
        self.logger.error("Received step count query for unknown component {}".format(wheel))


    def motors_stop(self, wheel):
        self.logger.info("Commanding motor stop for {}".format(wheel))
        if wheel == "FW1":
            return self.send_command_string(b"/1T")
        elif wheel == "FW2":
            return self.send_command_string(b"/2T")
        elif wheel == "GR_A":
            return self.send_command_string(b"/3T")
        elif wheel == "GR_B":
            return self.send_command_string(b"/4T")
        self.logger.error("Received motor stop command for unknown component {}".format(wheel))


    @motor_move(["filter"])
    def move_filter_wheel(self, position):
        self.logger.info("Commanding filter wheel move {}".format(position))
        if position in ["A1", "A2", "A3", "A4", "A5", "A6"]:
            return self._move_wheel(self.fw1_positions, self.fw1_commands, "FW1", position)
        elif position in ["B1", "B2", "B3", "B4", "B5", "B6"]:
            return self._move_wheel(self.fw2_positions, self.fw2_commands, "FW2", position)
        elif position.lower() in self.FILTER_WHEEL_MAPPINGS:
            results = []
            for item in self.FILTER_WHEEL_MAPPINGS[position.lower()]:
                results.append(self.move_filter_wheel(self.FILTER_WHEEL_MAPPINGS[item]))
            return results
        self.logger.error("Received filter move command to unknown position {}".format(position))


    def initialize_grism_rails(self):
        self.logger.warning("Initializing Grism Rails.")
        self.logger.warning("This should only need to be done on initial startup or after replacing a drive.")
        # Initialization settings for Grism Drives
        #
        # Notes:
        #   I set these already, and they only need to be programmed once. However, we
        # need to be able to send these commands in the event a drive is replaced.
        self.logger.info("Initializing Grism A")
        result = self.send_command_string(b"/3s0m23l23h0j4V7000v2500n2f1Z100000000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Initializing Grism B")
        result = self.send_command_string(b"/4s0m23l23h0j4V7000v2500n2f1Z100000000R")


    def stored_grism_rails_procedures(self):
        """
        GRISM RAIL STORED PROCEDURES - These need to be sent to the motor controllers
        the first time they are used… i.e if you replace a motor controller you should
        reinitialize with these commands…
        """
        self.logger.warning("Re-initializing Grism Rails.")
        self.logger.warning("This should only need to be done before first use or after replacing a controller.")
        self.logger.info("Storing Position 1 (A)")
        result = self.send_command_string(b"/3s1S12A69000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Position 1 (B)")
        result = self.send_command_string(b"/4s1S12A173000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Position 2 (A)")
        result = self.send_command_string(b"/3s2S12A103300R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Position 2 (B)")
        result = self.send_command_string(b"/4s2S12A207850R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Stowed Position (A)")
        result = self.send_command_string(b"/3s10A1000Z2000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Stowed Position (B)")
        result = self.send_command_string(b"/4s10A1000Z2000R")
        self.logger.info("Result was {}".format(result))


    def grism_sensor_status(self, grism):
        self.logger.info("Getting sensor status for {}".format(grism))
        if grism == "GR_A":
            return self.send_command_string(b"/3?4")
        if grism == "GR_B":
            return self.send_command_string(b"/4?4")
        self.logger.error("Received status request for unknown grism {}".format(grism))


    @motor_move(["grism"])
    def home_grism_rails(self, grism):
        self.logger.info("Returning grism {} to home".format(grism))
        if grism == "GR_A":
            return self.send_command_string(b"/3e0R")
        if grism == "GR_B":
            return self.send_command_string(b"/4e0R")
        self.logger.error("Received home command for unknown grism {}".format(grism))


    @motor_move(["grism"])
    def fast_home_grism_rails(self, grism):
        self.logger.info("Returning grism {} to home".format(grism))
        if grism == "GR_A":
            return self.send_command_string(b"/3e10R")
        if grism == "GR_B":
            return self.send_command_string(b"/4e10R")
        self.logger.error("Received home command for unknown grism {}".format(grism))


    @motor_move(["grism"])
    def move_grism_rails(self, position):
        """
        Grism will home automatically on power-up.
        
        Sled A must be home before sled B can move away from home.
        Sled B must be home before sled A can move away from home.
        """
        self.logger.info("Moving grism to {}".format(position))
        results = []
        if position in ["GR_H1", "GR_A1", "GR_A2"]:
            # Move Grism B to Home
            results.append(self._move_rail(self.grb_positions, self.grb_commands, "GRB", "GR_H2"))
            # Move Grism A to commanded location
            results.append(self._move_rail(self.gra_positions, self.gra_commands, "GRA", position))
            return results
        elif position in ["GR_H2", "GR_B1", "GR_B2"]:
            # Move Grism A to Home
            results.append(self._move_rail(self.gra_positions, self.gra_commands, "GRA", "GR_H1"))
            # Move Grism B to commanded location
            results.append(self._move_rail(self.grb_positions, self.grb_commands, "GRB", position))
            return results
        elif position.lower() in self.GRISM_RAIL_MAPPINGS:
            for item in self.GRISM_RAIL_MAPPINGS[position.lower()]:
                results.append(self.move_grism_rails(self.GRISM_RAIL_MAPPINGS[item]))
            return results
        self.logger.error("Received filter move command to unknown position {}".format(position))


    def current_grism_step(self, grism):
        self.logger.info("Getting step counts for {}".format(wheel))
        if wheel == "FW1":
            return self.send_command_string(b"/1?0")
        elif wheel == "FW2":
            return self.send_command_string(b"/2?0")
        elif wheel == "GR_A":
            return self.send_command_string(b"/3?0")
        elif wheel == "GR_B":
            return self.send_command_string(b"/4?0")
        self.logger.error("Received step count query for unknown component {}".format(wheel))


    def write_status(self):
        wheels = ['FW1', 'FW2', 'GR_A', 'GR_B']
        counts = []
        for wheel in wheels:
            counts.append(self.extract_steps_from_return_string(self.current_filter_step(wheel)))
        data = Table()
        data['wheel']= wheels
        data['counts']= counts
        ascii.write(data, get_data_file("motors", 'FW_GR_status.dat'), overwrite=True)


    def extract_sensorcode_from_return_string(self, bstring):
        decoded_string = str(bstring.decode())[3:]
        bits = bin(int(decoded_string)).lstrip('0b')
        return bits


    def extract_steps_from_return_string(self, bstring):
        return bstring[5:-1]   


    def _send(self, message):
        self.set_ip()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.IP_Host, self.IP_Port))
                s.sendall(message)
                data = s.recv(1024)
                return(data)
            except socket.error as e:
                self.logger.error("Socket Error {} when contacting motors".format(e))
                return None


    def _move_wheel(self, positions, commands, wheel, position):
        current_steps = self.extract_steps_from_return_string(self.current_filter_step(wheel))
        self.logger.info("Current {} position is {}".format(wheel, current_steps))
        while current_steps != str(positions[position]):
            response = self.send_command_string(commands[position])
            self.logger.info("PCM responded {} to move command".format(response))
            time.sleep(2)
            current_steps = self.extract_steps_from_return_string(self.current_filter_step(wheel))
        self.write_status()
        return position, current_steps


    def _move_rail(self, positions, commands, wheel, position):
        current_steps = self.extract_steps_from_return_string(self.current_grism_step(wheel))
        self.logger.info("Current {} position is {}".format(wheel, current_steps))
        while current_steps != str(positions[position]):
            response = self.send_command_string(commands[position])
            self.logger.info("PCM responded {} to move command".format(response))
            time.sleep(2)
            current_steps = self.extract_steps_from_return_string(self.current_grism_step(wheel))
        self.write_status()
        return position, current_steps


    FILTER_WHEEL_MAPPINGS = {
        "sloan-g": ("A1", "B3"),
        "sloan-r": ("A2", "B3"),
        "sloan-i": ("A3", "B3"),
        "open": ("A4", "B4"),
        "sloan-z": ("A5", "B3"),
        "blank": ("A6", "B3"),
        "halpha": ("A4", "B1"),
        "oiii": ("A4", "B2"),
        # "open": ("A4", "B3"),
        "glass": ("A4", "B4"),
        "hbeta": ("A4", "B5"),
        "sii": ("A4", "B6")
    }
