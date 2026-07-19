## 変更内容

<!-- 何を変更したか簡潔に記述 -->

## 変更の種類

- [ ] バグ修正
- [ ] 新機能（skill 追加・拡張）
- [ ] Hook 追加・変更（`plugins/udr/hooks/`、marketplace 配布限定）
- [ ] スキーマ変更（CONVENTIONS.md の更新を含む）
- [ ] ドキュメント更新
- [ ] ビルド・配布スクリプトの変更
- [ ] その他

## チェックリスト

- [ ] `.claude/skills/` を変更した場合、`plugins/udr/` ミラーは CI（`sync-mirrors.yml`）が自動生成するため対応不要（CI green を確認するだけでよい）
- [ ] `plugins/udr/hooks/` を変更した場合、`claude plugin validate ./plugins/udr` でエラーがなく、絶対パスを含まない（`${CLAUDE_PLUGIN_ROOT}` / `CLAUDE_PROJECT_DIR` 経由）
- [ ] YAML を追加/変更した場合、フォーマットが正しい（インデント・必須フィールドあり）
- [ ] スキーマ変更の場合、`plugins/udr/.claude-plugin/plugin.json` と `dist/VERSION` のバージョンを更新した
- [ ] ブランチが `develop` に向いている（`main` への直接 PR でない）

## 関連 Issue

closes #

## テスト方法

<!-- レビュアーがどうテストすればよいか記載 -->
