# render_human_maintenance_prompt

标签：#类型/代码

> 把一个已登记的人类维护 action 与通过验证的参数渲染为中文执行 Prompt，包含执行顺序、确认点、停止条件和结构化交付模板。 实际命令、外部依赖和待完成功能分别呈现，不把后两者伪装成可执行现有能力；验收与回滚要求依据有效参数重新计算，最终模板要求填写实际输入、输出和退出状态。

## 什么时候需要修改

维护 action 的参数、步骤映射、条件能力或验收标准变化时，联动 invocation 校验、active_command_steps、有效要求计算和交付模板，保持 Prompt 与审计合同一致。

## 在代码中的位置

[打开源码：scripts/ckb_core/human_maintenance_prompts.py 第 1936 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/human_maintenance_prompts.py:1936:1)  `scripts/ckb_core/human_maintenance_prompts.py:1936-2009`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[render_human_maintenance_prompt 与 ParameterSpec 的协作实现]] 汇总了本页。
