param([string[]]$Tests = @())
$ErrorActionPreference = 'Stop'
$Root = 'E:\knowledge_builder\self-workspace\worktrees\recruitment-source-migration-integrity'
$Python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe'
$Git = 'C:\Program Files\Git\cmd\git.exe'
$Evidence = 'E:\knowledge_builder\artifacts\verification\20260905-recruitment-source-migration-integrity'
$Entry = Join-Path $PSScriptRoot 'windows-verify.py'
$Arguments = @('-X', 'utf8', $Entry, $Root, $Evidence, $Git)
foreach ($Test in $Tests) {
    $Arguments += @('--test', $Test)
}
& $Python @Arguments
exit $LASTEXITCODE
