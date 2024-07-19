from __future__ import annotations

import asyncio
import struct
import typing
import zlib

from dataclasses import dataclass

from datastream import DeserializingStream, ByteOrder

from pydex.dalvik.models import DalvikHeader, DalvikHeaderItem, LazyDalvikString, DalvikStringID, DalvikStringItem


@dataclass
class DexPool:
    """A container for managing a collection of DexFile instances.

    This class provides a centralized structure for storing and managing multiple DexFile objects,
    allowing for operations that need to interact with or manipulate multiple dex files simultaneously.
    It is particularly useful in scenarios where dex files need to be aggregated for analysis,
    modification, or querying in a unified manner.
    """

    dex_files: list[DexFile]  #: The list of dex files that are managed by this pool.


class DexFile:
    """Represents a Dex file and provides methods to parse and manipulate it.

    This class encapsulates the functionality required to parse and interact with
    the contents of a Dex (Dalvik Executable) file. It provides methods to parse
    the file both synchronously and asynchronously.

    :param data: The raw bytes of the dex file.
    """

    def __init__(self, data: bytes):
        #: The raw bytes of the dex file.
        self.data: bytes = data

        #: The stream used to read the dex file.
        self.stream: DeserializingStream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

        #: The header of the dex file.
        self.header: DalvikHeaderItem = typing.cast(DalvikHeaderItem, None)

        #: The list of dalvik string items in the dex file.
        self.strings: list[LazyDalvikString] = []

    @classmethod
    def from_path(cls, path: str) -> DexFile:
        """
        Create a DexFile object from a file path.

        :param path: The path to the dex file.
        """

        with open(path, "rb") as f:
            return cls(f.read())

    def parse_dex_prologue(self) -> typing.Self:
        """
        Helper function that does misc startup tasks for parsing the dex file.

        :raises ValueError: If the endian tag is invalid.
        """

        # reset the stream in case it was read from before
        self.stream.seek(0)

        # get the byte order of the dex file
        # it is at 8 + 4 + 20 + 4 + 4 = 40
        endian_tag = int.from_bytes(self.stream.seekpeek(40, 4))

        if endian_tag == 0x12345678:
            self.stream.byteorder = ByteOrder.BIG_ENDIAN
        elif endian_tag == 0x78563412:
            self.stream.byteorder = ByteOrder.LITTLE_ENDIAN
        else:
            raise ValueError("Invalid endian tag")

        # parse the header
        self.header = self.parse_header()

        return self

    def parse_dex(self) -> typing.Self:
        """Parse the DEX file.

        This function will attempt to entirely parse this DEX file in one go and fill in all the uninitialized class
        attributes.
        """

        self.parse_dex_prologue()

        # collect all the dalvik string items as LazyDalvikStrings
        self.strings = self.parse_strings()

        return self

    def parse_header(self) -> DalvikHeaderItem:
        r"""
        Parse the header of the dex file.

        Raises:
            ValueError:
                - If the first 4 bytes don't match ``dex\x0A``.
                - If the checksum is invalid.
                - If the header size is not ``0x70``.
                - If the type ids size is greater than or equal to ``0xFFFF``.
                - If the proto ids size is greater than or equal to ``0xFFFF``.
                - If the data size is not divisible by the size of an unsigned integer.
        """

        clonestream = self.stream.clone()

        # get the magic bytes
        magic = clonestream.read(8)

        # the magic bytes are not constant, as they contain a version number
        # dex\0x0Axxx\x00, where xxx is the version number(zero padded).
        if magic[:4] != b"dex\x0A":
            raise ValueError("Invalid magic bytes")

        if magic[7] != 0:
            raise ValueError("Invalid magic bytes")

        # get the checksum
        checksum = clonestream.read_uint32()

        # verify the checksum. the checksum applies to the entire file except
        # the magic bytes and this field, so 8 bytes + 4 bytes = 12 bytes to
        # skip.
        if checksum != zlib.adler32(self.data[12:]):
            raise ValueError(f"Invalid checksum: {checksum}")

        # get the sha-1 signature bytes(fingerprint)
        signature = clonestream.read(20)

        # get the file size
        file_size = clonestream.read_uint32()

        # get the header size
        header_size = clonestream.read_uint32()

        # according to the spec, this should always be == 0x70
        if header_size != 0x70:
            raise ValueError(f"Invalid header size: {header_size}")

        # get the endian tag
        endian_tag = clonestream.read_uint32()

        # get the link size
        link_size = clonestream.read_uint32()

        # get the link offset
        link_off = clonestream.read_uint32()

        # get the map offset
        map_off = clonestream.read_uint32()

        # get the string ids size
        string_ids_size = clonestream.read_uint32()

        # get the string ids offset
        string_ids_off = clonestream.read_uint32()

        # get the type ids size
        type_ids_size = clonestream.read_uint32()

        # according to the spec, this should always be <= 0xFFFF
        if type_ids_size >= 0xFFFF:
            raise ValueError(f"Invalid type ids size: {type_ids_size}")

        # get the type ids offset
        type_ids_off = clonestream.read_uint32()

        # get the proto ids size
        proto_ids_size = clonestream.read_uint32()

        # according to the spec, this should always be <= 0xFFFF
        if proto_ids_size >= 0xFFFF:
            raise ValueError(f"Invalid proto ids size: {proto_ids_size}")

        # get the proto ids offset
        proto_ids_off = clonestream.read_uint32()

        # get the field ids size
        field_ids_size = clonestream.read_uint32()

        # get the field ids offset
        field_ids_off = clonestream.read_uint32()

        # get the method ids size
        method_ids_size = clonestream.read_uint32()

        # get the method ids offset
        method_ids_off = clonestream.read_uint32()

        # get the class defs size
        class_defs_size = clonestream.read_uint32()

        # get the class defs offset
        class_defs_off = clonestream.read_uint32()

        # get the data size
        data_size = clonestream.read_uint32()

        # this field should be divisible by sizeof(uint)
        if data_size % struct.calcsize("I") != 0:
            raise ValueError(f"Invalid data size: {data_size}")

        # get the data offset
        data_off = clonestream.read_uint32()

        return DalvikHeaderItem.from_raw_item(
            DalvikHeader(
                offset=0,
                size=header_size,
                data=self.data[:0x70],
                magic=magic,
                checksum=checksum,
                signature=signature,
                file_size=file_size,
                header_size=header_size,
                endian_tag=endian_tag,
                link_size=link_size,
                link_off=link_off,
                map_off=map_off,
                string_ids_size=string_ids_size,
                string_ids_off=string_ids_off,
                type_ids_size=type_ids_size,
                type_ids_off=type_ids_off,
                proto_ids_size=proto_ids_size,
                proto_ids_off=proto_ids_off,
                field_ids_size=field_ids_size,
                field_ids_off=field_ids_off,
                method_ids_size=method_ids_size,
                method_ids_off=method_ids_off,
                class_defs_size=class_defs_size,
                class_defs_off=class_defs_off,
                data_size=data_size,
                data_off=data_off,
            )
        )

    async def parse_header_async(self) -> DalvikHeaderItem:
        r"""
        Parse the header of the dex file.

        Raises:
            ValueError:
                - If the first 4 bytes don't match ``dex\x0A``.
                - If the checksum is invalid.
                - If the header size is not ``0x70``.
                - If the type ids size is greater than or equal to ``0xFFFF``.
                - If the proto ids size is greater than or equal to ``0xFFFF``.
                - If the data size is not divisible by the size of an unsigned integer.
        """

        return await asyncio.to_thread(self.parse_header)

    def parse_strings(self) -> list[LazyDalvikString]:
        """Collect all the dalvik string items.

        This function collects all the dalvik string items in this DEX file and returns them as a list of
        ``LazyDalvikString``. A clone stream is used so to not alter the DEX file stream.
        """

        if self.header is None:
            self.parse_dex_prologue()

        lazy_strings = []
        clonestream = self.stream.clone()

        for i in range(self.header.raw_item.string_ids_size):
            clonestream.seek(self.header.raw_item.string_ids_off + i * 4)
            string_id_off = clonestream.tell()

            string_data_off = clonestream.read_uint32()
            clonestream.seek(string_data_off)

            lazy_strings.append(
                LazyDalvikString(
                    DalvikStringID(
                        offset=string_id_off,
                        size=4,
                        data=self.data[string_id_off : string_id_off + 4],
                        string_data_off=string_data_off,
                        id_number=i,
                    )
                )
            )

        return lazy_strings

    async def parse_strings_async(self) -> list[LazyDalvikString]:
        """Collect all the dalvik string items.

        This function collects all the dalvik string items in this DEX file and returns them as a list of
        ``LazyDalvikString``. A clone stream is used so to not alter the DEX file stream.
        """

        return await asyncio.to_thread(self.parse_strings)

    def load_all_strings(self) -> list[DalvikStringItem]:
        """Load all the dalvik string items asynchronously.

        This function invokes the ``load()`` function for all the lazy dalvik strings in the :attr:`strings` attribute.
        It will also convert every model in :attr:`strings` to a loaded ``DalvikStringItem`` model.
        """

        strings = []

        for lazy_string in self.strings:
            strings.append(lazy_string.load(self.stream))

        return strings

    async def load_all_strings_async(self) -> list[DalvikStringItem]:
        """Load all the dalvik string items asynchronously.

        This function invokes the ``load()`` function for all the lazy dalvik strings in the ``strings`` attribute. It
        will also convert every model in ``strings`` to a loaded ``DalvikStringItem`` model.
        """

        return await asyncio.to_thread(self.load_all_strings)

    def get_string_by_id(self, string_id: int) -> LazyDalvikString:
        """Get a dalvik string by its id.

        Get a dalvik string by its id. The difference between this, and
        `dex.strings[id]` is that this method does not require all the strings
        to be collected from the dex file. This method is useful when you only
        need a single string from the dex file and don't want to load the
        entire dex file with `parse_dex`.

        :param string_id: The id of the string to get. IDs are 0-indexed, and are
            assigned in the order they appear in the dex file.
        """

        if self.header is None:
            self.parse_dex_prologue()

        if len(self.strings) > 0:
            return self.strings[string_id]

        clonestream = self.stream.clone()
        clonestream.seek(self.header.raw_item.string_ids_off + string_id * 4)

        string_id_off = clonestream.tell()
        string_data_off = clonestream.read_uint32()

        return LazyDalvikString(
            DalvikStringID(
                offset=string_id_off,
                size=4,
                data=self.data[string_id_off : string_id_off + 4],
                string_data_off=string_data_off,
                id_number=string_id,
            )
        )
