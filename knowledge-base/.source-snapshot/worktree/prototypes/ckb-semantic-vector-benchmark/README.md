# CKB 语义向量检索对照实验

该原型在稳定知识库的隔离副本上比较三条检索路线：

1. `sqlite-current`：当前生产 `retrieve_machine(..., profile="fast")`；
2. `semantic-vector`：FastEmbed 0.8.0 与固定 BGE 中文 ONNX 模型产生真实 embedding，再执行 float32 精确余弦排序；
3. `hybrid-rrf`：对前两条路线各自的 top 8 使用固定 `k=60` 的 Reciprocal Rank Fusion（RRF，倒数排名融合）。

默认检索源码、默认排序和稳定知识库均保持只读。模型、索引、运行时与测量输出只位于本原型目录或调用方指定的隔离输出目录。

## 环境

使用项目固定 Python 3.14 与 Windows `uv` 创建本目录 `.venv`，再按 `requirements-lock.txt` 安装。模型必须先按协议中的 Hugging Face revision 下载到 `.model-cache`，并与 `tests/fixtures/semantic-vector-retrieval/model-artifact-manifest.json` 的逐文件 SHA-256 一致。

## 运行

```powershell
$Root = 'E:\knowledge_builder\self-workspace\worktrees\semantic-vector-benchmark'
$Python = "$Root\prototypes\ckb-semantic-vector-benchmark\.venv\Scripts\python.exe"
$Runner = "$Root\prototypes\ckb-semantic-vector-benchmark\benchmark.py"

& $Python $Runner run `
  --protocol "$Root\tests\fixtures\semantic-vector-retrieval\protocol.json" `
  --model-manifest "$Root\tests\fixtures\semantic-vector-retrieval\model-artifact-manifest.json" `
  --model-dir "$Root\prototypes\ckb-semantic-vector-benchmark\.model-cache\Qdrant--bge-small-zh-v1.5--46fbe35f" `
  --source-corpus 'E:\knowledge_builder\self-workspace\knowledge-base' `
  --output "$Root\prototypes\ckb-semantic-vector-benchmark\.runs\fixed-v1"
```

运行结束后，用不导入 FastEmbed 或 CKB 源码的标准库脚本独立重算：

```powershell
& $Python "$Root\prototypes\ckb-semantic-vector-benchmark\recompute.py" `
  --protocol "$Root\tests\fixtures\semantic-vector-retrieval\protocol.json" `
  --raw "$Root\prototypes\ckb-semantic-vector-benchmark\.runs\fixed-v1\raw-results.json" `
  --reported "$Root\prototypes\ckb-semantic-vector-benchmark\.runs\fixed-v1\report.json" `
  --output "$Root\prototypes\ckb-semantic-vector-benchmark\.runs\fixed-v1\recomputed.json"
```

进程冷启动、热查询、首次/增量索引、峰值 RSS、索引/模型/运行时字节和子进程数均由 runner 保存。运行时以 socket guard 阻断网络连接；模型只从固定本地 snapshot 加载。
