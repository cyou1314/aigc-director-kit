"""Validation and dry-run compilation for skill workflow handoffs.

The workflow contract is deliberately an orchestration boundary. It records
which skill produced each handoff, embeds a public shot plan, and keeps action
requests as text until the supplied action catalog compiles them. It does not
run external skills, Blender, FFmpeg, model APIs, or video QC.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .actions import compile_action_request, load_action_library
from .contract import SUPPORTED_EVIDENCE, ValidationResult, load_json, validate_plan
from .prompt import validate_prompt_pack
from .qc import validate_qc_report


WORKFLOW_CONTRACT = "aigc-director-skill-workflow"
WORKFLOW_VERSION = 1
WORKFLOW_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
SUPPORTED_STAGE_STATUS = frozenset({"draft", "validated", "unverified"})


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_array(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not _text(item) for item in value):
        errors.append(f"{label} must be a string array.")


def validate_workflow(
    workflow: Any,
    action_library: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate a skill handoff and optionally compile its action requests.

    Without an action library, action requests remain valid but receive a
    warning because they have not been matched to runtime-safe action ids.
    With a library, an unmatched request is an error and no motion is invented.
    """

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(workflow, dict):
        return ValidationResult(False, ["The workflow root must be a JSON object."], [], {})

    if workflow.get("contract") != WORKFLOW_CONTRACT:
        errors.append(f"contract must be '{WORKFLOW_CONTRACT}'.")
    if workflow.get("version") != WORKFLOW_VERSION:
        errors.append(f"version must be {WORKFLOW_VERSION}.")
    if not _text(workflow.get("project")):
        errors.append("project must be a non-empty string.")

    stages = workflow.get("stages")
    stage_ids: set[str] = set()
    if not isinstance(stages, list) or not stages:
        errors.append("stages must be a non-empty array.")
        stages = []
    elif len(stages) > 32:
        errors.append("stages cannot contain more than 32 entries.")

    for index, stage in enumerate(stages):
        label = f"stages[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{label} must be an object.")
            continue
        stage_id = stage.get("id")
        if not isinstance(stage_id, str) or not WORKFLOW_ID_PATTERN.fullmatch(stage_id):
            errors.append(f"{label}.id must match {WORKFLOW_ID_PATTERN.pattern!r}.")
        elif stage_id in stage_ids:
            errors.append(f"{label}.id is duplicated: {stage_id}.")
        else:
            stage_ids.add(stage_id)
        for field_name in ("skill", "role", "output"):
            if not _text(stage.get(field_name)):
                errors.append(f"{label}.{field_name} must be a non-empty string.")
        evidence = stage.get("evidence")
        if evidence not in SUPPORTED_EVIDENCE:
            errors.append(f"{label}.evidence must be one of {sorted(SUPPORTED_EVIDENCE)}.")
        status = stage.get("status", "draft")
        if status not in SUPPORTED_STAGE_STATUS:
            errors.append(f"{label}.status must be one of {sorted(SUPPORTED_STAGE_STATUS)}.")

    shot_plan = workflow.get("shot_plan")
    plan_result: ValidationResult | None = None
    shot_ids: set[str] = set()
    if shot_plan is None:
        errors.append("shot_plan must be an embedded shot-plan object.")
    else:
        plan_result = validate_plan(shot_plan)
        errors.extend(f"shot_plan: {error}" for error in plan_result.errors)
        warnings.extend(f"shot_plan: {warning}" for warning in plan_result.warnings)
        if isinstance(shot_plan, dict) and isinstance(shot_plan.get("shots"), list):
            shot_ids = {
                shot.get("id")
                for shot in shot_plan["shots"]
                if isinstance(shot, dict) and isinstance(shot.get("id"), str)
            }

    action_requests = workflow.get("action_requests", [])
    compiled_action_count = 0
    matched_action_ids: list[str] = []
    if not isinstance(action_requests, list):
        errors.append("action_requests must be an array when provided.")
        action_requests = []
    elif len(action_requests) > 100:
        errors.append("action_requests cannot contain more than 100 entries.")

    for index, request in enumerate(action_requests):
        label = f"action_requests[{index}]"
        if not isinstance(request, dict):
            errors.append(f"{label} must be an object.")
            continue
        shot_id = request.get("shot_id")
        if shot_id not in shot_ids:
            errors.append(f"{label}.shot_id must reference a shot in shot_plan.")
        stage_id = request.get("stage_id")
        if stage_id not in stage_ids:
            errors.append(f"{label}.stage_id must reference a workflow stage.")
        if not _text(request.get("text")):
            errors.append(f"{label}.text must be a non-empty string.")
        if request.get("evidence") not in SUPPORTED_EVIDENCE:
            errors.append(f"{label}.evidence must be one of {sorted(SUPPORTED_EVIDENCE)}.")
        if action_library is None:
            warnings.append(f"{label} was not compiled; provide --library for deterministic matching.")
            continue
        if not _text(request.get("text")):
            continue
        compiled = compile_action_request(request["text"], action_library)
        if not compiled["valid"]:
            errors.append(f"{label} could not be compiled: {compiled['error']}")
            continue
        compiled_action_count += 1
        matched_action_ids.extend(item["id"] for item in compiled["matched_actions"])

    handoff = workflow.get("handoff", {})
    if not isinstance(handoff, dict):
        errors.append("handoff must be an object when provided.")
        handoff = {}
    elif "next_adapter" in handoff and not _text(handoff["next_adapter"]):
        errors.append("handoff.next_adapter must be a non-empty string.")
    for field_name in ("constraints", "unverified"):
        if field_name in handoff:
            _string_array(handoff[field_name], f"handoff.{field_name}", errors)

    prompt_pack = workflow.get("prompt_pack")
    prompt_pack_present = prompt_pack is not None
    if prompt_pack_present:
        prompt_result = validate_prompt_pack(prompt_pack, shot_plan if isinstance(shot_plan, dict) else None)
        errors.extend(f"prompt_pack: {error}" for error in prompt_result.errors)
        warnings.extend(f"prompt_pack: {warning}" for warning in prompt_result.warnings)

    qc_report = workflow.get("qc_report")
    qc_report_status = None
    if qc_report is not None:
        qc_result = validate_qc_report(qc_report)
        errors.extend(f"qc_report: {error}" for error in qc_result.errors)
        warnings.extend(f"qc_report: {warning}" for warning in qc_result.warnings)
        if isinstance(qc_report, dict):
            qc_report_status = qc_report.get("overall_status")

    plan_summary = plan_result.summary if plan_result else {}
    summary = {
        "stage_count": len(stages),
        "shot_count": plan_summary.get("shot_count", 0),
        "shot_ids": plan_summary.get("shot_ids", []),
        "action_request_count": len(action_requests),
        "compiled_action_count": compiled_action_count,
        "matched_action_ids": matched_action_ids,
        "next_adapter": handoff.get("next_adapter"),
        "prompt_pack_present": prompt_pack_present,
        "qc_report_status": qc_report_status,
    }
    return ValidationResult(not errors, errors, warnings, summary)


def validate_workflow_file(
    path: str | Path,
    action_library_path: str | Path | None = None,
) -> ValidationResult:
    """Load and validate a workflow, optionally compiling action requests."""

    workflow = load_json(path)
    library = load_action_library(action_library_path) if action_library_path else None
    return validate_workflow(workflow, library)
