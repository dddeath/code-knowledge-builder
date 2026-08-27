# LLM Wiki 快速检索确定性优化与 5.1.3 交付

标签：#类型/变更

## 修改内容

把 `retrieve_machine` 的候选渲染限制为固定 overscan 窗口，改用两次批量 SQL 读取实体与章节，并加入源码路径缓存、静态检索上下文缓存、紧凑目标保留、中文三元词项、元数据固定加权和测试实体折扣。同时补充迁移目录提升后的输出路径重定位，保持不可变基线和固定源码快照原字节不动。

## 修改原因

5.1.2 冻结基准显示逐实体查询与 Windows 路径重复解析放大延迟，且长目标会在预算不足时被跳过。实现需要在不引入向量模型和 Agent 排序不确定性的前提下，提高目标源码召回并降低可见上下文与查询延迟。迁移切换时还发现 staging 绝对路径会在目录改名后失效，因此加入受固定快照验证约束的重定位步骤。

## 验证结果

十二个问题、三种路径、2400 token、一次预热和九次重复的原冻结协议保持不变。目标源码 Recall@8 达到 100%，可见上下文减少 77.28%，中位延迟 25.29 ms，P95 为 45.36 ms，零回退且结果完全确定，七项预设门全部通过。源码、自动化和迁移测试分别为 18、18、1 项全部通过；full 安装、隔离回滚、真实回滚和重新安装均已逐文件复验。

## 相关知识页

- [[retrieve_machine 与 estimated_tokens 的协作实现]]
- [[SourceLinkRenderer.uri 与 SourceLinkRenderer 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/machine_knowledge.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/machine_knowledge.py:1:1)  `scripts/ckb_core/machine_knowledge.py:1-1458`
- [打开源码：scripts/ckb_core/source_links.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/source_links.py:1:1)  `scripts/ckb_core/source_links.py:1-184`
