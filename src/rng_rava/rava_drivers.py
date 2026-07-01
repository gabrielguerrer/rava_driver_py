"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Provides the high-level RAVA device classes used by applications.
"""

from .rava_comm_tcp import RAVACommTcp
from .rava_comm_usb import RAVACommUsb
from .rava_device import RAVADevice
from .rava_health import RAVAHealth
from .rava_log import RAVALog
from .rava_rng import RAVARng

############################
# RAVA DRIVERS
############################


class RAVA_USB(RAVADevice, RAVARng, RAVAHealth, RAVALog, RAVACommUsb):
    """
    USB-connected RAVA device implementation.

    Provides an interface that combines USB communication, device control, random number
    generation, and health-monitoring functionality.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVA_USB'



class RAVA_TCP(RAVADevice, RAVARng, RAVAHealth, RAVALog, RAVACommTcp):
    """
    TCP-connected RAVA device implementation.

    Provides an interface that combines TCP communication, device control, random number
    generation, and health-monitoring functionality.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVA_TCP'