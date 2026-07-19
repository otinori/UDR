# /udr-sync — コンテキストファイル同期

UDR のサマリを GEMINI.md / CLAUDE.md / AGENTS.md 等の SYNC マーカー間に書き込む。Claude Code の `/udr-sync` skill と等価な動作を Gemini CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む（特に §5 sync マーカー仕様）
2. **skill 本体を読み込む**: `.claude/skills/udr-sync/SKILL.md` を読み、その手順に **厳密に** 従って実行する
3. **sync ターゲットの確認**: `.udr/config.yaml` の `sync.targets` を読む
4. **UDR を収集**: `.udr/records/UDR-*.yaml` を全件読み込む
5. **選択ロジック**:
   - `pinned: true` の UDR を最大 5 件（優先）
   - 残りスロットを `severity` と `date` でスコアリングして自動選択（最大 15 件）
   - 合計 budget_tokens（デフォルト 1200）以内に収める
6. **書き込み**: 各 target ファイルの `<!-- [UDR-SYNC-START] -->` ～ `<!-- [UDR-SYNC-END] -->` の間に差分更新
7. **Atomic 書き込み**: 一時ファイルに書いてから rename する（NTFS 環境は例外）

## SYNC マーカー形式

```markdown
<!-- [UDR-SYNC-START] -->
<!-- 自動生成 — 直接編集不可 / 更新: /udr-sync -->

| ID | タイトル | 判断 | domain |
|---|---|---|---|
| UDR-XXX-... | タイトル | 決定の1行要約 | architecture |

<!-- [UDR-SYNC-END] -->
```

## 重要な制約

- マーカー内は **編集不可**（上書きされる）
- マーカーが存在しない場合は、ファイル末尾に追記してよいか user に確認する
