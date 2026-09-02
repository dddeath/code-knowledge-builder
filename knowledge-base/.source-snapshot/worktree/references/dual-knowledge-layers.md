# 双知识库与事实层

## 固定边界

一次完成构建同时产生三个职责互不混淆的层。Agent 不得把人类页面当作完整事实数据库，也不得把机器实体表直接投影成人类页面。

1. `OUTPUT/facts/` 是可重建事实层。它保存与根 `graph.json` 字节一致的图、逐实体源码清单、审阅包清单和计数契约。
2. `OUTPUT/machine/knowledge.sqlite` 是 Agent 专用完整知识库。它保存所有文件、声明、源码范围、关系、证据、提供器、诊断、审阅、职责群、局部边界、人类页归属、固定快照源码、分节中文叙述、Agent 笔记和工作树覆盖记录。启用会话自动化后，`OUTPUT/machine/automation.sqlite` 作为同层补充库保存脱敏 Harness 事件、会话、轮次、修改路径和待审阅记录；`retrieve` 与 `changes` 会合并查询结果。
3. `OUTPUT/human/` 是人类专用简体中文 Markdown/Obsidian 知识库。它只保留受页面配额约束的类、函数及其职责聚合页；附属实体只以一句中文说明进入附录。`OUTPUT/markdown/` 是兼容镜像。

Logseq DB 是可选的人类投影，不替代机器 SQLite。`agent-index.sqlite` 是旧接口兼容索引，不再是首选 Agent 检索入口。

自动化原始记录不会直接进入人类层。只有 `automation review` 验证中文正文、中文审阅证据和完整 changed-path source-check 集合后，才通过普通 note 投影进入 `human` 与 `markdown`。

## 中文硬契约

下列内容必须使用简体中文叙述：

- `meaning_zh`、`role_zh`、`change_when_zh`、`description_zh` 和 `evidence_note`；
- 人类首页、Wiki、职责说明、关系句子和附录句子；
- Agent 阅读包中的解释、分析、修改内容与原因、踩坑、实验和会话总结。

英文可保留在专有名词、代码符号、路径、命令和必要术语中。页面标题可以直接是源码类名或函数名；正文不得是纯英文段落。逐包审阅、全局图、人类层和机器层都会重新检查；任一层失败时三个完成标记都不成立。

## 确定性检索

第一版检索完全在本地 SQLite 和确定性图算法中完成：

- Unicode NFKC、路径分词、snake_case、camelCase、CJK 连续词和双字词；
- 类名、函数名、限定名和路径的精确锚点；
- `entity_fts`、`section_fts` 和 `source_fts` 的 FTS5 trigram 排序；
- 固定关系权重与高连接节点惩罚；
- `fast` 的有界两跳传播，或 `precise` 的固定 24 轮加权 PageRank；
- 最终按实体 ID 打破同分，保证同一库、同一查询的输出稳定。

本版不加载 embedding，不调用向量模型，也不访问网络排序服务。向量方案只在后续冻结数据集、下游修改任务、召回成本与上下文预算的 benchmark 中比较，达到明确门槛后再决定是否进入产品路径。

## 常用命令

```powershell
& PYTHON scripts\ckb.py retrieve --out OUTPUT "问题" --budget 1800 --profile fast
& PYTHON scripts\ckb.py retrieve --out OUTPUT "较难的问题" --budget 3000 --profile precise
& PYTHON scripts\ckb.py entity --out OUTPUT "Qualified.Name"
& PYTHON scripts\ckb.py neighbors --out OUTPUT "Qualified.Name" --depth 2
& PYTHON scripts\ckb.py source --out OUTPUT "Qualified.Name" --context-lines 3
& PYTHON scripts\ckb.py changes --out OUTPUT --kind change
& PYTHON scripts\ckb.py coverage --out OUTPUT
```

`retrieve` 返回 `passed` 时只读取它生成的 `machine/agent-packs/*.md`。返回 `needs-source-read` 时，按返回的路径和词项执行最窄源码读取；不要退回全仓实体图或无范围 grep。

## 完成标记

- `.machine.complete`：事实层、机器 SQLite、中文覆盖和完整性审计通过。
- `.human.complete`：中文页面、双链、可点击源码、Obsidian、页面配额和可读性审计通过。
- `.complete`：所有分段审阅、全局事实、请求格式及以上两个层同时通过。

重新运行任何构建或审计阶段会先撤销旧标记。只有 `finalize` 可以同时写入三个完成标记。
