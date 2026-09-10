# keyword_fallback_options

标签：#类型/代码

> 仅在允许或强制关键词回退时创建 KeywordFallbackOptions；两个开关均关闭时返回 None。 复用 Provider 配置构造，分别把 force 开关和缓存禁用开关转换为执行与缓存策略，供 retrieve/brief 决定是否绕过会话检索通道。

## 什么时候需要修改

修改回退启用条件、强制执行或缓存语义时，联动关键词参数声明及 main 中的会话分支和机器库存在性检查。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 315 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:315:1)  `scripts/ckb.py:315-322`

## 相关代码

- 实现时会用到 [[KeywordFallbackOptions]]。
- 与 [[keyword_provider_config]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[keyword_provider_config 与 keyword_fallback_options 的协作实现]] 汇总了本页。
- 与 [[main（ckb 实现）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
