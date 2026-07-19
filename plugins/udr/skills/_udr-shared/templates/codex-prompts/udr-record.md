# /udr-record — 判断の対話的記録

判断 (アーキ選定・要件解釈・技術選定など) を UDR YAML として対話的に記録する。Claude Code の `/udr-record` skill と等価な動作を Codex CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読み、ID 体系・スキーマ・status 遷移・ai-agent 判定パターンを理解する
2. **未初期化チェック**: `.udr/config.yaml` が存在しなければ `/udr-init` の実行を user に提案して中断する
3. **skill 本体を読み込む**: `.claude/skills/udr-record/SKILL.md` を読み、その対話フロー (Phase A 必須3項目 → Phase B 任意3項目 → Phase C メタ確定) に **厳密に** 従って実行する
4. 完成した YAML を `.udr/records/UDR-<repo_short>-<UTC YYYYMMDDTHHmm>-<rand3>.yaml` に書き込み、audit.log にも記録する
5. 記録後、`/udr-sync` の実行を提案する

## 重要な制約

- **棄却理由のヒアリングは必須** (BR-007 / FR-015)。棄却 0 件のまま進めるのは「本当に選択の余地がなかったか」を 1 回確認した後のみ
- AI 単独 (authors が ai-agent のみ) の判断は `status: proposed` 強制 (BR-002)
- 循環参照は新規作成時に DAG 走査で検出、検出時はブロック (FR-007)
- skip された任意項目は YAML から **キー自体を省略** (PO2-02、`null` や `[]` で書かない)
