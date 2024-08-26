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

from samos.ui.progress_windows import MotorMoveProgressWindow
from samos.utilities import get_data_file
from samos.utilities.constants import *


class PCM():
    def __init__(self, par, logger, fits_head, canvas_Indicator=None):
        self.PAR = par
        self.logger = logger
        self.main_fits_head = fits_head
        self.set_ip()
        self.initialized = False
        self.positions = {"FW1": {}, "FW2": {}, "GR_A": {}, "GR_B": {}}
        self.home = {}
        self.got_stop = False
        self.filter_moving = False
        self.grism_moving = False
        self.have_initial_status = False

        # Configure socket wait
        socket.setdefaulttimeout(3)
        
        # reference to indicator lights in main GUI
        self.canvas_Indicator = canvas_Indicator

        data = ascii.read(get_data_file("motors", 'IDG_Filter_positions.txt'))
        for i, name in enumerate(["A1", "A2", "A3", "A4", "A5", "A6"]):
            self.positions["FW1"][name] = data['Counts'][i]
        for i, name in enumerate(["B1", "B2", "B3", "B4", "B5", "B6"]):
            self.positions["FW2"][name] = data['Counts'][i+6]
        self.positions["GR_A"]["GR_H1"] = data['Counts'][12]
        self.positions["GR_A"]["GR_A1"] = data['Counts'][14]
        self.positions["GR_A"]["GR_A2"] = data['Counts'][16]
        self.positions["GR_B"]["GR_H2"] = data['Counts'][13]
        self.positions["GR_B"]["GR_B1"] = data['Counts'][15]
        self.positions["GR_B"]["GR_B2"] = data['Counts'][17]
        self.home["FW1"] = self.positions["FW1"]["A4"]
        self.home["FW2"] = self.positions["FW2"]["B4"]
        self.home["GR_A"] = self.positions["GR_A"]["GR_H1"]
        self.home["GR_B"] = self.positions["GR_B"]["GR_H2"]


    def initialize_motors(self):
        self.set_ip()
        self.initialized = True


    @property
    def is_on(self):
        if not self.initialized:
            return False
        return self.check_if_power_is_on()


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
        reply = self._send(self.PCM_COMMANDS["power_status"])
        self.reset_indicator(["filter", "grism"])
        if reply is not None:
            if "NO RESPONSE" in reply:
                self.logger.info("Motor power is off")
                return False
            if not self.have_initial_status:
                self.have_initial_status = True
                for wheel in ['FW1', 'FW2', 'GR_A', 'GR_B']:
                    reply = self.current_filter_step(wheel)
            self.logger.info("Motors replied {}".format(reply))
            return True
        self.logger.warning("No reply from Motors")
        return False


    def echo_client(self):
        self.logger.info("Sending PCM echo")
        return self._send(self.PCM_COMMANDS["on"])


    def power_on(self):
        self.logger.info("Sending PCM power on signal")
        result = self._send(self.PCM_COMMANDS["on"])
        self.reset_indicator(["filter", "grism"])
        return result


    def power_off(self):
        self.logger.info("Sending PCM power off signal")
        result = self._send(self.PCM_COMMANDS["off"])
        self.reset_indicator(["filter", "grism"])
        return result


    def send_command_string(self, string):
        self.logger.info("Sending PCM command string {}".format(string))
        return self._send(f"{self.PCM_COMMANDS['preamble']}{string}")


    def filter_sensor_status(self, FW):
        self.logger.info("Getting status from {}".format(FW))
        return self.send_command_string[self.PCM_COMMANDS["current_step"][FW]]


    def all_ports_status(self):
        self.logger.info("Getting status of all power ports")
        return self._send(self.PCM_COMMANDS["power_status"])


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
            return self.send_command_string("/1s0m23l23h0j32n2f1v2500V5000Z100000R")
        elif FW == "FW2":
            # WHEEL 2
            # Initial drive settings (velocity, steps ratio, current), plus homing routine
            # — this runs automatically on power up.
            return self.send_command_string("/2s0m23l23h0j32n2f1v2500V5000Z100000R")
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
        result = self.send_command_string("/1s1n0A46667R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A2")
        result = self.send_command_string("/1s2n0A62222R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A3")
        result = self.send_command_string("/1s3n0A77778R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A4")
        result = self.send_command_string("/1s4n0A0R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A5")
        result = self.send_command_string("/1s5n0A15555R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing A6")
        result = self.send_command_string("/1s6n0A31111R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing Wheel 2")
        self.logger.info("Initializing B1")
        result = self.send_command_string("/2s1n0A46667R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B2")
        result = self.send_command_string("/2s2n0A62222R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B3")
        result = self.send_command_string("/2s3n0A77778R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B4")
        result = self.send_command_string("/2s4n0A0R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B5")
        result = self.send_command_string("/2s5n0A15555R")
        self.logger.info("Result was {}".format(result))

        self.logger.info("Initializing B6")
        result = self.send_command_string("/2s6n0A31111R")
        self.logger.info("Result was {}".format(result))


    def return_wheel_home(self, wheel):
        """
        Homing is automatic on power-up, or can be forced with the following commands.
        """
        self.logger.info("Returning {} to home position".format(wheel))
        motor_window = MotorMoveProgressWindow(self, self.logger, wheel, self.home[wheel])
        result = self.send_command_string(self.PCM_COMMANDS["home"][wheel])
        motor_window.wait_window()
        self.got_stop = False
        return result


    def go_to_step(self, wheel, step):
        self.logger.info("Commanding {} to {}".format(wheel, step))
        motor_window = MotorMoveProgressWindow(self, self.logger, wheel, step)
        result = self.send_command_string(self.PCM_COMMANDS["go_step"][wheel].format(step))
        motor_window.wait_window()
        self.got_stop = False
        return result


    def current_filter_step(self, wheel):
        self.logger.info("Getting step counts for {}".format(wheel))
        result = self.send_command_string(self.PCM_COMMANDS["current_step"][wheel])
        param_name = f"{wheel.replace('_','').lower()}step"
        try:
            step = self.extract_steps_from_return_string(result)
        except Exception as e:
            self.logger.error(f"Trying to extract filter steps from {result} caused {e}")
            step = "UNKNOWN"
        self.main_fits_head.set_param(param_name, step)
        return result


    def motors_stop(self, wheel):
        self.logger.info("Commanding motor stop for {}".format(wheel))
        self.got_stop = True
        self.reset_indicator(["filter", "grism"])
        return self.send_command_string(self.PCM_COMMANDS["stop"][wheel])


    def move_filter_wheel(self, position):
        self.logger.info("Commanding filter wheel move {}".format(position))
        results = []
        if position in ["A1", "A2", "A3", "A4", "A5", "A6"]:
            results.append(self._move_wheel(self.positions, self.PCM_COMMANDS["move"], "FW1", position))
        elif position in ["B1", "B2", "B3", "B4", "B5", "B6"]:
            results.append(self._move_wheel(self.positions, self.PCM_COMMANDS["move"], "FW2", position))
        elif position.lower() in self.FILTER_WHEEL_MAPPINGS:
            results = []
            for item in self.FILTER_WHEEL_MAPPINGS[position.lower()]:
                if not self.got_stop:
                    results.append(self.move_filter_wheel(item))
                else:
                    results.append("STOP COMMAND RECEIVED")
        self.got_stop = False
        return results


    def initialize_grism_rails(self):
        self.logger.warning("Initializing Grism Rails.")
        self.logger.warning("This should only need to be done on initial startup or after replacing a drive.")
        # Initialization settings for Grism Drives
        #
        # Notes:
        #   I set these already, and they only need to be programmed once. However, we
        # need to be able to send these commands in the event a drive is replaced.
        self.logger.info("Initializing Grism A")
        result = self.send_command_string("/3s0m23l23h0j4V7000v2500n2f1Z100000000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Initializing Grism B")
        result = self.send_command_string("/4s0m23l23h0j4V7000v2500n2f1Z100000000R")


    def stored_grism_rails_procedures(self):
        """
        GRISM RAIL STORED PROCEDURES - These need to be sent to the motor controllers
        the first time they are used… i.e if you replace a motor controller you should
        reinitialize with these commands…
        """
        self.logger.warning("Re-initializing Grism Rails.")
        self.logger.warning("This should only need to be done before first use or after replacing a controller.")
        self.logger.info("Storing Position 1 (A)")
        result = self.send_command_string("/3s1S12A69000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Position 1 (B)")
        result = self.send_command_string("/4s1S12A173000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Position 2 (A)")
        result = self.send_command_string("/3s2S12A103300R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Position 2 (B)")
        result = self.send_command_string("/4s2S12A207850R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Stowed Position (A)")
        result = self.send_command_string("/3s10A1000Z2000R")
        self.logger.info("Result was {}".format(result))
        self.logger.info("Storing Stowed Position (B)")
        result = self.send_command_string("/4s10A1000Z2000R")
        self.logger.info("Result was {}".format(result))


    def grism_sensor_status(self, grism):
        self.logger.info("Getting sensor status for {}".format(grism))
        return self.send_command_string(self.PCM_COMMANDS["status"][grism])


    def home_grism_rails(self, grism):
        self.logger.info("Returning grism {} to home".format(grism))
        motor_window = MotorMoveProgressWindow(self, self.logger, wheel, self.home[wheel])
        result = self.send_command_string(self.PCM_COMMANDS["home"][grism])
        motor_window.wait_window()
        self.got_stop = False
        return result


    def fast_home_grism_rails(self, grism):
        self.logger.info("Returning grism {} to home".format(grism))
        motor_window = MotorMoveProgressWindow(self, self.logger, wheel, self.home[wheel])
        result = self.send_command_string(self.PCM_COMMANDS["fast_home"][grism])
        motor_window.wait_window()
        self.got_stop = False
        return result


    def move_grism_rails(self, position):
        """
        Grism will home automatically on power-up.
        
        Sled A must be home before sled B can move away from home.
        Sled B must be home before sled A can move away from home.
        """
        self.logger.info("Moving grism to {}".format(position))
        results = []
        if position in ["GR_H1", "GR_A1", "GR_A2"]:
            # Moving grism A away from home. Must home grism B
            if self.get_wheel_position("GR_B") != self.home["GR_B"]:
                if not self.got_stop:
                    self.logger.info("Moving grism B home.")
                    results.append(self._move_wheel(self.positions, self.PCM_COMMANDS["move"], "GR_B", "GR_H2"))
            # Move Grism A to position
            if not self.got_stop:
                self.logger.info(f"Moving grism A to {position}")
                results.append(self._move_wheel(self.positions, self.PCM_COMMANDS["move"], "GR_A", position))
        elif position in ["GR_H2", "GR_B1", "GR_B2"]:
            # Moving grism B away from home. Must home grism A
            if self.get_wheel_position("GR_A") != self.home["GR_A"]:
                if not self.got_stop:
                    self.logger.info("Moving grism A home.")
                    results.append(self._move_wheel(self.positions, self.PCM_COMMANDS["move"], "GR_A", "GR_H1"))
            # Move Grism B to position
            if not self.got_stop:
                self.logger.info(f"Moving grism B to {position}")
                results.append(self._move_wheel(self.positions, self.PCM_COMMANDS["move"], "GR_B", position))
        elif position.lower() in self.GRISM_RAIL_MAPPINGS:
            pos_a, pos_b = self.GRISM_RAIL_MAPPINGS[position.lower()]
            if pos_a != "GR_H1":
                # Treat as a grism A move
                results = self.move_grism_rails(pos_a)
            elif pos_b != "GR_H2":
                # Treat as a grism b move
                results = self.move_grism_rails(pos_b)
            else:
                # Both home. Treat as grism A
                results = seulf.move_grism_rails(pos_a)
        if self.got_stop:
            results.append("GOT STOP COMMAND")
            self.got_stop = False
        return results


    def current_grism_step(self, grism):
        self.logger.info("Getting step counts for {}".format(wheel))
        return self.send_command_string(self.PCM_COMMANDS["current_step"][grism])


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


    def start_move(self, wheel_types):
        if "filter" in wheel_types:
            self.filter_moving = True
        if "grism" in wheel_types:
            self.grism_moving = True


    def reset_indicator(self, wheel_types):
        if "filter" in wheel_types:
            self.filter_moving = False
        if "grism" in wheel_types:
            self.grism_moving = False


    def get_wheel_position(self, wheel, tolerance=5):
        """
        Return the position of the given wheel, by comparing the current step to the 
        defined positions (with a hit being defined as within the provided step 
        tolerance).
        """
        current_step = self.extract_steps_from_return_string(self.current_filter_step(wheel))
        try:
            current_step = int(current_step)
        except Exception as e:
            self.logger.error(f"Invalid {wheel} step value {current_step}")
            return "INVALID"

        for position in self.positions[wheel]:
            if abs(current_step - self.positions[wheel][position]) <= tolerance:
                self.logger.info(f"{wheel} step {current_step} corresponds to {position} ({self.positions[wheel][position]})")
                return position
        self.logger.warning(f"Current {wheel} position {current_step} has no known mapping.")
        return "UNKNOWN"


    def get_filter_label(self, tolerance=5):
        """
        Get the label assigned to the current pair of filter wheel positions (or UNKNOWN)
        """
        f1_pos = self.get_wheel_position("FW1", tolerance)
        f2_pos = self.get_wheel_position("FW2", tolerance)
        combined_pos = (f1_pos, f2_pos)
        self.logger.info(f"FW1 reports {f1_pos}, FW2 reports {f2_pos}")
        for mapping in self.FILTER_WHEEL_MAPPINGS:
            if combined_pos == self.FILTER_WHEEL_MAPPINGS[mapping]:
                self.logger.info(f"{f1_pos},{f2_pos} corresponds to {mapping}")
                return mapping
        return "UNKNOWN"


    def get_grating_label(self, tolerance=5):
        """
        Get the label assigned to the current pair of grating rail positions (or UNKNOWN)
        """
        ga_pos = self.get_wheel_position("GR_A", tolerance)
        gb_pos = self.get_wheel_position("GR_B", tolerance)
        combined_pos = (ga_pos, gb_pos)
        self.logger.info(f"GR_A reports {ga_pos}, GR_B reports {gb_pos}")
        for mapping in self.GRISM_RAIL_MAPPINGS:
            if combined_pos == self.GRISM_RAIL_MAPPINGS[mapping]:
                self.logger.info(f"{ga_pos},{gb_pos} corresponds to {mapping}")
                return mapping
        return "UNKNOWN"


    def _send(self, message):
        self.set_ip()
        text = None
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((self.IP_Host, self.IP_Port))
            s.sendall(bytearray(f"{message}\n", "utf-8"))
            data = s.recv(1024)
            text = data.decode("utf-8").strip()
        except socket.error as e:
            self.logger.error("Socket Error {} when contacting motors".format(e))
        finally:
            s.close()
        return text


    def _move_wheel(self, positions, commands, wheel, position):
        current_steps = self.extract_steps_from_return_string(self.current_filter_step(wheel))
        self.logger.info("Current {} position is {}".format(wheel, current_steps))
        if current_steps != positions[wheel][position]:
            motor_window = MotorMoveProgressWindow(self, self.logger, wheel, positions[wheel][position])
            response = self.send_command_string(commands[position])
            self.logger.info("PCM responded {} to move command".format(response))
            motor_window.wait_window()
        else:
            self.logger.info(f"{wheel} already at {position}")
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
    
    GRISM_RAIL_MAPPINGS = {
        "grating home": ("GR_H1", "GR_H2"),
        "low-red": ("GR_A1", "GR_H2"),
        "low-blue": ("GR_A2", "GR_H2"),
        "h-beta": ("GR_H1", "GR_B1"),
        "h-alpha": ("GR_H1", "GR_B2")
    }
    
    PCM_COMMANDS = {
        "preamble": "~@,9600_8N1T2000,",
        "on": '~se,all,on',
        "off": '~se,all,off',
        "power_status": "~ge,all",
        "move": {
            "A1": "1e1R",
            "A2": "1e2R",
            "A3": "1e3R",
            "A4": "1e4R",
            "A5": "1e5R",
            "A6": "1e6R",
            "B1": "2e1R",
            "B2": "2e2R",
            "B3": "2e3R",
            "B4": "2e4R",
            "B5": "2e5R",
            "B6": "2e6R",
            "GR_H1": "3e0R",
            "GR_A1": "3e1R",
            "GR_A2": "3e2R",
            "GR_H2": "4e0R",
            "GR_B1": "4e1R",
            "GR_B2": "4e2R",
            "template": r"(\d)e(\d)R",
        },
        "home": {
            "FW1": "/1e0R",
            "FW2": "/2e0R",
            "GR_A": "/3e0R",
            "GR_B": "/4e0R",
            "template": r"/(\d)e0R",
        },
        "fast_home": {
            "GR_A": "/3e10R",
            "GR_B": "/4e10R",
            "template": r"/(\d)e10R",
        },
        "go_step": {
            "FW1": "/1A{}R",
            "FW2": "/2A{}R",
            "GR_A": "/3A{}R",
            "GR_B": "/4A{}R",
            "template": r"/(\d)A(\d+)R",
        },
        "current_step": {
            "FW1": "/1?0",
            "FW2": "/2?0",
            "GR_A": "/3?0",
            "GR_B": "/4?0",
            "template": r"/(\d)\?0",
        },
        "stop": {
            "FW1": "/1T",
            "FW2": "/2T",
            "GR_A": "/3T",
            "GR_B": "/4T",
            "template": r"/(\d)T",
        },
        "status": {
            "GR_A": "/3?4",
            "GR_B": "/4?4",
            "template": r"/(\d)\?4",
        },
    }
