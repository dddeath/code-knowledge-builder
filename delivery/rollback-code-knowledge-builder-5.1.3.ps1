[CmdletBinding()]
param(
    [string]$ProbeRoot
)
$ErrorActionPreference = 'Stop'
if ($ProbeRoot) {
    $install = Join-Path $ProbeRoot 'code-knowledge-builder'
    $backup = Join-Path $ProbeRoot 'code-knowledge-builder-5.1.2-before-5.1.3'
    $quarantine = Join-Path $ProbeRoot 'code-knowledge-builder-5.1.3-rollback-quarantine'
} else {
    $install = 'C:\Users\19739\.codex\skills\code-knowledge-builder'
    $backup = 'C:\Users\19739\.codex\skills\.backups\code-knowledge-builder-5.1.2-before-5.1.3'
    $quarantine = 'C:\Users\19739\.codex\skills\.backups\code-knowledge-builder-5.1.3-rollback-quarantine'
}
if (-not (Test-Path -LiteralPath $install -PathType Container)) { throw "Installed Skill is missing: $install" }
if (-not (Test-Path -LiteralPath $backup -PathType Container)) { throw "Rollback backup is missing: $backup" }
if (Test-Path -LiteralPath $quarantine) { throw "Rollback quarantine already exists: $quarantine" }
Move-Item -LiteralPath $install -Destination $quarantine
try {
    Move-Item -LiteralPath $backup -Destination $install
} catch {
    Move-Item -LiteralPath $quarantine -Destination $install
    throw
}
[ordered]@{
    schema_version = 1
    status = 'passed'
    restored = $install
    restored_from = $backup
    displaced_new_install = $quarantine
    private_runtime = 'unchanged-preexisting'
    probe = [bool]$ProbeRoot
} | ConvertTo-Json -Depth 4
