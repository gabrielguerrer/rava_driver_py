"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Benchmarks throughput for integer and floating-point random numbers across different generation
parameters.
"""

import time
import rng_rava as rava

N = 25000
INT8_DELTAS = [1, 10, 50, 100, 200, 2**8-1]
INT16_DELTAS = [1, 10, 50, 100, 200, 1000, 5000, 10000, 30000, 40000, 60000, 2**16-1]
PP_NONE = rava.R_RngPP.NONE


def throughput_int8(delta):
    n_max = 2 * rng.rng_gen_max_nbytes_per_core

    # Start timer
    t0 = time.perf_counter()

    # Generate int8s
    for i in range(N // n_max):
        rng.gen_int8s(n_max, delta, PP_NONE)
    rng.gen_int8s(N % n_max, delta, PP_NONE)

    # Stop timer, compute time interval
    delta_s = time.perf_counter() - t0

    # Compute frequency
    freq_k = (N / delta_s) / 1000

    # Print
    print(f'  delta = {delta:3d},  freq Kint/s = {freq_k:.3f}')


def throughput_int16(delta):
    n_max = rng.rng_gen_max_nbytes_per_core

    # Start timer
    t0 = time.perf_counter()

    # Generate int16s
    for i in range(N // n_max):
        rng.gen_int16s(n_max, delta, PP_NONE)
    rng.gen_int16s(N % n_max, delta, PP_NONE)

    # Stop timer, compute time interval
    delta_s = time.perf_counter() - t0

    # Compute frequency
    freq_k = (N / delta_s) / 1000

    # Print
    print(f'  delta = {delta:5d},  freq Kint/s = {freq_k:.3f}')


def throughput_float():
    n_max = rng.rng_gen_max_nbytes_per_core // 2

    # Start timer
    t0 = time.perf_counter()

    # Generate floats
    for i in range(N // n_max):
        rng.gen_floats(n_max, PP_NONE)
    rng.gen_floats(N % n_max, PP_NONE)

    # Stop timer, compute time interval
    delta_s = time.perf_counter() - t0

    # Compute frequency
    freq_k = (N / delta_s) / 1000

    # Print
    print(f'  freq Kfloats/s = {freq_k:.3f}')


def throughput_float_downey():
    n_max = rng.rng_gen_max_nbytes_per_core // 2

    # Start timer
    t0 = time.perf_counter()

    # Generate floats
    for i in range(N // n_max):
        rng.gen_floats_downey(n_max, PP_NONE)
    rng.gen_floats_downey(N % n_max, PP_NONE)

    # Stop timer, compute time interval
    delta_s = time.perf_counter() - t0

    # Compute frequency
    freq_k = (N / delta_s) / 1000

    # Print
    print(f'  freq Kfloats/s = {freq_k:.3f}')


# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Throughputs
## Int8
print('\n> INT8')
for delta in INT8_DELTAS:
    throughput_int8(delta)

## Int16
print('\n> INT16')
for delta in INT16_DELTAS:
    throughput_int16(delta)

## Float
print('\n> FLOAT')
throughput_float()

## Float Downey
print('\n> FLOAT DOWNEY')
throughput_float_downey()

# Close device
rng.close()