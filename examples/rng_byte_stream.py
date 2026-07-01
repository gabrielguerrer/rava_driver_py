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

# Close device
rng.close()