# Music Companion Step 2 — Music Semantic Understanding POC

状态：独立代码、CUDA 实测、5 份真实 WAV 分析、自动化测试和一项 V1/V2 人工试听对照均已完成。Step 2 POC 完成；没有接入正式创作流程、数据库或前端。

## 目标与边界

Step 2 只回答“真实 WAV 与一组受控音乐语义标签有多相符”。它不从 Blueprint 倒推音乐，不把模型输出视为事实，也不生成面向用户的自然语言介绍（后者属于 Step 3）。

唯一选用的模型是 Music-CLAP checkpoint `laion/clap-htsat-unfused`。它将真实音频与英语短提示映射到同一向量空间，再计算余弦相似度。相似度仅用于同一模型、同一标签集内排序，**不是百分比、置信概率或乐器存在证明**。

## 已实现

- `music_companion/semantic_analysis.py`
  - `analyze_audio_artifact_semantics()` 严格通过既有 `AudioStore.get()` 与 `load_audio()` 取得真实 WAV；不由调用方拼接音频路径。
  - 保持 48 kHz、转为单声道后选择最多三个固定的 10 秒窗口（首 / 中 / 尾）。这避免 CLAP 对长音频的内部随机截断，使重复运行可复现。
  - `MusicClapScorer` 默认在 CUDA 可用时使用 CUDA；请求 CUDA 但 PyTorch 未识别 GPU 时明确失败，不悄悄降级。
  - 默认标签集为 18 个受控标签，分为情绪、能量、音乐特性、乐器线索；模型输入使用英文短提示，结果使用中文标签。
  - 输出每个窗口和聚合结果的完整排序，保存原始余弦相似度，而非伪造的 0–100 分。
- `music_companion/schema.py`
  - 增加 `SemanticLabelScore`、`SemanticTimeSegment` 与 `MusicSemanticAnalysisResult`；它们是 POC 临时契约，不是正式数据库实体。
- `test/music_companion/2/test_semantic_analysis.py`
  - 使用实际 `AudioStore.save()` / `load_audio()` 写入测试 WAV，并以可控假评分器验证 UUID、源文件未改、排序、缺失资产、模型结果维度异常和长音频首 / 中 / 尾窗口选择。

## 依赖与本机 CUDA 状态

已确认机器有 NVIDIA GeForce RTX 4060 Laptop GPU（8 GB），驱动 552.46，`nvidia-smi` 报告 CUDA 12.4。

最初从通用镜像安装的 `torch 2.14.1+cpu` 不能使用 GPU；现已替换为 `torch 2.6.0+cu124`。实际验证
`torch.cuda.is_available()` 为 `True`，设备为 `NVIDIA GeForce RTX 4060 Laptop GPU`。CUDA 版必须使用项目内的专用依赖文件：

```powershell
$taskTemp = "C:\Users\honor\Desktop\MuseGarden\.pip-tmp"
New-Item -ItemType Directory -Force -Path $taskTemp
$env:TEMP = $taskTemp
$env:TMP = $taskTemp
& "C:\Users\honor\Desktop\MuseGarden\.venv\Scripts\python.exe" -m pip install --force-reinstall --no-cache-dir -r "C:\Users\honor\Desktop\MuseGarden\requirements-music-companion-step2.txt"
```

完成后先验证：

```powershell
& "C:\Users\honor\Desktop\MuseGarden\.venv\Scripts\python.exe" -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

预期第二行是 `True`，第三行是 RTX 4060 名称。PyTorch 官方支持在 Windows 通过对应 CUDA wheel 安装，不需要另装完整 CUDA Toolkit。

## 模型实测入口与修复

`laion/clap-htsat-unfused` 的权重现存于项目 `models/music-clap/`，文件实际为约 614 MB；不写入正式 `database/`。

首次实测曾出现四通道输入错误。原因是 `unfused` checkpoint 只能接收单通道 mel 特征，却误使用了
会产生四通道特征的 `fusion` 预处理模式。现已将 `semantic_analysis.py` 改为 `rand_trunc`；本 POC 已先
把长音频切成固定的至多 10 秒窗口，因此不会触发随机长音频裁剪。也同步使用新 `audio=` 接口，消除了
`audios=` 的弃用警告。

可复现入口：

```powershell
& "C:\Users\honor\Desktop\MuseGarden\.venv\Scripts\python.exe" -m music_companion.semantic_analysis d2fcfd4d-6be2-4bba-9b5a-f8f1125a7996 --store-root database/preview --model-cache models/music-clap
```

输出 JSON 中有真实 AudioArtifact UUID、设备为 `cuda`、三个（或短音频时一个）时间窗口，以及每个标签的相似度排序。

## 真实 WAV 实测结果

实际使用 preview `AudioStore` 的 5 份 20 秒 WAV；每首用三个固定窗口（0–10、5–15、10–20 秒）评分。
以下是每首聚合后的前三项。它们是原始余弦相似度，**只适合在同一模型和同一标签集内比较**。

| AudioArtifact ID | 聚合前三标签（相似度） | GPU |
| --- | --- | --- |
| `ad1d99c2-b768-4002-adc5-a2b16df13b7f` | 忧郁 0.480；旋律突出 0.476；温暖 0.436 | CUDA |
| `cd521efe-9b9b-432b-8b04-7640702ee333` | 旋律突出 0.421；忧郁 0.420；温暖 0.418 | CUDA |
| `d37723a2-c46d-4e5b-af1b-35a21cb45ef0` | 忧郁 0.511；温暖 0.479；振奋 0.469 | CUDA |
| `d2fcfd4d-6be2-4bba-9b5a-f8f1125a7996`（V1） | 忧郁 0.449；旋律突出 0.423；温暖 0.419 | CUDA |
| `24c9bfa7-e8c3-4dac-9986-b79680d6ae2e`（V2） | 忧郁 0.524；振奋 0.508；温暖 0.503 | CUDA |

V1 重跑一次后，所有聚合标签相似度的最大差为 `0`，说明固定片段选择在当前环境可复现。

### V1 / V2 的有限观察

V2 的修改目标为“更轻快、保留钢琴、减少鼓点、结尾更明亮”。模型结果中，V2 的“明亮”相似度由 V1 的
0.375 增至 0.432，“振奋”由 0.402 增至 0.508；但“鼓点”也由 0.206 增至 0.245。这不是“修改失败”的
结论：CLAP 的标签相似度并不等于乐器数量或编配事实。它只是一个应当与人工试听、Step 1 声学测量和
Blueprint 分开保存的反例，证明不能拿单个模型标签直接验证创作意图。

运行 `pytest -q test/music_companion` 的实际结果为 `8 passed`。Step 1 保留 6 条既有第三方库警告；没有失败。

### 人工试听对照（2026-10-21）

用户试听 V1 / V2 后确认：**V2 确实更轻快**。这与模型从 V1 到 V2 的“明亮”相似度
`0.375 → 0.432` 和“振奋”相似度 `0.402 → 0.508` 的上升方向一致。因此，受控标签在这一个
真实版本比较中提供了有用的语义线索。

用户没有就“鼓点是否更少”给出试听结论；而模型的“鼓点”相似度反而从 `0.206 → 0.245`。该标签
在本组样本中不应被用来判断鼓点数量。这是 Step 2 的边界证据，而不是失败：模型结果应在 Step 3
作为带局限的输入，由语言模型用谨慎措辞解释。

据此，Step 2 POC 的完成条件已经满足：模型能在真实音频上稳定产生受控标签排序，并在至少一项
可试听的版本变化（更轻快）中与人工判断方向一致。可以在获得确认后进入 Step 3，但仍不应把
模型标签写回 Blueprint、数据库或正式产品流程。

## 明确未做

- 不修改 AI Engine、Music Engine、Flower Engine、Frontend 或现有生成调用链。
- 不新增数据库表、API、前端页面或自动 Blueprint 修改。
- 不下载 MOSS、MERT 或第二个音乐理解模型。
- 不把模型标签直接写成用户介绍；Step 3 才允许语言模型结合 Step 1 测量、Step 2 语义分数和创作背景生成表述。
