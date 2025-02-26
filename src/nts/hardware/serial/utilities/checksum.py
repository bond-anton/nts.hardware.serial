"""Serial communication helper functions."""


def check_sum(payload: bytes) -> int:
    """Calculate CRC-16/MODBUS checksum for the payload data."""
    cs = 0xFFFF
    for data_byte in payload:
        cs ^= data_byte
        for _ in range(8):
            if cs & 0x0001:
                cs = (cs >> 1) ^ 0xA001
            else:
                cs = cs >> 1
    return cs


def lrc(payload: bytes) -> int:
    """Calculate LRC for the payload data."""
    cs: int = 0
    for data_byte in payload:
        cs += int(data_byte)
    cs = ((cs ^ 0xFF) + 1) & 0xFF
    return cs


def check_lrc(message: bytes) -> bool:
    """Check LRС byte at the end of the message."""
    try:
        cs: int = message[-1]
        payload: bytes = message[:-1]
        if lrc(payload) == cs:
            return True
    except IndexError:
        pass
    return False
