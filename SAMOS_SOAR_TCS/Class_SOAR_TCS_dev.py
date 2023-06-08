#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 20:49:49 2023

@author: robberto
"""
import sys, os
import numpy as np

from pathlib import Path
#define the local directory, absolute so it is not messed up when this is called
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
sys.path.append(os.path.join(path.parent,'SAMOS_system_dev'))
from SAMOS_Functions import Class_SAMOS_Functions as SF

class SOAR_TCS:
    def __init__(self):
        all_IPs = SF.read_IP_default()
       
        """ switch when the correct IP and PORT are insterted"""
        # self.SOAR_TCS_IP = all_IPs['IP_SOAR'][0:i_columns]
        # self.SOAR_TCS_port = int(all_IPs['IP_SOAR'][i_columns+1:])
        # self.params = {'Host': self.SOAR_TCS_IP, 'Port': self.SOAR_TCS_port}
        self.params = {'Host': 0, 'Port': 0}


    
    def send_to_TCS(self,command):
        import socket
        socket.setdefaulttimeout(3)

        HOST = self.SOAR_TCS_IP   #self.params['Host']
        PORT = self.SOAR_TCS_port #self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((HOST, PORT))
                msg = command.encode('ascii')  #need to append "\n" at the end? 
                #s.sendall(msg)
                
                """ Coding the message to LabView
                From: https://forums.ni.com/t5/LabVIEW/TCP-to-Python-Encoding/td-p/4042297"""
                #msg = b"Hello, Python!" #<<<< using Byte array not native string
                length = np.ascontiguousarray(len(msg),dtype='>i4').tobytes()
                s.sendall(length+msg) 

                
                """Receiving and decoding the message fromm LabView
                From: https://forums.ni.com/t5/LabVIEW/TCP-to-Python-Encoding/td-p/4042297"""
                messagelen = s.recv(4)
                length = np.frombuffer(messagelen,dtype='>i4')[0]
                msg = s.recv(length)

                return msg
            except socket.error:
                return("no connection")
            finally:
                s.close()
    
    def way(self):
        return_string = self.send_to_TCS("WAY")  
    
    def offset(self,param,offset="E 0.0 N  0.0"):
        if param == "MOVE":
            command = "OFFSET MOVE " + offset
        if param == "STATUS":
            command = "OFFSET STATUS"
        return_string = self.send_to_TCS(command)  

    def clm(self,param):
        if param == "IN":
            command = "CLM IN "
        if param == "OUT":
            command = "CLM OUT "
        if param == "STATUS":
            command = "CLM STATUS"
        return_string = self.send_to_TCS(command)  
        
    def guider(self,param):
        if param == "DISABLE":
            command = "GUIDER DISABLE "
        if param == "ENABLE":
            command = "GUIDER ENABKE "
        if param == "STATUS":
            command = "GUIDER STATUS"
        return_string = self.send_to_TCS(command)  
        
    def whitespot(self,param):
        if param == "ON":
            command = "WHITESPOT ON "
        if param == "OFF":
            command = "WHITESPOT OFF "
        if param == "STATUS":
            command = "WHITESPOT STATUS"
        return_string = self.send_to_TCS(command)  
        
    def lamp(self,param):
        if param == "ON":
            command = "LAMP ON "
        if param == "OFF":
            command = "LAMP OFF "
        if param == "STATUS":
            command = "LAMP STATUS"
        return_string = self.send_to_TCS(command)  
        
    def adc(self,param):
        if param == "MOVE":
            command = "ADC MOVE "
        if param == "IN":
            command = "ADC IN "
        if param == "TRACK":
            command = "ADC TRACK "
        if param == "STATUS":
            command = "ADC STATUS"
        return_string = self.send_to_TCS(command)  

    def info(self):
        command = "INFO"
        return_string = self.send_to_TCS(command)  

    def infox(self):
        command = "INFOX"
        return_string = self.send_to_TCS(command)  
        
    def target(self,param,RADEC="RA=00:00:00.00 DEC=00:00:00:00 EPOCH=2000.0"):
        if param == "MOVE":
            command = "TARGET MOVE " + RADEC
        if param == "MOUNT":
            command = "TARGET MOUNT "
        if param == "STOP":
            command = "TARGET STOP "
        if param == "STATUS":
            command = "TARGET STATUS"
        return_string = self.send_to_TCS(command)  
        
    def ipa(self,param,ANGLE="00.0"):
        if param == "MOVE":
            command = "IPA MOVE " + ANGLE
        if param == "STATUS":
            command = "IPA STATUS"
        return_string = self.send_to_TCS(command)  

    def ginfo(self):
        command = "GINFO"
        return_string = self.send_to_TCS(command)  

    def sinfo(self):
        command = "SINFO"
        return_string = self.send_to_TCS(command)  

    def rotpos(self):
        command = "ROTPOS"
        return_string = self.send_to_TCS(command)  

    def infoa(self):
        command = "INFOA"
        return_string = self.send_to_TCS(command)  
        
        """
        (Taken from the SOAR_TCS_COMMANDS document.)
        TCS command 'INFOA' returns a string of variables with the
        current telescope settings, which will go into the FITS header.  
        The returned variables are:
            Date, Universal Time, Right ascention, 
            Declination, Hour Angle, Telescope Azimuth, 
            Telescope Elevation, Sidereal Time, 
            Parallactic Angle, MJD, Telescope Focus, 
            Airmass, IPA, Rotator Position, IROT, 
            M3 Position, Outside Temperature, Humidity, 
            Pressure, Wind Direction, Wind Speed, 
            Inside Temperature, ECS Time Stamp, Dimm Seeing
            Dome, Azimuth, Shutter Elevation, Guider Star ID
            Guider X Position, Guider Y Position, 
            Comparison Lamp Mirror, 
            Lamp 1 State (on/off), Lamp 1 Tag (Lamp name),
            Lamp 2 State, Lamp 2 Tag, Lamp 3 State, Lamp 3 Tag,
            Lamp 4 State, Lamp 4 Tag, Lamp 5 State, Lamp 5 Tag,
            Lamp 6 State, Lamp 6 Tag, Lamp 7 State, Lamp 7 Tag,
            Lamp 8 State, Lamp 8 Tag, Lamp 9 State, Lamp 9 Tag,
            Lamp 10 State, Lamp 10 Tag
            
        The ouput is formatted as a string of whitespace-separated variables,
        e.g., 'DONE TCS_DATE=2019-06-26 LAMP_1=OFF TAG_1=Hg(Ar)...'
        
        """
        
        TCS_dict = {}
        # Get the keyword/value pairs from the return string
        # and put into dictionary.  Dictionary can then be
        # added onto the FITS header dictionary.
        for var in return_string.strip("DONE ").split(" "):
            
            key,val = var.split("=")
            TCS_dict[key] = val
        
        return TCS_dict
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        