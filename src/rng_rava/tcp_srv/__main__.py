"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
RAVA TCP server.

This utility exposes a locally connected RAVA USB device through a TCP interface, allowing multiple 
remote clients to access the device using the RAVA TCP protocol.

The server can be started from the command line with: `python3 -m rng_rava.rcp_srv`. Available 
command-line options and their descriptions can be displayed using the -h or --help flag.
"""

import argparse
import asyncio
import ipaddress

from .rava_tcp_server import RAVATcpServer
from ..rava_comm_usb import find_rava_sns
from ..rava_drivers import RAVA_USB
from ..rava8.rava8_drivers import RAVA8_USB

############################
# TAVA TCP SERVER CLI
############################


RAVA_DEVS = ['RAVA_USB', 'RAVA8_USB']


def valid_ip(value):
    """
    Validates the input as a valid IP address.
    """
    try:
        return str(ipaddress.ip_address(value))

    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid IP address: {value}")


async def main():
    """
    Parse command-line arguments, open the selected RAVA device, and start the TCP server.
    """

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='RAVA TCP relay server')

    parser.add_argument(
        '--dev',
        choices = RAVA_DEVS,
        default = 'RAVA_USB',
        help = 'USB device type'
    )

    parser.add_argument(
        '--sn',
        default = '',
        help = 'Serial number of the RAVA device. If omitted, the first available device '
            '(sorted alphabetically by serial number) is used.'
    )

    parser.add_argument(
        '-o', '--host',
        type = valid_ip,
        default = '127.0.0.1',
        help = 'TCP bind address'
    )

    parser.add_argument(
        '-p', '--port',
        type = int,
        default = 4884,
        help = 'TCP port'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help = 'Enable verbose logging.'
    )

    args = parser.parse_args()

    # Instantiate the requested RAVA device implementation
    if args.dev == 'RAVA_USB':
        rng = RAVA_USB()

    elif args.dev == 'RAVA8_USB':
        rng = RAVA8_USB()

    else:
        raise RuntimeError(f"Unknown device {args.dev}. Valid choices are: {', '.join(RAVA_DEVS)}")

    # Resolve which physical device to open
    # If no serial number is specified, use the first detected device
    if args.sn == '':
        sns = find_rava_sns()

        if not sns:
            raise RuntimeError('No RAVA device found')

        sn = sns[0]

    else:
        sn = args.sn

    # Connect to RAVA device
    rng.open(sn)

    # Enable verbose device logging when requested
    if args.verbose == True:
        rng.log_level('DEBUG')

    # Create and run the TCP server
    rava_srv = RAVATcpServer(rng, args.host, args.port)

    await rava_srv.start()


# Program entry point
if __name__ == "__main__":
    try:
        asyncio.run(main())

    # Exit cleanly when interrupted from the terminal
    except KeyboardInterrupt:
        pass