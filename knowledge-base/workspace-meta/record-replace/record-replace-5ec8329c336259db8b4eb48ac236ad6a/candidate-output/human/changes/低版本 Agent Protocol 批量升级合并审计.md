# 低版本 Agent Protocol 批量升级合并审计

标签：#类型/变更

## 修改内容

系统现在可以按显式清单批量升级多个既有知识库的 Agent Protocol。每个知识库固定来源版本、目标版本、Harness、Python、CKB 和允许写入的工作区，并提供计划、执行、状态、审计和逐库回滚。升级只作用于协议管理区、跨 Harness 适配器、output contract 和对应机器状态，不重建源码图谱，也不改写知识页面正文。

## 修改时间

源码能力于 2026 年 9 月 1 日完成集成；本说明绑定到 2026 年 9 月 2 日完成同步的稳定知识库版本。

## 修改原因

多个旧知识库分布在不同 Harness 和工作区时，逐库更新容易遗漏管理文件，也难以证明用户自有内容、BOM、换行和固定图谱保持不变。旧锁如果只依据时间判断，还可能把存活进程持有的对象误当成可回收锁。

## 实现概述

版本矩阵保存可验证的历史协议输出与允许升级路径；managed block 只替换唯一的 CKB 管理区。每个知识库使用独立备份、状态和 owner token，失败时只恢复当前项目。锁的所有权同时核对进程、启动身份、host 和 token，不以单一超时覆盖活跃持有者。

## 关联特性

该变化与 Agent Policy、output contract、Harness 适配器、完整知识库批量迁移和维护结果相连。协议批量升级只更新接入合同；固定源码图谱和完整知识层迁移仍由独立迁移能力负责，两者不会互相替代。

## 当前结果

已验证真实历史协议重构、单库失败后的隔离恢复、续跑、存活与死亡锁、PID 复用、损坏记录、计划后漂移和子集回滚。多库场景中，升级前后的固定图谱和两份机器索引摘要保持一致，管理区外字节得到保留。

## 适用边界

批量升级依赖清单中的明确版本和可用 runtime，且只处理清单列出的知识库。Windows 状态与备份根需要预留足够路径长度；所有者无法确认或升级后管理区继续发生修改时，回滚会停止并报告冲突。

## 深入阅读

需要复查协议版本矩阵、managed block 或锁所有权时，从“audit_agent_protocol 与 _default_python 的协作实现”进入，并让 Agent 按目标知识库定位计划、审计和回滚测试。

## 相关知识页

- [[audit_agent_protocol 与 _default_python 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/agent_protocol.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_protocol.py:1:1)  `scripts/ckb_core/agent_protocol.py:1-507`
