"""
Copyright (c) 2026 Gabriel Guerrer

Distributed under the MIT license - See LICENSE for details
"""

"""
RAVA exception hierarchy.

Exceptions are grouped into three categories:
- Transport errors: communication and connection failures.
- Device errors: errors reported by the RAVA firmware.
- Host errors: errors detected by the driver itself.

RAVAError
│
├── RAVATransportError
│   ├── RAVAConnectError
│   ├── RAVAClosedError
│   ├── RAVADisconnectedError
│   ├── RAVAReadError
│   └── RAVAWriteError
│
├── RAVADeviceError
│   ├── RAVAFirmwareVersionError
│   ├── RAVAFirmwareModuleError
│   ├── RAVAProtocolError
│   ├── RAVAParameterError
│   ├── RAVAHealthError
│   └── RAVAByteStreamingError
│
└── RAVAHostError
    ├── RAVAMCUError
    ├── RAVAClientIDError
    ├── RAVARequestIDError
    ├── RAVAMissingQueueError
    └── RAVAQueueTimeoutError
"""

############################
# RAVA ERRORS
############################


class RAVAError(Exception):
    """Base class for all RAVA exceptions."""


# Transport

class RAVATransportError(RAVAError):
    """Base class for transport-related errors."""


class RAVAConnectError(RAVATransportError):
    """Failed to connect to a RAVA device."""


class RAVAClosedError(RAVATransportError):
    """Operation attempted on closed device."""


class RAVADisconnectedError(RAVATransportError):
    """Device disconnected during an operation."""


class RAVAReadError(RAVATransportError):
    """Failed to read data from the device."""


class RAVAWriteError(RAVATransportError):
    """Failed to write data to the device."""


# Device

class RAVADeviceError(RAVAError):
    """Base class for errors reported by the device."""


class RAVAFirmwareVersionError(RAVADeviceError):
    """Device Firmware version is incompatible with the driver."""


class RAVAFirmwareModuleError(RAVADeviceError):
    """Raised when the requested firmware module is disabled."""


class RAVAProtocolError(RAVADeviceError):
    """Protocol violation or malformed message detected."""


class RAVAParameterError(RAVADeviceError):
    """Device rejected one or more input parameters."""


class RAVAHealthError(RAVADeviceError):
    """Device startup health test failed."""


class RAVAByteStreamingError(RAVADeviceError):
    """Error associated to periodic byte streaming functionality."""


# Host

class RAVAHostError(RAVAError):
    """Base class for host-side driver errors."""


class RAVAMCUError(RAVAHostError):
    """Driver module is incompatible with the device's microcontroller."""


class RAVAClientIDError(RAVAHostError):
    """No unique client ID is available."""


class RAVARequestIDError(RAVAHostError):
    """No unique request ID is available."""


class RAVAMissingQueueError(RAVAHostError):
    """Response queue for the request could not be found."""


class RAVAQueueTimeoutError(RAVAHostError):
    """Timed out waiting for a response from the device."""