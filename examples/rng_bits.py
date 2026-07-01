"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example showcases the RNG usage for random bit generation for all core options.
"""

import rng_rava as rava

# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Generate random bits
for cores in rava.R_RngCores:
    print(f'\n> CORES {cores.name}')
    rnd = rng.gen_bit(cores)
    print(rnd)

# Close device
rng.close()