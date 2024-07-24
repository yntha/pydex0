import json

from dataclasses import asdict
from typing import Any

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


def dump_model_json(model: Any):
    """Dump a model to a JSON string.

    Args:
        Any model: The model to dump to a JSON string. Must be a dataclass.
    """

    return json.dumps(asdict(model), indent=2, cls=ModelEncoder)
