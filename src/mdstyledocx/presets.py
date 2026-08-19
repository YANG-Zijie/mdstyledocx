from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

PRESET_SCHEMA_VERSION = 1
_REQUIRED_STYLE_NAMES = {"title", "heading1", "heading2", "heading3", "body"}
_ALLOWED_PAGE_STYLE_NAMES = {"header", "footer", "watermark"}
_ALLOWED_ALIGNMENTS = {"left", "center", "right", "justify", "both"}
_ALLOWED_LINE_RULES = {"auto", "exact"}
_ALLOWED_NUMBERING_SCHEMES = {"cn-section", "cn-paren", "arabic-dot"}
_ALLOWED_TOP_LEVEL_FIELDS = {
    "schema_version",
    "name",
    "description",
    "extends",
    "page",
    "paragraph_defaults",
    "styles",
    "page_styles",
    "watermark_defaults",
    "list_settings",
    "heading_numbering",
}

_PRESET_ALIASES = {
    "gov-cn": "official-doc-cn",
    "gov-cn-hei": "official-doc-cn-system-fonts",
}


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
    overflow_punctuation: bool | None = None
    bottom_border_size: int = 0
    bottom_border_space: int = 0
    bottom_border_color: str = "auto"


@dataclass
class ListSettings:
    base_left_indent: int = 720
    hanging: int = 360
    level_step: int = 360


@dataclass
class WatermarkSettings:
    color: str = "D9D9D9"
    opacity: float = 0.25
    rotation: int = -45


@dataclass
class Preset:
    name: str
    description: str
    page: PageSettings
    styles: dict[str, Style]
    list_settings: ListSettings
    heading_numbering: dict[int, str] = field(default_factory=dict)
    page_styles: dict[str, Style] = field(default_factory=dict)
    watermark_defaults: WatermarkSettings = field(default_factory=WatermarkSettings)


def list_presets() -> list[tuple[str, str]]:
    return [
        (name, definition["description"])
        for name, definition in sorted(_builtin_definitions().items(), key=lambda item: item[0])
    ]


def load_preset(name: str, preset_file: Path | None = None) -> Preset:
    return _build_preset(load_preset_definition(name, preset_file))


def load_preset_definition(
    name: str, preset_file: Path | None = None
) -> dict[str, Any]:
    if preset_file:
        override_data = _read_json_object(preset_file)
        _validate_schema_version(override_data, str(preset_file))
        base_name = override_data.pop("extends", name)
        base = _base_definition(base_name)
        merged = _deep_merge(base, override_data)
        _validate_resolved_definition(merged)
        return merged

    definition = _base_definition(name)
    _validate_resolved_definition(definition)
    return definition


def load_preset_rules(name: str) -> str:
    canonical_name = _canonical_preset_name(name)
    rules_path = _preset_specs_dir().joinpath(f"{canonical_name}.md")
    if not rules_path.is_file():
        available = ", ".join(sorted(_builtin_definitions()))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")
    return rules_path.read_text(encoding="utf-8")


def load_preset_schema() -> str:
    return (
        files("mdstyledocx")
        .joinpath("preset.schema.json")
        .read_text(encoding="utf-8")
    )


def _base_definition(name: str, ancestry: tuple[str, ...] = ()) -> dict[str, Any]:
    canonical_name = _canonical_preset_name(name)
    definitions = _builtin_definitions()
    if canonical_name not in definitions:
        available = ", ".join(sorted(definitions))
        raise ValueError(f"Unknown preset '{name}'. Available presets: {available}")

    if canonical_name in ancestry:
        chain = " -> ".join((*ancestry, canonical_name))
        raise ValueError(f"Circular preset inheritance: {chain}")

    definition = deepcopy(definitions[canonical_name])
    base_name = definition.pop("extends", None)
    if not base_name:
        return definition

    base = _base_definition(base_name, (*ancestry, canonical_name))
    return _deep_merge(base, definition)


def _canonical_preset_name(name: str) -> str:
    return _PRESET_ALIASES.get(name, name)


@lru_cache(maxsize=1)
def _builtin_definitions() -> dict[str, dict[str, Any]]:
    definitions: dict[str, dict[str, Any]] = {}
    for definition_path in _preset_specs_dir().iterdir():
        if definition_path.suffix != ".json":
            continue
        raw = _read_json_object(definition_path)
        _validate_schema_version(raw, str(definition_path))
        name = raw.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"Preset file '{definition_path}' must define a non-empty name")
        if name != definition_path.stem:
            raise ValueError(
                f"Preset name '{name}' does not match file name '{definition_path.stem}'"
            )
        if name in definitions:
            raise ValueError(f"Duplicate preset name '{name}'")
        definitions[name] = raw
    return definitions


def _preset_specs_dir():
    return files("mdstyledocx").joinpath("preset_specs")


def _build_preset(data: dict[str, Any]) -> Preset:
    _validate_resolved_definition(data)
    paragraph_defaults = data.get("paragraph_defaults", {})
    try:
        preset = Preset(
            name=data["name"],
            description=data["description"],
            page=PageSettings(**data["page"]),
            styles={
                name: Style(**_deep_merge(paragraph_defaults, style))
                for name, style in data["styles"].items()
            },
            list_settings=ListSettings(**data["list_settings"]),
            heading_numbering={
                int(level): scheme
                for level, scheme in data.get("heading_numbering", {}).items()
            },
            page_styles={
                name: Style(**style)
                for name, style in data.get("page_styles", {}).items()
            },
            watermark_defaults=WatermarkSettings(
                **data.get("watermark_defaults", {})
            ),
        )
        _validate_preset(preset)
    except (TypeError, ValueError) as error:
        raise ValueError(f"Invalid preset '{data.get('name', '<unnamed>')}': {error}") from error

    return preset


def _read_json_object(path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValueError(f"Invalid JSON in preset file '{path}': {error}") from error
    if not isinstance(value, dict):
        raise TypeError(f"Preset file '{path}' must contain a JSON object")
    return value


def _validate_schema_version(data: dict[str, Any], source: str) -> None:
    unexpected = sorted(data.keys() - _ALLOWED_TOP_LEVEL_FIELDS)
    if unexpected:
        raise ValueError(
            f"Unsupported preset fields in '{source}': {', '.join(unexpected)}"
        )
    version = data.get("schema_version", PRESET_SCHEMA_VERSION)
    if (
        isinstance(version, bool)
        or not isinstance(version, int)
        or version != PRESET_SCHEMA_VERSION
    ):
        raise ValueError(
            f"Unsupported preset schema_version {version!r} in '{source}'; "
            f"expected {PRESET_SCHEMA_VERSION}"
        )


def _validate_resolved_definition(data: dict[str, Any]) -> None:
    unexpected = sorted(data.keys() - _ALLOWED_TOP_LEVEL_FIELDS)
    if unexpected:
        raise ValueError(f"Unsupported resolved preset fields: {', '.join(unexpected)}")
    required = {"name", "description", "page", "styles", "list_settings"}
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"Resolved preset is missing required fields: {', '.join(missing)}")

    styles = data["styles"]
    if not isinstance(styles, dict):
        raise TypeError("Resolved preset 'styles' must be an object")
    unexpected_styles = sorted(styles.keys() - _REQUIRED_STYLE_NAMES)
    if unexpected_styles:
        raise ValueError(
            f"Resolved preset contains unsupported styles: {', '.join(unexpected_styles)}"
        )
    missing_styles = sorted(_REQUIRED_STYLE_NAMES - styles.keys())
    if missing_styles:
        raise ValueError(
            f"Resolved preset is missing required styles: {', '.join(missing_styles)}"
        )

    page_styles = data.get("page_styles", {})
    if not isinstance(page_styles, dict):
        raise TypeError("Resolved preset 'page_styles' must be an object")
    unexpected_page_styles = sorted(page_styles.keys() - _ALLOWED_PAGE_STYLE_NAMES)
    if unexpected_page_styles:
        raise ValueError(
            "Resolved preset contains unsupported page styles: "
            f"{', '.join(unexpected_page_styles)}"
        )


def _validate_preset(preset: Preset) -> None:
    if not isinstance(preset.name, str) or not preset.name:
        raise ValueError("Preset name must be a non-empty string")
    if not isinstance(preset.description, str) or not preset.description:
        raise ValueError("Preset description must be a non-empty string")

    page = preset.page
    _validate_integer(page.width, "Page width", minimum=1)
    _validate_integer(page.height, "Page height", minimum=1)
    for label, value in (
        ("Page top margin", page.margin_top),
        ("Page right margin", page.margin_right),
        ("Page bottom margin", page.margin_bottom),
        ("Page left margin", page.margin_left),
        ("Header distance", page.header),
        ("Footer distance", page.footer),
        ("Page gutter", page.gutter),
    ):
        _validate_integer(value, label, minimum=0)
    if page.margin_left + page.margin_right >= page.width:
        raise ValueError("Horizontal margins must leave positive content width")
    if page.margin_top + page.margin_bottom >= page.height:
        raise ValueError("Vertical margins must leave positive content height")

    for name, style in {**preset.styles, **preset.page_styles}.items():
        if not isinstance(style.font_east_asia, str) or not isinstance(
            style.font_ascii, str
        ):
            raise TypeError(f"Style '{name}' font names must be strings")
        if not style.font_east_asia or not style.font_ascii:
            raise ValueError(f"Style '{name}' must define non-empty font names")
        _validate_integer(
            style.size_half_points,
            f"Style '{name}' font size",
            minimum=1,
        )
        if not isinstance(style.bold, bool) or not isinstance(style.italic, bool):
            raise TypeError(f"Style '{name}' bold and italic values must be booleans")
        if style.overflow_punctuation is not None and not isinstance(
            style.overflow_punctuation, bool
        ):
            raise TypeError(
                f"Style '{name}' overflow_punctuation must be a boolean or null"
            )
        if not isinstance(style.bottom_border_color, str) or not (
            style.bottom_border_color == "auto"
            or (
                len(style.bottom_border_color) == 6
                and all(
                    character in "0123456789abcdefABCDEF"
                    for character in style.bottom_border_color
                )
            )
        ):
            raise ValueError(
                f"Style '{name}' bottom_border_color must be 'auto' or six-digit RGB"
            )
        if style.align not in _ALLOWED_ALIGNMENTS:
            raise ValueError(f"Style '{name}' uses unsupported alignment '{style.align}'")
        if style.line_rule not in _ALLOWED_LINE_RULES:
            raise ValueError(
                f"Style '{name}' uses unsupported line rule '{style.line_rule}'"
            )
        _validate_integer(style.line, f"Style '{name}' line spacing", minimum=1)
        for label, value, minimum in (
            ("first-line indent", style.first_line_indent, None),
            ("left indent", style.left_indent, None),
            ("hanging indent", style.hanging, 0),
            ("space before", style.spacing_before, 0),
            ("space after", style.spacing_after, 0),
            ("bottom border size", style.bottom_border_size, 0),
            ("bottom border space", style.bottom_border_space, 0),
        ):
            _validate_integer(value, f"Style '{name}' {label}", minimum=minimum)

    _validate_integer(
        preset.list_settings.base_left_indent,
        "List base_left_indent",
        minimum=0,
    )
    _validate_integer(preset.list_settings.hanging, "List hanging", minimum=0)
    _validate_integer(preset.list_settings.level_step, "List level_step", minimum=0)

    for level, scheme in preset.heading_numbering.items():
        if level < 1 or level > 6:
            raise ValueError(f"Heading numbering level {level} is outside 1-6")
        if scheme not in _ALLOWED_NUMBERING_SCHEMES:
            raise ValueError(f"Unsupported heading numbering scheme '{scheme}'")

    watermark = preset.watermark_defaults
    if not isinstance(watermark.color, str):
        raise TypeError("Watermark color must be a string")
    color = watermark.color.strip().lstrip("#")
    if len(color) != 6 or any(
        character not in "0123456789abcdefABCDEF" for character in color
    ):
        raise ValueError("Watermark color must be a six-digit hexadecimal RGB value")
    if isinstance(watermark.opacity, bool) or not isinstance(
        watermark.opacity, (int, float)
    ):
        raise TypeError("Watermark opacity must be numeric")
    if not 0 <= watermark.opacity <= 1:
        raise ValueError("Watermark opacity must be between 0 and 1")
    _validate_integer(watermark.rotation, "Watermark rotation")


def _validate_integer(value: Any, label: str, minimum: int | None = None) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be at least {minimum}")


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
