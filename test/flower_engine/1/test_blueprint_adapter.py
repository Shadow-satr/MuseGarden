"""Flower Engine Step 1：FlowerSpec 与 Blueprint Adapter 测试。"""

import inspect
import json
from pathlib import Path
import sys

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.blueprint.progression import PROGRESSION_VALUES
from ai_engine.blueprint.schema import MusicBlueprint
from flower_engine import FlowerSpec, blueprint_to_flower_spec
import flower_engine.adapter as adapter_module


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
spec = blueprint_to_flower_spec(blueprint)

# 正常映射、公开类型与 JSON 序列化。
assert isinstance(spec, FlowerSpec)
assert spec.species == "tulip"
assert spec.palette == "warm_gold"
assert spec.size == 0.70
assert spec.petal_count == 8
assert spec.stem_height == 0.70
assert spec.sway_speed == 0.43
assert spec.glow == 0.56
assert spec.particle_effect == "sparkles"
assert spec.decoration == "light_ribbons"
assert spec.growth_direction == "rising"
assert json.loads(spec.model_dump_json()) == spec.model_dump(mode="json")

# 转换必须确定，且不能修改上游 Blueprint。
assert blueprint_to_flower_spec(blueprint) == spec
assert blueprint.model_dump(mode="json") == original_blueprint

# texture 决定现实花型；中英文常见值保持相同语义。
assert blueprint_to_flower_spec(
    blueprint.model_copy(update={"texture": "梦幻"})
).species == "lavender"
assert blueprint_to_flower_spec(
    blueprint.model_copy(update={"texture": "dreamy"})
).species == "lavender"

# 未知 texture 回退到情绪花型；两者均未知时使用 wildflower。
assert blueprint_to_flower_spec(
    blueprint.model_copy(
        update={"texture": "custom_texture", "primary_emotion": "joy"}
    )
).species == "sunflower"
unknown_spec = blueprint_to_flower_spec(
    blueprint.model_copy(
        update={
            "texture": "custom_texture",
            "primary_emotion": "一种独特的心情",
            "valence": 0.5,
            "instruments": [],
        }
    )
)
assert unknown_spec.species == "wildflower"
assert unknown_spec.palette == "balanced_pastel"
assert unknown_spec.decoration == "none"
assert unknown_spec.petal_count == 7

# 连续数值使用有界映射；极端 BPM 不会产生越界动画速度。
low_spec = blueprint_to_flower_spec(
    blueprint.model_copy(update={"energy": 0.0, "valence": 0.0, "tempo": 20})
)
high_spec = blueprint_to_flower_spec(
    blueprint.model_copy(update={"energy": 1.0, "valence": 1.0, "tempo": 220})
)
assert low_spec.size == 0.40
assert low_spec.stem_height == 0.55
assert low_spec.sway_speed == 0.15
assert high_spec.size == 0.95
assert high_spec.stem_height == 0.90
assert high_spec.sway_speed == 0.90
assert 0 <= low_spec.glow <= 1
assert 0 <= high_spec.glow <= 1

# 每一个正式 progression 都必须拥有稳定的视觉发展映射。
progression_outputs = {}
for progression in PROGRESSION_VALUES:
    progression_spec = blueprint_to_flower_spec(
        blueprint.model_copy(update={"progression": progression})
    )
    progression_outputs[progression] = (
        progression_spec.growth_direction,
        progression_spec.particle_effect,
    )
assert set(progression_outputs) == set(PROGRESSION_VALUES)
assert progression_outputs["dark_to_hopeful"] == ("rising", "fireflies")
assert progression_outputs["sparse_to_full"] == ("expanding", "petals")

# FlowerSpec 必须拒绝不受支持的 token 和越界数值。
valid_spec_data = spec.model_dump()
for field_name, invalid_value in (
    ("species", "unknown_flower"),
    ("palette", "unknown_palette"),
    ("size", 1.1),
    ("petal_count", 2),
    ("stem_height", -0.1),
    ("sway_speed", 1.1),
    ("glow", -0.1),
    ("particle_effect", "unknown_effect"),
    ("decoration", "unknown_decoration"),
    ("growth_direction", "unknown_direction"),
):
    try:
        FlowerSpec(**{**valid_spec_data, field_name: invalid_value})
    except ValidationError:
        pass
    else:
        raise AssertionError(f"应拒绝无效字段：{field_name}={invalid_value}")

try:
    blueprint_to_flower_spec({})  # type: ignore[arg-type]
except TypeError:
    pass
else:
    raise AssertionError("非 MusicBlueprint 输入应该被拒绝")

# Step 1 Adapter 只包含本地规则，不依赖生成模型、网络、存储或 Music Engine。
adapter_source = inspect.getsource(adapter_module).lower()
for forbidden_name in (
    "requests",
    "ollama",
    "openai",
    "http://",
    "https://",
    "music_engine",
    "database",
    "pixi",
):
    assert forbidden_name not in adapter_source

print("FlowerSpec Adapter: all checks passed.")
