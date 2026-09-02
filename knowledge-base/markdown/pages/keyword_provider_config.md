# keyword_provider_config

标签：#类型/代码

> `keyword_provider_config` 位于 `scripts/ckb.py` 第 270-290 行，本页用固定源码范围说明它如何完成CKB 主命令解析、分发和退出状态中的局部职责。 `keyword_provider_config` 负责在CKB 主命令解析、分发和退出状态中完成CKB 主命令解析、分发和退出状态中的局部职责。

## 什么时候需要修改

当 `scripts/ckb.py` 中 `keyword_provider_config` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 270 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:270:1)  `scripts/ckb.py:270-290`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。
