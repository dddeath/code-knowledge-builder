# KeywordFallbackOptions 与 KeywordProviderConfig 的协作实现

标签：#类型/代码

> 为可选关键词慢路径提供适配器配置、输出校验、缓存和机器记录。 仅调用显式配置的命令，以受限重试和超时获取关键词、符号锚点及改写；验证失败返回结构化原因。缓存区分问题与模型版本，本文件不证明真实模型已调用或检索效果改善。

## 什么时候需要修改

调整关键词输出合同、提供器调用、缓存身份或记录隐私边界时修改。

## 在代码中的位置

[打开源码：scripts/ckb_core/keyword_fallback.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/keyword_fallback.py:1:1)  `scripts/ckb_core/keyword_fallback.py:1-638`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[KeywordFallbackOptions]]。

## 谁会来到这里

- 与 [[KeywordFallbackOptions]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[maintenance_check]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[run_keyword_benchmark]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。
- 与 [[serve_stdio 与 _write_line 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 内部细节

<details><summary>查看本页收纳的 23 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `KeywordProviderConfig` | 保存关键词适配器的命令、Provider/模型/版本标识以及超时、重试和环境变量要求。 |
| `keyword_input_hash` | 对原始问题的 UTF-8 字节计算 SHA-256，作为输入身份。 |
| `keyword_request_id` | 使用问题哈希的前二十四位构造可重复的关键词请求标识。 |
| `keyword_cache_key` | 校验配置后，将问题哈希、Provider、模型、版本与提示协议稳定序列化并计算缓存键。 |
| `canonical_keyword_request` | 构造命令式关键词适配器的统一请求，包含问题、请求标识、输入哈希及各类候选的数量和字符限制。 |
| `_machine_token` | 要求 Provider 身份字段为匹配有界机器标记规则的字符串，失败时报告字段名。 |
| `validate_provider_config` | 检查非空命令参数、机器身份标记、超时范围、零或一次重试及合法环境变量名称。 |
| `_bounded_strings` | 校验候选字符串数组的数量、长度和字符范围，拒绝注入或凭据形态以及忽略大小写的重复项。 |
| `_usage` | 规范输入输出 token 和费用统计，拒绝未知字段、负数和非法类型，并检查非零总量与分项之和一致。 |
| `validate_provider_response` | 核验响应 schema、请求身份和候选列表，成功必须含至少一个候选，失败则规范为带空候选的标准失败对象。 |
| `parse_provider_json` | 解析 Provider 返回的 JSON 文本，解析失败转为统一关键词服务错误。 |
| `_failure` | 根据问题、配置和失败类型生成标准失败响应，清空候选并提供零用量统计。 |
| `keyword_cache_path` | 由问题和服务配置计算缓存键，再返回知识库机器元数据中的对应缓存路径。 |
| `_cache_path` | 将缓存键映射到知识库关键词回退缓存目录内的同名 JSON 路径。 |
| `_cache_record` | 将已验证响应与缓存键、输入哈希、提示协议和服务身份组成固定缓存记录。 |
| `_read_cache` | 只接受字段和身份均匹配且响应重新校验成功的缓存，其余缺失、损坏或不匹配情况返回 None。 |
| `_write_cache` | 构造固定缓存记录并写入对应 JSON，返回缓存文件路径。 |
| `_transient` | 把进程失败、限流、超时和不可用四种错误判断为可短暂重试的失败。 |
| `run_keyword_provider` | 校验环境与缓存后通过命令标准输入请求关键词，规范失败、有限重试并只缓存成功响应，返回次数、耗时和缓存状态。 |
| `audit_keyword_cache` | 不读取服务凭据而检查缓存 schema、键、输入哈希、身份和敏感形态，并报告异常文件或目录项。 |
| `write_keyword_fallback_record` | 以输入哈希和服务身份等元数据生成请求记录路径，保存回退前后结果与验证扩展，不保存原始问题。 |
| `audit_keyword_fallback` | 合并缓存与请求记录审计，核验 schema、状态、触发方式和文件身份，并拒绝原始问题、命令输出及凭据形态进入请求记录。 |
| `unique_casefold` | 去掉字符串首尾空白，以忽略大小写的身份去重，保持首个非空值的原始大小写与顺序。 |

</details>
