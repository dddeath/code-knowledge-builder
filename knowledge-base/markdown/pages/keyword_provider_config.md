# keyword_provider_config

标签：#类型/代码

> `keyword_provider_config` 是 `scripts/ckb.py` 第 237-257 行定义的函数，本页绑定该固定源码范围。 负责注册 CKB 命令、校验参数，并把子命令分派到对应的知识库实现。

## 什么时候需要修改

当 `keyword_provider_config` 的输入、输出、状态转换或失败返回变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 237 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:237:1)  `scripts/ckb.py:237-257`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[KeywordFallbackRetrievalWiringTests 等测试场景]]。
- 实现时会用到 [[command]]。
- 实现时会用到 [[run_keyword_provider 与 KeywordProviderConfig 的协作实现]]。

## 谁会来到这里

- [[keyword_provider_config 与 parser 的协作实现]] 汇总了本页。
