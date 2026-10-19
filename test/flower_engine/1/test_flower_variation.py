"""Flower Engine Step 3：花朵个体变化与稳定身份测试。"""

import inspect
import json
from pathlib import Path
import sys

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flower_engine import (
    FlowerSpec,
    FlowerVariationSpec,
    build_flower_variation,
)
from flower_engine.schema import MAX_VARIATION_SEED
import flower_engine.variation as variation_module


flower_spec = FlowerSpec(
    species="tulip",
    palette="warm_gold",
    size=0.70,
    petal_count=8,
    stem_height=0.70,
    sway_speed=0.43,
    glow=0.56,
    particle_effect="sparkles",
    decoration="light_ribbons",
    growth_direction="rising",
)
original_spec = flower_spec.model_dump(mode="json")

# 相同 species 和 seed 必须得到完全相同、可序列化的变化规格。
variation = build_flower_variation(flower_spec, variation_seed=20261007)
assert isinstance(variation, FlowerVariationSpec)
assert variation.variation_seed == 20261007
assert build_flower_variation(flower_spec, 20261007) == variation
assert json.loads(variation.model_dump_json()) == variation.model_dump(mode="json")
assert variation.model_dump(mode="json") == {
    "variation_seed": 20261007,
    "petal_length_scale": 0.9865,
    "bloom_width_scale": 1.0734,
    "stem_curve": 0.7494,
    "leaf_count": 3,
    "leaf_angle_offset": -6.57,
    "color_value_shift": 0.0561,
    "sway_phase": 0.043121,
    "particle_phase": 0.744388,
}

# 个体结构只由 species 和 seed 决定；其他语义字段变化不会改变个体身份。
semantic_edit = flower_spec.model_copy(
    update={
        "palette": "soft_pink",
        "size": 0.92,
        "glow": 0.80,
        "sway_speed": 0.75,
    }
)
assert build_flower_variation(semantic_edit, 20261007) == variation

# 不同 seed 或不同 species 必须得到不同的个体变化。
different_seed_variation = build_flower_variation(flower_spec, 20261008)
assert different_seed_variation.model_dump(
    exclude={"variation_seed"}
) != variation.model_dump(exclude={"variation_seed"})
rose_spec = flower_spec.model_copy(update={"species": "rose"})
rose_variation = build_flower_variation(rose_spec, 20261007)
assert rose_variation.model_dump(
    exclude={"variation_seed"}
) != variation.model_dump(exclude={"variation_seed"})
assert rose_variation.variation_seed == variation.variation_seed

# 多组 seed 的全部输出必须处于公开契约范围内。
for seed in (0, 1, 42, 20261007, MAX_VARIATION_SEED):
    sample = build_flower_variation(flower_spec, seed)
    assert 0.90 <= sample.petal_length_scale <= 1.10
    assert 0.90 <= sample.bloom_width_scale <= 1.10
    assert -1 <= sample.stem_curve <= 1
    assert 2 <= sample.leaf_count <= 5
    assert -15 <= sample.leaf_angle_offset <= 15
    assert -0.08 <= sample.color_value_shift <= 0.08
    assert 0 <= sample.sway_phase <= 1
    assert 0 <= sample.particle_phase <= 1

# 构建过程不能修改输入 FlowerSpec。
assert flower_spec.model_dump(mode="json") == original_spec

# 函数入口必须拒绝无效对象和无效 seed 类型或范围。
try:
    build_flower_variation({}, 1)  # type: ignore[arg-type]
except TypeError:
    pass
else:
    raise AssertionError("非 FlowerSpec 输入应该被拒绝")

for invalid_seed, expected_error in (
    (True, TypeError),
    (1.0, TypeError),
    (-1, ValueError),
    (MAX_VARIATION_SEED + 1, ValueError),
):
    try:
        build_flower_variation(flower_spec, invalid_seed)  # type: ignore[arg-type]
    except expected_error:
        pass
    else:
        raise AssertionError(f"应拒绝 variation_seed={invalid_seed!r}")

# Schema 自身也必须严格拒绝无效 seed 与越界变化参数。
valid_variation_data = variation.model_dump()
for update in (
    {"variation_seed": True},
    {"variation_seed": 1.0},
    {"petal_length_scale": 1.11},
    {"bloom_width_scale": 0.89},
    {"stem_curve": 1.01},
    {"leaf_count": 6},
    {"leaf_angle_offset": -15.01},
    {"color_value_shift": 0.081},
    {"sway_phase": -0.01},
    {"particle_phase": 1.01},
):
    try:
        FlowerVariationSpec(**{**valid_variation_data, **update})
    except ValidationError:
        pass
    else:
        raise AssertionError(f"应拒绝无效变化参数：{update}")

# Step 3 只使用稳定摘要算法，不依赖外部服务、持久化或系统随机状态。
variation_source = inspect.getsource(variation_module).lower()
for forbidden_name in (
    "import random",
    "random.",
    "requests",
    "ollama",
    "openai",
    "http://",
    "https://",
    "database",
    "pixi",
):
    assert forbidden_name not in variation_source

print("Flower Variation: all checks passed.")
