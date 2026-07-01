"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example showcases the RNG usage for random number generation.
"""

import rng_rava as rava

N = 10
PP_NONE = rava.R_RngPP.NONE

# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Gerentare random int8s
print(f'\n> INT8s [0, 100)')
rnd = rng.gen_int8s(N, 100)
print(rnd)

# Gerentare random int16s
print(f'\n> INT16s [0, 1000)')
rnd = rng.gen_int16s(N, 1000)
print(rnd)

# Gerentare random floats
print(f'\n> FLOATs [0, 1.)')
rnd = rng.gen_floats(N)
print(rnd)

# Gerentare random floats using Downey method
print(f'\n> FLOATs DOWNEY [0, 1.)')
rnd = rng.gen_floats_downey(N)
print(rnd)

# Close device
rng.close()