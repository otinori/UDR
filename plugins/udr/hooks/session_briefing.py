#!/usr/bin/env python3
"""UDR SessionStart hook: セッション開始時に判断記録の状態を簡潔にブリーフィングする。

設計方針:
- 非ブロッキング。additionalContext のみ提示する。
- 絶対パスは書かない。プロジェクトルートは環境変数 CLAUDE_PROJECT_DIR から取得する。
- .udr/records/ が存在しない（UDR 未初期化）プロジェクト、記録が 0 件のプロジェクト、
  .udr/config.yaml の hooks.enabled が true でない（既定 = 未設定 = 無効）プロジェクト
  では何も出力しない。/udr-init Step 2.7 で opt-in する設計。
- 「判断待ち draft の放置」(udr-review 観点9) と「AI 単独 proposed の承認待ち」
  (udr-review 観点3) の 2 点のみを軽量にチェックする。詳細な棚卸しは /udr-review
  に委ね、本 hook は "気づき" のトリガーに徹する。
- YAML を厳密パースせず単純な行走査で済ませる（PyYAML 等の追加依存を持ち込まない、
  Phase 1 PoC の C-006/C-007 方針に準拠）。
"""
import datetime
import glob
import json
import os
import sys


def read_field(text, key):
    prefix = key + ":"
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(prefix):
            return line[len(prefix):].strip().strip('"')
    return None


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


def age_days(date_str, today):
    if not date_str:
        return None
    try:
        return (today - datetime.date.fromisoformat(date_str)).days
    except ValueError:
        return None


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

    today = datetime.date.today()
    total = 0
    stale_drafts = []
    ai_pending = []

    for path in sorted(glob.glob(os.path.join(udr_dir, "*.yaml"))):
        try:
            with open(path, encoding="utf-8") as f:
                text = f.read()
        except OSError:
            continue

        total += 1
        record_id = os.path.splitext(os.path.basename(path))[0]
        status = read_field(text, "status")
        days = age_days(read_field(text, "updated"), today)

        if status == "draft" and days is not None and days >= 3:
            stale_drafts.append(record_id)
        elif status == "proposed" and days is not None and days >= 7 and "role: human" not in text:
            ai_pending.append(record_id)

    if total == 0:
        print(json.dumps({"continue": True}))
        return

    lines = ["[UDR] .udr/records/ に {0} 件の判断記録があります。".format(total)]
    if stale_drafts:
        lines.append(
            "判断待ち draft {0} 件: {1}".format(len(stale_drafts), ", ".join(stale_drafts))
        )
    if ai_pending:
        lines.append(
            "AI 単独提案で承認待ち {0} 件: {1}".format(len(ai_pending), ", ".join(ai_pending))
        )
    if stale_drafts or ai_pending:
        lines.append("詳細は /udr-review、一覧は /udr-dashboard で確認できます。")

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
