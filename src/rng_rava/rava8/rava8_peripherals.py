"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Peripherals functionality.
"""

import enum
import struct

from ..rava_comm import R_MessageComm, R_MessageError
from ..rava_device import R_DeviceMCUs
from ..rava_errors import RAVAMCUError, RAVAFirmwareModuleError, RAVAParameterError

############################
# RAVA8 PERIPHERALS
############################


PERIPHERALS_N = 5

TIMER3_MAXIMUM_DELAY_MS = 4194


class R_PeriphModes(enum.IntEnum):
    """
    Peripheral operating modes.
    """

    INPUT         = 0
    OUTPUT        = 1


class R_PeriphComms(enum.IntEnum):
    """
    Peripheral digital operations supported by the firmware.
    """

    MODE          = 0
    READ          = 1
    WRITE         = 2
    PULSE         = 3


class R_Timer3Prescalers(enum.IntEnum):
    """
    Timer3 clock prescaler settings.
    """

    CLK_OFF       = 0
    CLK_DIV_1     = 1
    CLK_DIV_8     = 2
    CLK_DIV_64    = 3
    CLK_DIV_256   = 4
    CLK_DIV_1024  = 5


class R_AdcPrescalers(enum.IntEnum):
    """
    ADC clock prescaler settings.
    """

    CLK_DIV_2     = 1
    CLK_DIV_4     = 2
    CLK_DIV_8     = 3
    CLK_DIV_16    = 4
    CLK_DIV_32    = 5
    CLK_DIV_64    = 6
    CLK_DIV_128   = 7


class RAVA8Peripherals:
    """
    Peripheral control interface for RAVA8 devices.

    Provides access to GPIO, timers, ADC, and other MCU peripheral functions exposed by the
    firmware.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVA8Peripherals'


    def open(self, *args, **kwargs):
        """
        Open the device connection and verify MCU compatibility with RAVA8.
        """

        super().open(*args, **kwargs)

        # Check MCU model
        if self.mcu != R_DeviceMCUs.ATMEGA32U4:
            mcu_str = R_DeviceMCUs(self.firmw_modules.mcu).name

            raise RAVAMCUError(
                f'{self.name} init -> Unsupported MCU {mcu_str} for RAVA8 modules'
                )


    def periph_digi(self, periph_id, digi_comm, digi_comm_par=0, pulse_duration_us=0):
        """
        Request for generic digital operations on port periph_id.

        Supported operations, defined by `R_PeriphComms`, include:
        - Configuring input/output mode
        - Reading the digital logic level
        - Writing HIGH/LOW logic levels
        - Generating digital pulses

        Parameters
        ----------
        periph_id : int
            Peripheral port identifier, ranging from 1 to 5.
        digi_comm : R_PeriphComms
            Digital operation to perform.
        digi_comm_par : R_PeriphModes if digi_comm == MODE; bool if digi_comm == WRITE
        pulse_duration_us : int
            Pulse duration in microseconds when digi_comm == PULSE.

        Returns
        ----------
        bool
            if digi_comm == READ
        True
            For all other operations
        """
        command_id = R_MessageComm.PERIPH_DIGI

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BBBH'
        data_in_format = 'B'   # digi_state

        # Validate Output
        if not(
            periph_id > 0 and
            periph_id <= PERIPHERALS_N and
            digi_comm < len(R_PeriphComms)
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        if (digi_comm == R_PeriphComms.PULSE and
            pulse_duration_us == 0
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(
            data_out_format, periph_id, digi_comm, digi_comm_par, pulse_duration_us)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        digi_state, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        if digi_comm == R_PeriphComms.READ:
            return digi_state
        else:
            return True


    def periph_d1_digi_fast(self, digi_comm, digi_comm_par=0, pulse_duration_us=0):
        """
        Request for fast digital operations on port D1.

        Parameters
        ----------
        digi_comm : R_PeriphComms
            Digital operation to perform.
        digi_comm_par : R_PeriphModes if digi_comm == MODE; bool if digi_comm == WRITE
        pulse_duration_us : int
            Pulse duration in microseconds when digi_comm == PULSE.

        Returns
        ----------
        bool
            if digi_comm == READ
        True
            For all other operations
        """
        command_id = R_MessageComm.PERIPH_D1_DIGI_FAST

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BBH'
        data_in_format = 'B'   # digi_state

        # Validate Output
        if not(digi_comm < len(R_PeriphComms)):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        if (digi_comm == R_PeriphComms.PULSE and
            pulse_duration_us == 0
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, digi_comm, digi_comm_par, pulse_duration_us)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        digi_state, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        if digi_comm == R_PeriphComms.READ:
            return digi_state
        else:
            return True


    def periph_d1_trigger_input(self, on):
        """
        Request to enable/disable the D1 external trigger input functionality.
        """
        command_id = R_MessageComm.PERIPH_D1_TRIGGER_INPUT

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware')

        # IO Structure
        data_out_format = '<B'
        data_in_format = ''

        # Validate Output
        # Serialize Output
        data_out = struct.pack(data_out_format, on)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d1_comparator(self, on, neg_to_d5=True):
        """
        Request to enable/disable the D1 comparator functionality.
        """
        command_id = R_MessageComm.PERIPH_D1_COMPARATOR

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BB'
        data_in_format = ''

        # Validate Output
        # Serialize Output
        data_out = struct.pack(data_out_format, on, neg_to_d5)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d1_delay_us_test(self, interval_us):
        """
        Request to test the device_delay_us(interval_us) delay function.
        """
        command_id = R_MessageComm.PERIPH_D1_DELAY_US_TEST

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<H'
        data_in_format = ''

        # Validate Output
        if not(interval_us > 0):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, interval_us)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg( command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d3_periodic_trigger_output(self, on, interval_ms=1):
        """
        Request to enable/disable the D3 pediodic trigger functionality.
        """
        command_id = R_MessageComm.PERIPH_D3_TIMER3_TRIGGER_OUTPUT

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BH'
        data_in_format = ''

        # Validate Output
        if not(
            interval_ms > 0 and
            interval_ms <= TIMER3_MAXIMUM_DELAY_MS
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, on, interval_ms)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d3_pwm(self, on, freq_prescaler=R_Timer3Prescalers.CLK_OFF, top=0, duty=0):
        """
        Request to enable/disable the D3 PWM functionality.
        """
        command_id = R_MessageComm.PERIPH_D3_TIMER3_PWM

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BBHH'
        data_in_format = ''

        # Validate Output
        if not(freq_prescaler < 8):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, on, freq_prescaler, top, duty)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d3_sound(self, on, volume=0, freq_hz=0):
        """
        Request to enable/disable the D3 sound functionality.
        """
        command_id = R_MessageComm.PERIPH_D3_TIMER3_SOUND

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BBH'
        data_in_format = ''

        # Validate Output
        # Serialize Output
        data_out = struct.pack(data_out_format, on, volume, freq_hz)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d4_pin_change(self, on):
        """
        Request to enable/disable the D4 pin change functionality.
        """
        command_id = R_MessageComm.PERIPH_D4_PIN_CHANGE

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<B'
        data_in_format = ''

        # Validate Output
        # Serialize Output
        data_out = struct.pack(data_out_format, on)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        # Process Input
        # Return Data
        return True


    def periph_d5_adc(self, on, ref_5v=True, clk_prescaler=R_AdcPrescalers.CLK_DIV_128, oversampling_n_bits=0):
        """
        Request to perform an ADC measurement on D5.
        """
        command_id = R_MessageComm.PERIPH_D5_ADC

        # Enabled?
        if not self.firmw_modules.peripherals_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Peripheral support is disabled in the device firmware'
                )

        # IO Structure
        data_out_format = '<BBBB'
        data_in_format = 'f'   # adc_reading

        # Validate Output
        if not(
            clk_prescaler > 0 and
            clk_prescaler <= len(R_AdcPrescalers) and
            oversampling_n_bits <= 6
            ):

            raise RAVAParameterError(
                f'{self.name} {command_id.name} -> {R_MessageError.INVALID_INPUT_VALUES.name}'
                )

        # Serialize Output
        data_out = struct.pack(data_out_format, on, ref_5v, clk_prescaler, oversampling_n_bits)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        adc_reading, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        return adc_reading