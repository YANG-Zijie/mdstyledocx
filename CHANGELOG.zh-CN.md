# 更新日志

[English](CHANGELOG.md) | [简体中文](CHANGELOG.zh-CN.md)

## 尚未发布

- 在连续的 Markdown 表格之间按当前 preset 的正文行高插入一个空段落，避免导出为 DOCX 后两张表格黏连。

## 0.3.0 - 2026-08-27

- 新增由仓库管理的 pre-push 预检，统一验证工作流 Action 引用、运行测试并构建发布包。
- 新增源自 Airalogy Markdown（AIMD）的 fenced `fig` 和 `ref_fig` 语法，支持本地图片解析、自动编号、图题、图例、Word 书签与内部链接、结构校验以及由 preset 控制的图号和样式；不参与引用的图片可以省略 `id`，且不会改写 Markdown 源文件。
- 新增显式 `<!-- blankline -->` 和 `<!-- blankline: N -->` 标记，可按当前 preset 的正文行高插入一行或指定 `1–20` 行空白。
- 中文公文 preset 将列表项按自然段排版：首行缩进两字符、回行顶格；`default` preset 继续保留悬挂缩进。
- preset 的列表设置新增可选且经过校验的 `first_line_indent` 字段，并禁止与悬挂缩进同时启用。

## 0.2.0 - 2026-08-20

- 将中文公文 preset 的正式名称调整为 `official-doc-cn*`，旧名称仅作为内部兼容别名保留。
- 新增 12 pt 小四号和通用系统字体变体。
- 为 28 pt 和 20 pt 两套公文基线定义全文统一的段落默认值。
- 公文 preset 默认将标题编号作为 Markdown 显式内容，同时保留供自定义 preset 启用的自动编号能力。
- 新增嵌套 YAML frontmatter、左右两区页眉、左中右三区页脚、Word 动态页码字段和文本水印。
- 新增带版本号的 preset JSON Schema，以及查看继承解析后完整 preset 的 CLI 功能。
- 新增原生 Markdown 表格输出、加粗重复表头以及按内容分配的自动列宽。
- 中文公文 preset 增加标题后空行、一二级标题两字符缩进、正文两端对齐和禁止标点溢出规则。
- 中文公文页眉与页脚统一为五号（`10.5 pt`），页眉增加细下边线，并修正缺少中区内容时右页眉的版心右对齐。
- YAML frontmatter 中的 `date` 自动在一级标题下方居中显示，并继承正文的字体与字号。
- 明确定义 Word 的 Header/Footer 样式，并将页码写为完整复合域；页眉、页脚及动态页码字段均固定西文字体和复杂文字字体，避免 Word 刷新字段后回落为 Calibri。
- 页眉明确限定为左、右两区；生成时先删除 Word Header/Footer 样式自带的中、右制表位，再按当前版心设置单个右边界制表位。不支持的中页眉会直接报错。
- 同步设置 Header Char/Footer Char 关联字符样式，避免页码或其他域更新后继承 Calibri。
- 不再为页码域启用“打开文档时更新所有域”，避免 Word 对仅含内部页码域的文档弹出外部文件引用警告。
- 新增由 GitHub Release 触发的 PyPI Trusted Publishing，并在分离的构建、发布作业之间校验发布标签与包版本。
- 完善可安装的 Agent Skill 和公开使用文档。

## 0.1.0 - 2026-03-31

- 首次发布至 PyPI，支持将 Markdown 转换为 DOCX 并复用 preset。
