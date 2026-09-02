---
name: ckb-canvas-prototype
description: 在隔离 staging 根中验证、生成或回滚冻结 CKB Canvas 原型，并运行冻结 Markdown/Canvas 对照。
---

# CKB Canvas 原型编排

本 Skill 只编排 `scripts/ckb_canvas.py`。候选选择、关系、预算、稳定 ID、editor URI、规范 JSON、promotion 和 rollback 均由确定性脚本完成。

## 生成或验证

1. 接收一个已填写的 schema 1 `canvas-request.json`。
2. 调用 `validate --request REQUEST.json`；记录字面 stdout、stderr 摘要和退出状态。
3. 需要写入时调用 `generate --request REQUEST.json`。
4. 重开成功结果列出的 Canvas、validation manifest 和 rollback manifest，核对路径与 SHA-256。

## 回滚

只调用：

```powershell
& $Python prototypes\ckb-canvas-skill\scripts\ckb_canvas.py rollback `
  --manifest TARGET.canvas.rollback.json `
  --expected-sha256 MANIFEST_SHA256
```

不得手工编辑或覆盖 Canvas。rollback 发现当前角色或 backup 漂移时，保留当前完整字节与 backup。

## 冻结对照

使用 `benchmark --run RUN.json --session SESSION_ID` 收集一个固定 sequence 的观察；使用 `summarize --run RUN.json --sessions SESSION-DIR --write SUMMARY.json` 统一计算指标和七门。Skill 不改变任务、顺序、答案、证据 hash 或预算。
