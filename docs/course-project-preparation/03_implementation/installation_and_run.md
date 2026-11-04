# 运行与环境说明

## 准备
Windows 项目根目录；本次使用项目虚拟环境 Python 3.12.14、Node 24.13.1。准备 Ollama 和 qwen2.5:3b、ACE-Step 1.5 服务及模型；外部安装、模型许可和硬件条件需按其官方说明核实，不能由 requirements 自动完成。

首次创建 Python 环境可参考：`py -3.12 -m venv .venv`，然后 `.venv\Scripts\python.exe -m pip install -r requirements.txt`；前端 `cd frontend; npm ci; cd ..`。音乐解读语义模型有独立可选依赖 requirements-music-companion-step2.txt，安装前需确认 GPU 与官方源。以上是安装指引，未在干净机器复验。

脚本默认在 `D:\MuseGarden-ace-step-poc\ACE-Step 1.5` 寻找启动脚本，可通过 `$env:MUSEGARDEN_ACESTEP_HOME="你的ACE-Step目录"` 覆盖；这是本地路径，不是密钥。

## 启动
双击根目录 `启动 MuseGarden.bat`；脚本等待 Ollama、ACE-Step 模型、Garden API 和 Vite 就绪，打开 http://127.0.0.1:5182/ 。日志 development/runtime_logs。单独运行 API：`.venv\Scripts\python.exe scripts\run_garden_preview_api.py`；单独运行前端：`cd frontend; npm run dev -- --port 5182`。

MUSEGARDEN_API_PORT 控制 API 及 Vite 代理；MUSEGARDEN_DATA_ROOT 指定数据根路径。测试专用 MUSEGARDEN_TEST_TERRAIN_GARDEN 和 MUSEGARDEN_TEST_FLOWER_SIZE_ROLLS 不应在正式运行时设置。关闭手动打开的终端可停止对应服务；脚本后台服务需在任务管理器确认程序后自行停止，切勿按端口盲目结束不明程序。

## 故障
启动失败先查看日志；模型未就绪不代表前端代码错误。若 Vite 构建提示系统临时文件权限，设置 TEMP、TMP 到有权限的项目临时目录后重试。现有数据可能含私人记忆，分享前不要包含 database/preview、database/local。
