#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_trending.py — 抓取 GitHub Trending 总榜 + 语言分榜，解析、去重、合并为 trending.json

只依赖 Python 3 标准库（urllib / re / json / html），无需 requests / bs4 / 浏览器。

用法:
    python3 fetch_trending.py --out trending.json
    python3 fetch_trending.py --since weekly --langs python,rust --out weekly.json
    python3 fetch_trending.py --spoken-language zh --out cn.json

输出 JSON 结构:
{
  "fetched_at": "2026-07-31T13:16:29+08:00",
  "since": "daily",
  "sources": ["总榜", "python", "rust", ...],
  "count": 159,
  "items": [
    {"repo":"owner/name","desc":"...","lang":"Python","stars":9169,
     "forks":628,"today":1657,"rank":1,"src":"总榜 #1","url":"https://github.com/owner/name"},
    ...
  ]
}
"""
import argparse
import datetime as _dt
import html as _html
import json
import re
import sys
import time
import urllib.error
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

DEFAULT_LANGS = ["python", "typescript", "javascript", "go",
                 "rust", "c++", "java", "jupyter-notebook"]

# GitHub Trending 页面结构（2026-07 校验有效）。若解析为 0 条，见 references/troubleshooting.md
RE_ARTICLE = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
RE_REPO = re.compile(r'<h2 class="h3 lh-condensed">.*?href="/([^"]+)"', re.S)
RE_DESC = re.compile(r'<p class="col-9 color-fg-muted my-1[^"]*">(.*?)</p>', re.S)
RE_LANG = re.compile(r'<span itemprop="programmingLanguage">([^<]+)</span>')
RE_STARS = re.compile(r'/stargazers"[^>]*>.*?</svg>\s*([\d,]+)', re.S)
RE_FORKS = re.compile(r'/forks"[^>]*>.*?</svg>\s*([\d,]+)', re.S)
RE_TODAY = re.compile(r'([\d,]+)\s*stars\s+(?:today|this week|this month)')
RE_TAG = re.compile(r'<[^>]+>')


def to_int(s):
    try:
        return int(str(s).replace(",", "").strip() or 0)
    except ValueError:
        return 0


def fetch(url, retries=3, timeout=30):
    """GET 一个 URL，返回 HTML 文本；失败重试。"""
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=timeout) as r:  # nosec B310 - callers only pass github.com URLs built here
                return r.read().decode("utf-8", "replace")
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            sys.stderr.write("  retry %d/%d %s -> %s\n" % (i + 1, retries, url, e))
            time.sleep(1.5 * (i + 1))
    sys.stderr.write("  FAILED %s: %s\n" % (url, last))
    return ""


def parse(page_html):
    """从 Trending 页面 HTML 解析出仓库条目列表。"""
    out = []
    for a in RE_ARTICLE.findall(page_html):
        m = RE_REPO.search(a)
        if not m:
            continue
        repo = m.group(1).strip()
        d = RE_DESC.search(a)
        desc = _html.unescape(RE_TAG.sub("", d.group(1))).strip() if d else ""
        desc = re.sub(r"\s+", " ", desc)
        lang = RE_LANG.search(a)
        st, fk, td = RE_STARS.search(a), RE_FORKS.search(a), RE_TODAY.search(a)
        out.append({
            "repo": repo,
            "desc": desc,
            "lang": lang.group(1).strip() if lang else "Other",
            "stars": to_int(st.group(1)) if st else 0,
            "forks": to_int(fk.group(1)) if fk else 0,
            "today": to_int(td.group(1)) if td else 0,
            "url": "https://github.com/" + repo,
        })
    return out


def build_url(lang, since, spoken):
    base = "https://github.com/trending"
    if lang:
        base += "/" + urllib.request.quote(lang)
    qs = ["since=" + since]
    if spoken:
        qs.append("spoken_language_code=" + spoken)
    return base + "?" + "&".join(qs)


def main():
    ap = argparse.ArgumentParser(description="Fetch & parse GitHub Trending")
    ap.add_argument("--out", default="trending.json")
    ap.add_argument("--since", default="daily", choices=["daily", "weekly", "monthly"])
    ap.add_argument("--langs", default=",".join(DEFAULT_LANGS),
                    help="逗号分隔的语言分榜；传 '' 表示只抓总榜")
    ap.add_argument("--spoken-language", default="", help="如 zh / en，可选")
    ap.add_argument("--sleep", type=float, default=0.8, help="请求间隔秒")
    args = ap.parse_args()

    langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    seen, sources = {}, []

    # 1) 总榜（保留名次，作为权重最高的来源）
    sys.stderr.write("[1/%d] 总榜 ...\n" % (len(langs) + 1))
    main_items = parse(fetch(build_url(None, args.since, args.spoken_language)))
    for i, x in enumerate(main_items, 1):
        x["rank"] = i
        x["src"] = "总榜 #%d" % i
        seen[x["repo"]] = x
    sources.append("总榜")
    sys.stderr.write("      -> %d 条\n" % len(main_items))

    # 2) 语言分榜（仅补充总榜没有的仓库）
    for n, lg in enumerate(langs, 2):
        time.sleep(args.sleep)
        sys.stderr.write("[%d/%d] %s ...\n" % (n, len(langs) + 1, lg))
        got = parse(fetch(build_url(lg, args.since, args.spoken_language)))
        added = 0
        for x in got:
            if x["repo"] not in seen:
                x["rank"] = 999
                x["src"] = lg
                seen[x["repo"]] = x
                added += 1
        sources.append(lg)
        sys.stderr.write("      -> %d 条，新增 %d\n" % (len(got), added))

    items = sorted(seen.values(), key=lambda x: (-x["today"], x["rank"]))
    tz = _dt.timezone(_dt.timedelta(hours=8))
    payload = {
        "fetched_at": _dt.datetime.now(tz).replace(microsecond=0).isoformat(),
        "since": args.since,
        "sources": sources,
        "count": len(items),
        "items": items,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)

    sys.stderr.write("\n=== 去重后 %d 个仓库 -> %s ===\n" % (len(items), args.out))
    if not items:
        sys.stderr.write("!! 解析到 0 条，GitHub 可能改版，请查 references/troubleshooting.md\n")
        return 1
    for x in items[:40]:
        sys.stderr.write("%-46s %-16s *%-8d +%-6d %s\n" % (
            x["repo"][:46], x["lang"][:16], x["stars"], x["today"], x["desc"][:70]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
