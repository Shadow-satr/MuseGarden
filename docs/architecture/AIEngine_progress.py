"""
MuseGarden AI Engine 开发进度

当前目录整理后，历史记录中的 scripts/demo_blueprint_flow.py 和 database/demo/
分别位于 development/scripts/demo_blueprint_flow.py 与 development/data/demo/。

本文件只记录 ai_engine/、Blueprint 创作流程、Memory、
CreationDraft、Revision 与相关演示、测试的发展过程。

Music Engine 的开发进度请单独查看：
docs/architecture/MusicEngine_progress.py
跨模块最新状态请查看 docs/architecture/MuseGarden_progress.py。

CURRENT_INTEGRATION_STATUS = "正式 Frontend 已使用 AI Engine 生成与编辑 MusicBlueprint，支持真实音乐修改及 V1 / V2 / V3 版本历史；AI 语义记忆检索仍未接入创作请求。"


当前已完成 Step 1 - Step 8：


Step 1: Music Blueprint 数据模型
--------------------------------
位置：
ai_engine/blueprint/schema.py

作用：
定义系统内部统一的数据结构。

Music Blueprint 作为用户语义理解、音乐生成、
花朵生成以及用户记忆模块之间的数据接口。


Step 2: Semantic Understanding
--------------------------------
位置：
ai_engine/semantic_understanding/emotion.py

作用：
负责理解用户输入文本，
提取用户情绪、场景等语义信息。

当前实现：
通过 LLM 分析用户输入，
生成结构化情绪结果。


Step 3: Blueprint Generator
--------------------------------
位置：
ai_engine/blueprint/generator.py

作用：
负责将语义理解结果转换为 Music Blueprint。

连接：
用户语义理解模块
        ↓
Music Blueprint
        ↓
音乐生成模块 / 花朵生成模块


Step 4: LLM Client
--------------------------------
位置：
ai_engine/llm/client.py

作用：
封装大语言模型调用接口。

当前实现：
通过 OpenAI 兼容接口调用本地 Ollama 模型。

当前模型：
qwen2.5:3b


数据流：

Python
    ↓
LLM Client
    ↓
Ollama
    ↓
qwen2.5:3b


Step 5: Prompt Engineering
--------------------------------
位置：
ai_engine/llm/prompts/

作用：
管理不同 AI 任务对应的 Prompt 模板。

通过角色定义、任务描述以及输出格式约束，
指导大语言模型完成特定任务。


当前已实现：
emotion prompt
blueprint prompt


Step 6: LLM Output Parser
--------------------------------
位置：
ai_engine/llm/parser.py

作用：
负责处理大语言模型返回结果。

功能：
将 LLM 返回的 JSON 字符串转换为 Python 数据结构，
方便后续模块调用。


数据流：

LLM Output(String)
        ↓
JSON Parser
        ↓
Python Dict
        ↓
Pydantic Model


Step 7: LLM-based Music Blueprint Generation
--------------------------------
位置：
ai_engine/blueprint/generator.py

作用：
由大语言模型根据用户情绪和场景，
自动生成完整 Music Blueprint。

当前流程：

User Input

    ↓

Semantic Understanding

    ↓

Emotion Result

    ↓

Blueprint Prompt

    ↓

LLM (Ollama)

    ↓

JSON Parser

    ↓

Music Blueprint


当前测试结果示例：

Emotion:

{
  "primary_emotion": "满足感",
  "secondary_emotions": ["疲劳"],
  "scene": "完成比赛后"
}


Blueprint:

{
  "primary_emotion": "满足感",
  "secondary_emotions": ["疲劳"],
  "energy": 0.8,
  "valence": 0.8,
  "tempo": 108,
  "key": "C Major",
  "instruments": [
      "piano",
      "guitar",
      "strings"
  ],
  "texture": "warm",
  "scene": "完成比赛后",
  "progression": "calm_to_rising"
}


当前完整 AI Pipeline：

User Input

    ↓

Semantic Understanding

    ↓

Prompt Template（输出约束）

    ↓

LLM (Ollama)

    ↓

Parser（容错解析）

    ↓

Pydantic Validation

    ↓

Reliable Music Blueprint

    ↓

Future:
Music Engine
Flower Engine
Memory System


Step 8: LLM 输出稳定性与可靠性保护
--------------------------------
问题：
LLM 能生成内容，不代表输出一定能被系统稳定使用。

真实 AI 工程中，模型可能：

1. 输出解释文字或 Markdown 代码块
2. 输出不完整或格式错误的 JSON
3. 缺少必填字段
4. 返回超出业务范围的数值

因此当前系统不直接相信 LLM 输出，而是采用三层保护：

LLM
    ↓
① Prompt 约束
    ↓
② Parser 容错
    ↓
③ Pydantic 校验
    ↓
可靠数据


第一层：Prompt 约束
-------------------
位置：
ai_engine/llm/prompts/emotion.py
ai_engine/llm/prompts/blueprint.py

当前实现：

1. 要求模型只输出 JSON 对象
2. 禁止输出解释、分析过程和 Markdown 标记
3. 明确列出所有必填字段
4. 给出字段语义、示例值和设计原则
5. 使用 {{ 和 }} 保留 JSON 示例，使用 {text} / {context} 注入实际输入

作用：
尽量在模型生成阶段降低格式错误与额外文本出现的概率。


第二层：Parser 容错
--------------------
位置：
ai_engine/llm/parser.py

当前实现：

1. 优先用 json.loads() 直接解析完整响应
2. 直接解析失败时，用正则提取响应中的 JSON 对象后再次解析
3. 仍无法解析时，抛出明确的 ValueError，而不是把无效文本交给下游

作用：
处理模型偶尔在 JSON 前后添加文字的情况，并隔离不可解析输出。


第三层：Pydantic 校验
----------------------
位置：
ai_engine/blueprint/schema.py
ai_engine/blueprint/generator.py

当前实现：

1. 使用 MusicBlueprint 作为系统唯一的 Blueprint 数据契约
2. 通过 MusicBlueprint(**data) 检查必填字段和数据类型
3. 对 energy 和 valence 强制限制在 0 到 1 的范围内
4. 校验失败时不返回不完整或不合法的 Blueprint

作用：
确保传入 Music Engine、Flower Engine 和未来 Memory System 的是受约束的结构化数据。


当前 Step 8 结论：

系统已经从“LLM 输出字符串”升级为“经过约束、解析和校验的 Music Blueprint”。
当前核心问题不再是“能不能生成”，而是持续提升生成结果的稳定性、可靠性和可控性。

后续可增强项：

1. 为 tempo 增加 BPM 范围校验
2. 为 key、texture、scene、progression 和 instruments 增加允许值约束
3. 增加 Parser 异常样例测试，例如 Markdown 包裹、额外文本和缺失括号
4. 为 Prompt 与 Pydantic 约束增加一致性测试


Step 9: Personal Music Memory
--------------------------------
目标：
让 MuseGarden 开始记住用户过去的创作经历。


Step 9.1: MusicMemory 数据结构
--------------------------------
位置：
ai_engine/memory/schema.py

当前实现：

1. EmotionSnapshot 保存一次情绪理解结果：
   primary_emotion、secondary_emotions、scene。
2. MusicMemory 保存一次完整经历：
   id、text、emotion、blueprint、created_at。
3. id 自动生成 UUID；created_at 自动生成带时区的北京时间。
4. text 拒绝空字符串和只含空格的输入。
5. emotion 会从当前 analyze_emotion() 返回的 dict 自动转换为 EmotionSnapshot。
6. blueprint 直接嵌套已经通过 Pydantic 校验的 MusicBlueprint。

数据流：

User Text
    ↓
EmotionSnapshot
    ↓
MusicBlueprint
    ↓
MusicMemory

当前测试：
test/ai_engine/2/test_memory.py

测试覆盖：

1. 正常创建与 JSON 序列化
2. 自动 UUID 与北京时间创建时间
3. 空白 text 校验失败
4. 缺失情绪字段校验失败
5. 无效 Blueprint 校验失败

当前范围：

只定义“记什么”，尚未保存到数据库或文件。
不包含 user_id、Embedding、向量数据库、RAG、音频、花朵或反馈记录。


Step 9.2: Memory Persistence
--------------------------------
位置：
ai_engine/memory/store.py
database/local/memories.json

当前实现：

1. save_memory() 将 MusicMemory 保存为本地 JSON 数组中的一条记录。
2. load_memories() 将 JSON 数据重新恢复为 list[MusicMemory]。
3. 第一次保存时自动创建 database/local/ 和 memories.json。
4. 保存时使用 UTF-8 和中文可读 JSON，方便直接查看本地记忆。
5. 重复 id、损坏 JSON、根结构不是列表或无效记录都会明确报错。
6. 当前测试使用临时文件，不会写入真实 memories.json。

数据流：

MusicMemory
    ↓
Memory Store
    ↓
database/local/memories.json
    ↓
程序重新启动
    ↓
MusicMemory

当前测试：
test/ai_engine/2/test_memory_store.py

测试覆盖：

1. 空文件读取
2. 自动创建目录与 JSON 文件
3. 保存后读取并恢复完整 Memory
4. 重复 id 拦截
5. 损坏 JSON 拦截
6. 无效记录拦截

当前范围：

使用本地 JSON 文件持久化 Memory。
不接 SQLite、数据库表、Embedding、向量数据库、RAG、LLM 新调用或多用户逻辑。


Step 9.3: Memory Retrieval
--------------------------------
位置：
ai_engine/memory/retriever.py

当前实现：

1. find_by_emotion() 根据 memory.emotion.primary_emotion 查询历史记忆。
2. find_by_scene() 根据 memory.emotion.scene 查询用户经历发生的场景。
3. search_by_text() 根据 memory.text 做关键词包含查询。
4. 三种查询都通过 load_memories() 读取已有 Memory，不修改原始 JSON 数据。
5. 字符串查询忽略大小写；查询不到内容时返回空列表。

数据流：

memories.json
    ↓
load_memories()
    ↓
Memory Retriever
    ↓
符合条件的历史 MusicMemory

当前测试：
test/ai_engine/2/test_memory_retriever.py

测试覆盖：

1. 主要情绪查询成功
2. 用户经历场景查询成功
3. text 关键词查询成功
4. 查询不存在内容时返回空列表
5. 大小写不影响查询结果

当前范围：

使用字段匹配与关键词包含匹配。
不引入 Embedding、bge-m3、相似度计算、FAISS、Qdrant、RAG、LangChain 或新的 LLM 调用。


下一阶段：

Step 9.4.1: Embedding Service
--------------------------------
位置：
ai_engine/memory/embedding.py

当前实现：

1. embed_text() 调用本地 Ollama 的 bge-m3:latest 模型。
2. 将一段非空文本转换成非空 list[float] Embedding 向量。
3. 空字符串或只含空格的输入会明确报错。
4. 本地模型调用失败或返回空向量时会明确报错。
5. 当前只负责“文本如何变成向量”，不负责比较或查找 Memory。

数据流：

用户文本
    ↓
bge-m3:latest
    ↓
Embedding 向量 list[float]

当前测试：
test/ai_engine/2/test_embedding.py

测试覆盖：

1. 普通中文文本可以生成向量
2. 返回值是非空 list
3. 向量元素都是 float
4. 空字符串与纯空格输入会被拒绝

当前范围：

只调用本地 bge-m3:latest 生成 Embedding。
不实现余弦相似度、语义检索、Top-K、FAISS、Qdrant、RAG、LangChain，
也不在 MusicMemory 中保存 Embedding。


下一阶段：

Step 9.4.2: Cosine Similarity
--------------------------------
位置：
ai_engine/memory/similarity.py

当前实现：

1. cosine_similarity() 计算两个 Embedding 向量的余弦相似度。
2. 返回 -1 到 1 之间的 float；越接近 1，表示两个向量方向越接近。
3. 空向量、维度不一致、零向量和无法参与计算的元素都会明确报错。
4. 使用 Python 标准库完成计算，没有新增 numpy 或其他依赖。
5. 当前只比较两个已经存在的向量，不生成 Embedding，也不读取 Memory。

数据流：

Embedding A
    ↓
Cosine Similarity
    ↓
相似度分数 float
    ↑
Embedding B

当前测试：
test/ai_engine/2/test_similarity.py

测试覆盖：

1. 相同向量的相似度接近 1
2. 不同向量可以正常计算
3. 不同维度向量会被拒绝
4. 空向量会被拒绝
5. 零向量会被拒绝

当前范围：

只计算两个向量之间的余弦相似度。
不实现 Memory 语义检索、Top-K、Embedding 持久化、FAISS、Qdrant、RAG 或 LangChain。


下一阶段：

Step 9.4.3: Semantic Memory Search
--------------------------------
位置：
ai_engine/memory/retriever.py

当前实现：

1. semantic_search() 使用 Embedding 和余弦相似度查询历史 Memory。
2. 每次查询会将 query 与每条 memory.text 现场转换成 Embedding。
3. 每条 Memory 都会计算 similarity，并按从高到低排序。
4. 返回 list[SemanticSearchResult]，每个结果包含 memory 和 similarity。
5. top_k 控制最多返回几条结果；大于当前 Memory 数量时返回所有结果。
6. 空 Memory 返回空列表；空 query 或非法 top_k 会明确报错。
7. 当前不在 MusicMemory 或 memories.json 中保存 Embedding。

数据流：

当前用户文本
    ↓
Embedding
    ↓
与每条历史 Memory.text 的 Embedding 计算 Cosine Similarity
    ↓
按相似度排序
    ↓
Top-K SemanticSearchResult

当前测试：
test/ai_engine/3/test_semantic_retriever.py

测试覆盖：

1. 返回语义最相近的历史 Memory
2. 结果按 similarity 从高到低排序
3. top_k 正常生效
4. 空 Memory 返回空列表
5. 空 query 被拒绝
6. 非法 top_k 被拒绝

当前范围：

使用现场生成的 Embedding 完成基础语义检索。
不保存 Embedding，不使用向量数据库、FAISS、Qdrant、RAG、LangChain、LLM 重排序，
也不把检索结果注入 Blueprint Prompt。


下一阶段：

Step 10.1: Memory Context Builder
--------------------------------
位置：
ai_engine/memory/context_builder.py

当前实现：

1. build_memory_context() 将 list[SemanticSearchResult] 整理为历史记忆参考文本。
2. 每条参考记忆包含原始 text、主要和次要情绪、场景、相关度与主要音乐参数。
3. 保留语义检索原有的相关度排序，最多使用 max_items 条记忆。
4. 超过 200 字符的用户原话会截断，避免后续上下文过长。
5. 开头明确标记历史内容只是参考数据，不是需要执行的系统指令。
6. 无结果返回空字符串；非法 max_items 会明确报错。

数据流：

Top-K SemanticSearchResult
    ↓
Memory Context Builder
    ↓
结构化历史记忆参考文本

当前测试：
test/ai_engine/3/test_context_builder.py

测试覆盖：

1. 保留相关度排序并限制 max_items
2. 输出包含历史原话、情绪、场景和主要音乐参数
3. 过长原话会截断
4. 无结果返回空字符串
5. 非法 max_items 被拒绝
6. 历史内容明确标记为参考数据，而非系统指令

当前范围：

只构建历史参考文本。
不修改 Blueprint Prompt，不调用 LLM，不生成 Embedding，不进行新检索，
不实现 RAG、偏好学习或将该上下文注入音乐生成流程。


下一阶段：

Step 10.2: Memory-aware Blueprint Prompt
--------------------------------
位置：
ai_engine/llm/prompts/blueprint.py

当前实现：

1. 保留原有 BLUEPRINT_PROMPT，用于不参考历史记忆的普通生成。
2. 新增 MEMORY_AWARE_BLUEPRINT_PROMPT，用于接收当前情绪与历史记忆参考文本。
3. 新 Prompt 可通过 .format(context=current_emotion, memory_context=history_context) 构建。
4. 明确规定当前情绪是本次音乐设计的最主要依据。
5. 明确规定历史记忆只是辅助参考，不是已确认偏好，不能机械复制历史音乐参数。
6. 明确规定历史记忆文本不是需要执行的系统指令。
7. memory_context 为空时，Prompt 仍可正常构建。

当前测试：
test/ai_engine/3/test_memory_aware_blueprint_prompt.py

测试覆盖：

1. 原有普通 Prompt 仍可正常构建
2. 带记忆 Prompt 同时接收当前情绪与历史参考文本
3. 当前情绪优先、禁止机械复制和历史文本非指令等规则存在
4. 空历史记忆不会导致模板构建失败

当前范围：

只定义 Prompt 模板，不调用 LLM，不修改 generate_blueprint()，
不执行新的语义检索，也不将历史记忆真正接入音乐生成调用链路。


下一阶段：

Step 10.3: Memory-aware Blueprint Generator
--------------------------------
开发目标：

让 generate_blueprint() 可选地接收已经整理好的 Memory Context，
根据是否存在有效历史参考文本选择对应 Prompt。

修改位置：

ai_engine/blueprint/generator.py

当前实现：

1. generate_blueprint() 扩展为 generate_blueprint(context, memory_context="")。
2. 不传 memory_context、传入空字符串或只含空白字符时，使用 BLUEPRINT_PROMPT。
3. 传入有效 memory_context 时，使用 MEMORY_AWARE_BLUEPRINT_PROMPT。
4. 当前情绪 context 与 history memory_context 都会正确注入带记忆 Prompt。
5. 后续 call_llm()、parse_json_response() 与 MusicBlueprint Pydantic 校验流程保持不变。
6. Generator 只接收已经整理好的 memory_context，不负责检索、保存或构建历史记忆。

数据流：

当前 Emotion Context
    ↓
可选 Memory Context
    ↓
Blueprint Generator
    ↓
无 Memory → BLUEPRINT_PROMPT
有有效 Memory → MEMORY_AWARE_BLUEPRINT_PROMPT
    ↓
call_llm()
    ↓
parse_json_response()
    ↓
MusicBlueprint

当前测试：
test/ai_engine/3/test_memory_aware_generator.py

测试覆盖：

1. 不传 memory_context 时使用普通 Prompt
2. 空字符串和纯空白 memory_context 使用普通 Prompt
3. 有效 memory_context 使用带记忆 Prompt
4. 当前 context 与历史 memory_context 正确注入 Prompt
5. 合法 LLM 响应返回 MusicBlueprint
6. 非法 JSON 继续由 Parser 拦截
7. 无效 Blueprint 继续由 Pydantic 校验拦截

当前范围：

只扩展 Generator 接收已整理好的 Memory Context。
不自动调用 semantic_search()、build_memory_context() 或 save_memory()，
不持久化 Embedding，不搭建完整 Pipeline，不实现偏好学习、Music Engine 或 Flower Engine。


下一阶段：

Step 10.4: Memory-assisted Music Pipeline
--------------------------------
开发目标：

将已有的情绪理解、历史记忆检索、Memory Context 构建与带记忆 Blueprint 生成串成统一流程。

新增文件：

ai_engine/pipeline.py

当前实现：

1. run_music_pipeline(text, use_memory=True, top_k=3) 是从用户输入到 MusicBlueprint 的统一接口。
2. 先调用 analyze_emotion(text) 得到当前情绪分析结果。
3. use_memory=True 时，调用 semantic_search(text, top_k=top_k)。
4. 检索到历史记忆时，调用 build_memory_context() 构建辅助参考文本。
5. use_memory=False 或历史 Memory 为空时，使用空 memory_context，Generator 自动走普通 Prompt。
6. 最后调用 generate_blueprint()，保留其原有 Prompt 选择、LLM、Parser 与 Pydantic 校验流程。
7. 空文本和非法 top_k 会明确报错；检索、模型调用或数据损坏等真实异常不会被吞掉。
8. 当前不会自动保存新生成的 Blueprint 或 Memory。

数据流：

User Input
    ↓
Semantic Understanding
    ↓
use_memory=True
    ↓
Semantic Memory Search
    ↓
Memory Context Builder
    ↓
Memory-aware Blueprint Generator
    ↓
MusicBlueprint

当前测试：
test/ai_engine/3/test_memory_pipeline.py

测试覆盖：

1. 正常输入完成完整 Pipeline 并返回合法 MusicBlueprint
2. use_memory=True 时调用 semantic_search() 并传递 top_k
3. 检索到历史记忆时调用 build_memory_context()，并将结果传给 generate_blueprint()
4. use_memory=False 时跳过检索和上下文构建
5. 历史 Memory 为空时使用空 memory_context 继续普通生成
6. 空字符串、纯空白输入和非法 top_k 被拒绝

当前范围：

只调度现有 AI 模块。
不自动 save_memory()，不持久化 Embedding，不使用 FAISS、Qdrant、LangChain 或 LangGraph，
不实现用户偏好学习、音频生成、花朵生成、FastAPI 或前端页面。


下一阶段：

Step 11.1: Memory Commit Service
--------------------------------
开发目标：

提供一个明确的保存入口，只在外部确认作品后，
将用户原始输入、情绪分析结果和最终 MusicBlueprint 正式写入个人 Memory。

新增文件：

ai_engine/memory/manager.py

当前实现：

1. commit_memory(text, emotion, blueprint) 创建完整 MusicMemory。
2. UUID 与 created_at 继续由 MusicMemory 自动生成。
3. emotion 可以传入 EmotionSnapshot 或当前情绪分析返回的 dict。
4. 复用 MusicMemory 的 Pydantic 校验规则拒绝无效 text、emotion 或 blueprint。
5. 校验通过后调用已有 save_memory() 写入本地 memories.json。
6. 保存成功后返回对应的 MusicMemory。
7. 保存失败时不伪装成功，直接向调用方暴露异常。
8. Manager 不负责判断用户是否真的点击了确认按钮；未来业务层应在确认后显式调用它。

数据流：

用户输入
    ↓
生成 MusicBlueprint
    ↓
等待用户明确确认
    ↓
commit_memory()
    ↓
MusicMemory
    ↓
save_memory()
    ↓
database/local/memories.json

当前测试：
test/ai_engine/4/test_memory_manager.py

测试覆盖：

1. 正常输入创建 MusicMemory 并调用 save_memory()
2. 临时 memories.json 可以实际保存并恢复完整 Memory
3. text、emotion 与 blueprint 字段正确保留，id 与 created_at 自动生成
4. 无效 text、emotion 与 blueprint 在写入前被拒绝
5. 保存失败时异常正确暴露

当前范围：

只提供用户确认后的显式记忆写入入口。
不自动修改 run_music_pipeline()，不自动保存所有生成结果，
不实现试听、反馈学习、Blueprint 版本管理、Embedding 持久化、FastAPI、前端确认按钮或 Music Engine。


下一阶段：

Step 11.2: Creation Draft Schema
--------------------------------
开发目标：

区分尚未确认的 CreationDraft 与已经确认的 MusicMemory，
只定义草稿数据结构，不实现草稿保存或确认操作。

新增文件：

ai_engine/creation/__init__.py
ai_engine/creation/schema.py

数据模型：

CreationDraft
    - id: 自动生成的 UUID
    - text: 用户原始输入
    - emotion: EmotionSnapshot
    - blueprint: 当前候选 MusicBlueprint
    - created_at: 自动生成的北京时间

当前实现：

1. CreationDraft 使用 Pydantic BaseModel 定义。
2. 复用现有 EmotionSnapshot 和 MusicBlueprint，不重复定义数据结构。
3. text 不允许为空字符串或只含空白字符。
4. id 自动生成，created_at 自动生成带时区的北京时间。
5. CreationDraft 只代表当前候选创作，不会自动转换为 MusicMemory。
6. 创建草稿时不调用 save_memory()，不会写入 memories.json。

当前测试：
test/ai_engine/4/test_creation_schema.py

测试覆盖：

1. 正常创建 CreationDraft
2. UUID 自动生成且不同草稿 id 不同
3. created_at 自动生成并带有北京时间时区
4. 空白 text 被拒绝
5. emotion 自动转换为 EmotionSnapshot
6. 无效 Blueprint 被 Pydantic 拒绝
7. model_dump() 和 JSON 序列化正常工作
8. 测试不调用 save_memory()，不修改真实 memories.json

当前范围：

只定义 CreationDraft 数据模型。
不修改 run_music_pipeline() 或 commit_memory()，不持久化草稿，
不实现草稿版本管理、用户确认、音频生成、反馈学习、FastAPI 或前端页面。


下一阶段：

Step 11.3: Creation Pipeline Integration
--------------------------------
开发目标：

让现有 AI Pipeline 在生成 MusicBlueprint 后，
自动构建并返回尚未确认的 CreationDraft。

修改位置：

ai_engine/pipeline.py

当前实现：

1. 新增 run_creation_pipeline(text, use_memory=True, top_k=3)，返回 CreationDraft。
2. run_music_pipeline() 保持原有签名和返回 MusicBlueprint 的行为不变。
3. 两个公开接口共享 _run_blueprint_generation()，不会因创建草稿重复调用情绪理解或 LLM。
4. 共享流程复用 analyze_emotion()、可选 semantic_search()、build_memory_context() 和 generate_blueprint()。
5. run_creation_pipeline() 使用同一次流程得到的 text、emotion_result 与 blueprint 构建 CreationDraft。
6. use_memory=False 时跳过历史记忆检索；历史 Memory 为空时继续普通生成。
7. 创建 Draft 不调用 commit_memory() 或 save_memory()，不会写入长期 Memory。
8. 情绪理解、检索或 Blueprint 生成的真实异常会继续向调用方暴露。

数据流：

User Input
    ↓
Semantic Understanding
    ↓
可选 Personal Memory Search
    ↓
可选 Memory Context
    ↓
Blueprint Generator
    ↓
MusicBlueprint
    ↓
CreationDraft

当前测试：
test/ai_engine/4/test_creation_pipeline.py

测试覆盖：

1. 正常输入返回 CreationDraft，包含正确 text、emotion 与 blueprint
2. id 与 created_at 自动生成
3. use_memory=True 时使用历史记忆与 Context Builder
4. use_memory=False 时跳过检索与上下文构建
5. 空历史 Memory 时仍正常创建 Draft
6. 一次执行只调用一次 analyze_emotion()
7. 不调用 commit_memory() 或 save_memory()
8. 原有 run_music_pipeline() 仍返回 MusicBlueprint

当前范围：

只将 CreationDraft 接入已有 AI Pipeline。
不持久化草稿，不修改草稿，不进行 Blueprint 版本管理，不自动提交 Memory，
不实现用户反馈学习、音频生成、FastAPI 或前端页面。


下一阶段：

Step 11.4: Creation Draft Persistence
--------------------------------
开发目标：

为尚未确认的 CreationDraft 建立独立本地存储，
让程序重新启动后仍能恢复草稿，同时不混入长期 MusicMemory。

新增文件：

ai_engine/creation/store.py

当前实现：

1. save_draft(draft) 将 CreationDraft 追加保存到 database/local/drafts.json。
2. load_drafts() 将 JSON 数据恢复为 list[CreationDraft]。
3. 首次保存时自动创建目录与草稿文件，使用 UTF-8 和中文可读 JSON。
4. 保存完整保留 id、text、emotion、blueprint 与 created_at。
5. 重复 id、损坏 JSON、非法根结构和无效草稿记录都会明确报错。
6. 保存先写入临时文件，再替换 drafts.json，避免写入中断破坏原有草稿。
7. 保存和读取都不调用 commit_memory() 或 save_memory()。
8. 当前支持新增保存、完整读取和指定草稿删除，不支持更新或版本管理。

数据流：

CreationDraft
    ↓
save_draft()
    ↓
database/local/drafts.json
    ↓
程序重新启动
    ↓
load_drafts()
    ↓
CreationDraft

当前测试：
test/ai_engine/4/test_creation_store.py

测试覆盖：

1. 文件不存在时返回空列表
2. 单条和多条草稿正常保存并恢复为 CreationDraft
3. id、created_at 与完整草稿字段正确恢复
4. 重复 id 被拒绝
5. 损坏 JSON 和无效草稿记录被拒绝
6. 测试不调用 save_memory()，不污染真实 drafts.json
7. 临时文件替换后不会遗留临时文件

当前范围：

提供草稿新增保存、完整读取与指定草稿删除能力。
不修改 run_creation_pipeline()，不自动保存草稿，不实现草稿修改、版本管理、自动确认、Memory Commit 集成、音频生成、FastAPI 或前端页面。


下一阶段：

Step 11.5: Draft Confirmation Service
--------------------------------
开发目标：

通过草稿 ID 确认指定 CreationDraft，将其提交为 MusicMemory，
并在长期记忆保存成功后移除对应草稿。

修改位置：

ai_engine/creation/store.py
ai_engine/creation/manager.py
ai_engine/memory/manager.py

当前实现：

1. 新增 confirm_draft(draft_id)，接受 UUID 或 UUID 字符串。
2. 确认时从 drafts.json 找到对应 CreationDraft；不存在或 ID 格式无效会明确报错。
3. 使用 Draft 的 text、emotion 与 blueprint 调用 commit_memory()。
4. 使用 Draft UUID 作为 MusicMemory UUID，原有三参数 commit_memory() 调用保持兼容。
5. Memory 保存成功后才调用 delete_draft() 移除草稿；其他 Draft 保持不变。
6. 新增 delete_draft(draft_id)，使用安全临时文件替换方式写入剩余草稿。
7. 如果 Memory 保存失败，Draft 不会删除。
8. 如果 Draft 删除失败，异常会暴露，Draft 保留，已保存 Memory 不会被伪装为完全确认成功。
9. 重试确认时会检查同 UUID Memory；内容一致时只补做 Draft 删除，内容冲突时明确报错，不会重复写入 Memory。

数据流：

drafts.json
    ↓
根据 draft_id 找到 CreationDraft
    ↓
commit_memory(memory_id=draft.id)
    ↓
memories.json
    ↓
Memory 保存成功后
    ↓
delete_draft(draft.id)
    ↓
drafts.json
    ↓
MusicMemory

当前测试：
test/ai_engine/4/test_draft_confirmation.py

测试覆盖：

1. 正常确认生成正确 MusicMemory 并移除对应 Draft
2. text、emotion 与 blueprint 正确保留，其他 Draft 不受影响
3. 不存在 Draft 和重复确认不会产生重复 Memory
4. Memory 保存失败时 Draft 保留
5. Draft 删除失败时异常暴露，Draft 保留且 Memory 已保存
6. 删除失败后重试不会重复生成 Memory，只完成 Draft 删除
7. 测试使用临时 drafts.json 与 memories.json，不污染项目真实数据

当前范围：

只实现显式确认单个草稿的提交与移除。
不自动确认所有生成 Draft，不实现草稿修改、版本管理、音频生成、Music Engine、试听、反馈学习、FastAPI、前端确认按钮或花朵生成。


下一阶段：

Step 12.1: Creation Draft Update
--------------------------------
开发目标：

让用户在确认前使用新的 MusicBlueprint 更新同一份 CreationDraft，
不创建重复草稿，也不影响长期 MusicMemory。

修改位置：

ai_engine/creation/store.py
ai_engine/creation/manager.py

当前实现：

1. 新增 update_draft_blueprint(draft_id, blueprint)，返回更新后的 CreationDraft。
2. 新增 replace_draft(draft)，使用同 ID 草稿安全替换已保存记录。
3. 更新只替换 blueprint；id、text、emotion 和 created_at 保持不变。
4. 新 Blueprint 通过 MusicBlueprint.model_validate() 与重新构造 CreationDraft 完成完整 Pydantic 校验。
5. 草稿不存在、无效 Blueprint 或持久化写入失败时明确报错，原有草稿不被破坏。
6. 如果同 UUID 已存在长期 MusicMemory，拒绝继续修改 Draft，处理确认中删除失败的特殊情况。
7. 更新不会调用 commit_memory()，不会自动确认或保存新的长期 Memory。
8. 已更新 Draft 仍可通过 confirm_draft() 正常确认，并提交更新后的 Blueprint。

数据流：

drafts.json
    ↓
根据 draft_id 找到 CreationDraft
    ↓
验证新的 MusicBlueprint
    ↓
只替换 Draft.blueprint
    ↓
replace_draft()
    ↓
drafts.json
    ↓
CreationDraft

当前测试：
test/ai_engine/5/test_draft_update.py

测试覆盖：

1. 正常更新指定 Draft 的 Blueprint 并能重新读取
2. id、text、emotion、created_at 保持不变，其他 Draft 不受影响
3. 不存在 Draft 与无效 Blueprint 被拒绝
4. 更新失败时原始草稿保持不变
5. 已存在同 ID 长期 Memory 的 Draft 不能继续修改
6. 更新不调用 commit_memory()
7. 已更新 Draft 可正常确认并提交更新后的 Blueprint
8. 测试使用临时 drafts.json 与 memories.json，不污染项目真实数据

当前范围：

只更新草稿当前候选 Blueprint。
不实现 LLM 自然语言修改、Blueprint 多版本历史、音频生成、AI Music Partner、自动确认、用户偏好学习、FastAPI 或前端页面。


下一阶段：

Step 12.2: AI Blueprint Edit Prompt
--------------------------------
开发目标：

设计一个专门用于修改已有 MusicBlueprint 的 Prompt，
让 LLM 能根据用户自然语言要求生成新的完整候选 Blueprint。

新增文件：

ai_engine/llm/prompts/blueprint_edit.py

Prompt 输入：

1. original_text：用户最初记录的经历或感受
2. current_blueprint：当前候选 MusicBlueprint 的完整 JSON
3. edit_instruction：用户本次提出的自然语言修改要求

当前实现：

1. 新增 BLUEPRINT_EDIT_PROMPT，支持三个输入占位符。
2. 明确规定当前 Blueprint 是修改基础，不完全重新设计无关音乐。
3. 优先遵循用户当前修改要求；未涉及字段原则上保持原有值。
4. 允许必要联动调整，但禁止无故大幅改变整体音乐设计。
5. original_text 用于理解创作意图，但不能覆盖当前明确修改要求。
6. 要求输出完整 MusicBlueprint JSON，不允许只返回变化字段、解释、Markdown 或 Schema 外字段。
7. 明确本次仅修改音乐设计参数，不声称生成或修改真实音频。

当前测试：
test/ai_engine/5/test_blueprint_edit_prompt.py

测试覆盖：

1. original_text、current_blueprint 与 edit_instruction 正确注入
2. JSON 示例大括号不会导致 str.format() 异常
3. Prompt 包含保留未涉及字段、避免无关修改和完整 JSON 输出约束
4. 原有 BLUEPRINT_PROMPT 与 MEMORY_AWARE_BLUEPRINT_PROMPT 仍可正常构建

当前范围：

只定义自然语言 Blueprint 修改 Prompt。
不实现 Edit Generator，不调用 LLM，不接入 update_draft_blueprint()，不实现草稿版本管理、音频生成、Music Engine、LangGraph、FastAPI 或前端修改界面。


下一阶段：

Step 12.3: AI Blueprint Editor
--------------------------------
开发目标：

实现独立的 Blueprint Editor，根据用户自然语言修改要求，
在当前 MusicBlueprint 基础上调用 LLM 并返回新的完整候选 Blueprint。

新增文件：

ai_engine/blueprint/editor.py

输入与输出：

edit_blueprint(original_text, current_blueprint, edit_instruction)
    ↓
新的 MusicBlueprint

当前实现：

1. edit_blueprint() 验证 original_text、edit_instruction 与 current_blueprint 的类型；
   合法性由调用边界的 Pydantic MusicBlueprint 保证。
2. 当前 Blueprint 直接序列化为完整 JSON 注入 BLUEPRINT_EDIT_PROMPT，不做重复校验。
3. 复用 call_llm() 调用模型，复用 parse_json_response() 解析输出。
4. LLM 输出通过 MusicBlueprint.model_validate() 完整校验后才返回。
5. Parser 或 Pydantic 校验失败会明确暴露异常，不静默丢弃字段或伪造默认结果。
6. 函数不原地修改 current_blueprint，只返回新的 MusicBlueprint。
7. 函数不调用 save_draft()、update_draft_blueprint() 或 commit_memory()。

数据流：

原始用户输入
    +
当前 MusicBlueprint JSON
    +
自然语言修改要求
    ↓
BLUEPRINT_EDIT_PROMPT
    ↓
call_llm()
    ↓
parse_json_response()
    ↓
MusicBlueprint Pydantic Validation
    ↓
新的 MusicBlueprint

当前测试：
test/ai_engine/5/test_blueprint_editor.py

测试覆盖：

1. 合法 LLM JSON 返回新的 MusicBlueprint
2. 三项输入正确注入 Prompt，当前 Blueprint 使用完整 JSON
3. 空 original_text 或 edit_instruction 被拒绝
4. 非法 JSON 由 Parser 拦截
5. 缺失字段和非法数值由 Pydantic 拦截
6. 原始 current_blueprint 不被修改
7. 不调用草稿保存、草稿更新或 Memory 提交

当前范围：

只实现 AI 修改 Blueprint 的独立能力。
不自动更新或保存 CreationDraft，不实现 Blueprint 版本管理、多轮对话状态、用户偏好学习、音频生成与修改、Music Engine、LangGraph、FastAPI 或前端页面。


下一阶段：

Step 12.4: Draft AI Revision Service
--------------------------------
开发目标：

将 edit_blueprint() 与 update_draft_blueprint() 连接，
让用户通过一句自然语言修改要求更新指定草稿。

修改位置：

ai_engine/creation/manager.py
ai_engine/creation/__init__.py
ai_engine/__init__.py

新增接口：

edit_creation_draft(draft_id, edit_instruction)
    ↓
更新后的 CreationDraft

当前实现：

1. 先验证草稿 ID 和非空的修改要求。
2. 从 drafts.json 找到指定 CreationDraft；草稿不存在时不调用 LLM。
3. 如果同 ID 已经存在长期 MusicMemory，拒绝继续修改，兼容确认时删除草稿失败的情况。
4. 复用 edit_blueprint()，将草稿原始 text、当前 blueprint 和修改要求交给 AI 编辑器。
5. 只有 AI 编辑器成功返回新 Blueprint 后，才复用 update_draft_blueprint() 写回草稿。
6. 更新同一份 Draft，只替换 blueprint；id、text、emotion 和 created_at 保持不变。
7. AI 调用、JSON 解析、Pydantic 校验或持久化失败时异常会明确暴露，原草稿不会被写入新数据。
8. 不调用 commit_memory()，不创建新的 MusicMemory，也不自动确认草稿。

数据流：

Draft ID + 用户修改要求
    ↓
load_drafts()
    ↓
指定 CreationDraft
    ↓
edit_blueprint()
    ↓
新的 MusicBlueprint
    ↓
update_draft_blueprint()
    ↓
更新后的 CreationDraft

当前测试：
test/ai_engine/5/test_creation_edit.py

测试覆盖：

1. 正常 AI 修改会更新指定草稿，并可从 drafts.json 恢复
2. 编辑器收到正确的原始文本、当前 Blueprint 和修改要求
3. 新 Blueprint 正确交给 update_draft_blueprint()
4. id、text、emotion、created_at 保持不变，其他 Draft 不受影响
5. 不存在草稿、空修改要求和已确认草稿被拒绝，且不会调用 AI 编辑器
6. AI 编辑失败或返回非法 Blueprint 时，原草稿保持不变
7. 修改过程不会调用 commit_memory()
8. 修改后的草稿仍能通过 confirm_draft() 正常确认

当前范围：

只更新草稿当前候选 Blueprint。
不实现 Blueprint 版本历史、撤销与重做、多轮对话状态、自动确认、用户偏好学习、音频生成或修改、Music Engine、LangGraph、FastAPI 或前端页面。


下一阶段：

Step 12.5: Blueprint Revision Schema
--------------------------------
开发目标：

定义独立的 BlueprintRevision 数据模型，
为后续版本记录、版本对比和撤销功能提供统一数据契约。

修改位置：

ai_engine/creation/schema.py
ai_engine/creation/__init__.py
ai_engine/__init__.py

数据模型：

BlueprintRevision
├── id：当前版本记录的唯一 UUID
├── draft_id：所属 CreationDraft 的 UUID
├── version：同一草稿内的版本号，从 1 开始
├── edit_instruction：产生当前版本的用户修改要求；初始版本允许为 None
├── blueprint：完整 MusicBlueprint 快照
└── created_at：自动生成的北京时间

当前实现：

1. id 使用 uuid4() 自动生成，version 必须大于或等于 1。
2. draft_id 使用 UUID，明确关联所属草稿。
3. 初始版本允许 edit_instruction=None；提供字符串时拒绝纯空白内容。
4. blueprint 复用现有 MusicBlueprint Schema，仍然执行完整 Pydantic 校验。
5. 创建 Revision 时复制一份完整 Blueprint，保证它是独立历史快照。
6. 不改变 CreationDraft 的字段，不在草稿内直接保存历史列表。
7. 不实现同一 Draft 内版本号重复检查；该规则留给后续持久化服务。
8. 创建 Revision 不会调用任何存储、LLM 或 Memory 提交逻辑。

当前测试：
test/ai_engine/5/test_blueprint_revision_schema.py

测试覆盖：

1. 正常创建初始版本与带修改指令的后续版本
2. UUID、draft_id、版本号和北京时间正确生成
3. 版本快照与外部 Blueprint 不共享引用
4. model_dump() 与 JSON 序列化正常
5. version=0、负数、空白修改要求和无效 Blueprint 被拒绝
6. 测试只创建内存对象，不写入 drafts.json 或 memories.json

当前范围：

只定义版本数据结构。
不实现 Revision 持久化、自动记录版本、edit_creation_draft() 修改、撤销与重做、Blueprint 差异比较、音频版本管理、用户反馈学习、FastAPI 或前端页面。


下一阶段：

Step 12.6: Blueprint Revision Persistence
--------------------------------
开发目标：

为 BlueprintRevision 创建独立本地存储，
使历史音乐设计版本可以在程序重新启动后恢复。

新增文件：

ai_engine/creation/revision_store.py

本地存储：

database/local/revisions.json

核心接口：

save_revision(revision)
load_revisions(draft_id=None)

当前实现：

1. 使用 revisions.json 的 JSON 数组追加保存完整 BlueprintRevision。
2. 第一次保存自动创建目录；使用 UTF-8、ensure_ascii=False 和缩进，中文内容可直接查看。
3. 保存时先写入临时文件，再原子替换正式文件，避免中断破坏已有历史版本。
4. load_revisions() 将 JSON 记录通过 Pydantic 恢复为 BlueprintRevision；文件不存在时返回空列表。
5. JSON 损坏、根结构不是列表或任一记录无效时明确报错，不静默清空数据。
6. Revision.id 全局唯一，不允许重复覆盖。
7. 同一 draft_id 内的 version 不允许重复；不同 Draft 可以都有 Version 1、Version 2。
8. 不传 draft_id 时保持保存顺序返回全部版本；传入 draft_id 时按 version 升序返回该草稿的历史版本。
9. 不强制版本号连续，不检查对应 Draft 是否仍存在。
10. Store 不调用 LLM，不修改 CreationDraft、drafts.json、memories.json 或 MusicMemory。

数据流：

BlueprintRevision
    ↓
save_revision()
    ↓
database/local/revisions.json
    ↓
程序重新启动
    ↓
load_revisions()
    ↓
BlueprintRevision 列表

当前测试：
test/ai_engine/6/test_revision_store.py

测试覆盖：

1. 文件不存在时返回空列表，首次保存自动创建 revisions.json
2. 多个 Draft 的版本可共同保存并完整恢复为 BlueprintRevision
3. 指定 Draft 的版本按 version 升序筛选返回
4. 不同 Draft 可使用同一版本号；同 Draft 重复版本号与重复 Revision ID 被拒绝
5. 非法 draft_id、损坏 JSON 和无效 Revision 记录明确报错
6. 模拟写入失败后，已有历史版本保持不变
7. Revision Store 不创建或修改 drafts.json、memories.json

当前范围：

只实现版本保存与读取。
不自动创建 Version 1，不在 AI 修改时自动记录 Revision，不实现撤销与重做、历史版本恢复、版本差异比较、音频版本管理、用户反馈学习、Music Engine、FastAPI 或前端页面。


下一阶段：

Step 12.7: Initial Blueprint Revision
--------------------------------
开发目标：

为正式开始的每次新创作自动保存 CreationDraft，
并建立对应的初始 BlueprintRevision（Version 1）。

修改位置：

ai_engine/creation/manager.py
ai_engine/creation/__init__.py
ai_engine/__init__.py

新增接口：

start_creation(text, use_memory=True, top_k=3)
    ↓
CreationDraft

当前实现：

1. start_creation() 复用 run_creation_pipeline() 生成 CreationDraft，不重复实现 AI Pipeline。
2. 生成成功后先调用 save_draft() 保存正式草稿。
3. 随后创建 BlueprintRevision，固定 version=1、edit_instruction=None，保存完整初始 Blueprint 快照。
4. 调用 save_revision() 保存 Version 1；Revision 的 id 和 created_at 由 Schema 自动生成。
5. 一次 start_creation() 只调用一次 run_creation_pipeline()，不为了 Revision 再调用 LLM。
6. AI Pipeline 失败时，不创建或保存 Draft、Revision。
7. save_draft() 失败时，不继续调用 save_revision()。
8. save_revision() 失败时，尝试 delete_draft() 回滚本次新保存的草稿；若回滚也失败，会明确抛出部分持久化失败错误。
9. 当前 drafts.json 与 revisions.json 不具备跨文件事务；代码不将它们描述为原子事务。
10. 不调用 commit_memory()，不创建长期 MusicMemory，不修改 run_creation_pipeline() 的独立行为。

数据流：

用户输入
    ↓
start_creation()
    ↓
run_creation_pipeline()
    ↓
CreationDraft
    ↓
save_draft()
    ↓
drafts.json
    ↓
BlueprintRevision Version 1
    ↓
save_revision()
    ↓
revisions.json
    ↓
返回 CreationDraft

当前测试：
test/ai_engine/6/test_creation_start.py

测试覆盖：

1. 正常开始创作会保存 Draft 和 Version 1
2. Version 1 的 draft_id、完整 Blueprint、version 和 edit_instruction 正确
3. 初始 Revision 是独立快照
4. 一次创作只调用一次 AI Pipeline，不调用 commit_memory()
5. 同一 Draft 不会重复保存 Version 1
6. AI Pipeline 失败时不写入文件
7. Draft 保存失败时不保存 Revision
8. Revision 保存失败时回滚刚保存的 Draft
9. 回滚失败时明确报告部分持久化错误，不伪装成成功

当前范围：

只自动记录初始 Version 1。
不在 AI 修改时自动记录 Version 2、Version 3，不实现历史版本恢复、撤销与重做、版本差异比较、音频生成与版本管理、用户反馈学习、FastAPI 或前端页面。


下一阶段：

Step 12.8: Automatic Revision Tracking
--------------------------------
开发目标：

让每次成功的 AI 自然语言草稿修改自动追加保存 BlueprintRevision，
形成 Version 2、Version 3 等完整历史。

修改位置：

ai_engine/creation/manager.py

当前实现：

1. edit_creation_draft() 先读取当前草稿对应的 Revision History。
2. 已有历史时，检查当前 Draft.blueprint 必须属于某个 Revision；不属于历史时明确报错，不调用 AI 编辑器。
3. 没有历史的旧草稿会先建立 Version 1；初始版本保存失败时停止本次编辑。
4. 根据最新版本号计算 next_version，成功编辑后自动新增对应 Version 2、Version 3 等记录。
5. 每条新 Revision 保存完整新 Blueprint、当前 draft_id 和用户原始 edit_instruction。
6. AI 编辑失败时不更新 Draft、不新增编辑版本。
7. Draft 更新失败时不调用 save_revision()。
8. Revision 保存失败时，检查草稿仍为本次新 Blueprint 后，尝试恢复修改前的 Blueprint。
9. 回滚失败时明确抛出数据可能不一致错误；两个 JSON 文件仍不是真正跨文件事务。
10. 不调用 commit_memory()；直接调用 update_draft_blueprint() 仍是独立底层操作，不自动记录 Revision。

数据流：

edit_creation_draft()
    ↓
load_drafts() + load_revisions()
    ↓
当前 Draft 属于历史版本的检查
    ↓
edit_blueprint()
    ↓
update_draft_blueprint()
    ↓
新的 BlueprintRevision
    ↓
save_revision()
    ↓
更新后的 CreationDraft

当前测试：
test/ai_engine/6/test_auto_revision.py

测试覆盖：

1. 连续两次 AI 修改自动保存 Version 2、Version 3，Version 1 保留
2. 新版本的 Blueprint、draft_id、版本号和 edit_instruction 正确
3. 当前 Draft 保持最新 Blueprint，其余核心字段不变
4. AI 编辑失败、Draft 更新失败时不新增错误版本
5. Revision 保存失败时恢复 Draft；回滚失败时明确报错
6. 无历史旧草稿编辑前自动建立 Version 1
7. 已确认草稿和草稿/最新版本不一致的状态被拒绝，不调用 AI 编辑器
8. 修改过程不调用 commit_memory()

当前范围：

只自动记录 AI 修改成功后的 Blueprint 历史。
不实现历史版本恢复、撤销与重做、Blueprint 差异比较、音频版本管理、音乐生成、用户反馈学习、LangGraph、FastAPI 或前端页面。


下一阶段：

Step 12.9: Blueprint Version Restore
--------------------------------
开发目标：

允许用户选择指定历史版本，将其完整 Blueprint 直接切回当前 CreationDraft，
不复制 Revision，保留原有全部历史。

修改位置：

ai_engine/creation/manager.py
ai_engine/creation/__init__.py
ai_engine/__init__.py

新增接口：

restore_blueprint_revision(draft_id, target_version)
    ↓
恢复后的 CreationDraft

版本恢复策略：

V1：初始 Blueprint
V2：第一次修改
V3：第二次修改
    ↓
恢复 V2
    ↓
当前设计直接回到 V2；不创建重复版本

当前实现：

1. 校验 draft_id 和大于等于 1 的整数 target_version，拒绝 bool 与其他非法类型。
2. 草稿不存在、已确认、无历史或目标版本不存在时明确拒绝恢复。
3. 目标版本已经等于当前 Blueprint 时，直接返回当前 Draft，不创建重复 Revision。
4. 正常恢复时复用 update_draft_blueprint() 写入目标版本的完整 Blueprint。
5. 旧 Revision 不会被删除、复制或修改；恢复过程不调用 LLM。
6. 从恢复后的版本继续自然语言修改时，才会按当前最大版本号加一创建新的 Revision。

数据流：

选择目标版本
    ↓
restore_blueprint_revision()
    ↓
load_drafts() + load_revisions()
    ↓
找到目标 Blueprint 快照
    ↓
update_draft_blueprint()
    ↓
更新后的 CreationDraft

当前测试：
test/ai_engine/6/test_revision_restore.py

测试覆盖：

1. 恢复 V2 后只保留 V1、V2、V3，Draft 直接使用 V2 Blueprint
2. 恢复不调用 LLM、不复制 Revision；恢复后仍可继续 AI 编辑创建下一版本
3. 当前版本恢复不改写数据
4. 非法或不存在版本、草稿不存在、已确认草稿和不一致状态被拒绝
5. Draft 更新失败时保持原 Blueprint

当前范围：

只按明确 target_version 恢复音乐设计参数。
不实现自然语言选择版本、LLM 对话管理、版本差异比较、自动确认、用户偏好学习、FastAPI 或前端版本选择界面。


下一阶段：

Step 12.10: Blueprint Revision Comparison
--------------------------------
开发目标：

根据 draft_id 和两个版本号，比较对应 MusicBlueprint 的完整字段，
返回可直接 JSON 序列化的结构化差异结果。

新增文件：

ai_engine/creation/revision_compare.py

核心接口：

compare_blueprint_revisions(draft_id, version_a, version_b)
    ↓
{
    "字段名": {
        "from": Version A 的值,
        "to": Version B 的值,
    }
}

当前实现：

1. 校验草稿 ID 和两个大于等于 1 的整数版本号，拒绝 bool 和其他非法类型。
2. 复用 load_revisions() 获取版本快照，不访问 drafts.json，因此已确认并删除草稿的作品仍可比较。
3. 使用 MusicBlueprint.model_fields 动态遍历全部 Blueprint 字段，不比较 Revision 的 id、版本号、时间、修改指令等元信息。
4. 相同字段不会出现在结果中；相同 Blueprint 或相同版本返回空字典。
5. from/to 严格保持 version_a 到 version_b 的传入方向；反向比较会交换两者。
6. 返回值复制列表等可变字段，不与历史 Revision 对象共享引用。
7. 模块只读：不调用 LLM、Store 写入、Draft 更新或 Memory 提交，不修改任何 JSON 文件。

数据流：

Draft ID + Version A + Version B
    ↓
load_revisions()
    ↓
两个 BlueprintRevision 快照
    ↓
逐字段比较 MusicBlueprint
    ↓
结构化差异结果

当前测试：
test/ai_engine/6/test_revision_compare.py

测试覆盖：

1. 字符串、数值和列表字段只在变化时返回差异
2. from/to 方向正确，反向比较正确交换
3. 相同版本与内容相同的不同版本返回空字典
4. 结果可 JSON 序列化，且不与历史列表共享引用
5. 已确认且没有 Draft 的作品仍可比较 Revision
6. 不存在版本、草稿 ID 和非法版本号被拒绝
7. 比较过程不会写入 revisions.json

当前范围：

只提供客观字段差异比较。
不实现 LLM 版本评价、最佳版本推荐、参数可视化、版本恢复逻辑修改、版本合并、音频差异比较、音频生成、FastAPI 或前端页面。


下一阶段：

Step 12.11: Final Blueprint Confirmation Consistency
--------------------------------
开发目标：

完善 confirm_draft()，确保首次确认写入 MusicMemory 的 Blueprint
与当前 CreationDraft 及某个既有 BlueprintRevision 完整一致。

修改位置：

ai_engine/creation/manager.py

当前实现：

1. confirm_draft() 找到当前 Draft 后，先检查是否已经存在同 UUID 的 MusicMemory。
2. 若已有内容一致的 Memory，说明此前 Memory 已保存但 Draft 删除失败；直接补做删除，不重复提交。
3. 若是首次确认，读取该 Draft 的 Revision History；存在历史时要求 Draft.blueprint 对应其中一个 Revision。
4. 一致性检查失败时明确报错，不写入 MusicMemory、不删除 Draft、不修改 Revision。
5. 没有 Revision 的旧版 Draft 保持原有确认行为，直接使用当前 Draft Blueprint。
6. 检查通过后，commit_memory() 使用当前 Draft 的 UUID、text、emotion 和 blueprint 保存长期 Memory。
7. 只有 Memory 保存成功后才删除 Draft；所有 Revision 始终保留且不被修改。
8. Draft 删除失败后的重试仍受已有幂等保护；同 UUID 但内容冲突的 Memory 明确报错。
9. 确认过程不调用 LLM，不新增 MusicMemory Schema 字段；drafts.json 与 memories.json 仍不是真正跨文件事务。

确认数据流：

confirm_draft()
    ↓
当前 CreationDraft
    ↓
已有 Memory 重试检查
    ↓
load_revisions()
    ↓
Draft.blueprint 对应某个 Revision.blueprint
    ↓
commit_memory(当前 Draft Blueprint)
    ↓
memories.json
    ↓
delete_draft()
    ↓
保留 revisions.json

当前测试：
test/ai_engine/7/test_final_confirmation.py

测试覆盖：

1. 初始 V1、修改后的 V3 与直接切回的 V2 都能确认当前最终 Blueprint
2. 确认后 Revision 全部保留，不创建额外 Revision
3. Draft 不属于任何 Revision 时不修改 Draft、Memory 或 Revision
4. Memory 保存失败时 Draft 保留；无 Revision 旧草稿兼容确认
5. Draft 删除失败后重试不重复创建 Memory
6. 同 UUID 内容冲突的 Memory 被拒绝
7. 确认过程不调用 LLM

当前范围：

只完善 Blueprint 最终确认一致性。
不创建 Final Creation 新模型，不实现音频生成、Music Engine、音频版本管理、自动试听、用户偏好学习、FastAPI、前端页面或新的版本恢复逻辑。


下一阶段：

Step 12.12: Blueprint Workflow Integration
--------------------------------
开发目标：

增加独立终端演示入口，将完整 Blueprint 创作流程串联起来，
并通过端到端集成测试确认各模块可以协同完成一次创作。

新增文件：

scripts/demo_blueprint_flow.py
test/ai_engine/7/test_blueprint_full_flow.py

当前实现：

1. 演示脚本提供 main()，可直接运行，不作为项目正式应用入口。
2. 启动时检查本地 Ollama 服务与 qwen2.5:3b；默认使用历史 Memory 时同时检查 bge-m3:latest。
3. Ollama 或模型不可用时明确说明原因，不会静默改用 Mock 数据。
4. 默认使用 database/demo/ 中独立的 drafts.json、revisions.json 和 memories.json，避免影响 database/local/ 正式数据。
5. 可使用 --use-project-data 明确切换到正式本地数据；可使用 --no-memory 跳过 Memory 检索。
6. 终端菜单支持自然语言修改、查看 Revision、比较版本、恢复版本、查看当前 Blueprint、确认创作和退出保留草稿。
7. 脚本只负责用户交互和调度，复用 start_creation()、edit_creation_draft()、load_revisions()、compare_blueprint_revisions()、restore_blueprint_revision() 和 confirm_draft()。
8. 退出时不会自动确认，未完成草稿保留在当前选择的数据目录。

演示数据流：

用户输入
    ↓
start_creation()
    ↓
V1 CreationDraft
    ↓
修改 / 查看 / 对比 / 恢复
    ↓
当前 Blueprint
    ↓
用户明确确认
    ↓
confirm_draft()
    ↓
MusicMemory

当前测试：
test/ai_engine/7/test_blueprint_full_flow.py

测试覆盖：

1. 创建 V1
2. 连续修改为 V2、V3
3. 直接切回 V2，保留 V1–V3，不生成重复 V4
4. 对比 V2 与 V3
5. 确认当前 V2，验证 MusicMemory 保存 V2 Blueprint
6. 确认后 Draft 被移除，所有 Revision 保留
7. 测试使用 Mock AI 调用与临时 JSON 文件，不污染项目数据

当前范围：

只提供 Blueprint 创作流程的终端演示与端到端验证。
不开发 Music Engine、真实音频生成、FastAPI、前端页面、音频版本管理或用户偏好学习。


AI Engine 当前阶段：

Blueprint 创作流程已完成首个可运行闭环：

用户输入
    ↓
情绪理解与 MusicBlueprint
    ↓
CreationDraft 与 Revision
    ↓
修改、对比、恢复
    ↓
最终确认 MusicMemory

后续如需继续 AI Engine，
在本文件中从新的 AI 能力或优化步骤继续记录。
Music Engine 开发已转移到 MusicEngine_progress.py。


Progression 标签体系收敛
--------------------------------
状态：已完成。

MusicBlueprint.progression 不再接受 LLM 自由生成的字符串，现已收敛为 18 个
受限的音乐发展标签。唯一来源为：
ai_engine/blueprint/progression.py。

该模块同时提供：
1. Pydantic Schema 使用的 Progression Literal 类型；
2. 生成与编辑 Prompt 使用的中文标签说明；
3. Music Engine Adapter 使用的固定英文音乐发展描述。

这使 LLM 输出、Blueprint 校验和下游音乐 Prompt 使用完全相同的标签集合。
现有的 steady、calm、calm_to_rising、restrained_to_open 均被保留，
无需迁移已有 Draft、Revision 或 Memory 数据。

"""


DEMO_INTEGRATION_STATUS_2026_10_13 = """
当前 Flower/Garden 网页 Demo 使用 AI Engine 的情绪理解、MusicBlueprint 生成和
自然语言 Blueprint 编辑；生成成功后保存 MusicMemory。

但 Demo 调用 run_creation_pipeline(text, use_memory=False)，没有调用 semantic_search()
或 build_memory_context()，所以已保存的旧记忆目前不会影响下一次创作。Demo 记忆位于
database/preview/memories.json，而 AI 检索器默认读取 database/local/memories.json。
Demo 也没有走 start_creation/edit_creation_draft/confirm_draft 的正式 Revision
持久化生命周期；音乐修改得到的 BlueprintRevision 只在本次请求中构建。

这不是 AI Engine 缺少上述能力，而是网页 Demo 尚未接线。接入前需先统一记忆数据源，
并确定何时检索旧记忆；完整当前状态与待实施方向见 MuseGarden_progress.py。
"""
