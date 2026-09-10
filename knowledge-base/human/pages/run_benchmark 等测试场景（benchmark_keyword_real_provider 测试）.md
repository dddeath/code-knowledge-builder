# run_benchmark 等测试场景（benchmark_keyword_real_provider 测试）

标签：#类型/代码

> 该模块以冻结十二题协议比较确定性检索与真实关键词提供器的冷、热缓存结果，采集调用次数、质量、延迟及实际用量，并单独执行故障注入矩阵。未配置可执行提供器时生成未执行报告。 它把真实模型测量与故障夹具证据分开，复用固定语料副本防止污染原库，通过协议一致性和索引完整性检查约束实验；费用未由提供器报告时保留未知，不推算成本。

## 什么时候需要修改

真实提供器适配、冻结题集、调用触发规则、缓存、故障判定或质量与用量汇总变化时修改此模块，并验证未执行分支不产生效果主张。

## 在代码中的位置

[打开源码：tests/benchmark_keyword_real_provider.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/benchmark_keyword_real_provider.py:1:1)  `tests/benchmark_keyword_real_provider.py:1-710`

## 相关代码

- 主要代码单元是 [[run_benchmark（benchmark_keyword_real_provider 测试）]]。

## 谁会来到这里

- 与 [[run_benchmark（benchmark_keyword_real_provider 测试）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 18 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `json_load` | 以可含字节序标记的 UTF-8 读取 JSON，并要求根值为对象。 |
| `json_write` | 创建报告父目录并以缩进中文 JSON 写入对象，末尾保留换行。 |
| `sha256` | 读取文件原始字节并计算 SHA-256，用于冻结协议与语料身份核对。 |
| `percentile` | 对排序数值按相邻位置线性插值计算分位数，空输入返回零。 |
| `marker_count` | 以标记文件行数计量适配器启动次数，文件不存在时返回零。 |
| `environment` | 临时设置或删除指定环境变量，并在退出上下文时恢复每项原值。 |
| `validate_protocol` | 核对真实提供器基准的冻结模式、原始协议哈希、十二题一致性、故障矩阵及调用用量来源合同。 |
| `real_config` | 有显式提供器可执行配置时构造适配器参数，绑定模型、版本、超时和必需环境变量，否则返回空配置。 |
| `not_executed_report` | 生成明确标记未执行的基准报告，保留冻结协议身份并将真实调用次数记为零，不宣称效果增益。 |
| `timed_retrieval` | 按冻结语料参数执行一次机器检索，以高精度计时器返回检索结果和毫秒耗时。 |
| `measured_result` | 从检索结果提取去重排序文档、质量指标、上下文用量和签名，形成单次测量记录。 |
| `fallback_observation` | 提取关键词回退的触发、提供器状态、用量、输入词项和经过验证的扩展结果，形成有界观测记录。 |
| `run_real_cases` | 对冻结问题分别运行确定性基线、真实提供器冷缓存和热缓存检索，记录启动次数、延迟、质量变化及条件触发观测。 |
| `fault_config` | 构造不重试的故障注入适配器配置，允许测试指定超时和必需环境变量。 |
| `fault_probe_checks` | 从已保存基准字段重算故障判定，检查预期失败类型、基线状态排序保持或成功输出召回不下降。 |
| `run_fault_probes` | 按冻结故障矩阵运行受控检索探针，并单独验证证据不足状态触发非强制关键词回退。 |
| `summarize` | 汇总基线与真实提供器质量变化、调用用量、冷热缓存和延迟分位数，将未知费用保留为空值。 |
| `main` | 解析真实提供器基准路径及运行参数，执行基准并输出 JSON，未执行状态不当作命令失败。 |

</details>
