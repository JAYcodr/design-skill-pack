---
name: pdf-designer
description: >
  PDF 设计的决策层——先读内容感受气质，再做设计决策（风格/字体/空间/强调），
  最后交给 elegant-pdf 执行渲染。10 套完整风格体系 + 内容→风格匹配指南。
  Use BEFORE generating any PDF when visual quality matters.
  Must be paired with elegant-pdf for execution.
version: 1.0.0
category: creative
metadata:
  author: "design-skill-pack <noreply@example.com>"
  hermes:
    triggers:
      - "PDF 设计"
      - "文档排版"
      - "选哪个风格"
      - "这份内容适合什么风格"
      - "设计决策"
    tags: [pdf, design, typography, layout, style-selection, decision-making]
---

# pdf-designer — PDF 设计决策层

> **执行层是 elegant-pdf**。本 skill 负责决策，不负责渲染。
>
> 工作流：pdf-designer（分析内容 → 选风格 → 做决策）→ elegant-pdf（执行渲染）。

## 核心原则：先读内容，再选风格

本 skill 的第一条。不要先选模板，读完内容再说它应该长什么样。

### 工作流

```
内容分析 → 风格选择 → 三项决策 → 交给 elegant-pdf
```

## Step 1: 内容分析

读完整篇内容，判断：

| 维度 | 问题 |
|------|------|
| 情感基调 | 理性/温暖/冷静/张扬？ |
| 信息密度 | 密集（数据表格）还是稀疏（散文诗歌）？ |
| 阅读场景 | 快速扫描（报告）还是慢读品味（文学）？ |
| 受众预期 | 需要权威感还是亲近感？ |

## Step 2: 风格匹配

### 10 套风格体系

| # | 风格 | 排版哲学 | 引擎支持 |
|---|------|----------|----------|
| ① | **瑞士国际主义** | 网格 + 编号 + 红色强调 + 信息扫描 | WeasyPrint `--style swiss` |
| ② | **日式文艺杂志** | 留白即内容 + 衬线 + 暖纸色 + Z 型慢读 | WeasyPrint `--style japanese` |
| ③ | **赛博朋克档案** | 终端界面 + 荧光绿 + 等宽数据 + 解密阅读 | WeasyPrint `--style cyberpunk` |
| ④ | **暖调学术风** | 金褐 × 象牙白 + 楷体 + 温润权威 | Both WeasyPrint & ReportLab `--style warm-academic` |
| ⑤ | **Nord 冰霜** | 蓝灰北欧风，清爽现代，代码友好 | ReportLab `--engine reportlab --theme nord-frost` |
| ⑥ | **GitHub 轻** | 蓝白极简，开发者风格，无装饰 | ReportLab `--engine reportlab --theme github-light` |
| ⑦ | **期刊蓝** | 藏蓝严谨，IEEE 期刊风格 | ReportLab `--engine reportlab --theme ieee-journal` |
| ⑧ | **海洋** | 青绿色调，清新自然，创意内容 | ReportLab `--engine reportlab --theme ocean-breeze` |
| ⑨ | **极简主义** | 超大留白 + 居中 + light 字重 + 无装饰 + 三线表格 | WeasyPrint `--style minimalism` |
| ⑩ | **复古打字机** | 牛皮纸 + 压痕 + Courier + 咖啡渍 + DOC_N 元信息感 | WeasyPrint `--style typewriter` |

### 风格选择速查表

| 内容类型 | 推荐风格 | 原因 |
|----------|----------|------|
| 技术文档、系统分析、API 文档 | swiss | 网格 + 编号 + 高信息密度 |
| 个人随笔、文化评论、文学 | japanese | 留白 + 慢读 + 纸感温度 |
| 正式报告、白皮书、学术论文 | warm-academic | 金褐权威 + 楷体温润 |
| 科幻、游戏设计文档、黑客文化 | cyberpunk | 终端质感 + 数据美学 |
| 纯学术论文（无装饰需求） | scholar | 极简，让内容说话 |
| 创意作品集、艺术相关 | bauhaus | 几何表现力 |
| 环保/自然/生活方式 | warm-natural | 大地色系 + 有机形态 |
| 极简文档、草稿级、纯文字 | minimalism | 留白即尊重 |
| 档案感、机密文档、复古笔记 | typewriter | 物理材质感 + 等宽 |

### 排除法（什么不该选）

- 内容严肃 + 赛博朋克 = 认知失调
- 数据密集 + 日式 = 留白太多，信息没地方放
- 文学随笔 + 瑞士 = 冰冷，没有温度

## Step 3: 三项设计决策

选定风格后，在这三个维度上做具体决策：

### A. 字体配对

| 风格 | 标题字体 | 正文字体 | 等宽字体 |
|------|----------|----------|----------|
| swiss | Noto Sans SC Bold | Noto Sans SC | SF Mono |
| japanese | Noto Serif SC / 楷体 | Noto Serif SC | SF Mono |
| cyberpunk | Noto Sans SC Black | Noto Sans SC | Courier New |
| warm-academic | 楷体 (Kaiti SC) | 宋体 (Songti SC) | SF Mono |

**规则**：
- 衬线 = 叙事/温暖
- 无衬线 = 理性/现代
- 等宽 = 技术/冷酷

### B. 空间节奏

| 风格 | 页边距 | 行距 | 段间距 | 信息密度 |
|------|--------|------|--------|----------|
| swiss | 18-20mm | 1.6 | 紧凑 | 高 |
| japanese | 25-30mm | 1.8 | 宽松 | 低 |
| cyberpunk | 16-18mm | 1.6 | 紧凑 | 高 |
| warm-academic | 20-22mm | 1.75 | 中等 | 中 |

### C. 强调系统

| 风格 | 主强调色 | 使用方式 | 次要色 |
|------|----------|----------|--------|
| swiss | #e63946 红 | 编号、左边条、表头 | 黑/白 |
| japanese | #8b5a2b 赭石 | 页眉线、印章、❧ 装饰 | #b8a890 石色 |
| cyberpunk | #00ff9d 绿 | 边框、标签、状态指示 | #00a8ff 蓝 |
| warm-academic | #b8a88a 金褐 | H1 底线、H2 左边线、封面渐变 | 象牙白 |

**规则**：不超过 2 个强调色。强调色用于结构标记（边框/线/编号），不用于大面积填充。

## Step 4: 移交 elegant-pdf 执行

```bash
python3 ~/.agents/skills/elegant-pdf/scripts/md2elegant.py input.md \
    --style swiss \          # 来自 Step 2 的决策
    -o output.pdf
```

## 完整风格档案

详细的设计 DNA、签名元素、反模式 → 见 `references/style-library.md`。

## 与 elegant-pdf 的关系

```
用户说"生成 PDF"但没指定风格
    ↓
pdf-designer（加载）
    ↓
读内容 → 分析气质 → 输出风格建议 + 三项决策
    ↓
用户确认
    ↓

elegant-pdf --engine <引擎> --style <风格>（执行）
    ↓
精美 PDF ✅
```

**elegant-pdf v2.0 双引擎**：
- WeasyPrint 引擎：支持 swiss / japanese / cyberpunk / warm-academic 4 种风格
- ReportLab 引擎：支持 warm-academic / nord-frost / github-light 等 10 种主题
- auto 模式：优先 WeasyPrint，失败自动回退 ReportLab

pdf-designer 给出的风格建议 → 映射到合适的 `--engine --style` 参数即可。

## 什么时候不用 pdf-designer

- 用户明确指定了风格（"用瑞士风格排"）→ 直接用 elegant-pdf
- 纯技术文档、草稿级输出 → 不需要设计决策
- 内容少于 1 页 → 不需要
