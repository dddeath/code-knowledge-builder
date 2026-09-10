param(
    [string]$Run = "prototypes\ckb-tag-navigation\.real-vault-run"
)

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$Prototype = (Resolve-Path (Join-Path $Repo "prototypes\ckb-tag-navigation")).Path
$Python = "C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe"
$Cli = Join-Path $Prototype "scripts\ckb_tag_navigation.py"
$RunPath = [System.IO.Path]::GetFullPath((Join-Path $Repo $Run))
$Relative = [System.IO.Path]::GetRelativePath($Prototype, $RunPath)
if ($Relative.StartsWith("..") -or [System.IO.Path]::IsPathRooted($Relative)) {
    throw "Run 必须位于 $Prototype 内"
}

& $Python -X utf8 $Cli study-rollback `
    --manifest (Join-Path $RunPath "study.rollback.json") `
    --workspace-root $Prototype
exit $LASTEXITCODE
