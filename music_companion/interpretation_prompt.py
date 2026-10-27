"""Music Companion Step 3 的专业音乐介绍 Prompt。"""

from __future__ import annotations

import json


def build_interpretation_prompt(evidence: dict) -> str:
    """将分层证据序列化为严格 JSON 生成任务。"""
    evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)
    return f"""
你是 MuseGarden 的专业音乐赏析编辑。请根据下面的分层证据，为一首短篇器乐作品撰写中文介绍。

写作目标：
1. 专业但可读，使用旋律线条、节奏脉动、动态起伏、音色层次、编配密度、前景与背景、段落推进等准确表达。
2. professional_introduction 写成一段 150–350 字的完整音乐赏析，不能写成数据报告或标签罗列。
3. instrumentation 必须逐件描述乐器或音色构成，并明确证据状态：
   - blueprint_and_audio：Blueprint 中有该乐器，音频模型也有相应音色线索；
   - audio_tendency：只有音频模型给出音色倾向；
   - blueprint_only：只在创作/编配设定中出现；
   - uncertain：证据矛盾或不足。
4. 不得把 Blueprint 中的乐器直接写成成品里确定可闻的乐器；Music-CLAP 结果也只能写成“音色线索、倾向、存在感”。
5. BPM 必须写成“估计约为”；不能根据频谱质心直接断言情绪，也不能根据起音数量直接断言鼓点多少。
6. 只能使用 evidence.allowed_instruments 中的乐器名称。不得虚构和弦、转调、调式变化、演奏技法、制作设备或不存在的乐器。
7. listening_guide 使用开头、中段、结尾，时间必须取自 evidence.acoustic.time_segments 的范围，描述真实可支持的动态、频谱和起音变化。
8. intent_alignment 只评价 evidence.edit_instruction 中明确出现的目标；证据冲突或不足时必须为 uncertain。
9. human_feedback 是最高优先级的听感验证，但只适用于它明确确认的内容。
10. caveats 用普通用户能理解的短句说明真正影响本次结论的限制，不要写免责声明套话。

只返回一个 JSON 对象，不要 Markdown，不要代码围栏，不要补充说明。严格使用以下结构：
{{
  "professional_introduction": "...",
  "mood_and_character": "...",
  "instrumentation": [
    {{
      "instrument": "钢琴",
      "evidence_status": "blueprint_and_audio",
      "description": "..."
    }}
  ],
  "listening_guide": [
    {{
      "section": "开头",
      "start_seconds": 0.0,
      "end_seconds": 6.667,
      "description": "..."
    }}
  ],
  "intent_alignment": [
    {{
      "intent": "...",
      "assessment": "supported | partially_supported | uncertain | not_supported",
      "explanation": "..."
    }}
  ],
  "caveats": ["..."]
}}

分层证据：
{evidence_json}
""".strip() + """

JSON 字段类型再次确认：mood_and_character 必须是一个字符串；
evidence_status 必须是四个固定值之一（不要把四个值用 `|` 写在一起）；
每一条 listening_guide 都必须同时含有 start_seconds 和 end_seconds 两个数字。
"""
