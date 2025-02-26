"""Virtual serial port pair creation"""

from typing import Optional, Callable, List
from logging import Logger

from .virtual_serial_network import VirtualSerialNetwork
from ..config import SerialConnectionMinimalConfig


class VirtualSerialPair(VirtualSerialNetwork):
    """A virtual serial port pair for simulating serial communication."""

    def __init__(self, logger: Optional[Logger] = None) -> None:
        super().__init__(
            virtual_ports_num=2, external_ports=None, loopback=False, logger=logger
        )

    def start(self, openpty_func: Optional[Callable] = None):
        super().start(openpty_func)
        if self.virtual_ports_num < 2:
            self.logger.error("VSN: Failed to create virtual serial ports.")
            self.stop()

    def add(self, external_ports: List[SerialConnectionMinimalConfig]):
        self.logger.info("VSN: Not implemented for Virtual Serial Pair.")

    def create(self, ports_num: int):
        self.logger.info("VSN: Not implemented for Virtual Serial Pair.")

    def remove(self, remove_list: List[str]):
        self.logger.info("VSN: Not implemented for Virtual Serial Pair.")
