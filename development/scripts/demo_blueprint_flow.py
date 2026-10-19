"""
MuseGarden Blueprint 创作流程终端演示。

默认使用 development/data/demo/ 中的独立演示数据，
不会影响 database/local/ 的正式本地数据。
"""

import argparse
import json
from contextlib import contextmanager
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_engine.creation import (
    compare_blueprint_revisions,
    confirm_draft,
    edit_creation_draft,
    load_revisions,
    restore_blueprint_revision,
    start_creation,
)
from ai_engine.llm.client import client


def main() -> None:
    """运行 Blueprint 创作流程的终端交互演示。"""
    arguments = _parse_arguments()
    use_memory = not arguments.no_memory

    try:
        _check_ollama_available(use_memory=use_memory)
    except RuntimeError as error:
        print(f"无法启动演示：{error}")
        return

    with _use_demo_storage(arguments.use_project_data) as storage_directory:
        print("MuseGarden Blueprint 创作演示")
        print(f"当前数据目录：{storage_directory}")
        print("提示：退出不会自动确认，未完成草稿会保留在当前数据目录。")

        text = input("\n请输入一段经历或心情：").strip()

        if not text:
            print("用户输入不能为空，演示结束。")
            return

        try:
            draft = start_creation(text=text, use_memory=use_memory)
        except Exception as error:
            print(f"创建失败：{error}")
            return

        print("\n已创建初始 Blueprint（Version 1）。")
        _show_draft(draft)

        while True:
            _show_menu()
            choice = input("请选择操作：").strip()

            try:
                if choice == "1":
                    instruction = input("请输入修改要求：").strip()
                    draft = edit_creation_draft(draft.id, instruction)
                    print("\n修改成功，已自动保存新版本。")
                    _show_draft(draft)

                elif choice == "2":
                    _show_revisions(draft.id)

                elif choice == "3":
                    version_a = _read_version("请输入第一个版本号：")
                    version_b = _read_version("请输入第二个版本号：")
                    differences = compare_blueprint_revisions(
                        draft.id,
                        version_a,
                        version_b,
                    )
                    print("\n版本差异：")
                    print(json.dumps(differences, ensure_ascii=False, indent=2))

                elif choice == "4":
                    target_version = _read_version("请输入要恢复的版本号：")
                    draft = restore_blueprint_revision(draft.id, target_version)
                    print("\n恢复成功，已自动保存新的恢复版本。")
                    _show_draft(draft)

                elif choice == "5":
                    _show_draft(draft)

                elif choice == "6":
                    memory = confirm_draft(draft.id)
                    print("\n确认成功，已保存 MusicMemory：")
                    print(json.dumps(memory.model_dump(mode="json"), ensure_ascii=False, indent=2))
                    return

                elif choice == "0":
                    print("已退出，当前未完成草稿仍保留。")
                    return

                else:
                    print("无效操作，请重新输入。")

            except Exception as error:
                print(f"操作失败：{error}")


def _parse_arguments() -> argparse.Namespace:
    """读取演示脚本选项。"""
    parser = argparse.ArgumentParser(description="MuseGarden Blueprint 创作流程演示")
    parser.add_argument(
        "--use-project-data",
        action="store_true",
        help="使用 database/local/ 正式本地数据，而不是独立演示数据。",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="不使用历史 Memory 检索，适用于未安装 bge-m3 的情况。",
    )
    return parser.parse_args()


def _check_ollama_available(use_memory: bool) -> None:
    """检查本地 Ollama 服务和本次演示需要的模型。"""
    try:
        models = client.models.list()
    except Exception as error:
        raise RuntimeError("无法连接本地 Ollama，请先启动 Ollama 服务。") from error

    model_ids = {model.id for model in models.data}
    required_models = {"qwen2.5:3b"}

    if use_memory:
        required_models.add("bge-m3:latest")

    missing_models = required_models - model_ids

    if missing_models:
        missing_text = "、".join(sorted(missing_models))
        raise RuntimeError(f"本地 Ollama 缺少模型：{missing_text}")


@contextmanager
def _use_demo_storage(use_project_data: bool):
    """临时切换演示数据路径，退出后恢复项目原有配置。"""
    if use_project_data:
        yield PROJECT_ROOT / "database" / "local"
        return

    import ai_engine.creation.revision_store as revision_store
    import ai_engine.creation.store as draft_store
    import ai_engine.memory.store as memory_store

    demo_directory = PROJECT_ROOT / "development" / "data" / "demo"
    original_draft_file = draft_store.DRAFT_FILE
    original_revision_file = revision_store.REVISION_FILE
    original_memory_file = memory_store.MEMORY_FILE

    draft_store.DRAFT_FILE = demo_directory / "drafts.json"
    revision_store.REVISION_FILE = demo_directory / "revisions.json"
    memory_store.MEMORY_FILE = demo_directory / "memories.json"

    try:
        yield demo_directory
    finally:
        draft_store.DRAFT_FILE = original_draft_file
        revision_store.REVISION_FILE = original_revision_file
        memory_store.MEMORY_FILE = original_memory_file


def _show_menu() -> None:
    """显示终端交互菜单。"""
    print("\n操作菜单：")
    print("1 - 使用自然语言修改当前 Blueprint")
    print("2 - 查看全部历史 Revision")
    print("3 - 对比两个历史版本")
    print("4 - 恢复指定历史版本")
    print("5 - 查看当前 Blueprint")
    print("6 - 确认当前创作")
    print("0 - 退出并保留未完成草稿")


def _show_draft(draft) -> None:
    """显示当前 Draft ID 和完整 Blueprint。"""
    print(f"\nDraft ID：{draft.id}")
    print("当前 Blueprint：")
    print(json.dumps(draft.blueprint.model_dump(mode="json"), ensure_ascii=False, indent=2))


def _show_revisions(draft_id) -> None:
    """显示指定草稿的全部历史版本。"""
    revisions = load_revisions(draft_id)

    if not revisions:
        print("当前草稿还没有历史版本。")
        return

    print("\n历史 Revision：")
    for revision in revisions:
        print(f"\nVersion {revision.version}")
        print(f"修改说明：{revision.edit_instruction}")
        print(json.dumps(revision.blueprint.model_dump(mode="json"), ensure_ascii=False, indent=2))


def _read_version(prompt: str) -> int:
    """读取并转换用户输入的版本号。"""
    try:
        return int(input(prompt).strip())
    except ValueError as error:
        raise ValueError("版本号必须是整数。") from error


if __name__ == "__main__":
    main()
