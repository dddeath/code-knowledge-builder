# ingest_web_reference

标签：#类型/代码

> 该函数在本地响应快照和显式联网请求之间要求恰选一种输入，先完成响应与正文提取核验，再归档原始 HTML、提取证据、来源清单和待审模板；相同来源内容幂等返回，变化必须指向最新已审阅修订。 它把网页获取适配器接入参考资料生命周期，记录最终地址、时间、状态及原文和正文双哈希，并标记不同地址下的重复内容。导入结束仍停在 Agent 审阅门，不直接生成已审阅主张。

## 什么时候需要修改

两种输入模式的参数边界、网页幂等键、显式修订条件、归档失败清理或获取证据字段变化时修改此函数，并验证网络失败未归档、重复导入和内容漂移分支。

## 在代码中的位置

[打开源码：scripts/ckb_core/reference_documents.py 第 402 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/reference_documents.py:402:1)  `scripts/ckb_core/reference_documents.py:402-640`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[ingest_web_reference 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[validate_web_extraction 与 WebSnapshotError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[ingest_web_reference 与 _root 的协作实现]] 汇总了本页。
