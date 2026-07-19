# 对抗性审查报告 — Case_Search_UI

- **日期**: 2026-07-18
- **范围**: 后端安全、后端逻辑正确性、前端、配置/运维/依赖（全仓库）
- **方法**: 攻击者视角人工审查，关键 pandas 行为经实测复现

**威胁模型**：应用监听 127.0.0.1:5000、无认证、`CORS(app)` 全开放。最大的攻击者不是本机用户，而是**用户浏览器里的任意恶意网页**——它可以跨域读写全部 API。很多"本地小问题"因此被放大为远程可打。

---

## 高危（建议立即修）

### 1. 文件上传路径穿越 → 任意位置写 .xls/.xlsx

`app/api/data_import_routes/data_import_routes.py:166-179`：`file.filename` 未经 `secure_filename` 直接 `os.path.join` 后 `file.save()`。项目里明明写了带消毒的 `save_temp_file`（`file_handlers.py:33`）却是死代码。构造 `filename=../../Desktop/x.xls` 即可写出临时目录；.xls 支持宏，种到桌面后被打开即 RCE。

### 2. confirm 接口 `temp_id` 未校验 → 路径穿越 + `shutil.rmtree`

`data_import_routes.py:265-326`：用户提交的 `temp_id` 直接拼路径，读取其中的 JSON，且**无论成败都执行** `rmtree(temp_dir)`。利用受几道闸门约束，但"未校验输入直接进 join + rmtree"是必须修的结构性缺陷。

### 3. CORS `*` + 零认证 → 恶意网页远程读写全部 API

`app/__init__.py:56`。用户浏览任意网站时，该站 JS 可读取所有搜索/相似度接口返回的明文数据（数据外泄），并可远程触发上面的 #1/#2、数据导入投毒、敏感词篡改。这是把本报告多数问题升级为远程漏洞的放大器。

### 4. 搜索结果含 NaN → jsonify 输出非法 JSON，前端直接炸

`app/api/data_source_routes.py:380-386`：`/search` 没做 NaN 处理（相似度路径有兜底，`calculator.py:149`）。当前生产数据即可触发——实测 `case.parquet` 申请时间列有 5010 个 NaN。命中这些行的搜索会让前端 `response.json()` 抛异常。一行可修：返回前 `result_df = result_df.where(result_df.notna(), None)`。

### 5. `clean_null_values` 把数值单元格永久损毁为 "无"

`app/core/data_processors/data_import_processor.py:191-201`：`.str.replace` 对非字符串单元格返回 NaN，随后 `fillna("无")`——object 列里的纯数字（序列号等）导入后全部变成"无"。pandas 实测复现，属静默数据损毁。

> 注：填"无"本身是产品有意为之的业务规则，本条目针对的是实现方式误伤数值单元格，而非该规则本身。

## 中危

### 6. 并发与数据完整性（一整组）

- parquet 非原子写 + 无锁：两个并发 confirm 互相覆盖丢失更新；写盘中途被读 → 异常被 `load_data_source` 裸 except 吞掉变成误导性 404（`data_import_processor.py:407`、`app/__init__.py:111`）。进程在写盘时被杀 → 主数据文件永久损坏。
- 处理器单例可变状态竞态：`DataImportProcessor.__new__` 单例但 `__init__` 每次覆写 `self.file_path`，并发导入会串文件，可能把别人文件确认入库（`data_import_processor.py:51-77`）。
- 敏感词 JSON 读写无锁、非原子覆写；读到半截文件时 `load_words` 把词表重置为空 dict 并可被随后落盘 → **敏感词文件被静默清空**（`word_manager.py:70-94,182-190`）。

### 7. 默认 DEBUG 模式运行 + 128MB 无内容校验的上传

`wsgi.py:11` 默认 development；`error_service.py:68-71` 在 DEBUG 下把完整 traceback 返回客户端。上传只查扩展名不查内容，xlsx zip bomb 可膨胀至 GB 级内存；配合 CORS 可远程 DoS。另外相似度接口每次全量 jieba+TF-IDF、limit 不封顶（`similarity_routes.py:84`），单次请求即 O(全数据集)。

### 8. 临时文件清理三重失效 → 磁盘无限增长、敏感上传文件永久残留

① `teardown_appcontext` 每个请求结束都触发，第一个请求后定时清理调度器就被永久关停（`app/__init__.py:199-202`）；② `TempFileManager` 扫的是 `data/temp/{search,process,export}`，而实际临时文件在 `%TEMP%\case_search_ui_temp` 的 UUID 子目录——**扫错了地方**；③ 预览后不 confirm 就不清理。`data/temp/` 现存 2025-08 的真实上传文件即为实证。

### 9. 预览与实际导入走两套合并逻辑，结果可不一致

`data_import_service.py:44-79` 与 `data_import_processor.py:327-363` 各自实现合并，归一化和 Unicode 清洗条件不同——会出现"预览说新增 1 条，确认后实际新增 0 条"。且 confirm 失败时返回的错误消息竟是预览成功文案。

### 10. `logs/app.log` 被 git 跟踪

`.gitignore` 漏了 `logs/` 和 `*.log`。已提交的日志含另一台机器的绝对路径、导入请求的完整 JSON 负载、列结构。修复：`git rm --cached logs/app.log` + 补 ignore 规则。

### 11. 前端

- CSV 导出公式注入：`table.js:198-208` 未过滤 `= + - @` 开头单元格。攻击者经无认证导入投毒 `=HYPERLINK(...)` 类内容，其他用户导出用 Excel 打开即执行。
- CDN 脚本无 SRI：Vue/Element UI/axios 全部从 baomitu CDN 加载且无 integrity，本地 vendor 回退文件是 0 字节空文件——CDN 被劫持即全线沦陷，CDN 挂了系统直接不可用。
- 连续搜索竞态：无 AbortController/序号守卫，旧响应覆盖新结果（`search.js:88-169`）。
- 大结果集全量渲染无分页，每单元格还跑高亮计算 → 浏览器冻结。

### 12. 备份机制多处失灵

退出码恒为 0（失败无法被计划任务感知，`backup_manager.py:408-438`）；`-force` 分支是 Python 语法错误、**自始不可用**（实测 SyntaxError）；`backup_config.ini` 整个是死配置、代码无任何重试逻辑；触发备份只比目录总字节数，等长数据订正漏检，最坏 10 天无备份。

## 低危（摘选）

- `SECRET_KEY` 硬编码回退（`default.py:16`）；错误响应回显 `str(e)` 泄露内部路径。
- 日期解析失败静默变 NaT、存量数据日期格式混杂（`'2025/3/3'` vs `'2025-03-02'`）→ 年月搜索漏结果、排序错误（`data_import_processor.py:223-263`）。
- 脱敏可绕过：正则无 IGNORECASE/词边界，`B 1234`、全角变体即绕过；且脱敏是客户端可选调用，不构成安全边界（`anonymizer.py:29-80`）。
- `r_and_i_record` 数据源配置指向不存在的 parquet 文件，搜索恒 404。
- 机号清洗 `.str.replace("all","ALL",case=True)` 裸子串替换误伤（`"Overall"→"OverALL"`，`case_processor.py:108`）。
- README 与实现不符：实际运行时是 CDN 加载的 Vue 2.6.14（已 EOL），`package.json` 的 Vue 3 + Vite 构建产物是未被引用的死代码。
- 新增为负时统计正则 `(\d+)` 匹配不到负数，"删了数据"显示成"成功导入 0 条"。
- 测试行覆盖率仅 ~34%，且 `conftest.py:156` 的 fixture 会加载真实生产数据。
- 大量死代码：`CaseService` 调不存在的方法、各 service 的 `process_*_file` 返回假成功、`ApiResponse.paginated/file_download` 无调用方、`/test` 测试页暴露在生产路由。
- 依赖无锁定、dev/prod 混杂，`requests 2.31.0`、`flask-cors 4.0.0` 均有后续安全修复版本。

## 修复优先级建议

1. **#1 + #3**（组合即远程入侵链）：`secure_filename` + 校验落盘路径在 temp_dir 内；CORS 收敛到具体 origin 或加本机 token。
2. **#4**（一行修复，当前正在影响搜索功能）。
3. **#2**：`temp_id` 校验 UUID 格式。
4. **#6**：parquet 写临时文件后 `os.replace` 原子替换 + 导入全局锁；处理器去单例化。
5. **#7**：生产入口显式 `FLASK_ENV=production` 并去掉 DEBUG traceback 回显。
6. **#8**：调度器改用 atexit 注册 + 清理指向真实临时目录。

## 已验证为无问题（排除误报）

- 无用户可控正则/ReDoS：搜索全部 `str.contains(..., regex=False)`。
- 无 send_file/send_from_directory 路由；`ApiResponse.file_download` 仅测试引用。
- Jinja2 模板无 `|safe`/关闭 autoescape；前端唯一 `v-html` 输出经完整 HTML 转义，当前安全。
- 无 innerHTML/document.write/eval；Element UI 表格默认渲染自动转义。
- `data/` 已被 .gitignore 覆盖；`scripts/` 无硬编码凭据；`pyarrow==14.0.1` 正是反序列化 CVE 修复版本。
- 测试断言质量合格（615 个 assert / 334 个测试），不是"只跑通"式测试；问题在覆盖面与和生产数据耦合。
