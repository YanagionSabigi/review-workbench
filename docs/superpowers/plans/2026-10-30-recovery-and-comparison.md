# 审核写入恢复与比较发布 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 修复架构诊断 A1/A2，保证进程中断后操作可完成，过时比较不能覆盖新审核结果。

**Architecture:** 保留原生前端、Python 和 JSON。Store 在共享包锁内将完整写入意图原子保存到本地日志，再写不可变提交、草稿与比较；下次获取锁时幂等重放。compare 在锁内获取 revision 和历史快照，锁外计算，在锁内核验快照仍有效后发布，否则返回 409。

**Tech Stack:** Python 3.11+、unittest、JSON、Git；无新增依赖。

**Spec:** `docs/audits/2026-10-30/architecture-and-ui.md` A1/A2；用户本轮要求改善并测试这两项待复现风险。

## Global Constraints

- 保留不可变历史、现有 JSON 协议、revision 冲突语义及业务原稿不写回的约定。
- 日志提交后采用完成写入策略；中断调用的响应可能未送达，但落盘意图在下一次访问时完成。
- 验证范围为进程中断/写入异常；不宣称物理断电时的跨平台文件系统持久性。
- 沿用当前功能分支；本轮修复范围已由报告与用户指令确定，直接在本会话执行。

## Review Focus

- 提交、导入和解决冲突的每个写入阶段中断后保持 revision、历史、草稿和冲突一致。
- 同一服务对象在写入异常后也必须恢复，不能只依赖重启。
- 重放再次中断可继续，重复恢复不重复提交或递增 revision。
- 导入多个决定时不因部分落盘丢失后续提交，重试导入去重。
- 新提交、导入、冲突解决以及草稿变动期间发布旧比较应拒绝，保留新视图。

## Task 1: 多文件写入恢复

**Files:** `review_workbench/storage.py` 管理恢复日志；`review_workbench/transfer.py` 在写前计算完整导入结果；`tests/test_recovery.py` 注入真实进程退出和磁盘错误。

**Interface:** `Store._commit(draft, submissions, comparison)` 仅在包锁内调用；`Store.lock()` 在交出锁前完成未决操作。现有 submit、resolve_conflict、import_results 外部参数与返回值不变。

- [x] 先编写并运行回归，确认旧实现发生 revision、冲突和草稿不一致。
- [x] 提取基于历史快照的冲突投影，提交/导入/解决统一使用写前日志。
- [x] 验证写入意图身份与结构，恢复在同一包锁下幂等执行。
- [x] 运行恢复测试，补充重放中断与未记录意图时的失败测试。

## Task 2: 比较版本核验

**Files:** `review_workbench/gitops.py`；`tests/test_recovery.py`。

**Interface:** `compare(root,current)` 在结果过时时抛出 `ReviewError(status=409)`，不覆盖现有 comparison.json；重跑可生成新比较。

- [x] 比较计算期间插入真实提交，确认旧实现未拒绝。
- [x] 在锁内捕获 revision 和不可变提交快照，锁外计算，发布前在锁内再次校验。
- [x] 扩展到导入和冲突解决交错，确认最新视图保留，重跑成功。
- [x] 跑 Python 全量、Node 现有测试及 diff 检查，记录复现/修复证据并提交 Git。

## 执行记录

- RED：运行代码修改前，3 个测试方法暴露 9 处失败；GREEN：新增 6 项及全量 33 项 Python、5 项 Node 测试通过。
- Ruling: 沿用当前功能分支与既有 JSON 存储，以完整操作意图和版本校验修复已明确的 A1/A2；不引入数据库或额外 worktree，避免扩大修复范围。
- 独立只读审阅未发现阻断问题；审阅者检查实现与测试，未重复运行父会话已执行的测试。
- 完整证据与限制见 `docs/audits/2026-10-30/recovery-verification.md`。
