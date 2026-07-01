"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Verify that crc16_ccitt_update() produces the expected CRC checksum for a known input sequence and
initial CRC value.
"""

from rng_rava import crc16_ccitt_update


def test_crc16_ccitt():
    # Input / Output
    INPUT_VECTOR = b'123456789'
    CRC_OUTCOME = 0x6f91

    # Compute CRC
    b = 0xFFFF
    for c in INPUT_VECTOR:
        b = crc16_ccitt_update(b, c)

    assert b == CRC_OUTCOME