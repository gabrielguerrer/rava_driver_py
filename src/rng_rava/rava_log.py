"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Logging support for RAVA components.
"""

import logging

############################
# RAVA LOG
############################


LOG_FILL = 17 * ' ' # Indentation used for multi-line log messages.


class RAVALog:
    """
    Provides logging support for RAVA components.
    """

    def __init__(self):
        """
        Initialize the RAVA logger.
        """

        super().__init__()
        self.name = 'RAVALog'

        # Logger instance shared by all RAVA components
        self.log = logging.getLogger('rava')
        self.log_setup()


    def log_setup(self):
        """
        Configure the RAVA logger on first use.
        """

        if not self.log.hasHandlers():

            # Create handler
            lg_fmt = logging.Formatter(
                fmt='%(asctime)s %(levelname)-7s %(message)s', datefmt='%H:%M:%S'
                )
            lg_sh = logging.StreamHandler()
            lg_sh.setFormatter(lg_fmt)
            self.log.addHandler(lg_sh)

            # Set defaulf level to INFO
            self.log_level('INFO')


    def log_level(self, level_str):
        """
        Set the logger verbosity level.

        Valid levels are: 'DEBUG', 'INFO', 'WARNING', and 'ERROR'.
        """

        level = getattr(logging, level_str.upper(), None)

        if isinstance(level, int):
            self.log.setLevel(level)
            
        else:
            self.log.error(f'{self.name} log_level -> Unknown level {level_str}')


    def log_dev_info(self, mcu, model, firmw_ver, firmw_modules, rng_gen_max_nbytes_per_core, serial_number):
        """
        Log the connected device information.
        """

        modules_str = ' '.join(f'\n    {LOG_FILL}{x.strip()}'
                               for x in str(self.firmw_modules).split(','))

        dev_info_str =  f'{self.name} > Device info\n' \
                        f'{LOG_FILL}  Serial Number   = {self.serial_number}\n' \
                        f'{LOG_FILL}  Microcontroller = {self.mcu.name}\n' \
                        f'{LOG_FILL}  Model           = {self.model.name}\n' \
                        f'{LOG_FILL}  Firmware        = {self.firmw_ver}\n' \
                        f'{LOG_FILL}  RNG Max N/core  = {self.rng_gen_max_nbytes_per_core}\n' \
                        f'{LOG_FILL}  Modules    {modules_str}'

        self.log.info(dev_info_str)


    def log_health_startup_results(self, res_global, pc, pc_diff, bias, chisq):
        """
        Log the startup health test results.
        """

        hs_res = f'{self.name} > Health Startup Results\n' \
                 f'{LOG_FILL}  Global       = {res_global}\n' \
                 f'{LOG_FILL}  Pulse Counts = {pc}\n' \
                 f'{LOG_FILL}  PC Diff      = {pc_diff}\n' \
                 f'{LOG_FILL}  Bit Bias     = {bias}\n' \
                 f'{LOG_FILL}  Byte chisq   = {chisq}'

        self.log.info(hs_res)