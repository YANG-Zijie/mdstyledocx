"""AIMD-compatible literal BibTeX references and deterministic citation ordering.

This deliberately supports literal fields, not BibTeX macros or TeX execution.
Unsupported constructs fail instead of silently dropping bibliographic data.
"""

from __future__ import annotations

import re

from mdstyledocx.model import Block, CitationSpan, Document, ReferenceEntry, ReferencesBlock

REFERENCE_ID_RE = re.compile(r'[^\s,{}()=#"|]+')


class _BibTeXParser:
    def __init__(self, source: str) -> None:
        self.source = source
        self.index = 0

    def error(self, message: str) -> ValueError:
        line = self.source.count("\n", 0, self.index) + 1
        return ValueError(f"Invalid refs BibTeX at line {line}: {message}")

    def skip_space(self) -> None:
        while self.index < len(self.source):
            if self.source[self.index].isspace():
                self.index += 1
            elif self.source[self.index] == "%":
                end = self.source.find("\n", self.index)
                self.index = len(self.source) if end < 0 else end + 1
            else:
                break

    def expect(self, token: str) -> None:
        self.skip_space()
        if not self.source.startswith(token, self.index):
            raise self.error(f"expected {token!r}")
        self.index += len(token)

    def identifier(self, pattern: str, description: str) -> str:
        self.skip_space()
        match = re.match(pattern, self.source[self.index :])
        if match is None:
            raise self.error(f"expected {description}")
        self.index += match.end()
        return match.group()

    def value(self) -> str:
        self.skip_space()
        if self.index >= len(self.source):
            raise self.error("missing field value")
        opener = self.source[self.index]
        if opener not in '{"':
            return self.identifier(r"[0-9]+", "a braced, quoted, or numeric literal (macros are unsupported)")

        self.index += 1
        start = self.index
        depth = 1 if opener == "{" else 0
        while self.index < len(self.source):
            char = self.source[self.index]
            if char == "\\":
                self.index += 2
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth < 0:
                    raise self.error("unbalanced field braces")
                if opener == "{" and depth == 0:
                    break
            elif char == '"' and opener == '"' and depth == 0:
                break
            self.index += 1
        else:
            raise self.error("unterminated field value")
        raw = self.source[start : self.index]
        self.index += 1
        # Protection braces are BibTeX syntax; escaped punctuation is literal.
        value = re.sub(r"\\([{}%&_#$\"\\])|[{}]", lambda m: m.group(1) or "", raw)
        return re.sub(r"\s+", " ", value).strip()

    def parse(self) -> list[ReferenceEntry]:
        entries: list[ReferenceEntry] = []
        self.skip_space()
        while self.index < len(self.source):
            self.expect("@")
            entry_type = self.identifier(r"[A-Za-z][\w-]*", "entry type").lower()
            if entry_type in {"string", "preamble", "comment"}:
                raise self.error(f"@{entry_type} is unsupported; use literal entries and % comments")
            self.skip_space()
            if self.index >= len(self.source) or self.source[self.index] not in "{(":
                raise self.error("expected '{' or '(' after entry type")
            closer = "}" if self.source[self.index] == "{" else ")"
            self.index += 1
            reference_id = self.identifier(REFERENCE_ID_RE.pattern, "reference id")
            self.expect(",")
            fields: dict[str, str] = {}
            while True:
                self.skip_space()
                if self.source.startswith(closer, self.index):
                    self.index += 1
                    break
                key = self.identifier(r"[A-Za-z][\w-]*", "field name").lower()
                if key in fields:
                    raise self.error(f"duplicate field {key!r} in {reference_id!r}")
                self.expect("=")
                fields[key] = self.value()
                self.skip_space()
                if self.source.startswith(closer, self.index):
                    self.index += 1
                    break
                self.expect(",")
            if not fields.get("title"):
                raise self.error(f"reference {reference_id!r} must have a non-empty title")
            entries.append(ReferenceEntry(reference_id, entry_type, fields))
            self.skip_space()
        if not entries:
            raise self.error("refs block must contain at least one entry")
        return entries


def parse_references(source: str) -> list[ReferenceEntry]:
    return _BibTeXParser(source).parse()


def ordered_references(document: Document, order: str = "first-citation") -> list[ReferenceEntry]:
    """Validate IDs and return entries without changing source or AST order."""
    if order not in {"first-citation", "source"}:
        raise ValueError(f"Unsupported citation order {order!r}")
    entries: dict[str, ReferenceEntry] = {}
    citations: dict[str, None] = {}
    for block in document.blocks:
        if isinstance(block, ReferencesBlock):
            for entry in block.entries:
                if entry.reference_id in entries:
                    raise ValueError(f'Duplicate reference id "{entry.reference_id}"')
                entries[entry.reference_id] = entry
        elif isinstance(block, Block):
            spans = [*block.spans]
            for row in block.table_rows:
                for cell in row:
                    spans.extend(cell)
            for span in spans:
                if isinstance(span, CitationSpan):
                    for reference_id in span.reference_ids:
                        citations.setdefault(reference_id, None)
    missing = citations.keys() - entries.keys()
    if missing:
        raise ValueError(f"Unknown cite target(s): {', '.join(sorted(missing))}")
    if order == "source":
        return list(entries.values())
    ids = dict.fromkeys([*citations, *entries])
    return [entries[reference_id] for reference_id in ids]
