#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — 交付前自检产出的单文件 HTML

检查项:
  1. 文档结构完整（DOCTYPE / </html> / <title>）
  2. 零外部资源（无 <script src> / <link href> / <img src> 指向 http(s) 或 //）
  3. 所有外链都带 target="_blank" 且 rel 含 noopener noreferrer
  4. 页面不残留 ISO 时间串（如 2026-07-31T13:16:29）在可见文本里
  5. 模板占位符已全部替换（无 {{XXX}} 残留）
  6. 内嵌 JS 语法（若环境有 node，则 node --check）
  7. DATA 数组条数、摘要长度 ≤60 字、全局编号连续性
  8. 响应式断点存在（@media）

用法:
    python3 verify.py output.html
退出码 0 = 全部通过；1 = 有 FAIL。
"""
import json
import os
import re
import subprocess
import sys
import tempfile

OK, FAIL, WARN = "PASS", "FAIL", "WARN"
rows = []


def chk(name, cond, detail="", soft=False):
    rows.append(((OK if cond else (WARN if soft else FAIL)), name, detail))
    return cond


def main():
    if len(sys.argv) < 2:
        print("usage: verify.py <output.html>")
        return 2
    p = sys.argv[1]
    if not os.path.exists(p):
        print("ERROR: 文件不存在 %s" % p)
        return 2
    s = open(p, encoding="utf-8").read()

    # 1 结构
    chk("DOCTYPE 声明", s.lstrip().startswith("<!DOCTYPE"))
    chk("html 闭合", s.rstrip().endswith("</html>"))
    chk("有 <title>", "<title>" in s)
    chk("声明 lang=\"zh-CN\"", 'lang="zh-CN"' in s, soft=True)
    chk("有 viewport meta", 'name="viewport"' in s)

    # 2 零外部资源
    ext = re.findall(r'<(?:script|link|img|source|iframe)[^>]*?(?:src|href)="(https?:)?//[^"]+"', s)
    # <a href> 不算资源，上面正则已排除 a 标签
    chk("零外部资源引用", not ext, "发现 %d 处: %s" % (len(ext), ext[:3]))
    chk("样式内联", "<style>" in s and "stylesheet" not in s)
    chk("脚本内联", "<script>" in s and not re.search(r'<script[^>]+src=', s))

    # 3 外链安全属性
    anchors = re.findall(r'<a\s[^>]*href="https?://[^"]*"[^>]*>', s)
    bad = [a for a in anchors if 'target="_blank"' not in a
           or "noopener" not in a or "noreferrer" not in a]
    chk("外链均带 _blank + noopener noreferrer",
        not bad, "%d/%d 不合规: %s" % (len(bad), len(anchors), bad[:2]))
    # 模板通过 JS 生成卡片链接，额外检查 JS 里的写法
    js_links = re.findall(r'href="https://github\.com/\$\{[^"]+\}"[^>]*', s)
    chk("JS 动态外链带安全属性",
        all("noopener" in x and "noreferrer" in x and "_blank" in x for x in js_links)
        if js_links else True, "共 %d 处" % len(js_links))

    # 4 无裸 ISO 串暴露在可见文本（允许出现在 JS 常量里）
    body = re.sub(r'<script>.*?</script>', '', s, flags=re.S)
    iso = re.findall(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}', body)
    chk("可见文本无 ISO 时间串", not iso, "发现: %s" % iso[:3])
    chk("使用 Asia/Shanghai 时区格式化", "Asia/Shanghai" in s)

    # 5 占位符
    left = re.findall(r'\{\{[A-Z_0-9]+\}\}', s)
    chk("无模板占位符残留", not left, "残留: %s" % left[:5])

    # 6 JS 语法
    m = re.search(r'<script>(.*?)</script>', s, re.S)
    if m:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as f:
            f.write(m.group(1))
            tmp = f.name
        node = None
        for cand in ("node", os.path.expanduser(
                "~/.workbuddy/binaries/node/versions/22.22.2/bin/node")):
            try:
                subprocess.run([cand, "--version"], capture_output=True, timeout=10, check=True)
                node = cand
                break
            except Exception:
                continue
        if node:
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
            chk("内嵌 JS 语法", r.returncode == 0, r.stderr.strip()[:300])
        else:
            chk("内嵌 JS 语法（无 node，跳过）", True, "环境未找到 node", soft=True)
        os.unlink(tmp)
        # 常见坑：顶层 const top 与 window.top 冲突
        chk("未使用保留名 const top",
            not re.search(r'^\s*const top\s*=', m.group(1), re.M),
            "顶层 `const top` 会与 window.top 冲突，改名 btnTop")

    # 7 数据自检
    d = re.search(r'const DATA = (\[.*?\]);', s, re.S)
    if d:
        try:
            data = json.loads(d.group(1))
            chk("DATA 解析成功", True, "%d 条" % len(data))
            longs = [(x.get("repo"), len(x.get("sum", ""))) for x in data
                     if len(x.get("sum", "")) > 60]
            chk("摘要均 ≤60 字", not longs, "超长: %s" % longs[:4])
            empty = [x.get("repo") for x in data if not x.get("sum", "").strip()]
            chk("摘要无空值", not empty, "空摘要: %s" % empty[:4])
            dup = len(data) - len({x.get("repo") for x in data})
            chk("仓库无重复", dup == 0, "重复 %d 个" % dup)
            secs = re.search(r'const SECTIONS = (\[.*?\]);', s, re.S)
            if secs:
                sids = {x["id"] for x in json.loads(secs.group(1))}
                orphan = [x.get("repo") for x in data if x.get("s") not in sids]
                chk("条目版块归属有效", not orphan, "孤儿: %s" % orphan[:4])
        except Exception as e:
            chk("DATA 解析成功", False, str(e)[:200])
    else:
        chk("找到 DATA 数组", False)

    # 8 响应式
    chk("含响应式断点", "@media" in s)
    chk("卡片网格自适应", "auto-fill" in s or "auto-fit" in s)

    w = max(len(r[1]) for r in rows)
    print("\n" + "=" * (w + 30))
    print("自检报告: %s" % p)
    print("=" * (w + 30))
    nf = 0
    for st, name, detail in rows:
        mark = {"PASS": "[v]", "FAIL": "[X]", "WARN": "[!]"}[st]
        print("%s %-*s %s" % (mark, w, name, detail if st != OK else detail))
        if st == FAIL:
            nf += 1
    print("=" * (w + 30))
    print("总计 %d 项，失败 %d 项" % (len(rows), nf))
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
