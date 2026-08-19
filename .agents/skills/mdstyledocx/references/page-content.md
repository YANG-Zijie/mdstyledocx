# Page content frontmatter

Read this reference only when a document needs a header, footer, page fields, or text watermark.

## Content contract

Put per-document content in YAML frontmatter at the start of the Markdown file:

```yaml
---
title: 关于开展示例工作的通知
date: 2026-08-19

header:
  left: "某某单位 {title}"
  right: 内部材料

footer:
  left: "{date}"
  center: "— {page} / {pages} —"
  right: 校对稿

watermark:
  text: 内部资料
---
```

`header` accepts a mapping containing only `left` and `right`. Centered headers are intentionally unsupported; `header.center` and a string-valued `header` are rejected. `footer` accepts either a centered string or a mapping containing `left`, `center`, and `right`. Their strings support:

- `{page}` for the Word `PAGE` field.
- `{pages}` for the Word `NUMPAGES` field.
- `{title}` for the frontmatter title, falling back to the first level-one heading.
- `{date}` for the frontmatter date, falling back to the export date.

`{page}` and `{pages}` are emitted as native Word fields. The renderer does not enable Word's global "update all fields on open" setting, because that setting can trigger a misleading warning that fields may refer to external files even when the document contains only internal page-number fields.

When `date` is present, it is also rendered automatically immediately below the level-one title. The date paragraph is centered, has no first-line indent, and inherits the body font and size from the selected preset. The title's normal trailing gap is placed after the date instead. Omit `date` when the document should not show a body date.

`watermark` accepts either a string or a mapping containing `text` and optional `enabled`. Use `enabled: false` to suppress an inherited or programmatically supplied value. Template fields are not expanded inside watermark text.

## Responsibility boundary

Frontmatter controls content only. Do not add font, size, color, opacity, rotation, coordinates, or other layout properties there. Those belong in preset JSON under `page_styles` and `watermark_defaults`; unsupported frontmatter fields cause conversion to fail.

Headers, footers, and watermarks are optional and are not enabled by the official-document presets unless content is supplied. The current renderer uses the same primary header and footer on every page. It does not yet model a different first page, odd/even pages, section-specific content, or the specialized page-number placement of a complete Chinese official-document standard.
