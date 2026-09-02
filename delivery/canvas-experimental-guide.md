## 实验功能：让 Agent 生成当前问题的 Obsidian Canvas

当文字页面已经说明了结论，但你还需要看清“哪些页面、源码范围和证据共同支持当前问题”时，可以让 Agent 生成一张小型 Obsidian Canvas。它是阅读已有知识库后的辅助视图，不替代首页、工作记录或机器知识图谱。

当前发布包含一个隔离原型：Agent 先从固定的 CKB 检索结果选择少量节点和关系，再在指定 staging 目录生成 Canvas、验证记录和回滚清单。生成失败不会改写稳定知识页；写入成功后也可以按清单恢复到生成前状态。

把下面的提示词交给已经安装本项目 Skill 的 Agent。通常只需要替换知识库路径和希望解释的问题：

```text
请使用 code-knowledge-builder Skill 先检索 KNOWLEDGE_BASE，回答“QUESTION”。
检索通过后，调用发布包中的实验性 ckb-canvas-prototype Skill，把本次问题涉及的少量知识页、工作记录和源码入口生成到一个隔离 Obsidian Canvas。

要求：
1. 只使用本次 CKB 检索包中已经返回的证据，不展开完整机器图谱；
2. 先验证请求和所有输出路径，再生成 Canvas；
3. 不改写稳定知识页、RECORDS.md、REFERENCES.md 或 SQLite；
4. 完成后重新打开 Canvas、validation manifest 和 rollback manifest；
5. 向我说明这张图回答了什么、遗漏了什么，并给出可直接执行的回滚入口；
6. 将成功、失败和回滚结果分开报告。
```

原型入口位于 `source/prototypes/ckb-canvas-skill/`。其中 `SKILL.md` 说明 Agent 编排顺序，`schemas/` 固定请求、结果和回滚合同，`scripts/ckb_canvas.py` 执行确定性验证、生成、benchmark 和回滚。

这是实验功能。当前已经验证确定性生成、路径隔离、失败恢复和回滚；真实 Obsidian 中的导航效率仍需要人类使用反馈。试用后请记录：你原本要解决的问题、Canvas 是否更快找到入口、哪些节点多余或缺失、是否发生错误跳转，以及回滚是否符合预期。这些反馈将决定它是否进入正式 Skill。
