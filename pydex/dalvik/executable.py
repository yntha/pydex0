from __future__ import annotations

import struct
import typing
import zlib

from dataclasses import dataclass

from datastream import DeserializingStream, ByteOrder

from pydex.dalvik.models import DalvikHeader, DalvikHeaderItem, LazyDalvikString, DalvikStringID, DalvikStringItem


@dataclass
class DexPool:
    """
    A class that holds a pool of dex files.
    """

    dex_files: list[DexFile]


class DexFile:
    def __init__(self, data: bytes):
        self.data = data
        self.stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

        self.header: DalvikHeaderItem = typing.cast(DalvikHeaderItem, None)
        self.strings: list[LazyDalvikString] = []

    @classmethod
    def from_path(cls, path: str) -> DexFile:
        """
        Create a DexFile object from a file path.
        """

        with open(path, "rb") as f:
            return cls(f.read())

    def parse_dex(self) -> typing.Self:
        """
        Parse the dex file.
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

        # collect all the dalvik string items as LazyDalvikStrings
        self.strings = self.parse_strings()

        return self

    def parse_header(self) -> DalvikHeaderItem:
        """
        Parse the header of the dex file.
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

    def parse_strings(self) -> list[LazyDalvikString]:
        """
        Collect all the dalvik string items.

        Returns: The dalvik string items as LazyDalvikStrings.
        """

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

    def load_all_strings(self) -> list[DalvikStringItem]:
        """
        Load all the dalvik string items.

        Returns: All the dalvik string items for this dex file.
        """

        strings = []

        for lazy_string in self.strings:
            strings.append(lazy_string.load(self.stream))

        return strings
