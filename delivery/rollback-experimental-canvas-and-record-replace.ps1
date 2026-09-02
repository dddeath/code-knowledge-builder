param(
  [string]$Remote = 'github',
  [string]$Branch = 'codex/release-5.4.0-stable-knowledge',
  [string]$Commit = ''
)

$ErrorActionPreference = 'Stop'
git fetch $Remote $Branch
if ($LASTEXITCODE -ne 0) { throw '获取远端发布分支失败。' }
git switch $Branch
if ($LASTEXITCODE -ne 0) { throw '切换到发布分支失败。' }
if (-not $Commit) {
  $Commit = git log --first-parent --format='%H' --grep='release: publish record replacement and experimental canvas' -n 1
}
if (-not $Commit) { throw '未找到 record replacement 与 experimental Canvas 发布提交。' }
git merge-base --is-ancestor $Commit HEAD
if ($LASTEXITCODE -ne 0) { throw '目标提交不是当前发布分支祖先。' }
git revert --no-edit $Commit
if ($LASTEXITCODE -ne 0) { throw '创建发布回滚提交失败。' }
git push $Remote "HEAD:refs/heads/$Branch"
if ($LASTEXITCODE -ne 0) { throw '远端回滚提交推送失败。' }
