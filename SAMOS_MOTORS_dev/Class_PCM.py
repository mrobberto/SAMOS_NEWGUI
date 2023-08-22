#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 28 08:11:18 2021

Module to work with the IDG PCM controller and EZHR Stepper module controller:

FOR TESTING TCP COMMUNICATION ON LOCALHOST (see instuction below)
> echo_server() 
> echo_client()

PCM procedures
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

To use/test
>>> from Class_PCM import Class_PCM
>>> PCM = Class_PCM()
>>> PCM.echo_client()
>>>     Received b'NL11111111'
>>> PCM.params()
>>>     {'Host': '10.0.0.179', 'PORT': 1000}
>>> PCM.params['Host']
@author: m. robberto
"""
# =============================================================================
#
# echo_server
#
# =============================================================================
# 1) open an xterm
# 2) move to the local directory of this file
# 3) only once, create an empty __init__.py file (>touch __init__.py) to
#    to the python interpreter that the developer intends this directory
#     to be an importable package.
#     See https://stackoverflow.com/questions/2349991/how-to-import-other-python-files
# 4) start >python
# 5) import this file: >import PCM
# 6) run this procedure >PCM.echo_server()). The terminal hangs...
# 7) go to the instructions for the following echo_client() procedure)

#import threading
import time 
from astropy.io import ascii
from astropy.table import Table
import os, sys
import numpy as np

from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)  
sys.path.append(parent_dir)

from SAMOS_system_dev.SAMOS_Functions import Class_SAMOS_Functions as SF

#PCM = Class_PCM()
#SF = Class_SAMOS_Functions()

#colorblind friendly 
indicator_light_on_color = "#08F903"
indicator_light_off_color = "#194A18"
indicator_light_pending_color = "#F707D3"

class Class_PCM():
    

    def __init__(self): 
        IP_status_dict = SF.read_IP_initial_status()
        print("\n Initial IP_dict:\n",IP_status_dict,"\n")
#        IP_dict = SF.read_IP_user()
        IP_dict = SF.read_IP_default()
        print("\n Current IP_default:\n",IP_dict,"\n")
        
        # reference to indicator lights in main GUI
        # indicator lights will be different colors depending on
        # if motors are moving or in position
        self.canvas_Indicator = None
        
        self.MOTORS_onoff = 0
        if IP_status_dict['IP_Motors'] == 'False':#../0'True':
#            self.IP_Host = str((IP_dict['IP_PCM'])[:12]) #str((IP_dict['IP_Motors'])[:15])
#            self.IP_Port = int((IP_dict['IP_PCM'])[13:]) #int((IP_dict['IP_Motors'])[16:])
            self.IP_Host = IP_dict['IP_Motors'].split(':')[0]#[:12]) #str((IP_dict['IP_Motors'])[:15])
#            print("\n motors ip",IP_dict['IP_Motors'],"\n")
            self.IP_Port = int(IP_dict['IP_Motors'].split(':')[1])#[13:])) #int((IP_dict['IP_Motors'])[16:])
            self.MOTORS_onoff = 1
        else: 
#            self.MOTORS_onoff = 0
            print('MOTORS NOT CONNECTED!!')
            self.canvas_Indicator.itemconfig("grism_ind", fill=indicator_light_off_color)
            self.canvas_Indicator.itemconfig("filter_ind", fill=indicator_light_off_color)
            self.MOTORS_onoff = 0
            return
 
#        self.params = {'Host': '128.220.146.254', 'Port': 8889}
        #self.params = {'Host': '172.16.0.128', 'Port': 1000}
                

    #       cwd = os.getcwd()
 #       dir_motors = '/SAMOS_MOTORS_dev'
        data = ascii.read(local_dir+'/IDG_Filter_positions.txt')
        #print(data)
        self.FW1_counts_pos1 = data['Counts'][0]
        self.FW1_counts_pos2 = data['Counts'][1]
        self.FW1_counts_pos3 = data['Counts'][2]
        self.FW1_counts_pos4 = data['Counts'][3]
        self.FW1_counts_pos5 = data['Counts'][4]
        self.FW1_counts_pos6 = data['Counts'][5]
        self.FW2_counts_pos1 = data['Counts'][6]
        self.FW2_counts_pos2 = data['Counts'][7]
        self.FW2_counts_pos3 = data['Counts'][8]
        self.FW2_counts_pos4 = data['Counts'][9]
        self.FW2_counts_pos5 = data['Counts'][10]
        self.FW2_counts_pos6 = data['Counts'][11]
        self.GR_A_counts_home = data['Counts'][12]
        self.GR_B_counts_home = data['Counts'][13]
        self.GR_A_counts_pos1 = data['Counts'][14]
        self.GR_A_counts_pos2 = data['Counts'][15]
        self.GR_B_counts_pos1 = data['Counts'][16]
        self.GR_B_counts_pos2 = data['Counts'][17]
 
# =============================================================================
#     def echo_server():
#         import socket
#
#         HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
#         PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
#
#         with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#             s.bind((HOST, PORT))
#             s.listen()
#             conn, addr = s.accept()
#             with conn:
#                 print('Connected by', addr)
#                 while True:
#                     data = conn.recv(1024)
#                     if not data:
#                         break
#                     conn.sendall(data)
#
# =============================================================================
    # =============================================================================
    #
    # INITIALIZE to receive the correct address
    #
    # =============================================================================
    def initialize(self, address='172.16.0.141', port=8888):  #INITITALIZED OUTSIDE, USE VPN
        self.IP_HOST = address
        self.IP_Port = port

        print('echo from server:')
        print(self.echo_client())

    # =============================================================================
    #
    # echo client()
    #
    # =============================================================================
    # 1) open an(other) xterm
    # 2) move to this local directory
    # 3) start >python
    # 4) import this file: >import PCM
    # 5) run this procedure >PCM.echo_client())
    # 6) the server gives you the anser and closes
    
    def check_if_power_is_on(self):       
        print('at startup, get echo from server:')
        t = self.echo_client() 
        self.Echo_String.set(t)
        if t!= None:
            print(t[2:13])
            if t[2:13] == "NO RESPONSE":
                self.is_on = False
                self.Echo_String.set(t[2:13])
            else:
                self.is_on = True
                self.Echo_String.set(t)
        else:
            print("No echo from the server")
            


    def echo_client(self):
        import socket
        socket.setdefaulttimeout(3)
        
        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            """
            s.connect((HOST, PORT))
                
            #    s.sendall(b'Hello, world')
            #    s.sendall(b'~Hello, world\n')
                s.sendall(b'~se,all,on\n')
                data = s.recv(1024)
    
            print('Received', repr(data))
            return data
            """    
            try:
                s.connect((HOST, PORT))
                s.sendall(b'~se,all,on\n')
                data = s.recv(1024)
                return(data)
            except socket.error:
                return("no connection")
            finally:
                s.close()
    # =============================================================================
    #
    # PCM_power_on
    #
    # =============================================================================
    def power_on(self):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
    # To talk to the motor controller, you will first need to power the controller power port.
    # The command for that is “~se,1,on\n” This means set enable for power port 1 on.
            s.sendall(b'~se,all,on\n')
            data = s.recv(1024)

        print('Received', repr(data))
        return data

    # =============================================================================
    #
    # PCM_power_off
    #
    # =============================================================================

    def power_off(self):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
    # To talk to the motor controller, you will first need to power the controller power port.
    # The command for that is “~se,1,on\n” This means set enable for power port 1 on.
            s.sendall(b'~se,all,off\n')
#            s.sendall(b'~se,ch5,off\n')
#            s.sendall(b'~se,ch5,on\n')
            data = s.recv(1024)

        print('Received', repr(data))
        return data


    # =============================================================================
    #
    # PCM_send_command_string
    #
    # =============================================================================

    def send_command_string(self, string):
        print('\nstring!: ',string)
        string = '~@,9600_8N1T2000,+string'
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            s.sendall(string.encode())
            
            data = s.recv(1024)

        print('Received', repr(data))
        return data


    # =============================================================================
    #
    # PCM_sensor_status
    #
    # =============================================================================

    def sensor_status(self, FW):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
            if FW == "FW1":
                s.sendall(b'~@,9600_8N1T2000,/1?0\n')

            if FW == "FW2":
                s.sendall(b'~@,9600_8N1T2000,/2?0\n')

            data = s.recv(1024)

        print('Received', repr(data))
        return data

        
    # =============================================================================
    #
    # PCM_all_port_status
    #
    # =============================================================================
    def all_ports_status(self):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
    # you can send "~ge,all\n” and it will return the status of all power ports
            s.sendall(b'~ge,all\n')
            data = s.recv(1024)

        print('Received', repr(data))
        return data

    # =============================================================================
    #
    # initialize_filter_wheel
    #
    # =============================================================================
    def initialize_filter_wheel(self, FW):
        import socket

    #    assign 0 value to FW just to avoid errors while testing w/o FW in input
#        if FW == None:
#            FW1 = "0"
#            FW2 = "0"

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

    # Here are filter wheel commands to send to the PCM…. The stored procedures only need to be sent once in the lifetime of the drive… You should have the ability to send these, but will not have to unless we replaced a drive.
    # The operating commands allow you to choose a particular filter by asking the drive to execute a stored procedure. This should be integrated into your code. You also ought to query the wheels to make sure they are where you think they are….
    # Note: all procedures include the command to route the drive packet via the PCM so it should be really simple to integrate.
    # BTW the camera is no facing the filter wheel.
    #
    #
    # FILTER WHEEL STORED PROCEDURES - These need to be sent to the motor controllers the first time they are used… i.e if you replace a motor controller you should reinitialize with these commands…
    # WHEEL 1
    # Initial drive settings (velocity, steps ratio, current), plus homing routine — this runs automatically on power up.
    # ~@,9600_8N1T2000,/1s0m23l23h0j32V4000v2500n0P0P100z0M500e1R
            if FW == "FW1":
                s.sendall(
#                     b'~@,9600_8N1T2000,/1s0m23l23h0j32V4000v2500n0P0P100z0M500e1R\n')
                    b'~@,9600_8N1T2000,/1s0m23l23h0j32n2f1v2500V5000Z100000R\n')
                     
    # WHEEL 2
    # Initial drive settings (velocity, steps ratio, current), plus homing routine — this runs automatically on power up.
    # ~@,9600_8N1T2000,/2s0m23l23h0j32V4000v2500n0P0P100z0M500e1R
            if FW == "FW2":
                s.sendall(
#                    b'~@,9600_8N1T2000,/2s0m23l23h0j32V4000v2500n0P0P100z0M500e1R\n')
                    b'~@,9600_8N1T2000,/2s0m23l23h0j32n2f1v2500V5000Z100000R\n')

            data = s.recv(1024)
    #
    # Initial drive settings (velocity, steps ratio, current), plus homing routine — this runs automatically on power up.
    # ~@,9600_8N1T2000,/2s0m23l23h0j32V4000v2500n0P0P100z0M500e1R

            print('Received', repr(data))
            return data

    # =============================================================================
    #
    # stored_filter_wheel_procedures
    #
    # =============================================================================
    """
     FILTER WHEEL STORED PROCEDURES - These need to be sent to the motor controllers the first 
     time they are used… i.e if you replace a motor controller you should reinitialize with these commands…
    """

    def stored_filter_wheel_procedures(self):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
# =============================================================================
#     #
#     # Position A1
#     # ~@,9600_8N1T2000,/1s1A46667R
#            s.sendall(b'~@,9600_8N1T2000,/1s1n0A46667R\n')
#     #
#     # Position A2
#     # ~@,9600_8N1T2000,/1s2A62222R
#            s.sendall(b'~@,9600_8N1T2000,/1s2n0A62222R\n')
#     #
#     # Position A3
#     # ~@,9600_8N1T2000,/1s3A77778R
#            s.sendall(b'~@,9600_8N1T2000,/1s3n0A77778R\n')
#     #
# =============================================================================
#    # Position A4
#    # ~@,9600_8N1T2000,/1s4A0R
#            s.sendall(b'~@,9600_8N1T2000,/1s4n0A0R\n')
# =============================================================================
#     #
#     # Position A5
#     # ~@,9600_8N1T2000,/1s5A15555R
#            s.sendall(b'~@,9600_8N1T2000,/1s5n0A15555R\n')
#     #
#     # Position A6
#     # ~@,9600_8N1T2000,/1s6A31111R
#            s.sendall(b'~@,9600_8N1T2000,/1s6n0A31111R\n')
#     #
#     # WHEEL 2
#     # #
#     # Position B1
#     # ~@,9600_8N1T2000,/2s1A46667R
#            s.sendall(b'~@,9600_8N1T2000,/2s1n0A46667R\n')
#     #
#     # Position B2
#     # ~@,9600_8N1T2000,/2s2A62222R
#            s.sendall(b'~@,9600_8N1T2000,/2s2n0A62222R\n')
#     #
#     # Position B3
#     # ~@,9600_8N1T2000,/2s3A77778R
#            s.sendall(b'~@,9600_8N1T2000,/2s3n0A77778R\n')
#     #
#     # Position B4
#     # ~@,9600_8N1T2000,/2s4A0R
#            s.sendall(b'~@,9600_8N1T2000,/2s4n0A0R\n')
#            print('done')
#     #
#     # Position B5
#     # ~@,9600_8N1T2000,/2s5A15555R
#            s.sendall(b'~@,9600_8N1T2000,/2s5n0A15555R\n')
#     #
#     # Position B6
#     # ~@,9600_8N1T2000,/2s6A31111R
#            s.sendall(b'~@,9600_8N1T2000,/2s6n0A31111R\n')
# 
# =============================================================================
        #data = s.recv(1024)

        #print('Received', repr(data))

    #
    # OPERATING COMMANDS:
    #
    # =============================================================================
    #
    # home_filter_wheel(FW)
    #
    # =============================================================================
    def home_FWorGR_wheel(self, FWorGR):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

# =============================================================================
#     #    assign 0 value to FW just to avoid errors while testing w/o FW in input
#             if FW == None:
#                 FW1 = "0"
#                 FW2 = "0"
# 
# =============================================================================
    # Homing occurs automatically on power up…. Or it can be forced using:
    #
    # ~@,9600_8N1T2000,/1e0R  (wheel 1)
    # ~@,9600_8N1T2000,/2e0R  (wheel 2)
            if FWorGR == "FW1":
#                s.sendall(b'~@,9600_8N1T2000,/1e0R\n')
                s.sendall(b'~@,9600_8N1T2000,/1e0R\n')
            if FWorGR == "FW2":
                s.sendall(b'~@,9600_8N1T2000,/2e0R\n')
            if FWorGR == "GR_A":
                s.sendall(b'~@,9600_8N1T2000,/3e10R\n')
            if FWorGR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
                

            data = s.recv(1024)

            print('Received', repr(data))

    # =============================================================================
    #
    # go_to_step
    #
    # =============================================================================
    def go_to_step(self, FWorGR, step):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            if FWorGR == "FW1":
#                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                bstring = bytes(string, 'utf-8')
                print('     sending ',bstring)
                s.sendall(bstring)
            if FWorGR == "FW2":
#                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                bstring = bytes(string, 'utf-8')
                print('     sending ',bstring)
                s.sendall(bstring)
#                s.sendall(b'~@,9600_8N1T2000,/2e1R\n')

            if FWorGR == "GR_A":
#                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                string = '~@,9600_8N1T2000,/3A'+step+'R\n'
                bstring = bytes(string, 'utf-8')
                print('     sending ',bstring)
                s.sendall(bstring)

            if FWorGR == "GR_B":
#                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                string = '~@,9600_8N1T2000,/4A'+step+'R\n'
                bstring = bytes(string, 'utf-8')
                print('     sending ',bstring)
                s.sendall(bstring)
#                s.sendall(b'~@,9600_8N1T2000,/2e1R\n')


            data = s.recv(1024)

            print('Received', repr(data))
#            threading.Timer(3.0, self.query_current_step_counts(FW)).start()

    # =============================================================================
    #
    # return_current_step_counts
    #
    # =============================================================================
    def query_current_step_counts(self,FWorGR):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']
        
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

    #    assign 0 value to FW just to avoid errors while testing w/o FW in input
#           if FW == None:
#               FW1 = "0"
#                FW2 = "0"

            if FWorGR == "FW1":
                # return s.sendall(b'~@,9600_8N1T2000,/1?0\n')
                s.sendall(b'~@,9600_8N1T2000,/1?0\n')
                print("s.sendall(b'~@,9600_8N1T2000,/1?0\n')")
                

            if FWorGR == "FW2":
                s.sendall(b'~@,9600_8N1T2000,/2?0\n')
                print("s.sendall(b'~@,9600_8N1T2000,/2?0\n')")
                

            if FWorGR == "GR_A":
                s.sendall(b'~@,9600_8N1T2000,/3?0\n')
                print("s.sendall(b'~@,9600_8N1T2000,/3?0\n')")
                

            if FWorGR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4?0\n')
                print("s.sendall(b'~@,9600_8N1T2000,/4?0\n')")
                

            data = s.recv(1024)

 #       print(FW)
        print('Received', repr(data))
        return repr(data)

    # =============================================================================
    #
    # PCM_motors_stop
    #
    # =============================================================================

    def motors_stop(self, FWorGR):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
            if FWorGR == "FW1":
                s.sendall(b'~@,9600_8N1T2000,/1T\n')

            if FWorGR == "FW2":
                s.sendall(b'~@,9600_8N1T2000,/2T\n')

            if FWorGR == "GR_A":
                s.sendall(b'~@,9600_8N1T2000,/3T\n')

            if FWorGR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4T\n')

            data = s.recv(1024)

        print('Received', repr(data))
        return data

    # =============================================================================
    #
    # extract_steps_from_return_string
    #
    # =============================================================================
    def extract_steps_from_return_string(self,bstring):
        print(bstring)
        return bstring[5:-1]   

    # =============================================================================
    #
    # extract_steps_from_return_string
    #
    # =============================================================================
    def extract_sensorcode_from_return_string(self,bstring):
        string = str(bstring.decode())[3:]
#        print('v1:',bin(int(string)).lstrip('0b'))
        bits=bin(int(string)).lstrip('0b')
        print(bits) 
        return bits

    # =============================================================================
    #
    # move_FW_pos_wheel
    #
    # =============================================================================
    def move_FW_pos_wheel(self, position):
        
        import socket
        import time 
        
        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        self.stop_timer = False

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    # =============================================================================
    # Positions 1 through six are commanded as follows:
    #
    # ~@,9600_8N1T2000,/1e1R  (Position A1)
    # ~@,9600_8N1T2000,/2e1R  (Position B1)
    #
    # ~@,9600_8N1T2000,/1e2R  (Position A2)
    # ~@,9600_8N1T2000,/2e2R  (Position B2)
    #
    # ~@,9600_8N1T2000,/1e3R  (Position A3)
    # ~@,9600_8N1T2000,/2e3R  (Position B3)
    #
    # ~@,9600_8N1T2000,/1e4R  (Position A4)
    # ~@,9600_8N1T2000,/2e4R  (Position B4)
    #
    # ~@,9600_8N1T2000,/1e5R  (Position A5)
    # ~@,9600_8N1T2000,/2e5R  (Position B5)
    #
    # ~@,9600_8N1T2000,/1e6R  (Position A6)
    # ~@,9600_8N1T2000,/2e6R  (Position B6)
    # =============================================================================
    #
    # Position A1
            if position == 'A1':
                current_steps = self.query_current_step_counts('FW1')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW1_counts_pos1):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/1e1R\n')
                    current_steps = self.query_current_step_counts('FW1')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW1_counts_pos1):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/1e1R\n')
                          current_steps = self.query_current_step_counts('FW1')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps

    # Position A2
            if position == 'A2':
                current_steps = self.query_current_step_counts('FW1')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW1_counts_pos2):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/1e2R\n')
                    current_steps = self.query_current_step_counts('FW1')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW1_counts_pos2):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/1e2R\n')
                          current_steps = self.query_current_step_counts('FW1')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                          
                self.write_status  
                return position,current_steps
    #
    # Position A3
            if position == 'A3':
                current_steps = self.query_current_step_counts('FW1')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW1_counts_pos3):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/1e3R\n')
                    current_steps = self.query_current_step_counts('FW1')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW1_counts_pos3):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/1e3R\n')
                          current_steps = self.query_current_step_counts('FW1')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps
    #
    # Position A4
            if position == 'A4':
                 current_steps = self.query_current_step_counts('FW1')
                 current_steps = self.extract_steps_from_return_string(current_steps)
                 print('1. current_steps:',current_steps)
                 #print(self.FW1_counts_pos4)
                 if current_steps != str(self.FW1_counts_pos4):
                     time.sleep(2)
                     s.sendall(b'~@,9600_8N1T2000,/1e4R\n')
                     current_steps = self.query_current_step_counts('FW1')
                     current_steps = self.extract_steps_from_return_string(current_steps)
                     print('2. current_steps:',current_steps)
                     #print(self.FW1_counts_pos4)
                     while current_steps != str(self.FW1_counts_pos4):
                           time.sleep(2)
                           s.sendall(b'~@,9600_8N1T2000,/14R\n')
                           current_steps = self.query_current_step_counts('FW1')
                           current_steps = self.extract_steps_from_return_string(current_steps)
                           print('3. current_steps:',current_steps)
                           #print(self.FW1_counts_pos4)
                 self.write_status()          
                 return position,current_steps

    # Position A5
            if position == 'A5':
                current_steps = self.query_current_step_counts('FW1')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW1_counts_pos5):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/1e5R\n')
                    current_steps = self.query_current_step_counts('FW1')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW1_counts_pos5):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/1e5R\n')
                          current_steps = self.query_current_step_counts('FW1')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                    self.write_status()          
                    return position,current_steps
    #
    # Position A6
            if position == 'A6':
                current_steps = self.query_current_step_counts('FW1')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW1_counts_pos6):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/1e6R\n')
                    current_steps = self.query_current_step_counts('FW1')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW1_counts_pos6):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/1e6R\n')
                          current_steps = self.query_current_step_counts('FW1')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps
    #
    # WHEEL 2
    # #
    # Position B1
            if position == 'B1':
                current_steps = self.query_current_step_counts('FW2')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW2_counts_pos1):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/2e1R\n')
                    current_steps = self.query_current_step_counts('FW2')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW2_counts_pos1):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/2e1R\n')
                          current_steps = self.query_current_step_counts('FW2')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                print('\n 4. returning position: ', position, ' - current_steps:',current_steps, 'should be',str(self.FW2_counts_pos1))
                return position,current_steps
    #
    # Position B2
            if position == 'B2':
                current_steps = self.query_current_step_counts('FW2')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW2_counts_pos2):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/2e2R\n')
                    current_steps = self.query_current_step_counts('FW2')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW2_counts_pos2):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/2e2R\n')
                          current_steps = self.query_current_step_counts('FW2')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps
    #
    # Position B3
            if position == 'B3':
                current_steps = self.query_current_step_counts('FW2')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW2_counts_pos3):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/2e3R\n')
                    current_steps = self.query_current_step_counts('FW2')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW2_counts_pos3):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/2e3R\n')
                          current_steps = self.query_current_step_counts('FW2')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps
    #
    # Position B4
            if position == 'B4':
                current_steps = self.query_current_step_counts('FW2')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('\n1. current_steps:',current_steps, 'should be',str(self.FW2_counts_pos4))
                if current_steps != str(self.FW2_counts_pos4):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/2e4R\n')
                    current_steps = self.query_current_step_counts('FW2')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('\n2. current_steps:',current_steps, 'should be',str(self.FW2_counts_pos4))
 #                   while current_steps != str(self.FW2_counts_pos4):
                    while abs(int(current_steps) - self.FW2_counts_pos4) >=500:
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/2e4R\n')
                          current_steps = self.query_current_step_counts('FW2')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('\n3. current_steps:',current_steps, 'should be',str(self.FW2_counts_pos4))
                self.write_status() 
                print('\n 4. returning position: ', position, ' - current_steps:',current_steps, 'should be',str(self.FW2_counts_pos4))
                return position,current_steps
    #
    # Position B5
            if position == 'B5':
                current_steps = self.query_current_step_counts('FW2')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW2_counts_pos5):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/2e5R\n')
                    current_steps = self.query_current_step_counts('FW2')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW2_counts_pos5):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/2e5R\n')
                          current_steps = self.query_current_step_counts('FW2')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps
    #
    # Position B6
            if position == 'B6':
                current_steps = self.query_current_step_counts('FW2')
                current_steps = self.extract_steps_from_return_string(current_steps)
                print('1. current_steps:',current_steps)
                if current_steps != str(self.FW2_counts_pos6):
                    time.sleep(2)
                    s.sendall(b'~@,9600_8N1T2000,/2e6R\n')
                    current_steps = self.query_current_step_counts('FW2')
                    current_steps = self.extract_steps_from_return_string(current_steps)
                    print('2. current_steps:',current_steps)
                    while current_steps != str(self.FW2_counts_pos6):
                          time.sleep(2)
                          s.sendall(b'~@,9600_8N1T2000,/2e6R\n')
                          current_steps = self.query_current_step_counts('FW2')
                          current_steps = self.extract_steps_from_return_string(current_steps)
                          print('3. current_steps:',current_steps)
                self.write_status()          
                return position,current_steps

            data = s.recv(1024)

        print('Received', repr(data))


# =============================================================================
#
# move_filter_wheel
#
# =============================================================================
    def move_filter_wheel(self, filter):
        print(filter)
        self.canvas_Indicator.itemconfig("filter_ind", 
                                         fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
#        data = ascii.read(local_dir+'/IDG_filter_positions.txt')
#        print(data)
# =============================================================================
# Position Counts Filter
# FW_A1 46667  SLOAN-g
# FW_A2 62222  SLOAN-r
# FW_A3 77778  SLOAN-i
# FW_A4 0      open
# FW_A5 15555  SLOAN-z
# FW_A6 31111  blank
# FW_B1 46667  Halpha
# FW_B2 62222  OIII
# FW_B3 77778  open
# FW_B4 0      glass 
# FW_B5 15555  Hbeta
# FW_B6 31111  SII
# GR_H1 5      GR_A_Home
# GR_H2 7      GR_B_Home 
# GR_A1 70600  TBD-[69800-71400]
# GR_A2 105300  TBD-[104500-106100]
# GR_B1 173200  TBD-[172499-174000]
# GR_B2 207850  TBD-[207000-208700]
# ============================================================================
        if filter == 'SLOAN-g':
            print('send FW1')
            self.move_FW_pos_wheel('A1')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B3')    
            print('\n >>> FW2 arrived \n') 
 
        if filter == 'SLOAN-r':
            print('send FW1')
            self.move_FW_pos_wheel('A2')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B3')    
            print('\n >>> FW2 arrived \n') 
  
        if filter == 'SLOAN-i':
            print('send FW1')
            self.move_FW_pos_wheel('A3')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B3')    

        if filter == 'open':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B4')    

        if filter == 'SLOAN-z':
            print('send FW1')
            self.move_FW_pos_wheel('A5')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B3')    

        if filter == 'blank':
            print('send FW1')
            self.move_FW_pos_wheel('A6')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B3')    

        if filter == 'Halpha':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B1')    
            
        if filter == 'OIII':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B2')    
            
        if filter == 'open':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B3')    
            
        if filter == 'glass':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B4')    

        if filter == 'Hbeta':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B5')    

        if filter == 'SII':
            print('send FW1')
            self.move_FW_pos_wheel('A4')
            print('\n >>> FW1 arrived \n') 
            print('send FW2')
            self.move_FW_pos_wheel('B6')    
        
        self.canvas_Indicator.itemconfig("filter_ind", 
                                         fill=indicator_light_on_color)
        self.canvas_Indicator.update()
    # =============================================================================
    # #
    # # QUERY COMMANDS:
    # #
    # # ~@,9600_8N1T2000,1/?0  (returns wheel 1, current step count)
    # # ~@,9600_8N1T2000,/2?0  (returns wheel 2, current step count)
    # #
    # # Example response: /0`15555
    # #
    # # When the wheel is in position (i.e. not moving) the step count should be:
    # # Position 1: 46667
    # # Position 2: 62222
    # # Position 3: 77778
    # # Position 4: 0
    # # Position 5: 15555
    # # Position 6: 31111
    # #
    # #
    # # ~@,9600_8N1T2000,1/?0  (returns wheel 1, sensor status)
    # # ~@,9600_8N1T2000,/2?0  (returns wheel 2, sensor status)
    # #
    # # Example Response: /0'14
    # #
    # # When the wheel is in position (i.e. not moving) the sensor status should be:
    # # Position 1: 14
    # # Position 2: 14
    # # Position 3: 14
    # # Position 4: 13
    # # Position 5: 14
    # # Position 6: 14
    # # =============================================================================
    #
    # =============================================================================


    ######

    def initialize_grism_rails(self):

        # =============================================================================
        # # =============================================================================
        # # Initialization settings for Grism Drives
        # #
        # # Notes:
        # # I set these already, and they only need to be programmed once. However, we need to be able to send these commands in the event a drive is replaced.
        # #
        # # ~@,9600_8N1T2000,/3s0m23l23h0j4V7000v2500n2f1Z100000000R ; init (A)
        # # ~@,9600_8N1T2000,/4s0m23l23h0j4V7000v2500n2f1Z100000000R ; init (B)
        # #
        # # ~@,9600_8N1T2000,/3s1S12A69000R
        # # ; position 1 (A)
        # # ~@,9600_8N1T2000,/4s1S12A173000R
        # # ; position 1 (B))
        # #
        # # ~@,9600_8N1T2000,/3s2S12A103300R
        # # ; position 2 (A)
        # # ~@,9600_8N1T2000,/4s2S12A207300R
        # # ; position 2 (B)
        # #
        # # ~@,9600_8N1T2000,/3s10A0R
        # # ; stowed position (A)
        # # ~@,9600_8N1T2000,/4s10A0R
        # # ; stowed stowed (B)
        # #
        # =============================================================================
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
    # Init (A)
            s.sendall(
                b'~@,9600_8N1T2000,/3s0m23l23h0j4V7000v2500n2f1Z100000000R\n')

    # Init (B)
            s.sendall(
                b'~@,9600_8N1T2000,/4s0m23l23h0j4V7000v2500n2f1Z100000000R\n')

            data = s.recv(1024)

            print('Received', repr(data))

    def stored_grism_rails_procedures(self):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
    # Position 1 (A)
    # # ~@,9600_8N1T2000,/3s1S12A69000R
#            s.sendall(b'~@,9600_8N1T2000,/3s1S12A69000R\n')
#            s.sendall(b'~@,9600_8N1T2000,/3s1S12A70600R\n')
    #
    # # ; position 1 (B))
    # # ~@,9600_8N1T2000,/4s1S12A173000R
#            s.sendall(b'~@,9600_8N1T2000,/4s1S12A173000R\n')
#            s.sendall(b'~@,9600_8N1T2000,/4s1S12A173200R\n')
    # #
    # # ; position 2 (A)
    # # ~@,9600_8N1T2000,/3s2S12A103300R
#            s.sendall(b'~@,9600_8N1T2000,/3s2S12A103300R\n')
#            s.sendall(b'~@,9600_8N1T2000,/3s2S12A105300R\n')
    #
    # # ; position 2 (B)
    # # ~@,9600_8N1T2000,/4s2S12A207300R
#            s.sendall(b'~@,9600_8N1T2000,/4s2S12A207300R\n')
            s.sendall(b'~@,9600_8N1T2000,/4s2S12A207850R\n')
    #
    # # ; stowed position (A)
    # # ~@,9600_8N1T2000,/3s10A0R
#            s.sendall(b'~@,9600_8N1T2000,/3s10A0R\n')
            s.sendall(b'~@,9600_8N1T2000,/3s10A1000Z2000R\n')  #line changed by S. Hope
    #
    # # ; stowed stowed (B)
    # # ~@,9600_8N1T2000,/4s10A0R
#            s.sendall(b'~@,9600_8N1T2000,/4s10A0R\n')
            s.sendall(b'~@,9600_8N1T2000,/4s10A1000Z2000R\n') #line changed by S. Hope

            data = s.recv(1024)

            print('Received', repr(data))

    # =============================================================================
    #
    # GrismRail_sensor_status
    #
    # =============================================================================

    def GR_sensor_status(self, GR):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
    #
            if GR == "GR_A":
                s.sendall(b'~@,9600_8N1T2000,/3?4\n')

            if GR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4?4\n')

            data = s.recv(1024)

        print('Received', repr(data))
        return data


    def home_grism_rails(self, GR):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']
        self.canvas_Indicator.itemconfig("grism_ind", 
                                         fill=indicator_light_pending_color)
        self.canvas_Indicator.update()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

    # # ~@,9600_8N1T2000,/3e0R
    # # ; Initialization/ homing (A)
    # # ~@,9600_8N1T2000,/4e0R
    # # ; Initialization/ homing (B)

            if GR == "GR_A":
                s.sendall(b'~@,9600_8N1T2000,/3e0R\n')
            if GR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4e0R\n')

            data = s.recv(1024)

            print('Received', repr(data))
        self.canvas_Indicator.itemconfig("grism_ind", 
                                         fill=indicator_light_on_color)
        self.canvas_Indicator.update()

    def fast_home_grism_rails(self, GR):
        import socket
        
        self.canvas_Indicator.itemconfig("grism_ind", 
                                         fill=indicator_light_pending_color)
        self.canvas_Indicator.update()

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

    # #
    # # ~@,9600_8N1T2000,/3e10R
    # # ; fast move to home
    # # ~@,9600_8N1T2000,/4e10R
    # # ; fast move to home
    #
            if GR == "GR_A":
                s.sendall(b'~@,9600_8N1T2000,/3e10R\n')
            if GR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4e10R\n')

            data = s.recv(1024)

            print('Received', repr(data))
        
        

    def move_grism_rails(self, position):
        print('>',position)
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']
        
        
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

    # =============================================================================
    # #
    # # Commands to execute in your code are as follows:
    # #
    # # Notes:
    # # Homing will happen automatically when the drive is powered up.
    # # Sled A must me home before sled B can move away from home
    # # Sled B must be home before sled A cam move away from home
    # #
    # #
    # # ~@,9600_8N1T2000,/3e0R
    # # ; Initialization/ homing (A)
    # # ~@,9600_8N1T2000,/4e0R
    # # ; Initialization/ homing (B)
    # #
    # # ~@,9600_8N1T2000,/3e1R
    # # ; position GR_A1
    # # ~@,9600_8N1T2000,/4e1R
    # # ; position GR_B1
    # #
    # # ~@,9600_8N1T2000,/3e2R
    # # ; position 2 (A)
    # # ~@,9600_8N1T2000,/4e2R
    # # ; position 2 (B)
    # #
    # # ~@,9600_8N1T2000,/3e10R
    # # ; fast move to home
    # # ~@,9600_8N1T2000,/4e10R
    # # ; fast move to home
    #
    # =============================================================================
    #
    # Position GR_A1
    # # GR B must be home before GR A cam move away from home
            if position == 'GR_A1':
               #1 Sent the other Grism Rail home
               #1.1 Query position of the other grism B rail
               current_steps = self.GR_query_current_step_counts('GR_B')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('1. current_steps GR_B:',current_steps,'should be around', self.GR_B_counts_home)
               current_sensor = self.GR_sensor_status('GR_B')
               #current_sensor = self.extract_sensorcode_from_return_string(current_sensor)
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('1.1 home_sensor GR_B:',bits[1],'should be exactly: 0')
               #
               #1.2 SEND GR B home if not at home...
               if (abs(int(current_steps) - (self.GR_B_counts_home)) > 10) or (bits[1] != '0') :
                   print('\n   sending GR_B at home...')
                   time.sleep(1)
                   #fast move to home
                   s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
                   current_steps = self.GR_query_current_step_counts('GR_B')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   #monitor loop
                   print('1.2 current_steps GR_B:',current_steps,'should be around', self.GR_B_counts_home)
                   while (abs(int(current_steps) - (self.GR_B_counts_home)) > 10) and (bits[1] != '0') :
                         time.sleep(1)
                         #fast move to home
                         s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
                         current_steps = self.GR_query_current_step_counts('GR_B')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('1.3 current_steps GR_B:',current_steps,'should be around', self.GR_B_counts_home)
                    #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_B')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               #at home according to the stepper motor; check the sensor...          
#               print('\n2. current_sensor GR_B:', bits[1],'expected: 0')
               if (abs(int(current_steps) - (self.GR_B_counts_home)) < 10) and (bits[1] == '0') :
                    print('\nGR_B is at home\n')
               # 
               # 1.3 move the grism rail at postion
               # is it already there?
               current_steps = self.GR_query_current_step_counts('GR_A')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('3. current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos1)
               current_sensor = self.GR_sensor_status('GR_A')
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('4. position_sensor GR_A:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - self.GR_A_counts_pos1)>10):# and (bits[2] == '0'): 
                   time.sleep(1)
                   s.sendall(b'~@,9600_8N1T2000,/3e1R\n')
                   current_steps = self.GR_query_current_step_counts('GR_A')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   print('4.1 current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos1)
                   while current_steps != str(self.GR_A_counts_pos1):
                         time.sleep(1)
                         s.sendall(b'~@,9600_8N1T2000,/3e1R\n')
                         current_steps = self.GR_query_current_step_counts('GR_A')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('4.2 current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos1)
                     #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_A')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               print('5 current_sensor GR_A:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - (self.GR_A_counts_pos1)) < 10) and (str(bits[3]) == '0') :
                    print('\nGR_A is at position 1\n')
               #self.write_status()          
               
               return position,current_steps

# =============================================================================
#             if position == 'GR_A1':
#                #1 Sent the other Grism rail home
#                #1.1 Query position of th other grism rail
#                current_steps = self.GR_query_current_step_counts('GR_B')
#                current_steps = self.extract_steps_from_return_string(current_steps)
#                print('1. current_steps GR_B:',current_steps,'should be', self.GR_B_counts_home)
#                #1.2 if the other grism rail is not at home, send it at home
#                if current_steps != str(self.GR_B_counts_home):
#                    time.sleep(1)
#                    #fast move to home
#                    s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
#                    current_steps = self.GR_query_current_step_counts('GR_B')
#                    current_steps = self.extract_steps_from_return_string(current_steps)
#                    print('2. current_steps GR_B:',current_steps,'should be', self.GR_B_counts_home)
#                    while current_steps != str(self.GR_B_counts_home):
#                          time.sleep(1)
#                          #fast move to home
#                          s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
#                          current_steps = self.GR_query_current_step_counts('GR_B')
#                          current_steps = self.extract_steps_from_return_string(current_steps)
#                          print('3. current_steps GR_B:',current_steps,'should be', self.GR_B_counts_home)
#                # 1.3 move the grism rail at postion
#                current_steps = self.GR_query_current_step_counts('GR_A')
#                current_steps = self.extract_steps_from_return_string(current_steps)
#                print('4. current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos1)
#                if current_steps != str(self.GR_A_counts_pos1):
#                    time.sleep(1)
#                    s.sendall(b'~@,9600_8N1T2000,/3e1R\n')
#                    current_steps = self.GR_query_current_step_counts('GR_A')
#                    current_steps = self.extract_steps_from_return_string(current_steps)
#                    print('5. current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos1)
#                    while current_steps != str(self.GR_A_counts_pos1):
#                          time.sleep(1)
#                          s.sendall(b'~@,9600_8N1T2000,/3e1R\n')
#                          current_steps = self.GR_query_current_step_counts('GR_A')
#                          current_steps = self.extract_steps_from_return_string(current_steps)
#                          print('6. current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos1)
#                self.write_status()          
#                return position,current_steps
#            
# =============================================================================
            if position == 'GR_A2':
    # # GR B must be home before GR A cam move away from home
               #1 Sent the other Grism Rail home
               #1.1 Query position of the other grism B rail
               current_steps = self.GR_query_current_step_counts('GR_B')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('1. current_steps GR_B:',current_steps,'should be around', self.GR_B_counts_home)
               current_sensor = self.GR_sensor_status('GR_B')
               #current_sensor = self.extract_sensorcode_from_return_string(current_sensor)
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('1.1 home_sensor GR_B:',bits[1],'should be exactly: 0')
               #
               #1.2 SEND GR B home if needed
               if (abs(int(current_steps) - (self.GR_B_counts_home)) > 10) or (bits[1]!= '0') :
                   time.sleep(1)
                   #fast move to home
                   s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
                   current_steps = self.GR_query_current_step_counts('GR_B')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   #monitor loop
                   print('1.2 current_steps GR_B:',current_steps,'should be around', self.GR_B_counts_home)
                   while (abs(int(current_steps) - (self.GR_B_counts_home)) > 10) and (bits[1] != '0') :
                         time.sleep(1)
                         #fast move to home
                         s.sendall(b'~@,9600_8N1T2000,/4e10R\n')
                         current_steps = self.GR_query_current_step_counts('GR_B')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('1.3 current_steps GR_B:',current_steps,'should be around', self.GR_B_counts_home)
                    #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_B')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               #at home according to the stepper motor; check the sensor...          
               print('\n2. current_sensor GR_B:', bits[1],'expected: 0')
               if (abs(int(current_steps) - (self.GR_B_counts_home)) < 10) and (bits[1] == '0') :
                    print('\nGR_B is at home\n')
               # 
               # 1.3 move the grism rail at postion
               # is it already there?
               current_steps = self.GR_query_current_step_counts('GR_A')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('3. current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos2)
               current_sensor = self.GR_sensor_status('GR_A')
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('4. position_sensor GR_A:',bits[3],'should be on beam at: 0')
               #check if it ok to move
               if (abs(int(current_steps) - self.GR_A_counts_pos2)>10):# and (bits[2] ==  '0'): 
                   time.sleep(1)
                   s.sendall(b'~@,9600_8N1T2000,/3e2R\n')
                   current_steps = self.GR_query_current_step_counts('GR_A')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   print('4.1 current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos2)
                   while current_steps != str(self.GR_A_counts_pos2):
                         time.sleep(1)
                         s.sendall(b'~@,9600_8N1T2000,/3e2R\n')
                         current_steps = self.GR_query_current_step_counts('GR_A')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('4.2 current_steps GR_A:',current_steps,'should be', self.GR_A_counts_pos2)
                     #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_A')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               print('5 current_sensor GR_A:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - (self.GR_A_counts_pos2)) < 10) and (str(bits[3]) == '0') :
                    print('\nGR_A is at position 2\n')
               #self.write_status()         
               #self.canvas_Indicator.itemconfig("grism_ind", 
               #                                 fill=indicator_light_on_color)
               #self.canvas_Indicator.update()
               return position,current_steps



            if position == 'GR_B1':
               # ; position 1 (B)
               # ~@,9600_8N1T2000,/3s2S12A173000R               
               #1 Sent the other Grism rail home
               #1.1 Query position of th other grism rail
               #1 Sent the other Grism Rail home
               #1.1 Query position of the other grism B rail
               current_steps = self.GR_query_current_step_counts('GR_A')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('\n\n1. current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
               current_sensor = self.GR_sensor_status('GR_A')
               #current_sensor = self.extract_sensorcode_from_return_string(current_sensor)
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('1.1 home_sensor GR_A:',bits[1],'should be exactly: 0')
               #
               #1.2 SEND GR A home if needed
               if (abs(int(current_steps) - (self.GR_A_counts_home)) > 10) or (bits[1] != '0') :
                   print('\n   sending GR_A at home...')
                   time.sleep(1)
                   #fast move to home
                   s.sendall(b'~@,9600_8N1T2000,/3e10R\n')
                   current_steps = self.GR_query_current_step_counts('GR_A')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   #monitor loop
                   print('1.2 current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
                   while (abs(int(current_steps) - (self.GR_A_counts_home)) > 10) and (bits[1] != '0') :
                         time.sleep(.1)
                         #fast move to home
                         s.sendall(b'~@,9600_8N1T2000,/3e10R\n')
                         current_steps = self.GR_query_current_step_counts('GR_A')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('1.3 current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
                    #check if the sensor concurs we are at home
                         time.sleep(.5)
                         current_sensor = self.GR_sensor_status('GR_A')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               #at home according to the stepper motor; check the sensor...          
               #print('1.3 current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
               #print('2. current_sensor GR_A:', GR_A_bits[1],'expected: 0')
               if (abs(int(current_steps) - (self.GR_A_counts_home)) < 10) and (bits[1] == '0') :
                    print('\nGR_A is at home\n')
               # 
               # 1.3 move the grism rail at postion
               # is it already there?
               current_steps = self.GR_query_current_step_counts('GR_B')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('\n\n3. current_steps GR_B:',current_steps,'should be', self.GR_B_counts_pos1)
               current_sensor = self.GR_sensor_status('GR_B')
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('4. position_sensor GR_B:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - self.GR_B_counts_pos1)>10):# and (bits[2] == '0'): 
                   time.sleep(1)
                   s.sendall(b'~@,9600_8N1T2000,/4e1R\n')
                   current_steps = self.GR_query_current_step_counts('GR_B')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   print('4.1 current_steps GR_B:',current_steps,'should be', self.GR_B_counts_pos1)
                   while current_steps != str(self.GR_B_counts_pos1):
                         time.sleep(1)
                         s.sendall(b'~@,9600_8N1T2000,/4e1R\n')
                         current_steps = self.GR_query_current_step_counts('GR_B')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('4.2 current_steps GR_B:',current_steps,'should be', self.GR_B_counts_pos1)
                     #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_B')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               print('5 current_sensor GR_B:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - (self.GR_B_counts_pos1)) < 10) and (str(bits[3]) == '0') :
                    print('\nGR_B is at position 1\n')
               #self.write_status()          
               
               return position,current_steps





            if position == 'GR_B2':
                # ; position 2 (B)
                # ~@,9600_8N1T2000,/3s2S12A103300R               
                #1 Sent the other Grism rail home
                #1.1 Query position of th other grism rail
               current_steps = self.GR_query_current_step_counts('GR_A')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('1. current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
               current_sensor = self.GR_sensor_status('GR_A')
               #current_sensor = self.extract_sensorcode_from_return_string(current_sensor)
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('1.1 home_sensor GR_A:',bits[1],'should be exactly: 0')
               #
               #1.2 SEND GR B home if needed
               if (abs(int(current_steps) - (self.GR_A_counts_home)) > 10) or (bits[1] != '0') :
                   time.sleep(1)
                   #fast move to home
                   s.sendall(b'~@,9600_8N1T2000,/3e10R\n')
                   current_steps = self.GR_query_current_step_counts('GR_A')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   #monitor loop
                   print('1.2 current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
                   while (abs(int(current_steps) - self.GR_A_counts_home) > 10) and (bits[1] != '0') :
                         time.sleep(1)
                         #fast move to home
                         s.sendall(b'~@,9600_8N1T2000,/3e10R\n')
                         current_steps = self.GR_query_current_step_counts('GR_A')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('1.3 current_steps GR_A:',current_steps,'should be around', self.GR_A_counts_home)
                    #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_A')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               #at home according to the stepper motor; check the sensor...          
               print('\n2. current_sensor GR_A:', bits[1],'expected: 0')
               if (abs(int(current_steps) - (self.GR_A_counts_home)) < 10) and (bits[1] == '0') :
                    print('\nGR_A is at home\n')
               # 
               # 1.3 move the grism rail at postion
               # is it already there?
               current_steps = self.GR_query_current_step_counts('GR_B')
               current_steps = self.extract_steps_from_return_string(current_steps)
               print('3. current_steps GR_B:',current_steps,'should be', self.GR_B_counts_pos2)
               current_sensor = self.GR_sensor_status('GR_B')
               bits = self.extract_sensorcode_from_return_string(current_sensor)
               print('4. position_sensor GR_B:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - self.GR_B_counts_pos2)>10):# and (bits[2] == '0'): 
                   time.sleep(1)
                   s.sendall(b'~@,9600_8N1T2000,/4e2R\n')
                   current_steps = self.GR_query_current_step_counts('GR_B')
                   current_steps = self.extract_steps_from_return_string(current_steps)
                   print('4.1 current_steps GR_B:',current_steps,'should be', self.GR_B_counts_pos2)
                   while current_steps != str(self.GR_B_counts_pos2):
                         time.sleep(1)
                         s.sendall(b'~@,9600_8N1T2000,/4e2R\n')
                         current_steps = self.GR_query_current_step_counts('GR_B')
                         current_steps = self.extract_steps_from_return_string(current_steps)
                         print('4.2 current_steps GR_B:',current_steps,'should be', self.GR_B_counts_pos2)
                     #check if the sensor concurs we are at home
                         current_sensor = self.GR_sensor_status('GR_B')
                         bits = self.extract_sensorcode_from_return_string(current_sensor) 
               print('5 current_sensor GR_B:',bits[3],'should be on beam at: 0')
               if (abs(int(current_steps) - (self.GR_B_counts_pos2)) < 10) and (str(bits[3]) == '0') :
                    print('\nGR_B is at position 2\n')
               #self.write_status()         
               
               return position,current_steps
                
                
                

    def GR_query_current_step_counts(self, GR):
        import socket

        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))

            if GR == "GR_A":
                # return s.sendall(b'~@,9600_8N1T2000,/1?0\n')
                s.sendall(b'~@,9600_8N1T2000,/3?0\n')
                print("s.sendall(b'~@,9600_8N1T2000,/3?0\n')")

            if GR == "GR_B":
                s.sendall(b'~@,9600_8N1T2000,/4?0\n')
                print("s.sendall(b'~@,9600_8N1T2000,/4?0\n')")

            data = s.recv(1024)

 #       print(FW)
        print('Received', repr(data))
        return repr(data)

    def GR_go_to_step(self, GR, step):
        import socket
        print('going to ',step)
        
        # '10.0.0.179'#127.0.0.1'  # The server's hostname or IP address
        HOST = self.IP_Host#self.params['Host']
        # 1000#65432        # The port used by the server
        PORT = self.IP_Port#self.params['Port']
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            
            if GR == "GR_A":
#                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                string = '~@,9600_8N1T2000,/3A'+step+'R\n'
                bstring = bytes(string, 'utf-8')
                print('     sending ',bstring)
                s.sendall(bstring)
            if GR == "GR_B":
#                string = '~@,9600_8N1T2000,/1A'+step+'R\n'
                string = '~@,9600_8N1T2000,/4A'+step+'R\n'
                bstring = bytes(string, 'utf-8')
                print('     sending ',bstring)
                s.sendall(bstring)
#                s.sendall(b'~@,9600_8N1T2000,/2e1R\n')

            data = s.recv(1024)

            print('Received', repr(data))
#            threading.Timer(3.0, self.query_current_step_counts(FW)).start()

    def write_status(self):
        current_steps = self.query_current_step_counts('FW1')
        FW1_steps = self.extract_steps_from_return_string(current_steps)
        current_steps = self.query_current_step_counts('FW2')
        FW2_steps = self.extract_steps_from_return_string(current_steps)
        current_steps = self.GR_query_current_step_counts('GR_A')
        GR_A_steps = self.extract_steps_from_return_string(current_steps)
        current_steps = self.GR_query_current_step_counts('GR_B')
        GR_B_steps = self.extract_steps_from_return_string(current_steps)
        data = Table()
        data['wheel']= ['FW1','FW2','GR_A','GR_B']
        data['counts']= [FW1_steps,FW2_steps,GR_A_steps,GR_B_steps]
        #cwd = os.getcwd()
        ascii.write(data,os.path.join(local_dir,'FW_GR_status.dat'),overwrite=True)
# =============================================================================
#     def timed_query_current_count_monitor(self, FW):
#         while self.stop_timer == False:
#             threading.Timer(30.0, self.query_current_step_counts(FW)).start()
# 
# =============================================================================
    ######


    #
    # AND NOW FOR SOMETHING NEW….
    #
    # All commands that you want to send to the EZHR motor controllers must be preceded with: ~@,9600_8N1T2000,
    #
    # ~ is the character that all messages to the PCM start with. @ means push the message to the RS485 bus. 9600_8N1T2000 means use 9600 baud, 8 data bits, no parity, 1 stop bit, with a 2000 millisecond timeout for a response message.
    #
    # All the commands you send to the EZHR start with a drive number: /1, /2, /3 etc.
    #
    # When you send a command like ~@,9600_8N1T2000,/3e1R you are asking drive 3 (/3) to execute stored procedure 1 (e1). The R last the end tells it to run the command
    #
    # Every command returns a response packet. The format of the packet is detailed in the EZHR instructions. See page 23 of the EZHR manual.
    #
    # You can also query the drive at anytime. Query commands start with a ? and do not need an R at the end. The command to query the current step count is ?0, and the command to query the limit switches is ?4. For example: ~@,9600_8N1T2000,/3?4… This asks drive 3 (/3) to return the position switch status (?4). Query commands are on page 9 of the manual.
    #
    # You should query the status of the motor controller to see if it has stopped moving, then query the step count, and the position sensor status, to make sure it went to where you thought it should go to.
    #
    # With the grisms you must send one drive home, and make sure it is home by checking its status before  moving the other drive…
    #
    # AND FOR SUPPORT...
    #
    # CALL ME from 8AM to 10PM +1(443) 299 7810
    # TEXT ME anytime +1(443) 299 7810
    # FB MESSENGER ME… Facebook.com/limey.steve.5 ...Use the video or audio chat option - it rings on my cell.
    # FACETIME ME +1(443)299 7810
    #
    # OK, I leave for the UK on Saturday for 2 weeks… I will have my cell phone and it should work… I will also have my computer… The UK is 5 hours ahead… I will be available from 10AM to 10PM UK time. This equates to 5AM to 5PM eastern standard time.
    #
    # Feel free to call anytime… If I can’t speak I will tell you, but I won’t be offended or annoyed…
    #
    # REMEMBER… It’s the squeaky wheel that get oiled first… Squeak loudly, and don’t feel sorry!
    #
    # Regards,
    # =============================================================================
