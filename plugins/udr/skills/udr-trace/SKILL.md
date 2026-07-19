---
name: udr-trace
description: UDR の依存関係 (depends_on / triggers / supersedes) を DAG として走査し、上流 (前提)・下流 (波及)・双方向を深度指定で辿る。変更影響分析として domain / severity 別に集計し、critical path を抽出する (FR-005/FR-006/FR-007)。
---

# udr-trace — DAG 追跡・影響分析 skill

> **前提:** `.claude/skills/_udr-shared/CONVENTIONS.md` を先読み。

## 何ができるか

既存 ADR ツールに存在しない UDR 固有の機能 (差別化 [D-1]):

- **上流追跡** (`upstream`): 指定 UDR が依存している判断を辿る (`depends_on` を逆に辿る)
- **下流追跡** (`downstream`): 指定 UDR が引き起こした後続を辿る (`triggers` と「他 UDR の `depends_on` 被参照」)
- **影響分析** (`impact`): 指定 UDR を変更した場合に影響を受ける下流を domain/severity 別に集計
- **循環検出**: DAG 整合性チェック (FR-007)

## 入力

```
/udr-trace <id> [--direction upstream|downstream|both] [--depth N] [--impact]
```

- `<id>`: 起点 UDR の ID (必須)
- `--direction`: デフォルト `both`
- `--depth`: デフォルト 3、最大 10（NFR-002 の 5 秒制約のため）
- `--impact`: 下流を集計して影響レポートを出す

## 処理

### Step 1. グラフ構築

1. `.udr/records/*.yaml` を Glob → 全 UDR の `id`, `domain`, `severity`, `status`, `title`, `relations.*` を Read
2. メモリ上に有向グラフを構築:
   - ノード: UDR ID
   - エッジ: `depends_on` / `triggers` / `supersedes` の 3 種をラベル付きで
3. `superseded` 状態の UDR は「歴史」として記録するがトラバースから除外（`--include-superseded` 指定時のみ含める）

### Step 2. 起点検証

- `<id>` が存在しなければ `UDR-TRACE-404`
- `<id>` が `rejected` / `superseded` なら警告（処理は続行）

### Step 3. BFS 走査

方向別に以下を展開:

**upstream** (前提を遡る):
- `<id>` の `depends_on` に挙がっている UDR を展開
- さらにその UDR の `depends_on` を展開（深度まで）

**downstream** (波及を辿る):
- `<id>` の `triggers` に挙がっている UDR を展開
- さらに「自身を `depends_on` に含む UDR」（逆参照）も展開
- 深度まで

**both**: upstream と downstream を別々に計算し、最後に結合

### Step 4. 循環検出 (FR-007)

走査中に「既訪問ノード」を再訪したら循環。パスを保持していれば `A → B → C → A` として報告。

→ 循環発見時は **エラー `UDR-TRACE-007`** を返し、DAG 是正を促す（修正対象 UDR と修正すべき関係を提示）。

### Step 5. 出力

#### 通常トレース

```
UDR-udr-20260423T1430-a3f  認証基盤に OAuth2.0+PKCE を採用
  domain: architecture  severity: high  status: accepted

▲ Upstream (depth 3)
├─ UDR-udr-20260218T0900-b12  モバイルアプリ対応方針          [requirements] high
│   └─ UDR-udr-20260115T1445-77a  事業計画 2026               [project]      high
└─ UDR-udr-20260110T0800-4cc  セキュリティ基準 SEC-2024-v3   [risk]         high

▼ Downstream (depth 3)
├─ UDR-udr-20260501T1000-9ab  API Gateway 製品選定          [design]       medium
│   ├─ UDR-udr-20260510T1030-2de  Gateway 認証キャッシュ方式  [design]       low
│   └─ UDR-udr-20260515T0900-55f  Gateway 監視設計           [operations]   medium
└─ UDR-udr-20260502T1400-7bc  認証移行スケジュール          [project]      high

循環: 検出されず
```

#### 影響分析レポート (`--impact`)

```
影響分析: UDR-udr-20260423T1430-a3f (OAuth2.0+PKCE 採用) を変更した場合

下流 UDR 数: 4

domain 別:
  design:      2 件
  project:     1 件
  operations:  1 件

severity 別:
  high:    1 件  ← 優先レビュー
  medium:  2 件
  low:     1 件

critical paths (high severity まで到達するパス):
  - UDR-udr-20260423T1430-a3f → UDR-udr-20260502T1400-7bc (認証移行スケジュール)

status 別:
  accepted:  4 件
  proposed:  0 件

推奨アクション:
  - 上記 critical paths の UDR を先にレビュー
  - variation があれば /udr-record で supersede を検討
  - sync に反映: /udr-sync
```

## エラーコード

| Code | 条件 |
|---|---|
| UDR-TRACE-001 | `.udr/` 未初期化 |
| UDR-TRACE-007 | DAG に循環検出 (メッセージに循環パスを含む) |
| UDR-TRACE-404 | 起点 ID が存在しない |
| UDR-TRACE-010 | YAML パース失敗 (該当 ID を提示) |
| UDR-TRACE-020 | `depth` が 10 超 → 10 に丸めて処理続行 (警告) |

## 性能 (NFR-002)

- 500 件 / 深度 3 / both: 5 秒以内を目標
- 超過したら `.udr/index.json` にキャッシュを書く運用を案内（Phase 2 で MCP 化）

## 実装メモ (Phase 1 PoC)

グラフ構築は 1 回の Glob + 全 Read で済ませる。毎回ファイルを舐めるため 500 件以下を前提。
再利用のため、大規模時は `.udr/index.json` にキャッシュする実装を後続 Phase で検討 (C-009)。
