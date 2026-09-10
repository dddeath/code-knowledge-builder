param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$baseCommit = "fcad08af3dac7ecf341f2833c1bfc8f352131a3b"
$allowedExact = @(
    "scripts/ckb_core/keyword_fallback.py",
    "tests/benchmark_keyword_real_provider.py",
    "tests/fixtures/keyword_provider.py",
    "tests/fixtures/keyword_real_provider_12case.json",
    "tests/test_keyword_fallback.py",
    "tests/test_keyword_real_provider_benchmark.py"
)
$allowedPrefix = "references/research-gap-enhancement-effects/llm-keyword-real-provider-12case-v1/"

$root = (& git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not $root) {
    throw "rollback must run inside the task Git repository"
}
Set-Location -LiteralPath $root

$dirty = @(& git status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -ne 0) {
    throw "rollback requires a clean worktree"
}

& git merge-base --is-ancestor $baseCommit HEAD
if ($LASTEXITCODE -ne 0) {
    throw "baseline commit is not an ancestor of HEAD"
}

$paths = @(& git diff --name-only "$baseCommit..HEAD")
if ($LASTEXITCODE -ne 0 -or $paths.Count -eq 0) {
    throw "rollback range has no task changes"
}
$unexpected = @(
    $paths | Where-Object {
        $_ -notin $allowedExact -and -not $_.StartsWith($allowedPrefix, [System.StringComparison]::Ordinal)
    }
)
if ($unexpected.Count -ne 0) {
    throw "rollback range contains paths outside the task boundary: $($unexpected -join ', ')"
}

Write-Output "rollback-check=passed base=$baseCommit head=$((& git rev-parse HEAD).Trim()) paths=$($paths.Count)"
if (-not $Apply) {
    exit 0
}

& git revert --no-commit "$baseCommit..HEAD"
if ($LASTEXITCODE -ne 0) {
    & git revert --abort 2>$null
    throw "git revert failed"
}
& git diff --cached --quiet $baseCommit --
if ($LASTEXITCODE -ne 0) {
    & git revert --abort 2>$null
    throw "rollback index differs from the baseline tree"
}
Write-Output "rollback-apply=passed staged-tree=$baseCommit"
