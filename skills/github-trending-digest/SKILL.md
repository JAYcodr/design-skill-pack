---
name: github-trending-digest
version: "1.0.0"
description: 把 GitHub Trending 榜单做成一份可直接交付的单文件 HTML 晨报星图。当用户要求「GitHub 每日/每周趋势」「trending 日报/晨报」「今天有什么新开源项目」「把趋势榜做成仪表盘/看板/HTML 报告」时使用。流程为抓取 Trending 总榜与语言分榜 → 去重合并 → 按固定版块归类并重写中文摘要 → 渲染零外部依赖的响应式单文件 HTML → 自动化自检。仅用 Python 3 标准库，无需 API Key、无需 npm 依赖、无需浏览器。
license: MIT
agent_created: true
metadata:
  author: WorkBuddy
display_name: "GitHub 趋势晨报"
display_name_en: "GitHub Trending Digest"
description_zh: "抓取 GitHub Trending 并生成「天文台星图」风格的单文件 HTML 晨报：交互式星座图 + 观测日志，分版块、全局连续编号，零外部依赖。"
description_en: "Turn GitHub Trending into a self-contained single-file HTML observatory starmap digest with themed constellations and continuous numbering."
visibility: "public"
---

# GitHub Trending Digest

把 GitHub Trending 的原始榜单，加工成一份**可以直接发出去**的中文晨报：深空天文台主题，每个仓库是星图上的一颗星，分星座（版块）、全局连续编号、中文摘要、零外部依赖单文件 HTML。

## 什么时候用

触发词：GitHub 趋势 / trending 日报 / 每日趋势晨报 / 今天有什么新开源项目 / 把趋势榜做成仪表盘或看板。

**不适用**：只想快速看几个仓库名（直接抓取并列表回答即可，不必上这套流水线）；需要历史趋势对比或 Star 增长曲线（本 skill 只取当前快照）。

## 环境要求

只需要 **Python 3.8+**，全部脚本仅用标准库（`urllib` / `re` / `json` / `html`）。
`node` 是可选的，仅在最后自检 JS 语法时使用；没有也不影响交付。

任何 agent（WorkBuddy / Claude Code / opencode / Cursor 等）只要能执行 shell 命令与读写文件，就能完整跑通。

```
SKILL_DIR = 本文件所在目录
scripts/fetch_trending.py   抓取 + 解析 + 去重合并
scripts/render.py           curated.json + 模板 -> 单文件 HTML
scripts/verify.py           22 项交付自检
assets/template.html        单文件 HTML 模板（内联全部 CSS/JS，10 个占位符）
assets/curated.example.json 完整可运行的示例输入
references/curation.md      版块划分与中文摘要写作规范  ← 第 2 阶段必读
references/troubleshooting.md 解析失效与常见坑
```

## 四阶段工作流

整条流水线是 **抓 → 编 → 渲 → 检**。第 1、3、4 阶段是确定性脚本，第 2 阶段是唯一需要你动脑的地方。

### 阶段 1 · 抓取（脚本，约 15 秒）

```bash
cd <工作目录>
python3 "$SKILL_DIR/scripts/fetch_trending.py" --out trending.json
```

默认抓总榜 + 8 个语言分榜（python / typescript / javascript / go / rust / c++ / java / jupyter-notebook），
按 `repo` 去重，语言分榜只补总榜没有的仓库，最终按今日新增 Star 降序排列。典型产出 120–170 个仓库。

常用变体：

| 需求 | 命令 |
|---|---|
| 只要总榜（最快） | `--langs ""` |
| 周榜 / 月榜 | `--since weekly` / `--since monthly` |
| 自定义语言 | `--langs python,rust,zig` |
| 只看中文项目 | `--spoken-language zh` |

抓完**必须先读一遍 `trending.json`**，对着真实描述做下一步，不要凭记忆编造仓库。

### 阶段 2 · 编排（你的核心工作）

**先读 `references/curation.md`**，然后产出 `curated.json`。这一步要做四件事：

1. **筛选**：从 150 左右的候选里挑 40–60 条。取舍看今日涨星、项目质量与版块平衡，不是简单截断 Top N。
2. **归类**：设计 5 个固定版块并把每条归位。默认版块（AI 主题日）：
   模型与多模态 / Agent 与 AI 应用 / 开发工具与效率 / 框架与基础设施 / 学习资源与精选清单。
   版块要按当天榜单的实际主题调整，不要硬套。
3. **写摘要**：每条一句 **≤60 字**的中文，说清"这东西是什么、解决什么问题"。英文原描述只是素材，必须重写，不能直译。
4. **配色**：5 个版块依次用 `s1`(紫) `s2`(蓝) `s3`(橙) `s4`(绿) `s5`(黄)，`color` 填 `var(--s1)`、`bg` 填 `var(--s1b)`。留空则按顺序自动补齐。

`curated.json` 结构（完整示例见 `assets/curated.example.json`）：

```json
{
  "captured_at": "2026-07-31T13:16:29+08:00",
  "title": "GitHub 每日趋势晨报",
  "headline": "GitHub <em>每日趋势</em>晨报",
  "kicker": "GitHub Trending · Daily Digest",
  "scope": "今日新增 Star（daily）",
  "source_html": "<a href=\"https://github.com/trending?since=daily\" target=\"_blank\" rel=\"noopener noreferrer\">github.com/trending（daily）</a>",
  "footer_note": "按 A / B / C / D / E 五个固定版块分组，序号全局连续编号。",
  "sections": [
    {"id":"models","name":"模型与多模态","icon":"01","color":"var(--s1)","bg":"var(--s1b)","desc":"一句话版块说明"}
  ],
  "items": [
    {"s":"models","repo":"huggingface/speech-to-speech","lang":"Python",
     "stars":9169,"today":1657,"forks":628,"src":"总榜 #1",
     "sum":"用开源模型搭建可本地运行的语音对话 Agent，串起识别、大模型与合成完整链路。"}
  ]
}
```

`captured_at` 用抓取时刻的北京时间，直接取 `trending.json` 里的 `fetched_at`，或：

```bash
TZ=Asia/Shanghai date "+%Y-%m-%dT%H:%M:%S+08:00"
```

`stars` / `today` / `forks` 必须是整数（不带引号、不带逗号），`repo` 必须是 `owner/name`。

### 阶段 3 · 渲染（脚本，秒级）

```bash
python3 "$SKILL_DIR/scripts/render.py" \
  --curated curated.json \
  --out github-trending-daily.html
```

渲染前会先校验 `curated.json`：字段缺失、摘要超 60 字、版块归属错误、数值类型不对，都会直接报错并指出是哪一条，修好再跑。
渲染成功会打印各版块条数分布。

**编号是渲染时自动生成的**：按 `sections` 顺序遍历，版块内按 `today` 降序，全局连续编号 01…N，不在版块内重新计数。不要在 `curated.json` 里手写序号。

### 阶段 4 · 自检 + 交付

```bash
python3 "$SKILL_DIR/scripts/verify.py" github-trending-daily.html
```

22 项检查覆盖：文档结构、零外部资源、外链 `target="_blank" rel="noopener noreferrer"`、
可见文本无 ISO 时间串、占位符清空、内嵌 JS 语法、摘要长度、仓库去重、版块归属、响应式断点。
**必须 0 失败才交付**。有 FAIL 就回到对应阶段修，不要手改产出的 HTML。

最后把 HTML 呈现给用户，并在回复里说明：数据来源与口径、收录条数、各版块分布、涨星冠军。

## 产出长什么样

单个 HTML 文件，约 40 KB，双击即开，可离线、可邮件附件、可直接部署。整体是一座「天文台」：深空主题 + 交互星图 + 观测日志。

- **Hero**：衬线大标题（金色高亮）、日期（北京时间人话格式）、抓取时刻、口径，加一条五格观测指标带（收录星体 / 今日增光合计 / 今夜最亮的星 / 覆盖语言 / 星座分区）
- **今夜星图**（核心视觉）：零依赖内联 SVG，JS 按黄金角螺旋把每个仓库画成一颗星——体积与光晕随今日新增 Star 对数缩放，5 个版块 = 5 个星座（各有专属色），星座内按编号虚线串联；位置由仓库名哈希决定，同一份数据每次渲染完全一致。悬停出 tooltip（仓库名 + 数据 + 摘要），点击星体直达日志对应行；单日涨星 ≥400 的亮星带脉冲光环，涨星冠军有「今夜最亮」标注；背景星野闪烁 + 偶发流星
- **星座图例**：悬停某星座图例让其他星座变暗，点击跳转对应版块
- **导航**：sticky 吸顶胶囊锚点，点击直达版块
- **观测日志**：按星座分组的账本式行长列表（非卡片），每行含全局连续编号、`owner / repo`、✦ 亮星标、≤60 字摘要、语言色点 / 来源 / Star / Fork、今日增光数值 + 对数亮度条、跳转按钮
- **页脚**：总条数、分组口径、语言分布磁贴、数据源链接、生成时间
- 深空主题（夜空蓝黑 + 金色），回到顶部悬浮按钮，支持 `prefers-reduced-motion`

## 硬性约束

这些是交付底线，`verify.py` 会逐条检查：

1. **单文件、零外部资源**。CSS 与 JS 全部内联，不引 CDN、不引字体、不引图片。图标一律用内联 SVG。
2. **摘要 ≤60 字**，中文重写，不直译英文描述，不留空。
3. **全局连续编号**，跨版块累加。
4. **所有外链** `target="_blank" rel="noopener noreferrer"`。
5. **时间只出现人话格式**。页面用 `Intl.DateTimeFormat` + `timeZone: "Asia/Shanghai"` 渲染成
   「2026 年 7 月 31 日 星期五 中午 13:16」，ISO 串只允许作为 JS 常量存在，不得出现在可见文本。
6. **数据必须现抓**，不靠模型记忆编造仓库、Star 数或描述。

## 换个主题复用

模板与脚本不绑定 GitHub。想做别的榜单（Hugging Face Trending、Product Hunt、arXiv 每日精选等）：

- 照着 `scripts/fetch_trending.py` 的 `parse()` 写一个新的解析器，输出同样的 `items` 结构；
- `curated.json` 里改 `title` / `headline` / `kicker` / `scope` / `source_html` / `footer_note` 与 `sections`；
- `render.py` 与 `verify.py` 完全不用改。

字段语义上，`repo` 是标题（会渲染成 `owner / name` 两段式），`src` 是来源 chip，`lang` 是带色点的分类 chip，`stars` / `today` / `forks` 是三个数值 chip。
