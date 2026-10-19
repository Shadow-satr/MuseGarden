# Music Companion Step 1 — Audio Understanding POC

状态：分析实现与样本清单已就绪；真实 `librosa` 测量待依赖可用后执行。

## 目的与边界

本 POC 验证的是“真实 WAV 中可被直接量化的声学信息”，而不是从 Blueprint 反推音频表现。
`MusicBlueprint` 是生成意图；本报告中的 WAV 测量、未来模型描述与基于两者作出的解释会保持分栏，不能相互替代。

本 Step 不写入 Music Engine 数据、不重生成音乐、不添加 API 或前端界面。

## 可复现分析方法

入口：

```powershell
.\.venv\Scripts\python.exe -m music_companion.audio_analysis <已有-wav路径> --artifact-id <AudioArtifact UUID>
```

实现使用 `librosa` 读取 WAV，保持原始采样率与声道数；多声道音频仅为计算全局特征而平均为单声道。输出包括：

- 时长（秒）、采样率（Hz）、声道数；
- RMS 振幅及其均值、范围、标准差；
- 频谱质心（Hz）及其均值、范围、标准差；
- 起音强度及检测到的起音数；
- BPM 估计（静音或无法稳定估计时为 `null`）；
- 前 / 中 / 后时间片段的 RMS、频谱质心与起音强度。

这些是声学测量，不可单独证明情绪、乐器、调性或“音乐变快乐/悲伤”。BPM 尤其可能出现半速或倍速估计。

## 已核实的真实样本池

`database/preview/audio_artifacts.json` 有 12 条 AudioArtifact，对应 12 个 WAV。以下五个样本都可通过现有 AudioArtifact 关联到网页创作文本，覆盖不同 Blueprint 目标 BPM；表中 BPM 只是生成规格的预期，**不是测量结果**。

| AudioArtifact ID | 创作文本摘要 | Blueprint BPM（预期） | 分析状态 |
| --- | --- | ---: | --- |
| `ad1d99c2-b768-4002-adc5-a2b16df13b7f` | 比赛结束后放松、开心 | 120 | 待运行 |
| `cd521efe-9b9b-432b-8b04-7640702ee333` | 现在不开心 | 100 | 待运行 |
| `d37723a2-c46d-4e5b-af1b-35a21cb45ef0` | 与伴侣和好、开心 | 120 | 待运行 |
| `cd379a7e-6e49-482b-b0a6-4fd4606194ab` | 上课无聊、想听有意思的音乐 | 100 | 待运行 |
| `50bce00c-a28d-4963-bbfc-3fb82104f416` | 从生气到原谅伴侣 | 100 | 待运行 |

另有一个同一创作的 V1/V2/V3 组：`d2fcfd4d-…`（100 BPM）、`24c9bfa7-…`（90 BPM）、`1137695e-…`（80 BPM）。依赖就绪后，这组优先用于验证“Blueprint 修改后，真实测量是否随版本发生可见变化”，但不会把目标 BPM 和测得 BPM 一致与否直接判为生成质量。

## 当前真实结果

暂无。项目虚拟环境在本次 POC 开始时没有 `librosa`、SoundFile、PyTorch 或 Torchaudio。已将 `librosa>=0.11,<0.12` 加入依赖清单；安装在当前受限环境被网络代理中断，因此没有伪造数值或模型描述。

自动化测试已覆盖合成单 / 双声道、静音、短音频、不可解码文件、序列化与源文件不变；依赖安装后需执行：

```powershell
.\.venv\Scripts\python.exe -m pytest -q test/music_companion
```

随后使用 `AudioStore` 关联的真实样本执行分析，并把原始 JSON 摘要补充到本报告。人工试听尚未进行，不能标记为已人工验证。

## MOSS-Music 评估

官方仓库当前提供 `MOSS-Music-8B-Instruct` 和 `MOSS-Music-8B-Thinking`，二者总规模均约 9.1B；任务范围包括音乐描述、乐器 / 人声识别、节拍 / 调性 / 和弦推理、结构分析和音乐问答。[官方仓库](https://github.com/OpenMOSS/MOSS-Music)

官方快速开始建议单独使用 Python 3.12 Conda 环境、FFmpeg 7、CUDA 12.8 PyTorch，并推荐 SGLang 服务；模型权重需另行下载。因此它不能作为 MuseGarden 主虚拟环境的普通依赖，也不应在本 Step 自动下载。当前机器先前的 ACE-Step 记录是 8 GB 显存的 DiT-only 方案；这不足以证明 9.1B 音乐理解模型可运行。MOSS-Music 本机推理状态为 **未验证**。

结论（暂定）：先完成低成本、可解释的 librosa 基线。只有在独立环境、可用权重和资源检查明确后，才用真实 WAV 评估 MOSS-Music 的描述价值；在那之前不采用 Mock 文本。

## 下一次执行后要做的判断

1. 基础特征是否在这些真实 WAV 上稳定可得，并能对版本比较提供有用信号。
2. MOSS-Music 是否可在独立环境运行，以及它的真实描述是否值得接入。
3. 再选择先设计正式 `MusicAnalysis` 持久化，还是先解决语义模型部署。
