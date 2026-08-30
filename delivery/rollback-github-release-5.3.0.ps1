[CmdletBinding()]
param(
    [switch]$Probe,
    [string]$Checkout = 'E:\knowledge_builder\self-workspace\github-publication'
)

$ErrorActionPreference = 'Stop'
$Repo = 'dddeath/code-knowledge-builder'
$Tag = 'v5.3.0'
$Baseline = 'e1cab441508b5eb47ea7523f2e3005922b8f1e60'
$Git = 'C:\Program Files\Git\cmd\git.exe'
$Gh = 'C:\Program Files\GitHub CLI\gh.exe'
if (-not (Test-Path -LiteralPath $Git)) { throw 'Windows Git not found' }
if (-not (Test-Path -LiteralPath $Gh)) { throw 'GitHub CLI not found' }
$env:PATH = "$(Split-Path -Parent $Git);$env:PATH"
if (-not (($env:PATHEXT -split ';') -contains '.EXE')) { $env:PATHEXT = '.COM;.EXE;.BAT;.CMD;' + $env:PATHEXT }

function Invoke-Native([string]$File, [string[]]$Arguments) {
    $quoted = ($Arguments | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join ' '
    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()
    try {
        $process = Start-Process -FilePath $File -ArgumentList $quoted -NoNewWindow -PassThru -Wait -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $outText = if ((Get-Item -LiteralPath $stdout).Length) { Get-Content -Raw -Encoding UTF8 -LiteralPath $stdout } else { '' }
        $errText = if ((Get-Item -LiteralPath $stderr).Length) { Get-Content -Raw -Encoding UTF8 -LiteralPath $stderr } else { '' }
        if ($process.ExitCode -ne 0) { throw "command failed ($($process.ExitCode)): $File $($Arguments -join ' ')`n$errText" }
        return $outText.Trim()
    } finally {
        Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
    }
}

$release = Invoke-Native $Gh @('release','view',$Tag,'--repo',$Repo,'--json','tagName,targetCommitish,url,isDraft,isPrerelease') | ConvertFrom-Json
Invoke-Native $Git @('-C',$Checkout,'fetch','origin','main','--tags') | Out-Null
$releaseCommit = (Invoke-Native $Git @('-C',$Checkout,'rev-list','-n','1',$Tag)).Trim()
$parent = (Invoke-Native $Git @('-C',$Checkout,'rev-parse',"$releaseCommit^1")).Trim()
$remoteMain = (Invoke-Native $Git @('-C',$Checkout,'rev-parse','origin/main')).Trim()
if ($parent -ne $Baseline) { throw "release parent is not verified baseline: $parent" }
if ($releaseCommit -ne $remoteMain) { throw "remote main no longer equals release commit: $remoteMain" }
if ($Probe) {
    [ordered]@{ status='passed'; mode='read-only-probe'; repository=$Repo; tag=$Tag; release_commit=$releaseCommit; baseline=$parent; remote_main=$remoteMain; release_url=$release.url } | ConvertTo-Json
    exit 0
}
$status = Invoke-Native $Git @('-C',$Checkout,'status','--porcelain')
if ($status) { throw 'publication checkout must be clean before remote rollback' }
Invoke-Native $Git @('-C',$Checkout,'switch','main') | Out-Null
Invoke-Native $Git @('-C',$Checkout,'pull','--ff-only','origin','main') | Out-Null
Invoke-Native $Git @('-C',$Checkout,'revert','--no-edit',$releaseCommit) | Out-Null
Invoke-Native $Git @('-C',$Checkout,'push','origin','main') | Out-Null
Invoke-Native $Gh @('release','delete',$Tag,'--repo',$Repo,'--yes','--cleanup-tag') | Out-Null
$newMain = (Invoke-Native $Git @('-C',$Checkout,'rev-parse','HEAD')).Trim()
[ordered]@{ status='passed'; mode='remote-rollback'; repository=$Repo; reverted_release_commit=$releaseCommit; rollback_commit=$newMain; release_deleted=$true } | ConvertTo-Json
