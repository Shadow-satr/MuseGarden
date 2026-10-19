"""
测试 bge-m3 Embedding 功能

需要本地 Ollama 已启动，
并且已经安装 bge-m3:latest 模型。
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.memory import embed_text
from test.output_format import format_record


text = "今天终于完成比赛了，虽然很累，但是感觉很值得。"
embedding = embed_text(text)


# 验证正常文本返回非空的浮点向量
assert isinstance(embedding, list)
assert embedding
assert all(isinstance(value, float) for value in embedding)


# 空文本和只含空格的文本都应被拒绝
for invalid_text in ["", "   "]:
    try:
        embed_text(invalid_text)
        raise AssertionError("空文本应该被拒绝。")
    except ValueError:
        pass


# 只显示前 10 个数值，避免完整向量过长而不方便查看
result = {
    "text": text,
    "embedding_length": len(embedding),
    "first_10_values": embedding[:10],
}

print("Embedding Result:")
print(format_record(result))
