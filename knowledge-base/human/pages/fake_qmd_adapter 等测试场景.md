# fake_qmd_adapter 等测试场景

标签：#类型/代码

> 该脚本按环境模式模拟 QMD 进程失败、构建输出模式漂移或查询字段漂移，返回固定身份和最小响应。 它为三组检索基准的失败检测提供可控输入，不执行真实向量检索，固定结果不用于评价实际检索质量。

## 什么时候需要修改

基准适配器模式合同或失败检测字段变化时修改此脚本，并核对各注入模式触发对应验收失败。

## 在代码中的位置

[打开源码：tests/fixtures/qmd-fixed-three-arm/fake_qmd_adapter.py 第 1 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/qmd-fixed-three-arm/fake_qmd_adapter.py:1:1)  `tests/fixtures/qmd-fixed-three-arm/fake_qmd_adapter.py:1-41`

## 谁会来到这里

- 可从 [[tests 职责导览]] 进入本页。
