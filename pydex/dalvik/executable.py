from __future__ import annotations

import asyncio
import struct
import typing
import zlib

from dataclasses import dataclass
from functools import wraps

from datastream import DeserializingStream, ByteOrder

from pydex.dalvik.models.dalvik import (
    DalvikHeader,
    DalvikHeaderItem,
    DalvikStringItem,
    DalvikStringID,
    LazyDalvikString,
    DalvikTypeID,
    DalvikTypeItem,
    DalvikTypeList,
    DalvikProtoID,
    DalvikProtoIDItem,
    DalvikTypeListItem,
    DalvikField,
    DalvikFieldItem,
    DalvikMethod,
    DalvikMethodItem,
)
from pydex.exc import InvalidDalvikHeader


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

    Certain flag constants exist in this class which let the parser know if a
    specific section has been parsed already. This prevents the parser from
    re-parsing the same section multiple times.

    .. admonition:: Note
        :class: note

        This class allows you to parse individual sections of the DEX file. This is useful when you only need to
        interact with a specific section of the DEX file and don't want to parse the entire file, for example, when
        you only need to access the strings in the DEX file:

        .. code-block:: python

            >>> from pydex.dalvik import DexFile
            >>> dex = DexFile.from_path("path/to/dex/file.dex")
            >>> types = dex.parse_types()
            >>> for dalvik_type in types:
            ...     type_str = str(dalvik_type)
            ...     if type_str.startswith("Ljava/"):
            ...         continue  # skip standard Java types
            ...     print(type_str)

        If you wish to parse the entire DEX file, you can use the :meth:`~pydex.dalvik.DexFile.parse_dex` method.

    :param data: The raw bytes of the dex file.
    :param no_lazy_load: A flag that indicates whether lazy loading should be disabled.
    """

    #: Flag that indicates the header has been parsed.
    FLAG_PARSED_HEADER: int = 1

    #: Flag that indicates the strings have been parsed.
    FLAG_PARSED_STRINGS: int = 2

    #: Flag that indicates the types have been parsed.
    FLAG_PARSED_TYPES: int = 4

    #: Flag that indicates the protos have been parsed.
    FLAG_PARSED_PROTOS: int = 8

    #: Flag that indicates the fields have been parsed.
    FLAG_PARSED_FIELDS: int = 16

    #: Flag that indicates the methods have been parsed.
    FLAG_PARSED_METHODS: int = 32

    def __init__(self, data: bytes, no_lazy_load: bool = False):
        #: The raw bytes of the dex file.
        self.data: bytes = data

        #: A flag that indicates whether lazy loading should be disabled.
        self.no_lazy_load: bool = no_lazy_load

        #: The flags that indicate which sections have been parsed.
        self.section_flags: int = 0

        #: The stream used to read the dex file.
        self.stream: DeserializingStream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

        #: The header of the dex file.
        self.header: DalvikHeaderItem = typing.cast(DalvikHeaderItem, None)

        #: The list of dalvik string items in the dex file.
        self.strings: list[LazyDalvikString | DalvikStringItem] = []

        #: The list of dalvik type items in the dex file.
        self.types: list[DalvikTypeItem] = []

        #: The list of dalvik proto items in the dex file.
        self.protos: list[DalvikProtoIDItem] = []

        #: The list of dalvik field items in the dex file.
        self.fields: list[DalvikFieldItem] = []

        #: The list of dalvik method items in the dex file.
        self.methods: list[DalvikMethodItem] = []

    @classmethod
    def from_path(cls, path: str, no_lazy_load: bool = False) -> DexFile:
        """
        Create a :class:`~pydex.dalvik.DexFile` object from a file path.

        :param path: The path to the dex file.
        :param no_lazy_load: A flag that indicates whether lazy loading should be disabled.
        """

        with open(path, "rb") as f:
            return cls(f.read(), no_lazy_load=no_lazy_load)

    @staticmethod
    def requires_section(flags: int) -> typing.Callable:
        """Decorator that checks if a section has been parsed.

        This decorator checks if a specific section has been parsed before executing the function. If the section has
        not yet been parsed, the function will parse it before executing the function.

        Args:
             int flags: The flags that indicate which sections need to be parsed.
        """

        def decorator(func: typing.Callable) -> typing.Callable:

            @wraps(func)
            def wrapper(self, *args, **kwargs):
                do_header = self.section_flags & self.FLAG_PARSED_HEADER == 0
                do_strings = self.section_flags & self.FLAG_PARSED_STRINGS == 0
                do_types = self.section_flags & self.FLAG_PARSED_TYPES == 0
                do_protos = self.section_flags & self.FLAG_PARSED_PROTOS == 0
                do_fields = self.section_flags & self.FLAG_PARSED_FIELDS == 0
                do_methods = self.section_flags & self.FLAG_PARSED_METHODS == 0

                if do_header and flags & self.FLAG_PARSED_HEADER != 0:
                    self.parse_dex_prologue()
                if do_strings and flags & self.FLAG_PARSED_STRINGS != 0:
                    self.strings = self.parse_strings()
                if do_types and flags & self.FLAG_PARSED_TYPES != 0:
                    self.types = self.parse_types()
                if do_protos and flags & self.FLAG_PARSED_PROTOS != 0:
                    self.protos = self.parse_protos()
                if do_fields and flags & self.FLAG_PARSED_FIELDS != 0:
                    self.fields = self.parse_fields()
                if do_methods and flags & self.FLAG_PARSED_METHODS != 0:
                    self.methods = self.parse_methods()

                return func(self, *args, **kwargs)

            return wrapper

        return decorator

    def parse_dex_prologue(self) -> typing.Self:
        """
        Helper function that does misc startup tasks for parsing the dex file.

        :raises InvalidDalvikHeader: If the endian tag is invalid.
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
            raise InvalidDalvikHeader("Invalid endian tag", InvalidDalvikHeader.INVALID_ENDIAN_TAG)

        # parse the header
        self.header = self.parse_header()

        return self

    def parse_dex(self) -> typing.Self:
        """Parse the DEX file.

        This function will attempt to entirely parse this DEX file in one go and fill in all the uninitialized class
        attributes.
        """

        self.parse_dex_prologue()

        # collect all the dalvik string items
        if not self.no_lazy_load:
            self.strings = self.parse_strings()
        else:
            self.strings = self.load_all_strings()

        # collect all the dalvik type items
        self.types = self.parse_types()

        # collect all the dalvik proto items
        self.protos = self.parse_protos()

        # collect all the dalvik field items
        self.fields = self.parse_fields()

        # collect all the dalvik method items
        self.methods = self.parse_methods()

        return self

    def parse_header(self) -> DalvikHeaderItem:
        r"""
        Parse the header of the dex file.

        Raises:
            InvalidDalvikHeader: If the parser encounters unexpected values in the header.
        """

        clonestream = self.stream.clone()

        # get the magic bytes
        magic = clonestream.read(8)

        # the magic bytes are not constant, as they contain a version number
        # dex\0x0Axxx\x00, where xxx is the version number(zero padded).
        if magic[:4] != b"dex\x0A":
            raise InvalidDalvikHeader("Invalid magic bytes", InvalidDalvikHeader.INVALID_MAGIC_BYTES)

        if magic[7] != 0:
            raise InvalidDalvikHeader("No terminating NULL character", InvalidDalvikHeader.INVALID_MAGIC_BYTES)

        # get the checksum
        checksum = clonestream.read_uint32()

        # verify the checksum. the checksum applies to the entire file except
        # the magic bytes and this field, so 8 bytes + 4 bytes = 12 bytes to
        # skip.
        if checksum != zlib.adler32(self.data[12:]):
            raise InvalidDalvikHeader(f"Invalid checksum: {checksum}", InvalidDalvikHeader.INVALID_CHECKSUM)

        # get the sha-1 signature bytes(fingerprint)
        signature = clonestream.read(20)

        # get the file size
        file_size = clonestream.read_uint32()

        # get the header size
        header_size = clonestream.read_uint32()

        # according to the spec, this should always be == 0x70
        if header_size != 0x70:
            raise InvalidDalvikHeader(f"Invalid header size: {header_size}", InvalidDalvikHeader.INVALID_HEADER_SIZE)

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
            raise InvalidDalvikHeader(f"Invalid type ids size: {type_ids_size}", InvalidDalvikHeader.INVALID_TYPES_SIZE)

        # get the type ids offset
        type_ids_off = clonestream.read_uint32()

        # get the proto ids size
        proto_ids_size = clonestream.read_uint32()

        # according to the spec, this should always be <= 0xFFFF
        if proto_ids_size >= 0xFFFF:
            raise InvalidDalvikHeader(
                f"Invalid proto ids size: {proto_ids_size}", InvalidDalvikHeader.INVALID_PROTOS_SIZE
            )

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
            raise InvalidDalvikHeader(f"Invalid data size: {data_size}", InvalidDalvikHeader.INVALID_DATA_SIZE)

        # get the data offset
        data_off = clonestream.read_uint32()

        self.section_flags |= self.FLAG_PARSED_HEADER

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
            InvalidDalvikHeader: If the parser encounters unexpected values in the header.
        """

        return await asyncio.to_thread(self.parse_header)

    @requires_section(FLAG_PARSED_HEADER)
    def parse_strings(self) -> list[LazyDalvikString]:
        """Collect all the dalvik string items.

        This function collects all the dalvik string items in this DEX file and returns them as a list of
        :class:`~pydex.dalvik.models.LazyDalvikString`. A clone stream is used so to not alter the DEX
        file stream.
        """

        lazy_strings = []
        clonestream = self.stream.clone()

        for i in range(self.header.raw_item.string_ids_size):
            clonestream.seek(self.header.raw_item.string_ids_off + i * DalvikStringID.struct_size)
            string_id_off = clonestream.tell()

            string_data_off = clonestream.read_uint32()
            clonestream.seek(string_data_off)

            lazy_strings.append(
                LazyDalvikString(
                    DalvikStringID(
                        offset=string_id_off,
                        size=DalvikStringID.struct_size,
                        data=self.data[string_id_off : string_id_off + DalvikStringID.struct_size],
                        string_data_off=string_data_off,
                        id_number=i,
                    )
                )
            )

        self.section_flags |= self.FLAG_PARSED_STRINGS

        return lazy_strings

    async def parse_strings_async(self) -> list[LazyDalvikString]:
        """Collect all the dalvik string items.

        This function collects all the dalvik string items in this DEX file and returns them as a list of
        :class:`~pydex.dalvik.models.LazyDalvikString`. A clone stream is used so to not alter the
        DEX file stream.
        """

        return await asyncio.to_thread(self.parse_strings)

    @requires_section(FLAG_PARSED_STRINGS)
    def parse_types(self) -> list[DalvikTypeItem]:
        """Collect all the dalvik type items.

        This function collects all the dalvik type items in this DEX file and returns them as a list of
        :class:`~pydex.dalvik.models.DalvikTypeItem`. A clone stream is used so to not alter the DEX
        file stream.
        """

        if not self.strings:
            return []

        types = []
        clonestream = self.stream.clone()

        for i in range(self.header.raw_item.type_ids_size):
            clonestream.seek(self.header.raw_item.type_ids_off + i * DalvikTypeID.struct_size)
            type_id_off = clonestream.tell()

            descriptor_idx = clonestream.read_uint32()
            descriptor = self.strings[descriptor_idx]

            types.append(
                DalvikTypeItem(
                    DalvikTypeID(
                        offset=type_id_off,
                        size=DalvikTypeID.struct_size,
                        data=self.data[type_id_off : type_id_off + DalvikTypeID.struct_size],
                        descriptor_idx=descriptor_idx,
                        id_number=i,
                    ),
                    descriptor=descriptor,
                )
            )

        self.section_flags |= self.FLAG_PARSED_TYPES

        return types

    async def parse_types_async(self) -> list[DalvikTypeItem]:
        """Collect all the dalvik type items asynchronously.

        This function collects all the dalvik type items in this DEX file and returns them as a list of
        :class:`~pydex.dalvik.models.DalvikTypeItem`. A clone stream is used so to not alter the DEX
        file stream.
        """

        return await asyncio.to_thread(self.parse_types)

    @requires_section(FLAG_PARSED_TYPES)
    def parse_protos(self) -> list[DalvikProtoIDItem]:
        """Collect all the dalvik proto items.

        This function collects all the dalvik prototyoe items in this DEX file and returns them as a
        list of :class:`~pydex.dalvik.models.DalvikProtoIDItem`. A clone stream is used so to not
        alter the DEX file stream.
        """

        if not self.types or not self.strings:
            return []

        protos = []
        clonestream = self.stream.clone()

        for i in range(self.header.raw_item.proto_ids_size):
            clonestream.seek(self.header.raw_item.proto_ids_off + (i * DalvikProtoID.struct_size))
            proto_id_off = clonestream.tell()

            shorty_idx = clonestream.read_uint32()
            return_type_idx = clonestream.read_uint32()
            parameters_off = clonestream.read_uint32()

            shorty = self.strings[shorty_idx]
            return_type = self.types[return_type_idx]

            if parameters_off != 0:
                clonestream.seek(parameters_off)
                length = clonestream.read_uint32()
                entries = []

                for j in range(length):
                    entries.append(self.types[clonestream.read_uint16()].raw_item)

                list_size = len(entries) * DalvikTypeID.struct_size

                param_type_list = DalvikTypeListItem.from_raw_item(
                    DalvikTypeList(
                        offset=parameters_off,
                        size=list_size + 4,
                        data=self.data[parameters_off : parameters_off + 4 + list_size],
                        length=length,
                        entries=entries,
                    ),
                    self.types,
                )
                param_string_list = [x.descriptor.value for x in param_type_list.types]
            else:
                param_type_list = None
                param_string_list = None

            protos.append(
                DalvikProtoIDItem(
                    DalvikProtoID(
                        offset=proto_id_off,
                        size=DalvikProtoID.struct_size,
                        data=self.data[proto_id_off : proto_id_off + DalvikProtoID.struct_size],
                        shorty_idx=shorty_idx,
                        return_type_idx=return_type_idx,
                        parameters_off=parameters_off,
                        id_number=i,
                    ),
                    shorty=shorty,
                    return_type=return_type,
                    parameters=param_type_list,
                    parameter_list=param_string_list,
                )
            )

        self.section_flags |= self.FLAG_PARSED_PROTOS

        return protos

    async def parse_protos_async(self) -> list[DalvikProtoIDItem]:
        """Collect all the dalvik proto items asynchronously.

        This function collects all the dalvik prototyoe items in this DEX file and returns them as a
        list of :class:`~pydex.dalvik.models.DalvikProtoIDItem`. A clone stream is used so to not
        alter the DEX file stream.
        """

        return await asyncio.to_thread(self.parse_protos)

    @requires_section(FLAG_PARSED_TYPES)
    def parse_fields(self) -> list[DalvikFieldItem]:
        """Collect all the dalvik field items.

        This function collects all the dalvik field items in this DEX file and returns them as a
        list of :class:`~pydex.dalvik.models.DalvikFieldItem`. A clone stream is used so to not
        alter the DEX file stream.
        """

        if not self.types or not self.strings:
            return []

        fields = []
        clonestream = self.stream.clone()

        for i in range(self.header.raw_item.field_ids_size):
            clonestream.seek(self.header.raw_item.field_ids_off + (i * DalvikField.struct_size))
            field_id_off = clonestream.tell()

            class_idx = clonestream.read_uint16()
            type_idx = clonestream.read_uint16()
            name_idx = clonestream.read_uint32()

            class_type = self.types[class_idx]
            type_type = self.types[type_idx]
            name = self.strings[name_idx]

            fields.append(
                DalvikFieldItem(
                    DalvikField(
                        offset=field_id_off,
                        size=DalvikField.struct_size,
                        data=self.data[field_id_off : field_id_off + DalvikField.struct_size],
                        class_idx=class_idx,
                        type_idx=type_idx,
                        name_idx=name_idx,
                        id_number=i,
                    ),
                    class_def=class_type,
                    type=type_type,
                    name=name,
                )
            )

        self.section_flags |= self.FLAG_PARSED_FIELDS

        return fields

    async def parse_fields_async(self) -> list[DalvikFieldItem]:
        """Collect all the dalvik field items asynchronously.

        This function collects all the dalvik field items in this DEX file and returns them as a
        list of :class:`~pydex.dalvik.models.DalvikFieldItem`. A clone stream is used so to not
        alter the DEX file stream.
        """

        return await asyncio.to_thread(self.parse_fields)

    @requires_section(FLAG_PARSED_PROTOS)
    def parse_methods(self) -> list[DalvikMethodItem]:
        """Collect all the dalvik method items.

        This function collects all the dalvik method items in this DEX file and returns them as a
        list of :class:`~pydex.dalvik.models.DalvikMethodItem`. A clone stream is used so to not
        alter the DEX file stream.
        """

        if not self.types or not self.strings or not self.protos:
            return []

        methods = []
        clonestream = self.stream.clone()

        for i in range(self.header.raw_item.method_ids_size):
            clonestream.seek(self.header.raw_item.method_ids_off + (i * DalvikMethod.struct_size))
            method_id_off = clonestream.tell()

            class_idx = clonestream.read_uint16()
            proto_idx = clonestream.read_uint16()
            name_idx = clonestream.read_uint32()

            class_type = self.types[class_idx]
            proto_type = self.protos[proto_idx]
            name = self.strings[name_idx]

            methods.append(
                DalvikMethodItem(
                    DalvikMethod(
                        offset=method_id_off,
                        size=DalvikMethod.struct_size,
                        data=self.data[method_id_off : method_id_off + DalvikMethod.struct_size],
                        class_idx=class_idx,
                        proto_idx=proto_idx,
                        name_idx=name_idx,
                        id_number=i,
                    ),
                    class_def=class_type,
                    proto=proto_type,
                    name=name,
                )
            )

        self.section_flags |= self.FLAG_PARSED_METHODS

        return methods

    async def parse_methods_async(self) -> list[DalvikMethodItem]:
        """Collect all the dalvik method items asynchronously.

        This function collects all the dalvik method items in this DEX file and returns them as a
        list of :class:`~pydex.dalvik.models.DalvikMethodItem`. A clone stream is used so to not
        alter the DEX file stream.
        """

        return await asyncio.to_thread(self.parse_methods)

    @requires_section(FLAG_PARSED_STRINGS)
    def load_all_strings(self) -> list[DalvikStringItem]:
        """Load all the dalvik string items.

        This function invokes the :meth:`~pydex.dalvik.models.LazyDalvikString.load` function for
        all the lazy dalvik strings in the :attr:`strings` attribute. It will also convert every
        model in :attr:`strings` to a loaded :class:`~pydex.dalvik.models.DalvikStringItem` model.
        """

        if not self.strings:
            return []

        strings = []

        for lazy_string in self.strings:
            strings.append(lazy_string.load(self.stream))

        return strings

    async def load_all_strings_async(self) -> list[DalvikStringItem]:
        """Load all the dalvik string items asynchronously.

        This function invokes the :meth:`~pydex.dalvik.models.LazyDalvikString.load_async`
        function for all the lazy dalvik strings in the :attr:`strings` attribute. It will
        also convert every model in :attr:`strings` to a loaded
        :class:`~pydex.dalvik.models.DalvikStringItem` model.
        """

        return await asyncio.to_thread(self.load_all_strings)

    @requires_section(FLAG_PARSED_STRINGS | FLAG_PARSED_HEADER)
    def get_string_by_id(self, string_id: int) -> LazyDalvikString:
        """Get a dalvik string by its id.

        Get a dalvik string by its id. The difference between this, and
        ``dex.strings[id]`` is that this method does not require all the strings
        to be collected from the dex file. This method is useful when you only
        need a single string from the dex file and don't want to load the
        entire dex file with :func:`parse_dex`.

        :param string_id: The id of the string to get. IDs are 0-indexed, and are
            assigned in the order they appear in the dex file.
        """

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
