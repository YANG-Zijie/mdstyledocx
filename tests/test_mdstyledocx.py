from __future__ import annotations

import base64
import io
import re
import tempfile
import unittest
import zipfile
from pathlib import Path

from mdstyledocx.cli import main
from mdstyledocx.docx_writer import build_docx
from mdstyledocx.markdown import parse_markdown
from mdstyledocx.presets import list_presets, load_preset, load_preset_rules

SAMPLE_MARKDOWN = """# 关于开展示例工作的通知

各有关单位：

为统一输出格式，现将有关事项通知如下。

## 一、工作目标

1. 统一内容源。
2. 统一输出格式。

<!-- pagebreak -->

## 二、工作要求

请各单位按要求执行。
"""

SAMPLE_MARKDOWN_WITH_SUBHEADING = """# 关于开展示例工作的通知

各有关单位：

为统一输出格式，现将有关事项通知如下。

## 一、工作目标

### （一）总体要求

请各单位按要求执行。
"""

SAMPLE_MARKDOWN_FOR_AUTONUM = """# 关于开展示例工作的通知

各有关单位：

## 工作目标

### 总体要求

#### 任务分工

请各单位按要求执行。
"""

PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+yF9kAAAAASUVORK5CYII="
)


class MarkdownParsingTests(unittest.TestCase):
    def test_parse_markdown_blocks(self) -> None:
        document = parse_markdown(SAMPLE_MARKDOWN)

        self.assertEqual(document.blocks[0].kind, "heading")
        self.assertEqual(document.blocks[0].level, 1)
        self.assertEqual(document.blocks[1].kind, "paragraph")
        self.assertEqual(document.blocks[3].kind, "heading")
        self.assertEqual(document.blocks[4].kind, "list_item")
        self.assertEqual(document.blocks[6].kind, "page_break")

    def test_parse_markdown_image_span_uses_base_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_path = temp_path / "seal.png"
            image_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))

            document = parse_markdown("![公章](seal.png)", base_path=temp_path)

            image_span = document.blocks[0].spans[0]
            self.assertEqual(image_span.alt_text, "公章")
            self.assertEqual(image_span.path, str(image_path.resolve()))


class PresetLoadingTests(unittest.TestCase):
    def test_builtin_presets_are_loaded_from_spec_files(self) -> None:
        presets = dict(list_presets())

        self.assertIn("default", presets)
        self.assertIn("gov-cn", presets)
        self.assertIn("gov-cn-hei", presets)
        self.assertEqual(presets["gov-cn"], "Chinese government document baseline preset")

    def test_preset_rules_are_available(self) -> None:
        rules = load_preset_rules("gov-cn")

        self.assertIn("推荐 Markdown 写法", rules)
        self.assertIn("仿宋_GB2312", rules)


class DocxGenerationTests(unittest.TestCase):
    def test_gov_preset_contains_expected_markers(self) -> None:
        document = parse_markdown(SAMPLE_MARKDOWN)
        payload = build_docx(document, load_preset("gov-cn"))

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            names = set(archive.namelist())
            xml = archive.read("word/document.xml").decode("utf-8")

        self.assertIn("word/document.xml", names)
        self.assertIn("docProps/core.xml", names)
        self.assertIn("仿宋_GB2312", xml)
        self.assertIn("方正小标宋简体", xml)
        self.assertIn('w:sz w:val="32"', xml)
        self.assertIn('w:firstLine="640"', xml)
        self.assertIn('w:line="560"', xml)
        self.assertIn('w:lineRule="exact"', xml)
        self.assertNotIn("一、一、工作目标", xml)

    def test_gov_hei_preset_contains_expected_markers(self) -> None:
        document = parse_markdown(SAMPLE_MARKDOWN_WITH_SUBHEADING)
        payload = build_docx(document, load_preset("gov-cn-hei"))

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")

        self.assertIn("黑体", xml)
        self.assertIn("楷体", xml)
        self.assertIn("仿宋", xml)
        self.assertNotIn("方正小标宋简体", xml)
        self.assertNotIn("楷体_GB2312", xml)
        self.assertNotIn("仿宋_GB2312", xml)

    def test_gov_presets_auto_number_headings(self) -> None:
        document = parse_markdown(SAMPLE_MARKDOWN_FOR_AUTONUM)
        payload = build_docx(document, load_preset("gov-cn-hei"))

        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            xml = archive.read("word/document.xml").decode("utf-8")
        visible_text = re.sub(r"<[^>]+>", "", xml)

        self.assertIn("一、工作目标", visible_text)
        self.assertIn("（一）总体要求", visible_text)
        self.assertIn("1. 任务分工", visible_text)

    def test_cli_writes_docx_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "notice.md"
            output_path = temp_path / "notice.docx"
            input_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")

            exit_code = main([str(input_path), "-o", str(output_path), "--preset", "gov-cn"])

            self.assertEqual(exit_code, 0)
            self.assertTrue(output_path.exists())
            self.assertGreater(output_path.stat().st_size, 0)

    def test_image_is_embedded_and_uses_single_spacing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_path = temp_path / "seal.png"
            image_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))
            markdown = "# 标题\n\n![公章](seal.png)\n"

            document = parse_markdown(markdown, base_path=temp_path)
            payload = build_docx(document, load_preset("gov-cn-hei"))

            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                xml = archive.read("word/document.xml").decode("utf-8")
                rels = archive.read("word/_rels/document.xml.rels").decode("utf-8")
                media = set(archive.namelist())

            self.assertIn("<w:drawing>", xml)
            self.assertIn('w:line="240"', xml)
            self.assertIn('w:lineRule="auto"', xml)
            self.assertIn('relationships/image', rels)
            self.assertIn("media/image1.png", rels)
            self.assertIn("word/media/image1.png", media)

    def test_cli_can_print_preset_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            original_stdout = __import__("sys").stdout
            stream = io.StringIO()
            __import__("sys").stdout = stream
            try:
                exit_code = main(["--show-preset-rules", "gov-cn"])
            finally:
                __import__("sys").stdout = original_stdout

            self.assertEqual(exit_code, 0)
            self.assertIn("当前版式基线", stream.getvalue())
