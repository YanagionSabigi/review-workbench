# Review Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成可离线迁移、自动保存、按 Git 版本比较的通用校对工具与 skill。

**Architecture:** 原生模块化前端、Python 标准库 HTTP 服务、JSON 文件存储。版本管理通过 Git 的临时 index 和基准引用保护业务暂存区；业务稿仅由上游 agent 修改。

**Tech Stack:** Python >=3.11, jsonschema >=4.23,<5, KaTeX pinned local distribution, JavaScript ES modules, unittest。

**Spec:** docs/superpowers/specs/2026-10-29-review-workbench-design.md（用户已批准）

## Global Constraints

- 不创建远程仓库，不内置业务技能适配；真实材料不加入工具源码仓库。
- 四按钮文案固定、初始无高亮；自动保存经后端确认；人工草稿不被批量覆盖。
- red 必审不可批量通过，comment 与已应用分离，支持部分提交。
- 相对资源离线可用，HTML 转义，路径受限，同源/令牌校验，JSON 原子写入和 revision 冲突保护。
- before/proposal 为展示版本；baseline 为 Git 固定的本轮实际工作稿；evidence 为原始证据。

## Review Focus

1. 断网、无 npm 或机器路径变化：导出 ZIP 依然可审阅；Task 4 解包运行验证。
2. 其他文件已暂存：prepare 不改变暂存内容、工作树和业务分支；Task 2 验证索引字节与 HEAD。
3. 同目标多问题、多次不同意见：导入保留冲突而非覆盖；Task 4 测试。
4. 两浏览器并行、失联与快速输入：旧 revision 返回409，本地输入保留；Task 1/3/5 验证。
5. 缺推荐、图像不可编辑、TeX 无效和未完成意见：不制造有效决定；Task 1/3/5 测试与浏览器验证。

## Files and responsibilities

`review_workbench/model.py` 协议校验、决定解析；`storage.py` 草稿/提交锁与原子持久化；`gitops.py` 范围基准与 Git diff；`transfer.py` 迁移与导入；`server.py` 安全 HTTP；`__main__.py` CLI。
`schemas/{package,drafts,submission}.schema.json`；`web/index.html`、`web/styles/{tokens,app}.css`、`web/scripts/{api,render,app}.js`；`web/vendor/katex/` 离线数学资源。
`skill/review-workbench/SKILL.md` 与 `references/protocol.md`；`examples/demo/`；`tests/test_{model,storage,gitops,server,transfer}.py`。

### Task 1: Protocol and persistent decisions

**Interfaces:** `validate_package(data, root=None)`；`resolve_decision(item, draft)` 返回完整 edits/待处理意见；`Store(root).save(draft, expected_revision)`；`Store.submit(item_ids, expected_revision)`。

- [ ] 写 model/storage 失败测试：重复编号、不同 block 错配、comment 空白、无推荐 accept、无图像编辑、revision 409、仅当前模式提交、部分提交及不可变历史。
- [ ] `python -m unittest tests.test_model tests.test_storage -v` 观察失败。
- [ ] 创建 schemas、model、storage（包级进程锁，串行临时文件原子替换，提交读取同一锁）。
- [ ] 同命令通过；提交 Task 1。

### Task 2: Prepare and Git comparison

**Interfaces:** `prepare(project, input_path, scope_path, destination)` 产生冻结审核包；`snapshot(project, paths, label)` 返回 commit SHA；`compare(root, current)` 返回 target/block 比较及提交冲突。

- [ ] 写 gitops 测试：初始仓库、已有未提交材料、无关已暂存文件、相关已暂存文件、worktree、before 与 baseline 不同、结果一致/可应用/冲突、缺基准。
- [ ] 运行 `python -m unittest tests.test_gitops -v` 观察失败。
- [ ] 实现临时 index 的独立 Git 基准引用，不移动 HEAD；prepare 只复制已声明资源、记录来源 SHA；compare 按块调用 Git diff 并保守判冲突。
- [ ] 测试通过；提交 Task 2。

### Task 3: HTTP and browser workbench

**Interfaces:** GET `/api/state`；PUT `/api/drafts`；POST `/api/submit`；POST `/api/compare`；GET 静态与 `/assets/*`。写入使用启动令牌和 same-origin。`serve(root, port=0, open_browser=True)`。

- [ ] 写 server 测试：加载/保存/重启、部分提交、令牌和 Origin、路径穿越、服务不可并发持包、资源 MIME、409。
- [ ] 运行 `python -m unittest tests.test_server -v` 观察失败。
- [ ] 实现 HTTP 与前端：专注/连续视图、目录筛选、多选批量、四模式、动态编辑、划选引用、分页、图片局部/整页/缩放/平移、KaTeX 实时渲染与错误、结构表格、提交历史与冲突对照。只执行受信本地渲染库，内容使用 DOM textContent。
- [ ] 浏览器检查桌面/窄屏、保存恢复、按钮状态、选区、失败提示；记录实际证据；提交 Task 3。

### Task 4: Portable package and CLI

**Interfaces:** `export_package(root, output, results_only=False, wheels=False)`；`import_results(root, source)`；CLI `prepare/serve/export/import-results/compare/validate/demo`。

- [ ] 写迁移失败测试：解包后新位置启动、最小 Git 不包含源历史、仅结果回传、重复导入去重、不同决定冲突、错误基准、恶意 ZIP 路径和符号链接。
- [ ] 运行 `python -m unittest tests.test_transfer -v` 观察失败。
- [ ] 实现导出自包含运行资源/依赖说明/可选 wheel、最小材料 Git；回传和导入遵循来源基准，不执行包内代码。提供跨平台 Python 启动入口。
- [ ] 测试并执行示例包导出/解包/重新启动/意见回传；提交 Task 4。

### Task 5: Skill, docs and final verification

**Interfaces:** README 命令与实际 CLI 一致；通用 skill 指向维护的 Schema 和协议，包含 Git 检查、材料生成、服务启动、人工提交、反馈处理与迁移。

- [ ] 创建可读 README、通用 skill、示例（文本、术语、OCR/TeX、图片、表格、冲突）与许可证说明；不修改已安装的业务 skills。
- [ ] 运行 skill quick_validate，完整 unittest、前端 JS 语法检查、桌面/窄屏浏览器流程、ZIP 离线检查。
- [ ] 独立全分支代码审阅；重大问题逐项回归测试后修复，最后运行完整验证并提交。
- [ ] 向用户交付可运行 URL、示例审核包、skill 位置、验证结果与实际限制。

## Execution record

用户已明确要求“开始执行”；本轮直接按计划在当前项目功能分支执行，不再请求计划批准。没有既存实现与测试，基线只有已批准设计及原型。原型是视觉参考，正式代码独立实现。
