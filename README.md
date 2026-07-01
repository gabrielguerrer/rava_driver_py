# RAVA Python Driver

<<<<<<< HEAD
The [RAVA Python Driver](https://github.com/gabrielguerrer/rng_rava_driver_py) 
implements the code for communicating with an 
[RAVA Device](https://github.com/gabrielguerrer/rng_rava) running the 
[RAVA Firmware](https://github.com/gabrielguerrer/rng_rava_firmware). 

The firmware establishes a USB CDC communication protocol with the computer 
host. Both Linux and Windows are equipped with generic drivers for CDC, 
eliminating the need for any specific driver software. This package implements
the serial commands used to control the RAVA device.

The RAVA_RNG class enables the request of pulse counts, random bits, random 
bytes, and random numbers (integers and floats). Additionally, it establishes 
the circuit's basic functionality encompassing key modules such as EEPROM, 
PWM BOOST, heath tests, peripherals, and interfaces.

The RAVA_RNG_AIO class offers the same functionality as RAVA_RNG but within an 
asynchronous framework.

The RAVA_RNG_LED class implements the code for controlling the LED module 
within the RAVA circuit. It allows users to adjust the color and the intensity 
of an attached WS2812B LED. 

For a deeper understanding of how the driver operates, please refer to the 
documentation provided within the source files and the provided examples.
=======
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
>>>>>>> 4fcf521 (Update v3.0.0)


## Installation

<<<<<<< HEAD
The driver code is available as the 
[rng_rava](https://pypi.org/project/rng_rava/) PyPI package. To install it, run:

=======
The driver is available on PyPI as [rng_rava](https://pypi.org/project/rng_rava/). 
After creating and activating a Python virtual environment, install it with:
>>>>>>> 4fcf521 (Update v3.0.0)
```
pip install rng_rava
```

<<<<<<< HEAD
Requirements: [pyserial](https://github.com/pyserial/pyserial), [numpy](https://github.com/numpy/numpy)


## Usage example
=======

## Usage
>>>>>>> 4fcf521 (Update v3.0.0)

```
import rng_rava as rava

# Find the serial number of the attached RAVA devices
rava_sns = rava.find_rava_sns()

<<<<<<< HEAD
# Create a RNG instance and connect to the first device
rng = rava.RAVA_RNG()
rng.connect(serial_number=rava_sns[0])

'''
The default PWM BOOST and RNG configuration parameters are stored in the EEPROM 
memory and can be accessed with rng.get_eeprom_pwm_boost() and 
rng.get_eeprom_rng(). If desired, users can modify the default values using the 
respective snd_ functions. Additionally, it is possible to make non-permanent 
configuration changes using the following commands:
'''

# Configure PWM BOOST
rng.snd_pwm_boost_setup(freq_id=rava.D_PWM_BOOST_FREQ['50_KHZ'], duty=20)

# Configure RNG
rng.snd_rng_setup(sampling_interval_us=10)

'''
Next, the generation of various random data types is demonstrated.
'''

# Measure 100 pulse counts
pc_a, pc_b = rng.get_rng_pulse_counts(n_counts=100)

# Generate a random bit XORing both channels
bit = rng.get_rng_bits(bit_source_id=rava.D_RNG_BIT_SRC['AB_XOR'])

# Generate 100 random bytes en each channel without post-processing
bytes_a, bytes_b = rng.get_rng_bytes(n_bytes=100, postproc_id=rava.D_RNG_POSTPROC['NONE'])

# Generate 100 8-bit integers between 0 and 99
ints8 = rng.get_rng_int8s(n_ints=100, int_delta=99)

# Generate 100 16-bit integers between 0 and 9999
ints16 = rng.get_rng_int16s(n_ints=100, int_delta=9999)

# Generate 100 32-bit floats ranging between 0 and 1
floats = rng.get_rng_floats(n_floats=100)
=======
# Create a RNG_USB instance and connect to the first device
rng = rava.RAVA_USB()
rng.open(rava_sns[0])

# Measure 100 pulse counts
pc_a, pc_b = rng.gen_pulse_counts(n_counts=100)

# Generate a random bit XORing both cores
bit = rng.gen_bit(rng_cores=rava.R_RngCores.AB_XOR)

# Generate 100 random bytes in each core
bytes_a, bytes_b = rng.gen_bytes(n_bytes=100)

# Generate 100 8-bit integers between 0 and 99
ints8 = rng.gen_int8s(n_ints=100, delta=100)

# Generate 100 16-bit integers between 0 and 999
ints16 = rng.gen_int16s(n_ints=100, delta=1000)

# Generate 100 32-bit floats ranging between 0 and 1
floats = rng.gen_floats(n_floats=100)
>>>>>>> 4fcf521 (Update v3.0.0)

# Close RAVA device
rng.close()
```

<<<<<<< HEAD

## Modules

Additionally, this package contains the following submodules.


### acq

The RAVA_ACQUISITION class implements the generation of extensive datasets
comprising random bytes, numbers or pulse counts extracted from a RAVA device.
Generation can occur in either threaded or blocking mode, and the output
can be presented as a memory array or a disk file.

For further insight, refer to the provided examples: acq_pcs.py, acq_bytes.py, 
acq_ints.py, and acq_floats.py.


### tk

Implements the RAVA_APP and RAVA_SUBAPP classes. The RAVA_APP is a 
[Tk](https://docs.python.org/3/library/tkinter.html) application designed to 
serve as a foundational framework for various Graphical User Interface (GUI) 
sub-applications utilizing the RAVA device.

Sub-applications are tk.Toplevel windows that integrate into the main 
application. Derived from the RAVA_SUBAPP class, they become part of the main 
application when included in the subapp_dicts argument. Once integrated, these 
sub-applications are easily accessible through the main application's menu and 
central buttons.


## Sub-Applications

### Control Panel

The Control Panel sub-app provides an GUI interface for testing the features 
implemented by the RAVA driver, including EEPROM, PWM, RNG, HEALTH, LED, and 
LAMP capabilities. 

Execute it using the following command:
```
python3 -m rng_rava.tk.ctrlp
```

<a href="https://github.com/gabrielguerrer/rng_rava_driver_py/blob/main/images/tk_control_panel.png">
<img src="https://github.com/gabrielguerrer/rng_rava_driver_py/blob/main/images/tk_control_panel.png" width="800">
</a>


### Acquisition

The Acquisition sub-app features a GUI interface for utilizing the 
RAVA_ACQUISITION class to generate files containing pulse counts, random bytes, 
or numbers.

Execute it using the following command:
```
python3 -m rng_rava.tk.acq
```

<a href="https://github.com/gabrielguerrer/rng_rava_driver_py/blob/main/images/tk_acquisition.png">
<img src="https://github.com/gabrielguerrer/rng_rava_driver_py/blob/main/images/tk_acquisition.png" width="800">
</a>
=======
Additional examples are available in the `examples/` directory.
>>>>>>> 4fcf521 (Update v3.0.0)


## Firmware Compatibility

<<<<<<< HEAD
Regarding the [RAVA Firmware](https://github.com/gabrielguerrer/rng_rava_firmware): 
- Driver versions v1.1.0 through v1.2.1 are compatible with Firmware v1.0.0
- Driver versions >= v2.0.0 are compatible with Firmware >= v2.0.0


## Associated projects

- [RAVA Device](https://github.com/gabrielguerrer/rng_rava)
- [RAVA Firmware](https://github.com/gabrielguerrer/rng_rava_firmware)
- [RAVA Python Diagnostics](https://github.com/gabrielguerrer/rng_rava_diagnostics_py)
=======
| Firmware Version | Driver Version  |
|------------------|-----------------|
| v1.0.0           | v1.1.0 – v1.2.1 |
| ≥ v2.0.0         | ≥ v2.0.0        |
| ≥ v3.0.0         | ≥ v3.0.0        |
>>>>>>> 4fcf521 (Update v3.0.0)


## Contact

<<<<<<< HEAD
gabrielguerrer [at] gmail [dot] com

![RAVA logo](https://github.com/gabrielguerrer/rng_rava/blob/main/images/rng_rava_logo.png)
=======
[gabrielguerrer.com](https://gabrielguerrer.com/en/gabriel/)

[![RAVA logo](https://github.com/gabrielguerrer/rava8_rng/blob/main/images/rng_rava_logo.png)](https://rava-rng.org)
>>>>>>> 4fcf521 (Update v3.0.0)
