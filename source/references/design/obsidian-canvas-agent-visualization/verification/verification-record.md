# CKB Canvas 设计验证记录

验证对象：`references/design/obsidian-canvas-agent-visualization/`
Git 基线：`62b15376e8de899a2eaeda1d10bcc62bd1b3d2a8`
验证日期：2026-09-02
验证范围：设计、schema、fixtures、benchmark 合同、patch replay、设计 rollback；不含产品实现或人工 Obsidian 效果 benchmark

## 1. CKB 紧凑检索

命令：

```bash
/mnt/c/Users/19739/.codex/cache/code-knowledge-builder/runtime/win-x64/win-x64-2.0.0/python/python.exe \
  'C:\Users\19739\.codex\skills\code-knowledge-builder\scripts\ckb.py' brief \
  --out 'E:\knowledge_builder\self-workspace\knowledge-base' \
  'ckb brief command CLI parser Agent pack schema local opener renderer Skill package distribution validator rollback atomic promotion path boundary' \
  --budget 2400 --max-pages 10 --profile fast
```

字面结果摘要：

```text
status=passed
open_feedback=0
pack=E:\knowledge_builder\self-workspace\knowledge-base\machine\agent-packs\pack-20260901-181734-756142-01.md
record=E:\knowledge_builder\self-workspace\knowledge-base\machine\agent-packs\pack-20260901-181734-756142-01.json
grep_fallback_required=false
exit=0
```

pack 指向的窄读入口包括 `compact_agent_brief`、`SourceLinkRenderer.absolute_path`、`_write_bytes_atomic`、`package_release.validate_core_boundary` 和 machine pack 入口。完整 record 实测 `schema_version=3`；`OUTPUT/state.json` 与 machine SQLite meta 的 snapshot commit 均为 `150a1ce8ea3fca0f7ce2f56c731d42a9973ee0e3`。这支持设计把 snapshot guard 放在 state/SQLite，而不是假设 record 自带 commit。

## 2. JSON、schema、fixture、链接与 benchmark

命令：

```bash
python3 references/design/obsidian-canvas-agent-visualization/verification/validate_design.py
```

字面输出：

```text
JSON_PARSE=passed files=36
SCHEMA_SHAPE=passed schemas=9 draft=2020-12 external_refs=0
FIXTURE_VALIDATION=passed instances=25
NEGATIVE_UNKNOWN_FIELDS=passed cases=9
FAILURE_REASON_COVERAGE=passed reasons=17
HASH_CONTRACT=passed request=7c30552fc5d50eb96d14b779aa48dd2605cf089a578cc6142743bf1c063ff7d0 canvas=3a444a1ef1f9d6c24189c67f775ffd98e40b8a68dafe134b1a11d5dfb5b29c70 rollback=4789297ced92e0daa03e1fc89177b039e6ccbb9a1c37ec2d7c77265ea3b33585
CANVAS_STRUCTURE=passed nodes=4 edges=3 dangling=0 canonical_files=5
BENCHMARK_CONTRACT=passed tasks=12 assignments=4 per_condition_coverage=12 evidence_equal=true
MARKDOWN_LINKS=passed links=25
DESIGN_VALIDATION=passed
```

退出状态：`0`。

验证器只实现本设计使用的确定性 schema 子集，用于证明 schema/fixture 互相一致；原型仍需按 `contracts-and-fixtures.md` 实现完整 schema 1 显式字段与语义校验。

## 3. Canvas rollback manifest 三探针

命令：

```bash
python3 references/design/obsidian-canvas-agent-visualization/verification/rollback_probe.py
```

字面输出：

```text
ROLLBACK_ABSENT=passed roles=3 final=absent
ROLLBACK_PRESENT=passed roles=3 byte_identical=true
ROLLBACK_DRIFT=passed refused=true manual_sha256=479183a7144bdafee28f3e3fbb7950ecd286a0154ef3781f9dee9bc2682034d5
ROLLBACK_PROBES=passed count=3/3
```

退出状态：`0`。

该探针验证 manifest 的三角色恢复语义；它不是 Canvas 生成器实现。原型任务仍需 fault injection 覆盖 flush、fsync、replace、reopen 和 delete。

## 4. Patch 生成与 replay

patch：`verification/design-delivery.patch`
SHA-256：`a3244fe2f1c051aaa94d3dac0b17b3864506c2f8a770c4d3d5bf594e73413802`
实质目标：40 个文件；patch 不递归包含 `verification/`。

生成命令：

```bash
'/mnt/c/Program Files/Git/cmd/git.exe' \
  -C 'E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-design' \
  diff --binary 62b15376e8de899a2eaeda1d10bcc62bd1b3d2a8 -- \
  'references/design/obsidian-canvas-agent-visualization' \
  ':(exclude)references/design/obsidian-canvas-agent-visualization/verification/**' \
  > references/design/obsidian-canvas-agent-visualization/verification/design-delivery.patch
```

Replay 在 detached baseline worktree 中显式设置 `core.autocrlf=false` 后执行 `git apply --check` 和 `git apply`，再逐文件比较 SHA-256。字面输出：

```text
PATCH_REPLAY=passed targets=40 byte_identical=true
PATCH_REPLAY_EXIT=0
```

探针 worktree 已用 Windows Git `worktree remove --force` 删除。

## 5. 设计分支回滚脚本

脚本：`verification/rollback_design.ps1`。它要求干净 worktree、可选 expected HEAD、且从基线到 HEAD 的所有变化都位于 owned 目录；随后删除 owned 目录，并验证暂存索引与基线一致。脚本使用 `.NET ProcessStartInfo` 调用用户指定 Windows Git，不依赖 PowerShell 5.1 native pipeline。

隔离探针输入：baseline detached worktree + `design-delivery.patch` + rollback 脚本，提交为一次临时 probe commit。字面输出：

```text
ROLLBACK_READY=passed
BASELINE=62b15376e8de899a2eaeda1d10bcc62bd1b3d2a8
OWNED_PATH=references/design/obsidian-canvas-agent-visualization
STAGED_DELETIONS=41
NEXT=review staged deletion, then commit the rollback
POWERSHELL_EXIT=0
ROLLBACK_SCRIPT_EXIT=0
INDEX_MATCHES_BASELINE=true
```

临时 probe commit 与 worktree 都未合并；worktree 已删除。正式使用时把本设计最终 HEAD 作为 `-ExpectedHead`。

## 6. Git 范围与 whitespace 门

命令：

```bash
'/mnt/c/Program Files/Git/cmd/git.exe' \
  -C 'E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-design' \
  diff --check 62b15376e8de899a2eaeda1d10bcc62bd1b3d2a8 -- \
  'references/design/obsidian-canvas-agent-visualization'
```

字面输出：空。退出状态：`0`。

范围断言：从基线到设计 HEAD 的每个 changed path 都以 `references/design/obsidian-canvas-agent-visualization/` 开头；最终 Git 状态在提交后另行重开核对。

## 7. 验证边界

已确认：设计 schema/fixture 自洽、17 个失败原因闭合、12 个 benchmark 任务和分配闭合、patch 可 replay、设计 rollback 可恢复基线索引。

尚未执行：Canvas 产品代码、Obsidian custom URI 行为、file node/subpath 行为、人工导航 session、效果判定、主 CLI/companion/MCP/发行接入。
