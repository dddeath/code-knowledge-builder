# package_showcase 与 _parse_sample 的协作实现

标签：#类型/代码

> 该文件集中实现人类可读样例集合、中文 Wiki 和展示归档。 它是 Code Knowledge Builder 中承载人类可读样例集合、中文 Wiki 和展示归档的源码边界，并连接相邻模块或测试。

## 什么时候需要修改

当人类可读样例集合、中文 Wiki 和展示归档的输入、输出、状态门或验证契约发生变化时，需要同步修改该文件并运行对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/showcase.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/showcase.py:1:1)  `scripts/ckb_core/showcase.py:1-173`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 主要代码单元是 [[package_showcase]]。

## 谁会来到这里

- [[package_showcase]] 会使用这里提供的行为。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_parse_sample` | 该附属代码负责解析命名声明并保存稳定源码范围，并把结果交给所属页面中的主流程使用。 |
| `_root_wiki` | 该附属代码负责人类可读样例集合、中文 Wiki 和展示归档，并把结果交给所属页面中的主流程使用。 |

</details>
