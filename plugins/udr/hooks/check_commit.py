#!/usr/bin/env python3
"""UDR PreToolUse hook: git commit 実行前に判断記録 (/udr-record) を軽くリマインドする。

設計方針 (IM-04 のコミット連携トリガーに対応):
- 非ブロッキング。permissionDecision は一切返さず、additionalContext のみ提示する。
- 絶対パスは書かない。プロジェクトルートは環境変数 CLAUDE_PROJECT_DIR
  （Claude Code がプラグイン hook プロセスに自動で渡す）から取得する。
- .udr/records/ が存在しない（UDR 未初期化）プロジェクトでは何もしない。
- .udr/config.yaml の hooks.enabled が true でない（既定 = 未設定 = 無効）
  プロジェクトでは何もしない。/udr-init Step 2.7 で opt-in する設計（python3
  非依存で UDR の基本機能が動くようにするため、既定は無効側に倒している）。
- PyYAML 等の追加依存を持ち込まない（標準ライブラリのみ、Phase 1 PoC の
  「LLM/外部ライブラリ依存なし」方針 C-006/C-007 に準拠）。
"""
import json
import os
import sys


def hooks_enabled(project_dir):
    """.udr/config.yaml の hooks.enabled を簡易パースする。未設定/読めない場合は False。"""
    config_path = os.path.join(project_dir, ".udr", "config.yaml")
    try:
        with open(config_path, encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return False

    in_hooks_block = False
    for line in lines:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if indent == 0:
            in_hooks_block = stripped == "hooks:"
            continue
        if in_hooks_block and stripped.startswith("enabled:"):
            value = stripped[len("enabled:"):].strip().strip('"').lower()
            return value == "true"
    return False


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "."
    udr_dir = os.path.join(project_dir, ".udr", "records")

    if not os.path.isdir(udr_dir) or not hooks_enabled(project_dir):
        print(json.dumps({"continue": True}))
        return

    message = (
        "[UDR reminder] このコミットに非自明な判断（アーキ選定・要件解釈・技術選定など）が"
        "含まれる場合は /udr-record で記録してください（棄却した選択肢と理由も必須、BR-007）。"
        "記録済み、または該当なしならこのリマインドは無視して構いません。"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": message,
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
