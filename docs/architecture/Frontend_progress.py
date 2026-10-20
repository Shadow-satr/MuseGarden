"""MuseGarden Frontend 开发进度，按正式章节顺序记录。"""

CURRENT_STATUS = "Frontend Step 12 — Map Art Integration & Viewport Calibration 已完成；正式大地图与 3 倍田地视角已接入，等待 Step 13 种植区域映射。"

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
- Player 保持 58px 可见高度、120px/s、四方向六帧动画与脚底 anchor。逻辑种植格保持
  48px，因此人物为约 1.21 个逻辑格高。每块小田地约定为 3 × 2、共 6 个逻辑格；
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

