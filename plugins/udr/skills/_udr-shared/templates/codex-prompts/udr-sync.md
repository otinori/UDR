# /udr-sync — UDR コンテキスト同期

UDR の要約を CLAUDE.md / AGENTS.md / `.github/copilot-instructions.md` / `.github/instructions/udr-decisions.instructions.md` の SYNC マーカー間に安全に書き込む。Claude Code の `/udr-sync` skill と等価な動作を Codex CLI で行うラッパー。

## 引数

`$ARGUMENTS` (任意):
- `--dry-run` — 書き込まず差分のみ表示
- `--target <path>` — 特定ターゲットのみ同期
- `--force` — マーカー不在時でも全体置換 (危険、確認必須)

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読み、sync マーカー規約とスコア式を理解する
2. **skill 本体を読み込む**: `.claude/skills/udr-sync/SKILL.md` を読み、その処理フロー (Step 1 対象選定 → Step 2 サマリ選択 → Step 3 出力組み立て → Step 4 パス許可チェック → Step 5 atomic write → Step 6 差分計算 → Step 7 audit.log → Step 8 報告) に **厳密に** 従って実行する
3. 各ターゲットファイルへの書き込み結果と差分 (added / removed / updated) を user に報告する

## 重要な制約

- pinned(5) + auto(15) のハイブリッド選択、token_budget 1200 を超過したら auto を打ち切り (AD-02)
- サマリ優先度: `claude_summary` > `client_summary` > `summary_hint`
- パストラバーサル防止: `config.yaml` の `allowed_sync_paths` グロブと照合 (NFR-009)
- atomic write は `.bak` バックアップ → `.tmp` 書き込み → rename の順 (Windows で rename 失敗時は `.bak` から復元)
- `policy+compact` / `policy-only` 形式は 0 件でも policy セクションを書く (UDR-SYNC-011 例外)
