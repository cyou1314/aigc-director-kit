"""Cross-platform verification of CineThread's public examples."""

from __future__ import annotations

import json
import platform
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ._version import __version__
from .actions import compile_action_request, list_actions, load_action_library
from .contract import ValidationResult, validate_plan_file
from .prompt import validate_prompt_pack_file
from .qc import validate_qc_report_file
from .runtime import build_runtime_handoff_file
from .workflow import validate_workflow_file


def find_project_root(root: Path | None = None) -> Path:
    """Find a CineThread source checkout without exposing local paths in errors."""

    start = (root or Path.cwd()).resolve()
    candidates = (start,) if root is not None else (start, *start.parents)
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (candidate / "examples").is_dir():
            return candidate
    raise FileNotFoundError(
        "Could not find a CineThread source checkout. Run this command from a cloned "
        "or extracted checkout, or pass --root <checkout>."
    )


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _sanitize_text(value: object, root: Path) -> str:
    text = str(value)
    native_root = str(root)
    return text.replace(native_root, ".").replace(native_root.replace("\\", "/"), ".")


def _validation_check(
    check_id: str,
    root: Path,
    path: Path,
    validate: Callable[[], ValidationResult],
) -> dict[str, Any]:
    try:
        result = validate()
        return {
            "id": check_id,
            "path": _relative_path(root, path),
            "valid": result.valid,
            "summary": result.summary,
            "errors": [_sanitize_text(error, root) for error in result.errors],
            "warnings": [_sanitize_text(warning, root) for warning in result.warnings],
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "id": check_id,
            "path": _relative_path(root, path),
            "valid": False,
            "summary": {},
            "errors": [_sanitize_text(exc, root)],
            "warnings": [],
        }


def _callable_check(
    check_id: str,
    root: Path,
    run: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    try:
        return run()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "id": check_id,
            "valid": False,
            "summary": {},
            "errors": [_sanitize_text(exc, root)],
            "warnings": [],
        }


def _json_fixture_check(root: Path) -> dict[str, Any]:
    paths = sorted((root / "examples").glob("*.json")) + sorted((root / "schemas").glob("*.json"))
    try:
        for path in paths:
            json.loads(path.read_text(encoding="utf-8"))
        return {
            "id": "json-fixtures",
            "valid": True,
            "summary": {"parsed_file_count": len(paths)},
            "errors": [],
            "warnings": [],
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "id": "json-fixtures",
            "valid": False,
            "summary": {},
            "errors": [_sanitize_text(exc, root)],
            "warnings": [],
        }


def run_public_example_verification(root: Path | None = None) -> dict[str, Any]:
    """Run deterministic checks over all public examples in a source checkout.

    The report contains relative paths and generic environment data so it can be
    safely copied into a public issue after the user reviews it.
    """

    project_root = find_project_root(root)
    examples = project_root / "examples"
    library_path = examples / "action_library.json"

    checks: list[dict[str, Any]] = [
        _validation_check(
            "shot-plan",
            project_root,
            examples / "shot_plan.json",
            lambda: validate_plan_file(examples / "shot_plan.json"),
        ),
        _validation_check(
            "one-take-previs-plan",
            project_root,
            examples / "one_take_previs_case.json",
            lambda: validate_plan_file(examples / "one_take_previs_case.json"),
        ),
        _validation_check(
            "film-contract-handoff-plan",
            project_root,
            examples / "film_contract_handoff_case.json",
            lambda: validate_plan_file(examples / "film_contract_handoff_case.json"),
        ),
        _validation_check(
            "multi-actor-prop-plan",
            project_root,
            examples / "multi_actor_prop_case.json",
            lambda: validate_plan_file(examples / "multi_actor_prop_case.json"),
        ),
        _validation_check(
            "skill-workflow",
            project_root,
            examples / "skill_workflow_case.json",
            lambda: validate_workflow_file(examples / "skill_workflow_case.json", library_path),
        ),
        _validation_check(
            "prompt-pack",
            project_root,
            examples / "prompt_pack_case.json",
            lambda: validate_prompt_pack_file(
                examples / "prompt_pack_case.json",
                examples / "one_take_previs_case.json",
            ),
        ),
        _validation_check(
            "qc-evidence-boundary",
            project_root,
            examples / "qc_report_unverified_case.json",
            lambda: validate_qc_report_file(examples / "qc_report_unverified_case.json"),
        ),
    ]

    def verify_action_catalog() -> dict[str, Any]:
        library = load_action_library(library_path)
        matches = list_actions(library, "run")
        matched_ids = [str(item["id"]) for item in matches]
        valid = "run_quick_stop" in matched_ids
        return {
            "id": "action-catalog-search",
            "valid": valid,
            "summary": {"matched_action_ids": matched_ids},
            "errors": [] if valid else ["Expected action 'run_quick_stop' was not found."],
            "warnings": [],
        }

    def verify_action_compilation() -> dict[str, Any]:
        library = load_action_library(library_path)
        result = compile_action_request(
            "run quick stop, blend 0.2s, fast, in place",
            library,
        )
        matched_ids = [str(item["id"]) for item in result["matched_actions"]]
        valid = bool(result["valid"]) and matched_ids == ["run_quick_stop"]
        return {
            "id": "action-request-compilation",
            "valid": valid,
            "summary": {"matched_action_ids": matched_ids},
            "errors": []
            if valid
            else [_sanitize_text(result.get("error", "Action request did not compile."), project_root)],
            "warnings": [],
        }

    def verify_runtime_handoff() -> dict[str, Any]:
        packet = build_runtime_handoff_file(
            examples / "skill_workflow_case.json",
            library_path,
            adapter_name="optional-runtime-adapter",
        )
        valid = bool(packet["valid"])
        validation = packet.get("validation", {})
        raw_errors = validation.get("errors", []) if isinstance(validation, dict) else []
        return {
            "id": "runtime-handoff",
            "valid": valid,
            "summary": {
                "adapter": packet["runtime"]["adapter"],
                "mode": packet["runtime"]["mode"],
                "compiled_action_count": len(packet["compiled_action_requests"]),
            },
            "errors": []
            if valid
            else [
                _sanitize_text(error, project_root)
                for error in (raw_errors or ["Runtime handoff did not validate."])
            ],
            "warnings": [],
        }

    checks.extend(
        [
            _callable_check("action-catalog-search", project_root, verify_action_catalog),
            _callable_check("action-request-compilation", project_root, verify_action_compilation),
            _callable_check("runtime-handoff", project_root, verify_runtime_handoff),
            _json_fixture_check(project_root),
        ]
    )

    return {
        "tool": "CineThread",
        "package": "aigc-director-kit",
        "version": __version__,
        "environment": {
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "platform": platform.system(),
            "python_executable": Path(sys.executable).name,
        },
        "valid": all(check["valid"] for check in checks),
        "summary": {
            "check_count": len(checks),
            "passed_check_count": sum(1 for check in checks if check["valid"]),
        },
        "checks": checks,
        "boundary": (
            "This verifies public JSON contracts and deterministic dry-run handoffs only. "
            "It does not render, generate, open media, or perform final video QC."
        ),
    }
