from __future__ import annotations

import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from mdstyledocx.cli import main
from mdstyledocx.docx_writer import build_docx
from mdstyledocx.markdown import parse_inline, parse_markdown
from mdstyledocx.model import CitationSpan, ReferencesBlock
from mdstyledocx.presets import list_presets, load_preset, load_preset_definition, load_preset_schema
from mdstyledocx.references import ordered_references, parse_references

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
REFS = """```refs
@misc{a, title={Alpha}, url={https://example.com/a}}
@article{b, title={Beta}, author={{Research Group}}, year=2025, doi={10.1000/b}}
@misc{c, title={Gamma}, note={Article 12}}
```"""


def rendered(markdown: str, preset=None):
    result = build_docx(parse_markdown(markdown), preset or load_preset("default"))
    with zipfile.ZipFile(io.BytesIO(result)) as archive:
        assert archive.testzip() is None
        root = ET.fromstring(archive.read("word/document.xml"))
        rels = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
    return root, rels


def text(element) -> str:
    return "".join(node.text or "" for node in element.findall(".//w:t", NS))


class CitationTests(unittest.TestCase):
    def test_first_citation_order_reuse_and_bibliography_are_consistent(self):
        source = "C {{cite|c}}. A {{cite|a}}. C {{cite|c}}. B {{cite|b}}.\n\n" + REFS
        root, _ = rendered(source)
        paragraphs = root.findall("./w:body/w:p", NS)
        self.assertEqual(text(paragraphs[0]), "C [1]. A [2]. C [1]. B [3].")
        self.assertTrue(text(paragraphs[1]).startswith("[1] Gamma"))
        self.assertTrue(text(paragraphs[2]).startswith("[2] Alpha"))
        self.assertTrue(text(paragraphs[3]).startswith("[3] Research Group. Beta"))
        doc = parse_markdown(source)
        self.assertEqual([x.reference_id for x in ordered_references(doc)], ["c", "a", "b"])
        block = next(x for x in doc.blocks if isinstance(x, ReferencesBlock))
        self.assertEqual([x.reference_id for x in block.entries], ["a", "b", "c"])

    def test_reordering_definitions_does_not_change_citation_numbers(self):
        body = "{{cite|c,a}} and {{cite|b,c}}\n\n"
        reversed_refs = "```refs\n@misc{c,title={C}}\n@misc{b,title={B}}\n@misc{a,title={A}}\n```"
        first, _ = rendered(body + REFS)
        second, _ = rendered(body + reversed_refs)
        self.assertEqual(text(first.find("./w:body/w:p", NS)), "[1, 2] and [1, 3]")
        self.assertEqual(text(first.find("./w:body/w:p", NS)), text(second.find("./w:body/w:p", NS)))

    def test_reordering_body_recalculates_numbers(self):
        root, _ = rendered("{{cite|b}} then {{cite|a}} then {{cite|c}}\n\n" + REFS)
        paragraphs = root.findall("./w:body/w:p", NS)
        self.assertEqual(text(paragraphs[0]), "[1] then [2] then [3]")
        self.assertIn("Beta", text(paragraphs[1]))
        self.assertIn("Alpha", text(paragraphs[2]))

    def test_heading_list_and_unescaped_table_citations_share_document_order(self):
        source = """# Title {{cite|c}}

- Item {{cite|a}}

| Evidence | Detail |
| --- | --- |
| {{cite|b,c,b}} | **Strong {{cite|a}}** |

""" + REFS
        root, _ = rendered(source)
        self.assertEqual(text(root.find("./w:body/w:p", NS)), "Title [1]")
        cells = root.findall(".//w:tbl/w:tr/w:tc", NS)
        self.assertEqual([text(c) for c in cells], ["Evidence", "Detail", "[1, 3]", "Strong [2]"])
        self.assertEqual(len(cells[-1].findall(".//w:hyperlink/w:r/w:rPr/w:b", NS)), 1)

    def test_references_have_unique_bookmarks_and_citations_have_internal_links(self):
        root, rels = rendered("{{cite|c,a,b,c}}\n\n" + REFS)
        bookmarks = root.findall(".//w:bookmarkStart", NS)
        names = {b.get(f"{{{W}}}name") for b in bookmarks}
        self.assertEqual(names, {"mdstyledocx_ref_1", "mdstyledocx_ref_2", "mdstyledocx_ref_3"})
        self.assertEqual(len({b.get(f"{{{W}}}id") for b in bookmarks}), 3)
        links = root.findall(".//w:hyperlink", NS)
        anchors = [x.get(f"{{{W}}}anchor") for x in links if x.get(f"{{{W}}}anchor")]
        self.assertEqual(anchors, ["mdstyledocx_ref_1", "mdstyledocx_ref_2", "mdstyledocx_ref_3"])
        external = {r.attrib["Target"] for r in rels if r.attrib.get("TargetMode") == "External"}
        self.assertEqual(external, {"https://example.com/a", "https://doi.org/10.1000/b"})

    def test_figure_and_reference_bookmarks_do_not_collide(self):
        import base64
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "pixel.png"
            p.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+yF9kAAAAASUVORK5CYII="))
            source = f"{{{{ref_fig|f}}}} {{{{cite|c}}}}\n\n```fig\nid: f\nsrc: {p}\n```\n\n{REFS}"
            root, _ = rendered(source)
        ids = [b.get(f"{{{W}}}id") for b in root.findall(".//w:bookmarkStart", NS)]
        self.assertEqual(len(ids), len(set(ids)))
        targets = {b.get(f"{{{W}}}name") for b in root.findall(".//w:bookmarkStart", NS)}
        self.assertTrue(all(link.get(f"{{{W}}}anchor") in targets for link in root.findall(".//w:hyperlink[@w:anchor]", NS)))

    def test_code_examples_are_literal_and_do_not_define_or_cite_references(self):
        source = """Use `{{cite|missing}}` or ``{{cite|also_missing}}``.

````markdown
{{cite|missing}}
```refs
@misc{example,title={Example}}
```
````

~~~python
print('{{cite|absent}}')
~~~
"""
        document = parse_markdown(source)
        self.assertEqual(ordered_references(document), [])
        self.assertFalse(any(isinstance(span, CitationSpan) for b in document.blocks for span in b.spans))
        root, _ = rendered(source)
        self.assertIn("{{cite|missing}}", text(root))
        self.assertIn("@misc{example,title={Example}}", text(root))

    def test_multiple_blocks_merge_and_uncited_entries_are_retained_at_end(self):
        source = """{{cite|c}}

```refs
@misc{a,title={A}}
```

Some text {{cite|b}}.

```refs
@misc{b,title={B}}
@misc{c,title={C}}
@misc{d,title={D}}
```
"""
        doc = parse_markdown(source)
        self.assertEqual([x.reference_id for x in ordered_references(doc)], ["c", "b", "a", "d"])
        root, _ = rendered(source)
        self.assertEqual(len(root.findall(".//w:bookmarkStart", NS)), 4)
        self.assertEqual(text(root).count("[3] A"), 1)

    def test_reference_position_and_explicit_title_and_pagebreak_are_preserved(self):
        root, _ = rendered("{{cite|a}}\n\n<!-- pagebreak -->\n\n# 参考资料\n\n" + REFS)
        self.assertEqual(text(root).count("参考资料"), 1)
        self.assertEqual(len(root.findall('.//w:br[@w:type="page"]', NS)), 1)
        self.assertNotIn("```refs", text(root))

    def test_literal_bibtex_nested_braces_quotes_unicode_comments_and_parentheses(self):
        source = r'''% Header
@misc(chinese-id,
 title = "欧李 {叶片} 的研究",
 author = {{某研究机构}},
 year = 2026,
 url = {https://example.com/a?x=1&y=2},
 note = {含量为 5\%，符号 \{x\}；联系 a@example.com},
)
'''
        entry = parse_references(source)[0]
        self.assertEqual(entry.fields["title"], "欧李 叶片 的研究")
        self.assertEqual(entry.fields["author"], "某研究机构")
        self.assertEqual(entry.fields["note"], "含量为 5%，符号 {x}；联系 a@example.com")
        self.assertEqual(entry.fields["year"], "2026")

    def test_invalid_bibtex_is_not_silently_accepted(self):
        invalid = [
            "", "garbage", "@misc{a,title={Unclosed}", '@misc{a,title="Unclosed}',
            "@misc{a,title={A} year=2026}", "@misc{a,title={A},title={B}}",
            "@misc{a,url={https://example.com}}", "@misc{a,title={}}",
            "@string{foo={A}}", "@preamble{abc}", "@misc{a,title=macro}",
            "@misc{a,title={A} # {B}}", "@misc{a b,title={A}}",
            "@misc{a,title={A}} trailing junk",
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "Invalid refs BibTeX"):
                parse_references(value)

    def test_missing_duplicate_and_malformed_citations_fail(self):
        for citation in ["{{cite|}}", "{{cite|a,}}", "{{cite|a,,b}}", "{{cite a}}", "{{cite|a", "{{cite|a b}}"]:
            with self.subTest(citation=citation), self.assertRaises(ValueError):
                parse_markdown(citation + "\n\n" + REFS)
        with self.assertRaisesRegex(ValueError, "Unknown cite target.*missing"):
            parse_markdown("{{cite|missing}}")
        with self.assertRaisesRegex(ValueError, "Duplicate reference id"):
            parse_markdown(REFS + "\n\n```refs\n@misc{a,title={Again}}\n```")
        with self.assertRaisesRegex(ValueError, "Unterminated refs block"):
            parse_markdown("```refs\n@misc{a,title={A}}")

    def test_emphasized_and_escaped_citation_syntax(self):
        spans = parse_inline("**Strong {{cite|a}}** and *{{cite|a}}* and \\{{cite|literal}}")
        citations = [x for x in spans if isinstance(x, CitationSpan)]
        self.assertEqual(len(citations), 2)
        self.assertTrue(citations[0].bold)
        self.assertTrue(citations[1].italic)

    def test_all_presets_default_to_first_citation_and_allow_explicit_source_order(self):
        for name, _ in list_presets():
            with self.subTest(preset=name):
                preset = load_preset(name)
                self.assertEqual(preset.citation_settings.order, "first-citation")
                self.assertFalse(preset.citation_settings.superscript)
                rendered("{{cite|c,a,b}}\n\n" + REFS, preset)
        with tempfile.TemporaryDirectory() as directory:
            override = Path(directory) / "preset.json"
            override.write_text(json.dumps({"citation_settings": {"order": "source", "superscript": True}}))
            preset = load_preset("default", override)
            root, _ = rendered("{{cite|c}}\n\n" + REFS, preset)
        paragraph = root.find("./w:body/w:p", NS)
        self.assertEqual(text(paragraph), "[3]")
        superscripts = paragraph.findall('.//w:vertAlign[@w:val="superscript"]', NS)
        self.assertEqual(len(superscripts), 3)

    def test_invalid_citation_preset_settings_fail(self):
        for settings in [{"order": "alphabetical"}, {"superscript": "yes"}, {"unknown": 1}]:
            with self.subTest(settings=settings), tempfile.TemporaryDirectory() as directory:
                override = Path(directory) / "preset.json"
                override.write_text(json.dumps({"citation_settings": settings}))
                with self.assertRaises(ValueError):
                    load_preset("default", override)
        schema = json.loads(load_preset_schema())
        self.assertIn("citation_settings", schema["properties"])
        self.assertEqual(load_preset_definition("default")["citation_settings"]["order"], "first-citation")

    def test_failed_conversion_does_not_overwrite_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.md"
            output = source.with_suffix(".docx")
            source.write_text("{{cite|missing}}")
            output.write_bytes(b"existing document")
            with self.assertRaisesRegex(ValueError, "Unknown cite target"):
                main([str(source), "-o", str(output)])
            self.assertEqual(output.read_bytes(), b"existing document")


if __name__ == "__main__":
    unittest.main()
