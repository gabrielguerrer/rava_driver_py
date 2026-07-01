"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Device management functionality.
"""

from array import array
import enum
import struct

from .rava_comm import R_MessageComm
from .rava_health import RAVAHealthContinuousRes

############################
# RAVA DEVICE
############################


class R_DeviceMCUs(enum.IntEnum):
    """
    Supported microcontroller models.
    """

    ATMEGA32U4  = 1


class R_DeviceModels(enum.IntEnum):
    """
    Supported RAVA device models.
    """

    RNG         = 1
    SYNC        = 2


class RAVAFirmwareModules:
    """
    Decoded firmware feature flags.
    """

    def __init__(self, modules_byte):
        self.health_startup_enabled     = bool(modules_byte & (1 << 0))
        self.health_continuous_enabled  = bool(modules_byte & (1 << 1))
        self.comm_usart_enabled         = bool(modules_byte & (1 << 2))
        self.peripherals_enabled        = bool(modules_byte & (1 << 3))
        self.rng_timing_debug_enabled   = bool(modules_byte & (1 << 4))

    def __repr__(self):
        return (
            f'health_startup_enabled    = {self.health_startup_enabled},'
            f'\nhealth_continuous_enabled = {self.health_continuous_enabled},'
            f'\ncomm_usart_enabled        = {self.comm_usart_enabled},'
            f'\nperipherals_enabled       = {self.peripherals_enabled},'
            f'\nrng_timing_debug_enabled  = {self.rng_timing_debug_enabled}'
        )


class RAVADevice:
    """
    Device management and status commands.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVADevice'


    def dev_ping(self):
        """
        Send ping request. Command used to verify that the device is responsive and communication
        is operational.
        """
        command_id = R_MessageComm.DEVICE_PING

        # IO Structure
        data_out_format = ''
        data_in_format = ''

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        return True


    def dev_get_info(self):
        """
        Retrieve device identification, firmware version, and enabled module data.
        """
        command_id = R_MessageComm.DEVICE_GET_INFO

        # IO Structure
        data_out_format = ''
        data_in_format = '<BBBBBBH10s'  # mcu_id, model_id, firmw_ver_major, firmw_ver_minor,
                                        # firmw_ver_patch, firmw_modules_byte,
                                        # rng_gen_max_nbytes_per_core, serial_number

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        mcu_id, model_id, firmw_ver_major, firmw_ver_minor, firmw_ver_patch, firmw_modules_byte, \
            rng_gen_max_nbytes_per_core, serial_number = \
                struct.unpack(data_in_format, rmsg.data)

        # Process Input
        mcu = R_DeviceMCUs(mcu_id)
        model = R_DeviceModels(model_id)
        firmw_ver = (firmw_ver_major, firmw_ver_minor, firmw_ver_patch)
        firmw_modules = RAVAFirmwareModules(firmw_modules_byte)

        # Return Data
        return mcu, model, firmw_ver, firmw_modules, rng_gen_max_nbytes_per_core, serial_number


    def dev_get_usage(self):
        """
        Retrieve the number of processed device requests and the total number of generated random
        bytes accumulated since the previous call. After transmitting the response, both usage
        counters are reset to zero in the RAVA device.
        """
        command_id = R_MessageComm.DEVICE_GET_USAGE

        # IO Structure
        data_out_format = ''
        data_in_format = '<HI'  # request_count, gen_bytes_count

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        request_count, gen_bytes_count = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        return request_count, gen_bytes_count


    def dev_get_free_ram(self):
        """
        Retrieve the amount of currently available RAM.
        """
        command_id = R_MessageComm.DEVICE_GET_FREE_RAM

        # IO Structure
        data_out_format = ''
        data_in_format = '<H'  # free_ram,

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        free_ram, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        return free_ram


    def dev_get_temperature(self):
        """
        Retrieve the device temperature measurement.
        """
        command_id = R_MessageComm.DEVICE_GET_TEMPERATURE

        # IO Structure
        data_out_format = ''
        data_in_format = '<H'  # temperature,

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        temperature, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        # Return Data
        return temperature


    def dev_get_vcc(self):
        """
        Retrieve the device supply voltage.
        """
        command_id = R_MessageComm.DEVICE_GET_VCC

        # IO Structure
        data_out_format = ''
        data_in_format = '<H'  # vcc,

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        vcc, = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        vcc_v = vcc / 1000.

        # Return Data
        return vcc_v


    def dev_monitor(self, n_pulse_counts, n_bytes):
        """
        Retrieve the device monitoring information, including device usage statistics, continuous
        health-test error counts, and the requested pulse counts and random bytes.
        """
        command_id = R_MessageComm.DEVICE_MONITOR

        # IO Structure
        data_out_format = '<BB'
        data_in_format = '<HI?4s4sBB'  # request_count, gen_bytes_count, has_error, data_nrc_error, data_nap_error, n_pulse_counts, n_bytes

        # Validate Output

        # Serialize Output
        data_out = struct.pack(data_out_format, n_pulse_counts, n_bytes)

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, data_out)

        # Deserialize Input
        request_count, gen_bytes_count, has_error, data_nrc_error, data_nap_error, _, _ = \
            struct.unpack(data_in_format, rmsg.data)

        # Process Input
        nrc_error = RAVAHealthContinuousRes('nrc', data_nrc_error)
        nap_error = RAVAHealthContinuousRes('nap', data_nap_error)

        pc_a = array('B', rmsg.rand[0:2*n_pulse_counts:2])
        pc_b = array('B', rmsg.rand[1:2*n_pulse_counts:2])
        bytes_a =  array('B', rmsg.rand[2*n_pulse_counts:2*n_pulse_counts + 2*n_bytes:2])
        bytes_b =  array('B', rmsg.rand[2*n_pulse_counts+1:2*n_pulse_counts + 2*n_bytes:2])

        # Return Data
        return (request_count, gen_bytes_count), (has_error, nrc_error, nap_error), \
            (pc_a, pc_b), (bytes_a, bytes_b)