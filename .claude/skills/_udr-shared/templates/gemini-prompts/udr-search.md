# /udr-search — UDR 検索

既存 UDR を ID 指定・フィールドフィルタ・全文キーワード検索の 3 モードで取得する。Claude Code の `/udr-search` skill と等価な動作を Gemini CLI で行うラッパー。

## 実行手順

1. **共通規約を読み込む**: `.claude/skills/_udr-shared/CONVENTIONS.md` を読む
2. **skill 本体を読み込む**: `.claude/skills/udr-search/SKILL.md` を読み、その検索ロジックに **厳密に** 従って実行する
3. **検索モードの判定**:
   - 引数が `UDR-` で始まる → ID 直接検索
   - `domain:`, `status:`, `severity:` を含む → フィールドフィルタ
   - それ以外 → 全文検索（スコア: title×3, decision×2, context×1, options×1）

## 直接実行コマンド例

```bash
# 全 UDR 一覧
ls .udr/records/UDR-*.yaml

# タイトル検索
grep -H "^title:" .udr/records/UDR-*.yaml | grep -i "<keyword>"

# 全文検索
grep -rl "<keyword>" .udr/records/

# domain でフィルタ
grep -l "^domain: architecture" .udr/records/UDR-*.yaml

# 特定 UDR の全文表示
cat .udr/records/<id>.yaml
```

## 出力形式

結果は以下の形式で表示する:
- ID（リンク形式）
- title
- domain / status / severity
- decision の1行要約
- 関連する棄却選択肢の summary
