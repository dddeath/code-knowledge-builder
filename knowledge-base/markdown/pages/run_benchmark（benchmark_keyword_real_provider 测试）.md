# run_benchmark（benchmark_keyword_real_provider 测试）

标签：#类型/代码

> 该函数验证冻结协议及提供器配置，复制语料后运行十二题真实模型与故障探针，核对默认不启动、强制单次启动、热缓存不重启及索引未变，再保存原始结果和报告。 它是真实关键词提供器基准的编排入口，缺少可执行配置时提前输出未执行状态；已运行时分别记录流程检查结果和质量主张，默认在结束时清理临时语料副本。

## 什么时候需要修改

提供器准入、实验执行顺序、调用计数验收、源副本索引校验或语料保留开关变化时修改此函数，并检查真实调用结果没有与故障夹具混算。

## 在代码中的位置

[打开源码：tests/benchmark_keyword_real_provider.py 第 544 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_keyword_real_provider.py:544:1)  `tests/benchmark_keyword_real_provider.py:544-686`

## 相关代码

- 与 [[run_benchmark 等测试场景（benchmark_keyword_real_provider 测试）]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[run_benchmark 等测试场景（benchmark_keyword_real_provider 测试）]] 汇总了本页。
