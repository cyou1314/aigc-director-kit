"""Build a deterministic handoff packet for optional runtime adapters."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .actions import compile_action_request, load_action_library
from .contract import load_json
from .workflow import validate_workflow


RUNTIME_HANDOFF_CONTRACT = "aigc-director-runtime-handoff"
RUNTIME_HANDOFF_VERSION = 1


def build_runtime_handoff(
    workflow: Any,
    action_library: dict[str, Any],
    *,
    adapter_name: str = "optional-runtime-adapter",
) -> dict[str, Any]:
    """Build a dry-run packet without executing an external runtime.

    The packet contains the validated contracts and compiled action requests,
    but it never maps ids to motion files, launches Blender, renders media, or
    claims that QC has happened.
    """

    if not isinstance(adapter_name, str) or not adapter_name.strip():
        raise ValueError("adapter_name must be a non-empty string.")

    validation = validate_workflow(workflow, action_library)
    workflow_dict = workflow if isinstance(workflow, dict) else {}
    compiled_requests: list[dict[str, Any]] = []
    for request in workflow_dict.get("action_requests", []):
        if not isinstance(request, dict):
            continue
        text = request.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        compiled = compile_action_request(text, action_library)
        if compiled["valid"]:
            compiled_requests.append(
                {
                    "shot_id": request.get("shot_id"),
                    "stage_id": request.get("stage_id"),
                    "input": text,
                    "compiled": compiled,
                }
            )

    qc_report = workflow_dict.get("qc_report")
    qc_status = qc_report.get("overall_status") if isinstance(qc_report, dict) else "not_provided"
    return {
        "contract": RUNTIME_HANDOFF_CONTRACT,
        "version": RUNTIME_HANDOFF_VERSION,
        "valid": validation.valid,
        "project": workflow_dict.get("project"),
        "validation": validation.as_dict(),
        "shot_plan": workflow_dict.get("shot_plan"),
        "prompt_pack": workflow_dict.get("prompt_pack"),
        "compiled_action_requests": compiled_requests,
        "runtime": {
            "adapter": adapter_name,
            "mode": "dry-run",
            "executed": False,
            "required_next_steps": [
                "Map compiled action ids to runtime-owned motion assets.",
                "Honor the shot entry and exit states and next-shot handle.",
                "Record actual render and QC evidence separately from this packet.",
            ],
        },
        "evidence": {
            "contract_validation": "passed" if validation.valid else "failed",
            "render_status": "not_run",
            "qc_status": qc_status,
        },
    }


def build_runtime_handoff_file(
    path: str | Path,
    action_library_path: str | Path,
    *,
    adapter_name: str = "optional-runtime-adapter",
) -> dict[str, Any]:
    """Load a workflow and action catalog, then build a dry-run packet."""

    workflow = load_json(path)
    library = load_action_library(action_library_path)
    return build_runtime_handoff(workflow, library, adapter_name=adapter_name)
