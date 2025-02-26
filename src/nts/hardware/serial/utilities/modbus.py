"""modbus basic utility functions"""

from typing import Optional, Union, List
import logging
from pymodbus import ModbusException, FramerType
from pymodbus.client import AsyncModbusSerialClient


from ..config import SerialConnectionMinimalConfigModel
from ..config.defaults import DEFAULT_TIMEOUT, DEFAULT_FRAMER


def modbus_connection_config(con_params: SerialConnectionMinimalConfigModel) -> dict:
    """Prepare dict for modbus connection over serial interface"""
    keys: tuple[str, ...] = (
        "port",
        "baudrate",
        "bytesize",
        "stopbits",
        "parity",
        "timeout",
        "framer",
    )
    if not isinstance(con_params, SerialConnectionMinimalConfigModel):
        raise TypeError("Invalid type for Modbus client config.")
    params_dict = con_params.to_dict()
    if "timeout" not in params_dict:
        params_dict["timeout"] = DEFAULT_TIMEOUT
    if "framer" not in params_dict:
        params_dict["framer"] = DEFAULT_FRAMER
    if params_dict["framer"] == "RTU":
        params_dict["framer"] = FramerType.RTU
    else:
        params_dict["framer"] = FramerType.ASCII
    return {k: params_dict[k] for k in keys}


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def modbus_read_registers(
    con_params: SerialConnectionMinimalConfigModel,
    start_register: int = 0,
    count: int = 1,
    slave: int = 1,
    label: Union[str, None] = None,
    logger: Union[logging.Logger, None] = None,
    holding: bool = True,
) -> Union[list[int], None]:
    """Read input registers data"""
    client = AsyncModbusSerialClient(**modbus_connection_config(con_params))
    await client.connect()
    if not client.connected:
        return None
    try:
        if holding:
            response = await client.read_holding_registers(
                start_register, count=count, slave=slave
            )
        else:
            response = await client.read_input_registers(
                start_register, count=count, slave=slave
            )
    except ModbusException as e:
        if logger:
            logger.error("%s: Modbus Exception on read input registers %s", label, e)
        return None
    finally:
        client.close()
    if response.isError():
        if logger:
            logger.error("%s: Received exception from device (%s)", label, response)
        return None
    if hasattr(response, "registers"):
        return response.registers
    return None


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def modbus_read_input_registers(
    con_params: SerialConnectionMinimalConfigModel,
    start_register: int = 0,
    count: int = 1,
    slave: int = 1,
    label: Union[str, None] = None,
    logger: Union[logging.Logger, None] = None,
) -> Optional[list[int]]:
    """Read input registers data"""
    if logger:
        logger.debug(
            "%s: Reading input registers, start: %i, count: %i",
            label,
            start_register,
            count,
        )
    return await modbus_read_registers(
        con_params, start_register, count, slave, label, logger, holding=False
    )


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def modbus_read_holding_registers(
    con_params: SerialConnectionMinimalConfigModel,
    start_register: int = 0,
    count: int = 1,
    slave: int = 1,
    label: Union[str, None] = None,
    logger: Union[logging.Logger, None] = None,
) -> Union[list[int], None]:
    """Read input registers data"""
    if logger:
        logger.debug(
            "%s: Reading holding registers, start: %i, count: %i",
            label,
            start_register,
            count,
        )
    return await modbus_read_registers(
        con_params, start_register, count, slave, label, logger, holding=True
    )


# pylint: disable=too-many-arguments, too-many-positional-arguments
async def modbus_write_registers(
    con_params: SerialConnectionMinimalConfigModel,
    register: int,
    value: List[int],
    slave: int = 1,
    label: Union[str, None] = None,
    logger: Union[logging.Logger, None] = None,
) -> Union[list[int], None]:
    """Write data value to registers"""
    if logger:
        logger.debug(
            "%s: Writing data to registers %i-%i",
            label,
            register,
            register + len(value),
        )
    client = AsyncModbusSerialClient(**modbus_connection_config(con_params))
    await client.connect()
    try:
        response = await client.write_registers(register, value, slave=slave)
    except ModbusException as e:
        if logger:
            logger.error("%s: Modbus Exception on write register %s", label, e)
        client.close()
        return None
    client.close()
    if response.isError():
        if logger:
            logger.error("%s: Received exception from device (%s)", label, response)
        return None
    if hasattr(response, "registers"):
        return response.registers
    return None
