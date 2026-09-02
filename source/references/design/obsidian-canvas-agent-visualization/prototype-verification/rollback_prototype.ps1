param(
    [string]$SourceRepo = 'E:\knowledge_builder\self-workspace\source',
    [string]$Worktree = 'E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-prototype',
    [string]$Branch = 'codex/obsidian-canvas-visualization-prototype',
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$Git = 'C:\Program Files\Git\cmd\git.exe'
$steps = @(
    @('-C', $SourceRepo, 'worktree', 'remove', '--force', $Worktree),
    @('-C', $SourceRepo, 'branch', '-D', $Branch)
)

if ($WhatIf) {
    [ordered]@{
        schema_version = 1
        status = 'verified-dry-run'
        git = $Git
        source_repo = $SourceRepo
        worktree = $Worktree
        branch = $Branch
        step_count = $steps.Count
    } | ConvertTo-Json -Compress
    exit 0
}

foreach ($arguments in $steps) {
    & $Git @arguments
    if ($LASTEXITCODE -ne 0) {
        throw "git rollback step failed with exit ${LASTEXITCODE}: $($arguments -join ' ')"
    }
}
