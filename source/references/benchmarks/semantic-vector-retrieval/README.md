# 语义向量检索实验来源

本目录只保存实验前核对过的上游身份与许可证证据，不进入生产检索。

## 已冻结的引擎与模型

- 引擎：FastEmbed `0.8.0`，来源为 Qdrant 原始仓库的 `v0.8.0` tag；项目声明 Apache License 2.0，并以 ONNX Runtime 执行本地 embedding。
- 模型：FastEmbed 注册名 `BAAI/bge-small-zh-v1.5`，实际 ONNX 仓库为 `Qdrant/bge-small-zh-v1.5`，冻结 revision 为 `46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59`。
- 模型规格：中文、512 维、最多 512 input tokens、模型登记大小约 0.09 GB、MIT License；FastEmbed 对该模型输出 L2 归一化向量。
- 查询格式：短查询前添加 `为这个句子生成表示以用于检索相关文章：`，文档不添加指令。该规则来自 BGE 原始模型卡。

## 证据入口

- [FastEmbed v0.8.0 原始仓库](https://github.com/qdrant/fastembed/tree/v0.8.0)
- [FastEmbed v0.8.0 项目元数据](https://raw.githubusercontent.com/qdrant/fastembed/v0.8.0/pyproject.toml)
- [FastEmbed v0.8.0 许可证](https://raw.githubusercontent.com/qdrant/fastembed/v0.8.0/LICENSE)
- [FastEmbed v0.8.0 模型注册表](https://github.com/qdrant/fastembed/blob/v0.8.0/fastembed/text/onnx_embedding.py#L83-L98)
- [FastEmbed v0.8.0 归一化实现](https://github.com/qdrant/fastembed/blob/v0.8.0/fastembed/text/onnx_embedding.py#L304-L322)
- [Qdrant ONNX 模型仓库](https://huggingface.co/Qdrant/bge-small-zh-v1.5/tree/46fbe35fd4374a00fee7de77dfddaeb6dd6a2c59)
- [BAAI 原始模型卡](https://huggingface.co/BAAI/bge-small-zh-v1.5)
- [FastEmbed 官方支持模型表](https://qdrant.github.io/fastembed/examples/Supported_Models/)

`source-manifest.json` 保存核对时间、上游响应摘要和本实验采用的事实。真实运行还必须生成本地模型文件清单；协议通过 revision 和逐文件 SHA-256 阻止模型身份漂移。
