"""MuseGarden 手动完整演示：从一句输入到最终确认的真实本地创作流程。"""

from pathlib import Path
import sys

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.creation import (
    edit_creation_draft,
    load_drafts,
    load_revisions,
    restore_blueprint_revision,
    start_creation,
)
from music_engine import (
    AudioStore,
    CreationFinalizationService,
    FinalCreationStore,
    MusicGenerationService,
    MusicVersionService,
    MusicWorkspaceService,
)
from music_engine.providers import AceStepClient


DEFAULT_TEXT = "比赛终于结束了，有点累，但很满足。"


def _show_blueprint(label, blueprint) -> None:
    print(f"\n{label}")
    for field in (
        "primary_emotion",
        "secondary_emotions",
        "energy",
        "valence",
        "tempo",
        "key",
        "instruments",
        "texture",
        "progression",
    ):
        print(f"  {field}: {getattr(blueprint, field)}")


def _check_local_services() -> bool:
    """在创建 Draft 前确认真实 Demo 所需的两个本地服务都可访问。"""
    services = (
        ("Ollama", "http://127.0.0.1:11434/api/tags", False),
        # ACE-Step API 没有定义根路径；404 仍表示 Uvicorn 已可访问。
        ("ACE-Step", "http://127.0.0.1:8001/", True),
    )
    for name, url, accepts_root_404 in services:
        try:
            response = requests.get(url, timeout=5)
            if not (accepts_root_404 and response.status_code == 404):
                response.raise_for_status()
        except requests.RequestException as error:
            print(f"\n{name} 当前不可用：{error}")
            print("Demo 尚未创建 Draft，因此没有写入任何创作数据。")
            return False
    return True


def _current_revision(draft_id):
    draft = next(draft for draft in load_drafts() if draft.id == draft_id)
    return next(
        revision
        for revision in reversed(load_revisions(draft_id))
        if revision.blueprint == draft.blueprint
    )


def _show_status(workspace: MusicWorkspaceService, draft_id) -> None:
    """显示当前 AI 设计稿和 Music Engine 的候选音频状态。"""
    revision = _current_revision(draft_id)
    candidates = workspace.list_current_revision_audio(draft_id)
    current = workspace.get_current_audio(draft_id)

    print("\n--- 当前创作状态 ---")
    print(f"Draft: {draft_id}")
    print(f"当前 Blueprint Revision: V{revision.version} ({revision.id})")
    _show_blueprint("当前音乐设计", revision.blueprint)
    print(f"当前 Revision 的音频候选数: {len(candidates)}")
    if current is None:
        print("当前播放音频: 尚未生成")
    else:
        print(f"当前播放音频: {current.id}")
        print(f"  文件: {current.file_path}")


def _show_revision_history(workspace: MusicWorkspaceService, draft_id) -> None:
    print("\n--- Blueprint 历史版本（AI Engine）---")
    for revision in load_revisions(draft_id):
        instruction = revision.edit_instruction or "初始设计"
        candidates = workspace.version_service.list_for_revision(revision.id)
        current = workspace.version_service.get_current_for_revision(revision.id)
        print(f"  V{revision.version}: {instruction}（音频候选 {len(candidates)} 份）")
        if current is not None:
            print(f"     当前历史音频: {current.id}  {current.file_path}")


def _generate_candidate(workspace: MusicWorkspaceService, draft_id) -> None:
    revision = _current_revision(draft_id)
    print(f"\n正在为 V{revision.version} 生成一个真实音乐候选，请等待……")
    artifact = workspace.generate_current(draft_id)
    print("生成成功。")
    print(f"  AudioArtifact: {artifact.id}")
    print(f"  文件: {artifact.file_path}")
    print("  新候选已自动成为当前播放音频；可在菜单 5 中改选。")


def _select_audio(workspace: MusicWorkspaceService, draft_id) -> None:
    candidates = workspace.list_current_revision_audio(draft_id)
    if not candidates:
        print("\n当前 Revision 还没有音频。请先使用菜单 4 生成。")
        return

    current = workspace.get_current_audio(draft_id)
    print("\n--- 当前 Revision 的音频候选 ---")
    for index, artifact in enumerate(candidates, start=1):
        marker = "（当前）" if current and artifact.id == current.id else ""
        print(f"  {index}. {artifact.id} {marker}")
        print(f"     文件: {artifact.file_path}")

    choice = input("输入要设为当前播放音频的编号；直接回车不修改： ").strip()
    if not choice:
        return
    try:
        selected = candidates[int(choice) - 1]
    except (ValueError, IndexError):
        print("编号无效，未修改当前音频。")
        return
    workspace.select_audio(draft_id, selected.id)
    print(f"已选择候选 {choice} 作为当前播放音频。")


def _edit_blueprint(draft_id) -> None:
    instruction = input("\n告诉 AI 要如何修改音乐设计：\n> ").strip()
    if not instruction:
        print("修改要求不能为空，未创建新版本。")
        return
    updated = edit_creation_draft(draft_id, instruction)
    revision = _current_revision(draft_id)
    print(f"\n已由 AI Engine 创建 V{revision.version} Blueprint。")
    _show_blueprint("修改后的音乐设计", updated.blueprint)
    print("这是新的 Revision，因此尚未有音频；请使用菜单 4 生成。")


def _restore_revision(workspace: MusicWorkspaceService, draft_id) -> None:
    _show_revision_history(workspace, draft_id)
    history = load_revisions(draft_id)
    was_current_version = _current_revision(draft_id).version
    value = input("输入要恢复的版本号；直接回车取消： ").strip()
    if not value:
        return
    try:
        version = int(value)
        source_revision = next(
            (revision for revision in history if revision.version == version),
            None,
        )
        if source_revision is None:
            raise ValueError(f"目标历史版本不存在：V{version}")
        restore_blueprint_revision(draft_id, version)
    except ValueError as error:
        print(f"无法恢复：{error}")
        return
    revision = _current_revision(draft_id)
    if was_current_version == source_revision.version:
        print(f"当前已经是 V{version}，没有创建重复版本。")
        return
    print(f"已直接切回 V{version}，原有音频也会重新显示。")


def _finalize(finalizer: CreationFinalizationService, workspace: MusicWorkspaceService, draft_id) -> bool:
    try:
        bundle = workspace.prepare_confirmation(draft_id)
    except ValueError as error:
        print(f"\n现在不能确认：{error}")
        return False
    print("\n--- 最终确认预览 ---")
    print(f"Blueprint Revision: {bundle.revision_id}")
    print(f"当前音频: {bundle.audio_artifact.id}")
    print(f"音频文件: {bundle.audio_artifact.file_path}")
    if input("输入 YES 确认并保存为最终创作；其他输入返回菜单： ").strip().upper() != "YES":
        print("未确认，所有 Draft、版本和音频继续保留。")
        return False
    final = finalizer.finalize(draft_id)
    print("\n=== 创作已完成 ===")
    print(f"FinalCreation: {final.id}")
    print(f"Memory: {final.memory_id}")
    print(f"最终 Revision: {final.revision_id}")
    print(f"最终 AudioArtifact: {final.audio_artifact_id}")
    return True


def main() -> None:
    print("=== MuseGarden Full Creation Demo ===")
    print("真实链路：用户输入 → AI Engine → Blueprint → ACE-Step → 音频候选 → 最终确认")
    print("需要本地 Ollama（qwen2.5:3b）与 ACE-Step API（127.0.0.1:8001）均已启动。")
    if not _check_local_services():
        return

    text = input(f"\n输入你的创作感受（直接回车使用示例）：\n{DEFAULT_TEXT}\n> ").strip() or DEFAULT_TEXT

    audio_store = AudioStore()
    workspace = MusicWorkspaceService(
        MusicGenerationService(AceStepClient(), audio_store),
        MusicVersionService(audio_store),
    )
    finalizer = CreationFinalizationService(workspace, FinalCreationStore())

    print("\nAI Engine 正在理解输入并生成第一版音乐设计……")
    draft = start_creation(text)
    print("第一版设计已生成。")
    _show_status(workspace, draft.id)
    _generate_candidate(workspace, draft.id)

    while True:
        print(
            "\n--- 你想做什么？ ---\n"
            "1. 查看当前创作状态\n"
            "2. 修改当前音乐设计（AI Engine 创建新 Blueprint Revision）\n"
            "3. 查看 / 恢复历史音乐设计\n"
            "4. 为当前设计生成新的音乐候选（ACE-Step）\n"
            "5. 查看候选并选择当前播放音频\n"
            "6. 确认本次创作并保存为 Memory + FinalCreation\n"
            "0. 暂停并退出（保留当前 Draft、版本和音频）"
        )
        choice = input("> ").strip()
        try:
            if choice == "1":
                _show_status(workspace, draft.id)
            elif choice == "2":
                _edit_blueprint(draft.id)
            elif choice == "3":
                _restore_revision(workspace, draft.id)
            elif choice == "4":
                _generate_candidate(workspace, draft.id)
            elif choice == "5":
                _select_audio(workspace, draft.id)
            elif choice == "6":
                if _finalize(finalizer, workspace, draft.id):
                    return
            elif choice == "0":
                print("已暂停。下次可从本地 Draft 和 Revision 数据继续处理。")
                return
            else:
                print("请输入 0 到 6 的菜单编号。")
        except Exception as error:
            print(f"\n本次操作没有完成：{error}")
            print("已有的 Draft、Revision 和音频文件不会被本 Demo 自动删除。")


if __name__ == "__main__":
    main()
