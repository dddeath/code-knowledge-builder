param(
    [string]$Current = 'C:\Users\19739\.codex\skills\code-knowledge-builder',
    [string]$Backup = 'C:\Users\19739\.codex\skills\.backups\code-knowledge-builder-5.1.1-before-5.1.2',
    [string]$Displaced = 'C:\Users\19739\.codex\skills\.backups\code-knowledge-builder-5.1.2-rolled-back',
    [string]$PluginNew = 'C:\Users\19739\.codex\plugins\cache\personal\code-knowledge-builder-sync\1.2.0',
    [string]$Registry = 'C:\Users\19739\.ckb\automation-registry.json',
    [string]$RegistryBackup = 'E:\knowledge_builder\self-workspace\backups\automation-registry.5.1.1-before-5.1.2.json',
    [string]$ExpectedVersion = '5.1.1',
    [switch]$SkipIntegrationState
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Backup -PathType Container)) {
    throw "Rollback backup is absent: $Backup"
}
if (Test-Path -LiteralPath $Displaced) {
    throw "Rollback displaced target already exists: $Displaced"
}
if (Test-Path -LiteralPath $Current) {
    Move-Item -LiteralPath $Current -Destination $Displaced
}
Move-Item -LiteralPath $Backup -Destination $Current

$skill = Join-Path $Current 'SKILL.md'
if (-not (Test-Path -LiteralPath $skill -PathType Leaf)) {
    throw "Restored Skill entrypoint is absent: $skill"
}
$text = Get-Content -LiteralPath $skill -Raw -Encoding UTF8
if ($text -notmatch ('version:\s*["'']?' + [regex]::Escape($ExpectedVersion) + '["'']?')) {
    throw "Restored Skill version does not match $ExpectedVersion"
}

if (-not $SkipIntegrationState) {
    if (Test-Path -LiteralPath $PluginNew) {
        Remove-Item -LiteralPath $PluginNew -Recurse -Force
    }
    if (-not (Test-Path -LiteralPath $RegistryBackup -PathType Leaf)) {
        throw "Registry rollback source is absent: $RegistryBackup"
    }
    Copy-Item -LiteralPath $RegistryBackup -Destination $Registry -Force
}

[pscustomobject]@{
    status = 'passed'
    restored = $Current
    restored_version = $ExpectedVersion
    displaced = $Displaced
    integration_state_restored = -not $SkipIntegrationState
} | ConvertTo-Json -Depth 4
