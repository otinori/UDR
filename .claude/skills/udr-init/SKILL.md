---
name: udr-init
description: プロジェクトに UDR (Universal Decision Record) を初期化する。.udr/ ディレクトリ、config.yaml、テンプレート、.gitignore 更新を冪等に行う。既存環境では不足分のみ補完する (FR-014)。他リポジトリからのコピー後の初期化（repo_short 更新・既存レコード整理・sync_targets 同期）もサポートする。
---

# udr-init — UDR 初期化 skill

> **前提:** 事前に `.claude/skills/_udr-shared/CONVENTIONS.md` を読むこと。

## 目的

プロジェクト配下に UDR Phase 1 PoC の運用環境を作る。**`config.yaml` の有無** が振る舞いの主な分岐点であり、冪等に動作する:

1. **`config.yaml` なし（新規作成）** → 全ファイル新規作成。`repo_short` を現リポジトリ名から決定し user 確認
2. **`config.yaml` あり、`repo_short` が現リポジトリと一致** → 通常の冪等初期化（不足キーのみ補完）
3. **`config.yaml` あり、`repo_short` が現リポジトリと不一致** → `repo_short` を更新し、既存レコードの整理・sync_targets の同期を対話的に処理する（本 skill の主拡張点）
4. `config.yaml` のスキーマバージョン変更時 → 既存値を保持しつつ不足キーを追加（破壊的変更なし、FR-014）

## 手順

### Step 1. 現状確認

以下を並列で確認する:

- `.udr/` の有無
- `.udr/records/` の有無と、その中の `UDR-*.yaml` ファイル一覧
- `.udr/config.yaml` の有無と内容（特に `repo_short` の値）
- `.gitignore` の有無と UDR 関連エントリの有無

### Step 2. repo_short の決定と更新判断

`config.yaml` の有無にかかわらず、以下で現リポジトリの候補 `repo_short` を導出し、既存値との照合を行う。

1. `git remote get-url origin` から現リポジトリの URL を取得する。失敗する主なケース（すべてカレントディレクトリ名にフォールバック）:
   - Git リポジトリでない（`git rev-parse` が失敗）
   - `origin` リモートが未設定
   - ネットワークや設定の問題で URL 取得が失敗
2. URL からリポジトリ名を抽出する（URL 末尾のパスコンポーネントを使用。`.git` サフィックスは除去）:
   - HTTPS 形式例: `https://github.com/org/myrepo.git` → `myrepo`
   - SSH 形式例: `git@github.com:org/myrepo.git` → `myrepo`
3. 抽出したリポジトリ名を正規化（英小文字、`-`/`_` を除去、先頭 8 文字）して候補値 `candidate` を得る
   > **注意:** `my-repo` と `myrepo` は同じ候補に正規化される。不一致検出が起きない場合でも、user が repo_short を変更したければ対話で上書きできる（下記 [C] を参照）。

#### [A] config.yaml なし（新規作成）

- `candidate` を user に提示して確認を取る（**ID に埋め込まれるため、後から変えにくい旨を必ず伝える**）
- user が承認した値を `new_repo_short` として決定し、Step 2.5 → Step 3 へ進む

#### [B] config.yaml あり、`repo_short` == `candidate`（一致）

- 変更不要。Step 3（通常の冪等初期化）へ直接進む

#### [C] config.yaml あり、`repo_short` != `candidate`（不一致）

- 「現リポジトリ候補: `<candidate>` / 記録済み repo_short: `<既存値>`」を user に伝え、以下を選択させる:
  ```
  repo_short を更新しますか？
    (Y) <candidate> に更新する（推奨）
    (N) <既存値> のまま維持する
    (M) 別の値を手動入力する
  ```
- **(Y)**: `new_repo_short = candidate` として Step 2.5 → Step 3 へ進む
- **(N)**: Step 3（通常の冪等初期化）へ進む。以降の UDR レコードや sync_targets は変更しない
- **(M)**: user が入力した値を `new_repo_short` として決定し、Step 2.5 → Step 3 へ進む

> [A] と [C] で `new_repo_short` が確定した場合、続けて Step 2.5 を実行する。

### Step 2.5. 既存 UDR レコードの処理（`new_repo_short` が確定した場合のみ）

`.udr/records/` に `UDR-*.yaml` が 1 件以上ある場合のみ実行する。

#### 2.5-A. 保持 or 削除の確認

user に以下を提示して選択を求める:

```
.udr/records/ に <N> 件の UDR レコードが存在します。
  (1) すべて削除（新規リポジトリとしてクリーンスタート）
  (2) すべて保持（コピー元の判断記録を引き継ぐ）
  (3) 個別に確認する（ファイル名と title を一覧表示し、1 件ずつ選択）

どれにしますか？
```

- **(1) 削除** の場合: `UDR-*.yaml` を全件削除し、`.gitkeep` を残す。Step 3 へ進む。
- **(2) 保持** / **(3) 個別確認（保持対象のみ残す）** の場合: 保持対象が確定したら Step 2.5-B へ進む。

#### 2.5-B. ファイル名・内容の repo_short 更新確認

保持対象のレコードに対して、以下を user に確認する:

```
保持する <M> 件のレコードのファイル名および YAML 内の id フィールドを
新しい repo_short (<new_repo_short>) に合わせて更新しますか？

現在のファイル名例: UDR-<old_repo_short>-20260423T1000-xxx.yaml
更新後のファイル名例: UDR-<new_repo_short>-20260423T1000-xxx.yaml

  (Y) 更新する（ファイル名 + YAML の id / relations 内 ID / summary_hint 内 ID をすべて置換）
  (N) 更新しない（古い repo_short のまま保持）
```

- **(Y) 更新する** 場合:
  1. 保持対象の各 YAML ファイルについて、`<old_repo_short>` → `<new_repo_short>` の文字列置換を行う対象フィールドを特定する:
     - `id` フィールド
     - `relations` 配下のすべての関係フィールド（`CONVENTIONS.md §6.1` に定義されている `depends_on` / `triggers` / `supersedes` およびそれらの各要素の `id` フィールド）内の ID
     - `summary_hint` 内の `[UDR-<old_repo_short>-...]` 形式の参照
     - `claude_summary` / `client_summary` フィールド内の ID 参照（存在する場合）
     - > **注意:** `CONVENTIONS.md §6.1` に定義されている関係フィールドが正式なリストである。スキーマ拡張時は `CONVENTIONS.md §6.1` を確認し、新たなフィールドをこのリストに含めること。
  2. 各ファイルの内容を更新する
  3. ファイル名を `UDR-<old_repo_short>-<ts>-<rand>.yaml` → `UDR-<new_repo_short>-<ts>-<rand>.yaml` にリネームする
  4. 更新・リネームしたファイルの一覧を user に提示して確認を取る
- **(N) 更新しない** 場合: 何もしない

### Step 2.6. ツールプロファイルの確認 (`tools`)

`config.yaml` 作成・更新の前に、このリポジトリで使う AI ツールを user に確認する。

```
このリポジトリで UDR を使う AI ツールを選んでください (複数可):
  [claude]  Claude Code     [codex]  Codex CLI       [gemini] Gemini CLI
  [copilot] GitHub Copilot  [cursor] Cursor           [windsurf] Windsurf
既定: claude
```

- 回答を `config.yaml` の `tools:` に反映する。`sync` の書き込み先はこの `tools` から導出される (CONVENTIONS §5.1)。
- **既存 `config.yaml` に `tools` がない場合** (旧スキーマからの移行): 既存の `sync.targets` / `sync.context_files` があればそれを尊重しつつ、対応するツールを推定して `tools:` を補完提案する (例: `CLAUDE.md`→claude, `AGENTS.md`→codex, `GEMINI.md`→gemini)。user 確認のうえ書き込む。
- 実行中のツールに関わらず、宣言した全ツールのファイルを sync で更新する点を user に伝える。

> **ツール別コンテキストファイルと操作テンプレートの対応:**
>
> | ツール | コンテキストファイル | 操作テンプレート | 備考 |
> |---|---|---|---|
> | `claude` | `CLAUDE.md` | `.claude/skills/udr-*/SKILL.md`（Claude Code が自動検出） | プラグイン版は `plugins/udr/` |
> | `codex` | `AGENTS.md` | `.codex/prompts/udr-*.md`（Step 3.4 で生成） | `~/.codex/prompts/` にコピーで slash command 化 |
> | `gemini` | `GEMINI.md` | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-*.md`（インストール済み） | GEMINI.md から `@path` で参照 |

#### Step 2.6.1. ツール変更の自動検知と調整 (drift reconciliation)

`config.yaml` に `tools` が既にある場合、**宣言値と実態の差分を検知して提案する**。これにより「使うツールを変えたら `/udr-init` を 1 回叩けば整う」状態にする。

**(a) 実行中エージェントの未宣言検知**

このスキルを実行しているエージェントは自分の種別を知っている (Claude Code / Codex CLI / GitHub Copilot CLI 等)。その種別が `config.tools` に**含まれていない**場合、user に提案する:

```
現在 <実行中ツール> で実行していますが、config.tools = [<現在値>] に含まれていません。
このツールを追加しますか？
  (Y) tools に <実行中ツール> を追加   (N) 追加しない
```

Y なら `tools` に追記し、以降の調整 (b)(c) と Step 3 を続行する。

**(b) 追加されたツール → 不足の生成**

`tools` の各値について、対応ファイル (CONVENTIONS §5.1) の状態を点検し、不足を補う:

| 検知 | 調整 |
|---|---|
| ターゲットファイルに `[UDR-SYNC]` ブロックが無い / ファイル自体が無い | Step 3.5 の sync で新規作成 |
| `codex` 宣言済みだが `.codex/prompts/udr-*.md` が無い | Step 3.4 を実行して生成 |

**(c) 削除されたツール → 残骸の検知 (除去は確認のうえ)**

`tools` に**含まれない**のに、ツール対応ファイルに UDR の痕跡が残っている場合は残骸として提示する:

| 検知 | 調整 (破壊的なので必ず user 確認) |
|---|---|
| 非宣言ツールのターゲットに `[UDR-SYNC-START]`〜`[UDR-SYNC-END]` ブロックが存在 | そのマーカー間の**ブロックのみ**削除を提案 (ファイル本体は残す) |
| `codex` 非宣言だが `.codex/prompts/udr-*.md` が存在 | 削除を提案 |

```
config.tools = [claude, codex] に含まれないツールの痕跡が見つかりました:
  - .github/copilot-instructions.md の UDR-SYNC ブロック (copilot 用)
これらを除去しますか？  (Y) 除去 / (N) 残す
```

**(d) 差分が無ければ** 何も提案せず通常の冪等初期化を続ける。検知・調整した内容は Step 3 完了時に user へまとめて報告する。

### Step 2.7. Hook 機能の有効化確認（Claude Code プラグイン版限定、任意）

`tools` に `claude` が含まれる場合のみ確認する。含まれない場合は本ステップをスキップし `hooks.enabled` を書き込まない（省略ルール PO2-02 と同様、未確認の項目はキー自体を書かない）。

```
Claude Code hook（plugins/udr/hooks/）を有効にしますか？

  git commit 前に「非自明な判断があれば /udr-record で記録を」とリマインドし、
  セッション開始時に判断待ち draft・AI 単独 proposed の件数を briefing します。

  ⚠ 要 python3（PATH 上にあること）。python3 が無い環境では、有効にしても
    hook は自動的に何もしません（エラーにはなりません）。
  ⚠ 手動配置（dist/ 経由のインストール）には hook 自体が含まれないため、
    このプロジェクトが Claude Code プラグイン版でない場合は無効のままで構いません。

  (Y) 有効にする   (N) 無効のまま（既定・推奨、python3 不要で確実に動く）
```

- **(Y)**: `config.yaml` に `hooks: { enabled: true }` を書き込む
- **(N)** または未確認: `config.yaml` に `hooks: { enabled: false }` を書き込む（**既定値**）。既存 `config.yaml` に `hooks` キーが無い場合も `false` 相当として扱われる（省略時のデフォルトは無効）

> hook 自体（`plugins/udr/hooks/hooks.json`）は python3 の有無を実行時に自己チェックし、無い場合は何も出力せず正常終了する（`command -v python3` による安全側フォールバック）。この設定は「python3 はあるが hook のリマインドを望まない」場合の明示的な opt-out、および「python3 が無い環境でも安心して Y/N を選べる」ことを目的とする。

### Step 3. 生成／追記

#### `.udr/config.yaml`

- **新規作成時（[A]）**: 以下のテンプレートで新規作成する。`repo_short` には `new_repo_short` を使用する
- **`repo_short` 更新時（[C] で Y/M を選択）**: `repo_short` の値を `new_repo_short` に更新する。他のキーは既存値を保持し、不足キーのみ追加する
- **通常の冪等初期化時（[B]）**: 不足キーのみ追加する（既存値は一切変更しない）

```yaml
# UDR プロジェクト設定 (Phase 1 PoC)
schema_version: "0.1"
repo_short: <決定値>

# ai-agent 判定パターン (BR-002)
ai_agent_patterns:
  - "^claude-code$"
  - "^claude-opus.*"
  - "^claude-sonnet.*"
  - "^claude-haiku.*"
  - "^gpt-.*"
  - "^copilot.*"
  - "^cursor.*"
  - ".*-ai-agent$"

# 対象 AI ツール (CONVENTIONS §5.1)。init 時に user に確認する (Step 2.6)。
# sync の書き込み先はこの tools から導出される (実行中ツールでは分岐しない):
#   claude  -> CLAUDE.md  (policy+compact)
#   codex   -> AGENTS.md  (policy+compact)  ※ 操作テンプレートは .codex/prompts/
#   gemini  -> GEMINI.md  (policy+compact)  ※ 操作テンプレートは .claude/skills/_udr-shared/templates/gemini-prompts/
#   copilot -> .github/copilot-instructions.md (policy-only)
#            + .github/instructions/udr-decisions.instructions.md (detailed)
#   cursor  -> .cursorrules (compact) / windsurf -> .windsurfrules (compact)
tools:
  - claude

# 同期設定 (FR-008)。targets は通常 tools から自動導出されるため省略する。
# 明示的に上書きしたい場合のみ targets を列挙する (tools より優先)。
sync:
  # targets:                     # 省略時は tools から導出 (CONVENTIONS §5.1)
  #   - path: "CLAUDE.md"
  #     format: "policy+compact"
  token_budget: 1200
  pinned_max: 5
  auto_max: 15

# 書き込み許可パス (NFR-009 パストラバーサル防止)
# tools で実際に使うものに限定してよい。生成物 (udr_dashboard.html) も許可に含める。
allowed_sync_paths:
  - "CLAUDE.md"
  - "AGENTS.md"
  - "GEMINI.md"
  - ".github/copilot-instructions.md"
  - ".github/instructions/**.md"
  - ".cursorrules"
  - ".windsurfrules"
  - "udr_dashboard.html"

# スコアリング重み (FR-002 / 同期選択)
scoring:
  severity: { high: 3, medium: 2, low: 1 }
  recency_30d: 2
  recency_90d: 1
  trigger_weight: 0.5
  trigger_cap: 2
  status_penalty: { deprecated: 2, superseded: 5, rejected: 5 }

# レビュー閾値 (FR-013)
review:
  orphan_age_days: 30
  ai_pending_days: 7

# Claude Code hook 設定 (marketplace 配布限定、Step 2.7 で確認)。
# python3 が無い環境でも安全（hook 側が command -v python3 で自己チェックし無害化する）。
# tools に claude を含まない場合は本キー自体を省略する。
hooks:
  enabled: false
```

#### `.udr/records/.gitkeep`

空ファイル。ディレクトリを Git に残す。

#### `.gitignore` に以下を追加（既存行は触らない）

```
# UDR (Phase 1 PoC)
.udr/index.json
.udr/audit.log
.udr/audit.log.*
```

既に `.udr/` 全体が ignore されていたら警告（records/ も除外されてしまう）。

#### `.udr/audit.log` を空で作成

### Step 3.4. Codex CLI プロンプトファイルの生成（`tools` に `codex` がある場合のみ）

> `config.yaml` の `tools:` に `codex` が含まれないときは本ステップを丸ごとスキップする（Codex を使わない repo に `.codex/` を作らない）。

`.claude/skills/_udr-shared/templates/codex-prompts/udr-*.md` を `.codex/prompts/` にコピーする。これにより、Codex CLI ユーザーは `cp .codex/prompts/udr-*.md ~/.codex/prompts/` の 1 コマンドで `/udr-init` 等のスラッシュコマンドが使えるようになる。

| 状況 | 動作 |
|---|---|
| `.codex/prompts/udr-<name>.md` が存在しない | テンプレートをそのままコピー |
| 既存ファイルあり、内容がテンプレートと一致 | 何もしない (冪等) |
| 既存ファイルあり、内容差分あり | user に diff を提示し、上書き / 保持 / 個別ファイル選択 を尋ねる |

テンプレート源が見つからない場合 (`.claude/skills/_udr-shared/templates/codex-prompts/` がない) は警告を出し、Codex CLI 連携は手動セットアップが必要である旨を user に伝えて続行する (UDR-INIT-005)。

### Step 3.5. sync ターゲットへの UDR 情報書き込み

書き込み先は **`tools` から導出**する（CONVENTIONS §5.1 / `/udr-sync` Step 0）: `sync.targets` が明示されていればそれ、なければ `tools:` を対応表で展開した和集合、どちらもなければ `[claude]`（`CLAUDE.md` のみ）。導出した**すべてのターゲットファイル**に対し UDR 情報を書き込む（または最新化する）。これは新規作成・`repo_short` 更新・通常の冪等初期化のいずれの場合にも実行する。**実行中のツールでは分岐しない**（宣言された全ツールのファイルを更新）。

具体的には `/udr-sync` skill の処理フローを実行する。各ターゲットファイルの状態に応じて以下の 3 つの動作を行う:

| ターゲットファイルの状態 | 動作 |
|---|---|
| **ファイルなし** | 新規作成し、UDR サマリを `[UDR-SYNC-START]`〜`[UDR-SYNC-END]` マーカー内に書き込む |
| **ファイルあり、UDR サマリなし**（マーカー不在） | ファイル末尾に UDR サマリとマーカーを追記する |
| **ファイルあり、UDR サマリあり**（マーカー存在） | `[UDR-SYNC-START]`〜`[UDR-SYNC-END]` 間を最新のサマリで置換する |

処理後、各ターゲットファイルへの書き込み結果（更新件数・差分・適用したケース）を user に提示する。

**sync 失敗時の扱い:**
- 対象ファイルが書き込み不可（パーミッションエラー等）の場合: エラーを user に報告し、**そのファイルをスキップして続行する**（初期化全体はアボートしない）
- `/udr-sync` の処理自体が失敗した場合: エラー内容を報告し、「`/udr-sync` を手動で後から実行してください」と案内する
- すべてのターゲットファイルで sync が失敗した場合も、`config.yaml` と `records/` の更新は確定している旨を伝える

> **備考:** Step 2.5 でレコードを削除した場合（クリーンスタート）、sync 後のターゲットファイルには「レコード 0 件」のマーカーが書き込まれる。

### Step 3.6. その他の確認事項（`repo_short` を更新した場合のみ）

以下の項目について user に確認し、必要に応じて対応する:

```
repo_short の更新後の確認事項:

1. AGENTS.md / CLAUDE.md のプロジェクト概要記述が旧リポジトリのまま残っていませんか？
   → 新しいリポジトリの内容に合わせて手動で更新することを推奨します。

2. .udr/records/ 内の UDR の context・decision 内容が旧リポジトリ固有のものではありませんか？
   → 引き継ぎ不要な判断記録は /udr-record で supersede するか削除することを検討してください。

3. config.yaml の sync_targets に現リポジトリに存在しないファイルが含まれていませんか？
   → 不要なターゲットは config.yaml から削除してください。

他に対応が必要そうな点があれば教えてください。
```

### Step 4. 初期化結果の記録

`audit.log` に 1 行追記:

```json
{"ts":"<UTC ISO>","actor":"<user>","role":"human","op":"init","id":null,"changed_fields":["schema_version","repo_short"]}
```

`repo_short` を更新した場合（[A] または [C] で Y/M を選択）は `"changed_fields":["repo_short"]` とする。

### Step 5. user への報告

生成・追記したファイルの一覧と、既に存在したため触らなかったファイルの一覧を提示する。

`repo_short` を更新した場合は追加で以下を含める:
- 旧 `repo_short` → 新 `repo_short` の変更内容
- 削除したレコード数（削除した場合）
- リネーム・更新したレコード数（更新した場合）
- sync_targets への書き込み結果サマリ（各ファイルに適用したケース: 新規作成 / 追記 / 更新）

## エラーハンドリング

| エラーコード | 条件 | メッセージ |
|---|---|---|
| UDR-INIT-001 | カレントが Git リポジトリでない | `Git リポジトリ配下で実行してください。UDR は Git 永続を前提とします (C-003)。` |
| UDR-INIT-002 | `.gitignore` で `.udr/` 全体が除外済 | `.udr/records/ が Git 管理外になっています。判断記録の不滅性 (BR-001) が担保できないため、.gitignore の .udr/ エントリを .udr/index.json と .udr/audit.log に絞ってください。` |
| UDR-INIT-003 | `schema_version` が未知 | `未対応の schema_version です (<version>)。Phase 1 PoC は 0.1 のみサポートします。` |
| UDR-INIT-004 | Step 2.5-B の ID 置換で relations 内の外部リポジトリ参照が検出された | 外部リポジトリ参照の判定基準: `relations` 配下の `id` フィールドが `UDR-<old_repo_short>-` で始まらない場合（例: `UDR-atelier-...` のように `old_repo_short` と異なる prefix を持つ）は外部参照と見なす。まず `.udr/records/` 内のファイル名一覧と照合し、存在するファイルは内部参照（外部リポジトリ参照ではない）と判断する。存在しないファイルかつ prefix が `old_repo_short` でない場合に本エラーを発行する。メッセージ: `relations 内に外部リポジトリへの参照 (<id>) が含まれています。この ID はコピー元外のリポジトリを指している可能性があります。(Y) 置換せずに保持する / (N) 新 repo_short で上書きする`。**(Y) 保持** の場合はその ID をそのまま残す。**(N) 上書き** の場合は他の ID と同様に `<old_repo_short>` → `<new_repo_short>` に置換する。どちらも処理を続行する（ブロックしない）。 |
| UDR-INIT-005 | Step 3.4 で Codex プロンプトテンプレート源が見つからない | `.claude/skills/_udr-shared/templates/codex-prompts/` ディレクトリが存在しない場合に警告を出す。メッセージ: `Codex CLI プロンプトテンプレートが見つかりません (.claude/skills/_udr-shared/templates/codex-prompts/)。Codex CLI を使う場合は手動で .codex/prompts/ をセットアップしてください。スキル本体 (.claude/skills/udr-*/SKILL.md) のみで運用する場合は無視可。`。処理は続行する（ブロックしない）。 |

## 完了条件

- `.udr/records/` が存在し Git 管理対象
- `.udr/config.yaml` が存在し、現リポジトリの `repo_short` / `schema_version` を持つ
- `.gitignore` に `.udr/index.json` と `.udr/audit.log` が含まれる
- `audit.log` に init 操作が記録されている
- `.codex/prompts/udr-*.md` (6 ファイル) が生成済み (テンプレート源があった場合)
- `sync_targets` の各ファイルに最新の UDR policy + サマリが書き込まれている (`policy+compact` / `policy-only` / `detailed` のいずれか)、policy セクションには **スラッシュコマンド一覧 / エージェント別動作経路 / Codex CLI 初回セットアップ / SKILL.md 参照パス** が含まれていること
