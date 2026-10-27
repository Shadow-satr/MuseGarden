# MuseGarden

正式代码：`ai_engine/`、`music_engine/`、`flower_engine/`、`application/`、`backend/`、`frontend/`。当前后端持久化数据在 `database/`，启动与导出入口在 `scripts/`。

当前产品进度：正式前端已推进至 Step 14。花园支持大世界摄像机、数据驱动的格子地图、
地形碰撞、444 个逐格种植位置、1×1 小花与 3×3 大花占地、四方向走路动画、脚底交互、真实创作与种花、花朵记忆详情，
以及音乐修改和历史版本选择。前端历史见 `docs/architecture/Frontend_progress.py`，当前地图
规格见 `docs/architecture/Frontend_map_v1.md`，跨模块现状见 `docs/architecture/MuseGarden_progress.py`。

开发与历史资料统一放在 `development/`，包括旧网页 Demo、演示脚本、演示数据、评估占位目录和测试运行缓存。`test/` 是维护正式代码的 Python 回归测试源码，保留在项目根目录；`docs/` 保存方案和进度记录。

正式前端的启动说明见 [frontend/README.md](frontend/README.md)。开发资料清单见 [development/README.md](development/README.md)。

日常启动可直接双击项目根目录的 `启动 MuseGarden.bat`。它会确认或启动 Ollama、ACE-Step、
Garden API 与前端，并等待 ACE-Step 的 `acestep-v15-turbo` 模型完成初始化；全部就绪后才会
自动打开 `http://127.0.0.1:5182/`。
