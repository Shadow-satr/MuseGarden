# MuseGarden Frontend

正式前端已推进至 Frontend Step 14：在 Garden World、Player、真实创作、花朵记忆、
音乐版本和走路动画之上，完成大世界摄像机、Grid Map V1、逐 SOIL 格种植、1×1 小花、
3×3 大花、持久化占地和冲突降级。地图完整规格见 `../docs/architecture/Frontend_map_v1.md`。

日常使用时，直接双击项目根目录的 `启动 MuseGarden.bat`。它会确认或启动 Ollama、ACE-Step、Garden API 与 Vite，全部就绪后自动打开 `http://127.0.0.1:5182/`。日志写入 `development/runtime_logs/`。

手动开发时，`npm ci` 后运行 `npm run dev -- --port 5182`，打开 `http://127.0.0.1:5182/` 即进入花园世界。前端从后端只读 `/api/garden-preview` 加载 GardenRenderSpec；后端未启动时会显示加载错误。先在项目根目录运行 `.venv\Scripts\python.exe scripts\run_garden_preview_api.py`，Vite 会将 `/api` 代理到 `127.0.0.1:8000`。

真实创作还需要本机 Ollama（`127.0.0.1:11434`）和 ACE-Step（`127.0.0.1:8001`）可用；若生成服务未启动，创作面板会显示后端错误并保留输入供重试。

`src/world/GardenWorld.ts` 管理 Pixi 生命周期与键盘输入，`src/world/WorldScene.ts` 复用 `src/rendering/flowers` 中的 Garden Renderer，`src/world/entities/Player.ts` 从 `src/assets/player-walk-sheet-v7.png` 读取每个方向 1 个站立帧和 6 个走路帧（`player-walk-sheet.json` 描述网格）。按住 WASD 或方向键时以 9fps 循环走路序列并保持脚底基线，停止时回到该方向站立帧；左右停止帧使用最初四视图中的直立、并脚侧面姿势。世界边界会限制位置。靠近花或空地时，页面顶部会提示按 E。React 只提供宿主 DOM 和提示界面；`src/ui` 为 HTML Overlay。旧工程演示统一存放于 `development/demo/creation_preview`，正式前端不包含演示页面或静态预览花园数据。

当前地图由 `src/world/TerrainMap.ts` 的 16px 逻辑格数据驱动，世界为 1448 × 1086px，
摄像机缩放为 2.5。`TerrainRenderer.ts` 绘制六类纯色地形；四块 3 × 2 田地包含 24 块
4 × 4 泥土区域；西北、东南田地已填平内部草缝，合计 444 个独立 SOIL 种植格。小花占 1 格，大花以选择格为中心占 3 × 3；
尺寸与占地由后端记录，刷新不会重新随机。水域与建筑不可通行；草地、道路、
土地和桥梁可通行。打开 `http://127.0.0.1:5182/map-overview` 可查看与游戏同源的完整地图。

玩家的世界坐标对应角色脚底；脚底进入空地格子时，按 E 会打开“留下一段记忆”面板。可输入最多 500 字；面板打开时玩家移动和 E 交互暂停，取消后恢复。点击“开始创作”会向正式 `POST /api/creations` 发送当前花园 ID、文字和该空地网格坐标。后端执行完整生成与种植；成功后前端重读 `/api/garden-preview`，将空地更新为花朵，结果面板可以播放返回的 `/api/audio/...`。脚底进入花朵所在格子时，按 E 会打开记忆详情：展示原始文字、这朵花自身的 Flower Engine 图案，并可播放、修改或选择 V1 / V2 / V3 等音乐版本。花园刷新失败时只重试刷新，不重复创作请求。
