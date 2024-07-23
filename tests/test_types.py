import os

from pydex.dalvik import DexFile


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "strings.dex"), "rb") as test_dex:
        return test_dex.read()


def test_type_parse():
    dex = DexFile(get_test_dex(), no_lazy_load=True).parse_dex()
    types = dex.types

    # class name
    assert types[3].descriptor.value == "Ltest/klass;"
