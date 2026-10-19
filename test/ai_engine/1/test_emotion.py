from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from ai_engine.semantic_understanding.emotion import analyze_emotion
from test.output_format import format_record



text = "今天宝宝终于和我表白了，虽然很紧张，但是我还是很开心。"


result = analyze_emotion(text)


print(format_record(result))
