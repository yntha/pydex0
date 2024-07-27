from __future__ import annotations

import enum

from dataclasses import dataclass

from datastream import ByteOrder, DeserializingStream


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
