"""
<<<<<<< HEAD
Copyright (c) 2023 Gabriel Guerrer
=======
Copyright (c) 2026 Gabriel Guerrer
>>>>>>> 4fcf521 (Update v3.0.0)

Distributed under the MIT license - See LICENSE for details
"""

"""
<<<<<<< HEAD
The RAVA driver implements the code for communicating with an RAVA device
running the RAVA firmware. The computer running the driver assumes the leader's
role, sending command requests and reading the data replies.

The RAVA_RNG class enables the request of pulse counts, random bits, random
bytes, and random numbers (integers and floats). Additionally, it establishes
the circuit's basic functionality encompassing key modules such as EEPROM, PWM,
heath tests, peripherals, and interfaces.

The functions that provide access to RAVA's functionality are prefixed with
"snd" and "get". "Snd" commands are unidirectional and do not expect a device's
response. Conversely, "get" commands are bidirectional, where the driver
immediately attempts to retrieve the expected information after signaling the
RAVA device.

The communication exchanges start with an 8-byte message. The first byte holds
the character '$' (00100100), signifying the message start. The second byte
encodes the command's identification code, while the subsequent bytes house the
command's specific data. The commands are sent to the RAVA device using the
snd_rava_msg() function, which generates the 8-byte information with the
pack_rava_msg() function.

The driver operates with a parallel thread running the loop_serial_listen()
function to continuously monitor RAVA responses. When a new message is detected,
it undergoes further processing within the process_serial_comm() function. This
function stores the command's variables in a queue object associated with the
respective command ID. To achieve this, the 6-byte data is transformed into the
command's specific variables using the unpack_rava_msgdata() function. These
variables are then available for retrieval by employing the get_queue_data()
function.

The queue-based design not only mitigates read-ordering conflicts but also
serves as the foundation for the asynchronous driver version, which uses asyncio
queues and implements get_queue_data() as an async function. This capability is
realized in the RAVA_RNG_AIO class.

The cable disconnection of an operational device is detected by the serial
functions. In response, the close() method is invoked. This method halts the
serial listen loop, closes the serial connection, and triggers the registered
device_close callback function.
"""

import logging
import struct
import time
import threading
import queue
import weakref

import serial
from serial.tools.list_ports import comports
import numpy as np

from rng_rava import __version__ as rng_rava_version
from rng_rava.rava_defs import *


### FUNCTIONS

def find_rava_sns(usb_vid=RAVA_USB_VID, usb_pid=RAVA_USB_PID):
    sns = [port_info.serial_number for port_info in comports()
            if (port_info.vid == usb_vid and port_info.pid == usb_pid)]
    sns.sort()
    return sns


def find_rava_port(serial_number):
    if isinstance(serial_number, bytes):
        serial_number = serial_number.decode()
    ports = [port_info.device for port_info in comports()
             if port_info.serial_number == serial_number]
    return ports[0] if len(ports) else None


def find_usb_info(port):
    return [(port_info.product, port_info.serial_number, port_info.vid, port_info.pid) for port_info in comports()
            if (port_info.device == port)][0]


def version_a_greater_b(v_a, v_b):
    v_ints_a = [int(i) for i in v_a.split('.')]
    v_ints_b = [int(i) for i in v_b.split('.')]

    # v_a > v_b?
    for i in range(len(v_ints_a)):
        if v_ints_a[i] > v_ints_b[i]:
            return True

    return False


def bytes_to_list(bytes_data, num_type='B'):
    int_size = len(bytes_data)
    if num_type.lower() == 'h':
        int_size = int_size // 2
    elif num_type.lower() in ['i', 'l', 'f']:
        int_size = int_size // 4
    elif num_type.lower() in ['q', 'd']:
        int_size = int_size // 8

    unpack_str = '<{}{}'.format(int_size, num_type)
    return list(struct.unpack(unpack_str, bytes_data))


def bytes_to_array(bytes_data, array_dtype=np.uint8):
    # Force little-endian
    array_dtype = np.dtype(array_dtype).newbyteorder('<')

    return np.frombuffer(bytes_data, dtype=array_dtype)


def print_health_startup_results(test_success, test_vars_dict):
    success_str = 'Success' if test_success else 'Failed'

    pc_result, pc_a, pc_b, pc_min = test_vars_dict['pulse_count']
    pc_diff_result, pc_diff_a, pc_diff_b, pc_diff_min = test_vars_dict['pulse_count_diff']
    bias_result, bias_a, bias_b, bias_abs_treshold = test_vars_dict['bit_bias']
    chisq_result, chisq_a, chisq_b, chisq_max_treshold = test_vars_dict['byte_bias']

    lg = logging.getLogger('rava')
    lg.info('Startup Health Tests: {}'.format(success_str) + \
            '\n{}Pulse Count: {}'.format(LOG_FILL, bool(pc_result)) + \
            '\n{}  pc_a={:.2f}, pc_b={:.2f}, pc_tresh={:.2f}'\
                .format(LOG_FILL, pc_a, pc_b, pc_min) + \
            '\n{}Pulse Count Difference: {}'.format(LOG_FILL, bool(pc_diff_result)) + \
            '\n{}  pc_diff_a={:.2f}, pc_diff_b={:.2f}, pc_diff_tresh={:.2f}'\
                .format(LOG_FILL, pc_diff_a, pc_diff_b, pc_diff_min) + \
            '\n{}Bit bias: {}'.format(LOG_FILL, bool(bias_result)) + \
            '\n{}  bias_a={:.4f}, bias_b={:.4f}, bias_tresh={:.2f}'\
                .format(LOG_FILL, bias_a, bias_b, bias_abs_treshold) + \
            '\n{}Byte bias: {}'.format(LOG_FILL, bool(chisq_result)) + \
            '\n{}  chisq_a={:.4f}, chisq_b={:.4f}, chisq_tresh={:.2f}'
                .format(LOG_FILL, chisq_a, chisq_b, chisq_max_treshold))


### RAVA_RNG

class RAVA_RNG:

    rava_instances = weakref.WeakSet()

    def __init__(self, dev_name='RAVA_RNG'):
        self.dev_name = dev_name
        self.queue_type = queue.Queue

        # Logging
        self.log_setup()

        # Debug
        self.lg.debug('> {} INIT'.format(self.dev_name))

        # Variables defined upon connection
        self.dev_serial_number = ''
        self.firmware_dict = None
        self.dev_usb_port = ''
        self.dev_usb_name = ''
        self.dev_usb_vid = None
        self.dev_usb_pid = None

        self.health_startup_enabled = None
        self.health_startup_success = None
        self.health_continuous_enabled = None
        self.led_enabled = None
        self.lamp_enabled = None
        self.peripherals_enabled = None

        # Serial variables
        self.serial = serial.Serial()
        self.serial_connected = threading.Event() # Used by loop_serial_listen()
        self.serial_read_lock = threading.Lock()
        self.serial_write_lock = threading.Lock()
        self.serial_data = {}
        self.serial_listen_thread = None

        # Byte streaming variables
        self.rng_streaming = False

        # Callback functions
        self.cbkfcn_device_close = lambda: None
        self.cbkfcn_rng_stream_data_available = lambda: None
        self.cbkfcn_d2_input_capture_available = lambda: None

        # Finalize any previous RAVA instance
        for rava in self.rava_instances.copy():
            rava.close()
            self.rava_instances.remove(rava)

        # Add new instance to weakref list
        self.rava_instances.add(self)


    def __del__(self):
        # Debug
        self.lg.debug('> {} DEL'.format(self.dev_name))


    def connect(self, serial_number):
        # Debug
        self.lg.debug('> {} CONNECT'.format(self.dev_name))

        # Find serial port
        port = find_rava_port(serial_number)
        if port is None:
            self.lg.error('{} Connect: No device found with SN {}'.format(self.dev_name, serial_number))
            return False

        # Open serial connection
        if not self.open_serial(port):
            return False

        # Reset serial data queues
        self.init_queue_data()

        # Start listening for serial commands
        self.serial_listen_thread = threading.Thread(target=self.loop_serial_listen)
        self.serial_listen_thread.start()

        # Stop any active RNG byte stream
        self.snd_rng_byte_stream_stop()

        # Request firmware info
        self.firmware_dict = self.get_eeprom_firmware()
        self.firmware_version =  self.firmware_dict['version']
        self.health_startup_enabled = self.firmware_dict['health_startup_enabled']
        self.health_continuous_enabled = self.firmware_dict['health_continuous_enabled']
        self.led_enabled = self.firmware_dict['led_enabled']
        self.lamp_enabled = self.firmware_dict['lamp_enabled']
        self.peripherals_enabled = self.firmware_dict['peripherals_enabled']

        # Check Firmware version
        if version_a_greater_b(FIRMWARE_MIN_VERSION, self.firmware_version):
            self.lg.error('{} Connect: Firmware version v{} is incompatible with driver v{}'.format(self.dev_name, self.firmware_version, rng_rava_version))
            self.close()
            return False

        # Print connection info
        self.lg.info('{} Connect: Success'
                '\n{}  SN={} at {}'
                '\n{}  Firmware v{},  Driver v{}'
                .format(self.dev_name,
                        LOG_FILL, self.dev_serial_number, self.serial.port,
                        LOG_FILL, self.firmware_version, rng_rava_version))

        # Request Health startup info
        if self.health_startup_enabled:
            self.health_startup_success, test_vars = self.get_health_startup_results()

            # Print test info
            print_health_startup_results(self.health_startup_success, test_vars)

            # Error? Users have then a limited command variety (see Firmware code)
            if not self.health_startup_success:
                self.lg.error('{} Connect: Startup tests failed'.format(self.dev_name))
                return False

        # Reset Health continuous erros
        self.get_health_continuous_errors()
=======
Randomness generation functionality.

The recommended configuration parameters for the RAVA RNG are as follows:
- PWM boost frequency: 50 kHz
- PWM boost duty-cycle setting: 20

These PWM boost parameters were determined experimentally by maximizing the avalanche pulse count 
while minimizing current consumption.

The recommended sampling interval is 10 µs. Values between 5 µs and 10 µs can increase the random 
number generation throughput at the cost of increased output bias. Sampling intervals below 5 µs 
may compromise the entropy of the generated data and are therefore not recommended.

Reference
Guerrer, G. (2023). Rava: An open hardware true random number generator based on avalanche noise. 
IEEE Access, 11, 119568-119583.
"""

from array import array
import enum
import queue
import struct

from .rava_comm import R_MessageComm, R_MessageError, QUEUE_READ_TIMEOUT_S
from .rava_errors import RAVAParameterError, RAVAFirmwareModuleError, \
    RAVAQueueTimeoutError, RAVAMissingQueueError, RAVAByteStreamingError
from .rava_pwm_boost import R_PwmBoostFreq, DEFAULT_PWM_BOOST_FREQ, DEFAULT_PWM_BOOST_DUTY

############################
# RAVA RNG
############################


DEFAULT_RNG_SAMPLING_INTERVAL_US = 10


class R_RngCores(enum.IntEnum):
    """
    RNG output modes based on the entropy cores A and B.

    AB_DUAL : Returns two separate output streams for cores A and B
    AB_ALT  : Returns a single stream with alternating bytes from A and B
    AB_XOR  : Returns a single stream formed by XORing corresponding bytes from A and B
    A       : Returns a single stream generated by core A
    B       : Returns a single stream generated by core A
    """

    AB_DUAL       = 0
    AB_ALT        = 1
    AB_XOR        = 2
    A             = 3
    B             = 4


DEFAULT_RNG_CORES = R_RngCores.AB_DUAL


class R_RngPP(enum.IntEnum):
    """
    Available byte post-processing modes.

    NONE       : No post-processing. Raw RNG bytes are returned unchanged
    XOR        : Generates two consecutive bytes and returns their bitwise XOR
    XOR DICHTL : Generates two consecutive bytes and combines them using the Dichtl method

    The XOR-based modes are provided for completeness and compatibility with traditional RNG
    post-processing approaches. They are not required for normal operation, as the RAVA
    architecture produces unbiased output bytes even when no post-processing is applied.

    Reference:
    M. Dichtl, "Bad and Good Ways of Post-processing Biased Physical Random Numbers",
    Fast Software Encryption (FSE 2007), Springer, 2007.
    """

    NONE          = 0
    XOR           = 1
    XOR_DICHTL    = 2


DEFAULT_RNG_POST_PROCESSING = R_RngPP.NONE


class RAVARngBytesStream:
    """
    Runtime state for fixed-interval random-byte streaming.
    """

    def __init__(self):
        self.streaming = False
        self.request_id = 0


class RAVARng():
    """
    Randomness generation commands.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVARng'

        self.rng_bytes_stream_cfg = RAVARngBytesStream()


    def get_config(self):
        """
        Retrieve the current RNG configuration.
        """
        command_id = R_MessageComm.RNG_GET_CONFIG

        # IO Structure
        data_out_format = ''
        data_in_format = '<BBB'    # pwm_boost_freq_id, pwm_boost_duty, rng_sampling_interval

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        pwm_boost_freq_id, pwm_boost_duty, rng_sampling_interval = \
            struct.unpack(data_in_format, rmsg.data)

        # Process Input
        pwm_boost_freq = R_PwmBoostFreq(pwm_boost_freq_id)

        # Return Data
        return pwm_boost_freq, pwm_boost_duty, rng_sampling_interval


    def set_config(self, pwm_boost_freq = DEFAULT_PWM_BOOST_FREQ,
                         pwm_boost_duty = DEFAULT_PWM_BOOST_DUTY,
                         rng_sampling_interval = DEFAULT_RNG_SAMPLING_INTERVAL_US):
        """
        Update the RNG configuration using the provided parameters.        
        """
        command_id = R_MessageComm.RNG_SET_CONFIG

        # IO Structure
        data_out_format = '<BBB'
        data_in_format = ''

        # Validate Output
        if not(
            pwm_boost_freq < len(R_PwmBoostFreq) and
            pwm_boost_duty > 0 and
            rng_sampling_interval > 0
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(
            data_out_format, pwm_boost_freq, pwm_boost_duty, rng_sampling_interval)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Return Data
        return True


    def set_timing_debug(self, on):
        """
        Enable/disable byte-generation timing debugging, exposed as a digital signal on a
        designated device output pin.

        This functionality needs to be enabled in the device firmware.
        """
        command_id = R_MessageComm.RNG_SET_TIMING_DEBUG

        # Enabled?
        if not self.firmw_modules.rng_timing_debug_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> RNG timing debug is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<B'
        data_in_format = ''

        # Validate Output
        # Serialize Output
        data_out = struct.pack(data_out_format, on)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)
>>>>>>> 4fcf521 (Update v3.0.0)

        return True


<<<<<<< HEAD
    def connected(self):
        return self.serial.is_open


    def close(self):
        # Debug
        self.lg.debug('> {} CLOSE'.format(self.dev_name))

        # Stop loop_serial_listen
        self.serial_connected.clear()

        # Close serial connection
        self.serial.close()

        # Callback
        try:
            self.cbkfcn_device_close()
        except:
            pass


    ## LOGGING

    def log_setup(self):
        self.lg = logging.getLogger('rava')

        # RAVA Logger 1st call
        if not self.lg.hasHandlers():

            # Create handler
            lg_fmt = logging.Formatter(fmt='%(asctime)s %(levelname)-7s %(message)s', datefmt='%H:%M:%S')
            lg_sh = logging.StreamHandler()
            lg_sh.setFormatter(lg_fmt)
            self.lg.addHandler(lg_sh)

            # Set defaulf level to INFO
            self.log_level('INFO')


    def log_level(self, level_str, level_id=None):
        if level_id:
            level = level_id
        else:
            try:
                level = logging.getLevelNamesMapping()[level_str]
            except:
                level = logging.INFO

        self.lg.setLevel(level)


    ## QUEUE

    def init_queue_data(self):
        # Create one queue for each command
        self.serial_data = {}
        for comm in D_DEV_COMM.keys():
            self.serial_data[comm] = self.queue_type()


    def put_queue_data(self, comm, value, comm_ext_id=0):
        # Check key
        if comm not in self.serial_data:
            self.lg.error('{} Data: Unknown comm {}'.format(self.dev_name, comm))
            return False

        # Extended key
        if comm_ext_id:
            comm_ext = '{}_{}'.format(comm, comm_ext_id)

            # Queue exists?
            if comm_ext not in self.serial_data:
                self.serial_data[comm_ext] = self.queue_type()
        else:
            comm_ext = comm

        # Try writing to queue
        try:
            self.serial_data[comm_ext].put(value)
            return True

        except queue.Full:
            self.lg.error('{} Data: {} Queue full'.format(self.dev_name, comm_ext))
            return False


    def get_queue_data(self, comm, comm_ext_id=0, timeout=GET_TIMEOUT_S):
        # Check key
        if comm not in self.serial_data:
            self.lg.error('{} Data: Unknown comm {}'.format(self.dev_name, comm))
            return None

        # Extended key
        if comm_ext_id:
            comm_ext = '{}_{}'.format(comm, comm_ext_id)

            # Queue exists?
            if comm_ext not in self.serial_data:
                self.serial_data[comm_ext] = self.queue_type()
        else:
            comm_ext = comm

        # Try reading from queue
        try:
            return self.serial_data[comm_ext].get(timeout=timeout)

        except queue.Empty:
            self.lg.error('{} Data: Timeout retrieving {}'.format(self.dev_name, comm_ext))
            return None


    ## SERIAL

    def open_serial(self, port):
        # Set serial port
        self.serial.port = port

        # Open serial connection
        try:
            self.serial.open()
            self.serial_connected.set()

            # Get USB parameters
            self.dev_usb_port = port
            self.dev_usb_name, self.dev_serial_number, self.dev_usb_vid, self.dev_usb_pid = find_usb_info(port)
            return True

        except Exception as err:
            self.lg.error('{} Serial: Failed opening {}'
                     '\n{}  {} - {}'
                     .format(self.dev_name, port, LOG_FILL, type(err).__name__, err))
            return False


    def inwaiting_serial(self):
        # Read in_waiting
        try:
            return self.serial.in_waiting

        except Exception as err:
            self.lg.error('{} Serial: Failed reading in_waiting'
                     '\n{}  {} - {}'
                     .format(self.dev_name, LOG_FILL, type(err).__name__, err))

            # Close device
            self.close()
            return None


    def read_serial(self, n_bytes):
        # Read serial
        try:
            with self.serial_read_lock:
                data = self.serial.read(n_bytes)
            return data

        except Exception as err:
            self.lg.error('{} Serial: Failed reading'
                     '\n{}  {} - {}'
                     .format(self.dev_name, LOG_FILL, type(err).__name__, err))

            # Close device
            self.close()
            return None


    def write_serial(self, comm_bytes):
        # Write serial
        try:
            with self.serial_write_lock:
                self.serial.write(comm_bytes)
            return True

        except Exception as err:
            self.lg.error('{} Serial: Failed writing'
                    '\n{}  {} - {}'
                    .format(self.dev_name, LOG_FILL, type(err).__name__, err))

            # Close device
            self.close()
            return False


    def loop_serial_listen(self):
        # Debug
        self.lg.debug('> {} LOOP SERIAL LISTEN'.format(self.dev_name))

        # Loop while connected
        while self.serial_connected.is_set():

            # Command available?
            comm_inwaiting = self.inwaiting_serial()
            if comm_inwaiting is None:
                continue # Disconnected

            if comm_inwaiting > 0:

                # Read command starting char
                comm_start = self.read_serial(1)
                if comm_start is None:
                    continue # Disconnected

                # Starts with $?
                if comm_start == COMM_MSG_START:

                    # Read remaining command bytes
                    comm_msg = self.read_serial(COMM_MSG_LEN-1)
                    if comm_msg is None:
                        continue # Disconnected

                    comm_id = comm_msg[0]
                    comm_data = comm_msg[1:]

                    # Known command id?
                    if comm_id in D_DEV_COMM_INV:

                        # Debug
                        self.lg.debug('> COMM RCV {}'.format([D_DEV_COMM_INV[comm_id], *[c for c in comm_data]]))

                        # Process Command
                        try:
                            self.process_serial_comm(comm_id, comm_data)

                        except Exception as err:
                            self.lg.error('{} Serial Listen Loop: Error processing command_id {}'
                                        '\n{}  {} - {}'
                                        .format(self.dev_name, comm_id, LOG_FILL, type(err).__name__, err))

                            # Close device
                            self.close()

                    else:
                        self.lg.warning('{} Serial Listen Loop: Unknown command_id {}'.format(self.dev_name, comm_id))

                else:
                    self.lg.warning('{} Serial Listen Loop: Commands must start with {}'.format(self.dev_name, COMM_MSG_START))

            # The non-blocking method is prefered for finishing the thread
            # when closing the device
            else:
                time.sleep(SERIAL_LISTEN_LOOP_INTERVAL_S)


    def process_serial_comm(self, comm_id, comm_data):
        # DEVICE_SERIAL_NUMBER
        if comm_id == D_DEV_COMM['DEVICE_SERIAL_NUMBER']:
            sn_n_bytes = self.unpack_rava_msgdata(comm_data, 'B')
            sn = self.read_serial(sn_n_bytes).decode()
            self.put_queue_data('DEVICE_SERIAL_NUMBER', sn)

        # DEVICE_FREE_RAM
        elif comm_id == D_DEV_COMM['DEVICE_FREE_RAM']:
            # free_ram
            self.put_queue_data('DEVICE_FREE_RAM', self.unpack_rava_msgdata(comm_data, 'H'))

        # DEVICE_DEBUG
        elif comm_id == D_DEV_COMM['DEVICE_DEBUG']:
            debug_bytes = self.unpack_rava_msgdata(comm_data, 'BBBBBB')
            debug_ints = [x for x in debug_bytes]
            self.lg.debug('> RAVA DEBUG MSG {} {} {} {} {} {}'.format(*debug_ints))


        # EEPROM_FIRMWARE
        elif comm_id == D_DEV_COMM['EEPROM_FIRMWARE']:
            # version_major, version_minor, version_patch, modules
            self.put_queue_data('EEPROM_FIRMWARE', self.unpack_rava_msgdata(comm_data, 'BBBB'))

        # EEPROM_PWM_BOOST
        elif comm_id == D_DEV_COMM['EEPROM_PWM_BOOST']:
            # freq_id, duty
            self.put_queue_data('EEPROM_PWM_BOOST', self.unpack_rava_msgdata(comm_data, 'BB'))

        # EEPROM_RNG
        elif comm_id == D_DEV_COMM['EEPROM_RNG']:
            # sampling_interval_us
            self.put_queue_data('EEPROM_RNG', self.unpack_rava_msgdata(comm_data, 'B'))

        # EEPROM_LED
        elif comm_id == D_DEV_COMM['EEPROM_LED']:
            # led_n
            self.put_queue_data('EEPROM_LED', self.unpack_rava_msgdata(comm_data, 'B'))

        # EEPROM_LAMP
        elif comm_id == D_DEV_COMM['EEPROM_LAMP']:
            exp_mag_smooth_n_trials, exp_mag_colorchg_thld, sound_volume, extra_n_bytes = self.unpack_rava_msgdata(comm_data, 'BBBB')
            extra_bytes = self.read_serial(extra_n_bytes)
            if extra_bytes is None:
                exp_movwin_n_trials, exp_deltahits_sigevt, exp_dur_max_s = None, None, None
            else:
                exp_movwin_n_trials, exp_deltahits_sigevt, exp_dur_max_s = struct.unpack('<HHH', extra_bytes)
            self.put_queue_data('EEPROM_LAMP', (exp_movwin_n_trials, exp_deltahits_sigevt, exp_dur_max_s, exp_mag_smooth_n_trials, exp_mag_colorchg_thld, sound_volume))

        # PWM_BOOST_SETUP
        elif comm_id == D_DEV_COMM['PWM_BOOST_SETUP']:
            # freq_id, duty
            self.put_queue_data('PWM_BOOST_SETUP', self.unpack_rava_msgdata(comm_data, 'BB'))

        # RNG_SETUP
        elif comm_id == D_DEV_COMM['RNG_SETUP']:
            # sampling_interval_us
            self.put_queue_data('RNG_SETUP', self.unpack_rava_msgdata(comm_data, 'B'))

        # RNG_PULSE_COUNTS
        elif comm_id == D_DEV_COMM['RNG_PULSE_COUNTS']:
            n_counts = self.unpack_rava_msgdata(comm_data, 'H')
            counts_bytes = self.read_serial(2 * n_counts)
            if counts_bytes is None:
                counts_bytes_a = None
                counts_bytes_b = None
            else:
                counts_bytes_a = counts_bytes[::2]
                counts_bytes_b = counts_bytes[1::2]
            self.put_queue_data('RNG_PULSE_COUNTS', (counts_bytes_a, counts_bytes_b))

        # RNG_BITS
        elif comm_id == D_DEV_COMM['RNG_BITS']:
            bit_type, bit_a, bit_b = self.unpack_rava_msgdata(comm_data, 'BBB')
            if bit_type == D_RNG_BIT_SRC['AB']:
                self.put_queue_data('RNG_BITS', (bit_type, bit_a, bit_b))
            else:
                self.put_queue_data('RNG_BITS', (bit_type, bit_a))

        # RNG_BYTES
        elif comm_id == D_DEV_COMM['RNG_BYTES']:
            n_bytes, request_id = self.unpack_rava_msgdata(comm_data, 'HB')
            rng_bytes = self.read_serial(n_bytes * 2)
            if rng_bytes is None:
                rng_bytes_a = None
                rng_bytes_b = None
            else:
                rng_bytes_a = rng_bytes[::2]
                rng_bytes_b = rng_bytes[1::2]
            self.put_queue_data('RNG_BYTES', (rng_bytes_a, rng_bytes_b), comm_ext_id=request_id)

        # RNG_STREAM_BYTES
        elif comm_id == D_DEV_COMM['RNG_STREAM_BYTES']:
            n_bytes = self.unpack_rava_msgdata(comm_data, 'H')
            rng_bytes = self.read_serial(n_bytes * 2)
            if self.rng_streaming:
                if rng_bytes is None:
                    rng_bytes_a = None
                    rng_bytes_b = None
                else:
                    rng_bytes_a = rng_bytes[::2]
                    rng_bytes_b = rng_bytes[1::2]
                self.put_queue_data('RNG_STREAM_BYTES', (rng_bytes_a, rng_bytes_b))
                # Callback
                try:
                    self.cbkfcn_rng_stream_data_available()
                except:
                    pass

        # RNG_STREAM_STATUS
        elif comm_id == D_DEV_COMM['RNG_STREAM_STATUS']:
            # stream_status
            self.put_queue_data('RNG_STREAM_STATUS', self.unpack_rava_msgdata(comm_data, '?'))

        # RNG_INT8S
        elif comm_id == D_DEV_COMM['RNG_INT8S']:
            n_ints = self.unpack_rava_msgdata(comm_data, 'H')
            # ints_bytes
            self.put_queue_data('RNG_INT8S', self.read_serial(n_ints))

        # RNG_INT16S
        elif comm_id == D_DEV_COMM['RNG_INT16S']:
            n_ints = self.unpack_rava_msgdata(comm_data, 'H')
            # ints_bytes
            self.put_queue_data('RNG_INT16S', self.read_serial(n_ints * 2))

        # RNG_FLOATS
        elif comm_id == D_DEV_COMM['RNG_FLOATS']:
            n_floats = self.unpack_rava_msgdata(comm_data, 'H')
            # ints_bytes
            self.put_queue_data('RNG_FLOATS', self.read_serial(n_floats * 4))

        # HEALTH_STARTUP_RESULTS
        elif comm_id == D_DEV_COMM['HEALTH_STARTUP_RESULTS']:
            success, pc_n_bytes, pc_diff_n_bytes, bias_bit_n_bytes, bias_byte_n_bytes = self.unpack_rava_msgdata(comm_data, '?BBBB')

            # pc_result, pc_a, pc_b, pc_min
            pc_bytes = self.read_serial(pc_n_bytes)
            if pc_bytes is None:
                pc_vars = None
            else:
                pc_vars = struct.unpack('<?fff', pc_bytes)

            # pc_diff_result, pc_diff_a, pc_diff_b, pc_avg_diff_min
            pc_diff_bytes = self.read_serial(pc_diff_n_bytes)
            if pc_diff_bytes is None:
                pc_diff_vars = None
            else:
                pc_diff_vars = struct.unpack('<?fff', pc_diff_bytes)

            # bias_result, bias_a, bias_b, bias_abs_treshold
            bias_bit_bytes = self.read_serial(bias_bit_n_bytes)
            if bias_bit_bytes is None:
                bias_bit_vars = None
            else:
                bias_bit_vars = struct.unpack('<?fff', bias_bit_bytes)

            # chisq_result, chisq_a, chisq_b, chisq_max_treshold
            bias_byte_bytes = self.read_serial(bias_byte_n_bytes)
            if bias_byte_bytes is None:
                bias_byte_vars = None
            else:
                bias_byte_vars = struct.unpack('<?fff', bias_byte_bytes)

            self.put_queue_data('HEALTH_STARTUP_RESULTS', (success, pc_vars, pc_diff_vars, bias_bit_vars, bias_byte_vars))

        # HEALTH_CONTINUOUS_ERRORS
        elif comm_id == D_DEV_COMM['HEALTH_CONTINUOUS_ERRORS']:
            n_extra_bytes = self.unpack_rava_msgdata(comm_data, 'B')
            # repetitive_count_a, repetitive_count_b, adaptative_proportion_a, adaptative_proportion_b
            health_extra_bytes = self.read_serial(n_extra_bytes)
            if health_extra_bytes is None:
                health_extra_vars = None
            else:
                health_extra_vars = struct.unpack('<HHHH', health_extra_bytes)

            self.put_queue_data('HEALTH_CONTINUOUS_ERRORS', health_extra_vars)

        # PERIPH_READ
        elif comm_id == D_DEV_COMM['PERIPH_READ']:
            # digi_state, digi_mode
            self.put_queue_data('PERIPH_READ', self.unpack_rava_msgdata(comm_data, 'BB'))

        # PERIPH_D2_TIMER3_INPUT_CAPTURE
        elif comm_id == D_DEV_COMM['PERIPH_D2_TIMER3_INPUT_CAPTURE']:
            # input_capture_interval_s
            self.put_queue_data('PERIPH_D2_TIMER3_INPUT_CAPTURE', self.unpack_rava_msgdata(comm_data, 'f'))
            # Callback
            try:
                self.cbkfcn_d2_input_capture_available()
            except:
                pass

        # PERIPH_D5_ADC
        elif comm_id == D_DEV_COMM['PERIPH_D5_ADC']:
            # adc_read_mv
            self.put_queue_data('PERIPH_D5_ADC', self.unpack_rava_msgdata(comm_data, 'f'))

        # INTERFACE_DS18B20
        elif comm_id == D_DEV_COMM['INTERFACE_DS18B20']:
            # temperature
            self.put_queue_data('INTERFACE_DS18B20', self.unpack_rava_msgdata(comm_data, 'f'))


    ## RAVA COMM

    def pack_rava_msg(self, comm_str, data_user=[], data_user_fmt=''):
        # Transform comm and variables into a 8-byte RAVA message

        # Get comm id
        if comm_str not in D_DEV_COMM:
            self.lg.error('{} MSG Pack: Unknown command {}'.format(self.dev_name, comm_str))
            return None
        comm_id = D_DEV_COMM[comm_str]

        # Check if data and data_fmt have the same size
        if len(data_user) != len(data_user_fmt):
            self.lg.error('{} MSG Pack: Data and data_fmt must have the same size'.format(self.dev_name))
            return None

        # Msg data contains (COMM_MSG_LEN - 2) bytes
        # (as the first 2 are always $ and the command id)
        data_usr_n_bytes = struct.calcsize('<' + data_user_fmt)
        data_n_bytes = COMM_MSG_LEN - 2
        if  data_usr_n_bytes > data_n_bytes:
            self.lg.error('{} MSG Pack: Data contains {} bytes - the maximum is {}'
                     .format(self.dev_name, data_usr_n_bytes, data_n_bytes))
            return None

        # Fill remaining data bytes with 0
        data_fmt = data_user_fmt + (data_n_bytes - data_usr_n_bytes) * 'B'
        data = data_user + (data_n_bytes - data_usr_n_bytes) * [0]

        # Pack rava msg
        return struct.pack('<cB' + data_fmt, COMM_MSG_START, comm_id, *data)


    def snd_rava_msg(self, comm_str, data_user=[], data_user_fmt=''):
        # Pack rava msg
        comm_bytes = self.pack_rava_msg(comm_str=comm_str, data_user=data_user, data_user_fmt=data_user_fmt)
        if comm_bytes is None:
            return False

        # Send command
        write_success = self.write_serial(comm_bytes)

        # Debug
        if write_success:
            comm_dbg = [c for c in comm_bytes][1:]
            comm_dbg[0] = D_DEV_COMM_INV[comm_dbg[0]]
            self.lg.debug('> COMM SND {}'.format(comm_dbg))

        return write_success


    def unpack_rava_msgdata(self, data, data_get_format):
        # Transform RAVA 6-byte message data into variables

        # Msg data contains (COMM_MSG_LEN - 2) bytes
        data_n_bytes = COMM_MSG_LEN - 2
        if  len(data) != data_n_bytes:
            self.lg.error('{} MSG Unpack: Data contains {} bytes - expected {}'
                     .format(self.dev_name, len(data), data_n_bytes))
            return None

        # Check data_get_fmt
        dataget_n_bytes = struct.calcsize('<' + data_get_format)
        if (dataget_n_bytes == 0) or (dataget_n_bytes > data_n_bytes):
            self.lg.error('{} MSG Unpack: Data format asks for {} bytes - expected 0 < size <= {}'
                     .format(self.dev_name, dataget_n_bytes, data_n_bytes))
            return None

        # Fill remaining data fmt bytes
        data_format = data_get_format + (data_n_bytes - dataget_n_bytes) * 'B'

        # Unpack and return data
        vars_n = len(data_get_format)
        vars = struct.unpack('<' + data_format, data)
        if vars_n == 1:
            return vars[:vars_n][0]
        else:
            return vars[:vars_n]


    ## CALLBACK REGISTER

    def cbkreg_device_close(self, fcn_device_close):
        if callable(fcn_device_close):
            self.cbkfcn_device_close = fcn_device_close
            self.lg.debug('{} Callback: Registering Device Close function to {}'
                    .format(self.dev_name, fcn_device_close.__name__))
        elif fcn_device_close is None:
            self.cbkfcn_device_close = lambda: None
            self.lg.debug('{} Callback: Unregistering Device Close function'.format(self.dev_name))
        else:
            self.lg.error('{} Callback: Provide fcn_device_close as a function or None'.format(self.dev_name))


    def cbkreg_stream_data_available(self, fcn_rng_stream_data_available):
        if callable(fcn_rng_stream_data_available):
            self.cbkfcn_rng_stream_data_available = fcn_rng_stream_data_available
            self.lg.debug('{} Callback: Registering Stream Data Available function to {}'
                    .format(self.dev_name, fcn_rng_stream_data_available.__name__))
        elif fcn_rng_stream_data_available is None:
            self.cbkfcn_rng_stream_data_available = lambda: None
            self.lg.debug('{} Callback: Unregistering Stream Data Available function'.format(self.dev_name))
        else:
            self.lg.error('{} Callback: Provide fcn_stream_data_available as a function or None'.format(self.dev_name))


    def cbkreg_d2_input_capture_available(self, fcn_d2_input_capture_available):
        if callable(fcn_d2_input_capture_available):
            self.cbkfcn_d2_input_capture_available = fcn_d2_input_capture_available
            self.lg.debug('{} Callback: Registering D2 Input Capture Available function to {}'
                    .format(self.dev_name, fcn_d2_input_capture_available.__name__))
        elif fcn_d2_input_capture_available is None:
            self.cbkfcn_d2_input_capture_available = lambda: None
            self.lg.debug('{} Callback: Unregistering D2 Input Capture Available function'.format(self.dev_name))
        else:
            self.lg.error('{} Callback: Provide fcn_input_capture_available as a function or None'.format(self.dev_name))


    ## DEVICE

    def get_device_serial_number(self, timeout=GET_TIMEOUT_S):
        comm = 'DEVICE_SERIAL_NUMBER'
        if self.snd_rava_msg(comm):
            return self.get_queue_data(comm, timeout=timeout)


    def get_device_free_ram(self, timeout=GET_TIMEOUT_S):
        comm = 'DEVICE_FREE_RAM'
        if self.snd_rava_msg(comm):
            return self.get_queue_data(comm, timeout=timeout)


    def snd_device_reboot(self):
        comm = 'DEVICE_REBOOT'
        return self.snd_rava_msg(comm)


    ## EEPROM

    def snd_eeprom_reset_to_default(self):
        comm = 'EEPROM_RESET_TO_DEFAULT'
        return self.snd_rava_msg(comm)


    def get_eeprom_firmware(self, timeout=GET_TIMEOUT_S):
        comm = 'EEPROM_FIRMWARE'
        if self.snd_rava_msg(comm):
            version_major, version_minor, version_patch, modules = self.get_queue_data(comm, timeout=timeout)

            version = '{}.{}.{}'.format(version_major, version_minor, version_patch)
            health_startup_enabled = modules & 1 << 0 != 0
            health_continuous_enabled = modules & 1 << 1 != 0
            led_enabled = modules & 1 << 2 != 0
            lamp_enabled = modules & 1 << 3 != 0
            peripherals_enabled = modules & 1 << 4 != 0
            serial1_enabled = modules & 1 << 5 != 0
            return {'version':version,
                    'health_startup_enabled':health_startup_enabled,
                    'health_continuous_enabled':health_continuous_enabled,
                    'led_enabled':led_enabled,
                    'lamp_enabled':lamp_enabled,
                    'peripherals_enabled':peripherals_enabled,
                    'serial1_enabled':serial1_enabled
                    }


    def snd_eeprom_pwm_boost(self, freq_id, duty):
        if freq_id not in D_PWM_BOOST_FREQ_INV:
            self.lg.error('{} EEPROM PWM: Unknown freq_id {}'.format(self.dev_name, freq_id))
            return False
        if duty == 0:
            self.lg.error('{} EEPROM PWM: Provide a duty > 0'.format(self.dev_name))
            return False

        comm = 'EEPROM_PWM_BOOST'
        rava_send = False
        return self.snd_rava_msg(comm, [rava_send, freq_id, duty], 'BBB')


    def get_eeprom_pwm_boost(self, timeout=GET_TIMEOUT_S):
        comm = 'EEPROM_PWM_BOOST'
        rava_send = True
        if self.snd_rava_msg(comm, [rava_send], 'B'):
            freq_id, duty = self.get_queue_data(comm, timeout=timeout)
            return {'freq_id':freq_id, 'freq_str':D_PWM_BOOST_FREQ_INV[freq_id], 'duty':duty}


    def snd_eeprom_rng(self, sampling_interval_us):
        if sampling_interval_us == 0:
            self.lg.error('{} EEPROM RNG: Provide a sampling_interval_us > 0'.format(self.dev_name))
            return False

        comm = 'EEPROM_RNG'
        rava_send = False
        return self.snd_rava_msg(comm, [rava_send, sampling_interval_us], 'BB')


    def get_eeprom_rng(self, timeout=GET_TIMEOUT_S):
        comm = 'EEPROM_RNG'
        rava_send = True
        if self.snd_rava_msg(comm, [rava_send], 'B'):
            sampling_interval_us = self.get_queue_data(comm, timeout=timeout)
            return {'sampling_interval_us':sampling_interval_us}


    def snd_eeprom_led(self, led_n):
        comm = 'EEPROM_LED'
        rava_send = False
        return self.snd_rava_msg(comm, [rava_send, led_n], 'BB')


    def get_eeprom_led(self, timeout=GET_TIMEOUT_S):
        comm = 'EEPROM_LED'
        rava_send = True
        if self.snd_rava_msg(comm, [rava_send], 'B'):
            led_n = self.get_queue_data(comm, timeout=timeout)
            return {'led_n':led_n}


    def snd_eeprom_lamp(self, exp_movwin_n_trials, exp_deltahits_sigevt, exp_dur_max_s, exp_mag_smooth_n_trials, exp_mag_colorchg_thld, sound_volume):
        if (exp_movwin_n_trials < 10) or (exp_movwin_n_trials > 1200):
            self.lg.error('{} EEPROM LAMP: Provide an 10 <= exp_movwin_n_trials <= 1200'.format(self.dev_name))
            return False
        if exp_deltahits_sigevt == 0:
            self.lg.error('{} EEPROM LAMP: Provide an exp_deltahits_sigevt > 0'.format(self.dev_name))
            return False
        if exp_dur_max_s < 10:
            self.lg.error('{} EEPROM LAMP: Provide an exp_dur_max_s > 10'.format(self.dev_name))
            return False
        if (exp_mag_smooth_n_trials == 0) or (exp_mag_smooth_n_trials > 255):
            self.lg.error('{} EEPROM LAMP: Provide an 0 < exp_mag_smooth_n_trials <= 255'.format(self.dev_name))
            return False
        if exp_mag_colorchg_thld > 255:
            self.lg.error('{} EEPROM LAMP: Provide an exp_mag_colorchg_thld <= 255'.format(self.dev_name))
            return False

        comm = 'EEPROM_LAMP'
        rava_send = False
        if self.snd_rava_msg(comm, [rava_send, exp_mag_smooth_n_trials, exp_mag_colorchg_thld, sound_volume, 6], 'BBBBB'):
            comm_extra = struct.pack('<HHH', exp_movwin_n_trials, exp_deltahits_sigevt, exp_dur_max_s)
            return self.write_serial(comm_extra)
        else:
            return False


    def get_eeprom_lamp(self, timeout=GET_TIMEOUT_S):
        comm = 'EEPROM_LAMP'
        rava_send = True
        if self.snd_rava_msg(comm, [rava_send], 'B'):
            data_vars = self.get_queue_data(comm, timeout=timeout)
            data_names = ['exp_movwin_n_trials', 'exp_deltahits_sigevt', 'exp_dur_max_s', 'exp_mag_smooth_n_trials', 'exp_mag_colorchg_thld', 'sound_volume']
            return dict(zip(data_names, data_vars))


    ## PWM

    def snd_pwm_boost_setup(self, freq_id, duty):
        if freq_id not in D_PWM_BOOST_FREQ_INV:
            self.lg.error('{} PWM: Unknown freq_id {}'.format(self.dev_name, freq_id))
            return False
        if duty == 0:
            self.lg.error('{} PWM: Provide a duty > 0'.format(self.dev_name))
            return False

        comm = 'PWM_BOOST_SETUP'
        rava_send = False
        return self.snd_rava_msg(comm, [rava_send, freq_id, duty], 'BBB')


    def get_pwm_boost_setup(self, timeout=GET_TIMEOUT_S):
        rava_send = True
        comm = 'PWM_BOOST_SETUP'
        if self.snd_rava_msg(comm, [rava_send], 'B'):
            freq_id, duty = self.get_queue_data(comm, timeout=timeout)
            return {'freq_id':freq_id, 'freq_str':D_PWM_BOOST_FREQ_INV[freq_id], 'duty':duty}


    ## RNG

    def snd_rng_setup(self, sampling_interval_us):
        if sampling_interval_us == 0:
            self.lg.error('{} RNG: Provide a sampling_interval_us > 0'.format(self.dev_name))
            return False

        comm = 'RNG_SETUP'
        rava_send = False
        return self.snd_rava_msg(comm, [rava_send, sampling_interval_us], 'BB')


    def get_rng_setup(self, timeout=GET_TIMEOUT_S):
        comm = 'RNG_SETUP'
        rava_send = True
        if self.snd_rava_msg(comm, [rava_send], 'B'):
            sampling_interval_us = self.get_queue_data(comm, timeout=timeout)
            return {'sampling_interval_us':sampling_interval_us}


    def snd_rng_timing_debug_d1(self, on=True):
        comm = 'RNG_TIMING_DEBUG_D1'
        return self.snd_rava_msg(comm, [on], 'B')


    def get_rng_pulse_counts(self, n_counts, output_type='array', timeout=GET_TIMEOUT_S):
        if n_counts == 0:
            self.lg.error('{} RNG PC: Provide n_counts > 0'.format(self.dev_name))
            return None, None
        if n_counts >= 2**16:
            self.lg.error('{} RNG PC: Provide n_counts as a 16-bit integer'.format(self.dev_name))
            return None, None

        comm = 'RNG_PULSE_COUNTS'
        if self.snd_rava_msg(comm, [n_counts], 'H'):
            counts_bytes_a, counts_bytes_b = self.get_queue_data(comm, timeout=timeout)

            if (counts_bytes_a is None) or (counts_bytes_a is None):
                return None, None

            else:
                if output_type == 'list':
                    counts_a = bytes_to_list(counts_bytes_a, 'B')
                    counts_b = bytes_to_list(counts_bytes_b, 'B')
                    return counts_a, counts_b

                elif output_type == 'array':
                    counts_a = bytes_to_array(counts_bytes_a, np.uint8)
                    counts_b = bytes_to_array(counts_bytes_b, np.uint8)
                    return counts_a, counts_b

                else:
                    return counts_bytes_a, counts_bytes_b


    def get_rng_bits(self, bit_source_id, timeout=GET_TIMEOUT_S):
        if bit_source_id not in D_RNG_BIT_SRC_INV:
            self.lg.error('{} RNG Bits: Unknown bit_source_id {}'.format(self.dev_name, bit_source_id))
            return None

        comm = 'RNG_BITS'
        if self.snd_rava_msg(comm, [bit_source_id], 'B'):
            bit_source_id_recv, *bits = self.get_queue_data(comm, timeout=timeout)

            if bit_source_id == D_RNG_BIT_SRC['AB_RND']:
                bit_type_str = D_RNG_BIT_SRC_INV[bit_source_id_recv]
                return [bit_type_str, bits[0]]
            elif bit_source_id == D_RNG_BIT_SRC['AB']:
                return list(bits)
            else:
                return bits[0]


    def get_rng_bytes(self, n_bytes, postproc_id=D_RNG_POSTPROC['NONE'], request_id=0, output_type='array',
                      timeout=GET_TIMEOUT_S):
        if n_bytes == 0:
            self.lg.error('{} RNG Bytes: Provide n_bytes > 0'.format(self.dev_name))
            return None, None
        if n_bytes >= 2**16:
            self.lg.error('{} RNG Bytes: Provide n_bytes as a 16-bit integer'.format(self.dev_name))
            return None, None
        if postproc_id not in D_RNG_POSTPROC_INV:
            self.lg.error('{} RNG Bytes: Unknown postproc_id {}'.format(self.dev_name, postproc_id))
            return None, None

        comm = 'RNG_BYTES'
        if self.snd_rava_msg(comm, [n_bytes, postproc_id, request_id], 'HBB'):
            rng_bytes_a, rng_bytes_b = self.get_queue_data(comm, comm_ext_id=request_id, timeout=timeout)

            if (rng_bytes_a is None) or (rng_bytes_b is None):
                return None, None

            else:
                if output_type == 'list':
                    rng_a = bytes_to_list(rng_bytes_a, 'B')
                    rng_b = bytes_to_list(rng_bytes_b, 'B')
                    return rng_a, rng_b

                elif output_type == 'array':
                    rng_a = bytes_to_array(rng_bytes_a, np.uint8)
                    rng_b = bytes_to_array(rng_bytes_b, np.uint8)
                    return rng_a, rng_b

                else:
                    return rng_bytes_a, rng_bytes_b


    def get_rng_int8s(self, n_ints, int_delta, output_type='array', timeout=GET_TIMEOUT_S):
        # int_delta = int_max - int_min
        if n_ints == 0:
            self.lg.error('{} RNG Ints: Provide n_ints > 0'.format(self.dev_name))
            return None
        if n_ints >= 2**16:
            self.lg.error('{} RNG Ints: Provide n_ints as a 16-bit integer'.format(self.dev_name))
            return None
        if int_delta >= 2**8:
            self.lg.error('{} RNG Ints: Provide int_delta as a 8-bit integer'.format(self.dev_name))
            return None
        if int_delta == 0:
            self.lg.error('{} RNG Ints: Provide int_delta > 0'.format(self.dev_name))
            return None

        comm = 'RNG_INT8S'
        if self.snd_rava_msg(comm, [n_ints, int_delta], 'HB'):
            ints_bytes = self.get_queue_data(comm, timeout=timeout)
            if ints_bytes is None:
                return None
            else:
                if output_type == 'list':
                    return bytes_to_list(ints_bytes, 'B')
                else:
                    return bytes_to_array(ints_bytes, np.uint8)


    def get_rng_int16s(self, n_ints, int_delta, output_type='array', timeout=GET_TIMEOUT_S):
        # int_delta = int_max - int_min
        if n_ints == 0:
            self.lg.error('{} RNG Ints: Provide n_ints > 0'.format(self.dev_name))
            return None
        if n_ints >= 2**16:
            self.lg.error('{} RNG Ints: Provide n_ints as a 16-bit integer'.format(self.dev_name))
            return None
        if int_delta >= 2**16:
            self.lg.error('{} RNG Ints: Provide int_delta as a 16-bit integer'.format(self.dev_name))
            return None
        if int_delta == 0:
            self.lg.error('{} RNG Ints: Provide int_delta > 0'.format(self.dev_name))
            return None

        comm = 'RNG_INT16S'
        if self.snd_rava_msg(comm, [n_ints, int_delta], 'HH'):
            ints_bytes = self.get_queue_data(comm, timeout=timeout)
            if ints_bytes is None:
                return None
            else:
                if output_type == 'list':
                    return bytes_to_list(ints_bytes, 'H')
                else:
                    return bytes_to_array(ints_bytes, np.uint16)


    def get_rng_floats(self, n_floats, output_type='array', timeout=GET_TIMEOUT_S):
        if n_floats == 0:
            self.lg.error('{} RNG Floats: Provide n_floats > 0'.format(self.dev_name))
            return None
        if n_floats >= 2**16:
            self.lg.error('{} RNG Floats: Provide n_floats as a 16-bit integer'.format(self.dev_name))
            return None

        comm = 'RNG_FLOATS'
        if self.snd_rava_msg(comm, [n_floats], 'H'):
            ints_bytes = self.get_queue_data(comm, timeout=timeout)
            if ints_bytes is None:
                return None
            else:
                if output_type == 'list':
                    return bytes_to_list(ints_bytes, 'f')
                else:
                    return bytes_to_array(ints_bytes, np.float32)


    def snd_rng_byte_stream_start(self, n_bytes, stream_interval_ms, postproc_id=D_RNG_POSTPROC['NONE']):
        if n_bytes == 0:
            self.lg.error('{} RNG Stream: Provide n_bytes > 0'.format(self.dev_name))
            return None
        if n_bytes >= 2**16:
            self.lg.error('{} RNG Stream: Provide n_bytes as a 16-bit integer'.format(self.dev_name))
            return None
        if stream_interval_ms > RNG_BYTE_STREAM_MAX_INTERVAL_MS:
            self.lg.error('{} RNG Stream: Provide a stream_interval_ms <= {}ms.'
                     .format(self.dev_name, RNG_BYTE_STREAM_MAX_INTERVAL_MS))
            return None
        if postproc_id not in D_RNG_POSTPROC_INV:
            self.lg.error('{} RNG Stream: Unknown postproc_id {}'.format(self.dev_name, postproc_id))
            return None

        comm = 'RNG_STREAM_START'

        # Make queue empty
        while not self.serial_data[comm].empty():
            self.serial_data[comm].get_nowait()

        # Send command
        msg_success = self.snd_rava_msg(comm, [n_bytes, stream_interval_ms, postproc_id], 'HHB')
        if msg_success:
            self.rng_streaming = True

        return msg_success


    def snd_rng_byte_stream_stop(self):
        comm = 'RNG_STREAM_STOP'
        msg_success = self.snd_rava_msg(comm)

        if msg_success:
            self.rng_streaming = False

        return msg_success


    def get_rng_byte_stream_data(self, output_type='array', timeout=GET_TIMEOUT_S):
        if not self.rng_streaming:
            self.lg.warning('{} RNG Stream: Streaming is disabled'.format(self.dev_name))
            return None, None

        comm = 'RNG_STREAM_BYTES'
        rng_bytes_a, rng_bytes_b = self.get_queue_data(comm, timeout=timeout)

        if (rng_bytes_a is None) or (rng_bytes_b is None):
            return None, None

        else:
            if output_type == 'list':
                rng_a = bytes_to_list(rng_bytes_a, 'B')
                rng_b = bytes_to_list(rng_bytes_b, 'B')
                return rng_a, rng_b

            elif output_type == 'array':
                    rng_a = bytes_to_array(rng_bytes_a, np.uint8)
                    rng_b = bytes_to_array(rng_bytes_b, np.uint8)
                    return rng_a, rng_b

            else:
                return rng_bytes_a, rng_bytes_b


    def get_rng_byte_stream_status(self, timeout=GET_TIMEOUT_S):
        comm = 'RNG_STREAM_STATUS'
        if self.snd_rava_msg(comm):
            return self.get_queue_data(comm, timeout=timeout)


    ## HEALTH

    def snd_health_startup_run(self):
        comm = 'HEALTH_STARTUP_RUN'
        return self.snd_rava_msg(comm)


    def get_health_startup_results(self, timeout=GET_TIMEOUT_S):
        comm = 'HEALTH_STARTUP_RESULTS'
        if self.snd_rava_msg(comm):
            success, pc_avg_vars, pc_avg_diff_vars, bias_bit_vars, bias_byte_vars = self.get_queue_data(comm, timeout=timeout)
            data_vars = [pc_avg_vars, pc_avg_diff_vars, bias_bit_vars, bias_byte_vars]
            data_names = ['pulse_count', 'pulse_count_diff', 'bit_bias', 'byte_bias']
            return success, dict(zip(data_names, data_vars))


    def get_health_continuous_errors(self, timeout=GET_TIMEOUT_S):
        comm = 'HEALTH_CONTINUOUS_ERRORS'
        if self.snd_rava_msg(comm):
            data_vars = self.get_queue_data(comm, timeout=timeout)
            n_errors = sum(data_vars)
            data_names = ['repetitive_count_a', 'repetitive_count_b',
                          'adaptative_proportion_a', 'adaptative_proportion_b']
            return n_errors, dict(zip(data_names, data_vars))


    ## PERIPHERALS

    def snd_periph_digi_mode(self, periph_id, mode_id):
        if periph_id == 0 or periph_id > 5:
            self.lg.error('{} Periph: Provide a periph_id between 1 and 5'.format(self.dev_name))
            return None
        if mode_id not in D_PERIPH_MODES_INV:
            self.lg.error('{} Periph: Unknown mode_id {}'.format(self.dev_name, mode_id))
            return None

        comm = 'PERIPH_MODE'
        return self.snd_rava_msg(comm, [periph_id, mode_id], 'BB')


    def get_periph_digi_state(self, periph_id=1, timeout=GET_TIMEOUT_S):
        if periph_id == 0 or periph_id > 5:
            self.lg.error('{} Periph: Provide a periph_id between 1 and 5'.format(self.dev_name))
            return None

        comm = 'PERIPH_READ'
        if self.snd_rava_msg(comm, [periph_id], 'B'):
            digi_state, digi_mode = self.get_queue_data(comm, timeout=timeout)
            return digi_state, D_PERIPH_MODES_INV[digi_mode]


    def snd_periph_digi_state(self, periph_id, digi_state):
        if periph_id == 0 or periph_id > 5:
            self.lg.error('{} Periph: Provide a periph_id between 1 and 5'.format(self.dev_name))
            return None

        comm = 'PERIPH_WRITE'
        return self.snd_rava_msg(comm, [periph_id, digi_state], 'BB')


    def snd_periph_digi_pulse(self, periph_id=1, pulse_duration_us=100):
        if periph_id == 0 or periph_id > 5:
            self.lg.error('{} Periph: Provide a periph_id between 1 and 5'.format(self.dev_name))
            return None
        if pulse_duration_us == 0:
            self.lg.error('{} Periph: Provide a pulse_duration_us > 0'.format(self.dev_name))
            return None

        comm = 'PERIPH_PULSE'
        return self.snd_rava_msg(comm, [periph_id, pulse_duration_us], 'BH')


    def snd_periph_d1_trigger_input(self, on=True):
        comm = 'PERIPH_D1_TRIGGER_INPUT'
        return self.snd_rava_msg(comm, [on], 'B')


    def snd_periph_d1_comparator(self, neg_to_d5=False, on=True):
        comm = 'PERIPH_D1_COMPARATOR'
        return self.snd_rava_msg(comm, [on, neg_to_d5], 'BB')


    def snd_periph_d1_delay_us_test(self, delay_us):
        if delay_us == 0:
            self.lg.error('{} Periph: Provide a delay_us > 0'.format(self.dev_name))
            return None

        comm = 'PERIPH_D1_DELAY_US_TEST'
        return self.snd_rava_msg(comm, [delay_us], 'B')


    def snd_periph_d2_input_capture(self, on=True):
        comm = 'PERIPH_D2_TIMER3_INPUT_CAPTURE'

        # Make queue empty
        if on:
            while not self.serial_data[comm].empty():
                self.serial_data[comm].get_nowait()

        # Send command
        return self.snd_rava_msg(comm, [on], 'B')


    def get_periph_d2_input_capture(self, timeout=GET_TIMEOUT_S):
        comm = 'PERIPH_D2_TIMER3_INPUT_CAPTURE'
        return self.get_queue_data(comm, timeout=timeout)


    def snd_periph_d3_timer3_trigger_output(self, interval_ms=1, on=True):
        if interval_ms == 0 or interval_ms > RNG_BYTE_STREAM_MAX_INTERVAL_MS:
            self.lg.error('{} Periph: Provide a {} > interval_ms > 0'.format(self.dev_name, RNG_BYTE_STREAM_MAX_INTERVAL_MS))
            return None

        comm = 'PERIPH_D3_TIMER3_TRIGGER_OUTPUT'
        return self.snd_rava_msg(comm, [on, interval_ms], 'BH')


    def snd_periph_d3_timer3_pwm(self, freq_prescaler=1, top=2**8-1, duty=10, on=True):
        if freq_prescaler == 0 or freq_prescaler > 5:
            self.lg.error('{} Periph D3: Provide a freq_prescaler between 1 and 5'.format(self.dev_name))
            return None
        if top == 0:
            self.lg.error('{} Periph D3: Provide a top > 0'.format(self.dev_name))
            return None
        if duty == 0:
            self.lg.error('{} Periph D3: Provide a duty > 0'.format(self.dev_name))
            return None

        comm = 'PERIPH_D3_TIMER3_PWM'
        return self.snd_rava_msg(comm, [on, freq_prescaler, top, duty], 'BBHH')


    def snd_periph_d3_timer3_sound(self, freq_hz=440, volume=255, on=True):
        comm = 'PERIPH_D3_TIMER3_SOUND'
        return self.snd_rava_msg(comm, [on, freq_hz, volume], 'BHB')


    def snd_periph_d4_pin_change(self, on=True):
        comm = 'PERIPH_D4_PIN_CHANGE'
        return self.snd_rava_msg(comm, [on], 'B')


    def get_periph_d5_adc_read(self, ref_5v=1, clk_prescaler=0, oversampling_n_bits=0, on=True, timeout=GET_TIMEOUT_S):
        if clk_prescaler == 0 or clk_prescaler > 7:
            self.lg.error('{} Periph D5: Provide a clk_prescaler between 1 and 7'.format(self.dev_name))
            return None
        if oversampling_n_bits > 6:
            self.lg.error('{} Periph D5: Provide a oversampling_n_bits <= 6'.format(self.dev_name))
            return None

        comm = 'PERIPH_D5_ADC'
        if self.snd_rava_msg(comm, [on, ref_5v, clk_prescaler, oversampling_n_bits], 'BBBB'):
            if on:
                return self.get_queue_data(comm, timeout=timeout)


    ## INTERFACES

    def get_interface_ds18bs0(self, timeout=GET_TIMEOUT_S):
        comm = 'INTERFACE_DS18B20'
        if self.snd_rava_msg(comm):
            return self.get_queue_data(comm, timeout=timeout)
=======
    def gen_pulse_counts(self, n_counts, rng_cores=DEFAULT_RNG_CORES):
        """
        Retrieve pulse-count measurements.

        Parameters
        ----------
        n_counts : uint16
            Number of pulse-count samples to acquire from each selected RNG core.
            The maximum allowed value is `self.rng_gen_max_nbytes_per_core`.
        rng_cores : R_RngCores
            Specifies which RNG core(s) to use.

        Returns
        ----------
        pulse_counts : (array, array) or array
            Pulse-count samples from the selected RNG core(s).
        """
        command_id = R_MessageComm.RNG_GEN_PULSE_COUNTS

        # IO Structure
        data_out_format = '<HB'
        data_in_format = '<HB'
        array_res_type = 'B'

        # Validate Output
        if not(
            n_counts > 0 and
            n_counts <= self.rng_gen_max_nbytes_per_core and
            rng_cores < len(R_RngCores) and
            rng_cores != R_RngCores.AB_XOR
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_counts, rng_cores)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # n_counts_in, rng_cores_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        if rng_cores == R_RngCores.AB_DUAL:
            pcs_a = array(array_res_type, rmsg.rand[::2])
            pcs_b = array(array_res_type, rmsg.rand[1::2])
            res = (pcs_a, pcs_b)

        else:
            pcs = array(array_res_type, rmsg.rand)
            res = pcs

        # Return Data
        return res


    def gen_bit(self, rng_cores=DEFAULT_RNG_CORES):
        """
        Retrieve random bits.

        Parameters
        ----------
        rng_cores : R_RngCores
            Specifies which RNG core(s) to use.

        Returns
        ----------
        bit : (bool, bool) or bool
            Bit samples from the selected RNG core(s).
        """
        command_id = R_MessageComm.RNG_GEN_BIT

        # IO Structure
        data_out_format = '<B'
        data_in_format = '<B'        

        # Validate Output
        if not(rng_cores < len(R_RngCores)):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, rng_cores)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # rng_cores_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        if rng_cores in [R_RngCores.AB_DUAL, R_RngCores.AB_ALT]:
            res = rmsg.rand[0], rmsg.rand[1]

        else:
            res = rmsg.rand[0]

        # Return Data
        return res


    def gen_bytes(self, n_bytes, rng_cores=DEFAULT_RNG_CORES, postproc=DEFAULT_RNG_POST_PROCESSING):
        """
        Retrieve random bytes.

        Parameters
        ----------
        n_bytes : uint16
            Number of random bytes to acquire from each selected RNG core.
            The maximum allowed value is `self.rng_gen_max_nbytes_per_core`.
        rng_cores : R_RngCores
            Specifies which RNG core(s) to use.
        postproc : R_RngPP
            Specifies the postprocessing mode.

        Returns
        ----------
        random_bytes : (array, array) or array
            Random bytes from the selected RNG core(s).
        """
        command_id = R_MessageComm.RNG_GEN_BYTES

        # IO Structure
        data_out_format = '<HBB'
        data_in_format = '<HBB'
        array_res_type = 'B'

        # Validate Output
        if not(
            n_bytes > 0 and
            n_bytes <= self.rng_gen_max_nbytes_per_core and
            rng_cores < len(R_RngCores) and
            postproc < len(R_RngPP)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_bytes, rng_cores, postproc)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # n_bytes_in, rng_cores_in, postproc_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        if rng_cores == R_RngCores.AB_DUAL:
            rnd_a = array(array_res_type, rmsg.rand[::2])
            rnd_b = array(array_res_type, rmsg.rand[1::2])
            res = rnd_a, rnd_b

        else:
            rnd = array(array_res_type, rmsg.rand)
            res = rnd

        # Return Data
        return res


    def gen_int8s(self, n_ints, delta, postproc=DEFAULT_RNG_POST_PROCESSING):
        """
        Retrieve 8-bit integers uniformly distributed over the interval [0, delta].

        Parameters
        ----------
        n_ints : uint16
            Number of ints to acquire.
            The maximum allowed value is `2 * self.rng_gen_max_nbytes_per_core`.
        delta : uint8
            Specifies the outcome interval as [0, int_delta].
        postproc : R_RngPP
            Specifies the postprocessing mode.

        Returns
        ----------
        ints : array
            Random ints generated.
        """
        command_id = R_MessageComm.RNG_GEN_INT8S

        # IO Structure
        data_out_format = '<HBB'
        data_in_format = '<HBB'
        array_res_type = 'B'

        # Validate Output
        if not(
            n_ints > 0 and
            n_ints <= 2 * self.rng_gen_max_nbytes_per_core and
            delta > 0 and
            postproc < len(R_RngPP)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_ints, delta, postproc)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # n_ints_in, delta_in, postproc_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        ints = array(array_res_type, rmsg.rand)

        # Return Data
        return ints


    def gen_int16s(self, n_ints, delta, postproc=DEFAULT_RNG_POST_PROCESSING):
        """
        Retrieve 16-bit integers uniformly distributed over the interval [0, delta].

        Parameters
        ----------
        n_ints : uint16
            Number of ints to acquire.
            The maximum allowed value is `self.rng_gen_max_nbytes_per_core`.
        delta : uint16
            Specifies the outcome interval as [0, int_delta].
        postproc : R_RngPP
            Specifies the postprocessing mode.

        Returns
        ----------
        ints : array
            Random ints generated.
        """
        command_id = R_MessageComm.RNG_GEN_INT16S

        # IO Structure
        data_out_format = '<HHB'
        data_in_format = '<HHB'
        array_res_type = 'H'

        # Validate Output
        if not(
            n_ints > 0 and
            n_ints <= self.rng_gen_max_nbytes_per_core and
            delta > 0 and
            postproc < len(R_RngPP)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_ints, delta, postproc)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # n_ints_in, delta_in, postproc_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        ints = array(array_res_type, rmsg.rand)

        # Return Data
        return ints


    def gen_floats(self, n_floats, postproc=DEFAULT_RNG_POST_PROCESSING):
        """
        Retrieve floats uniformly distributed over the interval [0, 1).

        Parameters
        ----------
        n_floats : uint16
            Number of floats to acquire.
            The maximum allowed value is `self.rng_gen_max_nbytes_per_core / 2`.
        postproc : R_RngPP
            Specifies the postprocessing mode.

        Returns
        ----------
        floats : array
            Random floats generated.
        """
        command_id = R_MessageComm.RNG_GEN_FLOATS

        # IO Structure
        data_out_format = '<HB'
        data_in_format = '<HB'
        array_res_type = 'f'

        # Validate Output
        if not(
            n_floats > 0 and
            n_floats <= self.rng_gen_max_nbytes_per_core / 2 and
            postproc < len(R_RngPP)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_floats, postproc)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # n_floats_in, postproc_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        floats = array(array_res_type, rmsg.rand)

        # Return Data
        return floats


    def gen_floats_downey(self, n_floats, postproc=DEFAULT_RNG_POST_PROCESSING):
        """
        Retrieve floats uniformly distributed over the interval [0, 1) using the method described
        in: Downey, Allen B. "Generating pseudo-random floating-point values"
        https://www.allendowney.com/research/rand/downey07randfloat.pdf

        Parameters
        ----------
        n_floats : uint16
            Number of floats to acquire.
            The maximum allowed value is `self.rng_gen_max_nbytes_per_core / 2`.
        postproc : R_RngPP
            Specifies the postprocessing mode.

        Returns
        ----------
        floats : array
            Random floats generated.
        """
        command_id = R_MessageComm.RNG_GEN_FLOATS_DOWNEY

        # IO Structure
        data_out_format = '<HB'
        data_in_format = '<HB'
        array_res_type = 'f'

        # Validate Output
        if not(
            n_floats > 0 and
            n_floats <= self.rng_gen_max_nbytes_per_core / 2 and
            postproc < len(R_RngPP)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_floats, postproc)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # n_floats_in, postproc_in = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        floats = array(array_res_type, rmsg.rand)

        # Return Data
        return floats


    def start_byte_stream(self, n_bytes, interval_ms,
                                rng_cores=DEFAULT_RNG_CORES, postproc=DEFAULT_RNG_POST_PROCESSING):
        """
        Request to start periodic random-byte streaming.

        Parameters
        ----------
        n_bytes : uint16
            Number of random bytes to acquire from each selected RNG core.
            The maximum allowed value is `self.rng_gen_max_nbytes_per_core`.
        interval_ms : uint16
            Time interval, in milliseconds, between successive byte-generation events.
        rng_cores : R_RngCores
            Specifies which RNG core(s) to use.
        postproc : R_RngPP
            Specifies the postprocessing mode.

        Returns
        ----------
        True
        """
        command_id = R_MessageComm.RNG_START_BYTE_STREAM

        # Is streaming?
        if self.rng_bytes_stream_cfg.streaming:
            raise RAVAByteStreamingError(f'{self.name} {command_id.name} -> Already streaming')

        # IO Structure
        data_out_format = '<HHBB'
        data_in_format = ''

        # Validate Output
        if not(
            n_bytes > 0 and
            n_bytes <= self.rng_gen_max_nbytes_per_core and
            rng_cores < len(R_RngCores) and
            postproc < len(R_RngPP)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, n_bytes, interval_ms, rng_cores, postproc)

        # Send Request
        request_id, q = self.send_rava_msg(command_id, data_out)

        # Get msg from queue
        try:
            rmsg = q.get(timeout=QUEUE_READ_TIMEOUT_S)

        except queue.Empty as err:
            raise RAVAQueueTimeoutError(
                f'{self.name} send_retrieve_rava_msg -> Empty Queue'
                ) from err

        # Test for error
        rmsg.validate()

        # Deserialize Input
        # Process Input
        self.rng_bytes_stream_cfg.streaming = True
        self.rng_bytes_stream_cfg.request_id = request_id

        # Return Data
        return True


    def get_byte_stream(self):
        """
        Retrieve random bytes produced by the asynchronous byte-stream generator. Bytes are
        returned in FIFO order.

        Returns
        ----------
        random_bytes : (array, array) or array
            Random bytes from the selected RNG core(s).
        """
        command_id = R_MessageComm.RNG_GEN_BYTES_STREAM

        # Is streaming?
        if not self.rng_bytes_stream_cfg.streaming:

            raise RAVAByteStreamingError(f'{self.name} {command_id.name} -> Not streaming')

        # IO Structure
        data_out_format = ''
        data_in_format = '<HHBB'
        array_res_type = 'B'

        # Get queue
        q = self.comm_pending_msgs.get(self.rng_bytes_stream_cfg.request_id, None)

        if q is None:
            raise RAVAMissingQueueError(
                f'{self.name} {command_id.name} -> Pending message queue '
                f'not found for request_id {rmsg.req_id}'
                )

        # Get msg
        try:
            rmsg = q.get(timeout=QUEUE_READ_TIMEOUT_S)

        except queue.Empty as err:
            self.log.info(f'{self.name} {command_id.name} -> No message available')
            return None

        # Test for error
        rmsg.validate()

        # Deserialize Input
        n_bytes, interval_ms, rng_cores, postproc = struct.unpack(data_in_format, rmsg.data)

        if rng_cores == R_RngCores.AB_DUAL:
            rnd_a = array(array_res_type, rmsg.rand[::2])
            rnd_b = array(array_res_type, rmsg.rand[1::2])
            res = rnd_a, rnd_b

        else:
            rnd = array(array_res_type, rmsg.rand)
            res = rnd

        # Process Input
        # Return Data
        return res


    def get_status_byte_stream(self):
        """
        Request to inform whether fixed-interval random-byte generation is enabled and the
        associated request identifier.

        Returns
        ----------
        streaming : bool
            True if periodic random-byte streaming is enabled.
        req_id : uint8
            Request ID associated with the streaming process.
        """
        command_id = R_MessageComm.RNG_GET_STATUS_BYTE_STREAM

        # IO Structure
        data_out_format = ''
        data_in_format = '<?H' # streaming, req_id

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        streaming, req_id, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        return streaming, req_id


    def stop_byte_stream(self):
        """
        Request to stop periodic random-byte streaming.
        """
        command_id = R_MessageComm.RNG_STOP_BYTE_STREAM

        # Is streaming?
        if not self.rng_bytes_stream_cfg.streaming:
            return True

        # IO Structure
        data_out_format = ''
        data_in_format = ''

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        # Process Input

        ## Remove stream queue from pending list
        self.comm_pending_msgs.pop(self.rng_bytes_stream_cfg.request_id)

        ## Update
        self.rng_bytes_stream_cfg.streaming = False
        self.rng_bytes_stream_cfg.request_id = 0

        # Return Data
        return True
>>>>>>> 4fcf521 (Update v3.0.0)
