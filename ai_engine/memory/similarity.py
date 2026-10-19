"""
用户音乐记忆向量相似度模块

负责比较两个 Embedding 向量的语义相似度。
不负责生成向量，也不负责读取或查询 Memory。
"""

from math import isfinite, sqrt


def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:
    """
    计算两个向量的余弦相似度。

    返回范围在 -1 到 1 之间的 float。
    数值越接近 1，表示两个向量的方向越接近。
    """
    values_a = _validate_vector(vector_a, "vector_a")
    values_b = _validate_vector(vector_b, "vector_b")

    if len(values_a) != len(values_b):
        raise ValueError("两个向量的维度必须一致。")

    length_a = sqrt(sum(value * value for value in values_a))
    length_b = sqrt(sum(value * value for value in values_b))

    if length_a == 0 or length_b == 0:
        raise ValueError("零向量不能参与余弦相似度计算。")

    dot_product = sum(
        value_a * value_b
        for value_a, value_b in zip(values_a, values_b)
    )
    similarity = dot_product / (length_a * length_b)

    # 避免浮点计算误差导致结果略微超出 -1 到 1 的范围
    return float(max(-1.0, min(1.0, similarity)))


def _validate_vector(vector: list[float], name: str) -> list[float]:
    """检查向量是否可以安全参与计算，并统一转换为 float。"""
    if not isinstance(vector, list) or not vector:
        raise ValueError(f"{name} 必须是非空列表。")

    try:
        values = [float(value) for value in vector]
    except (TypeError, ValueError) as error:
        raise ValueError(f"{name} 中包含无法计算的元素。") from error

    if not all(isfinite(value) for value in values):
        raise ValueError(f"{name} 中不能包含无穷大或 NaN。")

    return values
