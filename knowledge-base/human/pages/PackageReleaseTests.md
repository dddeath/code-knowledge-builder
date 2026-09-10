# PackageReleaseTests

标签：#类型/代码

> 组织核心与插件发行包的结构和运行能力测试。 比较轻量与完整版内容，构建归档检查清单，验证锁定的 PDF 解析器载荷和独立插件版本；用安装后的命令检查会话入口。

## 什么时候需要修改

修改包类型边界、运行时来源或会话模块打包规则时修改对应断言。

## 在代码中的位置

[打开源码：tests/test_package_release.py 第 30 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_package_release.py:30:1)  `tests/test_package_release.py:30-116`

## 谁会来到这里

- [[PackageReleaseTests 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `PackageReleaseTests.test_core_packages_exclude_plugins_and_full_only_adds_runtime` | 比较核心轻量与完整版文件集合，断言插件排除且完整版仅增加运行时文件。 |
| `PackageReleaseTests.test_lite_manifest_retains_core_capabilities` | 构建并解压轻量包，核对核心能力清单并运行会话命令帮助作为安装冒烟检查。 |
| `PackageReleaseTests.test_full_runtime_locks_pypdf_without_expanding_lite_runtime_boundary` | 核对完整版锁定的 PDF 解析器文件、许可和摘要，并断言轻量包不带运行时。 |
| `PackageReleaseTests.test_obsidian_plugin_is_independently_versioned` | 构建独立插件归档，检查版本、完整文件清单及与核心 Skill 的分离。 |

</details>
