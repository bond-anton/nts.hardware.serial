"""Virtual serial port network creation"""

from typing import Union, List, Optional, Callable
from multiprocessing import Pipe, Process
from multiprocessing.connection import Connection
from logging import Logger, getLogger

from .worker import create_serial_network
from ..config import SerialConnectionMinimalConfig


# pylint: disable=too-many-instance-attributes
class VirtualSerialNetwork:
    """A virtual serial port network management."""

    def __init__(
        self,
        virtual_ports_num: int = 2,
        external_ports: Optional[List[SerialConnectionMinimalConfig]] = None,
        loopback: bool = False,
        logger: Optional[Logger] = None,
    ) -> None:
        self.__master_io: Optional[Connection] = None
        self.__worker_io: Optional[Connection] = None
        self.__p: Union[Process, None] = None
        self.loopback: bool = loopback
        self.external_ports: List[SerialConnectionMinimalConfig] = (
            external_ports if external_ports is not None else []
        )
        self._ext_ports_remove_duplicates()
        self.virtual_ports_num: int = virtual_ports_num
        self.serial_ports: List[str] = []

        self.logger: Logger = logger if isinstance(logger, Logger) else getLogger()

    def start(self, openpty_func: Optional[Callable] = None):
        """Start the virtual serial network and initialize communication."""
        self.logger.debug("VSN: STARTING")
        self.__master_io, self.__worker_io = Pipe()
        external_ports = None
        if self.external_ports:
            external_ports = [
                con_params.to_dict() for con_params in self.external_ports
            ]
        virtual_ports_num = self.virtual_ports_num
        self.__p = Process(
            target=create_serial_network,
            args=(
                self.__worker_io,
                virtual_ports_num,
                external_ports,
                self.loopback,
                openpty_func,
            ),
        )
        self.__p.start()
        self.virtual_ports_num = 0
        for _ in range(virtual_ports_num):
            response = self.__master_io.recv()
            if response["status"] == "ERROR":
                self.logger.error("VSN: ERROR (%s)", response["data"]["error"])
            elif response["status"] == "OK":
                self.serial_ports.append(response["data"])
                self.virtual_ports_num += 1
        ports_connected = []
        for _ in range(len(self.external_ports)):
            response = self.__master_io.recv()
            if response["status"] == "ERROR":
                self.logger.error("VSN: ERROR (%s)", response["data"]["error"])
            elif response["status"] == "OK":
                ports_connected.append(response["data"])
        self._update_ext_ports(ports_connected)
        self._ext_ports_remove_duplicates()
        self.serial_ports += ports_connected
        self.serial_ports = list(set(self.serial_ports))
        self.logger.info("VSN: STARTED")
        self.logger.info("VSN: %s", self.serial_ports)

    def _ext_ports_remove_duplicates(self):
        """Remove duplicates from external ports list."""
        new_external_ports_list = []
        for port_params in self.external_ports:
            duplicate = False
            for added_port in new_external_ports_list:
                if port_params.port == added_port.port:
                    duplicate = True
                    break
            if not duplicate:
                new_external_ports_list.append(port_params)
        self.external_ports = new_external_ports_list

    def _update_ext_ports(self, ports_connected: List[str]):
        """Update external ports list."""
        new_external_ports_list = []
        for port_params in self.external_ports:
            for port_name in ports_connected:
                if port_params.port == port_name:
                    new_external_ports_list.append(port_params)
                    break
        self.external_ports = new_external_ports_list

    def stop(self):
        """Stop the virtual serial network."""
        if self.__p is not None:
            self.logger.debug("VSN: STOPPING")
            self.__master_io.send({"cmd": "stop"})
            self.__p.join(timeout=5)  # Wait for the process to terminate

            self.__p = None
            self.__master_io, self.__worker_io = None, None
            self.serial_ports = []
            self.logger.info("VSN: STOPPED")

    def add(self, external_ports: List[SerialConnectionMinimalConfig]):
        """Add external ports to the network."""
        if self.__master_io is not None:
            ext_ports = [
                con_params.to_dict() for con_params in list(set(external_ports))
            ]
            self.__master_io.send({"cmd": "add", "data": ext_ports})
            ports_connected = []
            for _ in range(len(ext_ports)):
                response = self.__master_io.recv()
                if response["status"] == "ERROR":
                    self.logger.error("VSN: ERROR (%s)", response["data"]["error"])
                elif response["status"] == "EXIST":
                    self.logger.error("VSN: Port (%s) already added.", response["data"])
                elif response["status"] == "OK":
                    for port in list(set(external_ports)):
                        if port.port == response["data"]:
                            ports_connected.append(port)
                            break
            self.external_ports += ports_connected
            self._ext_ports_remove_duplicates()
            self.serial_ports += [port.port for port in ports_connected]
            self.serial_ports = list(set(self.serial_ports))

    def create(self, ports_num: int):
        """Create new virtual ports in the network."""
        if self.__master_io is not None:
            self.__master_io.send({"cmd": "create", "data": ports_num})
            for _ in range(ports_num):
                response = self.__master_io.recv()
                if response["status"] == "ERROR":
                    self.logger.error("VSN: ERROR (%s)", response["data"]["error"])
                elif response["status"] == "OK":
                    self.serial_ports.append(response["data"])
                    self.virtual_ports_num += 1

    def remove(self, remove_list: List[str]):
        """Remove port from the network."""
        if self.__master_io is not None:
            self.__master_io.send({"cmd": "remove", "data": remove_list})
            removed_ports = []
            for _ in range(len(remove_list)):
                response = self.__master_io.recv()
                if response["status"] == "ERROR":
                    self.logger.error("VSN: ERROR (%s)", response["data"]["error"])
                if response["status"] == "NOT_EXIST":
                    self.logger.warning("VSN: Port %s not found", response["data"])
                elif response["status"] == "OK":
                    removed_ports.append(response["data"])
            for port in removed_ports:
                found = False
                for i, ext_port in enumerate(self.external_ports):
                    if ext_port.port == port:
                        del self.external_ports[i]
                        found = True
                        break
                if not found:
                    self.virtual_ports_num -= 1
            self.serial_ports = list(set(self.serial_ports) - set(removed_ports))
