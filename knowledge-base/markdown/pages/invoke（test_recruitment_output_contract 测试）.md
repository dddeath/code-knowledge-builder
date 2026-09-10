# invoke（test_recruitment_output_contract 测试）

标签：#类型/代码

> 该函数包装测试命令执行，在配置证据目录时保存命令、退出码、输出及关联正文和失败审计输入，随后返回原执行结果。 它为人类输出合同回归保留可复读执行证据，不把日志写入稳定人类页面；未配置证据目录时只执行原包装命令。

## 什么时候需要修改

测试证据目录、命令输入捕获或失败审计字段变化时修改此函数，并避免把证据日志当成命令成功本身。

## 在代码中的位置

[打开源码：tests/test_recruitment_output_contract.py 第 22 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_recruitment_output_contract.py:22:1)  `tests/test_recruitment_output_contract.py:22-46`

## 谁会来到这里

- [[invoke 等测试场景（test_recruitment_output_contract 测试）]] 汇总了本页。
