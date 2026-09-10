# 对话绑定管理 Agent 合并审计

标签：#类型/变更

## 修改内容

系统现在可以把一个 Harness 对话绑定到明确的 Code Knowledge Builder 项目身份，并在每次请求时生成当前管理上下文。绑定后可以查看状态、取得管理 Prompt、创建独立开发任务、审阅交付和解除绑定；任务审阅只给出是否满足合并条件，不代替管理任务执行合并。

## 修改时间

本说明绑定到 2026 年 9 月 2 日稳定知识库所采用的固定源码版本。

## 修改原因

跨对话管理项目时，如果项目身份、集成基线和能力边界只存在于临时 Prompt 中，容易复用过期状态或把不同项目混为一体。修改的目标是保存最小规范身份，并在派发和审阅时重新核对当前仓库与知识库状态。

## 实现概述

管理注册表只保存 Harness ID、opaque conversation ID、规范化路径、集成分支与绑定 HEAD、生命周期时间和能力字段。`status` 与 `context` 会重新读取分支、工作树、feedback、知识索引和维护状态；`task-create` 固定基线并建立独立 branch/worktree，`task-review` 在最终 HEAD 上运行登记测试并检查交付与工作树状态。

## 关联特性

该变化与 Agent Policy、紧凑检索、知识库维护、Harness 能力声明和独立 worktree 派发相连。各 Harness 分别声明 binding、Prompt injection、事件同步和任务派发能力；尚未自动注入的入口保持 manual-context，不会被描述成已经自动接管对话。

## 当前结果

已验证重复绑定幂等、跨项目冲突、解除绑定后的审计保留、并发绑定与解除、注册表恢复、隐私字段过滤、任务创建与审阅，以及不执行合并的 ready 结果。每次上下文读取均使用当前状态，旧的 ready 结论不会直接复用。

## 适用边界

该能力提供 Harness-neutral 的管理身份、上下文和派发准备，不保存原始对话、Prompt、assistant 文本、凭据、token 或 transcript 路径。真实 Codex 新任务仍由 Codex App 创建；管理接口本身不合并分支，也不把 manual-context 解释为自动 Prompt 注入。

## 深入阅读

需要复查注册表边界、当前上下文或派发条件时，从“ingest_event 与 default_registry_path 的协作实现”进入，并让 Agent 继续定位 management 相关接口与测试场景。

## 相关知识页

- [[ingest_event 与 default_registry_path 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/automation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/automation.py:1:1)  `scripts/ckb_core/automation.py:1-1783`
