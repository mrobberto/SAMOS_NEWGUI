#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Nov 16 08:56:51 2021

@author: robberto
"""


#FROM https://pythonprogramming.net/python-3-tkinter-basics-tutorial/
#========================================================================

#import tkinter as tk
from tkinter import *
import os,sys
from astropy.io import ascii

from pathlib import Path
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
parent_dir = str(path.parent)   
sys.path.append(parent_dir)

SF_path = parent_dir+"/SAMOS_system_dev"
os.sys.path.append(SF_path)


#check...


#from Class_PCM_module import Class_PCM_module
#import Class_PCM_module as PCM
from Class_PCM import Class_PCM
PCM = Class_PCM()

#Here, we are creating our class, Window, and inheriting from the Frame class. 
#Frame is a class from the tkinter module. (see Lib/tkinter/__init__)

class Window(Toplevel):

    # Define the settings upon initialization. Here you can specify
    def __init__(self, master=None):
        
 
        super().__init__(master = master) 
        #super() recalls and includes the __init__() of the master class (tk.Topelevel), so one can use that stuff there without copying the code.

        #reference to the master widget, which is the tk window                 
#        self.master = master 

        #with that, we want to then run init_window, which doesn't yet exist
#        self.init_window()
        
        #rename for convenience the imported class
#        PCM = Class_PCM_module()
        
#The above is really all we need to do to get a window instance started.
        
    #Creation of init_window
        self.geometry("400x330")

        # changing the title of our master widget      
        self.title("IDG - PCM module driver")

        # allowing the widget to take the full space of the root window
#        self.pack(fill=BOTH, expand=1)

        self.Echo_String = StringVar()         
        #self.check_if_power_is_on()

# =============================================================================
#         
#         #Get echo from Server 
# =============================================================================
        Button_Echo_From_Server = Button(self, text="Echo from server",command=self.call_echo_PCM, relief=RAISED)
        # placing the button on my window
        Button_Echo_From_Server.place(x=10,y=10)
        self.Echo_String = StringVar()        
        Label_Echo_Text = Label(self,textvariable=self.Echo_String,width=15,bg='white')
        Label_Echo_Text.place(x=160,y=13)
        
# =============================================================================
#         
#        # Power on/odd 
# =============================================================================
        self.is_on = False
        if self.is_on == False:
            text = "Turn power ON"
            color = "green"
        else: 
            text = "Turn power OFF"
            color = "red"
        self.Button_Power_OnOff = Button(self, text=text,command=self.power_switch, relief=RAISED,fg = color)
        self.Button_Power_OnOff.place(x=10,y=40)

# =============================================================================
#         All port statusPower on/odd 
# =============================================================================
        self.Button_All_Ports_Status = Button(self, text="All ports status",command=self.all_ports_status, relief=RAISED)
        self.Button_All_Ports_Status.place(x=200,y=40)
  
# =============================================================================
#         Select FW or GR    
# =============================================================================
        self.r1_v = IntVar()
        
        r1 = Radiobutton(self, text='FW1', variable=self.r1_v, value=1, command=self.Choose_FWorGR)
        r1.place(x=10,y=70) 
        
        r2 = Radiobutton(self, text='FW2', variable=self.r1_v, value=2, command=self.Choose_FWorGR)
        r2.place(x=70,y=70)  
        
        r3 = Radiobutton(self, text='GR_A', variable=self.r1_v, value=3, command=self.Choose_FWorGR)
        r3.place(x=130,y=70) 

        r3 = Radiobutton(self, text='GR_B', variable=self.r1_v, value=4, command=self.Choose_FWorGR)
        r3.place(x=190,y=70) 
   
        #start with FW1 
        self.r1_v.set(1)
        self.Choose_FWorGR()
# =============================================================================
#       home
# =============================================================================
        self.Button_home = Button(self, text="send to home",command=self.home, relief=RAISED)
        self.Button_home.place(x=10,y=100)

# =============================================================================
#        Initialize
# =============================================================================
        self.Button_Initialize = Button(self, text="Initialize Filter Wheels",command=self.FW_initialize, relief=RAISED)
        self.Button_Initialize.place(x=200,y=100)
  
# =============================================================================
#        Query current step counts
# =============================================================================
        self.Button_Initialize = Button(self, text="Current steps",command=self.query_current_step_counts, relief=RAISED)
        self.Button_Initialize.place(x=10,y=130)

    
# =============================================================================
#         
#         #Move to step.... 
# =============================================================================
        Button_Move_to_step = Button(self, text="Move to step",command=self.move_to_step, relief=RAISED)
        Button_Move_to_step.place(x=10,y=160)
        self.Target_step = StringVar()        
        Label_Target_step = Entry(self,textvariable=self.Target_step,width=6,bg='white')
        Label_Target_step.place(x=140,y=163)
        Button_Stop = Button(self, text="Stop",command=self.stop, relief=RAISED)
        Button_Stop.place(x=260,y=160)
    
# =============================================================================
#         
#         #Move to FW_position.... 
# =============================================================================
        FW_pos_options = [
             "A1",
             "A2",
             "A3",
             "A4",
             "A5",
             "A6",
             "B1",
             "B2",
             "B3",
             "B4",
             "B5",
             "B6",
             ]
#        data = ascii.read(local_dir+'/IDG_filter_positions.txt')
#        print(data)
        
#        # datatype of menu text
        self.selected_FW_pos = StringVar()
#        # initial menu text
        self.selected_FW_pos.set(FW_pos_options[0])
#        # Create Dropdown menu
        self.menu_FW_pos = OptionMenu(self, self.selected_FW_pos,  *FW_pos_options)
        self.menu_FW_pos.place(x=120, y=193)
        Button_Move_to_FW_pos = Button(self, text="FW Position",command=self.FW_move_to_position, relief=RAISED)
        Button_Move_to_FW_pos.place(x=10,y=190)

# =============================================================================
#         
#         #Move to Filter.... 
# =============================================================================
        filter_options = [
             "open",
             "SLOAN-g",
             "SLOAN-r",
             "SLOAN-i",
             "SLOAN-z",
             "Ha",
             "O[III]",
             "S[II]",
             ]
#        data = ascii.read(local_dir+'/IDG_Filter_positions.txt')
#        print(data)
        
#        # datatype of menu text
        self.selected_filter = StringVar()
#        # initial menu text
        self.selected_filter.set(filter_options[0])
#        # Create Dropdown menu
        self.menu_filters = OptionMenu(self, self.selected_filter,  *filter_options)
        self.menu_filters.place(x=300, y=193)
        Button_Move_to_filter = Button(self, text="Filter",command=self.FW_move_to_filter, relief=RAISED)
        Button_Move_to_filter.place(x=230,y=190)

# =============================================================================
#         
#         #Move to GR_position.... 
# =============================================================================
        GR_pos_options = [
             "GR_A1",
             "GR_A2",
             "GR_B1",
             "GR_B2",
             ]
#        # datatype of menu text
        self.selected_GR_pos = StringVar()
#        # initial menu text
        self.selected_GR_pos.set(GR_pos_options[0])
#        # Create Dropdown menu
        self.menu_GR_pos = OptionMenu(self, self.selected_GR_pos,  *GR_pos_options)
        self.menu_GR_pos.place(x=120, y=223)
        Button_Move_to_GR_pos = Button(self, text="GR Position",command=self.GR_move_to_position, relief=RAISED)
        Button_Move_to_GR_pos.place(x=10,y=220)

# =============================================================================
#         
#         #Enter command
# =============================================================================
        Button_Enter_Command = Button(self, text="Enter Command: ",command=self.enter_command, relief=RAISED)
        Button_Enter_Command.place(x=10,y=250)
        self.Command_string = StringVar()        
        Text_Command_string = Entry(self,textvariable=self.Command_string,width=15,bg='white')
        Text_Command_string.place(x=180,y=252)
        Label_Command_string_header = Label(self,text=" ~@,9600_8N1T2000,+")
        Label_Command_string_header.place(x=10,y=280)
        Label_Command_string_Example = Label(self,text=" (e.g. /1e1R\\n)")
        Label_Command_string_Example.place(x=165,y=280)


# =============================================================================
# 
#         # Exit
# =============================================================================
        quitButton = Button(self, text="Exit",command=self.client_exit)
        quitButton.place(x=280, y=300)
        
        
        
    def get_widget(self):
       return self.root
        
    """ 
    def check_if_power_is_on(self):       
        print('at startup, get echo from server:')
        t = PCM.echo_client() 
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
    """        

    def call_echo_PCM(self):       
        print('echo from server:')
        t = PCM.echo_client()
        self.Echo_String.set(t)
        print(t)

    def power_switch(self):     
    # Determine is on or off
        if self.is_on:  #True, power is on => turning off, prepare for turn on agaim
            t=PCM.power_off()
            self.is_on = False
            self.Button_Power_OnOff.config(text="Turn power On",fg = "green")
        else:            
            t=PCM.power_on()
            self.is_on = True
            self.Button_Power_OnOff.config(text="Turn power Off",fg = "red")
        self.Echo_String.set(t)
        print("Power switched to ", t)
    
    def all_ports_status(self):       
        print('all ports status:')
        t = PCM.all_ports_status()
        self.Echo_String.set(t)
        print(t)
        
    def Choose_FWorGR(self):
        if self.r1_v.get() == 1: 
            unit = 'FW1',
        if self.r1_v.get() == 2: 
            unit = 'FW2',
        if self.r1_v.get() == 3: 
            unit= 'GR_A',
        if self.r1_v.get() == 4: 
            unit = 'GR_B',
        self.FWorGR = unit[0]    #returns a list...
        print(self.FWorGR)    

    def FW_initialize(self):       
        print('Initialize:')
        t = PCM.initialize_filter_wheel("FW1")
        t = PCM.initialize_filter_wheel("FW2")
        self.Echo_String.set(t)
        print(t)

    def stop_the_motors(self):       
        print('Stop the motor:')
        t = PCM.motors_stop()
        self.Echo_String.set(t)

    def query_current_step_counts(self):       
        print('Current step counts:')
        t = PCM.query_current_step_counts(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def home(self):       
        print('home:')
        t = PCM.home_FWorGR_wheel(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def move_to_step(self):       
        print('moving to step:')
        t = PCM.go_to_step(self.FWorGR,self.Target_step.get())
        self.Echo_String.set(t)
        print(t)

    def stop(self):       
        print('moving to step:')
        t = PCM.stop_filter_wheel(self.FWorGR)
        self.Echo_String.set(t)
        print(t)

    def FW_move_to_position(self):       
        print('moving to FW position:',self.selected_FW_pos.get()) 
        FW_pos = self.selected_FW_pos.get()
        t = PCM.move_FW_pos_wheel(FW_pos)
        self.Echo_String.set(t)
        print(t)
        
    def FW_move_to_filter(self):       
        print('moving to filter:',self.selected_filter.get()) 
        filter = self.selected_filter.get()
        t = PCM.move_filter_wheel(filter)
        self.Echo_String.set(t)
        print(t)

    def GR_move_to_position(self):       
        print('moving to GR_position:') 
        GR_pos = self.selected_GR_pos.get()
        t = PCM.move_grism_rails(GR_pos)
        self.Echo_String.set(t)
        print(t)

    def enter_command(self):       
        print('command entered:',self.Command_string.get())         
        t = PCM.send_command_string(self.Command_string.get()) #convert StringVar to string
        self.Echo_String.set(t)
        print(t)
        
    def client_exit(self):
        print("destroy")
        self.destroy() 
    
'''
# #Root window created. 
# #Here, that would be the only window, but you can later have windows within windows.
root = Tk()
# 
# #size of the window
root.geometry("400x330")
# 
# #Then we actually create the instance.
app = Window(root)    
# 
# #Finally, show it and begin the mainloop.
root.mainloop()
'''
if __name__ == "__main__":
    testObj = Window()
    testObj.mainloop()
