# Code Knowledge Builder Agent 工作协议

本文件是自动加载的项目级工作指令，不是知识页面。凡是读取、解释或修改本知识库及其对应源码的智能体，都必须遵循以下流程；无需用户再次点名 Skill。

## 绑定范围

- 知识库：`E:\knowledge_builder\self-workspace\knowledge-base`
- 源码仓库：`E:\knowledge_builder\self-workspace\source`
- 命令入口：`E:\knowledge_builder\self-workspace\source\scripts\ckb.py`

## 先检索，后读源码

1. 回答架构、实现、定位或修改问题前，先执行紧凑阅读入口。它在一个小 JSON 中返回开放反馈数、Agent pack、完整检索 record 和固定阅读入口，不把候选实体、词项和得分展开到首轮上下文：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe' 'E:\knowledge_builder\self-workspace\source\scripts\ckb.py' brief --out 'E:\knowledge_builder\self-workspace\knowledge-base' "QUESTION" --budget 1800 --max-pages 8 --profile fast
```

2. 若 `open_feedback` 大于零，再列出开放反馈；任务涉及其目标页时按 `error`、`warn`、`suggest`、`info` 的固定优先级处理：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe' 'E:\knowledge_builder\self-workspace\source\scripts\ckb.py' feedback list --out 'E:\knowledge_builder\self-workspace\knowledge-base' --status open
```

3. 先阅读 `brief` 返回的预算化 Agent pack；完整候选与得分仍保存在 `record`。再按 pack 使用 `entity`、`neighbors`、`source` 或 `changes`；复杂跨模块问题才切换 `precise`。
4. 只有检索明确返回 `needs-source-read`，或返回了需要核实的精确路径和范围时，才使用窄范围源码读取。`grep`、全仓文件遍历和整库页面加载只作为这一分支的补充手段，不得替代首轮 SQLite 检索。
5. 人类需要查找已有分析、变更或实验时，从 `RECORDS.md` 按任务目的浏览；查找已审阅外部资料时从 `REFERENCES.md` 浏览。两个导览都由完整集合生成，不允许为单个查询手工挑选页面。

## 受控维护

1. `human/pages`、`markdown/pages`、`human/references`、`markdown/references`、`INDEX.md`、`WIKI.md`、`REFERENCES.md`、投影清单和 SQLite 文件属于生成器管理内容，不直接编辑。
2. 可复用分析、修改原因、踩坑和实验只通过 `record` 写入；正文使用简体中文，并通过 `--from-pack`、`--from-query` 或唯一 `--link` 回链至少一个知识页。
3. 创建分析页的标准命令：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe' 'E:\knowledge_builder\self-workspace\source\scripts\ckb.py' record --out 'E:\knowledge_builder\self-workspace\knowledge-base' --kind analysis --title 'TITLE' --body 'BODY.md' --from-pack 'PACK.json'
```

4. 更新已有人工笔记时使用同标题和 `--append`。Hook 仅采集会话与修改事件，并在 Agent 审核后新建会话页或修改页；其他已有页面只在任务明确要求时执行显式追加，不随每轮对话扩散更新。
5. 外部文本资料只通过 `reference ingest/review/audit/rollback` 进入独立参考层。Agent 必须重新打开归档原文，逐项提交精确行范围、原文文本、中文主张和中文来源核对；参考资料不成为代码实体。
6. 检索证据不足、来源冲突或反馈需要暂缓时，使用 `gaps create` 把中文待验证说明和现有证据路径写入机器缺口层。缺口不属于已确认事实，也不为每项缺口创建页面；开始新任务时可执行：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe' 'E:\knowledge_builder\self-workspace\source\scripts\ckb.py' gaps list --out 'E:\knowledge_builder\self-workspace\knowledge-base' --status open
```

7. 人工反馈通过 `feedback create` 进入带行范围和文本窗口的收件箱。处理前先执行：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe' 'E:\knowledge_builder\self-workspace\source\scripts\ckb.py' feedback locate --out 'E:\knowledge_builder\self-workspace\knowledge-base' --feedback 'FEEDBACK_ID'
```

生成器管理页面仍不直接编辑；采纳或部分采纳时先修改来源、生成规则或通过 `record` 写入落实记录，再用 `feedback resolve` 归档。拒绝必须写明中文理由；暂缓记录继续留在开放列表。反馈记录不删除。
8. 结束实质任务前执行聚合维护门；它统一检查反馈、Agent Policy、工作记录、参考资料、研究缺口、机器操作日志、人类可读性、机器知识库和兼容索引，并且不创建知识页面：

```powershell
& 'C:\Users\19739\.codex\cache\code-knowledge-builder\runtime\win-x64\win-x64-2.1.0\python\python.exe' 'E:\knowledge_builder\self-workspace\source\scripts\ckb.py' maintain --out 'E:\knowledge_builder\self-workspace\knowledge-base'
```

只有协议文件、中文与链接规则、human/markdown 镜像、笔记元数据以及两个 SQLite 索引全部一致时，才报告知识库维护完成。失败时根据 `failed_checks` 运行窄范围审计，修复对应笔记或重新执行 `record`/`reindex`，再复查。

## 最小上下文原则

- 优先顺序固定为：`brief fast` → Agent pack → `entity/neighbors/source/changes` → 返回路径的窄范围读取。
- 不预先加载整个模块、整个 vault 或完整关系图。
- 页面正文保持面向人类的简体中文叙述；英文仅保留专有名词、API、类型、函数、变量、命令和路径。
