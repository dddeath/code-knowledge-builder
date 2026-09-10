[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Repository,
    [switch]$Apply
)

$ErrorActionPreference = "Stop"
$Baseline = "fcad08af3dac7ecf341f2833c1bfc8f352131a3b"
$OwnedPaths = @(
    "scripts/ckb_core/reference_pdf.py",
    "tests/pdf_fixture_factory.py",
    "tests/test_reference_pdf.py",
    "tests/test_reference_pdf_effect_benchmark.py",
    "tests/test_reference_pdf_ocr_fidelity_benchmark.py",
    "tests/benchmark_reference_pdf_ocr_fidelity.py",
    "tests/generate_reference_pdf_ocr_fixtures.py",
    "tests/real_ocr_adapter.py",
    "tests/fixtures/reference-pdf-ocr",
    "tests/fixtures/research-gap-enhancement-effects/pdf-ocr-code-table-fidelity-v1.json",
    "references/research-gap-enhancement-effects/pdf-ocr-code-table-fidelity-v1"
)

$root = (Resolve-Path -LiteralPath $Repository).Path
$gitRoot = (& git -C $root rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or (Resolve-Path -LiteralPath $gitRoot).Path -ne $root) {
    throw "Repository must be the exact Git worktree root: $root"
}
& git -C $root merge-base --is-ancestor $Baseline HEAD
if ($LASTEXITCODE -ne 0) {
    throw "Baseline is not an ancestor of HEAD: $Baseline"
}
$dirty = & git -C $root status --porcelain
if ($LASTEXITCODE -ne 0 -or $dirty) {
    throw "Rollback requires a clean worktree"
}
$changed = @(& git -C $root diff --name-only "$Baseline..HEAD" -- @OwnedPaths)
if ($LASTEXITCODE -ne 0) {
    throw "Could not enumerate task-owned changes"
}
if (-not $Apply) {
    [ordered]@{ status = "verified-plan"; baseline = $Baseline; changed_paths = $changed } |
        ConvertTo-Json -Compress
    exit 0
}
foreach ($path in $OwnedPaths) {
    $candidate = [IO.Path]::GetFullPath((Join-Path $root $path.Replace('/', [IO.Path]::DirectorySeparatorChar)))
    if (-not ($candidate -eq $root -or $candidate.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase))) {
        throw "Rollback path escapes repository: $path"
    }
    & git -C $root cat-file -e "${Baseline}:$path" 2>$null
    if ($LASTEXITCODE -eq 0) {
        & git -C $root restore --source $Baseline --staged --worktree -- $path
        if ($LASTEXITCODE -ne 0) { throw "Could not restore baseline path: $path" }
    } else {
        & git -C $root rm -r --ignore-unmatch -- $path | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "Could not remove task-owned path: $path" }
    }
}
& git -C $root diff --quiet $Baseline --
if ($LASTEXITCODE -ne 0) {
    throw "Rollback tree does not match baseline"
}
& git -C $root commit -m "revert: rollback real OCR fidelity task" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Rollback commit failed"
}
& git -C $root diff --quiet $Baseline HEAD --
if ($LASTEXITCODE -ne 0) {
    throw "Committed rollback tree does not match baseline"
}
[ordered]@{
    status = "rolled-back"
    baseline = $Baseline
    rollback_commit = (& git -C $root rev-parse HEAD).Trim()
    tree_matches_baseline = $true
} | ConvertTo-Json -Compress