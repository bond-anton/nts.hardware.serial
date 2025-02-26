"""
RS485 Modbus Serial Server.

This module implements an RS485 Modbus server capable of managing multiple slave contexts and
responding to Modbus requests. It leverages the `pymodbus` library for serial communication and
server management.

Dependencies:
    - pymodbus: Provides base classes and utilities for building Modbus servers and clients.
    - pyserial-asyncio: Enables asynchronous I/O operations for serial communication.

Classes:
    - RS485Server: Main class implementing the RS485 Modbus server.

Methods:
    - start(self): Starts the server and listens for incoming Modbus requests.
    - update_slave(self, slave_id, store): Adds or updates a slave context in the server.
    - remove_slave(self, slave_id): Removes a slave context from the server.
    - stop(self): Stops the server and shuts down all connections.
    - restart(self): Restarts the server after stopping it.

This server is designed to handle multiple Modbus slaves efficiently, making it suitable for
industrial automation and IoT applications that require scalable and reliable communication
over RS485 interfaces.
"""

from typing import Dict, Union, Optional
import asyncio
from logging import Logger, getLogger

from pymodbus.datastore import (
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.server import ModbusSerialServer

from ..version import __version__ as version
from ..config import (
    SerialConnectionConfigModel,
    ModbusSerialConnectionConfigModel,
)
from ..utilities.modbus import modbus_connection_config
from .modbus_datablock import ReactiveSequentialDataBlock


SERVER_INFO = {
    "VendorName": "SCIETEX",
    "ProductCode": "SSMBRS",
    "VendorUrl": "https://scietex.ru",
    "ProductName": "Scietex MODBUS Server",
    "ModelName": "Scietex Serial MODBUS RTU Server",
    "MajorMinorRevision": version,
}


class RS485Server:
    """
    RS485 Modbus Serial Server.

    This class implements an RS485 Modbus server that can handle multiple slave contexts and
    respond to Modbus requests. It uses the `pymodbus` library for serial communication and
    server management.

    Attributes:
        slaves (dict): Mapping of slave IDs to their respective ModbusSlaveContext objects.
        context (ModbusServerContext): Server context containing all registered slave contexts.
        identity (ModbusDeviceIdentification): Identification information for the server.
        con_params (Union[SerialConnectionConfigModel, ModbusSerialConnectionConfigModel]):
            Connection parameters for the server.
        logger (Logger): Logging handler for recording operational information.
        task (Optional[asyncio.Task]): Task associated with the server execution.
        server (Optional[ModbusSerialServer]): Underlying ModbusSerialServer instance.

    Methods:
        - start(self): Starts the server and begins listening for incoming Modbus requests.
        - update_slave(self, slave_id, store): Adds or updates a slave context in the server.
        - remove_slave(self, slave_id): Removes a slave context from the server.
        - stop(self): Stops the server and shuts down all connections.
        - restart(self): Restarts the server after stopping it.
    """

    def __init__(
        self,
        con_params: Union[
            SerialConnectionConfigModel, ModbusSerialConnectionConfigModel
        ],
        slaves: Optional[Dict[int, ModbusSlaveContext]] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initialize the RS485Server instance.

        Args:
            con_params (Union[SerialConnectionConfigModel, ModbusSerialConnectionConfigModel]):
                Connection parameters for the server, such as port, baudrate, etc.
            slaves (Optional[Dict[int, ModbusSlaveContext]], optional): Mapping of slave IDs to
                their respective ModbusSlaveContext objects. Defaults to a single slave with
                predefined values.
            logger (Optional[Logger], optional): Logging handler for recording operational
                information. Defaults to a basic logger if none is provided.
        """
        self.slaves: Dict[int, ModbusSlaveContext] = {}
        if slaves is not None:
            if not isinstance(slaves, dict):
                raise TypeError(
                    "The 'slaves' argument must be a dict mapping integers to ModbusSlaveContext."
                )
            for addr, store in slaves.items():
                if (
                    isinstance(store, ModbusSlaveContext)
                    and isinstance(addr, int)
                    and 0 < addr < 248
                ):
                    self.slaves[addr] = store
        else:
            block = ReactiveSequentialDataBlock(0x01, [17] * 100)
            store = ModbusSlaveContext(di=block, co=block, hr=block, ir=block)
            self.slaves = {0x01: store}

        self.context = ModbusServerContext(slaves=self.slaves, single=False)
        self.identity = ModbusDeviceIdentification(info_name=SERVER_INFO)
        self.con_params: Union[
            SerialConnectionConfigModel, ModbusSerialConnectionConfigModel
        ] = con_params
        self.logger: Logger = logger if isinstance(logger, Logger) else getLogger()
        self._task: Union[asyncio.Task, None] = None
        self.server: Optional[ModbusSerialServer] = None

    async def start(self):
        """
        Start the server.

        This method starts the Modbus server and begins listening for incoming Modbus requests.
        It also initializes the server context and prepares the underlying communication
        infrastructure.

        Notes:
            - If the server is already running, this method has no effect.
        """
        if self.server is None:
            self.server = ModbusSerialServer(
                context=self.context,  # Data storage
                identity=self.identity,  # server identify
                **modbus_connection_config(self.con_params),
            )
        self._task = asyncio.create_task(self.server.serve_forever())
        self.logger.info("Server started")

    async def update_slave(self, slave_id: int, store: ModbusSlaveContext):
        """
        Add or update a slave context in the server.

        This method adds or updates a Modbus slave context in the server's context. It is useful
        for dynamically changing the server's behavior without restarting the entire server.

        Args:
            slave_id (int): Unique identifier for the slave being updated or added.
            store (ModbusSlaveContext): ModbusSlaveContext object representing the slave's data.

        Raises:
            ValueError: If the slave ID is invalid or out of range.

        Notes:
            - The server context is updated dynamically, allowing immediate changes to take effect.
        """
        if not isinstance(slave_id, int) or not 0 < slave_id < 248:
            raise ValueError("Invalid slave ID. Must be an integer between 1 and 247.")
        self.slaves[slave_id] = store
        self.context = ModbusServerContext(slaves=self.slaves, single=False)
        self.logger.info("Slave with ID %s added/updated successfully.", slave_id)
        if self._task is not None:
            await self.restart()

    async def remove_slave(self, slave_id: int):
        """
        Remove a slave context from the server.

        This method removes a Modbus slave context from the server's context, effectively disabling
        communication with that particular slave.

        Args:
            slave_id (int): Unique identifier of the slave to be removed.

        Raises:
            KeyError: If the specified slave ID does not exist in the server's context.

        Notes:
            - The server context is updated dynamically, allowing immediate removal of the slave.
        """
        if slave_id in self.slaves:
            del self.slaves[slave_id]
            self.context = ModbusServerContext(slaves=self.slaves, single=False)
            self.logger.info("Slave with ID %s deleted successfully.", slave_id)
            if self._task is not None:
                await self.restart()
        else:
            self.logger.warning("Slave with ID %s not found.", slave_id)

    async def stop(self):
        """
        Stop the server.

        This method stops the Modbus server, closes all open connections, and frees allocated
        resources. It should be called when the server is no longer needed to prevent resource
        leaks.

        Notes:
            - If the server is not running, this method has no effect.
        """
        if self._task is not None:
            if self.server.is_active():
                await self.server.shutdown()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            finally:
                if self._task.done():
                    self._task = None
                self.logger.info("Server Stopped")
        self.server = None

    async def restart(self):
        """
        Restart the server.

        This method safely stops the currently running server and starts it again.
        It is useful for refreshing the server context or resetting the server state.

        Notes:
            - If the server is not running, this method starts it afresh.
        """
        self.logger.info("Restarting the server.")
        await self.stop()
        await self.start()
