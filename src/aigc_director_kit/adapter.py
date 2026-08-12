"""Validate public metadata-only manifests for local Skill integrations.

An adapter manifest describes only the interface between a private/local Skill
stack and CineThread. It intentionally cannot carry prompts, source paths,
assets, credentials, generated media, or implementation code. A separate
skill-workflow packet carries sanitized, per-project handoff data.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .contract import SUPPORTED_EVIDENCE, ValidationResult, load_json
from .workflow import WORKFLOW_CONTRACT


ADAPTER_CONTRACT = "aigc-director-local-skill-adapter"
ADAPTER_VERSION = 1
PUBLIC_METADATA_VISIBILITY = "public-metadata-only"
LOCAL_ONLY_SOURCE_ACCESS = "local-only"
ADAPTER_ID_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,79}$")
CONTRACT_LABEL_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,79}$")
SENSITIVE_VALUE_PATTERN = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|secret|password|cookie|authorization|bearer\s|file://|[a-z]:[\\/]|\\\\)"
)
ROOT_FIELDS = frozenset(
    {
        "contract",
        "version",
        "adapter_id",
        "visibility",
        "source_access",
        "workflow_contract",
        "stages",
    }
)
STAGE_FIELDS = frozenset(
    {
        "id",
        "skill_label",
        "role",
        "input_contracts",
        "output_contract",
        "evidence",
    }
)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reject_unknown_fields(value: dict[str, Any], allowed: frozenset[str], label: str, errors: list[str]) -> None:
    unexpected = sorted(set(value) - allowed)
    if unexpected:
        fields = ", ".join(unexpected)
        errors.append(
            f"{label} contains unsupported fields: {fields}. "
            "Public adapters may contain only metadata fields."
        )


def _validate_public_text(value: Any, label: str, errors: list[str], *, max_length: int = 240) -> None:
    if not _text(value):
        errors.append(f"{label} must be a non-empty string.")
        return
    if len(value) > max_length:
        errors.append(f"{label} must be at most {max_length} characters.")
    if SENSITIVE_VALUE_PATTERN.search(value):
        errors.append(
            f"{label} looks like it contains a credential or local source path; "
            "publish labels only."
        )


def _validate_label(value: Any, label: str, errors: list[str]) -> None:
    _validate_public_text(value, label, errors, max_length=80)
    if isinstance(value, str) and not CONTRACT_LABEL_PATTERN.fullmatch(value):
        errors.append(f"{label} must use lowercase letters, digits, and hyphens only.")


def validate_local_skill_adapter(adapter: Any) -> ValidationResult:
    """Validate a public interface declaration for a local Skill stack.

    This only verifies manifest shape and coarse accidental-leak guards. It does
    not inspect, execute, package, or make claims about a local Skill's output.
    """

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(adapter, dict):
        return ValidationResult(False, ["The local Skill adapter root must be a JSON object."], [], {})

    _reject_unknown_fields(adapter, ROOT_FIELDS, "adapter", errors)
    if adapter.get("contract") != ADAPTER_CONTRACT:
        errors.append(f"contract must be '{ADAPTER_CONTRACT}'.")
    if adapter.get("version") != ADAPTER_VERSION:
        errors.append(f"version must be {ADAPTER_VERSION}.")

    adapter_id = adapter.get("adapter_id")
    _validate_label(adapter_id, "adapter_id", errors)
    if isinstance(adapter_id, str) and not ADAPTER_ID_PATTERN.fullmatch(adapter_id):
        errors.append("adapter_id must use lowercase letters, digits, and hyphens only.")

    if adapter.get("visibility") != PUBLIC_METADATA_VISIBILITY:
        errors.append(f"visibility must be '{PUBLIC_METADATA_VISIBILITY}'.")
    if adapter.get("source_access") != LOCAL_ONLY_SOURCE_ACCESS:
        errors.append(f"source_access must be '{LOCAL_ONLY_SOURCE_ACCESS}'.")
    if adapter.get("workflow_contract") != WORKFLOW_CONTRACT:
        errors.append(f"workflow_contract must be '{WORKFLOW_CONTRACT}'.")

    stages = adapter.get("stages")
    stage_ids: set[str] = set()
    skill_labels: list[str] = []
    output_contracts: list[str] = []
    input_contract_count = 0
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
        _reject_unknown_fields(stage, STAGE_FIELDS, label, errors)

        stage_id = stage.get("id")
        _validate_label(stage_id, f"{label}.id", errors)
        if isinstance(stage_id, str):
            if stage_id in stage_ids:
                errors.append(f"{label}.id is duplicated: {stage_id}.")
            else:
                stage_ids.add(stage_id)

        skill_label = stage.get("skill_label")
        _validate_label(skill_label, f"{label}.skill_label", errors)
        if isinstance(skill_label, str) and CONTRACT_LABEL_PATTERN.fullmatch(skill_label):
            skill_labels.append(skill_label)

        _validate_public_text(stage.get("role"), f"{label}.role", errors)

        input_contracts = stage.get("input_contracts")
        if not isinstance(input_contracts, list) or not input_contracts:
            errors.append(f"{label}.input_contracts must be a non-empty array.")
        elif len(input_contracts) > 12:
            errors.append(f"{label}.input_contracts cannot contain more than 12 entries.")
        else:
            seen_inputs: set[str] = set()
            for input_index, input_contract in enumerate(input_contracts):
                input_label = f"{label}.input_contracts[{input_index}]"
                _validate_label(input_contract, input_label, errors)
                if isinstance(input_contract, str):
                    if input_contract in seen_inputs:
                        errors.append(f"{input_label} is duplicated: {input_contract}.")
                    else:
                        seen_inputs.add(input_contract)
            input_contract_count += len(input_contracts)

        output_contract = stage.get("output_contract")
        _validate_label(output_contract, f"{label}.output_contract", errors)
        if isinstance(output_contract, str) and CONTRACT_LABEL_PATTERN.fullmatch(output_contract):
            output_contracts.append(output_contract)

        if stage.get("evidence") not in SUPPORTED_EVIDENCE:
            errors.append(f"{label}.evidence must be one of {sorted(SUPPORTED_EVIDENCE)}.")

    return ValidationResult(
        not errors,
        errors,
        warnings,
        {
            "stage_count": len(stages),
            "skill_labels": skill_labels,
            "input_contract_count": input_contract_count,
            "output_contracts": output_contracts,
            "visibility": adapter.get("visibility"),
            "source_access": adapter.get("source_access"),
            "workflow_contract": adapter.get("workflow_contract"),
        },
    )


def validate_local_skill_adapter_file(path: str | Path) -> ValidationResult:
    """Load and validate a metadata-only local Skill adapter manifest."""

    return validate_local_skill_adapter(load_json(path))
