"""调用本地 Ollama 的 OpenAI 兼容接口。"""

from openai import OpenAI


client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

def call_llm(message: str) -> str:
    """发送一条消息，并合并流式返回的文本片段。"""
    response = client.chat.completions.create(
        model="qwen2.5:3b",
        messages=[{"role": "user", "content": message}],
        temperature=0.7,
        stream=True,
    )
    return "".join(
        chunk.choices[0].delta.content
        for chunk in response
        if chunk.choices and chunk.choices[0].delta.content
    )
