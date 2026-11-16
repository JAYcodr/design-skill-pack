#!/usr/bin/env bash
# 安装 design-skill-pack 到 agent 的 skills 目录
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$HERE/skills"

TARGETS=()
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --agents) TARGETS+=("$HOME/.agents/skills") ;;
    --both)   TARGETS+=("$HOME/.claude/skills" "$HOME/.agents/skills") ;;
    --force)  FORCE=1 ;;
    -h|--help)
      sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "未知参数: $arg" >&2; exit 2 ;;
  esac
done

[ ${#TARGETS[@]} -eq 0 ] && TARGETS=("$HOME/.claude/skills")

if [ ! -d "$SRC" ]; then
  echo "找不到 skills/ 目录，请在仓库根目录运行。" >&2
  exit 1
fi

for dest in "${TARGETS[@]}"; do
  mkdir -p "$dest"
  echo "→ $dest"
  for skill in "$SRC"/*/; do
    name="$(basename "$skill")"
    if [ -e "$dest/$name" ]; then
      if [ "$FORCE" -eq 1 ]; then
        rm -rf "${dest:?}/$name"
      else
        echo "  跳过 $name（已存在，加 --force 覆盖）"
        continue
      fi
    fi
    cp -R "$skill" "$dest/$name"
    echo "  装好 $name"
  done
done

echo
echo "完成。重启 agent 会话后即可看到这些 skill。"
echo "PDF 依赖： pip3 install markdown-it-py PyYAML mdit-py-plugins"
echo "             pip3 install weasyprint   （或 reportlab）"
