"""
测试 Embedding 向量的余弦相似度计算。

只使用固定向量，
不调用 Ollama，也不读取或写入 Memory。
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.memory import cosine_similarity
from test.output_format import format_record


# 相同向量的相似度应为 1
same_vector_similarity = cosine_similarity(
    [1.0, 2.0, 3.0],
    [1.0, 2.0, 3.0],
)
assert abs(same_vector_similarity - 1.0) < 0.000001


# 不同向量也可以正常计算相似度
different_vector_similarity = cosine_similarity(
    [1.0, 2.0, 3.0],
    [2.0, 1.0, 0.0],
)
assert isinstance(different_vector_similarity, float)


# 不同维度、空向量和零向量都应被拒绝
invalid_vectors = [
    ([1.0, 2.0], [1.0]),
    ([], [1.0]),
    ([0.0, 0.0], [1.0, 2.0]),
]

for vector_a, vector_b in invalid_vectors:
    try:
        cosine_similarity(vector_a, vector_b)
        raise AssertionError("非法向量应该被拒绝。")
    except ValueError:
        pass


result = {
    "same_vector_similarity": same_vector_similarity,
    "different_vector_similarity": different_vector_similarity,
}

print("Similarity Result:")
print(format_record(result))
