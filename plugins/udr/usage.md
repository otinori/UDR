# UDR プラグイン — インストールと使い方

> ⚠️ **実験的プロジェクトです。** Phase 1 PoC 段階のため、スキーマ・コマンド体系は今後変更される可能性があります。

Claude Code の **プラグインマーケットプレイス**経由で UDR (Universal Decision Record) を導入するためのガイド。判断記録 skill 一式 (init / record / search / sync / trace / review / dashboard) に加え、`git commit` 前のリマインドなどの Claude Code hook (`hooks/`) を提供します。

> スクリプトによる手動展開（プラグイン非対応環境・Codex/Copilot 主体）は [`../../dist/usage.md`](../../dist/usage.md) を参照。両者は同じ source of truth (`.claude/skills/` / `.claude/deploy/`) から取得され、`.udr/` データは共通です。

---

## 1. インストール（ターミナル CLI ／ 推奨・確実）

```bash
# 1. マーケットプレイスを登録 (GitHub リポジトリを指定)
claude plugin marketplace add otinori/UDR

# 2. udr プラグインをインストール
claude plugin install udr@udr-marketplace
#   このリポジトリだけで使うなら:  claude plugin install udr@udr-marketplace --scope project
```

- `<source>` は `owner/repo` 短縮形（`otinori/UDR`）/ フル URL（`https://github.com/otinori/UDR`）/ ローカルパス（`/path/to/UDR`）いずれも可。短縮形は自動で github.com に解決されます。
- **Claude Code セッション内**から打つときは行頭に `!` を付ける（例: `!claude plugin install udr@udr-marketplace`）。
- スラッシュの `/plugin` は引数なしで**対話マネージャ**が開きます（インライン引数を受け付けないバージョンがあるため、確実なのは上記 CLI）。

### Gemini CLI でも同じマーケットプレイスが使える

Gemini CLI (Google の OSS AI CLI) は UDR の `gemini-prompts/` テンプレート経由でフル操作が可能です。
スキルのインストールは Claude Code マーケットプレイスと同じリポジトリから:

```bash
# 1. skills を手動展開（dist バンドルを使う）
bash dist/scripts/install.sh /path/to/target-project --gemini

# または GEMINI.md と .gemini/ だけ個別生成
cp plugins/udr/GEMINI.md /path/to/target-project/GEMINI.md
cp -r plugins/udr/.gemini /path/to/target-project/
```

導入後は `GEMINI.md` を Gemini CLI が自動で読み込みます。操作時は:
```
@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md
判断を記録してください: ...
```

> Gemini CLI は `GEMINI.md`（プロジェクトルート）をコンテキストファイルとして自動認識します（CLAUDE.md に相当）。
> `.gemini/extensions/udr/gemini-extension.json` を配置するとシステムプロンプトで UDR ポリシーが自動注入されます。

| ツール | 呼び出し方 |
|---|---|
| Gemini CLI | `@gemini-prompts/udr-record.md` のようにテンプレートをファイル参照 |

### Codex CLI でも同じマーケットプレイスが使える（0.139+）

Codex CLI は Claude と互換のプラグイン機構を持ち、**同じ `.claude-plugin/marketplace.json` を読みます**。インストールは `add`（`install` ではない点に注意）:

```bash
codex plugin marketplace add otinori/UDR   # local path / git URL も可
codex plugin add udr@udr-marketplace
codex plugin list                                # 確認
```

導入後、Codex 対話では **skill 扱いなので `$udr:udr-init`**（`$` + plugin 名前空間 `udr:`）で呼び出します。`/skills` で一覧表示・選択も可。

> ⚠️ Codex の **`/...` は組み込みコマンド**（`/skills` `/plugins` `/status` `/model` 等）。UDR skill の明示呼び出しは **`$udr:udr-init`** のように `$` を使う（`/udr-init` ではない）。
> plugin を使わず `.codex/prompts/udr-*.md` を `~/.codex/prompts/` にコピーした場合のみ、ファイル名の slash command `/udr-init` になります。

> Codex は Claude のプラグインを「経由」するわけではなく、**同じ repo（マーケットプレイス）を自前で取得**します。private repo の場合は Codex 側の git 認証/アクセス権が必要。

### GitHub Copilot CLI でも同じマーケットプレイスが使える（1.0+）

Copilot CLI も独自の plugin marketplace を持ち、**同じ `.claude-plugin/marketplace.json` を読みます**（`.claude/skills/` の自動検出は**しません**）。インストールは `install`:

```bash
copilot plugin marketplace add otinori/UDR
copilot plugin install udr@udr-marketplace          # または: copilot plugin install otinori/UDR:plugins/udr
copilot plugin list
```

導入後の呼び出しは **`/udr-init`（slash・名前空間なし）**。

### ツール別 呼び出し早見

| ツール | 導入 | 呼び出し |
|---|---|---|
| Claude Code (plugin) | `claude plugin install udr@udr-marketplace` | `/udr:udr-init` |
| Gemini CLI | `install.sh --gemini` でセットアップ | `@gemini-prompts/udr-record.md` |
| Codex CLI (plugin) | `codex plugin add udr@udr-marketplace` | `$udr:udr-init` |
| GitHub Copilot CLI (plugin) | `copilot plugin install udr@udr-marketplace` | `/udr-init` |

> Claude / Codex / Copilot は同一の `.claude-plugin/marketplace.json` を読む。Gemini は `install.sh --gemini` でテンプレートベースのセットアップを行う。

## 2. 使い方 (インストール後)

プラグイン経由の skill は **`udr` 名前空間**で呼び出します。

| コマンド | 役割 |
|---|---|
| `/udr:udr-init` | `.udr/` を初期化。`config.yaml` の `tools`（使う AI ツール）も設定 |
| `/udr:udr-record` | 判断を対話的に記録（棄却理由の併記が必須） |
| `/udr:udr-search <q>` | ID / フィルタ / 全文検索 |
| `/udr:udr-sync` | CLAUDE.md / AGENTS.md 等へ要約を同期 |
| `/udr:udr-trace <id> [--impact]` | 依存 DAG 走査・影響分析 |
| `/udr:udr-review` | 品質棚卸し（9 観点） |
| `/udr:udr-dashboard` | 判断状況を `udr_dashboard.html` に出力 |

基本フロー: `/udr:udr-init` → 判断発生時に `/udr:udr-record` → `/udr:udr-sync` でコンテキスト同期。詳細は `/udr:udr-search` 等、各 skill 本体の説明を参照。

### Hook（`git commit` 前のリマインド、既定で無効）

このプラグインには `hooks/`（[`hooks/hooks.json`](hooks/hooks.json)）が同梱されていますが、**既定では無効**です。`/udr:udr-init` の Step 2.7 で opt-in すると、`git commit` 実行前のリマインドやセッション開始時の briefing が有効になります（skill と違い、呼び出しコマンドは不要で自動発火）。

対応ツールの制約・Python 要件などの詳細は repo ルートの `README.md`「前提・依存関係」節を参照してください。

## 3. 更新 / アンインストール

```bash
claude plugin marketplace update udr-marketplace   # 定義を最新化
claude plugin update udr                           # プラグイン本体を更新 (要再起動)
claude plugin uninstall udr@udr-marketplace        # アンインストール (.udr/ データは残る)
```

## 4. 手動配置から移行する場合

既に `.claude/skills/` に手動配置済みの repo は、プラグイン導入後に手動配置分を削除します（`.udr/` は残す）。手順はリポジトリルートの `README.md`「手動配置からプラグイン版への移行」を参照。

## 5. マニフェスト

- マーケットプレイス: [`../../.claude-plugin/marketplace.json`](../../.claude-plugin/marketplace.json)
- プラグイン: [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)
