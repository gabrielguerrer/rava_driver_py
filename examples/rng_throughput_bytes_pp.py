"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Measures the throughput of random byte generation for all post-processing options.
"""

import time
import rng_rava as rava

N_BYTES = 35000
CORES = rava.R_RngCores.AB_DUAL


def rng_bytes_throughput(postproc_id):
    n_max = rng.rng_gen_max_nbytes_per_core

    # Start timer
    t0 = time.perf_counter()

    # Generate random bytes
    for i in range(N_BYTES // n_max):
        rng.gen_bytes(n_max, CORES, postproc_id)
    rng.gen_bytes(N_BYTES % n_max, CORES, postproc_id)

    # Stop timer, compute time interval
    delta_s = time.perf_counter() - t0

    # Compute frequency / interval
    freq_kbit = (2 * N_BYTES / delta_s) * 8 / 1000
    interv_us = (delta_s/ N_BYTES) * 1e6

    # Print
    print(f'\n> PP = {rava.R_RngPP(pp).name}')
    print(f'Throughput: Generation of {2 * N_BYTES} bytes took {delta_s:.2f}s')
    print(f'  Freq Kbit/s = {freq_kbit:.3f}')
    print(f'  Freq KByte/s = {freq_kbit/8:.3f}')
    print(f'  Byte interval (us) = {interv_us:.3f}')  # In each core


# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Obtain the throughput for all post-processing options
for pp in rava.R_RngPP:
    rng_bytes_throughput(pp)

# Close device
rng.close()