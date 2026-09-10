# finish_session

标签：#类型/代码

> 结束一个 active Agent 会话，将中文总结与实际工作树变化写成修改记录或会话总结，并保存最终覆盖层及完成状态。 先核验会话和总结文件，再同步源码差异；有改动时要求规定标题并选择 change，无改动时选择 session。已有检索记录可作为笔记来源，机器层未建立时明确保留等待状态，笔记通过统一记录或队列入口处理。

## 什么时候需要修改

修改会话状态、总结必需标题、工作树差异归集或笔记来源回链时，联动 start_session、_record_or_queue 和机器覆盖层同步，避免未写成记录就标记会话结束。

## 在代码中的位置

[打开源码：scripts/ckb_core/agent_maintenance.py 第 156 行](vscode://file/E:/knowledge_builder/self-workspace/source/scripts/ckb_core/agent_maintenance.py:156:1)  `scripts/ckb_core/agent_maintenance.py:156-228`

## 相关代码

- 与 [[CkbError]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[CkbError 与 DependencyError 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[build_machine_knowledge 与 estimated_tokens 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[finish_session 与 _session_directory 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。
- 与 [[record_note 与 page_tag 的协作实现]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[finish_session 与 _session_directory 的协作实现]] 汇总了本页。
