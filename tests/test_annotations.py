import pytest

from datastream import ByteOrder, DeserializingStream

from pydex.dalvik.models import (
    DalvikAnnotation,
    DalvikAnnotationVisibility,
    DalvikAnnotationSet,
    DalvikAnnotationSetRefList,
)


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


def test_annotation_set_parse():
    data = (
        b"\x00\x00\x00\x00"
        b"\x02\x00\x00\x00\x18\x00\x00\x00\x10\x00\x00\x00"
        b"\x02\x05\x00"
        b"\x00\x00\x00\x00\x00"
        b"\x01\x02\x01\x03\x04\x2a"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    stream.seek(4)

    item = DalvikAnnotationSet.from_stream(stream)

    assert item.offset == 4
    assert item.size == 12
    assert item.data == data[4:16]
    assert item.length == 2

    # ensure entries follow the offset table, not their order in the file
    assert item.entries[0].offset == 24
    assert item.entries[0].visibility is DalvikAnnotationVisibility.VISIBILITY_RUNTIME
    assert item.entries[0].annotation.type_idx == 2
    assert item.entries[0].annotation.elements[0][1].value == 42

    assert item.entries[1].offset == 16
    assert item.entries[1].visibility is DalvikAnnotationVisibility.VISIBILITY_SYSTEM
    assert item.entries[1].annotation.type_idx == 5
    assert item.entries[1].annotation.elements == []
    assert stream.tell() == 4


def test_empty_annotation_set_parse():
    stream = DeserializingStream(b"\x00\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)
    item = DalvikAnnotationSet.from_stream(stream)

    assert item.offset == 0
    assert item.size == 4
    assert item.data == b"\x00\x00\x00\x00"
    assert item.length == 0
    assert item.entries == []
    assert stream.tell() == 0


def test_annotation_set_byte_order():
    stream = DeserializingStream(b"\x00\x00\x00\x01\x00\x00\x00\x08\x01\x02\x00", ByteOrder.BIG_ENDIAN)
    item = DalvikAnnotationSet.from_stream(stream)

    assert item.size == 8
    assert item.length == 1
    assert item.entries[0].offset == 8
    assert item.entries[0].annotation.type_idx == 2
    assert stream.tell() == 0


def test_annotation_set_truncated_offsets():
    stream = DeserializingStream(b"\x02\x00\x00\x00\x08\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Corrupted annotation set"):
        DalvikAnnotationSet.from_stream(stream)

    assert stream.tell() == 0


def test_annotation_set_invalid_offset():
    stream = DeserializingStream(b"\x01\x00\x00\x00\x00\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid annotation offset"):
        DalvikAnnotationSet.from_stream(stream)

    assert stream.tell() == 0

    stream = DeserializingStream(b"\x01\x00\x00\x00\xff\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid annotation offset"):
        DalvikAnnotationSet.from_stream(stream)

    assert stream.tell() == 0


def test_annotation_set_ref_list_parse():
    data = (
        b"\x00\x00\x00\x00"
        b"\x03\x00\x00\x00\x18\x00\x00\x00\x00\x00\x00\x00\x14\x00\x00\x00"
        b"\x00\x00\x00\x00"
        b"\x01\x00\x00\x00\x20\x00\x00\x00"
        b"\x01\x02\x00"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    stream.seek(4)

    item = DalvikAnnotationSetRefList.from_stream(stream)

    assert item.offset == 4
    assert item.size == 16
    assert item.data == data[4:20]
    assert item.length == 3

    first = item.entries[0]
    assert first is not None
    assert first.offset == 24
    assert first.length == 1
    assert first.entries[0].offset == 32
    assert first.entries[0].annotation.type_idx == 2

    # ensure empty annotation sets are handled correctly
    assert item.entries[1] is None

    third = item.entries[2]
    assert third is not None
    assert third.offset == 20
    assert third.length == 0
    assert third.entries == []
    assert stream.tell() == 4


def test_empty_annotation_set_ref_list_parse():
    stream = DeserializingStream(b"\x00\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)
    item = DalvikAnnotationSetRefList.from_stream(stream)

    assert item.offset == 0
    assert item.size == 4
    assert item.data == b"\x00\x00\x00\x00"
    assert item.length == 0
    assert item.entries == []
    assert stream.tell() == 0


def test_annotation_set_ref_list_byte_order():
    data = (
        b"\x00\x00\x00\x01\x00\x00\x00\x08"
        b"\x00\x00\x00\x01\x00\x00\x00\x10"
        b"\x01\x02\x00"
    )
    stream = DeserializingStream(data, ByteOrder.BIG_ENDIAN)
    item = DalvikAnnotationSetRefList.from_stream(stream)

    assert item.size == 8
    assert item.length == 1
    first = item.entries[0]
    assert first is not None
    assert first.offset == 8
    assert first.entries[0].offset == 16
    assert first.entries[0].annotation.type_idx == 2
    assert stream.tell() == 0


def test_annotation_set_ref_list_truncated_offsets():
    stream = DeserializingStream(b"\x02\x00\x00\x00\x08\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Corrupted annotation set reference list"):
        DalvikAnnotationSetRefList.from_stream(stream)

    assert stream.tell() == 0


def test_annotation_set_ref_list_invalid_offset():
    stream = DeserializingStream(b"\x01\x00\x00\x00\xff\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid annotation set offset"):
        DalvikAnnotationSetRefList.from_stream(stream)

    assert stream.tell() == 0
