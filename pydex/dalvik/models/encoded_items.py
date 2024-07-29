from __future__ import annotations

import enum

from dataclasses import dataclass, field
from typing import Any

from datastream import ByteOrder, DeserializingStream

from pydex.dalvik.models.base import DalvikRawItem
from pydex.util import sizeof_uleb128


class DalvikValueFormats(enum.IntEnum):
    """Enumeration of the value formats that represent the different types of encoded values.

    .. admonition:: Source
        :class: seealso

        `dex::value_formats <https://source.android.com/docs/core/runtime/dex-format#value-formats>`_
    """

    VALUE_BYTE = 0x00
    """
    .. line-block::
        ``value_arg`` format: (`none`; must be 0)
        ``value`` format: ``ubyte[1]``
        ``description``: Signed one-byte integer value.
    """

    VALUE_SHORT = 0x02
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..1)
        ``value`` format: ``ubyte[size]``
        ``description``: Signed two-byte integer value, sign-extended.
    """

    VALUE_CHAR = 0x03
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..1)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned two-byte integer value, zero-extended.
    """

    VALUE_INT = 0x04
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Signed four-byte integer value, sign-extended.
    """

    VALUE_LONG = 0x06
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..7)
        ``value`` format: ``ubyte[size]``
        ``description``: Signed eight-byte integer value, sign-extended.
    """

    VALUE_FLOAT = 0x10
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Four-byte bit pattern, zero-extended `to the right`, and interpreted as an IEEE754 32-bit floating point value.
    """

    VALUE_DOUBLE = 0x11
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..7)
        ``value`` format: ``ubyte[size]``
        ``description``: Eight-byte bit pattern, zero-extended `to the right`, and interpreted as an IEEE754 64-bit floating point value.
    """

    VALUE_METHOD_TYPE = 0x15
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``proto_ids`` section and representing a method type value.
    """

    VALUE_METHOD_HANDLE = 0x16
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``method_handles`` section and representing a method handle value.
    """

    VALUE_STRING = 0x17
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``string_ids`` section and representing a string value.
    """

    VALUE_TYPE = 0x18
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``type_ids`` section and representing a type value.
    """

    VALUE_FIELD = 0x19
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``field_ids`` section and representing a field value.
    """

    VALUE_METHOD = 0x1A
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``method_ids`` section and representing a method value.
    """

    VALUE_ENUM = 0x1B
    """
    .. line-block::
        ``value_arg`` format: size - 1 (0..3)
        ``value`` format: ``ubyte[size]``
        ``description``: Unsigned (zero-extended) four-byte integer value, interpreted as an index into the ``field_ids`` section and representing an enum value.
    """

    VALUE_ARRAY = 0x1C
    """
    .. line-block::
        ``value_arg`` format: (`none`; must be 0)
        ``value`` format: ``encoded_array``
        ``description``: An array of values, in the format specified by "``encoded_array`` format" below. The size of the ``value`` is implicit in the encoding. 
    """

    VALUE_ANNOTATION = 0x1D
    """
    .. line-block::
        ``value_arg`` format: (`none`; must be 0)
        ``value`` format: ``encoded_annotation``
        ``description``: A sub-annotation, in the format specified by "``encoded_annotation`` format" below. The size of the ``value`` is implicit in the encoding.
    """

    VALUE_NULL = 0x1E
    """
    .. line-block::
        ``value_arg`` format: (`none`; must be 0)
        ``value`` format: `(none)`
        ``description``: ``null`` reference value.
    """

    VALUE_BOOLEAN = 0x1F
    """
    .. line-block::
        ``value_arg`` format: boolean (0..1)
        ``value`` format: `(none)`
        ``description``: one-bit value, 0 for ``false`` and 1 for ``true``. The bit is represented in the ``value_arg``.
    """


@dataclass
class DalvikEncodedValue(DalvikRawItem):
    """
    A dataclass that represents an encoded value in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex::encoded_value <https://source.android.com/docs/core/runtime/dex-format#encoding>`_
    """

    value: Any = field(init=False)

    def __post_init__(self):
        self.value = self.decode_value()

    def decode_value(self) -> Any:
        """Decode the encoded value based on the value format."""
        stream = DeserializingStream(self.data, byteorder=ByteOrder.LITTLE_ENDIAN)

        value_id = stream.read_uint8()
        value_format = DalvikValueFormats(value_id & 0x1F)
        value_arg = value_format >> 5

        if value_format == DalvikValueFormats.VALUE_BYTE:
            return stream.read_int8()
        elif value_format == DalvikValueFormats.VALUE_SHORT:
            return stream.read_int16()
        elif value_format == DalvikValueFormats.VALUE_CHAR:
            return stream.read_uint16()
        elif value_format == DalvikValueFormats.VALUE_INT:
            return stream.read_int32()
        elif value_format == DalvikValueFormats.VALUE_LONG:
            return stream.read_int64()
        elif value_format == DalvikValueFormats.VALUE_FLOAT:
            return stream.read_float()
        elif value_format == DalvikValueFormats.VALUE_DOUBLE:
            return stream.read_double()
        elif value_format == DalvikValueFormats.VALUE_METHOD_TYPE:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_METHOD_HANDLE:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_STRING:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_TYPE:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_FIELD:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_METHOD:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_ENUM:
            return stream.read_uint32()
        elif value_format == DalvikValueFormats.VALUE_ARRAY:
            return DalvikEncodedArray.from_stream(stream)
        elif value_format == DalvikValueFormats.VALUE_ANNOTATION:
            return DalvikEncodedAnnotation.from_stream(stream)
        elif value_format == DalvikValueFormats.VALUE_NULL:
            return None
        elif value_format == DalvikValueFormats.VALUE_BOOLEAN:
            return bool(value_arg)

    @classmethod
    def from_stream(cls, stream: DeserializingStream) -> DalvikEncodedValue:
        offset = stream.tell()
        value_id = stream.read_uint8()
        value_format = DalvikValueFormats(value_id & 0x1F)

        # use a clone stream to read the sizes
        clone_stream = stream.clone()

        if value_format == DalvikValueFormats.VALUE_ARRAY:
            # only read the size of the encoded element
            size = clone_stream.read_uleb128()
        elif value_format == DalvikValueFormats.VALUE_ANNOTATION:
            # type_idx.size + size
            size = sizeof_uleb128(clone_stream.read_uleb128()) + clone_stream.read_uleb128()
        else:
            size = (value_id >> 5) + 1  # value_arg + 1 is the size of the encoded value

        total_size = size + 1  # + 1 for value_id
        total_data = clone_stream.seekpeek(offset, total_size)

        clone_stream.close()

        return cls(
            offset,
            total_size,
            total_data,
        )
