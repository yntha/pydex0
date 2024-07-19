class InvalidMagicNumber(Exception):
    """Exception raised for invalid magic number.

    :param magic_number: The magic number that was invalid.
    """

    def __init__(self, magic_number: bytes):
        self.magic_number = magic_number
        super().__init__(f"Invalid magic number: {magic_number.hex()}")


class InvalidChecksum(Exception):
    """Exception raised for an invalid adler32 checksum.

    :param checksum: The checksum that was invalid.
    """

    def __init__(self, checksum: int):
        self.checksum = checksum
        super().__init__(f"Invalid checksum: {checksum}")


class InvalidHeaderSize(Exception):
    """Exception raised for an invalid header size.

    :param header_size: The invalid header size.
    """

    def __init__(self, header_size: int):
        self.header_size = header_size
        super().__init__(f"Invalid header size: {header_size}")
