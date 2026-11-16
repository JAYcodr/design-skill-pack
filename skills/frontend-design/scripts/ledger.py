#!/usr/bin/env python3
"""外观账本：记录每次交付的视觉指纹，开工前查重。

只记事实（底色 / 主色板 / 字体 / 骨架计数），不打分、不判断好坏。
存储：$HOME/.frontend-design/ledger.jsonl（FRONTEND_DESIGN_HOME 可改），只在本机。

用法：
    python3 scripts/ledger.py recent [--n 8]
    python3 scripts/ledger.py add <file.html> --project <名字> [--note "..."]
    python3 scripts/ledger.py check <file.html>
"""

import argparse
import datetime
import json
import os
import re
import sys
from pathlib import Path

HEX_RE = re.compile(r"#([0-9a-fA-F]{3,8})\b")
GENERIC_FONTS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
    "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "-apple-system",
    "blinkmacsystemfont", "inherit", "initial", "unset", "revert", "emoji",
}


def home_dir():
    env = os.environ.get("FRONTEND_DESIGN_HOME")
    return Path(env).expanduser() if env else Path.home() / ".frontend-design"


def ledger_path():
    return home_dir() / "ledger.jsonl"


def norm_hex(value):
    """#abc / #aabbcc / #aabbccdd → #aabbcc；非法返回 None。"""
    h = value.lower().lstrip("#")
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h[:3])
    elif len(h) in (6, 8):
        h = h[:6]
    if len(h) != 6 or not re.fullmatch(r"[0-9a-f]{6}", h):
        return None
    return "#" + h


def rgb(value):
    h = value.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def is_grayish(value):
    r, g, b = rgb(value)
    return max(r, g, b) - min(r, g, b) <= 12


def is_near_white(value):
    return min(rgb(value)) >= 235


def is_near_black(value):
    return max(rgb(value)) <= 24


def bg_class(value):
    """底色归成 浅暖 / 浅冷 / 中 / 中深 / 深，用于跨项目比较。"""
    r, g, b = rgb(value)
    light = (max(r, g, b) + min(r, g, b)) / 2 / 255
    warm = (r - b) >= 8
    if light >= 0.90:
        return "浅暖" if warm else "浅冷"
    if light >= 0.70:
        return "暖中" if warm else "中"
    if light >= 0.35:
        return "中深"
    return "深"


def extract_bg(html):
    """返回 (底色, 置信度)。优先 body 规则，其次任意 background 声明。"""
    m = re.search(r"body\s*(?:,[^{]*)?\{([^}]*)\}", html, re.S | re.I)
    if m:
        bm = re.search(r"background(?:-color)?\s*:\s*([^;}]+)", m.group(1), re.I)
        if bm:
            hm = HEX_RE.search(bm.group(1))
            if hm:
                return norm_hex(hm.group(1)), "高"
    for m in re.finditer(r"background(?:-color)?\s*:\s*([^;}]+)", html, re.I):
        hm = HEX_RE.search(m.group(1))
        if hm:
            return norm_hex(hm.group(1)), "中"
    return None, "无"


def extract_palette(html, limit=3):
    counts = {}
    for m in HEX_RE.finditer(html):
        h = norm_hex(m.group(1))
        if h:
            counts[h] = counts.get(h, 0) + 1
    vivid = [(h, c) for h, c in counts.items()
             if not is_near_white(h) and not is_near_black(h) and not is_grayish(h)]
    vivid.sort(key=lambda item: (-item[1], item[0]))
    return [h for h, _ in vivid[:limit]]


def extract_fonts(html, limit=4):
    # 先解析 CSS 变量里的字体定义：--serif: "Noto Serif SC", serif;
    var_map = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;}]+)", html):
        for part in m.group(2).split(","):
            name = part.strip().strip("'\"").strip()
            if name and name.lower() not in GENERIC_FONTS and not name.startswith("var("):
                var_map[m.group(1)] = name
                break
    counts = {}
    for m in re.finditer(r"font-family\s*:\s*([^;}]+)", html, re.I):
        names = []
        for part in m.group(1).split(","):
            name = part.strip().strip("'\"").strip()
            var_match = re.fullmatch(r"var\(\s*(--[\w-]+)\s*\)", name)
            if var_match:
                resolved = var_map.get(var_match.group(1))
                if resolved:
                    names.append(resolved)
                continue
            if name and name.lower() not in GENERIC_FONTS:
                names.append(name)
        for name in names:
            counts[name] = counts.get(name, 0) + 1
    fonts = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [name for name, _ in fonts[:limit]]


def extract_layout(html):
    return {
        "sections": len(re.findall(r"<section\b", html, re.I)) + len(re.findall(r"<main\b", html, re.I)),
        "grid": len(re.findall(r"display\s*:\s*grid", html, re.I)),
        "flex": len(re.findall(r"display\s*:\s*flex", html, re.I)),
        "radius": len(re.findall(r"border-radius\s*:", html, re.I)),
        "absolute": len(re.findall(r"position\s*:\s*absolute", html, re.I)),
        "fullbleed": len(re.findall(r"100vw|100vh", html, re.I)),
    }


def fingerprint(path):
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"找不到文件：{path}")
    html = p.read_text(encoding="utf-8", errors="replace")
    bg, bg_conf = extract_bg(html)
    palette = extract_palette(html)
    fonts = extract_fonts(html)
    layout = extract_layout(html)
    confidence = "高" if (bg and bg_conf == "高" and fonts) else ("中" if (bg or palette or fonts) else "低")
    return {
        "file": p.name,
        "size": len(html.encode("utf-8")),
        "lines": html.count("\n") + 1,
        "bg": bg,
        "bg_conf": bg_conf,
        "bg_class": bg_class(bg) if bg else None,
        "palette": palette,
        "fonts": fonts,
        "display_font": fonts[0] if fonts else None,
        "layout": layout,
        "confidence": confidence,
    }


def load_rows(path):
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def fingerprint_similarity(a, b):
    """返回 (维度, 说明) 列表；只比事实，不做评分。"""
    out = []
    if a.get("bg") and a.get("bg") == b.get("bg"):
        out.append(("同底色", a["bg"]))
    elif a.get("bg_class") and a.get("bg_class") == b.get("bg_class"):
        out.append(("同底色族", a["bg_class"]))
    pa, pb = set(a.get("palette") or []), set(b.get("palette") or [])
    if pa and pb:
        overlap = len(pa & pb) / max(1, min(len(pa), len(pb)))
        if overlap >= 0.5:
            out.append(("色板重合", f"{overlap:.0%}"))
    fa, fb = set(a.get("fonts") or []), set(b.get("fonts") or [])
    if fa and fb:
        overlap = len(fa & fb) / max(1, min(len(fa), len(fb)))
        if overlap >= 0.5:
            out.append(("字体重合", f"{overlap:.0%}"))
    la, lb = a.get("layout") or {}, b.get("layout") or {}
    if la.get("sections", 0) > 0 and abs(la.get("sections", 0) - lb.get("sections", 0)) <= 1:
        rounded_a = la.get("radius", 0) > la.get("sections", 0)
        rounded_b = lb.get("radius", 0) > lb.get("sections", 0)
        if rounded_a == rounded_b:
            out.append(("骨架相近", f"section {la.get('sections', 0)} vs {lb.get('sections', 0)}"))
    return out


def cmd_recent(args):
    rows = load_rows(ledger_path())
    if not rows:
        print("账本为空。这是第一次交付，开工前不用避让；交付后记得 add 一笔。")
        return 0
    for row in rows[-args.n:]:
        layout = row.get("layout") or {}
        palette = ",".join(row.get("palette") or []) or "-"
        print(
            f"{row.get('ts', '')[:10]}  {row.get('project', '?'):<14}  "
            f"{row.get('bg') or '?'} ({row.get('bg_class') or '?'})  "
            f"色板 {palette}  字体 {row.get('display_font') or '-'}  "
            f"骨架 sec{layout.get('sections', 0)}/grid{layout.get('grid', 0)}"
        )
    classes = {}
    for row in rows[-args.n:]:
        key = row.get("bg_class")
        if key:
            classes[key] = classes.get(key, 0) + 1
    repeats = [f"{key}×{count}" for key, count in classes.items() if count >= 2]
    if repeats:
        print("反复出现：" + "、".join(repeats) + "（这次要不要换？）")
    return 0


def cmd_add(args):
    fp = fingerprint(args.file)
    record = {
        "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "project": args.project or Path(args.file).resolve().parent.name,
        "note": args.note or "",
        "path": str(Path(args.file).resolve()),
        **fp,
    }
    path = ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"已记账：{record['project']} · 底色 {record['bg'] or '?'} · "
          f"色板 {','.join(record['palette']) or '-'} · 字体 {record['display_font'] or '-'}")
    if record["confidence"] != "高":
        print(f"（置信度 {record['confidence']}：静态提取没读全，以截图为准）")
    print(f"账本：{path}")
    return 0


def cmd_check(args):
    rows = load_rows(ledger_path())[-8:]
    candidate = fingerprint(args.file)
    if not rows:
        print("账本为空，无法比较。第一次交付不用避让。")
        return 0
    hits = []
    for row in rows:
        sims = fingerprint_similarity(candidate, row)
        if sims:
            hits.append((row, sims))
    if not hits:
        print("和最近 8 次交付没有明显撞车。仍然要问自己：这是概念推导的结果，还是舒适区？")
        return 0
    print(f"和最近 {len(hits)} 次交付有重合（提示，不是禁令）：")
    for row, sims in hits:
        desc = "、".join(f"{key}({value})" for key, value in sims)
        print(f"  {row.get('ts', '')[:10]}  {row.get('project', '?'):<14}  {desc}")
    print("处理方式：换一个决策点重做，或写一句「为什么这次必须重复」——重复是信息，不是罪。")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="外观账本：记录并检查交付的视觉指纹")
    subs = parser.add_subparsers(dest="command", required=True)

    recent = subs.add_parser("recent", help="看最近的交付的样子")
    recent.add_argument("--n", type=int, default=8)
    recent.set_defaults(func=cmd_recent)

    add = subs.add_parser("add", help="记一笔交付")
    add.add_argument("file")
    add.add_argument("--project", default=None)
    add.add_argument("--note", default="")
    add.set_defaults(func=cmd_add)

    check = subs.add_parser("check", help="和最近记录比对是否撞车")
    check.add_argument("file")
    check.set_defaults(func=cmd_check)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
