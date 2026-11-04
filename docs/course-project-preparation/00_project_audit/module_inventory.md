# 模块清单

|模块|文件|职责|
|---|---|---|
|前端|frontend/src/App.tsx|界面编排及交互|
|地图|frontend/src/world/TerrainMap.ts|地形格及地图|
|世界|frontend/src/world/GardenWorld.ts|Pixi 生命周期和移动|
|接口|backend/app/api/garden_preview.py|HTTP 路由和错误处理|
|创作|application/creation_service.py|生成、种植、版本编排|
|空间规则|application/garden_planting.py|地形、占地及冲突|
|AI|ai_engine/pipeline.py|情绪与蓝图流程|
|音乐|music_engine/service.py|生成服务|
|生成适配|music_engine/providers/ace_step.py|外部任务及轮询|
|音频理解|music_companion/audio_analysis.py|声学特征|
|花朵|flower_engine/lifecycle.py|花朵生命周期|
|持久化|flower_engine/garden_store.py|花园及种植 JSON|
