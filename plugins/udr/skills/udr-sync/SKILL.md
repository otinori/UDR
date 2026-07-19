---
name: udr-sync
description: UDR の要約を CLAUDE.md / copilot-instructions.md / instructions/udr-decisions.instructions.md / .cursorrules / AGENTS.md の SYNC マーカー間に安全に書き込む。pinned(5) + auto(15, スコア順) のハイブリッド、budget 1200 トークン、atomic write、差分 (added/removed/updated) を返却する (FR-008/FR-009/NFR-007/NFR-009)。
---

# udr-sync — コンテキスト同期 skill

> **前提:** `.claude/skills/_udr-shared/CONVENTIONS.md` を先読み。

## なぜ必要か

AI のコンテキスト圧縮・セッション切れで判断が蒸発する。sync は UDR をコンテキストファイルに常駐させて **棄却案の再提案を防ぐ** (KPI: AIの棄却済み案再提案率 50%削減)。

## 処理フロー

### Step 0. 対象ターゲットの決定 (`tools` プロファイル / CONVENTIONS §5.1)

書き込み先ファイルは **`config.yaml` から決まり、実行中のツールでは分岐しない**:

1. `config.yaml` に `sync.targets`（または `sync_targets`）が明示されていれば、それを使う。
2. なければ `config.yaml` の `tools:` を CONVENTIONS §5.1 の対応表で展開した和集合を使う。
3. どちらもなければ `[claude]`（`CLAUDE.md` のみ）。

決定したターゲット集合を、いまどのツール（Claude / Codex 等）で実行していても**毎回すべて**更新する。`--target <path>` 指定時はその 1 ファイルのみに限定する。

**ツールドリフトの警告 (検知のみ・sync は続行):** 次のいずれかを検知したら警告を出し、`/udr-init` での調整を促す（sync 自体は宣言ターゲットに対して実行する）:

- このスキルを実行しているエージェントの種別が `config.tools` に**含まれていない**（例: Codex で実行中だが `tools: [claude]`）。
- 導出ターゲット**以外**のファイルに `[UDR-SYNC-START]`〜`[UDR-SYNC-END]` ブロックが残っている（過去に使い、今は宣言から外したツールの残骸）。

```
⚠ ツール構成のずれを検知しました:
  - 現在 <実行中ツール> で実行中ですが config.tools に未宣言
  - <path> に未宣言ツール向けの UDR-SYNC ブロックが残存
  → `/udr-init` で tools を更新・調整してください。
```

### Step 1. 対象選定 (AD-02)

1. `.udr/records/*.yaml` を Glob → メタを Read
2. **除外:** `status in (superseded, rejected, draft)` — draft は未完成のため同期しない
3. **pinned:**
   - `pinned: true` を全件取得 (max 5)
   - 6 件以上なら警告し、`updated` 降順で上位 5 件に絞る
4. **auto:**
   - 残りを `CONVENTIONS.md §5.3` のスコア式で降順ソート
   - 推定トークン合算が `config.sync.token_budget` (デフォルト 1200) に達するまで追加 (max 15)
5. **推定トークン:** 簡易近似 `ceil(summary 文字数 / 2)` で十分 (Phase 1 PoC)

### Step 2. サマリ選択 (FR-009 Step 3)

各 UDR につき優先度:

```
claude_summary (人間/AI 手書き)  ──優先度1──▶ あれば採用
client_summary (クライアント LLM)──優先度2──▶ なければ次へ
summary_hint   (テンプレート生成)──優先度3──▶ フォールバック
```

### Step 3. 出力文字列組み立て

#### CLAUDE.md / AGENTS.md / GEMINI.md (policy+compact、複数エージェント横断ポリシー込み)

`policy+compact` 形式は、UDR をエージェント横断で運用するための **判断記録プロトコル (policy)** と **アクティブ判断のコンパクト要約** をマーカー間にまとめて書く。
- `CLAUDE.md` は Claude Code が読み、
- `AGENTS.md` は Codex CLI 等（AGENTS.md を自動読み込みするすべてのエージェント）が読み、
- `GEMINI.md` は Gemini CLI が読む。

内容は同一テンプレートを使う（ファイル間の差分は冒頭の見出しのみ）。

```markdown
<!-- [UDR-SYNC-START] -->
## UDR — 判断記録プロトコル (synced <UTC ISO>, <N>件中<M>件表示)

このプロジェクトでは、設計・要件・技術選定などの **非自明な判断** を UDR (Universal Decision Record) として `.udr/records/` 配下に YAML で記録します。Claude Code / Codex CLI / Gemini CLI / GitHub Copilot のいずれの環境でも、本プロトコルを厳守してください。

### スラッシュコマンド一覧

| コマンド | 役割 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI |
|---|---|:-:|:-:|:-:|:-:|
| `/udr-init` | プロジェクト初期化 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-record` | 判断の対話的記録 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-search <q>` | UDR 検索 (ID/フィルタ/全文) | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-sync` | コンテキストファイル同期 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-trace <id>` | DAG 走査・影響分析 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-review` | 品質棚卸し (9 観点) | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-dashboard` | 判断状況を HTML 出力 (udr_dashboard.html) | ✓ | ✓ | テンプレート参照 | ✓ |

> Gemini CLI は skill の直接呼び出しを持たない。`@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` のようにテンプレートをファイル参照して実行する。
> GitHub Copilot Chat (IDE 内) は slash command 不可。policy のみ反映され、判断記録時は user に CLI への切替か手動 YAML 作成を提案する。

### エージェント別の動作経路

- **Claude Code**: 配置方法は 2 通り。(1) project 配置 = `.claude/skills/udr-*/SKILL.md` を自動検出し `/udr-record` で使う。(2) **プラグイン版** = `claude plugin install udr@udr-marketplace` で導入し `/udr:udr-record` で使う。どちらも `.udr/` を同じように読み書きする
- **Gemini CLI**: `GEMINI.md` をプロジェクトルートから自動読み込み（コンテキストファイル）。操作テンプレートは `.claude/skills/_udr-shared/templates/gemini-prompts/` に配置済み。`@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` のように参照して使う。`.gemini/extensions/udr/` の拡張マニフェストでシステムプロンプトを自動注入
- **GitHub Copilot CLI**: 独自の plugin marketplace を持つ（`.claude/skills/` は自動検出**しない**）。`copilot plugin marketplace add <source>` → `copilot plugin install udr@udr-marketplace`（同じ `.claude-plugin/marketplace.json` を読む。`copilot plugin install <owner>/UDR:plugins/udr` でも可）。呼び出しは **`/udr-record` 等（slash・名前空間なし）**。MCP / AGENTS.md も読む
- **Codex CLI**: 2 通り。(1) **ネイティブ plugin**（推奨, Codex 0.139+）= `codex plugin marketplace add <source>` → `codex plugin add udr@udr-marketplace`（Claude と同じ `.claude-plugin/marketplace.json` を読む）。呼び出しは **skill 扱いで `$udr:udr-init`**（`$` + `udr:` 名前空間。`/skills` で一覧）。(2) `.codex/prompts/udr-*.md` を `~/.codex/prompts/` にコピー → ファイル名の slash command `/udr-init`。**注意: Codex の `/...` は組み込みコマンド（`/skills` `/plugins` 等）、skill 明示呼び出しは `$...`**（下記セットアップ参照）
- **GitHub Copilot Chat (IDE)**: slash command 不可。user に skill 手順の手動実行か、CLI 環境への切替を提案する

### Gemini CLI 初回セットアップ (一度だけ)

`tools` に `gemini` を宣言してから `/udr-init` を実行すると `GEMINI.md` が生成される。その後 Gemini CLI はプロジェクトを開くと自動的に `GEMINI.md` を読む。

拡張マニフェストを有効にする場合（システムプロンプト自動注入）:

```bash
# .gemini/ が install 済みであれば何もしない
ls .gemini/extensions/udr/gemini-extension.json 2>/dev/null || \
  echo "install.sh --gemini を実行して生成してください"
```

操作テンプレートはスキルインストール後から使える（追加コピー不要）:

```
# Gemini CLI での UDR 記録例
@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md
判断を記録してください: ...
```

### Codex CLI 初回セットアップ (一度だけ)

**方法 A（推奨・ネイティブ plugin / Codex 0.139+）** — Claude と同じマーケットプレイスをそのまま使える。`add` でインストール（`install` ではない）:

```bash
codex plugin marketplace add otinori/UDR   # local path / git URL も可
codex plugin add udr@udr-marketplace
codex plugin list                                # 確認
```

**方法 B（プロンプトコピー / フォールバック）** — plugin 機構を使わない場合:

```bash
mkdir -p ~/.codex/prompts && cp .codex/prompts/udr-*.md ~/.codex/prompts/
```

```powershell
$dst = "$env:USERPROFILE\.codex\prompts"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Copy-Item .codex\prompts\udr-*.md $dst -Force
```

呼び出し方は方式で異なる:
- **方法 A（plugin）**: skill 扱いなので **`$udr:udr-init`**（`$` + plugin 名前空間 `udr:`）。`/skills` で一覧から選択も可。
- **方法 B（プロンプトコピー）**: ファイル名がそのまま slash command → **`/udr-init`**。

> Codex の `/...` は組み込みコマンド（`/skills` `/plugins` `/status` `/model` 等）。**plugin 由来 skill の明示呼び出しは `$...`** と覚える。

### GitHub Copilot CLI 初回セットアップ (一度だけ)

Copilot CLI（1.0+）も独自の plugin marketplace を持ち、同じ `.claude-plugin/marketplace.json` を読む。`install` でインストール:

```bash
copilot plugin marketplace add otinori/UDR   # local path / URL も可
copilot plugin install udr@udr-marketplace         # または: copilot plugin install otinori/UDR:plugins/udr
copilot plugin list
```

呼び出しは **slash・名前空間なしで `/udr-init`**（Claude plugin の `/udr:`、Codex plugin の `$udr:` とは異なる）。`.claude/skills/` の自動検出は**しない**点に注意（必ず plugin 導入が必要）。

### あなた (AI エージェント) が判断を行う／検出した場合

- **Claude Code**: `/udr-record` を呼ぶ／user に提案する (project 配置の `.claude/skills/` を自動検出。plugin 版は `/udr:udr-record`)
- **GitHub Copilot CLI**: plugin 導入済みなら `/udr-record` を呼ぶ／提案する (未導入なら `copilot plugin install udr@udr-marketplace` を案内)
- **Codex CLI / その他の自律エージェント**: `/udr-record` (`.codex/prompts/` 経由) または `.claude/skills/udr-record/SKILL.md` を直接読み、Phase A (必須3項目: title+decision / context+rationale / 棄却選択肢+理由) → Phase B (任意3項目) → Phase C (メタ確定) の対話フローに従って `.udr/records/UDR-<repo_short>-<UTC YYYYMMDDTHHmm>-<rand3>.yaml` を作成する
- **GitHub Copilot Chat (IDE)**: 自身では能動的に YAML 作成はできないため、user に判断記録を提案する
- **必須**: 棄却した代替案とその理由を必ず記録する (UDR の核心 / BR-007 / FR-015)
- AI 単独 (authors が ai-agent のみ) の判断は `status: proposed` 強制 (BR-002)
- スキーマ・ID 体系・status 遷移は `.claude/skills/_udr-shared/CONVENTIONS.md` 参照

### コードを変更する前に

- 関連過去判断を確認: Claude Code/Codex は `/udr-search <keyword>`、それ以外は `.udr/records/*.yaml` を grep
- `verdict: rejected` の選択肢を **再提案しない** (sync で配信される過去判断を必ず参照)

### 矛盾しそうな変更

- Claude Code/Codex は `/udr-trace <id>` で影響分析、それ以外は YAML の `relations.depends_on` / `triggers` / `supersedes` を手動追跡

### スキル本体の場所 (詳細手順を読みたいとき)

> パスは **project 配置** (`.claude/skills/`) の場合。**プラグイン版**で導入したときは各 skill はプラグイン配下に置かれ (`/plugin` で管理)、呼び出しは `/udr:udr-*`。ファイルパスは異なるが内容と使い方は同じ。

- 共通規約: `.claude/skills/_udr-shared/CONVENTIONS.md`
- 各 skill: `.claude/skills/udr-{init,record,search,sync,trace,review,dashboard}/SKILL.md`
- Codex プロンプト: `.codex/prompts/udr-*.md`

---

## Active Decisions (<N> records)

### Pinned
- **<id>** [<domain[:3]>] <title>
  <選択したサマリの 1-2 行>

### Recent (score 降順)
- **<id>** [<domain[:3]>] <title>
  <選択したサマリの 1-2 行>

<!-- [UDR-SYNC-END] -->
```

レコード 0 件のときも policy セクションは書く (各エージェントに UDR 運用を周知するため)。Active Decisions セクションには「判断記録はまだありません」と記す。

#### CLAUDE.md / .cursorrules / .windsurfrules (compact、policy なし)

policy を別ファイル (AGENTS.md など) で集中管理したい場合のオプション。デフォルトでは CLAUDE.md は policy+compact を使う。

```markdown
<!-- [UDR-SYNC-START] -->
## UDR — Active Decisions (<N> records, synced <UTC ISO>)

### Pinned
- **<id>** [<domain[:3]>] <title>
  <選択したサマリの 1-2 行>

### Recent (score 降順)
- **<id>** [<domain[:3]>] <title>
  <選択したサマリの 1-2 行>

<!-- [UDR-SYNC-END] -->
```

#### `.github/instructions/udr-decisions.instructions.md` (detailed, YAML front matter 付き)

```markdown
---
applyTo: "**/*"
---

<!-- [UDR-SYNC-START] -->
# Active UDR Decisions (<N> records, synced <UTC ISO>)

## Pinned（常に考慮すべき判断）
- **<id>** [<domain>] <title>
  決定: <decision の 1 行>
  棄却: <rejected[0].name> (<20 字理由>), <rejected[1].name> ...

## Auto（スコア順）
- ...
<!-- [UDR-SYNC-END] -->
```

#### `.github/copilot-instructions.md` (policy-only、要約本体は書かない)

配置される行動指示テンプレート（既存ファイルには SYNC マーカー間だけ入れる）:

```markdown
<!-- [UDR-SYNC-START] -->
## UDR — 判断記録ポリシー (synced <UTC ISO>)

このプロジェクトは判断記録に UDR (Universal Decision Record) を使用しています。

### スラッシュコマンド (Claude Code / Codex CLI / GitHub Copilot CLI)

| コマンド | 役割 |
|---|---|
| `/udr-init` | プロジェクト初期化 |
| `/udr-record` | 判断の対話的記録 (棄却理由の併記が必須) |
| `/udr-search <q>` | UDR 検索 |
| `/udr-sync` | コンテキストファイル同期 |
| `/udr-trace <id>` | 依存関係 DAG 走査・影響分析 |
| `/udr-review` | 品質棚卸し |
| `/udr-dashboard` | 判断状況を HTML 出力 (udr_dashboard.html) |

> **Copilot CLI** は独自の plugin marketplace を持ちます（`.claude/skills/` は自動検出しません）。`copilot plugin marketplace add <source>` → `copilot plugin install udr@udr-marketplace` で導入すると上記 slash command が使えます。
> **Codex CLI** は `cp .codex/prompts/udr-*.md ~/.codex/prompts/` を一度実行すれば slash command が使えます。

GitHub Copilot Chat (IDE 内) 自身ではスラッシュコマンドを実行できません。判断記録が必要な場面では:

- user に `/udr-record` の実行 (Claude Code / Codex CLI / Copilot CLI のいずれかの環境) を提案する
- user 環境が IDE Chat のみの場合は `.claude/skills/udr-record/SKILL.md` の手順を提示し、`.udr/records/` 配下への YAML 作成を案内する

### 参照ファイル

- アクティブ判断の要約: `.github/instructions/udr-decisions.instructions.md`
- 判断スキーマ・ID 体系・status 遷移: `.claude/skills/_udr-shared/CONVENTIONS.md`
- 各 skill 詳細: `.claude/skills/udr-{init,record,search,sync,trace,review,dashboard}/SKILL.md` (project 配置の場合。プラグイン版では各 skill はプラグイン配下、呼び出しは `/udr:udr-*`)
- Codex プロンプト: `.codex/prompts/udr-*.md` (`~/.codex/prompts/` への 1 回コピーで有効化)

### 必須ルール

- コード変更前に `/udr-search <keyword>` または `.udr/records/*.yaml` の grep で関連判断を確認
- `verdict: rejected` の選択肢を **再提案しない**
- 矛盾しそうな変更は `/udr-trace <id>` または `relations:` フィールドの手動追跡で影響分析
- AI 単独 (authors が ai-agent のみ) の判断は `status: proposed` 強制 (BR-002)
<!-- [UDR-SYNC-END] -->
```

#### `AGENTS.md` (Codex CLI 等のエージェント向け、policy+compact)

CLAUDE.md と同じ `policy+compact` 形式を使う。Codex CLI は AGENTS.md を主要なプロジェクト指示として読み込むため、policy だけでなく Active Decisions の要約も同梱する。

### Step 4. パス許可チェック (NFR-009 パストラバーサル防止)

各ターゲットパスについて:

1. `config.yaml` の `allowed_sync_paths` グロブと照合
2. `..` を含む / 絶対パス化して project root 外 → エラー `UDR-SYNC-009`

### Step 5. atomic write (FR-008 / NFR-009 AR2-02)

1. 既存ファイル内容を読み込み（なければ新規扱い）
2. **前回サマリ抽出:** `[UDR-SYNC-START]` ～ `[UDR-SYNC-END]` 間の ID 集合を取得 → 差分計算用
3. 新サマリで マーカー間を置換（マーカー不在なら末尾追記、ファイル不在なら新規作成）
4. **書き込み手順:**
   - `<path>.bak` に現在内容をコピー (backup)
   - `<path>.tmp` に新内容を書き込み
   - `<path>.tmp` を `<path>` にリネーム
   - 成功したら `<path>.bak` を削除
5. **Windows NTFS で rename 失敗時:** `.bak` から復元して `UDR-SYNC-010` エラー (AR2-02)

Phase 1 PoC では Claude が Read → Write で 3/4/5 を模倣する。Write は上書きなので先に Read → 内容組み立て → Write の順で、失敗時は手動復元を案内。

### Step 6. 差分計算 (UX-03)

```
prev_ids = 前回 SYNC マーカー間にあった ID 集合
new_ids  = 今回書き込む ID 集合

added    = new - prev
removed  = prev - new
updated  = new ∩ prev のうち、サマリ文字列が変わったもの
```

### Step 7. audit.log 追記

```json
{"ts":"<UTC ISO>","actor":"<name>","role":"<role>","op":"sync","id":null,
 "targets":["CLAUDE.md",".github/..."],"record_count":<N>,"diff":{"added":<a>,"removed":<r>,"updated":<u>}}
```

### Step 7.5. 陳腐化チェック

sync 完了直前に、**前回 sync からの経過日数**を計算する:

1. 各ターゲットファイルの `[UDR-SYNC-START]` 直後の `synced <UTC ISO>` タイムスタンプを読む
2. 現在 UTC との差分を算出
3. `config.sync.stale_warn_days`（デフォルト 7）を超えていれば警告フラグを立てる

### Step 8. user への報告

```
sync 完了 (2026-06-21T10:30:00Z)

  target                                                    records  tokens(推定)
  ─────────────────────────────────────────────────────────
  CLAUDE.md                                                 20 件    ~980
  .github/copilot-instructions.md                           (policy)   -
  .github/instructions/udr-decisions.instructions.md        20 件   ~1180

差分:
  + added:    UDR-xxx, UDR-yyy
  - removed:  UDR-zzz (supersede されたため除外)
  * updated:  UDR-www (サマリ変更)

警告: なし
```

陳腐化警告（前回 sync から 7 日以上経過している場合に追加表示）:

```
⚠ 陳腐化警告: CLAUDE.md の最終 sync から 14 日経過 (前回: 2026-06-07)
  この間に追加・更新された UDR が同期されていない可能性があります。
  → /udr-sync を定期実行するか、CI に組み込むことを推奨します。
```

## エラーコード

| Code | 条件 |
|---|---|
| UDR-SYNC-001 | `.udr/` 未初期化 |
| UDR-SYNC-005 | pinned が 6 件以上 (警告、処理続行) |
| UDR-SYNC-008 | token_budget 超過で auto 切り捨て発生 (情報) |
| UDR-SYNC-009 | 許可されていないパスへの書き込み要求 |
| UDR-SYNC-010 | rename 失敗 (Windows) → `.bak` からの復元が必要 |
| UDR-SYNC-011 | 同期対象 UDR が 0 件のときの挙動を形式別・前回状態別に分岐する: <br>**`policy+compact` / `policy-only` 形式**: 常に書き込み (policy セクション必須、Active Decisions セクションは「判断記録はまだありません」プレースホルダ) <br>**`compact` / `detailed` 形式 (前回 sync ID 数 = 0、またはマーカー不在、またはファイル不在)**: 「判断記録はまだありません」プレースホルダ付きで書き込み (新規リポの初期セットアップで必要) <br>**`compact` / `detailed` 形式 (前回 sync ID 数 ≥ 1)**: 何もしない (ファイル破壊防止 — 既存の Active Decisions を 0 件で上書きしない) |

## オプション

- `--target <path>`: 特定ターゲットのみ同期
- `--dry-run`: 書き込まずに差分だけ表示
- `--force`: マーカー不在時でも末尾追記ではなく全体を置換（危険、確認必須）

## 関連 skill

- `/udr-record` 実行後の自動 sync 提案
- `/udr-review` の結果に応じた `/udr-sync` の再実行（supersede 発生時など）
