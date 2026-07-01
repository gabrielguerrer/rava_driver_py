"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example showcases the RNG usage for random byte generation for all core options.
"""

import rng_rava as rava

N_BYTES = 10
PP_NONE = rava.R_RngPP.NONE

# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Generate random bytes
for cores in rava.R_RngCores:
    print(f'\n> CORES {cores.name}')
    rnd = rng.gen_bytes(N_BYTES, cores, PP_NONE)
    print(rnd)

# Close device
rng.close()