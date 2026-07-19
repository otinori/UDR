---
name: "UDR (Universal Decision Record)"
description: "開発中に発生した判断をYAML形式で構造的に記録し、AIコンテキストファイルへ自動同期する意思決定記録基盤。"
background: "AIネイティブ開発では「なぜその判断をしたか」という経緯が会話の中に埋もれて失われやすい。この経緯をAIが読めるYAML台帳として残し、後から追跡・活用できるようにするために作った。"
version: "0.6.0.2-PoC"
nature: "experiment"
status: "active"
goal: "判断とその棄却理由をDAGで追跡可能な形で記録し、AIコンテキストファイルへの自動同期を維持できる状態を実現する。"
target_audience: "AIエージェント（Claude Code / Gemini CLI / Codex CLI / GitHub Copilot 等）を使って開発するエンジニア"
architecture: "Phase 1 PoC（プロンプトレベル実装 / Claude Code skills）"
language: ["Markdown", "YAML", "Python", "Shell"]
license: "MIT"
last_updated: 2026-07-20
---

# UDR — Universal Decision Record

> ⚠️ **これは実験的プロジェクトです。** Phase 1 PoC（プロンプトレベル実装）段階であり、スキーマ・コマンド体系・配布方式は今後の利用状況次第で破壊的に変更される可能性があります。本番の意思決定記録基盤として重要データを預ける前に、この点をご理解のうえでお試しください。

開発中に発生した判断（アーキテクチャ選定・要件解釈・技術選定など）を **YAML 形式で構造的に記録**し、**AI コンテキストファイル（CLAUDE.md / copilot-instructions.md 等）へ自動同期**するための仕組み。

AI ネイティブ開発において「なぜそう決めたか」を失わないための、AI 可読な意思決定台帳です。

---

## UDRって何？（専門用語なしの説明）

- ソフトウェア開発では「なぜこの設計にしたか」「なぜこのライブラリを選んだか」といった判断を、後から見返せる形で残しておきたい場面がよくあります。UDR（Universal Decision Record、直訳すると「汎用・意思決定記録」）は、そうした判断を **YAML というテキスト形式の台帳**に書き残しておく仕組みです。
- 台帳といっても手作業の記帳ではなく、**Claude Code や Gemini CLI のようなAIエージェント（人間の指示を受けて自律的にファイル操作やコード編集を行うAIツール）**が対話の中で判断を検知し、記録・検索・同期までを手伝ってくれます。
- 記録した判断は自動で `CLAUDE.md`（AIがセッション開始時に読み込む案内書のようなファイル）などに要約が反映されるため、後から別のAIエージェントが同じプロジェクトを触るときも、過去の判断の経緯を踏まえて作業できます。
- 「採用した案」だけでなく「検討したが採用しなかった案とその理由」も必ず記録するのが特徴で、これにより「なぜ別のやり方にしなかったのか」を後から再確認できます。

---

> **Project Goal:**
> 判断とその棄却理由を DAG（有向非巡回グラフ、判断同士のつながりを木構造のように辿れる形）として追跡可能にし、AI コンテキストファイルへの自動同期を維持できる状態を実現する。

---

## 既存 ADR との差別化

10 種以上の既存 ADR ツール（MADR 4.0, adr-tools, Log4brains, Structurizr 等）調査の結果、UDR は以下の 5 点で差別化されます。

| マーカー | 特徴 | 既存 ADR の限界 |
|:--:|---|---|
| **[D-1]** | 判断の連鎖を DAG で機械的に追跡（`depends_on` / `triggers` / `supersedes`） | 手動リンクのみ、影響範囲の自動算出不可 |
| **[D-2]** | AI コンテキストファイルへの自動同期 | この概念を持つツールは皆無 |
| **[D-3]** | 全体 YAML 形式による AI 可読性 | 全ツールが Markdown ベース |
| **[D-4]** | 棄却理由の必須級記録（0 件時警告） | MADR の Pros/Cons は任意で空欄が多い |
| **[D-5]** | AI 判断の帰属と承認フロー（AI 単独は `proposed` 強制） | 「人間が書く」前提でワークフロー未考慮 |

---

## フェーズ構成

| フェーズ | 内容 | 状態 |
|---|---|:--:|
| **Phase 1 PoC** | Claude Code skills（プロンプトレベル実装） | ✅ 実装済 |
| **Phase 2** | MCP Server STDIO (`@axis/udr-mcp-server`) | 🚀 早期着手（判断記録をリポジトリ外のナレッジサーバとして保持する方針。実装方針は `docs/Phase2_実装検討/UDR実装方法検討結果.md` で検討済、判断記録 UDR-UDR-20260719T0857-df1） |

現在は **Phase 1 PoC（Claude Code skills）が唯一の稼働実装**で、skill として YAML を直接読み書きします。MCP Server 化（Phase 2）は、判断記録（知的財産）をリポジトリ外の専用ナレッジサーバとして保持する根本対応として、当面保留の方針を撤回し早期着手する方針へ転換しました（判断記録 UDR-UDR-20260719T0857-df1）。Phase 2 移行時も YAML スキーマ・sync マーカーは互換を保証します。

---

## 配布チャネル（`dist` と `plugins/udr` のどっちが正？）

**どちらも「正」ではありません。** UDR skill の唯一の正（source of truth）は **`.claude/`**（`skills/` と `deploy/`）です。`plugins/udr/` の一部（`skills/` / `GEMINI.md` / `.gemini/`）は、そこから生成される**ミラー**で、`dist/` は手動展開時に `.claude/` を直接参照します（独立したコピーは持ちません、[0.6.0.1-PoC] 以降）。

| 場所 | 役割 | 編集 | 使う場面 |
|---|---|:--:|---|
| **`.claude/skills/` / `.claude/deploy/`** | ★source of truth（唯一の編集対象） | ✅ ここだけ | 開発・dogfooding・Claude Code が自動参照 |
| **`plugins/udr/`** | Claude Code **プラグイン版**（marketplace） | ⚠️ 一部生成物 | `claude plugin install`（★推奨・Claude 中心） |
| **`dist/`** | **手動 install バンドル**（install スクリプト + VERSION、skill 本体は含まない） | — （スクリプトのみ） | スクリプトで任意 repo に展開 / Gemini・Codex 主体 / プラグイン非対応環境 |

- **導入する側の選択**: Claude Code 中心なら `plugins/`（プラグイン）、スクリプトで撒く・Gemini/Codex 主体なら `dist/scripts/install.sh`。両方を同じ repo に入れると skill が二重になるのでどちらか一方に統一（→ [移行手順](#手動配置からプラグイン版への移行)）。
- **開発（編集）するときは `.claude/skills/` と `.claude/deploy/` だけ**を直します（→ [skills の一元管理](#skills-の一元管理)）。
- **`plugins/udr/skills/` / `plugins/udr/GEMINI.md` / `plugins/udr/.gemini/` の再生成は CI が自動化**: PR で `.claude/` に変更が入ると GitHub Actions（`.github/workflows/sync-mirrors.yml`）が `bash dist/scripts/build.sh` を実行し、差分があれば bot commit として同じ PR ブランチに push します。手元で `build.sh` を実行する必要はありません（CI が落ちていないか PR で確認するだけで十分）
- **`plugins/udr/` は完全な生成物ではない**: `skills/` / `GEMINI.md` / `.gemini/` は `.claude/` からのミラー（編集禁止、CI が自動生成）だが、`.claude-plugin/plugin.json` と `hooks/`（marketplace 配布専用の Claude Code hook）は `.claude/` に対応物がなく、**直接手編集**する（build.sh の対象外）。

---

## 前提・依存関係

導入前に以下を確認してください。

### 必須

| 項目 | 要件 |
|---|---|
| AI エージェント CLI | 下記いずれか 1 つ以上（併用可）: **Claude Code**（skills 機能対応版、★推奨）/ Gemini CLI / Codex CLI（0.139+）/ GitHub Copilot CLI（1.0+） |
| Git リポジトリ | UDR は判断記録の Git 永続を前提とする（C-003）。非 Git ディレクトリでは `udr-init` が失敗する |
| シェル | bash（POSIX / WSL / Git Bash）または PowerShell 7+（`install.sh` / `build.sh` 等のスクリプト実行用） |

### hook 機能（任意・既定で無効）

`git commit` 前のリマインド等の Claude Code hook（`plugins/udr/hooks/`）は **skill 本体とは独立した任意機能**で、**Claude Code のプラグイン版のみに対応**する（Codex CLI / GitHub Copilot CLI 等、同じ marketplace を共有する他ツールでは読み込まれない）。

- **基本機能（`udr-init` / `udr-record` 等の skill 一式）に Python は不要。** hook を使わない限り Python がインストールされていなくても UDR は問題なく動作する
- hook は `/udr-init` の Step 2.7 で **明示的に有効化した場合のみ**動作する（`.udr/config.yaml` の `hooks.enabled`、既定値 `false`）
- 有効化した場合のみ `python3`（PATH 上）が必要。ただし **`python3` が無い環境で誤って有効化しても壊れない**: hook 自身が `command -v python3` で存在確認してから実行するため、無ければ何も起きず無害に終了する（PyYAML 等の追加パッケージは不要、標準ライブラリのみで完結）

### 不要なもの

- **外部 API キー・有料サービスは一切不要。** LLM 外部呼び出し・embedding・ベクトル DB への依存を持たない設計（C-006/C-007）。`summary_hint` の生成もテンプレート結合のみで、ネットワークアクセスを必要としない
- **npm / pip 等のパッケージインストールは不要。** Phase 1 PoC はプロンプトレベル実装のみで、`package.json` / `requirements.txt` 等のマニフェスト自体が存在しない
- Cursor / Continue 等、専用 skill を持たないツールも `.udr/records/` を手動 YAML で共有できる（AGENTS.md §4 の手動テンプレート参照）

---

## インストール（Claude Code プラグインマーケットプレイス）★推奨

このリポジトリ自体が Claude Code の **プラグインマーケットプレイス** (`udr-marketplace`) になっており、`udr` プラグインとして UDR skill 一式を配布します。Claude Code から 2 ステップで導入できます。

### 手順（ターミナル CLI ／ 推奨・確実）

```bash
# 1. マーケットプレイスを登録（GitHub リポジトリを指定）
claude plugin marketplace add otinori/UDR

# 2. udr プラグインをインストール
claude plugin install udr@udr-marketplace
```

- `marketplace add <source>` の `<source>` は **`owner/repo` 短縮形**（例 `otinori/UDR`）/ フル URL（`https://github.com/otinori/UDR`）/ ローカルパスのいずれも可。短縮形は自動で `https://github.com/<owner>/<repo>.git` に解決されます。
- スコープ指定: `claude plugin install udr@udr-marketplace --scope project`（既定は user）。
- ローカルで試す: `claude plugin marketplace add /path/to/UDR`。

> **Claude Code セッション内から実行する場合**は、行頭に `!` を付けてください（例: `!claude plugin marketplace add otinori/UDR`）。
> スラッシュコマンドの `/plugin` は**引数なしで実行すると対話マネージャ**が開きます（バージョンによっては `/plugin marketplace add <source>` のインライン引数を受け付けないため、確実なのは上記 CLI 形式です）。

### 登録・更新・削除の運用コマンド

```bash
claude plugin marketplace list                    # 登録済みマーケットプレイス一覧
claude plugin marketplace update udr-marketplace  # 定義を最新化（リポジトリ更新を取り込む）
claude plugin update udr                           # プラグイン本体を更新（要再起動）
claude plugin uninstall udr@udr-marketplace        # アンインストール
claude plugin marketplace remove udr-marketplace   # マーケットプレイス登録を解除
```

### インストール後の呼び出し（名前空間に注意）

プラグイン経由で導入した skill は **`udr` 名前空間**で呼び出します。

| skill | プラグイン経由 |
|---|---|
| 初期化 | `/udr:udr-init` |
| 記録 | `/udr:udr-record` |
| 検索 | `/udr:udr-search <query>` |
| 同期 | `/udr:udr-sync` |
| 追跡 | `/udr:udr-trace <id> [--impact]` |
| レビュー | `/udr:udr-review` |
| ダッシュボード | `/udr:udr-dashboard` |

マニフェスト: [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json) / [`plugins/udr/.claude-plugin/plugin.json`](plugins/udr/.claude-plugin/plugin.json)

### Hooks（プラグイン限定）— コミット時の記録リマインド

プラグイン版には [`plugins/udr/hooks/`](plugins/udr/hooks/) に 2 つの hook を同梱しています（申し送り IM-04「コミット時UDR記録促進トリガー」に対応）。

| Hook | 発火タイミング | 内容 |
|---|---|---|
| `check_commit.py` | `git commit` 実行前（`PreToolUse`） | 「非自明な判断があれば `/udr-record` で記録を」と一言リマインド |
| `session_briefing.py` | セッション開始時（`SessionStart`） | 判断待ち draft・AI 単独 proposed の承認待ちがあれば件数を briefing |

- **既定で無効。** `/udr-init` の Step 2.7 で opt-in した場合（`.udr/config.yaml` の `hooks.enabled: true`）のみ動作する。python3 が無い環境でも安心して Y/N を選べるよう、無効を既定値にしている
- **両方とも非ブロッキング**（`additionalContext` のみ。コミットや操作を止めない）。
- **`.udr/` 未初期化のプロジェクト、hook 無効のプロジェクトでは何もしない**（静か）。
- **python3 が PATH に無い環境でも安全。** hook 自身が `command -v python3` で存在確認してから実行するシェルラッパー越しに呼ばれるため、無ければ何も起きず無害に終了する（エラーにはならない）。存在すれば Python 標準ライブラリのみで完結（PyYAML 等の追加依存なし、C-006/C-007 のポータビリティ方針を踏襲）
- **絶対パスを一切含まない**: プラグイン自身のスクリプトは `${CLAUDE_PLUGIN_ROOT}`、対象プロジェクトのパスは実行時に Claude Code が渡す `CLAUDE_PROJECT_DIR` 環境変数から解決する。インストール先のパスに依存しないため、マーケットプレイス経由でどの環境に配布されても動作する。
- **Claude Code のプラグイン版のみに対応。** 同じ marketplace を共有する Codex CLI / GitHub Copilot CLI では hook は読み込まれず、skill のみが利用可能（本書のみに記載する既知の制約）。
- **手動展開（`dist/`）には含まれない。** hook は Claude Code のプラグイン機構専用の仕組みのため、`plugins/udr/hooks/` は `.claude/` からのミラーではなく手動管理のプラグイン専用ファイル（`plugins/udr/.claude-plugin/plugin.json` と同様の扱い、[skills の一元管理](#skills-の一元管理) 参照）。

---

## 代替: 既存プロジェクトへ手動展開（スクリプト）

マーケットプレイスを使わず、対象プロジェクトの `.claude/skills/` 等へ直接コピーする方法もあります。

```bash
# Claude Code のみ
bash dist/scripts/install.sh /path/to/target-project

# Claude Code + Gemini CLI
bash dist/scripts/install.sh /path/to/target-project --gemini

# Claude Code + Codex CLI（セットアップ案内つき）
bash dist/scripts/install.sh /path/to/target-project --codex

# Windows PowerShell（同様に -Gemini / -Codex フラグあり）
pwsh dist/scripts/install.ps1 C:\path\to\target-project -Gemini
```

`--gemini` フラグを付けると `GEMINI.md` と `.gemini/extensions/udr/` が自動生成されます。
この方法で展開した Claude Code skill は名前空間なしで呼び出します（`/udr-init`、`/udr-record` …）。詳細は [`dist/usage.md`](dist/usage.md) を参照。

### 手動配置からプラグイン版への移行

既に手動配置（`.claude/skills/` に直接コピー）した repo をプラグイン版へ入れ替える手順。**`.udr/` の判断記録データはそのまま**（skill のプロンプトだけ差し替え）。

```bash
# 1. プラグイン版を入れる (セッション内なら行頭に ! を付ける)
claude plugin marketplace add otinori/UDR
claude plugin install udr@udr-marketplace

# 2. 手動配置の skill を削除（.udr/ は消さない！）
rm -rf .claude/skills/udr-init .claude/skills/udr-record .claude/skills/udr-search \
       .claude/skills/udr-sync .claude/skills/udr-trace .claude/skills/udr-review \
       .claude/skills/udr-dashboard .claude/skills/_udr-shared \
       .claude/skills/README.md .claude/skills/.udr-skills-version
rm -rf .claude/skills/*.bak-*
```

- 呼び出しは `/udr-init` → **`/udr:udr-init`**（名前空間付き）に変わる。
- データ（`.udr/records/` / `config.yaml`）は不変。以後の更新は `claude plugin update udr` だけ。
- `.claude/skills/` に UDR 以外の skill があれば、それらは残すこと。

---

## 設定: 使う AI ツール（`config.yaml` の `tools`）

`/udr-init` で `.udr/config.yaml` に **`tools:`**（使う AI ツール）を宣言します。sync の書き込み先はここから導出され、**宣言したツールのファイルだけ**が更新されます（実行中のツールでは分岐しません）。

```yaml
tools: [claude, gemini, codex]   # CLAUDE.md / GEMINI.md / AGENTS.md の 3 ファイルを同期
```

| `tools` の値 | sync 先 | 操作方法 |
|---|---|---|
| `claude` | `CLAUDE.md` | `/udr-record` 等の skill |
| `gemini` | `GEMINI.md` | `gemini-prompts/udr-*.md` テンプレート |
| `codex` | `AGENTS.md` | `codex-prompts/udr-*.md` テンプレート |
| `copilot` | `.github/copilot-instructions.md` + `.github/instructions/udr-decisions.instructions.md` | 参照のみ（記録は他ツールで） |
| `cursor` / `windsurf` | `.cursorrules` / `.windsurfrules` | 参照のみ |

使うツールを変えたら `tools` を更新して `/udr-init` を再実行すれば、不足ファイルの生成・不要な残骸の検知まで自動調整されます（`/udr-sync` も実行時にツールのずれを警告します）。

---

## 利用フロー（Claude Code 上）

> プラグイン経由なら頭に `udr:` を付けます（例: `/udr:udr-init`）。手動展開なら `/udr-init` のまま。

1. `udr-init` — `.udr/` ディレクトリと `config.yaml` を生成（初回のみ）
2. `udr-record` — 判断が発生したら対話的に記録（必須 3 項目 + 任意 3 項目）
3. `udr-search <query>` — ID 指定 / フィルタ / 全文検索
4. `udr-sync` — CLAUDE.md 等へ要約を同期（pinned 最大 5 件 + auto 最大 15 件、budget 1200 トークン）
5. `udr-trace <id> [--impact]` — DAG 上下流の走査・変更影響分析
6. `udr-review` — 品質棚卸し（orphan / ステータス不整合 / AI 承認待ち / 棄却理由欠落 / DAG・YAML 健全性 / sync 陳腐化 / code_refs 未記入 / 放置 draft の 9 観点）
7. `udr-dashboard` — 判断状況を `udr_dashboard.html` に出力（集計 / 一覧 / 棄却理由 / 依存関係、自己確認用）

---

## 要件カバレッジ（Phase 1 PoC）

| 要求 ID | 要求内容 | カバー skill |
|---|---|---|
| FR-001 | 判断の新規記録 | `udr-record` |
| FR-002 | 検索・取得（ID / フィルタ / 全文） | `udr-search` |
| FR-005 | 依存関係追跡 | `udr-trace` |
| FR-006 | 変更影響分析 | `udr-trace --impact` |
| FR-007 | 循環参照検出 | `udr-record` / `udr-trace` / `udr-review` |
| FR-008 | コンテキストファイル同期（atomic write） | `udr-sync` |
| FR-009 | AI 用サマリ自動生成 | `udr-record` + `udr-sync` |
| FR-010 | AI 生成 UDR の status 強制 | `udr-record` |
| FR-012 | 対話的な判断記録ガイド | `udr-record` |
| FR-013 | 判断レビュー | `udr-review` |
| FR-014 | プロジェクト初期化 | `udr-init` |
| FR-015 | 棄却選択肢 0 件警告 | `udr-record` |

FR-003（部分更新）/ FR-004（supersede）は Phase 2（MCP 化）で独立 skill / MCP tool 化する方針です。Phase 2 は早期着手の方針に転換しましたが、実装完了までの現状は直接 Edit + audit.log 手動追記、および `udr-record` での旧 UDR status 変更 + 新規作成で運用します。

---

## リポジトリの構成

- **UDR skill の正は `.claude/skills/` と `.claude/deploy/` だけ**。`plugins/udr/skills/` / `plugins/udr/GEMINI.md` / `plugins/udr/.gemini/` はそこから**生成されるミラー**（CI が PR 上で自動生成、[skills の一元管理](#skills-の一元管理) 参照）。`dist/` は独立ミラーを持たず、`install.sh` が `.claude/` を実行時に直接参照します。
- `.github/` は Issue/PR テンプレート・CI（`workflows/validate.yml` / `workflows/sync-mirrors.yml`）等、標準的な GitHub 運用ファイルのみで、UDR skill 本体は含みません。

```
UDR/
├── README.md                       (このファイル)
├── AGENTS.md                       (マルチエージェント共通ポリシー / UDR 自動検知ポリシー)
├── CLAUDE.md                       (Claude Code 固有指示 / AGENTS.md の派生)
├── GEMINI.md                       (Gemini CLI 固有指示 / AGENTS.md の派生)
│
├── .claude/
│   ├── skills/                     (★唯一の source of truth — UDR skill 一式: init/record/search/sync/trace/review/dashboard)
│   └── deploy/                     (★source of truth — デプロイテンプレート: GEMINI.md / .gemini/ 拡張)
├── plugins/
│   └── udr/                        (UDR プラグイン本体)
│       ├── .claude-plugin/plugin.json  (手動管理・.claude/に対応物なし)
│       ├── hooks/                  (手動管理・marketplace 配布専用の Claude Code hook。.claude/に対応物なし)
│       ├── GEMINI.md               (↑ .claude/deploy/ の生成ミラー / CI で自動再生成・直接編集しない)
│       ├── .gemini/extensions/udr/ (↑ .claude/deploy/.gemini/ の生成ミラー)
│       └── skills/                 (↑ .claude/skills/ の生成ミラー / CI で自動再生成・直接編集しない)
├── .claude-plugin/
│   └── marketplace.json            (udr-marketplace 定義: udr プラグインを配布)
├── dist/                           (手動 install 用バンドル。skill 本体は含まず .claude/ を直接参照)
│   ├── usage.md / VERSION
│   └── scripts/                    (install.sh / install.ps1 / build.sh / build.ps1)
├── .udr/                           (判断記録)
│   ├── records/                    (UDR-UDR-*.yaml ※1判断1ファイル)
│   └── config.yaml                 (repo_short: UDR ※index.json/audit.log は非追跡)
├── .github/
│   └── workflows/                  (validate.yml: 検証 / sync-mirrors.yml: PR でミラー自動生成)
│
└── docs/                           (ドキュメント・資料・成果物を集約)
    ├── Phase1_要求定義/            (要求定義 v2.2・既存 ADR 調査)
    └── Phase2_実装検討/            (Phase 2 実装方法検討結果 ※早期着手方針)
```

---

## マルチエージェント協働

UDR は複数の AI エージェント（Claude Code / Gemini CLI / Codex CLI / GitHub Copilot 等）が同じ判断記録を共有しながら協働することを前提に設計されています。

| ファイル | 内容 |
|---|---|
| [`AGENTS.md`](AGENTS.md) | 全エージェント共通ポリシー（会話開始時に最初に読む） |
| [`CLAUDE.md`](CLAUDE.md) | Claude Code 固有指示（AGENTS.md の派生） |
| [`GEMINI.md`](GEMINI.md) | Gemini CLI 固有指示（AGENTS.md の派生） |
| [`.udr/records/`](.udr/records/) | 判断記録（1 判断 = 1 YAML） |

---

## skills の一元管理

UDR skill の **唯一の source of truth は [`.claude/skills/`](.claude/skills/) と [`.claude/deploy/`](.claude/deploy/)** です（[0.6.0.1-PoC] で `src/` から移行）。Claude Code はこのリポジトリを開くと `.claude/skills/` を自動的に読み込むため、**このリポジトリ自身の dogfooding で使う skill と、配布物の source of truth が同じ場所**になります。

```
.claude/skills/   ← source of truth（ここだけを編集。Claude Code が自動参照）
   │  CI (sync-mirrors.yml) が PR 上で自動 build & commit
   └─▶ plugins/udr/skills/   （プラグインマーケットプレイス配布用ミラー）

.claude/deploy/    ← デプロイテンプレートの source of truth
   │  CI (sync-mirrors.yml) が PR 上で自動 build & commit
   └─▶ plugins/udr/ root     （GEMINI.md / .gemini/）

dist/scripts/install.sh・install.ps1 は .claude/skills/・.claude/deploy/ を
実行時に直接参照する（独立ミラーを持たない）。
```

`.claude/skills/` や `.claude/deploy/` を変更した PR を出すと、GitHub Actions（[`sync-mirrors.yml`](.github/workflows/sync-mirrors.yml)）が `plugins/udr/` ミラーを自動生成し、bot commit として同じ PR ブランチに push します。**手元で `build.sh` を実行する必要は基本的にありません**（CI が失敗した場合のフォールバック、またはローカルで生成結果を確認したい場合のみ使用）:

```bash
# Windows PowerShell
pwsh dist/scripts/build.ps1
# Windows バッチ (ダブルクリック / cmd 可。build.ps1 を呼ぶラッパー)
dist\scripts\build.bat

# POSIX / WSL / Git Bash
bash dist/scripts/build.sh
```

## 開発プロセス（ドッグフーディング）

本リポジトリは UDR の本家実装であり、**UDR 自身の開発判断も UDR として記録**します（`.udr/records/` 参照）。要求定義・アーキテクチャ選定・skill 設計方針等の判断は、検知次第 `udr-record` で起票します。

---

## ドキュメント

| 種別 | パス |
|---|---|
| 要求定義 v2.2 | [`docs/Phase1_要求定義/要求一覧.md`](docs/Phase1_要求定義/要求一覧.md) |
| Phase 2 実装検討 | [`docs/Phase2_実装検討/UDR実装方法検討結果.md`](docs/Phase2_実装検討/UDR実装方法検討結果.md) |
| 既存 ADR 調査 | [`docs/Phase1_要求定義/既存ADR調査_UDR特徴分析.md`](docs/Phase1_要求定義/既存ADR調査_UDR特徴分析.md) |
| インストール手順 | [`dist/usage.md`](dist/usage.md)（手動展開）/ [`plugins/udr/usage.md`](plugins/udr/usage.md)（プラグイン） |
| skill 共通規約 | [`.claude/skills/_udr-shared/CONVENTIONS.md`](.claude/skills/_udr-shared/CONVENTIONS.md) |
| マルチエージェント共通ポリシー | [`AGENTS.md`](AGENTS.md) |
| 変更履歴 | [`CHANGELOG.md`](CHANGELOG.md) |

---

## Phase 1 PoC の制約

- **LLM 外部呼び出しなし** (C-007): `summary_hint` はテンプレート結合のみ
- **embedding・ベクトルDB・外部LLM APIなし** (C-006/C-007): 全文検索は決定的スコアリング（Stage1）を既定とし、0件/低スコア時のみ呼び出し元AIによる追加探索（Stage2）にエスカレートする2段階ハイブリッド方式（判断記録 UDR-UDR-20260711T0728-f9f）
- **atomic write はベストエフォート** (AR2-02): Windows NTFS では rename アトミック保証が限定的
- **500 件上限** (NFR-005): 超過時は Phase 4 SQLite 移行で対応予定
- **Git リポジトリ必須** (C-003): 判断記録の永続性を Git に委譲

---

## バージョン

- **udr-skills**: `0.6.0.2-PoC` (Phase 1 PoC / prompt-level)。変更履歴は [`CHANGELOG.md`](CHANGELOG.md) 参照
- **schema_version**: `0.1`
- **対象**: Claude Code skills 機能対応版（将来的に MCP Server 対応クライアント全般）

---

## ライセンス

[MIT License](LICENSE)

---

## 謝辞

- **[Claude Code](https://claude.com/claude-code)**（Anthropic）— 本プロジェクトの Phase 1 PoC が実装対象とする AI エージェント CLI。UDR 自身の開発判断も Claude Code 上でドッグフーディングしている
- **既存 ADR ツール群**（[MADR](https://adr.github.io/madr/) / adr-tools / Log4brains / Structurizr 等）— UDR の設計方針（[D-1]〜[D-5] の差別化ポイント）は、これら 10 種以上の先行ツールの調査を踏まえて検討した。調査の詳細は [`docs/Phase1_要求定義/既存ADR調査_UDR特徴分析.md`](docs/Phase1_要求定義/既存ADR調査_UDR特徴分析.md) を参照
- **conclave**（マルチエージェントレビュー基盤）— `udr-record` の独立コンテキストレビュー機構（§文章品質ガイドライン）を検討する過程で、将来のマルチロールレビュー連携先として参照した別プロジェクト。現時点では未連携（本プロジェクトのスコープ外、関連判断: UDR-UDR-20260712T0314-47b）

コードレベルの外部ライブラリ依存は持たない（[前提・依存関係](#前提依存関係)参照）ため、上記は「思想的な参考・連携先」としての記載であり、ビルド・実行時の第三者コード同梱はない。
