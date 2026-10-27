"""调用本地 Ollama 的 OpenAI 兼容接口。"""

import requests


OLLAMA_CHAT_URL = "http://127.0.0.1:11434/v1/chat/completions"

def call_llm(message: str) -> str:
    """调用本地 Ollama，返回一次完整响应。

    当前环境下 OpenAI SDK 调用本机 Ollama 的兼容接口会返回 502；使用直接 HTTP 请求可稳定
    获得同一份 OpenAI 格式响应。Blueprint 的结果本就需要完整 JSON 后才能解析，因此这里
    不需要流式返回。
    """
    response = requests.post(
        OLLAMA_CHAT_URL,
        headers={"Authorization": "Bearer ollama"},
        json={
            "model": "qwen2.5:3b",
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "stream": False,
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise RuntimeError("Ollama 返回格式无效") from error
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama 返回了空响应")
    return content.strip()
