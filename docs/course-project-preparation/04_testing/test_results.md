# 测试结果

## 最新核心回归（2026-11-04）

`npm --prefix frontend test`：15 个测试文件、75 项测试通过；覆盖花园交互、花朵详情、音乐版本、删除花朵，以及首次使用引导的首次展示、关闭后不重复弹出和手动再次打开。

`.venv\Scripts\python.exe -m pytest test\flower_engine test\application\test_garden_planting.py test\backend\test_creation_api.py`：95 项测试通过；涵盖花朵生成、种植规则和创建/修改/删除接口。`npm --prefix frontend run build` 在项目内 TEMP/TMP 目录下通过；仅保留打包体积提示。

人工界面证据、真实体验反馈与改进记录已归档到 `docs/course/课程材料/04 测试与验证/`；其中 MT-10 记录首次使用引导界面。

---

2026-10-30 重新运行：`.venv\Scripts\python.exe -m pytest -v`：134 passed；`npm --prefix frontend test -- --reporter=verbose`：15 文件、71 测试通过；`npm --prefix frontend run build`：TypeScript 检查与 Vite 构建通过（使用项目内 TEMP/TMP）。退出码与逐项输出见 test_logs。

首轮系统临时目录构建失败，提示 esbuild 删除临时文件 access denied；保留 build.log 和 build-retry.log。重新指定项目内临时目录后通过，保留大包提示。package.json 未定义 lint，因此未执行 lint；不能把类型检查当作 lint。

隔离微基准：10 批次、每批 10000 次空花园 plan_planting，均值约 3.76 微秒/次；最大批均值约 4.64 微秒/次。不是系统性能或模型生成耗时。原始记录见 planting-benchmark.json。

真实端到端、性能负载、主观音乐质量、人工 UI 和真实用户反馈未测；自动化的 mock 不能作为实机模型证据。

日志中的用户目录路径已替换为 `<USER_PROFILE>`，不影响结果和错误信息。微基准可在仓库根目录运行 ` .venv\Scripts\python.exe docs\course-project-preparation\04_testing\benchmark_planting.py`；数值随机器和负载变化。

## 一次真实生成验证

2026-10-30 使用独立数据根目录和虚构文字，通过 CreationService 调用本机 Ollama qwen2.5:3b 和 ACE-Step acestep-v15-turbo，生成一个音频、sunflower 花和种植记录；耗时 29.49 秒，成功。WAV 参数见 test_logs/real-generation-audio.json，原始输出见 real-generation.log，代码见 real_generation_test.py。仅验证一次服务层链路，未验证浏览器操作、音乐质量或统计意义上的性能；没有人工试听。真实测试数据和音频不包含在资料包。
