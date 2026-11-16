# 排障手册

按"抓取 → 编排 → 渲染 → 自检"四个阶段排列。这些坑都是实战踩出来的。

---

## 阶段 1 · 抓取

### 解析到 0 条

GitHub 改版了页面结构。`fetch_trending.py` 顶部集中定义了全部正则，改那里即可：

```python
RE_ARTICLE = re.compile(r'<article class="Box-row">(.*?)</article>', re.S)
RE_REPO    = re.compile(r'<h2 class="h3 lh-condensed">.*?href="/([^"]+)"', re.S)
RE_DESC    = re.compile(r'<p class="col-9 color-fg-muted my-1[^"]*">(.*?)</p>', re.S)
...
```

诊断步骤：

```bash
curl -s -A "Mozilla/5.0" "https://github.com/trending?since=daily" -o /tmp/t.html
grep -c 'Box-row' /tmp/t.html          # 条目容器还在不在
python3 -c "
import re;s=open('/tmp/t.html',encoding='utf-8').read()
a=re.findall(r'<article class=\"Box-row\">(.*?)</article>',s,re.S)
print('articles:',len(a)); print(a[0][:2000] if a else s[:2000])"
```

拿到单条原始 HTML 后，对着实际结构改正则。**修完记得同步更新本文件顶部的"最近校验日期"。**

最近校验：2026-07-31，正则全部有效。

### 描述字段抓不到（`desc` 全空）

描述所在的 `<p>` class 是浮动的，历史上出现过 `col-9 color-fg-muted my-1 pr-4` 和 `col-9 color-fg-muted my-1`。
所以正则用了宽松匹配 `my-1[^"]*`。如果又变了，放宽到：

```python
RE_DESC = re.compile(r'<p class="[^"]*color-fg-muted[^"]*">(.*?)</p>', re.S)
```

### Star / Fork 数抓错或抓反

两个数字都在 `<a href=".../stargazers">` 和 `<a href=".../forks">` 里，中间隔着一个 `<svg>`。
**不要用"按出现顺序取第 1、第 2 个数字"的写法** —— 页面上还有 "N stars today" 和贡献者头像干扰，顺序不可靠。
必须像现在这样按 `href` 锚定：

```python
RE_STARS = re.compile(r'/stargazers"[^>]*>.*?</svg>\s*([\d,]+)', re.S)
RE_FORKS = re.compile(r'/forks"[^>]*>.*?</svg>\s*([\d,]+)', re.S)
```

注意数字带千分位逗号，必须走 `to_int()` 清洗。

### 请求超时 / 429 / 连接被拒

- 脚本已内置 3 次重试 + 递增退避，先让它自己重试完
- 分榜之间默认 sleep 0.8s，抓太快会被限流；网络差就 `--sleep 2`
- 必须带 User-Agent，GitHub 对空 UA 有更严的限流
- 沙箱环境里 `urllib` 被拦时，改用 `curl` 落盘再解析：
  ```bash
  curl -s -L -A "Mozilla/5.0" "https://github.com/trending?since=daily" -o /tmp/t.html
  ```
  然后写个几行脚本调用 `fetch_trending.py` 里的 `parse()` 处理本地文件。

### 语言分榜 URL 编码

`c++` 在 URL 里必须编码成 `c%2B%2B`，脚本已用 `urllib.request.quote` 处理。
`jupyter-notebook`、`objective-c` 这类用短横线连接，不是空格。语言 slug 全小写。

---

## 阶段 2 · 编排

### 摘要老是超 60 字

先写完整表达，再删。优先砍这些：

- "的"字：可去掉一半以上
- 括号补充说明
- "支持……"改成直接列举
- "一个""这是"等冗余开头
- 形容词："强大的""优秀的""完善的"

用这条命令批量找超长项：

```bash
python3 -c "
import json;d=json.load(open('curated.json',encoding='utf-8'))
for x in d['items']:
    n=len(x['sum'])
    if n>60: print(n, x['repo'], x['sum'])"
```

### JSON 写坏了

中文内容里的引号、`footer_note` 里的 HTML 标签属性引号，都要转义。
**建议用脚本生成 `curated.json` 而不是手写**：把数据整理成 Python 元组列表，`json.dump(..., ensure_ascii=False)` 输出，天然不会有转义问题。这也是原始实现采用的做法。

---

## 阶段 3 · 渲染

### `render.py` 报"占位符未替换干净"

模板里出现了 `curated.json` 没提供的占位符。当前模板共 10 个：

```
TITLE  DOC_TITLE_PREFIX  HEADLINE  KICKER  SCOPE
FOOTER_NOTE  SOURCE_HTML  CAPTURED_AT  SECTIONS  DATA
```

`render.py` 对除 `captured_at` / `sections` / `items` 外的字段都有默认值，所以正常不会触发。
如果你改过 `assets/template.html` 新增了占位符，记得在 `render.py` 的 `repl` 字典里补上。

### 页面白屏 / 卡片不出来

内嵌 JS 抛异常了。打开浏览器控制台看第一条报错，或者：

```bash
python3 -c "
import re;s=open('out.html',encoding='utf-8').read()
open('/tmp/_c.js','w',encoding='utf-8').write(re.search(r'<script>(.*)</script>',s,re.S).group(1))"
node --check /tmp/_c.js
```

### `const top` 冲突（重要）

**顶层 `const top = document.getElementById("toTop")` 会与 `window.top` 冲突**，在部分浏览器直接抛
`Uncaught SyntaxError: Identifier 'top' has already been declared`，整个脚本罢工、页面白屏。

模板已改名为 `btnTop`。自己改模板时，避开这些顶层保留名：
`top` `self` `parent` `name` `status` `length` `location` `origin` `history` `closed` `frames`。

`verify.py` 会专门检查这一项。

### 编号不连续 / 版块内重新计数

编号逻辑在模板 JS 里：

```javascript
let seq = 0;
groups.forEach(g => g.items.forEach(it => { it.no = ++seq; }));
```

`groups` 严格按 `SECTIONS` 顺序，版块内按 `today` 降序。
不要在 `curated.json` 里手写 `no` 字段 —— 会被渲染时覆盖。

---

## 阶段 4 · 自检

### "可见文本无 ISO 时间串" 失败

页面上直接打印了 `captured_at` 原值。时间必须全部走模板里的 `bj()` 函数：

```javascript
new Intl.DateTimeFormat("zh-CN", { timeZone: "Asia/Shanghai", ... })
```

ISO 串只允许作为 `const CAPTURED_AT` 常量存在于 `<script>` 内（`verify.py` 会剥离 script 后再检查）。

### "零外部资源引用" 失败

有 `<script src>` / `<link href>` / `<img src>` 指向了 http(s) 或 `//`。
图标一律用内联 SVG，字体只用系统字体栈：

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
             "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
```

注意 `<a href="https://...">` 是正常外链，不算外部资源，`verify.py` 的正则已排除 `a` 标签。

### "外链均带 _blank + noopener noreferrer" 失败

模板里所有 `<a href="http...">` 都必须三件套齐全。卡片链接是 JS 模板字符串拼的，容易漏，检查这两处：
`.ttl a` 标题链接和 `.go` 查看仓库按钮。

### node 找不到

`verify.py` 会依次尝试 `node` 和 WorkBuddy 的托管 node 路径，都没有就把该项标为 WARN 跳过，不影响退出码。
JS 语法检查是可选项，缺了不阻塞交付，但建议至少在浏览器里打开一次确认渲染正常。

---

## 通用建议

- **原始数据留档**。`trending.json` 别删，改筛选规则时可以直接重跑阶段 2、3，不用重新抓。
- **改模板前先备份**。`assets/template.html` 是整个 skill 的核心资产，改坏了用 `assets/curated.example.json` 跑一遍 `render.py` + `verify.py` 就能验证是否还完好。
- **端到端冒烟测试**（不联网，10 秒）：
  ```bash
  python3 scripts/render.py --curated assets/curated.example.json --out /tmp/_smoke.html \
    && python3 scripts/verify.py /tmp/_smoke.html
  ```
  预期：渲染 53 条 / 5 版块，自检 22 项全过。
