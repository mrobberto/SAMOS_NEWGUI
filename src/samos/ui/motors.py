"""
SAMOS Motors tk Frame Class
"""
import tkinter as tk
import ttkbootstrap as ttk
from samos.utilities import get_data_file, get_temporary_dir
from samos.utilities.constants import *

from .common_frame import SAMOSFrame, check_enabled


class MotorsPage(SAMOSFrame):

    def __init__(self, parent, container, **kwargs):
        super().__init__(parent, container, "Motors", **kwargs)
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
        b = ttk.Button(self.main_frame, text="Initialize", command=self.initialize_pcm, bootstyle="success")
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "initialized", False)]

        # Turn motor power on/off
        motor_frame = ttk.LabelFrame(self.main_frame, text="Motor Power")
        motor_frame.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.motor_switch_text = tk.StringVar(self, self.switch_text[self.PCM.is_on])
        l = tk.Label(motor_frame, textvariable=self.motor_switch_text, font=BIGFONT)
        l.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[l] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        self.motor_on_button = tk.Button(motor_frame, image=self.switch_img[self.PCM.is_on], command=self.power_switch)
        self.motor_on_button.grid(row=0, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[self.motor_on_button] = [("condition", self.PCM, "initialized", True)]

        # Port Status
        port_status_frame = ttk.LabelFrame(self.main_frame, text="Power Port Status")
        port_status_frame.grid(row=1, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        b = ttk.Button(port_status_frame, text="Get Status", command=self.all_ports_status, bootstyle="info")
        b.grid(row=0, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        self.port_status_info = self.make_db_var(tk.StringVar, "pcm_port_status", "")
        tk.Label(port_status_frame, textvariable=self.port_status_info).grid(row=1, column=0, sticky=TK_STICKY_ALL)

        # Mechanism Selection
        frame = ttk.LabelFrame(self.main_frame, text="Filter/Grating Control")
        frame.grid(row=2, column=0, columnspan=3, sticky=TK_STICKY_ALL)
        sel_frame = ttk.Frame(frame)
        sel_frame.grid(row=0, column=0, rowspan=4, sticky=TK_STICKY_ALL)
        # Select Mechanism to Act On
        self.active_wheel = self.make_db_var(tk.StringVar, "pcm_active_element", "FW1", callback=self.choose_wheel)
        active_wheel = self.active_wheel.get()
        b = tk.Radiobutton(sel_frame, text='FW1', value='FW1', variable=self.active_wheel)
        b.grid(row=0, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = tk.Radiobutton(sel_frame, text='FW2', value='FW2', variable=self.active_wheel)
        b.grid(row=1, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = tk.Radiobutton(sel_frame, text='GR_A', value='GR_A', variable=self.active_wheel)
        b.grid(row=2, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = tk.Radiobutton(sel_frame, text='GR_B', value='GR_B', variable=self.active_wheel)
        b.grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        # Send home
        b = ttk.Button(frame, text="Send to Home", command=self.home, bootstyle='success')
        b.grid(row=4, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        # Get Position
        b = ttk.Button(frame, text="Get Current Steps:", command=self.current_step, bootstyle='info')
        b.grid(row=0, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]

        self.step_positions = {}
        for element in PCM_ELEMENTS:
            self.step_positions[element] = self.make_db_var(tk.IntVar, f"pcm_{element}_pos", 0)

        self.step_labels = {}
        for element in self.step_positions:
            self.step_labels[element] = ttk.Label(frame, textvariable=self.step_positions[element])
        self.step_labels[self.active_wheel.get()].grid(row=0, column=2, sticky=TK_STICKY_ALL)

        # Move to step
        self.step_entry = tk.IntVar(self, 0)
        e = tk.Entry(frame, textvariable=self.step_entry)
        e.grid(row=1, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = ttk.Button(frame, text="Move to Step:", command=self.move_to_step, bootstyle="success")
        b.grid(row=1, column=1, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = ttk.Button(frame, text="Stop", command=self.stop_motors, bootstyle='warning')
        b.grid(row=4, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        # Move to Position
        ttk.Label(frame, text="Set Position").grid(row=2, column=1, sticky=TK_STICKY_ALL)
        self.pos_options = {
            "FW1": ["A1", "A2", "A3", "A4", "A5", "A6"],
            "FW2": ["B1", "B2", "B3", "B4", "B5", "B6"],
            "GR_A": ["GR_A1", "GR_A2"],
            "GR_B": ["GR_B1", "BR_B2"]
        }
        self.selected_pos = self.make_db_var(tk.StringVar, "pcm_selected_pos", self.pos_options[active_wheel][0])
        self.options = ttk.OptionMenu(frame, self.selected_pos, None, *self.pos_options[active_wheel], command=self.move_to_pos, bootstyle="success")
        self.options.grid(row=2, column=2, sticky=TK_STICKY_ALL)
        self.check_widgets[self.options] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]

        # Move to Filter
        ttk.Label(self.main_frame, text="Set Filter").grid(row=3, column=0, sticky=TK_STICKY_ALL)
        self.filter_options = ["open", "SLOAN-g", "SLOAN-r", "SLOAN-i", "SLOAN-z", "Ha", "O[III]", "S[II]"]
        self.selected_filter = self.make_db_var(tk.StringVar, "pcm_selected_filter", self.filter_options[0])
        m = ttk.OptionMenu(self.main_frame, self.selected_filter, None, *self.filter_options, command=self.move_to_filter, bootstyle="success")
        m.grid(row=3, column=1, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[m] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]

        # Custom Command
        ttk.Label(self.main_frame, text="Enter Command:").grid(row=4, column=0, sticky=TK_STICKY_ALL)
        self.command = self.make_db_var(tk.StringVar, "pcm_custom_command", "")
        e = tk.Entry(self.main_frame, textvariable=self.command)
        e.grid(row=4, column=1, sticky=TK_STICKY_ALL)
        self.check_widgets[e] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = ttk.Button(self.main_frame, text="Run", command=self.enter_command, bootstyle='success')
        b.grid(row=4, column=2, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]

        # Initialize Commands
        b = ttk.Button(self.main_frame, text="Initialize Filter Wheels", command=self.initialize_filters, bootstyle='danger')
        b.grid(row=5, column=0, padx=2, pady=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        b = ttk.Button(self.main_frame, text="Initialize Grism Rails", command=self.initialize_grisms, bootstyle='danger')
        b.grid(row=5, column=1, padx=2, pady=2, columnspan=2, sticky=TK_STICKY_ALL)
        self.check_widgets[b] = [("condition", self.PCM, "is_on", True), ("condition", self.PCM, "initialized", True)]
        self.set_enabled()


    @check_enabled
    def initialize_pcm(self):
        self.logger.info("Initializing contact with PCM")
        self.PCM.initialize_motors()


    @check_enabled
    def power_switch(self):
        """ power_switch """
        if self.PCM.is_on:
            self.logger.info("Turning motors off")
            response = self.PCM.power_off()
            self.logger.info("Motors responded {}".format(response))
        else:
            self.logger.info("Turning motors on")
            response = self.PCM.power_on()
            self.logger.info("Motors responded {}".format(response))


    @check_enabled
    def all_ports_status(self):
        """ all_ports_status """
        self.port_status_info.set(self.PCM.all_ports_status())


    @check_enabled
    def choose_wheel(self):
        """ Choose active wheel. On-change callback """
        wheel = self.active_wheel.get()
        for element in self.step_labels:
            if wheel == element:
                self.step_labels[element].grid(row=0, column=2, sticky=TK_STICKY_ALL)
            else:
                self.step_labels[element].grid_forget()
        self.step_entry.set(self.step_positions[wheel].get())
        self.selected_pos.set(self.pos_options[wheel][0])
        self.options.set_menu(None, *self.pos_options[wheel])


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
        self.step_positions[self.active_wheel.get()].set(result)


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
            self.main_fits_header.set_param("gratpos", new_pos)
        else:
            result = self.PCM.move_filter_wheel(new_pos)
            self.main_fits_header.set_param("filtpos", new_pos)
        self.logger.info(f"Moved {current_wheel} to {new_pos}. Result {result}")


    @check_enabled
    def move_to_filter(self, *args):
        result = self.PCM.move_filter_wheel(self.selected_filter.get())
        self.main_fits_header.set_param("filter", self.selected_filter.get())
        self.logger.info(f"Moved filters to {self.selected_filter.get()}. Result {result}")


    @check_enabled
    def enter_command(self):
        self.logger.info(f"Commanding PCM {self.command.get()}")
        result = self.PCM.send_command_string(self.command.get())
        self.logger.info(f"PCM returned {result}")


    def set_enabled(self, run_from_main=False):
        super().set_enabled(run_from_main=run_from_main)
        self.motor_switch_text.set(self.switch_text[self.PCM.is_on])
        self.motor_on_button.config(image=self.switch_img[self.PCM.is_on])
