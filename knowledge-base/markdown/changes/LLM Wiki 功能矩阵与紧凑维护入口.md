# LLM Wiki 功能矩阵与紧凑维护入口

标签：#类型/变更

## 本批次结果

本批次继续吸收 LLM Wiki 中能够降低 Agent 检索上下文、改善维护闭环且不增加生成页面数量的能力，并把其余候选固定为四态矩阵。矩阵只使用“已吸收、待吸收、明确排除、需要 benchmark”，每项均记录输入、输出、依赖、许可证、数据边界、完成门和实施批次。

当前矩阵共十九项：已吸收十项、待吸收三项、明确排除三项、需要 benchmark 三项。审阅文本参考资料层、有界机器操作日志、研究缺口登记进入下一小批次候选；qmd/向量检索、PDF/网页/OCR 和自动页面扩散保持隔离 benchmark；外部文档伪装成代码事实、复制第二套 Web 查看器和复制大型二进制保持明确排除。

## 紧凑阅读入口

新增 `brief` 命令。它复用现有确定性 SQLite `retrieve`，照常生成完整 JSON record 和预算化 Agent pack，但首轮命令响应只返回 pack、record、开放反馈数、固定阅读入口和源码回退判断，不展开词项、候选实体、得分分解、关系文档和检索统计。

在当前自身知识库、相同问题和相同 1800 token 预算下，完整 `retrieve` 响应为 12014 字节，`brief` 响应为 1089 字节，减少 10925 字节，即 90.94%。该数字只表示 Harness 首轮命令响应大小变化，不替代检索质量、延迟或任务完成率 benchmark。完整证据仍保存在 record，Agent pack 和 record 均已重新打开验证。

Agent 协议升级到 1.3.0，读取顺序变为 `brief fast → Agent pack → entity/neighbors/source/changes → 窄范围源码`。只有 `open_feedback` 大于零时才继续列出反馈，避免每次会话固定执行无结果命令。

## 聚合维护门

新增 `maintain --out OUTPUT`。它聚合 Agent Policy、工作记录索引、兼容 Agent index、完整机器知识库、人类知识层和人类可读性审计，结果写入 `workspace-meta/maintenance/latest.json`。该命令不创建知识页面。

真实自身知识库验收时，human 与 markdown 共二百一十七个 Markdown 文件在维护前后集合与字节摘要完全一致，`page_writes` 为零，所有子门通过。Obsidian 的 `appearance.json` 和 `core-plugins.json` 属于用户界面状态，允许两个 vault 产生差异；Agent Policy 仍独立验证必要的隐藏规则、输出契约和插件绑定。

## 后台子进程

CKB 的非交互 Git、批量 blob 读取、语言服务器和插件构建子进程在 Windows 使用 `CREATE_NO_WINDOW`，Obsidian stdio 与 Provider 路径继续使用 `windowsHide`。stdout、stderr、退出码、超时、取消和命令参数保持原语义。用户主动运行的 CLI、显式终端和 Shell 功能继续使用 Harness 的可见界面。

## 许可证和数据边界

本批次只吸收 LLM Wiki 的行为与接口思想，未复制其本地参考源码，因为该参考目录没有可确认的许可证声明。新增运行时代码为 CKB 独立实现，不增加第三方依赖。固定 Git 源码事实层仍只接收受支持代码语言；外部资料必须进入未来独立参考层，并在来源、许可、页面配额和审计完成前保持待审阅。

## 验证

核心三十项测试、跨 Harness Hook 二十二项测试、发行边界三项测试和单独维护集成测试通过。Skill 源码与安装版结构验证通过；5.2.9 lite 与安装版六百六十六个文件逐项一致；真实维护门通过且知识页字节未变化。

## 相关知识页

- [[package_showcase 与 _parse_sample 的协作实现]]
- [[initialize 与 _replace_output_prefix 的协作实现]]
- [[CkbError 与 DependencyError 的协作实现]]
- [[audit_migration 与 _entity_key 的协作实现]]
- [[MigrationTest 等测试场景]]
- [[query_graph 与 _networkx_modules 的协作实现]]
- [[audit_obsidian 与 prepare_vault 的协作实现]]
- [[retrieve_machine 与 estimated_tokens 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3314`
- [打开源码：scripts/ckb_core/common.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/common.py:1:1)  `scripts/ckb_core/common.py:1-158`
- [打开源码：scripts/ckb_core/migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/migration.py:1:1)  `scripts/ckb_core/migration.py:1-585`
- [打开源码：tests/test_migration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_migration.py:1:1)  `tests/test_migration.py:1-194`
- [打开源码：scripts/ckb_core/graphify_core.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/graphify_core.py:1:1)  `scripts/ckb_core/graphify_core.py:1-676`
- [打开源码：scripts/ckb_core/obsidian.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/obsidian.py:1:1)  `scripts/ckb_core/obsidian.py:1-134`
- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
