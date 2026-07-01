"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates how the RNG pulse count distribution changes with different values of the
sampling interval configuration.

The recommended sampling interval is 10 µs. Values between 5 µs and 10 µs can increase the random
number generation throughput at the cost of increased output bias. Sampling intervals below 5 µs
may compromise the entropy of the generated data and are therefore not recommended.
"""

import rng_rava as rava

N_COUNTS_PER_CORE = 25000
PWM_BOOST_FREQ = rava.R_PwmBoostFreq.F50_KHZ
PWM_BOOST_DUTY = 20

# Open RAVA device
rng = rava.RAVA_USB()
rng.open(rava.find_rava_sns()[0])

# Save initial RNG cfg
rng_cfg0 = rng.get_config()

# Vary sampling intervals
sampling_intervals = range(1, 20+1)

for si in sampling_intervals:
    rng.set_config(
        pwm_boost_freq=PWM_BOOST_FREQ, pwm_boost_duty=PWM_BOOST_DUTY, rng_sampling_interval=si)

    # Measure pulse counts
    n_max = rng.rng_gen_max_nbytes_per_core
    pcs_a = 0
    pcs_b = 0
    for _ in range(N_COUNTS_PER_CORE // n_max):
        _pcs_a, _pcs_b = rng.gen_pulse_counts(n_max, rava.R_RngCores.AB_DUAL)
        pcs_a += sum(_pcs_a)
        pcs_b += sum(_pcs_b)

    _pcs_a, _pcs_b = rng.gen_pulse_counts(N_COUNTS_PER_CORE % n_max, rava.R_RngCores.AB_DUAL)
    pcs_a += sum(_pcs_a)
    pcs_b += sum(_pcs_b)

    # Calculate mean values
    pcs_mean_a = pcs_a / N_COUNTS_PER_CORE
    pcs_mean_b = pcs_b / N_COUNTS_PER_CORE

    # Inform mean values
    print(f'SI = {si:2d} us;  pc_a = {pcs_mean_a:5.2f},  pc_b = {pcs_mean_b:5.2f}')

# Restore initial sampling interval
rng.set_config(*rng_cfg0)

# Close device
rng.close()