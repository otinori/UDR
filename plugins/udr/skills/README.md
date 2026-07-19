# UDR Skills — Phase 1 PoC (プロンプトレベル実装)

Claude Code の skill として UDR (Universal Decision Record) を運用するための最小セット。
MCP Server は未実装 (Phase 2 以降)。本 skill 群は **YAML ファイル直編集 + Claude の対話ガイド** で動く。

## 利用順序

1. `/udr-init` — 初回のみ。`.udr/` ディレクトリ構造と `config.yaml` を生成。他リポジトリからのコピー後には、既存レコードの保持／削除、`repo_short` 更新、`sync_targets` への同期も行う。
2. `/udr-record` — 判断が発生したら呼ぶ。対話で YAML を構築。記録後 `/udr-sync` を自動提案。
3. `/udr-search <query>` — 既存判断を確認。ID 直接／フィルタ／全文検索。
4. `/udr-sync` — CLAUDE.md 等へ要約を同期。pinned(5) + auto(15) をスコア順に選択、budget 1200。
5. `/udr-trace <id> [--impact]` — 上下流の DAG を辿る／変更影響を集計。
6. `/udr-review` — スプリント末などに品質棚卸し (orphan / 不整合 / AI 承認待ち / 棄却理由欠落)。
7. `/udr-dashboard` — 判断状況を自己完結 HTML (`udr_dashboard.html`) に出力 (集計 / 一覧 / 棄却理由 / 依存関係)。

## ファイル構成

```
.claude/skills/
├── README.md                 (このファイル)
├── _udr-shared/
│   └── CONVENTIONS.md        (ID/スキーマ/status 遷移/sync マーカー等の共通規約。全 skill が参照)
├── udr-init/SKILL.md         (FR-014)
├── udr-record/SKILL.md       (FR-001 / FR-010 / FR-012 / FR-015 / BR-002 / BR-007)
├── udr-search/SKILL.md       (FR-002)
├── udr-sync/SKILL.md         (FR-008 / FR-009 / NFR-007 / NFR-009)
├── udr-trace/SKILL.md        (FR-005 / FR-006 / FR-007)
├── udr-review/SKILL.md       (FR-013)
└── udr-dashboard/SKILL.md    (FR-013 補完 / D-1・D-4 の HTML 可視化)
```

## 要件カバレッジ

| 要求 ID | カバー skill | 状態 |
|---|---|---|
| FR-001 判断の新規記録 | udr-record | ✅ |
| FR-002 検索・取得 | udr-search | ✅ |
| FR-003 部分更新 | (直接 Edit + audit.log 手動追記) | Phase 2 で skill 化 |
| FR-004 supersede | (udr-record で旧 UDR の status 変更 + 新 UDR 作成) | Phase 2 で skill 化 |
| FR-005 依存追跡 | udr-trace | ✅ |
| FR-006 影響分析 | udr-trace --impact | ✅ |
| FR-007 循環検出 | udr-record / udr-trace / udr-review | ✅ |
| FR-008 コンテキスト同期 | udr-sync | ✅ |
| FR-009 サマリ自動生成 | udr-record (Step 1) + udr-sync (Step 3 優先度) | ✅ |
| FR-010 AI 生成は proposed | udr-record (BR-002 判定) | ✅ |
| FR-011 サマリーレポート | udr-review (簡易版) | ✅ (limited) |
| FR-012 対話的記録ガイド | udr-record | ✅ |
| FR-013 判断レビュー | udr-review | ✅ |
| FR-014 プロジェクト初期化 | udr-init | ✅ |
| FR-015 棄却 0 件警告 | udr-record | ✅ |

Phase 2 (MCP Server) で `FR-003` / `FR-004` を独立 skill / MCP tool 化する。

## Phase 1 PoC の明示的な制約

- **LLM 外部呼び出しなし** (C-007): `summary_hint` はテンプレート結合のみ。
- **embedding・ベクトルDB・外部LLM APIなし** (C-006/C-007): 全文検索は決定的スコアリング（Stage1）を既定とし、0件/低スコア時のみ AI エスカレート探索（Stage2）を行う 2 段階ハイブリッド方式（UDR-UDR-20260711T0728-f9f）。
- **atomic write はベストエフォート** (FR-008 / AR2-02): Claude の Write は単発書き込み。失敗時は手動復元を案内。
- **500 件上限** (C-009 / NFR-005): 超過時は Phase 4 SQLite 移行を案内するのみ。

## 申し送り (Phase 2 への引継ぎ)

- 各 skill の処理ロジックを MCP tool (`udr_create` / `udr_read` / `udr_update` / `udr_trace` / `udr_sync_context` / `udr_init` / `udr_summary`) に移植する。
- `CONVENTIONS.md` は Phase 2 でも MCP Server の設計ドキュメントとして流用可能。
- 同期マーカーと YAML スキーマは Phase 1 と Phase 2 で **互換** を保証する (Phase 1 で書かれた UDR は Phase 2 でそのまま読める)。
