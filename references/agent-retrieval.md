# Agent 确定性检索

在读取大范围源码或执行全仓 grep 前，先使用本页接口。

## 主索引

每种输出格式都生成 `OUTPUT/machine/knowledge.sqlite`。它不是页面缓存，而是 Agent 专用完整知识库，包含全部实体、范围、关系、来源证据、审阅说明、固定快照源码、职责群、人类页映射、Agent 记录和工作树覆盖层。`OUTPUT/agent-index.sqlite` 只保留旧接口兼容能力。

```powershell
& PYTHON scripts\ckb.py reindex --out OUTPUT
& PYTHON scripts\ckb.py coverage --out OUTPUT
```

`reindex` 同时重建机器库和兼容索引。`coverage` 必须报告所有实体均为 `agent-reviewed`、中文叙述覆盖率为 `1.0`，并通过 SQLite 完整性和外键检查。

## 查询档位

```powershell
& PYTHON scripts\ckb.py retrieve --out OUTPUT `
  "修改订单失败后的库存回滚" --budget 1800 --max-pages 8 --profile fast

& PYTHON scripts\ckb.py retrieve --out OUTPUT `
  "跨模块失败恢复与持久化边界" --budget 3000 --max-pages 12 --profile precise
```

两种档位均为纯确定性：

- `fast`：精确锚点、词项、实体/章节 FTS5，加固定权重的两跳图传播；
- `precise`：增加固定源码 FTS，并使用固定 24 轮、固定重启率的加权 PageRank。

同分按稳定实体 ID 排序。同一机器库和查询重复执行时，实体顺序、得分与得分分解必须一致。本版没有向量模型、embedding、外部模型调用或随机采样。

结果会生成预算内 `machine/agent-packs/*.md` 和 JSON 记录。先打开阅读包，再按需使用下列窄接口：

```powershell
& PYTHON scripts\ckb.py entity --out OUTPUT "OrderService"
& PYTHON scripts\ckb.py neighbors --out OUTPUT "OrderService" --depth 2
& PYTHON scripts\ckb.py source --out OUTPUT "OrderService" --context-lines 3
& PYTHON scripts\ckb.py changes --out OUTPUT --kind analysis
```

`passed` 结果已经给出来源绑定候选，不再加载完整图。`needs-source-read` 表示索引中没有可信候选，此时只按返回路径、词项和已知范围继续读取源码。

## 分节与上下文

机器库把每个实体拆成含义、职责、修改时机、来源说明和有界源码片段等章节；人类笔记按 Markdown 标题拆分。FTS 先命中章节，再把得分归属到来源实体，因此 Agent 可以读取少量相关章节而不是整页或整文件。文件实体不复制整个文件到实体章节；固定源码只在 `files/source_fts` 保存一次。

## 完成门

- `PRAGMA integrity_check` 返回 `ok`，外键检查为空；
- 文件、实体、源码范围、关系、审阅和人类归属计数与事实图一致；
- 所有要求叙述的字段含中文内容；
- 成功阅读包不超过请求预算，并带有可点击源码位置；
- `fast` 与 `precise` 重复查询结果稳定；
- 机器库缺少来源绑定候选时明确返回 `needs-source-read`，不生成猜测结果。
