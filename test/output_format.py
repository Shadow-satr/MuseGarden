"""Console formatting helpers for test output."""

import json
from collections.abc import Mapping
from typing import Any


def format_record(record: Mapping[str, Any]) -> str:
    """每个字段单独一行，列表保持紧凑显示。"""
    return _format_mapping(record)


def _format_mapping(record: Mapping[str, Any], indent: int = 0) -> str:
    """递归格式化字典，让嵌套对象也按字段换行。"""
    current_indent = " " * indent
    field_indent = " " * (indent + 2)
    lines = [f"{current_indent}{{"]
    items = list(record.items())

    for index, (key, value) in enumerate(items):
        suffix = "," if index < len(items) - 1 else ""

        if isinstance(value, Mapping):
            nested_value = _format_mapping(value, indent + 2)
            lines.append(f'{field_indent}"{key}": {nested_value.lstrip()}{suffix}')
        else:
            rendered_value = json.dumps(value, ensure_ascii=False)
            lines.append(f'{field_indent}"{key}": {rendered_value}{suffix}')

    lines.append(f"{current_indent}}}")
    return "\n".join(lines)
