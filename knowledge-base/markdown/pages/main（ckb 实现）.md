# main（ckb 实现）

标签：#类型/代码

> 解析一个 CLI 请求并调用相应核心能力，输出结果；审阅待办、审计失败、输入失败和新鲜度状态各按分支返回不同退出码。 将 argparse 命名空间转换为核心函数参数，并在检索命令中选择会话复用、完整机器库或旧索引路径。页面候选文稿异常返回结构化失败，Hook 异常另写 stderr；迁移、参考资料和审计分支不把待审状态当作完成。

## 什么时候需要修改

调整任何公开命令的状态、参数或返回结构时，应同时核对 parser 与分派分支；重点联动会话检索、关键词回退、迁移待审退出码、Hook 非阻塞约定及页面候选文稿输入错误处理。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 996 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:996:1)  `scripts/ckb.py:996-1838`

## 相关代码

- 与 [[keyword_fallback_options]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[keyword_provider_config]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[keyword_provider_config 与 keyword_fallback_options 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[parser]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[keyword_provider_config 与 keyword_fallback_options 的协作实现]] 汇总了本页。
