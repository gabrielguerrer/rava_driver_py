"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Base communication layer for RAVA devices.
"""

import queue
import threading

from .rava_comm_protocol import RNG_GEN_MAX_NBYTES_PER_CORE, \
    FIRMWARE_MIN_VERSION_MAJOR, FIRMWARE_MIN_VERSION_MINOR, FIRMWARE_MIN_VERSION_PATCH
from .rava_comm_protocol import R_MessageComm, R_MessageError, RAVAMessage, RAVAMessageParser
from .rava_errors import *

############################
# RAVA COMM
############################

COMM_READ_TIMEOUT_S = 0.020
COMM_READ_LONG_TIMEOUT_S = 2.
COMM_WRITE_TIMEOUT_S = 5.
QUEUE_READ_TIMEOUT_S = 5.


class RAVAComm:
    """
    Base communication layer for RAVA devices.

    Responsibilities:
    - Serialize and transmit commands to the firmware
    - Receive and parse protocol messages asynchronously
    - Match responses to requests using request IDs
    - Validate protocol integrity, converting errors into Python exceptions

    Communication follows a request/response model in which the main thread sends commands while a
    dedicated listener thread continuously receives and dispatches incoming messages.

    Transport-specific derived classes (USB, TCP, etc.) are responsible for providing the low-level
    read() and write() methods.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVAComm'

        # Device
        self.mcu = None
        self.model = None
        self.firmw_ver = None
        self.firmw_modules = None
        self.rng_gen_max_nbytes_per_core = RNG_GEN_MAX_NBYTES_PER_CORE
        self.serial_number = b''

        # Communication
        self.rmsg_parser = RAVAMessageParser()

        self.comm_request_id = 0
        self.comm_pending_msgs = {}

        self.listening = threading.Event()
        self.comm_listen_thread = None


    def open(self):
        """
        Called after the transport-derived class has successfully opened its underlying transport.

        Initialize communication with the device. Steps:
          - Start listener thread
          - Query device information
          - Verify firmware compatibility
          - Check startup health tests
        """

        # Start listening for USB commands
        self.start_listen_thread()

        # Get device information
        dev_infos = self.dev_get_info()

        self.mcu, self.model, self.firmw_ver, self.firmw_modules, \
            self.rng_gen_max_nbytes_per_core, self.serial_number = dev_infos

        self.log_dev_info(*dev_infos)

        # Update message parser
        self.rmsg_parser.update_gen_max_nbytes(self.rng_gen_max_nbytes_per_core)

        # Check compatibility with Firmware Version
        firmw_ver_min = (
            FIRMWARE_MIN_VERSION_MAJOR, FIRMWARE_MIN_VERSION_MINOR, FIRMWARE_MIN_VERSION_PATCH
            )

        if not self.firmw_ver >= firmw_ver_min:
            raise RAVAFirmwareVersionError(
                f'{self.name} open -> Firmware version {self.firmw_ver} is incompatible '
                f'with minimum required version {firmw_ver_min}'
                )

        # Check startup health tests
        if self.firmw_modules.health_startup_enabled:
            heath_startup_res = self.health_startup_get_results()

            res_global, pc, pc_diff, bias, chisq = heath_startup_res

            self.log_health_startup_results(*heath_startup_res)

            if not res_global:
                self.log.warning(f'{self.name} open -> Health Startup Tests Failed!')


    def close(self):
        """
        Called before the transport-derived class closes its transport.
        """

        self.stop_listen_thread()


    def start_listen_thread(self):
        """
        Start the background thread responsible for receiving and processing incoming RAVA messages.
        """

        self.comm_listen_thread = threading.Thread(target=self.read_rava_msg_loop, daemon=True)
        self.comm_listen_thread.start()


    def stop_listen_thread(self):
        """
        Stop the message listener thread and wait for it to terminate.

        If called from within the listener thread itself, the join step is skipped to avoid a
        self-join deadlock.
        """

        # Quit read_rava_msg_loop()
        self.listening.clear()

        # Terminate read_rava_msg_loop()
        if self.comm_listen_thread:
            if self.comm_listen_thread != threading.current_thread():
                self.comm_listen_thread.join()


    def next_request_id(self):
        """
        Allocate a unique request ID.
        """
        for _ in range(256):

            # Max value = 255
            self.comm_request_id = (self.comm_request_id + 1) & 0xFF

            # Available?
            if self.comm_request_id not in self.comm_pending_msgs:
                return self.comm_request_id

        raise RAVARequestIDError(f'{self.name} next_request_id -> No request IDs available')


    def send_rava_msg(self, command_id, data_bytes):
        """
        Compose and transmit a RAVA message.

        The message is serialized, CRC protected, and sent through the transport layer. A response
        queue is created and associated with the generated request ID, enabling the listener thread
        to asynchronously route the corresponding reply back to the caller.

        Parameters
        ----------
        command_id : R_MessageComm
            Command identifier from the R_MessageComm enum.
        data_bytes: bytes
            Command parameters serialized in little-endian format.

        Returns
        ----------
        request_id : int
            Unique identifier assigned to the message request.
        q : Queue
            Response queue associated with the request. The caller can use this queue to wait for
            and retrieve the corresponding response message.
        """

        # Compose message
        rmsg = RAVAMessage(
            client_id = 0,
            request_id = self.next_request_id(),
            request_error = R_MessageError.OK,
            command_id = command_id,
            data = data_bytes,
            rand = b''
        )

        rmsg_bytes = rmsg.to_bytes()

        # Debug
        self.log.debug(f'{self.name} > Sending RAVAMessage\n{rmsg}')

        # Create response queue
        # Unlimited size for rng stream; 1 otherwise
        q_size = 0 if command_id == R_MessageComm.RNG_START_BYTE_STREAM else 1
        q = queue.Queue(maxsize = q_size)

        # Add queue to pending message dictionary
        # Needs to be done before sending the message, otherwise can create racing condition
        self.comm_pending_msgs[rmsg.request_id] = q

        # Send Message
        self.write(rmsg_bytes)

        return rmsg.request_id, q


    def send_retrieve_rava_msg(self, command_id, data_bytes):
        """
        Send a RAVA message and wait for the corresponding response.

        This method provides a synchronous wrapper around the underlying asynchronous
        request/response mechanism. While the asynchronous API is primarily intended for continuous
        RNG byte streaming, most commands are more conveniently accessed through this blocking
        interface. If the firmware reports an error, the corresponding Python exception is raised
        automatically.

        Parameters
        ----------
        command_id : R_MessageComm
            Command identifier from the R_MessageComm enum.
        data_bytes: bytes
            Command parameters serialized in little-endian format.

        Returns
        ----------
        rmsg : RAVAMessage
            RAVA message payload.
        """

        # Send Request
        request_id, q = self.send_rava_msg(command_id, data_bytes)

        # Get msg from queue
        try:
            rmsg = q.get(timeout=QUEUE_READ_TIMEOUT_S)

        except queue.Empty as err:

            raise RAVAQueueTimeoutError(
                f'{self.name} send_retrieve_rava_msg -> Message queue is empty'
                ) from err

        # Remove queue from pending
        self.comm_pending_msgs.pop(request_id, None)

        # Test for error
        rmsg.validate()

        # Return RAVA Message
        return rmsg


    def read_rava_msg_header(self, listening_event):
        """
        Read bytes from the transport layer until a RAVA protocol message header is reconstructed.

        Bytes are continuously read from the transport layer and fed to the protocol parser until
        a message header is received. If the message includes a random payload, only the header is
        returned; the payload must be read separately.

        Transport implementations should use timeout-based reads to allow graceful detection of
        disconnections and prevent indefinite blocking.

        Parameters
        ----------
        listening_event : threading.Event
            Controls the receive loop. The method exits when the event is cleared.

        Returns
        ----------
        rmsg : RAVAMessage | None
            The reconstructed message header, or None if the receive loop terminates before a
            message is received.
        """

        while listening_event.is_set():

            # Bit available?
            # Transport protocols reads must use a timeout
            b = self.read(1)

            # Read timed out
            if b == b'':
                continue

            # Command header received?
            rmsg = self.rmsg_parser.parse_byte(b)
            if rmsg is not None:

                # Debug
                self.log.debug(f'{self.name} > RAVAMessage Received\n{rmsg}')

                return rmsg

        return None


    def read_rava_msg_rand(self, rmsg):
        """
        Read the random payload of a previously parsed protocol message.

        This method is intended to be called only for messages whose `rand_len > 0`. After reading
        the random bytes, the parser state is reset so it is ready to receive the next protocol
        message.

        Parameters
        ----------
        rmsg : RAVAMessage
            The protocol message whose random payload is to be read.
        """

        rmsg.rand = self.read(rmsg.rand_len, COMM_READ_LONG_TIMEOUT_S)
        self.rmsg_parser.random_payload_retrieved()

        if rmsg.rand_len != len(rmsg.rand):
            raise RAVAReadError(
                f'{self.name} read_rava_msg_rand -> Random payload size mismatch'
            )


    def read_rava_msg_loop(self):
        """
        RAVA message dispatch loop.

        Continuously parses incoming bytes and routes completed messages to the queue associated
        with the corresponding request ID.

        This mechanism allows multiple requests to be in flight simultaneously while presenting a
        synchronous API to the caller.
        """

        self.listening.set()

        try:

            # Loop while connected
            while self.listening.is_set():

                # RAVA message available?
                rmsg = self.read_rava_msg_header(self.listening)

                # stop_listen_thread called()
                if rmsg is None:
                  break

                # Obtain rand if available
                if rmsg.rand_len > 0:
                    self.read_rava_msg_rand(rmsg)

                # Retrieve message queue from pending dict
                q = self.comm_pending_msgs.get(rmsg.request_id, None)

                if q is None:
                    raise RAVAMissingQueueError(
                        f'{self.name} read_rava_msg_loop -> Pending message queue '
                        f'not found for request_id {rmsg.request_id}'
                        )

                # Send data via queue
                q.put(rmsg)

        except (RAVAMissingQueueError, RAVADisconnectedError) as err:
            self.log.error(str(err))

        except Exception as err:
            self.log.exception(f'{self.name} read_rava_msg_loop -> Unexpected failure: {err}')

        finally:
            self.listening.clear()