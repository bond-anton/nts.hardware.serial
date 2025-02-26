"""Serial connection config validation routines"""

from typing import Union

from .exceptions import SerialConnectionConfigError
from .defaults import (
    DEFAULT_BAUDRATE,
    DEFAULT_BAUDRATE_LIST,
    DEFAULT_BYTESIZE,
    DEFAULT_BYTESIZE_LIST,
    DEFAULT_PARITY,
    DEFAULT_PARITY_LIST,
    DEFAULT_STOPBITS,
    DEFAULT_STOPBITS_LIST,
    DEFAULT_TIMEOUT,
    DEFAULT_FRAMER,
    DEFAULT_FRAMER_LIST,
)


def validate_port(port: Union[str, None]) -> str:
    """
    Validate the port value.

    Args:
        port (str): Port name to validate.

    Raises:
        SerialConnectionConfigError: If the port is invalid.

    Returns:
        str: Validated port name.
    """
    if not port:
        raise SerialConnectionConfigError("Port cannot be empty")
    if not isinstance(port, str):
        raise SerialConnectionConfigError(f"Port must be a string, got {type(port)}")
    if len(port) < 3:
        raise SerialConnectionConfigError("Port name is too short")
    return port


def validate_baudrate(baudrate: Union[int, None]) -> int:
    """
    Validate the baudrate value.

    Args:
        baudrate (int): Baud rate to validate.

    Returns:
        int: Validated baud rate.
    """
    if baudrate is None:
        return DEFAULT_BAUDRATE
    if not isinstance(baudrate, int):
        raise SerialConnectionConfigError(
            f"Baudrate must be integer number, got {type(baudrate)}"
        )
    if baudrate not in DEFAULT_BAUDRATE_LIST:
        raise SerialConnectionConfigError(f"Invalid baudrate: {baudrate}")
    return baudrate


def validate_bytesize(bytesize: Union[int, None]) -> int:
    """
    Validate the bytesize value.

    Args:
        bytesize (int): Number of data bits to validate.

    Returns:
        int: Validated bytesize.
    """
    if bytesize is None:
        return DEFAULT_BYTESIZE
    if not isinstance(bytesize, int):
        raise SerialConnectionConfigError(
            f"Bytesize must be integer number, got {type(bytesize)}"
        )
    if bytesize not in DEFAULT_BYTESIZE_LIST:
        raise SerialConnectionConfigError(f"Invalid bytesize: {bytesize}")
    return bytesize


def validate_parity(parity: Union[str, None]) -> str:
    """
    Validate the parity value.

    Args:
        parity (str): Parity value to validate.

    Returns:
        str: Validated parity.
    """
    if parity is None:
        return DEFAULT_PARITY
    if not isinstance(parity, str):
        raise SerialConnectionConfigError(
            f"Parity must be a string, got {type(parity)}"
        )
    if parity not in DEFAULT_PARITY_LIST:
        raise SerialConnectionConfigError(f"Invalid parity: {parity}")
    return parity


def validate_stopbits(stopbits: Union[int, None]) -> int:
    """
    Validate the stopbits value.

    Args:
        stopbits (int): Stop bits to validate.

    Returns:
        int: Validated stopbits.
    """
    if stopbits is None:
        return DEFAULT_STOPBITS
    if not isinstance(stopbits, int):
        raise SerialConnectionConfigError(
            f"Stopbits must be integer number, got {type(stopbits)}"
        )
    if stopbits not in DEFAULT_STOPBITS_LIST:
        raise SerialConnectionConfigError(f"Invalid stopbits: {stopbits}")
    return stopbits


def validate_timeout(timeout: Union[float, None]) -> Union[float, None]:
    """
    Validate the timeout value.

    Args:
        timeout (Union[float, None]): Timeout value to validate.

    Returns:
        Union[float, None]: Validated timeout.
    """
    if timeout is None:
        return DEFAULT_TIMEOUT
    if not isinstance(timeout, (float, int)):
        raise SerialConnectionConfigError(
            f"Timeout must be a float, got: {type(timeout)}"
        )
    if timeout < 0:
        raise SerialConnectionConfigError(f"Timeout cannot be negative: {timeout}")
    return float(timeout)


def validate_framer(framer: Union[str, None]) -> str:
    """
    Validate the framer value.

    Args:
        framer (str): Framer value to validate.

    Returns:
        str: Validated framer.
    """
    if framer is None:
        return DEFAULT_FRAMER
    if framer not in DEFAULT_FRAMER_LIST:
        raise SerialConnectionConfigError(f"Unsupported Framer type: {framer}")
    return framer
