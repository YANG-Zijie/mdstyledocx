from __future__ import annotations

from dataclasses import dataclass, field


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


@dataclass
class Block:
    kind: str
    spans: list[InlineElement] = field(default_factory=list)
    level: int = 0
    list_kind: str | None = None
    list_level: int = 0
    number: int | None = None


@dataclass
class Document:
    metadata: dict[str, str] = field(default_factory=dict)
    blocks: list[Block] = field(default_factory=list)
