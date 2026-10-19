"""Flower Engine Step 4：FlowerRenderSpec 构建与校验测试。"""

import inspect
import json
from pathlib import Path
import re
import sys
from typing import get_args

from pydantic import ValidationError


PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flower_engine import (
    FlowerRenderSpec,
    FlowerSpec,
    build_flower_render_spec,
    build_flower_variation,
    get_flower_reference,
)
from flower_engine.schema import (
    RENDER_LAYER_ORDER,
    FlowerPalette,
    FlowerSpecies,
)
import flower_engine.renderer as renderer_module


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
variation = build_flower_variation(flower_spec, 20261007)
original_spec = flower_spec.model_dump(mode="json")
original_variation = variation.model_dump(mode="json")
render_spec = build_flower_render_spec(flower_spec, variation)

# 标准输入应生成完整、稳定、可序列化的 Renderer 契约。
assert isinstance(render_spec, FlowerRenderSpec)
assert render_spec.renderer_schema_version == "1.0"
assert render_spec.template_id == "tulip_v1"
assert render_spec.species == "tulip"
assert render_spec.variation_seed == 20261007
assert render_spec.geometry.bloom_shape == "cup"
assert render_spec.geometry.leaf_shape == "lance"
assert render_spec.geometry.anchor_x == 0.5
assert render_spec.geometry.anchor_y == 1.0
assert render_spec.layer_order == RENDER_LAYER_ORDER
assert json.loads(render_spec.model_dump_json()) == render_spec.model_dump(mode="json")
assert build_flower_render_spec(flower_spec, variation) == render_spec

# 所有命名 palette 都必须转换为完整的大写十六进制色板。
hex_pattern = re.compile(r"#[0-9A-F]{6}")
for palette in get_args(FlowerPalette):
    palette_spec = flower_spec.model_copy(
        update={"species": "wildflower", "palette": palette}
    )
    palette_variation = build_flower_variation(palette_spec, 42)
    palette_render = build_flower_render_spec(palette_spec, palette_variation)
    for color in palette_render.colors.model_dump().values():
        assert hex_pattern.fullmatch(color)

# 明暗偏移只调整花瓣和效果色，茎叶与花心保持基础色。
positive_variation = variation.model_copy(update={"color_value_shift": 0.08})
negative_variation = variation.model_copy(update={"color_value_shift": -0.08})
# 手动篡改的 variation 会被拒绝，因此直接验证内部纯颜色转换规则。
positive_colors = renderer_module._build_colors("warm_gold", 0.08)
negative_colors = renderer_module._build_colors("warm_gold", -0.08)
assert positive_colors.petal_primary == "#EDB855"
assert negative_colors.petal_primary == "#C5902D"
assert positive_colors.stem == negative_colors.stem == "#47704B"
assert positive_colors.leaf == negative_colors.leaf == "#5F8A58"
assert positive_colors.flower_center == negative_colors.flower_center == "#7A4F27"
assert positive_colors.petal_highlight.startswith("#")
assert negative_colors.particle.startswith("#")

# 连续语义值必须转换为有界的几何与动画参数。
low_spec = flower_spec.model_copy(
    update={
        "size": 0.0,
        "sway_speed": 0.0,
        "glow": 0.0,
        "particle_effect": "none",
    }
)
high_spec = flower_spec.model_copy(
    update={
        "size": 1.0,
        "sway_speed": 1.0,
        "glow": 1.0,
        "particle_effect": "stardust",
    }
)
low_render = build_flower_render_spec(
    low_spec,
    build_flower_variation(low_spec, 11),
)
high_render = build_flower_render_spec(
    high_spec,
    build_flower_variation(high_spec, 12),
)
assert 0.50 <= low_render.geometry.bloom_scale_x <= 1.50
assert 0.50 <= high_render.geometry.bloom_scale_y <= 1.50
assert low_render.animation.sway_amplitude == 0.02
assert low_render.animation.sway_period_ms == 3600
assert high_render.animation.sway_amplitude == 0.08
assert high_render.animation.sway_period_ms == 1200
assert low_render.animation.glow_opacity == 0
assert high_render.animation.glow_opacity == 0.65
assert low_render.animation.particle_rate == 0
assert high_render.animation.particle_rate == 5

# 每个现实花型必须生成对应模板及参考库中的结构 token。
for species in get_args(FlowerSpecies):
    reference = get_flower_reference(species)
    species_spec = flower_spec.model_copy(
        update={
            "species": species,
            "palette": reference.supported_palettes[0],
            "petal_count": reference.base_petal_count,
            "stem_height": reference.base_stem_height,
            "decoration": reference.supported_decorations[0],
        }
    )
    species_variation = build_flower_variation(species_spec, 100)
    species_render = build_flower_render_spec(species_spec, species_variation)
    assert species_render.template_id == f"{species}_v1"
    assert species_render.geometry.bloom_shape == reference.bloom_shape
    assert species_render.geometry.leaf_shape == reference.leaf_shape

# 输入对象不能被修改。
assert flower_spec.model_dump(mode="json") == original_spec
assert variation.model_dump(mode="json") == original_variation

# 篡改后的 variation 或属于其他 species 的 variation 必须被拒绝。
for invalid_variation in (
    positive_variation,
    negative_variation,
    build_flower_variation(
        flower_spec.model_copy(update={"species": "rose"}),
        20261007,
    ),
):
    try:
        build_flower_render_spec(flower_spec, invalid_variation)
    except ValueError:
        pass
    else:
        raise AssertionError("不匹配的 variation 应该被拒绝")

try:
    build_flower_render_spec({}, variation)  # type: ignore[arg-type]
except TypeError:
    pass
else:
    raise AssertionError("非 FlowerSpec 输入应该被拒绝")

try:
    build_flower_render_spec(flower_spec, {})  # type: ignore[arg-type]
except TypeError:
    pass
else:
    raise AssertionError("非 FlowerVariationSpec 输入应该被拒绝")

# Renderer Schema 必须拒绝错误颜色、范围、版本、模板和图层顺序。
valid_render_data = render_spec.model_dump()
invalid_updates = (
    {"renderer_schema_version": "2.0"},
    {"template_id": "rose_v1"},
    {"variation_seed": True},
    {"colors": {**render_spec.colors.model_dump(), "petal_primary": "#gg0000"}},
    {"geometry": {**render_spec.geometry.model_dump(), "bloom_scale_x": 1.51}},
    {"geometry": {**render_spec.geometry.model_dump(), "anchor_x": 0.4}},
    {"animation": {**render_spec.animation.model_dump(), "sway_period_ms": 1199}},
    {"animation": {**render_spec.animation.model_dump(), "particle_rate": 5.1}},
    {"layer_order": tuple(reversed(RENDER_LAYER_ORDER))},
)
for update in invalid_updates:
    try:
        FlowerRenderSpec(**{**valid_render_data, **update})
    except ValidationError:
        pass
    else:
        raise AssertionError(f"应拒绝无效渲染规格：{update}")

# Step 4 不引入具体渲染框架、外部服务、存储或图片处理库。
renderer_source = inspect.getsource(renderer_module).lower()
for forbidden_name in (
    "pixi",
    "requests",
    "ollama",
    "openai",
    "http://",
    "https://",
    "database",
    "pillow",
    "from pil",
):
    assert forbidden_name not in renderer_source

print("Flower RenderSpec: all checks passed.")
