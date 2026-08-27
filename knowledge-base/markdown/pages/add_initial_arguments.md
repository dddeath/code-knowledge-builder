# add_initial_arguments

标签：#类型/代码

> `add_initial_arguments` 为首次构建命令登记仓库、输出、范围、格式和语言选项。 它复用统一参数定义，保证 `init` 等入口采用一致的固定快照输入契约。

## 什么时候需要修改

初始化参数、局部扫描选项或 Git 启动方式变化时，需要修改该函数。

## 在代码中的位置

[打开源码：scripts/ckb.py 第 80 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb.py:80:1)  `scripts/ckb.py:80-95`

## 相关代码

- 实现时会用到 [[add_git_bootstrap_arguments]]。
- 实现时会用到 [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]]。
- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[add_initial_arguments 与 add_git_bootstrap_arguments 的协作实现]] 汇总了本页。
- [[parser]] 会使用这里提供的行为。

## 相关测试

- [[MigrationTest]]
- [[execute 等测试场景]]
- [[main（generate_large_fixture 测试）]]
