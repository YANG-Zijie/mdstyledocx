from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from io import BytesIO

from docx import Document as WordDocument
from docx.document import Document as WordprocessingDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt, Twips

from mdstyledocx.model import Block, Document, ImageSpan, InlineElement, InlineSpan
from mdstyledocx.presets import Preset, Style


@dataclass
class BuildState:
    preset: Preset
    heading_counters: dict[int, int] = field(default_factory=dict)


def build_docx(document: Document, preset: Preset) -> bytes:
    word_document = WordDocument()
    _configure_document(word_document, preset)
    _set_core_properties(word_document, _document_title(document))

    state = BuildState(preset=preset)
    for block in document.blocks:
        _append_block(word_document, block, state)

    buffer = BytesIO()
    word_document.save(buffer)
    return buffer.getvalue()


def _configure_document(word_document: WordprocessingDocument, preset: Preset) -> None:
    section = word_document.sections[0]
    section.page_width = Twips(preset.page.width)
    section.page_height = Twips(preset.page.height)
    section.top_margin = Twips(preset.page.margin_top)
    section.right_margin = Twips(preset.page.margin_right)
    section.bottom_margin = Twips(preset.page.margin_bottom)
    section.left_margin = Twips(preset.page.margin_left)
    section.header_distance = Twips(preset.page.header)
    section.footer_distance = Twips(preset.page.footer)
    section.gutter = Twips(preset.page.gutter)


def _set_core_properties(word_document: WordprocessingDocument, title: str) -> None:
    properties = word_document.core_properties
    properties.title = title
    properties.author = "mdstyledocx"
    properties.last_modified_by = "mdstyledocx"
    now = datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)
    properties.created = now
    properties.modified = now


def _document_title(document: Document) -> str:
    if document.metadata.get("title"):
        return document.metadata["title"]
    for block in document.blocks:
        if block.kind == "heading" and block.level == 1:
            return "".join(span.text for span in block.spans if isinstance(span, InlineSpan)).strip()
    return "Document"


def _append_block(word_document: WordprocessingDocument, block: Block, state: BuildState) -> None:
    if block.kind == "page_break":
        word_document.add_page_break()
        return

    rendered_spans = _rendered_spans(block, state)
    style = _resolve_style(block, state.preset)
    if _spans_have_image(rendered_spans):
        style = replace(style, line=240, line_rule="auto")

    paragraph = word_document.add_paragraph()
    _apply_paragraph_style(paragraph, style)

    if block.kind == "list_item":
        prefix = "• " if block.list_kind == "bullet" else f"{block.number}. "
        _add_text_run(paragraph, InlineSpan(text=prefix), style)

    for span in rendered_spans:
        if isinstance(span, ImageSpan):
            _add_image_run(paragraph, span, state)
        elif span.text:
            _add_text_run(paragraph, span, style)

    if not paragraph.runs:
        paragraph.add_run("")


def _resolve_style(block: Block, preset: Preset) -> Style:
    if block.kind == "heading":
        key = {1: "title", 2: "heading1", 3: "heading2"}.get(block.level, "heading3")
        return preset.styles[key]

    base = preset.styles["body"]
    if block.kind == "list_item":
        left_indent = (
            preset.list_settings.base_left_indent
            + block.list_level * preset.list_settings.level_step
        )
        return replace(
            base,
            first_line_indent=0,
            left_indent=left_indent,
            hanging=preset.list_settings.hanging,
        )

    return base


def _apply_paragraph_style(paragraph, style: Style) -> None:
    alignment_map = {
        "left": WD_ALIGN_PARAGRAPH.LEFT,
        "center": WD_ALIGN_PARAGRAPH.CENTER,
        "right": WD_ALIGN_PARAGRAPH.RIGHT,
        "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
        "both": WD_ALIGN_PARAGRAPH.JUSTIFY,
    }
    if style.align:
        paragraph.alignment = alignment_map[style.align]

    paragraph_format = paragraph.paragraph_format
    paragraph_format.space_before = Twips(style.spacing_before)
    paragraph_format.space_after = Twips(style.spacing_after)
    paragraph_format.left_indent = Twips(style.left_indent)

    if style.hanging:
        paragraph_format.first_line_indent = Twips(-style.hanging)
    else:
        paragraph_format.first_line_indent = Twips(style.first_line_indent)

    if style.line_rule == "exact":
        paragraph_format.line_spacing = Pt(style.line / 20)
        paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    elif style.line_rule == "auto":
        paragraph_format.line_spacing = style.line / 240
    else:
        paragraph_format.line_spacing = style.line / 240


def _add_text_run(paragraph, span: InlineSpan, style: Style) -> None:
    run = paragraph.add_run(span.text)
    font_ascii = style.font_ascii
    font_east_asia = style.font_east_asia
    bold = style.bold or span.bold
    italic = style.italic or span.italic

    if span.code:
        font_ascii = "Consolas"
        font_east_asia = "等线"

    run.font.name = font_ascii
    run.font.size = Pt(style.size_half_points / 2)
    run.bold = bold
    run.italic = italic

    r_fonts = run._element.get_or_add_rPr().get_or_add_rFonts()
    r_fonts.set(qn("w:ascii"), font_ascii)
    r_fonts.set(qn("w:hAnsi"), font_ascii)
    r_fonts.set(qn("w:eastAsia"), font_east_asia)


def _add_image_run(paragraph, span: ImageSpan, state: BuildState) -> None:
    run = paragraph.add_run()
    inline_shape = run.add_picture(span.path)
    max_width = _max_image_width(state.preset)
    if inline_shape.width > max_width:
        scale = max_width / inline_shape.width
        inline_shape.width = max_width
        inline_shape.height = int(inline_shape.height * scale)

    description = span.alt_text or os.path.basename(span.path)
    inline_shape._inline.docPr.set("descr", description)
    inline_shape._inline.docPr.set("name", description)


def _max_image_width(preset: Preset) -> int:
    return Twips(preset.page.width - preset.page.margin_left - preset.page.margin_right)


def _spans_have_image(spans: list[InlineElement]) -> bool:
    return any(isinstance(span, ImageSpan) for span in spans)


def _rendered_spans(block: Block, state: BuildState) -> list[InlineElement]:
    if block.kind != "heading":
        return block.spans

    scheme = state.preset.heading_numbering.get(block.level)
    if not scheme:
        return block.spans

    _advance_heading_counters(state, block.level)
    if _has_number_prefix(block.spans, scheme):
        return block.spans

    prefix = _format_heading_prefix(scheme, state.heading_counters[block.level])
    return [InlineSpan(text=prefix)] + block.spans


def _advance_heading_counters(state: BuildState, level: int) -> None:
    state.heading_counters[level] = state.heading_counters.get(level, 0) + 1
    for deeper_level in list(state.heading_counters):
        if deeper_level > level:
            state.heading_counters[deeper_level] = 0


def _has_number_prefix(spans: list[InlineElement], scheme: str) -> bool:
    text = "".join(span.text for span in spans if isinstance(span, InlineSpan)).lstrip()
    patterns = {
        "cn-section": r"^[一二三四五六七八九十百千万零〇两]+、",
        "cn-paren": r"^（[一二三四五六七八九十百千万零〇两]+）",
        "arabic-dot": r"^\d+[.．]\s*",
    }
    return re.match(patterns[scheme], text) is not None


def _format_heading_prefix(scheme: str, number: int) -> str:
    if scheme == "cn-section":
        return f"{_to_chinese_number(number)}、"
    if scheme == "cn-paren":
        return f"（{_to_chinese_number(number)}）"
    if scheme == "arabic-dot":
        return f"{number}. "
    raise ValueError(f"Unsupported heading numbering scheme: {scheme}")


def _to_chinese_number(number: int) -> str:
    digits = "零一二三四五六七八九"
    units = ["", "十", "百", "千"]
    raw = str(number)
    parts: list[str] = []

    for index, char in enumerate(raw):
        digit = int(char)
        unit_index = len(raw) - index - 1
        if digit == 0:
            if parts and parts[-1] != "零" and any(next_char != "0" for next_char in raw[index + 1 :]):
                parts.append("零")
            continue
        if not (digit == 1 and unit_index == 1 and not parts and len(raw) == 2):
            parts.append(digits[digit])
        parts.append(units[unit_index])

    return "".join(parts) or "零"
