# source_files 与 sha256 的协作实现

标签：#类型/代码

> 该文件构建可复验的 lite 与 full-win-x64 Skill 发行包。 它校验锁定运行时、筛选源码、生成逐文件清单，并验证 ZIP CRC 与归档内清单。

## 什么时候需要修改

版本号、载荷锁、发行文件规则或归档验证要求变化时，需要修改该文件。

## 在代码中的位置

[打开源码：scripts/package_release.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/package_release.py:1:1)  `scripts/package_release.py:1-142`

## 相关代码

- 实现时会用到 [[parser]]。
- 主要代码单元是 [[source_files]]。
- 实现时会用到 [[status]]。

## 谁会来到这里

- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `sha256` | 流式计算发行文件的 SHA-256 校验值。 |
| `validate_full_payload` | 核对 full 运行时载荷的路径、大小、哈希和必需成员。 |
| `build` | 按 lite 或 full 规则收集文件、生成清单并写出可复验 ZIP。 |
| `main` | 解析发行打包参数并输出构建结果。 |

</details>
