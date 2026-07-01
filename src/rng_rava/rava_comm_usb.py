"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
USB transport implementation for RAVA devices.

This module provides device discovery and a USB communication interface built on top of pySerial.
It is responsible for locating RAVA devices, opening and closing USB connections, and performing
raw byte-level I/O with disconnection detection.
"""

import serial
from serial.tools.list_ports import comports

from .rava_comm import RAVAComm, COMM_READ_TIMEOUT_S
from .rava_errors import RAVAConnectError, RAVAClosedError, RAVADisconnectedError, RAVAWriteError

############################
# RAVA COMM USB
############################


RAVA_USB_VID = 0x1209
RAVA_USB_PID = 0x4884


def find_rava_sns(usb_vid=RAVA_USB_VID, usb_pid=RAVA_USB_PID):
    """
    Find connected RAVA USB devices, returning a list of device serial numbers.
    """

    sns = [ 
        port_info.serial_number for port_info in comports()        
        if ( 
            port_info.vid == usb_vid and
            port_info.pid == usb_pid and
            port_info.serial_number is not None 
            ) 
        ]
    sns.sort()
    return sns


class RAVACommUsb(RAVAComm):
    """
    USB communication transport for RAVA devices.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVACommUsb'
        self.name_conn = ''        

        self.usb = serial.Serial(timeout=COMM_READ_TIMEOUT_S)
      

    def is_open(self):
        """
        Test whether the USB connection is locally open.

        This method does not detect unexpected device disconnections.
        """

        return self.usb.is_open


    def open(self, rava_sn):
        """
        Open a USB connection to a RAVA device with serial number `rava_sn`.
        """

        if isinstance(rava_sn, bytes):
            rava_sn = rava_sn.decode()

        # Find port associated to SN
        ports = [
            port_info.device for port_info in comports() 
            if port_info.serial_number == rava_sn
            ]
        
        if not ports:            
            raise RAVAConnectError(
                f'{self.name} open -> No device found for SN={rava_sn} :-('
                )

        port = ports[0]

        # Already open? Close first
        if self.usb.is_open:
            self.close()

        # Open connection to port
        self.usb.port = port
        try:
            self.usb.open()

        except serial.SerialException as err:            
            raise RAVAConnectError(
                f'{self.name} open -> Could not open SN={rava_sn} @ {port} :-('
                ) from err

        # Reset buffers
        self.usb.reset_input_buffer()
        self.usb.reset_output_buffer()

        # Log
        self.log.info(f'{self.name} open -> Connected to SN={rava_sn} @ {port} :-)')

        # RAVAComm open
        super().open()

        # Update connection identifier
        self.name_conn = f': SN={self.serial_number} @ {port}'


    def close(self):
        """
        Close the USB connection and stop communication.
        """

        # RAVAComm close
        super().close()

        # Close USB connection
        try:
            if self.is_open():
                self.usb.close()

                # Log
                self.log.info(f'{self.name} close {self.name_conn} -> Connection closed')
        except:
            pass


    def bytes_waiting(self):
        """
        Return the number of bytes available for reading.
        """

        # Open?
        if not self.is_open():
            raise RAVAClosedError(
                f'{self.name} bytes_waiting {self.name_conn} -> Attempt to read from a closed device'
                )

        # Read in_waiting
        try:
            return self.usb.in_waiting

        # Close device and propagate error
        except (serial.SerialException, OSError) as err:
            self.close()        

            raise RAVADisconnectedError(
                f'{self.name} bytes_waiting {self.name_conn} -> Device disconnected :-('
                ) from err


    def read(self, n_bytes, timeout = COMM_READ_TIMEOUT_S):
        """
        Returns bytes read from the RAVA device.

        May return fewer bytes than `n_bytes` requested if a timeout occurs, including b'' if no
        bytes are received before the timeout expires.
        """

        # Open?
        if not self.is_open():
            raise RAVAClosedError(
                f'{self.name} read {self.name_conn} -> Attempt to read from a closed device'
                )

        # Set timeout
        self.usb.timeout = timeout

        # Read
        try:
            # Returns b'' in case of timeout
            return self.usb.read(n_bytes)

        # Close device and propagate error
        except (serial.SerialException, OSError) as err:
            self.close()

            raise RAVADisconnectedError(
                f'{self.name} read {self.name_conn} -> Device disconnected :-('
                ) from err


    def write(self, comm_bytes):
        """
        Write bytes to the RAVA device.
        """

        # Open?
        if not self.is_open():
            raise RAVAClosedError(
                f'{self.name} write {self.name_conn} -> Attempt to write to a closed device'
                )

        # Write
        try:
            n_written = self.usb.write(comm_bytes)

        # Close device and propagate error
        except (serial.SerialException, OSError) as err:
            self.close()

            raise RAVADisconnectedError(
                f'{self.name} write {self.name_conn} -> Device disconnected :-('
                ) from err

        # Check if all bytes were written
        if n_written != len(comm_bytes):

            raise RAVAWriteError(
                f'{self.name} write {self.name_conn} -> Failed to write all bytes'
                )