# コントリビューションガイド

UDR (Universal Decision Record) プロジェクトへのコントリビューションを歓迎します。

## 開発の前に

1. [Issue](https://github.com/otinori/udr/issues) で変更内容を事前に議論してください
2. 大きな変更（新 skill の追加・スキーマ変更）は Issue を先に立てることを推奨します

## ブランチ戦略

- `main` — 安定リリース
- `develop` — 開発中の変更はこちらにマージ
- feature ブランチ: `feature/<short-description>`
- bugfix ブランチ: `fix/<short-description>`

## Pull Request のルール

- PR は `develop` ブランチへ向けてください（`main` への直接 PR は禁止）
- タイトルは日本語または英語、変更内容を簡潔に
- 以下のチェックリストをすべて確認してから PR を出してください:
  - [ ] `.claude/skills/` を変更した場合、`plugins/udr/skills/` 等のミラー再生成は CI（`sync-mirrors.yml`）が PR 上で自動 commit するため、手動での `build.sh` 実行は不要（CI が失敗していないことだけ確認）
  - [ ] 新しい skill を追加した場合、`_udr-shared/CONVENTIONS.md` と整合している
  - [ ] YAML ファイルを追加/変更した場合、`yamllint` でエラーがない
  - [ ] `plugins/udr/.claude-plugin/plugin.json` のバージョンを更新した（API Breaking Change の場合）
  - [ ] `plugins/udr/hooks/` を変更した場合、`claude plugin validate ./plugins/udr` でエラーがない

## CI セットアップ（リポジトリ管理者向け、初回のみ）

`sync-mirrors.yml` が PR ブランチへ bot commit を push するには、リポジトリの
**Settings → Actions → General → Workflow permissions** で
**「Read and write permissions」** を有効にする必要がある（GitHub の既定は
read-only）。未設定の場合、`sync-mirrors.yml` は push に失敗してエラーになる
（`.claude/` 側の変更自体は正常にマージできるが、ミラーは手動で
`bash dist/scripts/build.sh` を実行してコミットする必要がある）。

## Skill の変更

`.claude/skills/` が **source of truth**（[0.6.0.1-PoC] で `src/skills/` から移行）。`plugins/udr/skills/` はそこから生成されるミラーで直接編集しない。`.claude/skills/` を直接編集して PR を出すだけでよい。

PR を作成すると GitHub Actions（`.github/workflows/sync-mirrors.yml`）が `bash dist/scripts/build.sh` を実行し、`plugins/udr/skills/` 等の差分を検知すると bot commit として同じ PR ブランチに自動 push する（人間のレビューは `.claude/` の差分だけ見れば済む）。**手元で `build.sh` を実行する必要は基本的にない。** ローカルで生成結果を確認したい場合、または CI が失敗した場合のフォールバックとしてのみ使う:

```bash
bash dist/scripts/build.sh
```

## Hook の変更（`plugins/udr/hooks/`）

`plugins/udr/hooks/`（`hooks.json` + スクリプト）は `plugins/udr/.claude-plugin/plugin.json` と同様、**`.claude/` に対応物がなく build.sh の対象外**（marketplace 配布専用の Claude Code hook のため、手動配置の `dist/` には存在しない）。直接編集する。

- 絶対パスを書かない。プラグイン自身のファイルは `${CLAUDE_PLUGIN_ROOT}`、対象プロジェクトのパスは実行時の `CLAUDE_PROJECT_DIR` 環境変数を使う
- 変更後は `claude plugin validate ./plugins/udr` でスキーマエラーがないことを確認する
- 新しい依存（PyYAML 等）を追加しない。標準ライブラリのみで完結させる（C-006/C-007 のポータビリティ方針）
- ブロッキング hook（`permissionDecision: deny` 等）は追加しない。UDR の hook は常に非ブロッキング（`additionalContext` のみ）とする方針（FR-015 の「警告のみ・ブロックしない」思想を踏襲）

## スキーマ変更

`.claude/skills/_udr-shared/CONVENTIONS.md` のスキーマを変更する場合:

1. 後方互換性を維持するか、明示的に非互換であることを PR に記載する
2. `plugins/udr/.claude-plugin/plugin.json` と `.claude-plugin/marketplace.json` のバージョンをセマンティックバージョニングに従って上げる
3. `dist/VERSION` を更新する
4. `CHANGELOG.md` にエントリを追加する

## UDR 判断の記録

本プロジェクト自体の設計判断も UDR として記録するドッグフーディング方針を採用しています。  
コントリビューション時に重要な判断をした場合は PR 説明に記載してください（プロジェクトオーナーが UDR 化します）。

## コード規約

- Markdown: CommonMark 準拠
- YAML: 2スペースインデント、`yamllint` でエラーなし
- JSON: 2スペースインデント

## ライセンス

コントリビュートされたコードは [MIT License](../LICENSE) の下でリリースされます。
