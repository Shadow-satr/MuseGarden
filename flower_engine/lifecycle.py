"""连接 FinalCreation 与 FlowerArtifact 的花朵生命周期服务。"""

from uuid import UUID

from flower_engine.binding import build_flower_artifact_from_blueprint
from flower_engine.artifact import create_flower_artifact
from flower_engine.renderer import build_flower_render_spec
from flower_engine.schema import FlowerArtifact
from flower_engine.store import FlowerArtifactStore
from flower_engine.variation import build_flower_variation
from music_engine.final_creation import FinalCreationStore


class FlowerLifecycleService:
    """为已归档创作生成、重新生成并查询花朵资产。"""

    def __init__(
        self,
        final_store: FinalCreationStore,
        flower_store: FlowerArtifactStore,
    ) -> None:
        if not isinstance(final_store, FinalCreationStore):
            raise TypeError("final_store 必须是 FinalCreationStore 实例")
        if not isinstance(flower_store, FlowerArtifactStore):
            raise TypeError("flower_store 必须是 FlowerArtifactStore 实例")
        self.final_store = final_store
        self.flower_store = flower_store

    def create_for_creation(
        self,
        creation_id: UUID | str,
        variation_seed: int,
    ) -> FlowerArtifact:
        """根据 FinalCreation 的 Blueprint 生成并保存第一朵或新一朵花。"""
        final_creation = self.final_store.get(creation_id)
        if final_creation is None:
            raise ValueError(f"FinalCreation 不存在：{creation_id}")

        artifact = build_flower_artifact_from_blueprint(
            final_creation.blueprint,
            variation_seed,
            creation_id=final_creation.id,
        )
        self.flower_store.save(artifact)
        return artifact

    def regenerate(
        self,
        artifact_id: UUID | str,
        variation_seed: int | None = None,
    ) -> FlowerArtifact:
        """保留旧资产，以原语义快照和相同或新 seed 生成新历史版本。"""
        source = self.flower_store.get(artifact_id)
        if source is None:
            raise ValueError(f"FlowerArtifact 不存在：{artifact_id}")
        if source.creation_id is None:
            raise ValueError("FlowerArtifact 尚未关联 FinalCreation，不能重新生成")
        if self.final_store.get(source.creation_id) is None:
            raise RuntimeError("FlowerArtifact 引用了不存在的 FinalCreation")

        seed = source.variation_seed if variation_seed is None else variation_seed
        variation = build_flower_variation(source.flower_spec, seed)
        render_spec = build_flower_render_spec(source.flower_spec, variation)
        artifact = create_flower_artifact(
            source.flower_spec,
            render_spec,
            creation_id=source.creation_id,
        )
        self.flower_store.save(artifact)
        return artifact

    def list_for_creation(
        self,
        creation_id: UUID | str,
    ) -> list[FlowerArtifact]:
        """读取某次创作的全部花朵历史，并先验证创作存在。"""
        final_creation = self.final_store.get(creation_id)
        if final_creation is None:
            raise ValueError(f"FinalCreation 不存在：{creation_id}")
        return self.flower_store.list_by_creation(final_creation.id)

    def get_current_for_creation(
        self,
        creation_id: UUID | str,
    ) -> FlowerArtifact | None:
        """返回某次创作最新生成的花；尚未生成时返回 None。"""
        artifacts = self.list_for_creation(creation_id)
        return artifacts[-1] if artifacts else None
