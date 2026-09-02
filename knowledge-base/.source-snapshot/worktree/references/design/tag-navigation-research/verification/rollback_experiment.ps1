[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Repo = 'E:\knowledge_builder\self-workspace\worktrees\tag-navigation-research',
    [string]$ExpectedHead = ''
)

$ErrorActionPreference = 'Stop'
$Git = 'C:\Program Files\Git\cmd\git.exe'
$Baseline = '19152b227ccf687e7e4d89337d421c22a4e1a75f'
$ExpectedBranch = 'codex/tag-navigation-research'
$AllowedPatterns = @(
    '^prototypes/ckb-tag-navigation/',
    '^tests/test_ckb_tag_navigation_[^/]+\.py$',
    '^tests/fixtures/tag-navigation/',
    '^references/design/tag-navigation-research/'
)

function Invoke-Git {
    param([string[]]$Arguments)
    $StartInfo = New-Object System.Diagnostics.ProcessStartInfo
    $StartInfo.FileName = $Git
    $StartInfo.WorkingDirectory = $Repo
    $StartInfo.UseShellExecute = $false
    $StartInfo.CreateNoWindow = $true
    $StartInfo.RedirectStandardOutput = $true
    $StartInfo.RedirectStandardError = $true
    $StartInfo.Arguments = (($Arguments | ForEach-Object { '"' + ($_.Replace('"', '\"')) + '"' }) -join ' ')
    $Process = New-Object System.Diagnostics.Process
    $Process.StartInfo = $StartInfo
    [void]$Process.Start()
    $StdOut = $Process.StandardOutput.ReadToEnd()
    $StdErr = $Process.StandardError.ReadToEnd()
    $Process.WaitForExit()
    [pscustomobject]@{
        ExitCode = $Process.ExitCode
        StdOut = $StdOut
        StdErr = $StdErr
    }
}

if (-not (Test-Path -LiteralPath $Git -PathType Leaf)) {
    throw "Windows Git 不存在：$Git"
}
if (-not (Test-Path -LiteralPath $Repo -PathType Container)) {
    throw "仓库目录不存在：$Repo"
}

Push-Location -LiteralPath $Repo
try {
    $Result = Invoke-Git @('rev-parse', '--show-toplevel')
    $Top = $Result.StdOut.Trim()
    if ($Result.ExitCode -ne 0 -or $Top -ne ($Repo -replace '\\', '/')) {
        throw "目标不是预期 worktree：$Top"
    }
    $Result = Invoke-Git @('branch', '--show-current')
    $Branch = $Result.StdOut.Trim()
    if ($Result.ExitCode -ne 0 -or $Branch -ne $ExpectedBranch) {
        throw "当前分支不是 $ExpectedBranch：$Branch"
    }
    $Result = Invoke-Git @('rev-parse', 'HEAD')
    $Head = $Result.StdOut.Trim()
    if ($Result.ExitCode -ne 0) {
        throw '读取 HEAD 失败'
    }
    if ($ExpectedHead -and $Head -ne $ExpectedHead) {
        throw "HEAD 与 ExpectedHead 不一致：$Head"
    }
    $Result = Invoke-Git @('merge-base', '--is-ancestor', $Baseline, $Head)
    if ($Result.ExitCode -ne 0) {
        throw "基线不是当前 HEAD 的祖先：$Baseline"
    }
    $Result = Invoke-Git @('status', '--porcelain')
    $Dirty = @($Result.StdOut -split "`r?`n" | Where-Object { $_ })
    if ($Result.ExitCode -ne 0 -or $Dirty.Count -ne 0) {
        throw "worktree 不干净：$($Dirty -join ', ')"
    }
    $Result = Invoke-Git @('diff', '--name-only', "$Baseline..$Head")
    $Changed = @($Result.StdOut -split "`r?`n" | Where-Object { $_ })
    if ($Result.ExitCode -ne 0) {
        throw '读取分支变更路径失败'
    }
    $Unexpected = @(
        $Changed | Where-Object {
            $Path = $_
            -not ($AllowedPatterns | Where-Object { $Path -match $_ })
        }
    )
    if ($Unexpected.Count -ne 0) {
        throw "分支含实验范围外路径：$($Unexpected -join ', ')"
    }
    if ($PSCmdlet.ShouldProcess($Repo, "把 $ExpectedBranch 从 $Head 回退到 $Baseline")) {
        $Result = Invoke-Git @('reset', '--hard', $Baseline)
        if ($Result.ExitCode -ne 0) {
            throw 'git reset --hard 失败'
        }
        $Result = Invoke-Git @('rev-parse', 'HEAD')
        $RestoredHead = $Result.StdOut.Trim()
        $Result = Invoke-Git @('status', '--porcelain')
        $RestoredDirty = @($Result.StdOut -split "`r?`n" | Where-Object { $_ })
        if ($RestoredHead -ne $Baseline -or $RestoredDirty.Count -ne 0) {
            throw "回滚后核验失败：HEAD=$RestoredHead dirty=$($RestoredDirty -join ', ')"
        }
        [ordered]@{
            status = 'passed'
            branch = $ExpectedBranch
            previous_head = $Head
            restored_head = $RestoredHead
            changed_path_count = $Changed.Count
        } | ConvertTo-Json -Compress
    }
}
finally {
    Pop-Location
}
