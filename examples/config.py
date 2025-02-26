"""Example of SerialConnectionConfig class usage."""

from nts.hardware.serial.config.serial_connection_implementation import (
    SerialConnectionMinimalConfig,
    SerialConnectionConfig,
    ModbusSerialConnectionConfig,
)


min_conf = SerialConnectionMinimalConfig(port="COM1", bytesize=7, parity="N")
ser_conf = SerialConnectionConfig(port="COM1", bytesize=7, write_timeout=1.0)
mod_conf = ModbusSerialConnectionConfig(port="COM1")


if __name__ == "__main__":
    print(min_conf)
    print(ser_conf)
    print(mod_conf)
