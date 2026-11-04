# 实际架构

React/Pixi 前端通过 Vite 代理请求本地 HTTP API；GardenInteractionService 提供花园视图，CreationService 编排 AI、音乐与花朵引擎，存储落在 JSON 与 WAV。Ollama 和 ACE-Step 是独立本机服务。图源见 diagrams；不包括未接入的历史检索。

依据 frontend/vite.config.ts、backend/app/api/garden_preview.py、application/creation_service.py。
