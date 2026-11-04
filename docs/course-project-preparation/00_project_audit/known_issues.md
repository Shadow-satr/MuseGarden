# 已知限制

- CreationService 使用 use_memory=False，历史语义检索未接入创作主流程。
- 当前本地演示不含账户、多用户或任务队列；多 JSON 文件之间没有跨文件事务。
- 音乐历史保存在 DemoCreationRecord，未统一写入 AI Engine 正式 revision store。
- 真实模型浏览器端到端、音乐质量和系统性能本次未验证。
- 浏览器访问隔离页面遭权限审核拒绝，未采集截图。
- 系统临时目录导致构建 esbuild 删除失败；改用项目内临时目录后成功。
依据 docs/architecture/MuseGarden_progress.py、application/creation_service.py 和本次日志。

补充：2026-10-30 在隔离数据中完成一次 Ollama 与 ACE-Step 的真实服务层创作；浏览器操作、试听和真实用户体验尚未验收。详见 04_testing/test_results.md。
