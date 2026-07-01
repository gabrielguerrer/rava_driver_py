"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Measures the throughput of random byte generation for different values of sampling interval.

The recommended sampling interval is 10 µs. Values between 5 µs and 10 µs can increase the random 
number generation throughput at the cost of increased output bias. Sampling intervals below 5 µs 
may compromise the entropy of the generated data and are therefore not recommended.
"""

import time
import rng_rava as rava

N_BYTES = 35000
CORES = rava.R_RngCores.AB_DUAL
PP = rava.R_RngPP.NONE


def rng_bytes_throughput(sampling_interval):
    n_max = rng.rng_gen_max_nbytes_per_core

    # Set sampling interval
    pwmb_freq, pwmb_duty, _ = rng_cfg0    
    rng.set_config(pwmb_freq, pwmb_duty, sampling_interval)

    # Start timer
    t0 = time.perf_counter()

    # Generate random bytes
    for i in range(N_BYTES // n_max):
        rng.gen_bytes(n_max, CORES, PP)
    rng.gen_bytes(N_BYTES % n_max, CORES, PP)

    # Stop timer, compute time interval
    delta_s = time.perf_counter() - t0

    # Compute frequency / interval
    freq_kbit = (2 * N_BYTES / delta_s) * 8 / 1000
    interv_us = (delta_s/ N_BYTES) * 1e6

    # Print
    print(f'\n> SI = {sampling_interval}')
    print(f'Throughput: Generation of {2 * N_BYTES} bytes took {delta_s:.2f}s')
    print(f'  Freq Kbit/s = {freq_kbit:.3f}')
    print(f'  Freq KByte/s = {freq_kbit/8:.3f}')
    print(f'  Byte interval (us) = {interv_us:.3f}')  # In each core


# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Save initial RNG cfg
rng_cfg0 = rng.get_config()

# Vary sampling intervals
sampling_intervals = range(1, 20+1)

for si in sampling_intervals:
    rng_bytes_throughput(si)

# Restore initial sampling interval
rng.set_config(*rng_cfg0)

# Close device
rng.close()