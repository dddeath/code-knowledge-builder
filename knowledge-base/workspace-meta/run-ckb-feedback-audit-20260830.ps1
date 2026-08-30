$ErrorActionPreference = 'Stop'
$python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe'
$ckb = 'C:\Users\19739\.codex\skills\code-knowledge-builder\scripts\ckb.py'
$outFile = 'E:\knowledge_builder\self-workspace\knowledge-base\workspace-meta\ckb-feedback-audit-20260830.stdout.txt'
$errFile = 'E:\knowledge_builder\self-workspace\knowledge-base\workspace-meta\ckb-feedback-audit-20260830.stderr.txt'
$p = Start-Process -FilePath $python -ArgumentList @(('"'+$ckb+'"'),'feedback','audit','--out','E:\knowledge_builder\self-workspace\knowledge-base') -NoNewWindow -Wait -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
if (Test-Path $outFile) { Get-Content -Raw -Encoding UTF8 $outFile }
if (Test-Path $errFile) { $e=Get-Content -Raw -Encoding UTF8 $errFile; if($e){[Console]::Error.Write($e)} }
Write-Output ('CKB_EXIT=' + $p.ExitCode)
exit $p.ExitCode
