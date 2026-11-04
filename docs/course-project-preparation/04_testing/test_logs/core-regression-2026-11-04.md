# 核心回归执行记录（2026-11-04）

执行环境：Windows 本机项目环境。

## 前端

执行：`npm test`（目录：`frontend/`）

结果：15 个测试文件通过，75 项测试通过，0 项失败。

执行：`npm run build`（目录：`frontend/`）

结果：TypeScript 检查与 Vite 生产构建通过。首次使用系统临时目录时，esbuild 清理临时文件遇到访问锁定；将 TEMP/TMP 指向项目内独立临时目录后构建成功。仅有既有的打包体积提示。

## 后端核心回归

执行：`.venv\Scripts\python.exe -m pytest test\flower_engine test\application\test_garden_planting.py test\backend\test_creation_api.py`

结果：95 项通过，0 项失败，耗时约 2.12 秒。

范围：花朵生成、种植规则、种植位置校验，以及创建、修改、删除等接口规则。完整 AI 生成依赖本机 Ollama 和 ACE-Step，不将本次自动化结果表述为每台设备的端到端生成保证。
