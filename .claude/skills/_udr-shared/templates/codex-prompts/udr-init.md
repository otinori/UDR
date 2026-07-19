# /udr-init — UDR プロジェクト初期化

UDR (Universal Decision Record) のプロジェクト初期化を実行する。Claude Code の `/udr-init` skill と等価な動作を Codex CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読み、UDR の ID 体系・スキーマ・status 遷移・sync マーカー規約を理解する
2. **skill 本体を読み込む**: `.claude/skills/udr-init/SKILL.md` を読み、その手順 (Step 1 〜 Step 5) に **厳密に** 従って実行する
3. ファイル操作は Read/Write/Edit/Bash を使い、必要な user 確認 (repo_short の決定、既存レコードの保持/削除など) を必ず取る
4. 実行完了後、生成・更新したファイル一覧と、検出した警告・エラーを user に報告する

## 重要な制約

- skill の手順を変更・省略しない。判断分岐 (config.yaml の有無、repo_short 一致/不一致) は SKILL.md §Step 2 のとおり処理する
- sync_targets への書き込みでは AGENTS.md / CLAUDE.md には `policy+compact` 形式 (UDR プロトコル + 要約) を、`.github/copilot-instructions.md` には `policy-only` 形式を、`.github/instructions/udr-decisions.instructions.md` には `detailed` 形式を使う
- audit.log への init 操作の記録を忘れないこと
