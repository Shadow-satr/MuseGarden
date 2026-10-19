"""Step 13.2：MusicBlueprint 到 MusicGenerationSpec 的确定性转换测试。"""

import inspect
import json
from pathlib import Path
import sys

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.schema import MusicBlueprint
from ai_engine.blueprint.progression import PROGRESSION_CAPTIONS, PROGRESSION_VALUES
from music_engine import MusicGenerationSpec, blueprint_to_generation_spec
import music_engine.adapter as adapter_module


blueprint = MusicBlueprint(
    primary_emotion="满足感",
    secondary_emotions=["疲劳"],
    energy=0.55,
    valence=0.8,
    tempo=92,
    key="C Major",
    instruments=["piano", "strings"],
    texture="warm",
    scene="比赛结束之后",
    progression="calm_to_rising",
)

original_blueprint = blueprint.model_dump(mode="json")
spec = blueprint_to_generation_spec(blueprint)

# 核心字段映射和默认值。
assert isinstance(spec, MusicGenerationSpec)
assert spec.bpm == 92
assert spec.key == "C Major"
assert spec.duration_seconds == 20
assert spec.instrumental is True
assert spec.seed is None

# Caption 应表达音乐语义，而不是程序字段名。
caption = spec.caption.lower()
assert "warm instrumental music" in caption
assert "piano and strings" in caption
assert "satisfaction" in caption
# scene 与 secondary_emotions 是 AI Engine 的经历/细节语义，当前不进入核心 caption。
assert "slight tiredness" not in caption
assert "after finishing a competition" not in caption
assert "moderate energy" in caption
assert "strongly uplifting and joyful emotional tone" in caption
assert "begin calmly and gradually become brighter and more uplifting" in caption
assert "primary_emotion=" not in caption
assert "energy=0.55" not in caption

# 显式参数、确定性及不修改输入。
seeded_spec = blueprint_to_generation_spec(blueprint, duration_seconds=30, seed=20261005)
assert seeded_spec.duration_seconds == 30
assert seeded_spec.seed == 20261005
assert blueprint_to_generation_spec(blueprint) == spec
assert blueprint.model_dump(mode="json") == original_blueprint

# 能量和情绪倾向均采用五档近似语义映射，而不是向模型传递伪精确数值。
very_low_blueprint = blueprint.model_copy(update={"energy": 0.15, "valence": 0.15})
low_blueprint = blueprint.model_copy(update={"energy": 0.35, "valence": 0.35})
moderate_blueprint = blueprint.model_copy(update={"energy": 0.55, "valence": 0.55})
high_blueprint = blueprint.model_copy(update={"energy": 0.72, "valence": 0.72})
very_high_blueprint = blueprint.model_copy(update={"energy": 0.92, "valence": 0.92})
assert "very low energy" in blueprint_to_generation_spec(very_low_blueprint).caption.lower()
assert "deeply melancholic and dark" in blueprint_to_generation_spec(very_low_blueprint).caption.lower()
assert "low energy" in blueprint_to_generation_spec(low_blueprint).caption.lower()
assert "somewhat melancholic" in blueprint_to_generation_spec(low_blueprint).caption.lower()
assert "moderate energy" in blueprint_to_generation_spec(moderate_blueprint).caption.lower()
assert "balanced and neutral" in blueprint_to_generation_spec(moderate_blueprint).caption.lower()
assert "high energy" in blueprint_to_generation_spec(high_blueprint).caption.lower()
assert "warm and positive" in blueprint_to_generation_spec(high_blueprint).caption.lower()
assert "very high energy" in blueprint_to_generation_spec(very_high_blueprint).caption.lower()
assert "strongly uplifting and joyful" in blueprint_to_generation_spec(very_high_blueprint).caption.lower()

# 主情绪等开放语义允许安全保留；progression 则必须是正式标签。
unknown_blueprint = blueprint.model_copy(
    update={
        "primary_emotion": "一种独特的心情",
        "scene": "my custom scene",
    }
)
unknown_caption = blueprint_to_generation_spec(unknown_blueprint).caption
assert "一种独特的心情" in unknown_caption
assert "my custom scene" not in unknown_caption

# 每一个正式 progression 标签都必须可稳定转换为其固定音乐发展描述。
for progression in PROGRESSION_VALUES:
    progression_blueprint = blueprint.model_copy(update={"progression": progression})
    progression_caption = blueprint_to_generation_spec(progression_blueprint).caption
    assert progression_caption.endswith(PROGRESSION_CAPTIONS[progression])

# Schema 边界和 JSON 序列化。
assert json.loads(spec.model_dump_json()) == spec.model_dump(mode="json")
for invalid_kwargs in (
    {"caption": "   ", "bpm": 100, "key": "C Major"},
    {"caption": "valid", "duration_seconds": 0, "bpm": 100, "key": "C Major"},
    {"caption": "valid", "bpm": 0, "key": "C Major"},
    {"caption": "valid", "bpm": 100, "key": "  "},
    {"caption": "valid", "bpm": 100, "key": "C Major", "seed": -1},
):
    try:
        MusicGenerationSpec(**invalid_kwargs)
    except ValidationError:
        pass
    else:
        raise AssertionError(f"应拒绝无效规格：{invalid_kwargs}")

# Adapter 源码只包含本地规则，不引入 LLM 或 ACE-Step REST 调用。
adapter_source = inspect.getsource(adapter_module).lower()
for forbidden_name in ("requests", "ollama", "openai", "http://", "https://", "release_task"):
    assert forbidden_name not in adapter_source

print("MusicBlueprint Adapter: all checks passed.")
