"""Command-line interface for AIGC Director Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .actions import compile_action_request, list_actions, load_action_library
from .contract import validate_plan_file


def _dump(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aigc-director-kit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate-plan", help="Validate a shot-plan JSON file.")
    validate.add_argument("path", type=Path)
    validate.add_argument("--json", action="store_true", dest="as_json")

    search = subparsers.add_parser("list-actions", help="Search an action catalog.")
    search.add_argument("--library", required=True, type=Path)
    search.add_argument("--query", default="")
    search.add_argument("--category")
    search.add_argument("--limit", type=int, default=20)

    compile_parser = subparsers.add_parser("compile-action", help="Compile a bounded action request.")
    compile_parser.add_argument("--library", required=True, type=Path)
    compile_parser.add_argument("--text", required=True)
    compile_parser.add_argument("--output", type=Path)
    compile_parser.add_argument("--output-fps", type=float, default=24.0)
    return parser


def _write_new_json(path: Path, value: Any) -> None:
    target = path.resolve()
    if target.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "validate-plan":
            result = validate_plan_file(args.path)
            if args.as_json:
                _dump(result.as_dict())
            else:
                print(f"valid: {'yes' if result.valid else 'no'}")
                print(f"shots: {result.summary.get('shot_count', 0)}")
                print(f"duration_s: {result.summary.get('total_duration_s', 0)}")
                for error in result.errors:
                    print(f"error: {error}")
                for warning in result.warnings:
                    print(f"warning: {warning}")
            return 0 if result.valid else 2

        if args.command == "list-actions":
            library = load_action_library(args.library)
            _dump(list_actions(library, args.query, category=args.category, limit=args.limit))
            return 0

        if args.command == "compile-action":
            library = load_action_library(args.library)
            result = compile_action_request(args.text, library, args.output_fps)
            if args.output:
                _write_new_json(args.output, result)
            _dump(result)
            return 0 if result["valid"] else 2
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 1
