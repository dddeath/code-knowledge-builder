param(
    [string]$Repository = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
)

$ErrorActionPreference = 'Stop'
$ImplementationCommit = 'cb3996c'
$EvidenceCommit = '5ae4c81'
$RelativeScript = 'references/benchmarks/qmd-fixed-three-arm/rollback.ps1'

Push-Location -LiteralPath $Repository
try {
    if ((git status --porcelain).Count -ne 0) {
        throw 'Rollback requires a clean worktree.'
    }
    $RollbackCommit = (git log -1 --format=%H -- $RelativeScript).Trim()
    if (-not $RollbackCommit) {
        throw 'Rollback script commit is not present in this history.'
    }
    foreach ($Commit in @($RollbackCommit, $EvidenceCommit, $ImplementationCommit)) {
        git merge-base --is-ancestor $Commit HEAD
        if ($LASTEXITCODE -ne 0) {
            throw "Required commit is not an ancestor of HEAD: $Commit"
        }
        git revert --no-edit $Commit
        if ($LASTEXITCODE -ne 0) {
            throw "git revert failed for $Commit"
        }
    }
    git diff --exit-code 'fcad08af3dac7ecf341f2833c1bfc8f352131a3b' HEAD
    if ($LASTEXITCODE -ne 0) {
        throw 'Rollback tree differs from the frozen baseline.'
    }
    Write-Output 'ROLLBACK_VERIFIED=tree-equals-fcad08af3dac7ecf341f2833c1bfc8f352131a3b'
}
finally {
    Pop-Location
}
