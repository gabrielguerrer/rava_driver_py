"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
PWM boost configuration constants.
"""

import enum

############################
# RAVA PWM BOOST
############################


class R_PwmBoostFreq(enum.IntEnum):
    """
    PWM switching frequencies for the boost converter.
    """

    F30_KHZ = 0
    F40_KHZ = 1
    F50_KHZ = 2
    F60_KHZ = 3
    F75_KHZ = 4


DEFAULT_PWM_BOOST_FREQ = R_PwmBoostFreq.F50_KHZ
DEFAULT_PWM_BOOST_DUTY = 20