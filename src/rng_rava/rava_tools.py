"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Utility functions used throughout the RAVA driver.
"""

############################
# RAVA TOOLS
############################


def crc16_ccitt_update(crc, data):
    """
    Update a CRC-16/CCITT (PPP/IrDA flavor) checksum with a single byte.

    Uses polynomial 0x8408 and initial value 0xFFFF.
    """

    data &= 0xFF
    data ^= (crc & 0xFF)          # lo8(crc)
    data ^= (data << 4) & 0xFF    # keep it 8-bit

    crc = (
        (((data << 8) & 0xFFFF) | ((crc >> 8) & 0xFF)) ^
        ((data >> 4) & 0xFF) ^ ((data << 3) & 0xFFFF)
    ) & 0xFFFF

    return crc