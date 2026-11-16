# skills/

五个技能目录。每个目录一个 `SKILL.md`（带 YAML frontmatter，`name` + `description` 是必需的），配套脚本和参考资料放在同级子目录里。

| 目录 | 大小 | 一句话 |
|---|---|---|
| `elegant-pdf/` | ~350K | Markdown → 印刷级 PDF，双引擎（WeasyPrint / ReportLab）+ 20 套风格 |
| `pdf-designer/` | ~20K | PDF 设计决策层，决定"这份内容该长什么样"，不负责渲染 |
| `frontend-design/` | ~160K | 前端设计红线 + 案例教材 + `quick_check.py` 交付自检 |
| `github-trending-digest/` | ~4M（其中 4M 是 demo 图） | GitHub Trending → 单文件 HTML 晨报 |
| `ai-musume/` | ~1.6M | AI 娘立绘七条公式 + 8 个角色的现成 prompt |

装法见仓库根目录 `install.sh`。直接 `cp -R skills/* ~/.claude/skills/` 也行。
