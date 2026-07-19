# /udr-init — UDR 初期化

`.udr/` ディレクトリ構造を初期化する。Claude Code の `/udr-init` skill と等価な動作を Gemini CLI で行うラッパー。

## 実行手順

1. **既存確認**: `.udr/config.yaml` が既に存在する場合は「既に初期化済みです」と伝え、不足ファイルのみ補完するかを確認する
2. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読み、ID 体系・スキーマを理解する
3. **skill 本体を読み込む**: `.claude/skills/udr-init/SKILL.md` を読み、その手順に従って実行する
4. **作成するもの**:
   - `.udr/` ディレクトリ
   - `.udr/records/` ディレクトリ
   - `.udr/config.yaml`（下記テンプレートを使用）
   - `GEMINI.md` が存在しない場合は user に作成を提案する
5. 完了後、`udr-record.md` を使った最初の判断記録を提案する

## config.yaml テンプレート

```yaml
project:
  name: <プロジェクト名>
  repo: <repo_short>
  description: <説明>

storage:
  directory: .udr
  format: yaml
  index_file: index.json

id_format: "UDR-{repo}-{YYYYMMDD}T{HHMM}-{hex3}"
repo_short: <REPO_SHORT>   # ID に使う識別子（例: MyProject -> MP）

tools:
  - gemini
  # - claude
  # - codex

sync:
  targets:
    - GEMINI.md
    # - CLAUDE.md
    # - AGENTS.md
  budget_tokens: 1200
  auto_select_top_n: 5
```

## .gitignore への追記

以下を `.gitignore` に追加するよう提案する:

```
.udr/index.json
.udr/audit.log*
udr_dashboard.html
```
