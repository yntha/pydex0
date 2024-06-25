import os

from pydex.dalvik import DexFile


def get_test_dex() -> bytes:
    root_dir = os.getcwd()

    with open(os.path.join(root_dir, "resources", "dex-files", "strings.dex"), "rb") as test_dex:
        return test_dex.read()


def get_modified_dex(mod_offset: int, mod_data: bytes) -> bytes:
    dex_data = get_test_dex()

    return dex_data[:mod_offset] + mod_data + dex_data[mod_offset + len(mod_data) :]


def test_string_parse():
    dex = DexFile(get_test_dex()).parse_dex()
    strings = dex.load_all_strings()

    # static final field value
    assert strings[1].raw_item.size == 9
    assert strings[1].raw_item.utf16_size == 8
    assert strings[1].string_id.id_number == 1
    assert strings[1].value == "Anthy :)"

    # method name
    assert strings[10].raw_item.size == 11
    assert strings[10].raw_item.utf16_size == 10
    assert strings[10].string_id.id_number == 10
    assert strings[10].value == "helloWorld"

    # const-string
    assert strings[4].raw_item.size == 16
    assert strings[4].raw_item.utf16_size == 15
    assert strings[4].string_id.id_number == 4
    assert strings[4].value == "Hello World! :)"

    # field name
    assert strings[3].raw_item.size == 10
    assert strings[3].raw_item.utf16_size == 9
    assert strings[3].string_id.id_number == 3
    assert strings[3].value == "CONST_STR"

    # class(type) name
    assert strings[8].raw_item.size == 13
    assert strings[8].raw_item.utf16_size == 12
    assert strings[8].string_id.id_number == 8
    assert strings[8].value == "Ltest/klass;"


def test_fetch_single_string():
    dex = DexFile(get_test_dex())

    # const-string
    const_string_ref = dex.get_string_by_id(4)
    const_string = const_string_ref.load(dex.stream)

    assert const_string.value == "Hello World! :)"
