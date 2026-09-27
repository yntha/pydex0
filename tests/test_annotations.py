import pytest

from datastream import ByteOrder, DeserializingStream

from pydex.dalvik.models import (
    DalvikAnnotation,
    DalvikAnnotationVisibility,
    DalvikAnnotationSet,
    DalvikAnnotationSetRefList,
    DalvikAnnotationsDirectory,
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


def test_annotations_directory_parse():
    data = (
        b"\x00\x00\x00\x00"
        b"\x2c\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00"
        b"\x07\x00\x00\x00\x2c\x00\x00\x00"
        b"\x0b\x00\x00\x00\x2c\x00\x00\x00"
        b"\x0b\x00\x00\x00\x30\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    stream.seek(4)

    item = DalvikAnnotationsDirectory.from_stream(stream)

    assert item.offset == 4
    assert item.size == 40
    assert item.data == data[4:44]
    assert item.class_annotations_off == 44
    assert item.class_annotations is not None
    assert item.class_annotations.offset == 44
    assert item.class_annotations.entries == []
    assert item.fields_size == 1
    assert item.annotated_methods_size == 1
    assert item.annotated_parameters_size == 1
    assert len(item.field_annotations) == 1
    assert len(item.method_annotations) == 1
    assert len(item.parameter_annotations) == 1

    field = item.field_annotations[0]
    assert field.offset == 20
    assert field.size == 8
    assert field.data == data[20:28]
    assert field.field_idx == 7
    assert field.annotations_off == 44
    assert field.annotations is not None
    assert field.annotations.offset == 44
    assert field.annotations.entries == []

    method = item.method_annotations[0]
    assert method.offset == 28
    assert method.size == 8
    assert method.data == data[28:36]
    assert method.method_idx == 11
    assert method.annotations_off == 44
    assert method.annotations is not None
    assert method.annotations.offset == 44
    assert method.annotations.entries == []

    parameter = item.parameter_annotations[0]
    assert parameter.offset == 36
    assert parameter.size == 8
    assert parameter.data == data[36:44]
    assert parameter.method_idx == 11
    assert parameter.annotations_off == 48
    assert parameter.annotations is not None
    assert parameter.annotations.offset == 48
    assert parameter.annotations.entries == []
    assert stream.tell() == 4


def test_empty_annotations_directory_parse():
    data = b"\x00" * 16
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    item = DalvikAnnotationsDirectory.from_stream(stream)

    assert item.offset == 0
    assert item.size == 16
    assert item.data == data
    assert item.class_annotations_off == 0
    assert item.class_annotations is None
    assert item.fields_size == 0
    assert item.annotated_methods_size == 0
    assert item.annotated_parameters_size == 0
    assert item.field_annotations == []
    assert item.method_annotations == []
    assert item.parameter_annotations == []
    assert stream.tell() == 0


def test_annotations_directory_byte_order():
    data = (
        b"\x00\x00\x00\x28\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x00\x00\x01\x00\x00\x00\x00\x28"
        b"\x00\x00\x02\x00\x00\x00\x00\x28"
        b"\x00\x00\x02\x00\x00\x00\x00\x2c"
        b"\x00\x00\x00\x00\x00\x00\x00\x00"
    )
    stream = DeserializingStream(data, ByteOrder.BIG_ENDIAN)
    item = DalvikAnnotationsDirectory.from_stream(stream)

    assert item.size == 40
    assert item.class_annotations_off == 40
    assert item.class_annotations is not None
    assert item.class_annotations.offset == 40
    assert item.class_annotations.entries == []
    assert item.fields_size == 1
    assert item.annotated_methods_size == 1
    assert item.annotated_parameters_size == 1
    assert item.field_annotations[0].field_idx == 256
    assert item.field_annotations[0].annotations_off == 40
    assert item.field_annotations[0].annotations is not None
    assert item.field_annotations[0].annotations.offset == 40
    assert item.field_annotations[0].annotations.entries == []
    assert item.method_annotations[0].method_idx == 512
    assert item.method_annotations[0].annotations_off == 40
    assert item.method_annotations[0].annotations is not None
    assert item.method_annotations[0].annotations.entries == []
    assert item.parameter_annotations[0].method_idx == 512
    assert item.parameter_annotations[0].annotations_off == 44
    assert item.parameter_annotations[0].annotations is not None
    assert item.parameter_annotations[0].annotations.entries == []
    assert stream.tell() == 0


def test_annotations_directory_truncated_header():
    stream = DeserializingStream(b"\x00" * 12, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Corrupted annotations directory"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0


def test_annotations_directory_truncated_records():
    data = (
        b"\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00"
        b"\x07\x00\x00\x00\x00\x00\x00\x00"
        b"\x0b\x00\x00\x00\x00\x00\x00\x00"
        b"\x0b\x00\x00\x00"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Corrupted annotations directory"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0


def test_annotations_directory_class_annotations():
    data = (
        b"\x00\x00\x00\x00"
        b"\x14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x01\x00\x00\x00\x1c\x00\x00\x00"
        b"\x01\x02\x01\x03\x04\x2a"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    stream.seek(4)

    item = DalvikAnnotationsDirectory.from_stream(stream)

    assert item.offset == 4
    assert item.size == 16
    assert item.data == data[4:20]
    assert item.class_annotations is not None
    assert item.class_annotations.offset == 20
    assert item.class_annotations.length == 1
    annotation = item.class_annotations.entries[0]
    assert annotation.offset == 28
    assert annotation.visibility is DalvikAnnotationVisibility.VISIBILITY_RUNTIME
    assert annotation.annotation.type_idx == 2
    assert annotation.annotation.elements[0][0] == 3
    assert annotation.annotation.elements[0][1].value == 42
    assert stream.tell() == 4


def test_annotations_directory_invalid_class_annotations_offset():
    data = b"\xff\x00\x00\x00" + b"\x00" * 12
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid class annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0

    data = b"\x10\x00\x00\x00" + b"\x00" * 14
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid class annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0


def test_annotations_directory_field_annotations():
    data = (
        b"\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x07\x00\x00\x00\x28\x00\x00\x00"
        b"\x08\x00\x00\x00\x24\x00\x00\x00"
        b"\x00\x00\x00\x00"
        b"\x01\x00\x00\x00\x30\x00\x00\x00"
        b"\x01\x02\x01\x03\x04\x2a"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    stream.seek(4)

    item = DalvikAnnotationsDirectory.from_stream(stream)

    assert item.offset == 4
    assert item.size == 32
    assert item.data == data[4:36]
    assert len(item.field_annotations) == 2
    first = item.field_annotations[0]
    assert first.field_idx == 7
    assert first.offset == 20
    assert first.size == 8
    assert first.data == data[20:28]
    assert first.annotations is not None
    assert first.annotations.offset == 40
    assert first.annotations.length == 1
    annotation = first.annotations.entries[0]
    assert annotation.offset == 48
    assert annotation.visibility is DalvikAnnotationVisibility.VISIBILITY_RUNTIME
    assert annotation.annotation.type_idx == 2
    assert annotation.annotation.elements[0][1].value == 42

    second = item.field_annotations[1]
    assert second.field_idx == 8
    assert second.annotations is not None
    assert second.annotations.offset == 36
    assert second.annotations.entries == []
    assert stream.tell() == 4


def test_annotations_directory_invalid_field_annotations_offset():
    data = (
        b"\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        b"\x07\x00\x00\x00\x00\x00\x00\x00"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid field annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0

    stream = DeserializingStream(data[:20] + b"\xff\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid field annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0


def test_annotations_directory_method_and_parameter_annotations():
    data = (
        b"\x00\x00\x00\x00"
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00"
        b"\x0b\x00\x00\x00\x30\x00\x00\x00"
        b"\x0b\x00\x00\x00\x24\x00\x00\x00"
        b"\x02\x00\x00\x00\x00\x00\x00\x00\x30\x00\x00\x00"
        b"\x01\x00\x00\x00\x38\x00\x00\x00"
        b"\x01\x02\x01\x03\x04\x2a"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)
    stream.seek(4)

    item = DalvikAnnotationsDirectory.from_stream(stream)

    assert item.size == 32
    assert item.data == data[4:36]
    method = item.method_annotations[0]
    assert method.method_idx == 11
    assert method.offset == 20
    assert method.size == 8
    assert method.data == data[20:28]
    assert method.annotations is not None
    assert method.annotations.offset == 48
    assert method.annotations.length == 1
    assert method.annotations.entries[0].annotation.elements[0][1].value == 42

    parameter = item.parameter_annotations[0]
    assert parameter.method_idx == 11
    assert parameter.offset == 28
    assert parameter.size == 8
    assert parameter.data == data[28:36]
    assert parameter.annotations is not None
    assert parameter.annotations.offset == 36
    assert parameter.annotations.length == 2
    assert parameter.annotations.entries[0] is None
    second = parameter.annotations.entries[1]
    assert second is not None
    assert second.offset == 48
    assert second.entries[0].annotation.elements[0][1].value == 42
    assert stream.tell() == 4


def test_annotations_directory_invalid_method_annotations_offset():
    data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
        b"\x0b\x00\x00\x00\x00\x00\x00\x00"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid method annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0

    stream = DeserializingStream(data[:20] + b"\xff\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid method annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0


def test_annotations_directory_invalid_parameter_annotations_offset():
    data = (
        b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00"
        b"\x0b\x00\x00\x00\x00\x00\x00\x00"
    )
    stream = DeserializingStream(data, ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid parameter annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0

    stream = DeserializingStream(data[:20] + b"\xff\x00\x00\x00", ByteOrder.LITTLE_ENDIAN)

    with pytest.raises(ValueError, match="Invalid parameter annotations offset"):
        DalvikAnnotationsDirectory.from_stream(stream)

    assert stream.tell() == 0
