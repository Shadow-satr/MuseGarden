"""把 LLM 返回的 JSON 文本解析为 Python 数据。"""

import json
import re


def parse_json_response(response: str):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        match = re.search(
            r"\{.*\}",
            response,
            re.S,
        )
        if not match:
            raise ValueError("无法解析 LLM 输出为 JSON")
        return json.loads(match.group())
