from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any


@dataclass
class PageSettings:
    width: int
    height: int
    margin_top: int
    margin_right: int
    margin_bottom: int
    margin_left: int
    header: int = 708
    footer: int = 708
    gutter: int = 0


@dataclass
class Style:
    font_east_asia: str
    font_ascii: str
    size_half_points: int
    bold: bool = False
    italic: bool = False
    align: str = "left"
    first_line_indent: int = 0
    left_indent: int = 0
    hanging: int = 0
    spacing_before: int = 0
    spacing_after: int = 0
    line: int = 240
    line_rule: str = "auto"


@dataclass
class ListSettings:
    base_left_indent: int = 720
    hanging: int = 360
    level_step: int = 360


@dataclass
class Preset:
    name: str
    description: str
    page: PageSettings
    styles: dict[str, Style]
    list_settings: ListSettings
    heading_numbering: dict[int, str] = field(default_factory=dict)


def list_presets() -> list[tuple[str, str]]:
    return [
        (name, definition["description"])
        for name, definition in sorted(_builtin_definitions().items(), key=lambda item: item[0])
    ]


def load_preset(name: str, preset_file: Path | None = None) -> Preset:
    if preset_file:
        override_data = json.loads(preset_file.read_text(encoding="utf-8"))
        base_name = override_data.pop("extends", name)
        base = _base_definition(base_name)
        merged = _deep_merge(base, override_data)
        return _build_preset(merged)

    return _build_preset(_base_definition(name))


def load_preset_rules(name: str) -> str:
    rules_path = _preset_specs_dir().joinpath(f"{name}.md")
    if not rules_path.is_file():
        available = ", ".join(sorted(_builtin_definitions()))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
    return rules_path.read_text(encoding="utf-8")


def _base_definition(name: str) -> dict[str, Any]:
    definitions = _builtin_definitions()
    if name not in definitions:
        available = ", ".join(sorted(definitions))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
    return deepcopy(definitions[name])


@lru_cache(maxsize=1)
def _builtin_definitions() -> dict[str, dict[str, Any]]:
    definitions: dict[str, dict[str, Any]] = {}
    for definition_path in _preset_specs_dir().iterdir():
        if definition_path.suffix != ".json":
            continue
        raw = json.loads(definition_path.read_text(encoding="utf-8"))
        definitions[raw["name"]] = raw
    return definitions


def _preset_specs_dir():
    return files("mdstyledocx").joinpath("preset_specs")


def _build_preset(data: dict[str, Any]) -> Preset:
    return Preset(
        name=data["name"],
        description=data["description"],
        page=PageSettings(**data["page"]),
        styles={name: Style(**style) for name, style in data["styles"].items()},
        list_settings=ListSettings(**data["list_settings"]),
        heading_numbering={
            int(level): scheme for level, scheme in data.get("heading_numbering", {}).items()
        },
    )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
