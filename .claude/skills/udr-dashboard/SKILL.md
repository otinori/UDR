---
name: udr-dashboard
description: UDR の判断状況を 1 枚の自己完結 HTML (udr_dashboard.html) として出力する。集計 (status/domain/severity 別)・pinned・全 UDR 一覧 (検索/フィルタ/行展開で decision・棄却理由・constraints・code_refs・owner)・依存関係 (depends_on/triggers/supersedes/superseded_by)・tags フィルタを可視化する。外部依存なし・オフライン閲覧可。`/udr-dashboard` で呼ぶ (FR-013 補完 / D-1/D-4 可視化)。
---

# udr-dashboard — UDR ダッシュボード出力 skill

> **前提:** `.claude/skills/_udr-shared/CONVENTIONS.md` を先読み。

## 目的

`.udr/records/` の全 UDR を読み取り、判断状況を俯瞰できる **単一 HTML ファイル `udr_dashboard.html`** を生成する。ブラウザでローカルに開くだけで動く (外部 CDN・ビルド・サーバ不要)。

- UDR の差別化ポイント **[D-1] DAG / [D-4] 棄却理由の可視化** を人間が一目で確認できるようにする。
- 既定の出力先はリポジトリ直下 `udr_dashboard.html`。`--out <path>` で変更可。

## 処理フロー

### Step 1. 収集

1. `.udr/records/*.yaml` を Glob → 各ファイルを Read してパース。
2. `.udr/config.yaml` を Read (`project.name` / `repo_short` を表示に使う)。
3. レコード 0 件なら、空状態メッセージ入りの HTML を出力して終了 (エラーにしない)。

### Step 2. 集計

各レコードから以下を算出する:

- **総数**、`status` 別 (draft/proposed/accepted/deprecated/superseded/rejected) の件数
- `domain` 別、`severity` 別の件数
- `pinned: true` の一覧
- 各レコードの **棄却選択肢数** = `options[].verdict == rejected` の数
- 関係: `relations.depends_on` / `triggers` / `supersedes` / `superseded_by` の件数とリンク先 ID
- **全レコード横断の一意タグ一覧** (`tags` フィールドを集約 → フィルタ用 `<option>` 生成)
- `owner` / `code_refs` の有無フラグ（展開行の表示制御用）

### Step 3. HTML 生成

下記テンプレートの `{{...}}` を実データで置換して **1 ファイル**を組み立てる。CSS / JS はインライン。

- 一覧テーブルの各行は **クリックで展開**し、**まず「やさしい解説」(下記「人間向けやさしい解説の生成」節参照) を表示してから** `decision` / `constraints` / 採用・棄却の選択肢 + rationale / `code_refs` / `owner` を表示する (棄却理由を強調表示)。
- 上部に **検索ボックス** (id/title/decision/owner 部分一致) と **status / domain / tag / severity フィルタ** を置く (素の JS、依存なし)。
- **上部サマリカードは全種類クリック可能にする** (total=全件表示に戻る `resetAll()` / status 別各カード=`setStatus(status)` / pinned=`setPinned()` / high severity=`setSeverity('high')`)。draft カードだけを特別扱いせず、9 枚全カードに同じ操作性を持たせる (2026-07-19 時点の運用フィードバックで、draft 以外のカードが押せないのは一貫性を欠くと判明したため必須化)。
- **依存関係 DAG をグラフとして可視化する** (下記「DAG グラフ生成」節参照)。ノードクリックで対応レコードに絞り込み・詳細展開・スクロールする (`focusId(shortId)`)。
- `tags` は行の title 列にピル表示。`tag フィルタ` で絞り込み可（スプリント別・マイルストーン別の確認を想定）。
- `relations` を持つレコードは依存リンク (`→ <id>`) を表示。`superseded_by` がある場合は「後継→ <id>」を明示して旧→新の追跡を可能にする。
- `constraints` がある場合は警告色ボーダーで強調表示。
- `code_refs` はモノスペースで path + note を表示（コード→UDR 逆引きの手がかり）。
- `owner` がある場合は展開行の先頭に責任者バッジを表示。
- `status` は色分け (accepted=緑 / proposed=黄 / deprecated=灰 / superseded=取消線 / rejected=赤)。
- XSS 防止のため、YAML 由来の文字列は HTML エスケープして埋め込む (`&`,`<`,`>`,`"` を実体参照に)。

#### DAG グラフ生成 (2026-07-19 追加)

サマリカードの下・フィルタコントロールの上に、`relations.depends_on` から構築した依存関係グラフを SVG で描画する。

1. **グラフ構築**: 各レコードの `relations.depends_on[].id` を辺とする。矢印の向きは `depends_on` を反転し、**前提 (upstream) → 帰結 (downstream)** で描く（例: B が A に depends_on なら、矢印は A→B）。
2. **レイヤー配置**: 各ノードのレイヤー = `depends_on` を持たなければ 0、持てば「参照先レイヤーの最大値 + 1」。同一レイヤー内は縦に並べる (例: x = layer × 300px、y = レイヤー内インデックス × 120px + 70px、viewBox は概ね `0 0 <layer数×300+100> <最大行数×120+100>`)。
3. **孤立ノード** (`depends_on` を持たず、かつどのレコードからも参照されていない) は、通常のレイヤー配置とは視覚的に区別する: 枠線を黄色破線 (`stroke="#d29922" stroke-dasharray="4 3"`) にし、ノード下に「(孤立・関連なし)」の小さいラベルを添える。
4. **ノード表現**: 半径 34 の円 + 中央に `{{id_short}}` (末尾 rand3) + 円下にタイトルの短縮ラベル (目安 12〜16 文字、超える場合は「…」で省略) + `<title>` 要素にフル ID とタイトルを入れてホバー時のツールチップにする。円の枠色は一覧の `status` 色分けと合わせる (accepted=緑 `--ok` / proposed=黄 `--warn` / deprecated=灰 `--mut2` / superseded=灰・取消線相当 / rejected=赤 `--bad` / draft=青 `--blue`)。
5. **辺の描画**: `<line>` + 矢印マーカー (`<marker id="arrow">`、`#8b90a0` の三角形) で結ぶ。`supersedes` がある場合は同じ矢印方向 (旧→新) だが色を変える (例: `stroke="#f85149"`) などして `depends_on` 由来の辺と視覚的に区別する。
6. **クリック挙動**: 各ノード `<g class="dnode" onclick="focusId('{{id_short}}')">` として、クリックで一覧テーブルをそのレコードに絞り込み・該当行の詳細を展開・スクロール表示する。
7. **レコード件数が多い場合** (目安 20 件超): 全件を 1 枚のグラフに詰め込むと可読性が落ちるため、`depends_on`/`triggers`/`supersedes` のいずれも持たない孤立ノードをグラフから省き「孤立レコード N 件 (一覧で確認)」のような注記に置き換えることを検討する。
8. グラフ下に凡例 (矢印の意味・色分けの意味・「ノードクリックで絞り込み」の説明) を小さく添える。

#### 人間向けやさしい解説の生成 (2026-07-19 追加)

UDR の YAML はそもそも AI が読み書きする前提の仕様（技術用語・略語・社内固有のID等を含む）だが、
このダッシュボードは人間（技術的背景を持たない第三者も含む）が眺めて概要をつかむ用途を兼ねる。
各レコードの詳細展開行の **先頭**（`owner` バッジより前、`decision` セクションより前）に、
専門知識のない読み手（例: 文系大学1〜2年生）でも読める「やさしい解説」ブロックを追加する。

- 元にする情報: `title` / `context` / `decision` / 採用理由 / 主要な棄却理由（1〜2件で十分、全棄却案を網羅しなくてよい）。
- 書き方の基準（`project-settings` の `docs-check`/`init-project` skill が定める文書規約と同じ方針を踏襲）:
  - 専門用語（YAML・DAG・MCP・Git・エージェント等）は初出時に一言かっこ書きで説明する（例:「Git（変更履歴を管理する仕組み）」）。
  - 可能な範囲で比喩・具体例を使い、正確さを保ったまま平易にする（数値・固有名詞などの正確性は落とさない）。
  - 分量は3〜6行程度。「何が問題だったか」「何を決めたか」「なぜそれが良いと判断したか」の3点を平易な言葉で押さえる。
  - 技術的な `decision`/`options[].rationale` セクションは省略・置換せず、やさしい解説の**後に**そのまま残す（技術者はスクロールして詳細を読める）。
- HTML 上は `.plain` クラスのブロックとして、青系の左ボーダー + 📝 アイコン付きラベルで他のセクションと視覚的に区別する（下記テンプレート参照）。
- レコードが `draft` の場合や情報が薄い場合でも、書ける範囲でやさしい解説を書く（無理に長くしない）。

#### テキスト整形: YAML の折り返し改行を残さない (2026-07-19 追加)

`context` / `decision` / `options[].rationale` 等の自由記述フィールドは、YAML 側でブロックリテラル (`|`) を使い**可読性のため約70字で折り返して**いる。この折り返し改行をそのまま HTML にコピーして `white-space:pre-wrap` で表示すると、文中の不自然な位置に改行が入って読みにくくなる。HTML へ書き出す際は次のルールで整形する:

- YAML 上の**単純な折り返し改行**（段落途中の改行）は取り除き、**そのまま連結**する（日本語なので単語間にスペースは入れない）。
- YAML 上の**空行（段落区切り）**は、意図的な段落分けとして扱い、`<p>` 要素を分けて出力する（`<br><br>` ではなく別 `<p>`）。
- 上記の変換を行った後は `white-space:pre-wrap` は不要（通常の折り返しに任せる）。`decision` は `{{decision_paragraphs}}`（段落ごとの `<p>` 群）、`options[].rationale` は `{{opt_*.rationale_formatted}}`（同様に整形済みテキスト）としてテンプレートに渡す。
- この整形は「やさしい解説」ブロックにも同様に適用する（新規執筆する文章なので通常は該当しないが、長文になる場合は同じ基準で段落分けする）。

### Step 4. 書き込みと報告

1. `udr_dashboard.html` (既定) を Write で出力 (既存は上書き)。
2. user に「出力先パス / 集計サマリ (総数・status 別) / ブラウザで開く案内」を報告。
3. audit.log に追記 (任意): `{"ts":...,"op":"dashboard","id":null,"record_count":<N>}`。

> このファイルは生成物のため `.gitignore` に `udr_dashboard.html` を含めることを推奨 (init が設定する)。

## HTML テンプレート (骨子)

```html
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UDR Dashboard — {{project_name}}</title>
<style>
  :root{--bg:#0f1117;--card:#1a1d27;--fg:#e6e8ee;--mut:#8b90a0;--line:#2a2e3a;
        --ok:#3fb950;--warn:#d29922;--bad:#f85149;--mut2:#6e7681;--blue:#58a6ff;}
  *{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);
    font:14px/1.6 system-ui,"Segoe UI",sans-serif}
  header{padding:20px 24px;border-bottom:1px solid var(--line)}
  h1{margin:0;font-size:18px} .sub{color:var(--mut);font-size:12px;margin-top:4px}
  .wrap{padding:20px 24px;max-width:1200px;margin:0 auto}
  .cards{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:8px;
        padding:12px 16px;min-width:110px;cursor:pointer} .card .n{font-size:24px;font-weight:700}
  .card:hover{background:#20242f;border-color:#3a3f4d}
  .card .l{color:var(--mut);font-size:12px}
  .dnode:hover circle{filter:brightness(1.4)}
  .controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center}
  input,select{background:var(--card);color:var(--fg);border:1px solid var(--line);
        border-radius:6px;padding:6px 10px;font-size:13px}
  input{min-width:220px}
  table{width:100%;border-collapse:collapse} th,td{text-align:left;padding:8px 10px;
        border-bottom:1px solid var(--line);vertical-align:top}
  th{color:var(--mut);font-size:12px;font-weight:600}
  tr.row{cursor:pointer} tr.row:hover{background:#20242f}
  /* status pills */
  .pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:11px}
  .s-draft{background:rgba(88,166,255,.15);color:var(--blue);border:1px dashed var(--blue)}
  .s-accepted{background:rgba(63,185,80,.15);color:var(--ok)}
  .s-proposed{background:rgba(210,153,34,.15);color:var(--warn)}
  .s-deprecated{background:rgba(110,118,129,.2);color:var(--mut2)}
  .s-superseded{color:var(--mut2);text-decoration:line-through}
  .s-rejected{background:rgba(248,81,73,.15);color:var(--bad)}
  /* draft rows: dashed border to signal incompleteness */
  tr.row[data-s="draft"]{opacity:0.85}
  tr.row[data-s="draft"] td:first-child::after{content:" 🤔";font-size:11px}
  /* tag pills */
  .tag{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;
       background:rgba(88,166,255,.15);color:var(--blue);margin:1px 2px 0 0;cursor:pointer}
  .tag:hover{background:rgba(88,166,255,.3)}
  /* pin */
  .pin{color:var(--warn)}
  /* detail row */
  .detail{display:none;background:#13161f}
  .detail.open{display:table-row} .detail td{padding:14px 18px}
  /* options */
  .opt{margin:6px 0;padding:8px 10px;border-left:3px solid var(--mut2);background:#161a24;font-size:13px}
  .opt.acc{border-color:var(--ok)} .opt.rej{border-color:var(--bad)}
  .opt .on{font-weight:600;margin-bottom:2px}
  /* constraints */
  .constraints{margin:8px 0;padding:8px 12px;border-left:3px solid var(--warn);
               background:#161a24;font-size:13px}
  .constraints .cl{color:var(--warn);font-size:11px;font-weight:600;margin-bottom:4px}
  /* code refs */
  .crefs{margin:8px 0;font-size:13px}
  .crefs .cl{color:var(--mut);font-size:11px;font-weight:600;margin-bottom:4px}
  .cref{font-family:monospace;font-size:12px;color:var(--blue);background:#161a24;
        padding:2px 6px;border-radius:4px;display:inline-block}
  .cref-note{color:var(--mut);font-size:11px;margin-left:8px}
  /* owner */
  .owner{display:inline-block;font-size:12px;color:var(--mut);margin-bottom:8px}
  .owner b{color:var(--fg)}
  /* plain-language summary (for non-technical readers) */
  .plain{margin:0 0 14px;padding:10px 14px;border-left:3px solid var(--blue);
         background:#101827;font-size:13px;line-height:1.7}
  .plain .cl{color:var(--blue);font-size:11px;font-weight:600;margin-bottom:6px}
  /* relations */
  .rel{color:var(--mut);font-size:12px;margin-top:8px}
  .rel a{color:var(--blue);text-decoration:none}
  .rel-sup{color:var(--ok)}
  .mut{color:var(--mut)}
  /* section label */
  .sec{font-size:11px;font-weight:600;color:var(--mut);margin:10px 0 4px}
</style>
</head>
<body>
<header>
  <h1>UDR Dashboard — {{project_name}}</h1>
  <div class="sub">{{total}} records · generated {{generated_utc}} · repo_short: {{repo_short}}</div>
</header>
<div class="wrap">
  <!-- ── サマリカード: 総数 / status別 / pinned / severity別 (全カードクリック可能) ── -->
  <div class="cards">
    <div class="card" onclick="resetAll()" title="クリックで全件表示">
      <div class="n">{{total}}</div><div class="l">total</div>
    </div>
    <div class="card" onclick="setStatus('accepted')" title="クリックで accepted を絞り込み">
      <div class="n" style="color:var(--ok)">{{n_accepted}}</div><div class="l">accepted</div>
    </div>
    <div class="card" onclick="setStatus('proposed')" title="クリックで proposed を絞り込み">
      <div class="n" style="color:var(--warn)">{{n_proposed}}</div><div class="l">proposed</div>
    </div>
    <div class="card" onclick="setStatus('draft')" title="クリックで draft を絞り込み">
      <div class="n" style="color:var(--blue)">{{n_draft}}</div>
      <div class="l">🤔 判断待ち</div>
    </div>
    <div class="card" onclick="setStatus('deprecated')" title="クリックで deprecated を絞り込み">
      <div class="n">{{n_deprecated}}</div><div class="l">deprecated</div>
    </div>
    <div class="card" onclick="setStatus('superseded')" title="クリックで superseded を絞り込み">
      <div class="n" style="color:var(--mut2)">{{n_superseded}}</div><div class="l">superseded</div>
    </div>
    <div class="card" onclick="setStatus('rejected')" title="クリックで rejected を絞り込み">
      <div class="n" style="color:var(--bad)">{{n_rejected}}</div><div class="l">rejected</div>
    </div>
    <div class="card" onclick="setPinned()" title="クリックで pinned を絞り込み">
      <div class="n" style="color:var(--warn)">{{n_pinned}}</div><div class="l">★ pinned</div>
    </div>
    <div class="card" onclick="setSeverity('high')" title="クリックで high severity を絞り込み">
      <div class="n" style="color:var(--bad)">{{n_high}}</div><div class="l">high severity</div>
    </div>
  </div>

  <!-- ── 依存関係 DAG グラフ (「DAG グラフ生成」節の手順で動的に組み立てる) ── -->
  <h2 style="font-size:14px;margin:0 0 10px">依存関係グラフ (DAG)</h2>
  <div style="background:var(--card);border:1px solid var(--line);border-radius:8px;padding:16px;margin-bottom:20px">
    <svg viewBox="0 0 {{graph_w}} {{graph_h}}" style="width:100%;max-width:{{graph_w}}px;height:auto;display:block;margin:0 auto">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#8b90a0"/>
        </marker>
      </defs>
      {{graph_edges}}
      <!-- <line x1="..." y1="..." x2="..." y2="..." stroke="#8b90a0" stroke-width="2" marker-end="url(#arrow)"/> -->
      {{graph_nodes}}
      <!--
      <g class="dnode" onclick="focusId('{{id_short}}')" style="cursor:pointer">
        <circle cx="{{x}}" cy="{{y}}" r="34" fill="#161a24" stroke="{{status_color}}" stroke-width="2"
                {{isolated ? 'stroke-dasharray="4 3"' : ''}}/>
        <text x="{{x}}" y="{{y+5}}" text-anchor="middle" fill="#e6e8ee" font-size="14" font-family="monospace">{{id_short}}</text>
        <title>{{full_id}} — {{title}}</title>
      </g>
      <text x="{{x}}" y="{{y+48}}" text-anchor="middle" fill="#8b90a0" font-size="10">{{title_short}}</text>
      {{isolated ? '<text x="'+x+'" y="'+(y+62)+'" text-anchor="middle" fill="#6e7681" font-size="9">(孤立・関連なし)</text>' : ''}}
      -->
    </svg>
    <div style="display:flex;gap:16px;flex-wrap:wrap;margin-top:8px;font-size:11px;color:var(--mut)">
      <span>→ = depends_on を反転表示（矢印の始点が前提、終点が帰結）</span>
      <span>枠色 = status（一覧の色分けと同じ）</span>
      <span>┄ 黄破線 = 依存関係を持たないレコード</span>
      <span>ノードクリックで下の一覧を絞り込み・詳細展開</span>
    </div>
  </div>

  <!-- ── フィルタコントロール ── -->
  <div class="controls">
    <input id="q" placeholder="検索 (id / title / decision / owner)" oninput="flt()">
    <select id="fs" onchange="flt()">
      <option value="">status: all</option>
      <option>draft</option><option>accepted</option><option>proposed</option>
      <option>deprecated</option><option>superseded</option><option>rejected</option>
    </select>
    <select id="fd" onchange="flt()">
      <option value="">domain: all</option>{{domain_options}}
    </select>
    <select id="ftag" onchange="flt()">
      <option value="">tag: all</option>{{tag_options}}
      <!-- tag_options: 全レコードの tags を重複排除して <option> 生成 -->
    </select>
    <select id="fsev" onchange="flt()">
      <option value="">severity: all</option>
      <option>high</option><option>medium</option><option>low</option>
    </select>
  </div>

  <!-- ── 一覧テーブル ── -->
  <table id="t">
    <thead>
      <tr>
        <th>ID / pin</th>
        <th>title / tags</th>
        <th>domain</th>
        <th>status</th>
        <th>sev</th>
        <th>owner</th>
        <th>date</th>
        <th>rel</th>
      </tr>
    </thead>
    <tbody>
      <!--
        各レコードにつき row + detail の 2 行を生成。
        data-s=status, data-d=domain, data-tag="タグ スペース区切り",
        data-sev=severity, data-pin="0"|"1", data-q="検索対象テキスト全文" で JS フィルタ。
      -->
      <!--
      <tr class="row"
          data-s="accepted" data-d="architecture"
          data-sev="high" data-pin="0" data-tag="sprint-7 milestone-v2"
          data-q="udr-udr-20260423t1430-a3f oauth2.0 認証基盤 otinori"
          onclick="tg(this)">
        <td style="white-space:nowrap">
          {{id_short}}  ← 末尾 rand3 まで表示 (例: a3f)
          {{pin ? '<span class=pin title="pinned">★</span>' : ''}}
        </td>
        <td>
          {{title}}
          <br>
          {{tag_pills}}  ← <span class="tag" onclick="setTag(event,'sprint-7')">sprint-7</span> ...
        </td>
        <td>{{domain}}</td>
        <td><span class="pill s-{{status}}">{{status}}</span></td>
        <td>{{severity}}</td>
        <td style="font-size:12px;color:var(--mut)">{{owner_or_blank}}</td>
        <td style="white-space:nowrap">{{date}}</td>
        <td class="rel" style="white-space:nowrap">{{rel_summary}}</td>
        <!--
          rel_summary 例: ↑2 ↓1 ⇒1
            ↑ = depends_on 件数
            ↓ = triggers 件数
            ⇒ = supersedes 件数
            後継あり時: 後→1 (superseded_by)
        -->
      </tr>
      <tr class="detail"><td colspan="8">

        <!-- やさしい解説 (「人間向けやさしい解説の生成」節参照。専門知識がない読み手向けの3〜6行要約。必ず decision より前に表示) -->
        <div class="plain">
          <div class="cl">📝 解説</div>
          <p style="margin:0">{{plain_summary}}</p>
        </div>

        <!-- owner バッジ (owner フィールドがある場合のみ) -->
        <div class="owner">責任者: <b>{{owner}}</b></div>

        <!-- decision (改行の扱いは下記「テキスト整形」節を参照。段落ごとに <p> を分ける) -->
        <div class="sec">DECISION</div>
        {{decision_paragraphs}}
        <!-- <p style="margin:0 0 10px">{{段落1}}</p><p style="margin:0 0 10px">{{段落2}}</p> ... -->

        <!-- constraints (ある場合のみ表示) -->
        <div class="constraints">
          <div class="cl">制約 CONSTRAINTS</div>
          {{constraints_items}}
          <!-- <div>・予算上限: $500/月 (2026 Q3 まで)</div> などを並べる -->
        </div>

        <!-- options: accepted → rejected の順に全件表示 -->
        <div class="sec">OPTIONS</div>
        <div class="opt acc">
          <div class="on">✅ 採用: {{opt_acc.name}}</div>
          <div>{{opt_acc.rationale_formatted}}</div>
        </div>
        <div class="opt rej">
          <div class="on">❌ 棄却: {{opt_rej.name}}</div>
          <div>{{opt_rej.rationale_formatted}}</div>
        </div>
        <!-- 棄却案が複数ある場合は繰り返し -->

        <!-- code_refs (ある場合のみ表示) -->
        <div class="crefs">
          <div class="cl">コード参照 CODE REFS</div>
          <!-- <div><code class="cref">src/auth/TokenValidator.java</code>
               <span class="cref-note">JWT 検証ロジックを実装</span></div> -->
          {{code_refs_items}}
        </div>

        <!-- relations: 全4種を表示 -->
        <div class="rel">
          depends_on: {{depends_on_links}} ／
          triggers: {{triggers_links}} ／
          supersedes: {{supersedes_links}}
          {{superseded_by_block}}
          <!-- superseded_by がある場合:
               ／ <span class="rel-sup">後継→ <a href="#UDR-xxx">UDR-xxx</a></span> -->
        </div>

      </td></tr>
      -->
    </tbody>
  </table>
</div>
<script>
// 行展開トグル
function tg(r){
  const d=r.nextElementSibling;
  if(d&&d.classList.contains('detail'))d.classList.toggle('open');
}
// タグクリックでフィルタをセット
function setTag(e,tag){
  e.stopPropagation();
  document.getElementById('ftag').value=tag;
  flt();
}
// status カードクリックでフィルタをセット
function setStatus(s){
  document.getElementById('fs').value=s;
  pinFilter=false;
  flt();
}
// severity カードクリックでフィルタをセット
function setSeverity(sv){
  document.getElementById('fsev').value=sv;
  pinFilter=false;
  flt();
}
// pinned フィルタの状態 (select を使わず変数で保持)
let pinFilter=false;
function setPinned(){
  document.getElementById('q').value='';
  document.getElementById('fs').value='';
  document.getElementById('fd').value='';
  document.getElementById('ftag').value='';
  document.getElementById('fsev').value='';
  pinFilter=true;
  flt();
}
// total カードクリックで全フィルタをリセット
function resetAll(){
  document.getElementById('q').value='';
  document.getElementById('fs').value='';
  document.getElementById('fd').value='';
  document.getElementById('ftag').value='';
  document.getElementById('fsev').value='';
  pinFilter=false;
  flt();
}
// グラフのノードクリックで対応レコードに絞り込み・詳細展開・スクロール
function focusId(shortId){
  document.getElementById('q').value=shortId;
  document.getElementById('fs').value='';
  document.getElementById('fd').value='';
  document.getElementById('ftag').value='';
  document.getElementById('fsev').value='';
  pinFilter=false;
  flt();
  const row=[...document.querySelectorAll('#t tbody tr.row')]
    .find(r=>r.dataset.q.includes(shortId));
  if(row){
    const d=row.nextElementSibling;
    if(d&&d.classList.contains('detail'))d.classList.add('open');
    row.scrollIntoView({behavior:'smooth',block:'center'});
  }
}
// フィルタ適用
function flt(){
  const q=document.getElementById('q').value.toLowerCase();
  const s=document.getElementById('fs').value;
  const d=document.getElementById('fd').value;
  const tg=document.getElementById('ftag').value;
  const sv=document.getElementById('fsev').value;
  document.querySelectorAll('#t tbody tr.row').forEach(r=>{
    const tags=r.dataset.tag?r.dataset.tag.split(' '):[];
    const ok=(!q||r.dataset.q.toLowerCase().includes(q))
            &&(!s||r.dataset.s===s)
            &&(!d||r.dataset.d===d)
            &&(!tg||tags.includes(tg))
            &&(!sv||r.dataset.sev===sv)
            &&(!pinFilter||r.dataset.pin==='1');
    r.style.display=ok?'':'none';
    const dt=r.nextElementSibling;
    if(dt&&dt.classList.contains('detail')){
      dt.style.display=ok?'':'none';
      if(!ok)dt.classList.remove('open');
    }
  });
}
</script>
</body>
</html>
```

### テンプレート展開メモ（Claude が HTML を生成する際の対応表）

| テンプレート変数 | データ元 | 備考 |
|---|---|---|
| `{{tag_options}}` | 全 `tags[]` を重複排除してソート | `<option value="sprint-7">sprint-7</option>` 形式 |
| `{{tag_pills}}` | `tags[]` | `<span class="tag" onclick="setTag(event,'sprint-7')">sprint-7</span>` 形式 |
| `{{owner_or_blank}}` | `owner` フィールド | 未設定なら空文字 |
| `{{rel_summary}}` | relations 各配列の長さ | `↑2 ↓1` など。`superseded_by` がある場合は `後→1` を追加 |
| `{{constraints_items}}` | `constraints[]` | `<div>・{{item}}</div>` 形式。フィールド自体なければブロックごと省略 |
| `{{code_refs_items}}` | `code_refs[]` | `<div><code class="cref">{{path}}</code><span class="cref-note">{{note}}</span></div>` |
| `{{superseded_by_block}}` | `relations.superseded_by[]` | 存在する場合のみ `/ <span class="rel-sup">後継→ <a>...</a></span>` を出力 |
| `{{graph_w}}` / `{{graph_h}}` | レイヤー数・各レイヤー内の最大件数から算出 | 目安: `graph_w = layer数×300+100`、`graph_h = 最大行数×120+100` |
| `{{graph_edges}}` | `relations.depends_on` を反転した辺一覧 | 「DAG グラフ生成」節の手順2・5参照。`<line>` + `marker-end="url(#arrow)"` |
| `{{graph_nodes}}` | 全レコード | 「DAG グラフ生成」節の手順2〜4参照。孤立ノードは黄破線・ラベル付記 |
| `{{title_short}}` | `title` | 目安12〜16文字で切り詰め、超過時は末尾に「…」 |
| `{{status_color}}` | `status` | 一覧の色分けと同じ対応表を使う (accepted=`--ok` 等) |
| `{{plain_summary}}` | `title`/`context`/`decision`/主要な採用・棄却理由から Claude が新規執筆 | 「人間向けやさしい解説の生成」節の基準に従う。YAML の既存フィールドをそのまま転記するのではなく、都度書き起こす |
| `{{decision_paragraphs}}` | `decision` | 「テキスト整形」節の手順で折り返し改行を除去し、段落ごとに `<p style="margin:0 0 10px">...</p>` を並べる |
| `{{opt_*.rationale_formatted}}` | `options[].rationale` | 同上。折り返し改行を除去した1つ以上の `<p>`/連結テキスト |

## オプション

- `--out <path>`: 出力先を変更 (既定: `udr_dashboard.html`)。
- `--open`: 生成後にブラウザで開くコマンドを案内 (OS 依存: `start` / `open` / `xdg-open`)。

## エラーコード

| Code | 条件 |
|---|---|
| UDR-DASH-001 | `.udr/` 未初期化 (`/udr-init` を案内) |
| UDR-DASH-002 | 出力先パスが `allowed_sync_paths` 外 (NFR-009、`--out` 指定時のみ検査) |

## 関連 skill

- `/udr-review` (品質棚卸し) の結果を視覚的に確認する用途に補完的。
- `/udr-record` で記録を追加したら再実行して最新化する。
