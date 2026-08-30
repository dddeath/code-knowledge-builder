[CmdletBinding()]
param(
    [switch]$Probe,
    [string]$ProbeRoot = 'E:\knowledge_builder\artifacts\reference-ingest-v1-20260830-01\rollback-probe'
)

$ErrorActionPreference = 'Stop'
$Artifact = 'E:\knowledge_builder\artifacts\reference-ingest-v1-20260830-01'
$Source = 'E:\knowledge_builder\self-workspace\source'
$Installed = 'C:\Users\19739\.codex\skills\code-knowledge-builder'
$KnowledgeBase = 'E:\knowledge_builder\self-workspace\knowledge-base'
$Python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe'
$Ckb = 'C:\Users\19739\.codex\skills\code-knowledge-builder\scripts\ckb.py'
$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if ($GitCommand) {
    $Git = $GitCommand.Source
} elseif (Test-Path -LiteralPath 'C:\Program Files\Git\cmd\git.exe') {
    $Git = 'C:\Program Files\Git\cmd\git.exe'
} elseif (Test-Path -LiteralPath 'C:\Program Files\Git\bin\git.exe') {
    $Git = 'C:\Program Files\Git\bin\git.exe'
} else {
    throw 'Windows Git executable was not found'
}
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$OutputEncoding = [Text.UTF8Encoding]::new($false)
$env:PATH = "$(Split-Path -Parent $Git);$env:PATH"
if (-not (($env:PATHEXT -split ';') -contains '.EXE')) { $env:PATHEXT = '.COM;.EXE;.BAT;.CMD;' + $env:PATHEXT }
$ReferenceId = 'reference-829120de44175ec3a772a70f940da830'
$Title = 'CKB 5.3.0 审阅文本资料吸收'
$BaselineCommit = '3f117b8'
$FeatureCommit = 'b666233'
$ProtocolCommit = '02b3f9b'

function Invoke-Native([string]$File, [string[]]$Arguments) {
    $quoted = ($Arguments | ForEach-Object { '"' + ($_ -replace '"', '\"') + '"' }) -join ' '
    $stdout = [IO.Path]::GetTempFileName()
    $stderr = [IO.Path]::GetTempFileName()
    try {
        $process = Start-Process -FilePath $File -ArgumentList $quoted -NoNewWindow -PassThru -Wait -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        $outText = if ((Get-Item -LiteralPath $stdout).Length -gt 0) { Get-Content -Raw -Encoding UTF8 -LiteralPath $stdout } else { '' }
        $errText = if ((Get-Item -LiteralPath $stderr).Length -gt 0) { Get-Content -Raw -Encoding UTF8 -LiteralPath $stderr } else { '' }
        if ($process.ExitCode -ne 0) {
            throw "command failed ($($process.ExitCode)): $File $($Arguments -join ' ')`n$errText"
        }
        return $outText.TrimEnd()
    } finally {
        Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-Checked([string]$File, [string[]]$Arguments) {
    [void](Invoke-Native $File $Arguments)
}

if ($Probe) {
    $allowed = Join-Path $Artifact 'rollback-probe'
    if ([IO.Path]::GetFullPath($ProbeRoot) -ne [IO.Path]::GetFullPath($allowed)) { throw "ProbeRoot must be $allowed" }
    if (Test-Path -LiteralPath $ProbeRoot) { Remove-Item -LiteralPath $ProbeRoot -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $ProbeRoot | Out-Null
    $clone = Join-Path $ProbeRoot 'source'
    Invoke-Checked $Git @('clone','--no-local',$Source,$clone)
    Invoke-Checked $Git @('-C',$clone,'checkout',$ProtocolCommit)
    Invoke-Checked $Git @('-C',$clone,'config','user.email','rollback-probe@local.invalid')
    Invoke-Checked $Git @('-C',$clone,'config','user.name','CKB Rollback Probe')
    Invoke-Checked $Git @('-C',$clone,'revert','--no-edit',$ProtocolCommit,$FeatureCommit)
    Invoke-Checked $Git @('-C',$clone,'diff','--quiet',$BaselineCommit,'HEAD')
    $testOut = Join-Path $ProbeRoot 'reference-test.stdout.txt'
    $testErr = Join-Path $ProbeRoot 'reference-test.stderr.txt'
    $process = Start-Process -FilePath $Python -ArgumentList @(
        'E:\knowledge_builder\self-workspace\source\tests\test_ckb.py',
        'CodeKnowledgeBuilderTests.test_reviewed_text_reference_is_searchable_revisioned_and_reversible','-v'
    ) -NoNewWindow -PassThru -Wait -RedirectStandardOutput $testOut -RedirectStandardError $testErr
    if ($process.ExitCode -ne 0) { throw "isolated reference rollback test failed: $(Get-Content -Raw $testErr)" }
    [ordered]@{
        status = 'passed'
        mode = 'isolated-probe'
        source_git_revert_matches = $BaselineCommit
        reference_lifecycle_test_exit = $process.ExitCode
        reference_lifecycle_test = $testErr
        private_runtime_changed = $false
    } | ConvertTo-Json -Depth 4
    exit 0
}

$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$repoStatus = Invoke-Native $Git @('-C',$Source,'status','--porcelain')
if ($repoStatus) { throw 'source repository must be clean before rollback' }
$current = (Invoke-Native $Git @('-C',$Source,'rev-parse','HEAD')).Trim()
if (-not $current.StartsWith($ProtocolCommit)) { throw "source HEAD is not the verified 5.3.0 commit: $current" }

$manifest = Join-Path $KnowledgeBase "references\manifests\$ReferenceId.json"
if (Test-Path -LiteralPath $manifest) {
    Invoke-Checked $Python @('-X','utf8',$Ckb,'reference','rollback','--out',$KnowledgeBase,'--reference',$ReferenceId)
}

Invoke-Checked $Git @('-C',$Source,'revert','--no-edit',$ProtocolCommit,$FeatureCommit)
Invoke-Checked $Git @('-C',$Source,'diff','--quiet',$BaselineCommit,'HEAD')

$oldPackage = Join-Path $Artifact 'original-dist\code-knowledge-builder-lite-5.2.9.zip'
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $oldPackage).Hash -ne '3B8B994448B7B1B73F79AE520ECFD7B7706C6B87D0F43011FB056C7029ADF0AD') { throw '5.2.9 rollback package hash mismatch' }
$temp = Join-Path $env:TEMP 'ckb-reference-rollback-5.2.9'
if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Recurse -Force }
Expand-Archive -LiteralPath $oldPackage -DestinationPath $temp -Force
Copy-Item -Path (Join-Path $temp 'code-knowledge-builder\*') -Destination $Installed -Recurse -Force
foreach ($relative in @('scripts\ckb_core\reference_documents.py','references\reference-ingest.md')) {
    $path = Join-Path $Installed $relative
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
}
Remove-Item -LiteralPath $temp -Recurse -Force

foreach ($path in @(
    (Join-Path $KnowledgeBase "human\changes\$Title.md"),
    (Join-Path $KnowledgeBase "markdown\changes\$Title.md"),
    (Join-Path $KnowledgeBase "workspace-meta\notes\$Title.json")
)) {
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
}
$referenceRoot = Join-Path $KnowledgeBase 'references'
if (Test-Path -LiteralPath $referenceRoot) { Remove-Item -LiteralPath $referenceRoot -Recurse -Force }
foreach ($relative in @('human\references','markdown\references')) {
    $path = Join-Path $KnowledgeBase $relative
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force }
}
foreach ($relative in @('human\REFERENCES.md','markdown\REFERENCES.md')) {
    $path = Join-Path $KnowledgeBase $relative
    if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
}

$refresh = "import sys; from pathlib import Path; sys.path.insert(0, r'$Installed\scripts'); from ckb_core.work_record_index import refresh_work_record_index; print(refresh_work_record_index(Path(r'$KnowledgeBase')))"
Invoke-Checked $Python @('-X','utf8','-c',$refresh)
Invoke-Checked $Python @('-X','utf8',$Ckb,'reindex','--out',$KnowledgeBase)
Invoke-Checked $Python @('-X','utf8',$Ckb,'agent-policy','install','--out',$KnowledgeBase,'--workspace-root','E:\knowledge_builder','--python',$Python,'--ckb',$Ckb)
Invoke-Checked $Python @('-X','utf8',$Ckb,'feedback','audit','--out',$KnowledgeBase)
Invoke-Checked $Python @('-X','utf8',$Ckb,'agent-policy','check','--out',$KnowledgeBase)

$owned = [ordered]@{
    'E:\knowledge_builder\dist\code-knowledge-builder-lite-5.3.0.zip' = 'C044568B52E81736041C2353C583C2C8FB1D7D64899DC4FCF038D56879D7ED69'
    'E:\knowledge_builder\dist\code-knowledge-builder-lite-5.3.0.manifest.json' = '71EE05F04DE702FEB2A1505C7950553B36902C0EF5203134DB746A857F885B14'
    'E:\knowledge_builder\dist\code-knowledge-builder-full-win-x64-5.3.0.zip' = 'DABB8A928246735CC9EA6E6F5D33D6B9A4341202822DF24473E6A17377DB8DE4'
    'E:\knowledge_builder\dist\code-knowledge-builder-full-win-x64-5.3.0.manifest.json' = '57ECC9A079D5F0C0CBC799655C94C708C2C7B48596439ECAE5BBA366BF66D35F'
}
foreach ($entry in $owned.GetEnumerator()) {
    if (Test-Path -LiteralPath $entry.Key) {
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $entry.Key).Hash -ne $entry.Value) { throw "owned artifact changed: $($entry.Key)" }
        Remove-Item -LiteralPath $entry.Key -Force
    }
}

$versionText = Get-Content -Raw -Encoding UTF8 (Join-Path $Installed 'SKILL.md')
if ($versionText -notmatch 'version: "5\.2\.9"') { throw 'installed Skill version rollback failed' }
$protocol = Get-Content -Raw -Encoding UTF8 (Join-Path $KnowledgeBase 'workspace-meta\agent-protocol.json') | ConvertFrom-Json
if ($protocol.protocol_version -ne '1.3.0') { throw 'Agent protocol rollback failed' }
if (Test-Path -LiteralPath (Join-Path $KnowledgeBase 'human\REFERENCES.md')) { throw 'reference navigation remained after rollback' }

[ordered]@{
    status = 'passed'
    mode = 'real-rollback'
    source_branch = 'codex/reference-ingest-v1'
    source_tree = $BaselineCommit
    restored_skill_version = '5.2.9'
    restored_protocol_version = '1.3.0'
    reference_removed = $true
    private_runtime_changed = $false
} | ConvertTo-Json -Depth 4
