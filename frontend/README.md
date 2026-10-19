# MuseGarden Frontend

正式前端已完成 Frontend Step 1–9：Garden World、Player、Interaction、Creation Overlay、
真实创作与种花、花朵记忆详情、音乐修改与版本选择，以及四方向循环走路动画。

日常使用时，直接双击项目根目录的 `启动 MuseGarden.bat`。它会确认或启动 Ollama、ACE-Step、Garden API 与 Vite，全部就绪后自动打开 `http://127.0.0.1:5182/`。日志写入 `development/runtime_logs/`。

手动开发时，`npm ci` 后运行 `npm run dev -- --port 5182`，打开 `http://127.0.0.1:5182/` 即进入花园世界。前端从后端只读 `/api/garden-preview` 加载 GardenRenderSpec；后端未启动时会显示加载错误。先在项目根目录运行 `.venv\Scripts\python.exe scripts\run_garden_preview_api.py`，Vite 会将 `/api` 代理到 `127.0.0.1:8000`。

真实创作还需要本机 Ollama（`127.0.0.1:11434`）和 ACE-Step（`127.0.0.1:8001`）可用；若生成服务未启动，创作面板会显示后端错误并保留输入供重试。

`src/world/GardenWorld.ts` 管理 Pixi 生命周期与键盘输入，`src/world/WorldScene.ts` 复用 `src/rendering/flowers` 中的 Garden Renderer，`src/world/entities/Player.ts` 从 `src/assets/player-walk-sheet.png` 读取每个方向 1 个站立帧和 6 个走路帧（`player-walk-sheet.json` 描述网格）。按住 WASD 或方向键时以 9fps 循环走路序列并保持脚底基线，停止时回到该方向站立帧；世界边界会限制位置。靠近花或空地时，页面顶部会提示按 E。React 只提供宿主 DOM 和提示界面；`src/ui` 为 HTML Overlay。旧工程演示统一存放于 `development/demo/creation_preview`，正式前端不包含演示页面或静态预览花园数据。

玩家的世界坐标对应角色脚底；脚底进入空地格子时，按 E 会打开“留下一段记忆”面板。可输入最多 500 字；面板打开时玩家移动和 E 交互暂停，取消后恢复。点击“开始创作”会向正式 `POST /api/creations` 发送当前花园 ID、文字和该空地网格坐标。后端执行完整生成与种植；成功后前端重读 `/api/garden-preview`，将空地更新为花朵，结果面板可以播放返回的 `/api/audio/...`。脚底进入花朵所在格子时，按 E 会打开记忆详情：展示原始文字、这朵花自身的 Flower Engine 图案，并可播放、修改或选择 V1 / V2 / V3 等音乐版本。花园刷新失败时只重试刷新，不重复创作请求。
