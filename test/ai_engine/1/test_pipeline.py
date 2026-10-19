from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.semantic_understanding.emotion import analyze_emotion

from ai_engine.blueprint.generator import generate_blueprint
from test.output_format import format_record


text = """
今天终于完成比赛了，
虽然很累，
但是感觉很值得。
"""

# 第一步：理解文本

context = analyze_emotion(text)

print("Emotion:")
print(format_record(context))

# 第二步：生成 Blueprint

blueprint = generate_blueprint(
    context
)

print("\nBlueprint:")
print(format_record(blueprint.model_dump()))
