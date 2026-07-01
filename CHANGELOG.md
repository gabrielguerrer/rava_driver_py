## v3.0.0

This release introduces a major redesign of the communication layer to support the new firmware
v3.0.0 protocol and network-based access to RAVA devices.

### Added
- Support for the new framed binary protocol with an incremental byte-wise state parser
- Support for TCP communication, enabling multiple remote clients to share a single USB-connected
  RAVA device
- Multi-client TCP relay server
- New examples demonstrating TCP communication and server usage
- Added automated tests using `pytest`.

### Changed
- Updated to support firmware v3.0.0
- Improved protocol validation, including CRC verification, payload length validation, and
  structured device error handling
- Refactored the driver into a transport-independent communication layer shared by the USB and TCP
  drivers
- Improved exception handling by mapping protocol and device errors to dedicated Python exception
  classes
- Reorganized the source tree so that each command category is implemented in its own module file
- Removed the dependency on NumPy


## v2.0.0
- Adapted for firmware v2.0.0, reflecting updates in the EEPROM, LAMP and PERIPHERALS modules


## v1.2.1
- Correcting MANIFEST.in with the correct location of the rava logo


## v1.2.0
- Moving configuration functionality from RAVA_APP to new class RAVA_CFG
- RAVA_APP parameter rava_class allows to choose between RAVARng or RAVARng_LED
- Changed RAVA_APP default show_on_startup to True; Avoid macos issue of not showing matplotlib
  plots
- Fixed a bug in get_rng_byte_stream_data() that was returning the same bytes for both A and B
  channels
- snd_rng_byte_stream_start() now empties the queue data


## v1.1.0
- Adding numpy requirement
- Changing parameter list_output to output_type
- Including acq submodule for acquiring data from a RAVA device
- Including acq_pcs.py, acq_bytes.py, acq_ints.py, and acq_floats.py to examples/
- Including tk submodule for GUI apps defining RAVA_APP and RAVA_SUBAPP classes
- Including tk.acq used to evoke the tk acquire subapp via python3 -m rava.tk.acq
- Including tk.ctrlp used to evoke the tk control panel subapp via python3 -m rava.tk.ctrlp


## v1.0.2
- Checking for n > 0 in data generation
- Max n of pulse counts, bytes, ints, and floats changed to 2^16 (instead of 2^32)
- Improved the disconnection detection methodology
- Corrected the int_delta in integers generation


## v1.0.1
- Changed maximum line length from 80 to 120. This change does not apply to the code's documentation
- Using "not in" and "is not None"
- Correcting firmware version in eeprom_firmware
- Adding callbacks
- Setting logger name to 'rava'
- Changed health startup results format
- Including hardware float generation
