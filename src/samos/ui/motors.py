"""
SAMOS Motors tk Frame Class
"""
import tkinter as tk
from tkinter import ttk

from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class MotorsPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Motors", **kwargs)
        self.initialized = False
        self.is_on = False
        self.move_window = None
        self.switch_text = {
            True: "Turn Motors OFF",
            False: "Turn Motors ON"
        }
        self.switch_img = {
            True: self.on_big,
            False: self.off_big
        }

        # Initialize all motors
        b = ttk.Button(self.main_frame, text="Initialize", command=self.initialize_pcm)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)

        # Turn motor power on/off
        motor_frame = ttk.LabelFrame(self.main_frame, text="Motor Power")
        motor_frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.motor_switch_text = tk.StringVar(self, self.switch_text[self.is_on])
        l = tk.Label(motor_frame, textvariable=self.motor_switch_text, font=BIGFONT)
        l.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[l] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        self.motor_on_button = tk.Button(motor_frame, image=self.switch_img[self.is_on], command=self.power_switch)
        self.motor_on_button.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.motor_on_button] = [("condition", self, "initialized", True)]

        # Port Status
        port_status_frame = ttk.LabelFrame(self.main_frame, text="Power Port Status")
        port_status_frame.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        b = ttk.Button(port_status_frame, text="Get Status", command=self.all_ports_status)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        self.port_status_info = tk.StringVar(self, "")
        tk.Label(port_status_frame, textvariable=self.port_status_info).grid(row=1, column=0, sticky=TK_STICKY_ALL)

        # Mechanism Selection
        frame = ttk.LabelFrame(self.main_frame, text="Filter/Grating Control")
        frame.grid(row=2, column=0, columnspan=2, sticky=TK_STICKY_ALL)
        sel_frame = ttk.Frame(frame)
        sel_frame.grid(row=0, column=0, rowspan=4, sticky=TK_STICKY_ALL)
        # Select Mechanism to Act On
        self.active_wheel = tk.StringVar(self, 'FW1')
        self.current_wheel = 'FW1'
        b = tk.Radiobutton(sel_frame, text='FW1', value='FW1', variable=self.active_wheel, command=self.choose_wheel)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = tk.Radiobutton(sel_frame, text='FW2', value='FW2', variable=self.active_wheel, command=self.choose_wheel)
        b.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = tk.Radiobutton(sel_frame, text='GR_A', value='GR_A', variable=self.active_wheel, command=self.choose_wheel)
        b.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = tk.Radiobutton(sel_frame, text='GR_B', value='GR_B', variable=self.active_wheel, command=self.choose_wheel)
        b.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        # Send home
        b = ttk.Button(frame, text="Send to Home", command=self.home)
        b.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        # Get Position
        b = ttk.Button(frame, text="Get Current Steps", command=self.current_step)
        b.grid(row=1, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        self.step_position = tk.StringVar(self, "")
        tk.Label(frame, textvariable=self.step_position).grid(row=1, column=2, sticky=TK_STICKY_ALL)
        # Move to step
        ttk.Label(frame, text="Step:").grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.step_entry = tk.StringVar(self, "")
        e = tk.Entry(frame, textvariable=self.step_entry)
        e.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = ttk.Button(frame, text="Move to Step", command=self.move_to_step)
        b.grid(row=2, column=3, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = ttk.Button(frame, text="Stop", command=self.stop_motors)
        b.grid(row=2, column=4, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        # Move to Position
        ttk.Label(frame, text="Set Position").grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.pos_options = {"FW1": ["A1", "A2", "A3", "A4", "A5", "A6"],
                            "FW2": ["B1", "B2", "B3", "B4", "B5", "B6"],
                            "GR_A": ["GR_A1", "GR_A2"],
                            "GR_B": ["GR_B1", "BR_B2"]}
        self.selected_pos = tk.StringVar(self, self.pos_options[self.active_wheel.get()][0])
        self.options = ttk.OptionMenu(frame, self.selected_pos, *self.pos_options[self.active_wheel.get()], command=self.move_to_pos)
        self.options.grid(row=3, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.options] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]

        # Move to Filter
        ttk.Label(self.main_frame, text="Set Filter").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.filter_options = ["open", "SLOAN-g", "SLOAN-r", "SLOAN-i", "SLOAN-z", "Ha", "O[III]", "S[II]"]
        self.selected_filter = tk.StringVar(self, self.filter_options[0])
        m = ttk.OptionMenu(self.main_frame, self.selected_filter, *self.filter_options, command=self.move_to_filter)
        m.grid(row=3, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[m] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]

        # Custom Command
        ttk.Label(self.main_frame, text="Enter Command:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.command = tk.StringVar(self, "")
        e = tk.Entry(self.main_frame, textvariable=self.command)
        e.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = ttk.Button(self.main_frame, text="Run", command=self.enter_command)
        b.grid(row=4, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]

        # Initialize Commands
        b = ttk.Button(self.main_frame, text="Initialize Filter Wheels", command=self.initialize_filters)
        b.grid(row=5, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        b = ttk.Button(self.main_frame, text="Initialize Grism Rails", command=self.initialize_grisms)
        b.grid(row=5, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self, "is_on", True), ("condition", self, "initialized", True)]
        self.set_enabled()


    @check_enabled
    def initialize_pcm(self):
        self.logger.info("Initializing contact with PCM")
        response = self.PCM.echo_client()
        self.logger.info("Server Responded {}".format(response))
        if response is not None:
            self.initialized = True
            self.is_on = self.PCM.check_if_power_is_on()


    @check_enabled
    def power_switch(self):
        """ power_switch """
        if self.is_on:
            self.logger.info("Turning motors off")
            response = self.PCM.power_off()
            self.logger.info("Motors responded {}".format(response))
            self.is_on = self.PCM.check_if_power_is_on()
        else:
            self.logger.info("Turning motors on")
            response = self.PCM.power_on()
            self.logger.info("Motors responded {}".format(response))
            self.is_on = self.PCM.check_if_power_is_on()


    @check_enabled
    def all_ports_status(self):
        """ all_ports_status """
        self.port_status_info.set(self.PCM.all_ports_status())


    @check_enabled
    def choose_wheel(self):
        """ Choose_FWorGR """
        chosen_wheel = self.active_wheel.get()
        if chosen_wheel != self.current_wheel:
            # Empty out all status labels
            self.step_position.set("")
            self.step_entry.set("")
            self.current_wheel = chosen_wheel
            self.selected_pos.set(self.pos_options[chosen_wheel][0])
            self.options.set_menu(self.selected_pos.get(), *self.pos_options[chosen_wheel])


    @check_enabled
    def initialize_filters(self):
        msg = "Do you really want to initialize the filter wheels? This should only be "
        msg += "needed after changing a motor or other component."
        res = ttk.messagebox.askquestion("Initialize Filter Wheels", msg)
        if res == 'yes':
            self.logger.info("Initializing wheel 1")
            result = self.PCM.initialize_filter_wheel("FW1")
            self.logger.info("Result of initializing wheel 1: {}".format(result))
            self.logger.info("Initializing wheel 2")
            result = self.PCM.initialize_filter_wheel("FW2")
            self.logger.info("Result of initializing wheel 2: {}".format(result))


    @check_enabled
    def initialize_grisms(self):
        msg = "Do you really want to initialize the grism rails? This should only be "
        msg += "needed after changing a motor or other component."
        res = ttk.messagebox.askquestion("Initialize Grism Rails", msg)
        if res == 'yes':
            self.logger.info("Initializing rails")
            result = self.PCM.initialize_grism_rails()
            self.logger.info("Result of initializing rails: {}".format(result))


    @check_enabled
    def stop_motors(self):
        result = self.PCM.motors_stop()
        self.logger.info("Result of stopping motors is: {}".format(result))


    @check_enabled
    def current_step(self):
        result = self.PCM.current_filter_step(self.active_wheel.get())
        self.logger.debug(f"Initial step result is {result}")
        result = self.PCM.extract_steps_from_return_string(result)
        self.step_position.set("{}".format(result))


    @check_enabled
    def home(self):
        result = self.PCM.return_wheel_home(self.active_wheel.get())
        self.logger.info("Result of home command is {}".format(result))


    @check_enabled
    def move_to_step(self, *args):
        result = self.PCM.go_to_step(self.active_wheel.get(), self.step_entry.get())
        self.logger.info("Result of moving to step: {}".format(result))


    @check_enabled
    def move_to_pos(self, *args):
        self.logger.info(f"Commanded to move to position with argument {args}")
        current_wheel = self.active_wheel.get()
        new_pos = self.selected_pos.get()
        if "GR" in current_wheel:
            result = self.PCM.move_grism_rails(new_pos)
            self.main_fits_header.set_param("grismpos", new_pos)
        else:
            result = self.PCM.move_filter_wheel(new_pos)
            self.main_fits_header.set_param("filtpos", new_pos)
        self.logger.info("Moved {} to {}. Result {}".format(current_wheel, new_pos, result))


    @check_enabled
    def move_to_filter(self, *args):
        result = self.PCM.move_filter_wheel(self.selected_filter.get())
        self.main_fits_header.set_param("filter", self.selected_filter.get())
        self.logger.info("Moved filters to {}. Result {}".format(self.selected_filter.get(), result))


    @check_enabled
    def enter_command(self):
        self.logger.info("Commanding PCM {}".format(self.command.get()))
        result = self.PCM.send_command_string(self.command.get())
        self.logger.info("PCM returned {}".format(result))


    def set_enabled(self):
        super().set_enabled()
        self.motor_switch_text.set(self.switch_text[self.is_on])
        self.motor_on_button.config(image=self.switch_img[self.is_on])
        
