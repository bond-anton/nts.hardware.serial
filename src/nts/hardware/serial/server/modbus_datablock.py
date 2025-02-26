"""Custom reactive DataBlock for modbus server"""

from logging import Logger, getLogger
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
)


class ReactiveSequentialDataBlock(ModbusSequentialDataBlock):
    """DataBlock with custom action on value change."""

    def __init__(self, *args, logger=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger if isinstance(logger, Logger) else getLogger()

    def setValues(self, address, values):
        """setValue redefined with custom callback."""
        super().setValues(address, values)
        self.on_change(address, values)

    def on_change(self, address, values):
        """Register value change callback."""
        self.logger.debug("Register %s changed value to %s", address, values)
