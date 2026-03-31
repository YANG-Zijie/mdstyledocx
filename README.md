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
- `<!-- pagebreak -->`：分页

然后执行一次命令，就能得到带统一字体、字号、缩进、页边距的 `.docx`。

## 内置预设

各 preset 的详细说明都放在 `src/mdstyledocx/preset_specs/` 下：

- [default](src/mdstyledocx/preset_specs/default.md)：通用正式文档版式
- [gov-cn](src/mdstyledocx/preset_specs/gov-cn.md)：中文政府公文风格基线
- [gov-cn-hei](src/mdstyledocx/preset_specs/gov-cn-hei.md)：黑体标题、楷体二级标题、仿宋正文

目录约定：

- `*.json`：样式参数、页边距、字体、缩进等机器可读定义
- `*.md`：该模板的写作约定、推荐语法和边界说明

## 安装

已发布到 PyPI：

- https://pypi.org/project/mdstyledocx/

如果你使用 `uv`，推荐直接安装为命令行工具：

```bash
uv tool install mdstyledocx
mdstyledocx --list-presets
```

如果你只想临时执行一次，也可以：

```bash
uvx mdstyledocx --list-presets
```

如果你使用 `pip`：

```bash
pip install mdstyledocx
mdstyledocx --list-presets
```

## 使用方式

安装完成后，可以直接这样使用：

```bash
mdstyledocx --list-presets
mdstyledocx --show-preset-rules gov-cn
mdstyledocx examples/gov_notice.md -o examples/gov_notice.docx --preset gov-cn
```

如果你是在本仓库里做开发，推荐直接用 `uv`：

```bash
uv sync
uv run python -m unittest
uv run mdstyledocx --list-presets
uv run mdstyledocx --show-preset-rules gov-cn
uv run mdstyledocx examples/gov_notice.md -o examples/gov_notice.docx --preset gov-cn
```

如果不使用 `uv`，也可以用传统方式：

```bash
pip install -e .
python3 -m unittest
mdstyledocx examples/gov_notice.md -o examples/gov_notice.docx --preset gov-cn
```

## 自定义预设

可以在内置 preset 基础上再叠加一个 JSON 覆盖文件：

```bash
mdstyledocx input.md -o output.docx --preset gov-cn --preset-file my-preset.json
```

如果想先看某个模板要求什么 Markdown 写法：

```bash
mdstyledocx --show-preset-rules gov-cn
```

示例：

```json
{
  "extends": "gov-cn",
  "styles": {
    "body": {
      "line": 520,
      "line_rule": "exact"
    },
    "title": {
      "size_half_points": 40
    }
  }
}
```

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

## 当前边界

当前版本优先保证：

- 标题、段落、列表、分页可稳定导出
- 预设版式可复用
- 产物是标准 `.docx`

暂未覆盖：

- 表格
- 图片
- 脚注
- 复杂嵌套列表
- 目录自动生成

如果后面继续做，这个工具可以自然扩展成：

- 多个行业 preset 集合
- frontmatter 驱动的页面元信息
- 更完整的 Markdown 语法支持
- GUI 或 Web 包装层
