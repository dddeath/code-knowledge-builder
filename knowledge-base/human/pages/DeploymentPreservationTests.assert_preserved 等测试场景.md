# DeploymentPreservationTests.assert_preserved 等测试场景

标签：#类型/代码

> 验证 Obsidian 插件升级只替换包文件而保留用户状态，并覆盖失败恢复与占用文件。 建立临时库和字节快照，运行模拟故障、真实发行包双部署入口及 Windows 原生共享句柄用例；不把它当作真实用户库的界面验收。

## 什么时候需要修改

调整升级保留、原位复制回退、部分写入恢复或发行部署入口时修改。

## 在代码中的位置

[打开源码：tests/test_obsidian_deployment_preservation.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_obsidian_deployment_preservation.py:1:1)  `tests/test_obsidian_deployment_preservation.py:1-162`

## 相关代码

- 主要代码单元是 [[DeploymentPreservationTests.assert_preserved]]。

## 谁会来到这里

- 与 [[DeploymentPreservationTests.assert_preserved]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 16 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `tree` | 以相对路径到原始字节的映射拍摄测试目录文件快照。 |
| `DeploymentPreservationTests` | 验证插件升级保留用户状态，并覆盖实际发行包、写入失败与 Windows 占用语义。 |
| `DeploymentPreservationTests.setUp` | 建立新旧包、用户设置、白板和其他插件，注册新包并保存升级前字节快照。 |
| `DeploymentPreservationTests.deploy` | 使用测试库及测试注册文件调用核心插件部署入口。 |
| `DeploymentPreservationTests.test_normal_upgrade_preserves_settings_user_files_canvas_and_other_plugins` | 验证普通升级更新声明包文件，同时保留设置、白板与其他插件。 |
| `DeploymentPreservationTests.test_actual_distribution_core_and_independent_deploy_preserve_user_state` | 分别运行实际发行包的核心和独立部署入口，核对包文件与用户状态。 |
| `DeploymentPreservationTests.test_replace_denied_falls_back_to_declared_file_copy` | 模拟重命名权限错误，断言部署切换原位复制并保留用户状态。 |
| `DeploymentPreservationTests.test_partial_copy_failure_restores_old_package_and_config` | 注入部分复制失败，断言旧包与配置完整恢复到升级前目录快照。 |
| `DeploymentPreservationTests.test_partial_copy_failure_restores_old_package_and_config.denied` | 仅对样式文件注入重命名失败，其他目标调用原始替换操作。 |
| `DeploymentPreservationTests.test_partial_copy_failure_restores_old_package_and_config.partial` | 首次复制样式文件时写入残片后抛错，后续复制沿用原始实现以测试恢复。 |
| `DeploymentPreservationTests.test_invalid_enabled_list_fails_before_package_update` | 写入非列表启用配置，断言部署在修改包文件前失败且目录字节不变。 |
| `DeploymentPreservationTests.test_absent_optional_package_file_removed_but_user_file_preserved` | 移除新包的可选构建记录，断言升级删除对应旧文件但保留用户文件。 |
| `DeploymentPreservationTests.hold_windows` | 用指定共享标志打开 Windows 文件或目录，并返回待关闭的原生句柄。 |
| `DeploymentPreservationTests.test_real_windows_open_directory_upgrade` | 持有实际 Windows 目录句柄期间升级，断言用户状态保留。 |
| `DeploymentPreservationTests.test_real_windows_file_deny_delete_allows_copy_fallback` | 持有拒绝删除但允许写入的文件句柄，验证原位复制回退与新包字节。 |
| `DeploymentPreservationTests.test_real_windows_file_deny_write_restores_prior_files` | 持有拒绝写入的样式文件句柄，断言部署报错并恢复先前已更新的文件。 |

</details>
