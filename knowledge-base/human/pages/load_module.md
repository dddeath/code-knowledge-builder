# load_module

标签：#类型/代码

> 该函数从指定文件路径构造模块规格并执行加载，要求规格与加载器存在，返回模块对象。 它让测试直接加载隔离原型文件而不把原型安装为生产包；执行模块会触发其顶层初始化。

## 什么时候需要修改

原型文件布局或动态加载方式变化时修改此函数，并核对加载的文件路径及依赖初始化。

## 在代码中的位置

[打开源码：tests/test_ckb_semantic_vector_benchmark.py 第 19 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_ckb_semantic_vector_benchmark.py:19:1)  `tests/test_ckb_semantic_vector_benchmark.py:19-24`

## 谁会来到这里

- [[load_module 等测试场景]] 汇总了本页。
