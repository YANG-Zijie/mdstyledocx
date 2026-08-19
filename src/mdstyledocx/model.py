from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class InlineSpan:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


@dataclass
class ImageSpan:
    path: str
    alt_text: str = ""


InlineElement = InlineSpan | ImageSpan
TableCell = list[InlineElement]
TableRow = list[TableCell]


@dataclass
class Block:
    kind: str
    spans: list[InlineElement] = field(default_factory=list)
    level: int = 0
    list_kind: str | None = None
    list_level: int = 0
    number: int | None = None
    table_rows: list[TableRow] = field(default_factory=list)
    table_alignments: list[str | None] = field(default_factory=list)


@dataclass
class Document:
    metadata: dict[str, Any] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
