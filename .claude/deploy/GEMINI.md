# GEMINI.md — Gemini CLI 作業ガイド (UDR テンプレート)

> **このファイルはテンプレートです。** UDR の `install.sh --gemini` で生成される雛形。プロジェクトに合わせて編集してください。

**最初に `AGENTS.md` を必ず読むこと（存在する場合）。** UDR 自動検知ポリシー・プロジェクト構成のマスタは `AGENTS.md` に集約されている。本書は Gemini CLI 固有の追加指示のみを扱う。

---

## UDR 操作の実行方法

Gemini CLI は Claude Code の `/udr-record` 等のスキルを直接呼び出せない。代わりに、以下の **プロンプトテンプレート** を参照して同等の動作を実現する。

| 操作 | テンプレートファイル |
|---|---|
| 初期化 | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-init.md` |
| 記録 | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` |
| 検索 | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-search.md` |
| 同期 | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-sync.md` |
| 追跡 | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-trace.md` |
| 棚卸し | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-review.md` |
| ダッシュボード | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-dashboard.md` |

Gemini の操作例:
```
@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md
判断を記録してください: ...
```

## UDR 候補の検知

`.udr/config.yaml` の `tools` に `gemini` が含まれる場合、判断が発生したら応答末尾に付記:

```
[UDR 候補] 「<一行要約>」を記録しますか？
  Y → gemini-prompts/udr-record.md を参照   N → スキップ   D → gemini-prompts/udr-search.md で検索
```

## 手動記録（テンプレートなし）

`AGENTS.md §4` のテンプレートで `.udr/records/<id>.yaml` を直接作成できる。
ID 生成: `UDR-$(cat .udr/config.yaml | grep repo_short | awk '{print $2}')-$(date -u +%Y%m%dT%H%M)-$(printf '%03x' $((RANDOM % 4096)))`

---

## UDR サマリ（`/udr-sync` で自動更新、編集不可）

<!-- [UDR-SYNC-START] -->
<!-- [UDR-SYNC-END] -->

---

*UDR v0.6.0.2-PoC / このファイルは `install.sh --gemini` で生成されました*
