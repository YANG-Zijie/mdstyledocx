---
name: mdstyledocx
description: Create standardized DOCX files from Markdown using mdstyledocx presets. Use for Markdown-to-Word exports, especially Chinese government-style documents (中文公文), formal notices, reports, and briefs. Do not use for direct edits to existing DOCX files, tracked changes, comments, tables, footnotes, or generated tables of contents.
---

# mdstyledocx

Use the `mdstyledocx` CLI as the deterministic renderer. Let the model prepare content and choose a preset; let the CLI control Word layout.

## Prepare the source

- Determine the Markdown input, DOCX output, and whether the user wants content changes or export only.
- Preserve an existing Markdown source unless the user asks to revise it. If the user provides notes or prose instead of a file, create an editable `.md` source before export.
- Honor a requested output path. Otherwise write beside the source with a `.docx` suffix. Do not replace an existing DOCX unless the user asked to update or overwrite it.
- Do not use this skill to modify an existing DOCX. Use a document-editing workflow for tracked changes, comments, or direct Word edits.

## Choose the CLI runner

Use one runner consistently for the task:

1. Inside the `mdstyledocx` source checkout, use `uv run mdstyledocx`.
2. Otherwise use `mdstyledocx` when it is already on `PATH`.
3. Otherwise use `uvx mdstyledocx` when `uv` and network access are available.

Do not install global packages without authorization. If dependency download or network access needs approval, request it immediately before running the command.

## Select and inspect the preset

Run the selected runner with `--list-presets`, then run `--show-preset-rules PRESET` before drafting or normalizing Markdown.

- Use the user's named preset when provided.
- Use `default` for a general clean formal document.
- Use `gov-cn` for the Chinese government-document baseline with FangZheng and GB2312 font names.
- Use `gov-cn-hei` when the user prefers common system font names: Hei, Kai, and FangSong.
- Use `--preset-file PATH` only when the user supplies or requests a custom JSON override.

Do not invent preset names or rely on remembered rules when the installed CLI can report them.

## Keep Markdown within the supported contract

- Follow the selected preset's reported heading and numbering rules.
- Use headings, paragraphs, ordered or unordered lists, explicit `<!-- pagebreak -->` markers, and local Markdown images.
- Resolve image paths relative to the Markdown file and confirm referenced files exist.
- Do not silently flatten tables, footnotes, complex nested lists, or generated tables of contents. Explain the limitation and use another document workflow when those features are required.
- Treat `gov-cn` and `gov-cn-hei` as layout baselines, not proof of compliance with every Chinese official-document rule.
- Remember that the DOCX names fonts but does not ensure that the recipient has them installed. Do not claim exact visual fidelity without rendering in an environment that has the intended fonts.

## Convert

Run:

```bash
RUNNER INPUT.md -o OUTPUT.docx --preset PRESET
```

Add `--preset-file OVERRIDE.json` only when needed. Quote paths safely and keep generated output out of version control unless the user requests otherwise.

## Validate and report

- Require a successful command exit, a non-empty `.docx`, and a valid ZIP package. A portable structural check is `python -m zipfile -t OUTPUT.docx`.
- When a DOCX renderer is available, render and inspect the pages for clipping, unexpected page breaks, image sizing, heading numbering, and font substitution. If rendering is unavailable, say that visual QA was not performed.
- Report the Markdown source, DOCX output, chosen preset, checks performed, and any remaining limitations.
