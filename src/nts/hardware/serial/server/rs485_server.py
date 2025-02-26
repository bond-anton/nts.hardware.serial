"""RS485 Server"""

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
    """RS485 Modbus Serial Server."""

    def __init__(
        self,
        con_params: Union[
            SerialConnectionConfigModel, ModbusSerialConnectionConfigModel
        ],
        slaves: Optional[Dict[int, ModbusSlaveContext]] = None,
        logger: Optional[Logger] = None,
    ):
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
        """Start server"""
        if self.server is None:
            self.server = ModbusSerialServer(
                context=self.context,  # Data storage
                identity=self.identity,  # server identify
                **modbus_connection_config(self.con_params)
            )
        self._task = asyncio.create_task(self.server.serve_forever())
        self.logger.info("Server started")

    async def update_slave(self, slave_id, store: ModbusSlaveContext):
        """
        Add or update a slave to the server context.
        :param slave_id: Slave ID (for example, 0x01)
        :param store: Slave datastore (ModbusSlaveContext)
        """
        self.slaves[slave_id] = store
        self.context = ModbusServerContext(slaves=self.slaves, single=False)
        self.logger.info("Slave with ID %s added/updated successfully.", slave_id)
        if self._task is not None:
            await self.restart()

    async def remove_slave(self, slave_id):
        """
        Delete a slave with provided ID from the server context.
        :param slave_id: Slave id (for example, 0x01)
        """
        if slave_id in self.slaves:
            del self.slaves[slave_id]
            self.context = ModbusServerContext(slaves=self.slaves, single=False)
            self.logger.info("Slave with ID %s deleted successfully.", slave_id)
            if self._task is not None:
                await self.restart()
        else:
            self.logger.info("Slave with ID %s not found.", slave_id)

    async def stop(self):
        """Stop server"""
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
        """Restart server"""
        self.logger.info("Restarting the server.")
        await self.stop()
        await self.start()
