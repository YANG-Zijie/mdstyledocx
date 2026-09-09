---
name: mdstyledocx
description: Create standardized DOCX files from Markdown using mdstyledocx presets, including native tables, external hyperlinks, and optional YAML-driven headers, footers, page fields, and text watermarks. Use for Markdown-to-Word exports, especially Chinese government-style documents (中文公文), formal notices, reports, and briefs. Do not use for direct edits to existing DOCX files, tracked changes, comments, footnotes, or generated tables of contents.
---

# mdstyledocx

Use the `mdstyledocx` CLI as the deterministic renderer. Let the model prepare content and choose a preset; let the CLI control Word layout.

## Prepare the source

- Determine the Markdown input, DOCX output, and whether the user wants content changes or export only.
- Preserve an existing Markdown source unless the user asks to revise it. If the user provides notes or prose instead of a file, create an editable `.md` source before export.
- Honor a requested output path. Otherwise write beside the source with a `.docx` suffix. Do not replace an existing DOCX unless the user asked to update or overwrite it.
- Do not use this skill to modify an existing DOCX. Use a document-editing workflow for tracked changes, comments, or direct Word edits.

## Choose the CLI runner

The canonical preset names, page-content features, explicit blank-line markers, and official-document list layout in this skill require `mdstyledocx >= 0.3.0`. Use one runner consistently for the task:

1. Inside the `mdstyledocx` source checkout, use `uv run mdstyledocx`.
2. Otherwise run `mdstyledocx --version` and use `mdstyledocx` when version 0.3.0 or newer is already on `PATH`.
3. Otherwise use `uvx --from "mdstyledocx>=0.3.0" mdstyledocx` when `uv` and network access are available.

Do not install global packages without authorization. If dependency download or network access needs approval, request it immediately before running the command.

## Select and inspect the preset

Run the selected runner with `--list-presets`, then run `--show-preset-rules PRESET` before drafting or normalizing Markdown.

- Use the user's named preset when provided.
- Use `default` for a general clean formal document.
- Use `official-doc-cn` for the Chinese official-document baseline: a 22 pt (二号) title, 16 pt (三号) headings and body, exact 28 pt line spacing throughout, and FangZheng/GB2312 font names.
- Use `official-doc-cn-12pt` only when the user explicitly wants the small-four variant: an 18 pt (小二号) title, 12 pt (小四号) headings and body, and exact 20 pt line spacing throughout.
- Use `official-doc-cn-system-fonts` for the same 22/16 pt hierarchy and 28 pt line spacing with common Hei, Kai, and FangSong font names.
- Use `official-doc-cn-system-fonts-12pt` for the same 18/12 pt hierarchy and 20 pt line spacing with common system font names.
- Use `--preset-file PATH` only when the user supplies or requests a custom JSON override.

Do not invent preset names or rely on remembered rules when the installed CLI can report them.

## Keep Markdown within the supported contract

- Follow the selected preset's reported heading and numbering rules.
- In the `official-doc-cn*` presets, heading numbers are source content rather than automatic layout. Write `一、`, `（一）`, or `1.` explicitly only where the document requires them, and leave intentionally unnumbered headings unnumbered. Do not expect the CLI to infer or resequence them. Automatic heading numbering applies only when a custom preset explicitly defines `heading_numbering`.
- Use headings, paragraphs, ordered or unordered lists, standard inline Markdown links, pipe-style Markdown tables, explicit `<!-- blankline -->` or `<!-- blankline: N -->` markers for `1–20` blank body lines, explicit `<!-- pagebreak -->` markers, and local Markdown images.
- Use an AIMD-derived fenced `fig` block when an image needs automatic numbering, a title, a legend, or a stable reference target. An unreferenced figure may omit `id`; mdstyledocx assigns an internal identifier without rewriting the Markdown source. To use `{{ref_fig|FIGURE_ID}}` in prose, give the target figure an explicit unique `id`. Strict AIMD files still require every figure to declare `id`. Resolve `src` relative to the Markdown file. Ordinary `![](...)` images remain unnumbered.
- When the user requests page content, read [references/page-content.md](references/page-content.md), then use its nested YAML frontmatter contract.
- Keep page-content styling in the preset. Do not add font, size, color, opacity, rotation, or positioning fields to Markdown frontmatter.
- A frontmatter `date` is rendered automatically below the level-one title, centered with the preset's body font and size; it remains available as `{date}` in headers and footers.
- Resolve image paths relative to the Markdown file and confirm referenced files exist.
- Tables are emitted as native Word tables with bold repeating headers and content-aware autofit widths. Markdown separator alignment markers are honored; merged cells, multiline cells, and images inside cells are not supported.
- Inline `[text](target)` links are emitted as native external Word hyperlinks in headings, paragraphs, lists, and table cells. Keep link text plain; nested emphasis or code inside link text is not supported.
- For bibliographic citations, use AIMD-compatible `{{cite|id}}` or `{{cite|id1,id2}}` with literal BibTeX in a fenced `refs` block. This is an Unreleased/source-checkout capability; confirm the selected installed runner includes it before using it. Do not replace it with hand-numbered markers when the runner supports it.
- Citation numbers default to first appearance across headings, paragraphs, lists, and table cells, regardless of BibTeX order. Repeated IDs reuse numbers. Uncited entries remain after cited entries in definition order. Preset `citation_settings.order: source` opts into AIMD's current definition-order numbering; `citation_settings.superscript` controls raised citation markers.
- Put a `refs` block after the author-chosen reference heading and optional page break. The combined list is rendered once at the first `refs` block; other `refs` blocks contribute definitions only. Word citations link to bibliography bookmarks, and reference titles link to URLs or DOIs. No reference heading or page break is generated automatically.
- Each BibTeX entry needs a unique ID and non-empty `title`. Use braced, quoted, or numeric literal fields; nested braces and common escaped punctuation are supported. Macros, concatenation, `@string`, `@preamble`, and `@comment` are rejected. Preserve source metadata; do not invent absent dates, authors, or identifiers. Compact bibliography output is not full GB/T 7714 or CSL formatting.
- Validate missing citation targets, duplicate IDs, and malformed/unclosed `refs` blocks. Code examples must remain literal. Table citations do not require escaping the template's pipe. Use optional preset `styles.reference` for bibliography layout; otherwise it inherits body typography with a two-character hanging indent.
- Do not silently flatten footnotes, complex nested lists, generated tables of contents, or unsupported complex table structures. Explain the limitation and use another document workflow when those features are required.
- Treat the `official-doc-cn*` presets as layout baselines, not proof of compliance with every Chinese official-document rule.
- Do not add ordinary headers, footers, watermarks, or inferred official page-number layouts unless the source or user requests them.
- Remember that the DOCX names fonts but does not ensure that the recipient has them installed. Do not claim exact visual fidelity without rendering in an environment that has the intended fonts.

## Convert

Run:

```bash
RUNNER INPUT.md -o OUTPUT.docx --preset PRESET
```

Add `--preset-file OVERRIDE.json` only when needed. Quote paths safely and keep generated output out of version control unless the user requests otherwise.

## Validate and report

- Require a successful command exit, a non-empty `.docx`, and a valid ZIP package. A portable structural check is `python -m zipfile -t OUTPUT.docx`.
- When a DOCX renderer is available, render and inspect the pages for clipping, unexpected page breaks, image sizing, heading text and numbering, and font substitution. If rendering is unavailable, say that visual QA was not performed.
- Report the Markdown source, DOCX output, chosen preset, checks performed, and any remaining limitations.
