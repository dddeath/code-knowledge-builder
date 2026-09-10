# create_gap

标签：#类型/代码

> 该函数校验输出、缺口种类、中文说明和一至十二个证据文件，以规范化内容生成稳定编号；重复编号直接返回原记录，新记录按种类进入开放或暂缓状态。 它是研究缺口登记入口，新增记录后更新缺口索引、已有的人类导览和机器索引，并执行缺口审计，不把待验证说明转成已确认知识主张。

## 什么时候需要修改

创建准入、说明规范化、编号去重依据、初始状态或索引同步顺序变化时修改此函数，并检查相同输入幂等及新记录的证据路径有效性。

## 在代码中的位置

[打开源码：scripts/ckb_core/research_gaps.py 第 124 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/research_gaps.py:124:1)  `scripts/ckb_core/research_gaps.py:124-150`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[create_gap 与 _root 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[create_gap 与 _root 的协作实现]] 汇总了本页。
