param(
  [Parameter(Mandatory=$true)][string]$ExpectedHead,
  [string]$Worktree = 'E:\knowledge_builder\self-workspace\publish-worktrees\development-knowledge-builder',
  [string]$Branch = 'codex/development-knowledge-builder'
)
$ErrorActionPreference = 'Stop'
$GitPath = 'C:\Program Files\Git\cmd\git.exe'
$Baseline = '6f6ab1547cd9ca2dc365bd187a99a7bc4ecf86ce'
$GitOptions = @(
  '-c','filter.lfs.process=',
  '-c','filter.lfs.smudge=cat',
  '-c','filter.lfs.clean=cat',
  '-c','filter.lfs.required=false'
)
$GitDirectory = Split-Path -Parent $GitPath
if (-not (($env:PATH -split ';') -contains $GitDirectory)) {
  $env:PATH = "$GitDirectory;$env:PATH"
}

function Invoke-GitText([string[]]$GitArguments) {
  $token = [Guid]::NewGuid().ToString('N')
  $stdoutPath = Join-Path $env:TEMP "ckb-development-rollback-$token.out"
  $stderrPath = Join-Path $env:TEMP "ckb-development-rollback-$token.err"
  try {
    $process = Start-Process -FilePath $GitPath -ArgumentList ($GitOptions + $GitArguments) `
      -WorkingDirectory $Worktree -Wait -PassThru -NoNewWindow `
      -RedirectStandardOutput $stdoutPath -RedirectStandardError $stderrPath
    $stdout = if (Test-Path -LiteralPath $stdoutPath) { [IO.File]::ReadAllText($stdoutPath, [Text.Encoding]::UTF8) } else { '' }
    $stderr = if (Test-Path -LiteralPath $stderrPath) { [IO.File]::ReadAllText($stderrPath, [Text.Encoding]::UTF8) } else { '' }
    if ($process.ExitCode -ne 0) { throw "git $($GitArguments -join ' ') failed: $stderr" }
    return $stdout.Trim()
  } finally {
    Remove-Item -LiteralPath $stdoutPath -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $stderrPath -Force -ErrorAction SilentlyContinue
  }
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
