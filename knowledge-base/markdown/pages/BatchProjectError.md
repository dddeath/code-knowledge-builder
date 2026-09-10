# BatchProjectError

标签：#类型/代码

> 保存批量项目失败的分类与错误说明：构造时把 detail 交给 CkbError，再将 category 保留为独立属性。 让批量流程按错误类别记录单个项目失败，同时沿用 CkbError 的异常消息与退出码机制，不需要从错误文本反解析分类。

## 什么时候需要修改

调整批量失败分类或异常基类时，联动捕获 BatchProjectError 的计划、执行和回滚分支及结构化 failure 字段。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_protocol_batch.py 第 161 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol_batch.py:161:1)  `scripts/ckb_core/agent_protocol_batch.py:161-164`

## 相关代码

- 实现时会用到 [[CkbError]]。

## 谁会来到这里

- [[BatchProjectError 与 ProtocolRelease 的协作实现]] 汇总了本页。
- 与 [[create_knowledge_batch_plan]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_knowledge_batch_plan 与 KnowledgeRelease 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 内部细节

<details><summary>查看本页收纳的 1 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `BatchProjectError.__init__` | `BatchProjectError.__i...` 是第 162-164 行的函数，供所属页面定位实现。 |

</details>
