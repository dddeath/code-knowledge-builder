# fixture_output

标签：#类型/代码

> 该函数构造规范关键词请求，设置指定夹具模式后执行测试提供器，返回捕获的标准输出。 它为协议校验测试提供真实子进程传输路径，非零退出不在此函数中抛错，具体输出和失败由测试调用方判定。

## 什么时候需要修改

夹具命令、请求格式或环境模式变化时修改此函数，并检查输入请求仍绑定同一规范问题身份。

## 在代码中的位置

[打开源码：tests/test_keyword_fallback.py 第 47 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_keyword_fallback.py:47:1)  `tests/test_keyword_fallback.py:47-58`

## 谁会来到这里

- [[fixture_output 等测试场景]] 汇总了本页。
