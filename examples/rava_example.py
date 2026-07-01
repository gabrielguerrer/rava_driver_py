"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Basic usage example for the RAVA_USB driver.
"""

import rng_rava as rava

# Find the serial number of the attached RAVA devices
rava_sns = rava.find_rava_sns()

# Create a RNG_USB instance and connect to the first device
rng = rava.RAVA_USB()
rng.open(rava_sns[0])

"""
On RAVA8 devices, the RNG configuration is stored in the EEPROM and is automatically loaded during 
device startup. See `examples/rava8/rava8_eeprom.py` for details.

To change the configuration used by the running device without modifying the EEPROM, call 
`set_rng_config()`. The example below applies the default configuration values at runtime.

The default PWM boost settings (a frequency of 50 kHz and a duty-cycle value of 20) were determined 
experimentally by maximizing the avalanche pulse count while minimizing current consumption. 

The recommended sampling interval is 10 µs. Values between 5 µs and 10 µs can increase the random 
number generation throughput at the cost of increased output bias. Sampling intervals below 5 µs 
may compromise the entropy of the generated data and are therefore not recommended.
"""

# Configure RNG
rng.set_config(
  pwm_boost_freq = rava.R_PwmBoostFreq.F50_KHZ, 
  pwm_boost_duty = 20, 
  rng_sampling_interval = 10)

"""
The following examples demonstrate the generation of different types of random data.
"""

# Measure 100 pulse counts
pc_a, pc_b = rng.gen_pulse_counts(n_counts=100)

# Generate a random bit XORing both cores
bit = rng.gen_bit(rng_cores=rava.R_RngCores.AB_XOR)

# Generate 100 random bytes from each entropy core
bytes_a, bytes_b = rng.gen_bytes(n_bytes=100)

# Generate 100 8-bit integers between 0 and 99
ints8 = rng.gen_int8s(n_ints=100, delta=100)

# Generate 100 16-bit integers between 0 and 999
ints16 = rng.gen_int16s(n_ints=100, delta=1000)

# Generate 100 32-bit floats ranging between 0 and 1
floats = rng.gen_floats(n_floats=100)

# Close RAVA device
rng.close()