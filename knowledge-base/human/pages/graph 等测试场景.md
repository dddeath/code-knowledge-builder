# graph 等测试场景

标签：#类型/代码

> 该文件使用真实 Tree-sitter 解析与词法关系提取，在公开小型标注样例中核对 Python 作用域、导入别名、遮蔽和成员失效边界，并可输出精确率与召回。 它是关系误连回归与开发样例测量入口，特别防止无关测试里的同名函数改变局部调用候选；公开开发样例不是留出评价，也不代表编码成功率。

## 什么时候需要修改

Python 词法绑定、模块解析或属性写入失效规则变化时修改对应样例与断言，并保留误报和漏报分别计量。

## 在代码中的位置

[打开源码：tests/test_recruitment_relation_scope.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/test_recruitment_relation_scope.py:1:1)  `tests/test_recruitment_relation_scope.py:1-150`

## 相关代码

- 主要代码单元是 [[graph]]。

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 9 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `measurements` | 按公开关系标注样例计算真阳性、误报和漏报及精确率召回，并明确非留出评测和非编码成功率。 |
| `RecruitmentRelationScopeTests` | 用真实语法解析核对局部绑定、导入、遮蔽和成员写入失效，防止无关同名函数形成伪引用。 |
| `RecruitmentRelationScopeTests.test_labeled_parser_cases` | 逐个比较公开标注样例中指定调用者的实际目标集合与期望集合。 |
| `RecruitmentRelationScopeTests.test_unrelated_tests_do_not_change_local_call` | 加入无关测试中的同名辅助函数，要求原文件局部调用关系完全不变。 |
| `RecruitmentRelationScopeTests.test_additional_binding_boundaries` | 覆盖注解、闭包表达式、赋值表达式、异常模式绑定、全局写入和静态接收者等额外作用域边界。 |
| `RecruitmentRelationScopeTests.test_import_path_is_not_an_arbitrary_module_suffix` | 要求导入模块按真实模块路径匹配，不把任意目录下同名文件后缀当作导入目标。 |
| `RecruitmentRelationScopeTests.test_attribute_store_and_delete_invalidate_only_matching_member` | 分别写入、删除和增量赋值模块及类成员，要求仅匹配成员在当前作用域失效而保留其他调用。 |
| `RecruitmentRelationScopeTests.test_attribute_invalidation_reaches_nested_scope_not_unrelated_receiver` | 要求成员写入失效传播到嵌套作用域，但不影响另一未修改调用者的同名成员引用。 |
| `RecruitmentRelationScopeTests.test_real_maintenance_append` | 解析实际维护模块和管理测试文件，要求列表追加操作不误连到测试中的同名嵌套函数。 |

</details>
