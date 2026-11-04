# 技术清单

- Python 标准库 ThreadingHTTPServer 与 Pydantic；不是 FastAPI。
- React、TypeScript、Vite、Pixi.js；版本和脚本以 frontend/package.json、package-lock.json 为准。
- Ollama qwen2.5:3b（ai_engine/llm/client.py）；ACE-Step API 与 acestep-v15-turbo（music_engine/providers/ace_step.py）。
- librosa 声学分析；可选依赖 requirements-music-companion-step2.txt。
- JSON 及 WAV 文件持久化，未发现本地演示主链路使用关系数据库。
- 运行环境 Python 3.12.14（项目虚拟环境），Node v24.13.1，npm 11.8.0。
依据：仓库当前代码和已有开发记录；未经本次运行验证的结论标明为代码审计或历史记录。个人项目，开发者为同一人。
