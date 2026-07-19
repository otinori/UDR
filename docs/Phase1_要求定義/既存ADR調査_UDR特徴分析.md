# 既存ADR調査とUDR特徴分析

> **目的**: 世の中に存在するADR（Architecture Decision Records）ツール・フレームワークを調査し、UDRの独自性と位置づけを明確にする
> **作成日**: 2026-04-03
> **ステータス**: draft

---

## 1. 既存ADRツール・フレームワーク一覧

### 1.1 主要ツール

| # | 名称 | 開発元 | フォーマット | ツール種別 | 採用度 | 概要 |
|---|------|--------|-------------|-----------|--------|------|
| 1 | **MADR 4.0** | Olaf Zimmermann他 / adr org | Markdown + YAML frontmatter | テンプレート | 非常に高い | 業界標準のADRテンプレート。v4.0で「Any Decision」に改称 |
| 2 | **adr-tools** | Nat Pryce | Markdown | CLI（Bash） | 高い（GitHub Stars 4,400+） | ADRツールの原点。`adr link`で判断間リンクをサポート |
| 3 | **Log4brains** | thomvaill | Markdown（MADR準拠） | CLI + 静的Web | 中（GitHub Stars 1,100+） | ADRを検索可能なWebサイトとして自動公開 |
| 4 | **ADR Manager** | adr org | Markdown（MADR準拠） | VS Code拡張 | 低〜中 | GUIフォームでADRを作成・編集 |
| 5 | **Structurizr Decision Log** | Simon Brown | Markdown / AsciiDoc | Web（SaaS） | 中 | C4モデルとADRの統合。関係の力指向グラフ可視化 |
| 6 | **Backstage ADR Plugin** | Spotify OSS | Markdown（MADR準拠） | Webポータル | 中 | 組織横断でのADR発見・検索が可能 |
| 7 | **dotnet-adr** | endjin | Markdown | CLI（.NET） | 低〜中 | .NET Global Tool。複数テンプレート対応 |
| 8 | **adr-log** | adr org | Markdown | CLI（Node.js） | 低 | ADRインデックス（目次）自動生成に特化 |
| 9 | **phodal/adr** | phodal | Markdown | CLI（Node.js） | 低 | HTMLレポート生成。多言語対応 |

### 1.2 フォーマット・テンプレート

| # | 名称 | 提案者 | 構造 | 特徴 |
|---|------|--------|------|------|
| A | **Nygard形式**（原型） | Michael Nygard（2011年） | Status / Context / Decision / Consequences | ADRの原点。極めてシンプル |
| B | **MADR 4.0** | Olaf Zimmermann他 | Context / Decision Drivers / Options / Decision Outcome / Pros and Cons | Nygardを拡張。選択肢比較とConfirmationセクション |
| C | **Y-Statements** | Olaf Zimmermann（2012年） | 1文で6パート | 超圧縮表現。MADRの前身 |
| D | **Tyree & Akerman** | Jeff Tyree他（IEEE 2005年） | Issue / Decision / Positions / Argument / Implications / Related decisions 等 | 学術的テンプレート。最も多くのセクションを持つ |
| E | **LADR** | ThoughtWorks | Nygard形式ベース（最小限） | 軽量ADR。記録の負担を最小化 |

### 1.3 学術・標準規格

| # | 名称 | 概要 |
|---|------|------|
| I | **ISO/IEC/IEEE 42010:2022** | アーキテクチャ記述の国際標準。Architecture Rationaleの記録を要件として含む。Decision Detail / Relationship / Chronology / Stakeholder Involvement の4ビューポイントを定義 |
| II | **MADR学術論文**（CEUR-WS 2018） | MADRフォーマットの形式的定義。Y-Statement→MADRの発展を学術的に記述 |
| III | **LLM×ADR研究**（2024-2025年） | AIによるADRドラフト自動生成、マルチエージェントADR Writer、コードベーススキャンからの自動ADR生成 |

### 1.4 クラウドベンダーのADRガイダンス

| ベンダー | 特徴 |
|----------|------|
| **AWS Prescriptive Guidance** | Context / Decision / Consequences + Compliance。コードレビュー統合 |
| **Azure Well-Architected** | append-onlyログ形式。ブラウンフィールド（既存改修）にも推奨 |
| **Google Cloud Architecture Center** | Options / Requirements / Decisions。コードベース隣接配置を推奨 |

---

## 2. 機能比較マトリクス

既存ツールとUDRの機能を8つの観点で比較する。

| 観点 | Nygard形式 | MADR 4.0 | adr-tools | Log4brains | Structurizr | Backstage | **UDR** |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **スコープ** | Arch | Any | Arch | Arch+ | Arch | Arch | **全領域**（arch/req/design/risk/project/other） |
| **フォーマット** | MD | MD+YAML FM | MD | MD(MADR) | MD/AsciiDoc | MD(MADR) | **全体YAML** |
| **判断間リレーション** | - | 手動リンク | `adr link` | superseded | 可視化あり | - | **DAG（depends_on/triggers/supersedes）** |
| **影響範囲分析** | - | - | Graphviz図 | - | 力指向グラフ | - | **udr_impact（domain/severity別集計、critical paths）** |
| **棄却理由の記録** | - | Pros/Cons | - | Pros/Cons | - | Pros/Cons | **options[].verdict: rejected + rationale（必須級）** |
| **AI連携** | - | - | - | - | - | - | **MCP Server + コンテキスト同期 + summary自動生成** |
| **マルチツール対応** | - | 多い | - | MADR互換 | adr-tools互換 | MADR互換 | **MCP Protocol（Claude/Copilot/Cursor/Windsurf）** |
| **コンテキスト同期** | - | - | - | - | - | - | **CLAUDE.md/copilot-instructions.md等への自動同期** |

---

## 3. UDRの独自価値（5つの差別化ポイント）

### 3.1 判断の連鎖をDAGで機械的に追跡できる

**既存の限界**: adr-toolsの`adr link`やStructurizrの可視化が最も近いが、いずれも手動リンクまたは表示に限定される。「判断Aを変更したら、影響を受ける判断B, C, Dは何か」を機械的に算出する仕組みは存在しない。

**UDRの解決**: `depends_on` / `triggers` / `supersedes` の3種の関係で有向非巡回グラフ（DAG）を構築。`udr_trace`で上流/下流を追跡し、`udr_impact`でdomain/severity別に影響を集計できる。循環参照は`udr_create`/`udr_update`時に自動検出してブロックする。

**価値**: 要件変更→影響範囲の自動特定が可能になり、変更前のリスク評価が実現する。

---

### 3.2 AIのコンテキストファイルへの自動同期（蒸発防御）

**既存の限界**: 既存ADRツールにはコンテキスト同期の概念が皆無。ADRはドキュメントとして保存されるが、AIツールのコンテキスト（CLAUDE.md等）に自動反映される仕組みはない。AIは毎回ADRを手動で読み込む必要がある。

**UDRの解決**: `udr_sync_context`で判断の要約をCLAUDE.md / copilot-instructions.md / .cursorrules / .windsurfrules に自動同期。pinned（重要判断5件）+ auto（スコア順15件）のハイブリッド方式で、トークンbudget内に収める。

**価値**: AIが新しいセッションを開始した時点で、過去の判断（採用理由・棄却理由）を認識した状態で作業を始められる。「前に棄却した案をAIが再提案する」問題を根本的に解決する。

---

### 3.3 全体YAML形式によるAI可読性

**既存の限界**: 全ての既存ADRツールがMarkdownベース。Markdownは人間可読性に優れるが、LLMが構造的にパースして選択肢・棄却理由を抽出する際に曖昧さが生じる。ヘッダーの解析、テーブルの解析等でパースエラーが起きやすい。

**UDRの解決**: 全体をYAML構造で記録。LLMが確実にフィールドを特定し、選択肢（options[]）の各要素のverdict/rationaleを正確に抽出できる。同時にYAMLは人間にもスキャン可能（AI可読と人間可読の両立）。

**価値**: AIがUDRを読み込んだ際のパース精度が向上し、判断の文脈をより正確に理解した上でコード生成・提案を行える。

---

### 3.4 棄却理由の必須級記録と促進

**既存の限界**: MADR 4.0はPros/Consセクションで選択肢の長所・短所を記録できるが、棄却理由の記録は任意。実運用では棄却理由が空欄のまま放置されることが多い。Nygard形式、LADR等には棄却理由のセクション自体がない。

**UDRの解決**: `options[].verdict: rejected`と`options[].rationale`で棄却理由を構造化記録。rejected選択肢が0件の場合は警告を出す（FR-015）。棄却理由こそがコンパクションで消失する最も価値のある情報であるという思想を設計に組み込んでいる。

**価値**: 「なぜその選択肢を棄却したのか」が確実に記録され、後日の「なぜこの設計なのか」という疑問に即座に回答できる。AIが棄却済みの案を再提案することを防ぐ。

---

### 3.5 AI判断の帰属と承認フロー

**既存の限界**: 既存ADRツールはすべて「人間がADRを書く」前提で設計されている。AIがADRを自動生成するシナリオ、AIの判断を人間が承認するワークフローは一切考慮されていない。

**UDRの解決**: `authors`フィールドでAI/人間の帰属を明記。AIエージェントが単独で作成したUDRは自動的に`status: proposed`に強制され、人間の承認（`accepted`への遷移）なしには確定しない。リアルタイム承認とバッチ承認の2パターンを定義。

**価値**: AI-native開発において「誰が判断したか」「AIの判断は人間が確認したか」を追跡可能にし、判断の透明性とガバナンスを確保する。

---

## 4. ポジショニングマップ

```
                        AI-native統合度
                            高
                            │
                            │         ★ UDR
                            │        （DAG + AI同期 + YAML）
                            │
                            │
                            │
              ──────────────┼──────────────── 判断追跡の構造化度
            低              │              高
                            │
                 LADR       │    Structurizr
                 Nygard     │    （可視化あり）
                            │
                 MADR 4.0   │    adr-tools
                 Log4brains │    （adr link）
                            │
                            低
```

**UDRの位置づけ**: 既存ADRツールが「判断追跡の構造化度」の軸に沿って分布する中で、UDRは「AI-native統合度」という新しい軸を加え、両軸で最も高い位置を占める。

---

## 5. MADR 4.0との詳細比較

MADR 4.0はUDRが設計思想を継承する最も重要な先行フォーマットである。

### 5.1 継承している要素

| MADR 4.0の要素 | UDRでの対応 |
|---------------|------------|
| Context and Problem Statement | `context`フィールド |
| Considered Options | `options[]`配列 |
| Decision Outcome | `decision`フィールド |
| Pros and Cons | `options[].pros[]` / `options[].cons[]` |
| Status (proposed/accepted/deprecated/superseded) | `status`（同一の遷移モデル） |
| YAML frontmatter（date, status, decision-makers） | YAMLのメタデータセクション |
| Confirmation | `verification`セクション |

### 5.2 UDRが追加した要素

| UDR独自の要素 | MADR 4.0にない理由 | UDRでの実装 |
|-------------|-------------------|------------|
| DAG構造（判断の連鎖） | MADRは各ADRが独立文書。関係は手動記載 | `depends_on` / `triggers` / `supersedes` + `udr_trace` / `udr_impact` |
| AI連携サマリ | MADRはAI連携を想定していない | `summary_hint`（自動） / `claude_summary`（手動/AI） |
| コンテキスト同期 | MADRにはAIコンテキストの概念がない | `udr_sync_context`（4ツールチェーン対応） |
| 全体YAML形式 | MADRはMarkdownの読みやすさを重視 | 全フィールドがYAML構造（AI可読性優先） |
| AI帰属・承認 | MADRは人間が書く前提 | `authors`配列 + `status: proposed`強制 |
| domain分類 | MADRは「Any Decision」だが分類機構がない | `domain` enum（6種 + カスタム拡張） |
| severity（影響度） | MADRにはない | `severity`（high/medium/low） |
| MCP Server | MADRはテンプレートのみ | 9ツール + 2プロンプトのMCPサーバー |

### 5.3 UDRが変更した要素

| MADR 4.0の要素 | UDRでの変更 | 変更理由 |
|---------------|------------|---------|
| Markdown本文 | 全体YAML | LLMのパース精度向上。構造化フィルタ・検索を可能にするため |
| Decision Drivers（判断動因） | `constraints`（制約条件） | 判断を「縛るもの」を明示的に構造化するため |
| More Information（自由記載） | `relations`（構造化リレーション） | 判断間の関係を機械的に追跡可能にするため |
| 手動テンプレート記入 | MCP Serverによる対話的記録 | 記録の負荷を下げ、必須フィールドの漏れを防ぐため |

---

## 6. 一文サマリー

> **UDRは、業界標準MADR 4.0の判断記録構造を継承しつつ、「判断の連鎖をDAGで追跡」「AIコンテキストへの自動同期」「全体YAML形式によるAI可読性」「棄却理由の必須級記録」「AI判断の帰属と承認」の5つのAI-native拡張を加えた、世界初のAI-native判断記録基盤である。**

---

## 出典

- [MADR 公式](https://adr.github.io/madr/) / [GitHub](https://github.com/adr/madr)
- [adr-tools](https://github.com/npryce/adr-tools)（Nat Pryce）
- [Log4brains](https://github.com/thomvaill/log4brains)
- [ADR Manager VS Code拡張](https://github.com/adr/vscode-adr-manager)
- [ADR GitHub Organization](https://adr.github.io/)
- [Y-Statements](https://medium.com/olzzio/y-statements-10eb07b5a177)（Olaf Zimmermann）
- [Lightweight ADR - ThoughtWorks Radar](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)
- [Structurizr Decision Log](https://docs.structurizr.com/ui/decisions/)
- [Backstage ADR Plugin](https://backstage.io/docs/architecture-decisions/)
- [dotnet-adr](https://github.com/endjin/dotnet-adr)
- [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html)
- [MADR学術論文（CEUR-WS Vol-2072, 2018）](https://ceur-ws.org/Vol-2072/paper9.pdf)
- [Michael Nygard 原提案（2011）](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [AI + ADR統合の最新動向](https://handsonarchitects.com/blog/2025/using-generative-ai-as-architect-buddy-for-adrs/)
- [ADRテンプレート一覧](https://adr.github.io/adr-templates/)
- [joelparkerhenderson ADR集](https://github.com/joelparkerhenderson/architecture-decision-record)
