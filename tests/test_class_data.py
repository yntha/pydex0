from datastream import ByteOrder, DeserializingStream

from pydex.dalvik.models import DalvikEncodedField


def test_encoded_field_parse():
    stream = DeserializingStream(b"\xff\x03\x19\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    item = DalvikEncodedField.from_stream(stream)

    assert item.offset == 1
    assert item.size == 2
    assert item.data == b"\x03\x19"
    assert item.field_idx_diff == 3
    assert item.access_flags == 0x19
    assert stream.tell() == 1


def test_encoded_field_zero_values():
    stream = DeserializingStream(b"\x00\x00", ByteOrder.LITTLE_ENDIAN)

    item = DalvikEncodedField.from_stream(stream)

    assert item.size == 2
    assert item.field_idx_diff == 0
    assert item.access_flags == 0
    assert stream.tell() == 0


def test_encoded_field_multibyte_values():
    stream = DeserializingStream(b"\x80\x01\x81\x20", ByteOrder.BIG_ENDIAN)

    item = DalvikEncodedField.from_stream(stream)

    assert item.size == 4
    assert item.data == b"\x80\x01\x81\x20"
    assert item.field_idx_diff == 128
    assert item.access_flags == 0x1001
    assert stream.tell() == 0
