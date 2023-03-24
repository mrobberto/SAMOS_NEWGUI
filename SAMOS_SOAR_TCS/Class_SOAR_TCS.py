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
        """ This will need to be finalized once we are in the SOAR network"""
        all_IPs = SF.read_IP_default()
        i_columns=all_IPs['IP_SOAR'].find(':')        
        self.SOAR_TCS_IP = all_IPs['IP_SOAR'][0:i_columns]
        self.SOAR_TCS_port = int(all_IPs['IP_SOAR'][i_columns+1:])
        self.params = {'Host': self.SOAR_TCS_IP, 'Port': self.SOAR_TCS_port}
        
        
        
    
    def send_to_TCS(self,command):
        import socket
        socket.setdefaulttimeout(3)

        HOST = self.SOAR_TCS_IP   #self.params['Host']
        PORT = self.SOAR_TCS_port #self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((HOST, PORT))
                msg = command.encode('ascii')  #need to append "\n" at the end? 
                
                """Coding the message to LabView
                From: https://forums.ni.com/t5/LabVIEW/TCP-to-Python-Encoding/td-p/4042297"""
                #test
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
        """(Who are you?) This command returns an identification string."""
        command = "WAY"
        return_string = self.send_to_TCS(command)
    
    def offset(self,param,offset="E 0.0 N  0.0"):
        """This command send an offset motion request to the TCS. The offset is given in units of arcseconds, 
        and must be preceded by one of the direction characters N, S, E and W."""
        if param == "MOVE":
            command = "OFFSET MOVE " + offset
        if param == "STATUS":
            command = "OFFSET STATUS"
        return_string = self.send_to_TCS(command)  
        
    def focus(self,param,value=0.0):
        """This command requests actions to the focus mechanism associated with the secondary mirror (M2)."""
        if param == "MOVEABS":
            command = "FOCUS MOVABS " + str(value)
        if param == "MOVEREL":
            command = "FOCUS MOVEREL" + str(value)
        if param == "STATUS":
            command = "FOCUS STATUS"
            
        return_string = self.send_to_TCS(command)  
    

    def clm(self,param):
        """This command requests actions to the comparison lamps mirror mechanism."""
        if param == "IN":
            command = "CLM IN "
        if param == "OUT":
            command = "CLM OUT "
        if param == "STATUS":
            command = "CLM STATUS"
        return_string = self.send_to_TCS(command)  
        
    def guider(self,param):
        """This command enable or disable the guider device."""
        if param == "DISABLE":
            command = "GUIDER DISABLE "
        if param == "ENABLE":
            command = "GUIDER ENABKE "
        if param == "STATUS":
            command = "GUIDER STATUS"
        return_string = self.send_to_TCS(command)  
        
    def whitespot(self,param):
        """his command requests actions to the lamps associated with the white spot."""
        if param == "ON":
            command = "WHITESPOT ON "
        if param == "OFF":
            command = "WHITESPOT OFF "
        if param == "STATUS":
            command = "WHITESPOT STATUS"
        return_string = self.send_to_TCS(command)  
        
    def lamp(self,LN,param,percent):
        """This command turns on or off the calibration lamps. Where “LN” is the location of the lamp (1 to 12).
        There are two position that have dimmers, position L9 and L12, therefore, a percentage must be added."""
        if (LN == L9) or (LN = L12):          
            if param == "ON":
                command = "LAMP "+ LN +" ON " + str(percent)
            if param == "OFF":
                command = "LAMP "+ LN +"  OFF " + str(percent
        else:                                                      
            if param == "ON":
                command = "LAMP "+ LN +" ON"
            if param == "OFF":
                command = "LAMP "+ LN +"  OFF "
        if param == "STATUS":
            command = "LAMP "+ LN +" STATUS"
        return_string = self.send_to_TCS(command)  
        
    def adc(self,param):
        """To work with the ADC, you must first place it in the IN position, after that, you can command it between [0, 100] %.
        If you use ADC TRACK, you must add ENABLE | DISABLE."""
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
        """This command returns a long list of parameters"""
        command = "INFO"
        info_string = self.send_to_TCS(command)  
        #unpack the python string
        val = info_string.split()
        #DONE 2002-04-15 17:06:52 05:52:53.81 -52:14:46.54 -03:54:13.05 136.34 42.31 274.64 136.34 42.31 1.484 1 1 1
        info_dict  = {
                      'DONE': val[0], #DONE 
                      'date': val[1], #2002-04-15 
                      'time': val[2], #17:06:52 
                      'right ascension': val[3], #05:52:53.81 
                      'declinatiom':  val[4], #-52:14:46.54 
                      'hour angle':  val[5] , #-03:54:13.05 
                      'azimuth':  val[6], #136.34 
                      'elevation':  val[7], #42.31 
                      'rotator angle':  val[8], #274.64 
                      'dome azimuth':  val[9], #136.34 
                      'dome elevation':  val[10], #42.31 
                      'airmass':   val[11], #1.484 
                      'dome ready': val[12], # 1
                      'dome init': val[13], # 1
                      'shutter init': val[14], # 1
                     }
        return info_dict

    def infox(self):
        """This command returns a long list of parameters"""
        command = "INFOX"
        infox_string = self.send_to_TCS(command)  
        #unpack the python string
        val = infox_string.split()
        #DONE 53490 01:34:30.2 IN_DONE_51.60 -1420.00 8.5 34.1 738.0 357.1 13.2 
        infox_dict  = {
                    'DONE' : val[0], # DONE
                    'mjd': val[1],   #53490 
                    'sideral time' : val[2], #01:34:30.2 
                    'position adc' : val[3], #IN_DONE_51.60 
                    'telescope focus' :val[4] , #-1420.00 
                    'outside temperature' : val[5], # 8.5 
                    'humidity': val[6], #34.1  
                    'pressure': val[7], # 738.0
                    'wind direction': val[8], #357.1  
                    'wind speed': val[9], #13.2
                    'actual target telescope (Ra)' : val[10], #11:23:59.374 
                    'actual target telescope (Dec)' : val[11], #-12:17:48.001 
                    'weather date': val[12], #2005-04-30T03:07:01 
                    'zenith distance': val[13], #27.76 
                    'ra pangl': val[14], #-90.0 
                    'dec pangl': val[15], #0.0
                    'rotator offset': val[16], # 0.0 
                    'inside temperature': val[17], #9.0 
                    'dimm seeing': val[18], #0.8
                    }
        return infox_dict

        
    def target(self,param,RADEC="RA=00:00:00.00 DEC=00:00:00:00 EPOCH=2000.0"):
        """This command send a new position request to the TCS. The target is given in units of RA (HH:MM:SS.SS), DEC (DD:MM:SS.SS) 
        and EPOCH (year).
        This command involves the movement of mount, dome, rotator, adc and optics. 
        If it is required to know only the state of the mount, use option "MOUNT"""
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
        """This command set a new instrument position angle to the TCS. The IPA is given in units of degrees."""
        if param == "MOVE":
            command = "IPA MOVE " + ANGLE
        if param == "STATUS":
            command = "IPA STATUS"
        return_string = self.send_to_TCS(command)  

    def instrument(self,param,instrument):
        """This command select the new instrument in use."""
        command = "INSTRUMENT"
        if param == "MOVE":
            command = "INSTRUMENT MOVE " + instrument
        if param == "STATUS":
            command = "INSTRUMENT STATUS"
        return_string = self.send_to_TCS(command)  

    def ginfo(self):
        """This command returns a long list of parameters"""
        command = "GINFO"
        ginfo_string = self.send_to_TCS(command)  
        #unpack the python string
        val = ginfo_string.split()
        #DONE 70.56 180.30 -1420.00 13.2 0.9 250.4 90.0 0.0 90.0 0.0 5 0.0 0.0 3.2 2516
        ginfo_dict  = {
                    'DONE' : val[0], # DONE
                   'telescope elevation' : val[1], # 70.56 
                   'telescope azimuth' : val[2], # 180.30 
                   'telescope focus' : val[3], # -1420.00 
                   'wind speed' : val[4], # 13.2 
                   'seeing' : val[5], # 0.9 
                   'rotator position' : val[6], #  250.4 
                   'ipa' : val[7], # 90.0 
                   'iaa' : val[8], # 0.0 
                   'ipa' : val[9], # 90.0 
                   'iaa' : val[10], # 0.0 
                   'm3 position' : val[11], #  5 
                   'guider x position' : val[12], #  0.0 
                   'guider y position' : val[13], # 0.0 
                   'guider focus' : val[14], #  3.2   
                   'guider star id' : val[15], #  2516
                   }
        return ginfo_dict
    
    def sinfo(self):
        """This command returns a long list of parameters"""
        command = "SINFO"
        sinfo_string = self.send_to_TCS(command)  
        #unpack the python string
        val = ginfo_string.split()
        #DONE 05:52:53.81 -52:14:46.54 2000.0 136.34 42.31 -1420.00 7.6 55.5 738.4 306.0 16.92 0.9 274.64 90.0 90.0 5
        sinfo_dict  = {
                    'DONE' : val[0], # DONE
                   'right ascension' : val[1], # 05:52:53.81 
                   'declination' : val[1], # -52:14:46.54 
                   'epoch' : val[1], # 2000.0 
                   'telescope elevation' : val[1], #  136.34 
                   'telescope azimuth' : val[1], #  42.31 
                   'telescope focus' : val[1], #  -1420.00
                   'outside temperature' : val[1], #   7.6 
                   'humidity' : val[1], # 55.5 
                   'pressure' : val[1], # 738.4 
                   'wind direction' : val[1], # 306.0  
                   'wind speed' : val[1], #  16.92 
                   'seeing' : val[1], #  0.9 
                   'rotator position' : val[1], #  274.64 
                   'ipa' : val[1], # 90.0 
                   'ipa' : val[1], # 90.0 
                   'm3 position' : val[1], # 5
                   }
        return sinfo_dict

    def rotpos(self):
        """This command returns a long list of parameters"""
        command = "ROTPOS"
        return_string = self.send_to_TCS(command)  

    def infoa(self):
        """This command returns a long list of parameters"""
        command = "INFOA"
        INFOA_string = self.send_to_TCS(command)  
        val = INFOA_string.split()
        #INFOA
        #DONE TCS_DATE=2019-06-26 TCS_UT=19:07:23.558 MOUNT_RA=08:40:58.775 MOUNT_DEC=22:29:05.070 
        #MOUNT_HA=00:01:57.062 MOUNT_AZ=359.983700 MOUNT_EL=37.004100 TCS_ST=08:42:55.837 TCS_PARALLACTICANGLE=90.0 
        #TCS_MJD=58660 TCS_FOCUS=-1570.31 TCS_AIRMASS=1.66 TCS_IPA=0.000 NIR_POS=359.9 IROT_TRIPLESPEC=40.7 M3_POS=5 ECS_TEM- 
        #POUT=5.800000 ECS_HUMIDITY=39.200000 ECS_PRESSURE=733.600000 ECS_WINDDIR=319.000000 ECS_WINDSPD=33.840000 #
        #ECS_TEMPIN=4.783000 ECS_TIMESTAMP=2019-06-26T19:07:17 ECS_SEE- ING=-1 DOME_AZ=89.983956 SHUTTER_EL=0.000324 
        #GUIDER_STARID= ISBIR_GUIDERX=-0.107 ISBIR_GUIDERY=2.841 ISBIR_CLM=OUT LAMP_1=OFF TAG_1=Hg(Ar) LAMP_2=OFF TAG_2=Neon 
        #LAMP_3=OFF TAG_3=Argon LAMP_4=OFF TAG_4=Hollow LAMP_5=OFF TAG_5=None LAMP_6=OFF TAG_6=None LAMP_7=OFF TAG_7=None 
        #LAMP_8=OFF TAG_8=None LAMP_9=OFF TAG_9=Quartz LAMP_10=OFF TAG_10=None LAMP_11=OFF TAG_11=None LAMP_12=OFF TAG_12=None
        infoA_dict  = {
                    'DONE' : val[0], # DONE
                    'date' :                val.split()[1].split("=")[1], #
                    'universal time' :      val.split()[2].split("=")[1], # 
                    'right ascension' :     val.split()[3].split("=")[1], #
                    'declination' :         val.split()[4].split("=")[1], #
                    'hour angle' :          val.split()[5].split("=")[1], #
                    'telescope azimuth' :   val.split()[6].split("=")[1], #
                    'telescope elevation' : val.split()[7].split("=")[1], # 
                    'sidereal time' :       val.split()[8].split("=")[1], #
                    'parallactic angle' :   val.split()[9].split("=")[1], #
                    'mjd' :                 val.split()[10].split("=")[10], #
                    'telescope focus' :     val.split()[11].split("=")[1], #
                    'airmass' :             val.split()[12].split("=")[1], #
                    'ipa' :                 val.split()[13].split("=")[1], #
                    'rotator position' :    val.split()[14].split("=")[1], #
                    'irot' :                val.split()[15].split("=")[15], #
                    'm3 position' :         val.split()[16].split("=")[1], #
                    'outside temperature' : val.split()[17].split("=")[1], # 
                    'humidity' :            val.split()[18].split("=")[1], #
                    'pressure' :            val.split()[19].split("=")[1], #
                    'wind direction' :      val.split()[20].split("=")[1], #
                    'wind speed' :          val.split()[21].split("=")[1], #
                    'inside temperature' :  val.split()[22].split("=")[1], #
                    'ecs time stamp' :      val.split()[23].split("=")[1], #
                    'dimm seeing' :         val.split()[24].split("=")[1], #
                    'dome azimuth' :        val.split()[25].split("=")[1], #
                    'shutter elevation' :   val.split()[26].split("=")[1], #
                    'guider star id' :      val.split()[27].split("=")[1], #
                    'guider x position' :   val.split()[28].split("=")[1], #
                    'guider y position ' :  val.split()[29].split("=")[1], #
                    'comparison lamp mirror' : val.split()[30].split("=")[1], # 
                    'lamp 1 state' :        val.split()[31].split("=")[1], #
                    'lamp 1 tag' :          val.split()[32].split("=")[1], #
                    'lamp 2 state' :        val.split()[33].split("=")[1], #
                    'lamp 2 tag' :          val.split()[34].split("=")[1], #
                    'lamp 3 state' :        val.split()[35].split("=")[1], #
                    'lamp 3 tag' :          val.split()[36].split("=")[1], #
                    'lamp 4 state' :        val.split()[37].split("=")[1], #
                    'lamp 4 tag' :          val.split()[38].split("=")[1], #
                    'lamp 5 state' :        val.split()[39].split("=")[1], #
                    'lamp 5 tag' :          val.split()[40].split("=")[1], #
                    'lamp 6 state' :        val.split()[41].split("=")[1], #
                    'lamp 6 tag' :          val.split()[42].split("=")[1], #
                    'lamp 7 state' :        val.split()[43].split("=")[1], #
                    'lamp 7 tag' :          val.split()[44].split("=")[1], #
                    'lamp 8 state' :        val.split()[45].split("=")[1], #
                    'lamp 8 tag' :          val.split()[46].split("=")[1], #
                    'lamp 9 state' :        val.split()[47].split("=")[1], #
                    'lamp 9 tag' :          val.split()[48].split("=")[1], #
                    'lamp 10 state' :       val.split()[49].split("=")[1], #
                    'lamp 10 tag' :         val.split()[50].split("=")[1], #
                    'lamp 11 state' :       val.split()[51].split("=")[1], #
                    'lamp 11 tag' :         val.split()[52].split("=")[1], #
                   }
        return infoA_dict
        
        

        