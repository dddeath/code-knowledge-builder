# source_files 与 sha256 的协作实现

标签：#类型/代码

> 该代码页汇总 lite 与 full-win-x64 发行包的可复现打包、运行时锁定校验、包内清单和 CRC 复核。 它只收集 Skill 交付文件，确定性排除 `.git`、缓存与字节码，并在 full 包中核对离线运行时载荷后写入版本化 ZIP。

## 什么时候需要修改

当发行版本、排除边界、运行时载荷结构、包内清单或 ZIP 验证规则变化时，需要修改本页并重新检查两个发行包。

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
| `sha256` | 以分块读取方式计算大文件 SHA-256，供载荷锁定和发行包校验复用。 |
| `validate_full_payload` | 核对 full 运行时载荷的路径、大小、摘要和必需成员是否符合锁定清单。 |
| `build` | 收集发行文件、生成逐文件清单、写入可复现 ZIP，并复查 CRC 与内嵌清单一致性。 |
| `main` | 解析发行类型和输出目录，依次构建请求的发行包并返回机器可读结果。 |

</details>
