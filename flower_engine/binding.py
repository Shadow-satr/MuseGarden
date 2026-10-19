"""把一份 MusicBlueprint 直接绑定为独立花朵资产。"""

from uuid import UUID

from ai_engine.blueprint.schema import MusicBlueprint

from flower_engine.adapter import blueprint_to_flower_spec
from flower_engine.artifact import create_flower_artifact
from flower_engine.renderer import build_flower_render_spec
from flower_engine.schema import FlowerArtifact
from flower_engine.variation import build_flower_variation


def build_flower_artifact_from_blueprint(
    blueprint: MusicBlueprint,
    variation_seed: int,
    *,
    creation_id: UUID | None = None,
) -> FlowerArtifact:
    """以 Blueprint 快照和显式 seed 决定视觉，返回尚未保存的 Artifact。"""
    flower_spec = blueprint_to_flower_spec(blueprint)
    variation = build_flower_variation(flower_spec, variation_seed)
    render_spec = build_flower_render_spec(flower_spec, variation)
    return create_flower_artifact(
        flower_spec,
        render_spec,
        creation_id=creation_id,
    )
