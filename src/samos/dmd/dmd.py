import codecs
import logging
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
from PIL import Image
import socket
import sys
import time

from samos.utilities import get_data_file


class DigitalMicroMirrorDevice():
    """ 
    Class to control the Digital Micromirror Array created by the JHU
    Instrument Development Group. This has been designed around and tested with
    a DLP7000, which is a 768x1024 pixel device, but should be generalizable to
    other sizes, etc. 
    """
    def __init__(self, logger, par, db):
        self.logger = logger
        self.PAR = par
        self.db = db
        self.is_on = False
        # Set invert to false
        self.invert = False
        # Are the extended basic patterns (e.g. checkerboard) available as single commands?
        self.extended_patterns = False


    def initialize(self, **kwargs):
        """ Initial function for the DMD Controller."""
        self.logger.info("Initializing DMD")
        dmd_ip, dmd_port = self._get_address()
        hostname = socket.gethostname()
        self.logger.debug("DMD hostname: {}".format(hostname))
        self.logger.debug("DMD IP:Port: {}:{}".format(dmd_ip, dmd_port))
        
        self.start_on_whiteout = kwargs.get("start_on_whiteout", False)
        self.dmd_size = kwargs.get("dmd_size", (1080, 2048))
        self.max_diff = kwargs.get("max_diff", self.dmd_size[0] * self.dmd_size[1])
        self.display_type = kwargs.get("display_type", 32)
        self.dmd_data_path = get_data_file("dmd")
        
        self._shapes = {'blackout': (np.zeros(self.dmd_size), self.apply_blackout), 
                        'whiteout': (np.ones(self.dmd_size), self.apply_whiteout)}
        # Checkerboard Pattern
        data_file = get_data_file('dmd.pattern.basic_patterns', 'checkerboard.npy')
        self._shapes["checkerboard"] = (np.load(data_file), "checkerboard")
        
        self.current_dmd_shape = None


    def _open(self):
        """ 
        Opens a connection to the DMD device. The socket connection will
        time out after a few seconds of inactivity, so this is less opening a
        constant connection and more testing our connection method responds as
        expected.
        """
        self.logger.info("Opening a connection to DMD")
        dmd_ip, dmd_port = self._get_address()
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as instrument:
                try:
                    instrument.connect((dmd_ip, dmd_port))
                except Exception as e:
                    self.is_on = False
                    self.logger.error("DMD did not respond!")
                    self.logger.error("Error was {}".format(e))
                    return("no DMD")
            
        self.is_on = True
        self.logger.info("Sending test message")
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            instrument.sendall(b':TEST\n')
            response = instrument.recv(1024)
            self.logger.info("Received response '{}'".format(response.decode('ascii')))
            instrument.close()
        return response


    @property
    def shapes(self):
        """ Make a property so our core shapes are indeditable."""
        return self._shapes


    def send(self, command):
        """
        Send a message to the controller and check the controller sucessfully received it.
        """
        self.logger.info("Sending DMD the command '{}'".format(command))
        dmd_ip, dmd_port = self._get_address()
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as instrument:
                try:
                    instrument.connect((dmd_ip, dmd_port))
                except Exception as e:
                    self.is_on = False
                    self.logger.error("DMD did not respond!")
                    self.logger.error("Error was {}".format(e))
                    raise RuntimeError("Unable to contact DMD controller")

                if isinstance(command, list):
                    message_type = command[-1][4]
                    command = ''.join(command)
                else:
                    message_type = command[4]

                instrument.sendall(codecs.encode(command,'utf-8'))
                reply = instrument.recv(1024)
                response = reply.decode('ascii')
                self.logger.info("Received response {}".format(response))

                if 'invalid ~ command' in response and message_type in response:
                    self.logger.error("Invalid command sent to DMD controller")
                    raise ValueError("An invalid command was sent to the controller.")
                elif response == b'':
                    self.is_on = False
                    self.logger.error("Controller not responding as if a message was sent")
                    raise RuntimeError("The controller is not responding as if a message was sent.")
                else:
                    self.logger.info("Command {} successfully written.".format(command[:-1]))
        else:
            self.logger.info("General status is disconnected")


    def apply_checkerboard(self):
        """ Apply a checkerboard to the DMD. """
        self.logger.info("DMD applying checkerboard pattern")
        message = ['~enable\n', '~test,0\n', '~load,slow\n']
        if not self._send_command_set(message, "checkerboard"):
            return
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['checkerboard'][0])
        self.update_dmd_plot()


    def apply_dotpattern(self):
        """ Apply a dotpattern to the DMD. """
        self.logger.info("DMD applying dot pattern")
        message = ['~enable\n', '~test,1\n', '~load,slow\n']
        if not self._send_command_set(message, "dotpattern"):
            return
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()


    def apply_gridpattern(self):
        """ Apply a gridpattern to the DMD. """
        self.logger.info("DMD applying grid pattern")
        message = ['~enable\n', '~test,2\n', '~load,slow\n']
        if not self._send_command_set(message, "gridpattern"):
            return
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()
    
    
    def apply_whiteout(self):
        """ Apply a full whiteout to the DMD. (All ones, all mirrors flipped.) """
        self.logger.info("DMD applying whiteout pattern")
        message = ['~enable\n', '~fill,1\n', '~load,slow\n']
        if not self._send_command_set(message, "whiteout"):
            return
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()


    def apply_blackout(self):
        """ Apply a full blackout to the DMD. (All zeros, no mirrors flipped.) """
        self.logger.info("DMD applying blackout pattern")
        message = ['~enable\n', '~fill,0\n', '~load,slow\n']
        if not self._send_command_set(message, "blackout"):
            return
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['blackout'][0])
        self.update_dmd_plot()


    def apply_invert(self):
        """ Invert the last pattern on the DMD."""
        self.logger.info("Inverting pattern")
        message = ['~load_neg,slow\n']
        if not self._send_command_set(message, "invert"):
            return
        self.invert = not self.invert
        self.update_dmd_plot()


    def apply_antinvert(self):
        """ Undo the invert"""
        self.logger.info("Undoing inverted pattern")
        message = ['~load,slow\n']
        if not self._send_command_set(message, "antinvert"):
            return
        self.invert = not self.invert
        self.update_dmd_plot()


    def apply_current(self):
        """ Noop function to map the "current" shape of the DMD to a function. """
        self.logger.info("Asked to apply current pattern. Doing nothing.")


    def apply_shape(self, dm_shape, dm_num=1):
        """ 
        Function to apply a shape to the DMD. The DMD controller can set a
        row and repeat said row. The logic here to optimize does the following :
        
        1. Checks the specified shape against a few preloaded patterns. (Right
           now there's just all white/all black, but those patterns can be updated
           as needed.
        2. Figures out what rows need to be changed given we preset the closet
           pattern. 
        3. Figures out if any of those rows are the same and can be set with a
           repeat row command. 

        For example, if you wanted to set one column to black, we'd start with
        a whiteout, apply the first one with one black pixel, and repeat that
        row all the way down the controller. This would take 4 messages.
        (Start, apply row, repeat row, update and refresh controller.)

        We can set every row individually. Having tested a handful of examples,
        this takes 2ish minutes.

        Parameters
        ----------
        dm_shape : np.array
            Array of 1s/0s to apply to the DMD.
        dm_num : int
            Required parameter from DeformableMirror class.
        """
        self.logger.info("DMD applying custom shape to DMD")
        # flip the dmd shape to match the new orientation avoiding the pond mirrors
        dm_shape = self.flip_shape(dm_shape)    
        if dm_shape.shape != self.dmd_size:
            msg = f"Provided shape {dm_shape.shape} does not match DMD shape {self.dmd_size}."
            self.logger.error(msg)
            raise IndexError(msg)

        # Apply starting shape
        pre_shape, rows, columns = find_closest_match(dm_shape)
        pre_shape()
        rows = rows[0]

        # If we have notable deviation from that starting shape 
        if len(rows) > 0:
            messages = []
            # Start message to set default + display type
            messages.append(self._build_message(data=self.display_type))
            
            n = 0
            # Iterate through the pattern rows
            while n < len(dm_shape):
                # Build a message (only) for each row that diverges
                if n in rows:
                    # Check for repeated rows to save on commands
                    sums = np.sum(dm_shape != dm_shape[n], axis=1)
                    row_sums = np.array([np.sum(sums[n:n+i]) for i in range(1, len(sums)-n)])
                    
                    # Pad the end so we can pick up repeats at the bottom of the DMD
                    row_sums = np.array([elem for elem in row_sums] + [1])
                    indices = np.where(row_sums > 0)[0]
                    index = np.min(indices) if len(indices) > 0 else len(indices) + 1
                    
                    # Specify a single row with command
                    row_content = dm_shape[n]
                    msg = self._build_message(data_length=int(len(row_content)/8), command_type=1, row=n, data=row_content)
                    messages.append(msg)

                    if index > 1:
                        # Apply that row index - 1 times with command
                        messages.append(self._build_message(data_length=2, command_type=3, row=n+1, data=int(index-1)))
                        
                        # And move forward in the rows to where we are now
                        n += index
                    else:
                        # Otherwise we only scootch one position forward
                        n += 1
                # And likewise
                else:
                    n += 1

            # End / refresh message
            messages.append(self._build_message(data_length=0, command_type=7))            
            if not self._send_command_set(messages, "custom shape"):
                return
            # Update internal track of the DMD shape
            for row in rows:
                row_content = dm_shape[row]
                self.current_dmd_shape[row] = row_content
            self.update_dmd_plot()
        else:
            print(f'Shape perfectly matches {pre_shape.__name__} preset.')


    def find_closest_match(self, dm_shape):
        """ Find the closest default pattern."""
        if self.current_dmd_shape is not None:
            self._shapes['current'] = (self.current_dmd_shape, self.apply_current)
        
        min_shape_diff = self.max_diff
        shape_key = None
        
        # Loop through and iteratively reset until we have the lowest deviation
        for shape_key in self.shapes:
            shape = self.shapes[shape_key][0]
            shape_diff = np.absolute(shape - dm_shape)
            
            if np.sum(shape_diff) < min_shape_diff:
                row_adjustment = np.where(np.sum(shape_diff, axis=1) > 0)
                
                min_shape_diff = np.sum(shape_diff)
                shape_function = self.shapes[shape_key][1]
                
                #mr: we want to track also the columns
                col_adjustment = np.where(np.sum(shape_diff, axis=0) > 0) 

        return shape_function, row_adjustment, col_adjustment
          


    def update_dmd_plot(self, shape=None, plot_name='current_dmd_state'):
        """ Consistent plotting method to write out DMD plot. """
        self.logger.info("Updating current DMD plot")
        if shape is None:
            shape = self.current_dmd_shape
        shape[np.where(shape>0)] = 1
        if self.invert:
            shape = abs(shape-1)
        shape_rotated = np.rot90(shape, k=1, axes=(0, 1))
        plot_image = Image.fromarray(shape_rotated.astype("uint8")*255)
        plot_image.save(get_data_file("dmd") / "current_dmd_state.png")


    def _build_message(self, data_length=2, command_type=0, row=0, column=0, data=None):
        """
        Function to build messages for the DMD controller. 
        
        Parameters
        ----------
        data_length : int
            How many bits the message consists of.
        command_type : int
            What kind of command we send, 1-7. Notes follows.
        row : int
        column : int
            The place where the command update starts columnwise.
            The row we're updating or where we're starting to update.
        data : np.array
            The values to set for the row at hand or the number of rows to
            fill. (Defaults to None for start/end messages.)

        Returns
        -------
        message : str
            Str of hex code that represents a correct message to the
            controller.

        Notes
        -----
        Sample message :00200000000020C0 [CR]
        : 002 0 0000 00 0020 C0 [CR]
        [colon start of command] [packet with 2 8b words] 
        [default character / display type] [row address] [ column address]
        [data] [checksum] [end character]
        (This is the start and set default command.)

        Message types :
        - 0: default for unspecified values 
        - 1: write a single row
        - 2: fill row with default
        - 3: fill row with copy of last data
        - 4-6: reserved 
        - 7: end transmission / refresh display
        """
        # Start character
        message = ':'
        # Data length
        message += convert_int_to_n_hex(data_length, 3)
        # Message type
        message += convert_int_to_n_hex(command_type, 1)
        # Row address 
        message += convert_int_to_n_hex(row, 4)
        # Column address
        message += convert_int_to_n_hex(column, 2)
        # Add 00 data for defaults or calculate row hex
        
        # No data for update display command
        if data is None:
            data_hex = ''

        # Single int data for default set or set n rows command
        elif type(data) == int:
            data_hex = convert_int_to_n_hex(data, data_length*2)
        
        # Otherwise we'll have an array of of bits to convert to bytes to send
        # to the controller to set a single row
        else:
            data_hex = ''

            # Convert 8 bits at a time into bytes
            for byte_index in np.arange(0, len(data), 8):
                byte = self._calculate_byte(data[byte_index:byte_index+8])
                data_hex += byte
        
        message += data_hex
        
        # Checksum 
        checksum_int = self._calculate_checksum(message)[0]
        message += convert_int_to_n_hex(checksum_int, 2)
        
        # Add end character
        message = message.upper() + '\n' 
        
        return message


    def convert_int_to_n_hex(self, integer, length):
        """ Convenience function to convert an integer to some number of bytes."""
        
        # Gives us something like 0x14 (but could be 0xNNNN --> 0xN)
        hex_convert = hex(integer)
        
        # Taking only the numerical characters
        numerical = hex_convert.split('x')[-1]
        
        # Pad with zeros so shorter ints still are the right length
        padded_hex = length*'0' + numerical
        hex_int = padded_hex[-1*length:]

        return hex_int
        
    
    def _calculate_byte(self, hex_array):
        """ Calculates a byte from 8 hex bits.

        Parameters
        ----------
        hex_array : np.array 
            Array of 8 1s or 0s.

        Returns
        -------
        byte : str
            Str of hex.
        """

        if len(hex_array) != 8:
            raise IndexError("Hex array is the wrong size.")
        
        hex_array = np.array(np.array(hex_array, dtype=int), dtype='str')
        bit_sum = ''
        for bit in hex_array:
            # Reverse the order of the bits
            bit_sum = bit + bit_sum
        int_value = int(bit_sum, 2)
        hex_value = hex(int_value)
        
        # Pad in case it's a one digit
        hex_value = '00' + hex_value.split('x')[-1]
        byte = hex_value[-2:]

        return byte


    def _calculate_checksum(self, str_byte_message): 
        """  
        Calculates the checksum for a message. 
         
        Parameters 
        ---------- 
        str_byte_message : str
            Str message of hex bytes. 
        
        Returns 
        ------- 
        checksum : tuple 
            The checksum in int and str of hex form. 
        
        Notes
        -----
        # 0x00 + 0x20 + 0x00 + 0x00 + 0x00 + 0x00 + 0x20 = 0x0040 = 0x40
        # 0xFF - 0x40 = 0xC0 
        # to verify :00200000000020C0 [CR]
        # 0x00 + 0x20 + 0x00 + 0x00 + 0x00 + 0x20 + 0xC0 = 0x0100 + 0x00 = 0
        
        """
        if str_byte_message[0] == ':':
            str_byte_message = str_byte_message[1:]
        
        # Split the str message into bits
        byte_list = [f'0x{str_byte_message[n:n+2]}' for n in np.arange(0, len(str_byte_message), 2)] 
        byte_sum = 0 
        
        for byte in byte_list: 
            # convert the bit into an integer
            byte_sum += int(byte, 16) 

        # Pull the least significant bit
        byte_digits = hex(byte_sum).split('x')[-1][-2:] 

        # Calculate the two's complement 
        checksum = int('0xff', 16) - int(f'0x{byte_digits}', 16) + 1 
        
        return checksum, hex(checksum)


    def apply_slits(self, slits, dm_num=1):
        """
        Convert a set of slits into a custom shape, and then apply them using that code.
        """
        self.logger.info("DMD Applying slit set")
        dm_shape= np.ones((1080,2048))
        for slit in slits:
            self.logger.info("DMD applying slit {}".format(slit))
            dm_shape[slit['x1']:slit['x2']+1,slit['y1']:slit['y2']+1] = 0
        self.apply_shape(dm_shape, dm_num=1)


    def flush(self, iterations=None):
        """
        Flush the DMD state by applying repeated whiteout/blackout sequences.
        """
        i=0
        try:
            while True:
                    self.apply_blackout()
                    time.sleep(0.2)
                    self.apply_whiteout()
                    if iterations is not None:
                        self.logger.warning("DMD Flush Loop: Iteration {} of {}".format(i, iterations))
                    else:
                        self.logger.warning("DMD Flush Loop: Iteration {}".format(i))
                    time.sleep(0.2)
                    i += 1
                    if (iterations is not None) and (i > iterations):
                        break
        except KeyboardInterrupt:
            self.logger.warning("DMD Flush Loop interrupted by user. Terminating.")


    def flip_shape(self,dm_shape):
        "flip the dmd shape to match the new orientation avoiding the pond mirrors"
        #1. rotate array, from https://stackoverflow.com/questions/8421337/rotating-a-two-dimensional-array-in-python
        list_of_tuples = zip(*dm_shape[::-1]) 
        rotated_1 = [list(elem) for elem in list_of_tuples]
        list_of_tuples = zip(*rotated_1[::-1])
        rotated_2 = [list(elem) for elem in list_of_tuples]
        dm_shape_flipped = np.array(rotated_2) * (-1) + 1
        return dm_shape_flipped


    def _send_command_set(self, message, note):
        """
        Wraps sending a list of messages in a try/except block, and prints out a semi-
        custom error message, then returns false, on any failure.
        """
        if self.db.get_value("config_ip_location", default="disconnected") == "connected":
            try:
                for m in message:
                    self.send(m)
            except Exception as e:
                self.logger.error("Failed to apply {}".format(note))
                return False
        return True


    def _get_address(self):
        """
        Get the current IP address and port from the parameters class
        """
        ip_port = self.db.get_value("config_ip_dmd", default="none").split(":")
        dmd_ip = ip_port[0]
        dmd_port = int(ip_port[1])
        return dmd_ip, dmd_port
