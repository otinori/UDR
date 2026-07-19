# /udr-trace — UDR 依存関係トレース

UDR の依存関係 (depends_on / triggers / supersedes) を DAG として走査し、上流 (前提) ・下流 (波及) ・双方向を深度指定で辿る。Claude Code の `/udr-trace` skill と等価な動作を Codex CLI で行うラッパー。

## 引数

`$ARGUMENTS` — UDR ID と任意のオプション。例:
- `UDR-atlas-20260423T1430-a3f` (基本: 双方向 depth=2)
- `UDR-atlas-20260423T1430-a3f --upstream --depth=3` (上流のみ)
- `UDR-atlas-20260423T1430-a3f --impact` (変更影響分析モード、domain/severity 別集計と critical path 抽出)

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読み、relations の種類と循環検出ルールを理解する
2. **skill 本体を読み込む**: `.claude/skills/udr-trace/SKILL.md` を読み、その走査ロジック (FR-005 / FR-006 / FR-007) に従って実行する
3. DAG をテキストで可視化する (インデントベースのツリー表示)。`--impact` 指定時は domain / severity 別の影響件数と critical path を併記する

## 重要な制約

- 循環参照を検出した場合はパス (例: `A → B → C → A`) を明示してエラー報告
- `status in (superseded, rejected)` のノードは終端として扱い、それ以上辿らない
- 深度のデフォルトは 2、最大 5 までの制限
