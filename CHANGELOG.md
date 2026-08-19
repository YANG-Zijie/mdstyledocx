# Changelog

[English](CHANGELOG.md) | [简体中文](CHANGELOG.zh-CN.md)

## 0.2.0 - Unreleased

- Rename the canonical Chinese presets to `official-doc-cn*`, retaining the old names only as internal compatibility aliases.
- Add 12 pt and common-system-font variants.
- Define global paragraph defaults for the 28 pt and 20 pt official-document baselines.
- Treat heading numbers as explicit Markdown content in the official-document presets, while retaining opt-in automatic numbering for custom presets.
- Add nested YAML frontmatter, two-zone headers, three-zone footers, dynamic Word page fields, and text watermarks.
- Add the versioned preset JSON Schema and resolved-preset CLI inspection.
- Add native Markdown tables with bold repeating headers and content-aware autofit widths.
- Add a post-title gap, two-character first- and second-level heading indents, justified body text, and disabled punctuation overflow to the Chinese official-document presets.
- Match Chinese official-document header and footer sizes at 10.5 pt, add a thin header rule, and align right-zone header content to the right text boundary.
- Render a YAML frontmatter `date` automatically below the level-one title, centered with the body font and size.
- Define explicit Word Header/Footer styles and emit page numbers as complete complex fields, pinning Latin and complex-script fonts so field refreshes do not fall back to Calibri.
- Limit headers to left and right zones, remove the built-in Header/Footer style tabs, and add a single tab at the current right text boundary; unsupported center headers now fail explicitly.
- Configure the linked Header Char/Footer Char styles so refreshed page fields do not inherit Calibri.
- Do not enable Word's global update-fields-on-open setting for page fields, avoiding misleading external-file warnings for documents that contain only internal page numbering.
- Add GitHub Release-triggered PyPI Trusted Publishing with release-tag version checks and separate build and publish jobs.
- Expand the installable Agent Skill and public usage documentation.

## 0.1.0 - 2026-03-31

- Initial PyPI release with Markdown-to-DOCX conversion and reusable presets.
