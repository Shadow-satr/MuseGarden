"""从已完成的花朵规格创建可持久化 FlowerArtifact。"""

from uuid import UUID

from flower_engine.schema import FlowerArtifact, FlowerRenderSpec, FlowerSpec


def create_flower_artifact(
    flower_spec: FlowerSpec,
    render_spec: FlowerRenderSpec,
    creation_id: UUID | None = None,
) -> FlowerArtifact:
    """冻结一朵花的语义与渲染快照，不执行渲染或调用外部服务。"""
    if not isinstance(flower_spec, FlowerSpec):
        raise TypeError("flower_spec 必须是 FlowerSpec 实例")
    if not isinstance(render_spec, FlowerRenderSpec):
        raise TypeError("render_spec 必须是 FlowerRenderSpec 实例")
    if creation_id is not None and not isinstance(creation_id, UUID):
        raise TypeError("creation_id 必须是 UUID 或 None")

    return FlowerArtifact(
        creation_id=creation_id,
        species=flower_spec.species,
        variation_seed=render_spec.variation_seed,
        flower_spec=flower_spec,
        render_spec=render_spec,
        renderer_schema_version=render_spec.renderer_schema_version,
        template_id=render_spec.template_id,
    )
