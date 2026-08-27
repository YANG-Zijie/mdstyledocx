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


@dataclass
class FigureReferenceSpan:
    figure_id: str


InlineElement = InlineSpan | ImageSpan | FigureReferenceSpan
TableCell = list[InlineElement]
TableRow = list[TableCell]


@dataclass
class Block:
    kind: str
    spans: list[InlineElement] = field(default_factory=list)
    level: int = 0
    blank_lines: int = 1
    list_kind: str | None = None
    list_level: int = 0
    number: int | None = None
    table_rows: list[TableRow] = field(default_factory=list)
    table_alignments: list[str | None] = field(default_factory=list)


@dataclass
class FigureBlock:
    figure_id: str | None
    image: ImageSpan
    title: str | None = None
    legend: str | None = None
    kind: str = field(default="figure", init=False)


DocumentBlock = Block | FigureBlock


@dataclass
class Document:
    metadata: dict[str, Any] = field(default_factory=dict)
    blocks: list[DocumentBlock] = field(default_factory=list)
