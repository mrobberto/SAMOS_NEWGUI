"""
This module defines a `start_simulator()` function that will be spawned by the
multiprocessing library if contacting the real instrument doesn't work (note that this
will also potentially involve user input/feedback in the future). That function receives
network requests from the SAMOS instrument, logs the calls (and their values), and returns
the appropriate value to signal success.

In addition to `start_simulator()`, the module also defines SAMOSSimulator class that 
pretends to be all of the SAMOS hardware.

Authors
-------

    - Brian York (york@stsci.edu)

Use
---

    This module is not intended to be used independently. Ideally it will only be used
    when the user has directed the SAMOS control interface to create a fake instrument.

Dependencies
------------
    
    None.
"""
from copy import deepcopy
from datetime import datetime, timedelta
import logging
import re
from select import select
import signal
import socket
import sys

from samos.motors import PCM
from samos.system.SAMOS_Parameters_out import SAMOS_Parameters


class ExitGracefully:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    self.kill_now = True


class SimulatedPCM:
    """
    Simulates a PCM, including the ability to "remember" where its filter and grating 
    wheels are, simulate wheel moves, and simulate moves taking some time to execute.
    """
    def __init__(self, logger, move_speed=1000):
        self.logger = logger
        self.PCM = PCM(SAMOS_Parameters(), self.logger)
        self.is_on = False
        self.move_speed = move_speed  # steps/second
        self.steps = {"FW1": 0, "FW2": 0, "GR_A": self.PCM.positions["GR_A"]["GR_H1"], "GR_B": self.PCM.positions["GR_B"]["GR_H2"]}
        self.home = deepcopy(self.steps)
        self.move = None
        self.element_mapping = {"1": "FW1", "2": "FW2", "3": "GR_A", "4": "GR_B"}
        self.command_types = ["home", "fast_home", "move", "go_step", "current_step", "stop", "status"]
        self.reverse_mapping = {
            "FW1": {"1": "A1", "2": "A2", "3": "A3", "4": "A4", "5": "A5", "6": "A6"},
            "FW2": {"1": "B1", "2": "B2", "3": "B3", "4": "B4", "5": "B5", "6": "B6"},
            "GR_A": {"0": "GR_H1", "1": "GR_A1", "2": "GR_A2"},
            "GR_B": {"0": "GR_H2", "1": "GR_B1", "2": "GR_B2"},
        }
    
    
    def handle_command(self, command):
        command = command.strip()
        # The PCM control class sends the "turn on" command *very* frequently.
        if command == self.PCM.PCM_COMMANDS["on"]:
            self.is_on = True
            return "SUCCESS"
        elif command == self.PCM.PCM_COMMANDS["off"]:
            self.is_on = False
            return "SUCCESS"
        if command == self.PCM.PCM_COMMANDS["power_status"]:
            if self.is_on:
                return "POWERED"
            return "NO RESPONSE"
        # If after receiving the command, we are still not on, return nothing.
        if not self.is_on:
            return None
        command = command.replace(self.PCM.PCM_COMMANDS["preamble"], "")
        for command_type in self.command_types:
            matches = re.search(self.PCM.PCM_COMMANDS[command_type]["template"], command)
            if matches is not None:
                element = self.element_mapping[matches.group(1)]
                if command_type == "current_step":
                    # For whatever reason the actual motor responds with a bunch of other stuff as well as the count.
                    return f"?????{self.steps[element]}?"
                elif command_type == "status":
                    return "OKAY"
                elif command_type == "stop":
                    self.move = None
                    return "STOPPED {}".format(element)
                if command_type == "go_step":
                    destination = int(matches.group(2))
                else:
                    if command_type in ["home", "fast_home"]:
                        destination = self.home[element]
                    else:
                        destination_name = self.reverse_mapping[element][matches.group(2)]
                        destination = self.PCM.positions[element][destination_name]
                self.move = {}
                self.move["move_start_time"] = datetime.now()
                self.move["element"] = element
                self.move["initial"] = self.steps[element]
                self.move["destination"] = destination
                if self.move["destination"] >= self.move["initial"]:
                    self.move["sign"] = 1.
                else:
                    self.move["sign"] = -1.
                move_delta = abs(self.move["destination"] - self.move["initial"])
                self.move["move_end_time"] = self.move["move_start_time"] + timedelta(seconds=move_delta/self.move_speed)
                return "MOVING"
        return None


    def update(self):
        if self.move is None:
            return "READY"
        elif datetime.now() > self.move["move_end_time"]:
            self.steps[self.move["element"]] = self.move["destination"]
            self.move = None
            return "READY"
        elapsed_time = datetime.now() - self.move["move_start_time"]
        self.steps[self.move["element"]] = self.move["initial"] + self.move["sign"] * self.move_speed * elapsed_time.total_seconds()
        return "MOVING"


class SAMOSSimulator:
    def __init__(self, ip_dict, parent_pipe):
        self.logger = logging.getLogger("samos")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.info("Simulator started on localhost.")
        self.ip_dict = ip_dict
        self.comm_pipe = parent_pipe
        self.shutdown_signal = ExitGracefully()
        self.port_mappings = {}
        self.listen_sockets = {}
        self.connected_sockets = {}
        for key in self.COMPONENT_KEYS:
            self.port_mappings[key] = int(ip_dict[key].split(":")[1])
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.listen_sockets[new_socket] = key
            try:
                new_socket.bind(('localhost', self.port_mappings[key]))
                new_socket.listen(1)
            except socket.error as msg:
                self.logger.error("Bind failed. Error: {}".format(msg))
                sys.exit(1)
            self.logger.info("Listening for {} at port {}".format(key, self.port_mappings[key]))
        self.sim_pcm = SimulatedPCM(self.logger)


    def run(self):
        socket_list = list(self.listen_sockets.keys()) + list(self.connected_sockets.keys()) + [self.comm_pipe]
        self.logger.debug("Socket list is {}".format(socket_list))
        while not self.shutdown_signal.kill_now:
            reads, writes, errors = select(socket_list, [], [])
            
            self.logger.info("Got reads: {}".format(reads))
            self.logger.info("Got writes: {}".format(writes))
            self.logger.info("Got errors: {}".format(errors))
            
            # When the parent exits, this will show as "ready for reading"
            if self.comm_pipe in reads:
                self.logger.info("Got shutdown signal")
                self.shutdown_signal.kill_now = True 
                continue
            
            for sock in reads:
                # Connection attempt
                if sock in self.listen_sockets:
                    component = self.listen_sockets[sock]
                    self.logger.info("Opening connection for {}".format(component))
                    connection, address = sock.accept()
                    self.connected_sockets[connection] = component
                    self.logger.debug("Connected Sockets is: {}".format(self.connected_sockets))
                    self._receive(connection, component)
                elif sock in self.connected_sockets:
                    component = self.connected_sockets[sock]
                    self.logger.info("Receiving data for {}".format(component))
                    self._receive(connection, component)
            # End for loop
        # End while loop

        self.logger.warning("Shutting down simulator.")
        for key in self.connected_sockets:
            key.close()
        for key in self.listen_sockets:
            key.close()
        self.logger.warning("Sockets closed.")


    def _receive(self, connection, component):
        """
        Try receiving data from a connection
        """
        try:
            data = connection.recv(1024)
        except ConnectionResetError:
            self.logger.info("Connnection to {} closed by remote".format(component))
            data = b""
        
        if data:
            text = data.decode("utf-8")
            self.logger.info("{} sent {}".format(component, text))
            
            if component == "IP_PCM":
                status = self.sim_pcm.update()
                reply = self.sim_pcm.handle_command(text)
            else:
                # Currently, by default, reply with "success"
                reply = "SUCCESS"

            if reply is None:
                self.logger.info("No valid reply. Closing connection.")
                connection.close()
                if connection in self.connected_sockets:
                    del self.connected_sockets[connection]
            else:
                self.logger.info(f"Replying with '{reply}'")
                connection.sendall(bytearray(f"{reply}\n", "utf8"))
        else:
            connection.close()
            if connection in self.connected_sockets:
                del self.connected_sockets[connection]


    COMPONENT_KEYS = ["IP_PCM", "IP_CCD", "IP_DMD", "IP_SOAR", "IP_SAMI"]


def start_simulator(ip_dict, parent_pipe):
    """
    Simulated instrument hardware for the SAMOS control software to talk to, either to 
    test out new code or to allow for code running and testing when the actual instrument 
    is not available on the network.
    
    This function creates a SAMOSSimulator class, and passes it in the appropriate port
    and message passing information.
    """
    samos_simulator = SAMOSSimulator(ip_dict, parent_pipe)
    samos_simulator.run()
