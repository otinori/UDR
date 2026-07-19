# /udr-search — UDR 検索

UDR を ID 指定 / フィールドフィルタ / 全文キーワード検索の 3 モードで取得する。Claude Code の `/udr-search` skill と等価な動作を Codex CLI で行うラッパー。

## 引数

`$ARGUMENTS` — 検索クエリまたは ID。例:
- `UDR-atlas-20260423T1430-a3f` (ID 直接指定)
- `domain:architecture severity:high` (フィールドフィルタ)
- `subtree split` (全文キーワード)

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む
2. **skill 本体を読み込む**: `.claude/skills/udr-search/SKILL.md` を読み、3 モード (ID / フィルタ / 全文) のいずれに該当するか判定し、その手順に従って `.udr/records/*.yaml` を走査する
3. 結果を表示する。全文検索の場合は `CONVENTIONS.md §5.3` のスコア式 (title×3 + decision×2 + context×1 + options×1) で降順ソートする
4. 件数が多い場合は上位 10 件 + 件数サマリを返す

## 重要な制約

- embedding・ベクトル DB・外部 LLM API は使わない (Phase 1 PoC 制約 C-006/C-007)。全文検索は SKILL.md の Stage1 決定的スコアリングを既定とし、0 件 / 低スコア時のみ Stage2 (Codex 自身による Read/Grep 追加探索) にエスカレートする (UDR-UDR-20260711T0728-f9f)
- ID 直接指定で見つからない場合はファジーマッチ候補を 3 件まで提示
