def sizeof_uleb128(value: int) -> int:
    """
    Get the size of an unsigned LEB128 value.
    """
    size = 0

    while True:
        size += 1
        value >>= 7

        if value == 0:
            break

    return size


def sizeof_sleb128(value: int) -> int:
    """
    Get the size of a signed LEB128 value.
    """
    size = 0

    if value >= 0:
        while value > 0x3F:
            size += 1
            value %= 0x100000000
            value >>= 7

        size += 1
    else:
        while value < -0x40:
            size += 1
            value >>= 7

        size += 1

    return size
