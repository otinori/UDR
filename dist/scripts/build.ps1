#requires -Version 7.0
<#
.SYNOPSIS
  .claude/ を唯一の source of truth として配布先へミラーする。

.DESCRIPTION
  .claude\skills\   → plugins\udr\skills\      (プラグインマーケットプレイス用)

  .claude\deploy\    → plugins\udr\ (root)     (GEMINI.md / .gemini/ — プラグイン配布用)

  dist\scripts\install.ps1 は .claude\skills\ と .claude\deploy\ を直接参照するため
  (独立ミラーを持たない)、本スクリプトの対象外。

.EXAMPLE
  pwsh dist\scripts\build.ps1
#>

$ErrorActionPreference = 'Stop'

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistRoot   = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$RepoRoot   = (Resolve-Path (Join-Path $DistRoot '..')).Path
$SkillsSrc  = Join-Path $RepoRoot '.claude\skills'
$DeploySrc  = Join-Path $RepoRoot '.claude\deploy'

if (-not (Test-Path $SkillsSrc -PathType Container)) {
  Write-Error ".claude\skills が見つかりません: $SkillsSrc"
  exit 1
}

# ── 1. skills ミラー ────────────────────────────────────────
Write-Host ">> Rebuilding skills mirror from .claude\skills"
Write-Host "   src: $SkillsSrc"

$Dst = Join-Path $RepoRoot 'plugins\udr\skills'
Write-Host ">> dst: $Dst"
if (Test-Path $Dst) { Remove-Item -Recurse -Force -Path $Dst }
New-Item -ItemType Directory -Path $Dst -Force | Out-Null
Copy-Item -Recurse -Force -Path (Join-Path $SkillsSrc '*') -Destination $Dst

# .bak-* 混入除去
Get-ChildItem -Path $Dst -Recurse -Force |
  Where-Object { $_.Name -like '*.bak-*' } |
  Remove-Item -Recurse -Force

$count = (Get-ChildItem -Path $Dst -Recurse -File).Count
Write-Host "   -> $count files"

# ── 2. デプロイテンプレートミラー ───────────────────────────
if (Test-Path $DeploySrc -PathType Container) {
  Write-Host ""
  Write-Host ">> Rebuilding deploy template mirror from .claude\deploy"
  Write-Host "   src: $DeploySrc"

  $Dst = Join-Path $RepoRoot 'plugins\udr'
  New-Item -ItemType Directory -Path $Dst -Force | Out-Null
  # hidden ファイル・ディレクトリ (.gemini/ 等) も含めてコピー
  Get-ChildItem -Path $DeploySrc -Force | ForEach-Object {
    Copy-Item -Recurse -Force -Path $_.FullName -Destination $Dst
  }
  Write-Host "   -> $Dst"
} else {
  Write-Host ""
  Write-Host "   (.claude\deploy not found, skipping deploy templates)"
}

Write-Host ""
Write-Host ">> Done."
