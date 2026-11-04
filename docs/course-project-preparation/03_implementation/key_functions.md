# 关键函数

|函数|文件|作用|
|---|---|---|
|CreationService.create_memory|application/creation_service.py|编排文字、蓝图、音频、花朵和种植|
|CreationService.regenerate_music|application/creation_service.py|基于修改要求生成新版本|
|plan_planting|application/garden_planting.py|判定地形、占地、冲突及降级|
|analyze_wav|music_companion/audio_analysis.py|声学测量|
|create_handler|backend/app/api/garden_preview.py|构造 HTTP 请求处理器|
|AceStepClient.submit_task|music_engine/providers/ace_step.py|提交生成任务|
