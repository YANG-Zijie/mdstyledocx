# `default` preset

## 适用场景

通用正式文档，不强调行业模板约束，适合先把内容稳定导出成干净的 Word 版式。

## 样式说明

- 页面大小：A4
- 标题：居中、等线、较大字号
- 正文：宋体，常规正式文档风格
- 一级到三级标题：按层级逐步缩小字号

## 可选页面内容

- 页眉：宋体，`9 pt`
- 页脚：宋体，`9 pt`
- 文本水印：黑体，`36 pt`，默认颜色 `#D9D9D9`、透明度 `0.25`、旋转 `-45°`

页眉、页脚和水印默认不显示。需要时在 Markdown 开头使用 YAML frontmatter 提供内容：

```yaml
---
header:
  left: 项目名称
  right: 内部材料
footer:
  center: "{page} / {pages}"
watermark:
  text: 草案
---
```

页眉支持 `left`、`right`；页脚支持 `left`、`center`、`right`。两者均可使用 `{page}`、`{pages}`、`{title}`、`{date}` 动态字段。中页眉不受支持。字体、字号和水印外观由 preset JSON 控制，不写入 frontmatter。

## Markdown 约定

- `#`：文档主标题
- `##`：一级标题
- `###`：二级标题
- 普通段落：空行分段
- `1.`：有序列表
- `-` / `*` / `+`：无序列表
- `| ... |`：表格；首行加粗，列宽根据内容自动分配
- `![说明](./image.png)`：插入不编号的本地图片
- fenced `fig`：插入自动编号并带图题、图例和可选稳定 ID 的本地图片；正文可使用 `{{ref_fig|ID}}` 引用显式 ID
- `<!-- blankline -->` / `<!-- blankline: N -->`：空一行或指定 `1–20` 行
- `<!-- pagebreak -->`：分页

`fig` / `ref_fig` 源自 [Airalogy Markdown（AIMD）的结构化图片语法](https://github.com/airalogy/airalogy/blob/main/docs/airalogy/en/syntax/fig.md)。不参与引用的图片可省略 `id`；严格的 AIMD 文件仍应显式填写。`default` preset 使用 `Figure 1: Title` 格式。

## 示例

```md
# 项目阶段性汇报

本周工作进展如下。

## 一、已完成事项

1. 完成需求梳理。
2. 完成文档输出规范。
```
