from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from ai_engine.llm.client import call_llm


result = call_llm(
    "你好，请用中文介绍一下自己。"
)


print(result)
