"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
Run all RAVA module commands with different parameter configurations, checking for execution errors.
"""

import rng_rava as rava
from rng_rava import R_PwmBoostFreq, R_RngCores, R_RngPP


def test_device():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # Device methods
        rng.dev_ping()
        rng.dev_get_info()
        rng.dev_get_usage()
        rng.dev_get_free_ram()
        rng.dev_get_temperature()
        rng.dev_get_vcc()
        rng.dev_monitor(n_pulse_counts=100, n_bytes=100)

    finally:
        # Close RAVA device
        rng.close()


def test_health():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # Health methods
        if rng.firmw_modules.health_startup_enabled:
            rng.health_startup_get_results()
            rng.health_startup_run()

        if rng.firmw_modules.health_continuous_enabled:
            rng.health_continuous_get_errors()

    finally:
        # Close RAVA device
        rng.close()


def test_rng_cfg():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        ## Config
        rava_cfg0 = rng.get_config()
        for pf in R_PwmBoostFreq:
            rng.set_config(pwm_boost_freq=pf, pwm_boost_duty=10, rng_sampling_interval=10)
        rng.set_config(*rava_cfg0)

        ## Timing Debug
        if rng.firmw_modules.rng_timing_debug_enabled:
            rng.set_timing_debug(on = True)
            rng.set_timing_debug(on = False)

    finally:
        # Close RAVA device
        rng.close()


def test_rng_gen_pc_bits():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # RNG methods
        N = 10

        ## Pulse Counts
        for rc in [R_RngCores.AB_DUAL, R_RngCores.AB_ALT, R_RngCores.A, R_RngCores.B]:
            rng.gen_pulse_counts(n_counts=N, rng_cores=rc)

        ## Bits
        for rc in R_RngCores:
            rng.gen_bit(rng_cores=rc)

    finally:
        # Close RAVA device
        rng.close()


def test_rng_gen_bytes():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # RNG methods
        N = 10

        ## Bytes
        for rc in R_RngCores:
            for pp in R_RngPP:
                rng.gen_bytes(n_bytes=N, rng_cores=rc, postproc=pp)

    finally:
        # Close RAVA device
        rng.close()


def test_rng_gen_byte_stream():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # RNG methods
        N = 10

        ## Byte Stream
        for rc in R_RngCores:
            for pp in R_RngPP:
                rng.start_byte_stream(n_bytes=N, interval_ms=10, rng_cores=rc, postproc=pp)
                rng.get_status_byte_stream()
                for i in range(10):
                    rng.get_byte_stream()
                rng.stop_byte_stream()

    finally:
        # Close RAVA device
        rng.close()


def test_rng_gen_ints():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # RNG methods
        N = 10

        ## Int8s
        for pp in R_RngPP:
            rng.gen_int8s(n_ints=N, delta=100, postproc=pp)

        ## Int16s
        for pp in R_RngPP:
            rng.gen_int16s(n_ints=N, delta=10000, postproc=pp)

    finally:
        # Close RAVA device
        rng.close()


def test_rng_gen_floats():
    try:
        # RAVA device available?
        sns = rava.find_rava_sns()
        assert len(sns) > 0

        # Open RAVA device
        rng = rava.RAVA_USB()
        rng.open(sns[0])

        # RNG methods
        N = 10

        ## Floats
        for pp in R_RngPP:
            rng.gen_floats(n_floats=N, postproc=pp)

        ## Floats Downey
        for pp in R_RngPP:
            rng.gen_floats_downey(n_floats=N, postproc=pp)

    finally:
        # Close RAVA device
        rng.close()