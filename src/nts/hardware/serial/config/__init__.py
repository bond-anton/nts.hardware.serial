"""
Module for defining serial communication config models.

This module contains abstract base classes for serial communication config, allowing for
customizable and extendable setups as well as dataclass implementation.

Abstract classes include:

1. **SerialConnectionMinimalConfigModel**: Defines the minimal config for serial
   communication, including properties such as port, baudrate, bytesize, parity, and stopbits.

2. **SerialConnectionConfigModel**: Extends `SerialConnectionMinimalConfigModel` by adding
   timeout-related settings like `timeout`, `write_timeout`, and `inter_byte_timeout`.

3. **ModbusSerialConnectionConfigModel**: Extends `SerialConnectionMinimalConfigModel` by adding
   Modbus-specific config, including the `framer` property for Modbus framing types
   (e.g., "RTU", "ASCII").

These classes are designed to be extended by concrete implementations, providing flexibility in how
serial communication configurations are structured and used in various applications.


"""

from .exceptions import SerialConnectionConfigError
from .serial_connection_interface import (
    SerialConnectionMinimalConfigModel,
    SerialConnectionConfigModel,
    ModbusSerialConnectionConfigModel,
)
from .serial_connection_implementation import (
    SerialConnectionMinimalConfig,
    SerialConnectionConfig,
    ModbusSerialConnectionConfig,
)
