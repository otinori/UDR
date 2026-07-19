# Changelog

UDR (Universal Decision Record) の変更履歴。[Keep a Changelog](https://keepachangelog.com/) の形式に準拠する。

本ファイルは `0.6.0.1` を起点として記録を開始する。

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

