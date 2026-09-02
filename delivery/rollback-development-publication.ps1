param(
  [Parameter(Mandatory=$true)][string]$ExpectedHead,
  [string]$Worktree = 'E:\knowledge_builder\self-workspace\publish-worktrees\development-knowledge-builder'
)
$ErrorActionPreference = 'Stop'
$GitPath = 'C:\Program Files\Git\cmd\git.exe'
$Branch = 'codex/development-knowledge-builder'
$Baseline = 'e864d84c361e1d871ca43f535f8ff85cb1eaa117'

function Invoke-GitText([string[]]$GitArguments) {
  $output = & $GitPath -C $Worktree @GitArguments 2>&1
  if ($LASTEXITCODE -ne 0) { throw "git $($GitArguments -join ' ') failed: $output" }
  return ($output -join "`n").Trim()
}

if (-not (Test-Path -LiteralPath $Worktree -PathType Container)) { throw "worktree missing: $Worktree" }
$currentBranch = Invoke-GitText @('branch','--show-current')
$currentHead = Invoke-GitText @('rev-parse','HEAD')
$status = Invoke-GitText @('status','--porcelain=v1','--untracked-files=all')
if ($currentBranch -ne $Branch) { throw "branch guard failed: expected=$Branch actual=$currentBranch" }
if ($currentHead -ne $ExpectedHead) { throw "HEAD guard failed: expected=$ExpectedHead actual=$currentHead" }
if ($status.Length -ne 0) { throw 'clean worktree required' }
Invoke-GitText @('merge-base','--is-ancestor',$Baseline,$currentHead) | Out-Null
Invoke-GitText @('reset','--hard',$Baseline) | Out-Null
$after = Invoke-GitText @('rev-parse','HEAD')
$afterStatus = Invoke-GitText @('status','--porcelain=v1','--untracked-files=all')
$passed = $after -eq $Baseline -and $afterStatus.Length -eq 0
[ordered]@{
  schema_version = 1
  status = $(if ($passed) { 'rolled-back' } else { 'verification-failed' })
  branch = $Branch
  before = $currentHead
  after = $after
  baseline = $Baseline
  clean = $afterStatus.Length -eq 0
} | ConvertTo-Json -Depth 4
if (-not $passed) { exit 5 }
