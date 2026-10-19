# Music Engine 模型选型与实测报告

## Step 13.1：ACE-Step 1.5 本地 POC

**状态：通过**

ACE-Step 1.5 已完成本机可行性验证，并确定为 MuseGarden 当前阶段的本地音乐生成方案。
本 Step 仅完成模型选型、部署与首次真实生成验证；尚未将模型接入正式 Music Engine。

## 最终运行位置

~~~text
D:\MuseGarden-ace-step-poc\ACE-Step 1.5
~~~

该目录是唯一保留的 ACE-Step 运行目录，包含核心代码、独立 Python 环境、必要权重、
配置和 Windows 启动脚本。它不影响 MuseGarden 的 ai_engine/.venv 或 Ollama 配置。

启动入口：

~~~text
D:\MuseGarden-ace-step-poc\ACE-Step 1.5\start_musegarden_api.bat
~~~

API 仅监听：

~~~text
http://127.0.0.1:8001
~~~

## 本机适配结果

| 项目 | 最终结果 |
| --- | --- |
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| 显存 | 8,188 MiB |
| ACE-Step 版本 | 1.5.0 |
| 主音乐模型 | acestep-v15-turbo（非 XL） |
| POC 语言模型 | acestep-5Hz-lm-0.6B（仅 Step 13.1 POC 使用） |
| 当前 MuseGarden 运行模式 | DiT-only：不启用 5Hz LM / thinking |
| 推理后端 | PyTorch |
| 执行方式 | 单任务串行 |
| 本地调用方式 | 官方 REST API |

本机 8 GB 显存适合使用 Turbo 非 XL 模型。Step 13.1 的独立 POC 曾使用 0.6B LM；
但在真实 MuseGarden Demo 中，LM+DiT 请求在 600 秒内没有进入 GPU 推理并超时。因此当前
项目运行配置改用官方定义的 DiT-only 路径：`thinking=false`、`use_cot_caption=false`、
`use_cot_language=false`，由 MuseGarden 直接提供已构建的英文 caption、BPM、调性与时长。

## 已验证的创作链路

~~~text
Music Prompt + 结构化参数
        ↓
POST /release_task
        ↓
POST /query_result 轮询状态
        ↓
GET /v1/audio 下载 WAV
~~~

固定 POC 参数：

| 参数 | 值 |
| --- | --- |
| 纯音乐 | instrumental=true |
| 时长 | 20 秒 |
| 速度 | 108 BPM |
| 调性 | C Major |
| 输出格式 | WAV |
| 随机种子 | 20260929 |

## 实际生成结果

生成文件：[ace_step_poc_01.wav](../../development/data/demo/audio/ace_step_poc_01.wav)

| 项目 | 验证结果 |
| --- | --- |
| 实际时长 | 20.000000 秒 |
| 采样率 | 48,000 Hz |
| 声道 | 立体声（2 声道） |
| 格式 | WAV / FLOAT |
| 文件大小 | 7,680,088 bytes |
| SHA-256 | b0cb898212e51df35cf276ddeaffe7ac952e8716a501fc6a2a36972d45ed5565 |

音频已使用 soundfile/libsndfile 成功解码验证。生成请求使用纯音乐模式且未传入歌词，
接口返回歌词字段为空；最终听感与是否存在类似人声纹理仍由人工试听确认。

## 性能记录

- 首次端到端任务耗时：242.6 秒。
- 该时间包含首次模型加载与 0.6B LM 下载，不代表热启动速度。
- 记录到的 GPU 使用快照最高为 4,947 MiB；不是连续峰值性能分析。

## 运行时模型取舍

~~~text
checkpoints/
├── acestep-v15-turbo        # MuseGarden 当前 DiT-only 主音乐模型
└── vae                      # 音频解码模型
~~~

`acestep-5Hz-lm-0.6B` 只在未来重新尝试 LM+DiT 或独立 POC 时需要；当前 MuseGarden
Demo 不会使用它。`acestep-5Hz-lm-1.7B` 与 `Qwen3-Embedding-0.6B` 也不属于当前
MuseGarden 音乐生成运行路径。

## 最新真实 Demo 结果（2026-10-09）

- ACE-Step API 已可访问，V1 请求成功提交并持续轮询 `/query_result`。
- 原 LM+DiT 请求在 600 秒内没有完成；任务期间观测到 GPU 约占用 4,759 MiB、利用率 0%，
  没有产生新的 WAV。因此这次 Demo 不能算作成功生成。
- 已将项目请求调整为 DiT-only，并将 `start_musegarden_api.bat` 设置为
  `ACESTEP_INIT_LLM=false` 与 `ACESTEP_OFFLOAD_DIT_TO_CPU=true`：前者避免启动时预加载
  0.6B LM，后者在 VAE 解码前释放 DiT 占用的显存。
- 重启后，真实完整 Demo 成功生成 V1 音频：
  [7a1bf183-fff3-4f66-967c-8073762484a8.wav](../../database/local/audio/7a1bf183-fff3-4f66-967c-8073762484a8.wav)。
  对应 Draft 为 `c7599d3d-c9d3-42bd-ab0c-ba02819de705`、Revision 为 V1，ACE-Step
  task ID 为 `0ebee868-e7cf-45df-ae03-5ffcce2aba6c`。
- WAV 已由 soundfile/libsndfile 成功解码：20.000 秒、48,000 Hz、双声道、32-bit float、
  7,680,088 bytes，SHA-256 为
  `C1C748DA42776A016349075D41D74E53D8419163CDE49F632A8A23B69E161D7C`。
- 请求使用 `instrumental=true` 与空歌词；是否存在细微类人声纹理由人工试听确认。服务日志显示
  DiT 扩散实际在 PyTorch CUDA 上运行，且在约 6 次、每 2 秒一次的轮询后返回音频；本次没有
  单独写入高精度计时器，因此只记录为约 12 秒的首次 API 任务观察值。

## 后续接入结论

下一步可开始正式实现“已确认的 MusicBlueprint → ACE-Step REST 请求”：

- 将 Blueprint 的情绪、乐器、场景、结构发展转换为音乐 Prompt；
- 将 tempo、key 等可控字段映射为 API 参数；
- 保持本地 API、单任务串行与 CPU offload；
- 保存每次生成的请求参数、音频文件与版本信息。

本 Step 未实现 Prompt Builder、Generator、Provider 抽象、Schema、音频版本管理、
FastAPI、前端或 AI Engine 数据模型改动。
