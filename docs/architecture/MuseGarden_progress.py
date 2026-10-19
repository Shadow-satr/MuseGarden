"""MuseGarden 跨模块当前进度快照（更新至 2026-10-19）。

本文件记录实际接入状态，不替代各 Engine 的逐 Step 历史：
AIEngine_progress.py、MusicEngine_progress.py、FlowerEngine_progress.py。
"""

CURRENT_STATUS = "本地端到端链路已接通；正式 Frontend 已完成 Step 1–9，包括花园探索、真实创作、花朵记忆、音乐修改与版本选择、四方向走路动画。AI 语义记忆检索尚未接入。"

CURRENT_LAYOUT = "旧网页 Demo 与开发缓存位于 development/；正式 frontend/ 不再包含静态预览花园数据。当前本地 API 仍使用 database/preview/，该数据没有迁移。项目根目录的 启动 MuseGarden.bat 会统一准备 Ollama、ACE-Step、Garden API 与前端。"


COMPLETED = """
一、当前可运行的产品链
用户在正式 Pixi 花园中控制角色行走 → 脚底进入空地后按 E 输入记忆 → AI 情绪理解与
MusicBlueprint → ACE-Step 生成 WAV → Flower Engine 由同一初始 Blueprint 生成
FlowerArtifact → GardenService 保存 PlantingRecord → React/Pixi 显示花园、详情和音乐。

二、已有功能
- 正式创建会保存 MusicMemory、FinalCreation、AudioArtifact、FlowerArtifact、
  PlantingRecord 与 Creation 关联；重新打开前端仍可读取已种下的记忆。
- 玩家可用 WASD / 方向键四方向行走；移动时按 9fps 循环 6 帧走路动画，停止时回到
  对应方向站立帧，坐标始终代表脚底。
- 脚底进入空地按 E 可创作；进入已种花格子按 E 可查看原始文字、这朵花自己的
  render_spec 缩略图，以及对应真实音频。
- 用户提出音乐修改要求时，现有 AI Engine 编辑最新 MusicBlueprint，并由 ACE-Step
  生成 V2、V3 等真实音频。所有版本保留，前端可选择并播放历史版本；当前播放版本
  与最新版本分别持久化，花、原始文字与种植位置不变。
- 选地高亮会显示角色当前所在网格；世界边界允许角色脚底进入最外圈格子，同时角色
  图像不会越出画面。
- HTTP 传输的 63 位 variation_seed 为十进制字符串，避免 JavaScript 整数精度丢失。

验证基线：正式前端 Vitest 43 项及 TypeScript/Vite 构建通过；Creation API 与
CreationService、Music Engine 的相关 Python 回归测试 38 项通过。真实浏览器已验收：
创建花朵、回访记忆、V1 → V2 → V3 真实生成、版本切换和走路动画。
"""


KNOWN_INTEGRATION_GAPS = """
一、版本数据仍是 Preview Creation 层的持久化模型
- 正式前端已列出、播放并选择 V1 / V2 / V3；CreationService 将每版的音频 ID、修改要求
  与 Blueprint 快照保存到 demo_creations.json，并兼容从已有 AudioStore 补齐旧记录。
- 这些版本尚未写入 AI Engine 的正式 revision store；这不影响当前本地产品功能，但未来
  若统一为正式 CreationDraft 生命周期，需要设计一次数据迁移。
- Music Engine 仍保留“同 Revision 多候选”的底层能力；当前产品规则是一版 Blueprint
  对应一首当前音频，网页未暴露候选生成界面。

二、正式前端尚未使用 AI Engine 的历史记忆检索
- 当前创作确实调用 AI Engine 的情绪理解、Blueprint 生成与编辑；成功后也保存 MusicMemory。
- 当前调用明确使用 run_creation_pipeline(text, use_memory=False)，所以新创作不会检索
  之前的记忆，不会把记忆上下文交给 Blueprint Generator。
- Demo 记忆写在 database/preview/memories.json；AI Engine 检索器默认读
  database/local/memories.json。未来接入检索时必须统一数据源或显式传入路径。
- Demo 没有走 AI Engine 正式的 start_creation/edit_creation_draft/confirm_draft
  持久化生命周期；这也是 BlueprintRevision 历史缺失的原因之一。

三、工程边界
- 本地多个 JSON Store 没有跨文件事务；生成中途失败需要后续补偿、幂等与并发控制。
- 当前页面是本地 Demo，不包含账户、多用户、任务队列或完整产品 UI。
"""


AGREED_DIRECTION_NOT_YET_IMPLEMENTED = """
已实现的产品规则：一版 Blueprint 对应一首音乐；修改音乐先产生下一版 Blueprint，
再为该版本生成一首 AudioArtifact，不在同一版本下提供多次候选生成。网页可列出并
选择播放已有的 V1/V2/V3；选择旧版本不重生花，也不改种植位置。花继续代表初次
确认的情绪记忆。

下一阶段可单独讨论 AI 历史记忆检索：需先解决 preview/local 数据源一致性，以及
何时把旧记忆提供给新的 Blueprint Generator。
"""
