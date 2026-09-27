from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import ClassVar

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


@dataclass
class DalvikAnnotationSetRefList(DalvikRawItem):
    """
    A dataclass that represents an ``annotation_set_ref_list`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::annotation_set_ref_list <https://source.android.com/docs/core/runtime/dex-format#annotation-set-ref-list>`_
    """

    #: Size of the list, in entries.
    length: int  # 4 bytes

    #: Elements of the list.
    entries: list[DalvikAnnotationSet | None]

    @classmethod
    def from_stream(cls, stream: DeserializingStream) -> DalvikAnnotationSetRefList:
        """Read an annotation set reference list from a stream.

        Args:
            DeserializingStream stream: The stream to read from.
        """
        clone_stream = stream.clone()
        clone_stream.seek(stream.tell())

        try:
            offset = clone_stream.tell()
            length = clone_stream.read_uint32()
            if length > clone_stream.remaining() // 4:
                raise ValueError("Corrupted annotation set reference list")

            annotation_offsets = []
            for _ in range(length):
                annotation_offsets.append(clone_stream.read_uint32())

            size = clone_stream.tell() - offset
            data = clone_stream.seekpeek(offset, size)
            entries = []

            for annotations_off in annotation_offsets:
                if annotations_off == 0:
                    entries.append(None)
                    continue
                if annotations_off >= clone_stream.size():
                    raise ValueError("Invalid annotation set offset")

                clone_stream.seek(annotations_off)
                entries.append(DalvikAnnotationSet.from_stream(clone_stream))

            return cls(offset, size, data, length, entries)
        finally:
            clone_stream.close()


@dataclass
class DalvikFieldAnnotation(DalvikRawItem):
    """A dataclass that represents a ``field_annotation`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::field_annotation <https://source.android.com/docs/core/runtime/dex-format#field-annotation>`_
    """

    struct_size: ClassVar[int] = 0x08

    #: Index into the ``field_ids`` list for the identity of the field being annotated.
    field_idx: int  # 4 bytes

    #: Offset from the start of the file to the list of annotations for the field.
    annotations_off: int  # 4 bytes

    #: List of annotations for the field.
    annotations: DalvikAnnotationSet | None = None


@dataclass
class DalvikMethodAnnotation(DalvikRawItem):
    """A dataclass that represents a ``method_annotation`` in a dex file.
    
    .. admonition:: Source
        :class: seealso

        `dex_format::method_annotation <https://source.android.com/docs/core/runtime/dex-format#method-annotation>`_
    """

    struct_size: ClassVar[int] = 0x08

    #: Index into the ``method_ids`` list for the identity of the method being annotated.
    method_idx: int  # 4 bytes

    #: Offset from the start of the file to the list of annotations for the method.
    annotations_off: int  # 4 bytes

    #: List of annotations for the method.
    annotations: DalvikAnnotationSet | None = None


@dataclass
class DalvikParameterAnnotation(DalvikRawItem):
    """A dataclass that represents a ``parameter_annotation`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::parameter_annotation <https://source.android.com/docs/core/runtime/dex-format#parameter-annotation>`_
    """

    struct_size: ClassVar[int] = 0x08

    #: Index into the ``method_ids`` list for the identity of the method whose parameters are being annotated.
    method_idx: int  # 4 bytes

    #: Offset from the start of the file to the list of annotations for the method parameters.
    annotations_off: int  # 4 bytes

    #: List of annotations for the method parameters.
    annotations: DalvikAnnotationSetRefList | None = None


@dataclass
class DalvikAnnotationsDirectory(DalvikRawItem):
    """
    A dataclass that represents an ``annotations_directory_item`` in a dex file.

    .. admonition:: Source
        :class: seealso

        `dex_format::annotations_directory_item <https://source.android.com/docs/core/runtime/dex-format#annotations-directory-item>`_
    """

    #: Offset from the start of the file to the annotations made directly on the class.
    class_annotations_off: int  # 4 bytes

    #: Count of fields annotated by this item.
    fields_size: int  # 4 bytes

    #: Count of methods annotated by this item.
    annotated_methods_size: int  # 4 bytes

    #: Count of method parameter lists annotated by this item.
    annotated_parameters_size: int  # 4 bytes

    #: List of associated field annotations.
    field_annotations: list[DalvikFieldAnnotation]

    #: List of associated method annotations.
    method_annotations: list[DalvikMethodAnnotation]

    #: List of associated method parameter annotations.
    parameter_annotations: list[DalvikParameterAnnotation]

    #: Annotations made directly on the class.
    class_annotations: DalvikAnnotationSet | None = None

    @classmethod
    def from_stream(cls, stream: DeserializingStream) -> DalvikAnnotationsDirectory:
        """Read an annotations directory from a stream.

        Args:
            DeserializingStream stream: The stream to read from.
        """
        clone_stream = stream.clone()
        clone_stream.seek(stream.tell())

        try:
            offset = clone_stream.tell()
            if clone_stream.remaining() < 16:
                raise ValueError("Corrupted annotations directory")

            class_annotations_off = clone_stream.read_uint32()
            fields_size = clone_stream.read_uint32()
            annotated_methods_size = clone_stream.read_uint32()
            annotated_parameters_size = clone_stream.read_uint32()

            records_size = (
                fields_size * DalvikFieldAnnotation.struct_size
                + annotated_methods_size * DalvikMethodAnnotation.struct_size
                + annotated_parameters_size * DalvikParameterAnnotation.struct_size
            )
            if records_size > clone_stream.remaining():
                raise ValueError("Corrupted annotations directory")

            field_annotations = []
            for _ in range(fields_size):
                field_off = clone_stream.tell()
                field_idx = clone_stream.read_uint32()
                annotations_off = clone_stream.read_uint32()
                field_annotations.append(
                    DalvikFieldAnnotation(
                        field_off,
                        DalvikFieldAnnotation.struct_size,
                        clone_stream.seekpeek(field_off, DalvikFieldAnnotation.struct_size),
                        field_idx,
                        annotations_off,
                    )
                )

            method_annotations = []
            for _ in range(annotated_methods_size):
                method_off = clone_stream.tell()
                method_idx = clone_stream.read_uint32()
                annotations_off = clone_stream.read_uint32()
                method_annotations.append(
                    DalvikMethodAnnotation(
                        method_off,
                        DalvikMethodAnnotation.struct_size,
                        clone_stream.seekpeek(method_off, DalvikMethodAnnotation.struct_size),
                        method_idx,
                        annotations_off,
                    )
                )

            parameter_annotations = []
            for _ in range(annotated_parameters_size):
                parameter_off = clone_stream.tell()
                method_idx = clone_stream.read_uint32()
                annotations_off = clone_stream.read_uint32()
                parameter_annotations.append(
                    DalvikParameterAnnotation(
                        parameter_off,
                        DalvikParameterAnnotation.struct_size,
                        clone_stream.seekpeek(parameter_off, DalvikParameterAnnotation.struct_size),
                        method_idx,
                        annotations_off,
                    )
                )

            size = clone_stream.tell() - offset
            data = clone_stream.seekpeek(offset, size)

            if class_annotations_off != 0:
                if class_annotations_off > clone_stream.size() - 4:
                    raise ValueError("Invalid class annotations offset")

                clone_stream.seek(class_annotations_off)
                class_annotations = DalvikAnnotationSet.from_stream(clone_stream)
            else:
                class_annotations = None

            for field_annotation in field_annotations:
                annotations_off = field_annotation.annotations_off
                if annotations_off == 0 or annotations_off > clone_stream.size() - 4:
                    raise ValueError("Invalid field annotations offset")

                clone_stream.seek(annotations_off)
                field_annotation.annotations = DalvikAnnotationSet.from_stream(clone_stream)

            for method_annotation in method_annotations:
                annotations_off = method_annotation.annotations_off
                if annotations_off == 0 or annotations_off > clone_stream.size() - 4:
                    raise ValueError("Invalid method annotations offset")

                clone_stream.seek(annotations_off)
                method_annotation.annotations = DalvikAnnotationSet.from_stream(clone_stream)

            for parameter_annotation in parameter_annotations:
                annotations_off = parameter_annotation.annotations_off
                if annotations_off == 0 or annotations_off > clone_stream.size() - 4:
                    raise ValueError("Invalid parameter annotations offset")

                clone_stream.seek(annotations_off)
                parameter_annotation.annotations = DalvikAnnotationSetRefList.from_stream(clone_stream)

            return cls(
                offset,
                size,
                data,
                class_annotations_off,
                fields_size,
                annotated_methods_size,
                annotated_parameters_size,
                field_annotations,
                method_annotations,
                parameter_annotations,
                class_annotations,
            )
        finally:
            clone_stream.close()
