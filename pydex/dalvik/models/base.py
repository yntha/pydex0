from dataclasses import dataclass


@dataclass
class DalvikRawItem:
    """
    A dataclass that represents a low-level item in a dex file.
    """

    #: The offset of the item in the dex file.
    offset: int

    #: The size of the item in the dex file.
    size: int

    #: The raw data of the item.
    data: bytes
