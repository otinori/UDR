# AGENTS.md — UDR マルチエージェント共通ポリシー

本リポジトリで作業する全 AI エージェント（**OpenAI Codex CLI** / **Google Gemini CLI** / **Claude Code** / **Cursor** / **Continue** / **GitHub Copilot** 等）が **会話開始時に最初に読む** ファイル。UDR（判断記録）の自動検知ポリシーと、プロジェクトの現状を集約している。

各エージェント固有の追加指示がある場合は、以下の派生ファイルを参照:
- `CLAUDE.md` — Claude Code 向け（本書のミラー + 個別追記）
- `GEMINI.md` — Google Gemini CLI 向け（本書のミラー + 個別追記）

GitHub Copilot 向けの `.github/copilot-instructions.md` 等は本リポジトリでは未セットアップ（`.udr/config.yaml` の `tools` に `copilot` を追加し `/udr-init` を実行すれば生成される）。

---

## 1. このプロジェクトについて

**UDR (Universal Decision Record)** は、開発中の判断を YAML 形式で構造的に記録し、AI コンテキストファイルへ自動同期する仕組みの **本家実装プロジェクト**。Phase 1 PoC は Claude Code skills として実装済み、Phase 2 で MCP Server 化する。このリポジトリ自体が UDR のドッグフーディング対象。

**主要構成**:
- `docs/Phase1_要求定義/` — 要求定義 v2.2（FR/NFR/BR/C）・既存 ADR 調査・レビュー結果
- `docs/Phase2_実装検討/` — Phase 2 実装方法検討結果
- `.claude/skills/` — UDR skill 一式の **source of truth**（udr-init / record / search / sync / trace / review / dashboard）。`plugins/udr/skills/` は PR 上で CI（`sync-mirrors.yml`）が生成するミラーで直接編集しない
- `.claude/skills/_udr-shared/CONVENTIONS.md` — UDR 共通規約（スキーマ / ID 体系 / status 遷移 / sync）
- `.claude/deploy/` — デプロイテンプレートの source of truth（GEMINI.md / .gemini/ 拡張。`plugins/udr/` root へミラーされる）
- `plugins/udr/` — Claude Code プラグインマーケットプレイス配布用（`claude plugin install udr@udr-marketplace`）。`skills/` / `GEMINI.md` / `.gemini/` はミラー、`.claude-plugin/plugin.json` / `hooks/` は手動管理
- `dist/` — 他プロジェクトへの手動配布バンドル（usage.md / install スクリプト / VERSION。skill 本体は含まず `.claude/` を直接参照）
- `.udr/records/UDR-UDR-*.yaml` — 判断記録（1 判断 1 ファイル、`records/` 配下）
- `.udr/config.yaml` — UDR プロジェクト設定（`repo_short: UDR`）
- `.udr/index.json` — DAG キャッシュ（動的生成・`.gitignore` 管理＝非追跡）

**開発プロセス**: 本リポジトリ自身の開発判断も UDR として記録する（ドッグフーディング）。要求定義・アーキテクチャ選定・skill 設計方針等の判断は、検知次第 `udr-record` で起票する。

**現状**:
- Phase 1 PoC 実装済み（Skills 7 種一式 + プラグイン配布 + 手動配布バンドル）
- 要求定義 v2.2 完成（index.json 動的管理を FR-014 / NFR-003 に反映）
- Phase 2（MCP Server STDIO 化）は実装方針を `docs/Phase2_実装検討/UDR実装方法検討結果.md` で検討済み。判断記録をリポジトリ外のナレッジサーバとして保持する根本対応として、早期着手の方針に転換済み（判断記録 UDR-UDR-20260719T0857-df1）
- UDR 記録件数・最新の判断一覧は本書下部の「Active Decisions」セクション参照（`/udr-sync` で自動更新されるため、ここには件数を固定記載しない）
- 判断記録は `.udr/records/` 配下に `UDR-UDR-*.yaml`（repo_short=UDR）として格納。`.claude/skills/_udr-shared/CONVENTIONS.md` §1/§2 に準拠

---

## 2. UDR 自動検知ポリシー（本書の中核）

本プロジェクトは **UDR** で設計判断を構造化記録する。AI は会話中に判断が発生した瞬間を検知し、UDR 起票を **必ず提案** すること。

### 2.1 検知トリガー（以下のいずれかが出現したら UDR 候補）

1. **明示的な決定宣言** — user が「〜にする」「〜で決定」「〜を採用」「〜は棄却」と述べた
2. **複数案の選定** — 2 つ以上の候補を比較して 1 つを選択する議論が発生した（技術選定・アーキ選定・命名・ライセンス・ディレクトリ構造・ID 体系など）
3. **既存設計の変更** — 要求定義 / 設計書 / UDR 等の確定済み方針を改訂する判断（supersede の可能性）
4. **AI 判断の受容** — AI が提案した方針を user が黙認・承認して進めた（暗黙的判断、`status: proposed` 強制、BR-002）
5. **スコープ境界の決定** — 「Phase 1 に含む / Phase 2+ に延期」「実装する / 型だけ予約」のフェーズ配分判断
6. **トレードオフの意識的選択** — コスト / 複雑度 / 保守性 / 互換性を明示的に引き換えた選択

### 2.2 除外パターン（UDR 化しない）

- 変数名・関数名・改行・インデント等の **瑣末な表層スタイル**
- タイポ修正・誤字訂正・言い回し調整
- 一時的な作業手順（「まず Read してから Edit」など）
- 会話の繰り返し・言い直し・確認
- 既に記録済みの判断（迷ったら `.udr/records/UDR-UDR-*.yaml` を grep で重複確認）

### 2.3 処理フロー

1. **検知**: トリガー発生を認識したら、応答の末尾に以下を付記する:
   ```
   [UDR 候補] 「<一行要約>」を記録しますか？
     Y → 記録を開始   N → スキップ   D → 既存を検索
   ```

2. **user 応答待ち**: Y なら UDR 記録を開始。会話文脈で必須 3 項目（title / decision / context + 棄却選択肢）が既に揃っていれば、ヒアリングを省略してメタ確定（domain / authors / pinned）から。

3. **記録手段** — エージェントごとの使い分け:

   | エージェント | 記録方法 |
   |---|---|
   | Claude Code | `/udr-record` skill を呼び出す（`.claude/skills/udr-record/SKILL.md`） |
   | Google Gemini CLI | `.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` を参照して実行 |
   | OpenAI Codex CLI | `.claude/skills/_udr-shared/templates/codex-prompts/udr-record.md` を参照して実行（または本書 §4 テンプレートで手動作成） |
   | Cursor / Continue | 本書 §4 のスキーマに従い `.udr/records/<id>.yaml` を手動作成 |
   | Copilot | ポリシー通知のみ、記録は人間が Claude Code / Gemini / Codex で実施 |

4. **棄却理由の補完**: `options.rejected` が 0 件なら、「他に検討した案は？棄却理由は？」と 1 回だけ確認（BR-007 / FR-015）。棄却案 0 件でも記録は続行（警告のみ）。

5. **AI-only 判断の扱い**: user 不在で AI 単独が選択した内容は `status: proposed` 強制（BR-002）。user レビュー待ちとして記録。

6. **記録後**: CLAUDE.md / AGENTS.md / GEMINI.md のサマリ同期を促す（Claude Code なら `/udr-sync`、他エージェントは本書 §3 マーカーを手動更新）。

### 2.4 曖昧ケースの判断規則

- 「これは判断か？」迷ったら → **記録寄り** で user に判定を委ねる（`[UDR 候補]` 提示）
- 1 セッション中に 5 件以上検知した場合 → user に「まとめて 1 件で記録するか？」と提案（巨大判断の分割検討）
- user が「記録しなくていい」と明言 → 該当セッション中は同種トリガーを静かに抑制

---

## 3. UDR サマリ（`/udr-sync` で自動更新、人間・AI 共に編集不可）

<!-- [UDR-SYNC-START] -->
## UDR — 判断記録プロトコル (synced 2026-07-19T09:03:24Z, 6件中5件表示)

このプロジェクトでは、設計・要件・技術選定などの **非自明な判断** を UDR (Universal Decision Record) として `.udr/records/` 配下に YAML で記録します。Claude Code / Codex CLI / Gemini CLI / GitHub Copilot のいずれの環境でも、本プロトコルを厳守してください。

### スラッシュコマンド一覧

| コマンド | 役割 | Claude Code | Codex CLI | Gemini CLI | Copilot CLI |
|---|---|:-:|:-:|:-:|:-:|
| `/udr-init` | プロジェクト初期化 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-record` | 判断の対話的記録 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-search <q>` | UDR 検索 (ID/フィルタ/全文) | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-sync` | コンテキストファイル同期 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-trace <id>` | DAG 走査・影響分析 | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-review` | 品質棚卸し (9 観点) | ✓ | ✓ | テンプレート参照 | ✓ |
| `/udr-dashboard` | 判断状況を HTML 出力 (udr_dashboard.html) | ✓ | ✓ | テンプレート参照 | ✓ |

> Gemini CLI は skill の直接呼び出しを持たない。`@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` のようにテンプレートをファイル参照して実行する。
> GitHub Copilot Chat (IDE 内) は slash command 不可。policy のみ反映され、判断記録時は user に CLI への切替か手動 YAML 作成を提案する。

### エージェント別の動作経路

- **Claude Code**: 配置方法は 2 通り。(1) project 配置 = `.claude/skills/udr-*/SKILL.md` を自動検出し `/udr-record` で使う。(2) **プラグイン版** = `claude plugin install udr@udr-marketplace` で導入し `/udr:udr-record` で使う。どちらも `.udr/` を同じように読み書きする
- **Gemini CLI**: `GEMINI.md` をプロジェクトルートから自動読み込み（コンテキストファイル）。操作テンプレートは `.claude/skills/_udr-shared/templates/gemini-prompts/` に配置済み。`@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` のように参照して使う。`.gemini/extensions/udr/` の拡張マニフェストでシステムプロンプトを自動注入
- **GitHub Copilot CLI**: 独自の plugin marketplace を持つ（`.claude/skills/` は自動検出**しない**）。`copilot plugin marketplace add <source>` → `copilot plugin install udr@udr-marketplace`（同じ `.claude-plugin/marketplace.json` を読む。`copilot plugin install <owner>/UDR:plugins/udr` でも可）。呼び出しは **`/udr-record` 等（slash・名前空間なし）**。MCP / AGENTS.md も読む
- **Codex CLI**: 2 通り。(1) **ネイティブ plugin**（推奨, Codex 0.139+）= `codex plugin marketplace add <source>` → `codex plugin add udr@udr-marketplace`（Claude と同じ `.claude-plugin/marketplace.json` を読む）。呼び出しは **skill 扱いで `$udr:udr-init`**（`$` + `udr:` 名前空間。`/skills` で一覧）。(2) `.codex/prompts/udr-*.md` を `~/.codex/prompts/` にコピー → ファイル名の slash command `/udr-init`。**注意: Codex の `/...` は組み込みコマンド（`/skills` `/plugins` 等）、skill 明示呼び出しは `$...`**（下記セットアップ参照）
- **GitHub Copilot Chat (IDE)**: slash command 不可。user に skill 手順の手動実行か、CLI 環境への切替を提案する

### あなた (AI エージェント) が判断を行う／検出した場合

- **Claude Code**: `/udr-record` を呼ぶ／user に提案する (project 配置の `.claude/skills/` を自動検出。plugin 版は `/udr:udr-record`)
- **GitHub Copilot CLI**: plugin 導入済みなら `/udr-record` を呼ぶ／提案する (未導入なら `copilot plugin install udr@udr-marketplace` を案内)
- **Codex CLI / その他の自律エージェント**: `/udr-record` (`.codex/prompts/` 経由) または `.claude/skills/udr-record/SKILL.md` を直接読み、Phase A (必須3項目: title+decision / context+rationale / 棄却選択肢+理由) → Phase B (任意3項目) → Phase C (メタ確定) の対話フローに従って `.udr/records/UDR-<repo_short>-<UTC YYYYMMDDTHHmm>-<rand3>.yaml` を作成する
- **GitHub Copilot Chat (IDE)**: 自身では能動的に YAML 作成はできないため、user に判断記録を提案する
- **必須**: 棄却した代替案とその理由を必ず記録する (UDR の核心 / BR-007 / FR-015)
- AI 単独 (authors が ai-agent のみ) の判断は `status: proposed` 強制 (BR-002)
- スキーマ・ID 体系・status 遷移は `.claude/skills/_udr-shared/CONVENTIONS.md` 参照

### コードを変更する前に

- 関連過去判断を確認: Claude Code/Codex は `/udr-search <keyword>`、それ以外は `.udr/records/*.yaml` を grep
- `verdict: rejected` の選択肢を **再提案しない** (sync で配信される過去判断を必ず参照)

### 矛盾しそうな変更

- Claude Code/Codex は `/udr-trace <id>` で影響分析、それ以外は YAML の `relations.depends_on` / `triggers` / `supersedes` を手動追跡

### スキル本体の場所 (詳細手順を読みたいとき)

> パスは **project 配置** (`.claude/skills/`) の場合。**プラグイン版**で導入したときは各 skill はプラグイン配下に置かれ (`/plugin` で管理)、呼び出しは `/udr:udr-*`。ファイルパスは異なるが内容と使い方は同じ。

- 共通規約: `.claude/skills/_udr-shared/CONVENTIONS.md`
- 各 skill: `.claude/skills/udr-{init,record,search,sync,trace,review,dashboard}/SKILL.md`
- Codex プロンプト: `.codex/prompts/udr-*.md`

---

## Active Decisions (6 records)

### Pinned
- (なし)

### Recent (score 降順)
- **UDR-UDR-20260719T0846-d39** [pro] 個人プロジェクトの .udr/ をGit非追跡化 — 公開時の漏洩リスクを構造的に排除
  個人プロジェクトの .udr/ をGit非追跡化。決定:.gitignoreで除外しUDR引用箇所は自己完結の説明に書き換え。棄却:新規リポジトリ移行時のみ除外(移行実行までリスク残存)。制約:チーム開発private repoでは共有継続。
- **UDR-UDR-20260719T0857-df1** [arc] Phase 2 (MCP化) の当面保留を撤回し、ナレッジサーバとして早期に着手する方針とする
  Phase 2 (MCP化) の当面保留を撤回し早期着手する方針。決定:判断記録をリポジトリ外のナレッジサーバで保持する実装に早期着手。棄却:保留継続(知的財産の流出リスクが構造的に残るため)。
- **UDR-UDR-20260711T0728-f9f** [arc] UDR全文検索に2段階ハイブリッド方式を導入 — 表記ゆれによる再現率低下を解消
  UDR全文検索(Mode 3)に「Stage1決定的スコアリング→ヒット件数2件未満/低スコア/短トークン時のみStage2 AIエスカレート」の2段階方式を追加。実測シミュレーションで表記ゆれによる再現率50%への低下と短トークン誤検出を確認した上での判断。実装直後の3回検証で「score条件だけでは強い1件ヒットケースを救えない」不具合を発見し、ヒット件数条件を追加して是正済み。embedding等の新規外部依存は追加せず、C-006/C-007のポータビリティ確保という根本動機は維持する。
- **UDR-UDR-20260712T0314-47b** [des] udr-recordに独立コンテキストのフレッシュレビューを追加 — 同一文脈の自己チェックだけでは第三者可読性を保証できない
  udr-recordの読者テスト（同一会話コンテキストでの自己チェック）は自己採点の弱さを構造的に持つ。会話履歴を持たない独立コンテキストのサブエージェントによるフレッシュレビュー（最大2回、Claude Code限定）を下書き完成後・user提示前に追加した。userが提案した「サブエージェントが書きメインが精査」は、レビュー主体が会話文脈を持つ限り本質的な解決にならないため、レビュー主体の独立化に組み替えて採用。マルチロールレビューは今回のスコープ外とし、将来のconclave連携時に改めて判断する。
- **UDR-UDR-20260711T1059-a5a** [des] udr-recordの読者テストにverification等の事後追記フィールドを追加
  udr-search Mode 3 UDR(UDR-UDR-20260711T0728-f9f)のverification.criteriaが一時スクラッチパッドのテストID(sim-XXX)を参照しており、第三者が読めない状態になっていたことを受けて、udr-record/SKILL.mdの読者テストにverification等の事後追記フィールド向けの4問目とフィールド別ガイドを追加。検証結果は一時ファイル・IDに依存せず手法と定量結果だけで自己完結させるルールを明文化。

<!-- [UDR-SYNC-END] -->

---

## 4. UDR YAML 最小テンプレート（手動作成時のリファレンス）

Codex CLI 等で skill を使わず手動記録する場合の最小テンプレート。完全なスキーマは `.claude/skills/_udr-shared/CONVENTIONS.md §3`（ただし ID 体系・配置は現状実装に合わせて下記参照）:

```yaml
id: UDR-UDR-<YYYYMMDDTHHmm UTC>-<rand3 [0-9a-f]>   # 例: UDR-UDR-20260424T1430-a3f
title: "<50字以内>"
domain: architecture     # architecture | requirements | design | risk | project | operations | other
status: proposed         # AI-only は proposed 強制 (BR-002)。人間関与ありは accepted 可
severity: medium         # high | medium | low
pinned: false
date: 2026-04-24
updated: 2026-04-24
authors:
  - name: <user名>
    role: human
  - name: codex-cli       # または claude-code, cursor 等
    role: ai-agent

context: |
  （判断に至った背景、3-6 行）

options:
  - id: opt-1
    name: "採用案"
    verdict: accepted
    rationale: |
      採用理由
  - id: opt-2
    name: "棄却案（必須、UDR の存在意義）"
    verdict: rejected
    rationale: |
      棄却理由

decision: |
  最終決定の 2-3 行要約

consequences:
  positive: ["..."]
  negative: ["..."]

relations:
  depends_on: []          # [{ id: "UDR-UDR-..." }]
  triggers: []

claude_summary: |
  [UDR-UDR-<rand3>] <title>。決定:<decision1行>。棄却:<rejected[0].name>(<理由1語>)。
```

保存先: `.udr/records/<id>.yaml`（1 判断 1 ファイル、`.udr/records/` 配下）

### 4.1 ID 生成の具体手順（手動記録時、bash）

```bash
# UTC タイムスタンプ
UTC_TS=$(date -u +%Y%m%dT%H%M)

# rand3 生成（3 桁 hex）
RAND3=$(printf '%03x' $((RANDOM % 4096)))

# 衝突チェック（既存と重なれば再生成）
while ls .udr/records/UDR-UDR-${UTC_TS}-${RAND3}.yaml 2>/dev/null; do
  RAND3=$(printf '%03x' $((RANDOM % 4096)))
done

UDR_ID="UDR-UDR-${UTC_TS}-${RAND3}"
echo "$UDR_ID"   # 例: UDR-UDR-20260424T1430-a3f
```

PowerShell の場合:
```powershell
$UTC_TS = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmm")
$RAND3  = "{0:x3}" -f (Get-Random -Maximum 4096)
$UDR_ID = "UDR-UDR-$UTC_TS-$RAND3"
```

### 4.2 audit.log 追記（ローカル履歴、gitignore 対象）

```bash
ISO_TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ACTOR="otinori"                # または "claude-code" / "codex-cli" 等
ROLE="human"                # または "ai-agent"

echo "{\"ts\":\"${ISO_TS}\",\"actor\":\"${ACTOR}\",\"role\":\"${ROLE}\",\"op\":\"create\",\"id\":\"${UDR_ID}\",\"changed_fields\":[\"*\"]}" >> .udr/audit.log
```

### 4.3 既存 UDR の確認（`depends_on` / `triggers` を張る前）

```bash
# 全一覧
ls .udr/records/UDR-UDR-*.yaml

# タイトル / domain で検索
grep -H "^title:" .udr/records/UDR-UDR-*.yaml
grep -l "MCP" .udr/records/UDR-UDR-*.yaml   # キーワード検索

# 特定 UDR の relations 確認（循環防止）
grep -A 10 "^relations:" .udr/records/<target-id>.yaml
```

---

## 5. 補助ルール

- **ID 体系**: `UDR-<repo_short>-<UTC_TS>-<rand3>`。本リポジトリは `config.yaml` の `repo_short: UDR`（大文字）を明示設定しているため `UDR-UDR-*` になる（CONVENTIONS §2 の小文字例は `repo_short` 未設定時のデフォルト挙動の例示であり、明示設定時はそちらが優先される）
- **supersede**: 既存判断を上書きする場合は `supersedes` フィールドでリンク（FR-004）
- **commit**: user の明示指示がある場合のみ。通常は変更を検知したら `git status` の結果を伝える
- **要求定義の整合**: `docs/Phase1_要求定義/要求一覧.md` の FR/NFR/BR/C 参照が崩れる編集をしたら、必ず他ドキュメントへの波及を grep で確認
- **Phase 2 実装**: `docs/Phase2_実装検討/UDR実装方法検討結果.md` に沿って MCP Server STDIO を構築（早期着手方針、判断記録 UDR-UDR-20260719T0857-df1）
- **修正後の効果検証**: skill・hook を修正したら、記述を直すだけで終わらせず**実際に動かして効果を確認**する。例:
  - hook（`plugins/udr/hooks/`）: `claude --plugin-dir plugins/udr --debug hooks --debug-file <path> -p "<prompt>"` で実セッションを起動し、debug log で意図した hook が発火し期待した `additionalContext` を返しているか確認する（`claude plugin validate` はスキーマ検証のみで実行時の動作までは保証しない）
  - skill の対話フロー・文章品質ガイドライン等の変更: 実際にそのフローで UDR を 1 件記録してみる（本プロジェクト自身のドッグフーディング記録として使ってよい）などにより、意図通りの出力になるか確認する
  - 検証した内容は PR 説明・commit メッセージに残す（「修正した」だけでなく「こう確認した」まで書く）

---

*最終更新: 2026-07-19*
