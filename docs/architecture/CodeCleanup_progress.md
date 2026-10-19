# Code Cleanup Progress

## 2026-10-05：可读性优先整理

这次整理不新增任何产品功能，也不改变 MusicBlueprint、CreationDraft、
BlueprintRevision、MusicMemory 或 ACE-Step REST API 的数据契约。

### 已完成

- ACE-Step 客户端改用 `requests` 发送和下载 HTTP 请求；依赖已记录在
  `requirements.txt`。
- 客户端只保留当前 MVP 真正使用的六个动作：构造请求、提交任务、查询状态、
  等待任务、下载音频、串联生成。
- Provider 异常只保留一个 `AceStepProviderError`，结果对象只保留 `task_id`、
  `audio_bytes` 和 `content_type`。
- 删除未使用的旧 `music_engine/provider` 空模块；当前唯一有效入口为
  `music_engine/providers/ace_step.py`。
- 简化 Blueprint 生成、编辑、LLM 调用与 JSON 解析的直线流程，删除重复的
  Blueprint 再校验和多余中间变量。
- 同步更新 Music Engine 和 AI Engine 的进度说明。

### 特意保留的保护逻辑

- Pydantic 对 LLM 输出、Blueprint、草稿、版本和记忆数据的校验。
- CreationDraft 与 BlueprintRevision 写入失败时的回滚。
- JSON Store 的原子临时文件写入、重复 ID 检查和恢复/确认时的一致性检查。
- ACE-Step 的服务不可用、HTTP/JSON 异常、失败任务、超时和空音频检查。

### 没有提前实现

- Provider 工厂、注册表、多 Provider 抽象和配置中心。
- 音频持久化、版本管理、数据库迁移、FastAPI 或前端。
- 对外部 Ollama / ACE-Step 服务的自动启动或自动模型切换。

这些内容只有在真实出现第二个 Provider、正式音频存储或部署需求时再引入。

### 本次验证

- `python -m compileall -q ai_engine music_engine scripts test`：通过。
- 31 个不依赖外部服务的断言脚本（Blueprint、progression、Memory、Draft、
  Revision、确认流程、Adapter、ACE-Step HTTP Mock）已回归通过。
- 依赖真实 Ollama 的 4 个手动连通性脚本没有在本机执行：当前命令行未找到
  `ollama`。这不是代码失败，也不能视为已验证；恢复 Ollama 后可单独运行
  `test/ai_engine/1/test_emotion.py`、`test_llm.py`、`test_pipeline.py` 与
  `test/ai_engine/2/test_embedding.py`。

## 2026-10-19：本地启动入口

项目根目录新增 `启动 MuseGarden.bat` 和 `scripts/Start-MuseGarden.ps1`。这不是 Engine
内部的自动模型切换：它只负责确认或启动本机 Ollama、ACE-Step、Garden API 和 Vite，等待
四个本地端口就绪后打开花园网址。ACE-Step 路径可用 `MUSEGARDEN_ACESTEP_HOME` 覆盖，运行
日志写入 `development/runtime_logs/`。已在本机完成一次不打开浏览器的端到端启动验收。
