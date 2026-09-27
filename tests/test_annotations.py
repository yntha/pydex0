import pytest

from datastream import ByteOrder, DeserializingStream

from pydex.dalvik.models import DalvikAnnotation, DalvikAnnotationVisibility


def test_annotation_parse():
    stream = DeserializingStream(b"\xff\x01\x02\x01\x03\x04\x2a\xff", ByteOrder.LITTLE_ENDIAN)
    stream.seek(1)

    item = DalvikAnnotation.from_stream(stream)

    assert item.offset == 1
    assert item.size == 6
    assert item.data == b"\x01\x02\x01\x03\x04\x2a"
    assert item.visibility is DalvikAnnotationVisibility.VISIBILITY_RUNTIME
    assert item.annotation.offset == 2
    assert item.annotation.size == 5
    assert item.annotation.type_idx == 2
    assert item.annotation.length == 1
    assert item.annotation.elements[0][0] == 3
    assert item.annotation.elements[0][1].value == 42
    assert item.annotation.elements[0][1].offset == 5
    assert stream.tell() == 1


def test_empty_annotation_parse():
    # build visibility
    stream = DeserializingStream(b"\x00\x01\x00", ByteOrder.LITTLE_ENDIAN)
    item = DalvikAnnotation.from_stream(stream)

    assert item.visibility is DalvikAnnotationVisibility.VISIBILITY_BUILD
    assert item.size == 3
    assert item.annotation.type_idx == 1
    assert item.annotation.length == 0
    assert item.annotation.elements == []
    assert stream.tell() == 0

    # system visibility
    stream = DeserializingStream(b"\x02\x01\x00", ByteOrder.LITTLE_ENDIAN)
    item = DalvikAnnotation.from_stream(stream)

    assert item.visibility is DalvikAnnotationVisibility.VISIBILITY_SYSTEM
    assert item.size == 3
    assert item.annotation.elements == []
    assert stream.tell() == 0


def test_annotation_invalid_visibility():
    stream = DeserializingStream(b"\x03\x01\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError):
        DalvikAnnotation.from_stream(stream)

    assert stream.tell() == 0


def test_annotation_truncated_value():
    stream = DeserializingStream(b"\x01\x02\x01\x03\x24\x01", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Corrupted encoded value"):
        DalvikAnnotation.from_stream(stream)

    assert stream.tell() == 0
