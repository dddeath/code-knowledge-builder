# clickNode

标签：#类型/代码

> 将指定原生节点缩放到可见范围后，通过真实鼠标点击选择它。 读取节点 DOM 矩形计算内部点击坐标，并等待原生选择事件更新侧栏，避免直接调用选择接口替代交互。

## 什么时候需要修改

节点定位、缩放行为或宿主界面事件响应时序变化时修改。

## 在代码中的位置

[打开源码：tests/fixtures/obsidian-interactive-nodes/host-smoke.cjs 第 40 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/fixtures/obsidian-interactive-nodes/host-smoke.cjs:40:1)  `tests/fixtures/obsidian-interactive-nodes/host-smoke.cjs:40-40`

## 谁会来到这里

- [[clickNode 等测试场景]] 汇总了本页。

## 内部细节

<details><summary>查看本页收纳的 2 个辅助实现</summary>

| 代码单元 | 一句话作用 |
|---|---|
| `clickNode.box` | 保存节点内部点击坐标，供鼠标触发原生选择事件。 |
| `clickNode.box.r` | 读取指定原生节点的 DOM 矩形，用于计算实际鼠标点击位置。 |

</details>
