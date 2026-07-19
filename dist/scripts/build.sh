#!/usr/bin/env bash
# .claude/ を唯一の source of truth として配布先へミラーする。
#
# .claude/skills/   → plugins/udr/skills/      (プラグインマーケットプレイス用)
#
# .claude/deploy/    → plugins/udr/ (root)     (GEMINI.md / .gemini/ — プラグイン配布用)
#
# dist/scripts/install.sh は .claude/skills/ と .claude/deploy/ を直接参照するため
# (独立ミラーを持たない)、本スクリプトの対象外。
#
# 使い方:
#   bash dist/scripts/build.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$DIST_ROOT/.." && pwd)"

SKILLS_SRC="$REPO_ROOT/.claude/skills"
DEPLOY_SRC="$REPO_ROOT/.claude/deploy"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "ERROR: .claude/skills が見つかりません: $SKILLS_SRC" >&2
  exit 1
fi

# ── 1. skills ミラー ────────────────────────────────────────
echo ">> Rebuilding skills mirror from .claude/skills"
echo "   src: $SKILLS_SRC"

DST="$REPO_ROOT/plugins/udr/skills"
echo ">> dst: $DST"
rm -rf "$DST"
mkdir -p "$DST"
cp -r "$SKILLS_SRC/"* "$DST/"

# .bak-* が混入していたら除去
find "$DST" -name '*.bak-*' -type d -exec rm -rf {} + 2>/dev/null || true
find "$DST" -name '*.bak-*' -type f -delete 2>/dev/null || true

echo "   -> $(find "$DST" -type f | wc -l | tr -d ' ') files"

# ── 2. デプロイテンプレートミラー ───────────────────────────
if [ -d "$DEPLOY_SRC" ]; then
  echo
  echo ">> Rebuilding deploy template mirror from .claude/deploy"
  echo "   src: $DEPLOY_SRC"

  DST="$REPO_ROOT/plugins/udr"
  mkdir -p "$DST"
  # dotglob を一時有効にして .gemini/ 等の hidden ディレクトリも含める
  (shopt -s dotglob; cp -r "$DEPLOY_SRC/"* "$DST/")
  echo "   -> $DST"
else
  echo
  echo "   (.claude/deploy not found, skipping deploy templates)"
fi

echo
echo ">> Done."
