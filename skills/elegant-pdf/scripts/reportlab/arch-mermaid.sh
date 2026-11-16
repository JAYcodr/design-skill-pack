#!/bin/bash
# arch-pdf: Markdown（含 Mermaid） → 蓝色风格 PDF 报告
# Usage: arch-pdf <input.md> [options]
#   -o <output.pdf>   输出路径（默认 <input-stem>.pdf）
#   --theme <name>    主题（默认 nord-frost）
#   --title <title>   封面标题（默认取文档第一个 H1）
#   --author <name>   作者
#   --watermark <text> 水印

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(cd "$SCRIPT_DIR/../skills" && pwd)"
MD2PDF="$SKILLS_DIR/lovstudio-any2pdf/scripts/md2pdf.py"

INPUT=""
OUTPUT=""
THEME="nord-frost"
TITLE=""
AUTHOR=""
WATERMARK=""

show_help() {
  cat << 'EOF'
arch-pdf: Markdown（含 Mermaid） → PDF 报告

Usage: arch-pdf <input.md> [options]

Options:
  -o, --output <path>   输出 PDF 路径（默认 <input-stem>.pdf）
  --theme <name>         主题（默认 nord-frost）
  --title <title>        封面标题（默认取文档第一个 H1）
  --author <name>        作者
  --watermark <text>     水印
  -h, --help             显示帮助

Themes:
  nord-frost       蓝灰北欧风，清爽现代（默认）
  ocean-breeze     青绿海洋风
  ieee-journal     藏蓝期刊风
  warm-academic    暖学术风
  github-light     GitHub 蓝白极简
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) show_help; exit 0 ;;
    -o|--output) OUTPUT="$2"; shift 2 ;;
    --theme) THEME="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --author) AUTHOR="$2"; shift 2 ;;
    --watermark) WATERMARK="$2"; shift 2 ;;
    -*) echo "未知选项: $1"; exit 1 ;;
    *) INPUT="$1"; shift ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "错误：需要指定输入文件"
  show_help
  exit 1
fi

if [[ ! -f "$INPUT" ]]; then
  echo "错误：文件不存在: $INPUT"
  exit 1
fi

# 判断是否包含 mermaid
HAS_MERMAID=false
if grep -q '```mermaid' "$INPUT" 2>/dev/null || grep -q '\.mmd' "$INPUT" 2>/dev/null; then
  HAS_MERMAID=true
fi

BASENAME="$(basename "$INPUT" .md)"

# 计算输出路径（相对于原目录）
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="$(dirname "$INPUT")/${BASENAME}.pdf"
fi

# Mermaid 转换（如果需要）
if $HAS_MERMAID; then
  cd "$(dirname "$INPUT")"  # mmdc 需要在输入文件所在目录运行，才能正确解析相对路径
  ASSETS_DIR="$(dirname "$INPUT")/assets"
  mkdir -p "$ASSETS_DIR"
  mmdc -i "$(basename "$INPUT")" -o "$(basename "$INPUT")" -a "$ASSETS_DIR" -e png
  cd - > /dev/null
fi

# 构建 PDF 命令
PYTHON_ARGS=(--input "$INPUT" --output "$OUTPUT" --theme "$THEME")
[[ -n "$TITLE" ]] && PYTHON_ARGS+=(--title "$TITLE")
[[ -n "$AUTHOR" ]] && PYTHON_ARGS+=(--author "$AUTHOR")
[[ -n "$WATERMARK" ]] && PYTHON_ARGS+=(--watermark "$WATERMARK")

python3 "$MD2PDF" "${PYTHON_ARGS[@]}"