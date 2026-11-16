#!/usr/bin/env python3
"""事实检查：只量能核对的东西，不判断好不好看。

检查：裂图 / 资源路径 / 空标题 / 缺 viewport / 无媒体查询 /
      字号过小 / 图片缺 alt / 占位残留 / 外链依赖 / 调试残留。

用法：
    python3 scripts/quick_check.py <file.html> [--json] [--min-body 14] [--min-label 12]

退出码：0 = 无硬伤；1 = 有硬伤；2 = 用法/文件错误。
"""

import argparse
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

FONT_SIZE_RE = re.compile(
    r"font-size\s*:\s*(?:clamp\(\s*([\d.]+)\s*(px|rem|em)|([\d.]+)\s*(px|rem|em))", re.I)


def font_size_px(match):
    """px 直接取；rem/em 按 16px 根字号折算；clamp() 取最小档（可读性看下限）。"""
    if match.group(1):
        value, unit = float(match.group(1)), match.group(2)
    else:
        value, unit = float(match.group(3)), match.group(4)
    return value if unit.lower() == "px" else value * 16

DATA_URI_RE = re.compile(r"data:[^\"')\s]+;base64,([A-Za-z0-9+/=]+)")
PLACEHOLDER_RE = re.compile(
    r"lorem ipsum|todo|待填|待补|待定|占位|示例文本|此处填写|xxxx", re.I)
EXTERNAL_RE = re.compile(r"^https?://|^//", re.I)


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.in_title = False
        self.lang = None
        self.has_viewport = False
        self.has_favicon = False
        self.images = []
        self.scripts = []
        self.stylesheets = []
        self.text = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html":
            self.lang = attrs.get("lang")
        elif tag == "title":
            self.in_title = True
        elif tag == "meta":
            if (attrs.get("name") or "").lower() == "viewport":
                self.has_viewport = True
        elif tag == "link":
            rel = (attrs.get("rel") or "").lower()
            if "icon" in rel:
                self.has_favicon = True
            if "stylesheet" in rel and attrs.get("href"):
                self.stylesheets.append(attrs["href"])
        elif tag == "img":
            self.images.append(attrs)
        elif tag == "script":
            if attrs.get("src"):
                self.scripts.append(attrs["src"])
            self.skip_depth += 1
        elif tag == "style":
            self.skip_depth += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ("script", "style") and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        elif self.skip_depth == 0:
            self.text.append(data)


def resolve_local(ref, base_dir):
    """本地引用返回 (是否本地, 是否存在)；远程/内联返回 (False, True)。"""
    ref = (ref or "").strip()
    if not ref or ref.startswith("#"):
        return False, True
    if ref.lower().startswith(("data:", "blob:", "mailto:", "tel:", "javascript:")):
        return False, True
    if EXTERNAL_RE.match(ref):
        return False, True
    path = ref.split("?")[0].split("#")[0]
    return True, (base_dir / path).is_file()


def check_file(path, min_body=14, min_label=12):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"找不到文件：{path}")
    raw = p.read_text(encoding="utf-8", errors="replace")
    collector = Collector()
    collector.feed(raw)
    collector.close()

    base_dir = p.parent
    hard, warn, info = [], [], []
    title = "".join(collector.title).strip()
    visible = " ".join(" ".join(collector.text).split())

    # 本地外部 CSS / JS 一并扫描；远程文件不抓（单文件交付本来也不该依赖它们）
    style_sources = [raw]
    script_sources = []
    for href in collector.stylesheets:
        local, exists = resolve_local(href, base_dir)
        if local and exists:
            style_sources.append((base_dir / href.split("?")[0]).read_text(encoding="utf-8", errors="replace"))
    for src in collector.scripts:
        local, exists = resolve_local(src, base_dir)
        if local and exists:
            script_sources.append((base_dir / src.split("?")[0]).read_text(encoding="utf-8", errors="replace"))
    style_text = "\n".join(style_sources)
    script_text = "\n".join(script_sources)
    sizes = [font_size_px(m) for m in FONT_SIZE_RE.finditer(style_text)]
    small_label = [s for s in sizes if s < min_label]
    small_body = [s for s in sizes if s < min_body]

    # ---- 硬伤 ----
    if not title:
        hard.append("缺少 <title>（或为空）")
    for ref in [img.get("src") for img in collector.images] + collector.scripts + collector.stylesheets:
        local, exists = resolve_local(ref, base_dir)
        if local and not exists:
            hard.append(f"本地资源不存在：{ref}")
    for img in collector.images:
        src = (img.get("src") or "").strip()
        if src.startswith("data:image") and len(src) < 64:
            hard.append("图片 data URI 看起来是空的")
            break

    # ---- 警告 ----
    if not collector.has_viewport:
        warn.append("没有 <meta name=\"viewport\">：手机上会按桌面缩放（固定尺寸海报可忽略）")
    if "@media" not in style_text:
        warn.append("没有媒体查询 @media：窄屏布局没做（固定尺寸交付可忽略）")
    external = [ref for ref in collector.scripts + collector.stylesheets
                if EXTERNAL_RE.match((ref or "").strip())]
    if external:
        warn.append(f"外链资源 {len(external)} 个（{', '.join(external[:3])}）：单文件交付要 base64 内嵌")
    missing_alt = [img.get("src", "")[:40] for img in collector.images if "alt" not in img]
    if missing_alt:
        warn.append(f"图片缺 alt {len(missing_alt)} 张：{', '.join(missing_alt[:3])}")
    if small_body and small_label:
        warn.append(f"字号低于正文下限 {min_body:g}px：{len(small_body)} 处（最小 {min(small_body):g}px）；"
                    f"低于标签下限 {min_label:g}px：{len(small_label)} 处")
    elif small_body:
        warn.append(f"字号低于正文下限 {min_body:g}px：{len(small_body)} 处（最小 {min(small_body):g}px）")
    elif small_label:
        info.append(f"有 {len(small_label)} 处字号低于 {min_label:g}px（图注/页脚可接受，正文字号要查）")
    placeholders = sorted({m.group(0) for m in PLACEHOLDER_RE.finditer(visible)})
    if placeholders:
        warn.append(f"可见文本疑似占位：{', '.join(placeholders)}")
    if not collector.has_favicon:
        info.append("没有 favicon：作品习惯项，不是硬伤")

    # ---- 提示 ----
    data_uris = DATA_URI_RE.findall(raw)
    data_size = sum(len(x) * 3 // 4 for x in data_uris)
    if data_uris:
        info.append(f"内联图片 {len(data_uris)} 张，约 {data_size // 1024} KB")
    if re.search(r"console\.log\s*\(", raw + script_text):
        info.append("代码里有 console.log：交付前清掉调试残留")
    if ("@keyframes" in style_text or re.search(r"(?:animation|transition)\s*:", style_text)) \
            and "prefers-reduced-motion" not in style_text:
        info.append("有动画但没有 prefers-reduced-motion 降级：对晕动症用户不友好")
    if not collector.lang:
        info.append("html 缺 lang 属性")

    return {
        "file": str(p),
        "size": len(raw.encode("utf-8")),
        "lines": raw.count("\n") + 1,
        "hard": hard,
        "warn": warn,
        "info": info,
        "stats": {
            "images": len(collector.images),
            "font_sizes": len(sizes),
            "external_refs": len(external),
            "data_uris": len(data_uris),
        },
    }


def render_report(result):
    size_label = f"{result['size'] // 1024} KB" if result['size'] >= 1024 else f"{result['size']} B"
    lines = [f"== {result['file']} ==",
             f"{size_label} · {result['lines']} 行 · "
             f"图 {result['stats']['images']} · 字号声明 {result['stats']['font_sizes']}（rem 按 16px 折算）· "
             f"外链 {result['stats']['external_refs']}"]
    sections = [("硬伤（必须修）", result["hard"]), ("警告（逐条判断）", result["warn"]), ("提示", result["info"])]
    for title, items in sections:
        lines.append("")
        lines.append(f"-- {title} --")
        lines.extend([f"  ✗ {item}" for item in items] if items else ["  （无）"])
    lines.append("")
    lines.append("脚本没检查：控制台运行时错误、真实对比度、视觉质量——这些必须看截图。")
    lines.append("结论：" + ("有硬伤，修完再交。" if result["hard"] else "无硬伤；警告逐条判断后再交。"))
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="前端交付前的事实检查")
    parser.add_argument("files", nargs="+")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--min-body", type=float, default=14)
    parser.add_argument("--min-label", type=float, default=12)
    args = parser.parse_args(argv)

    results, failed = [], 0
    for path in args.files:
        try:
            results.append(check_file(path, args.min_body, args.min_label))
        except FileNotFoundError as exc:
            print(f"错误：{exc}", file=sys.stderr)
            failed = 2
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for result in results:
            print(render_report(result))
            print()
    if failed:
        return failed
    return 1 if any(result["hard"] for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
