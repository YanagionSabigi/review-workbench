# 校对工作台

轻量的本地人工校对工具：原生网页、Python 服务、JSON 决定、Git 基准。支持中文 diff、术语、OCR、图片、TeX 公式和表格。业务 agent 负责准备材料与修改原稿，工具只保存和展示人工审核结果。

## 运行示例

需要 Python 3.11+ 与 Git；提交或导入公式决定时还需要 Node.js，以便服务端使用同一份 KaTeX 校验。无需 npm 安装或前端构建。

```powershell
python -m pip install -r requirements.txt
python -m review_workbench demo --out demo-project
python -m review_workbench serve demo-project/review
```

终端给出仅本机可用的完整链接并打开浏览器。保留链接中的 `key`；页面载入后会从地址栏移除它。服务使用随机端口，重新启动时使用新打印的链接。关闭页面不影响已落盘的数据；关闭服务后重新启动即可继续。

示例包含六项：译文、公式源图、术语、图表说明、表格、没有推荐方案的必审项。示例图片为生成的演示材料。

## 审核

默认一次看一项，也可以切换连续阅读。目录互斥，筛选可交叉；选中的筛选条件取交集。“未审”包括必审项。每页最多 24 项。

四个按钮互斥：接受建议、保留原版、手动修改、提出修改意见。手动修改与意见输入按选择展开；选中文字后可以引用。仅引用但未写意见不算完成。切换模式保留草稿，提交时只使用当前选择。右上角“已保存”意味着服务已确认落盘；“未保存”时应重试，旧页面冲突可先比较草稿。

批量批准只接受有推荐的普通待审项，跳过必审、已有决定或人工草稿的条目。提交本轮时可以选择部分范围。已审只表示人已作决定，意见仍需要 agent 处理。

图片可查看整页（调用方需提供），支持适应窗口、原比例、放大缩小、滚轮缩放与拖动。公式在本机渲染，编辑 TeX 时实时预览；不支持的命令明确显示错误。KaTeX 不是完整 LaTeX 编译器。首版图片圈画只有数据接口，尚无绘图按钮。

## 交给其他 skill 使用

通用入口：[skill/review-workbench/SKILL.md](skill/review-workbench/SKILL.md)。保持本仓库目录完整即可调用其中 launcher；也可生成含运行资源的独立 skill 安装包。

```powershell
python -m review_workbench export-skill --out artifacts/review-workbench-skill.zip
```

将 ZIP 内 `review-workbench/` 放入使用者的 skills 目录。也可在其他 skill 中引用其 `SKILL.md`，并调用 `python <skill目录>/scripts/review.py ...`。安装包内含离线前端和 Python 代码；首次仍需安装 `runtime/requirements.txt`。本工具不会修改已有业务 skills。

输入和回馈见 [通用协议](skill/review-workbench/references/protocol.md)，机器约束见 [schemas](schemas)。完整可运行输入见 [examples/demo/package.json](examples/demo/package.json)。

## 准备自己的审核包

1. 业务 skill 提供明确项目根目录、输入 JSON、资源与范围清单。范围清单是项目相对普通文件路径数组，不能包含无关暂存文件或整个目录。
2. `before` 是页面原版，`proposal` 是建议，`baseline` 是本轮准备时的实际工作稿，`evidence` 是外文/扫描图等证据。先执行推荐时 `baseline` 可以不同于 `before`。
3. 输入中的图片放在 `assets/`，路径相对于输入 JSON。没有推荐时 `proposal` 写 `null`，人工必审项设 `requires_human: true`。

```powershell
python -m review_workbench validate input/package.json
python -m review_workbench prepare --project PROJECT --input INPUT_JSON --scope SCOPE_JSON --out NEW_PACKAGE_DIR
python -m review_workbench serve NEW_PACKAGE_DIR
```

prepare 复用项目已有 Git（含 worktree），没有则初始化指定项目。它用临时 index 把指定文件和审核材料保存为独立的 `refs/review-workbench/round-*` 基准提交，不移动业务 HEAD，不改变原有暂存内容，不执行 stash。身份未配置时会给出 Git 错误；由调用方处理，不写全局配置。真实材料会进入**业务项目的本地 Git 对象**，不是工具源码仓库；不会推送。

一轮材料冻结后不要原地改 package.json 或图片。新的建议或原稿版本使用新输出目录；旧材料继续支持回传审核。

## 迁移与回传

```powershell
python -m review_workbench export PACKAGE --out review.zip
# 接收者需要离线安装 Python 依赖时：
python -m review_workbench export PACKAGE --out review-offline.zip --offline-deps
```

ZIP 包含网页、公式资源、Python 运行代码、材料和一个仅含本轮材料的最小 Git 仓库，不复制业务仓库历史或账号配置。接收者解压后运行 `python -m pip install -r requirements.txt`，再运行 `python start_review.py`。

带 `wheels/` 时离线安装：`python -m pip install --no-index --find-links wheels -r requirements.txt`。wheel 默认匹配导出机器的 Python/系统；跨平台接收者应联网安装声明依赖，或自行准备匹配 wheel。

网页“记录”可以下载结果 JSON。也可回传仅结果 ZIP：

```powershell
python -m review_workbench export PACKAGE --results-only --out results.zip
python -m review_workbench import-results ORIGINAL_PACKAGE --from results.zip
```

导入只读取数据，不执行回传包的程序。重复提交去重，不同决定保留并列出冲突；同编号不同内容拒绝导入。草稿不视为已提交结果。版本比较中可“采用此决定”明确解决冲突：生成带解决引用的新提交，旧记录仍保留；不会因为导入先后顺序自动覆盖。

## Agent 继续工作与比较

用户明确指示继续后，读取 `submissions/*.json` 的完整最终块或意见。工具不替业务 agent 写回。先生成当前工作稿投影，再比较：

```powershell
python -m review_workbench compare PACKAGE --current current.json
```

`current.json` 含 `package_id`、原 `base_commit`、`targets: [{target_id, blocks}]`。块结构与审核材料一致。结果写入 `comparison.json`，刷新页面后可查看基准、当前稿和人工决定。相同为已满足、当前未变为可应用、双方不同为冲突；多条不同人工决定保留冲突。Git 文本无冲突不代表语义正确。二进制图片不会自动合并。

## 文件与验证

`package.json` 为冻结材料；`drafts.json` 为自动保存的草稿；`submissions/` 为不可变人工提交；`comparison.json` 为比较结果。运行时锁文件无需人工处理。

```powershell
python -m unittest discover -s tests -t . -v
node --test tests/frontend.test.mjs tests/drafts.test.mjs
```

Python 依赖为 jsonschema 及其传递依赖；HTTP 使用标准库。KaTeX 固定为 0.19.1，资源及 MIT 许可证位于 `web/vendor/katex/`，来源记录在 `VERSION`。设计参考 [Refactoring UI skill](https://github.com/edisonmbli/refactoring-ui-skill)，未复制其书籍内容。
