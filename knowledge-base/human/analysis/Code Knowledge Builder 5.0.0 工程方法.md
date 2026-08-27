# Code Knowledge Builder 5.0.0 工程方法

标签：#类型/分析

## 核心工程方法

### 确定性脚本判断，Agent 只做来源绑定解释

页面选择、附属实体归属、排序、关系裁剪、检索权重、上下文预算、审阅集合和完成门都由脚本固定。Agent 逐项读取固定源码并写中文解释，不重新决定重要性，从而把不确定性限制在可审计叙述层。

### 事实、机器和人类三层分离

事实层提供重建边界；机器层完整保存实体、关系、源码和过程文档；人类层只投影少量中文导航页。人类压缩不会删除事实，机器扩张也不会把实体清单倾倒给读者。

### 分节检索替代整页加载

实体说明拆成中文含义、职责、修改时机、来源核对和有界源码片段，工作记录按 Markdown 标题拆节。FTS 先命中章节，再归属来源实体并按固定关系权重扩展，因此 Agent 只读预算内章节。

### 两档算法仍保持可重复

`fast` 使用有界两跳传播，适合日常修改定位；`precise` 使用固定二十四轮加权 PageRank，适合跨模块问题。两者使用固定词法、权重、惩罚和同分排序；向量模型留到冻结 benchmark 验证下游效果与成本之后。

### 固定基线与可变工作树分离

Git blob 与 detached worktree 构成稳定基线；活动修改进入 overlay、会话和变更页。这样可一边建立长期知识基线，一边编码，并明确区分已审计事实与尚待下一提交吸收的变化。

### 分段恢复与最小返工

解析批次和审阅包各自保存状态、实体集合和证据。跨段关系在 merge 解析；失败只重跑对应批次或阶段，降低大型仓库的重复读取与 Agent 上下文压力。

### 中文是完成条件而非写作偏好

审阅提交、全局图、人类层和机器层都检查叙述字段是否包含中文。英文类名、函数名和技术术语保持源码形式，但纯英文说明不会进入完成状态。

### 证据先于状态标记

实体集合、源码范围、关系端点、双链、SQLite、投影一致性、检索预算和中文覆盖均可重新计算。三个完成标记只是审计结果，不是人工宣告。

### 生成器所有权保护长期人工知识

人类 vault 仅替换清单内生成文件；分析、修改原因、实验、踩坑和 Obsidian 工作区持续保留。机器重建与人类积累因此可以长期并存。

## 相关知识页

- [[status]]
- [[status 与 _replace_output_prefix 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/pipeline.py 第 3058 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:3058:1)  `scripts/ckb_core/pipeline.py:3058-3068`
- [打开源码：scripts/ckb_core/pipeline.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/pipeline.py:1:1)  `scripts/ckb_core/pipeline.py:1-3126`
