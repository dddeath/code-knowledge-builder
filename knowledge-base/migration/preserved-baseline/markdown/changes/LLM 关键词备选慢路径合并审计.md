# LLM 关键词备选慢路径合并审计

标签：#类型/变更

## 合并结果

开发分支 `codex/llm-keyword-slowpath` 的 4 个独立提交已由管理任务以普通非 squash merge 合入 `codex/reference-ingest-v1`。冲突只位于 CLI 导入、机器检索接线与 operation journal 文档：管理命令和慢路径命令均被保留；默认机器检索继续使用已合并的中文 `query_terms`；两类日志边界文档均被保留。

## 已确认行为

- 默认 `fast`、`precise` 和 `brief` 不构造 Provider 配置、不启动 Provider 进程，也不产生慢路径机器记录。管理任务以合并前中文词项集成提交为基准实际比较，结果对象、检索 record 和中文词项签名一致。
- `--allow-keyword-fallback` 只在原确定性检索返回 `needs-source-read` 时触发；`--force-keyword-fallback` 可显式扩展已通过的查询。Provider 失败时保留原确定性结果并写有界原因。
- LLM 只能给出结构化关键词、代码锚点和少量改写；候选通过 schema、身份、数量、长度、字符、重复、提示注入与凭据形态校验后，重新进入 SQLite FTS5 与确定性图排序。模型不直接决定实体、分数、完成状态或事实。
- 缓存键绑定输入哈希、Provider、Model、Version 与 Prompt schema。request record 和 operation journal 不保存问题正文、Provider 命令、环境变量值、stdout 或 stderr；`maintain` 增加慢路径缓存与 request schema 审计。

## 管理任务独立验证

合并前实际通过慢路径专项 15 项、核心 33 项、Harness 22 项和发行 3 项。解决三处冲突并合并后，实际通过中文词项 12 项、慢路径 15 项、管理 Agent 18 项、核心 37 项、Harness 22 项和发行 3 项。

管理任务还以真实 `codex-cli` 与 `gpt-5.6-luna` 执行一次强制 canary：单次 Provider 调用通过，验证后的扩展词项重新进入确定性检索；request record 审计、`machine/knowledge.sqlite` 完整性与外键检查通过。完整命令、字面输出、冲突决策和退出状态位于 `E:\knowledge_builder\artifacts\verification\llm-keyword-slowpath\management-audit.json`。

## 已测量边界

固定真实 benchmark 的平均定位质量增量为零，`quality_claim` 为 `not-demonstrated`；因此本记录只确认显式慢路径、回落、审计和缓存合同，不声明定位质量收益。真实 canary adapter 没有账单 telemetry，usage 与费用字段的零值表示未报告，不表示零 token 或零成本。管理 canary 的冷调用约 28 秒，默认路径仍保持零 Provider 启动。

## 回滚

集成回滚脚本位于 `E:\knowledge_builder\artifacts\verification\llm-keyword-slowpath\rollback-integration-merge.sh`。该脚本已在隔离 clone 中实际创建反向提交，验证回滚后的整树与合并前集成提交一致且工作树干净。

## 相关知识页

- [[serve_stdio 与 _write_line 的协作实现]]
- [[build 的协作边界]]
- [[maintenance_check 与 capability_matrix 的协作实现]]
- [[doctor_report 与 _version_matches 的协作实现]]
- [[deploy 的协作边界]]
- [[keyword_provider_config 与 parser 的协作实现]]
- [[serve_stdio]]

## 源码入口

- [打开源码：scripts/ckb_core/stdio_server.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:1:1)  `scripts/ckb_core/stdio_server.py:1-283`
- [打开源码：scripts/ckb_core/llm_wiki_capabilities.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/llm_wiki_capabilities.py:1:1)  `scripts/ckb_core/llm_wiki_capabilities.py:1-453`
- [打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-611`
- [打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-788`
- [打开源码：scripts/ckb_core/stdio_server.py 第 146 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/stdio_server.py:146:1)  `scripts/ckb_core/stdio_server.py:146-282`
