# mdstyledocx

[![PyPI version](https://img.shields.io/pypi/v/mdstyledocx.svg)](https://pypi.org/project/mdstyledocx/)
[![Python versions](https://img.shields.io/pypi/pyversions/mdstyledocx.svg)](https://pypi.org/project/mdstyledocx/)
[![License](https://img.shields.io/pypi/l/mdstyledocx.svg)](https://pypi.org/project/mdstyledocx/)

一个按约定编写 Markdown、再一键导出标准化 Word (`.docx`) 的小工具。

当前设计重点不是“完整支持所有 Markdown 语法”，而是“稳定地把结构化 Markdown 落成统一版式的 Word 文档”。它适合做：

- 政府公文预设
- 单位通知 / 简报 / 汇报材料
- 团队内部统一模板

## 核心思路

把 Markdown 当成“内容源”，把版式规范抽成“preset”。

你只要按固定约定写 Markdown：

- `#`：文档标题
- `##`：一级标题
- `###`：二级标题
- 空行分段
- `-` / `*` / `+`：无序列表
- `1.`：有序列表
- `| ... |`：Markdown 表格；导出为原生 Word 表格
- `<!-- pagebreak -->`：分页

然后执行一次命令，就能得到带统一字体、字号、缩进、页边距的 `.docx`。

## 内置预设

各 preset 的详细说明都放在 `src/mdstyledocx/preset_specs/` 下：

- [default](https://github.com/YANG-Zijie/mdstyledocx/blob/main/src/mdstyledocx/preset_specs/default.md)：通用正式文档版式
- [official-doc-cn](https://github.com/YANG-Zijie/mdstyledocx/blob/main/src/mdstyledocx/preset_specs/official-doc-cn.md)：二号标题、三号标题层级和正文，全文固定 `28 pt` 行距
- [official-doc-cn-12pt](https://github.com/YANG-Zijie/mdstyledocx/blob/main/src/mdstyledocx/preset_specs/official-doc-cn-12pt.md)：小二号标题、小四号标题层级和正文，全文固定 `20 pt` 行距
- [official-doc-cn-system-fonts](https://github.com/YANG-Zijie/mdstyledocx/blob/main/src/mdstyledocx/preset_specs/official-doc-cn-system-fonts.md)：使用通用黑体、楷体、仿宋字体名称的三号版本
- [official-doc-cn-system-fonts-12pt](https://github.com/YANG-Zijie/mdstyledocx/blob/main/src/mdstyledocx/preset_specs/official-doc-cn-system-fonts-12pt.md)：使用通用字体名称的小四版本

目录约定：

- `*.json`：唯一的机器可读样式源；`paragraph_defaults` 定义全文通用行距和段距，`styles` 定义正文样式差异，`page_styles` 定义页眉、页脚和水印样式
- `*.md`：该模板的写作约定、推荐语法和边界说明

JSON 中的字号使用半磅（`size_half_points`），行距、段距和缩进使用 twip（`20 twips = 1 pt`）。对应 Markdown 说明统一换算成磅值，并以结构化样式表展示。

所有新 preset 文件都声明 `schema_version: 1`，其正式结构由 [`preset.schema.json`](https://github.com/YANG-Zijie/mdstyledocx/blob/main/src/mdstyledocx/preset.schema.json) 定义。可以直接从 CLI 查看 JSON Schema 或某个继承解析后的完整 preset：

```bash
mdstyledocx --show-preset-schema
mdstyledocx --show-preset-json official-doc-cn-12pt
```

## 安装

已发布到 PyPI：

- https://pypi.org/project/mdstyledocx/

如果你使用 `uv`，推荐直接安装为命令行工具：

```bash
uv tool install "mdstyledocx>=0.2.0"
mdstyledocx --version
mdstyledocx --list-presets
```

如果你只想临时执行一次，也可以：

```bash
uvx --from "mdstyledocx>=0.2.0" mdstyledocx --list-presets
```

如果你使用 `pip`：

```bash
pip install "mdstyledocx>=0.2.0"
mdstyledocx --version
mdstyledocx --list-presets
```

`official-doc-cn*` 命名、12 pt 变体、嵌套 YAML frontmatter、页眉页脚和水印均要求 `mdstyledocx >= 0.2.0`。如果 `--list-presets` 中没有这些名称，应先升级命令行工具。

## Codex / AI Agent Skill

本仓库同时提供 [`mdstyledocx` Skill](https://github.com/YANG-Zijie/mdstyledocx/tree/main/.agents/skills/mdstyledocx)，用于让 Codex 或兼容 Agent Skills 结构的 AI 工具选择 preset、整理受支持的 Markdown，并调用 `mdstyledocx` 生成和检查 Word 文档。

当前能力不需要单独发布 Codex plugin：转换完全由本地 CLI 完成，公开仓库中的 Skill 已足以提供模型侧的发现、选型和执行说明。只有以后需要额外的账号连接、远程服务或交互界面时，才有必要再考虑 plugin。

在本仓库目录中启动 Codex 时，它会自动发现这个 Skill。也可以让 Codex 从公开 GitHub 仓库安装：

```text
$skill-installer
请从 https://github.com/YANG-Zijie/mdstyledocx/tree/main/.agents/skills/mdstyledocx 安装 mdstyledocx skill。
```

安装 Skill 不会把 Python 运行时嵌入模型。执行时会优先使用本仓库或 `mdstyledocx >= 0.2.0` 的已安装命令，也可以通过 `uvx --from "mdstyledocx>=0.2.0" mdstyledocx` 临时运行；首次下载依赖可能需要用户允许联网。

## 使用方式

安装完成后，可以直接这样使用：

```bash
mdstyledocx --list-presets
mdstyledocx --show-preset-rules official-doc-cn
mdstyledocx --show-preset-json official-doc-cn
mdstyledocx examples/gov_notice.md -o examples/gov_notice.docx --preset official-doc-cn
```

带页眉、页脚和水印的完整示例见 [`examples/page_content.md`](https://github.com/YANG-Zijie/mdstyledocx/blob/main/examples/page_content.md)。

如果你是在本仓库里做开发，推荐直接用 `uv`：

```bash
uv sync
uv run python -m unittest
uv run mdstyledocx --list-presets
uv run mdstyledocx --show-preset-rules official-doc-cn
uv run mdstyledocx examples/gov_notice.md -o examples/gov_notice.docx --preset official-doc-cn
```

如果要从其他项目测试尚未发布的本地开发版本，可以直接指向 `mdstyledocx` 源码目录：

```bash
cd /path/to/document-project
uv run --project /path/to/mdstyledocx \
  mdstyledocx input.md -o output.docx \
  --preset official-doc-cn
```

这种方式使用本地工作区中的最新代码和 preset，包括尚未提交的修改，不依赖 PyPI 上已经发布的版本。

如果不使用 `uv`，也可以用传统方式：

```bash
pip install -e .
python3 -m unittest
mdstyledocx examples/gov_notice.md -o examples/gov_notice.docx --preset official-doc-cn
```

维护者发布新版本时，请遵循 [`RELEASING.md`](https://github.com/YANG-Zijie/mdstyledocx/blob/main/RELEASING.md)；GitHub Release 发布后将通过 PyPI Trusted Publishing 自动上传构建产物。

## 自定义预设

可以在内置 preset 基础上再叠加一个 JSON 覆盖文件：

```bash
mdstyledocx input.md -o output.docx --preset official-doc-cn --preset-file my-preset.json
```

如果想先看某个模板要求什么 Markdown 写法：

```bash
mdstyledocx --show-preset-rules official-doc-cn
```

示例：

```json
{
  "schema_version": 1,
  "extends": "official-doc-cn",
  "paragraph_defaults": {
    "line": 520,
    "line_rule": "exact"
  },
  "styles": {
    "title": {
      "size_half_points": 40
    }
  }
}
```

## YAML frontmatter

Markdown 文件开头可以使用嵌套 YAML frontmatter，为当前文档提供日期、页眉、页脚和文本水印内容：

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

`date` 会按填写内容自动显示在一级标题正下方，居中且使用正文的字体与字号；标题原有的后间距会移到日期之后。若不需要正文日期，请不要填写 `date`。日期仍可通过 `{date}` 在页眉或页脚中复用。

页眉支持 `left`、`right` 两个位置；页脚支持 `left`、`center`、`right` 三个位置，也可以直接写一个字符串作为居中页脚。中页眉不受支持，填写 `header.center` 会使转换失败。支持以下动态字段：

- `{page}`：当前页码，对应 Word `PAGE` 字段
- `{pages}`：总页数，对应 Word `NUMPAGES` 字段
- `{title}`：frontmatter 中的标题或正文一级标题
- `{date}`：frontmatter 中的日期；未提供时使用导出日期

这些动态字段只在页眉和页脚中展开。`watermark` 可以直接写字符串，也可以使用包含 `text` 和 `enabled` 的对象；`enabled: false` 用于关闭水印。

`{page}` 和 `{pages}` 会写入原生 Word 域，但不会启用“打开文档时更新所有域”的全局设置，以免 Word 对仅含内部页码域的文档误报“域可能引用其他文件”。

frontmatter 只负责每份文档的实际内容。字体、字号、颜色、透明度和旋转角度等版式参数由 preset JSON 的 `page_styles` 与 `watermark_defaults` 统一控制，写入 frontmatter 的样式字段会被拒绝。`official-doc-*` 默认不添加普通页眉、页脚或水印，只有 frontmatter 提供内容时才生成。当前版本在所有页面使用同一套页眉和页脚，暂不区分首页与奇偶页；公文版心外页码等专门规则也不由通用 `footer` 自动推断。

## Markdown 约定

README 只保留通用约定。某个 preset 的专用写法，以对应的 `preset_specs/*.md` 为准。

通用写法：

```md
# 关于开展示例工作的通知

各有关单位：

为统一输出格式，现将有关事项通知如下。

## 一、工作目标

1. 统一内容源。
2. 统一输出格式。

## 二、工作要求

请各单位按要求执行。
```

`official-doc-cn*` 默认把编号视为标题内容：需要编号时在 Markdown 中明确写入 `一、`、`（一）`、`1.`，不需要编号时直接写标题文字。导出器会保持原文，不会自动添加、删除或重排编号，因此同一级别可以混用有编号和无编号标题。

只有在自定义 preset 明确要求所有对应层级连续编号时，才建议选择自动编号：

```json
{
  "schema_version": 1,
  "extends": "official-doc-cn",
  "heading_numbering": {
    "2": "cn-section",
    "3": "cn-paren",
    "4": "arabic-dot"
  }
}
```

## 支持范围

当前版本优先保证：

- 标题、段落、列表、表格、分页、本地图片可稳定导出
- 表格首行自动加粗并在跨页时重复显示，列宽依据各列内容分配后继续允许 Word 自动调整
- YAML frontmatter 驱动的页眉、页脚、动态页码字段和文本水印
- 预设版式可复用
- 产物是标准 `.docx`

暂未覆盖：

- 合并单元格、表格内图片等复杂表格能力
- 脚注
- 复杂嵌套列表
- 目录自动生成

如果后面继续做，这个工具可以自然扩展成：

- 多个行业 preset 集合
- 首页与奇偶页使用不同的页眉、页脚
- 更完整的 Markdown 语法支持
- GUI 或 Web 包装层
