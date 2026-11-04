# 关键算法

## 种植占地
输入中心坐标、已有种植及 prefer_large；先判断中心属于 SOIL 并检查被占用；若大花的 3×3 九格均位于同一田地且无冲突，使用大花，否则降级为 1×1；中心被占用或不属于 SOIL 则报错。输出 PlantingPlan。依据 application/garden_planting.py，边界由 test/application/test_garden_planting.py 验证。

## 创作编排
输入文字、花园 UUID 和坐标；验证后调用蓝图管线、生成音频、保存记忆与 FinalCreation，构造花朵并种植，保存关联记录；外部服务失败可中断且跨文件无事务。依据 application/creation_service.py。

## 音频测量
analyze_wav 读取 WAV，检查路径、段数、采样后计算声学特征；无效或不可解码输入报错。依据 music_companion/audio_analysis.py。
