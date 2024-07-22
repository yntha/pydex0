import pytest
import os

from datastream import ByteOrder
from pydex.dalvik import DexFile
from pydex.exc import InvalidDalvikHeader


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "empty.dex"), "rb") as test_dex:
        return test_dex.read()


def get_modified_dex(mod_offset: int, mod_data: bytes) -> bytes:
    dex_data = get_test_dex()

    return dex_data[:mod_offset] + mod_data + dex_data[mod_offset + len(mod_data) :]


def test_header_parse():
    dex = DexFile(get_test_dex()).parse_dex()

    assert dex.header.version == 35
    assert dex.header.file_size == 140
    assert dex.header.checksum == 0xD9700BBE
    assert dex.header.signature == bytes.fromhex("1D9C3F88730D0ED6CAA377D4520465E7322D365A")
    assert dex.header.byte_order == ByteOrder.LITTLE_ENDIAN


def test_header_invalid_magic():
    dex_data = get_modified_dex(0, b"abcd\x0A")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_MAGIC_BYTES

    # check null byte
    dex_data = get_modified_dex(7, b"\x01")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_MAGIC_BYTES


def test_header_invalid_checksum():
    dex_data = get_modified_dex(8, b"\x00\x00\x00\x00")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_CHECKSUM


def test_header_invalid_header_size():
    dex_data = get_modified_dex(36, b"\x00\x00\x00\x00")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_HEADER_SIZE


def test_header_invalid_endian_tag():
    dex_data = get_modified_dex(40, b"\x00\x00\x00\x00")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_ENDIAN_TAG


def test_header_invalid_type_ids_size():
    dex_data = get_modified_dex(64, b"\xFF\xFF\xFF\xFF")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_TYPES_SIZE


def test_header_invalid_proto_ids_size():
    dex_data = get_modified_dex(72, b"\xFF\xFF\xFF\xFF")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_PROTOS_SIZE


def test_header_invalid_data_size():
    dex_data = get_modified_dex(94, b"\x05\x00\x00\x00")
    dex = DexFile(dex_data)

    with pytest.raises(InvalidDalvikHeader) as exc_info:
        dex.parse_dex()

        assert exc_info.value.code == InvalidDalvikHeader.INVALID_DATA_SIZE
