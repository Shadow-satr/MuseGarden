"""
用户情绪理解模块

负责分析用户输入，
提取情绪、场景等信息，
为 Music Blueprint 提供输入。
"""

from ai_engine.llm.client import call_llm

from ai_engine.llm.parser import parse_json_response

from ai_engine.llm.prompts.emotion import EMOTION_PROMPT

def analyze_emotion(text:str):

    prompt = EMOTION_PROMPT.format(
        text=text
    )

    response = call_llm(prompt)

    result = parse_json_response(
        response
    )

    return result
