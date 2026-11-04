# 特色及证据边界

|内容|用户价值假设|实际机制和证据|限制|
|---|---|---|---|
|文字与花园记忆关联|用空间位置回访记忆|CreationService 将记忆、音频、FlowerArtifact、PlantingRecord 关联|非首创性论断；用户价值待验证|
|音乐和花共用初始蓝图|让视觉和音乐来自同一次创作|application/creation_service.py；flower_engine/lifecycle.py|不证明花朵与音乐感知上一致|
|可修改和选择版本|用户能比较不同音乐版本|regenerate_music、select_music_version 与前端详情|真实模型效果本次未测|
|可解释音频信息|帮助用户了解音频|librosa 特征、受控语义得分、按需解读|CLAP 相似度不是事实或概率；不能单靠数值判断情绪|
|格子与动态占地|在可探索场景安排花朵|plan_planting：1×1、3×3、冲突降级|无并发事务保证|
