# 面向收件人的双击启动入口

导出的审核包现在包含 Windows `开始校对.cmd`、macOS `start_review.command` 和原有 `start_review.py`。启动步骤与前置依赖统一在 OPEN-ME.txt，不增加第二份给人阅读的依赖说明；requirements.txt 继续供 pip 使用。

Windows 入口先查找可用的 Python 3.11+，优先 py -3，再尝试 python。失败时保留窗口与提示，不自动安装或联网下载。Python 入口在依赖缺失或版本不符时展示 requirements.txt 的安装方式，并提供 --check 环境检查。启动参数支持 --no-open 和 --port。

说明要求先完整解压 ZIP，写明各系统应点击或运行哪个文件，不要直接打开 web/index.html；也说明首次安装依赖、含公式时的 Node.js 要求、离线安装与回传结果。

## 验证

- 新测试先在旧导出上因缺少 CMD 入口失败，再实现入口。
- Windows 下实际执行 CMD：导出包放在包含空格、中文的路径，通过 --check；Python -S 模拟未安装依赖，确认输出安装指引且没有 traceback。
- ZIP 为 macOS .command 保存 Unix 可执行位；未声称已经在 macOS 上运行。
- 实际解压并运行 Python 入口至服务 URL 输出成功；暖环境样例约 0.279 秒，此数字不是冷启动或所有机器的性能保证。
- 示例包 27 个文件、47,432 字节；没有新增 skill、示例或 Git 仓库。
- Python 全量 36 项通过，30.255 秒；Node 7 项通过；compileall、Git diff 检查通过。

旧 ZIP 不会自动获得这些入口，需要用新版重新导出。独立 skill 安装包仍保留生成新审核包所需的模板，收件人包只复制根目录入口、不携带重复模板目录。

独立只读审阅未发现可操作的正确性或安全问题，检查了解释器回退、出错保留窗口、中文路径、依赖校验和 macOS 参数引用。
