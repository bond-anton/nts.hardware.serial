"""
Modbus basic utility functions.

This module provides essential utility functions for working with the Modbus protocol, specifically
for serial communication. It includes routines for setting up connections, reading and writing
register values, and handling exceptions gracefully. These functions leverage the `pymodbus`
library and aim to simplify interactions with Modbus-compatible devices.

Dependencies:
    - pymodbus: A popular Python library for implementing Modbus clients and servers.

Functions:
    - modbus_connection_config(con_params: SerialConnectionMinimalConfigModel) -> dict:
        Prepares a dictionary of parameters for establishing a Modbus connection over
        a serial interface.
    - modbus_read_registers(con_params: ..., start_register: int = 0, ...)
        -> Union[list[int], None]: Reads data from Modbus holding or input registers.
    - modbus_read_input_registers(con_params: ..., start_register: int = 0, ...)
        -> Optional[list[int]]: Reads data specifically from Modbus input registers.
    - modbus_read_holding_registers(con_params: ..., start_register: int = 0, ...)
        -> Union[list[int], None]: Reads data specifically from Modbus holding registers.
    - modbus_write_registers(con_params: ..., register: int, value: List[int], ...)
        -> Union[list[int], None]: Writes data to Modbus registers.

These functions facilitate robust and efficient Modbus communication, ensuring proper error
handling and adherence to Modbus specifications.

This module simplifies working with Modbus by abstracting low-level details, allowing developers to
focus on higher-level tasks such as retrieving or updating device states.
"""

from typing import Optional, Union, List
import logging
from pymodbus import ModbusException, FramerType
from pymodbus.client import AsyncModbusSerialClient

from ..config import SerialConnectionMinimalConfigModel
from ..config.defaults import DEFAULT_TIMEOUT, DEFAULT_FRAMER


def modbus_connection_config(con_params: SerialConnectionMinimalConfigModel) -> dict:
    """
    Prepare dict for Modbus connection over serial interface.

    This function generates a dictionary containing the necessary parameters for connecting
    to a Modbus device via a serial interface. It validates the input configuration and fills in
    default values for missing fields.

    Args:
        con_params (SerialConnectionMinimalConfigModel): Configuration object specifying serial
            connection settings such as baud rate, parity, etc.

    Returns:
        dict: Dictionary of validated and completed connection parameters.

    Raises:
        TypeError: If the input parameter is not of the expected type.

    Notes:
        - Missing timeout and framer settings are filled with defaults.
        - Supported framer types include ASCII and RTU, mapped to corresponding `FramerType` enums.
    """
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
    """
    Read input registers data.

    Asynchronously reads Modbus register values, either from holding registers or input registers,
    depending on the `holding` flag. Handles exceptions and logs errors for debugging purposes.

    Args:
        con_params (SerialConnectionMinimalConfigModel): Object containing serial connection
            parameters.
        start_register (int, optional): Starting address of the register to read. Defaults to 0.
        count (int, optional): Number of registers to read. Defaults to 1.
        slave (int, optional): Slave ID of the Modbus device. Defaults to 1.
        label (Union[str, None], optional): Label for logging purposes.
        logger (Union[logging.Logger, None], optional): Logger instance for logging events.
        holding (bool, optional): Whether to read from holding registers (True)
            or input registers (False). Defaults to True.

    Returns:
        Union[list[int], None]: List of register values if successful, otherwise None.

    Raises:
        ModbusException: If there is an issue communicating with the Modbus device.

    Notes:
        - Logs any exceptions encountered during the operation.
        - Closes the Modbus client connection after completion.
    """
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
    """
    Read input registers data.

    Asynchronously reads data from Modbus input registers. This is a convenience wrapper around
    `modbus_read_registers` with `holding=False`.

    Args:
        con_params (SerialConnectionMinimalConfigModel): Object containing serial connection
            parameters.
        start_register (int, optional): Starting address of the register to read. Defaults to 0.
        count (int, optional): Number of registers to read. Defaults to 1.
        slave (int, optional): Slave ID of the Modbus device. Defaults to 1.
        label (Union[str, None], optional): Label for logging purposes.
        logger (Union[logging.Logger, None], optional): Logger instance for logging events.

    Returns:
        Optional[list[int]]: List of register values if successful, otherwise None.

    See Also:
        - `modbus_read_registers`: General-purpose register reader.
    """
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
    """
    Read holding registers data.

    Asynchronously reads data from Modbus holding registers. This is a convenience wrapper around
    `modbus_read_registers` with `holding=True`.

    Args:
        con_params (SerialConnectionMinimalConfigModel): Object containing serial connection
            parameters.
        start_register (int, optional): Starting address of the register to read. Defaults to 0.
        count (int, optional): Number of registers to read. Defaults to 1.
        slave (int, optional): Slave ID of the Modbus device. Defaults to 1.
        label (Union[str, None], optional): Label for logging purposes.
        logger (Union[logging.Logger, None], optional): Logger instance for logging events.

    Returns:
        Union[list[int], None]: List of register values if successful, otherwise None.

    See Also:
        - `modbus_read_registers`: General-purpose register reader.
    """
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
    """
    Write data value to registers.

    Asynchronously writes data to Modbus registers. This function connects to the Modbus device,
    sends the write request, and handles any exceptions that may arise during the process.

    Args:
        con_params (SerialConnectionMinimalConfigModel): Object containing serial connection
            parameters.
        register (int): Address of the first register to write to.
        value (List[int]): List of integer values to write to the registers.
        slave (int, optional): Slave ID of the Modbus device. Defaults to 1.
        label (Union[str, None], optional): Label for logging purposes.
        logger (Union[logging.Logger, None], optional): Logger instance for logging events.

    Returns:
        Union[list[int], None]: List of written register values if successful, otherwise None.

    Raises:
        ModbusException: If there is an issue communicating with the Modbus device.

    Notes:
        - Logs any exceptions encountered during the operation.
        - Closes the Modbus client connection after completion.
    """
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
