# C++ 解析与 SCons 回退合并审计

标签：#类型/变更

## 合并结论

`codex/cpp-parser-scons-fallback` 已通过管理 Agent 独立审计，并以保留五个开发提交的普通 merge 合入 integration branch。合并提交为 `ea455e2…`；稳定知识库的固定源码图谱更新仍按八项队列终态统一进入隔离 staging，本记录只保存已确认行为、测试与回滚边界。

## 已确认行为

- 有效 `#ifndef NDEBUG` 区域通过语法门；缺失 `#endif` 的相邻负例保留失败诊断。
- 块内 `const T &x(expr);` 记录为所属函数下的 declaration，不生成伪函数实体。
- pinned Tree-sitter 对完整 `template class/struct` 显式实例化的唯一缺失节点形状进入显式 recovery；其他 ERROR/MISSING 仍失败，模板定义保留真实类和函数实体。
- 无 `compile_commands.json` 时只静态读取 `SConstruct`/`SConscript` 等受支持构建文件：唯一标准进入 fallback flags，缺失或冲突证据使用固定默认值；precision 保持 `bounded-approximate`。
- 存在 compilation database 时保持 `exact`，SCons 证据不覆盖该路径；provider 记录真实子进程 `exit_status`。

## 独立与合并后验证

管理审计在开发 worktree 重跑 4 项专项、37 项核心、22 项自动化、3 项发行和 10 个真实 Provider 场景，全部通过。合并后在 integration HEAD 再次运行相同的 4 项专项、37 项核心、22 项自动化、3 项发行和 10 个真实 Provider 场景，全部通过；真实场景覆盖 C/C++ exact、bounded、missing-header negative、SCons C++20 证据、Python、JavaScript 和 C#。

## 回滚

开发分支提交和 merge commit均保留。integration 回滚入口为撤销 merge commit `ea455e2…`；开发任务还提供逐 commit 逆序回滚脚本。回滚后需要重跑同一专项、核心、Provider 和发行测试。完整管理证据位于 `E:\knowledge_builder\artifacts\verification\cpp-parser-scons-fallback\management-audit.json`。

## 相关知识页

- [[parser]]
- [[parse_file 与 _language 的协作实现]]
- [[render_integration 与 _looks_windows 的协作实现]]
- [[execute 等测试场景]]
- [[AutomationTest.register 等测试场景]]
- [[CodeKnowledgeBuilderTests]]
- [[initialize 与 _replace_output_prefix 的协作实现]]
- [[doctor_report 与 _version_matches 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb.py 第 164 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:164:1)  `scripts/ckb.py:164-488`
- [打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-446`
- [打开源码：scripts/ckb_core/automation_integrations.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation_integrations.py:1:1)  `scripts/ckb_core/automation_integrations.py:1-536`
- [打开源码：tests/provider_integration.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/provider_integration.py:1:1)  `tests/provider_integration.py:1-252`
- [打开源码：tests/test_automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_automation.py:1:1)  `tests/test_automation.py:1-882`
- [打开源码：tests/test_ckb.py 第 198 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb.py:198:1)  `tests/test_ckb.py:198-2127`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3482`
- [打开源码：scripts/ckb_core/providers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/providers.py:1:1)  `scripts/ckb_core/providers.py:1-611`
