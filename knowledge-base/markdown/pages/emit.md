# emit

标签：#类型/代码

> 代码单元 `emit`负责解析 CKB 命令行输入并把请求分派到检索、迁移、参考资料和管理能力。 它属于所有 Harness 调用 CKB 的统一公开入口，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当公开命令、参数合同、退出状态或子系统入口变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 925 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:925:1)  `scripts/ckb.py:925-928`

## 相关代码

- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。

## 谁会来到这里

- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。
- [[render_integration 与 harness_retrieval_contract 的协作实现]] 会使用这里提供的行为。

## 相关测试

- [[AutomationTest.register 等测试场景]]
