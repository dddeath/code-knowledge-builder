# CKB 审阅文本资料层说明

标签：#类型/资料

## 这份资料讲什么

这份资料说明 CKB 如何把本地文本保存在独立参考层，经逐项来源审阅后进入 SQLite 检索，同时维持单来源单摘要页和可回滚修订。

## 关键结论

- 文档吸收只把本地 UTF-8 Markdown/TXT 放入独立参考层，不改变固定代码事实图。（[原文第 4–5 行](vscode://file/E:/knowledge_builder/self-workspace/knowledge-base/references/raw/CKB%20%E5%AE%A1%E9%98%85%E6%96%87%E6%9C%AC%E8%B5%84%E6%96%99%E5%B1%82%E8%AF%B4%E6%98%8E--r1.md:4:1））
- 审阅通过的原文章节进入 SQLite FTS，并以参考资料类型加入 Agent pack。（[原文第 8–9 行](vscode://file/E:/knowledge_builder/self-workspace/knowledge-base/references/raw/CKB%20%E5%AE%A1%E9%98%85%E6%96%87%E6%9C%AC%E8%B5%84%E6%96%99%E5%B1%82%E8%AF%B4%E6%98%8E--r1.md:8:1））
- 资料层要求精确行引用、单来源单摘要页和许可审计，并在修订通过前保留旧摘要。（[原文第 12–14 行](vscode://file/E:/knowledge_builder/self-workspace/knowledge-base/references/raw/CKB%20%E5%AE%A1%E9%98%85%E6%96%87%E6%9C%AC%E8%B5%84%E6%96%99%E5%B1%82%E8%AF%B4%E6%98%8E--r1.md:12:1））

## 来源

- 资料来源：CKB 5.3.0 本地演示资料
- 作者或组织：DDDeath
- 许可：CC0-1.0
- [打开归档原文](vscode://file/E:/knowledge_builder/self-workspace/knowledge-base/references/raw/CKB%20%E5%AE%A1%E9%98%85%E6%96%87%E6%9C%AC%E8%B5%84%E6%96%99%E5%B1%82%E8%AF%B4%E6%98%8E--r1.md:1:1)
