# C++ 解析与 SCons 回退合并审计

标签：#类型/变更

## 修改内容

C++ 解析现在能够区分预处理区域、块内声明、模板显式实例化和真实函数或类型实体。在缺少 `compile_commands.json` 时，系统只读取受支持的 `SConstruct`、`SConscript` 构建证据，得到唯一语言标准时用于解析回退；证据缺失或冲突时使用固定默认值，并把精度标为 `bounded-approximate`。

## 修改时间

本说明绑定到 2026 年 9 月 2 日稳定知识库所采用的固定源码版本。

## 修改原因

此前异常预处理片段、块内直接初始化声明和部分模板显式实例化可能产生误报或伪实体；SCons 项目没有 compilation database 时也缺少可复查的语言标准来源。修改的目标是减少错误实体，同时明确回退结果不能支撑缺失性推断。

## 实现概述

解析器先用语法结构判断预处理区域与块内声明，再只对 pinned Tree-sitter 已确认缺失的完整 `template class` 或 `template struct` 节点形状执行受限恢复。Provider 优先使用现有 compilation database；只有该入口不存在时才读取受支持的 SCons 文件，并保存真实子进程退出状态和证据精度。

## 关联特性

该变化同时影响 C/C++ 实体抽取、构建证据选择、Provider 精度标记和后续知识图谱审阅。`exact` 路径继续由 compilation database 决定，SCons 回退不会覆盖它；`bounded-approximate` 结果也不会被后续页面解释为完整源码事实。

## 当前结果

已验证的场景包括有效与缺失闭合的预处理区域、块内 `const T &x(expr);` 声明、模板定义与显式实例化、SCons 唯一或冲突标准、缺失头文件负例，以及 C/C++ 的 exact 与 bounded Provider 路径。有效声明不再生成伪函数，未闭合和其他 ERROR/MISSING 形状继续报告失败。

## 适用边界

SCons 回退只覆盖受支持构建文件中的静态证据，不执行构建脚本，也不声称恢复任意 Tree-sitter 错误。没有唯一构建证据时使用固定默认值；处于 `bounded-approximate` 的结果不允许据此断言某个实体不存在。

## 深入阅读

需要复查解析分支、声明归属或证据精度时，从“parse_file 与 _language 的协作实现”进入，再让 Agent 按当前固定源码范围定位相应解析与 Provider 测试。

## 相关知识页

- [[parse_file 与 _language 的协作实现]]

## 源码入口

- [打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-719`
