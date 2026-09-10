# keyword_provider_config 与 keyword_fallback_options 的协作实现

标签：#类型/代码

> 将终端参数转换为建库、检索、迁移、参考资料、页面候选文稿和管理操作，输出结构化结果及对应退出码；同时保留 stdio 服务和会话复用入口。 统一维护 argparse 子命令、参数默认值与核心函数分派。普通 JSON 输出附带操作记录；Prompt 输出使用固定 UTF-8 字节。检索可复用会话，显式关键词回退则直接调用完整机器检索；Hook 入口将内部异常写到 stderr 而不阻塞调用方。

## 什么时候需要修改

新增或调整命令时同时修改 parser、main 分派和退出码约定；检索回退、页面候选文稿、参考资料或管理字段改变时，还需检查相应核心调用和 CLI 契约测试，避免参数声明与实际执行脱节。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:1:1)  `scripts/ckb.py:1-1850`

## 相关代码

- 主要代码单元是 [[keyword_fallback_options]]。
- 主要代码单元是 [[keyword_provider_config]]。
- 主要代码单元是 [[main（ckb 实现）]]。
- 主要代码单元是 [[parser]]。

## 谁会来到这里

- 与 [[main（ckb 实现）]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[parser]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `add_initial_arguments` | 向解析器登记仓库、输出、格式、范围、入口、展开方向与页面配置参数，并复用 C# 和首次 Git 初始化选项。 |
| `add_csharp_arguments` | 向解析器添加 C# solution/project 选择及显式允许 dotnet restore 的开关。 |
| `add_git_bootstrap_arguments` | 登记显式首次 Git 初始化、初始提交说明与作者参数，默认不启用初始化。 |
| `add_keyword_provider_arguments` | 登记关键词 Provider 的命令与重复参数、模型版本、二十秒默认超时、零或一次重试、环境要求及缓存禁用开关。 |
| `add_keyword_fallback_arguments` | 登记允许和强制关键词回退两个开关，再添加共用 Provider 参数。 |
| `emit` | 存在活动命令参数时先记录 CLI 操作，再将结果以保留中文的缩进 JSON 输出。 |
| `emit_prompt_json` | 将保留中文、带末尾换行的 JSON 编码为 UTF-8 后直接写入标准输出字节流。 |
| `emit_prompt_text` | 将给定 Prompt 文本按 UTF-8 原样写入标准输出字节流，不额外追加换行。 |
| `_session_query` | 尝试复用指定知识库的会话请求，未启动时返回 None，响应错误或缺少字典结果时报错，成功时补充进程与代次元数据。 |

</details>
