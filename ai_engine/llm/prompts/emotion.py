"""
情绪理解 Prompt
"""


EMOTION_PROMPT = """

你是 MuseGarden 的情绪理解模块。

你的任务是分析用户输入的文字，
提取用户当前的情绪状态和场景信息。


请严格输出 JSON 格式：

{{
    "primary_emotion": "主要情绪",
    "secondary_emotions": [
        "次要情绪1",
        "次要情绪2"
    ],
    "scene": "当前场景"
}}


要求：

1. primary_emotion 表示最核心情绪
2. secondary_emotions 可以包含多个伴随情绪
3. scene 表示这个情绪发生的环境


用户输入：

{text}

"""
