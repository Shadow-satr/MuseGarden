"""测试受限 progression 标签在 Schema、Prompt 与 Adapter 中保持一致。"""

from pathlib import Path
import sys

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.progression import (
    PROGRESSION_CAPTIONS,
    PROGRESSION_DESCRIPTIONS,
    PROGRESSION_VALUES,
)
from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.llm.prompts import BLUEPRINT_EDIT_PROMPT, BLUEPRINT_PROMPT
from music_engine import blueprint_to_generation_spec


assert len(PROGRESSION_VALUES) == 18
assert set(PROGRESSION_VALUES) == set(PROGRESSION_DESCRIPTIONS) == set(PROGRESSION_CAPTIONS)

base_blueprint = {
    "primary_emotion": "relief",
    "secondary_emotions": ["fatigue"],
    "energy": 0.55,
    "valence": 0.72,
    "tempo": 92,
    "key": "C Major",
    "instruments": ["piano", "strings"],
    "texture": "warm",
    "scene": "late_night",
}

for progression in PROGRESSION_VALUES:
    blueprint = MusicBlueprint(**base_blueprint, progression=progression)
    assert blueprint.progression == progression
    assert blueprint_to_generation_spec(blueprint).caption.endswith(
        PROGRESSION_CAPTIONS[progression]
    )
    prompt_line = f"- {progression}: {PROGRESSION_DESCRIPTIONS[progression]}"
    assert prompt_line in BLUEPRINT_PROMPT
    assert prompt_line in BLUEPRINT_EDIT_PROMPT

for invalid_progression in ("slowly_opening", "平静到释然"):
    try:
        MusicBlueprint(**base_blueprint, progression=invalid_progression)
    except ValidationError:
        pass
    else:
        raise AssertionError(f"应拒绝非正式 progression 标签：{invalid_progression}")

assert "{progression_guide}" not in BLUEPRINT_PROMPT
assert "{progression_guide}" not in BLUEPRINT_EDIT_PROMPT
assert "必须从以下固定标签中选择一个" in BLUEPRINT_PROMPT
assert "必须从下面固定标签中选择一个" in BLUEPRINT_EDIT_PROMPT

print("Progression catalog: all checks passed.")
