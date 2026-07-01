"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates how to restore the EEPROM contents to their factory default values.
"""

import rng_rava as rava

# Open RAVA8 device
rng = rava.RAVA8_USB()
rng.open(rava.find_rava_sns()[0])

# Reset EEPROM
rng.eeprom_reset_to_default()

# Close device
rng.close()