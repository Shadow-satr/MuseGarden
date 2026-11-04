# 功能清单

|编号|功能|代码|验证依据|状态|
|---|---|---|---|---|
|FUNC-001|地图、移动和碰撞|frontend/src/world/GardenWorld.ts|前端测试|代码已实现；真实端到端本次未验收|
|FUNC-002|空地输入与创作|application/creation_service.py|test/backend/test_creation_api.py|代码已实现；真实端到端本次未验收|
|FUNC-003|音乐生成|music_engine/service.py|test/music_engine/1/test_music_generation_service.py|代码已实现；真实端到端本次未验收|
|FUNC-004|花朵生成与种植|application/garden_planting.py|test/application/test_garden_planting.py|代码已实现；真实端到端本次未验收|
|FUNC-005|音乐修改和版本选择|application/creation_service.py|test/music_engine/2/test_music_version_service.py|代码已实现；真实端到端本次未验收|
|FUNC-006|声学分析|music_companion/audio_analysis.py|test/music_companion/1/test_audio_analysis.py|代码已实现；真实端到端本次未验收|
|FUNC-007|花朵详情与播放|frontend/src/ui/FlowerDetailOverlay.tsx|frontend/src/ui/FlowerDetailOverlay.test.tsx|代码已实现；真实端到端本次未验收|

历史记忆检索：模块存在但未接入当前创作；真实模型及服务状态无法据本次自动化测试断言。
