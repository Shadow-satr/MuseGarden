"""
MuseGarden Music Engine 开发进度

目录整理后，历史记录中的 database/demo/ 与 scripts/demo_full_creation_flow.py
分别位于 development/data/demo/ 与 development/scripts/demo_full_creation_flow.py；
历史记录中的 scripts/manual_ace_step_provider.py 现位于 development/scripts/。

本文件只记录 Music Engine 的开发状态。
AI Engine 的开发历史请查看：
docs/architecture/AIEngine_progress.py。
跨模块最新状态：docs/architecture/MuseGarden_progress.py。
"""

CURRENT_STATUS = "Music Engine 已支持真实生成、同 Revision 多候选和当前音频选择；正式 Frontend 已接入基于最新 Blueprint 的音乐修改、V1 / V2 / V3 历史播放与当前版本选择。"

STEP_13_1 = """
Step 13.1：Music Model Selection & POC
======================================

状态：通过。

最终方案：
- 本地模型：ACE-Step 1.5。
- 最终运行目录：D:\\MuseGarden-ace-step-poc\\ACE-Step 1.5。
- 本机硬件：NVIDIA GeForce RTX 4060 Laptop GPU，8,188 MiB 显存。
- 实际配置：acestep-v15-turbo（非 XL）+ acestep-5Hz-lm-0.6B。
- 推理方式：PyTorch、单任务串行、自动 CPU offload。
- 调用方式：官方 REST API，仅监听 127.0.0.1:8001。

已验证：
1. API 可正常启动并通过健康检查。
2. API 调用链可用：
   POST /release_task → POST /query_result → GET /v1/audio。
3. 已真实生成并验证一段纯音乐 WAV：
   database/demo/audio/ace_step_poc_01.wav。
4. 固定 POC 参数为 instrumental=true、20 秒、108 BPM、C Major、WAV、
   seed 20260929。
5. 音频验证结果：20.000000 秒、48 kHz、立体声、WAV / FLOAT、
   7,680,088 bytes。
6. 最终运行代码已针对 0.6B LM 调整加载检查，不会因未使用的 1.7B LM
   而触发大模型重复下载。

结论：
ACE-Step 1.5 是本机当前可行的本地 Music Provider 路径。
正式接入应继续使用本地 REST API、单任务串行队列与 CPU offload。

本 Step 未实现：
- MusicBlueprint → Prompt Builder
- 正式 Generator 或 Provider 抽象
- Schema、MusicTask、音频版本管理
- FastAPI、前端或 AI Engine 数据模型修改

详细实测记录见：
docs/architecture/music_provider_evaluation.md。
"""


STEP_13_2 = """
Step 13.2：MusicBlueprint to GenerationSpec Adapter
===================================================

状态：通过。

开发目标：
在不调用 ACE-Step、LLM 或任何网络服务的前提下，建立 AI Engine 与未来
Music Provider 之间稳定、可验证的输入边界。

新增文件：
- music_engine/schema.py
- music_engine/adapter.py
- test/music_engine/1/test_blueprint_adapter.py
- ai_engine/blueprint/progression.py（与 AI Engine 共享的 progression 标签定义）

MusicGenerationSpec：
- caption：非空的音乐描述；常见值输出英文，未知自由文本保留原文。
- duration_seconds：正整数，MVP 默认 20 秒。
- bpm：正整数。
- key：非空调性文本。
- instrumental：固定默认 True。
- seed：None 或非负整数，供后续复现使用。

字段映射：
- MusicBlueprint.tempo → MusicGenerationSpec.bpm。
- MusicBlueprint.key → MusicGenerationSpec.key。
- 调用方未传 duration_seconds 时使用 20。
- 调用方未传 seed 时保持 None。
- 当前 MVP 固定 instrumental=True。

Caption 规则：
以确定性 Python 规则组合主情绪、乐器、texture、progression、energy 和
valence；energy 与 valence 使用五档近似语义映射，而非伪精确控制值。常见
中英文值使用小型映射，未知自由文本安全保留。secondary_emotions 与 scene
继续完整保存在 Blueprint / Memory 中，但当前不进入核心 caption：二者更适合
描述用户经历，而不是作为第一版音乐模型的主控制信息。
不调用 qwen、Ollama、ACE-Step REST API 或其他翻译/生成模型。

Progression 约束：
MusicBlueprint.progression 已改为 AI Engine 共享模块定义的 18 个受限音乐发展
标签。Adapter 只查表生成固定英文发展描述，不再接受或拼接自由 progression
文本；这使 Prompt、Schema 与 Music Engine 的音乐结构语义保持一致。

数据流：
AI Engine MusicBlueprint → blueprint_to_generation_spec() → MusicGenerationSpec。
本 Step 到此结束，不包含 Provider、任务提交、轮询、音频下载或存储。

测试覆盖：
- 常规映射、默认值和显式 seed/duration。
- Caption 中的主情绪、乐器、texture、progression、能量和情绪倾向；并确认
  scene 与 secondary_emotions 不会误进入 caption。
- energy / valence 五档、确定性、Blueprint 不被修改、开放情绪文本回退。
- 18 个正式 progression 标签与固定英文发展描述的一一对应。
- Pydantic 校验、JSON 序列化，以及源码不引入 LLM 或 REST 调用。
"""


STEP_13_3 = """
Step 13.3：ACE-Step Provider Client
===================================

状态：通过。

开发目标：
将 MusicGenerationSpec 发送到 Step 13.1 已验证的本地 ACE-Step 1.5 REST API，
完成提交、轮询和临时音频下载；本 Step 不保存 MuseGarden 正式音频文件。

新增文件：
- music_engine/providers/__init__.py
- music_engine/providers/ace_step.py
- test/music_engine/1/test_ace_step_provider.py
- scripts/manual_ace_step_provider.py

新增结果契约：
- AceStepGenerationResult：task_id、非空 audio_bytes、content_type。结果只存在于
  调用方内存中，不含 CreationDraft、MusicMemory、音频路径或调试 metadata。

已按本机 ACE-Step 实际接口实现的调用链：
MusicGenerationSpec → POST /release_task → POST /query_result（轮询）
→ GET /v1/audio → AceStepGenerationResult。

实际请求映射：
- caption → prompt。
- duration_seconds → audio_duration。
- bpm → bpm。
- key → key_scale。
- 固定 WAV → audio_format="wav"。
- 固定单条任务 → batch_size=1。
- 固定本机模型 → acestep-v15-turbo、acestep-5Hz-lm-0.6B、lm_backend="pt"。
- ACE-Step REST Schema 没有独立 instrumental 字段；纯音乐通过 lyrics="" 表达。
- seed 有值时传 seed 且 use_random_seed=false；seed=None 时只传
  use_random_seed=true，不伪造 -1、0 或本地随机值。

轮询与错误处理：
- API 状态 0 表示 queued/running，1 表示 succeeded，2 表示 failed。
- 默认每 2 秒轮询，默认 600 秒超时；不会无限等待。
- 对本地服务不可用、HTTP 错误、异常 JSON、缺失 task_id、失败任务、超时、
  成功任务缺少音频地址、下载失败与空音频均抛出明确异常。
- Provider 不自动启动、安装或切换模型；服务不可用时提示先运行
  D:\\MuseGarden-ace-step-poc\\ACE-Step 1.5\\start_musegarden_api.bat。

测试：
- Mock HTTP 测试已通过，覆盖真实 payload 字段、seed 两种行为、提交、处理中轮询、
  成功、失败、超时、HTTP/JSON 异常、非空下载与 generate_audio 串联。
- Step 13.2 Adapter 回归测试仍通过。
- 客户端使用 requests 直接表达 HTTP 请求，不保留 urllib 的底层协议封装或 Provider
  工厂；这符合当前单一 ACE-Step Provider 的 MVP 范围。

测试目录规则：
- `test/music_engine/1/` 当前包含 Adapter、ACE-Step Provider、AudioArtifact Schema、
  AudioStore 与 MusicGenerationService 五份测试。
- `test/music_engine/2/` 当前包含 Audio Version Lifecycle 与 Current Audio Selection
  、Draft Music Workspace、Music Confirmation Bundle 与 Final Creation 五份测试。
- 每个编号目录最多放 5 份测试；第二组现已满，下一份 Music Engine 测试应创建在
  `test/music_engine/3/`。

真实集成验证：
- scripts/manual_ace_step_provider.py 已准备固定 20 秒纯音乐请求，调用新的
  AceStepClient，不写入 MuseGarden 正式音频目录。
- 已于 2026-10-05 使用该脚本对 127.0.0.1:8001 完成真实生成。ACE-Step 在自身
  临时输出目录生成 WAV；MuseGarden 未复制或命名该文件。
- 随后使用 AceStepClient.download_audio() 经 GET /v1/audio 读取真实音频：
  content_type=audio/wav、7,680,088 bytes、RIFF 文件头。
- 音频可正常解码：20.000 秒、48 kHz、双声道、WAV / FLOAT。

本 Step 未实现：
- 音频持久化、命名、数据库、版本管理或与 CreationDraft / MusicMemory 关联。
- Provider 抽象工厂、FastAPI、前端、Flower Engine 或 AI Engine 修改。
"""


STEP_13_4 = """
Step 13.4：AudioArtifact Schema
===============================

状态：通过。

开发目标：
定义 MuseGarden 对一份已生成音乐资产的统一 metadata 契约。它描述音频属于哪次
创作、对应哪个 BlueprintRevision、实际使用过的生成输入，以及未来文件的保存位置；
它本身不保存 WAV 文件。

新增内容：
- music_engine/schema.py：AudioArtifact。
- test/music_engine/1/test_audio_artifact_schema.py。

AudioArtifact 字段：
- id：自动生成的 UUID，表示音频资产自身。
- draft_id：所属 CreationDraft 的 UUID。
- revision_id：生成依据 BlueprintRevision 的 UUID，而非版本序号。
- generation_spec：完整的 MusicGenerationSpec 快照。
- provider：当前默认 "ace_step"；不引入 Provider Enum 或注册表。
- provider_task_id、content_type、file_path：不可为空白的 Provider 任务、MIME 类型与
  未来本地文件路径。
- created_at：自动生成的带时区北京时间。

关系与数据流：
CreationDraft → BlueprintRevision → MusicGenerationSpec → ACE-Step → AudioArtifact。
一个 Draft 可以有多份 Revision；每一份 Revision 未来可以关联不同的 AudioArtifact。
draft_id 表示所属创作，revision_id 精确表示产生该音乐的设计版本。

快照语义：
generation_spec 包含 caption、duration_seconds、bpm、key、instrumental 与 seed。
创建 Artifact 时会复制该 Pydantic 对象，因此调用方之后修改原对象，不会改写历史资产的
实际生成输入记录。

测试覆盖：
- 正常创建、自动 UUID、北京时间、Draft / Revision UUID 保留与默认 Provider。
- MusicGenerationSpec 完整嵌套和 JSON 序列化。
- generation_spec 独立快照。
- provider_task_id、content_type、file_path 空白，以及无效 UUID、无效生成规格会被
  Pydantic 拒绝。
- AudioArtifact 的字段中不存在 audio_bytes。

本 Step 未实现：
- WAV 文件写入、音频目录、Audio Store、audio_artifacts.json 或文件命名。
- AceStepClient、Draft / Revision Manager、MusicMemory、confirm_draft 的任何修改。
- 音频查询、版本管理、自动生成、FastAPI、前端或 Flower Engine。
"""


STEP_13_5 = """
Step 13.5：Audio Persistence / AudioStore
==========================================

状态：通过。

开发目标：
将 Step 13.3 已生成的 AceStepGenerationResult.audio_bytes 保存为真实 WAV 文件，
并保存对应的 AudioArtifact metadata。本 Step 只做持久化，不调用 ACE-Step，也不串联
Blueprint、Adapter、Provider 与 Store。

新增内容：
- music_engine/audio_store.py：直接、单一的 AudioStore。
- test/music_engine/1/test_audio_store.py：pytest 临时目录测试。

保存位置与命名：
- 默认数据根目录：database/local/。
- 音频文件：database/local/audio/<audio_artifact_id>.wav。
- metadata：database/local/audio_artifacts.json。
- Artifact.file_path 保存相对 data root 的 audio/<audio_artifact_id>.wav，不写入开发者
  电脑的绝对路径。

保存流程：
1. AudioStore.save() 接收 draft_id、revision_id、MusicGenerationSpec 和
   AceStepGenerationResult。
2. 创建新的 AudioArtifact UUID，以该 UUID 构造文件名和相对 file_path。
3. 先将 audio_bytes 写入临时音频文件，再原子替换为正式 WAV。
4. 创建 AudioArtifact（provider 固定默认 ace_step，task ID / content type 来自生成结果），
   并原子写入完整 JSON metadata 列表。
5. 若 metadata 写入失败，删除本次刚创建的正式 WAV，不留下无法追踪的音频文件。

最小读取能力：
- get(audio_id) 返回对应 AudioArtifact 或 None。
- load_audio(audio_id) 返回对应真实文件的 bytes。
- 同一 Draft / Revision 可多次保存，生成不同 UUID 文件，不会覆盖以前的音频。

测试覆盖：
- 使用 pytest tmp_path，因此不会污染 database/local/audio/ 或 audio_artifacts.json。
- 正常 WAV 保存、字节一致性、UUID 文件名、metadata JSON、无 audio_bytes metadata、
  Draft / Revision / GenerationSpec / Provider 字段、get() 与 load_audio()。
- 同一 Revision 两次保存产生不同的 Artifact 与真实文件。
- metadata 写入失败时清理刚写入的音频文件。
- 空 audio_bytes 继续由 AceStepGenerationResult 的 Pydantic 契约在进入 Store 前拒绝。

本 Step 未实现：
- ACE-Step 调用、自动 Blueprint → Generation → Storage 服务。
- 音频查询、删除、版本选择、版本恢复，或与 Draft / Revision / Memory Manager 的业务连接。
- FastAPI、前端、Flower Engine 或任何新的 Provider 抽象。
"""


STEP_13_6 = """
Step 13.6：MusicGenerationService
=================================

状态：通过。

开发目标：
为上层提供生成音乐的统一业务入口，隐藏 Adapter、ACE-Step Provider 与 AudioStore 的
内部调用顺序。调用方只需提供 draft_id、BlueprintRevision，以及可选的 duration_seconds
和 seed，即可得到一个新的 AudioArtifact。

新增内容：
- music_engine/service.py：MusicGenerationService。
- test/music_engine/1/test_music_generation_service.py。

输入与输出：
- 输入：draft_id、revision、duration_seconds=20、seed=None。
- 输出：AudioArtifact。
- revision 使用 revision.blueprint 生成 MusicGenerationSpec，并使用 revision.id 作为
  AudioArtifact.revision_id；不使用 revision.version 代替 UUID 关联。

编排流程：
BlueprintRevision.blueprint
→ blueprint_to_generation_spec(duration_seconds, seed)
→ AceStepClient.generate_audio(spec)
→ AudioStore.save(draft_id, revision.id, spec, result)
→ AudioArtifact。

依赖边界与错误处理：
- AceStepClient 与 AudioStore 均从构造函数注入；Service 不负责 Provider 配置或存储路径。
- Service 不重新实现 caption、HTTP、轮询、WAV 写入或 JSON metadata 写入。
- Provider 与 Storage 的原始异常自然向上传递，不创建笼统的 Service 异常包装。
- 每次调用都会请求一次新的生成并保存新的 Artifact；不查询旧音频，也不在 Service 层
  阻止同一 Revision 的再次生成。

测试覆盖：
- 真实 Adapter + Mock AceStepClient + tmp_path AudioStore 的轻量集成测试。
- Blueprint / Revision 不被修改；duration_seconds、seed、draft_id、revision.id、Spec 与
  Provider Result 均按原值传递。
- Provider 错误与 Storage 错误向上传递。
- 同一 Revision 连续生成两次得到两个不同的 AudioArtifact。
- 未调用真实 ACE-Step，未污染 database/local。

本 Step 未实现：
- Draft Store 查询、自动选择当前 Revision、当前音频选择或任何音频生命周期策略。
- 音频删除、恢复、比较、MusicMemory / confirm_draft 修改。
- FastAPI、前端、任务队列、并发生成、多 Provider Factory 或 Flower Engine。
"""


STEP_13_7 = """
Step 13.7：Audio Version Lifecycle
==================================

状态：通过。

开发目标：
建立最小的音频版本查询规则，回答某一 BlueprintRevision 或 CreationDraft 已经生成过
哪些 AudioArtifact，以及该 Revision 当前默认播放哪一份音频。

新增内容：
- AudioStore.list_by_revision(revision_id)：按 created_at 从旧到新返回该 Revision 的
  全部 AudioArtifact。
- AudioStore.list_by_draft(draft_id)：按 created_at 从旧到新返回该 Draft 的全部
  AudioArtifact。
- AudioStore.get_latest_by_revision(revision_id)：返回最新 Artifact；没有记录时返回 None。
- music_engine/version_service.py：轻量 MusicVersionService。
- test/music_engine/2/test_music_version_service.py。

当前规则：
current audio = 该 Revision created_at 最新的一份 AudioArtifact。
不保存 current_audio_id，也没有额外的状态文件。查询显式按 created_at 排序，不依赖
audio_artifacts.json 的数组顺序。

服务接口：
- list_for_revision(revision_id) 直接代理 AudioStore.list_by_revision()。
- list_for_draft(draft_id) 直接代理 AudioStore.list_by_draft()。
- get_current_for_revision(revision_id) 直接代理 get_latest_by_revision()。
MusicVersionService 不注入 AceStepClient、不生成音频，也不修改 MusicGenerationService。

Revision 恢复语义：
上层恢复到旧 Revision 后，可以用 get_current_for_revision(revision.id) 取得该 Revision
过去最后生成的一份音频；如果没有生成记录则得到 None。是否重新生成由上层未来决定。

测试覆盖：
- 无记录返回空列表 / None。
- 同一 Revision 的三份 Artifact 全部可查，且不会混入其他 Revision。
- 同一 Draft 的多个 Revision 音频可查，且不会混入其他 Draft。
- 特意打乱 metadata JSON 数组后，仍按 created_at 排序并正确返回最新 Artifact。
- 查询不会改写 metadata JSON 或真实 WAV bytes。
- MusicVersionService 的三个方法正确委托给 AudioStore。
- 测试使用 tmp_path，不调用 ACE-Step 或 LLM。

本 Step 未实现：
- current_audio_id 持久化、手动将旧音频设为当前、删除、恢复、比较或自动重新生成。
- MusicGenerationService、AI Engine Revision / Draft / Memory / confirm_draft 的修改。
- FastAPI、前端、队列、并发生成或 Flower Engine。
"""


STEP_13_8 = """
Step 13.8：Current Audio Selection
===================================

状态：通过。

开发目标：
允许用户显式选择某一份历史 AudioArtifact 作为指定 BlueprintRevision 的当前音频，
同时保留 13.7 的向后兼容规则：没有显式选择时，当前音频仍是最新生成的一份。

状态设计：
- AudioArtifact 是不可变的历史生成记录，不增加 is_current 字段。
- database/local/current_audio.json 单独保存轻量映射：revision_id → audio_id。
- 显式选择相当于 pin；只有 select_current() 或 clear_current_selection() 改变它。

新增内容：
- AudioStore.get_selected_audio_id(revision_id)。
- AudioStore.set_selected_audio(revision_id, audio_id)。
- AudioStore.clear_selected_audio(revision_id)。
- MusicVersionService.select_current(revision_id, audio_id)。
- MusicVersionService.clear_current_selection(revision_id)。
- test/music_engine/2/test_current_audio_selection.py。

当前音频规则：
1. 若 current_audio.json 存在该 Revision 的显式 audio_id，读取并返回对应 Artifact。
2. 若没有显式选择，返回 AudioStore.get_latest_by_revision()。
3. 若完全没有音频，返回 None。
4. clear_current_selection() 取消 pin，恢复“latest 为 current”的自动模式。

一致性与边界：
- select_current() 先确认 audio_id 存在，且该 Artifact.revision_id 与请求 Revision
  完全一致；跨 Revision 选择会被拒绝。
- 显式映射引用不存在 Artifact，或指向其他 Revision 时，抛出明确 RuntimeError，
  不会静默回退到 latest。
- 选择不会复制、重命名或修改 WAV，不会创建新 Artifact，不会调用 ACE-Step 或 LLM。
- MusicGenerationService 保持不变：新生成音频不会覆盖已显式 pin 的选择；无 pin 时
  latest 会自然成为 current。

测试覆盖：
- 无显式选择时 current=latest；选择较旧 Artifact 后会持久化并覆盖默认规则。
- 重建 AudioStore / MusicVersionService 后显式选择仍有效。
- 新生成 Artifact 不会覆盖显式选择；clear 后恢复最新 Artifact。
- 清除不存在选择保持安全；不存在 audio_id、跨 Revision 选择和失效映射都会明确失败。
- 选择前后 metadata JSON 与 WAV bytes 不变，全部测试使用 tmp_path。

本 Step 未实现：
- 音频删除、恢复、比较、波形、重命名或自动重新生成。
- BlueprintRevision、Draft / Memory / confirm_draft、MusicGenerationService 的修改。
- FastAPI、前端、Flower Engine、并发生成或队列。
"""


STEP_13_9 = """
Step 13.9：Draft Music Workspace
================================

状态：通过。

开发目标：
将 Music Engine 接到 AI Engine 既有的 CreationDraft / BlueprintRevision 生命周期。
上层只需提供 draft_id，即可对该 Draft 的当前 Revision 生成音乐、查询候选、取得当前
音频、选择或清除选择，无需自行处理 revision_id、Adapter、Provider 或 AudioStore。

新增内容：
- music_engine/workspace.py：MusicWorkspaceService。
- test/music_engine/2/test_music_workspace.py。

当前 Revision 的确定方式：
1. 通过 AI Engine 公开的 load_drafts() 确认 Draft 存在。
2. 通过公开的 load_revisions(draft.id) 读取该 Draft 的版本历史。
3. 在历史中倒序查找与 Draft 当前 Blueprint 相同的 Revision，作为当前 Revision。
4. 没有 Revision 或 Draft 不属于任何历史版本时明确报错。
Workspace 不读取 JSON、不创建 current_revision_id，也不重写 AI Engine Revision 逻辑。

服务接口：
- generate_current(draft_id, duration_seconds=20, seed=None)：委托
  MusicGenerationService.generate_for_revision()。
- list_current_revision_audio(draft_id)：委托 MusicVersionService.list_for_revision()。
- get_current_audio(draft_id)：委托 MusicVersionService.get_current_for_revision()；当前
  Revision 没有音频时返回 None，不自动生成。
- select_audio(draft_id, audio_id)、clear_audio_selection(draft_id)：委托当前 Revision 的
  MusicVersionService 选择接口。

Revision 更新语义：
- Draft 编辑产生新 Revision 后，Workspace 自动操作新 Revision；旧 Revision 音频不会
  自动成为新设计的音频。
- Restore 历史 Blueprint 会直接切回旧 Revision；它原有的 AudioArtifact 会重新显示，且不复制
  Revision、metadata 或 WAV。
- 跨 Revision 选择由 MusicVersionService 保证；Workspace 只把当前 Revision.id 传入，
  不重复实现底层选择校验。

测试覆盖：
- 生成、列表、当前读取、选择、清除均使用正确当前 Revision 与 draft_id，duration / seed
  原样透传。
- Draft 不存在、无 Revision、Draft 不属于任何 Revision 时明确报错。
- 编辑后的新 Revision 不会复用旧音频；切回历史 Revision 则使用它原有的音频。
- 当前 Revision 尝试选择旧 Revision 的 Audio 会由 Version Service 拒绝。
- 测试全部 Mock MusicGenerationService / MusicVersionService，不调用 ACE-Step、LLM、
  AudioStore 文件读写或真实 AI Engine JSON 数据。

本 Step 未实现：
- Audio 删除、清理、比较、波形、最终确认成果归档。
- Draft confirmation、MusicMemory、Revision Manager、MusicGenerationService 的修改。
- FastAPI、前端、Flower Engine、并发生成、队列或多 Provider。
"""


STEP_13_10 = """
Step 13.10：Music Confirmation Bundle
======================================

状态：通过。

开发目标：
在真正跨 Engine 最终确认之前，冻结当前 Draft 对应的 BlueprintRevision 与当前应使用的
AudioArtifact，形成稳定的 MusicConfirmationBundle 交接对象。本 Step 不持久化 Bundle，
不修改 AI Engine confirm_draft()，也不创建 Final Creation。

新增内容：
- music_engine/schema.py：MusicConfirmationBundle。
- MusicWorkspaceService.prepare_confirmation(draft_id)。
- test/music_engine/2/test_music_confirmation.py。

Bundle 字段与快照语义：
- draft_id：当前 CreationDraft UUID。
- revision_id：当前 BlueprintRevision UUID。
- blueprint：当前 Revision 的完整 MusicBlueprint 独立快照。
- audio_artifact：当前实际选择的 AudioArtifact 独立快照。
Bundle 不重复保存 bpm、key、caption、seed、provider 或 file_path；这些信息已经包含在
Blueprint / AudioArtifact 内。外部之后修改 Revision 或 AudioArtifact 对象，不会篡改已创建
Bundle 的内容。

准备确认流程：
1. 复用 Workspace 既有 _get_current_revision()，不重写 Draft / Revision 查询。
2. 通过 MusicVersionService.get_current_for_revision(revision.id) 获取当前音频，因此会尊重
   13.8 的显式 pin；没有 pin 时自然使用 latest。
3. 当前 Revision 没有音频时明确失败；不会自动调用 ACE-Step，也不会拿旧 Revision 音频。
4. 确认音频的 draft_id 与 revision_id 分别匹配当前 Draft / Revision 后，构造并返回 Bundle。

新 Revision / Restore 语义：
编辑或 Restore 产生新的 Revision 后，它必须先拥有自己生成的 AudioArtifact，才能准备确认。
即使 Restore 后 Blueprint 内容和旧 Revision 相同，也不会复用旧音频。

测试覆盖：
- 当前 Revision + 当前音频可构造 Bundle，字段关联正确。
- 模拟 Version Service 返回 pinned 而非 latest 的音频，Bundle 使用 pinned 音频。
- Bundle Blueprint / AudioArtifact 为独立快照。
- 无当前音频、跨 Draft 音频、跨 Revision 音频均明确失败。
- Restore 风格的新 Revision 无音频时无法确认。
- 测试不调用生成服务、ACE-Step、LLM、AudioStore 文件写入或 AI Engine confirm_draft()。

本 Step 未实现：
- FinalCreation、Bundle 持久化、confirm_draft() 修改、MusicMemory 修改或 Draft 删除。
- WAV 移动 / 复制、音频删除、最终成果存储、FastAPI、前端、Flower Engine、队列或多 Provider。
"""


STEP_13_11 = """
Step 13.11：Final Creation / Cross-Engine Confirmation
=======================================================

状态：通过。

开发目标：
完成 Music Engine 与 AI Engine 的首次正式最终确认。用户确认后，AI Engine 保留用于
个性化的 MusicMemory，Music Engine 保存代表产品正式成果的 FinalCreation；Draft 结束其
未完成生命周期，Revision 历史和 WAV 文件保留原位。

新增内容：
- music_engine/final_creation.py：FinalCreation 与 FinalCreationStore。
- music_engine/finalization.py：CreationFinalizationService。
- test/music_engine/2/test_final_creation.py。

FinalCreation：
- 保存 id、draft_id、revision_id、memory_id、audio_artifact_id、blueprint、
  audio_artifact、confirmed_at。
- Blueprint 和 AudioArtifact 都是独立快照；Schema 还确保 AudioArtifact 的 ID、Draft 与
  Revision 关系和 FinalCreation 字段一致。
- FinalCreation 是用户正式完成的产品成果，不是 MusicMemory 或 AudioArtifact 的别名。
- 使用 database/local/final_creations.json 原子持久化；每个 Draft 只能有一份最终成果。

最终确认流程：
1. 先调用 MusicWorkspaceService.prepare_confirmation()；无当前 Revision 音频时立刻失败，
   不会调用 confirm_draft()。
2. 复用 AI Engine confirm_draft() 创建 / 复用 MusicMemory，并按既有逻辑删除 Draft。
3. 用 Bundle 当前 Blueprint 与当前 AudioArtifact、以及真实 MusicMemory.id 创建并保存
   FinalCreation。
4. 重复 finalize(draft_id) 时先查询 FinalCreationStore，已有成果直接返回，不创建第二份
   Memory 或 FinalCreation。

一致性处理：
- 当前 AI Engine confirm_draft() 先保存 Memory，再删除 Draft，并以 Draft UUID 作为
  Memory UUID；FinalizationService 检查返回的 memory.id 与 Bundle.draft_id 一致。
- FinalCreation 保存失败时，服务恢复确认前的 Draft。下次重试会复用已有 Memory，现有
  confirm_draft() 会完成 Draft 删除，随后可再次归档 FinalCreation，不产生重复 Memory。
- Draft 恢复本身失败时抛出明确 RuntimeError，不静默掩盖可能的半完成状态。

确认语义与边界：
- 最终成果严格使用 Bundle 的当前音频，因此显式 pin 优先于 latest。
- 不复制、不移动、不重命名 WAV；FinalCreation 只保存 AudioArtifact 快照并继续引用原文件。
- 不清理 current_audio.json，不删除 BlueprintRevision 历史，也不把音频塞进 MusicMemory。
- 本 Step 不修改 confirm_draft()、MusicMemory Schema、Draft / Revision Manager 或
  MusicGenerationService。

测试覆盖：
- 合法 Bundle 可确认、写入 JSON、重新读取、Blueprint / Audio 快照和幂等重复调用。
- 音乐准备失败时 confirm_draft() 不被调用；confirm_draft() 失败时不创建 FinalCreation。
- 最终归档失败会恢复 Draft，供后续安全重试。
- Memory ID 不一致会恢复 Draft 并明确失败。
- 所有测试使用 tmp_path / Mock，不调用 ACE-Step、Ollama，也不操作真实 database/local。

本 Step 未实现：
- FlowerArtifact、Flower Engine、Garden placement、最终成果搜索。
- Audio 删除、清理、比较、波形、FastAPI、前端、并发生成、队列或多 Provider。
"""


STEP_13_12 = """
Step 13.12：End-to-End Validation & Music Engine Closeout
==========================================================

状态：自动验证通过；真实 DiT-only V1 生成通过。

开发目标：
不再新增 Music Engine 业务模型；使用一条完整自动端到端链路验证从用户输入到
FinalCreation 的数据关系，并补充可供真实本地模型人工验证的终端 Demo 与架构说明。

新增内容：
- test/music_engine/3/test_music_engine_end_to_end.py。
- scripts/demo_full_creation_flow.py。
- docs/architecture/music_engine.md。

自动端到端验证：
- 真实临时 Draft / Revision / Memory JSON Store、真实 AudioStore、真实 FinalCreationStore，
  配合 Fake ACE-Step Client 与 Mock AI Blueprint 生成 / 编辑。
- 正式 start_creation() 保存 Draft 与 V1；V1 生成第一段 AudioArtifact。
- 正式 edit_creation_draft() 创建 V2；V2 不继承 V1 音频，必须自己生成。
- V2 生成两个候选并 pin 较早候选；MusicConfirmationBundle 和 FinalCreation 均使用该 pin，
  而非较新的候选。
- finalize() 创建 MusicMemory、删除 Draft、保留 Revision 历史、保存 FinalCreation；重复
  finalize() 返回已有成果，不创建第二份最终成果。
- 测试全过程只使用 tmp_path，不污染 database/local，也不调用 Ollama 或 ACE-Step。

手动真实 Demo：
- demo_full_creation_flow.py 复用 start_creation、edit_creation_draft、
  MusicWorkspaceService 与 CreationFinalizationService。
- 人工运行时先生成 V1 Blueprint 与对应音乐，然后进入完整交互菜单：查看当前状态、自然语言修改
  Blueprint、查看或恢复历史 Revision、为当前 Revision 生成额外候选、选择 current audio、最终确认。
  修改创建新的当前 Revision；恢复历史 Blueprint 则直接切回源 Revision，恢复它已有的 current audio，
  不创建重复 Revision 或 WAV。只有
  输入 YES 才会执行最终确认。
- Demo 会先检查 Ollama 与 ACE-Step 是否可访问；任一服务不可用时在创建 Draft 前退出，
  避免留下只有半条流程的新草稿。
- 需要本机 Ollama qwen2.5:3b 和 ACE-Step API 127.0.0.1:8001 都已启动；它会写入
  database/local，因此与自动测试分离。
- 真实模型验证结果（2026-10-09）：此前 `thinking=true` 的 LM+DiT 请求在 600 秒内未完成，
  GPU 利用率观测为 0%，没有生成 WAV；该路径不采用为当前项目运行方案。
- 已根据官方 API 语义切换为 DiT-only：`thinking=false`、关闭 CoT caption/language，且
  ACE-Step 启动脚本显式设定 `ACESTEP_INIT_LLM=false` 与
  `ACESTEP_OFFLOAD_DIT_TO_CPU=true`。重启后，真实 Demo 成功完成用户输入 → AI Engine
  V1 Blueprint → ACE-Step → AudioStore 链路；生成音频为
  `database/local/audio/7a1bf183-fff3-4f66-967c-8073762484a8.wav`。
- 该 WAV 已解码验证为 20.000 秒、48 kHz、双声道、32-bit float。Demo 在生成后按菜单 `0`
  暂停，因此保留可继续编辑的 Draft 与音频，但没有代替用户执行最终确认；跨 Engine 的最终确认
  已由自动端到端测试覆盖。

最终模块结构：
MusicBlueprint → Adapter → MusicGenerationSpec → MusicGenerationService → AceStepClient
→ AudioArtifact / AudioStore → MusicVersionService → MusicWorkspaceService
→ MusicConfirmationBundle → CreationFinalizationService → MusicMemory + FinalCreation。
各层职责与数据文件已记录于 docs/architecture/music_engine.md。

回归与收尾：
- Music Engine pytest 端到端与模块测试均通过（26 项）；既有 Adapter、Provider、Schema 断言测试
  也通过。
- 检查后未移除任何仍被正式流程使用的模块；没有新增 Provider Factory、队列、前端或
  Flower Engine。
- test/music_engine/3/ 当前包含端到端测试一份；第一、二组均已满。

MVP 已支持：
- Blueprint 到本地 ACE-Step 音乐生成、WAV 与 metadata 持久化。
- Revision 多音频候选、latest / pinned current 选择。
- Draft 上下文操作、MusicConfirmationBundle、跨 Engine 最终确认、MusicMemory 与
  FinalCreation 归档。

暂未支持 / TODO：
- Audio 删除、恢复、比较、波形、清理。
- FastAPI、前端、并发 / 队列、多 Provider。
- Flower Engine、Garden placement、最终成果搜索与部署型存储。

下一阶段：
Step 14 — Flower Engine。
"""


DEMO_INTEGRATION_STATUS_2026_10_13 = """
历史 Step 13.12 的“下一阶段”是当时的记录，不代表当前项目状态。Flower Engine 与
Garden 已接入网页 Demo，真实 ACE-Step AudioArtifact 可播放，音乐修改可生成下一份音频。

当前差距：Music Engine 支持同一 BlueprintRevision 多候选和当前音频选择；网页 Demo
没有接入 MusicVersionService 的历史列表/选择，也没有保存完整 BlueprintRevision
历史，只保存当前音乐 Blueprint、音频 ID 和版本号。因此页面只能播放当前版本，
不能选回 V1/V2。旧 AudioArtifact 仍保留在 AudioStore，并非被删除。

用户提出的下一步产品规则是“一版 Blueprint 对应一首音乐”，即改 Blueprint 产生新
Revision，每版只生成一首 AudioArtifact；网页可选历史版本播放。此规则尚未实施，
Music Engine 现有多候选能力也未删除。详见 MuseGarden_progress.py。
"""
