# 交付验证

验证日期：2026-10-30。实现位于本地 `feat/review-workbench`，不配置远程仓库，不自动修改已安装的业务 skills。

## 自动检查

- `python -m unittest discover -s tests -t . -v`：27 项通过。
- `node --test tests/frontend.test.mjs tests/drafts.test.mjs`：5 项通过。
- skill-creator `quick_validate.py`：通过（Windows 下使用 `python -X utf8` 读取中文 skill）。
- Python compileall、前端脚本语法及 Git diff 空白检查通过。

覆盖：Schema 与内容块配对、有效决定、部分提交、revision 冲突、冻结材料、批量跳过人工草稿/必审、Git 暂存与 HEAD 不变、无首个提交、worktree、不同人工决定、迁移解包、去重、防伪造 accept、ZIP 路径逃逸和显式冲突解决。

## 浏览器验证

在 Windows 本机浏览器执行：

- 手动修改 → 后端确认已保存 → 刷新 → 原输入恢复。
- 原版文字实际拖选 → 引用 → 意见模式；仅有引用不计已审，填写意见后正常保存。
- 批准本页在六项中批准三项，跳过两项必审和已有手动草稿；手动稿保持原值。
- 提交范围四项中仅勾选一项，实际提交成功，其余审核进度保留。
- 本地 KaTeX 对照；输入无效 `\frac{1` 显示错误且不计已审，改为合法公式后恢复；预览不重复堆积。
- 图片放大、切换整页、原比例/适应窗口；375px 窄屏可展开主目录与交叉筛选。
- 最终交付示例直接从 `artifacts/example-review.zip` 的实际解包目录启动，页面显示 0/6 已审、没有人工提交。

源码中的旧视觉原型不是运行入口。交付页面无标语、重复摘要、差异图例及常驻功能解释；四模式初始不高亮，互斥选中，按模式展开编辑。

## 独立验证与修复

一个未读取本对话的 agent 按通用 skill 完成两术语审核包及朋友 ZIP 的准备、验证与导出；业务原稿 SHA256 前后一致，未代替人批准。包在异地目录基准验证、短时服务初始化均成功。

独立全分支代码审阅发现三个 Important，无 Critical/Minor。已逐项用失败回归验证并修复：

1. 旧 sessionStorage 备份不再套用磁盘新 revision。恢复不同版本备份必须进入明确比较，不静默覆盖另一页输入。
2. 本地提交在同一包锁内重算历史冲突；不再只在导入时刷新冲突视图。
3. accept/keep/edit 的公式在前端和后端使用同份 KaTeX 校验，提交和导入共同遵守；comment 保留反馈通道。

额外回归检查合法 ID `constructor`，避免被 JavaScript 对象继承属性冒充草稿。

## 交付包

- `artifacts/example-review.zip`：约 1.46 MB，六条未审核示例、材料、离线数学资源、最小 Git、Python 运行代码和五个依赖 wheel。
- `artifacts/review-workbench-skill.zip`：约 1.03 MB，独立 skill、launcher 和运行资源；真实解包后的 launcher 验证示例成功。

迁移包不含源业务仓库历史或原机绝对路径。离线 wheel 匹配导出机 Windows/Python 版本，其他 Python/系统使用联网安装 requirements 或匹配 wheel；未声称跨系统离线安装都已验证。

已在新建的 Windows/Python 3.14 虚拟环境中，使用 `--no-index --find-links wheels` 完全离线安装全部五个依赖，并验证解包后的启动入口可加载。其他操作系统仍未实测。

## 实施取舍与成本

这些取舍均已在实现中兑现，不暗示用户逐项指定了内部实现：

- 连续在当前会话、用户指定目录的功能分支实施，没有额外 worktree；成本是 `main` 仍保留设计基线，合并由用户决定。
- Git 基准使用独立 refs 与临时 index；成本是基准不出现在普通业务分支日志中，但可按包内完整 commit ID 查找，原暂存及分支保持不变。
- 不同人工意见保守列为冲突，显式解决产生新的不可变提交；成本是兼容但不同的意见也可能需要人选一次，避免自动覆盖。
- 独立 skill 包携带 runtime；成本是版本更新需重新生成安装包，而非依赖原机器路径。
- 公式提交/导入使用 Node 调用随包 KaTeX；用户已允许 Python/Node。成本是公式审核人需安装 Node，普通文本仍只需 Python/Git，无 npm 构建。
- 最终审阅没有独立复核像素、压缩 vendor 源码、其他操作系统 wheel 和业务适配。作者已做本机视觉与操作验证，保留上游许可证；其他系统需实际环境验证，上游业务投影与写回仍是业务 skill 的责任。

没有延后处理的代码审阅 Minor。图片圈画 UI 按已批准范围仅预留协议；不属于漏做的现成功能。
