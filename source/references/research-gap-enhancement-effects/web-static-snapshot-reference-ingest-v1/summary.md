# 静态 Web 快照 reference 吸收结果

## 结果

CKB reference 层现在提供两个相互独立的显式入口：

- `reference web-snapshot` 只读取调用者提供的本地响应正文和 HTTP 元数据，不访问网络；
- `reference web-fetch` 只在调用者显式选择该命令时抓取 HTTP/HTTPS URL。

两条路径都归档原始响应正文，记录重定向后的最终 URL、获取时间、最终状态码、Content-Type、响应头、原始快照 SHA-256、正文快照 SHA-256、正文边界、排除区域和正文片段来源行范围。抓取或校验成功后状态仍为 `pending-agent-review`，不会替代现有 `reference review`、`reference audit` 和 `reference rollback` 门禁。

## 输入协议

离线导入调用者提供的快照：

```powershell
& PYTHON scripts\ckb.py reference web-snapshot `
  --out OUTPUT `
  --snapshot SNAPSHOT.html `
  --source-root LOCAL_INPUT_ROOT `
  --requested-url "https://example.test/start" `
  --final-url "https://example.test/article" `
  --retrieved-at "2026-09-05T01:02:03Z" `
  --status-code 200 `
  --content-type "text/html; charset=utf-8" `
  --response-header 'ETag:"fixture-v1"' `
  --title "网页快照资料" `
  --origin "调用者提供的静态 HTTP 快照" `
  --license "CC0-1.0"
```

显式实时抓取：

```powershell
& PYTHON scripts\ckb.py reference web-fetch `
  --out OUTPUT `
  --url "https://example.test/article" `
  --timeout-seconds 20 `
  --max-response-bytes 2097152 `
  --title "实时网页资料" `
  --origin "显式实时 URL 抓取" `
  --license "CC0-1.0"
```

普通 `reference ingest` 继续只接收本地 Markdown、TXT 和 PDF，不会根据后缀或内容自动切换到 Web 抓取。

## 抽取与审阅边界

- 仅接受最终状态为 2xx 且 Content-Type 为 `text/html` 或 `application/xhtml+xml` 的响应；默认响应上限为 2 MiB，默认超时为 20 秒。
- `script`、`style`、`noscript`、`template`、`svg`、`header`、`footer`、`aside`、`nav` 和导航类 ARIA role 不进入正文；每个排除区域保留标签、原因和原始 HTML 行范围。
- 每个正文片段记录结构标签、抽取文本、原始 HTML 行范围和对应行文本哈希。
- 审阅主张必须提交 extraction manifest 中的 `fragment_id`，并逐字匹配归档 HTML 的一基闭区间行范围。
- 相同标题、来源、最终 URL、许可和原始正文重复导入返回原记录；同一来源内容漂移要求 `--revision-of`；不同 URL 的相同正文建立 `duplicate_content_of` 关系。
- `Set-Cookie`、`WWW-Authenticate` 和 `Proxy-Authenticate` 不写入响应头记录，遗漏项名称保留在 `omitted_response_headers`。

## 实际结果

固定成功样例包含 380 字节原始 HTML、2 个正文片段和 6 个排除区域：

- 原始快照 SHA-256：`bcf726e6d73fbcc6854726040f7148bc996ad1e270d7b6a7436b730b79fac34e`
- 正文快照 SHA-256：`d78bbc7716f1184c6ad0d382e80350882ee2c323996976717fab99c460741ed5`
- 成功导入后的审阅状态：`pending-agent-review`

最终验证共通过 16 项测试：8 项 Web 测试、7 项 PDF reference 回归和 1 项文本 reference 全流程回归。失败样例覆盖非 HTML、响应过大、编码错误、超时、网络不可用、重复 URL/内容、快照漂移以及网络失败不污染既有 reference；测试失败数为 0。

## 证据与回滚

- `verification-record.json`：命令、输入、完整输出、退出状态和实际指标；
- `success-sample.json`、`failure-samples.json`：固定成功样例与失败状态；
- `modified-artifacts.zip`：修改后的实现与测试文件；
- `implementation.patch`、`patch-verification.json`：可重放补丁及基线克隆复放结果；
- `artifact-verification.json`：ZIP 重开和文件 SHA-256 比对；
- `rollback-verification.json`：隔离克隆中的实际 `-Apply` 回滚与基线比对；
- `rollback.ps1`：先无参数执行预检，再以 `-Apply` 将本任务路径恢复到基线内容。

## 建议知识库结论

Web reference 应记录为“显式输入、许可先行、快照不可变、抽取边界可审计、主张回链原始行范围、成功抓取不等于审阅通过”。普通本地 reference 导入不承担联网职责；网络错误发生在 reference 事务创建之前，因此不会新增或改写既有 reference 文件。
