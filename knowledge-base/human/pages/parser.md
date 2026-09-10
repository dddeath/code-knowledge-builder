# parser

标签：#类型/代码

> 构造完整的 argparse 命令树，定义建库、检索、来源审阅、迁移、页面候选文稿、会话及管理操作所接受的参数。 使用必选子命令、类型转换、固定 choices 和互斥组约束输入；例如审计范围、记录追加/替换和页面配置写入/校验各有明确互斥入口。它只描述并返回解析器，不执行知识库操作。

## 什么时候需要修改

核心接口增加字段或默认行为改变时，同步调整参数声明、main 分派、帮助文案和命令行契约测试；保持源路径与格式等必填条件及互斥关系一致。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 325 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:325:1)  `scripts/ckb.py:325-949`

## 相关代码

- 与 [[keyword_provider_config 与 keyword_fallback_options 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[keyword_provider_config 与 keyword_fallback_options 的协作实现]] 汇总了本页。
- 与 [[main（ckb 实现）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
