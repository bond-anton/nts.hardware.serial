"""
Implementation of serial connection config interface.
"""

from typing import Union

from .serial_connection_interface import (
    SerialConnectionMinimalConfigModel,
    SerialConnectionConfigModel,
    ModbusSerialConnectionConfigModel,
)
from .validation import (
    validate_port,
    validate_baudrate,
    validate_bytesize,
    validate_parity,
    validate_stopbits,
    validate_timeout,
    validate_framer,
)


class SerialConnectionMinimalConfig(SerialConnectionMinimalConfigModel):
    """
    Represents the minimal config for a serial connection.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        port: Union[str, None] = None,
        baudrate: Union[int, None] = None,
        bytesize: Union[int, None] = None,
        parity: Union[str, None] = None,
        stopbits: Union[int, None] = None,
        **kwargs
    ) -> None:
        self._port: str = validate_port(port)
        self._baudrate = validate_baudrate(baudrate)
        self._bytesize = validate_bytesize(bytesize)
        self._parity = validate_parity(parity)
        self._stopbits = validate_stopbits(stopbits)
        if kwargs is not None:
            # Placeholder for kwargs processing
            pass

    @property
    def port(self) -> str:
        """
        The serial port name (COM1, /dev/serial0, etc.).

        Returns:
            str: The name of the serial port.
        """
        return self._port

    @port.setter
    def port(self, value: str) -> None:
        self._port = validate_port(value)

    @property
    def baudrate(self) -> int:
        """
        The serial port baudrate.

        Returns:
            int: The baudrate of the serial port.
        """
        return self._baudrate

    @baudrate.setter
    def baudrate(self, value: int) -> None:
        self._baudrate = validate_baudrate(value)

    @property
    def bytesize(self) -> int:
        """
        The serial port bytesize.

        Returns:
            int: The bytesize of the serial port.
        """
        return self._bytesize

    @bytesize.setter
    def bytesize(self, value: int) -> None:
        self._bytesize = validate_bytesize(value)

    @property
    def parity(self) -> str:
        """
        The serial port parity. One of ("N", "O", "E").

        Returns:
            str: The parity of the serial port.
        """
        return self._parity

    @parity.setter
    def parity(self, value: str) -> None:
        self._parity = validate_parity(value)

    @property
    def stopbits(self) -> int:
        """
        The serial port stopbits (1 or 2).

        Returns:
            int: The stopbits of the serial port.
        """
        return self._stopbits

    @stopbits.setter
    def stopbits(self, value: int) -> None:
        self._stopbits = validate_stopbits(value)

    def to_dict(self) -> dict:
        """
        Converts the serial connection config to a dictionary.

        Returns:
            dict: A dictionary representation of the serial connection config.
        """
        return {
            "port": self.port,
            "baudrate": self.baudrate,
            "bytesize": self.bytesize,
            "parity": self.parity,
            "stopbits": self.stopbits,
        }


class SerialConnectionConfig(
    SerialConnectionMinimalConfig, SerialConnectionConfigModel
):
    """
    Serial connection config.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        port: Union[str, None] = None,
        baudrate: Union[int, None] = None,
        bytesize: Union[int, None] = None,
        parity: Union[str, None] = None,
        stopbits: Union[int, None] = None,
        timeout: Union[float, None] = None,
        write_timeout: Union[float, None] = None,
        inter_byte_timeout: Union[float, None] = None,
        **kwargs
    ) -> None:
        super().__init__(port, baudrate, bytesize, parity, stopbits, **kwargs)
        self._timeout = validate_timeout(timeout)
        self._write_timeout = validate_timeout(write_timeout)
        self._inter_byte_timeout = validate_timeout(inter_byte_timeout)

    @property
    def timeout(self) -> Union[float, None]:
        """
        The timeout value for the serial connection.

        Returns:
            value (Union[float, None]): Timeout value in seconds, or None to disable the timeout.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: Union[float, None]) -> None:
        self._timeout = validate_timeout(value)

    @property
    def write_timeout(self) -> Union[float, None]:
        """
        The write timeout value for the serial connection.

        Returns:
            Union[float, None]: The write timeout value in seconds, or None if no timeout is set.
        """
        return self._write_timeout

    @write_timeout.setter
    def write_timeout(self, value: Union[float, None]) -> None:
        self._write_timeout = validate_timeout(value)

    @property
    def inter_byte_timeout(self) -> Union[float, None]:
        """
        The inter-byte timeout value for the serial connection.

        Returns:
            Union[float, None]: Inter-byte timeout value in seconds, or None if no timeout is set.
        """
        return self._inter_byte_timeout

    @inter_byte_timeout.setter
    def inter_byte_timeout(self, value: Union[float, None]) -> None:
        self._inter_byte_timeout = validate_timeout(value)

    def to_dict(self) -> dict:
        return super().to_dict() | {
            "timeout": self.timeout,
            "write_timeout": self.write_timeout,
            "inter_byte_timeout": self.inter_byte_timeout,
        }


class ModbusSerialConnectionConfig(
    SerialConnectionMinimalConfig, ModbusSerialConnectionConfigModel
):
    """
    Modbus serial connection config.
    """

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def __init__(
        self,
        port: Union[str, None] = None,
        baudrate: Union[int, None] = None,
        bytesize: Union[int, None] = None,
        parity: Union[str, None] = None,
        stopbits: Union[int, None] = None,
        timeout: Union[float, None] = None,
        framer: Union[str, None] = None,
        **kwargs
    ) -> None:
        super().__init__(port, baudrate, bytesize, parity, stopbits, **kwargs)
        self._timeout = validate_timeout(timeout)
        self._framer = validate_framer(framer)

    @property
    def timeout(self) -> Union[float, None]:
        """
        The timeout value for the serial connection.

        Returns:
            value (Union[float, None]): Timeout value in seconds, or None to disable the timeout.
        """
        return self._timeout

    @timeout.setter
    def timeout(self, value: Union[float, None]) -> None:
        self._timeout = validate_timeout(value)

    @property
    def framer(self) -> str:
        """
        The Modbus framer type.

        Returns:
            str: The type of Modbus framing used (e.g., "RTU", "ASCII").
        """
        return self._framer

    @framer.setter
    def framer(self, value: str) -> None:
        self._framer = validate_framer(value)

    def to_dict(self) -> dict:
        return super().to_dict() | {"framer": self.framer, "timeout": self.timeout}
