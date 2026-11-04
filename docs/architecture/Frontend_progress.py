"""MuseGarden Frontend 开发进度，按正式章节顺序记录。"""

CURRENT_STATUS = "核心功能开发阶段暂时收尾：Garden World、玩家探索、种植与记忆回访、真实 Creation / 音乐流程、版本修改、Grid Map V1、Mini Map 与基础地形美术均已完成。后续只按需进行美化、体验维护与 Bug 修复；不自动启动新的 Frontend Step。环境装饰仅保留为未实施的开发参考，不属于当前版本功能。"

STEP_1 = """
Frontend Step 1 — Garden World Shell
====================================

目标：把独立的 Garden Preview 升级为 MuseGarden 的主场景容器。打开根路径 / 即进入花园。

实现：
- 建立 frontend/src/world、ui、components、api、assets 等目录。
- GardenWorld 管理 Pixi Application 生命周期、花园数据加载、Scene 挂载与销毁。
- WorldScene 复用已有 Garden / Flower Renderer，不重写花朵渲染算法。
- React 负责挂载容器；HTML WorldOverlay 与 Pixi 画布同时存在。
- 前端读取后端 /api/garden-preview 提供的 GardenRenderSpec。

范围：这一阶段没有 Player、移动、交互、摄像机或 Creation UI。
后端及 AI / Music / Flower Engine 未修改；读取花园不会修改后端数据。

验证：正式前端 TypeScript / Vite 构建通过，Vitest 5 项通过；旧 Demo 构建通过。
当时未完成浏览器画面的人工验收。早期本地数据回退已在后续目录整理时移除。
"""


STEP_14_1 = """
Frontend Step 14.1 — Real Flower Gameplay Validation
====================================================

目标：在隔离数据目录中，以真实浏览器、Creation API、Ollama 与 ACE-Step 验收 Step 14。

结果（2026-10-23）：固定随机序列实际创建并核验 small 占 1 格、large 占 9 格、田地
边缘 large 自动降级 small、相邻占地冲突 large 自动降级 small；刷新后位置、大小和
occupied_tiles 保持不变。浏览器实际提交记忆并播放音频；刷新后按 E 可查看对应原文与
V1。生成 V2 后又切回 V1。已占中心格与非 SOIL 格均返回 400，且 Creation 数量不增加。

修复：隔离 API 支持测试数据根目录、端口、确定性随机序列与空的 91 × 68 花园；Vite
支持代理至测试 API；LLM 若返回空 key、texture、scene、primary_emotion，则回填当前
Blueprint，其他无效字段仍被 Pydantic 拒绝。

验证：前端 Vite 构建通过；Blueprint Editor 测试通过；Garden Planting / Demo Creation
回归 24 passed。隔离测试目录已删除，正式 database/preview 未写入测试花朵。

范围：没有新增玩法或美术。Step 14.1 已完成，下一步进入 Step 15 Terrain Visual Polish。
"""

STEP_2 = """
Frontend Step 2 — Player System
===============================

目标：让玩家在花园里用键盘连续移动。

实现：
- Player 最初用 Pixi Graphics 绘制临时角色，以脚底作为世界坐标。
- GardenWorld 将 Player 放入 WorldScene.entities，由 Pixi ticker 更新位置。
- 支持 WASD / 方向键、按住连续移动、斜向速度归一化和世界边界。
- 窗口失焦或 World 销毁时清空按键状态，并移除键盘监听。

范围：这一阶段没有交互、种花、碰撞、摄像机、走路动画或 NPC。
Flower / Garden Renderer 与旧 Demo 未修改。

验证：正式前端构建通过，Vitest 9 项通过，覆盖移动、方向键、斜向等速、
边界及生命周期；Garden Renderer 原有测试通过。
"""

DIRECTORY_REORGANIZATION = """
章节之间的目录整理：旧网页 Demo、演示脚本、演示数据和测试运行缓存统一收进
development/。正式 frontend/ 移除了静态预览花园数据与离线回退；正式花朵渲染器
保留在 frontend/src/rendering/flowers。Python 回归测试源码 test/、运行环境 .venv/
和当前后端使用的 database/preview/ 保留原位。

整理后验证：正式前端构建和 Vitest 11 项通过；旧 Demo 构建及 12 项测试通过；
Flower 与 Music Engine 的 Python 测试合计 98 项通过。
"""

STEP_3 = """
Frontend Step 3 — Interaction System
====================================

目标：Player 靠近花或测试空地时识别可交互对象，按 E 触发本地交互反馈。

实现：
- frontend/src/world/interactions.ts 定义 Plant Spot 与 Flower 两种 Interactable。
- 从 GardenRenderSpec 获取已种花朵的位置；在未被花占用的网格中放置最多 4 个
  固定测试空地。WorldScene 在 Pixi 实体层绘制空地十字标记。
- 空地和花朵都以 Player 的脚底坐标所在网格判断：脚底进入对象所在格才显示
  交互提示。同一格有多个目标时选择距脚底最近的；没有目标时 currentTarget 为 null。
- GardenWorld 在 Player 更新后检测目标变化，并把目标通知 React。按 E 触发当前
  目标的本地回调；忽略长按重复事件及输入控件中的按键。
- WorldOverlay 随目标显示 [E] 种下记忆或 [E] 查看记忆；按 E 后临时显示
  “已选择空地 / 花朵”，离开范围后清除提示。

范围：没有调用 Creation API，没有输入文字、真正种花、生成音乐 / 花、摄像机或碰撞。
Garden / Flower Renderer、AI / Music / Flower Engine 和旧 Demo 未修改。

验证：正式前端构建通过，Vitest 16 项通过，覆盖最近目标、离开范围、两类提示、
E 键回调及原有移动；旧 Demo 构建和 Vitest 12 项通过。
"""

STEP_4 = """
Frontend Step 4 — Player Character Integration
==============================================

目标：用正式四视图角色替换 Step 2 的临时小人，保留 Step 2 移动与 Step 3 交互。

素材：frontend/src/assets/四视图像素风女孩角色精灵图.png，透明 PNG，原图
1254 × 1254。运行时从同一张图裁出 Front、Left、Right、Back 四个静态视图。

方向：W / 上显示 Back，S / 下显示 Front，A / 左显示 Left，D / 右显示 Right。
斜向移动时选择分量较大的方向；分量相等时优先竖直方向。停止移动保持最后朝向。
本阶段没有加入走路动画，原有移动速度与斜向归一化逻辑保持不变。

Sprite 由 Player 管理，GardenWorld 在 Pixi 初始化后加载贴图，React 不操作 Sprite。
角色显示高度 58 世界像素，Sprite anchor = (0.5, 1)，Player.container 的坐标
对应脚底。边界留出角色半宽及全高，避免走出画面。

Step 3 的 Interaction System、E 键、Plant Spot 和 UI 提示保持可用。本阶段没有
扩展交互或接入 Creation API。Flower Engine、Garden Renderer 与旧 Demo 未修改。

验证：正式前端 TypeScript / Vite 构建通过，Vitest 17 项通过，覆盖四方向切换、
停止保持朝向、脚底锚点、原有移动与交互。浏览器中确认正式角色显示在花园中，
与花朵的比例协调；未把四方向的浏览器人工逐项检查记为已完成。
"""

STEP_5 = """
Frontend Step 5 — Creation Overlay
==================================

目标：Player 脚底进入空的 Plant Spot 所在格并按 E 后，在花园画面前打开“留下一段记忆”
的 React 表单；本阶段只建立前端创作入口。

实现：
- frontend/src/ui/CreationOverlay.tsx：独立的半透明浮层与简洁面板。提供多行输入、
  placeholder、500 字限制、实时计数、“开始创作”和“取消”。打开后 textarea 自动聚焦。
- App 根据 GardenWorld 的 Plant Spot 交互回调保存当前空地，显示 CreationOverlay。
  Flower 交互继续保留原有本地反馈，不会打开创作面板。
- 打开面板时 GardenWorld.setInputPaused(true) 清空已按住的方向键并阻止新的移动与
  E 交互；取消或提交后恢复输入。关闭表单时组件卸载，输入内容随之清空。
- “开始创作”会将去除首尾空白的文字与 plantSpotId 组成临时 CreationDraft，
  输出到浏览器控制台，关闭面板并显示“准备开始创作……”。空白输入不能提交。

边界：没有调用后端、AI / Music / Flower Engine，也没有真正种花或保存数据库。
Step 3 的最近目标检测、交互范围和 Step 4 的四视图角色保持原有职责。

后续体验修正：按 E 打开表单时阻止该按键的浏览器默认输入，避免字母 e 落入
自动聚焦的 textarea。空地和花朵提示都改为严格按玩家脚底进入对应网格判断。
新增测试确认脚底跨过网格边界时才激活目标，以及触发交互的 E 键会取消浏览器
默认输入。

验证：正式前端 TypeScript / Vite 构建通过，Vitest 22 项通过，覆盖表单开关、
自动聚焦、输入与 500 字限制、CreationDraft、花朵交互不误开表单、暂停移动与
E 键、取消后恢复移动及原有渲染相关测试。当前沙箱无法从浏览器访问本地
开发服务器，因此本阶段没有把实际画面人工检查记为通过。
"""

STEP_6 = """
Frontend Step 6 — Real Creation Flow
====================================

目标：Player 在空地按 E，输入文字后调用现有正式 POST /api/creations，由后端
CreationService 编排 AI Blueprint、Flower、Music、保存和种花；刷新花园显示新花，
结果面板可以播放生成的音乐。

正式请求按 CreateMemoryRequest 发送 {garden_id, text, x, y}。前端把选中的
plantSpotId（spot:x,y）解析成网格坐标，garden_id 取当前 GardenRenderSpec。
CreationService.describe 的真实响应包含 creation_id、text、flower、planting、
music；music.url 为现有 /api/audio/{artifact_id} 路由。前端检查响应里的种植
坐标与选中空地一致，并要求 Flower、Planting 和 Audio 字段齐全。

实现：
- 创作期间保持 Overlay 与 Player 暂停，显示统一 loading，禁用重复提交。
- 成功后重读 /api/garden-preview，验证新 planting 和 flower 出现在目标网格，
  并用原 Garden / Flower Renderer 重建场景。Player 对象、脚底位置和方向保留；
  该格的 Plant Spot 自然变为 Flower 交互目标。
- 完成结果显示真实文字和简单播放 / 暂停按钮；点击完成返回花园并恢复移动。
- API 失败保留文字，可重试或取消。刷新失败只重试读取花园，不重新 POST 创作。
  若 HTTP 成功但响应不完整，避免再次提交可能重复种花；尝试刷新花园并提示
  用户回到花园检查。取消中止前端请求并忽略迟到结果；服务端已开始的生成
  不保证能被浏览器取消。
- 确认旧 /api/creations/draft 只有上个临时 Step 6 使用后，移除路由、Schema
  和测试。原正式 Creation Service、AI / Music / Flower Engine 未改动。

范围：没有音乐版本、编辑、Memory Retrieval、摄像机、NPC 或 Music Studio。

自动验证：前端构建与 Vitest 29 项通过；后端正式路由 2 项契约测试及 Music /
Flower Engine 98 项测试通过。AI Engine 全套旧测试未在本 Step 重新跑通。

2026-10-19 真实浏览器验收：启动本地 Ollama（qwen2.5:3b）、ACE-Step API、
Garden API 与 Vite，在网页中移动角色进入空地 (8,3)，按 E 打开表单并输入
“今天终于完成了比赛，感觉特别开心。”。真实 POST /api/creations 完成后显示
结果及音乐按钮；播放 / 暂停按钮状态正常。点击完成后同一格出现新花，交互
提示由“种下记忆”变为“查看记忆”，玩家可以继续移动。刷新网页后花仍在。
后端 GET /api/creations 中的种植记录为 (8,3)，GET 音频返回 200、audio/wav，
大小 7,680,088 字节。测试创作已保存在 database/preview 中。
"""

STEP_7 = """
Frontend Step 7 — Flower Memory Detail
======================================

目标：让已种下的花成为可以反复访问的记忆。Player 脚底进入已有花朵所在格后按 E，
在花园背景前打开详情，查看原始文字并播放或暂停这朵花当前对应的真实音乐。

数据关系：复用现有 GET /api/creations，不新增后端接口。该接口由 CreationService
从 database/preview/demo_creations.json 等正式持久化记录生成详情。前端同时使用
planting_record_id 与 flower_artifact_id 精确匹配 GardenRenderSpec 中选中的花，读取
对应的 text 和 music.url；不会把最近一次 Creation Result 当作其他花朵的详情。

实现：
- frontend/src/ui/FlowerDetailOverlay.tsx 提供独立详情浮层，花园保留为背景；显示
  真实原始文字、花朵种类、播放 / 暂停与返回操作。
- 花朵详情具有 loading、error、retry、success 状态。记录不存在或列表格式无效时
  显示错误并允许重新读取或返回，不伪造文字和音频。
- 复用 AudioPlayer。每朵花使用自身 music.artifact_id 与 /api/audio/{artifact_id}；
  关闭详情或切换花朵时组件卸载并暂停旧播放器，避免继续播放上一朵花。
- 复用现有 Interaction System、脚底网格判断与 E 键监听。空地仍打开 Creation
  Overlay；花朵打开 Flower Detail Overlay，没有复制距离检测或键盘监听。
- 详情一打开即暂停 Player 并清空移动键；WorldOverlay 隐藏 E 提示。关闭详情后
  恢复移动，不刷新或重建 GardenWorld，也不改变花朵位置。

范围：没有音乐修改、音乐版本选择、RAG / 搜索、删除或移动花朵、摄像机、NPC、
Inventory 或花园 UI 重构。AI / Music / Flower Engine 未修改。

自动验证：正式前端 TypeScript / Vite 构建通过；Vitest 10 个测试文件、37 项测试
通过，覆盖持久化关系匹配、多花详情隔离、详情文字与音频 URL、播放 / 暂停、错误
与重试、关闭恢复移动、原 Creation Overlay、Interaction、Player 和 Renderer。
Creation API 与 CreationService 相关 Python 测试 11 项通过。

2026-10-19 真实浏览器验收：在本地 Vite 与 Garden API 环境中，Player 进入已有
Sunflower 所在格后出现 [E] 查看记忆；按 E 打开详情，显示该花保存的原始文字
“和我家宝宝关系和好了，我很开心”。点击播放后按钮切换为暂停，暂停正常；返回
花园后详情关闭，原花朵保持不变，Player 可继续移动，提示随脚底所在格恢复为
[E] 种下记忆。
"""

STEP_8 = """
Frontend Step 8 — Music Revision & Version Management
=====================================================

目标：在花朵记忆详情中修改当前记忆对应的音乐，保留每一次真实生成结果，并允许在
V1、V2、V3 等历史版本之间反复选择和播放。原始记忆文字、花朵和种植位置保持不变。

后端数据：继续复用 POST /api/creations/{creation_id}/music 和现有 AI Blueprint
编辑、Music Engine、AudioStore。DemoCreationRecord 增加 music_versions 与
blueprint_revisions，保存每版稳定的 revision_id、audio_artifact_id、修改要求、
创建时间和 Blueprint 快照。旧记录会从 AudioStore 中已有的真实音频自动补齐历史，
不会复制 Creation 数据源。新增 POST /api/creations/{creation_id}/music-selection，
只持久化当前选择的音频；latest_music_version 与当前选择互相独立。

实现：
- Flower Detail Overlay 增加“修改音乐”表单、500 字限制、loading、失败重试和取消。
  修改期间 Player 继续暂停，返回、重复提交和版本切换均禁用。
- 修改请求始终基于最新 Blueprint 生成下一版，而不是基于用户当前试听的旧版本。
  成功后新版本成为最新且自动选中；失败不会写入伪版本或改变当前音频。
- 版本列表显示 V1 / V2 / V3、修改要求、“最新”和“当前播放”。选择旧版本会调用
  后端保存选择，重新打开详情后仍保持；只使用一个 AudioPlayer，切换版本或关闭详情
  时安全暂停旧音频，避免多个播放器并存。
- GET /api/creations 返回完整 music_versions、latest_music_version 和每版真实音频 URL。
  新生成音乐不会修改原始文字、FlowerArtifact、PlantingRecord 或花园布局。

范围：没有音乐删除、版本重命名、Music Studio、RAG / 搜索、花朵移动、NPC 或下一
章节功能。Flower Engine 的生成与渲染逻辑未修改。

自动验证：正式前端 TypeScript / Vite 构建通过；Vitest 10 个测试文件、41 项测试
通过，覆盖版本历史解析、真实修改与选择请求、500 字限制、loading、错误保留、
多版本切换、对应音频 URL、单播放器生命周期和原有花园流程。Creation API、
CreationService 与 Music Engine 的相关 Python 回归测试通过。

2026-10-19 真实浏览器验收：选择原本只有 V1 的 Sunflower 记忆，确认 V1 可播放；
输入“整体更轻快一些，保留钢琴，减少鼓点，让结尾更明亮。”，本地 AI 与 ACE-Step
生成真实 V2。切回 V1 后再次输入“在上一版基础上更温柔一些，加入柔和弦乐，降低
整体能量。”，成功生成 V3，证明修改始终承接最新 Blueprint。V1、V2、V3 均能
切换并播放；最终选择 V2 后关闭详情再重新打开，V2 仍为当前播放，V3 仍标记最新，
原始文字和花朵位置未改变。

后续体验补充：详情页不再使用固定的粉色花朵图标，而是读取当前 FlowerArtifact 的
render_spec，以花型、花瓣数、颜色、花蕊、茎叶绘制该花自身的缩略图。版本卡片中的
修改要求默认单行摘要；点击摘要可展开完整文字，再点收起。前端构建通过，Vitest
43 项通过。
"""


STEP_9 = """
Frontend Step 9 — Walking Animation
===================================

目标：把 Player 从四张静态视图改为可循环的走路序列帧。移动时真正抬脚、摆臂，
停止时回到该方向的站立帧；所有帧共用同一画布与脚底基线，避免人物上下跳动。

素材与处理：
- 新素材位于 frontend/src/assets：正 / 左 / 右 / 背面各 2 张 1536×1024 图，
  每张 3 帧，合计 24 个走路帧。
- 黑色背景用边界洪泛去除；左 1 的棋盘格背景用双色聚类去除，仅对四周被头发
  包围的棋盘块做局部修补，避免把外套的灰白阴影误当成背景。
- 每帧单独缩放到角色高 352px，画布 288×384，脚底基线 y=376；缩放后用 LAB
  皮肤中位数把各帧肤色统一到同一目标，减少走动时的明暗和肤色跳变。
- 正面 / 背面站立帧复用原四视图；左 / 右站立帧取自走路序列中脚部最接近并拢的
  帧，避免侧面原图被裁切、人物偏小。
- 生成 player-walk-sheet.png（7 列 × 4 行）与 player-walk-sheet.json；Player 按
  JSON 网格切片，不再在运行时裁切原四视图。

动画：
- 按住 WASD / 方向键时以 9fps 循环 6 帧；起步从该方向的中性帧开始，转向时保留
  当前步态相位，只在停止时切回站立帧。
- 位移速度保持 120px/s；如果后续要完全消除滑步，可调整 Player.ts 中的
  WALK_FPS 或 SPEED_PX_PER_SECOND。
- 所有帧 anchor 均为画布宽度的 0.5、基线 376/384，容器坐标继续表示脚底位置。

验证：前端 Vitest 43 项通过，新增起步帧、9fps 推帧、循环、停止与转向相位测试；
TypeScript / Vite 构建通过。

2026-10-21 侧向肤色稳定性修正：最终版本回到原始 player-walk-sheet.png 的动作像素，
不再重新生成或镜像姿势。player-walk-sheet-v6.png 仅在 Left / Right 六帧的脸、耳、
手和腿皮肤蒙版内统一色调与明度；动作、帧顺序、轮廓、衣服、头发、鞋、透明通道、
尺寸和脚底基线与原版完全一致。像素校验确认透明通道变化为 0，皮肤蒙版外变化为 0。
Front / Back、站立帧、9fps 与 120px/s 移动速度均未改变，旧精灵表保留作回退。

同日停止姿势修正：Left / Right 的 idleColumn 不再复用双脚张开的走路姿势，改为
从最初四视图素材精确裁取的侧面直立帧，双腿伸直、双脚并拢。两帧统一为 352px
角色高和 y=376 脚底基线，并将肤色校准到当前侧向行走帧；六个走路帧的像素经校验
完全未变。运行时素材更新为 player-walk-sheet-v7.png。
"""


STEP_10 = """
Frontend Step 10 — Plot & Character Scale Calibration
=====================================================

目标：在进入大地图与摄像机工作前，先以一个清晰可见的 3 × 2 六格田地校准
玩家、单格与田地整体的显示比例。

实现：
- frontend/src/world/PlotCalibration.ts 集中定义标准田地：3 列 × 2 行、每格 48px、
  格间距 8px、外沿 18px。每块泥土格对应一朵花，沿用现有 GardenRenderSpec 的
  单个绿地 / 种植格尺寸；整块田地为 196 × 140px，在当前 768 × 480 的世界内居中。
- WorldScene 在既有草地与世界实体之间绘制简洁泥土田地：统一田埂、六块等大的
  深色土壤、轻量像素颗粒和投影。它是开发期的视觉原型，不声明新的后端 Plant Spot，
  不改变 GardenRenderSpec 的 48px 逻辑网格、花朵记录或种植接口。
- Player 继续使用原有女孩序列帧与脚底 anchor，维持原来的 58px 可见高度。
  相对 48px 田地格短边为约 1.21 倍；动画帧、方向切换、速度、边界和脚底坐标保持。

范围：没有摄像机、大地图、完整园区布局、道路、建筑、复杂装饰或新的种植能力。
Flower / Music / AI Engine 与现有创作、查看记忆和音乐版本流程未修改。

验证：正式前端 TypeScript / Vite 构建通过；Vitest 11 个测试文件、45 项测试通过。
新增 PlotCalibration 单测覆盖田地 3 × 2 尺寸、居中占比、单格一致性和维持既有角色高度。
2026-10-19 重新以 1414 × 800 CSS 视口完成真实 Chrome 验收：页面显示“花园已就绪”，
每块泥土格与原先单个绿地同为 48px，人物保持既有 58px 高度，站在田地中间时与单格
比例一致；六格田地完整可见，周围保留可走草地。截图保存为
development/test_artifacts/step10-plot-calibration.png（Git 忽略的验收产物）。

遗留：本 Step 的田地是比例原型，尚未和后端稳定 Plant Spot 标识一一绑定；这将留给
Step 11 的大地图坐标和 Step 13 的种植区域接入处理。
"""


STEP_11 = """
Frontend Step 11 — World Coordinate & Camera Foundation
=======================================================

目标：让世界尺寸大于可视区域，并在不修改实体世界坐标的前提下实现有边界的摄像机跟随；
暂时继续使用简洁草地、现有花朵与 Step 10 的六格田地。

实现：
- 当前 frontend/src/assets/ 只有角色与走路序列帧，没有可直接接入的正式大地图素材。
  因此临时世界使用 TEMPORARY_WORLD_MULTIPLIER = 2：逻辑可移动世界为 1536 × 960px，
  既有可视区域保持 840 × 552px（含 36px 边沿），为 Step 12 替换地图美术留出接口。
- WorldScene 新增 world-camera-content 容器。完整扩展草地背景在该容器内覆盖
  1608 × 1032px（世界加边沿），继续绘制轻量格纹与草地点缀，移动时不会出现透明区、
  黑边或未绘制区域。
- Camera.ts 提供纯 cameraPositionFor 函数，根据玩家脚底所在的世界位置计算镜头，
  以视口中心为目标并约束到世界四条边。WorldScene 只平移 world-camera-content；
  Player、花朵、田地、交互目标和后端 GardenRenderSpec 坐标均不被摄像机改写。
- Player 的移动边界扩展到 1536 × 960px，但其起点继续是原花园的中心 (384, 240)，
  因而初始画面仍能看到六格田地、周围花朵和人物。现有花朵、田地、互动目标继续使用
  原本 768 × 480px 内容坐标；离开该区域只是暂时的草地行走空间，不伪造新的 Plant Spot。
- React 的标题、E 键提示和各 Overlay 位于 Pixi Canvas 外，保持屏幕坐标；键盘监听、
  输入暂停和 World 销毁生命周期保持原有单一职责。

比例保持：Player 58px、单格田地 48px、3 × 2 六格、8px 格间距、18px 外沿、
田地整体 196 × 140px；移动速度与六帧走路动画未修改。

验证：前端 TypeScript / Vite 构建通过；Vitest 12 个测试文件、48 项测试通过。
新增 Camera 单测覆盖起点不移动、世界中部跟随以及四边 clamp。原有 GardenWorld
键盘、交互、暂停、刷新测试继续通过，证明摄像机未改变脚底交互世界坐标。

2026-10-19 真实 Chrome 浏览器验收使用 1414 × 800 CSS 视口：初始画面可见人物、
六格田地及既有花朵；按住右方向键后人物回到视口中央附近而田地向左移动；继续走到
右侧边界时人物自然偏离中心、草地仍完整填满画布。HTML 标题与右上角控制仍固定在
屏幕位置。验收截图保存于 development/test_artifacts/step11-camera-start.png、
step11-camera-follow.png、step11-camera-right-edge.png（均为 Git 忽略的产物）。
在初始田地附近真实按 E 后，“留下一段记忆”面板与 textarea 正常打开；未提交创作，
未写入后端数据。

范围：未接入正式大地图图片、河流 / 建筑 / 树木 / 围栏碰撞、稳定地图田地标识、
新增后端 Plant Spot、NPC、小地图或传送。这些留给 Step 12–14。
"""


STEP_12 = """
Frontend Step 12 — Map Art Integration & Viewport Calibration
=============================================================

目标：接入用户提供的正式大花园地图，使用已有摄像机显示局部花园视野；保留 Player、
花朵、创作与记忆流程，为下一阶段的田地坐标映射准备基础。

素材与世界：
- 正式地图原图存于 frontend/src/assets/musegarden-map.png，真实尺寸为 1448 × 1086px。
  frontend/src/world/MapArt.ts 集中记录此尺寸，并在 GardenWorld 初始化期间先由 Pixi
  Assets 完成加载，因此第一次渲染即是正式地图，没有旧草地闪现。
- WorldScene 将地图放进既有 world-camera-content 容器，地图原比例显示，不拉伸；
  世界边界直接使用原图尺寸。Step 11 的 TEMPORARY_WORLD_MULTIPLIER、扩展草地和
  程序绘制六格田地已移除，因而不会叠在正式地图已有田地、道路和建筑上。
- 旧的绿格纹只保留为内部坐标 / 数据概念，不再作为可见背景绘制。地图原图自身的
  像素草地纹理属于美术内容，不是逻辑格线。

视野与比例：
- MAP_VIEW_ZOOM = 2.5。它让一块 3 × 2 的泥土田地成为画面主要内容，同时仍能看到
  周围道路和环境；摄像机根据缩放后的可见世界范围进行 clamp，边缘不会露出地图外部。
- Player 使用 30px 可见高度、120px/s、四方向六帧动画与脚底 anchor。逻辑种植格为
  16px，因此人物为约 1.88 个
  逻辑格高。每块
  小田地约定为 3 × 2、共 6 个逻辑格；
  这些格不会显示为绿色线。
- GardenRenderSpec 的动态花朵继续按原有后端坐标绘制在地图层之上；现有 E 键交互、
  Creation Overlay、花朵记忆与音乐版本流程没有改写。下一阶段才会给地图中每块田地
  指定稳定 ID，并将六个逻辑格与后端种植记录逐项映射。

验证：前端 TypeScript / Vite 构建通过；完整 Vitest 在可访问测试缓存的运行环境中
12 个文件、48 项测试通过。受限沙箱中有 3 个既有测试文件会因临时 Vitest 缓存路径
不可读取而无法加载，非代码断言失败；在隔离运行环境重新执行后全部通过。

2026-10-20 真实浏览器验收：本地服务启动后，首次进入即展示正式地图；移动时摄像机
随 Player 移动且不显示地图外部。以 2.5 倍视角查看，顶部左侧田地的六块泥土格占据
主要画面区域，人物略高于单格。按 E 能进入“留下一段记忆”面板，取消后恢复花园；
移动至已有花朵所在格时仍显示“[E] 查看记忆”。

范围：没有实现地图碰撞、河流 / 建筑 / 树木通行规则、地图所有田地的稳定种植 ID、
新的后端 Plant Spot、NPC、小地图或传送。不要把当前动态花朵临时坐标误认为最终
田地映射；这些留给 Step 13。
"""


STEP_13 = """
Frontend Step 13 — Grid Terrain Map Prototype
=============================================

目标：保留 Step 11–12 已完成的世界坐标、摄像机、人物比例与业务流程，将运行时地图
从整张背景图片改为可逐格编辑的地形数据。musegarden-map.png 继续留在 assets 中作为
布局参考，但不再参与运行时渲染。

地形数据：
- frontend/src/world/TerrainMap.ts 定义 1448 × 1086px 世界、16 × 16px 逻辑格，
  使用 91 列 × 68 行覆盖完整世界；最右列与最下行由世界边界自然裁切。
- 每格都具有 GRASS、PATH、WATER、SOIL、STRUCTURE 或 BRIDGE 之一，未涂色区域默认
  为 GRASS。区域通过集中式矩形涂色描述，方便后续调整河道、道路、田地和建筑轮廓，
  不为每个格子创建 React 组件。
- 第一版布局按正式大地图的大致空间关系勾勒：左右与底部水域、入口及主路、四片土地、
  两处建筑占位和四座桥梁。它是地图骨架，不代表最终美术和通行规则。

渲染与兼容：
- frontend/src/world/TerrainRenderer.ts 使用单个 Pixi Graphics 按世界坐标绘制纯色地形；
  WorldScene 将地形层放在动态花园与 Player 下方，摄像机继续只变换世界容器。
- GardenWorld 不再加载地图纹理，MapArt.ts 已移除；正式构建产物中不再包含
  musegarden-map 图片依赖。MAP_VIEW_ZOOM 保持 2.5，逻辑格保持 16px，Player 可见高度
  保持 30px，移动速度、四方向走路动画和脚底 anchor 均未修改。
- 现有 GardenRenderSpec 花朵、脚底格高光、按 E 种下记忆、查看记忆、真实 Creation API、
  音乐播放 / 修改 / 历史版本和所有 React Overlay 继续使用原有世界坐标与生命周期。

验证：2026-10-21 正式 TypeScript / Vite 构建通过；Vitest 13 个测试文件、51 项测试
全部通过。新增 TerrainMap 测试覆盖世界尺寸、91 × 68 全格分类、六种地形存在及关键
区域采样；原 Camera、Player、Interaction、Creation 和 Overlay 测试继续通过。

2026-10-21 真实浏览器验收：本地四项服务启动后进入 http://127.0.0.1:5182/，可看到
由纯色格子组成的草地、土地和水域；按住方向键时人物动画与摄像机跟随正常，世界移动
不会露出透明背景。人物保持 30px，视角保持 2.5 倍。站在可交互格时显示 [E] 种下记忆，
按 E 能打开原“留下一段记忆”面板，取消后正常返回花园；验收过程中没有提交创作，
没有写入后端数据。

范围：本 Step 没有实现地形碰撞、稳定田地 / 种植格 ID、后端坐标重构、地图编辑器、
正式纹理、树木、围栏或建筑细节。SOIL 当前只是地形分类，不会自动获得新的种植能力。
下一步应先根据浏览器中的纯色地图确认河流、道路和田地轮廓，再进入 Planting Plot Mapping。
"""


GRID_BASED_MAP_LAYOUT_V1 = """
Frontend Step — Grid-based Map Layout V1
========================================

目标：根据用户提供的最新“像素田园岛屿地图”参考图，重做 Step 13 的空间布局；继续使用
16px 地形格和纯色 Pixi 渲染，不重新引入整张图片背景，不修改人物、镜头或后端创建流程。
参考图保存为 frontend/src/assets/grid-map-layout-v1-reference.png，只用于布局对照。

布局：
- 世界继续为 1448 × 1086px、91 × 68 个地形格，MAP_VIEW_ZOOM 保持 2.5，Player
  可见高度保持 30px。
- 左侧河流使用多段网格区域形成弯曲河岸，水域沿南侧延伸，并在右下方回弯；中央横向
  主路、中央广场、南北主路、建筑支路和农田支路形成连续路网。
- 北侧保留一处主要建筑和一处辅助建筑占位。左入口、南入口和右侧水域连接处使用
  BRIDGE，桥面与道路对齐。
- 四块农田位于西北、东北、西南、东南。每块田由 3 列 × 2 行共六个独立 SOIL 槽组成，
  每个槽占 4 × 4 个 16px 地形格，相邻槽之间保留一个地形格间隔，画面中可清楚辨认。

种植兼容：
- GardenMapLayout.ts 为 24 个可见槽位建立稳定的现有后端 grid_x / grid_y 绑定。新种植
  仍提交原 API 所需坐标；前端只负责将绑定坐标映射到田块世界位置，不修改数据库结构。
- WorldScene 在传给既有 Flower Renderer 前创建展示副本，把已绑定花朵的 pixel_x /
  pixel_y 移到对应槽中心；原始 GardenRenderSpec、花朵 ID、种植记录和音乐关系保持不变。
- 不属于这 24 个映射格的既有历史花朵继续使用原 pixel 坐标，避免隐藏或删除旧数据。
  InteractionManager 使用玩家脚底进入槽位矩形判断目标，Creation Overlay 与详情流程不变。

碰撞：
- Player 新增可选的脚底通行判断，位移按 X / Y 轴分别尝试，因此撞到水域或建筑时停止，
  斜向移动仍可沿边缘滑行。WATER 与 STRUCTURE 不可通行；GRASS、PATH、BRIDGE 和 SOIL
  可通行。角色速度、四方向动画、脚底 anchor 和世界边界限制均未改变。

地图总览：
- /map-overview 直接读取与游戏相同的 TerrainMap 生成完整 SVG 总览，并显示六类地形图例，
  不再维护一份容易过期的手写预览图。

验证：2026-10-21 TypeScript / Vite 正式构建通过；Vitest 14 个测试文件、55 项测试
全部通过。新增与更新的测试覆盖四块 3×2 农田、24 个后端槽位绑定、花朵映射与历史
坐标回退、水域 / 建筑阻挡、可通行地形和沿障碍滑动。

真实浏览器验收：/map-overview 能一次显示完整岛屿、弯河、南侧水岸、连续道路、两处建筑、
三座桥和四块六槽农田。游戏视角中人物出生于西北田块的有效种植槽，六个槽位清晰；
持续向左移动会停在河岸，不会进入水域；站在槽内显示 [E] 种下记忆，按 E 可打开原有
“留下一段记忆”面板，取消后恢复花园。验收未提交创作，未写入后端数据。

范围：没有新增树木、围栏、建筑细节、寻路、地图编辑器或新游戏机制；Music Companion、
AI Engine、Music Engine、Flower Engine 和后端 Creation / Planting 数据结构未修改。
"""


STEP_13_1 = """
Frontend Step 13.1 — Map Connectivity Fix
=========================================

目标：在 Grid-based Map Layout V1 基础上只修复道路连通、水域连续性、桥梁落点和农田
入口，不改变 1448 × 1086px 世界、16px 地形格、2.5 倍镜头、30px Player 或业务系统。

修改：
- 删除左上方停在主建筑侧墙的孤立横向道路和没有目标的西北竖向支路。主建筑改由正南方
  的连续道路进入；辅助建筑继续通过中央道路的东北支路连接。
- 左侧河流的下段向南延伸，与底部水域直接相连，清除了左下方的草地断层。南侧水域现在
  从第 60 行延伸至地图底部，形成连续约 8 个逻辑格深的水带。
- 左桥保持横向，完整跨越西侧竖河；桥西增加短入口道路，桥东直接接入中央主路。南桥
  调整为从南岸第 58 行纵向延伸至地图底部，主体覆盖南侧水域并连接中央南北道路。
  原右侧临时桥及其无用途支路已移除，当前地图只保留左入口桥和南入口桥。
- 西北、东北田地使用下方中央入口；西南、东南田地的上下入口均对准中间列。南部两段
  道路合并为一条连续横路，消除了中间一格断点。全部 24 个 SOIL 种植槽保持完整，
  GardenMapLayout 的后端 grid_x / grid_y 绑定未改变。
- 四块田地的所有入口道路统一扩为 4 个逻辑格，与田地中间种植槽逐格对齐。左桥只保留
  水面上的 9 格桥身并保持 4 格道路宽度；南桥只保留南侧 8 格深水面上的桥身，宽度由
  7 格收窄为与南北道路一致的 4 格。两岸陆地区域继续使用 PATH，不再用 BRIDGE 覆盖；
  左桥西岸入口上缘补回 1 个 GRASS 河岸格，避免陆地道路的角落直接贴住开放水面。

验证：2026-10-21 TypeScript / Vite 正式构建通过；Vitest 14 个测试文件、60 项测试
全部通过。新增测试验证西河至南水域连续、南侧水深为 8 格、左右岸 / 南岸桥头连接、
桥梁主体只处于水面、桥宽与道路一致、田地入口为 4 格，以及全部 PATH / BRIDGE 格
属于同一个道路连通分量。

真实浏览器验收：/map-overview 显示左河连续汇入南侧水域，西桥横跨河流，南桥纵向穿过
加宽水域；主建筑、辅助建筑、四块农田和两个地图入口均由同一路网连接。四块农田仍为
3 × 2 六槽布局，入口位于边缘中部，没有道路覆盖 SOIL。未修改或提交任何花园数据。

范围：没有增加树木、围栏、花丛、建筑细节、地图编辑器或新游戏机制；人物、摄像机、
Creation、Flower Memory、音乐版本和后端接口均未改动。
"""


CURRENT_MAP_DOCUMENTATION = """
当前地图的完整规格集中记录在 docs/architecture/Frontend_map_v1.md，包括：
- 1448 × 1086 世界、16px 地形格与 4 × 4 泥土区域的三层坐标；
- 六种地形及通行规则；
- 四块田地的起点、西北与东南连续泥土区及 444 个逐格种植位置；
- 1 × 1 小花、以中心格定位的 3 × 3 大花、降级和占地冲突规则；
- 当前河流、路网、两座桥、4 格田地入口及浏览器入口；
- Pixi 渲染层、摄像机、脚底碰撞与既有业务流程的关系；
- 2026-10-21 的 63 项前端测试、92 项相关 Python 测试和后续未实现范围。

后续修改地图时，应同时更新 TerrainMap.ts、相关测试、本进度文件和 Frontend_map_v1.md，
避免运行时地图、全局总览与文字记录出现不同版本。
"""


STEP_14 = """
Frontend Step 14 — Per-Tile Planting with 1×1 / 3×3 Flowers
===========================================================

目标：把每个 16 × 16px SOIL 地形格变成独立种植单位。小花占 1 × 1；大花以玩家选中格
为中心占 3 × 3。大花放不下时降级为小花，任何花朵都不能与已有占地重叠。

实现：
- application/garden_planting.py 集中定义四块田地的 SOIL 判断、大小花 footprint、旧坐标
  兼容、冲突检查和降级规则。CreationService 在耗时生成前调用一次可注入随机源，50%
  尝试 large、50% small；最终结果写入种植记录，刷新与渲染不再随机。
- PlantingRecord 与 GardenRenderFlower 新增 placement_schema_version、flower_size 和
  occupied_tiles。terrain-v1 记录保存中心 x/y 以及 1 或 9 个占地格；旧记录缺少字段时
  默认 legacy + small。GardenService 在保存前再次检查边界和占地冲突。
- Preview Garden 从旧 16 × 10 坐标扩为 91 × 68 地形坐标。前端每个 SOIL 格都创建独立
  Plant Spot。西北与东南田地内部的五条草缝均改为 SOIL，另外两块仍保留六块分区，
  四块田地共 444 个种植格；大花 9 格共享同一个 Flower 交互目标。
- 小花与大花使用稳定的不同渲染比例。摄像机视口固定为 840 × 552，不会因后端网格扩大
  而缩小画面；人物、2.5 倍镜头、地图和现有 Creation / Memory / Music UI 保持不变。
- 按用户要求清空 database/preview/planting_records.json 中 8 条旧种植记录。旧记忆、音乐、
  FinalCreation 和 FlowerArtifact 资产保留，删除范围没有扩大。

测试：2026-10-21 TypeScript / Vite 构建通过；Vitest 14 个测试文件、63 项通过；
Application、Backend 与 Flower Engine 相关 Python 测试 92 项通过。Step 14 测试覆盖 1×1、
3×3、边缘 / 间隔 / 冲突降级、中心已占用、非 SOIL、九格同一记忆、随机注入、持久化和
历史记录默认 small。整个 Python 仓库测试另有 19 个旧 AI 测试在收集阶段因本地模型网络
和系统临时目录权限失败，本次相关测试没有断言失败。

真实浏览器验收：重启 Garden API 后确认 garden 为 91 × 68、旧花数量为 0；正式页面保持
原视野和人物比例，玩家位于 SOIL 单格时显示 [E] 种下记忆，移动到相邻格提示仍正确；
Creation Overlay 可以打开、取消并恢复移动。验收没有提交真实 AI / ACE-Step 创建，所以
尚未把“大花实际生成、边缘实际降级、刷新后保持”标为浏览器通过。

后续布局微调：按用户要求把西北、东南田地六块土地之间的草缝全部改成 SOIL，两块田地
分别成为 14 × 9 的连续大田；东北、西南仍保持六块分隔布局。前后端 SOIL 判断已同步，
种植位置总数为 444。全局地图浏览器验收确认两块合并田地显示正确。

西桥东侧桥头下方另补 1 × 3 的竖向 GRASS 河岸，使道路与水域之间具有清楚的绿色过渡。

详细地图与占地规格见 docs/architecture/Frontend_map_v1.md。完成后没有开始地图美化。
"""


CREATION_RUNTIME_FIX_2026_10_23 = """
运行修复 — 本地真实创作链路（2026-10-23）
============================================

问题：浏览器提交种花时曾收到 502。原因有两项：ACE-Step 的 HTTP 服务可以监听 8001，
但音乐模型尚未初始化；同时本机 Ollama 的 OpenAI SDK 流式调用返回 502，直接访问其
OpenAI 兼容 HTTP 接口则正常。

修复：
- scripts/Start-MuseGarden.ps1 在启动 Garden API 前检查 ACE-Step /health；若模型未加载，
  自动调用 /v1/init 加载 acestep-v15-turbo，确认完成后才继续启动。
- ai_engine/llm/client.py 改为以 requests 直接调用 127.0.0.1:11434/v1/chat/completions，
  使用非流式完整响应，再维持原有 Blueprint 解析流程。

验证：2026-10-23 从干净临时数据目录完成真实 AI 文本解析、ACE-Step 音频生成、Flower
Engine 创建及 91 × 68 地形花园的种植。结果为 lily、large（3 × 3）、音频 artifact
e944461b-95a3-4c3e-aa9e-73458c869a89。测试目录已删除，未向正式 database/preview
写入测试花朵。启动脚本随后确认 Ollama、ACE-Step、ACE-Step 模型、Garden API 与前端均
已就绪。
"""


STEP_15 = """
Frontend Step 15 — Mini Map Overlay
===================================

目标：在花园场景内按 M 打开完整地图缩略图，显示玩家当前位置；再次按 M 或 Esc 关闭。

实现：
- 新增 ui/MiniMapOverlay.tsx，直接遍历 MUSE_GARDEN_TERRAIN 绘制 SVG 缩略图；没有第二份地图
  数据，也没有路由跳转或重新创建 Pixi 世界。
- GardenWorld 暴露玩家脚底的真实世界坐标。打开地图时 App 读取该坐标，以 worldWidth/worldHeight
  相同坐标系标记玩家位置；地图打开时玩家已暂停，因此不会发生过期位置或位置漂移。
- App 使用一个受控的全局快捷键：非输入控件、且没有 Creation / Flower Detail 面板时，M 切换地图；
  Esc 仅在地图已打开时关闭。地图与既有面板互斥，复用 GardenWorldView 的 paused 输入锁，并在
  暂停时清除 held keys，关闭后不会让角色突然移动。

验证：新增 App 测试覆盖 M 打开/关闭、Esc 关闭、位置标记和 Creation / 输入框互斥；该文件 12 项
测试通过。Vite 构建通过。完整 Vitest 在当前受限运行时中有若干既有套件因临时 Vite 缓存文件
ENOENT 无法加载；单文件测试与 TypeScript 构建均正常。用户已在真实浏览器手动确认功能通过。

范围：未修改世界尺寸、地形、种植、摄像机、人物或后端。Step 15 完成；下一步为 Step 16 地图美化。
"""

STEP_16_0 = """
Frontend Step 16.0 — Mini Meadow Asset Download & Inspection
=============================================================

完成：2026-10-25 从官方 itch.io 页面下载 Mini Meadow — 16×16 Pixel-Art Tileset，保存原始 ZIP
与完整解压内容到 assets/third-party/mini-meadow/。ZIP 为 65,675 bytes，SHA-256 为
608ba6d099c4f8aedf363afc7e483f996c9c4c03d1672dfa4f0b43739d0a5674；解压前检查了目录项，
未发现路径穿越或根路径。manifest.json 的 75 项均存在。

检查：独立地形和装饰均为 16×16 RGBA PNG；ground.png 为 144×16，三个静态边缘图集为
128×16，四个水岸帧图集各为 128×16，props.png 为 160×16。包含 grass_a/grass_b、dirt、
water_1..4、草地与水/土/沙/石的八方向过渡、以及 10 个透明装饰。包内已有 atlas.png 与
scene.png 预览。

适配结论：grass_a/grass_b 适合未来 GRASS 原型；dirt 可以随后评估用于 PATH / SOIL；四帧
water 与草水岸边适合后续 WATER；没有桥梁或建筑瓦片，BRIDGE / STRUCTURE 保持当前表现。
保留原 README、manifest 和 CC0-1.0 许可说明；完整索引在 assets/third-party/mini-meadow/
ASSET_INDEX.md。

范围：没有修改任何游戏代码、地图、渲染、碰撞、种植或后端。等待确认后才开始 Step 16.1。
"""

STEP_16_1 = """
Frontend Step 16.1 — Grass Tileset Prototype
==============================================

目标：只把 GRASS 的纯色格换为 Mini Meadow 像素瓦片，保持 TerrainMap、坐标、碰撞、种植、
摄像机、人物与其他五种地形不变。

实现：
- 保留第三方原始素材在 assets/third-party/mini-meadow/，仅复制实际运行需要的 grass_a.png 和
  grass_b.png 到 frontend/src/assets/third-party/mini-meadow/。
- 新增 TerrainTextures.ts：Pixi Assets 以 nearest filtering 异步加载两张 16×16 纹理一次，并由
  GardenWorld 缓存后交给 WorldScene；刷新花园复用同一纹理，不重复加载。
- TerrainRenderer 保持 PATH / WATER / SOIL / STRUCTURE / BRIDGE 的既有 Graphics 颜色。只为每个
  GRASS 格建立 Mini Meadow Sprite；grass_a 为基础，grass_b 由稳定坐标 hash 以约 1/11 概率选择。
  同一坐标刷新后始终使用同一变体，避免逐帧随机与棋盘式交替。
- TerrainColors.ts 让全局地图和 Mini Map 继续使用现有简化地形颜色；缩略图没有复制新的瓦片渲染。

验证：TerrainRenderer 与 GardenWorld 聚焦测试 6 项通过；App / Mini Map 测试 12 项通过；Vite
TypeScript 正式构建通过。完整 Vitest 在当前受限运行时仍可能因临时 Vite 缓存 ENOENT 影响部分
既有套件加载，聚焦测试本身没有失败。正常本地服务已确认在 5182 就绪；当前打开的 5183 为旧的
隔离前端且测试 API 已停止，不能用于本次浏览器画面验收。

范围：没有改动 SOIL、PATH、WATER、BRIDGE、STRUCTURE、地图布局、业务数据或后端。Step 16.1
完成后暂停，等待用户在 http://127.0.0.1:5182/ 检查草地效果。
"""

STEP_16_1_1 = """
Frontend Step 16.1.1 — Grass Variety Refinement
================================================

目标：减轻大面积草地的重复感，只调整 GRASS 的基础瓦片搭配。

检查结果：Mini Meadow 的连续草地底纹只有 `grass_a` 与 `grass_b` 两张；两张均已在 Step 16.1 接入。
此前 `grass_b` 的稳定坐标 hash 覆盖率约为 1/11，且两张瓦片色调接近，因此远看仍较单调。透明 `tuft`
草丛素材存在于原始素材包，但未用于最终运行时画面。

实现：将 `grass_b` 的确定性覆盖率调整为约 1/5；每个坐标刷新后仍选择相同底纹。未加载、复制或渲染
`tuft`，也未使用其他装饰素材。TerrainMap、碰撞、种植、人物、道路、田地、水域、桥梁、地图布局和
Mini Map 均未改动。

验证：TerrainRenderer 聚焦测试 3 项通过，覆盖稳定选择、第二张底纹 15% 至 25% 的覆盖范围，以及非
GRASS 地形仍留在原有颜色层。此前本 Step 的 Vite TypeScript 构建通过；本次最后一次构建被
`FlowerDetailOverlay.tsx` 向 `MusicCompanionCard` 传递已不存在的 `onUseSuggestion` 参数阻断，
这是同时进行的音乐详情代码不匹配，与草地修改无关，尚未在本 Step 扩大修复范围。

浏览器：正常本地服务 5182 已加载两种基础草地纹理；本次未改变用户打开的花朵详情面板状态。当前打开的
5183 为旧隔离前端，不能作为正式画面验收地址。

范围：只改善 GRASS。当前素材包仅有两种连续草地底纹；若后续仍需更丰富的草地，需要另选或制作更多
基础草地变体。
"""

STEP_16_1_2 = """
Frontend Step 16.1.2 — Grass Asset Review
===========================================

目标：在不修改正式游戏画面的前提下，检查 Mini Meadow 草地素材的实际像素与重复效果，为后续基础底纹选择提供依据。

检查结果：manifest 与 PNG 内容确认仅有 `grass_a.png`、`grass_b.png` 两张连续、无透明的 16×16 草地底纹。
两者共用相近的三档绿色，并均包含固定的小斑点；所有 `edge_grass_*` 都包含另一种地形和边界线，不能作为
连续草地。`tuft`、灌木、花、蘑菇、石头等均为透明装饰，不适合基础地面，且未接入运行时。

交付：新增 development/asset-previews/mini-meadow-grass-review.svg，包含 grass_a 单独重复、grass_b 单独重复、
以及当前稳定 80% A / 20% B 的三组 32×18 格对比。配套说明在同目录 mini-meadow-grass-review.md。预览采用内嵌
原始 PNG 与最近邻显示，不会修改原素材。

结论：素材包没有更安静的第三种连续草地；当前重复感来自两张 16×16 底纹本身，并非遗漏了未接入的基础素材。
下一步需要由人工在预览中选择保留混合、只使用其中较安静的一张，或另选兼容的连续草地素材；本 Step 未实施任何
运行时草地修改。

范围：没有修改 TerrainRenderer、TerrainTextures、TerrainMap、运行时素材、地形、碰撞、人物、种植、镜头、
Mini Map、后端或地图布局。
"""

STEP_16_2 = """
Frontend Step 16.2 — Path & Soil Visual Foundation
===================================================

目标：只为 PATH 接入像素泥土纹理，同时保持 SOIL 的深棕色种植区域，以建立道路与可种植土地之间清楚的视觉区分。

素材检查：Mini Meadow 的 `dirt.png` 是 16×16、不透明、可无缝重复的基础地面瓦片。它适合作为道路连续底纹；
同一瓦片若同时用于 SOIL，会降低道路和种植区域的辨识度，因此 SOIL 暂不贴图，继续使用现有深棕色纯色。

实现：将实际运行需要的 dirt.png 复制到 frontend/src/assets/third-party/mini-meadow/。TerrainTextures 以 nearest
filtering 一次加载该纹理；TerrainRenderer 只为每个 PATH 格创建 `mini-meadow-path-tiles` Sprite。每个 PATH
格固定使用同一张无缝 dirt 瓦片，位置、尺寸、TerrainMap、地图布局和地形分类均未改变。GRASS 继续使用既有
两张瓦片混合；SOIL、WATER、BRIDGE、STRUCTURE 仍保留原渲染。

验证：TerrainRenderer 聚焦测试 3 项通过，覆盖草地稳定变体、草地比例、PATH Sprite 数量以及其他地形仍在颜色层；
TerrainMap 测试 9 项通过。Vite TypeScript 正式构建通过。合并运行两个 Vitest 文件时，本机受限运行时仍偶发
临时 Vite 缓存 ENOENT；单文件运行均通过。Chrome 正式服务 5182 浏览器验收确认：道路为像素泥土纹理、SOIL
仍为深棕色种植区，Player、花朵与当前格提示正常显示。

范围：未改动 TerrainMap、道路布局、碰撞、玩家、镜头、种植规则、花朵、Creation、Flower Detail、Music
Revision、Mini Map、后端、草地、水域、桥梁或建筑。Step 16.2 完成后暂停，等待人工检查整体地图效果。
"""

STEP_16_3 = """
Frontend Step 16.3 — Water & Shoreline Foundation
==================================================

目标：为 WATER 接入静态水面与草水河岸过渡，不改变 TerrainMap、河道、桥梁、角色或任何游戏业务。

素材：使用 Mini Meadow 的 `water_1.png` 作为唯一静态、可无缝重复的水面帧；不混用 water_2..4，因此本 Step
没有水面动画或相邻格棋盘感。曾检查 frame 1 的草水边缘 PNG，但其直边与转角自带的黑线在连续拼接时粗细不一致，
故不作为运行时河岸素材；原始第三方文件仍完整保存在素材归档中。

实现：TerrainTextures 以 nearest filtering 一次加载水面，并继续由 GardenWorld 缓存。TerrainRenderer 新增独立
water 与 water-bank 容器。每个 WATER 格先绘制 water_1；再对每条直接相邻的 WATER→非 WATER、非 BRIDGE 边界
绘制一条固定 1 个世界像素、颜色 `#1e1c28` 的深色线。直边和转角因此采用同一个线宽；WATER→BRIDGE 不画岸线，
保证桥面不会被压线。这只改变视觉绘制，不改变任一地形分类或通行规则。

层级：grass 基础层 → water 基础层 → 原有 Graphics（SOIL / STRUCTURE / BRIDGE）→ path → water-bank 线条。
桥梁邻接水面不生成岸线；动态 Player 与花朵仍由 WorldScene 的实体层绘制。

验证：TerrainRenderer 聚焦测试 4 项通过，覆盖水→草、水→PATH/SOIL、桥面相邻水格不画线，以及 grass / water /
path / water-bank 分层数量；TerrainMap 测试 9 项通过；Vite TypeScript 正式构建通过。Chrome 正式服务 5182
浏览器验收：河道直边和阶梯状转角均显示同样的细岸线，水面连续，路径与 SOIL 没有被岸线遮盖。未实现动画、
泡沫、粒子或任何装饰。

范围：未修改 TerrainMap、世界尺寸、格子、摄像机、人物、移动、碰撞、田地、种植规则、Creation、Flower Detail、
Music Revision、Mini Map、后端、草地、道路、桥梁或建筑。Step 16.3 完成后停止，等待人工检查。
"""

STEP_16_4 = """
Frontend Step 16.4 — Bridge & Structure Visual Foundation
==========================================================

目标：只改善既有 BRIDGE 与 STRUCTURE 的基础像素美术；不改 TerrainMap、坐标、碰撞、种植、人物、相机或业务流程。

实现：TerrainColors 集中定义克制的木材和屋顶色板。TerrainRenderer 在静态地形初始化时识别 BRIDGE 与 STRUCTURE
的四向连通区域，新增 `pixel-wood-bridge-details` 与 `pixel-structure-details` 两个 Graphics 层；不会在每帧重复
分析或创建图形。

桥梁：每个现有 BRIDGE 格保持原位置，绘制木棕桥面；只在连通桥段的外边界画 1px 深色轮廓，内部格不画粗边。
规则矩形桥段依据长边自动判定方向：横桥绘制纵向木板线，竖桥绘制横向木板线，并只加一条轻微高光。桥面绝不延伸
到 WATER / PATH / GRASS，且 WATER→BRIDGE 不生成 Step 16.3 的岸线。

建筑：按真实 STRUCTURE 连通区域逐格覆盖屋顶色，外边界使用统一 1px 轮廓；矩形区域添加浅色屋顶上沿、稀疏横向
屋顶线及位于底边中央的小入口。所有细节都被限制在 STRUCTURE 格内，因而不会覆盖道路、田地或水域。

层级：grass → water → 原有基础 Graphics（SOIL / STRUCTURE / BRIDGE）→ path → bridge details → structure details
→ water-bank outlines → 动态实体。Mini Map 与 /map-overview 继续使用其简化色块，不承担运行时细节绘制。

验证：修改前的组合 Vitest 命令曾在受限环境遇到临时 SSR 缓存 ENOENT；修改后分别执行的 TerrainRenderer 测试
5 项通过、TerrainMap 测试 9 项通过，`npm run build` 通过（只有既有的 bundle 大小提示）。Chrome 5182 浏览器
验收确认建筑轮廓、顶面与屋顶线清楚显示，且人物移动未受影响；桥梁方向、外边界和不穿越桥面的岸线由针对性单元
测试覆盖。本次没有修改地图布局或任何业务数据。

范围：未修改 TerrainMap、世界尺寸、格子、摄像机、移动、碰撞、田地、种植、Creation、Flower Detail、Music
Revision、Mini Map、后端、AI / Music / Flower Engine，亦未新增外部素材或依赖。Step 16.4 完成后停止，等待人工检查。
"""

STEP_16_5 = """
Frontend Step 16.5 — Terrain Visual Harmony & Polish
=====================================================

目标：对已完成的 GRASS、PATH、SOIL、WATER、BRIDGE 与 STRUCTURE 进行整体检查，只修复可确认的视觉问题，
不为制造改动而添加装饰或重构渲染器。

检查结果：正式 5182 服务的实际游戏视角、`/map-overview` 全图、草地与道路、田地入口、建筑与道路、河道边线及
桥梁布局均已检查。地形层级维持 grass → water → 基础图形 → path → bridge details → structure details →
water-bank outlines → 动态实体；未发现透明缝隙、岸线压桥、道路遮田地或建筑越出 STRUCTURE 格的问题。

唯一确认调整：实际视角中建筑屋顶的原冷灰基调较重，因此仅在 TerrainColors 的集中色板中把 `structureRoof`、
`structureRoofLight` 与 `structureRoofShade` 调为稍暖的自然棕灰；轮廓、屋顶线、入口、地图格和所有层级均保持
不变。草地的稳定双瓦片混合、PATH dirt、SOIL 深棕、water_1、统一 1px 岸线和木桥色板均已保留。

验证：分别执行 TerrainRenderer 5 项、TerrainMap 9 项、GardenWorld 4 项、Player 7 项、interactions 6 项及
App 12 项测试，合计 43 项通过；`npm run build` 通过（仅保留已有 bundle 大小提示）。Chrome 5182 已检查正式
游戏视角与完整地图总览；没有提交 Creation、生成音乐或更改任何花园数据。M 键、Creation、Flower Detail 与音乐
版本流程本轮未产生代码改动，相关 App / interaction 回归测试通过。

范围：未修改 TerrainMap、世界尺寸、格子、地图布局、碰撞、移动、相机、花朵占地、Creation、Flower Detail、
Music Revision、Mini Map、后端或任一 Engine；未新增素材、依赖、树木、草丛、石头、粒子与水面动画。Step 16.5
完成后停止，等待人工检查是否进入环境装饰设计。
"""

STEP_16_6_1 = """
Frontend Step 16.6.1 — Environmental Decoration Layout Preview (Shelved)
=======================================================================

状态：未实施，不属于当前版本功能。

曾生成仅供讨论的开发期装饰预览，但人工评审认为灌木、岩石等道具会使当前地图显得幼稚，故明确不接入正式游戏。
相关预览保留在 `development/asset-previews/` 作为以后重新设计环境美术时的参考；它们不被运行时代码加载，也不应
被计入功能完成、浏览器验收或后续路线图。

若未来重新启动环境美术，应先重新选择更成熟、统一的视觉方向，再单独决定树木素材、装饰密度与碰撞规则。
"""

PHASE_MILESTONE = """
MuseGarden 阶段性里程碑 — 核心功能开发暂时收尾
====================================================

当前版本已完成：Pixi Garden World 与 React Overlay、四方向角色及移动动画、世界边界与摄像机、基于脚底位置的
交互、Creation Overlay、真实 Creation API、种花与花朵持久化、花朵记忆详情、音频播放、音乐修改与版本选择、
Grid Terrain Map、1×1 / 3×3 花朵占地、Mini Map，以及 Step 16.1–16.5 的基础地形美术与整体协调。

当前阶段不再主动扩展核心业务功能。后续工作仅限于 Bug 修复、真实体验验收、性能或稳定性维护，以及用户明确
提出的按需美化。未实施事项包括：环境装饰、树木与碰撞、动态水面、NPC、背包、搜索 / RAG 与其他新玩法。

验证边界：前端构建、各模块自动化测试和若干正式浏览器流程已在各 Step 分别执行；完整端到端 AI / ACE-Step
生成仍依赖本机 Ollama、ACE-Step 与模型就绪状态，不能把自动化测试等同于每次机器环境中的人工生成验收。
"""

MAINTENANCE_FLOWER_REMOVAL = """
Maintenance — Flower Removal & Tile Replanting
================================================

目标：在不扩展新玩法的前提下，让玩家能在已种植花朵的占地范围内直接移除花朵，并把对应 SOIL 格恢复为可种植状态。

实现：复用已有 `DELETE /api/gardens/{garden_id}/plantings/{planting_record_id}` 种植移除接口；前端不伪造删除状态。
当玩家脚底进入一朵小花的 1×1 或大花的 3×3 占地范围，World Overlay 同时显示原有 `[E] 查看记忆` 与
`[Delete] 删除花朵`。查看与删除提示以分开的横向间距显示。Delete 或 Backspace 键只在当前目标为花朵、未长按、
无修饰键且焦点不在输入控件时触发；按键后刷新
GardenRenderSpec，因此已移除花朵的格子会重新变为可用的 SOIL 种植位。

数据约定：依据后续确认，删除只移除花园中的 PlantingRecord 与不再引用的 FlowerArtifact；该次创作的原始文字、
音乐和版本记录仍在本地归档中保留，但不会再作为花园中的可交互花朵出现。没有前端恢复按钮；若要再次种植，玩家在
释放后的 SOIL 格重新走完整创作流程。

验证：前端 API、Overlay、GardenWorld 键盘及 App 回归共 26 项 Vitest 测试通过；后端既有种植移除、保留记忆和
HTTP DELETE 契约合计 19 项测试通过。未在正式花园数据上按 Delete 做人工删除，以避免为了验收而删除用户现有记忆；需由用户在想
移除的实际花朵上进行一次人工验收。此前 `npm run build` 曾被系统临时 esbuild 文件的访问拒绝阻断，不是 TypeScript
编译错误；在该锁释放后应重新运行构建确认。

范围：未修改地形地图、大小花规则、Player、摄像机、Creation、Flower Detail、音乐版本、后端数据模型或任一 Engine。
"""

MAINTENANCE_ONBOARDING = """
Maintenance — First-use Onboarding
==================================

目标：根据真实试用中“初次进入不清楚从何开始”的反馈，为首次使用者提供简短、可重复查看的操作引导。

实现：`OnboardingOverlay` 在首次访问时显示移动、空地/花朵 `E` 交互、`M` 地图及 `Delete` 删除花朵四项说明。
关闭“开始探索”后，将完成状态写入浏览器 localStorage 的 `musegarden-onboarding-complete`；后续访问不会自动打断体验，
但用户可从 World Overlay 的“新手指引”按钮随时重新打开。引导显示时暂停世界输入，与创建、花朵详情和地图弹窗共用暂停边界。

验证（2026-11-04）：前端 Vitest 15 个测试文件、75 项测试通过，覆盖首次展示、关闭后的持久化和手动再次打开；
TypeScript / Vite 构建通过。真实本地界面截图已归档到课程材料的 `04 测试与验证/测试截图/MT10-首次使用引导.png`。

范围：不更改创建、音乐生成、花朵数据、地图布局或后端接口；仅改善首次理解成本。
"""
