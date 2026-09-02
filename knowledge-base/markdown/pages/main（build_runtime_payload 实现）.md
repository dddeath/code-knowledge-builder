# main（build_runtime_payload 实现）

标签：#类型/代码

> 代码单元 `main`负责构建并核验 Windows 完整运行时归档，包括 PDF 解析依赖、许可证和可重复载荷清单。 它属于完整发行包的运行时边界与可回滚部署依据，当前说明只覆盖所列固定源码范围。

## 什么时候需要修改

当运行时依赖、归档成员、锁版本或完整性规则变化时，应同步复查本页及其直接关联测试。

## 在代码中的位置

[打开源码：scripts/build_runtime_payload.py 第 142 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/build_runtime_payload.py:142:1)  `scripts/build_runtime_payload.py:142-153`

## 相关代码

- 实现时会用到 [[ckb_canvas 的协作边界]]。
- 实现时会用到 [[parser]]。

## 谁会来到这里

- [[main 与 sha256 的协作实现]] 汇总了本页。
