"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Commands for reading and updating configuration values stored in EEPROM.
"""

import struct

from ..rava_comm import R_MessageComm, R_MessageError
from ..rava_errors import RAVAMCUError, RAVAParameterError
from ..rava_device import R_DeviceMCUs
from ..rava_pwm_boost import R_PwmBoostFreq, DEFAULT_PWM_BOOST_FREQ, DEFAULT_PWM_BOOST_DUTY
from ..rava_rng import DEFAULT_RNG_SAMPLING_INTERVAL_US

############################
# RAVA8 EEPROM
############################


class RAVA8Eeprom:
    """
    EEPROM commands.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVA8Eeprom'


    def open(self, *args, **kwargs):
        """
        Verify device compatibility.
        """

        super().open(*args, **kwargs)

        # Check MCU model
        if self.mcu != R_DeviceMCUs.ATMEGA32U4:
            mcu_str = R_DeviceMCUs(self.firmw_modules.mcu).name

            raise RAVAMCUError(
                f'{self.name} init -> Unsupported MCU {mcu_str} for RAVA8 modules'
                )


    def eeprom_reset_to_default(self):
        """
        Request to restore all EEPROM configuration values to their factory defaults.
        """
        command_id = R_MessageComm.EEPROM_RESET_TO_DEFAULT

        # IO Structure
        data_out_format = ''
        data_in_format = '<?'

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        success, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        return success


    def eeprom_get_rng_config(self):
        """
        Retrieve the RNG configuration stored in EEPROM.
        """
        command_id = R_MessageComm.EEPROM_RNG_GET_CONFIG

        # IO Structure
        data_out_format = ''
        data_in_format = '<BBB'  # pwm_boost_freq_id, pwm_boost_duty, rng_sampling_interval

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        pwm_boost_freq_id, pwm_boost_duty, rng_sampling_interval = \
            struct.unpack(data_in_format, rmsg.data)

        # Process Input
        pwm_boost_freq = R_PwmBoostFreq(pwm_boost_freq_id)

        # Return Data
        return pwm_boost_freq, pwm_boost_duty, rng_sampling_interval


    def eeprom_set_rng_config(self, pwm_boost_freq = DEFAULT_PWM_BOOST_FREQ,
                       pwm_boost_duty = DEFAULT_PWM_BOOST_DUTY,
                       rng_sampling_interval = DEFAULT_RNG_SAMPLING_INTERVAL_US):
        """
        Update the RNG configuration stored in EEPROM using the provided parameters.
        """
        command_id = R_MessageComm.EEPROM_RNG_SET_CONFIG

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