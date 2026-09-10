# git（test_management_agent 测试）

标签：#类型/代码

> 该函数在指定管理测试仓库运行 Git 子命令，捕获 UTF-8 输出并在非零退出时抛出错误，成功返回去除首尾空白的标准输出。 它为管理 Agent 测试统一提供提交和仓库状态查询结果，命令失败不会被当作有效标识返回。

## 什么时候需要修改

测试 Git 参数或输出处理约定变化时修改此函数，并检查失败状态被明确传播。

## 在代码中的位置

[打开源码：tests/test_management_agent.py 第 37 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_management_agent.py:37:1)  `tests/test_management_agent.py:37-47`

## 谁会来到这里

- [[git 等测试场景（test_management_agent 测试）]] 汇总了本页。
