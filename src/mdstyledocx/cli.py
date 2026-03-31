from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from mdstyledocx.docx_writer import build_docx
from mdstyledocx.markdown import parse_markdown
from mdstyledocx.presets import list_presets, load_preset, load_preset_rules


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mdstyledocx",
        description="Convert convention-based Markdown into standardized DOCX using reusable presets.",
    )
    parser.add_argument("input", nargs="?", help="Input Markdown file path, or '-' to read from stdin.")
    parser.add_argument("-o", "--output", help="Output DOCX file path.")
    parser.add_argument(
        "--preset",
        default="default",
        help="Built-in preset name. Use --list-presets to inspect available values.",
    )
    parser.add_argument(
        "--preset-file",
        type=Path,
        help="Optional JSON override file to extend or replace parts of a preset.",
    )
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="Print built-in presets and exit.",
    )
    parser.add_argument(
        "--show-preset-rules",
        metavar="PRESET",
        help="Print the Markdown conventions and style notes for a built-in preset, then exit.",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.list_presets:
        for name, description in list_presets():
            print(f"{name}: {description}")
        return 0

    if args.show_preset_rules:
        print(load_preset_rules(args.show_preset_rules).rstrip())
        return 0

    if not args.input:
        parser.error("an input Markdown file is required unless --list-presets is used")

    if args.input == "-":
        markdown_text = sys.stdin.read()
        if not args.output:
            parser.error("--output is required when reading Markdown from stdin")
        output_path = Path(args.output)
    else:
        input_path = Path(args.input)
        markdown_text = input_path.read_text(encoding="utf-8")
        output_path = Path(args.output) if args.output else input_path.with_suffix(".docx")

    preset = load_preset(args.preset, args.preset_file)
    base_path = Path.cwd() if args.input == "-" else input_path.parent
    document = parse_markdown(markdown_text, base_path=base_path)
    output_path.write_bytes(build_docx(document, preset))
    print(f"Wrote {output_path} with preset '{preset.name}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
