import json

from dataclasses import asdict
from typing import Any, cast

from pydex.dalvik.models.dalvik import (
    DalvikRawItem,
    DalvikHeader,
    DalvikHeaderItem,
    DalvikStringItem,
    DalvikStringData,
    DalvikStringID,
    LazyDalvikString,
    DalvikTypeID,
    DalvikTypeItem,
    DalvikTypeList,
    DalvikProtoID,
    DalvikProtoIDItem,
    DalvikTypeListItem,
    DalvikField,
    DalvikFieldItem,
)


class ModelEncoder(json.JSONEncoder):
    """Custom JSON encoder for encoding models.

    This class extends the ``json.JSONEncoder`` class and provides custom encoding logic for handling ``bytes`` objects.
    It converts ```bytes``` objects to hexadecimal strings before encoding them to JSON.
    """

    def default(self, o: Any) -> Any:
        if isinstance(o, bytes):
            return o.hex()

        return super().default(o)

    def encode(self, o: Any) -> str:
        if isinstance(o, bytes):
            o = o.hex()

        return super().encode(o)


def custom_dict_factory(data: list[tuple[str, Any]]) -> Any:
    """Custom dictionary factory for dalvik model classes.

    This function manipulates certain fields in the dalvik model classes before converting them to a dictionary. These
    are the list of fields that are manipulated and their corresponding manipulation:

    - ``string_data``: Convert the bytes object into a string.

    More fields can be added to this function to make the JSON output more human-readable.

    Args:
        list[tuple[str, Any]] data: The dataclass fields to convert.
    """

    for idx, item in enumerate(data):
        key, value = item

        if key == "string_data":
            data[idx] = (key, ''.join([chr(c) for c in cast(bytes, value)]))

    return dict(data)


def dump_model_json(model: Any) -> str:
    """Dump a model to a JSON string.

    Args:
        Any model: The model to dump to a JSON string. Must be a dataclass.
    """

    return json.dumps(asdict(model, dict_factory=custom_dict_factory), indent=2, cls=ModelEncoder)
