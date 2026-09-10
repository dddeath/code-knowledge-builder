# create_protocol_fixture

标签：#类型/代码

> 该函数构造指定历史协议版本的输出与工作区适配文件，给工作区协议块保留用户前言和结尾，并生成绑定解释器、命令入口及预期摘要的批量升级清单。 它为协议批量升级测试提供受控旧版本输入，覆盖内部根目录、工作区文件归属和宿主隐藏配置；这是测试 fixture，不是完整真实知识库的审计产物。

## 什么时候需要修改

历史协议文本、适配器路径、用户块保留或批量计划字段变化时修改此函数，并检查夹具版本与预期摘要一致。

## 在代码中的位置

[打开源码：tests/test_agent_protocol_batch.py 第 47 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_agent_protocol_batch.py:47:1)  `tests/test_agent_protocol_batch.py:47-118`

## 谁会来到这里

- [[create_protocol_fixture 等测试场景]] 汇总了本页。
