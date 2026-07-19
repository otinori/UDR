# Changelog

UDR (Universal Decision Record) の変更履歴。[Keep a Changelog](https://keepachangelog.com/) の形式に準拠する。

本ファイルは `0.6.0.1` を起点として記録を開始する。

## 0.6.0.2-PoC - 2026-07-20

初回 GitHub 公開（Public化）に向けた棚卸しリリース。`.udr/` の非追跡化方針、Phase 2 早期着手方針への転換、`udr-dashboard` の大幅強化、公開前監査で見つかった記述不整合の修正を行った。

### Added

- `udr-dashboard` にレコードごとの「解説」ブロックを追加（専門知識のない読み手向けの平易な要約。技術的な decision/rationale はそのまま併記）
- `udr-dashboard` の依存関係 DAG をグラフ（SVG）として可視化。ノードクリックで一覧を絞り込み・詳細展開
- `udr-dashboard` の上部サマリカードを全種類クリック可能化（total/各status/pinned/high severity）
- `SECURITY.md`（`.github/SECURITY.md` に統一。GitHub Private Vulnerability Reporting を使用し個人メールは非公開）

### Fixed

- README.md が参照する存在しない `要求定義レビュー結果報告書.md` へのリンクを削除
- README/AGENTS.md の Phase 2「当面保留」表記を実際の方針（早期着手）に合わせて更新
- `docs/要求一覧.md`・`dist/usage.md` に残っていた「`.udr/*.yaml` は Git 管理対象」という旧前提の記述に、個人プロジェクトでの非追跡化方針を反映する注記を追加
- `plugins/udr/skills/` ミラーが `.claude/skills/` の更新（dashboard 強化分）に対して未同期だったため再生成
- `CONVENTIONS.md`・`docs/要求一覧.md` に残っていた、削除済み入力資料フォルダへの疑似パス参照を、外部資料であることが明確な文章に書き換え
- ルートの重複する `SECURITY.md`（個人メール直書き）を削除し `.github/SECURITY.md` に統一
- CI（`validate.yml`）が `.udr/config.yaml` の不在で無条件に失敗していた問題を修正（存在しない場合はスキップ）

### Changed

- 個人プロジェクトでの利用時は `.udr/`（判断記録含む）を `.gitignore` で Git 非追跡にする方針へ転換（チーム開発の private リポジトリ内での共有は従来通り継続）
- Phase 2（MCP Server 化）の「当面保留」方針を撤回し、判断記録をリポジトリ外のナレッジサーバとして保持する実装に早期着手する方針へ転換
- README.md に Obsidian 用 YAML frontmatter、平易な説明セクション、マルチエージェント協働セクションを追加
- リポジトリを GitHub へ Public 公開し、Secret scanning・Push protection・Dependabot・CodeQL・ブランチ保護 ruleset を有効化

### Known Limitations

- Phase 1 PoC の制約（LLM 外部呼び出しなし・embedding/ベクトルDBなし・500件上限 等）は [README.md](README.md#phase-1-poc-の制約) を参照
- `.udr/` を非追跡にする方針は個人プロジェクト限定。ローカル環境の消失時に判断記録を失うリスクがあるためバックアップは利用者の責任

## 0.6.0.1-PoC - 2026-07-12

Claude Code hook 機能の追加と、実験的プロジェクトである旨の明記を行ったリリース。

### Added

- Claude Code hook 機能（`check_commit.py` / `session_briefing.py`、既定は無効）
- README 冒頭に実験的プロジェクトである旨の免責ブロックを追加

### Fixed

### Changed

- バージョン表記に Phase 1 PoC であることを示す `-PoC` サフィックスを付与

### Known Limitations

- Phase 1 PoC の制約（LLM 外部呼び出しなし・embedding/ベクトルDBなし・500件上限 等）は [README.md](README.md#phase-1-poc-の制約) を参照

