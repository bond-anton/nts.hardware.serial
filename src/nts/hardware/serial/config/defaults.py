"""Serial connection config defaults"""

from typing import Union


DEFAULT_BAUDRATE: int = 9600
DEFAULT_BAUDRATE_LIST: tuple[int, ...] = (
    300,
    600,
    1200,
    2400,
    4800,
    9600,
    14400,
    19200,
    38400,
    57600,
    115200,
)

DEFAULT_BYTESIZE = 8
DEFAULT_BYTESIZE_LIST: tuple[int, int, int, int] = (5, 6, 7, 8)

DEFAULT_PARITY: str = "N"
DEFAULT_PARITY_LIST: tuple[str, str, str] = ("N", "E", "O")

DEFAULT_STOPBITS: int = 1
DEFAULT_STOPBITS_LIST: tuple[int, int] = (1, 2)

DEFAULT_TIMEOUT: Union[float, None] = None

DEFAULT_FRAMER: str = "RTU"
DEFAULT_FRAMER_LIST: tuple[str, str] = ("RTU", "ASCII")
