[CmdletBinding()]
param(
  [string]$Root,
  [string]$Write
)

$ErrorActionPreference = 'Stop'
$ExpectedCurrent = '255ff54a543a1658da678fc6bdfb4b526b58bce6ebd55d0a620c1ea2891c0b8a'
$ExpectedBaseline = '63b5f320d600f92c4aa83dc71aa45f464773e685c5706b41f1b71d7c04ac0135'

if (-not $Root) {
  $Root = Join-Path $PSScriptRoot '..\..'
}
$Root = (Resolve-Path -LiteralPath $Root).Path
$Readme = Join-Path $Root 'README.md'
$ArtifactDirectory = Join-Path $Root 'delivery\readability-readme-v4'
$Baseline = Join-Path $ArtifactDirectory 'README.baseline.md'

if (-not (Test-Path -LiteralPath $Readme -PathType Leaf)) {
  throw "README is missing: $Readme"
}
if (-not (Test-Path -LiteralPath $Baseline -PathType Leaf)) {
  throw "README baseline is missing: $Baseline"
}

$CurrentHash = (Get-FileHash -LiteralPath $Readme -Algorithm SHA256).Hash.ToLowerInvariant()
$BaselineHash = (Get-FileHash -LiteralPath $Baseline -Algorithm SHA256).Hash.ToLowerInvariant()
if ($CurrentHash -ne $ExpectedCurrent) {
  throw "README drifted: expected=$ExpectedCurrent actual=$CurrentHash"
}
if ($BaselineHash -ne $ExpectedBaseline) {
  throw "README baseline drifted: expected=$ExpectedBaseline actual=$BaselineHash"
}

$OwnedFiles = @(
  Get-ChildItem -LiteralPath $ArtifactDirectory -Recurse -File |
    ForEach-Object { $_.FullName.Substring($Root.Length + 1).Replace('\', '/') } |
    Sort-Object
)
$Temporary = Join-Path $Root ('.README.readability-v4.rollback.{0}.tmp' -f ([Guid]::NewGuid().ToString('N')))
[System.IO.File]::WriteAllBytes($Temporary, [System.IO.File]::ReadAllBytes($Baseline))
Move-Item -LiteralPath $Temporary -Destination $Readme -Force

$RestoredHash = (Get-FileHash -LiteralPath $Readme -Algorithm SHA256).Hash.ToLowerInvariant()
if ($RestoredHash -ne $ExpectedBaseline) {
  throw "README rollback hash mismatch: expected=$ExpectedBaseline actual=$RestoredHash"
}

$WritePath = $null
if ($Write) {
  $WritePath = [System.IO.Path]::GetFullPath($Write)
  if ($WritePath.StartsWith($ArtifactDirectory, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'The rollback record must be written outside the artifact directory.'
  }
}

Remove-Item -LiteralPath $ArtifactDirectory -Recurse -Force
if (Test-Path -LiteralPath $ArtifactDirectory) {
  throw "Artifact directory was not removed: $ArtifactDirectory"
}

$Result = [ordered]@{
  schema_version = 1
  status = 'passed'
  root = $Root
  restored = 'README.md'
  removed = 'delivery/readability-readme-v4/'
  removed_files = $OwnedFiles
  baseline_sha256 = $ExpectedBaseline
  restored_sha256 = $RestoredHash
  artifact_directory_absent = $true
}
$Json = $Result | ConvertTo-Json -Depth 6
if ($WritePath) {
  $Parent = Split-Path -Parent $WritePath
  if ($Parent -and -not (Test-Path -LiteralPath $Parent)) {
    New-Item -ItemType Directory -Path $Parent -Force | Out-Null
  }
  [System.IO.File]::WriteAllText($WritePath, $Json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}
$Json
exit 0
