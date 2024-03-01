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
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
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

            # Currently, by default, reply with "success"
            self.logger.info("Replying with 'SUCCESS'")
            connection.sendall(b'SUCCESS\n')
        else:
            connection.close()
            if connection in self.connected_sockets:
                del self.connected_sockets[connection]


    COMPONENT_KEYS = ["IP_Motors", "IP_CCD", "IP_DMD", "IP_SOAR", "IP_SAMI"]


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
