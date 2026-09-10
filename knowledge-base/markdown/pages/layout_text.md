# layout_text

标签：#类型/代码

> 该函数将文字检测框按行聚合，估计字符宽度和常见行间距，以较大竖向间隔分块，再按相对横坐标插入空格重建文本。 它承担 OCR 输出中可见列间距和相对代码缩进的近似恢复，不更改识别文字本身；块内以最左位置为基线，同行多个框至少用两个空格分隔。

## 什么时候需要修改

行聚合、字符宽度估计、分块阈值或间距舍入规则变化时修改此函数，并检查表格续行与代码缩进的单独评分。

## 在代码中的位置

[打开源码：tests/real_ocr_adapter.py 第 77 行](vscode://file/E:/knowledge_builder/self-workspace/source/tests/real_ocr_adapter.py:77:1)  `tests/real_ocr_adapter.py:77-112`

## 相关代码

- 与 [[layout_text 等测试场景]] 存在待核验的词法关联；是否调用或依赖需查看源码。

## 谁会来到这里

- [[layout_text 等测试场景]] 汇总了本页。
