# deployment_plan

标签：#类型/代码

> `deployment_plan` 是 `scripts/ckb_core/runtime.py` 中负责根据锁定运行时清单生成所需组件、来源和部署动作的函数。 它按源码所示的参数、条件分支和数据结构完成根据锁定运行时清单生成所需组件、来源和部署动作，并把确定结果交给调用方或后续审计、索引、投影阶段。

## 什么时候需要修改

当scripts/ckb_core/runtime.py 的职责的输入格式、状态规则、错误处理或输出契约变化时，需要修改该代码单元并复核对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/runtime.py 第 26 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/runtime.py:26:1)  `scripts/ckb_core/runtime.py:26-67`

## 相关代码

- 实现时会用到 [[deployment_plan 与 skill_root 的协作实现]]。
- 实现时会用到 [[doctor_report 与 _version_matches 的协作实现]]。

## 谁会来到这里

- [[deployment_plan 与 skill_root 的协作实现]] 汇总了本页。
