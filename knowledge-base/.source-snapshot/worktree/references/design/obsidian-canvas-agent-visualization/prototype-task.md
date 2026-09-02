# 原型任务交接：独立 CKB Canvas Skill

本文件是可直接派发给独立 prototype worktree 的完整任务合同。派发管理 Agent 必须把本设计分支最终 HEAD 作为精确 baseline 传入，不以 integration branch 的移动 HEAD 代替。

## 1. 目标

实现一个不接线主 CLI、companion 或 MCP 的独立实验 Skill：从 schema 1 `canvas-request.json` 生成确定性 JSON Canvas 1.0、validation manifest 和 rollback manifest，执行严格 staging/promotion/replace/rollback，并提供冻结 Markdown 对照 runner。

原型只证明合同可实现和对照可执行。它不决定产品 Canvas 路径归属，不写活动稳定知识库，不部署 Obsidian 插件，不发布 lite/full，不推送远端。

## 2. 分支与 worktree 输入

```text
source branch: codex/obsidian-canvas-visualization-design
source baseline: 管理 Agent 交接中给出的最终 40 位 HEAD
prototype branch: codex/obsidian-canvas-visualization-prototype
prototype worktree: E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-prototype
integration branch: codex/reference-ingest-v1
```

Git 统一使用：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' -C 'E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-prototype' ...
```

## 3. 规范输入

实现前逐项读取，不重新设计：

```text
references/design/obsidian-canvas-agent-visualization/technical-design.md
references/design/obsidian-canvas-agent-visualization/contracts-and-fixtures.md
references/design/obsidian-canvas-agent-visualization/benchmark-contract.md
references/design/obsidian-canvas-agent-visualization/schemas/*.json
references/design/obsidian-canvas-agent-visualization/fixtures/**
```

当前真实复用入口只读引用：

```text
scripts/ckb_core/source_links.py::SourceLinkRenderer
scripts/ckb_core/source_links.py::audit_source_uri
scripts/ckb_core/common.py::sha256_file
```

不要导入或调用 `agent_protocol_batch.py` 的私有写入函数；在原型模块中实现同合同的受控写入，避免把批处理内部 API 变成公共依赖。

## 4. 允许修改路径

```text
prototypes/ckb-canvas-skill/**
tests/fixtures/obsidian-canvas-agent-visualization/**
tests/test_ckb_canvas_contracts.py
tests/test_ckb_canvas_graph.py
tests/test_ckb_canvas_transaction.py
tests/test_ckb_canvas_rollback.py
tests/test_ckb_canvas_paths.py
tests/test_ckb_canvas_determinism.py
tests/test_ckb_canvas_benchmark_contract.py
tests/benchmark_obsidian_canvas_navigation.py
references/design/obsidian-canvas-agent-visualization/prototype-verification/**
```

原型将本设计的九个 schema byte-identical 复制到 `prototypes/ckb-canvas-skill/schemas/`，测试逐文件核对 SHA-256。设计目录只允许新增 `prototype-verification/` 的实际记录，不修改已经冻结的 schema、预算、任务或算法。

## 5. 禁止修改路径

```text
scripts/ckb.py
scripts/ckb_core/**
scripts/package_release.py
SKILL.md
agents/**
assets/**
plugins/**
references/research/obsidian-canvas-agent-visualization/**
references/design/obsidian-canvas-agent-visualization/*.md
references/design/obsidian-canvas-agent-visualization/schemas/**
references/design/obsidian-canvas-agent-visualization/fixtures/**
E:\knowledge_builder\self-workspace\knowledge-base/**
```

原型不能新增 SQL 查询、glob 扫描、模型关系、网络请求、MCP server、companion command、主 CLI parser 分支或发布包能力字段。

## 6. 必须实现的模块

严格按 [`technical-design.md` 第 3 节](technical-design.md#3-建议新增模块与公开函数)：

```text
contracts.py: schema 1 显式字段校验、成功/失败结果
freeze.py: request/path/hash/record/snapshot/evidence 闭合
graph.py: 选择、稳定 ID、布局、canonical bytes、Canvas 验证
transaction.py: 三角色 baseline/staging/promotion/reopen/rollback
commands.py: generate/validate/rollback 编排和 stdout JSON
benchmark.py: block runner、judge、summary
scripts/ckb_canvas.py: argparse 薄入口
SKILL.md: 只编排，不生成图或直接写文件
```

运行时不得依赖本机未锁定的 `jsonschema`、Node 或 Obsidian API。`contracts.py` 对 schema 1 实现显式确定性校验；测试同时 JSON 解析设计 schema、验证全部正反 fixture，并证明每一层未知字段失败。

## 7. 固定命令合同

```powershell
& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py validate --request REQUEST.json
& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py generate --request REQUEST.json
& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py rollback --manifest TARGET.canvas.rollback.json --expected-sha256 MANIFEST_SHA256
& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py benchmark --run BENCHMARK-RUN.json --session SESSION_ID
& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py summarize --run BENCHMARK-RUN.json --sessions SESSION-DIR --write SUMMARY.json
```

stdout 恰好一个 schema 化 JSON 对象；日志写 stderr。退出状态只用 `0,2,5,6,7`，reason/phase/目标状态与设计一致。不能提供 `--force`、`--skip-validation`、`--allow-outside-root`、`--max-nodes` 或 `--overwrite`。

## 8. Fixture 实例化

在 `tests/fixtures/obsidian-canvas-agent-visualization/` 提交：

```text
README.md                         # runtime builder 合同
template/                         # 无绝对临时根的最小 UTF-8 输入
expected/                         # canonical Canvas/result/manifest 字节
failure-results/                  # 17 个 byte-identical 设计 failure fixture
benchmark/                        # runner/session/summary schema fixture
```

测试运行时在 `%TEMP%\ckb-canvas-fixtures\CASE_ID` 创建最小 `state.json`、SQLite meta、pack/record、人类投影和 detached source。symlink/junction 与 250–259 字符路径只在 runtime 创建，不把不可移植链接提交进 Git。

## 9. Commit 批次

按以下顺序独立提交，不 squash：

1. `feat(prototype): add strict canvas contracts and input freezer`
2. `feat(prototype): add deterministic canvas graph and transaction`
3. `test(prototype): add canvas fixtures and rollback probes`
4. `test(benchmark): add frozen markdown canvas runner`

每个 commit 只包含其职责；verification 记录跟随对应 test commit 或最后单独 `docs(prototype): record canvas verification`，不得混入产品目录。

## 10. 自动验收命令

固定 Windows Python：

```powershell
$Python = 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.0.0\python\python.exe'
$Repo = 'E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-prototype'

& $Python -m unittest `
  tests.test_ckb_canvas_contracts `
  tests.test_ckb_canvas_graph `
  tests.test_ckb_canvas_transaction `
  tests.test_ckb_canvas_rollback `
  tests.test_ckb_canvas_paths `
  tests.test_ckb_canvas_determinism `
  tests.test_ckb_canvas_benchmark_contract

& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py validate `
  --request tests\fixtures\obsidian-canvas-agent-visualization\runtime\success\request.json

& 'C:\Program Files\Git\cmd\git.exe' -C $Repo diff --check
& 'C:\Program Files\Git\cmd\git.exe' -C $Repo status --short
```

必须把字面 stdout、stderr 摘要和每条退出状态写到：

```text
references/design/obsidian-canvas-agent-visualization/prototype-verification/verification-record.json
```

## 11. 自动验收断言

1. 九个 schema JSON 可解析，schema 与原型副本 byte-identical；
2. success request/result/Canvas/validation/rollback 全部通过显式 validator；
3. 17 个 failure result 全部通过 failure validator，reason 集合无缺失、无额外项；
4. 每层 request object 增加未知字段均 exit 2；
5. machine record 1、keyword fallback record 和未知 record 字段均拒绝；
6. 12 节点/16 边硬上限、稳定 ID、数组顺序和固定坐标通过；
7. 10 次隔离生成 Canvas 原始 hash 只有 1 种，两个 manifest 规范化 hash 各 1 种；
8. 三条 rollback probe 3/3，present baseline 三角色 byte-identical；
9. 中文路径、长路径、symlink/junction、损坏 JSON、悬空边、并发目标变化分别命中预期 reason/exit/目标状态；
10. 目标 Canvas 在所有 fault 注入后都只有完整 baseline、完整 generated 或外部当前字节；
11. runner input 恰好 12 个唯一 task，四个 assignment 各 6 个唯一 task，两 sequence/condition 合计各覆盖 12 个 task；
12. Markdown/Canvas evidence hash、问题、来源和预算完全相同；
13. diff 只含允许路径，工作树干净。

## 12. 人工 Obsidian benchmark 输入

自动门通过后，复制隔离 `OUTPUT/human` 和生成 Canvas 到 benchmark 根，填写 `OBSIDIAN_VERSION`，冻结 request/run hash，再按 [`benchmark-contract.md`](benchmark-contract.md) 执行。

每个 sequence 至少 2 个独立 session；同一参与者重复时至少相隔 24 小时。每个 session 按 sequence block order 运行，block 内严格使用 JSON `task_order`。原型 Agent 只收集观察，不解释结果；`summarize` 统一计算门。

若 fixed Obsidian 不能打开 editor URI 或 file node 精确行为不一致，立即 `stopped` 并返回设计，不把该轮作为 Canvas 效果差的普通样本。

## 13. 完成输出

向管理 Agent 返回：

1. 分支、精确 baseline、最终 HEAD、干净状态；
2. commit 列表与职责；
3. 模块和命令路径；
4. schema/fixture hash parity；
5. 全部自动验收命令、字面结果与退出状态；
6. 10 次 hash、三条 rollback probe、路径/并发用例结果；
7. benchmark run 的完整路径/hash；
8. 已确认实现结果、尚未运行的人工 benchmark、待用户产品决策；
9. 明确声明未接线主 CLI、未修改 companion/MCP/发布包、未更新活动稳定知识库、未合并、未推送。

## 14. 原型回滚

分支未合并时，删除 prototype worktree 和分支即完整回滚，不触碰 integration：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' -C 'E:\knowledge_builder\self-workspace\source' worktree remove --force 'E:\knowledge_builder\self-workspace\worktrees\obsidian-canvas-visualization-prototype'
& 'C:\Program Files\Git\cmd\git.exe' -C 'E:\knowledge_builder\self-workspace\source' branch -D 'codex/obsidian-canvas-visualization-prototype'
```

若管理 Agent 选择在 integration 中审阅 commit，使用 `git revert` 按新到旧撤销原型 commit；不得 `reset` integration，不运行稳定知识库 rollback，因为本任务禁止写稳定知识库。
