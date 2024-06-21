from __future__ import annotations

import typing

from dataclasses import dataclass


@dataclass
class DalvikRawItem:
    """
    A class that represents a low-level item in a dex file.
    """

    offset: int
    size: int
    data: bytes


@dataclass
class DalvikItem:
    """
    A class that represents a high-level item in a dex file.
    """

    raw_item: DalvikRawItem
