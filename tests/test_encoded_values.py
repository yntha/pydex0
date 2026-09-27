import pytest

from datastream import ByteOrder, DeserializingStream

from pydex.dalvik.models.encoded_items import DalvikEncodedValue, DalvikEncodedArray, DalvikEncodedAnnotation


def get_encoded_value(data: bytes) -> DalvikEncodedValue:
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    return DalvikEncodedValue.from_stream(stream)


def test_encoded_integer_parse():
    # byte
    assert get_encoded_value(b"\x00\x80").value == -128

    # short
    assert get_encoded_value(b"\x02\xff").value == -1
    assert get_encoded_value(b"\x22\x00\x80").value == -32768

    # char
    assert get_encoded_value(b"\x03\xff").value == 255
    assert get_encoded_value(b"\x23\xff\xff").value == 65535

    # int
    assert get_encoded_value(b"\x04\x80").value == -128
    assert get_encoded_value(b"\x24\x80\x00").value == 128
    assert get_encoded_value(b"\x44\xff\xff\x7f").value == 8388607
    assert get_encoded_value(b"\x64\x00\x00\x00\x80").value == -2147483648

    # long
    assert get_encoded_value(b"\x06\xff").value == -1
    assert get_encoded_value(b"\xe6\x00\x00\x00\x00\x00\x00\x00\x80").value == -9223372036854775808


def test_encoded_float_parse():
    assert get_encoded_value(b"\x10\x00").value == 0.0
    assert get_encoded_value(b"\x30\x80\x3f").value == 1.0
    assert get_encoded_value(b"\x70\x00\x00\x20\xc0").value == -2.5


def test_encoded_double_parse():
    assert get_encoded_value(b"\x31\xf0\x3f").value == 1.0
    assert get_encoded_value(b"\xf1\x00\x00\x00\x00\x00\x00\x04\xc0").value == -2.5


def test_encoded_reference_parse():
    # method type and method handle
    assert get_encoded_value(b"\x15\xff").value == 255
    assert get_encoded_value(b"\x16\xff").value == 255

    # string, type, field, method, and enum
    assert get_encoded_value(b"\x17\xff").value == 255
    assert get_encoded_value(b"\x18\xff").value == 255
    assert get_encoded_value(b"\x19\xff").value == 255
    assert get_encoded_value(b"\x1a\xff").value == 255
    assert get_encoded_value(b"\x1b\xff").value == 255

    # full width unsigned int
    assert get_encoded_value(b"\x77\xff\xff\xff\xff").value == 4294967295


def test_encoded_value_byte_order():
    stream = DeserializingStream(b"\x37\x80\x00", ByteOrder.BIG_ENDIAN)
    value = DalvikEncodedValue.from_stream(stream)

    # encoded values are always little-endian
    assert value.value == 128
    assert value.size == 3
    assert stream.tell() == 0


def test_encoded_null_parse():
    value = get_encoded_value(b"\x1e")

    assert value.value is None
    assert value.size == 1


def test_encoded_boolean_parse():
    false_value = get_encoded_value(b"\x1f")
    true_value = get_encoded_value(b"\x3f")

    assert false_value.value is False
    assert false_value.size == 1
    assert true_value.value is True
    assert true_value.size == 1


def test_encoded_value_stream_position():
    stream = DeserializingStream(b"\xff\x24\x80\x00\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    value = DalvikEncodedValue.from_stream(stream)

    assert value.value == 128
    assert value.offset == 1
    assert value.size == 3
    assert value.data == b"\x24\x80\x00"
    assert stream.tell() == 1


def test_truncated_encoded_value():
    with pytest.raises(ValueError, match="Corrupted encoded value"):
        get_encoded_value(b"\x00")

    with pytest.raises(ValueError, match="Corrupted encoded value"):
        get_encoded_value(b"\x24\x01")

    with pytest.raises(ValueError, match="Corrupted encoded value"):
        get_encoded_value(b"\x70\x00\x00\x80")


def test_encoded_array_parse():
    stream = DeserializingStream(b"\xff\x03\x04\x2a\x3f\x1e\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    array = DalvikEncodedArray.from_stream(stream)

    assert array.offset == 1
    assert array.size == 5
    assert array.data == b"\x03\x04\x2a\x3f\x1e"
    assert array.length == 3
    assert array.values[0].value == 42
    assert array.values[1].value is True
    assert array.values[2].value is None
    assert stream.tell() == 6
    assert stream.read_uint8() == 0xFF


def test_empty_encoded_array_parse():
    stream = DeserializingStream(b"\x00", ByteOrder.LITTLE_ENDIAN)
    array = DalvikEncodedArray.from_stream(stream)

    assert array.size == 1
    assert array.data == b"\x00"
    assert array.length == 0
    assert array.values == []


def test_encoded_annotation_parse():
    stream = DeserializingStream(b"\xff\x80\x01\x02\x80\x01\x04\x2a\x81\x01\x3f\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    annotation = DalvikEncodedAnnotation.from_stream(stream)

    assert annotation.offset == 1
    assert annotation.size == 10
    assert annotation.data == b"\x80\x01\x02\x80\x01\x04\x2a\x81\x01\x3f"
    assert annotation.type_idx == 128
    assert annotation.length == 2

    assert annotation.elements[0][0] == 128
    assert annotation.elements[0][1].value == 42
    assert annotation.elements[0][1].offset == 6

    assert annotation.elements[1][0] == 129
    assert annotation.elements[1][1].value is True
    assert annotation.elements[1][1].offset == 10

    assert stream.tell() == 11
    assert stream.read_uint8() == 0xFF


def test_empty_encoded_annotation_parse():
    stream = DeserializingStream(b"\x01\x00", ByteOrder.LITTLE_ENDIAN)
    annotation = DalvikEncodedAnnotation.from_stream(stream)

    assert annotation.size == 2
    assert annotation.data == b"\x01\x00"
    assert annotation.type_idx == 1
    assert annotation.length == 0
    assert annotation.elements == []
    assert stream.tell() == 2


def test_encoded_array_value_parse():
    stream = DeserializingStream(b"\xff\x1c\x03\x04\x2a\x3f\x1e\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    value = DalvikEncodedValue.from_stream(stream)
    array = value.value

    assert value.offset == 1
    assert value.size == 6
    assert value.data == b"\x1c\x03\x04\x2a\x3f\x1e"
    assert array.size == 5
    assert array.length == 3
    assert array.values[0].value == 42
    assert array.values[1].value is True
    assert array.values[2].value is None
    assert stream.tell() == 1


def test_encoded_annotation_value_parse():
    stream = DeserializingStream(b"\xff\x1d\x80\x01\x02\x80\x01\x04\x2a\x81\x01\x3f\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    value = DalvikEncodedValue.from_stream(stream)
    annotation = value.value

    assert value.offset == 1
    assert value.size == 11
    assert value.data == b"\x1d\x80\x01\x02\x80\x01\x04\x2a\x81\x01\x3f"
    assert annotation.size == 10
    assert annotation.type_idx == 128
    assert annotation.length == 2
    assert annotation.elements[0][0] == 128
    assert annotation.elements[0][1].value == 42
    assert annotation.elements[1][0] == 129
    assert annotation.elements[1][1].value is True
    assert stream.tell() == 1


def test_empty_encoded_array_value_parse():
    value = get_encoded_value(b"\x1c\x00")

    assert value.size == 2
    assert value.data == b"\x1c\x00"
    assert value.value.length == 0
    assert value.value.values == []


def test_empty_encoded_annotation_value_parse():
    value = get_encoded_value(b"\x1d\x01\x00")

    assert value.size == 3
    assert value.data == b"\x1d\x01\x00"
    assert value.value.type_idx == 1
    assert value.value.length == 0
    assert value.value.elements == []


def test_nested_encoded_value_parse():
    value = get_encoded_value(b"\x1c\x03\x1c\x01\x24\x80\x00\x1d\x01\x01\x02\x1c\x01\x3f\x1e")
    array = value.value

    assert value.size == 15
    assert array.length == 3

    # array with an int
    assert array.values[0].size == 5
    assert array.values[0].value.values[0].value == 128

    # annotation with an array
    annotation = array.values[1].value
    assert array.values[1].size == 7
    assert annotation.type_idx == 1
    assert annotation.elements[0][0] == 2
    assert annotation.elements[0][1].value.values[0].value is True

    # null after both nested values
    assert array.values[2].size == 1
    assert array.values[2].value is None
