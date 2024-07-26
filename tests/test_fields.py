import os

from pydex.dalvik import DexFile


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "min.dex"), "rb") as test_dex:
        return test_dex.read()


def test_field_parse():
    dex = DexFile(get_test_dex(), no_lazy_load=True).parse_dex()
    fields = dex.fields

    # static final field
    assert str(fields[0].class_def) == "Ltest/klass;"
    assert str(fields[0].type) == "I"
    assert str(fields[0].name) == "CONSTANT"

    assert str(fields[1].class_def) == "Ltest/klass;"
    assert str(fields[1].type) == "Ljava/lang/String;"
    assert str(fields[1].name) == "CONST_STR"
