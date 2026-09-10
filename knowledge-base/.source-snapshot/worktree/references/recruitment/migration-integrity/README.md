# 快照登记与迁移来源完整性

固定快照随知识库目录切换后，Git 登记仍指向当前快照；迁移保留记录引用的证据、V3 作者包和原文，并在目标根重新生成来源链接。

## V3 作者包保留

迁移先复用 note_contract_metadata 校验真实作者包，核对记录正文摘要、validation_context、section_evidence 及其摘要。authoring_package_inventory 返回 manifest、body.md 和实际引用的包内本地证据的角色、相对路径与 SHA-256；URI 保持历史来源标识，不作为本地文件复制。

通过预检后，只将清单中的文件归档到 OUTPUT/machine/authoring 下，以完整 manifest 摘要的短前缀定位，并用完整文件摘要检查冲突。记录的 authoring_package 改指向目标归档；包内正文、验证上下文、章节证据和摘要保持原字节，不参与通用路径重写。不复制整个外部作者工作目录。

归档文件的不可变基线按完整内容摘要保存，避免重复嵌套作者包内的长证据路径。缺失正文、manifest、本地证据，以及正文、证据、上下文或既有归档摘要漂移均使迁移失败。增量迁移和 cold-build 在创建 staging 前预检；普通历史读取不增加这一前置门。

## 快照与 reference

- 创建 detached 快照时同时锁定登记。改名时只核验和修复该快照的 gitdir 与 backlink，验证固定 commit、tree 和已跟踪文件，不执行全仓 prune。
- 相对 gitdir 深度变化时，以 r+ 原位更新既有 .git 文件，不使用截断创建、不替换文件、不修改 hidden 属性或 ACL。
- 工作记录和 gap 的明确证据字段、保留笔记的 Markdown 来源链接形成文件引用闭包。只复制被引用文件；缺失、冲突或篡改明确失败。
- references/projection.json 决定 reference 生成页归属。工作记录、学习笔记、原始 HTML/PDF/文本和保留基线不因重投影改写。
- 来源相对归档路径用于恢复遗留 staging 链接。PDF／Web 提取元数据先验证原摘要，再重定位自有路径并更新对应提取摘要；原文和文本片段不变。

## 验证入口

tests/test_recruitment_migration_provenance.py 覆盖真实 V3 record、移除外部原包和原始证据后的独立校验、连续迁移与改名、maintain、目录回滚、漂移负例，以及 Windows hidden 属性专项。

tests/test_knowledge_batch_migration.py 额外覆盖自包含 V3 输出的两次正式切换和逐层回滚；每次重新校验包文件，最终比较输出全树原字节。自包含回滚基线由首次迁移形成，不把仍依赖外部作者包的历史原始库冒充已归档基线。

实际结果与完整命令见 verification.json。Windows 运行 windows-verify.ps1，输出 windows-native-v3.json；Linux 跳过真实 hidden 属性专项不计为通过。原始验证日志保留在 verification.json 指定的机器目录，不进入知识库普通页面。

## 补丁与回滚

创建基线为 b6c36ee11efeff75021782a82babf7a5c6452276。已审阅的人类输出依赖 386b1ae756164b4647de87d3e9f230ab3961c458 通过 5ad80b0f77b59b8b3dd802172f9ae17162a4f3cf 合入本开发分支。

当前 implementation.patch 绑定 5ad80b0f77b59b8b3dd802172f9ae17162a4f3cf，只包含 V3 整合与 hidden gitfile 更新涉及的四份实现和两份测试文件。modified-files.zip 保存这六份修改后文件，patch-manifest.json 记录修改前后摘要。

回滚入口为 python rollback.py --target TARGET --bundle BUNDLE。脚本先检查补丁和目标摘要，再反向应用并复核依赖合并基线；保留此前的快照迁移修复和人类输出依赖。存在后续修改时停止，不覆盖其他工作，不切换分支、不修改 Git 登记、不接触稳定知识库。
