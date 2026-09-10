# invoke 等测试场景（test_recruitment_output_contract 测试）

标签：#类型/代码

> 该文件在真实生成的知识库投影和记录上验证人类输出合同，覆盖缓存审计不能掩盖正文漂移、源码快照失败、旧事实查询、来源候选不确定性及 V3 证据披露。 它将受控写入和维护门串成回归场景，正文保留有用技术摘要但排除完整测试日志和命令，作者包机器证据另存且替换必须重新验证。

## 什么时候需要修改

人类可读性、历史例外、作者包替换或词法候选显示变化时修改此文件，并分别检查原文未改和当前缺陷确实被重新发现。

## 在代码中的位置

[打开源码：tests/test_recruitment_output_contract.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_recruitment_output_contract.py:1:1)  `tests/test_recruitment_output_contract.py:1-271`

## 相关代码

- 主要代码单元是 [[invoke（test_recruitment_output_contract 测试）]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 14 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `RecruitmentOutputContractTests` | 在实际投影与记录上验证人类合同、快照和新鲜度边界，覆盖旧审计失效、机器证据分离及候选关系不确定性。 |
| `RecruitmentOutputContractTests.setUpClass` | 建立临时多语言仓库，完成初始化、审阅、合并和投影，作为人类输出合同测试的共享基线。 |
| `RecruitmentOutputContractTests.tearDownClass` | 清理人类输出合同测试类拥有的临时目录。 |
| `RecruitmentOutputContractTests.test_old_passed_report_does_not_hide_changed_output` | 向现有人类页注入测试总数，要求维护重新发现泄漏而不是信任旧通过报告，最后恢复原页面。 |
| `RecruitmentOutputContractTests.test_snapshot_failure_is_reported_not_hidden` | 把固定快照路径改为缺失目录，要求维护显式报告快照检查失败，随后恢复状态文件。 |
| `RecruitmentOutputContractTests.test_newer_head_is_stale_but_query_remains_available` | 推进活动仓库提交后要求旧事实标记过期，但固定快照维护仍通过且紧凑检索可用。 |
| `RecruitmentOutputContractTests.test_record_rejects_l4_and_vague_copy_before_page_write` | 向记录正文注入完整命令、测试总数、空泛说明和无目的链接，要求写页前拒绝。 |
| `RecruitmentOutputContractTests.test_record_allows_useful_technical_summary_and_replace_rechecks` | 允许含适用边界的技术摘要写入，再用泄漏测试明细的替换正文验证旧页被保留。 |
| `RecruitmentOutputContractTests.test_actual_navigation_does_not_expose_commands_or_configuration` | 核对实际首页和阅读方法不暴露完整命令或页面配置，并保留职责阅读章节。 |
| `RecruitmentOutputContractTests.test_candidate_is_not_confirmed_dependency` | 核对词法候选关系用待核验措辞，而语言服务调用证据可使用明确调用表述。 |
| `RecruitmentOutputContractTests.test_new_projection_rejects_vague_prose_without_rewriting_source_reviews` | 在副本投影注入空泛中文，要求新合同报错，只有未升级历史页转为提示，原始审阅图不被改写。 |
| `RecruitmentOutputContractTests.test_graphify_advisory_is_exact_and_never_exempts_new_outputs` | 要求图导览历史命令例外精确限定，新增测试总数或其他人类页中的同命令仍触发泄漏错误。 |
| `RecruitmentOutputContractTests.test_v3_package_record_and_replace_keep_machine_evidence_and_recheck` | 创建并替换真实 V3 记录，要求机器证据留在作者包，阻止旧式降级，并在双镜像同错时重新发现章节缺失。 |
| `RecruitmentOutputContractTests.test_actual_projection_keeps_lexical_candidates_uncertain` | 在隔离图中仅设置词法候选链接，要求实际 Markdown 渲染保留待核验说明而不宣称确认依赖。 |

</details>
