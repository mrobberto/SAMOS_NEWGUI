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
import logging
from select import select
import signal
import socket
import sys


class ExitGracefully:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self, signum, frame):
    self.kill_now = True


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
        self.sockets = {}
        for key in self.ip_dict:
            self.port_mappings[key] = int(ip_dict[key].split(":")[1])
            self.sockets[key] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.sockets[key].bind(('localhost', self.port_mappings[key]))
                self.sockets[key].listen(1)
            except socket.error as msg:
                self.logger.error("Bind failed. Error: {}".format(msg))
                sys.exit(1)
            self.logger.info("Listening for {} at port {}".format(key, self.port_mappings[key]))

    
    def run(self):
        while not self.shutdown_signal.kill_now:
            reads, writes, errors = select(list(self.sockets.values()) + [self.comm_pipe], [], [])
            
            # When the parent exits, this will show as "ready for reading"
            if self.comm_pipe in reads:
                self.shutdown_signal.kill_now = True 
                continue
            
            for key in self.sockets:
                for socket in reads:
                    if self.sockets[key] == socket:
                        self.logger.info("Received connection for {}".format(key))
                        data = socket.recv(1024)
                        text = data.decode("utf-8")
                        if not data:
                            self.logger.warning("{} disconnected".format(key))
                        else:
                            self.logger.info("SAMOS {} was sent {}".format(key, text))
                        if self.key_functions[key] is not None:
                            self.key_functions[key](text, socket)
        self.logger.warning("Shutting down simulator.")
        for key in self.sockets:
            self.sockets[key].close()
        self.logger.warning("Sockets closed.")


    def handle_dmd(self, data, socket):
        """
        Handle incoming data from the DMD class
        """
        self.logger.info("DMD sent {}".format(text))
        self.logger.info("Replying with SUCCESS")
        socket.sendall(b'SUCCESS\n')
    
    
    @property
    def component_functions(self):
        key_functions = {
            "IP_Motors": None,
            "IP_CCD": None,
            "IP_DMD": "handle_dmd",
            "IP_SOAR": None,
            "IP_SAMI": None
        }
        return key_functions


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
