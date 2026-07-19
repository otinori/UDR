# /udr-review — 品質棚卸し

UDR 記録の品質を棚卸しする。Claude Code の `/udr-review` skill と等価な動作を Gemini CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む
2. **skill 本体を読み込む**: `.claude/skills/udr-review/SKILL.md` を読み、その 9 観点チェックに **厳密に** 従って実行する
3. **全 UDR を収集**: `.udr/records/UDR-*.yaml` を全件読み込む

## 9 観点チェック

| 観点 | 検出方法 |
|---|---|
| Orphan（孤立） | `depends_on` / `triggers` が空かつ他 UDR からも参照されておらず、`updated` が `orphan_age_days`（既定 30）日以上前 |
| ステータス不整合 | `deprecated` なのに置き換え先の逆リンクがない / `proposed` が `ai_pending_days`（既定 7）日以上放置 / `superseded` なのに自身に `supersedes` がない |
| 未承認 AI 単独判断 | `authors` が全員 `ai-agent` かつ `status: proposed` のまま `ai_pending_days` 日以上経過 |
| 棄却理由欠落 | `options.rejected` が 0 件 |
| DAG 健全性 | 循環参照・存在しない ID への参照（dangling link）・500 件閾値の超過警告 |
| YAML 健全性 | パース可否・`:␣` 混入によるパース破壊の検出と自動クォート救済 |
| sync 陳腐化 | 各コンテキストファイルの `synced <UTC ISO>` から `sync_stale_days`（既定 7）日以上経過 |
| code_refs 未記入 | `status: accepted` かつ `domain in (architecture, design)` で `code_refs` が存在しない |
| 放置 draft | `status: draft` かつ `updated` から `draft_stale_days`（既定 3）日以上経過 |

## 直接実行コマンド例

```bash
# 棄却理由が 0 件のファイルを検出
for f in .udr/records/UDR-*.yaml; do
  rejected=$(grep -c "verdict: rejected" "$f" || true)
  if [ "$rejected" -eq 0 ]; then
    echo "WARN: no rejected option: $f"
  fi
done

# proposed のまま放置（30日以上）
python3 -c "
import yaml, pathlib, datetime
threshold = datetime.date.today() - datetime.timedelta(days=30)
for p in pathlib.Path('.udr/records').glob('UDR-*.yaml'):
  with open(p) as f:
    data = yaml.safe_load(f)
  if data.get('status') == 'proposed':
    d = data.get('date', data.get('updated'))
    if d and d < threshold:
      print(f'STALE proposed: {p} (date: {d})')
"
```

## 出力形式

問題を重篤度順に列挙し、改善アクション（修正コマンドまたは対話手順）を提示する。
