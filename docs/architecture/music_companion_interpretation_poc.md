# Music Companion Step 3 — Professional Music Interpretation POC

状态：独立代码、真实 V2 WAV、项目内 CUDA Music-CLAP、本地语言模型、自动化测试与人工试听反馈均已验证。Step 3 POC 完成；尚未接入正式产品页面、数据库或生成调用链。

## 目标与边界

Step 3 将同一份真实 AudioArtifact 的三层信息组合为可阅读的中文音乐介绍：

- Step 1 的声学测量：时长、节拍估计、分段动态与频谱变化；
- Step 2 的 Music-CLAP 受控标签相似度：只代表音色或语义倾向；
- 与该音频版本精确匹配的创作 Blueprint、修改指令和人工试听反馈。

它不进行声部分离、不证明乐器真实存在、不把 Blueprint 写回生成结果，也不自动判断修改成功。

## 已实现

- `music_companion/interpretation.py`
  - `interpret_audio_artifact()` 只通过既有 `AudioStore` 读取真实音频资产，并要求 Step 1 / Step 2 的 UUID 与目标资产一致。
  - `resolve_creation_context()` 优先按 `revision_id` 取对应历史 Blueprint；旧资产无法精确匹配时降级标记为 `current_record` 或 `generation_spec_only`。
  - 本地 `qwen2.5:3b` 生成结构化初稿，再经 Pydantic、乐器白名单、时间范围和事实边界校验。
  - 程序级补全每个 Blueprint 乐器，以及开头 / 中段 / 结尾的真实声学时间范围，避免小模型漏项。
  - 最终文案明确区分“编配设定”“模型音色线索”“人工试听确认”。若没有人工确认，不会把鼓点数量、具体和声或具体乐器写成成品事实。
- `music_companion/schema.py`
  - 增加专业介绍、乐器构成、分段聆听、修改意图对照与限制说明的 POC 结果契约。
- `test/music_companion/3/test_interpretation.py`
  - 覆盖真实 `AudioStore` 读取、资产 UUID 一致性、无依据乐器拒绝与重试、精确版本解析、Blueprint 乐器补全，以及无修改指令时移除无依据的意图对照。

## V2 真实验证

目标资产为 `24c9bfa7-e8c3-4dac-9986-b79680d6ae2e`，能精确匹配 V2 BlueprintRevision。其修改指令是“整体更轻快一些，保留钢琴，减少鼓点，让结尾更明亮。”

人工试听唯一确认的结论是：**V2 比 V1 更加轻快**。因此最终结果将整条修改指令标为 `partially_supported`；“鼓点是否减少”没有人工确认，且 CLAP 相似度不能判断乐器数量，不作结论。

输出文件为 `models/music-clap/interpretation-v2.json`。它包含：

- 一段带证据边界的专业介绍；
- 钢琴、弦乐、贝斯、鼓点、吉他、合成器六项编配构成；
- 0–6.667 秒、6.667–13.333 秒、13.333–20 秒三段聆听范围；
- 计划乐器与音频线索的分别标注；
- 对未确认鼓点变化的明确保留。

## 运行入口

Music-CLAP 已在项目内 `models/music-clap/`，默认 CUDA 可用时使用 CUDA。为了确认不触发网络下载，可在 PowerShell 运行：

```powershell
Set-Location "C:\Users\honor\Desktop\MuseGarden"
$env:HF_HUB_OFFLINE = "1"
& ".\.venv\Scripts\python.exe" -m music_companion.interpretation 24c9bfa7-e8c3-4dac-9986-b79680d6ae2e --store-root database/preview --human-feedback "人工试听确认：V2 比 V1 更加轻快。未确认鼓点是否减少。" --output models/music-clap/interpretation-v2.json
```

验证命令：

```powershell
& ".\.venv\Scripts\python.exe" -m pytest -q test/music_companion
```

当前结果为 `15 passed`；其余 6 条为 librosa / audioread 的既有第三方警告。

## 明确未做

- 不新增正式数据库实体、API、前端页面或自动化通知。
- 不向 Blueprint 或音乐生成模型反写分析结论。
- 不安装第二个音乐理解模型。
- 不把 POC 输出视为专业制作分析、混音报告或声部分离结果。
