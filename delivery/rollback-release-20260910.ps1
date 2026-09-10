param([Parameter(Mandatory=$true)][string]$ExpectedHead, [switch]$Push)
$ErrorActionPreference = 'Stop'
$git = 'C:\Program Files\Git\cmd\git.exe'
if (-not (Test-Path -LiteralPath $git)) { $git = 'git' }
$root = (& $git rev-parse --show-toplevel).Trim()
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath (Join-Path $root 'publication-manifest.json'))) { throw 'Run in the published source-plus-knowledge repository.' }
$head = (& $git rev-parse HEAD).Trim()
if ($head -ne $ExpectedHead) { throw 'HEAD differs from the explicitly selected release commit.' }
if ((& $git status --porcelain)) { throw 'Preserve local changes before rollback.' }
$base = '4ead5dc1a56487c4d70b6d549e01759be075b09c'
& $git merge-base --is-ancestor $base HEAD
if ($LASTEXITCODE -ne 0) { throw 'Release baseline is not an ancestor.' }
if ($Push) {
    $branch = (& $git branch --show-current).Trim()
    if ($branch -notin @('codex/development-knowledge-builder','codex/release-5.4.0-stable-knowledge')) { throw 'Push is restricted to the two published branches.' }
}
& $git revert --no-commit "$base..$head"
if ($LASTEXITCODE -ne 0) { throw 'Revert needs conflict resolution; no push was attempted.' }
$actual = (& $git write-tree).Trim()
$expected = (& $git rev-parse "$base`^{tree}").Trim()
if ($actual -ne $expected) { throw 'Reverted tree differs from the published baseline; inspect staged changes.' }
& $git commit -m 'revert: restore publication before the September 10 release'
if ($LASTEXITCODE -ne 0) { throw 'Rollback commit failed; no push was attempted.' }
if ($Push) {
    & $git push github "HEAD:refs/heads/$branch"
    if ($LASTEXITCODE -ne 0) { throw 'Local rollback committed; remote push needs attention.' }
}
Write-Output 'Publication restored by a new commit; public history was retained.'
