import os

from pydex.dalvik import DexFile


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
    assert protos[1].parameters.types[0].descriptor.value == "Ljava/lang/Object;"
    assert protos[1].parameter_list == ["Ljava/lang/Object;"]
