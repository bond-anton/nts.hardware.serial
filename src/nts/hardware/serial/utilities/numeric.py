"""Utility functions to convert between signed and unsigned numbers."""

from typing import Union, Tuple
from enum import Enum


class ByteOrder(Enum):
    """Byte order enumeration"""

    LITTLE_ENDIAN = "le"
    BIG_ENDIAN = "be"


def to_signed32(n: int) -> int:
    """Convert a 32-bit unsigned integer to its signed representation."""
    n &= 0xFFFFFFFF  # Ensure 32-bit
    if n & 0x80000000:
        return n - 0x100000000
    return n


def from_signed32(n: int) -> int:
    """Convert a signed 32-bit integer to its unsigned representation."""
    return n & 0xFFFFFFFF


def to_signed16(n: int) -> int:
    """Convert a 16-bit unsigned integer to its signed representation."""
    n = n & 0xFFFF  # Ensure 16-bit
    if n & 0x8000:
        return n - 0x10000
    return n


def from_signed16(n: int) -> int:
    """Convert a signed 16-bit integer to its unsigned representation."""
    return n & 0xFFFF


def float_to_int(f: float, factor: Union[int, float] = 100) -> int:
    """Convert float to integer multiplied by a factor"""
    return int(round(f * factor))


def float_to_int16(f: float, factor: Union[int, float] = 100) -> int:
    """Convert float to 16-bit integer multiplied by a factor"""
    return to_signed16(float_to_int(f, factor))


def float_to_int32(f: float, factor: Union[int, float] = 100) -> int:
    """Convert float to 32-bit integer multiplied by a factor"""
    return to_signed32(float_to_int(f, factor))


def float_to_unsigned16(f: float, factor: Union[int, float] = 100) -> int:
    """Convert float to unsigned 16-bit integer multiplied by a factor"""
    return from_signed16(float_to_int(f, factor))


def float_to_unsigned32(f: float, factor: Union[int, float] = 100) -> int:
    """Convert float to unsigned 32-bit integer multiplied by a factor"""
    return from_signed32(float_to_int(f, factor))


def float_from_int(n: int, factor: Union[int, float] = 100) -> float:
    """Convert integer to float divided by a factor"""
    if factor == 0:
        raise ValueError("Factor cannot be zero.")
    return n / factor


def float_from_unsigned16(n: int, factor: Union[int, float] = 100) -> float:
    """Convert 16-bit unsigned integer to float divided by a factor"""
    if factor == 0:
        raise ValueError("Factor cannot be zero.")
    return to_signed16(n) / factor


def float_from_unsigned32(n: int, factor: Union[int, float] = 100) -> float:
    """Convert 32-bit unsigned integer to float divided by a factor"""
    if factor == 0:
        raise ValueError("Factor cannot be zero.")
    return to_signed32(n) / factor


def split_32bit(
    n: int, byteorder: ByteOrder = ByteOrder.LITTLE_ENDIAN
) -> Tuple[int, int]:
    """Split 32-bit integer between two 16-bit values"""
    if not isinstance(n, int):
        raise TypeError("Invalid type of input")
    if byteorder == ByteOrder.BIG_ENDIAN:
        return (n & 0xFFFFFFFF) >> 16, n & 0xFFFF
    if byteorder == ByteOrder.LITTLE_ENDIAN:
        return n & 0xFFFF, (n & 0xFFFFFFFF) >> 16
    raise ValueError("Invalid byteorder value")


def combine_32bit(
    a: int, b: int, byteorder: ByteOrder = ByteOrder.LITTLE_ENDIAN
) -> int:
    """Combine 32-bit integer from two 16-bit values"""
    if not isinstance(a, int) or not isinstance(b, int):
        raise TypeError("Invalid type of input")
    if byteorder == ByteOrder.LITTLE_ENDIAN:
        return ((b & 0xFFFF) << 16) + (a & 0xFFFF)
    if byteorder == ByteOrder.BIG_ENDIAN:
        return ((a & 0xFFFF) << 16) + (b & 0xFFFF)
    raise ValueError("Invalid byteorder value")
