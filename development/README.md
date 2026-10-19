# 开发与历史资料

这个目录不属于正式应用的运行时代码：

- `demo/creation_preview/`：旧 React/Pixi 创作流程网页 Demo。
- `scripts/`：手动演示、音乐提供方检查和预览数据导出脚本。
- `data/demo/`：早期独立演示的 JSON 与音频；当前本地 API 使用的 `database/preview/` 保留在原位。
- `fixtures/`：从正式前端移出的花园预览 JSON，供渲染契约测试使用。
- `test_artifacts/`：从项目根目录收拢的 pytest 缓存、`.test-tmp-*` 运行结果和 Python `__pycache__`。后续运行 Python 仍可能重新生成字节码缓存。
- `runtime_logs/`：`启动 MuseGarden.bat` 运行时写入的 Ollama、ACE-Step、Garden API 与前端日志；可随时删除，下一次启动会重新生成。
- `evaluation/`、`datasets/`：目前未被正式应用引用的评估和数据预留目录。
- `legacy_frontend/`：旧预览前端遗留的接口文件。

旧网页 Demo 从项目根目录运行：

```powershell
cd development\demo\creation_preview
npm run dev -- --port 5181
```

`frontend/src/rendering/flowers/` 是正式前端实际使用的花朵渲染器，因此保留在 `frontend/`；旧 Demo 的 ghost 种花预览只保留在本目录。`test/` 是回归测试源码，也保留在根目录；两者都不是演示页面或运行缓存。
