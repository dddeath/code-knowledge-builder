# PackageReleaseTests

标签：#类型/代码

> 代码单元 `test_core_packages_exclude_plugins_and_full_only_adds_runtime`负责验证 Lite、Full 和插件发行边界以及 PDF 运行时依赖清单。 它属于发行物内容、体积责任和许可证边界的回归保护，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当发行类型、运行时锁、依赖或插件独立版本变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：tests/test_package_release.py 第 30 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_package_release.py:30:1)  `tests/test_package_release.py:30-116`

## 相关代码

- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[main 与 sha256 的协作实现]]。
- 实现时会用到 [[source_files]]。
- 实现时会用到 [[source_files 与 sha256 的协作实现]]。

## 谁会来到这里

- [[PackageReleaseTests 等测试场景]] 汇总了本页。
- [[main 与 sha256 的协作实现]] 关联到这里的验证场景。
- [[source_files 与 sha256 的协作实现]] 关联到这里的验证场景。

## 内部细节

<details><summary>查看本页收纳的 4 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `PackageReleaseTests.test_core_packages_exclude_plugins_and_full_only_adds_runtime` | 该测试验证“core packages exclude plugins…”场景，保护发行边界回归验证的预期结果与失败边界。 |
| `PackageReleaseTests.test_lite_manifest_retains_core_capabilities` | 该测试验证“lite manifest retains core ca…”场景，保护发行边界回归验证的预期结果与失败边界。 |
| `PackageReleaseTests.test_full_runtime_locks_pypdf_without_expanding_lite_runtime_boundary` | 该测试验证“full runtime locks pypdf with…”场景，保护发行边界回归验证的预期结果与失败边界。 |
| `PackageReleaseTests.test_obsidian_plugin_is_independently_versioned` | 该测试验证“obsidian plugin is independen…”场景，保护发行边界回归验证的预期结果与失败边界。 |

</details>
