class InvalidDalvikHeader(Exception):
    """Exception raised when the parser encounters an invalid Dalvik header.

    A number of codes exist as class attributes in this class which represent
    the reason for the exception. These codes exist so that multiple exception
    classes don't have to be created for each possible reason.
    """

    #: The magic bytes of the header are invalid.
    INVALID_MAGIC_BYTES = 0

    #: The checksum of the header does not match the calculated checksum.
    INVALID_CHECKSUM = 1

    #: The endian tag of the header representing byte order is invalid.
    INVALID_ENDIAN_TAG = 2

    #: The size of the header is not ``0x70``.
    INVALID_HEADER_SIZE = 3

    #: The ``proto_ids_size`` is greater than or equal to ``0xFFFF``.
    INVALID_PROTOS_SIZE = 4

    #: The ``type_ids_size`` is greater than or equal to ``0xFFFF``.
    INVALID_TYPES_SIZE = 5

    #: The ``data_size`` is not divisible by the size of a word.
    INVALID_DATA_SIZE = 6

    def __init__(self, message: str, code: int):
        #: The message of the exception.
        self.message = message

        #: The code of the exception.
        self.code = code

        super().__init__(self.message)
