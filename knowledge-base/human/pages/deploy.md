# deploy

标签：#类型/代码

> 该函数依据部署计划决定是否直接返回已有运行时，或在明确接受部署后解包锁定负载到暂存目录，核验压缩成员路径与清单文件的大小及哈希，再替换版本目录。 它负责私有运行时的落地，保留部署前宿主快照和负载身份；未接受部署或负载状态无效时提前报错，不修改系统级依赖配置。

## 什么时候需要修改

运行时负载格式、路径约束、成员校验、版本目录替换或接受标记规则变化时修改此函数，并验证错误包不会被登记为就绪。

## 在代码中的位置

[打开源码：scripts/ckb_core/runtime.py 第 70 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:70:1)  `scripts/ckb_core/runtime.py:70-123`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[deploy 与 skill_root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[deploy 与 skill_root 的协作实现]] 汇总了本页。
