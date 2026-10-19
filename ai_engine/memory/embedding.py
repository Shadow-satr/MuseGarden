"""
用户音乐记忆 Embedding 模块

负责调用本地 Ollama 的 bge-m3 模型，
将一段文本转换成浮点向量。
"""

from openai import OpenAI


EMBEDDING_MODEL = "bge-m3:latest"


# 使用本地 Ollama 的 OpenAI 兼容接口
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama",
)


def embed_text(text: str) -> list[float]:
    """
    将文本转换成 Embedding 向量。

    返回的列表中，每一个元素都是 float。
    """
    if not text or not text.strip():
        raise ValueError("Embedding 文本不能为空。")

    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
    except Exception as error:
        raise RuntimeError(
            "调用本地 Ollama 的 bge-m3 模型生成 Embedding 失败。"
        ) from error

    embedding = response.data[0].embedding

    if not embedding:
        raise RuntimeError("bge-m3 返回的 Embedding 向量为空。")

    return [float(value) for value in embedding]
