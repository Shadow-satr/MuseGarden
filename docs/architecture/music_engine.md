# Music Engine MVP

Music Engine 把 AI Engine 的 `MusicBlueprint` 转换为可生成、可选择、可确认的音乐成果。

```text
CreationDraft
  → BlueprintRevision
  → MusicWorkspaceService
  → MusicGenerationService
  → MusicGenerationSpec
  → AceStepClient
  → AudioStore
  → AudioArtifact
  → MusicVersionService
  → MusicConfirmationBundle
  → CreationFinalizationService
  → MusicMemory + FinalCreation
```

## 模块职责

- `adapter.py`：确定性地将 `MusicBlueprint` 变为 `MusicGenerationSpec`。
- `providers/ace_step.py`：调用本机 ACE-Step REST API，取得临时音频字节。
- `audio_store.py`：保存 WAV、AudioArtifact metadata，并管理当前音频选择状态。
- `service.py`：按 Revision 编排 Adapter → Provider → Store。
- `version_service.py`：查询 Revision / Draft 的音频历史；默认最新音频为当前，也支持 pin。
- `workspace.py`：依据 Draft 当前 Revision 调用生成和版本服务，供上层使用 Draft ID。
- `final_creation.py`：定义并持久化用户最终成果 `FinalCreation`。
- `finalization.py`：编排“音乐准备 → AI Engine 确认 → 最终成果归档”。

## 数据文件

默认存储在 `database/local/`：

- `audio/<audio_artifact_id>.wav`：真实音频文件。
- `audio_artifacts.json`：音频资产 metadata。
- `current_audio.json`：`revision_id → audio_id` 的可选 pin 映射。
- `final_creations.json`：已经确认完成的用户创作成果。

WAV 不会复制到 FinalCreation；FinalCreation 保存 AudioArtifact 快照并继续引用已有文件。

## 当前音频规则

没有手动选择时，某个 Revision 最新生成的 AudioArtifact 是 current audio。用户 pin 某个
历史候选后，pin 优先于 latest；清除选择后恢复自动 latest 规则。

恢复历史 Blueprint 时，AI Engine 直接切回该既有 Revision，不创建重复的 BlueprintRevision、
AudioArtifact 或 WAV。该 Revision 原来选择的音频会立即重新成为 current audio；只有用户从恢复
后的设计再次修改时，才会创建一个新的 Revision，并需要生成新的音乐候选。

## 最终确认

`workspace.prepare_confirmation(draft_id)` 冻结当前 Revision 与 current audio。没有当前
Revision 音频时会失败，不能混用旧 Revision 的音频。

`CreationFinalizationService.finalize(draft_id)` 复用 AI Engine 的 `confirm_draft()` 创建
MusicMemory，再保存 FinalCreation。重复调用返回同一份 FinalCreation。归档失败时会恢复
Draft，允许利用既有 MusicMemory 幂等语义重试。

## 手动真实 Demo

启动前需准备：

- 本地 Ollama 的 `qwen2.5:3b`，服务地址为 `http://localhost:11434/v1`。
- ACE-Step API，监听 `http://127.0.0.1:8001`。

当前 8 GB 显存配置使用 DiT-only 生成：启动脚本会设置 `ACESTEP_INIT_LLM=false` 与
`ACESTEP_OFFLOAD_DIT_TO_CPU=true`，而 MuseGarden 请求会关闭 ACE-Step 的 `thinking` 与
CoT 自动补全；Blueprint 已经提供所需 caption、BPM、调性与时长。启动脚本变更后须先停止旧
服务，再重新启动它。

从项目根目录运行：

```powershell
.\.venv\Scripts\python.exe scripts\demo_full_creation_flow.py
```

Demo 会先由 AI Engine 生成 V1 Blueprint，并用 ACE-Step 生成真实 V1 音乐。随后进入交互菜单，
完整展示创作会话：查看当前设计、用自然语言修改并创建新的 Blueprint Revision、查看或恢复历史
Revision、为当前 Revision 生成多个音乐候选、选择当前播放音频，以及最终确认。

菜单中的修改会创建新的 Revision；恢复则直接切回历史 Revision 和它已有的音频，不产生重复文件。
新的 Revision 不会沿用不同设计的音频，必须由用户明确选择“生成新的音乐候选”。最终确认前会显示当前 Revision 和当前
AudioArtifact，只有输入 `YES` 才会写入 MusicMemory 和 FinalCreation。Demo 会写入
`database/local/`，因此仅用于人工验证，不属于自动测试。

## MVP 尚未包含

- Audio 删除、恢复、比较、波形和清理。
- FastAPI、前端、任务队列、并发生成和多 Provider。
- Flower Engine、Garden placement 与 FinalCreation 搜索。
