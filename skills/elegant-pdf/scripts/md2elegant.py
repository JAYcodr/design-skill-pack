#!/usr/bin/env python3
"""elegant-pdf: Markdown → 印刷级 PDF（统一入口）

多引擎支持:
  - weasyprint (默认): HTML/CSS 模板渲染，4 套设计风格
  - reportlab: 基于 any2pdf 引擎，10 套主题，CJK 稳定
  - auto: 先试 weasyprint，失败自动回退 reportlab

可选 mermaid 预处理: 自动将 ```mermaid 代码块转为 PNG 嵌入文档。

Usage:
    python3 md2elegant.py input.md -o output.pdf
    python3 md2elegant.py input.md --engine reportlab --theme nord-frost
    python3 md2elegant.py input.md --mermaid
    python3 md2elegant.py input.md --engine weasyprint --style swiss
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import date as dt_date

# ─── Dependencies ─────────────────────────────────────────────

try:
    from markdown_it import MarkdownIt
except ImportError:
    sys.exit("ERROR: pip3 install markdown-it-py")

try:
    import yaml
except ImportError:
    sys.exit("ERROR: pip3 install PyYAML")

try:
    from mdit_py_plugins.container import container_plugin
except ImportError:
    sys.exit("ERROR: pip3 install mdit-py-plugins")

# WeasyPrint: try Python API first, fallback to Homebrew CLI
_HAS_WEASYPRINT_PY = False
_WEASYPRINT_CLI = "/opt/homebrew/bin/weasyprint"
try:
    import weasyprint
    _HAS_WEASYPRINT_PY = True
except (ImportError, OSError):
    pass

_EMOJI_RE = re.compile(
    "["
    "\\U0001F300-\\U0001F9FF"
    "\\U0001FA00-\\U0001FAFF"
    "\\U0001F600-\\U0001F64F"
    "\\U0001F680-\\U0001F6FF"
    "\\U0001F900-\\U0001F95F"
    "\\U00002600-\\U000027BF"
    "\\U00002B50"
    "\\U0001F000-\\U0001F02F"
    "\\U0001F0A0-\\U0001F0FF"
    "\\U0001F100-\\U0001F1FF"
    "\\U0001F200-\\U0001F2FF"
    "\\U0001F300-\\U0001F5FF"
    "\\U0001F780-\\U0001F7FF"
    "\\U0001F800-\\U0001F8FF"
    "\\U00002300-\\U000023FF"
    "\\U00002B00-\\U00002BFF"
    "]+",
    re.UNICODE,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTLAB_ENGINE = os.path.join(SCRIPT_DIR, "reportlab", "md2pdf.py")

# ─── Mermaid preprocessing ────────────────────────────────────

def has_mermaid(text: str) -> bool:
    return "```mermaid" in text

def run_mermaid(md_path: str) -> None:
    """Run mmdc to convert mermaid blocks to PNG.
    Must cd to the file's directory so relative paths resolve.
    """
    md_dir = os.path.dirname(os.path.abspath(md_path))
    md_name = os.path.basename(md_path)
    assets_dir = os.path.join(md_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    result = subprocess.run(
        ["mmdc", "-i", md_name, "-o", md_name, "-a", assets_dir, "-e", "png"],
        cwd=md_dir,
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        print(f"  ⚠ mmdc warning (rc={result.returncode}): {result.stderr[:300]}")
    else:
        print(f"  ✓ Mermaid diagrams rendered to PNG")

# ─── WeasyPrint helpers ───────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from markdown body."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    body = parts[2].strip()
    return meta, body


def md_to_html(md_text: str) -> str:
    """Convert markdown to HTML using markdown_it.

    支持 ::: fenced div 容器（intro-block / quote-box / memo-section /
    memo-title / section-note / theorem）触发模板里的自定义设计块。
    """
    md = MarkdownIt("commonmark", {"typographer": True, "html": True})
    md.enable(["table", "strikethrough", "linkify"])
    for container_name in (
        "intro-block", "quote-box", "memo-section",
        "memo-title", "section-note", "theorem",
    ):
        md.use(container_plugin, container_name, marker=":")
    return add_heading_ids(md.render(md_text))


def add_heading_ids(html: str) -> str:
    """给 h1-h3 补 id，TOC 的 target-counter 才有可跳转的锚点。"""
    seen = {}

    def repl(m):
        lvl, inner = m.group(1), m.group(2)
        plain = re.sub(r'<[^>]+>', '', inner)
        base = "sec-" + re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', plain).strip('-').lower()
        base = base[:60] or "sec"
        n = seen.get(base, 0)
        seen[base] = n + 1
        aid = base if n == 0 else f"{base}-{n}"
        return f'<h{lvl} id="{aid}">{inner}</h{lvl}>'

    return re.sub(r'<h([1-3])>(.+?)</h\1>', repl, html, flags=re.DOTALL)


_HEADING_RE = re.compile(r'<h([1-3])(?:\s+id="([^"]*)")?\s*>(.+?)</h[1-3]>', re.DOTALL)


def extract_toc(html_body: str) -> list[dict]:
    """Extract headings from HTML for TOC generation."""
    items = []
    for m in _HEADING_RE.finditer(html_body):
        level = int(m.group(1))
        anchor = m.group(2)
        text = m.group(3).strip()
        text = re.sub(r'<[^>]+>', '', text)
        if not anchor:
            anchor = "sec-" + re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff-]', '-', text).strip('-').lower()
        items.append({"level": level, "text": text, "anchor": anchor})
    return items


def build_toc_html(items: list[dict]) -> str:
    """Build TOC list HTML from heading items."""
    lines = []
    for item in items:
        css_class = f"toc-l{item['level']}"
        indent = "    " * (item["level"] - 1)
        lines.append(
            f'{indent}<li class="{css_class}">'
            f'<a href="#{item["anchor"]}">{item["text"]}</a>'
            f"</li>"
        )
    return "\n".join(lines)


def render_html_to_pdf(html_path: str, pdf_path: str) -> None:
    """Render HTML to PDF. Python API first, then CLI fallback."""
    if _HAS_WEASYPRINT_PY:
        doc = weasyprint.HTML(filename=html_path)
        doc.write_pdf(pdf_path)
        return
    cli = _WEASYPRINT_CLI or "weasyprint"
    # Clear PYTHONPATH to avoid Hermes venv contamination —
    # the venv's Pillow (Python 3.11) breaks WeasyPrint (Python 3.14)
    clean_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    result = subprocess.run(
        [cli, html_path, pdf_path],
        capture_output=True, text=True, timeout=120,
        env=clean_env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"weasyprint failed (rc={result.returncode}):\n{result.stderr[:500]}")


def verify_pdf_size(pdf_path: str) -> int:
    """Return PDF size in KB. Returns 0 if absent."""
    if os.path.exists(pdf_path):
        return os.path.getsize(pdf_path) // 1024
    return 0


# ─── WeasyPrint path ──────────────────────────────────────────

def build_weasyprint(args, meta: dict, body_md: str) -> None:
    """Render via WeasyPrint HTML templates (4 design styles)."""
    title = args.title or meta.get("title", os.path.splitext(os.path.basename(args.input))[0])
    subtitle = meta.get("subtitle", "")
    author = args.author or meta.get("author", "")
    date_str = meta.get("date", dt_date.today().isoformat())
    lang = meta.get("lang", "zh-CN")
    cover_label = meta.get("cover_label", "")

    body_html = md_to_html(body_md)

    if args.strip_emoji:
        body_html = _EMOJI_RE.sub("", body_html)
        title = _EMOJI_RE.sub("", title).strip()
        subtitle = _EMOJI_RE.sub("", subtitle).strip()

    toc_items = extract_toc(body_html) if not args.no_toc else []
    toc_html = build_toc_html(toc_items) if toc_items else ""

    STYLE_TEMPLATES = {
        "warm-academic": "warm-academic.html",
        "swiss": "swiss.html",
        "japanese": "japanese.html",
        "cyberpunk": "cyberpunk.html",
        "art-nouveau": "art-nouveau.html",
        "bauhaus": "bauhaus.html",
        "ink-wash": "ink-wash.html",
        "minimalism": "minimalism.html",
        "typewriter": "typewriter.html",
        "scholar": "scholar.html",
    }
    template_filename = STYLE_TEMPLATES.get(args.style, "warm-academic.html")

    template_path = os.path.join(SCRIPT_DIR, "..", "templates", template_filename)
    if not os.path.exists(template_path):
        template_path = os.path.join(
            os.path.expanduser("~/.agents/skills/elegant-pdf/templates"),
            template_filename,
        )
    if not os.path.exists(template_path):
        sys.exit(f"ERROR: template not found: {template_path}")

    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    html = template.format(
        lang=lang, title=title, running_title=title,
        cover_label=cover_label, subtitle=subtitle,
        author_line=author, date_line=date_str,
        toc_items=toc_html, body=body_html,
    )

    if args.no_cover:
        html = re.sub(
            r'<!-- ===== Cover ===== -->.*?<!-- ===== TOC ===== -->',
            "", html, flags=re.DOTALL
        )
    if args.no_toc or not toc_items:
        html = re.sub(
            r'<!-- ===== TOC ===== -->.*?<!-- ===== Body ===== -->',
            "", html, flags=re.DOTALL
        )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", encoding="utf-8", delete=False
    ) as f:
        f.write(html)
        temp_html = f.name

    output = args.output or os.path.splitext(args.input)[0] + ".pdf"

    try:
        print(f"  Rendering [WeasyPrint/{args.style}] → {output} ...")
        render_html_to_pdf(temp_html, output)
        size_kb = os.path.getsize(output) / 1024
        print(f"  ✓ Done ({size_kb:.0f} KB, {len(toc_items)} sections)")
    except Exception as e:
        print(f"  ✗ WeasyPrint failed: {e}")
        print(f"  HTML saved at: {temp_html}")
        raise
    finally:
        if os.path.exists(temp_html):
            os.unlink(temp_html)


# ─── ReportLab (any2pdf) path ─────────────────────────────────

def build_reportlab(args, body_md: str, raw: str) -> None:
    """Render via reportlab (any2pdf engine, 10 themes)."""
    if not os.path.exists(REPORTLAB_ENGINE):
        # Fallback: try lovstudio-any2pdf (may have been deleted; try system path)
        alt_path = os.path.expanduser(
            "~/.agents/skills/elegant-pdf/scripts/reportlab/md2pdf.py"
        )
        if os.path.exists(alt_path):
            engine = alt_path
        else:
            sys.exit(f"ERROR: reportlab engine not found at {REPORTLAB_ENGINE}")

    # Map style to theme for reportlab backend
    theme_map = {
        "warm-academic": "warm-academic",
        "swiss": "nord-frost",
        "japanese": "paper-classic",
        "cyberpunk": "solarized-light",
        "art-nouveau": "warm-academic",
        "bauhaus": "github-light",
        "ink-wash": "warm-academic",
        "minimalism": "github-light",
        "typewriter": "classic-thesis",
        "scholar": "classic-thesis",
        # Direct any2pdf themes also accepted
    }
    theme = args.theme or theme_map.get(args.style, "warm-academic")

    cmd = [
        sys.executable, REPORTLAB_ENGINE,
        "--input", args.input,
        "--theme", theme,
    ]
    if args.output:
        cmd += ["--output", args.output]
    if args.title:
        cmd += ["--title", args.title]
    if args.author:
        cmd += ["--author", args.author]

    print(f"  Rendering [ReportLab/{theme}] → {args.output or '<input>.pdf'} ...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  ✗ ReportLab failed (rc={result.returncode})")
        print(f"  stderr: {result.stderr[:500]}")
        sys.exit(1)
    # Print engine's output
    for line in result.stdout.strip().split("\n"):
        print(f"  {line}")
    size_kb = verify_pdf_size(args.output or os.path.splitext(args.input)[0] + ".pdf")
    if size_kb > 0:
        print(f"  ✓ Done ({size_kb} KB)")


# ─── Main ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="elegant-pdf: Markdown → 印刷级 PDF（统一入口）"
    )
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("-o", "--output", help="Output PDF path (default: <input-stem>.pdf)")
    parser.add_argument("--title", help="Override cover title")
    parser.add_argument("--author", help="Override author")
    parser.add_argument("--no-cover", action="store_true", help="Skip cover page")
    parser.add_argument("--no-toc", action="store_true", help="Skip table of contents")
    parser.add_argument("--strip-emoji", action="store_true", help="Remove emoji (formal docs)")
    parser.add_argument(
        "--style",
        default="warm-academic",
        help="Visual style for weasyprint engine (default: warm-academic)",
    )
    parser.add_argument(
        "--theme",
        default=None,
        help="Explicit theme name for reportlab backend (overrides --style→theme mapping)",
    )
    parser.add_argument(
        "--engine",
        choices=["weasyprint", "reportlab", "auto"],
        default="auto",
        help="Rendering engine (default: auto — try weasyprint, fallback reportlab)",
    )
    parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Preprocess ```mermaid blocks to PNG via mmdc",
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.exists(args.input):
        sys.exit(f"ERROR: file not found: {args.input}")

    with open(args.input, encoding="utf-8") as f:
        raw = f.read()

    # Mermaid preprocessing (if requested or if file contains mermaid blocks)
    if args.mermaid or has_mermaid(raw):
        print("  🔄 Preprocessing Mermaid diagrams ...")
        run_mermaid(args.input)
        # Re-read file (mmdc modifies it in-place)
        with open(args.input, encoding="utf-8") as f:
            raw = f.read()

    # Parse frontmatter (needed by both engines)
    meta, body_md = parse_frontmatter(raw)

    # Set default output path
    if not args.output:
        args.output = os.path.splitext(args.input)[0] + ".pdf"

    # ── Engine selection ──

    if args.engine == "weasyprint":
        build_weasyprint(args, meta, body_md)

    elif args.engine == "reportlab":
        build_reportlab(args, body_md, raw)

    else:  # auto — try weasyprint, fall back to reportlab
        weasyprint_cli_exists = os.path.exists(_WEASYPRINT_CLI)
        if _HAS_WEASYPRINT_PY or weasyprint_cli_exists:
            try:
                build_weasyprint(args, meta, body_md)
                # Verify PDF has content (WeasyPrint can silently fail on CJK)
                size_kb = verify_pdf_size(args.output)
                if size_kb < 80:
                    print(f"  ⚠ PDF seems empty ({size_kb} KB, threshold <80KB), trying reportlab fallback...")
                    raise RuntimeError("Empty PDF from WeasyPrint")
                return
            except Exception as e:
                print(f"  ⚠ WeasyPrint failed ({e}), falling back to reportlab...")
        else:
            print(f"  ℹ WeasyPrint not available, using reportlab engine")

        build_reportlab(args, body_md, raw)


if __name__ == "__main__":
    main()
