# UDR 共通規約 (Phase 1 PoC / プロンプトレベル)

> すべての `udr-*` skill はこのファイルを最初に読み、規約を遵守すること。
> 出典: 設計初期に作成した入力資料（フォーマット案・インタフェース設計・コンテキストファイル設計・アーキテクチャー決定書。本リポジトリには含まれない）と `docs/Phase1_要求定義/要求一覧.md`。

---

## 1. ディレクトリ構造

```
<project root>/
├── .udr/
│   ├── records/                    # UDR YAML 本体 (1判断 = 1ファイル)
│   │   └── UDR-<repo>-<ts>-<rand>.yaml
│   ├── index.json                  # DAG キャッシュ (gitignore)
│   ├── config.yaml                 # プロジェクト設定
│   └── audit.log                   # 操作ログ (gitignore)
└── .gitignore                      # .udr/index.json, .udr/audit.log を追加
```

- `records/` と `config.yaml` のみ Git 管理対象。
- `index.json` と `audit.log` は `.gitignore` で除外（NFR-011 / AR2-04）。

---

## 2. ID 体系（FR-001 / AD-03 / AD-05）

**フォーマット:** `UDR-<repo_short>-<UTC_TS>-<rand3>`

- `repo_short` — `config.yaml` の `repo_short` キー（未設定時はリポ名の英小文字 8 文字まで）。
- `UTC_TS` — `YYYYMMDDTHHmm`（UTC）。例: `20260423T1430`
- `rand3` — 3 桁の `[0-9a-f]`（衝突時はリトライ）。

**例:** `UDR-udr-20260423T1430-a3f`

> 生成時は必ず `date -u +%Y%m%dT%H%M` 相当で UTC を使うこと。ローカルタイムは禁止。

---

## 3. UDR YAML スキーマ（FR-001 / フォーマット案 v0.1）

```yaml
# --- メタ情報 ---
id: UDR-<repo>-<ts>-<rand>            # 自動採番
title: "<50字以内の一行要約>"
domain: architecture                   # 下記 enum から 1 つ
status: proposed                       # draft | proposed | accepted | deprecated | superseded | rejected
severity: medium                       # high | medium | low
pinned: false                          # true=同期で常時先頭 (max 5 件)
owner: otinori                         # 最終判断の責任者 (任意。authors と重複可)
tags:                                  # 自由タグ: スプリント番号・マイルストーン等 (任意)
  - "sprint-7"
date: 2026-04-23
updated: 2026-04-23
authors:
  - name: otinori
    role: human            # human | ai-agent | reviewer
  - name: claude-code
    role: ai-agent

# --- コンテキスト ---
context: |
  （なぜこの判断が必要になったかを 3-6 行で）

constraints:                           # 判断を縛る制約 (強く推奨 — 外部制約・コスト・方針がある場合は必ず記録)
  - "..."

code_refs:                             # この判断に関係するファイル・実装箇所 (任意)
  - path: "src/auth/TokenValidator.java"
    note: "このクラスで JWT 検証ロジックを実装"

# --- 選択肢 ---
options:
  - id: opt-1
    name: "採用案の名前"
    verdict: accepted                  # accepted | rejected | deferred
    rationale: |
      なぜ採用（or 棄却）したか
    pros: ["..."]
    cons: ["..."]
  - id: opt-2
    name: "棄却案"
    verdict: rejected
    rationale: |
      棄却理由（UDR の存在意義の核心）

# --- 判断 ---
decision: |
  最終決定の 2-3 行要約

consequences:
  positive: ["..."]
  negative: ["..."]
  risks: ["..."]

# --- DAG 関係 ---
relations:
  depends_on: []    # [{id, title, domain, relationship}]  relationship = 関係の性質 (技術的依存/要件由来/方針遵守 等)
  triggers:    []
  supersedes:  []
  superseded_by: [] # この判断を無効化した後継 UDR。udr-record が自動書き込み (FR-004)

# --- 検証 ---
verification:
  criteria: []
  review_date: null
  review_trigger: null

# --- サマリ（同期用） ---
summary_hint: |                        # 自動生成。上書き優先度 最低
  [UDR-xxx] <title>。決定:<decision1行>。棄却:<rejected[0].name>(<理由1語>)。
claude_summary: null                   # 人間/AI 手書き。優先度 最高
client_summary: null                   # クライアント側 LLM リライト。中
```

### 3.1 domain enum（要求一覧 / DE-02）

`architecture` | `requirements` | `design` | `risk` | `project` | `operations` | `other`

### 3.2 文章品質原則（PJ 外読者テスト）

各テキストフィールド（`context` / `decision` / `options[].rationale`）は
**「このリポジトリを今日初めて見た経験豊富なエンジニアが文脈なしで読んで、
判断の背景・選択理由・棄却根拠を理解できる」** 水準で書く。

詳細な Good/Bad 例と自己チェックリストは `udr-record/SKILL.md §文章品質ガイドライン` を参照。

Claude Code では、この基準を Claude 自身の自己チェックに加え、**会話履歴を持たない
独立コンテキストのサブエージェントレビュー**で二重に検証する
（`udr-record/SKILL.md §4.3 独立コンテキストレビュー`）。マルチロールでのレビュー
（PM 視点・監査視点等）は本 Phase ではスコープ外とし、multi-agent レビュー基盤との
連携を将来検討する。

### 3.3 省略ルール（FR-012 / PO2-02）

補完フェーズでスキップされたフィールドは **キー自体を省略** する。`null` や `[]` で書かない。
→ 「記録されなかった」と「空で記録された」を Git diff で区別可能にする。

### 3.5 コード注釈規約（コード → UDR 逆引き）

ソースコードに UDR ID を注釈として埋め込み、「なぜこのコードがこう書かれているか」を逆引き可能にする:

```python
# UDR: UDR-<repo>-<ts>-<rand>   （Python / Shell / YAML）
```
```java
// UDR: UDR-<repo>-<ts>-<rand>  （Java / JavaScript / Go / C# 等）
```
```sql
-- UDR: UDR-<repo>-<ts>-<rand>  （SQL）
```

- 注釈は判断が最も反映されているロジックの直上に置く（ファイル先頭ではなく該当箇所）。
- 逆引き検索: `/udr-search code:<path>` または `grep -r "UDR:" <src_dir>` で一覧取得。
- UDR 側の `code_refs[].path` と対で管理すると双方向追跡が可能になる。

### 3.4 スカラー出力規約（**必須・YAML パース破壊防止**）

生成 YAML は標準パーサ（PyYAML `safe_load` 等）で例外なく読めること。プレーンスカラー内の `:␣`（半角コロン+空白）はマッピング区切りと誤解され `could not find expected ':'` / `mapping values are not allowed here` を引き起こす。

- **複数行フリーテキスト**（`context` / `decision` / `options[].rationale` / `consequences.*` の長文）は **ブロックリテラル `|`**。
- **リスト項目**（`constraints` / `options[].pros` / `options[].cons` / `consequences.{positive,negative,risks}` の `- …`）は **必ず `- "…"`**（ダブルクォート）。
- **単一行スカラー**（`title` / `options[].name` 等）は、`:␣` / `#␣` / 先頭が `- ? : , [ ] { } & * ! | > ' " % @ \`` / 先頭・末尾空白 を含むなら**必ずダブルクォート**。
- **簡便則: 値に `:␣` を含むなら無条件でクォート**。ダブルクォート内は `"`→`\"`、`\`→`\\`。迷えばクォート（過剰クォートは無害）。
- 全角コロン `：` は安全。半角 `:` の混入のみ要注意。

> ❌ `- 旧 README の : を見落とす可能性` → ✅ `- "旧 README の : を見落とす可能性"`

---

## 4. status 遷移（BR-004）

```
draft ──[人間が decision を入力・承認]──▶ accepted
draft ──[人間が完成させるが承認は後で]──▶ proposed
draft ──[廃棄]─────────────────────────▶ rejected (終端)
proposed ──[人間承認]──▶ accepted
proposed ──[人間棄却]──▶ rejected (終端)
accepted ──[非推奨化]──▶ deprecated
accepted ──[FR-004]────▶ superseded (終端, BR-003)
deprecated ──[FR-004]──▶ superseded (終端)
```

- **逆方向遷移は全て禁止。** `deprecated → accepted` も不可（再活性化は新 UDR を作り `depends_on` で旧を参照）。
- **初期 status:**
  - 通常: `proposed`
  - `udr-record` (FR-012) 経由で **authors に人間が含まれる** 場合のみ `accepted`
  - `authors` 全員が ai-agent の場合 → `proposed` **強制** (BR-002、FR-012 経由でも優先)
  - AI が判断依頼として記録する場合 → `draft`（BR-002 の対象外。判断ではなく依頼のため）

### 4.2 draft の特則

`draft` は「判断が必要だが人間がまだ決めていない」状態を表す。判断記録ではなく **判断依頼の記録**。

- **`decision` フィールドは placeholder を許容:** `「（未定 — 人間判断待ち）」` という文字列で保存する（draft 限定の例外）。
- **`options[].verdict` は `deferred` を使用:** accepted / rejected はまだ決まっていないため。
- **`/udr-sync` の対象外:** 中途半端な内容を AI コンテキストファイルに流さない。
- **AI 単独での draft 作成を許容:** 情報収集 + 依頼行為であり BR-002（AI 単独 proposed 禁止）の対象外。draft → proposed/accepted 昇格時に authors を再評価する。
- **放置検出:** `/udr-review` が `config.review.draft_stale_days`（デフォルト 3）日以上の draft を検出し、完成または廃棄を促す。

### 4.1 ai-agent 判定

`config.yaml` の `ai_agent_patterns` リストで照合。デフォルト:

```yaml
ai_agent_patterns:
  - "^claude-code$"
  - "^claude-opus.*"
  - "^claude-sonnet.*"
  - "^gpt-.*"
  - "^copilot.*"
  - "^cursor.*"
  - ".*-ai-agent$"
```

---

## 5. 同期マーカー（FR-008 / コンテキストファイル設計）

UDR 要約はターゲットファイルの以下マーカー間に書き込む:

```
<!-- [UDR-SYNC-START] -->
...（自動生成）...
<!-- [UDR-SYNC-END] -->
```

- マーカー不在時はファイル末尾に追記。
- ファイル不在時は新規作成。
- 書き込みは temp file → rename で atomic に（NFR-009 / FR-008）。Windows では rename 失敗時 `.bak` からリストア。

### 5.1 sync ターゲット（`tools` プロファイルから導出）

**原則:** `config.yaml` の `tools:` に宣言した AI ツールに対応するファイル**のみ**を sync/init の対象とする。これにより「使わないツールのファイルを生成しない」「使うツールのファイルは常に最新」を両立する。

**ツール → ターゲット対応:**

| `tools` の値 | sync ターゲット | 形式 |
|---|---|---|
| `claude` | `CLAUDE.md` | `policy+compact` |
| `codex` | `AGENTS.md` | `policy+compact` |
| `gemini` | `GEMINI.md` | `policy+compact` |
| `copilot` | `.github/copilot-instructions.md` | `policy-only`（行動指示のみ） |
| `copilot` | `.github/instructions/udr-decisions.instructions.md` | `detailed`（要約本体） |
| `cursor` | `.cursorrules` | `compact` |
| `windsurf` | `.windsurfrules` | `compact` |

**導出ルール:**

1. `config.yaml` に `sync.targets`（または `sync_targets`）が**明示**されていれば、それを最優先で使う（高度な上書き）。
2. なければ `tools:` の各値を上表で展開した**和集合**を sync ターゲットとする。
3. `tools:` も `sync.targets` もなければ、後方互換として `[claude]`（`CLAUDE.md` のみ）を既定とする。

**重要 — 実行中ツールでは分岐しない:** sync/init は「いま動かしているツール」に関係なく、宣言された**全ターゲット**を毎回更新する。例: `tools: [claude, codex]` の repo では、Claude Code で実行しても Codex で実行しても、`CLAUDE.md` と `AGENTS.md` の両方を最新化する（ツールを切り替えても双方が陳腐化しない）。

> `AGENTS.md` はマルチエージェント共通ポリシーのマスタ（UDR-UDR-20260610T0345-e3c）。`codex` を宣言している場合の sync 先であると同時に、全ツール向けの共通ポリシー文書でもある。

### 5.2 選択ロジック（AD-02）

1. `pinned: true` を全件（max 5）
2. 残りを **スコア降順** で `auto` として選択（max 15）
3. 合算推定トークンが **1200** を超えたら `auto` を打ち切り
4. サマリ優先度: `claude_summary` > `client_summary` > `summary_hint`

### 5.3 スコア（FR-002 / 全文検索と共通）

```
score = severity_w + recency_w + dag_w - status_penalty
  severity_w: high=3, medium=2, low=1
  recency_w:  updated から 30 日以内=2, 90 日以内=1, それ以外=0
  dag_w:      triggers 件数 × 0.5 (max 2)
  status_penalty: deprecated=2, superseded=5, rejected=5
```

---

## 6. DAG（FR-005 / FR-006 / FR-007）

### 6.1 関係の種類

- `depends_on` — 上流（この判断の前提）。`relationship` フィールドに性質を記録（技術的依存／要件由来／方針遵守 等）
- `triggers` — 下流（この判断により必要になる後続）
- `supersedes` — 置換（旧判断の無効化）
- `superseded_by` — 被置換（この判断を無効化した後継。`udr-record` が supersede 時に自動書き込み）

### 6.2 循環検出（FR-007）

新規作成・更新時に DAG を走査し、循環があれば **ブロック**してエラー。
エラーメッセージには循環パスを含める（例: `A → B → C → A`）。

### 6.3 FR-004 上書きロジック

旧 UDR を `superseded` 化し、新 UDR に `supersedes` リンク追加。
旧の `depends_on` / `triggers` は **コピー** して新に引き継ぐ（旧の関係は残置）。
**旧 UDR の `relations.superseded_by` に新 UDR の ID を自動追記**（`udr-record` §4.2 が担当）。
これにより旧レコードから後継へ直接辿れるようになる（双方向リンク）。

---

## 7. 監査ログ（NFR-011）

`.udr/audit.log` に 1 操作 1 行 JSON で追記（gitignore）:

```json
{"ts":"2026-04-23T14:30:12Z","actor":"otinori","role":"human","op":"create","id":"UDR-udr-20260423T1430-a3f","changed_fields":["*"]}
```

`op`: `create` | `update` | `supersede` | `sync` | `review`

---

## 8. エラーコード体系（NFR-010）

形式: `UDR-<TOOL>-<NNN>`

| TOOL | 用途 |
|---|---|
| INIT | 初期化 |
| REC | 記録 (FR-001 / FR-012) |
| SEARCH | 検索 (FR-002) |
| UPDATE | 更新 (FR-003) |
| SUP | 上書き (FR-004) |
| TRACE | DAG 走査 (FR-005/006) |
| SYNC | 同期 (FR-008) |
| REVIEW | レビュー (FR-013) |
| VALIDATE | 構造検証 |

各エラーは `{ code, message, hint, ref }` の 4 項目を最低限含める。

---

## 9. Phase 1 PoC の制約

- **MCP Server なし。** すべて Claude が Read/Write/Edit/Bash で YAML を直接操作する。
- **LLM 呼び出しなし。** summary_hint はテンプレート結合のみ（C-007）。
- **セマンティック検索なし。** C-006/C-007 の根本動機は embedding・ベクトル DB・外部 LLM API キーへの依存を排除しポータビリティを確保することであり、そのような新規外部依存は禁止する。全文検索は Stage1（title×3/decision×2/context×1/options×1 の決定的スコアリング + 構造化フィルタ）を既定とする。Stage1 が 0 件 / 低スコアの場合に限り、呼び出し元 AI が Read/Grep/`/udr-trace` の追加ラウンドで探索する Stage2 エスカレートを許容する（embedding・外部 API は使わない、UDR-UDR-20260711T0728-f9f）。
- **検証は手動。** 各 skill 実行後に user に変更内容を提示して確認を得る。
