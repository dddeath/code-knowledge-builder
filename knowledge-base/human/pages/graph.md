# graph

标签：#类型/代码

> 该函数把多文件源码转换为字节并逐一解析，要求语法通过后汇集实体，再将词法引用边转换为路径和限定名组成的关系集合。 它是关系范围测试的真实解析入口，只保留 references 链接用于标注比较，稳定标识使用测试来源而不是生产仓库版本。

## 什么时候需要修改

解析实体结构、词法链接字段或测试输入编码变化时修改此函数，并检查返回关系仍可定位到具体文件与符号。

## 在代码中的位置

[打开源码：tests/test_recruitment_relation_scope.py 第 13 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_recruitment_relation_scope.py:13:1)  `tests/test_recruitment_relation_scope.py:13-23`

## 谁会来到这里

- [[graph 等测试场景]] 汇总了本页。
