# RAVA Python Driver

[![Website](https://img.shields.io/badge/Website-rava--rng.org-blue)](https://rava-rng.org)
[![Docs](https://img.shields.io/badge/Docs-docs.rava--rng.org-blue)](https://docs.rava-rng.org)
[![Author](https://img.shields.io/badge/Author-gabrielguerrer.com-blue)](https://gabrielguerrer.com)
[![Publication](https://img.shields.io/badge/Publication-IEEE_Express-purple)](https://ieeexplore.ieee.org/document/10295491)

[![OS](https://img.shields.io/badge/OS-Windows%20%7C%20Linux%20%7C%20macOS-blue)]()
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)]()
[![PyPI](https://img.shields.io/pypi/v/rng_rava)](https://pypi.org/project/rng_rava/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

The **RAVA Python Driver** provides a Python interface for communicating with
[RAVA8](https://github.com/gabrielguerrer/rava8_rng) True Random Number Generator (TRNG)
devices running the [RAVA8 Firmware](https://github.com/gabrielguerrer/rava8_rng_firmware).


## Features

- USB communication with RAVA8 devices
- Random bit, byte, integer and floating-point generation
- TCP relay server supporting simultaneous access by multiple TCP clients


## Requirements

- Python 3.11 or later
- [pyserial](https://github.com/pyserial/pyserial)


## Installation

The driver is available on PyPI as [rng_rava](https://pypi.org/project/rng_rava/).
After creating and activating a Python virtual environment, install it with:
```
pip install rng_rava
```


## Usage

```
import rng_rava as rava

# Find the serial number of the attached RAVA devices
rava_sns = rava.find_rava_sns()

# Create a RNG_USB instance and connect to the first device
rng = rava.RAVA_USB()
rng.open(rava_sns[0])

# Measure 100 pulse counts
pc_a, pc_b = rng.gen_pulse_counts(n_counts=100)

# Generate a random bit XORing both cores
bit = rng.gen_bit(rng_cores=rava.R_RngCores.AB_XOR)

# Generate 100 random bytes from each entropy core
bytes_a, bytes_b = rng.gen_bytes(n_bytes=100)

# Generate 100 8-bit integers between 0 and 99
ints8 = rng.gen_int8s(n_ints=100, delta=100)

# Generate 100 16-bit integers between 0 and 999
ints16 = rng.gen_int16s(n_ints=100, delta=1000)

# Generate 100 32-bit floats ranging between 0 and 1
floats = rng.gen_floats(n_floats=100)

# Close RAVA device
rng.close()
```

Additional examples are available in the `examples/` directory.


### TCP Communication

The driver also supports communication over TCP through a relay server, allowing one or more remote
clients to access a locally connected RAVA8 device.

Start the TCP server with:
```
python3 -m rng_rava.tcp_srv --host 127.0.0.1 --port 4884
```

The following example connects to the TCP server and uses the same API as the USB driver:
```
import rng_rava as rava

# Connect to the RAVA TCP server
rng = rava.RAVA8_TCP()
rng.open('127.0.0.1', 4884)

# Generate 100 random bytes from each entropy core
bytes_a, bytes_b = rng.gen_bytes(n_bytes=100)

...

# Close the connection
rng.close()
```


## Firmware Compatibility

| Firmware Version | Driver Version  |
|------------------|-----------------|
| v1.0.0           | v1.1.0 – v1.2.1 |
| ≥ v2.0.0         | ≥ v2.0.0        |
| ≥ v3.0.0         | ≥ v3.0.0        |


## Contact

[gabrielguerrer.com](https://gabrielguerrer.com/en/gabriel/)

[![RAVA logo](https://github.com/gabrielguerrer/rava8_rng/blob/main/images/rng_rava_logo.png)](https://rava-rng.org)
