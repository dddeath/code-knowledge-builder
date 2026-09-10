# keyword_provider_config

标签：#类型/代码

> 从命令行命名空间构造关键词 Provider 配置，先检查命令、Provider 名称、模型及版本四项必填信息，再交统一校验器验证配置。 把可重复命令参数与环境变量要求转换为元组，并传递超时和重试设置；缺少必填项时列出对应命令行选项，不返回半成品配置。

## 什么时候需要修改

调整关键词服务的启动参数、环境要求或超时重试字段时，联动 add_keyword_provider_arguments、KeywordProviderConfig 与 validate_provider_config。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 292 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:292:1)  `scripts/ckb.py:292-312`

## 谁会来到这里

- 与 [[keyword_fallback_options]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- [[keyword_provider_config 与 keyword_fallback_options 的协作实现]] 汇总了本页。
- 与 [[main（ckb 实现）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
