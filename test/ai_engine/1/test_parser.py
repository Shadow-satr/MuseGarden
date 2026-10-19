from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from ai_engine.llm.parser import parse_json_response



response = """
{
    "primary_emotion":"achievement",

    "secondary_emotions":[
        "fatigue",
        "relief"
    ],

    "scene":"night"
}
"""


result = parse_json_response(response)


print(result)

print(type(result))
