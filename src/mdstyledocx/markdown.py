from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from mdstyledocx.model import Block, Document, ImageSpan, InlineElement, InlineSpan

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
BULLET_RE = re.compile(r"^(\s*)[-*+]\s+(.*?)\s*$")
ORDERED_RE = re.compile(r"^(\s*)(\d+)\.\s+(.*?)\s*$")
INLINE_TOKEN_RE = re.compile(r"(!\[[^\]]*]\([^)]+\)|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")
PAGEBREAK_MARKERS = {"<!-- pagebreak -->", "<!--pagebreak-->", "\f", "\\f"}
TABLE_SEPARATOR_RE = re.compile(r"^:?-{3,}:?$")


def parse_markdown(text: str, base_path: Path | None = None) -> Document:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
    lines = normalized.split("\n")
    metadata, body_lines = _parse_frontmatter(lines)
    blocks = _parse_blocks(body_lines, base_path)

    has_title = any(block.kind == "heading" and block.level == 1 for block in blocks)
    if metadata.get("title") and not has_title:
        blocks.insert(
            0,
            Block(
                kind="heading",
                level=1,
                spans=parse_inline(str(metadata["title"]), base_path),
            ),
        )

    if (raw_date := metadata.get("date")) not in (None, ""):
        date_block = Block(
            kind="date",
            spans=parse_inline(str(raw_date), base_path),
        )
        title_index = next(
            (
                index
                for index, block in enumerate(blocks)
                if block.kind == "heading" and block.level == 1
            ),
            None,
        )
        blocks.insert(0 if title_index is None else title_index + 1, date_block)

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


def _parse_frontmatter(lines: list[str]) -> tuple[dict[str, Any], list[str]]:
    if not lines or lines[0].strip() != "---":
        return {}, lines

    for index in range(1, len(lines)):
        if lines[index].strip() != "---":
            continue

        source = "\n".join(lines[1:index])
        try:
            metadata = yaml.safe_load(source) or {}
        except yaml.YAMLError as error:
            raise ValueError(f"Invalid YAML frontmatter: {error}") from error

        if not isinstance(metadata, dict):
            raise TypeError("YAML frontmatter must contain a mapping at the top level")
        return metadata, lines[index + 1 :]

    raise ValueError("Unterminated YAML frontmatter")


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

        table_result = _parse_table(lines, index, base_path)
        if table_result is not None:
            table, index = table_result
            blocks.append(table)
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
        while index < len(lines) and not _starts_new_block(lines, index):
            paragraph_lines.append(_strip_blockquote(lines[index].rstrip()))
            index += 1

        blocks.append(
            Block(kind="paragraph", spans=parse_inline(_join_paragraph_lines(paragraph_lines), base_path))
        )

    return blocks


def _starts_new_block(lines: list[str], index: int) -> bool:
    line = lines[index]
    stripped = line.strip()
    if not stripped:
        return True
    if stripped in PAGEBREAK_MARKERS:
        return True
    if HEADING_RE.match(line):
        return True
    if _is_table_start(lines, index):
        return True
    if BULLET_RE.match(line):
        return True
    return bool(ORDERED_RE.match(line))


def _parse_table(
    lines: list[str], index: int, base_path: Path | None
) -> tuple[Block, int] | None:
    if not _is_table_start(lines, index):
        return None

    header_cells = _split_table_row(lines[index])
    separators = _split_table_row(lines[index + 1])
    column_count = len(header_cells)
    if len(separators) != column_count:
        raise ValueError(
            "Markdown table header and separator must have the same column count"
        )

    alignments = [_table_alignment(value) for value in separators]
    rows = [[parse_inline(value, base_path) for value in header_cells]]
    index += 2

    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped or "|" not in stripped:
            break
        cells = _split_table_row(lines[index])
        if len(cells) != column_count:
            raise ValueError(
                "Markdown table rows must have the same column count as the header"
            )
        rows.append([parse_inline(value, base_path) for value in cells])
        index += 1

    return (
        Block(
            kind="table",
            table_rows=rows,
            table_alignments=alignments,
        ),
        index,
    )


def _is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines) or "|" not in lines[index]:
        return False
    separators = _split_table_row(lines[index + 1])
    return bool(separators) and all(
        TABLE_SEPARATOR_RE.fullmatch(value) for value in separators
    )


def _split_table_row(line: str) -> list[str]:
    source = line.strip()
    if source.startswith("|"):
        source = source[1:]
    if source.endswith("|") and not source.endswith("\\|"):
        source = source[:-1]

    cells: list[str] = []
    current: list[str] = []
    in_code = False
    index = 0
    while index < len(source):
        character = source[index]
        if character == "`":
            in_code = not in_code
            current.append(character)
            index += 1
            continue
        if (
            character == "\\"
            and index + 1 < len(source)
            and source[index + 1] == "|"
        ):
            current.append("|")
            index += 2
            continue
        if character == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(character)
        index += 1

    cells.append("".join(current).strip())
    return cells


def _table_alignment(separator: str) -> str | None:
    left = separator.startswith(":")
    right = separator.endswith(":")
    if left and right:
        return "center"
    if right:
        return "right"
    if left:
        return "left"
    return None


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
