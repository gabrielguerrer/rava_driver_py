"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates how to update the EEPROM values that define the RNG configuration.
"""

import rng_rava as rava

PWM_BOOST_FREQ = rava.R_PwmBoostFreq.F50_KHZ
PWM_BOOST_DUTY = 20
RNG_SAMPLING_INTERVAL = 10

# Open RAVA8 device
rng = rava.RAVA8_USB()
rng.open(rava.find_rava_sns()[0])

# Show current configuration
rng_cfg = rng.eeprom_get_rng_config()
cfg_labels = ['PWM_BOOST_FREQ = ', 'PWM_BOOST_DUTY = ', 'RNG_SAMPLING_INTERVAL = ']
cfg_str = '\n'.join(f'{label}{value}' for label, value in zip(cfg_labels, rng_cfg))
print(cfg_str)

# Reconfigure EEPROM
rng.eeprom_set_rng_config(
  pwm_boost_freq = PWM_BOOST_FREQ,
  pwm_boost_duty = PWM_BOOST_DUTY,
  rng_sampling_interval = RNG_SAMPLING_INTERVAL
)

# Close device
rng.close()