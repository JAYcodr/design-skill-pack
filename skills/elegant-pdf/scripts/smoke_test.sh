#!/bin/bash
# elegant-pdf smoke test — render all styles and validate output
# Usage: bash scripts/smoke_test.sh [input.md]
# Default input: test/fixtures/sample.md

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
INPUT="${1:-${SKILL_DIR}/test/fixtures/sample.md}"
OUTPUT_DIR="/tmp/elegant-pdf-smoke-$$"
TOTAL=0
PASS=0
FAIL=0

mkdir -p "$OUTPUT_DIR"

# Styles to test
STYLES=(
  "weasyprint:warm-academic"
  "weasyprint:swiss"
  "weasyprint:japanese"
  "weasyprint:cyberpunk"
  "weasyprint:art-nouveau"
  "weasyprint:bauhaus"
  "weasyprint:ink-wash"
  "weasyprint:minimalism"
  "weasyprint:typewriter"
  "weasyprint:scholar"
  "reportlab:warm-academic"
  "reportlab:nord-frost"
  "reportlab:github-light"
)

echo "=========================================="
echo "  elegant-pdf smoke test"
echo "  Input: $INPUT"
echo "  Output: $OUTPUT_DIR"
echo "=========================================="

# Check input
if [ ! -f "$INPUT" ]; then
  echo "❌ Input not found: $INPUT"
  echo ""
  echo "Creating default sample..."
  mkdir -p "$(dirname "$INPUT")"
  cat > "$INPUT" << 'EOF'
---
title: Smoke Test Sample
author: elegant-pdf
date: 2026-07-10
lang: zh-CN
---

# 一、中文渲染测试

这是中文字体渲染测试段落。技术巫魅化世界观设定集 · 余烬大陆 · 沉默圣典。
编译、纠缠、太虚能、源核、织机、原纹、调律者、祭司、术士。

## 1.1 带数字和符号

版本 v0.3 | 协议 v2.1.0 | 温度 -273.15°C
熵增定律 ΔS ≥ 0 | E = mc² | 纠缠态 Ψ(1,2)

### 1.1.1 深嵌套小标题

测试深层级 heading 渲染、目录跨页、widow/orphan 控制。

| 左列 | 中列 | 右列 |
|------|------|------|
| 编译保真度 | 血脉纯度 | v0.3 新增 |
| 纠缠网络 | 织机 | 行星级 |
| 真空涨落 | 太虚能 | 零点能 |

```python
# 代码块测试
def hello():
    print("你好，世界！")
```

> 引用块：沉默之神不回应祈祷，因为它不能。
EOF
fi

# Get sample page count from warm-academic for reference
echo ""
echo "--- Rendering all styles ---"

for entry in "${STYLES[@]}"; do
  ENGINE="${entry%%:*}"
  STYLE="${entry##*:}"
  TOTAL=$((TOTAL + 1))

  OUTFILE="${OUTPUT_DIR}/smoke-${ENGINE}-${STYLE}.pdf"
  echo -n "  [$ENGINE/$STYLE] ... "

  if [ "$ENGINE" = "weasyprint" ]; then
    python3 "$SCRIPT_DIR/md2elegant.py" "$INPUT" \
      -o "$OUTFILE" \
      --engine weasyprint \
      --style "$STYLE" \
      --no-cover --no-toc 2>/dev/null
  else
    python3 "$SCRIPT_DIR/md2elegant.py" "$INPUT" \
      -o "$OUTFILE" \
      --engine reportlab \
      --theme "$STYLE" \
      --no-cover --no-toc 2>/dev/null
  fi

  # Validate: file exists, >100KB, has Chinese chars
  if [ ! -f "$OUTFILE" ]; then
    echo "❌ FILE NOT CREATED"
    FAIL=$((FAIL + 1))
    continue
  fi

  SIZE=$(stat -f%z "$OUTFILE" 2>/dev/null || stat -c%s "$OUTFILE" 2>/dev/null)
  if [ "$SIZE" -lt 102400 ]; then  # <100KB → empty shell
    echo "❌ SHELL ONLY (${SIZE}B)"
    FAIL=$((FAIL + 1))
    continue
  fi

  # Use python to check Chinese chars
  CN_COUNT=$(python3 -c "
import fitz
try:
    doc = fitz.open('$OUTFILE')
    cn = sum(sum(1 for c in doc[i].get_text() if '\u4e00' <= c <= '\u9fff') for i in range(doc.page_count))
    print(cn)
except Exception as e:
    print(-1)
" 2>/dev/null)

  if [ "$CN_COUNT" -gt 0 ]; then
    echo "✅ $(python3 -c "print($SIZE/1024)" 2>/dev/null)KB cn=$CN_COUNT"
    PASS=$((PASS + 1))
  else
    echo "❌ NO CHINESE TEXT (${SIZE}B)"
    FAIL=$((FAIL + 1))
  fi
done

# Summary
echo ""
echo "=========================================="
echo "  Results: $PASS/$TOTAL passed, $FAIL failed"
echo "=========================================="

# Cleanup unless DEBUG
if [ -z "${DEBUG:-}" ]; then
  rm -rf "$OUTPUT_DIR"
fi

exit $FAIL
