#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SCL
SOAR Communication Library

Procedures for SOAR TCS Communications
The command protocol is client/server with immediate response. A response should be never take longer than 1500 ms.
"""

import socket
import logging
import threading
from time import sleep


class SCLError(Exception):
    pass


class SCL:
    def __init__(self, host, port, on_change=lambda x:x):
        """
        Constructor for SCL.

        Parameters
        ----------
        host : str
            The hostname or IP address of the server.
        port : int
            The port number of the server.
        on_change : function, optional
            A callback function to be used when the connection status changes.
            The function should take one argument, a boolean indicating whether
            the connection is up (True) or down (False).

        Returns
        -------
        None
        """
        self._socket    = socket.socket()
        self._host      = host
        self._port      = port
        self._on_change = on_change
        self._connected = False
        self._logger    = logging.getLogger()
        self._lock      = threading.Lock()
        try:
            self._socket.connect((self._host, self._port))
            self._connected = True
            self._on_change(True)
        except:
            self._on_change(False)
            self._connected = self.reconnect()


    def reconnect(self, attempts=None):
        """
        Attempt to reconnect to the server.

        Parameters
        ----------
        attempts : int, optional
            The number of times to attempt to reconnect before giving up.

        Returns
        -------
        bool
            True if the connection was re-established, False otherwise.
        """
        try_count = 0
        sleep(5)
        while True:
            try:
                self.close()
                del self._socket
                self._socket = socket.socket()
                self._socket.connect((self._host, self._port))
                self._logger.debug("Connected to host %s, port %s" %(self._host, self._port))
                self._on_change(True)
                return True
            except:
                self._logger.debug("Attempt %s - Cannot connect to TCP/IP socket, host %s, port %s, trying again in 5 seconds..." %(try_count, self._host, self._port))
                sleep(5)
                try_count += 1
                if attempts is not None:
                    if try_count >= attempts:
                        self._logger.error("Reconnection aborted after %s attempts - host %s, port %s, trying again in 5 seconds..." %(try_count, self._host, self._port))
                        return False


    def is_connected(self):
        """
        Return the current status of the connection.

        Returns
        -------
        bool
            The current status of the connection.
        """
        return self._connected


    def _transmit(self, cmd):
        """
        Internal method to send a command to the server.

        Parameters
        ----------
        cmd : str
            The command to send.

        Returns
        -------
        bool
            True if the command was successfully sent, False otherwise.
        """
        size = (len(cmd)).to_bytes(4, byteorder='big')
        cmd_bytes = bytes(cmd, 'ascii')
        try:
            self._socket.send(size + cmd_bytes)
            return True
        except:
            return False


    def _receive(self, timeout=1.5):
        """
        Internal method to receive a response from the server.

        Parameters
        ----------
        timeout : float, optional
            The maximum time to wait for a response, in seconds. Defaults to 1.5.

        Returns
        -------
        str
            The response received from the server, or None if the timeout was reached.
        """
        try:
            self._socket.settimeout(timeout)
            size = self._socket.recv(4)
            full_size = int.from_bytes(size, byteorder='big', signed=False)
            data = self._socket.recv(full_size)
            data = bytes.decode(data)
            if len(data) != full_size:
                for i in range(3):
                    self._logger.debug("Incomplete block, sleep 0.5s and retry - Attempt %i" %(i+1))
                    sleep(0.5)
                    aux_data = self._socket.recv(full_size - len(data))
                    aux_data = bytes.decode(aux_data)
                    data += aux_data
                    if len(data) == full_size:
                        break
                else:
                    raise SCLError("Incomplete block received after %i attempts" %(i))
        except socket.timeout:
            data = None
        return data


    def send_command(self, cmd, timeout=1.5):
        """
        Send a command to the server.

        Parameters
        ----------
        cmd : str
            The command to send.
        timeout : float, optional
            The maximum time to wait for a response, in seconds. Defaults to 1.5.

        Returns
        -------
        str
            The response received from the server, or None if the timeout was reached.

        Raises
        ------
        SCLError
            If the command cannot be sent or a response cannot be received.
        """
        max_retries = False
        max_reconnect = False
        self._lock.acquire()
        if not self._connected:
            self._lock.release()
            raise SCLError("Socket still disconnected - command %s" %(cmd))
        for i in range(12):
            try:
                self.clear_socket()
                sleep(0.05)
                if not self._transmit(cmd):
                    self._logger.error("Tx Socket Error - command %s" %(cmd))
                    raise SCLError("Socket Error Transmitting")
                resp = self._receive(timeout)
                if resp is None:
                    self._logger.error("Rx Socket Timeout - command %s" %(cmd))
                    raise SCLError("Socket Timeout Receiving")
                if resp == "":
                    self._logger.error("Empty socket response - command %s" %(cmd))
                    raise SCLError("Empty socket response")
                break
            except SCLError as e:
                self._on_change(False)
                self._connected = False
                self._connected = self.reconnect(attempts=20)
                if not self._connected:
                    max_reconnect = True
                    break
        else:
            max_retries = True
        if max_retries:
            self._lock.release()
            raise SCLError("Error after retring 12 times sending command - command %s" %(cmd))
        elif max_reconnect:
            self._lock.release()
            raise SCLError("Error after trying to reconnect 20 times to socket - command %s" %(cmd))
        self._lock.release()
        return resp


    def clear_socket(self):
        """
        Clear the socket of any pending data.

        The method sets the socket timeout to 50ms and then reads any data
        available in the socket until there is no more data available or the
        timeout is reached. Any data read is discarded.

        This method is useful when the connection has been re-established
        after a disconnection and there is data pending in the socket.
        """
        self._socket.settimeout(0.05)
        try:
            while True:
                discard_buffer = self._socket.recv(1024)
                if len(discard_buffer) < 1024:
                    break
        except:
            pass


    def close(self):
        """
        Close the socket.

        Tries to close the socket, but does not throw an exception if
        something goes wrong.

        Returns
        -------
        None
        """
        try:
            self._socket.close()
        except:
            raise SCLError("Error closing socket")
