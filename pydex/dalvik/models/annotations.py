from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from datastream import DeserializingStream

from pydex.dalvik.models.base import DalvikRawItem
from pydex.dalvik.models.encoded_items import DalvikEncodedAnnotation


class DalvikAnnotationVisibility(IntEnum):
    """Enumeration of the visibility values for an ``annotation_item``."""

    VISIBILITY_BUILD = 0x00
    """Intended only to be visible at build time."""

    VISIBILITY_RUNTIME = 0x01
    """Intended to be visible at runtime."""

    VISIBILITY_SYSTEM = 0x02
    """Intended to be visible at runtime, but only to the underlying system."""


@dataclass
class DalvikAnnotation(DalvikRawItem):
    """
    A dataclass that represents an ``annotation_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::annotation_item <https://source.android.com/docs/core/runtime/dex-format#annotation-item>`_
    """

    #: Intended visibility of this annotation.
    visibility: DalvikAnnotationVisibility  # 1 byte

    #: Encoded annotation contents.
    annotation: DalvikEncodedAnnotation

    @classmethod
    def from_stream(cls, stream: DeserializingStream) -> DalvikAnnotation:
        """Read an annotation item from a stream.

        Args:
            DeserializingStream stream: The stream to read from.
        """
        clone_stream = stream.clone()
        clone_stream.seek(stream.tell())

        try:
            offset = clone_stream.tell()
            visibility = DalvikAnnotationVisibility(clone_stream.read_uint8())

            annotation = DalvikEncodedAnnotation.from_stream(clone_stream)
            size = clone_stream.tell() - offset
            data = clone_stream.seekpeek(offset, size)

            return cls(offset, size, data, visibility, annotation)
        finally:
            clone_stream.close()
