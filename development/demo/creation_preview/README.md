# Creation Preview

这是 MuseGarden 的工程预览页，用于验证 Flower/Garden Renderer、CreationService、API、音乐播放和铲花交互。正式 Garden World 是项目根目录下独立的 `frontend/` 工程。

从项目根目录启动本地 API（另需 Ollama 与 ACE-Step 服务）：

```powershell
.venv\Scripts\python.exe scripts\run_garden_preview_api.py
```

在第二个终端启动此预览页：

```powershell
cd development\demo\creation_preview
npm run dev -- --port 5181
```

浏览器访问 `http://127.0.0.1:5181/`。Vite 将 `/api` 代理到 `127.0.0.1:8000`。

在本目录运行 `npm test` 和 `npm run build`。花园预览数据生成脚本仍在项目根目录的 `scripts/`；花朵预览导出脚本在 `development/scripts/`。当前本地 API 使用的持久化数据仍位于 `database/preview/`，此次整理没有移动或重置该数据。
