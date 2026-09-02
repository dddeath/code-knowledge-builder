# CKB Canvas runtime fixture

`runtime_builder.py` 只从本目录 `template/` 的 UTF-8 相对输入创建测试对象，不在 Git 中保存绝对临时根、symlink 或 junction。

常规 case 固定创建在 `%TEMP%\ckb-canvas-fixtures\CASE_ID`；每次创建前清理同名 case。builder 写入最小 `state.json`、SQLite `meta`、同 stem pack/record、人类 projection/manifest、detached source 和 schema 1 request，并在写 request 前计算真实 SHA-256。

`expected/` 保存设计 success fixture 的 canonical 示例字节；`failure-results/` 与设计目录 17 个失败结果逐文件 byte-identical。运行时生成结果按 schema、规范字节和动态根计算的 hash 断言，不把临时绝对路径反写到本目录。

Windows 长路径、根内/根外链接只在运行时创建。`runtime/success/request.json` 是自动验收命令使用的 ignored runtime，由测试准备，不进入 Git。
