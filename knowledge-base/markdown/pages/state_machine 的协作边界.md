# state_machine 的协作边界

标签：#类型/边界

> 这里汇集当前扫描范围之外、但与所选功能直接协作的代码。

## 本次未继续展开的代码

- **_replay**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/state_machine.py:20-37`。
- **_classify**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/state_machine.py:40-130`。
- **audit_assertions**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/state_machine.py:133-157`。
- **audit_database**：位于 `prototypes/ckb-tag-navigation/ckb_tag_navigation/state_machine.py:160-169`。

## 相关代码

- 实现时会用到 [[_Transport.close]]。
- 实现时会用到 [[append]]。
- 实现时会用到 [[assertions]]。
- 实现时会用到 [[contracts 的协作边界（959fe0e0）]]。
- 实现时会用到 [[ingest 与 connect 的协作实现]]。

## 谁会来到这里

- [[TagNavigationCanvasCompatibilityTests]] 会使用这里提供的行为。
- [[TagNavigationProjectionTests]] 会使用这里提供的行为。
- [[TagNavigationStateMachineTests]] 会使用这里提供的行为。
