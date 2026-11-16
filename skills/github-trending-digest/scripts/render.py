#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — 把 curated.json 注入 assets/template.html，产出单文件 HTML 星图晨报

只依赖 Python 3 标准库。模板自带全部 CSS/JS，输出零外部资源。

用法:
    python3 render.py --curated curated.json --out github-trending-daily.html
    python3 render.py --curated curated.json --out out.html --template /path/to/template.html

curated.json 结构（由 agent 依据 references/curation.md 编写）:
{
  "captured_at": "2026-07-31T13:16:29+08:00",     # ISO8601，带 +08:00
  "title":    "GitHub 每日趋势晨报",                # <title> 与 hero 标题基底
  "headline": "GitHub <em>每日趋势</em>晨报",        # hero h1，<em> 内文字带渐变
  "kicker":   "GitHub Trending · Daily Digest",
  "scope":    "今日新增 Star（daily）",
  "source_html": "<a href=\"...\" target=\"_blank\" rel=\"noopener noreferrer\">...</a>",
  "footer_note": "按 A / B / C 五个固定版块分组，序号全局连续编号。",
  "sections": [
    {"id":"models","name":"模型与多模态","icon":"01",
     "color":"var(--s1)","bg":"var(--s1b)","desc":"一句话版块说明"}
  ],
  "items": [
    {"s":"models","repo":"owner/name","lang":"Python",
     "stars":9169,"today":1657,"forks":628,"src":"总榜 #1","sum":"≤60 字中文摘要"}
  ]
}

sections 的 color/bg 从模板内置的 5 组配色里取: s1/s1b(紫) s2/s2b(蓝) s3/s3b(橙) s4/s4b(绿) s5/s5b(黄)
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TPL = os.path.join(HERE, "..", "assets", "template.html")

REQ_TOP = ["captured_at", "sections", "items"]
REQ_SEC = ["id", "name", "icon", "color", "bg", "desc"]
REQ_ITEM = ["s", "repo", "lang", "stars", "today", "forks", "src", "sum"]

PALETTE = [("var(--s1)", "var(--s1b)"), ("var(--s2)", "var(--s2b)"),
           ("var(--s3)", "var(--s3b)"), ("var(--s4)", "var(--s4b)"),
           ("var(--s5)", "var(--s5b)")]


def die(msg):
    sys.stderr.write("ERROR: %s\n" % msg)
    sys.exit(1)


def validate(c):
    errs = []
    for k in REQ_TOP:
        if k not in c:
            errs.append("缺少顶层字段: %s" % k)
    if errs:
        die("; ".join(errs))

    ids = []
    for i, s in enumerate(c["sections"]):
        # 缺省配色按顺序自动补齐
        s.setdefault("icon", "%02d" % (i + 1))
        if "color" not in s or "bg" not in s:
            col, bg = PALETTE[i % len(PALETTE)]
            s.setdefault("color", col)
            s.setdefault("bg", bg)
        s.setdefault("desc", "")
        for k in REQ_SEC:
            if k not in s:
                errs.append("sections[%d] 缺少 %s" % (i, k))
        ids.append(s.get("id"))

    for i, it in enumerate(c["items"]):
        for k in REQ_ITEM:
            if k not in it:
                errs.append("items[%d] (%s) 缺少 %s" % (i, it.get("repo", "?"), k))
        if it.get("s") not in ids:
            errs.append("items[%d] (%s) 的版块 s=%r 不在 sections 里"
                        % (i, it.get("repo", "?"), it.get("s")))
        n = len(it.get("sum", ""))
        if n > 60:
            errs.append("items[%d] (%s) 摘要 %d 字 > 60" % (i, it.get("repo", "?"), n))
        if "/" not in str(it.get("repo", "")):
            errs.append("items[%d] repo 必须是 owner/name 格式" % i)
        for k in ("stars", "today", "forks"):
            if not isinstance(it.get(k), int):
                errs.append("items[%d] (%s) %s 必须是整数" % (i, it.get("repo", "?"), k))
    if errs:
        die("curated.json 校验失败:\n  - " + "\n  - ".join(errs))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--curated", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--template", default=DEFAULT_TPL)
    args = ap.parse_args()

    if not os.path.exists(args.template):
        die("模板不存在: %s" % args.template)
    with open(args.curated, encoding="utf-8") as f:
        c = json.load(f)
    validate(c)

    title = c.get("title", "GitHub 每日趋势晨报")
    day = c["captured_at"][:10]
    repl = {
        "TITLE": "%s · %s" % (title, day),
        "DOC_TITLE_PREFIX": title,
        "HEADLINE": c.get("headline", title),
        "KICKER": c.get("kicker", "GitHub Trending · Daily Digest"),
        "SCOPE": c.get("scope", "今日新增 Star（daily）"),
        "FOOTER_NOTE": c.get("footer_note", "序号全局连续编号。"),
        "SOURCE_HTML": c.get(
            "source_html",
            '<a href="https://github.com/trending?since=daily" target="_blank" '
            'rel="noopener noreferrer">github.com/trending（daily）</a>'),
        "CAPTURED_AT": c["captured_at"],
        "SECTIONS": json.dumps(c["sections"], ensure_ascii=False, indent=0).replace("\n", ""),
        "DATA": json.dumps(c["items"], ensure_ascii=False, indent=0).replace("\n", ""),
    }

    with open(args.template, encoding="utf-8") as f:
        tpl = f.read()
    for k, v in repl.items():
        tpl = tpl.replace("{{%s}}" % k, v)

    left = [k for k in repl if "{{%s}}" % k in tpl]
    if left:
        die("占位符未替换干净: %s" % left)

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(tpl)

    per = {}
    for it in c["items"]:
        per[it["s"]] = per.get(it["s"], 0) + 1
    print("OK -> %s (%d bytes)" % (args.out, len(tpl.encode("utf-8"))))
    print("   条目 %d，版块 %d" % (len(c["items"]), len(c["sections"])))
    for s in c["sections"]:
        print("   - %-22s %d 条" % (s["name"], per.get(s["id"], 0)))


if __name__ == "__main__":
    main()
