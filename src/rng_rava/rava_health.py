"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Health monitoring functionality.
"""

import struct

from .rava_comm import R_MessageComm
from .rava_errors import RAVAFirmwareModuleError

############################
# RAVA HEALTH
############################


class RAVAHealthStartupRes:
    """
    Result of a startup health test.

    Contains the test success, the measured statistic in both RNG cores, and the acceptance
    threshold.
    """

    def __init__(self, data_bytes):
        self.data_in_format = '<?fff'
        self.result, self.a, self.b, self.tresh = struct.unpack(self.data_in_format, data_bytes)

    def __repr__(self):
        return f'{self.result}, a = {self.a:.2f}, b = {self.b:.2f}, tresh = {self.tresh:.2f}'


class RAVAHealthContinuousRes:
    """
    Error counters for a continuous health test.
    """
    def __init__(self, name, data_bytes):

        self.name = name
        self.data_in_format = '<HH'
        self.count_a, self.count_b = struct.unpack(self.data_in_format, data_bytes)

    def __repr__(self):
        return f'{self.name}: count a = {self.count_a}, count b = {self.count_b}\n'


class RAVAHealth:
    """
    Device health commands.
    """

    def __init__(self):
        super().__init__()
        self.name = 'RAVAHealth'


    def health_startup_run(self):
        """
        Execute the startup health tests and retrieve the results.
        """
        command_id = R_MessageComm.HEALTH_STARTUP_RUN

        # Enabled?
        if not self.firmw_modules.health_startup_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Health Startup Tests are disabled in the device firmware'
                )

        # IO Structure
        data_out_format = ''
        data_in_format = '<?13s13s13s13s' # res_global, data_pc, data_pc_diff, data_bias, data_chisq

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        res_global, data_pc, data_pc_diff, data_bias, data_chisq = \
            struct.unpack(data_in_format, rmsg.data)

        # Process Input
        pc = RAVAHealthStartupRes(data_pc)
        pc_diff = RAVAHealthStartupRes(data_pc_diff)
        bias = RAVAHealthStartupRes(data_bias)
        chisq = RAVAHealthStartupRes(data_chisq)

        # Return Data
        return res_global, pc, pc_diff, bias, chisq


    def health_startup_get_results(self):
        """
        Retrieve the most recent startup health-test results.
        """
        command_id = R_MessageComm.HEALTH_STARTUP_GET_RESULTS

        # Enabled?
        if not self.firmw_modules.health_startup_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Health Startup Tests are disabled in the device firmware'
                )

        # IO Structure
        data_out_format = ''
        data_in_format = '<?13s13s13s13s' # res_global, data_pc, data_pc_diff, data_bias, data_chisq

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        res_global, data_pc, data_pc_diff, data_bias, data_chisq = \
            struct.unpack(data_in_format, rmsg.data)

        # Process Input
        pc = RAVAHealthStartupRes(data_pc)
        pc_diff = RAVAHealthStartupRes(data_pc_diff)
        bias = RAVAHealthStartupRes(data_bias)
        chisq = RAVAHealthStartupRes(data_chisq)

        # Return Data
        return res_global, pc, pc_diff, bias, chisq


    def health_continuous_get_errors(self):
        """
        Retrieve continuous health-test error information.
        """
        command_id = R_MessageComm.HEALTH_CONTINUOUS_GET_ERRORS

        # Enabled?
        if not self.firmw_modules.health_continuous_enabled:

            raise RAVAFirmwareModuleError(
                f'{self.name} {command_id.name} -> Health Continuous Tests are disabled in the device firmware'
                )

        # IO Structure
        data_out_format = ''
        data_in_format = '<?4s4s'    # has_error, data_nrc_error, data_nap_error

        # Send and Retrieve Request
        rmsg = self.send_retrieve_rava_msg(command_id, None)

        # Deserialize Input
        has_error, data_nrc_error, data_nap_error = struct.unpack(data_in_format, rmsg.data)

        # Process Input
        nrc_error = RAVAHealthContinuousRes('nrc', data_nrc_error)
        nap_error = RAVAHealthContinuousRes('nap', data_nap_error)

        # Return Data
        return has_error, nrc_error, nap_error