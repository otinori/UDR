---
name: udr-search
description: UDR を ID 指定 / フィールドフィルタ / 全文キーワード検索の 3 モードで取得する。全文検索は Stage1 決定的スコアリング (title×3, decision×2, context×1, options×1) を既定とし、0 件 / 低スコア時のみ Stage2 AI エスカレート探索を行う 2 段階ハイブリッド方式 (FR-002、UDR-UDR-20260711T0728-f9f)。
---

# udr-search — UDR 検索 skill

> **前提:** `.claude/skills/_udr-shared/CONVENTIONS.md` を先読み。

## 3 つの検索モード

### Mode 1. ID 直接取得

user が `UDR-<repo>-<ts>-<rand>` 形式の ID を指定した場合:

1. `.udr/records/<id>.yaml` を Read
2. 存在すれば full YAML を整形して表示
3. 不在なら `UDR-SEARCH-404` エラー

### Mode 2. フィールドフィルタ (AND 結合)

user が以下の key=value を指定した場合:

| フィルタキー | 値 | 対応 YAML フィールド |
|---|---|---|
| `domain` | architecture など | `domain` |
| `status` | proposed / accepted / deprecated / superseded / rejected | `status` |
| `severity` | high / medium / low | `severity` |
| `pinned` | true / false | `pinned` |
| `author` | 名前 | `authors[].name` の部分一致 |
| `role` | human / ai-agent / reviewer | `authors[].role` |
| `tag` | 文字列 | `tags[]` 部分一致 |
| `code` | ファイルパス | `code_refs[].path` 部分一致 |
| `owner` | 名前 | `owner` フィールド完全一致 |
| `after` | YYYY-MM-DD | `date >=` |
| `before` | YYYY-MM-DD | `date <=` |

処理:

1. `.udr/records/*.yaml` を Glob で列挙
2. 各ファイルの YAML を Read → メタ情報を抽出
3. フィルタを AND で適用
4. **デフォルトで `status: superseded` は除外** (HO-09、user が明示 `status=superseded` を指定した場合のみ含める)
5. 件数 + 1 行サマリ一覧を返す

### Mode 3. 全文キーワード検索（Stage1 決定的スコアリング → Stage2 AI エスカレートの 2 段階ハイブリッド、UDR-UDR-20260711T0728-f9f）

user がフリーテキストクエリを渡した場合、まず Stage1 を実行し、条件を満たした場合のみ Stage2 に進む。

#### Stage1（既定・決定的スコアリング）

1. `.udr/records/*.yaml` を Glob
2. 各ファイルに対して以下の重み付きスコアリング:

```
score  = title_hits    × 3
       + decision_hits × 2
       + context_hits  × 1
       + options_hits  × 1  (name + rationale + pros + cons の合算)

全 query トークン (空白区切り) について AND 結合で検索。
大文字小文字無視、部分一致可、正規表現は使わない。
```

3. score > 0 のファイルをスコア降順でソート
4. Stage2 へのエスカレート判定（下記いずれかに該当すれば Stage2 へ）:
   - **ヒット件数が 2 件未満**（0 件、または強い 1 件ヒットのみの場合を含む。1 件だけの強いヒットは「表記ゆれの見落としがないか」を確認すべきサインであり、score の高さでは救えないため件数を主条件とする）
   - 上位ヒットの score が 3 未満（title/decision に一致がなく、context/options の弱い一致のみ）
   - query に長さ 2 文字以下の英数トークンを含む（例: `CI` が `Citus`/`Glacier` 等の部分文字列に誤ヒットしやすいため、Stage1 のヒット自体の真陽性確認が必要）
5. 上記いずれにも該当しなければ、上位 `limit` 件（デフォルト 20）を 1 行サマリで返して終了（Stage2 は実行しない）

#### Stage2（AI エスカレート探索、条件付き実行）

**目的:** 表記ゆれ・同義語（例: クエリ「認証」に対する記録側の「SSO」「ログイン基盤」）による再現率低下と、短トークンの部分一致誤検出を補う。実測シミュレーション（UDR-UDR-20260711T0728-f9f）で Stage1 単独は表記ゆれ 5 組中 5 組を取りこぼし、短トークンクエリでは precision 25% まで低下することを確認済み。**なお初版のエスカレート条件（0 件 / score<3 / 短トークンのみ）は独立 3 回のシミュレーションで、5 組中 4 組（強い 1 件ヒットが存在するケース）が一度も Stage2 に到達しないという欠陥が発見されたため、上記「ヒット件数 2 件未満」条件を追加して修正した。

処理:

1. `.udr/records/*.yaml` の全ファイルを Read し、title / context / decision / options を通読する
2. query の同義語・関連語（表記ゆれ、略語展開、類義表現）を踏まえて意味的な関連性を判断する
3. Stage1 でヒットしていたファイルについては、短トークン誤ヒット（無関係な単語内の部分文字列一致）でないか再確認し、誤検出なら除外する
4. 追加で関連すると判断したファイルは、判断根拠を 1 行添えて結果に含める
5. embedding・外部 API・ベクトル DB など新規の外部依存は一切使わない（Read/Glob/`/udr-trace` の追加ラウンドのみ。C-006/C-007 の根本動機であるポータビリティ確保に抵触しないための制約）

**出力上の注意:** Stage2 の結果は Stage1 の決定的スコアと異なり非決定的（実行ごとに変動しうる）。一覧の各行に `[Stage2]` を付与し、Stage1 のみで完結した結果と明確に区別すること。

## 出力フォーマット

### 単一取得 (Mode 1)

full YAML を表示した後、末尾に:

```
---
関係 (DAG):
  depends_on: UDR-xxx (件), UDR-yyy
  triggers:   UDR-zzz
次のアクション:
  - 上下流追跡: /udr-trace <id>
  - 更新:       このファイルを直接 Edit し /udr-sync
```

### 一覧 (Mode 2 / 3)

```
<N> 件ヒット (query: "<入力>")

1. UDR-udr-20260423T1430-a3f  [architecture] accepted pinned
   認証基盤に OAuth2.0+PKCE を採用
   棄却: SAML, 独自トークン  |  深度: depends=2 triggers=2
   score: 17

2. UDR-udr-20260418T0901-8e2  [design]        accepted
   ...
```

Mode 3 で Stage2 が実行された場合は、末尾に区切りを入れて追加ヒットを提示する:

```
<N> 件ヒット (query: "<入力>", Stage1: <n1> 件 / Stage2 追加: <n2> 件)

1. UDR-udr-20260423T1430-a3f  [architecture] accepted
   ...
   score: 8

--- Stage2 エスカレート（表記ゆれ・同義語による追加ヒット、非決定的） ---

2. [Stage2] UDR-udr-20260501T0900-c1d  [architecture] accepted
   SAML SSO によるログイン基盤刷新
   判断根拠: クエリ「認証」と同義（SSOはID連携文脈での認証方式）
```

## ショートカット

- 引数なし: 「最近の UDR 20 件」(`updated` 降順) を表示
- `pinned` 単独: pinned のみ一覧
- `orphan`: `depends_on` も `triggers` も空で、かつ他からも参照されていない UDR 一覧 (`/udr-review` のサブセット)
- `ai-only`: `authors` 全員が ai-agent の UDR 一覧 (承認待ち確認用)
- `tag:<name>`: 指定タグを持つ UDR 一覧（例: `tag:sprint-7`）
- `code:<path>`: 指定パスを `code_refs` に持つ UDR 一覧（コード→UDR 逆引き、例: `code:src/auth`）
- `owner:<name>`: 指定者が最終判断者の UDR 一覧

## エラーコード

| Code | 条件 |
|---|---|
| UDR-SEARCH-001 | `.udr/records/` 不在 |
| UDR-SEARCH-404 | Mode 1 で ID 不在 |
| UDR-SEARCH-010 | YAML パース失敗 → 該当ファイルパスを提示し、構造修正を促す |

## 性能目安 (NFR-001)

- Stage1: 500 件以下で 1 秒以内を目標
- Stage2: NFR-001 の対象外（全文 Read を伴うため件数に比例してコストが増える）。エスカレート条件（Mode 3 §Stage1 手順 4）を満たした場合のみ実行し、常時実行はしない
- **「ヒット件数 2 件未満」条件により、Stage2 は単一の強いヒットしかない一般的なクエリでも頻繁に発火する。** これは表記ゆれの見落としを防ぐための意図的なトレードオフ（UDR-UDR-20260711T0728-f9f）であり、コストが問題になる場合は `--stage1-only` 等での抑制をユーザーが選べるようにすることを今後の検討事項とする
- 500 件超: `/udr-review` で棚卸しを案内（NFR-005 / C-009）
