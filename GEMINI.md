# GEMINI.md — Gemini CLI 向け作業ガイド

**最初に `AGENTS.md` を必ず読むこと。** 本リポジトリの UDR 自動検知ポリシー、プロジェクト構成、手動テンプレート等のマスタは `AGENTS.md` に集約されている。本書は Gemini CLI 固有の追加指示のみを扱う。

---

## Gemini CLI 固有の運用

### UDR 操作の実行方法

Gemini CLI は Claude Code の `/udr-record` 等のスキルを直接呼び出せない。代わりに、以下の **プロンプトテンプレート** を使って同等の動作を実現する。

各テンプレートは `.claude/skills/_udr-shared/templates/gemini-prompts/` に配置されている。
操作時は該当ファイルを読み込み、その手順に厳密に従うこと。

| 操作 | テンプレートファイル | 用途 |
|---|---|---|
| 初期化 | `gemini-prompts/udr-init.md` | `.udr/` 構造を初期化 |
| 記録 | `gemini-prompts/udr-record.md` | 判断を対話的に記録 |
| 検索 | `gemini-prompts/udr-search.md` | 既存 UDR の検索 |
| 同期 | `gemini-prompts/udr-sync.md` | コンテキストファイルへのサマリ同期 |
| 追跡 | `gemini-prompts/udr-trace.md` | 依存関係 DAG の追跡 |
| 棚卸し | `gemini-prompts/udr-review.md` | 品質レビュー |
| ダッシュボード | `gemini-prompts/udr-dashboard.md` | HTML 可視化 |

**例：判断を記録する場合**

```
@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md
```

と入力するか、ファイルの内容を参照するよう Gemini に指示する。

### UDR 候補の検知

`AGENTS.md §2` の検知フローと同じトリガーを使用する。応答末尾に以下を付記:

```
[UDR 候補] 「<一行要約>」を記録しますか？
  Y → gemini-prompts/udr-record.md を参照して記録   N → スキップ   D → gemini-prompts/udr-search.md で検索
```

### 手動 YAML 作成

Gemini CLI でスキルなしに記録する場合は `AGENTS.md §4` のテンプレートを使用する。  
保存先: `.udr/records/<id>.yaml`

### Codex CLI / Claude Code との共存

すべてのエージェントが `.udr/records/` を共有する。ID 採番時は必ず既存ファイルを確認:

```bash
ls .udr/records/UDR-UDR-*.yaml
```

---

## UDR サマリ（`/udr-sync` で自動更新、編集不可）

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

*最終更新: 2026-07-19*
