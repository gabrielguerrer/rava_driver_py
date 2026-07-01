"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Multi-client TCP relay server for RAVA devices.

The server exposes a single locally connected RAVA USB device through the RAVA TCP protocol,
allowing multiple remote clients to share the same hardware device concurrently.

The current implementation assumes that clients are trusted. Consequently, all device functionality
is exposed, including operations that modify the device configuration. Future versions should
introduce authentication, access control, and permission management to protect against potentially
malicious clients.

Future enhancements:
  - Support for multiple RAVA USB devices
  - Client authentication; Client groups ; Quota
  - List of authorized commands per client group
  - Enforce a `rng_gen_max_nbytes_per_core` different from the RAVA devices
  - Cache responses to static commands (e.g., device_info and health_startup_get_results) in
    RAVAUsbWorker and return the cached data to clients instead of querying the device
  - Monitoring of client and device usage
  - Byte stream with periodic byte generation managed by the server instead of the MCU
  - TLS/SSL support
"""

import asyncio
import threading

from ..rava_comm import R_MessageComm, R_MessageError, RAVAMessageParser
from ..rava_drivers import RAVA_USB
from ..rava_errors import RAVAClientIDError
from ..rava_log import RAVALog

############################
# RAVA COMM TCP SERVER
############################


class RAVAUsbWorker(RAVALog):
    """
    Shared context for the RAVA USB communication workers.

    This class owns the RAVA USB device instance together with the queues, events, and
    synchronization primitives shared by the communication workers.

    A dedicated listener thread continuously receives bytes from the USB device, reconstructs
    complete RAVA protocol messages, and places them into the `usb_to_cli_queue`.

    Two asyncio workers handle message forwarding:
      - `usb_to_cli_worker()` retrieves messages from `usb_to_cli_queue` and routes them to the
        appropriate client.
      - `cli_to_usb_worker()` receives client commands and forwards them to the RAVA device.

    Since the RAVA device processes only one request at a time, `usb_send_ready` is used to ensure
    that only a single client command is processed while waiting for the corresponding response.
    """

    def __init__(self, rava_usb : RAVA_USB, clients_max = None):
        super().__init__()
        self.name = f'RAVAUsbWorker SN={str(rava_usb.serial_number)}'

        # RAVA_USB
        self.rava_usb = rava_usb

        # The listening on the USB device is managed by this class, instead of RAVACommUsb
        self.rava_usb.stop_listen_thread()

        # Asyncio loop used for `call_soon_threadsafe()` in `usb_listen_loop()`
        self.aio_loop = asyncio.get_running_loop()

        # Queue of RAVA messages waiting to be sent to the client: USB -> Client
        self.usb_to_cli_queue = asyncio.Queue()

        # Queue of RAVA messages waiting to be sent to the USB device: Client -> USB
        self.cli_to_usb_queue = asyncio.Queue()

        # A new command is transmitted to the USB device only when the previous response has been
        # received
        self.usb_send_ready = asyncio.Event()

        # Clients info
        self.client_id = 0
        self.clients = {}
        self.clients_max = clients_max

        # Start RAVA device listening thread
        self.usb_listening = threading.Event()
        self.usb_listen_loop_thread = threading.Thread(target=self.usb_listen_loop, daemon=True)
        self.usb_listen_loop_thread.start()


    def close(self):
        """
        Shut down the USB worker.

        Stops the USB listener thread, closes the USB device, disconnects all connected clients,
        and resets the worker state.
        """

        # Stop usb listening thread and wait for its completion
        self.usb_listening.clear()

        if self.usb_listen_loop_thread:
            if self.usb_listen_loop_thread != threading.current_thread():
                self.usb_listen_loop_thread.join()

        # Close USB device
        self.rava_usb.close()

        # Disconnect all clients
        for client in self.clients.values():
            client.writer.close()

        # Reset client counter
        # self.clients are emptied in RAVATcpServer.disconnect_client()
        self.client_id = 0


    def next_client_id(self):
        """
        Allocate a unique client ID.
        """

        for _ in range(256):

            # Max value = 255
            self.client_id = (self.client_id + 1) & 0xFF

            # Available?
            if self.client_id not in self.clients:
                return self.client_id

        raise RAVAClientIDError(f'{self.name} next_client_id -> No client IDs available')


    def usb_listen_loop(self):
        """
        Listen for messages from the RAVA USB device.

        This method runs in a dedicated thread. It continuously reads RAVA protocol messages from
        the USB device and forwards them to the asyncio event loop through `usb_to_cli_queue`.

        When a message header is successfully received, it signals `cli_to_usb_worker` via the
        `usb_send_ready` event that the device is ready to accept the next client request.
        """

        self.usb_listening.set()

        while self.usb_listening.is_set():

            try:
                # Read the next RAVA message header
                rmsg = self.rava_usb.read_rava_msg_header(self.usb_listening)

                # stop_listen_thread called()
                if rmsg is None:
                    break

                # Enable `cli_to_usb_worker` to process a new message
                if rmsg.command_id != R_MessageComm.RNG_GEN_BYTES_STREAM:
                    self.aio_loop.call_soon_threadsafe(self.usb_send_ready.set)

                # Read the random payload, if present
                if rmsg.rand_len > 0:
                    self.rava_usb.read_rava_msg_rand(rmsg)

                # Forward the complete message to the `usb_to_cli_worker` asyncio worker
                self.aio_loop.call_soon_threadsafe(self.usb_to_cli_queue.put_nowait, rmsg)

            # Forward any exception to the asyncio loop so the server can terminate gracefully
            except Exception as e:
                self.aio_loop.call_soon_threadsafe(self.usb_to_cli_queue.put_nowait, e)

                self.close()


    async def usb_to_cli_worker(self):
        """
        Receive RAVA messages from the USB device and route them to clients.

        Each message contains a client identifier that is used to locate the destination TCP
        connection.

        After a response is forwarded to a client, the client's `send_ready` event is set, allowing
        it to transmit the next command. This mechanism ensures that each client has at most one
        outstanding request at a time, preventing it from flooding the server with requests.
        """

        while True:
            # Read rmsg header from queue
            rmsg = await self.usb_to_cli_queue.get()

            # usb_listen_loop thread crashed?
            if isinstance(rmsg, Exception):
                raise rmsg

            # Transform rmsg to bytes
            rmsg_bytes = rmsg.to_bytes()

            # Obtain client writer
            client_id = rmsg.client_id
            client = self.clients.get(client_id)

            if client is None:
                self.log.error(
                    f'{self.name} usb_to_cli_worker -> #{client_id} not found in clients dictionary')
                continue

            # Debug
            self.log.debug(
                f'{self.name} usb_to_cli_worker -> Received {rmsg_bytes} from RNG; '
                f'Sending to client #{client_id}'
                )

            # Forward rmsg to TCP client
            try:
                client.writer.write(rmsg_bytes)
                await client.writer.drain()

            # Client disconnected; Continue running
            except (ConnectionResetError, BrokenPipeError, OSError):
                pass

            # TCP error; Continue running
            except Exception as err:
                self.log.error(f'{self.name} usb_to_cli_worker -> TCP send error : {err}')

            # Enable client to send a new command request
            if rmsg.command_id != R_MessageComm.RNG_GEN_BYTES_STREAM:
                client.send_ready.set()


    async def cli_to_usb_worker(self):
        """
        Forward client requests to the USB device.

        Commands are consumed from the transmit queue and written to the RAVA device.

        The synchronization event serializes USB transactions, ensuring that only one command is in
        flight at a time. A new command is transmitted only after `usb_to_cli_worker()` receives the
        response to the previous command.
        """

        self.usb_send_ready.set()

        while True:

            # Wait for event; They are set in `usb_listen_loop` whenever a message is received from
            # the RNG device
            await self.usb_send_ready.wait()

            # Read RAVA message
            rmsg = await self.cli_to_usb_queue.get()
            rmsg_bytes = rmsg.to_bytes()

            # Debug
            self.log.debug(f'{self.name} cli_to_usb_worker -> Sending {rmsg_bytes} to RNG')

            # Forward message to RAVA device
            try:
                self.rava_usb.write(rmsg_bytes)

            # Error with the RAVA device; Terminate the server
            except Exception as err:
                self.log.error(f'{self.name} cli_to_usb_worker -> USB write error : {err}')
                raise

            # Block new USB requests until the current request has been processed
            self.usb_send_ready.clear()


class RAVAClient:
    """
    Connected TCP client.

    Stores the client's TCP streams, unique client ID, and a dedicated message parser used to
    interpret incoming requests from the client.
    """

    def __init__(self, client_id, reader, writer, rng_gen_max_nbytes_per_core):
        self.client_id = client_id

        # TCP
        self.reader = reader
        self.writer = writer
        self.addr = writer.get_extra_info('peername')

        # RAVA message parser
        self.rmsg_parser = RAVAMessageParser(rng_gen_max_nbytes_per_core)

        # A new command is transmitted to the USB device only when the previous response has been
        # received; Avoids the client flooding the command queue
        self.send_ready = asyncio.Event()


class RAVATcpServer(RAVALog):
    """
    Multi-client TCP relay for a RAVA USB device.

    The server accepts connections from multiple TCP clients and forwards their requests to a
    locally connected RAVA device. Responses received from the device are routed back to the
    originating client.
    """

    def __init__(self, rava_usb, host, port, clients_max=None):
        super().__init__()
        self.name = 'RAVATcpServer'

        # RAVA USB
        self.rava_worker = RAVAUsbWorker(rava_usb, clients_max)

        # Server
        self.host = host
        self.port = port
        self.server = None


    async def start(self):
        """
        Start the TCP server.

        Also launches the USB transmit and receive worker. The method blocks until all workers
        terminate or one of them raises an exception.
        """

        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self.rava_worker.cli_to_usb_worker(), name='cli_to_usb_worker')
                tg.create_task(self.rava_worker.usb_to_cli_worker(), name='usb_to_cli_worker')
                tg.create_task(self.server_worker(), name='server_worker')

        # Log the last exception
        except Exception as err:
            if isinstance(err, ExceptionGroup):
                exc = err.exceptions[0]
                self.log.error(exc)
            else:
                self.log.error(err)

        finally:
            await self.close()


    async def server_worker(self):
        """
        Create and run the TCP listener.

        Accepts incoming client connections and dispatches them to `handle_client()`.
        """

        # Create server
        self.server = await asyncio.start_server(
            client_connected_cb = self.handle_client,
            host = self.host,
            port = self.port,
            reuse_address=True
            )

        # Log
        self.log.info(f'{self.name} start -> Listening on {self.host}:{self.port}...')

        # Run server
        async with self.server:
            await self.server.serve_forever()


    async def close(self):
        """
        Shut down the server and release all resources.

        Closes the TCP listener, disconnects all clients, and closes the underlying RAVA USB device.
        """

        if self.server is None:
            return

        # Stop accepting new connections.
        self.server.close()

        # Close all active client connections
        clients = list(self.rava_worker.clients.values())
        for cli in clients:
            cli.writer.close()
        await asyncio.gather(*(cli.writer.wait_closed() for cli in clients), return_exceptions=True)

        # Wait until the listening socket is closed
        await self.server.wait_closed()

        self.server = None

        # Close rng worker
        self.rava_worker.close()

        # Log
        self.log.info(f'{self.name} close -> Server closed')


    async def handle_client(self, reader, writer):
        """
        Handle a newly accepted TCP client connection.

        Allocates a unique client identifier, registers the client, and processes incoming protocol
        messages via `listen_client()` until the client disconnects.
        """

        # Assign RAVA USB device
        rava_worker = self.rava_worker

        # Max clients reached? Disconnect
        if rava_worker.clients_max is not None and \
           len(rava_worker.clients) >= rava_worker.clients_max:
            writer.close()
            await writer.wait_closed()
            return

        # Get client ID
        try:
            client_id = rava_worker.next_client_id()

        # More than 256 clients? Disconnect
        except RAVAClientIDError as err:
            self.log.error(err)
            writer.close()
            await writer.wait_closed()
            return

        # Update client info
        client = RAVAClient(client_id, reader, writer, rava_worker.rava_usb.rng_gen_max_nbytes_per_core)
        rava_worker.clients[client_id] = client

        # Log
        self.log.info(
            f'{self.name} handle_client -> Hello #{client_id} @ {client.addr} '
            f' assigned to RAVA SN={rava_worker.rava_usb.serial_number}'
            )

        # Run client listener
        try:
            await self.listen_client(client, rava_worker.cli_to_usb_queue)

        except asyncio.CancelledError:
            raise

        except Exception as err:
            self.log.error(f'{self.name} handle_client -> {err}')

        # Client disconnected
        finally:
            await self.disconnect_client(client_id, rava_worker)


    async def listen_client(self, client, cli_to_usb_queue):
        """
        Receive and process messages from a TCP client.

        Complete protocol messages are tagged with the client's identifier and forwarded to the USB
        transmit worker.

        The event `client.send_ready` ensures a new command is transmitted to the USB device only
        when the previous response has been received; Avoids the client flooding the command queue.
        """

        client.send_ready.set()

        while True:

            # Read client byte
            b = await client.reader.read(1)

            # Clean disconnect?
            if not b:
                break

            # RAVA message received?
            rmsg = client.rmsg_parser.parse_byte(b)
            if rmsg is not None:

                # Log
                self.log.info(
                    f'{self.name} listen_client -> Received command_id {rmsg.command_id} '
                    f'from client #{client.client_id}'
                    )

                # Inject client_id for proper routing
                rmsg.client_id = client.client_id

                # Test for errors
                if rmsg.request_error != R_MessageError.OK:

                    # Send error to client; avoiding unecessary processing by the RNG device
                    client.writer.write(rmsg.to_bytes())
                    await client.writer.drain()
                    continue

                # Wait for the completion of the previous request
                await client.send_ready.wait()
                client.send_ready.clear()

                # Forward command bytes to USB worker
                cli_to_usb_queue.put_nowait(rmsg)


    async def disconnect_client(self, client_id, rava_worker):
        """
        Remove a client from the server and close its TCP connection.
        """

        # Find client in dictionary
        try:
            client = rava_worker.clients.pop(client_id)

        except KeyError as err:
            self.log.error(
                f'{self.name} disconnect_client -> #{client_id} not found in clients dictionary '
                f'assigned to RAVA SN={rava_worker.rava_usb.serial_number}'
                )
            return

        # Close client
        try:
            client.writer.close()
            await client.writer.wait_closed()

        except Exception:
            pass

        # Log
        self.log.info(
            f'{self.name} disconnect_client -> Bye #{client_id} @ {client.addr} '
            f' assigned to RAVA SN={rava_worker.rava_usb.serial_number}'
            )