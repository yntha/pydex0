import os

from pydex.dalvik import DexFile


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "min.dex"), "rb") as test_dex:
        return test_dex.read()


def test_method_parse():
    dex = DexFile(get_test_dex(), no_lazy_load=True).parse_dex()
    methods = dex.methods

    assert str(methods[2].class_def) == "Ltest/klass;"
    assert str(methods[2].name) == "helloWorld"
    assert str(methods[2].proto) == "(Ljava/lang/Object;)V"

    assert str(methods[0].class_def) == "Ljava/lang/Object;"
    assert str(methods[0].name) == "<init>"
    assert str(methods[0].proto) == "()V"

    assert str(methods[1].class_def) == "Ltest/klass;"
    assert str(methods[1].name) == "<init>"
    assert str(methods[1].proto) == "()V"
