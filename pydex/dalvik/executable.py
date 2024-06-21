from __future__ import annotations

import hashlib
import struct
import typing
import zlib

from datastream import DeserializingStream, ByteOrder

from pydex.dalvik.models import DalvikHeader, DalvikHeaderItem


class DexFile:
    def __init__(self, data: bytes):
        self.data = data
        self.stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

        self.header = None

    def parse_header(self) -> DalvikHeaderItem:
        """
        Parse the header of the dex file.
        """

        # get the magic bytes
        magic = self.stream.read(8)

        # the magic bytes are not constant, as they contain a version number
        # dex\0x0Axxx\x00, where xxx is the version number(zero padded).
        if magic[:4] != b"dex\x0A":
            raise ValueError("Invalid magic bytes")

        if magic[7] != 0:
            raise ValueError("Invalid magic bytes")

        # get the checksum
        checksum = self.stream.read_uint32()

        # verify the checksum. the checksum applies to the entire file except
        # the magic bytes and this field, so 8 bytes + 4 bytes = 12 bytes to
        # skip.
        if checksum != zlib.adler32(self.data[12:]):
            raise ValueError("Invalid checksum")

        # get the sha-1 signature bytes(fingerprint)
        signature = self.stream.read(20)

        # get the file size
        file_size = self.stream.read_uint32()

        # get the header size
        header_size = self.stream.read_uint32()

        # according to the spec, this should always be == 0x70
        if header_size != 0x70:
            raise ValueError("Invalid header size")

        # get the endian tag
        endian_tag = self.stream.read_uint32()

        # get the link size
        link_size = self.stream.read_uint32()

        # get the link offset
        link_off = self.stream.read_uint32()

        # get the map offset
        map_off = self.stream.read_uint32()

        # get the string ids size
        string_ids_size = self.stream.read_uint32()

        # get the string ids offset
        string_ids_off = self.stream.read_uint32()

        # get the type ids size
        type_ids_size = self.stream.read_uint32()

        # according to the spec, this should always be == 0xFFFF
        if type_ids_size != 0xFFFF:
            raise ValueError("Invalid type ids size")

        # get the type ids offset
        type_ids_off = self.stream.read_uint32()

        # get the proto ids size
        proto_ids_size = self.stream.read_uint32()

        # according to the spec, this should always be == 0xFFFF
        if proto_ids_size != 0xFFFF:
            raise ValueError("Invalid proto ids size")

        # get the proto ids offset
        proto_ids_off = self.stream.read_uint32()

        # get the field ids size
        field_ids_size = self.stream.read_uint32()

        # get the field ids offset
        field_ids_off = self.stream.read_uint32()

        # get the method ids size
        method_ids_size = self.stream.read_uint32()

        # get the method ids offset
        method_ids_off = self.stream.read_uint32()

        # get the class defs size
        class_defs_size = self.stream.read_uint32()

        # get the class defs offset
        class_defs_off = self.stream.read_uint32()

        # get the data size
        data_size = self.stream.read_uint32()

        # this field should be divisible by sizeof(uint)
        if data_size % struct.calcsize("I") != 0:
            raise ValueError("Invalid data size")

        # get the data offset
        data_off = self.stream.read_uint32()

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
