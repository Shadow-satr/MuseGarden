# Music Companion Step 1 — Audio Understanding POC

状态：Music Companion Step 1 已完成；没有开始 Step 2。

## 目的与边界

本 POC 验证的是“真实 WAV 中可被直接量化的声学信息”，而不是从 Blueprint 反推音频表现。
`MusicBlueprint` 是生成意图；本报告中的 WAV 测量、未来模型描述与基于两者作出的解释会保持分栏，不能相互替代。

Music Companion 重新规划为三个独立 POC：Step 1 测量、Step 2 音乐语义理解、Step 3 面向
用户的解释。本报告只记录 Step 1；不写入 Music Engine 数据、不重生成音乐、不添加 API 或前端界面。

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
| `ad1d99c2-b768-4002-adc5-a2b16df13b7f` | 比赛结束后放松、开心 | 120 | 已实测 |
| `cd521efe-9b9b-432b-8b04-7640702ee333` | 现在不开心 | 100 | 已实测 |
| `d37723a2-c46d-4e5b-af1b-35a21cb45ef0` | 与伴侣和好、开心 | 120 | 已实测 |
| `cd379a7e-6e49-482b-b0a6-4fd4606194ab` | 上课无聊、想听有意思的音乐 | 100 | 本轮未选取 |
| `50bce00c-a28d-4963-bbfc-3fb82104f416` | 从生气到原谅伴侣 | 100 | 本轮未选取 |

另有一个同一创作的 V1/V2/V3 组：`d2fcfd4d-…`（100 BPM）、`24c9bfa7-…`（90 BPM）、`1137695e-…`（80 BPM）。本轮已实测 V1 / V2，用于验证“Blueprint 修改后，真实测量是否随版本发生可见变化”；没有把目标 BPM 和测得 BPM 是否一致直接判为生成质量。

## 实际运行环境与自动化验证

实际使用项目目标解释器 `C:\Users\honor\Desktop\MuseGarden\.venv\Scripts\python.exe`（Python 3.12.14）。
已成功导入 librosa 0.11.0、NumPy 2.5.4、SciPy 1.18.1、SoundFile 0.14.0。

```powershell
.\.venv\Scripts\python.exe -m pytest -q test/music_companion
```

实际结果为 `4 passed`。测试覆盖合成单 / 双声道、静音、短音频、不可解码文件、JSON 序列化、源文件不变，
并通过真实 `AudioStore.save()` / `load_audio()` 创建 WAV 验证 AudioArtifact ID 关联。初版资产分析使用
`NamedTemporaryFile`，在 Windows 上因解码器遇到仍打开的句柄而失败；已改用 `BytesIO` 内存解码，相关测试通过。
独立入口也已实际运行：`python -m music_companion.audio_analysis <wav-path> --artifact-id <UUID>` 对真实
WAV 输出了可序列化 JSON，且不再出现包重复导入警告。

## 真实 WAV 测量

以下 5 份样本均通过 `AudioStore.get()` 和 `AudioStore.load_audio()` 读取，不重新生成音乐、不修改源 WAV。
所有样本均成功解码为 20.000 秒、48,000 Hz、双声道。数值是实际运行结果。

| AudioArtifact ID | BPM 估计 | RMS 均值 | 频谱质心均值 Hz | 起音强度均值 | 起音数 | Revision 关联 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ad1d99c2-b768-4002-adc5-a2b16df13b7f` | 119.681 | 0.039046 | 1685.843 | 0.486872 | 52 | 无可靠 Revision 快照 |
| `cd521efe-9b9b-432b-8b04-7640702ee333` | 125.000 | 0.025878 | 2899.672 | 0.812160 | 61 | 无可靠 Revision 快照 |
| `d37723a2-c46d-4e5b-af1b-35a21cb45ef0` | 119.681 | 0.039499 | 2326.157 | 0.339290 | 28 | 无可靠 Revision 快照 |
| `d2fcfd4d-6be2-4bba-9b5a-f8f1125a7996` | 148.026 | 0.021676 | 2826.841 | 0.608154 | 31 | V1，见下表 |
| `24c9bfa7-e8c3-4dac-9986-b79680d6ae2e` | 119.681 | 0.038393 | 2347.383 | 0.561337 | 81 | V2，见下表 |

### 可可靠关联的 BlueprintRevision 对照

`d2fcfd4d-…` 与 `24c9bfa7-…` 都属于 creation `6196a0ce-12d0-4bb9-b2f7-a3dd49d08d20`。

| 版本 | AudioArtifact | Blueprint / 修改内容 | 实测观察 |
| --- | --- | --- | --- |
| V1 | `d2fcfd4d-…` | 100 BPM、energy 0.8、`gentle_to_climax` | BPM 估计 148.026；第三段 RMS 降至 0.001254、频谱质心升至 4868.441 Hz、起音强度升至 1.084569。|
| V2 | `24c9bfa7-…` | 90 BPM、energy 0.7、`gentle_to_bright`；“更轻快、保留钢琴、减少鼓点、结尾更明亮” | BPM 估计 119.681；第三段 RMS 为 0.012867、频谱质心为 3661.966 Hz、起音强度为 0.693139。|

这只记录可观察差异：两版估计 BPM 都没有等于目标 BPM，且 V2 的后段频谱质心低于 V1。BPM 可能发生倍速 / 半速误判；频谱质心和 RMS 也不能单独证明“更轻快”“更明亮”或某种乐器出现。没有进行人工试听。

```powershell
.\.venv\Scripts\python.exe -m pytest -q test/music_companion
```

## Step 1 完成后的判断

1. 基础特征可从真实 WAV 稳定提取，且能量化版本间的差异；它们适合作为后续解释的证据，不是语义结论。
2. 具备进入单一模型验证的条件（Step 2），但本报告不选型、不安装模型。
3. 不应在 POC 之前建立正式 `MusicAnalysis` 持久化；先验证 Step 2、Step 3 的实际价值。
