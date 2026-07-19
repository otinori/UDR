---
name: udr-review
description: UDR 記録の品質を棚卸しする。orphan (孤立) / ステータス不整合 / 未承認 AI 単独判断 / 棄却理由 0 件 / DAG 健全性 / YAML 健全性 / sync 陳腐化 / code_refs 未記入 / 放置 draft の 9 観点で検出し、改善アクションを提示する (FR-013)。
---

# udr-review — 判断レビュー skill

> **前提:** `.claude/skills/_udr-shared/CONVENTIONS.md` を先読み。

## 検出観点

### ① Orphan UDR

**定義:** `status: accepted` かつ `depends_on` も `triggers` も空で、**他 UDR からも参照されていない**。
→ プロジェクトの他判断と繋がりがなく、記録されていても活用されていない可能性が高い。
→ `config.yaml` の `review.orphan_age_days` (デフォルト 30) より古いものに限る。

### ② ステータス不整合

- `status: deprecated` だが `supersedes` の逆リンク（他 UDR から `supersedes: this` で参照）がない
  → 置き換え先が記録されていない。理由不明の deprecated。
- `status: proposed` が `review.ai_pending_days` (デフォルト 7 日) 以上放置
  → 人間承認待ちがスタック。
- `status: superseded` だが自身に `relations.supersedes` (置き換え先) がない
  → BR-004 状態遷移の不整合。

### ③ 未承認 AI 単独判断 (D-5)

- `authors` 全員が ai-agent
- かつ `status: proposed` のまま `ai_pending_days` 以上経過

→ 人間の承認が必要。user に一覧を提示し、承認 or rejected を促す。

### ④ 棄却理由 0 件 (BR-007 / D-4)

- `options[].verdict: rejected` が 0 件の UDR を検出
- ただし `status: accepted` かつ本文に「選択の余地なし」旨の note があれば除外（Phase 1 PoC では heuristic、要 user 確認）

→ UDR の存在意義に反する記録。`udr-record` 経由で棄却案を追記提案。

### ⑤ DAG 健全性

- 循環参照 (FR-007) の再チェック
- 存在しない ID への `depends_on` / `triggers` / `supersedes` 参照（dangling link）
- 500 件閾値 (C-009 / NFR-005): 超えていれば警告

### ⑨ 放置 draft（判断依頼の未完成）

`status: draft` かつ `updated` から `config.review.draft_stale_days`（デフォルト 3 日）以上経過した UDR を検出。

draft は「人間が決める必要がある」という依頼記録であり、放置されると判断が宙吊りになりプロジェクトが止まるリスクがある。

→ action: `/udr-record --complete <id>` で decision を入力して昇格、または不要なら rejected に変更

### ⑦ sync 陳腐化

各コンテキストファイル（CLAUDE.md / AGENTS.md / GEMINI.md 等）の `[UDR-SYNC-START]` 直後の `synced <UTC ISO>` タイムスタンプを読み、現在との差が `config.review.sync_stale_days`（デフォルト 7 日）を超えていれば警告。

→ action: `/udr-sync` を実行して最新化

### ⑧ code_refs 未記入（アーキテクチャ・設計判断のコード紐付けなし）

`status: accepted` かつ `domain in (architecture, design)` でかつ `code_refs` フィールドが存在しない UDR を検出。

実装が存在するはずの判断にコード参照がない状態は、後から読む人（特にプログラマー）が判断とコードを結びつけられないリスクがある。

→ action: `/udr-search <id>` で確認し、`code_refs` を追記。またはソースコードに `# UDR: <id>` 注釈を追加（CONVENTIONS.md §3.5）

### ⑥ YAML 健全性（パース可否）

- 各レコードを標準パーサ相当（PyYAML `safe_load` 等）で読めるか検査する。
- **典型破壊**: プレーンスカラー内の `:␣`（半角コロン+空白）が mapping 区切りと誤解され `could not find expected ':'` / `mapping values are not allowed here` になる（`constraints` / `options[].pros|cons` / `consequences.*` / `title` 等のフリーテキスト欄、CONVENTIONS §3.3）。
- 検出時は **問題行と原因を提示し、該当スカラーをダブルクォート化する救済（`- foo: bar` → `- "foo: bar"`）を提案**する。`--fix yaml` で 1 件ずつ確認しながら自動クォートを適用。
- 根治はジェネレータ側（udr-record §4.1 / CONVENTIONS §3.3 のクォート規約）。本観点は既存の壊れたレコードの救済用。

## 処理フロー

### Step 1. 全 UDR 読み込み

1. `.udr/records/*.yaml` を Glob
2. 全ファイルの YAML を Read、メタと relations を抽出
3. 逆参照インデックスを構築（他から参照されている ID 集合）

### Step 2. 9 観点チェック

並行に検査して、観点ごとに「該当 UDR ID + 理由」を収集。⑥ は読み込み（Step 1）でパース失敗したファイルを対象にする。⑦ はコンテキストファイルのタイムスタンプを読む。⑨ は `status: draft` かつ経過日数を確認する。

### Step 3. レポート出力

```
UDR Review — <UTC ISO>

総件数: 142
  accepted:   98
  proposed:   12 (うち AI 単独 5)
  deprecated:  8
  superseded: 19
  rejected:    5

─────────────────────────────────────
① Orphan (30 日以上放置・関係なし)          3 件
  - UDR-udr-20260120T0900-11a  ログ出力方針
  - UDR-udr-20260203T1400-22b  エラーメッセージ i18n
  - UDR-udr-20260210T1600-33c  Lint ルール追加

  → action: /udr-record で関連判断を追記、または deprecated 化

② ステータス不整合                           2 件
  - UDR-udr-20260301T0900-44d  [deprecated, 置き換え先不明]
  - UDR-udr-20260315T1100-55e  [proposed 18 日経過]

  → action: supersedes 先を明示 / 人間承認 or rejected

③ 未承認 AI 単独判断 (7 日以上)              1 件
  - UDR-udr-20260416T0800-66f  HikariCP 採用

  → action: 内容レビュー後 /udr-record を update で人間 author を追加

④ 棄却理由 0 件                              4 件
  - UDR-udr-20260122T1500-77g  ...
  - UDR-udr-20260201T0900-88h  ...

  → action: /udr-search <id> で中身確認、棄却案を追記

⑤ DAG 健全性
  - 循環: 検出されず
  - dangling link: 1 件
    * UDR-udr-20260330T1000-99i が存在しない UDR-udr-20251201T-xxx を depends_on に記載
  - 件数警告: 142 / 500 (28%)

⑨ 放置 draft (3 日以上)                      2 件
  - UDR-udr-20260619T1400-aa1  認証ライブラリ選定 [draft 5 日経過]
  - UDR-udr-20260620T0900-bb2  ログ保持期間の方針 [draft 4 日経過]

  → action: /udr-record --complete <id>

⑦ sync 陳腐化                               1 件
  - CLAUDE.md: 最終 sync 14 日前 (2026-06-07)

  → action: /udr-sync を実行

⑧ code_refs 未記入 (architecture/design)   3 件
  - UDR-udr-20260210T0900-11a  認証基盤に OAuth2.0+PKCE を採用
  - UDR-udr-20260305T1400-22b  キャッシュ層を Redis に一本化
  - UDR-udr-20260401T1000-33c  API Gateway 製品選定

  → action: /udr-search <id> で確認し code_refs を追記
     またはソースコードに # UDR: <id> 注釈を追加

─────────────────────────────────────
優先対応:
  1. ⑨ の放置 draft を完成または廃棄（判断が宙吊りになっている）
  2. ③ の AI 単独 proposed を人間レビュー (BR-002 関連)
  3. ⑦ の sync 陳腐化解消 → /udr-sync
  4. ⑤ の dangling link 修正
  5. ④ の棄却理由補完（UDR 本来の価値）
  6. ⑧ の code_refs 追記（アーキ判断とコードの紐付け）
```

### Step 4. audit.log 追記

```json
{"ts":"<UTC ISO>","actor":"<name>","role":"human","op":"review","id":null,
 "findings":{"orphan":3,"status_inconsistent":2,"ai_pending":1,"no_reject":4,"dangling":1}}
```

## オプション

- `--fix orphan`: orphan を 1 件ずつ提示し user に deprecated 化するか確認
- `--fix ai-pending`: 未承認 AI 判断を 1 件ずつ提示し accept/reject を決める対話モード
- `--fix yaml`: ⑥ で検出したパース不能レコードを 1 件ずつ提示し、原因スカラーのダブルクォート化を確認のうえ適用（救済）
- `--format json`: 機械可読な JSON で出力（CI 用、Phase 3）
- `--threshold <N>`: 件数警告の閾値上書き（デフォルト 500）

## エラーコード

| Code | 条件 |
|---|---|
| UDR-REVIEW-001 | `.udr/` 未初期化 |
| UDR-REVIEW-010 | YAML パース失敗 (⑥ で問題ファイル・原因行を提示し、`--fix yaml` で自動クォート救済を提案) |
| UDR-REVIEW-500 | 件数が 500 件超 → C-009 に基づき Phase 4 SQLite 移行を案内 |

## 運用の目安

- **スプリントレトロスペクティブ**: スプリントごとに 1 回 `/udr-review` を実行し、アクション項目を次スプリントの TODO に反映。
- **月次**: ④ と ⑤ を必ず解消。① は四半期棚卸しでも可。

## KPI との紐付け (要求一覧 BC-01)

- `③ 未承認 AI 単独判断` 件数 → D-5 の運用品質
- `④ 棄却理由 0 件` 件数 → D-4 (棄却理由の記録定着率)
- 総件数の推移 → 「UDR 記録定着率」KPI のベース
