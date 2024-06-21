from __future__ import annotations

import typing
import zlib

from dataclasses import dataclass

from datastream import ByteOrder


@dataclass
class DalvikRawItem:
    """
    A class that represents a low-level item in a dex file.
    """

    offset: int
    size: int
    data: bytes


@dataclass
class DalvikItem:
    """
    A class that represents a high-level item in a dex file.
    """

    raw_item: DalvikRawItem


@dataclass
class DalvikHeader(DalvikRawItem):
    """
    A class that represents the raw header of a dex file.

    Source:
        https://source.android.com/docs/core/runtime/dex-format#header-item
    """

    magic: bytes  # 8 bytes
    checksum: int  # 4 bytes
    signature: bytes  # 20 bytes
    file_size: int  # 4 bytes
    header_size: int  # 4 bytes
    endian_tag: int  # 4 bytes
    link_size: int  # 4 bytes
    link_off: int  # 4 bytes
    map_off: int  # 4 bytes
    string_ids_size: int  # 4 bytes
    string_ids_off: int  # 4 bytes
    type_ids_size: int  # 4 bytes
    type_ids_off: int  # 4 bytes
    proto_ids_size: int  # 4 bytes
    proto_ids_off: int  # 4 bytes
    field_ids_size: int  # 4 bytes
    field_ids_off: int  # 4 bytes
    method_ids_size: int  # 4 bytes
    method_ids_off: int  # 4 bytes
    class_defs_size: int  # 4 bytes
    class_defs_off: int  # 4 bytes
    data_size: int  # 4 bytes
    data_off: int  # 4 bytes


@dataclass
class DalvikHeaderItem(DalvikItem):
    """
    A class that represents the high-level header of a dex file.
    """

    version: int
    checksum: int
    signature: bytes
    file_size: int
    byte_order: ByteOrder

    @classmethod
    def from_raw_item(cls, raw_item: DalvikHeader) -> DalvikHeaderItem:
        """
        Create a DalvikHeaderItem from a DalvikRawItem.
        """

        version = int(raw_item.magic[4:7])
        checksum = raw_item.checksum
        signature = raw_item.signature
        file_size = raw_item.file_size

        if raw_item.endian_tag == 0x12345678:
            byte_order = ByteOrder.LITTLE_ENDIAN
        elif raw_item.endian_tag == 0x78563412:
            byte_order = ByteOrder.BIG_ENDIAN
        else:
            raise ValueError("Invalid endian tag")

        return cls(raw_item, version, checksum, signature, file_size, byte_order)
