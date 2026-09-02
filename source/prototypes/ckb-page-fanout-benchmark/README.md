# 单文档页面扩散隔离 benchmark

该原型只在显式 `--workspace-root` 内复制冻结的保守页面集并生成实验页面。它不导入生产页面生成器，不写稳定知识库，也不根据模型常识补全文本。

候选必须来自冻结 manifest；术语必须出现在精确原文范围内，中文主张必须与该范围逐字相同。单文档页面数、全局页面数和每页内部链接数均由合同固定，超额候选写入 `rejected_candidates`，不静默扩张。

```powershell
python scripts/ckb_page_fanout.py generate `
  --contract CONTRACT.json --corpus CORPUS.json `
  --source-root FIXTURE_ROOT --conservative-root CONSERVATIVE_ROOT `
  --out ISOLATED_OUTPUT --rollback-manifest ROLLBACK.json `
  --workspace-root WORKTREE

python scripts/ckb_page_fanout.py rollback `
  --manifest ROLLBACK.json --workspace-root WORKTREE
```

回滚只删除 manifest 中路径和整树摘要均匹配的隔离输出；任何漂移都会返回稳定失败原因并保留现场。
