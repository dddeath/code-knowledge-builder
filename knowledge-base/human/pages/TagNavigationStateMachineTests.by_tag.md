# TagNavigationStateMachineTests.by_tag

标签：#类型/代码

> 该方法从当前审计结果中返回首个标签名称完全匹配的结果。 它为状态机测试简化指定标签的断言入口，标签不存在时让迭代异常暴露缺失。

## 什么时候需要修改

审计结果结构或标签唯一性约定变化时修改此方法，并核对返回对象确为目标标签。

## 在代码中的位置

[打开源码：tests/test_ckb_tag_navigation_state_machine.py 第 36 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_tag_navigation_state_machine.py:36:1)  `tests/test_ckb_tag_navigation_state_machine.py:36-37`

## 谁会来到这里

- [[TagNavigationStateMachineTests.by_tag 等测试场景]] 汇总了本页。
