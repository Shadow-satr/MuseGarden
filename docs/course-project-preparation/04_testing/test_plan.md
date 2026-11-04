# 测试计划

范围：地形和移动、创建接口、JSON 持久化、音频生成与版本、声学分析、花园渲染、异常和用户体验。

测试层次：Python pytest 与前端 Vitest 使用 fixture 或替身，详细结果见 verbose 日志；生产构建包括 TypeScript 检查。测试用例索引 test_cases.csv，人工用例 manual_cases.csv。标注 BLOCKED 的项目不代表失败或通过。

性能：只对纯函数 plan_planting 做单进程微基准；生成耗时、内存、并发和长时间运行需另行在真实模型和机器上测量，不能由微基准推出。

安全与环境：测试使用临时 fixture，不对真实记忆进行写入；真实模型生成和人为体验需事先确定测试数据和环境。
