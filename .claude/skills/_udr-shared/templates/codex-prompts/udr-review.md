# /udr-review — UDR 品質棚卸し

UDR 記録の品質を 9 観点 (orphan / ステータス不整合 / 未承認 AI 単独判断 / 棄却理由 0 件 / DAG 健全性 / YAML 健全性 / sync 陳腐化 / code_refs 未記入 / 放置 draft) で検出し、改善アクションを提示する。Claude Code の `/udr-review` skill と等価な動作を Codex CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む
2. **設定を読み込む**: `.udr/config.yaml` の `review.orphan_age_days` (デフォルト 30) / `review.ai_pending_days` (デフォルト 7) / `review.sync_stale_days` (デフォルト 7) / `review.draft_stale_days` (デフォルト 3) を取得
3. **skill 本体を読み込む**: `.claude/skills/udr-review/SKILL.md` を読み、その検出ロジック (FR-013) に従って `.udr/records/*.yaml` を走査する
4. 9 観点それぞれに該当する UDR 一覧と推奨アクション (`/udr-record` で supersede / 人間レビュー依頼 / 棄却理由の追記など) を表示する
5. レビュー結果を audit.log に `op:"review"` で記録する

## 検出観点 (9 つ)

1. **orphan**: depends_on / triggers / supersedes のいずれも持たず他 UDR からも参照されておらず、`updated` が `orphan_age_days` 日以上前
2. **ステータス不整合**: `deprecated` なのに置き換え先 (supersedes 逆リンク) がない / `proposed` が `ai_pending_days` 日以上放置 / `superseded` なのに自身に `supersedes` がない
3. **未承認 AI 単独判断**: `authors` が全員 ai-agent かつ `status: proposed` のまま `ai_pending_days` 日以上経過
4. **棄却理由 0 件**: options に rejected が 1 件もない (FR-015 警告で進めた UDR)
5. **DAG 健全性**: 循環参照の再チェック / 存在しない ID への depends_on・triggers・supersedes 参照 (dangling link) / 500 件閾値の超過警告
6. **YAML 健全性**: 標準パーサ (PyYAML `safe_load` 等) で読めるか。プレーンスカラー内の `:␣` 混入によるパース破壊を検出し、ダブルクォート化で救済提案
7. **sync 陳腐化**: 各コンテキストファイルの `synced <UTC ISO>` から `review.sync_stale_days` 日以上経過
8. **code_refs 未記入**: `status: accepted` かつ `domain in (architecture, design)` で `code_refs` が存在しない
9. **放置 draft**: `status: draft` かつ `updated` から `review.draft_stale_days` 日以上経過（判断依頼が宙吊りのまま）
