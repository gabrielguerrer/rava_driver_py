"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
This example demonstrates interactive use of the RAVA device over a TCP connection. It is intended
for experimenting with and testing the device functionality.

Before running this example, start the RAVA TCP server. From a Python environment with the `rava`
package installed, run:
```
python3 -m rng_rava.tcp_srv --host 127.0.0.1 --port 4884
```
For details see `tcp/__main__.py` and `tcp/rava_tcp_server.py`.

If using Visual Studio Code, press `F6` to start an IPython console. You can then execute the
script interactively by placing the cursor on a line (or selecting multiple lines) and pressing
`Shift+Enter`.
"""

import rng_rava as rava
from rng_rava import R_RngCores, R_RngPP, R_PwmBoostFreq

# Connect to the RAVA TCP server
RAVA_TCP_HOST = '127.0.0.1'
RAVA_TCP_PORT = 4884

rng = rava.RAVA8_TCP()
rng.open(RAVA_TCP_HOST, RAVA_TCP_PORT)

# Set lof level
rng.log_level('INFO')   # Simpler
# rng.log_level('DEBUG')  # More detailed

# Number of samples
N = 100


def DEVICE():
    rng.dev_ping()
    rng.dev_get_info()
    rng.dev_get_usage()
    rng.dev_get_free_ram()
    rng.dev_get_temperature()
    rng.dev_get_vcc()

    rng.dev_monitor(n_pulse_counts=100, n_bytes=100)


def HEALTH():
    rng.health_startup_run()
    rng.health_startup_get_results()

    rng.health_continuous_get_errors()


def RNG():
    # Config
    rng.get_config()
    rng.set_config(pwm_boost_freq=R_PwmBoostFreq.F50_KHZ, pwm_boost_duty=20, rng_sampling_interval=10)
    rng.set_config(pwm_boost_freq=R_PwmBoostFreq.F50_KHZ, pwm_boost_duty=20, rng_sampling_interval=20)

    rng.set_timing_debug(True)
    rng.set_timing_debug(False)

    # Pulse counts
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.AB_DUAL)
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.AB_ALT)
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.A)
    rng.gen_pulse_counts(n_counts=N, rng_cores=R_RngCores.B)

    # Bit
    rng.gen_bit(rng_cores=R_RngCores.AB_DUAL)
    rng.gen_bit(rng_cores=R_RngCores.AB_ALT)
    rng.gen_bit(rng_cores=R_RngCores.AB_XOR)
    rng.gen_bit(rng_cores=R_RngCores.A)
    rng.gen_bit(rng_cores=R_RngCores.B)

    # Bytes
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_ALT, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_XOR, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.A, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.B, postproc=R_RngPP.NONE)

    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.NONE)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.XOR)
    rng.gen_bytes(n_bytes=N, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.XOR_DICHTL)

    # Byte stream
    rng.start_byte_stream(n_bytes=N, interval_ms=1000, rng_cores=R_RngCores.AB_DUAL, postproc=R_RngPP.NONE)
    rng.start_byte_stream(n_bytes=N, interval_ms=1000, rng_cores=R_RngCores.AB_ALT, postproc=R_RngPP.XOR)

    rng.get_byte_stream()
    rng.get_status_byte_stream()
    rng.stop_byte_stream()

    # Int8s
    rng.gen_int8s(n_ints=N, delta=100, postproc=R_RngPP.NONE)
    rng.gen_int8s(n_ints=N, delta=100, postproc=R_RngPP.XOR)
    rng.gen_int8s(n_ints=N, delta=100, postproc=R_RngPP.XOR_DICHTL)

    # Int16s
    rng.gen_int16s(n_ints=N, delta=1000, postproc=R_RngPP.NONE)
    rng.gen_int16s(n_ints=N, delta=1000, postproc=R_RngPP.XOR)
    rng.gen_int16s(n_ints=N, delta=1000, postproc=R_RngPP.XOR_DICHTL)

    # Floats
    rng.gen_floats(n_floats=N, postproc=R_RngPP.NONE)
    rng.gen_floats(n_floats=N, postproc=R_RngPP.XOR)
    rng.gen_floats(n_floats=N, postproc=R_RngPP.XOR_DICHTL)

    # Floats Downey
    rng.gen_floats_downey(n_floats=N, postproc=R_RngPP.NONE)
    rng.gen_floats_downey(n_floats=N, postproc=R_RngPP.XOR)
    rng.gen_floats_downey(n_floats=N, postproc=R_RngPP.XOR_DICHTL)