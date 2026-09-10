# parse_file 与 _language 的协作实现

标签：#类型/代码

> 该模块从固定源码字节提取五种语言的文件与声明实体，记录提交、blob、字节范围和父子关系；对可保留的局部 C/C++ 语法诊断显式降低事实完整性，并将 C# 分部声明合并为带来源片段的逻辑实体。 它提供解析目录和候选链接的语法基础，而不等同于运行时调用证明；Python 使用作用域绑定解析候选引用，其他语言使用唯一名称词项候选，语义提供器在后续阶段补充更强证据。

## 什么时候需要修改

语言声明识别、名称范围、实体编号、薄声明排除、诊断降级阈值、C# 分部合并或 Python 词法绑定规则变化时修改此模块，并同时核对源码范围、警告传播和候选关系的精度边界。

## 在代码中的位置

[打开源码：scripts/ckb_core/parsers.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/parsers.py:1:1)  `scripts/ckb_core/parsers.py:1-1020`

## 相关代码

- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 主要代码单元是 [[parse_file]]。

## 谁会来到这里

- 与 [[parse_file]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 可从 [[scripts 职责导览]] 进入本页。

## 内部细节

<details><summary>查看本页收纳的 43 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `_language` | 按语言加载对应 Tree-sitter 模块并构造 Language，加载或映射失败统一转为依赖错误。 |
| `_walk` | 通过显式栈按子节点原顺序深度遍历语法树并依次产出节点。 |
| `_node_text` | 按节点字节范围切出源码并解码 UTF-8，非法字节用替代字符处理。 |
| `_byte_position` | 直接从源码字节与偏移计算一基行号和零基 UTF-8 字节列，不读取语法节点 Point。 |
| `_find_name` | 先从名字字段再遍历节点寻找标识符，返回名称与字节位置，并保留访问过的节点引用。 |
| `_public_evidence` | 依据语言的下划线、export 附近文本或访问修饰符启发式标记公开性，C/C++ 默认视为公开候选。 |
| `_single_statement_shape` | 识别访问器、单表达式体和不含控制流的单返回/调用或赋值，为薄声明返回硬排除原因。 |
| `_csharp_fallback_name` | 为 C# 索引器、访问器和运算符推导回退名称及源码位置，其他声明返回 None。 |
| `_has_ancestor` | 沿节点父链查找指定类型祖先，找到即返回真。 |
| `_cpp_function_declarator_kind` | 根据祖先上下文排除模板实例化伪函数，并将块内引用声明与真实函数形状区分。 |
| `_cpp_explicit_class_instantiation_recovery` | 只识别固定语法中显式类或结构体模板实例化的特定缺失标识符形态，返回可恢复范围。 |
| `_parse_diagnostics` | 将语法错误节点分为已知 C++ 恢复形态和未解决诊断，必要时为不可定位的根错误补充全文件诊断。 |
| `_union_size` | 合并排序后的重叠区间并累加长度，空输入返回零。 |
| `_diagnostic_contract` | 根据语言、根节点和诊断数量及覆盖比例，将解析结果判定为完整、局部缺失或不可用并返回阻断原因。 |
| `_diagnostic_overlaps` | 比较实体与诊断字节区间是否相交，零宽诊断按落点位于实体边界内判断。 |
| `syntax_warning_id` | 把提交、blob、路径及诊断类别和字节范围绑定成语法警告标识。 |
| `merge_csharp_partials` | 将同种类同限定名的 C# partial 类型合为逻辑实体，保留全部片段来源并重定向成员父级。 |
| `_python_lexical_pairs` | 按 Python 词法作用域、导入和唯一绑定解析内部引用，重绑定或未知接收者不连边，结果明确不确认运行时分派。 |
| `_python_lexical_pairs.bind` | 向作用域某个名称的绑定列表追加一个候选或未知标记。 |
| `_python_lexical_pairs.Collector` | 遍历 Python 名称、属性、导入、定义和局部作用域，收集使用点、绑定及成员写入，为保守词法解析提供上下文。 |
| `_python_lexical_pairs.Collector.__init__` | 保存当前词法作用域帧，供后续 AST 访问方法读取和更新。 |
| `_python_lexical_pairs.Collector.visit_Name` | 把名称写入或删除登记为未知绑定，把读取登记为带当前作用域的使用点。 |
| `_python_lexical_pairs.Collector.visit_Attribute` | 分别收集属性读取与成员写入，并继续遍历非简单名称的接收者表达式。 |
| `_python_lexical_pairs.Collector.visit_Global` | 将 global 声明中的名称加入当前作用域的全局声明集合。 |
| `_python_lexical_pairs.Collector.visit_Nonlocal` | 将 nonlocal 声明中的名称加入当前作用域的非局部声明集合。 |
| `_python_lexical_pairs.Collector.visit_Import` | 按别名或顶层模块名登记普通 import 的模块绑定。 |
| `_python_lexical_pairs.Collector.visit_ImportFrom` | 根据当前包和相对导入层级解析模块，登记导入名称或别名，星号导入则标记解析不确定性。 |
| `_python_lexical_pairs.Collector.definition` | 将定义绑定到已有源码实体，分别访问头部表达式和新作用域正文，并为明确实例或类方法绑定首参数接收者。 |
| `_python_lexical_pairs.Collector.visit_FunctionDef` | 将普通函数定义交给统一定义处理逻辑，建立函数作用域和源码实体绑定。 |
| `_python_lexical_pairs.Collector.visit_ClassDef` | 将类定义交给统一定义处理逻辑，建立类作用域并访问基类与正文。 |
| `_python_lexical_pairs.Collector.visit_Lambda` | 在外部作用域访问 Lambda 默认值，在新函数作用域登记参数并访问表达式体。 |
| `_python_lexical_pairs.Collector.comprehension` | 先在外层访问首个迭代源，再在独立推导式作用域访问目标、过滤条件和结果表达式。 |
| `_python_lexical_pairs.Collector.visit_NamedExpr` | 处理海象表达式时越过推导式帧把名称写入外层作用域，再访问赋值表达式。 |
| `_python_lexical_pairs.Collector.visit_ExceptHandler` | 将异常处理器绑定的名称登记为未知值，再继续访问异常处理语法节点。 |
| `_python_lexical_pairs.Collector.visit_MatchAs` | 将模式匹配捕获的名称登记为未知绑定，再继续遍历模式内容。 |
| `_python_lexical_pairs.Collector.visit_MatchMapping` | 将映射匹配的剩余项变量登记为未知绑定，再遍历该模式的子节点。 |
| `_python_lexical_pairs.new_frame` | 建立携带父作用域、所属实体、绑定集合及成员失效集合的词法帧，并继承文件和模块信息。 |
| `_python_lexical_pairs.parameters` | 将位置、关键字及可变参数名称全部登记为未知绑定，防止把参数误解为外层同名实体。 |
| `_python_lexical_pairs.enclosing` | 查找外层作用域时跳过类作用域，并将声明为全局的名称定位到最外层作用域。 |
| `_python_lexical_pairs.module_frame` | 仅在模块名称对应唯一词法帧时返回该帧，避免歧义模块参与引用解析。 |
| `_python_lexical_pairs.lookup` | 沿词法作用域查找唯一绑定，限制循环与星号导入，并继续解析显式导入的实体或子模块。 |
| `_python_lexical_pairs.resolve` | 递归解析名称及属性引用，仅接受明确的模块或类成员绑定，并排除已写入失效的成员。 |
| `lexical_links` | 合并 Python 词法绑定候选、其他语言的唯一同名词项候选和实体包含关系，生成稳定编号的链接。 |

</details>
