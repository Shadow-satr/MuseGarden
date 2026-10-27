"""MuseGarden Music Companion 开发进度。"""

CURRENT_STATUS = "Music Companion Step 1–3 POC 均已完成；Step 4 已将按需生成、缓存的音乐解读卡接入花朵记忆详情。用户可在 V1/V2 间切换后主动查看对应解读；V2 显示相对上一版的修改指令和证据边界。"


STEP_1 = """
Music Companion Step 1 — Audio Understanding POC
================================================

章节路线：
1. Step 1 — Audio Understanding POC：从真实 WAV 得到可解释的基础声学测量。
2. Step 2 — Music Semantic Understanding POC：只选择一个经验证的模型，检查它能否描述真实音乐。
3. Step 3 — Music Interpretation POC：结合测量、模型描述和创作背景，验证面向普通用户的介绍。

当前 Step 1 目标：
验证能否从 Music Engine 已保存的真实 WAV 中提取可解释的基础声学特征。此 Step 不接入
正式产品流程，也不评估、安装或部署任何音乐理解模型。

已建立：
- `music_companion/schema.py`：POC 结果契约。`AudioAnalysisResult` 明确保存 AudioArtifact
  稳定 ID（如果以资产方式调用）、时长、采样率、声道、可空 BPM 估计、基础声学摘要与
  时间片段。没有把声学数值伪装成情绪、风格或乐器结论。
- `music_companion/audio_analysis.py`：基于 librosa 的 WAV 分析入口。提取 RMS、频谱质心、
  起音强度 / 起音数量、BPM 估计，并默认对前 / 中 / 后三段重复测量。静音音频不会强行
  给出 BPM；短音频、单 / 双声道和无法解码输入都有明确处理。
- `analyze_audio_artifact()` 通过既有 `AudioStore.get()` / `load_audio()` 读取真实资产，再临时
  解码，不由调用方拼接项目音频路径；不会修改源 WAV 或 AudioArtifact。
- 命令行入口：`python -m music_companion.audio_analysis <wav-path>`；可选
  `--artifact-id`、`--segments` 与 `--output`，默认将 JSON 打印到终端。
- `test/music_companion/1/test_audio_analysis.py`：覆盖正常单声道、双声道、静音、短音频、
  JSON 序列化、无效路径、不可解码文件及源文件不变；另使用真实 `AudioStore.save()` /
  `load_audio()` 创建测试 WAV，验证 `analyze_audio_artifact()` 不会替换 AudioArtifact ID。
  测试独立于已满的 Music Engine 目录，且不再以 `pytest.importorskip()` 掩盖依赖缺失。
- 实测修复：初版 `analyze_audio_artifact()` 使用仍打开的 `NamedTemporaryFile` 交给 Windows
  音频解码器，导致拒绝访问。现已改为通过 `BytesIO` 在内存中解码 `AudioStore.load_audio()`
  返回的字节；不修改源 WAV，也不再依赖临时文件句柄。

真实样本基线（开始本 Step 时核实）：
- `database/preview/` 有 12 个真实 WAV、12 条 AudioArtifact 和 7 条网页创作记录。
- `database/local/` 有 3 个真实 WAV 与 3 条 AudioArtifact。
- POC 将优先选择 preview AudioStore 中关联清晰的 3–5 个资产；不会为了数量虚构音频。

依赖与验证结果：
- 目标解释器为 `C:\Users\honor\Desktop\MuseGarden\.venv\Scripts\python.exe`（Python 3.12.14）。
- 已验证 `librosa 0.11.0`、NumPy 2.5.4、SciPy 1.18.1 与 SoundFile 0.14.0 可导入。
- `pytest -q test/music_companion`：4 项通过。保留 6 条第三方库警告（Python 3.12 的 audioread
  弃用提醒、极短合成样本的 mel 滤波器提醒、以及不可解码文件的 fallback 提醒），没有测试失败。
- 通过 preview `AudioStore` 实测 5 份真实 WAV；全部成功解码，详见
  `docs/architecture/music_companion_audio_poc.md`。其中 2 份可可靠关联同一创作的 V1/V2
  BlueprintRevision；另 3 份只有 AudioArtifact metadata / 创作文本关联，未猜测 Revision。

本 Step 明确未做：
- 不增加数据库表、MusicAnalysis 正式实体、API、前端 UI、自动 Blueprint 修改、RAG 或版本比较。
- 不修改 AI Engine、Music Engine、Flower Engine、Frontend 的业务调用链。
- 不下载或部署任何音乐理解模型，不把任何模型描述当作真实结果。

完成条件：
Step 1 完成：以上条件均已满足。人工试听没有执行；RMS、频谱质心、起音和 BPM 都只是声学
测量，不能单独认定情绪、乐器或生成质量。
"""


STEP_2 = """
Music Companion Step 2 — Music Semantic Understanding POC
==========================================================

目标：只验证一个 Music-CLAP 模型能否对真实 AudioStore WAV 的受控音乐语义标签给出稳定、
可审计的相似度排序。标签涵盖情绪、能量、音乐特性和乐器线索；它们不是事实证明或概率。

已建立：
- `music_companion/semantic_analysis.py`：`analyze_audio_artifact_semantics()` 使用现有
  `AudioStore.get()` / `load_audio()`，对真实 WAV 选择固定首 / 中 / 尾窗口并评分。
- `music_companion/schema.py`：Step 2 临时结果契约，包含每段和聚合的原始余弦相似度。
- `test/music_companion/2/`：使用真实 AudioStore 测试资产与假评分器，不下载模型但覆盖
  资产 ID、源文件不变、排序、缺失资产、评分维度异常、确定性窗口选择。
- `requirements-music-companion-step2.txt`：将 GPU 依赖与 Step 1 基础依赖分开，明确固定
  CUDA 12.4 的官方 PyTorch wheel，避免普通镜像误装 CPU wheel。

本机实测：RTX 4060 Laptop GPU（8 GB）/ NVIDIA 驱动 552.46 / CUDA 12.4；已安装
`torch 2.6.0+cu124`，`torch.cuda.is_available()` 为 True。Music-CLAP 权重已下载到项目
`models/music-clap/`（约 614 MB），并经 5 份 preview AudioStore WAV 成功在 CUDA 上推理。V1 重跑的
聚合分数最大差为 0。初版的 `fusion` 预处理不适用于 `unfused` checkpoint 的单通道输入，已改为固定
至多十秒窗口配合 `rand_trunc`，不再报错。

实测发现：V2 的“明亮”与“振奋”相似度高于 V1，但“鼓点”相似度也略高，不能将模型标签当作乐器事实或
Blueprint 是否兑现的结论。2026-10-21 的人工试听确认 V2 确实更轻快，与“明亮 / 振奋”分数上升方向
一致；用户没有对鼓点减少作出试听结论。因此 Step 2 POC 已完成，但鼓点标签在该组样本中必须保留不确定性。

完成条件：CUDA PyTorch、Music-CLAP 和至少 5 份真实 preview AudioStore WAV（含一组 V1/V2）的
运行条件已经满足；人工试听已确认 V2 更轻快，并记录鼓点标签的适用边界。详见
`docs/architecture/music_companion_semantic_poc.md`。

本 Step 明确未做：不增加正式数据库/API/前端，不修改任一生成引擎，不下载第二个音乐模型，
不开始 Step 3 自然语言解释。
"""


STEP_3 = """
Music Companion Step 3 — Professional Music Interpretation POC
===============================================================

目标：将同一份真实 AudioArtifact 的 Step 1 声学测量、Step 2 Music-CLAP 受控标签、精确匹配的
Blueprint / 修改指令以及人工试听反馈，合成为普通用户可以阅读的专业音乐介绍。

已建立：
- `music_companion/interpretation.py`：只使用既有 AudioStore 读取真实资产；检查 Step 1 / Step 2
  结果 UUID 一致；按 revision_id 优先解析版本 Blueprint；调用本地 qwen2.5:3b 形成结构化初稿。
- `music_companion/schema.py`：定义专业介绍、乐器构成、开头 / 中段 / 结尾聆听提示、修改意图对照和
  限制说明的 POC 契约。
- 程序级证据边界：Blueprint 乐器只能写为编配设定；CLAP 乐器标签只能写为音色线索；缺少人工确认时，
  不写“鼓点减少”等结论。小模型漏列的 Blueprint 乐器和声学分段会由程序补全，但不会虚构听感事实。
- `test/music_companion/3/`：覆盖真实 AudioStore、无依据乐器拒绝、版本精确匹配、乐器/分段补全和无
  修改指令时移除无依据意图；`pytest -q test/music_companion` 实测 15 项通过。

真实 V2 验证：资产 `24c9bfa7-e8c3-4dac-9986-b79680d6ae2e` 精确匹配 V2 Blueprint。完整结果输出到
`models/music-clap/interpretation-v2.json`，包含钢琴、弦乐、贝斯、鼓点、吉他、合成器六项编配设定及
三段真实时间范围。人工试听确认 V2 比 V1 更轻快；“鼓点是否减少”没有确认，故整条修改指令只标为
`partially_supported`。详见 `docs/architecture/music_companion_interpretation_poc.md`。

本 Step 明确未做：不接入正式数据库、API、前端或生成引擎，不回写 Blueprint，不安装第二个理解模型，
也不将 POC 结果伪装成声部分离、混音报告或专业制作结论。
"""


STEP_4 = """
Music Companion Step 4 — Result Card Integration
=================================================

目标：把 Step 3 结果从命令行 JSON 接入花朵记忆详情，不让用户打开文件或重复等待模型加载。

已建立：
- 后端 `POST /api/music-companion/<audio_id>`：用户主动请求时生成解读；结果按 AudioArtifact ID 缓存到
  `database/preview/music_companion_interpretations.json`。`GET` 可读取已有缓存。
- 前端 `MusicCompanionCard`：位于当前播放器下方，首次只显示“查看音乐解读”；生成后展示专业介绍、
  编配构成、分段聆听与限制说明。
- 版本切换：卡片随当前选择的 V1 / V2 音频重置。对 V2 等后续版本，会显示相对上一版的修改指令，以及
  Step 3 的支持程度与不确定性；不会展示伪精确分数。
- V2 的已验证解读已写入 preview 缓存，因此首次打开能保留“V2 比 V1 更轻快”的人工试听结论。

验证：前端 `npm run build` 通过；后端和 Music Companion 测试共 18 项通过。

边界：仍不自动执行分析，不阻塞正常生成，不修改 Blueprint 或音频资产，不新增第二个模型。
"""


STEP_5 = """
Music Companion Step 5 — Revision Suggestions
==============================================

目标：在已展开的音乐解读下提供三条由本地语言模型生成的可执行修改建议，帮助用户让旋律、编配层次、
段落衔接或结尾更完整。

已建立：`POST /api/music-companion/<audio_id>/suggestions` 读取当前已验证的解读并生成恰好三条建议；
前端可“给我 3 条建议”或“换一组建议”。刷新时会提交已展示标题，要求新建议避开重复；本地模型不遵循
JSON 契约时，受约束备用建议仍会给出三条不同标题。点击“采用这条建议”会自动展开既有自定义修改框并
填入可编辑的完整指令，用户也始终可直接自定义修改。

边界：建议不自动修改 Blueprint 或生成音频，不把不确定的乐器线索写成事实，不以简单加速或加鼓点代替
音乐性修改。
"""
