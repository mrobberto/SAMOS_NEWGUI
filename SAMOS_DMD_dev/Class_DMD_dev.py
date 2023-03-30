import os
import socket

import matplotlib.pyplot as plt
import numpy as np
import time

import codecs
#from catkit.interfaces.DeformableMirrorController import DeformableMirrorController

#import SAMOS functions to handle IP addresses
import sys
from pathlib import Path
#define the local directory, absolute so it is not messed up when this is called
path = Path(__file__).parent.absolute()
local_dir = str(path.absolute())
sys.path.append(os.path.join(path.parent,'SAMOS_system_dev'))
from SAMOS_Functions import Class_SAMOS_Functions as SF

#class DigitalMicroMirrorDevice(DeformableMirrorController):
class DigitalMicroMirrorDevice():
    """ Class to control the Digital Micromirror Array created by the JHU
    Instrument Development Group. This has been designed around and tested with
    a DLP7000, which is a 768x1024 pixel device, but should be generalizable to
    other sizes, etc. 

    Parameters
    ----------
    config_id : str
        ID to map the controller to device specifics. 
    address : str
        Address for the scoket connection. NOTE : this will almost definitely
        change when the DMD gets a more permanent home?
    port : int
        Port number for the socket connection.
    start_on_whiteout : bool
        Whether to apply a whiteout to the controller to start. 
    max_diff : int
        How many pixels different the potential shape could be from a base
        pattern. If set to None, it will be calculated from the ``dmd_shape``.
    dmd_size : tuple of ints
        Size of the dmd_controller. 
    display_type : int
        Display type for the DMD.
    dmd_data_path : str
        Where to write out data and plots.
    """
    instrument_lib = socket    
    


    def __init__(self):
        #read the IP addresses
        all_IPs = SF.read_IP_default()
        #select the one for the DMD controller and split the ID and the port
        i_columns=all_IPs['IP_DMD'].find(':')
        
        self.DMD_IP = all_IPs['IP_DMD'][0:i_columns]
        self.DMD_port = int(all_IPs['IP_DMD'][i_columns+1:])
        #print(self.DMD_IP,self.DMD_port)
#        self.params = {'Host': '128.220.146.254', 'Port': 8888}
        self.params = {'Host': self.DMD_IP, 'Port': self.DMD_port}
        #print(self.params)
        self.invert = False
#         
     
# =============================================================================
#     def initialize(self, config_id='dlp_7000', address='prolix.dynamic-dns.net', port=1000,
#                    start_on_whiteout=True, max_diff=786432, dmd_size=(768, 1024), 
#                    display_type=32, dmd_data_path='.'):
# =============================================================================
    def initialize(self, config_id='DC2K', 
#                   address='172.16.0.141',port=8888,# 
                   address='172.16.0.141', port=8888,
                   start_on_whiteout=False, max_diff=2211840, dmd_size=(1080,2048), 
                   display_type=32, dmd_data_path='.'):
        
        """ Initial function for the DMD Controller."""
        hostname = socket.gethostname()
        #for some reason the 
        # local_ip = socket.gethostbyname(hostname)
        #line does not t
        local_ip = '172.16.1.108'
        
        print("hostname: %s"%(hostname))
        print("local IP: %s"%(local_ip))
        print("DMD IP: %s"%(address))
        self.address = address
        
        self.port = port
        
        self.start_on_whiteout = start_on_whiteout
        self.dmd_size = dmd_size
        self.max_diff = dmd_size[0]*dmd_size[1] if max_diff is None else max_diff
        self.display_type = display_type
        self.dmd_data_path = dmd_data_path
        
        self._shapes = {'blackout': (np.zeros(self.dmd_size), self.apply_blackout), 
                        'whiteout': (np.ones(self.dmd_size), self.apply_whiteout)}
                        # add more if any other common shapes pop up? 
        self.current_dmd_shape = None

    def _open(self):
        """ Opens a connection to the DMD device. The socket connection will
        time out after a few seconds of inactivity, so this is less opening a
        constant connection and more testing our connection method responds as
        expected."""

        # Connection is reset every ~10 seconds
        instrument = self.instrument_lib.socket(self.instrument_lib.AF_INET, self.instrument_lib.SOCK_STREAM)
#        instrument.connect((self.address, self.port))

        try:
            instrument.connect((self.address, self.port))
        except:
            print("no DMD")
            return("no DMD")
            
        # If we get this far, a connection has been successfully opened.
        # Set self.instrument so that we can close if anything here subsequently fails.
        self.instrument = instrument

        # Send a test message to make sure this worked 
        instrument.sendall(b':TEST\n')
        response = instrument.recv(100)
     #   if 'INVALID' not in response:
    #        raise ConnectionError(f'The socket is not responding as expected, test message responded with {response}.')
     #   else:
        print(response)
        return(response)
        
        # Apply a whiteout to start 
#        if self._start_on_whiteout:
#            self.apply_whiteout()
     
    def _close(self):
        self.instrument.close()

    @property
    def shapes(self):
        """ Make a property so our core shapes are indeditable."""
        return self._shapes

    def send(self, command):
        """ Send a message to the controller and check the controller
        sucessfully received it."""

        # reinstantiate connection since it times out
        instrument = self.instrument_lib.socket(self.instrument_lib.AF_INET, self.instrument_lib.SOCK_STREAM)
        instrument.connect((self.address, self.port))
        
        # Check the command message type
        ##> [mr]: try to send all commands in a single string
        if type(command) == list:
            message_type = command[-1][4]
            command = ''.join(command)
        else:
        ##<     
            message_type = command[4]

        # Send command
#        command = ':00200000000040A0\n:0002020000FC\n:0023020100005585\n:0007000000F9\n'
#        instrument.sendall(command.encode())
        instrument.sendall(codecs.encode(command,'utf-8'))
#        response = str(instrument.recv(30))
        
        """OLD"""
        data = instrument.recv(300)
        """NEW"""
        #instrument.setblocking(0)
        #timeout_in_seconds = 2
        #import select
        #ready = select.select([instrument], [], [], timeout_in_seconds)
        
        #if ready[0]:
        #    data = instrument.recv(4096)
        #    print("instrument is ready", ready)
        #else:
        #    print("not ready?")
        #    print(instrument)
            
        
        response = data.decode('ascii')
        print('response: ',response)
        # Make sure we successfully send the command, and the message type matches
# =============================================================================
#         if 'SUCCESS' in response and message_type in response:
#             # log or print?
#             print(f'Message: {command[:-1]} sucessfully written.')
#         elif 'INVALID COMMAND' in response:
#             raise ValueError("An invalid command was sent to the controller.")
#         elif response == b'':
#             raise RuntimeError("The controller is not responding as if a message was sent.")
#         else:
#             raise RuntimeError(f"Message {command} failed in an unexpected way with {response}.")
# =============================================================================

        if 'invalid ~ command' in response and message_type in response:
            raise ValueError("An invalid command was sent to the controller.")
        elif response == b'':
            raise RuntimeError("The controller is not responding as if a message was sent.")
        else:  
            print(f'Message: {command[:-1]} sucessfully written.')
    
    
    def apply_checkerboard(self):
        """ Apply a checkerboard to the DMD. """
        
        message = ['~enable\n',
                   '~test,0\n',
                   '~load,slow\n']
        
        for m in message:
             self.send(m)
             
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()

    def apply_dotpattern(self):
        """ Apply a dotpattern to the DMD. """
        
        message = ['~enable\n',
                   '~test,1\n',
                   '~load,slow\n']
        
        for m in message:
              self.send(m)
        
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()
 
    def apply_gridpattern(self):
        """ Apply a gridpattern to the DMD. """
        
        message = ['~enable\n',
                   '~test,2\n',
                   '~load,slow\n']
        
        for m in message:
            self.send(m)
            
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()
    

    
    def apply_whiteout(self):
        """ Apply a full whiteout to the DMD. (All ones, all mirrors flipped.) """
        
        message = ['~enable\n',
                   '~fill,1\n',
                   '~load,slow\n']

# =============================================================================
#         message = [':00200000000020C0\n',   #>002< : MESSAGE LENGTH (will be 00,20)
#                                             #002 >0< : DEFAULT VALUE SETTING
#                                             #0020 >0000< : ROW ADDRESS = 0000
#                                             #00200000 >00< : COLUMN ADDRESS = 00
#                                             #0020000000 >0020< : DATA FOR DEFAULT RECORD = 0020
#                                             #00200000000020 >C0< : CHECKSUM                                           
#                    ':08010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F7\n',
#                                             #>080< MESSAGE LENGTH (X80 = 128 pairs of 00/FF=8 bits, or 1024 0 bits)
#                                             #080 >1< : DATA RECORD 
#                                             #0801 >0000< : ROW ADDRESS = 0000
#                                             #08010000 >00< : COLUMN ADDRESS = 00
#                                             #0020000000 >0...0< :  0 x 256 = 1024 bits/pixels set to 0 = 0020
#                                             #00200000000..0 >F7< : CHECKSUM                        
#                    ':00230001000300D9\n',   #>002< : MESSAGE LENGTH (will be 00,20)
#                                             #002 >3< : REPEAT FILL last line x number of lines
#                                             #0023 >0001< : ROW ADDRESS = 0001
#                                             #00230001 >00< : COLUMN ADDRESS = 00
#                                             #0023000100 >0300< : X0300 = 768: Number of Rows to repeat fill
#                                             #00230001000300 >D9< : CHECKSUM               
#                    
#                    ':0007000000F9\n']       #>000< : MESSAGE LENGTH (will be 00,20)
#                                             #000 >7< : UPLOAD TO DISPLAY
#                                             #0007 >0000< : ROW ADDRESS = 0001
#                                             #00070000 >00< : COLUMN ADDRESS = 00
#                                             #0007000000 >F9< : CHECKSUM            
#         
# =============================================================================
        self.send(message)
#        for m in message:
#            self.send(m)
        
        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()



    def apply_blackout(self):
        """ Apply a full blackout to the DMD. (All zeros, no mirrors flipped.) """

        message = ['~enable\n',
                   '~fill,0\n',
                   '~load,slow\n']

# =============================================================================
#         message = [':00200000000020C0\n',
#                    ':0801000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF77\n',
#                    ':00230001000300D9\n',
#                    ':0007000000F9\n']
# =============================================================================

        for m in message:
            self.send(m)

        self.invert = False
        self.current_dmd_shape = np.copy(self.shapes['blackout'][0])
        self.update_dmd_plot()
        
        

    def apply_invert(self):
        """ Invert the last pattern on the DMD. (All ones, all mirrors flipped.) """
        
        message = ['~load_neg,slow\n']

        for m in message:
            self.send(m)
        
        self.invert = not self.invert
        #self.current_dmd_shape = np.copy(self.shapes['blackout'][0])
        self.update_dmd_plot()

    def apply_antinvert(self):
        """ Undo the invert"""
        
        message = ['~load,slow\n']

        self.invert = not self.invert
        for m in message:
            self.send(m)
        
        #self.current_dmd_shape = np.copy(self.shapes['blackout'][0])
        self.update_dmd_plot()

    def apply_current(self):
        """ Noop function to map the "current" shape of the DMD to a function. """
        pass

    def apply_shape(self, dm_shape, dm_num=1):
        """ Function to apply a shape to the DMD. The DMD controller can set a
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
        
        #self.update_dmd_plot(shape=dm_shape, plot_name='attempted_dmd_shape')

        if dm_shape.shape != self.dmd_size:
            raise IndexError(f"Given shape to apply to DMD is of size {dm_shape.shape}, while we expect the DMD to be of size {self.dmd_size}.")

        def find_closest_match(dm_shape):
            """ Find the closest default pattern."""

            if self.current_dmd_shape is not None:
                self._shapes['current'] = (self.current_dmd_shape,
                        self.apply_current)
            
            min_shape_diff = self.max_diff
            shape_key = None
            
            # Loop through and iteratively reset until we have the lowest deviation
            for shape_key in self.shapes.keys():
                shape = self.shapes[shape_key][0]
                shape_diff = np.absolute(shape - dm_shape)
                
                if np.sum(shape_diff) < min_shape_diff:
                    row_adjustment = np.where(np.sum(shape_diff, axis=1) > 0)
                    
                    min_shape_diff = np.sum(shape_diff)
                    shape_function = self.shapes[shape_key][1]
                    
                    #mr: we want to track also the columns
                    col_adjustment = np.where(np.sum(shape_diff, axis=0) > 0) 

            #mr therefore I add col_adjustemt 
            return shape_function, row_adjustment
#            return shape_function, row_adjustment, col_adjustment
          
        # Apply starting shape
        #adding the columns also here...
        pre_shape, rows = find_closest_match(dm_shape)
#        pre_shape, rows, columns = find_closest_match(dm_shape)
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
                    
                    
# =============================================================================
#                     ##################################################
#                     ## Here is where we compact the row
#                     cols = np.array(columns)[0]
#                     #ncolumns = len(cols)
#                     column = int(cols[0]/8)
#                     #counting the number of bytes
#                     #nchar = 1
# #                    arr=((cols-column*8-1)% 8)
#                     arr=(cols-column*8)#-1)
#                     nchar = int(np.ceil(max(arr / 8)))
#                     #for i in range(len(arr)-1):
#                     #    if arr[i]>arr[i+1]:
#                     #        nchar+=1
#                     #column = int(cols[0]/8)
#                     ncolumns = np.zeros(nchar*8, dtype=int)
#                     ncolumns[arr]=1
#                     #here below 
#                     # ncolumns=(0,0,0,0, 1,1,1,1, 1,1,0,0, 0,0,0,0)
#                     #becomes
#                     # ncolumns=(1,1,1,1, 0,0,0,0, 0,0,0,0, 0,0,1,1)
#                     print(ncolumns)
# # =============================================================================
# #                     v=[]
# #                     for i in range(nchar):
# #                         #print(i,ncolumns[0+(i*8):8+(i*8)])
# #                         #print(i,np.flip(ncolumns[0+(i*8):8+(i*8)]))
# #                         v=np.concatenate((v,np.flip(ncolumns[0+(i*8):8+(i*8)])))
# #                         #print(v)
# #                     ncolumns = v    
# #                     print(ncolumns)
# # 
# # =============================================================================
#                     messages.append(self._build_message(data_length=nchar,
#                                                         command_type=1, row=n, column=column, 
#                                                         data=ncolumns))
#                     ######################################################
# =============================================================================

                    # Specify a single row with command
                    row_content = dm_shape[n]
                    #####
                    #####
                    messages.append(self._build_message(data_length=int(len(row_content)/8),
                                                        command_type=1, row=n, 
                                                        data=row_content))

                    if index > 1:
                        # Apply that row index - 1 times with command
                        messages.append(self._build_message(data_length=2,
                            command_type=3, row=n+1, data=int(index-1)))
                        
                        # And move forward in the rows to where we are now
                        n += index
                    
                    # Otherwise we only scootch one position forward
                    else:
                        n += 1
                
                # And likewise
                else:
                    n += 1

            # End / refresh message
            messages.append(self._build_message(data_length=0, command_type=7))
 
            self.send(messages)    
#            for message in messages:
#                self.send(message)
            
            # Update internal track of the DMD shape
            for row in rows:
                row_content = dm_shape[row]
                self.current_dmd_shape[row] = row_content
            
            self.update_dmd_plot()
        
        else:
            print(f'Shape perfectly matches {pre_shape.__name__} preset.')
    
    def update_dmd_plot(self, shape=None, plot_name='current_dmd_state'):
        """ Consistent plotting method to write out DMD plot. """
        
        # No shape input means we plot out the current DMD shape.
        shape = shape if shape is not None else self.current_dmd_shape
        if self.invert == True:
            shape = abs(shape-1)
        
        plt.clf()
        shape_rotated = np.rot90(shape, k=1, axes=(0, 1))
        plt.imshow(shape_rotated, vmin=0, vmax=1)
        plt.colorbar()
        plt.savefig(local_dir + "/current_dmd_state.png")
        plt.close()  #needed to overwrite!
    
    def _build_message(self, data_length=2, command_type=0, row=0, column=0, data=None):
        """Function to build messages for the DMD controller. 
        
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
        
        def convert_int_to_n_hex(integer, length):
            """ Convenience function to convert an integer to some number of
            bytes."""
            
            # Gives us something like 0x14 (but could be 0xNNNN --> 0xN)
            hex_convert = hex(integer)
            
            # Taking only the numerical characters
            numerical = hex_convert.split('x')[-1]
            
            # Pad with zeros so shorter ints still are the right length
            padded_hex = length*'0' + numerical
            hex_int = padded_hex[-1*length:]

            return hex_int
        
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
        
        """  Calculates the checksum for a message. 
         
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
    
    def echo_client(self,string):
        
        import socket
        
        
        HOST = self.address  # The server's hostname or IP address
        PORT = self.port     # The port used by the server
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall( bytes(string, 'utf-8'))
            data = s.recv(1024)
        
        print('Received', repr(data))
        
        
    
    def send_smart_whiteout(self):
        """ Apply a full whiteout to the DMD. (All ones, all mirrors flipped.) """
        

        message = [':00200000000040A0\n',   #>002< : MESSAGE LENGTH (will be 00,20)
                                            #002 >0< : DEFAULT VALUE SETTING
                                            #0020 >0000< : ROW ADDRESS = 0000
                                            #00200000 >00< : COLUMN ADDRESS = 00
                                            #0020000000 >0020< : DATA FOR DEFAULT RECORD = 0020
                                            #00200000000020 >C0< : CHECKSUM                                           
                    ':0002020000FC\n',
                    ':0023020100005585\n',

# =============================================================================
#                     ':08010000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000F7\n',
#                                             #>080< MESSAGE LENGTH (X80 = 128 pairs of 00/FF=8 bits, or 1024 0 bits)
#                                             #080 >1< : DATA RECORD 
#                                             #0801 >0000< : ROW ADDRESS = 0000
#                                             #08010000 >00< : COLUMN ADDRESS = 00
#                                             #0020000000 >0...0< :  0 x 256 = 1024 bits/pixels set to 0 = 0020
#                                             #00200000000..0 >F7< : CHECKSUM                        
#                    ':00230001000300D9\n',   #>002< : MESSAGE LENGTH (will be 00,20)
#                                             #002 >3< : REPEAT FILL last line x number of lines
#                                             #0023 >0001< : ROW ADDRESS = 0001
#                                             #00230001 >00< : COLUMN ADDRESS = 00
#                                             #0023000100 >0300< : X0300 = 768: Number of Rows to repeat fill
# =============================================================================
                                            #00230001000300 >D9< : CHECKSUM               
                   
                   ':0007000000F9\n']       #>000< : MESSAGE LENGTH 
                                            #000 >7< : UPLOAD TO DISPLAY
                                            #0007 >0000< : ROW ADDRESS = 0000
                                            #00070000 >00< : COLUMN ADDRESS = 00
                                            #0007000000 >F9< : CHECKSUM            
        
        self.send(message)
#        for m in message:
#            self.send(m)
        
        self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
        self.update_dmd_plot()
    

    def send_smart_column(self):
       """ Apply a vertical column to the DMD. (of ones, all other mirrors at 0=white) """
        
        #first line: defaault
       message = [':00200000000040A0\n',   #>002< : MESSAGE LENGTH (will be 00,20, therefore 2 bytes)
                                            #002 >0< : MESSAGE TYPE = 0 (default value to be set)
                                            #0020 >0000< : ROW ADDRESS = 0000
                                            #00200000 >00< : COLUMN ADDRESS = 00
                                            #0020000000 >0020< : MESSAGE DATA: For MESSAGE TYPE = 0: DEFAULT RECORD = 0020 (00 fill value, 20=32 bit bus for DLP7000)
                                            #00200000000020 >C0< : CHECKSUM                                           
        #second line: 
#                    ':0002020000FC\n',      #000< : MESSAGE LENGTH
                                            #000 >2< : DEFAULT Fill Line with default value up to...
                                            #0002 >0200< : ROW ADDRESS = 512
                                            #00020200 >00< : COLUMN ADDRESS = 0
                                            
        #third line:
#                    ':0023020100005585\n',  #>002< : MESSAGE LENGTH (will be 00,55)
                                            #002 >3< : REPEAT FILL last line x number of lines
                                            #0023 >0201< : ROW ADDRESS = 513
                                            #00230201 >00< : COLUMN ADDRESS = 00
                                            #0023000100 >0055< : X0055 = d85: Number of Rows  (85)to repeat fill                    

                    ':0007000000F9\n']      #>000< : MESSAGE LENGTH 
                                            #000 >7< : UPLOAD TO DISPLAY
                                            #0007 >0000< : ROW ADDRESS = 0000
                                            #00070000 >00< : COLUMN ADDRESS = 00
                                            #0007000000 >F9< : CHECKSUM            
 
       for m in message:
            self.send(m)
        
       self.current_dmd_shape = np.copy(self.shapes['whiteout'][0])
       self.update_dmd_plot()



    def send_smart_box(self,x0,x1,y0,y1):

        
        #first line: default fill line value setting 
        message = [':00200000000040A0\n',   #>002< : MESSAGE LENGTH (will be 00,20, therefore 2 bytes)
                                            #002 >0< : MESSAGE TYPE = 0 (default value to be set)
                                            #0020 >0000< : ROW ADDRESS = 0000
                                            #00200000 >00< : COLUMN ADDRESS = 00
                                            #0020000000 >0020< : MESSAGE DATA: For MESSAGE TYPE = 0: DEFAULT RECORD = 0020 (00 fill value, 20=32 bit bus for DLP7000)
                                            #00200000000020 >C0< : CHECKSUM                                           
  
        #second line:
                    ':0023020100005585\n',  #>002< : MESSAGE LENGTH (will be 00,55)
                                            #002 >3< : MESSAGE TYPE = 3 (REPEAT FILL last line x number of lines)
                                            #0023 >0201< : ROW ADDRESS = 513
                                            #00230201 >00< : COLUMN ADDRESS = 00
                                            #0023000100 >0055< : MESSAGE DATA: For MESSAGE TYPE = 3: X0055 = d85: Number of Rows  (85) to repeat fill                    
        
        #third line:
                    ':0007000000F9\n']      #>000< : MESSAGE LENGTH 
                                            #000 >7< : MESSAGE TYPE = 7 UPLOAD TO DISPLAY
                                            #0007 >0000< : ROW ADDRESS = 0000
                                            #00070000 >00< : COLUMN ADDRESS = 00
                                            #0007000000 >F9< : CHECKSUM            
       


    def send_smart_message(self):
        pass

    def apply_slits(self, slits, dm_num=1):
        dm_shape= np.ones((1080,2048))
        for slit in slits:
            print(slit)
            dm_shape[slit['x1']:slit['x2']+1,slit['y1']:slit['y2']+1] = 0
        self.apply_shape(dm_shape, dm_num=1)

    def apply_slits_old(self, slits, dm_num=1):
        """ Function to apply a shape to the DMD. The DMD controller can set a
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
        
        dm_shape= np.ones((1080,2048))
        for slit in slits:
            print(slit)
            dm_shape[slit['x1']:slit['x2']+1,slit['y1']:slit['y2']+1] = 0
            
        
        #self.update_dmd_plot(shape=dm_shape, plot_name='attempted_dmd_shape')

        if dm_shape.shape != self.dmd_size:
            raise IndexError(f"Given shape to apply to DMD is of size {dm_shape.shape}, while we expect the DMD to be of size {self.dmd_size}.")

        def find_closest_match(dm_shape):
            """ Find the closest default pattern."""

            if self.current_dmd_shape is not None:
                self._shapes['current'] = (self.current_dmd_shape,
                        self.apply_current)
            
            min_shape_diff = self.max_diff
            shape_key = None
            
            # Loop through and iteratively reset until we have the lowest deviation
            for shape_key in self.shapes.keys():
                shape = self.shapes[shape_key][0]
                shape_diff = np.absolute(shape - dm_shape)
                
                if np.sum(shape_diff) < min_shape_diff:
                    row_adjustment = np.where(np.sum(shape_diff, axis=1) > 0)
                    
                    min_shape_diff = np.sum(shape_diff)
                    shape_function = self.shapes[shape_key][1]
                    
                    #mr: we want to track also the columns
                    col_adjustment = np.where(np.sum(shape_diff, axis=0) > 0) 

            #mr therefore I add col_adjustemt 
#            return shape_function, row_adjustment
            return shape_function, row_adjustment, col_adjustment
          
        messages = []
        # Start message to set default + display type
        messages.append(self._build_message(data=self.display_type))

        for slit in slits:
            dm_shape_slit = np.ones((1080,2048))
            print(slit)
            dm_shape_slit[slit['x1']:slit['x2']+1,slit['y1']:slit['y2']+1] = 0
            
           # Apply starting shape
            #adding the columns also here...
    #        pre_shape, rows = find_closest_match(dm_shape_slit)
            pre_shape, rows, columns = find_closest_match(dm_shape_slit)
            if slit['index'] == 1:
                pre_shape()
            rows = rows[0]
        
            # If we have notable deviation from that starting shape 
            if len(rows) > 0:
               
                n = 0
                # Iterate through the pattern rows
                while n < len(dm_shape_slit):
                    
                    # Build a message (only) for each row that diverges
                    if n in rows:
                        
                        # Check for repeated rows to save on commands
                        sums = np.sum(dm_shape_slit != dm_shape_slit[n], axis=1)
                        row_sums = np.array([np.sum(sums[n:n+i]) for i in range(1, len(sums)-n)])
                        
                        # Pad the end so we can pick up repeats at the bottom of the DMD
                        row_sums = np.array([elem for elem in row_sums] + [1])
                        indices = np.where(row_sums > 0)[0]
                        index = np.min(indices) if len(indices) > 0 else len(indices) + 1
                                                
                        
                        ##################################################
                        ## Here is where we compact the row
                        cols = np.array(columns)[0]
                        #ncolumns = len(cols)
                        column = int(cols[0]/8)
                        #counting the number of bytes
                        #nchar = 1
    #                    arr=((cols-column*8-1)% 8)
                        arr=(cols-column*8)#-1)
                        nchar = int(np.ceil(max(arr / 7)))
                        #for i in range(len(arr)-1):
                        #    if arr[i]>arr[i+1]:
                        #        nchar+=1
                        #column = int(cols[0]/8)
                        ncolumns = np.zeros(nchar*8, dtype=int)
                        ncolumns[arr]=1
                        #here below 
                        # ncolumns=(0,0,0,0, 1,1,1,1, 1,1,0,0, 0,0,0,0)
                        #becomes
                        # ncolumns=(1,1,1,1, 0,0,0,0, 0,0,0,0, 0,0,1,1)
                        print('ncolumns: ',ncolumns)
                        print('n :',n,'\n column: ',column)
    # =============================================================================
# =============================================================================
#                         v=[]
#                         for i in range(nchar):
#                             #print(i,ncolumns[0+(i*8):8+(i*8)])
#                             #print(i,np.flip(ncolumns[0+(i*8):8+(i*8)]))
#                             v=np.concatenate((v,np.flip(ncolumns[0+(i*8):8+(i*8)])))
#                             #print(v)
#                         ncolumns = v    
#                         print(ncolumns)
#     # =============================================================================
# =============================================================================
                        messages.append(self._build_message(data_length=nchar,
                                                            command_type=1, row=n, column=column, 
#                                                            data=rows))
                                                            data=ncolumns))
                        ######################################################
    
    # =============================================================================
    #                     # Specify a single row with command
    #                     row_content = dm_shape_slit[n]
    #                     #####
    #                     #####
    #                     messages.append(self._build_message(data_length=int(len(row_content)/8),
    #                                                         command_type=1, row=n, 
    #                                                         data=row_content))
    # 
    # =============================================================================
                        if index > 1:
                            # Apply that row index - 1 times with command
                            messages.append(self._build_message(data_length=2,
 #                               command_type=3, row=n+1, data=int(index-1)))
                                command_type=3, data=int(index-1)))
                            
                            # And move forward in the rows to where we are now
                            n += index
                        
                        # Otherwise we only scootch one position forward
                        else:
                            n += 1
                    
                    # And likewise
                    else:
                        n += 1

            # End / refresh message
        messages.append(self._build_message(data_length=0, command_type=7))
 
        self.send(messages)    
#            for message in messages:
#                self.send(message)
            
            # Update internal track of the DMD shape
        for row in rows:
            row_content = dm_shape[row]
            self.current_dmd_shape[row] = row_content
            
        self.update_dmd_plot(shape=dm_shape)
        
#     else:
#            print(f'Shape perfectly matches {pre_shape.__name__} preset.')

    def flush(self):
        i=0
        try:
            while True:
                    self.apply_blackout()
                    time.sleep(0.2)
                    self.apply_whiteout()
                    print(i, "Flush loop")
                    time.sleep(0.2)
                    i = i+1
        except KeyboardInterrupt:
            pass
        
    def flip_shape(dm_shape):
        "flip the dmd shape to match the new orientation avoiding the pond mirrors"
        
        #1. rotate array, from https://stackoverflow.com/questions/8421337/rotating-a-two-dimensional-array-in-python
        list_of_tuples = zip(*dm_shape[::-1]) 
        rotated_1 = [list(elem) for elem in list_of_tuples]
        list_of_tuples = zip(*rotated_1[::-1])
        return [list(elem) for elem in list_of_tuples]