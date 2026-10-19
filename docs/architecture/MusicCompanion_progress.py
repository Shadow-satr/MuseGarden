"""MuseGarden Music Companion 开发进度。"""

CURRENT_STATUS = "Step 1 — Audio Understanding POC 开发中：独立分析包、结果 Schema 与命令行入口已建立；等待 librosa 可用后运行真实 WAV 验证。"


STEP_1 = """
Music Companion Step 1 — Audio Understanding POC
================================================

目标：
验证能否从 Music Engine 已保存的真实 WAV 中提取可解释的基础声学特征；并评估
MOSS-Music 是否值得、且是否能在本机单独部署。此 Step 不接入正式产品流程。

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
  JSON 序列化、无效路径、不可解码文件及源文件不变。测试独立于已满的 Music Engine 目录。

真实样本基线（开始本 Step 时核实）：
- `database/preview/` 有 12 个真实 WAV、12 条 AudioArtifact 和 7 条网页创作记录。
- `database/local/` 有 3 个真实 WAV 与 3 条 AudioArtifact。
- POC 将优先选择 preview AudioStore 中关联清晰的 5–10 个资产；不会为了数量虚构音频。

依赖与验证状态：
- 已把 `librosa>=0.11,<0.12` 写入 `requirements.txt`，但当前虚拟环境尚未完成安装，故未将
  声学分析或自动化测试标记为通过，也没有生成任何假冒的真实分析结果。
- 当前安装尝试受到受限环境网络 / 代理阻断。待依赖可用后，运行真实 WAV 分析、Step 1 测试和
  `music_companion_audio_poc.md` 中的对照实验。

MOSS-Music 初步可行性评估（未运行）：
- 官方仓库当前发布 MOSS-Music-8B-Instruct 与 MOSS-Music-8B-Thinking；总规模均约 9.1B，
  推荐 Python 3.12、单独 Conda 环境、FFmpeg 7，以及 CUDA 12.8 PyTorch 运行时。
- 官方还建议用 SGLang 服务，并要求先下载模型权重。因此不能直接安装进 MuseGarden 主虚拟环境，
  也不能在本 Step 自动下载权重或宣称已有模型描述结果。
- 当前 MuseGarden 虚拟环境未安装 torch / torchaudio；现有机器先前的 ACE-Step 运行记录是
  8 GB 显存 DiT-only 配置。仅据此推断，9.1B MOSS-Music 的本机推理不应在未做独立显存与
  权重评估前承诺可运行。

本 Step 明确未做：
- 不增加数据库表、MusicAnalysis 正式实体、API、前端 UI、自动 Blueprint 修改、RAG 或版本比较。
- 不修改 AI Engine、Music Engine、Flower Engine、Frontend 的业务调用链。
- 不下载 MOSS-Music 权重、不创建模型服务、不把任何模型描述当作真实结果。

完成条件：
1. librosa 环境可用，且自动化边界测试通过。
2. 用 AudioStore 关联的真实 WAV 运行 5–10 份分析，记录数值结果与 Blueprint 对照。
3. 输出 `docs/architecture/music_companion_audio_poc.md`，如实说明 MOSS-Music 是否实际运行。
4. 完成后停止在 Step 1，再决定正式数据结构 / 持久化还是先解决语义模型部署。
"""
