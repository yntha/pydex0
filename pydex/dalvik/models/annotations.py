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


@dataclass
class DalvikAnnotationSet(DalvikRawItem):
    """
    A dataclass that represents an ``annotation_set_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::annotation_set_item <https://source.android.com/docs/core/runtime/dex-format#annotation-set-item>`_
    """

    #: Size of the set, in entries
    length: int  # 4 bytes

    #: Elements of the set.
    entries: list[DalvikAnnotation]

    @classmethod
    def from_stream(cls, stream: DeserializingStream) -> DalvikAnnotationSet:
        """Read an annotation set from a stream.

        Args:
            DeserializingStream stream: The stream to read from.
        """
        clone_stream = stream.clone()
        clone_stream.seek(stream.tell())

        try:
            offset = clone_stream.tell()
            length = clone_stream.read_uint32()
            if length > clone_stream.remaining() // 4:
                raise ValueError("Corrupted annotation set")

            annotation_offsets = []
            for _ in range(length):
                annotation_offsets.append(clone_stream.read_uint32())

            size = clone_stream.tell() - offset
            data = clone_stream.seekpeek(offset, size)
            entries = []

            for annotation_off in annotation_offsets:
                if annotation_off == 0 or annotation_off >= clone_stream.size():
                    raise ValueError("Invalid annotation offset")

                clone_stream.seek(annotation_off)
                entries.append(DalvikAnnotation.from_stream(clone_stream))

            return cls(offset, size, data, length, entries)
        finally:
            clone_stream.close()
