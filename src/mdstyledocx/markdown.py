from __future__ import annotations

import re
from pathlib import Path

from mdstyledocx.model import Block, Document, ImageSpan, InlineElement, InlineSpan

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*?)\s*$")
ORDERED_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*?)\s*$")
INLINE_TOKEN_RE = re.compile(r"(!\[[^\]]*]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")
PAGEBREAK_MARKERS = {"<!-- pagebreak -->", "<!--pagebreak-->", "\f", "\\f"}


def parse_markdown(text: str, base_path: Path | None = None) -> Document:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = normalized.split("\n")
    metadata, body_lines = _parse_frontmatter(lines)
    blocks = _parse_blocks(body_lines, base_path)

    has_title = any(block.kind == "heading" and block.level == 1 for block in blocks)
    if metadata.get("title") and not has_title:
        blocks.insert(0, Block(kind="heading", level=1, spans=parse_inline(metadata["title"], base_path)))

    return Document(metadata=metadata, blocks=blocks)


def parse_inline(text: str, base_path: Path | None = None) -> list[InlineElement]:
    spans: list[InlineElement] = []
    for token in INLINE_TOKEN_RE.split(text):
        if not token:
            continue
        image_match = IMAGE_RE.match(token)
        if image_match:
            spans.append(
                ImageSpan(
                    path=_resolve_asset_path(image_match.group(2), base_path),
                    alt_text=image_match.group(1),
                )
            )
        elif token.startswith("**") and token.endswith("**") and len(token) > 4:
            spans.append(InlineSpan(text=token[2:-2], bold=True))
        elif token.startswith("*") and token.endswith("*") and len(token) > 2:
            spans.append(InlineSpan(text=token[1:-1], italic=True))
        elif token.startswith("`") and token.endswith("`") and len(token) > 2:
            spans.append(InlineSpan(text=token[1:-1], code=True))
        else:
            spans.append(InlineSpan(text=token))
    return spans or [InlineSpan(text="")]


def _parse_frontmatter(lines: list[str]) -> tuple[dict[str, str], list[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines

    metadata: dict[str, str] = {}
    for index in range(1, len(lines)):
        current = lines[index].strip()
        if current == "---":
            return metadata, lines[index + 1 :]
        if ":" not in lines[index]:
            return {}, lines
        key, value = lines[index].split(":", 1)
        metadata[key.strip()] = value.strip()

    return {}, lines


def _parse_blocks(lines: list[str], base_path: Path | None) -> list[Block]:
    blocks: list[Block] = []
    index = 0

    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()

        if not stripped:
            index += 1
            continue

        if stripped in PAGEBREAK_MARKERS:
            blocks.append(Block(kind="page_break"))
            index += 1
            continue

        heading_match = HEADING_RE.match(raw)
        if heading_match:
            blocks.append(
                Block(
                    kind="heading",
                    level=len(heading_match.group(1)),
                    spans=parse_inline(heading_match.group(2), base_path),
                )
            )
            index += 1
            continue

        bullet_match = BULLET_RE.match(raw)
        if bullet_match:
            blocks.append(
                Block(
                    kind="list_item",
                    list_kind="bullet",
                    list_level=len(bullet_match.group(1).replace("\t", "    ")) // 2,
                    spans=parse_inline(bullet_match.group(2), base_path),
                )
            )
            index += 1
            continue

        ordered_match = ORDERED_RE.match(raw)
        if ordered_match:
            blocks.append(
                Block(
                    kind="list_item",
                    list_kind="ordered",
                    list_level=len(ordered_match.group(1).replace("\t", "    ")) // 2,
                    number=int(ordered_match.group(2)),
                    spans=parse_inline(ordered_match.group(3), base_path),
                )
            )
            index += 1
            continue

        paragraph_lines: list[str] = []
        while index < len(lines) and not _starts_new_block(lines[index]):
            paragraph_lines.append(_strip_blockquote(lines[index].rstrip()))
            index += 1

        blocks.append(
            Block(kind="paragraph", spans=parse_inline(_join_paragraph_lines(paragraph_lines), base_path))
        )

    return blocks


def _starts_new_block(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped in PAGEBREAK_MARKERS:
        return True
    if HEADING_RE.match(line):
        return True
    if BULLET_RE.match(line):
        return True
    if ORDERED_RE.match(line):
        return True
    return False


def _strip_blockquote(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith(">"):
        return stripped[1:].lstrip()
    return line.strip()


def _join_paragraph_lines(lines: list[str]) -> str:
    if not lines:
        return ""

    result = lines[0].strip()
    for line in lines[1:]:
        candidate = line.strip()
        if not candidate:
            continue
        if _needs_space(result[-1], candidate[0]):
            result += " " + candidate
        else:
            result += candidate
    return result


def _needs_space(previous_char: str, next_char: str) -> bool:
    return previous_char.isascii() and next_char.isascii() and (
        previous_char.isalnum() or previous_char in {")", "]"}
    ) and (next_char.isalnum() or next_char in {"(", "["})


def _resolve_asset_path(raw_path: str, base_path: Path | None) -> str:
    candidate = raw_path.strip().strip("<>").strip()
    path = Path(candidate)
    if path.is_absolute() or base_path is None:
        return str(path)
    return str((base_path / path).resolve())
