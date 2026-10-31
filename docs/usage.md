# 校对工作台操作指南

首次使用可以先运行 [README 中的演示](../README.md#先试一下)。下面的命令都在仓库目录执行；`PROJECT`、`INPUT_JSON` 等大写名称需要换成自己的路径。

## 准备自己的材料

每条审核材料包含原版、建议，以及可选的上下文、图片等证据。可以让负责翻译或修改的 AI 按 [skill 协议](../skill/review-workbench/references/protocol.md)整理，也可以参考 [输入示例](../examples/demo/package.json)手动准备。

准备时需要三样东西：

1. 业务项目目录，放着实际要修改的稿件。
2. 输入 JSON 和它引用的图片等资源。
3. 范围清单 JSON，内容是本轮涉及的项目相对文件路径数组，例如 `["chapters/03.md"]`。

```sh
python -m review_workbench validate INPUT_JSON
python -m review_workbench prepare --project PROJECT --input INPUT_JSON --scope SCOPE_JSON --out NEW_PACKAGE_DIR
python -m review_workbench serve NEW_PACKAGE_DIR
```

审核包目录必须位于指定项目内，且尚不存在。工作台会复用项目已有的 Git；项目没有 Git 时会初始化。首次为自己的项目准备材料前，需要已配置 Git 提交身份。准备操作会保存本轮文件的基准，保留原分支和暂存内容。

输入里的几个版本有不同用途：`before` 是页面左侧的原版，`proposal` 是建议，`baseline` 是准备审核时实际工作稿的内容，`evidence` 是参考证据。如果 AI 已先把建议写进工作稿，baseline 就应记录写入后的内容。没有建议时将 proposal 设为 null；必须由人判断的项目设为 requires_human。

材料准备完成后，请使用新的审核包目录开始下一轮，避免原地替换已经审核过的文字或图片。真实材料的基准会进入业务项目的本地 Git，不会自动推送到网上。

## 保存、提交和版本比较

草稿会自动保存。确认右上角显示“已保存”后，即可关闭网页；重新启动服务并使用新打印的完整链接，可以继续审核。

“已审”表示这一项有可用的决定，提交时还可以选择其中一部分。条目与目录以整块底色区分待审（蓝）、已审（绿）、必审（红）；目录下仍有必审项时显示红色，全部已审后显示绿色，其余显示蓝色。当前所在位置用边框突出。

展开条目后，点击左上角全选图标可直接批准本页，悬停提示为“全选本页，跳过必审”。有建议的采用建议，无建议的保留原文，处理后均显示绿色；必审项、已有提交和人工草稿会跳过。仅有引用、没有填写意见时，意见模式不计为完成。

逐条审核时，← 返回上一项，→ 或空格进入下一项；导航会跨页并在首尾循环。输入框、文字编辑和对话框保留原有键盘操作。

如果多个窗口修改了同一份草稿，页面会提示“比较草稿”：

- **本机版本**：当前会话中的修改，可能尚未保存。
- **该文件版本**：审核文件中已经保存的草稿。

比较按条目展示实际内容。选择“使用本机版本”或“保留该文件版本”会应用到整份草稿；它不会自动逐条合并。展开“其他草稿内容”可以查看切换处理方式时保留的输入，技术结构在“技术详情”中。

提交、结果导入和冲突解决若被进程退出打断，下一次访问会自动继续完成已经记录的操作。不要删除审核包里的未完成操作文件。持续的磁盘写入故障仍需先处理；此恢复机制不等于物理断电或存储介质损坏时的保证。

## 转交与回收

把整轮材料导出为 ZIP：

```sh
python -m review_workbench export PACKAGE --out review.zip
```

对方先完整解压 ZIP，再打开 `OPEN-ME.txt`。这一个文件同时说明双击哪个文件、Python/Node.js 版本、首次依赖安装和结果回传：

- Windows：环境已准备好后双击 `开始校对.cmd`。
- macOS：可双击 `start_review.command`；若解压工具未保留执行权限，在终端运行 `python3 start_review.py`。
- Linux：在解压目录运行 `python3 start_review.py`。

入口会自动打开浏览器，启动失败时保留提示；不要直接打开 `web/index.html`，它不能启动保存服务。依赖仅需首次手动安装，启动入口不会安装或下载东西。命令行用户仍可使用 `python start_review.py`，或先用 `--check` 检查 Python 与依赖。

对方需要 Python 3.11+；提交公式决定时还需要 Node.js 18+。接收者无需 Git 或任何 AI skill。ZIP 只含审核材料、网页、必要的 Python 保存/校验服务和依赖说明；公式资源仅在材料含公式时携带，示例、skill、Git 仓库和开发命令行不再打包。启动脚本直接启动本机服务，不安装依赖或联网下载。

完成后，在网页“记录”中下载结果 JSON 并交回即可。下面的仅结果 ZIP 命令由材料提供者在完整工具仓库中执行，精简审核包不携带命令行工具：

```sh
python -m review_workbench export PACKAGE --results-only --out results.zip
```

原项目接收结果：

```sh
python -m review_workbench import-results ORIGINAL_PACKAGE --from results.zip
```

重复回传会去重，不同决定会保留为冲突。同编号却内容不同的结果会拒绝导入。导入只读取数据，不运行对方回传包中的程序。

如果接收者无法联网安装 Python 依赖，导出时可使用 `--offline-deps`。对方再运行：

```sh
python -m pip install --no-index --find-links wheels -r requirements.txt
```

依赖包默认匹配导出机器的系统和 Python 版本；跨系统使用时，应联网安装声明依赖，或准备相匹配的 wheel。

## 交回原工作流程

人工提交之后，负责修改的人或 AI 读取 `submissions/` 中的完整决定或意见，再按原有流程处理原稿。`drafts.json` 是恢复输入用的草稿，尚未提交的内容不应当作最终决定。

如果原稿在审核期间继续发生了变化，调用方应先提供当前稿的结构化投影，再运行比较：

```sh
python -m review_workbench compare PACKAGE --current current.json
```

`current.json` 的字段见 [协议](../skill/review-workbench/references/protocol.md)。比较结果区分已满足、可应用、冲突和待处理意见；仍需人工判断语义是否正确。比较计算期间若审核结果又被更新，命令会提示重新运行，避免覆盖较新的结果。

## 安装为独立 skill

```sh
python -m review_workbench export-skill --out artifacts/review-workbench-skill.zip
```

将 ZIP 中的 `review-workbench/` 放进使用者的 skills 目录。安装包携带运行资源；首次使用仍需安装其中 `runtime/requirements.txt` 的依赖。具体调用方式见包内 SKILL.md。
