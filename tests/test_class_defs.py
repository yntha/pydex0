import asyncio
import hashlib
import os
import zlib

import pytest

from pydex.dalvik import DexFile
from pydex.dalvik.models import LazyDalvikString


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "min.dex"), "rb") as test_dex:
        return test_dex.read()


def test_class_def_parse():
    dex = DexFile(get_test_dex(), no_lazy_load=True).parse_dex()

    assert len(dex.class_defs) == 1
    item = dex.class_defs[0]
    assert str(item.class_type) == "Ltest/klass;"
    assert str(item.superclass) == "Ljava/lang/Object;"
    assert str(item.source_file) == "klass.java"
    assert item.interfaces is None
    assert item.annotations is None

    assert item.raw_item.offset == 248
    assert item.raw_item.size == 32
    assert item.raw_item.data == dex.data[248:280]
    assert item.raw_item.id_number == 0
    assert item.raw_item.access_flags == 1
    assert item.raw_item.annotations_off == 0
    assert item.raw_item.class_data_off == 486
    assert item.raw_item.static_values_off == 430
    assert item.static_values is not None
    assert item.static_values.offset == 430
    assert item.static_values.size == 6
    assert item.static_values.data == dex.data[430:436]
    assert item.static_values.length == 2
    assert item.static_values.values[0].offset == 431
    assert item.static_values.values[0].value == 4628
    assert item.static_values.values[1].offset == 434
    assert item.static_values.values[1].value == 1
    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS != 0

    dex.stream.seek(12)
    assert dex.parse_class_defs() == dex.class_defs
    assert dex.stream.tell() == 12


def test_class_def_parse_async():
    dex = DexFile(get_test_dex())
    items = asyncio.run(dex.parse_class_defs_async())

    assert len(items) == 1
    assert items[0].class_type is dex.types[3]
    assert items[0].superclass is dex.types[1]
    assert isinstance(items[0].source_file, LazyDalvikString)
    assert items[0].source_file.load(dex.stream).value == "klass.java"
    assert items[0].static_values is not None
    assert items[0].static_values.values[0].value == 4628
    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS != 0


def test_empty_class_defs_parse():
    dex = DexFile.from_path(os.path.join("resources", "dex-files", "empty.dex")).parse_dex()

    assert dex.class_defs == []
    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS != 0


def test_class_def_missing_superclass_and_source():
    data = bytearray(get_test_dex())
    data[256:260] = b"\xff\xff\xff\xff"
    data[264:268] = b"\xff\xff\xff\xff"
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data), no_lazy_load=True).parse_dex()

    assert dex.class_defs[0].superclass is None
    assert dex.class_defs[0].source_file is None
    assert dex.class_defs[0].raw_item.superclass_idx == 0xFFFFFFFF
    assert dex.class_defs[0].raw_item.source_file_idx == 0xFFFFFFFF


def test_class_def_interfaces():
    data = bytearray(get_test_dex())
    interfaces_off = len(data)
    data += b"\x01\x00\x00\x00\x02\x00\x00\x00"
    data[260:264] = interfaces_off.to_bytes(4, "little")
    data[32:36] = len(data).to_bytes(4, "little")
    data_size = int.from_bytes(data[104:108], "little") + 8
    data[104:108] = data_size.to_bytes(4, "little")
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data), no_lazy_load=True).parse_dex()
    interfaces = dex.class_defs[0].interfaces

    assert interfaces is not None
    assert interfaces.types == [dex.types[2]]
    assert interfaces.raw_item.offset == interfaces_off
    assert interfaces.raw_item.size == 6
    assert interfaces.raw_item.length == 1
    assert interfaces.raw_item.data == b"\x01\x00\x00\x00\x02\x00"


def test_class_def_truncated_record():
    dex = DexFile(get_test_dex()).parse_dex_prologue()
    dex.header.raw_item.class_defs_off = len(dex.data) - 16

    with pytest.raises(ValueError, match="Corrupted class definition"):
        dex.parse_class_defs()

    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS == 0


def test_class_def_annotations():
    data = bytearray(get_test_dex())
    annotations_off = len(data)
    data += (
        (annotations_off + 40).to_bytes(4, "little")
        + b"\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00"
        + b"\x00\x00\x00\x00"
        + (annotations_off + 40).to_bytes(4, "little")
        + b"\x02\x00\x00\x00"
        + (annotations_off + 40).to_bytes(4, "little")
        + b"\x02\x00\x00\x00"
        + (annotations_off + 44).to_bytes(4, "little")
        + b"\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00"
    )
    data[268:272] = annotations_off.to_bytes(4, "little")
    data[32:36] = len(data).to_bytes(4, "little")
    data_size = int.from_bytes(data[104:108], "little") + 52
    data[104:108] = data_size.to_bytes(4, "little")
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data), no_lazy_load=True).parse_dex()
    annotations = dex.class_defs[0].annotations

    assert annotations is not None
    assert annotations.offset == annotations_off
    assert annotations.size == 40
    assert annotations.data == data[annotations_off : annotations_off + 40]
    assert annotations.class_annotations_off == annotations_off + 40
    assert annotations.class_annotations is not None
    assert annotations.class_annotations.offset == annotations_off + 40
    assert annotations.class_annotations.entries == []
    assert annotations.fields_size == 1
    assert annotations.field_annotations[0].field_idx == 0
    assert annotations.field_annotations[0].annotations_off == annotations_off + 40
    assert annotations.field_annotations[0].annotations is not None
    assert annotations.field_annotations[0].annotations.offset == annotations_off + 40
    assert annotations.field_annotations[0].annotations.entries == []
    assert annotations.annotated_methods_size == 1
    assert annotations.method_annotations[0].method_idx == 2
    assert annotations.method_annotations[0].annotations is not None
    assert annotations.method_annotations[0].annotations.offset == annotations_off + 40
    assert annotations.method_annotations[0].annotations.entries == []
    assert annotations.annotated_parameters_size == 1
    assert annotations.parameter_annotations[0].method_idx == 2
    assert annotations.parameter_annotations[0].annotations is not None
    assert annotations.parameter_annotations[0].annotations.offset == annotations_off + 44
    assert annotations.parameter_annotations[0].annotations.entries == [None]

    dex.stream.seek(12)
    assert dex.parse_class_defs() == dex.class_defs
    assert dex.stream.tell() == 12


def test_class_def_invalid_annotations_offset():
    data = bytearray(get_test_dex())
    data[268:272] = len(data).to_bytes(4, "little")
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data))
    dex.types = dex.parse_types()
    dex.stream.seek(12)

    with pytest.raises(ValueError, match="Invalid annotations directory offset"):
        dex.parse_class_defs()

    assert dex.stream.tell() == 12
    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS == 0


def test_class_def_missing_static_values():
    data = bytearray(get_test_dex())
    data[276:280] = b"\x00\x00\x00\x00"
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data), no_lazy_load=True).parse_dex()

    assert dex.class_defs[0].static_values is None


def test_class_def_invalid_static_values_offset():
    data = bytearray(get_test_dex())
    data[276:280] = len(data).to_bytes(4, "little")
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data))
    dex.types = dex.parse_types()
    dex.stream.seek(12)

    with pytest.raises(ValueError, match="Invalid static values offset"):
        dex.parse_class_defs()

    assert dex.stream.tell() == 12
    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS == 0


def test_class_def_truncated_static_values():
    data = bytearray(get_test_dex())
    data[276:280] = (len(data) - 2).to_bytes(4, "little")
    data[-2:] = b"\x01\x04"
    data[12:32] = hashlib.sha1(data[32:]).digest()
    data[8:12] = zlib.adler32(data[12:]).to_bytes(4, "little")

    dex = DexFile(bytes(data))
    dex.types = dex.parse_types()
    dex.stream.seek(12)

    with pytest.raises(ValueError, match="Corrupted encoded value"):
        dex.parse_class_defs()

    assert dex.stream.tell() == 12
    assert dex.section_flags & dex.FLAG_PARSED_CLASS_DEFS == 0
