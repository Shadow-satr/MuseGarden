"""
MuseGarden Flower Engine 开发进度

本文件只记录 Flower Engine 的开发状态。
AI Engine 与 Music Engine 的历史分别查看：
docs/architecture/AIEngine_progress.py
docs/architecture/MusicEngine_progress.py
跨模块最新状态：docs/architecture/MuseGarden_progress.py。
历史 Step 中的 frontend/ 路径为当时位置；现有工程预览页已迁至 development/demo/creation_preview/。
"""

CURRENT_STATUS = "Step 12 工程 Demo 位于 development/demo/creation_preview；正式 frontend/ 已完成 Garden World、真实种花与记忆详情，并在 Step 9 接入四方向 Player 走路动画。"

CURRENT_INTEGRATION_NOTE = (
    "FlowerArtifact 绑定初始 MusicBlueprint，后续音乐修改不重生花。"
    "正式前端已接入历史音乐版本选择；AI 记忆检索尚未接入。"
)


STEP_1 = """
Step 1：FlowerSpec 与 Blueprint Adapter
=======================================

状态：通过。

开发目标：
在不调用 LLM、网络、数据库或像素渲染器的前提下，建立 AI Engine 与
Flower Engine 之间稳定、可验证的输入边界。

新增文件：
- flower_engine/schema.py
- flower_engine/adapter.py
- test/flower_engine/1/test_blueprint_adapter.py
- docs/architecture/FlowerEngine_progress.py

FlowerSpec：
- species：现实花型 token，首版包含 rose、peony、sunflower、tulip、
  hydrangea、lily、daisy、lavender 和安全回退 wildflower。
- palette：命名色调 token；具体像素颜色由后续 FlowerRenderSpec 定义。
- size、stem_height、sway_speed、glow：范围 0-1 的渲染语义参数。
- petal_count：范围 3-16 的花瓣复杂度近似值。
- particle_effect、decoration、growth_direction：受限视觉 token。

确定性映射：
- texture 优先决定现实花型；未知 texture 回退到主情绪，再回退 wildflower。
- 主情绪决定已知 palette；未知情绪按 valence 五档选择安全色调。
- energy 决定 size、stem_height，并与乐器数量共同影响 petal_count。
- tempo 在 40-180 BPM 范围内归一化为 sway_speed，范围外安全截断。
- valence 与部分 texture 共同决定 glow。
- 18 个正式 progression 标签均固定映射为 growth_direction 与
  particle_effect。
- 主情绪决定轻量 decoration；未知情绪使用 none。
- 所有浮点输出统一保留两位。

边界：
- scene 与 secondary_emotions 当前继续保存在 MusicBlueprint 中，不参与首版
  视觉映射。
- Adapter 只接受 MusicBlueprint，不修改输入对象。
- FlowerSpec 只表达渲染语义，不包含像素坐标、十六进制颜色、Sprite、文件路径、
  Draft、Revision 或 Artifact 信息。

测试覆盖：
- 正常映射、公开类型、JSON 序列化、确定性和输入不变。
- 常见中英文 texture、未知值回退与空乐器列表。
- energy、valence、tempo 的低值、高值与有界映射。
- 18 个 progression 标签的完整视觉映射。
- 所有受限 token 和数值边界的 Pydantic 校验。
- 非 MusicBlueprint 输入拒绝，以及 Adapter 不引入外部服务或跨 Engine 依赖。

下一步：
Step 2 将建立 Flower Reference Library，为各现实花型定义正式参考数据、基础结构、
适用语义范围与未来渲染标识。
"""


STEP_2 = """
Step 2：Flower Reference Library
================================

状态：通过。

开发目标：
建立可扩展的现实花卉参考库，使 FlowerSpec 中的音乐视觉变化保持在对应花型可识别的
结构范围内，并为后续 Pixel Renderer 提供稳定的现实结构依据。

新增与修改：
- flower_engine/schema.py：新增 FlowerReference、BloomShape 与 LeafShape 契约。
- flower_engine/reference_library.py：现实花库、查询接口与规格约束规则。
- flower_engine/adapter.py：输出 FlowerSpec 前自动应用现实花型约束。
- flower_engine/__init__.py：公开 FlowerReference、查询和约束接口。
- test/flower_engine/1/test_reference_library.py：Step 2 测试。

首版花库：
- rose / 玫瑰
- peony / 牡丹
- sunflower / 向日葵
- tulip / 郁金香
- hydrangea / 绣球
- lily / 百合
- daisy / 雏菊
- lavender / 薰衣草
- wildflower / 野花安全回退

FlowerReference：
- species、display_name：稳定花型 token 与中文显示名称。
- bloom_shape、leaf_shape：供未来像素模板使用的花冠与叶片结构 token。
- base_petal_count、petal_count_range：基础花瓣数量与可识别范围。
- base_stem_height、stem_height_range：基础茎高与允许变化范围。
- supported_palettes、supported_decorations：该现实花型允许的色调和装饰。
- Schema 校验基础值必须位于范围内，选项非空且不能重复。

公开接口：
- get_flower_reference(species)：查询参考数据并返回独立深拷贝；未知花型明确失败。
- constrain_flower_spec(spec)：不修改输入，将花瓣数量和茎高截断到现实范围；不支持的
  palette 回退到该花默认色调，不支持的 decoration 优先回退 none。
- blueprint_to_flower_spec() 已接入约束流程，对外直接返回现实花型兼容的最终规格。

扩展原则：
首版使用 8 种现实花型加 wildflower。未来增加花型时，只需扩展 FlowerSpecies、结构
token（如需要）、FLOWER_REFERENCES 和对应测试，不改变 Blueprint Adapter 的公开接口。

测试覆盖：
- 花型枚举与花库完整一一对应，所有参考数据可 JSON 序列化。
- 查询返回独立副本，未知 species 被拒绝。
- 花瓣、茎高、色调与装饰的确定性修正，输入对象保持不变。
- 合法规格保持相同语义。
- FlowerReference 的名称、范围、非空选项与重复选项校验。
- 花库源码不引入网络、LLM、数据库或渲染器。

下一步：
Step 3 将增加 variation_seed 与稳定的个体变化参数，使同一现实花型能够产生可复现但
不完全相同的花朵身份。
"""


STEP_3 = """
Step 3：Flower Variation & Stable Identity
==========================================

状态：通过。

开发目标：
在 FlowerSpec 的情绪与音乐视觉语义之上，增加可复现的轻微个体变化，使同一种现实
花型能够产生不同个体，同时让历史花朵可以通过 seed 稳定重建。

新增与修改：
- flower_engine/schema.py：新增 FlowerVariationSpec 与 63 位 seed 上限。
- flower_engine/variation.py：版本化 SHA-256 个体变化算法。
- flower_engine/__init__.py：公开 FlowerVariationSpec 与 build_flower_variation()。
- test/flower_engine/1/test_flower_variation.py：Step 3 测试。

FlowerVariationSpec：
- variation_seed：0 到 2^63-1 的严格整数，不接受布尔值或浮点数。
- petal_length_scale、bloom_width_scale：0.90-1.10 的轻微比例变化。
- stem_curve：-1 到 1 的归一化弯曲方向和强度。
- leaf_count：2-5。
- leaf_angle_offset：-15 到 15 度。
- color_value_shift：-0.08 到 0.08，只表达未来渲染时的明暗偏移。
- sway_phase、particle_phase：0-1 的动画起始相位。

稳定身份算法：
- build_flower_variation(spec, variation_seed) 要求调用方显式提供 seed。
- 每个参数使用“算法版本 + species + seed + 参数名”的 UTF-8 文本计算 SHA-256，
  再将摘要前 64 位确定性映射到目标范围。
- 不使用 Python random 或进程级随机状态，结果不依赖调用顺序。
- variation 只依赖 species 与 seed；同一花型修改 palette、size、glow 等语义后，
  个体结构仍保持一致。species 改变时重新生成个体变化。
- 函数不修改输入 FlowerSpec，不改变花型、色调或 Step 2 的现实结构约束。

测试覆盖：
- 相同 species 与 seed 的确定性、JSON 序列化和不同语义参数下的身份保持。
- 不同 seed 与不同 species 产生不同结果。
- seed 0、普通值和最大 63 位值，以及所有变化字段的范围。
- 非 FlowerSpec、布尔/浮点/负数/超范围 seed 和无效 Schema 字段被拒绝。
- 输入对象保持不变，源码不引入网络、LLM、数据库、系统随机数或 PixiJS。

边界与下一步：
Step 3 不生成像素坐标、十六进制颜色、图层、Sprite 或图片，也不自动创建 seed。
Step 4 将定义 FlowerRenderSpec，把 FlowerSpec、FlowerReference 与
FlowerVariationSpec 转换为 PixiJS 可直接消费的具体渲染参数。
"""


STEP_4 = """
Step 4：FlowerRenderSpec
========================

状态：通过。

开发目标：
将 FlowerSpec、FlowerReference 与 FlowerVariationSpec 组合成前端无需重新理解情绪、
音乐或命名色调即可消费的版本化渲染契约。

新增与修改：
- flower_engine/schema.py：新增颜色、几何、动画和总渲染规格。
- flower_engine/renderer.py：固定像素色板与 RenderSpec 构建规则。
- flower_engine/__init__.py：公开四个渲染模型和 build_flower_render_spec()。
- test/flower_engine/1/test_render_spec.py：Step 4 测试；当前编号目录共 4 份测试。

FlowerRenderSpec：
- renderer_schema_version 固定为 1.0，支持未来兼容升级。
- template_id 固定为“{species}_v1”，用于未来选择像素模板。
- colors 包含花瓣主色、辅色、高光、花心、茎叶、glow 与粒子颜色，统一使用大写
  #RRGGBB。
- geometry 使用归一化花冠比例、茎高、弯曲、叶片和固定底部中心锚点，不绑定具体
  Sprite 分辨率。
- animation 包含摆动幅度、1200-3600ms 周期、glow 参数、粒子速率和稳定相位。
- particle_effect、decoration、growth_direction 保留 FlowerSpec 的视觉语义 token。
- layer_order 固定为 shadow、stem、leaves、bloom_back、bloom_front、decoration、
  glow、particles。

转换规则：
- 9 个命名 palette 均映射到固定像素色板。
- color_value_shift 以有界 RGB 通道平移调整花瓣、glow 与粒子明暗；花心和茎叶保持
  基础色，避免个体变化破坏可读性。
- size 与个体 bloom scale 共同决定横纵花冠比例；现实参考提供 bloom/leaf shape。
- sway_speed 映射为 0.02-0.08 摆幅和 3600-1200ms 周期。
- glow 映射为最高 0.65 透明度与 0.18 归一化范围。
- 粒子速率固定为 none/soft_glow=0、sparkles=3.5、petals=1.5、
  fireflies=2、stardust=5。
- 构建时重新计算 species + seed 对应的正式 variation，拒绝篡改或跨花型复用。
- 输入 FlowerSpec 会先通过 Step 2 现实花型约束，所有输入对象保持不变。

测试覆盖：
- 标准构建、确定性、JSON 序列化、固定图层和输入不变。
- 9 套 palette 的完整合法颜色，以及正负明暗偏移与通道边界。
- size、sway、glow、粒子映射的低值、高值和范围。
- 8 种现实花型与 wildflower 的模板、花冠和叶片结构。
- 篡改 variation、跨 species variation、错误输入类型与所有渲染 Schema 边界。
- 源码不引入 PixiJS、网络、LLM、数据库或图片处理库。

边界与下一步：
Step 4 只输出 JSON 友好的渲染参数，不创建图片、Sprite、Canvas 或前端动画循环。
Step 5 将实现 Pixel Flower Renderer，使用这些模板、色板、几何、动画和图层参数生成
可视花朵与独立预览。
"""


STEP_5 = """
Step 5：Pixel Flower Renderer
=============================

状态：通过。

开发目标：
将 Step 4 的 FlowerRenderSpec 交给独立、无业务语义判断的 PixiJS v8 渲染器，首次把
Flower Engine 的版本化 JSON 契约转换为可见、可动、可复现的像素花，并提供独立预览页。

新增与修改：
- frontend/package.json、Vite 与 TypeScript 配置：建立 React 19 + PixiJS 8 前端工程。
- frontend/src/game/flowers/types.ts：镜像 Renderer v1.0 的 TypeScript 契约。
- frontend/src/game/flowers/validate.ts：在运行时拒绝错误版本、花型、颜色、几何、动画、
  视觉 token 和图层顺序。
- frontend/src/game/flowers/templates.ts：九种花的程序化像素模板。
- frontend/src/game/flowers/renderer.ts：图层组装、装饰、glow、粒子与动画循环。
- frontend/src/game/flowers/FlowerCanvas.tsx：管理 Pixi Application 的挂载与清理。
- frontend/src/App.tsx、styles.css：独立花园预览和响应式控制界面。
- development/scripts/export_flower_preview_specs.py：从真实 Python Flower Engine 导出预览 fixture。
- frontend/public/flower-preview-specs.json：9 种花 × 3 个稳定个体，共 27 个 RenderSpec。
- frontend/src/game/flowers/flowers.test.ts：Renderer 契约、模板、粒子和 fixture 测试。
- frontend/src/App.test.tsx：用真实控件完成花型筛选、Seed 切换和暂停/恢复循环。

渲染规则：
- 48×64 逻辑像素画布以 3 倍整数比例显示，关闭抗锯齿并保持 pixelated 输出。
- rose、peony、sunflower、tulip、hydrangea、lily、daisy、lavender、wildflower
  各有可辨识的 v1 程序化模板；不依赖外部图片素材。
- 严格按 RenderSpec 的 shadow、stem、leaves、bloom_back、bloom_front、decoration、
  glow、particles 顺序创建容器。
- 颜色、花冠比例、茎高与弯曲、叶片数量直接来自 RenderSpec；前端不重新解释情绪、
  texture、energy 或 BPM。
- sway_period_ms、sway_amplitude 和 sway_phase 驱动整株摆动；glow 参数驱动呼吸；
  particle_rate 与 particle_phase 驱动稳定粒子循环。
- 粒子的初始空间布局只依赖 variation_seed，相同 RenderSpec 可重复呈现相同个体。
- Pixi Application 的异步初始化与 React effect 清理使用显式 initialized/disposed 状态协调，
  禁止在 init 完成前调用 destroy；开发入口不再用 StrictMode 重复创建 WebGL 上下文。

预览能力：
- 默认同时展示全部九种花，可过滤单个 species。
- Seed A/B/C 切换同一现实花型的三个稳定个体。
- 暂停/继续动画可冻结并恢复相位，不重建 Flower Engine 语义。
- 桌面三列、窄屏两列与移动端单列响应式布局。

验证结果：
- Vitest：2 个测试文件、5 项通过，包含 Python 导出的全部 27 个 RenderSpec 和完整
  控件交互循环。
- TypeScript 严格类型检查与 Vite 生产构建通过。
- npm 完整依赖审计：0 个已知漏洞。
- Flower Engine 4 份测试与 Music Engine 11 份离线回归测试继续通过；会在导入时调用
  外部 LLM/Ollama 的旧 AI Engine 测试不属于本次离线验证范围。
- Windows 主机端口浏览器验收通过：全新页面生成 9 张花卡与 9 个 Pixi Canvas，控制台
  0 条 warning/error，花型筛选、Seed A/B 切换及暂停/恢复控件均可操作。
- 1280px 桌面与 390px 移动视口均完成截图检查，无横向溢出、画布缺失或控件裁切。

边界与下一步：
Step 5 只负责把 RenderSpec 画出来，不创建数据库记录、FlowerArtifact、图片导出或
Creation/BlueprintRevision 关联。Step 6 将建立 FlowerArtifact 与版本生命周期，把
renderer_schema_version、template_id、variation_seed 和可重建的 RenderSpec 绑定到创作版本。
"""


STEP_6 = """
Step 6：FlowerArtifact & Flower Lifecycle
=========================================

状态：通过。

开发目标：
把 Step 1-5 已经可以稳定描述和绘制的花，提升为具有唯一身份、生成时间、可持久化
视觉快照和未来创作关联入口的正式资产。Artifact 负责“这是谁”，Renderer 继续只负责
“怎么画”。

新增与修改：
- flower_engine/schema.py：新增 FlowerArtifact 快照模型。
- flower_engine/artifact.py：新增 create_flower_artifact() 纯构建入口。
- flower_engine/store.py：新增最小本地 JSON FlowerArtifactStore。
- flower_engine/__init__.py：公开 Artifact、Store 和构建函数。
- test/flower_engine/2/test_flower_artifact.py：Step 6 生命周期测试。

FlowerArtifact：
- id：每次正式生成事件的独立 UUID。
- creation_id：可选 UUID，仅为未来 FinalCreation 集成预留；本 Step 不修改 FinalCreation。
- species、variation_seed：花型与稳定个体身份。
- flower_spec、render_spec：生成时语义与完整 v1.0 渲染参数的独立快照。
- renderer_schema_version、template_id：显式保存渲染契约与模板版本。
- created_at：北京时间生成时间。
- 模型会检查顶层 species、seed、schema version 和 template 与两个快照之间的关系，
  防止组合出自相矛盾的资产。

创建与确定性语义：
- create_flower_artifact(flower_spec, render_spec, creation_id=None) 只冻结已经完成的输入，
  不调用 LLM、音乐模型、Pixi Renderer 或任何外部服务，也不修改输入对象。
- 创建时深拷贝 FlowerSpec 与 FlowerRenderSpec；原对象后续改变不影响历史 Artifact。
- 相同 species、variation_seed 和 RenderSpec 得到相同的可重建视觉快照。
- id 与 created_at 表示一次真实生成事件，因此重复创建会拥有不同事件身份和时间；这两个
  metadata 字段不属于花朵视觉确定性的比较范围。
- 不保存图片、文件路径、Canvas、Pixi Sprite 或 React 状态。

Persistence：
- FlowerArtifactStore 使用 database/local/flower_artifacts.json 作为默认 MVP 存储。
- 支持 save()、get()、list_all()；读取时重新执行 Pydantic 校验。
- JSON 使用 UTF-8、可读缩进和临时文件替换，避免中断破坏已有记录。
- 重复 Artifact id、无效 UUID、损坏 JSON、非列表根节点和无效记录都会明确拒绝。

测试结果：
- Step 6 pytest：9 项通过，覆盖完整字段、JSON、快照独立、输入不变、确定性视觉内容、
  不同 seed、持久化往返、重复保护、损坏数据和外部依赖边界。
- Flower Engine Step 1-4 的 4 份旧测试通过。
- Music Engine 的 11 份离线回归测试通过。
- Blueprint、progression、CreationDraft、BlueprintRevision 与 FinalCreation 的 5 份相关
  回归脚本通过。

未实现范围与下一步：
本 Step 不实现 Flower Garden、种植、位置、交互、Flower UI、图片导出、Memory、Agent，
也不修改 FinalCreation。Step 7 将建立 FlowerArtifact 与 FinalCreation 的正式关联，使一次
创作可以同时追踪已选音乐与花朵。
"""


STEP_7 = """
Step 7：FlowerArtifact ↔ FinalCreation
======================================

状态：通过。

开发目标：
让已经归档的 FinalCreation 可以按照其 Blueprint 生成正式 FlowerArtifact，并支持查询、
相同个体重建和新个体再生成，使一次创作同时拥有冻结的音乐成果与可追踪的花朵历史。

新增与修改：
- flower_engine/lifecycle.py：新增 FlowerLifecycleService。
- flower_engine/store.py：新增 list_by_creation() 与 get_latest_by_creation()。
- flower_engine/__init__.py：公开 FlowerLifecycleService。
- test/flower_engine/3/test_flower_lifecycle.py：Step 7 关联与生命周期测试。
- test/flower_engine/2/test_flower_artifact.py：将旧边界断言更新为禁止 Store 导入
  Music Engine；允许 Step 7 查询方法在说明中提到 FinalCreation。

关联模型：
- 使用 FlowerArtifact.creation_id → FinalCreation.id 的花侧外键。
- FinalCreation 继续保持 Music Engine 已归档的冻结结构，不为追加花朵而被改写。
- Music Engine 不反向依赖 Flower Engine；跨 Engine 编排集中在 FlowerLifecycleService。
- 一个 FinalCreation 可以关联多份 FlowerArtifact，天然保存重新生成历史。
- 创建和查询前必须从 FinalCreationStore 验证创作真实存在，不能为任意 UUID 创建正式花。

正式生成流程：
FinalCreation.blueprint
→ blueprint_to_flower_spec()
→ build_flower_variation(seed)
→ build_flower_render_spec()
→ create_flower_artifact(creation_id)
→ FlowerArtifactStore.save()

- 花型仍由 Step 1 的 Blueprint 固定对照规则决定，不让 LLM 随机选择。
- seed 由上层显式提供；无效、布尔、浮点、负数或超过 63 位的 seed 在保存前被拒绝。
- 整条流程不调用 LLM、音乐模型、网络、PixiJS 或图片服务。

重新生成与当前花：
- regenerate(artifact_id) 默认保留原 seed，因此保持相同花型、结构、颜色与动画个体参数，
  但创建新的 Artifact UUID 与生成时间，保留真实事件历史。
- regenerate(artifact_id, variation_seed=new_seed) 保留原 FlowerSpec 语义快照，生成新的个体。
- 重新生成只追加记录，不覆盖源 Artifact。
- list_for_creation() 返回完整历史；get_current_for_creation() 采用最新 Artifact 作为当前花。
- 未关联 Artifact、悬空 creation_id 与不存在的源 Artifact 都会明确拒绝。

测试结果：
- Step 7 pytest：11 项通过，覆盖正式关联、规则生成、创作存在校验、跨创作隔离、空历史、
  同 seed 重建、新 seed 个体、历史不覆盖、无效关联、seed 边界和外部依赖边界。
- Step 6 与 Step 7 合计 20 项 pytest 通过；Flower Step 1-4 的 4 份旧测试通过。
- Music Engine 的 11 份离线回归测试通过。
- Blueprint、progression、CreationDraft、BlueprintRevision 与 FinalCreation 的 5 份相关
  回归脚本通过。

未实现范围与下一步边界：
本 Step 不实现 Garden、planting、position、交互、前端页面、图片导出、Memory 或 Agent。
后续 Step 8 可建立 Flower Garden / Planting 领域，把已存在的 FlowerArtifact 放入花园坐标；
花朵身份与花园摆放将继续保持为两个独立职责。
"""


STEP_8 = """
Step 8：Garden Placement Domain
===============================

状态：通过。

开发目标：
在不开发前端、地图或 Pixi Garden Renderer 的前提下，为长期存在的花朵增加独立空间
领域，使一份 FlowerArtifact 可以通过 PlantingRecord 被种植到 Garden 的二维网格位置。

新增与修改：
- flower_engine/schema.py：新增 Garden 与 PlantingRecord。
- flower_engine/garden_store.py：新增 GardenStore JSON 持久化。
- flower_engine/garden_service.py：新增 GardenService 空间业务流程。
- flower_engine/__init__.py：公开 Garden、PlantingRecord、GardenStore 与 GardenService。
- test/flower_engine/3/test_garden_placement.py：Step 8 领域、存储和服务测试。

Garden：
- id：独立 UUID。
- name：去除首尾空白后的非空名称。
- width、height：严格正整数，表示整数网格尺寸。
- created_at：北京时间创建时间。
- Garden 只描述空间容器，不嵌入 FlowerArtifact 或 PlantingRecord。

PlantingRecord：
- id：独立 UUID。
- garden_id：所处 Garden 的引用。
- flower_artifact_id：被展示 FlowerArtifact 的引用。
- x、y：非负严格整数坐标。
- planted_at：北京时间种植时间。
- 位置属于种植记录而非 FlowerArtifact，因此移动、重新布局或多处展示不会改变花朵身份。

空间规则：
- 有效坐标为 0 ≤ x < width、0 ≤ y < height。
- plant_flower() 依次验证 Garden、FlowerArtifact、坐标边界和同花园位置冲突，全部通过后
  才追加 PlantingRecord，不留下部分记录。
- 相同 Garden 的一个坐标只能有一条记录；不同 Garden 可以使用相同坐标。
- 同一 FlowerArtifact 可以在多个不同位置出现，符合未来复制展示需求。
- get_garden_layout() 返回按 planted_at 排列的 PlantingRecord，前端未来无需解释业务规则。

Persistence：
- GardenStore 分别使用 gardens.json 与 planting_records.json。
- 支持 save_garden()、get_garden()、list_gardens()、save_planting()、list_plantings()。
- UTF-8 JSON 使用临时文件替换原子写入；重复 ID、损坏 JSON、非列表根节点和无效模型
  都会明确拒绝。
- PlantingRecord 只保存 FlowerArtifact UUID；花朵对象后续改变或从资产存储移除，不会
  改写已经存在的空间历史记录。

测试结果：
- Step 8 pytest：19 项通过，覆盖模型、创建、序列化、持久化、种花、坐标类型和边界、
  位置冲突、跨花园隔离、同花多位置、缺失引用、历史独立和依赖边界。
- Flower Step 6-8 合计 39 项 pytest 通过；Flower Step 1-4 的 4 份旧测试通过。
- Music Engine 的 11 份离线回归测试通过。
- Blueprint、progression、CreationDraft、BlueprintRevision 与 FinalCreation 的 5 份相关
  回归脚本通过。

未实现范围与下一步边界：
本 Step 不实现 Garden UI、Garden Renderer、草地或地图素材、拖拽、角色移动、地图编辑、
季节系统或生长系统。后续 Step 9 可以读取 Garden、PlantingRecord 与 FlowerArtifact，
在独立 Pixi 预览中第一次组合显示完整花园；领域层不需要为表现层反向修改。
"""


STEP_9 = """
Step 9：Garden Renderer Preview
===============================

状态：通过。

开发目标：
把 Garden、PlantingRecord 与已经存在的 FlowerArtifact 转换为独立、版本化的
GardenRenderSpec，再由 React + Pixi 预览组合成第一个可见的 MuseGarden 花园。领域层
只描述“哪里有什么花”，Renderer 只描述“怎么显示”。

新增与修改：
- flower_engine/schema.py：新增 GardenBackgroundSpec、GardenRenderFlower 和
  GardenRenderSpec。
- flower_engine/garden_adapter.py：新增 garden_to_render_spec() 确定性转换层。
- flower_engine/__init__.py：公开 Garden 渲染模型与 Adapter。
- scripts/export_garden_preview_spec.py：用真实 Python Flower Engine 导出稳定预览 fixture。
- development/fixtures/garden-preview-spec.json：16×10 网格、9 朵真实 RenderSpec 花朵（现存路径）。
- frontend/src/game/flowers/types.ts、validate.ts：镜像并验证 Garden Renderer v1.0 契约。
- frontend/src/game/flowers/gardenRenderer.ts：Pixi 草地、花朵放置、缩放、层级与动画组装。
- frontend/src/game/flowers/GardenCanvas.tsx：管理 Pixi Application 挂载和销毁。
- frontend/src/App.tsx、styles.css：无编辑操作的独立花园预览页。
- test/flower_engine/3/test_garden_render_spec.py：Python Adapter 与 Schema 测试。
- frontend/src/game/flowers/gardenRenderer.test.ts、App.test.tsx：场景与页面测试。

GardenRenderSpec：
- renderer_schema_version 固定为 1.0。
- 保存 garden_id、逻辑 grid 尺寸、24-96 的 cell_size 和最终像素尺寸。
- background 保存 meadow token 与三种严格 #RRGGBB 像素色。
- 每个 GardenRenderFlower 保存 planting_record_id、flower_artifact_id、template_id、
  grid_x/grid_y、pixel_x/pixel_y、scale、z_index 和完整 FlowerRenderSpec。
- 完整嵌入 FlowerRenderSpec 使前端无需读取 Storage，也不需要重新解释花型、色板或动画。

转换规则：
- 默认 cell_size=48；pixel_x=(grid_x+0.5)×cell_size，
  pixel_y=(grid_y+1)×cell_size，使花朵以格子下边中点为落地锚点。
- scale=0.75+FlowerSpec.size×0.5，范围 0.75-1.25。
- z_index=grid_y×garden.width+grid_x；越靠下的花越晚绘制，横向位置用于稳定排序。
- Adapter 拒绝跨 Garden 记录、越界坐标、重复位置、缺失 FlowerArtifact、重复资产 ID
  和非法 cell_size。
- 输入 Garden、PlantingRecord 与 FlowerArtifact 均保持不变；Adapter 不读取 Store、
  不生成新花，也不调用 LLM、网络或 Pixi。

Pixi Preview：
- 使用 16×10、768×480 的草地场景，带稳定方格和少量像素草地细节。
- 九种已有程序化像素花全部复用 Step 5 Renderer；不新增图片素材或另一套花型规则。
- Pixi 容器按 GardenRenderFlower 的像素坐标、scale 与 z_index 组装，并继续驱动每朵花
  原有摆动、glow 与粒子动画。
- 页面展示花园概要、完整 Canvas、九种花图例与 Domain → RenderSpec → Pixi 数据流，
  不提供种植、拖拽或编辑控件。

验证结果：
- Step 9 Python pytest：11 项通过；Flower Step 6-9 合计 50 项 pytest 通过，旧 Flower
  Step 1-4 的 4 份测试通过。
- 前端 Vitest：3 个测试文件、9 项通过；TypeScript 严格检查和 Vite 生产构建通过。
- Music Engine 11 份离线回归，以及 Blueprint/Creation 相关 5 份回归脚本通过。
- 1280×720 桌面浏览器实际验收：9 朵花、位置、大小、动画、草地和图例均可见；Canvas
  内部分辨率 768×480，CSS 显示 1080×675；无横向溢出，控制台 0 warning/error。
- 当前浏览器自动化未提供 390px 视口能力，因此窄屏仅完成响应式代码和构建验证，未记录
  为视觉验收通过。

未实现范围与下一步边界：
本 Step 不实现 Garden 编辑器、放置保存、玩家角色、种植动画、房屋、NPC、天气、季节、
camera、viewport 或大地图。Step 10 可以实现 Planting Interaction：用户选择已有花，在空格
点击放置并通过 GardenService 保存；交互层仍不得改写 FlowerArtifact。
"""


STEP_10 = """
Step 10：Planting Interaction
==============================

状态：通过。

开发目标：
把 Step 9 的只读花园预览变为最小、真实、可持久化的种植闭环。用户选择已有
FlowerArtifact，在 Pixi 草地上选择网格位置；前端仅提交花朵 ID 和坐标，Python
GardenService 继续作为边界与位置冲突的唯一最终裁决者。

新增与修改：
- backend/app/schemas/garden.py：PlantFlowerRequest、AvailableFlower 与
  GardenPreviewResponse API 契约。
- backend/app/services/garden_interaction.py：连接 HTTP 交互、GardenService 与刷新后的
  GardenRenderSpec，不复制领域规则。
- backend/app/api/garden_preview.py：最小本地 GET/POST JSON 预览 API。
- scripts/run_garden_preview_api.py：稳定 seed、启动 API，并把预览记录保存到
  database/preview/。
- scripts/export_garden_preview_spec.py：抽出可复用的 build_preview_domain()。
- frontend/src/game/flowers/plantingClient.ts：加载花园与提交种植的前端端口。
- frontend/src/game/flowers/types.ts：AvailableFlower、GardenPreviewPayload、
  GardenGridCell 与四态 PlantingMode。
- frontend/src/game/flowers/gardenRenderer.ts：合法/非法格子提示和半透明 ghost flower。
- frontend/src/game/flowers/GardenCanvas.tsx：把指针位置转换为逻辑网格坐标。
- frontend/src/App.tsx、styles.css：选花、放置、错误、成功和刷新界面。
- test/flower_engine/3/test_planting_interaction.py 与 frontend/src/App.test.tsx：领域与交互测试。

PlantingMode：
- idle：只读浏览，用户可以开始一次种植。
- select_flower：显示来自后端的已有 FlowerArtifact，不创建临时或新 Artifact。
- placing：鼠标经过时显示当前坐标、网格高亮和半透明花朵；绿色/红色只提供即时提示。
- confirmed：后端保存成功且返回新的 GardenRenderSpec 后才进入完成状态。

前后端职责：
- 前端负责用户选择、指针到 grid x/y 的换算、ghost flower 和反馈文本。
- POST 只发送 flower_artifact_id、x、y；前端不写 JSON、不创建 PlantingRecord。
- 即使前端已判断位置被占用，点击仍提交给服务端；GardenService 再验证 Garden、
  FlowerArtifact、整数边界与位置冲突，失败时不留下部分记录。
- GardenInteractionService 成功后重新读取真实 PlantingRecord，并通过
  garden_to_render_spec() 返回完整刷新快照。
- FlowerArtifact 和 Garden 输入对象始终不被交互层修改。

本地运行：
- 终端一：.venv\\Scripts\\python.exe scripts\\run_garden_preview_api.py
- 终端二：cd development/demo/creation_preview；npm run dev -- --port 5181
- Vite 把 /api 代理到 127.0.0.1:8000；浏览器只需访问 http://127.0.0.1:5181/。
- database/preview/ 保存本地预览 Garden、FlowerArtifact 与 PlantingRecord，重启后仍存在。

验证结果：
- Step 10 Python：9 项通过；Flower Engine pytest 完整回归 59 项通过。
- Flower Step 1-4 的 4 份独立检查脚本通过。
- 前端 Vitest：3 个测试文件、10 项通过；TypeScript 严格检查与 Vite 生产构建通过。
- Music Engine 离线 pytest 完整回归 24 项通过；Blueprint full flow 与 FinalCreation
  confirmation 两份脚本通过。
- 本地真实浏览器验收：选择郁金香，在 (8, 2) 点击种植后，PlantingRecord 成功保存，
  GardenRenderSpec 自动刷新，画面由 11 朵更新为 12 朵；控制台 0 warning/error。

未实现范围与下一步边界：
本 Step 不实现拖拽编辑器、移动或删除、玩家角色、种植动画、生长、浇水、收获、房屋、
NPC、季节、天气、camera、viewport 或大地图。下一阶段应优先把这个已验证的种植闭环接入
最终 Frontend 主应用和真实创作完成流程，让新生成的 FlowerArtifact 成为可选择的当前花；
不在 Flower Engine 内继续扩展游戏模拟规则。
"""


STEP_11 = """
Step 11：Blueprint-driven Flower Binding
========================================

状态：通过。

目标与边界：
MusicBlueprint → Flower Adapter → FlowerSpec → FlowerVariationSpec → FlowerRenderSpec
→ FlowerArtifact 是正式花朵生成链。FinalCreation 中冻结的 MusicBlueprint 是已归档创作
的语义来源；variation_seed 由调用方明确提供。AudioArtifact、WAV 文件和音频分析结果
不进入 Flower Adapter 或花朵构建函数。

新增与修改：
- flower_engine/adapter.py：secondary_emotions 和 scene 加入确定性语义映射。
- flower_engine/binding.py：新增 build_flower_artifact_from_blueprint(blueprint, seed,
  creation_id=None)，返回未持久化的独立 Artifact。
- flower_engine/lifecycle.py：已归档创作统一调用上述构建函数，再保存 Artifact。
- flower_engine/__init__.py：公开 Blueprint 构建入口。
- test/flower_engine/4/test_blueprint_flower_binding.py：字段映射、确定性、持久化和
  音乐版本独立性测试。

映射规则：
- texture 优先决定 species；未知 texture 回退 primary_emotion，再回退列表中首个
  已识别的 secondary_emotion，最后回退 wildflower。
- primary_emotion 优先决定 palette；未知主情绪时尝试 secondary_emotions，最后依据
  valence 五档回退。花型参考库仍会限制每种真实花可用的 palette。
- energy 决定 size、stem_height，并参与 petal_count；instruments 数量作为初始
  Blueprint 语义层数参与 petal_count。
- valence、texture、secondary_emotions 和 scene 决定 glow：已识别的喜悦/希望
  每项 +0.04、悲伤/焦虑每项 -0.04，附属情绪总调整限于 ±0.08；晴朗午后 +0.08、
  深夜 -0.08、安静房间 -0.04；最后截断到 0-1 并保留两位。
- 初始 Blueprint 的 tempo 决定 sway_speed，progression 决定 growth_direction 和
  particle_effect；这些都是生成时冻结的语义输入。后来 AudioArtifact 的 BPM、音频
  文件或当前音频版本变化不会重新计算已有花。
- 本版不增加 bloom_level、animation_style 等同义字段：现有 size/petal_count 表达
  花冠程度，sway_speed/growth_direction/particle_effect 表达动画表现；具体像素参数
  仍由既有 FlowerRenderSpec 提供。

身份与快照：
- 同一 Blueprint 与 seed 生成相同 FlowerSpec 和 FlowerRenderSpec；每次正式创建仍有
  独立 Artifact id、created_at，表示不同生成事件。
- FlowerArtifact 持有 FlowerSpec 与 FlowerRenderSpec 快照，FinalCreation 持有
  MusicBlueprint 快照；更改调用方 Blueprint 或切换 MusicVersionService 的当前音频，
  不会改写已经保存的花。
- FlowerLifecycleService.create_for_creation() 从已保存 FinalCreation.blueprint 读取，
  不从 AudioArtifact 反推花朵，也不因为音乐重生成而隐式重生成花。

测试结果：
- Step 11 新增 6 项 pytest 通过；Flower Engine 全部 65 项 pytest 通过。
- Music Engine 24 项离线 pytest 通过；旧 Flower Blueprint Adapter 检查通过。
- 实测保存 Audio v1 对应的花、生成 BPM 不同的 Audio v2 并切换当前音频后，花的
  持久化 JSON 与视觉快照保持不变；同一冻结 Blueprint 与 seed 可以重建相同视觉。

后续边界：
本 Step 未修改 Garden、Planting、Renderer、Pixi 或 Frontend。Flower Engine 的生成
来源与版本关系至此固定；下一阶段应把 AI → Music → Flower → Garden 的完整用户流程
接入主应用，而非继续扩展 Flower 领域模型。
"""


STEP_12 = """
Step 12：MuseGarden Demo Flow
============================

状态：功能、自动化测试及真实 HTTP 闭环通过；浏览器视觉验收待确认。
范围是本地端到端演示，不是正式账户系统或完整产品前端。

用户流程：
1. 在现有 Pixi 花园点选空格，输入一段记忆文字。
2. 应用层调用 AI Engine 得到 CreationDraft/MusicBlueprint，然后从同一份 Blueprint
   分别生成真实 AudioArtifact 和 FlowerArtifact。
3. GardenService 在先前选择的位置保存 PlantingRecord；页面刷新 GardenRenderSpec，
   展示新花、情绪信息和可播放的 WAV。
4. 输入音乐修改要求后，生成下一份 BlueprintRevision 和 AudioArtifact。既有
   FinalCreation 的 Blueprint 快照、FlowerArtifact 和 PlantingRecord 不变。
5. 重开页面可从持久化 Demo 记录恢复创作，点已创作的花可再次查看并播放其当前音乐。

新增与修改：
- application/creation_service.py：CreationService 编排 AI、Music、Flower 和 Garden，
  DemoCreationRecord/Store 只保存页面恢复与当前音频版本所需的关系。
- flower_engine/garden_service.py：公开 validate_planting_position()，在高成本生成前
  预检空格；最终落地仍由 plant_flower() 再次执行领域校验。
- backend/app/api/garden_preview.py 与 backend/app/schemas/garden.py：本地创建、列表、
  修改音乐、WAV 读取接口，保留原 Step 10 的手动种植功能。
- scripts/run_garden_preview_api.py：组合真实 Ollama AI、ACE-Step Music、Flower 与 Garden。
- frontend/src/game/flowers/creationClient.ts、frontend/src/App.tsx、styles.css：花园空格
  创建入口、过程反馈、音频播放、音乐再生成和已有创作查看。
- test/flower_engine/4/test_demo_flow.py 与 frontend/src/App.test.tsx：应用层及交互回归。

边界与持久化：
- Flower 仅由首次确认的 MusicBlueprint 与 seed 决定；后续音乐修改不重新生成花。
- React/Pixi 只提供位置选择和表现；越界、冲突和 PlantingRecord 保存仍归 GardenService。
- AudioArtifact、FlowerArtifact、FinalCreation 和 Garden 数据沿用既有 Store；
  database/preview/demo_creations.json 记录当前音频版本及跨资产引用。
- 音乐版本修改保留原 FinalCreation 快照；演示记录中的 music_blueprint 只供下一次
  音乐编辑使用，不回写花的语义来源。
- 本地预检无法提供跨 AI/音频/花/种植多 Store 的原子事务。生成中途失败会返回错误，
  不会宣称成功；正式部署需补偿机制、幂等请求和并发位置锁定。

本地运行：
- Ollama 可提供 qwen2.5:3b，ACE-Step REST API 监听 127.0.0.1:8001。
- 终端一：.venv\\Scripts\\python.exe scripts\\run_garden_preview_api.py
- 终端二：cd development/demo/creation_preview；npm run dev -- --port 5181
- 浏览器访问 http://127.0.0.1:5181/；Vite 将 /api 代理到 127.0.0.1:8000。
- 第一次生成音乐可能较慢，且需要本机 AI/ACE-Step 服务及模型可用。

测试与实测：
- 新增 Step 12 Python 5 项通过；Flower Engine 全套 70 项、Music Engine 24 项通过。
- 前端 Vitest 13 项通过，TypeScript 检查与 Vite 生产构建通过。
- 本地真实 HTTP 流程：记忆文字生成 Blueprint、向日葵 FlowerArtifact、WAV
  AudioArtifact 和 (0,0) PlantingRecord；花园 RenderSpec 的花朵数从 12 增至 13。
- 真实修改音乐后得到 v2 AudioArtifact，原 flower_artifact_id 与 planting_record_id
  未改变；新 WAV 接口返回 200、audio/wav 和非空音频数据。
- 本次浏览器 UI 自动化被浏览器安全策略拒绝访问 localhost，因此没有把画面视觉检查
  记为通过；页面交互由 Vitest 覆盖，服务链由真实 HTTP 请求验证。
- Step 12 实机数据修复：Python 的 63 位 variation_seed 超过 JavaScript 安全整数范围时，
  旧前端会报“variation_seed 无效”。HTTP 响应现统一以十进制字符串传输 seed；
  Python 领域模型与磁盘记录仍为整数，前端用 BigInt 校验上界并计算稳定粒子布局。
  已有 13 朵花的实时花园接口全部返回字符串 seed；Flower/Music 合计 95 项 pytest
  与前端 13 项 Vitest 通过。

后续边界：
Step 12 不做账户、正式数据库事务、任务队列、完整 UI 重构、花园玩法扩展或跨设备同步。
正式产品化应先处理异步生成、失败补偿与进度持久化，再统一主应用的创作入口。
"""


POST_STEP_12_GARDEN_POLISH = """
Step 12 后续花园交互修补
========================

1. 铲子与永久删除：点击已种花后出现铲子，必须再点一次“确认永久铲除”。取消不发
   DELETE 请求；确认后 GardenService 删除 PlantingRecord。FlowerArtifact 只在没有其他
   种植记录引用时删除。CreationService 保留文字、MusicMemory、FinalCreation 与
   AudioArtifact，把 Demo 创作记录标记为花已铲除。网页可以播放保留的音乐，不提供恢复花的
   控件。错误花园或不存在的种植记录不允许删除。
2. 坐标显示：内部 Garden 网格与既有 JSON 记录仍为 0 起点，API 不迁移旧数据；网页给人看的
   位置统一转换为 x+1、y+1，左上角显示 (1,1)。点格子时高亮，生成后高亮约 3.5 秒；
   点击别处立即切换高亮。
3. 移除手动种花：网页不再出现花朵选择器、ghost flower 或手动种植按钮；公开 HTTP
   POST /api/gardens/{id}/plantings 不再提供。自动创作仍通过 GardenService.plant_flower()
   保存种植位置。历史 Step 10 的领域服务保留，以免破坏已归档记录和应用层能力。
4. 预览初始种子只在 Garden 首次创建时写入；重启 API 不会补回用户已铲除的示例花。

验证：Flower/Music Python 回归 98 项通过；前端 Vitest 12 项、TypeScript 检查与 Vite
生产构建通过。覆盖取消/确认删除、资产共享引用、记忆和音频保留、坐标显示、高亮切换、
自动生成及手动入口消失。浏览器视觉验收仍待人工确认。
"""
