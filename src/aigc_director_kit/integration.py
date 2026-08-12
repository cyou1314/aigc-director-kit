"""Cross-validate a local Skill adapter against a project workflow packet.

This module checks that the reusable metadata adapter and the per-project
workflow agree on stage identity, Skill labels, output contracts, and evidence
semantics. It also applies high-confidence public-safety checks without
executing Skills, runtimes, generation, or media inspection.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .actions import load_action_library
from .adapter import validate_local_skill_adapter
from .contract import ValidationResult, load_json
from .prompt import PROMPT_CONTRACT
from .qc import QC_CONTRACT
from .workflow import WORKFLOW_CONTRACT, validate_workflow


SHOT_PLAN_CONTRACT = "aigc-director-shot-plan"
ACTION_REQUEST_CONTRACT = "aigc-director-action-request"
SENSITIVE_KEYS = frozenset(
    {
        "api_key",
        "access_token",
        "refresh_token",
        "auth_token",
        "token",
        "password",
        "passwd",
        "secret",
        "client_secret",
        "cookie",
        "authorization",
        "credential",
        "credentials",
    }
)
LOCAL_PATH_PATTERN = re.compile(
    r"(?i)(?:file://|\b[a-z]:[\\/]|\\\\[^\\\s]+[\\/]|/(?:home|users|private|tmp|var/tmp)/)"
)
CREDENTIAL_VALUE_PATTERN = re.compile(
    r"(?i)(?:\bbearer\s+[a-z0-9._~+/=-]{8,}|\bgh[pousr]_[a-z0-9_]{20,}\b|\bsk-[a-z0-9_-]{20,}\b)"
)
EMAIL_PATTERN = re.compile(r"(?i)\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z0-9-]+)+\b")


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).lower()).strip("_")


def _audit_public_value(value: Any, label: str, errors: list[str]) -> None:
    """Find high-confidence leaks without echoing the sensitive value."""

    if isinstance(value, dict):
        for key, child in value.items():
            child_label = f"{label}.{key}"
            if _normalized_key(key) in SENSITIVE_KEYS:
                errors.append(
                    f"public safety: {child_label} is a credential-bearing field; remove it."
                )
            _audit_public_value(child, child_label, errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _audit_public_value(child, f"{label}[{index}]", errors)
        return
    if not isinstance(value, str):
        return
    if LOCAL_PATH_PATTERN.search(value):
        errors.append(f"public safety: {label} contains a local or network path; replace it with a public label.")
    if CREDENTIAL_VALUE_PATTERN.search(value):
        errors.append(f"public safety: {label} contains a credential-like value; remove it.")
    if EMAIL_PATTERN.search(value):
        errors.append(f"public safety: {label} contains an email address; replace it with a public alias.")


def validate_skill_integration(
    adapter: Any,
    workflow: Any,
    action_library: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate adapter/workflow compatibility and a public-safety boundary.

    A valid result proves only that the two public contracts are structurally
    compatible and contain no high-confidence leak patterns known to this
    validator. Manual privacy review and all runtime/media evidence remain
    separate requirements.
    """

    adapter_result = validate_local_skill_adapter(adapter)
    workflow_result = validate_workflow(workflow, action_library)
    errors = [f"adapter: {error}" for error in adapter_result.errors]
    errors.extend(f"workflow: {error}" for error in workflow_result.errors)
    warnings = [f"adapter: {warning}" for warning in adapter_result.warnings]
    warnings.extend(f"workflow: {warning}" for warning in workflow_result.warnings)

    adapter_dict = adapter if isinstance(adapter, dict) else {}
    workflow_dict = workflow if isinstance(workflow, dict) else {}
    adapter_stages = {
        stage.get("id"): stage
        for stage in adapter_dict.get("stages", [])
        if isinstance(stage, dict) and isinstance(stage.get("id"), str)
    }
    workflow_stages = {
        stage.get("id"): stage
        for stage in workflow_dict.get("stages", [])
        if isinstance(stage, dict) and isinstance(stage.get("id"), str)
    }

    matched_stage_count = 0
    for stage_id, workflow_stage in workflow_stages.items():
        adapter_stage = adapter_stages.get(stage_id)
        if adapter_stage is None:
            errors.append(f"integration: workflow stage '{stage_id}' is not declared by the adapter.")
            continue
        matched_stage_count += 1
        comparisons = (
            ("skill", "skill_label", "Skill label"),
            ("output", "output_contract", "output contract"),
            ("evidence", "evidence", "evidence semantics"),
        )
        for workflow_field, adapter_field, description in comparisons:
            if workflow_stage.get(workflow_field) != adapter_stage.get(adapter_field):
                errors.append(
                    f"integration: stage '{stage_id}' {description} does not match the adapter."
                )

    required_outputs = {WORKFLOW_CONTRACT, SHOT_PLAN_CONTRACT}
    action_requests = workflow_dict.get("action_requests")
    if isinstance(action_requests, list) and action_requests:
        required_outputs.add(ACTION_REQUEST_CONTRACT)
    if workflow_dict.get("prompt_pack") is not None:
        required_outputs.add(PROMPT_CONTRACT)
    if workflow_dict.get("qc_report") is not None:
        required_outputs.add(QC_CONTRACT)

    workflow_outputs = {
        stage.get("output")
        for stage in workflow_stages.values()
        if isinstance(stage.get("output"), str)
    }
    for output_contract in sorted(required_outputs - workflow_outputs):
        errors.append(
            f"integration: no workflow stage declares required output '{output_contract}'."
        )

    if isinstance(action_requests, list):
        for index, request in enumerate(action_requests):
            if not isinstance(request, dict):
                continue
            stage_id = request.get("stage_id")
            stage = workflow_stages.get(stage_id)
            if stage is not None and stage.get("output") != ACTION_REQUEST_CONTRACT:
                errors.append(
                    f"integration: action_requests[{index}].stage_id must reference a stage "
                    f"that outputs '{ACTION_REQUEST_CONTRACT}'."
                )

    safety_errors: list[str] = []
    _audit_public_value(adapter_dict, "adapter", safety_errors)
    _audit_public_value(workflow_dict, "workflow", safety_errors)
    errors.extend(safety_errors)

    unused_adapter_stage_ids = sorted(set(adapter_stages) - set(workflow_stages))
    summary = {
        "adapter_valid": adapter_result.valid,
        "workflow_valid": workflow_result.valid,
        "adapter_stage_count": len(adapter_stages),
        "workflow_stage_count": len(workflow_stages),
        "matched_stage_count": matched_stage_count,
        "unused_adapter_stage_ids": unused_adapter_stage_ids,
        "required_output_contracts": sorted(required_outputs),
        "compiled_action_count": workflow_result.summary.get("compiled_action_count", 0),
        "public_safety_issue_count": len(safety_errors),
        "manual_privacy_review_required": True,
    }
    return ValidationResult(not errors, errors, warnings, summary)


def validate_skill_integration_files(
    adapter_path: str | Path,
    workflow_path: str | Path,
    action_library_path: str | Path | None = None,
) -> ValidationResult:
    """Load and cross-validate public adapter and workflow JSON files."""

    adapter = load_json(adapter_path)
    workflow = load_json(workflow_path)
    library = load_action_library(action_library_path) if action_library_path else None
    return validate_skill_integration(adapter, workflow, library)
