# source_files

标签：#类型/代码

> `source_files` 按发行类型返回稳定排序的待归档文件集合。 它排除版本库和缓存产物，并确保 lite 包不携带 Windows 私有运行时载荷。

## 什么时候需要修改

源码布局、排除目录或 lite/full 文件边界变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/package_release.py 第 27 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/package_release.py:27:1)  `scripts/package_release.py:27-38`

## 谁会来到这里

- [[query_graph]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
