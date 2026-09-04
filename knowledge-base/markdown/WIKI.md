# 如何阅读 source 代码知识库

> 这是一套面向理解和修改代码的中文导航，而不是机器实体清单。

## 从哪里开始

先判断当前任务需要代码事实、历史工作记录，还是精确符号定位：

- 理解或修改代码：先打开 [[source 代码导览]]，再进入对应职责导览。
- 查找已有分析、变更、实验或会话：打开 [工作记录导览](RECORDS.md)。
- 查找经过来源和许可审阅的外部资料：打开 [参考资料导览](REFERENCES.md)。
- 精确定位源码或资料：使用机器层 `brief`，再打开返回的 Agent pack 和最窄来源范围。

代码职责入口：

- [[prototypes 职责导览]]
- [[references 职责导览]]
- [[scripts 职责导览]]
- [[tests 职责导览]]

## 页面只保留什么

- **类与函数页**：说明它做什么、何时修改、位于哪里，以及会和哪些代码协作。
- **职责聚合页**：把同一实现文件或相邻目录中的类、函数和辅助逻辑放在一起讲清楚。
- **内部细节**：访问器、简单判断、局部辅助函数和薄包装只以一句话收纳，不膨胀成独立页面。
- **自然双链**：关系写成“会使用”“由测试覆盖”“继续浏览”等阅读提示，不展示机器关系类型或计数。
- **页面类型**：每页只有一个 `#类型/...` 标签，用于区分代码、职责和边界。
- **源码入口**：带源码位置的页面可以直接打开本地编辑器中的对应行。

页面正文不展示内部 ID、版本标识、机器分类和解析器字段；这些真实性证据仍保存在机器审计层，并继续决定知识库能否完成。

## 中文描述约定

所有职责、修改时机、内部细节、关系说明以及 Agent 分析和修改记录都使用简体中文。英文只保留在专有名词、API、代码符号、命令、路径和必要技术术语中。类名和函数名无需翻译，但不得用纯英文段落代替中文解释。

## 本次页面配置

普通文件、核心文件和邻近文件最多分别生成 1、4、1 个关键实体页；每个入口最多选择 4 个核心页和 3 个邻近页。

代码页按以下顺序组织内容：overview、change_when、source_location、partial_fragments、related_code、backlinks、tests、hidden_relation_hint、appendix。附录采用 `collapsed` 展示方式。完整规范化配置保存在 `E:\knowledge_builder\self-workspace\knowledge-base.staging-fcad08af3dac\page-config.json`。

## 如何寻找修改入口

1. 从职责导览找到最接近需求的业务区域。
2. 打开相关类或函数页，先读“它做什么”和“什么时候需要修改”。
3. 沿“相关代码”和“谁会来到这里”继续浏览。
4. 在“相关测试”中确认修改后应验证的场景。
5. 只有需要实现细节时才展开“内部细节”。

## Graphify 关系导览

Graphify 会把彼此连接紧密的代码归为职责群；机器知识库先按确定性词项和章节检索选择实体，再按固定图权重扩展关系。人类版关系报告见 [项目关系导览](../graphify-out/GRAPH_REPORT.md)。

## Agent 确定性检索

Agent 默认查询 `machine/knowledge.sqlite`，不把整套人类页面或完整实体图装入上下文。`fast` 使用有界图传播，`precise` 使用固定轮次加权排序；两者都不调用向量模型。

```powershell
& PYTHON scripts\ckb.py brief --out OUTPUT "职责或资料关键词" --budget 1800 --profile fast
& PYTHON scripts\ckb.py entity --out OUTPUT "类名或函数名"
& PYTHON scripts\ckb.py neighbors --out OUTPUT "类名或函数名" --depth 2
& PYTHON scripts\ckb.py path --out OUTPUT "起点类或函数" "目标类或函数"
```

## Agent 分析与修改记录

Agent 解释代码时先读取 retrieve 产生的阅读包，再把结论保存到 `analysis`；修改内容和原因保存到 `changes`，独立失败经验和实验分别进入 `pitfalls` 与 `experiments`。这些笔记使用双链回到代码页，并在重新投影后继续保留。

## 工作记录如何查找

[工作记录导览](RECORDS.md) 会列出全部分析、变更、实验、踩坑和会话记录，并为每条记录提取一句中文说明。先按任务目的浏览，再用 Obsidian 核心搜索输入两个或三个稳定关键词；不要逐个打开目录中的文件猜测内容。

## 在 Obsidian 中打开

把 `E:\knowledge_builder\self-workspace\knowledge-base.staging-fcad08af3dac\human` 作为 vault 打开。核心搜索、图谱、反向链接、出链、标签和页面预览配置已经准备好；从 `INDEX` 或本页开始。`E:\knowledge_builder\self-workspace\knowledge-base.staging-fcad08af3dac\markdown` 是兼容镜像。

## 在 Logseq 中打开

选择知识库输出目录 `E:\knowledge_builder\self-workspace\knowledge-base.staging-fcad08af3dac`。该目录已经包含 Logseq 文件图谱所需的配置；进入图谱后从 `INDEX` 或本页开始阅读。
