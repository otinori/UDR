# UDR Skills — 他環境への展開手順

> ⚠️ **実験的プロジェクトです。** Phase 1 PoC 段階のため、スキーマ・コマンド体系は今後変更される可能性があります。

**バージョン:** `udr-skills 0.6.0.1-PoC` (Phase 1 PoC / プロンプトレベル実装)

このバンドルは Claude Code で動作する UDR (Universal Decision Record) の skill 一式です。
MCP Server は Phase 2 で提供されます。本 Phase では Claude が YAML を直接読み書きします。

> **どの導入方法を使う？**
> Claude Code 中心なら **プラグインマーケットプレイス版が推奨**です（`claude plugin marketplace add otinori/UDR` → `claude plugin install udr@udr-marketplace`、呼び出しは `/udr:udr-*`）。
> **本書は「スクリプトによる手動展開」**（プラグイン非対応環境・Gemini/Codex 主体・任意 repo への一括コピー向けの代替手段）の手順です。両者は同じ source of truth（UDR リポジトリの `.claude/skills/` / `.claude/deploy/`）から取得した同一内容で、`.udr/` データは共通です。詳細は repo ルートの `README.md`「配布チャネル」節を参照。
> **注意:** 本書の手動展開では skill のみが導入されます（`git commit` 前のリマインド等の hook はプラグイン版のみ。詳細は repo ルートの `README.md`「前提・依存関係」節を参照）。

---

## 1. 何が含まれるか

`dist/` 自体には skill 本体は含まれません（独立ミラーを廃止し、UDR リポジトリの `.claude/skills/`・`.claude/deploy/` を **source of truth として直接参照**する方式に変更したため、[0.6.0.1-PoC] 以降）。`install.sh` / `install.ps1` を UDR リポジトリの clone 内から実行してください。

```
UDR/ (このリポジトリの clone)
├── .claude/
│   ├── skills/                 (★ source of truth。install.sh がここから直接コピーする)
│   │   ├── README.md
│   │   ├── _udr-shared/
│   │   │   └── CONVENTIONS.md  (全 skill が参照する共通規約)
│   │   ├── udr-init/SKILL.md
│   │   ├── udr-record/SKILL.md
│   │   ├── udr-search/SKILL.md
│   │   ├── udr-sync/SKILL.md
│   │   ├── udr-trace/SKILL.md
│   │   ├── udr-review/SKILL.md
│   │   └── udr-dashboard/SKILL.md
│   └── deploy/                 (★ source of truth。GEMINI.md / .gemini/ 拡張テンプレート)
└── dist/
    ├── usage.md                (この文書)
    ├── VERSION                 (バージョン情報)
    └── scripts/
        ├── install.sh          (POSIX 用インストーラ、.claude/skills を直接参照)
        ├── install.ps1         (Windows PowerShell 用インストーラ)
        ├── build.sh            (.claude/ → plugins/udr/ ミラー再生成。UDR 本体リポジトリ内でのみ使用)
        └── build.ps1           (同 PowerShell 版)
```

## 2. 前提

| 項目 | 要件 |
|---|---|
| Claude Code CLI | skills 機能対応版 (`~/.claude/skills/` または `<project>/.claude/skills/` を認識すること) |
| Git リポジトリ | UDR は Git 永続を前提 (C-003)。非 Git ディレクトリでは `udr-init` が失敗 |
| シェル | bash (POSIX/WSL/Git Bash) または PowerShell 7+ |
| UDR データ形式 | YAML (js-yaml SAFE schema 互換) |

---

## 3. 展開パターン

以下 4 パターンから選択します。**A が推奨** (プロジェクトごとに Git 管理できチーム共有も容易)。

### A. プロジェクトローカル展開 (推奨)

対象プロジェクトの `.claude/skills/` にコピー。Git コミットすればチーム全員で共有可。

#### A-1. スクリプト展開 (ワンコマンド)

```bash
# POSIX
bash dist/scripts/install.sh /path/to/target-project

# Windows PowerShell
pwsh dist/scripts/install.ps1 C:\path\to\target-project
```

スクリプトは以下を行います:

1. target に `.claude/skills/` ディレクトリを作成
2. UDR リポジトリの `.claude/skills/`（source of truth）の全内容をコピー
3. 既存 `udr-*` skill があれば `.bak-<timestamp>` にバックアップ
4. target に `.gitignore` がなければ作成し `.claude/skills/*.bak-*` を追加
5. 最後に「`/udr-init` を Claude Code で実行してください」と案内

#### A-2. 手動展開

```bash
# 対象プロジェクトのルートで（/path/to/udr-repo は UDR リポジトリの clone 先）
mkdir -p .claude/skills
cp -r /path/to/udr-repo/.claude/skills/* .claude/skills/
```

その後 Claude Code でプロジェクトを開き:

```
/udr-init
```

### B. ユーザーグローバル展開 (全プロジェクトで使う)

`~/.claude/skills/` に配置すると、どのプロジェクトでも `/udr-*` が使えます。

```bash
# POSIX / WSL / Git Bash（UDR リポジトリの clone のルートで実行）
mkdir -p ~/.claude/skills
cp -r .claude/skills/* ~/.claude/skills/
```

```powershell
# Windows PowerShell（UDR リポジトリの clone のルートで実行）
New-Item -ItemType Directory -Path "$HOME\.claude\skills" -Force
Copy-Item -Recurse -Force .claude\skills\* "$HOME\.claude\skills\"
```

**注意:**
- プロジェクトローカル (`.claude/skills/`) が存在する場合はそちらが優先されます。
- `_udr-shared/CONVENTIONS.md` のパス解決はグローバル展開でも動作しますが、プロジェクト側に同名 skill があれば上書きされるため、**A との併用は避ける**。

### C. チーム共有 (Git 経由)

上記 A をプロジェクトの Git にコミットします:

```bash
cd /path/to/target-project
# install.sh で展開後
git add .claude/skills
git commit -m "Add UDR skills (Phase 1 PoC)"
git push
```

他メンバーは `git pull` するだけで skill が反映されます。

### D. 他 AI ツールでの参照・記録 (参考情報)

UDR データ (`.udr/`) と sync 先ファイルは複数の AI ツールで共有できます。ツールごとのセットアップ:

| ツール | context ファイル | 記録手段 | 備考 |
|---|---|---|---|
| **Google Gemini CLI** | `GEMINI.md` | `gemini-prompts/udr-*.md` テンプレートを参照して記録 | `install.sh --gemini` でセットアップ |
| **OpenAI Codex CLI** | `AGENTS.md` | `codex-prompts/udr-*.md` テンプレートを参照して記録 | `install.sh --codex` でセットアップ案内 |
| GitHub Copilot | `.github/copilot-instructions.md` + `.github/instructions/udr-decisions.instructions.md` | 参照のみ（記録は Claude / Gemini / Codex で） | `/udr-sync` が自動で両方に書き込む |
| Cursor | `.cursorrules` | 参照のみ | `/udr-sync --target .cursorrules` |
| Windsurf | `.windsurfrules` | 参照のみ | 同上 |

#### Gemini CLI セットアップ (`--gemini`)

```bash
bash dist/scripts/install.sh /path/to/target-project --gemini
```

以下が生成されます:
- `GEMINI.md` — Gemini CLI 向け指示書（UDR-SYNC マーカー付き）
- `.gemini/extensions/udr/gemini-extension.json` — Gemini 拡張マニフェスト

操作時は `@.claude/skills/_udr-shared/templates/gemini-prompts/udr-record.md` のようにテンプレートを参照します。

#### Codex CLI セットアップ (`--codex`)

```bash
bash dist/scripts/install.sh /path/to/target-project --codex
```

Codex CLI 向けのセットアップ手順を案内します（AGENTS.md への UDR ポリシー追加）。
操作テンプレートは `.claude/skills/_udr-shared/templates/codex-prompts/` を参照してください。

---

## 4. 初回セットアップ (展開後、共通)

1. Claude Code で対象プロジェクトを開く
2. `/udr-init` を実行
   - `repo_short` の確認プロンプトに回答
   - **使う AI ツール (`tools`) を選択**（例: `claude` / `gemini` / `codex`）。sync 先はこの宣言から導出される
   - `.udr/records/`、`.udr/config.yaml`、`.gitignore` 更新が行われる
3. `/udr-record` で最初の 1 件を記録してみる
4. `/udr-sync` で CLAUDE.md / `.github/instructions/udr-decisions.instructions.md` に反映
5. `git status` で変更内容を確認し、必要に応じてコミット

---

## 5. アップデート手順 (新バージョンが出たとき)

### A / C で展開している場合

```bash
# 新 dist を取得して再実行 (既存は .bak-<ts> に退避される)
bash dist/scripts/install.sh /path/to/target-project
```

`_udr-shared/CONVENTIONS.md` の互換性:

- **0.x 系内**: 後方互換。Phase 1 で書いた UDR はそのまま使える。
- **1.0 (Phase 2 MCP)**: YAML スキーマは互換。skill は MCP tool に置換されるが UDR データは移行不要。

### B で展開している場合

```bash
# UDR リポジトリの clone を最新化してから
cp -rf .claude/skills/* ~/.claude/skills/
```

上書きコピー。旧版のバックアップが必要ならスクリプト利用を推奨。

---

## 6. アンインストール

### skill のみ削除 (UDR データは残す、**推奨**)

```bash
# プロジェクトローカル
rm -rf /path/to/target-project/.claude/skills/udr-*
rm -rf /path/to/target-project/.claude/skills/_udr-shared

# グローバル
rm -rf ~/.claude/skills/udr-*
rm -rf ~/.claude/skills/_udr-shared
```

CLAUDE.md 等の `<!-- [UDR-SYNC-START] -->` ～ `<!-- [UDR-SYNC-END] -->` セクションは手動で削除してください (sync 断絶後も UDR ポリシーとして残す判断もあり)。

### UDR データも完全削除 (非推奨)

**判断記録の不滅性 (BR-001)** に反します。本番プロジェクトでは実施しないこと。開発用の検証プロジェクトのみ:

```bash
rm -rf /path/to/target-project/.udr
```

Git 履歴には残るので完全消去にはフィルタブランチ等が別途必要です。

---

## 7. Troubleshooting

| 症状 | 原因 | 対処 |
|---|---|---|
| `/udr-init` が "Git リポジトリ配下で実行してください" で失敗 | 非 Git ディレクトリ | `git init` を実行するか、Git リポ配下に移動 |
| skill が `/` 補完で表示されない | Claude Code の skill 認識がリフレッシュされていない | セッションを開き直す |
| `.udr/records/` が Git で追跡されない | 個人プロジェクトでは `.udr/` 全体を `.gitignore` で除外する方針（判断記録 UDR-UDR-20260719T0846-d39）。意図した挙動 | チーム開発で `.udr/` を private リポジトリ内で共有したい場合のみ、`.gitignore` を `.udr/index.json` と `.udr/audit.log` に絞る (UDR-INIT-002) |
| `/udr-sync` が何も書き込まない | 有効な UDR が 0 件 (全部 superseded / rejected) | まず `/udr-record` で追加 |
| Windows で `/udr-sync` が失敗 | NTFS の rename atomic 保証が限定的 | `.bak` から手動復元。詳細は AR2-02 / UDR-SYNC-010 |
| skill が重複展開されている | A と B を併用 | B 側を削除して A のみに統一 |

---

## 8. Phase 2 移行時の注意

Phase 2 で MCP Server (`@axis/udr-mcp-server`) が提供されたら:

1. `.udr/records/*.yaml` と `.udr/config.yaml` はそのまま使える (YAML スキーマ互換)
2. `.claude/skills/udr-*` は MCP tool に置換されるので削除可
3. sync 先ファイルの `<!-- [UDR-SYNC-START] -->` マーカーは互換なので再 sync すれば新形式で上書きされる
4. `audit.log` は Phase 1/2 で共通フォーマット

---

## 9. 参考

- 共通規約: UDR リポジトリの `.claude/skills/_udr-shared/CONVENTIONS.md`
- 利用順序・要件カバレッジ: UDR リポジトリの `.claude/skills/README.md`
- 要件定義: UDR リポジトリの `docs/Phase1_要求定義/要求一覧.md`
