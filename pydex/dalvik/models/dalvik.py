from __future__ import annotations

import asyncio

from dataclasses import dataclass
from typing import ClassVar

from datastream import ByteOrder, DeserializingStream

from pydex.util import sizeof_uleb128
from pydex.exc import InvalidDalvikHeader


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


@dataclass
class DalvikHeader(DalvikRawItem):
    """
    A dataclass that represents the raw ``header_item`` of a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::header_item <https://source.android.com/docs/core/runtime/dex-format#header-item>`_
    """

    struct_size: ClassVar[int] = 0x70

    #: Magic value.
    magic: bytes  # 8 bytes

    #: Adler32 checksum of the rest of the file (everything but magic and this field).
    #: Used to detect file corruption.
    checksum: int  # 4 bytes

    #: SHA-1 hash of the rest of the file (everything but magic, checksum, and this field).
    #: Used to uniquely identify the file.
    signature: bytes  # 20 bytes

    #: Size of the entire file (including the header), in bytes.
    file_size: int  # 4 bytes

    #: Header size in bytes. This value should be ``0x70``.
    header_size: int  # 4 bytes

    #: Endian tag. The value should be either ``0x12345678`` or ``0x78563412``.
    endian_tag: int  # 4 bytes

    #: Size of the link section.
    link_size: int  # 4 bytes

    #: Offset from the start of the file to the link section.
    link_off: int  # 4 bytes

    #: Offset from the start of the file to the map section.
    map_off: int  # 4 bytes

    #: Size of the string identifiers list.
    string_ids_size: int  # 4 bytes

    #: Offset from the start of the file to the string identifiers list.
    string_ids_off: int  # 4 bytes

    #: Size of the type identifiers list.
    type_ids_size: int  # 4 bytes

    #: Offset from the start of the file to the type identifiers list.
    type_ids_off: int  # 4 bytes

    #: Size of the prototype identifiers list.
    proto_ids_size: int  # 4 bytes

    #: Offset from the start of the file to the prototype identifiers list.
    proto_ids_off: int  # 4 bytes

    #: Size of the field identifiers list.
    field_ids_size: int  # 4 bytes

    #: Offset from the start of the file to the field identifiers list.
    field_ids_off: int  # 4 bytes

    #: Size of the method identifiers list.
    method_ids_size: int  # 4 bytes

    #: Offset from the start of the file to the method identifiers list.
    method_ids_off: int  # 4 bytes

    #: Size of the class definitions list.
    class_defs_size: int  # 4 bytes

    #: Offset from the start of the file to the class definitions list.
    class_defs_off: int  # 4 bytes

    #: Size of the data section.
    data_size: int  # 4 bytes

    #: Offset from the start of the file to the data section.
    data_off: int  # 4 bytes


@dataclass
class DalvikHeaderItem:
    """
    A dataclass that represents the high-level ``header_item`` of a dex file.
    """

    #: The raw header item.
    raw_item: DalvikHeader

    #: The version of the dex file.
    version: int

    #: The adler32 checksum of the dex file.
    checksum: int

    #: The unique SHA-1 fingerprint of the dex file.
    signature: bytes

    #: The size of the dex file in bytes.
    file_size: int

    #: The byte order of the dex file.
    byte_order: ByteOrder

    @classmethod
    def from_raw_item(cls, raw_item: DalvikHeader) -> DalvikHeaderItem:
        """
        Create a ``DalvikHeaderItem`` from a ``DalvikHeader``.

        Args:
            DalvikHeader raw_item: The ``DalvikHeader`` that contains the primitive data for this item.

        Raises:
            InvalidDalvikHeader: If ``endian_tag`` is invalid.
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
            raise InvalidDalvikHeader("Invalid endian tag", InvalidDalvikHeader.INVALID_ENDIAN_TAG)

        return cls(raw_item, version, checksum, signature, file_size, byte_order)

    def __str__(self) -> str:
        return (
            f"Version: {self.version},\n"
            f"File Size: {self.file_size},\n"
            f"Checksum: {self.checksum},\n"
            f"Signature: {self.signature.hex()}"
        )


@dataclass
class DalvikStringID(DalvikRawItem):
    """
    A dataclass that represents a raw ``string_id_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::string_id_item <https://source.android.com/docs/core/runtime/dex-format#string-item>`_
    """

    struct_size: ClassVar[int] = 0x04

    #: Offset from the start of the file to the string data.
    string_data_off: int  # 4 bytes

    #: The index of the string in the string table. This field is not part of
    #: the dex file format.
    id_number: int


@dataclass
class DalvikStringData(DalvikRawItem):
    """
    A dataclass that represents a raw ``string_data_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::string_data_item <https://source.android.com/docs/core/runtime/dex-format#string-data-item>`_
    """

    struct_size: ClassVar[int] = 0x00

    #: Size of the string in UTF-16 code units.
    utf16_size: int  # uleb128

    #: The raw string data.
    string_data: bytes  # mutf8 encoded


@dataclass
class DalvikStringItem:
    """
    A dataclass that represents a high-level ``string_data_item`` in a dex file.
    """

    #: The raw string data item.
    raw_item: DalvikStringData

    #: The raw string id item.
    string_id: DalvikStringID

    _value: str = ""

    @classmethod
    def from_raw_item(cls, raw_item: DalvikStringData, string_id: DalvikStringID) -> DalvikStringItem:
        """
        Create a ``DalvikStringItem`` from a ``DalvikStringID`` and ``DalvikStringData``.

        Args:
            DalvikStringData raw_item: The ``DalvikStringData`` that will contain the data of this item.
            DalvikStringID string_id: The ``DalvikStringID``.
        """

        return cls(raw_item, string_id)

    @property
    def value(self) -> str:
        """
        Get the value of the string decoded as MUTF-8.

        Raises:
            ValueError: If an invalid MUTF-8 sequence is encountered.

        Returns:
            The MUTF-8 decoded string.
        """
        # check if the value is already decoded
        if self._value:
            return self._value

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

        self._value = decoded

        return decoded

    @value.setter
    def value(self, value: str):
        """
        Set the value of the dalvik string encoded as MUTF-8.

        Raises:
            ValueError: If an invalid codepoint is encountered.

        Args:
            str value: The string value to set.
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

    async def get_value_async(self) -> str:
        """
        Get the value of the string decoded as MUTF-8 asynchronously.

        Returns:
            The MUTF-8 decoded string.
        """

        return await asyncio.to_thread(self.__class__.value.fget)

    async def set_value_async(self, value: str):
        """
        Set the value of the dalvik string encoded as MUTF-8 asynchronously.

        Args:
            str value: The string value to set.
        """

        return await asyncio.to_thread(self.__class__.value.fset, value)

    def __str__(self) -> str:
        return self.value


@dataclass
class LazyDalvikString:
    """
    A dataclass that represents a dalvik string which can be loaded at any time.
    """

    string_id: DalvikStringID

    def load(self, stream: DeserializingStream) -> DalvikStringItem:
        """
        Load the string from the stream.

        Args:
            DeserializingStream stream: The ``DeserializingStream`` to read from.
        Returns:
            A loaded ``DalvikStringItem``.
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
            DalvikStringData(offset, sizeof_uleb128(utf16_size) + len(data), item_data, utf16_size, data),
            self.string_id,
        )

    async def load_async(self, stream: DeserializingStream) -> DalvikStringItem:
        """
        Load the string from the stream asynchronously.
        Args:
            DeserializingStream stream: The ``DeserializingStream`` to read from.

        Returns: A loaded ``DalvikStringItem``.
        """

        return await asyncio.to_thread(self.load, stream)


@dataclass
class DalvikTypeID(DalvikRawItem):
    """
    A dataclass that represents a raw ``type_id_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::type_id_item <https://source.android.com/docs/core/runtime/dex-format#type-id-item>`_
    """

    struct_size: ClassVar[int] = 0x04

    #: Index into the ``string_ids`` list for the descriptor string of this type.
    descriptor_idx: int  # 4 bytes

    #: The index number of this type. This field is not part of the dex file format.
    id_number: int


@dataclass
class DalvikTypeItem:
    """
    A dataclass that represents a high-level ``type_id_item`` in a dex file.
    """

    #: The raw type id item.
    raw_item: DalvikTypeID

    #: The raw string item.
    descriptor: DalvikStringItem | LazyDalvikString

    @classmethod
    def from_raw_item(
        cls, raw_item: DalvikTypeID, strings: list[DalvikStringItem | LazyDalvikString]
    ) -> DalvikTypeItem:
        """
        Create a ``DalvikTypeItem`` from a ``DalvikTypeID``.

        Args:
            DalvikTypeID raw_item: The ``DalvikTypeID`` that will contain the data of this item.
            list[DalvikStringItem | LazyDalvikString] strings: The list of string items.
        """

        return cls(raw_item, strings[raw_item.descriptor_idx])

    def __str__(self) -> str:
        return self.descriptor.value


@dataclass
class DalvikProtoID(DalvikRawItem):
    """
    A dataclass that represents a ``proto_id_item`` found in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::proto_id_item <https://source.android.com/docs/core/runtime/dex-format#proto-id-item>`_
    """

    struct_size: ClassVar[int] = 0x0C

    #: Index into the ``string_ids list`` for the short-form descriptor string of this prototype.
    shorty_idx: int  # 4 bytes

    #: Index into the ``type_ids`` list for the return type of this prototype.
    return_type_idx: int  # 4 bytes

    #: Offset from the start of the file to the list of parameter types for this prototype, or 0 if this prototype has
    #: no parameters.
    parameters_off: int  # 4 bytes

    #: The index number of this prototype. This field is not part of the dex file format.
    id_number: int


@dataclass
class DalvikTypeList(DalvikRawItem):
    """
    A dataclass that represents a ``type_list`` item found in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::type_list <https://source.android.com/docs/core/runtime/dex-format#type-list>`_
    """

    struct_size: ClassVar[int] = 0x00

    #: Size of the list, in entries. Renamed from ``size`` to avoid shadowing.
    length: int  # 4 bytes

    #: Elements of the list. Renamed from ``list`` to avoid shadowing.
    entries: list[DalvikTypeID]


@dataclass
class DalvikTypeListItem:
    """
    A dataclass that represents a high-level ``type_list`` item in a dex file.
    """

    #: The raw type list item.
    raw_item: DalvikTypeList

    #: The list of type items.
    types: list[DalvikTypeItem]

    @classmethod
    def from_raw_item(cls, raw_item: DalvikTypeList, types: list[DalvikTypeItem]) -> DalvikTypeListItem:
        """
        Create a ``DalvikTypeListItem`` from a ``DalvikTypeList``.

        Args:
            DalvikTypeList raw_item: The ``DalvikTypeList`` instance that will contain the data of
                this item.
            list[DalvikTypeItem] types: The complete list of types in the dex file.
        """

        referenced_types = [types[type_id.id_number] for type_id in raw_item.entries]

        return cls(raw_item, referenced_types)

    def __str__(self) -> str:
        return ", ".join(str(type_item) for type_item in self.types)


@dataclass
class DalvikProtoIDItem:
    """
    A dataclass that represents a high-level ``proto_id_item`` in a dex file.
    """

    #: The raw prototype id item.
    raw_item: DalvikProtoID

    #: The shorty string item.
    shorty: DalvikStringItem | LazyDalvikString

    #: The return type of the prototype.
    return_type: DalvikTypeItem

    #: The list of parameter types for this prototype.
    parameters: DalvikTypeListItem | None

    #: String list of parameters
    parameter_list: list[str] | None

    @classmethod
    def from_raw_item(
        cls,
        raw_item: DalvikProtoID,
        shorty: DalvikStringItem | LazyDalvikString,
        return_type: DalvikTypeItem,
        parameters: DalvikTypeListItem | None,
    ) -> DalvikProtoIDItem:
        """
        Create a ``DalvikProtoIDItem`` from a ``DalvikProtoID``.

        Args:
            DalvikProto raw_item: The ``DalvikProtoID`` instance that will contain the data of this item.
            DalvikStringItem | LazyDalvikString shorty: The shorty string item.
            DalvikTypeItem return_type: The return type item.
            DalvikTypeListItem parameters: The list of parameter type items.
        """

        if parameters is not None:
            string_list = []

            for type_item in parameters.types:
                string_list.append(str(type_item))
        else:
            string_list = None

        return cls(raw_item, shorty, return_type, parameters, string_list)

    def __str__(self) -> str:
        if self.parameters is not None:
            param_list = ", ".join(str(param) for param in self.parameters.types)
        else:
            param_list = ""

        return f"({param_list}){self.return_type.descriptor.value}"


@dataclass
class DalvikField(DalvikRawItem):
    """
    A dataclass that represents a ``field_id_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::field_id_item <https://source.android.com/docs/core/runtime/dex-format#field-id-item>`_
    """

    struct_size: ClassVar[int] = 0x08

    #: Index into the ``type_ids`` list for the definer of this field.
    class_idx: int  # 2 bytes

    #: Index into the ``type_ids`` list for the type of this field.
    type_idx: int  # 2 bytes

    #: Index into the ``string_ids`` list for the name of this field.
    name_idx: int  # 4 bytes

    #: The index number of this field. This field is not part of the dex file format.
    id_number: int


@dataclass
class DalvikFieldItem:
    """
    A dataclass that represents a high-level ``field_id_item`` in a dex file.
    """

    #: The raw ``field_id_item``.
    raw_item: DalvikField

    #: The class this field belongs to.
    class_def: DalvikTypeItem

    #: The type of the field.
    type: DalvikTypeItem

    #: The name of the field.
    name: DalvikStringItem

    @classmethod
    def from_raw_item(
        cls,
        raw_item: DalvikField,
        types: list[DalvikTypeItem],
        strings: list[DalvikStringItem],
    ) -> DalvikFieldItem:
        """
        Create a ``DalvikFieldItem`` from a ``DalvikField``

        Args:
            DalvikField raw_item: The ``DalvikField`` instance that will contain the data of this item.
            list[DalvikTypeItem] types: The list of type items.
            list[DalvikStringItem] strings: The list of string items.
        """

        return cls(raw_item, types[raw_item.class_idx], types[raw_item.type_idx], strings[raw_item.name_idx])

    def __str__(self) -> str:
        return f"{self.class_def}->{self.name}:{self.type}"


@dataclass
class DalvikMethod(DalvikRawItem):
    """
    A dataclass that represents a ``method_id_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::method_id_item <https://source.android.com/docs/core/runtime/dex-format#method-id-item>`_
    """

    struct_size: ClassVar[int] = 0x08

    #: Index into the ``type_ids`` list for the definer of this method.
    class_idx: int  # 2 bytes

    #: Index into the ``proto_ids`` list for the prototype of this method.
    proto_idx: int  # 2 bytes

    #: Index into the ``string_ids`` list for the name of this method.
    name_idx: int  # 4 bytes

    #: The index number of this method. This field is not part of the dex file format.
    id_number: int


@dataclass
class DalvikMethodItem:
    """
    A dataclass that represents a high-level ``method_id_item`` in a dex file.
    """

    #: The raw ``method_id_item``.
    raw_item: DalvikMethod

    #: The class this method belongs to.
    class_def: DalvikTypeItem

    #: The prototype of the method.
    proto: DalvikProtoIDItem

    #: The name of the method.
    name: DalvikStringItem

    @classmethod
    def from_raw_item(
        cls,
        raw_item: DalvikMethod,
        types: list[DalvikTypeItem],
        protos: list[DalvikProtoIDItem],
        strings: list[DalvikStringItem],
    ) -> DalvikMethodItem:
        """
        Create a ``DalvikMethodItem`` from a ``DalvikMethod``.

        Args:
            DalvikMethod raw_item: The ``DalvikMethod`` instance that will contain the data of this item.
            list[DalvikTypeItem] types: The list of type items.
            list[DalvikProtoIDItem] protos: The list of prototype items.
            list[DalvikStringItem] strings: The list of string items.
        """

        return cls(raw_item, types[raw_item.class_idx], protos[raw_item.proto_idx], strings[raw_item.name_idx])

    def __str__(self) -> str:
        return f"{self.class_def}->{self.name}{self.proto}"
