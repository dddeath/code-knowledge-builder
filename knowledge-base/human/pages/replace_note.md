# replace_note

标签：#类型/代码

> `replace_note` 位于 `scripts/ckb_core/record_replace.py` 第 930-991 行，本页用固定源码范围说明它如何完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。 `replace_note` 负责在工作记录正文替换、候选验证、原子 promotion 和回滚中完成工作记录正文替换、候选验证、原子 promotion 和回滚中的局部职责。

## 什么时候需要修改

当 `scripts/ckb_core/record_replace.py` 中 `replace_note` 的输入合同、状态转换、输出字段或失败边界变化时，应更新本页并重跑对应测试。

## 在代码中的位置

[打开源码：scripts/ckb_core/record_replace.py 第 930 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/record_replace.py:930:1)  `scripts/ckb_core/record_replace.py:930-991`

## 相关代码

- 实现时会用到 [[CkbError]]。
- 实现时会用到 [[CkbError 与 DependencyError 的协作实现]]。
- 实现时会用到 [[audit_operation_journal 与 _root 的协作实现]]。
- 实现时会用到 [[build_case 等测试场景]]。
- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[replace_note 与 RecordReplaceLockError 的协作实现]]。

## 谁会来到这里

- [[RecordReplaceTests]] 会使用这里提供的行为。
- [[replace_note 与 RecordReplaceLockError 的协作实现]] 汇总了本页。

## 相关测试

- [[RecordReplaceTests]]
