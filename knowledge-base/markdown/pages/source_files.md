# source_files

标签：#类型/代码

> `source_files` 枚举允许进入发行包的 Skill 文件，并按发行类型决定是否包含 Windows 离线运行时。 它过滤 `.git`、Python 缓存和字节码，防止源码仓库元数据或测试副产物进入用户安装包。

## 什么时候需要修改

当项目目录结构、缓存种类或 lite/full 文件边界变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/package_release.py 第 27 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/package_release.py:27:1)  `scripts/package_release.py:27-38`

## 谁会来到这里

- [[query_graph]] 会使用这里提供的行为。
- [[retrieve_machine 与 estimated_tokens 的协作实现]] 会使用这里提供的行为。
- [[source_files 与 sha256 的协作实现]] 汇总了本页。

## 相关测试

- [[CodeKnowledgeBuilderTests]]
