param(
    [Parameter(Mandatory=$true)][string]$Repository,
    [string]$ExpectedHead = ""
)
$ErrorActionPreference = "Stop"
$Git = "C:\Program Files\Git\cmd\git.exe"
$Baseline = "62b15376e8de899a2eaeda1d10bcc62bd1b3d2a8"
$Owned = "references/design/obsidian-canvas-agent-visualization"
function Quote-Argument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}
function Invoke-Git([string[]]$GitArguments) {
    $Info = New-Object System.Diagnostics.ProcessStartInfo
    $Info.FileName = $Git
    $Info.Arguments = (($GitArguments | ForEach-Object { Quote-Argument ([string]$_) }) -join ' ')
    $Info.UseShellExecute = $false
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    $Info.CreateNoWindow = $true
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $Info
    if (-not $Process.Start()) { throw "failed to start git" }
    $Stdout = $Process.StandardOutput.ReadToEnd()
    $Stderr = $Process.StandardError.ReadToEnd()
    $Process.WaitForExit()
    return [PSCustomObject]@{ ExitCode = $Process.ExitCode; Stdout = $Stdout; Stderr = $Stderr }
}
$Result = Invoke-Git @('-C', $Repository, 'rev-parse', 'HEAD')
if ($Result.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($Result.Stdout)) { throw "git rev-parse failed: $($Result.Stderr)" }
$Head = $Result.Stdout.Trim()
if ($ExpectedHead -and $Head -ne $ExpectedHead) { throw "HEAD drift: expected $ExpectedHead, got $Head" }
$Result = Invoke-Git @('-C', $Repository, 'status', '--porcelain')
if ($Result.ExitCode -ne 0 -or -not [string]::IsNullOrWhiteSpace($Result.Stdout)) { throw "rollback requires a clean worktree: $($Result.Stderr)" }
$Result = Invoke-Git @('-C', $Repository, 'diff', '--name-only', "$Baseline..HEAD")
$Changed = @($Result.Stdout -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
if ($Result.ExitCode -ne 0 -or $Changed.Count -eq 0) { throw "no design delivery changes found: $($Result.Stderr)" }
foreach ($PathValue in $Changed) {
    $PathText = [string]$PathValue
    if (-not $PathText.StartsWith($Owned + "/")) { throw "change outside rollback scope: $PathText" }
}
$Result = Invoke-Git @('-C', $Repository, 'rm', '-r', '--', $Owned)
if ($Result.ExitCode -ne 0) { throw "git rm failed: $($Result.Stderr)" }
$Result = Invoke-Git @('-C', $Repository, 'diff', '--cached', '--quiet', $Baseline, '--', '.')
if ($Result.ExitCode -ne 0) { throw "staged rollback does not match baseline" }
$Result = Invoke-Git @('-C', $Repository, 'diff', '--cached', '--name-only')
$Staged = @($Result.Stdout -split "`r?`n" | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
Write-Output "ROLLBACK_READY=passed"
Write-Output "BASELINE=$Baseline"
Write-Output "OWNED_PATH=$Owned"
Write-Output "STAGED_DELETIONS=$($Staged.Count)"
Write-Output "NEXT=review staged deletion, then commit the rollback"
