---
name: elegant-pdf
description: >
  One-command Markdown → 精美 PDF。双引擎渲染：WeasyPrint（10 套设计风格）
  + ReportLab/any2pdf（10 套主题，CJK 稳定），自动回退。支持 Mermaid 图转 PNG
  嵌入、封面页、自动目录、页眉页脚、专业表格、`:::` fenced div 设计块。
  效果对标顶级印刷品。
  Use when user asks to convert markdown to a beautiful/polished/professional PDF.
  Unified entry point — use this instead of any2pdf, arch-pdf, or markdown-to-pdf.
version: 2.1.0
category: productivity
metadata:
  author: "design-skill-pack <noreply@example.com>"
  hermes:
    triggers:
      - "markdown 转精美 PDF"
      - "生成精美的 PDF 报告"
      - "elegant PDF"
      - "md 转 pdf 要好看"
      - "把这份文档排成印刷质感"
      - "any2pdf"
      - "md2pdf"
      - "带 mermaid 转 PDF"
      - "含架构图的文档转 PDF"
    tags: [pdf, markdown, weasyprint, reportlab, cjk, mermaid, chinese, typography]
---

# elegant-pdf — Markdown → 精美印刷级 PDF（统一入口）

**一站式 PDF 渲染工具。** 所有 Markdown→PDF 场景都走这个技能，不用再找 any2pdf / arch-pdf / markdown-to-pdf。

- 双引擎：WeasyPrint（10 套设计风格）+ ReportLab/any2pdf（10 套主题，CJK 稳定）
- Mermaid 自动渲染：`--mermaid` 参数，无需单独走 arch-pdf
- 自动回退：WeasyPrint 渲染失败时自动切到 ReportLab
- 设计决策层：搭配 `pdf-designer` skill 一起用

## 统一引擎架构

```
                                                                       ┌─ WeasyPrint ──→ warm-academic
                                ┌─ WeasyPrint ──────────────┐         ├─ swiss
用户输入 .md ──→ md2elegant.py ─┤                            ├→ 渲染 ──┤─ japanese
                                └─ ReportLab (any2pdf) ────┘         └─ cyberpunk
                                      ↓                               ┌─ warm-academic
                                 自动回退 (WeasyPrint 失败时)          ├─ nord-frost
                                                                      ├─ github-light
                                                                      ├─ 11 个主题...
                                                                      └─ ocean-breeze
```

| 场景 | 引擎 | 参数 |
|------|------|------|
| 日常使用 | auto（优先WeasyPrint，失败回退ReportLab） | (默认) |
| 要 WeasyPrint 的设计风格 | WeasyPrint | `--engine weasyprint --style swiss` |
| CJK 确定稳定 | ReportLab | `--engine reportlab --theme warm-academic` |
| 含 Mermaid 图 | auto + mermaid | `--mermaid` |
| 先选风格再看效果 | pdf-designer → elegant-pdf | 先加载 `pdf-designer` skill |

## 快速开始

```bash
# 默认：auto 引擎，暖调学术风
python3 ~/.agents/skills/elegant-pdf/scripts/md2elegant.py input.md -o output.pdf

# 指定引擎和风格
python3 ~/.agents/skills/elegant-pdf/scripts/md2elegant.py input.md --engine reportlab --theme nord-frost
python3 ~/.agents/skills/elegant-pdf/scripts/md2elegant.py input.md --engine weasyprint --style swiss

# 含 Mermaid 图
python3 ~/.agents/skills/elegant-pdf/scripts/md2elegant.py input.md --mermaid

# 跳过封面/TOC
python3 ~/.agents/skills/elegant-pdf/scripts/md2elegant.py input.md --no-cover --no-toc
```

**Markdown 文件需包含 YAML frontmatter**：

```yaml
---
title: 媒体与审美口味白皮书
subtitle: 审美基因 · 体验边界 · 推荐引擎
author: 你的名字
date: 2026-06-05
lang: zh-CN
cover_label: TASTE PROFILE   # 可选，封面标签
---
```

## `:::` 自定义设计块（6 个命名容器）

模板支持 6 种语义块，用 `:::` fenced div 触发（依赖 `mdit-py-plugins`）：

| 容器 | 用途 |
|------|------|
| `::: intro-block` | 引导/命中规则块 |
| `::: quote-box` | 拉引/格言框 |
| `::: memo-section` | 备忘/关键边界块（可含 `memo-title`） |
| `::: memo-title` | 备忘块标题（嵌在 memo-section 内） |
| `::: section-note` | 章节注/边注 |
| `::: theorem` | 定理/定义框（scholar 主用，自动编号） |

**嵌套语法**（与 code fence 相同：外层冒号数 ≥ 内层）：

    ::: quote-box
    格言内容
    :::

    :::: memo-section
    ::: memo-title
    关键边界
    :::
    内容...
    ::::

    ::: theorem
    定理陈述
    :::

未注册类名（如 `::: unknown-class`）→ 降级为普通段落，不崩。

## 所有参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `input.md` | 输入 Markdown（位置参数） | 必填 |
| `-o, --output` | 输出 PDF 路径 | `<input-stem>.pdf` |
| `--engine` | 渲染引擎：`weasyprint` / `reportlab` / `auto` | `auto` |
| `--style` | 视觉风格（WeasyPrint 引擎） | `warm-academic` |
| `--theme` | 显式主题名（ReportLab 引擎，覆盖 style→theme 映射） | 自动映射 |
| `--title` | 覆盖封面标题 | frontmatter 的 title |
| `--author` | 覆盖作者 | frontmatter 的 author |
| `--no-cover` | 跳过封面页 | false |
| `--no-toc` | 跳过目录页 | false |
| `--strip-emoji` | 移除所有 emoji（正式文档推荐） | false |
| `--mermaid` | 自动渲染 ` ```mermaid ` 图为 PNG | false |

## 风格 × 引擎对照

### WeasyPrint 引擎（10 套设计风格）

| 风格 | `--style` | 排版哲学 | 字体 | 色调 |
|------|-----------|----------|------|------|
| 暖调学术风 | `warm-academic` (默认) | 金褐 × 象牙白，楷体标题，温润阅读 | 宋体 + 楷体 | #b8a88a 金褐 |
| 瑞士国际主义 | `swiss` | 网格 + 编号 + 红色强调 + 信息扫描 | 无衬线 (Noto Sans CJK SC) | #e63946 红 |
| 日式文艺杂志 | `japanese` | 大面积留白 + 衬线 + 暖纸色 + Z 型慢读 | 衬线 (Noto Serif CJK SC) | #8b5a2b 赭石 |
| 赛博朋克档案 | `cyberpunk` | 深色终端 + 荧光绿 + 等宽数据 + 解密阅读 | 无衬线 + 等宽 | #00ff9d 绿 + #00a8ff 蓝 |
| 新艺术 | `art-nouveau` | 四角圆角花纹 + 双圆环 + 金褐装饰 + 有机曲线 | 宋体 | #b8945a 金褐 |
| 包豪斯海报 | `bauhaus` | 散落原色几何 + 黄色色块标题 + 三原色 | 无衬线 | #e63946 红 + #2563eb 蓝 + #f59e0b 黄 |
| 东方水墨 | `ink-wash` | 墨点 + 竖线书法格 + 晕染 + 印章 + 大量留白 | 宋体 | #8b5a2b 赭石 + 印章红 |
| 极简主义 | `minimalism` | 超大留白 + 居中 + light 字重 + 无装饰 | 无衬线 light | 无（黑灰白） |
| 复古打字机 | `typewriter` | 牛皮纸 + 压痕 + 回形针 + 咖啡渍 + Courier | 等宽 + 宋体 | #3d3428 深棕 |
| 古典学者 | `scholar` | 纯白 + 无装饰 + Booktabs + 让内容说话 | 宋体 | 黑 + 灰 |

### ReportLab 引擎（10 套主题）

| 主题 | `--theme` | 氛围 | 典型用途 |
|------|-----------|------|----------|
| 暖学术 | `warm-academic` | 陶土色调，温润典雅 | 人文/社科报告、白皮书 |
| Nord 冰霜 | `nord-frost` | 蓝灰北欧风，清爽现代 | 技术文档、系统分析 |
| GitHub 轻 | `github-light` | 蓝白极简，开发者风格 | README、技术笔记 |
| Solarized 浅 | `solarized-light` | 温暖护目，代码友好 | 代码文档、手册 |
| 经典论文 | `classic-thesis` | 棕色调，LaTeX 经典 | 学术论文 |
| Tufte | `tufte` | 极简留白，深红点缀 | 数据叙事 |
| 期刊蓝 | `ieee-journal` | 藏蓝严谨，正式发表风格 | 期刊投稿 |
| 精装书 | `elegant-book` | 咖啡色调，书卷气 | 长篇专著 |
| 海洋 | `ocean-breeze` | 青绿海洋风，清新自然 | 创意内容 |
| GitHub 默认 | `github-light` | 开发者风格 | 通用 |

### 风格选择速查

| 内容类型 | 推荐引擎 | 推荐风格 |
|----------|----------|----------|
| 技术文档、系统分析 | WeasyPrint | `swiss` |
| 个人随笔、文化评论 | WeasyPrint | `japanese` |
| 正式报告、白皮书 | ReportLab (CJK 稳定) | `warm-academic` |
| 科幻、游戏、系统档案 | WeasyPrint | `cyberpunk` |
| 代码文档、API 手册 | ReportLab | `nord-frost` |
| 含 Mermaid 图的技术文档 | auto + `--mermaid` | `nord-frost` |
| 创意、艺术文档、装饰性内容 | WeasyPrint | `art-nouveau` |
| 创意作品集、艺术/设计文档 | WeasyPrint | `bauhaus` |
| 东方文化、随笔、传统著述 | WeasyPrint | `ink-wash` |
| 草稿、纯文字、极简哲学 | WeasyPrint | `minimalism` |
| 档案、机密文档、复古笔记 | WeasyPrint | `typewriter` |
| 纯学术论文、学位论文、正式报告 | WeasyPrint | `scholar` |

> 更详细的内容→风格匹配指南见 `pdf-designer` skill。

## 工作流程

### 引擎选择逻辑

```
auto 模式:
  WeasyPrint 可用?
    ├─ 是 → 渲染 → PDF >20KB? → 完成 ✅
    │              └─ PDF 空壳 → ReportLab 回退
    └─ 否 → ReportLab 渲染
```

### Mermaid 预处理

当 `--mermaid` 指定或文件中检测到 ` ```mermaid ` 块：

1. `mmdc` 将每个 mermaid 代码块渲染为 PNG（需 `npm install -g @mermaid-js/mermaid-cli`）
2. 图片嵌入到所在位置
3. 接着走标准渲染流程

**关键**：`mmdc` 必须在 md 文件所在目录运行，否则相对路径会出错。脚本已自动处理。

## 与 pdf-designer 的关系

`elegant-pdf` 是**执行层**——输入 Markdown，输出 PDF。
`pdf-designer` 是**设计决策层**——先分析内容气质，再决定用哪个风格/字体/空间/强调系统。

**推荐工作流**：用户说"生成 PDF"但没指定风格 → 先调 `pdf-designer` 做设计决策 → 再调 `elegant-pdf` 执行。

## 验证

```bash
file output.pdf          # PDF document
python3 -c "
import fitz  # PyMuPDF
doc = fitz.open('output.pdf')
print(f'{doc.page_count} pages')
"
```

验证 PDF 是否包含实际内容（非空壳）：
```bash
ls -la output.pdf  # 含文本的 PDF 通常 >150KB；空壳 ~75KB
```

## 前置依赖

```bash
# 核心
pip3 install markdown-it-py PyYAML
pip3 install mdit-py-plugins   # ::: fenced div 容器支持（6 个命名设计块）

# WeasyPrint 引擎
brew install weasyprint  # macOS

# CJK 字体（完整版，非 Google Fonts 子集版）
brew install font-noto-sans-cjk-sc font-noto-serif-cjk-sc

# ReportLab 引擎 (CJK 稳定)
pip3 install reportlab

# Mermaid 渲染（可选）
npm install -g @mermaid-js/mermaid-cli

# 验证字体安装
fc-list : family | grep -i "noto.*cjk"
# 应输出: Noto Sans CJK SC 和 Noto Serif CJK SC
```

## 已知陷阱

### WeasyPrint

- **⚠️ 模板文件 HTML 实体编码**：如果模板 .html 文件的 `<` 被写成 `&lt;`（常见于通过 write_file 或 skill_manage 写入时被自动转义），WeasyPrint 会把 HTML 标签当纯文本渲染——输出 PDF 显示原始 HTML 源码而非渲染结果。修复：`python3 -c "import html; open(path,'w').write(html.unescape(open(path).read()))"` 对所有模板执行一次。
- **⚠️ PYTHONPATH 污染**：Hermes venv 的 PYTHONPATH 会注入 Homebrew Python 3.14，导致 WeasyPrint 找到 venv 里坏掉的 Pillow 3.11。`md2elegant.py` 已 patch 清除 PYTHONPATH。
- `li::marker` 和 `::before` 伪元素在 WeasyPrint 中渲染不可靠，用 `list-style-type: none` + `li::before` 模拟
- Google Fonts CDN 会卡 weasyprint，模板只使用系统字体
- Homebrew weasyprint CLI (`/opt/homebrew/bin/weasyprint`) 优先于 Python API（因 libgobject 依赖问题）
- **⚠️ WeasyPrint CLI 静默 CJK 渲染失败**：即使 CLI 无报错结束，PDF 也可能不包含任何文本内容（中英文均缺失）。原因是系统级 Pango/GDK-Pixbuf 依赖不完整 (`libgobject-2.0-0` 缺失)，WeasyPrint 进入降级模式——嵌入字体但不写入文本。**必须验证 PDF 内容**（检查文件大小——含文本的 PDF 通常 >150KB；空壳 PDF 约 75KB）。
- **WeasyPrint 风格字体依赖**：`swiss` 风格依赖 "Noto Sans CJK SC" 字体名称。系统可能安装的是旧版 `Noto Sans SC`（Google Fonts 子集版，仅 3500 常用字）而非完整版 `Noto Sans CJK SC`（约 16MB/字重），导致非常用字显示为空白。建议通过 Homebrew 安装完整版：`brew install font-noto-sans-cjk-sc font-noto-serif-cjk-sc`。`warm-academic` 风格使用 `Songti SC` / `Kaiti SC` 等 macOS 内置字体，兼容性更好。

### ReportLab

- Code blocks lose line breaks without `esc_code()` — 脚本已自动处理
- CJK/Latin mixed text needs `wordWrap='CJK'` and `_font_wrap()` — 脚本已自动处理
- Canvas text (cover, footers) needs `_draw_mixed()` for CJK — 脚本已自动处理

### Mermaid

- `-e png` 是强制的：reportlab 的 ImageReader 不支持 SVG 格式
- mmdc 会原地修改 markdown 文件（替换 ` ```mermaid ` 为 `![](assets/...)`）

## WeasyPrint 故障时的替代方案：fpdf2

当 WeasyPrint 和 ReportLab 都无法使用时，可用 fpdf2 直接生成 PDF：

```bash
pip3 install fpdf2
```

```python
from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.add_font("CJK", "", "/Library/Fonts/Arial Unicode.ttf")
pdf.set_font("CJK", "", 10)
pdf.cell(0, 5, "中文内容", new_x="LMARGIN", new_y="NEXT")
pdf.output("output.pdf")
```

> 详细示例见 `references/fpdf2-cjk-fallback.md`

## 被合并的旧技能

此版本整合了以下旧技能的功能：

| 旧技能 | 对应新功能 | 状态 |
|--------|-----------|------|
| any2pdf / lovstudio-any2pdf | `--engine reportlab` | ✅ 已吸收 |
| arch-pdf | `--mermaid` | ✅ 已吸收 |
| markdown-to-pdf (LaTeX) | LaTeX 参考见 references/fallback-latex.md | ✅ 已吸收 |
| markdown-to-pdf 多风格扩展 | `--style art-nouveau/bauhaus/ink-wash/minimalism/typewriter/scholar` | ✅ 已吸收 |
