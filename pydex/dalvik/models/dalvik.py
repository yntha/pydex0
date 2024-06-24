from __future__ import annotations

from dataclasses import dataclass

from datastream import ByteOrder, DeserializingStream

from pydex.util import sizeof_uleb128, sizeof_sleb128


@dataclass
class DalvikRawItem:
    """
    A class that represents a low-level item in a dex file.
    """

    offset: int
    size: int
    data: bytes


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
class DalvikHeaderItem:
    """
    A class that represents the high-level header of a dex file.
    """

    raw_item: DalvikHeader
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


@dataclass
class DalvikStringID(DalvikRawItem):
    """
    A class that represents the raw string id of a dex file. Aligns to 4 bytes.

    Source:
        https://source.android.com/docs/core/runtime/dex-format#string-item
    """

    string_data_off: int  # 4 bytes
    id_number: int


@dataclass
class DalvikStringData(DalvikRawItem):
    """
    A class that represents the raw string data of a dex file.

    Source:
        https://source.android.com/docs/core/runtime/dex-format#string-data-item
    """

    utf16_size: int  # uleb128
    string_data: bytes  # mutf8 encoded


@dataclass
class DalvikStringItem:
    """
    A class that represents a high-level string data item in a dex file.
    """

    raw_item: DalvikStringData
    string_id: DalvikStringID

    @classmethod
    def from_raw_item(cls, raw_item: DalvikStringData, string_id: DalvikStringID) -> DalvikStringItem:
        """
        Create a DalvikStringItem from a DalvikStringID and DalvikStringData.

        Args:
            raw_item: The DalvikStringData that will contain the data of this item.
            string_id: The DalvikStringID.
        """

        return cls(raw_item, string_id)

    @property
    def value(self) -> str:
        """
        Get the value of the string decoded as MUTF-8.

        Returns:
            The MUTF-8 decoded string.
        """
        data = bytearray(self.raw_item.string_data)
        decoded = ""

        while len(data) > 0:
            b = data.pop(0)

            if b & 0x80 == 0x00:
                decoded += chr(b)
            elif b & 0xE0 == 0xC0:
                decoded += chr(((b & 0x1F) << 6) | (data.pop(0) & 0x3F))
            elif b & 0xF0 == 0xE0:
                decoded += chr(((b & 0x0F) << 12) | ((data.pop(0) & 0x3F) << 6) | (data.pop(0) & 0x3F))
            else:
                raise ValueError("Invalid MUTF-8 sequence")

        return decoded

    @value.setter
    def value(self, value: str):
        """
        Set the value of the dalvik string encoded as MUTF-8.

        Args:
            value: The string value to set.
        """
        encoded = bytearray()

        for char in value:
            codepoint = ord(char)

            if codepoint <= 0x7F:
                encoded.append(codepoint)
            elif codepoint <= 0x7FF:
                encoded.append(0xC0 | ((codepoint >> 6) & 0x1F))
                encoded.append(0x80 | (codepoint & 0x3F))
            elif codepoint <= 0xFFFF:
                encoded.append(0xE0 | ((codepoint >> 12) & 0x0F))
                encoded.append(0x80 | ((codepoint >> 6) & 0x3F))
                encoded.append(0x80 | (codepoint & 0x3F))
            else:
                raise ValueError("Invalid codepoint")

        self.raw_item.string_data = bytes(encoded)
        self.raw_item.utf16_size = len(encoded)

    def __str__(self) -> str:
        return self.value


@dataclass
class LazyDalvikString:
    """
    A class that represents a dalvik string which can be loaded at any time.
    """

    string_id: DalvikStringID

    def load(self, stream: DeserializingStream) -> DalvikStringItem:
        """
        Load the string from the stream.

        Args:
            stream: The DeserializingStream to read from.
        Returns:
            A loaded DalvikStringItem.
        """

        # save the current position so to not disrupt the processing flow.
        # we should NOT use stream.clone() here as this will copy the entire
        # stream for every string item which is not efficient.
        pos = stream.tell()
        stream.seek(self.string_id.string_data_off)

        offset = stream.tell()
        utf16_size = stream.read_uleb128()
        data = stream.read(utf16_size)

        leb128_size = sizeof_uleb128(utf16_size)
        item_data = stream.seekpeek(self.string_id.string_data_off, leb128_size + utf16_size)

        # restore the position
        stream.seek(pos)

        return DalvikStringItem(
            DalvikStringData(offset, sizeof_uleb128(utf16_size), item_data, utf16_size, data),
            self.string_id,
        )
