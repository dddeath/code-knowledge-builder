# add_git_bootstrap_arguments

标签：#类型/代码

> `add_git_bootstrap_arguments` 登记可选 Git 初始化、首次提交信息和作者参数。 它把非 Git 目录的显式初始化能力限制在首次构建入口，避免隐式改动仓库。

## 什么时候需要修改

Git 启动授权、提交元数据或参数名称变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 104 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:104:1)  `scripts/ckb.py:104-112`

## 相关代码

- 实现时会用到 [[parser]]。
- 实现时会用到 [[status 与 _replace_output_prefix 的协作实现]]。

## 谁会来到这里

- [[add_initial_arguments]] 会使用这里提供的行为。
- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 汇总了本页。
- [[parser]] 会使用这里提供的行为。

## 相关测试

- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
