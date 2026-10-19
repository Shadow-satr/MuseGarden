"""Flower Engine Step 2：现实花卉参考库与约束规则测试。"""

import inspect
import json
from pathlib import Path
import sys
from typing import get_args

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flower_engine import (
    FlowerReference,
    FlowerSpec,
    constrain_flower_spec,
    get_flower_reference,
)
from flower_engine.reference_library import FLOWER_REFERENCES
from flower_engine.schema import FlowerSpecies
import flower_engine.reference_library as reference_library_module


# 首版现实花型和安全回退必须完整登记。
expected_species = set(get_args(FlowerSpecies))
assert expected_species == {
    "rose",
    "peony",
    "sunflower",
    "tulip",
    "hydrangea",
    "lily",
    "daisy",
    "lavender",
    "wildflower",
}
assert set(FLOWER_REFERENCES) == expected_species

# 每份参考数据都必须与查询键一致，并可稳定序列化。
for species in expected_species:
    reference = get_flower_reference(species)
    assert isinstance(reference, FlowerReference)
    assert reference.species == species
    assert reference.petal_count_range[0] <= reference.base_petal_count
    assert reference.base_petal_count <= reference.petal_count_range[1]
    assert reference.stem_height_range[0] <= reference.base_stem_height
    assert reference.base_stem_height <= reference.stem_height_range[1]
    assert json.loads(reference.model_dump_json()) == reference.model_dump(mode="json")

# 查询结果是独立副本，调用方修改不会污染正式花库。
tulip_reference = get_flower_reference("tulip")
tulip_reference.display_name = "临时名称"
assert get_flower_reference("tulip").display_name == "郁金香"

# 不受支持的 species 必须给出明确错误，不能静默伪造参考数据。
try:
    get_flower_reference("orchid")
except ValueError as error:
    assert "orchid" in str(error)
else:
    raise AssertionError("未登记的花型应该被拒绝")

# 现实花型约束应修正花瓣、茎高、色调和装饰，且不修改输入对象。
unconstrained_tulip = FlowerSpec(
    species="tulip",
    palette="fresh_green",
    size=0.8,
    petal_count=16,
    stem_height=0.2,
    sway_speed=0.5,
    glow=0.6,
    particle_effect="sparkles",
    decoration="star_charms",
    growth_direction="opening",
)
original_tulip = unconstrained_tulip.model_dump(mode="json")
constrained_tulip = constrain_flower_spec(unconstrained_tulip)
assert constrained_tulip is not unconstrained_tulip
assert constrained_tulip.petal_count == 8
assert constrained_tulip.stem_height == 0.55
assert constrained_tulip.palette == "warm_gold"
assert constrained_tulip.decoration == "none"
assert constrained_tulip.size == unconstrained_tulip.size
assert constrained_tulip.sway_speed == unconstrained_tulip.sway_speed
assert constrained_tulip.particle_effect == unconstrained_tulip.particle_effect
assert unconstrained_tulip.model_dump(mode="json") == original_tulip

# 已符合现实参考的数据不能被无意义改写。
valid_rose = FlowerSpec(
    species="rose",
    palette="deep_crimson",
    size=0.7,
    petal_count=12,
    stem_height=0.7,
    sway_speed=0.4,
    glow=0.5,
    particle_effect="petals",
    decoration="dew_drops",
    growth_direction="opening",
)
assert constrain_flower_spec(valid_rose) == valid_rose

# FlowerReference 必须拒绝空名称、错误范围、空选项和重复选项。
valid_reference_data = get_flower_reference("daisy").model_dump()
invalid_updates = (
    {"display_name": "   "},
    {"base_petal_count": 7},
    {"petal_count_range": (12, 8)},
    {"base_stem_height": 0.2},
    {"stem_height_range": (0.9, 0.4)},
    {"supported_palettes": ()},
    {"supported_decorations": ()},
    {"supported_palettes": ("soft_pink", "soft_pink")},
    {"supported_decorations": ("none", "none")},
)
for update in invalid_updates:
    try:
        FlowerReference(**{**valid_reference_data, **update})
    except ValidationError:
        pass
    else:
        raise AssertionError(f"应拒绝无效花卉参考：{update}")

try:
    constrain_flower_spec({})  # type: ignore[arg-type]
except TypeError:
    pass
else:
    raise AssertionError("非 FlowerSpec 输入应该被拒绝")

# 花库是本地确定性数据，不引入网络、LLM、数据库或渲染器。
library_source = inspect.getsource(reference_library_module).lower()
for forbidden_name in (
    "requests",
    "ollama",
    "openai",
    "http://",
    "https://",
    "database",
    "pixi",
):
    assert forbidden_name not in library_source

print("Flower Reference Library: all checks passed.")
