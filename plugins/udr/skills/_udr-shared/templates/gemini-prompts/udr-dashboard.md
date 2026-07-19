# /udr-dashboard — HTML ダッシュボード生成

UDR の判断状況を 1 枚の自己完結 HTML (`udr_dashboard.html`) として出力する。Claude Code の `/udr-dashboard` skill と等価な動作を Gemini CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む
2. **skill 本体を読み込む**: `.claude/skills/udr-dashboard/SKILL.md` を読み、その HTML 生成手順に **厳密に** 従って実行する
3. **全 UDR を収集**: `.udr/records/UDR-*.yaml` を全件読み込む
4. **HTML を生成**: `udr_dashboard.html` をプロジェクトルートに出力する（`.gitignore` 対象）

## 生成する HTML の構成

- **集計セクション**: status別・domain別・severity別の件数グラフ（棒グラフ）
- **Pinned UDR**: `pinned: true` の UDR をカード形式で表示
- **全 UDR 一覧テーブル**: 検索・フィルタ機能付き、行クリックで decision / 棄却理由を展開
- **依存関係ビジュアライザ**: `depends_on` / `triggers` / `supersedes` を矢印で可視化

## 設計制約

- **外部依存なし**: CDN 不使用、オフライン閲覧可能な単一 HTML ファイル
- **自己完結**: JavaScript / CSS はすべてインライン埋め込み
- **文字コード**: UTF-8

## 出力確認

生成後、ブラウザで開いて確認するよう user に提案する:

```bash
# macOS
open udr_dashboard.html
# Linux
xdg-open udr_dashboard.html
# Windows
start udr_dashboard.html
```
