param(
  [string]$Remote = 'origin',
  [string]$Branch = 'codex/release-5.4.0-stable-knowledge'
)

$ErrorActionPreference = 'Stop'
git fetch $Remote $Branch
git switch $Branch
$releaseCommit = git log --merges --first-parent --format='%H' --grep='release: publish CKB 5.4.0 stable knowledge' -n 1
if (-not $releaseCommit) {
  throw '未找到 CKB 5.4.0 发布合并提交。'
}
git revert -m 1 --no-edit $releaseCommit
git push $Remote "HEAD:refs/heads/$Branch"
if ($LASTEXITCODE -ne 0) {
  throw '远端回滚提交推送失败。'
}
