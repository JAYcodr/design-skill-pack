# design-skill-pack

四个 Agent Skill，给会写文档和做页面的人用。全部是**纯本地、零 API Key**：一个 Python 文件 + 一堆 markdown 参考资料 + HTML 模板，脚本只依赖 Python 3 标准库或装得上的常规包。

| Skill | 干什么 | 依赖 |
|---|---|---|
| [`elegant-pdf`](skills/elegant-pdf/) | 一条命令把 Markdown 排成印刷级 PDF：10 套设计风格（WeasyPrint）+ 10 套主题（ReportLab），双引擎自动回退，支持封面、自动目录、Mermaid 图、中文排版 | `markdown-it-py` `PyYAML` `mdit-py-plugins` + weasyprint **或** reportlab |
| [`pdf-designer`](skills/pdf-designer/) | PDF 的**决策层**：先读内容感受气质，再定风格/字体/空间/强调，最后交给 elegant-pdf 渲染。10 套风格体系 + 内容→风格匹配指南 | 无（纯文档 + 配套 elegant-pdf） |
| [`frontend-design`](skills/frontend-design/) | 做任何网页/落地页/UI 之前的必读：三条硬红线 + 案例教材 + 交付门，附 `quick_check.py` 自动查裂图、字号过小、缺 viewport 之类的硬伤 | Python 3 标准库 |
| [`github-trending-digest`](skills/github-trending-digest/) | 把 GitHub Trending 抓下来，做成单文件 HTML 中文晨报：天文台星图主题、星座分版块、全局连号、零外部依赖 | Python 3 标准库 |

## 安装

### 一键（推荐）

```bash
git clone https://github.com/JAYcodr/design-skill-pack.git
cd design-skill-pack
./install.sh              # 装到 ~/.claude/skills/
./install.sh --agents     # 装到 ~/.agents/skills/（DSH / Hermes 等）
./install.sh --both       # 两边都装
```

脚本做的事：把 `skills/` 下四个目录复制到目标目录，已存在则提示、不覆盖（`--force` 才覆盖）。

### 手动

```bash
cp -R skills/* ~/.claude/skills/
```

然后重启你的 agent 会话，skill 列表里就会多出这四项。

## 装环境

```bash
# PDF 必需
pip3 install markdown-it-py PyYAML mdit-py-plugins

# 两条渲染路线，至少装一条
pip3 install weasyprint        # 或者：brew install weasyprint
pip3 install reportlab         # CJK 最稳的一条

# 只想转 Mermaid 图才需要
npm install -g @mermaid-js/mermaid-cli
```

其余三个 skill 不需要装任何东西。

## 直接用

```bash
# Markdown → 漂亮 PDF（默认 auto：先 WeasyPrint，失败自动切 ReportLab）
python3 ~/.claude/skills/elegant-pdf/scripts/md2elegant.py 输入.md -o 输出.pdf

# 指定风格
python3 ~/.claude/skills/elegant-pdf/scripts/md2elegant.py 输入.md --engine weasyprint --style swiss
python3 ~/.claude/skills/elegant-pdf/scripts/md2elegant.py 输入.md --engine reportlab --theme warm-academic

# 含 Mermaid 图
python3 ~/.claude/skills/elegant-pdf/scripts/md2elegant.py 输入.md --mermaid

# 页面交付前自检
python3 ~/.claude/skills/frontend-design/scripts/quick_check.py index.html

# GitHub 晨报（抓数据 + 渲染 + 自检）
python3 ~/.claude/skills/github-trending-digest/scripts/fetch_trending.py --out trending.json
python3 ~/.claude/skills/github-trending-digest/scripts/render.py trending.json -o 晨报.html
```

Markdown 要带 YAML frontmatter：

```yaml
---
title: 文档标题
subtitle: 副标题
author: 你的名字
date: 2026-11-16
lang: zh-CN
---
```

## 风格预览

`elegant-pdf` 的 WeasyPrint 风格：`warm-academic` `swiss` `japanese` `scholar` `bauhaus` `art-nouveau` `ink-wash` `minimalism` `typewriter` `cyberpunk`
ReportLab 主题：`warm-academic` `nord-frost` `github-light` `ocean-breeze` 等 11 套。

`github-trending-digest` 带 6 套完整示例，在 [`assets/demos/`](skills/github-trending-digest/assets/demos/)，直接用浏览器打开 .html 就能看。

## 三个 skill 怎么配合

```
写内容 → pdf-designer（定风格）→ elegant-pdf（出 PDF）
做页面 → frontend-design（守红线、写逐屏稿）→ 交付前 quick_check.py
看趋势 → github-trending-digest（抓 + 渲染）→ 单文件 HTML
```

## License

MIT。各 skill 内的原始版权声明见各自目录下的 LICENSE / frontmatter。
