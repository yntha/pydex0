import asyncio
import os

from pydex.dalvik import DexFile
from pydex.dalvik.models import LazyDalvikString


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "min.dex"), "rb") as test_dex:
        return test_dex.read()


def test_proto_parse():
    dex = DexFile(get_test_dex(), no_lazy_load=True).parse_dex()
    protos = dex.protos

    # method proto
    assert protos[1].shorty.value == "VL"
    assert protos[1].return_type.descriptor.value == "V"
    assert protos[1].parameters is not None
    assert protos[1].parameters.types[0].descriptor.value == "Ljava/lang/Object;"
    assert protos[1].parameter_list == ["Ljava/lang/Object;"]
    assert protos[1].parameters.raw_item.length == 1
    assert protos[1].parameters.raw_item.size == 6
    assert protos[1].parameters.raw_item.data == b"\x01\x00\x00\x00\x01\x00"


def test_proto_parse_lazy_strings():
    dex = DexFile(get_test_dex()).parse_dex()
    protos = dex.protos

    assert protos[0].parameter_list is None
    assert protos[1].parameter_list == ["Ljava/lang/Object;"]
    assert protos[1].parameters is not None
    assert isinstance(protos[1].parameters.types[0].descriptor, LazyDalvikString)
    assert isinstance(protos[1].shorty, LazyDalvikString)
    assert isinstance(dex.strings[0], LazyDalvikString)
    assert len(dex.class_defs) == 1


def test_proto_parse_async_lazy_strings():
    dex = DexFile(get_test_dex())
    dex.types = dex.parse_types()
    dex.stream.seek(12)

    protos = asyncio.run(dex.parse_protos_async())

    assert protos[1].parameter_list == ["Ljava/lang/Object;"]
    assert protos[1].parameters is not None
    assert isinstance(protos[1].parameters.types[0].descriptor, LazyDalvikString)
    assert dex.stream.tell() == 12
