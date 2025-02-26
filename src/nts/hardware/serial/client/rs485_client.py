"""
RS485 Client Module.

This module provides a client implementation for communicating with Modbus devices over an RS485
serial interface. It leverages the `pymodbus` library to handle Modbus requests and responses,
offering a simple yet powerful way to interact with remote devices.

Key Features:
    - Supports asynchronous operations for efficient communication.
    - Handles common Modbus commands like reading and writing registers.
    - Facilitates logging of client activities for debugging and monitoring.

This module simplifies interaction with Modbus devices over RS485, making it easier to integrate
with industrial automation systems and IoT applications.
"""

from typing import Union, Optional
from logging import Logger, getLogger

from ..config import (
    SerialConnectionConfigModel,
    ModbusSerialConnectionConfigModel,
)
from ..utilities.modbus import (
    modbus_read_input_registers,
    modbus_read_holding_registers,
    modbus_write_registers,
)

from ..utilities.numeric import (
    ByteOrder,
    to_signed16,
    from_signed16,
    to_signed32,
    from_signed32,
    float_from_int,
    float_to_unsigned16,
    float_from_unsigned16,
    combine_32bit,
    split_32bit,
)


class RS485Client:
    """RS485 Client."""

    def __init__(
        self,
        con_params: Union[
            SerialConnectionConfigModel, ModbusSerialConnectionConfigModel
        ],
        address: int = 1,
        label: str = "RS485 Device",
        logger: Optional[Logger] = None,
    ):
        self.con_params: Union[
            SerialConnectionConfigModel, ModbusSerialConnectionConfigModel
        ] = con_params
        self.address: int = address
        self.response_delay: float = 5e-3
        self.label: str = label
        self.logger: Logger
        if logger is None:
            self.logger = getLogger()
        else:
            self.logger = logger

    async def read_registers(
        self, start_register: int = 0, count: int = 1, holding: bool = True
    ) -> Union[list[int], None]:
        """
        Read registers data using pymodbus.
        Redefine this method for custom protocol.
        """
        if holding:
            return await modbus_read_holding_registers(
                self.con_params,
                start_register=start_register,
                count=count,
                slave=self.address,
                logger=self.logger,
            )
        return await modbus_read_input_registers(
            self.con_params,
            start_register=start_register,
            count=count,
            slave=self.address,
            logger=self.logger,
        )

    async def read_register(
        self, register: int, holding: bool = True, signed: bool = False
    ) -> Union[int, None]:
        """
        Read data from single register.
        """
        response: Union[list[int], None] = await self.read_registers(
            register, count=1, holding=holding
        )
        if response:
            if signed:
                return to_signed16(response[0])
            return response[0]
        return None

    async def write_register(
        self, register: int, value: int, signed: bool = False
    ) -> Union[int, None]:
        """
        Write the data value to the register using pymodbus.
        Redefine this method for custom protocol.
        """
        if signed:
            value = from_signed16(value)

        response = await modbus_write_registers(
            self.con_params,
            register=register,
            value=[value],
            slave=self.address,
            logger=self.logger,
        )
        if response:
            if signed:
                return to_signed16(response[0])
            return response[0]
        return await self.read_register(register, holding=True, signed=signed)

    async def read_register_float(
        self,
        register: int,
        factor: int = 100,
        signed: bool = False,
        holding: bool = True,
    ) -> Union[float, None]:
        """Parse a float number from the register data value divided by provided factor"""
        response: Union[int, None] = await self.read_register(
            register, holding=holding, signed=signed
        )
        if response:
            return float_from_int(response, factor)
        return None

    async def write_register_float(
        self, register: int, value: float, factor: int = 100, signed: bool = False
    ) -> Union[float, None]:
        """Write a float number to the register multiplied by the provided factor"""
        response: Union[int, None] = await self.write_register(
            register, float_to_unsigned16(value, factor), signed=False
        )
        if response:
            if signed:
                return float_from_unsigned16(response, factor)
            return float_from_int(response, factor)
        return await self.read_register_float(register, factor, signed=signed)

    async def read_two_registers_int(
        self,
        start_register: int,
        holding: bool = True,
        byteorder: ByteOrder = ByteOrder.LITTLE_ENDIAN,
        signed: bool = False,
    ) -> Union[int, None]:
        """
        Parse a 32-bit integer number from the data split between two registers.

        Args:
            start_register (int): The starting register address to read from.
            holding (bool): If True, read from holding registers;
                            otherwise, read from input registers.
            byteorder (ByteOrder): Byte order for combining the two registers.
                                   Use `ByteOrder.LITTLE_ENDIAN` for little-endian
                                   or `ByteOrder.BIG_ENDIAN` for big-endian.
                                   Defaults to `ByteOrder.LITTLE_ENDIAN`.
            signed (bool): Converts register value to signed int.

        Returns:
            Union[int, None]: The parsed 32-bit integer, or None if the read operation
                              fails or the response does not contain exactly two registers.

        Raises:
            ValueError: If an invalid `byteorder` value is provided.
        """
        response: Union[list[int], None] = await self.read_registers(
            start_register, count=2, holding=holding
        )
        if response and len(response) == 2:
            val = combine_32bit(response[0], response[1], byteorder)
            if signed:
                return to_signed32(val)
            return val
        self.logger.debug("Invalid response: expected 2 registers, got %s", response)
        return None

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    async def read_two_registers_float(
        self,
        start_register: int,
        factor: Union[int, float] = 100,
        holding: bool = True,
        byteorder: ByteOrder = ByteOrder.LITTLE_ENDIAN,
        signed: bool = False,
    ) -> Union[float, None]:
        """
        Parse a float number from the data split between two registers.

        The integer value read from the registers is divided by `factor` to produce the result.
        For example, if the register value is 31415 and `factor` is 100, the result is 314.15.

        Args:
            start_register (int): The starting register address to read from.
            factor (int/float): The divisor used to scale the integer value into a float.
                                Must not be zero. Defaults to 100.
            holding (bool): If True, read from holding registers;
                            otherwise, read from input registers.
            byteorder (ByteOrder): Byte order for combining the two registers.
                                   Use `ByteOrder.LITTLE_ENDIAN` for little-endian
                                   or `ByteOrder.BIG_ENDIAN` for big-endian.
                                   Defaults to `ByteOrder.LITTLE_ENDIAN`.
            signed (bool): Converts register value to signed int before conversion.

        Returns:
            Union[float, None]: The parsed float, or None if the read operation fails.

        Raises:
            ValueError: If `factor` is zero.
        """
        if factor == 0:
            raise ValueError("Factor cannot be zero.")
        response: Union[int, None] = await self.read_two_registers_int(
            start_register, holding=holding, byteorder=byteorder, signed=signed
        )
        if response is not None:
            return float_from_int(response, factor)
        self.logger.debug("Failed to read registers for float conversion.")
        return None

    async def write_two_registers(
        self,
        start_register: int,
        value: int,
        byteorder: ByteOrder = ByteOrder.LITTLE_ENDIAN,
        signed: bool = False,
    ) -> Union[int, None]:
        """
        Write the data value to the register using pymodbus.
        Redefine this method for custom protocol.
        """
        if signed:
            value = from_signed32(value)
        value_a, value_b = split_32bit(value, byteorder)
        response = await modbus_write_registers(
            self.con_params,
            register=start_register,
            value=[value_a, value_b],
            slave=self.address,
            logger=self.logger,
        )
        if response and len(response) == 2:
            val = combine_32bit(response[0], response[1], byteorder)
            if signed:
                return to_signed32(val)
            return val
        return await self.read_two_registers_int(
            start_register=start_register,
            holding=True,
            byteorder=byteorder,
            signed=signed,
        )
