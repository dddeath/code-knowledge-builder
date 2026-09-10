[CmdletBinding()]
param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Base = "f7d2181fd7cbf619d6337abfc17a85124f2c302f"
$Repository = (& git rev-parse --show-toplevel).Trim()
if (-not $Repository) {
    throw "Git repository root was not found."
}

$Paths = @(
    "scripts/ckb.py",
    "scripts/ckb_core/reference_inputs.py",
    "scripts/ckb_core/reference_documents.py",
    "tests/test_reference_pdf.py",
    "tests/test_reference_web.py",
    "references/research-gap-enhancement-effects/web-static-snapshot-reference-ingest-v1"
)

& git cat-file -e "$Base^{commit}"
if ($LASTEXITCODE -ne 0) {
    throw "Rollback baseline commit is unavailable: $Base"
}

if (-not $Apply) {
    [ordered]@{
        status = "ready"
        apply = $false
        repository = $Repository
        baseline = $Base
        paths = $Paths
        command = "rollback.ps1 -Apply"
    } | ConvertTo-Json -Depth 4
    exit 0
}

$Dirty = @(& git status --porcelain -- @Paths)
if ($LASTEXITCODE -ne 0) {
    throw "Unable to inspect rollback paths."
}
if ($Dirty.Count -gt 0) {
    throw "Rollback paths contain uncommitted changes; commit or discard them before applying rollback."
}

& git restore --source=$Base --staged --worktree -- @Paths
if ($LASTEXITCODE -ne 0) {
    throw "git restore failed."
}
& git diff --cached --check
if ($LASTEXITCODE -ne 0) {
    throw "Rollback produced an invalid staged diff."
}
$Remaining = @(& git diff --name-only $Base -- @Paths)
if ($LASTEXITCODE -ne 0 -or $Remaining.Count -gt 0) {
    throw "Rollback paths do not match the baseline."
}

[ordered]@{
    status = "reverted-to-baseline"
    apply = $true
    repository = $Repository
    baseline = $Base
    staged_paths = @(& git diff --cached --name-only -- @Paths)
} | ConvertTo-Json -Depth 4
