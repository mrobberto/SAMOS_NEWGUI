#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on May 3, 2024

# Based on the SAMI/FP Manual

This code is based on taking the commands that are available through the SAMI-FP scripting
reference and, in particular, replicating the commands available through the `sendsockcmd`
interface via direct TCP/IP connections. As I understand it, this is how things work:

* On [some computer] at SOAR is the SAMI GUI. As far as I know, the GUI itself can't be
  controlled remotely.
* This GUI includes a SAMI-FP plug-in. When that plug-in is started, it creates a socket
  server on [some computer] on a port defined in the plug-in (called "service port") in
  the plug-in interface. It also opens its *own* connection to the computer that is 
  actually connected to the FP, and uses that to command the FP in an undocumented way.
* The `sendsockcmd` command, or the `sami` shell script, or any interface that we write,
  communicates with the web server that was set up by the SAMI-FP GUI plug-in, sends 
  commands to it, and waits for a response. The response is going to be either DONE, ERROR,
  the requested information (e.g. from reading the FP position), and some sort of optional
  message.
"""
import numpy as np
import os
from pathlib import Path
import socket
import sys


class SAMI:
    def __init__(self, par, logger):
        self.PAR = par
        self.logger = logger
        self.connected = False
        self.default_timeout = 40000


    def set_ip(self):
        try:
            items = self.PAR.IP_dict['IP_SAMI'].split(":")
            self.SAMI_IP = items[0]
            self.SAMI_PORT = int(items[1])
        except IndexError as e:
            self.logger.error(f"Error {e} when trying to set IP to {self.PAR.IP_dict['IP_SAMI']}")
            self.logger.error(f"Falling back to using localhost:8888")
            # Probably means this isn't a valid IP address. Set to loopback.
            self.SAMI_IP = "127.0.0.1"
            self.SAMI_PORT = 8888


    def echo_client(self):
        if self._send("get currpos") != "CONNECTION FAILURE":
            self.connected = True


    def move(self, move_type, move_value):
        self.logger.info(f"Moving {move_type} by {move_value}")
        if move_type == "absolute":
            return self._send(f"fp moveabs {move_value}")
        elif move_type == "relative":
            return self._send(f"fp moveoff {move_value}")


    def dhe(self, parameter, value):
        self.logger.info(f"Setting DHE {parameter} to {value}")
        return self._send(f"dhe set {parameter} {value}")


    def expose(self):
        self.logger.info("Starting Exposure")
        return self._send("dhe expose")


    def _send(self, message, timeout=None):
        self.set_ip()
        reply = "CONNECTION FAILURE"
        sami_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if timeout is None:
            timeout = self.default_timeout
        try:
            sami_socket = socket.create_connection((self.SAMI_IP, self.SAMI_PORT), timeout=timeout)
            sami_socket.sendall(f"{message}\n".encode('ascii'))
            response = sami_socket.recv(2048)
            reply = response.decode('utf-8').strip()
            self.connected = True
        except socket.error as e:
            self.connected = False
            self.logger.error(f"Connection Failure {e}")
        finally:
            sami_socket.close()
            return reply
