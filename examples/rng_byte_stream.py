<<<<<<< HEAD
'''
This example showcases RNG byte stream.

This example code is in the public domain.
Author: Gabriel Guerrer
'''

import rng_rava as rava

# Variables
STREAM_INTERVAL_MS = 500
STREAM_N_BYTES = 5

# Find RAVA device and connect
rng = rava.RAVA_RNG()
dev_sns = rava.find_rava_sns()
if len(dev_sns):
    rng.connect(serial_number=dev_sns[0])
else:
    print('No device found')
    exit()

# Generate 3 bytes every 0.5s
rng.snd_rng_byte_stream_start(n_bytes=STREAM_N_BYTES, stream_interval_ms=STREAM_INTERVAL_MS)

# Print 10 first values
print()
for i in range(10):
    rnd_a, rnd_b = rng.get_rng_byte_stream_data(output_type='list')
    print('RNG A, B = {}, {}'.format(rnd_a, rnd_b))

# Stop stream
rng.snd_rng_byte_stream_stop()
=======
"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates how to generate random bytes at fixed intervals using the
microcontroller's hardware timers.
"""

import rng_rava as rava

N_BYTES = 10
INTERVAL_MS = 250
CORES_DUAL = rava.R_RngCores.AB_DUAL
PP_NONE = rava.R_RngPP.NONE

# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Generate 2xN_BYTES bytes every 250 ms
rng.start_byte_stream(N_BYTES, INTERVAL_MS, CORES_DUAL, PP_NONE)

# Print 30 first values
for _ in range(30):
    rnd_a, rnd_b = rng.get_byte_stream()
    print(f'\nA = {rnd_a.tolist()}\nB = {rnd_b.tolist()}')

# Stop stream
rng.stop_byte_stream()
>>>>>>> 4fcf521 (Update v3.0.0)

# Close device
rng.close()