#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 20:49:49 2023

# According to SAMI User Manual:

The SAMI data acquisition software runs on the soarhrc computer (IP 139.229.15.163). It is 
accessed by VNC connection to soarhrc:9. To launch the SAMI GUI, use the icon in the 
desktop menu in the lower-right corner.

# INFOA

(Taken from the SOAR_TCS_COMMANDS document.)
TCS command 'INFOA' returns a string of variables with the current telescope settings, 
which will go into the FITS header. The returned variables are:

- Date, 
- Universal Time, 
- Right ascention, 
- Declination, 
- Hour Angle, 
- Telescope Azimuth, 
- Telescope Elevation, 
- Sidereal Time, 
- Parallactic Angle, 
- MJD, 
- Telescope Focus, 
- Airmass, 
- IPA, 
- Rotator Position, 
- IROT, 
- M3 Position, 
- Outside Temperature, 
- Humidity, 
- Pressure, 
- Wind Direction, 
- Wind Speed, 
- Inside Temperature, 
- ECS Time Stamp, 
- Dimm Seeing
- Dome, 
- Azimuth, 
- Shutter Elevation, 
- Guider Star ID
- Guider X Position, 
- Guider Y Position, 
- Comparison Lamp Mirror, 
- Lamp 1 State (on/off), 
- Lamp 1 Tag (Lamp name),
- Lamp 2 State, 
- Lamp 2 Tag, 
- Lamp 3 State, 
- Lamp 3 Tag,
- Lamp 4 State, 
- Lamp 4 Tag, 
- Lamp 5 State, 
- Lamp 5 Tag,
- Lamp 6 State, 
- Lamp 6 Tag, 
- Lamp 7 State, 
- Lamp 7 Tag,
- Lamp 8 State, 
- Lamp 8 Tag, 
- Lamp 9 State, 
- Lamp 9 Tag,
- Lamp 10 State, 
- Lamp 10 Tag

The ouput is formatted as a string of whitespace-separated variables, e.g., 
'DONE TCS_DATE=2019-06-26 LAMP_1=OFF TAG_1=Hg(Ar)...'

@author: robberto
"""
import numpy as np
import os
from pathlib import Path
import socket
import sys


class Class_SOAR:
    def __init__(self, par):
        socket.setdefaulttimeout(3)
        self.PAR = par
        self.is_on = False


    def set_ip(self):
        try:
            items = self.PAR.IP_dict['IP_SOAR'].split(":")
            self.SOAR_TCS_IP = items[0]
            self.SOAR_TCS_PORT = int(items[1])
        except IndexError as e:
            # Probably means this isn't a valid IP address. Set to loopback.
            self.SOAR_TCS_IP = "127.0.0.1"
            self.SOAR_TCS_PORT = 9898


    def echo_client(self):
        self.set_ip()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.SOAR_TCS_IP, self.SOAR_TCS_PORT))
                s.sendall(b"INFOA\n")
                data = s.recv(1024)
                self.is_on = True
                return(data)
            except socket.error:
                self.is_on = False
                return("no connection")
            finally:
                s.close()    


    def send_to_TCS(self, command):
        self.set_ip()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.SOAR_TCS_IP, self.SOAR_TCS_PORT))
                s.sendall(f"{command}\n".encode("ascii"))
                response = s.recv(1024)
                return response
            except socket.error:
                return("no connection")
            finally:
                s.close()


    def way(self):
        return self.send_to_TCS("WAY")


    def offset(self, param, offset="E 0.0 N 0.0"):
        if param == "MOVE":
            command = "OFFSET MOVE {}".format(offset)
        if param == "STATUS":
            command = "OFFSET STATUS"
        return self.send_to_TCS(command)  


    def focus(self, param, offset="E 0.0 N  0.0"):
        if param == "MOVEABS":
            command = "FOCUS MOVEABS {}".format(offset)
        if param == "MOVEREL":
            command = "FOCUS MOVEREL {}".format(offset)
        if param == "STATUS":
            command = "FOCUS STATUS"
        return self.send_to_TCS(command)


    def clm(self, param):
        if param == "IN":
            command = "CLM IN"
        if param == "OUT":
            command = "CLM OUT"
        if param == "STATUS":
            command = "CLM STATUS"
        return self.send_to_TCS(command)  


    def guider(self, param):
        if param == "DISABLE":
            command = "GUIDER DISABLE "
        if param == "ENABLE":
            command = "GUIDER ENABLE "
        if param == "STATUS":
            command = "GUIDER STATUS"
        return self.send_to_TCS(command)  


    def whitespot(self, param, percentage):
        if param == "ON":
            command = "WHITESPOT ON {}".format(percentage)
        if param == "OFF":
            command = "WHITESPOT OFF"
        if param == "STATUS":
            command = "WHITESPOT STATUS"
        return self.send_to_TCS(command)  


    def lamp_id(self, param, location):
        if param == "ON":
            command = "LAMP ON {}".format(location)
        if param == "OFF":
            command = "LAMP OFF"
        if param == "STATUS":
            command = "LAMP STATUS"
        return self.send_to_TCS(command)  


    def adc(self, param, percent):
        if param == "MOVE":
            command = "ADC MOVE {}".format(percent)
        if param == "IN":
            command = "ADC IN"
        if param == "PARK":
            command = "ADC PARK"
        if param == "TRACK":
            command = "ADC TRACK"
        if param == "STATUS":
            command = "ADC STATUS"
        return self.send_to_TCS(command)  


    def info_whatever(self, message):
        return self.send_to_TCS(message)


    def target(self, param, radec="RA=00:00:00.00 DEC=00:00:00:00 EPOCH=2000.0"):
        if param == "MOVE":
            command = "TARGET MOVE {}".format(radec)
        if param == "MOUNT":
            command = "TARGET MOUNT"
        if param == "STOP":
            command = "TARGET STOP"
        if param == "STATUS":
            command = "TARGET STATUS"
        return self.send_to_TCS(command)  
        
    def ipa(self, param, angle="00.0"):
        if param == "MOVE":
            command = "IPA MOVE {}".format(angle)
        if param == "STATUS":
            command = "IPA STATUS"
        return self.send_to_TCS(command)   

    def instrument(self, param, instrument="GOODMAN"):
        if param == "MOVE":
            command = "INSTRUMENT MOVE {}".format(instrument)
        if param == "STATUS":
            command = "INSTRUMENT STATUS"
        return self.send_to_TCS(command)   
