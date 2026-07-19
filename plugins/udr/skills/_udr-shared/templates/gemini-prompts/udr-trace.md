# /udr-trace — 依存関係 DAG 追跡

UDR の依存関係（depends_on / triggers / supersedes）を DAG として走査し、変更影響分析を行う。Claude Code の `/udr-trace` skill と等価な動作を Gemini CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む（特に §4 relations 仕様）
2. **skill 本体を読み込む**: `.claude/skills/udr-trace/SKILL.md` を読み、その DAG 走査ロジックに **厳密に** 従って実行する
3. **対象 UDR の特定**: 引数の ID から `.udr/records/<id>.yaml` を読み込む
4. **走査方向**:
   - `--upstream` / デフォルト: `depends_on` を再帰的に遡る（前提となる判断）
   - `--downstream`: `depends_on` の逆引き（この判断に依存しているもの）
   - `--impact`: `triggers` と `supersedes` を含む全方向走査
5. **循環検出**: 訪問済みノードを追跡し、循環を検出したら警告
6. **出力**: DAG をテキスト木構造で表示、domain/severity 別集計を付加

## 直接実行コマンド例

```bash
TARGET_ID="UDR-UDR-20260424T1430-a3f"

# 上流（前提）を確認
grep -A 5 "^relations:" .udr/records/${TARGET_ID}.yaml

# この UDR に depends_on しているものを検索
grep -rl "${TARGET_ID}" .udr/records/ | xargs grep -l "depends_on"

# supersedes チェーンを確認
grep -H "supersedes" .udr/records/UDR-*.yaml
```

## 出力形式

```
UDR-XXX (起点)
  ├── depends_on → UDR-YYY (前提)
  │     └── depends_on → UDR-ZZZ (前提の前提)
  └── triggers → UDR-WWW (派生)

影響集計:
  architecture: 2件, requirements: 1件
  critical path: UDR-ZZZ → UDR-YYY → UDR-XXX
```
