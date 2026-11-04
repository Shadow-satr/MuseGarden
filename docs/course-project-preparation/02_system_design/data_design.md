# 数据设计

本地演示使用 Pydantic 模型、JSON 和 WAV，不是关系型数据库；ER 草图仅表示 UUID 引用，不存在 SQL 外键。`database_dictionary.csv` 从模型定义导出字段类型及必填性，约束、嵌套模型与校验逻辑应结合源代码。

|文件（相对 data_root）|用途|关键依据|
|---|---|---|
|gardens.json|花园容器|flower_engine/garden_store.py|
|planting_records.json|位置、尺寸、占地、花园与花朵引用|flower_engine/garden_store.py|
|flower_artifacts.json|花朵及渲染快照|flower_engine/store.py|
|demo_creations.json|文本、花、种植、当前音频及版本列表|application/creation_service.py|
|final_creations.json|最终创作关联|music_engine/final_creation.py|
|memories.json|文字、情绪与蓝图记忆|ai_engine/memory/store.py|
|audio_artifacts.json、audio/*.wav|音频元数据及 WAV|music_engine/audio_store.py|
|current_audio.json|当前音频选择|music_engine/audio_store.py|
|music_companion_interpretations.json|按需音乐解读缓存|music_companion/result_store.py|

默认 data_root 为 database/preview；可使用 MUSEGARDEN_DATA_ROOT 指向其他位置。若文件不存在，一些 store 读取为空列表；对无效 JSON/模型验证会报错。多个 store 使用临时文件替换，但 memory/store.py 直接写入，且整个创作跨多个文件没有事务或回滚保证。备份数据根目录后才能做恢复测试。
