"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This module provides the high-level RAVA8 device classes used by applications.

RAVA8 is the ATmega32U4-based implementation of the RAVA architecture.
"""

from ..rava_comm_tcp import RAVACommTcp
from ..rava_comm_usb import RAVACommUsb
from ..rava_device import RAVADevice
from ..rava_health import RAVAHealth
from ..rava_log import RAVALog
from ..rava_rng import RAVARng
from .rava8_eeprom import RAVA8Eeprom
from .rava8_peripherals import RAVA8Peripherals

############################
# RAVA8 DRIVERS
############################


class RAVA8_USB(RAVA8Eeprom, RAVA8Peripherals, RAVADevice, RAVARng, RAVAHealth, RAVALog, RAVACommUsb):
    """
    USB-connected RAVA8 device implementation.

    Provides an interface that combines USB communication, device control, random number
    generation, health-monitoring, EEPROM, and peripherals functionality.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVA8_USB'


class RAVA8_TCP(RAVADevice, RAVARng, RAVAHealth, RAVALog, RAVACommTcp):
    """
    TCP-connected RAVA8 device implementation.

    Provides an interface that combines TCP communication, device control, random number
    generation, health-monitoring, EEPROM, and peripherals functionality.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVA8_TCP'