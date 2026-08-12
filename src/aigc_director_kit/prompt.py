"""Validation for reusable, shot-aware AIGC prompt packs."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from .contract import SHOT_ID_PATTERN, SUPPORTED_EVIDENCE, ValidationResult, load_json, validate_plan


PROMPT_CONTRACT = "aigc-director-prompt-pack"
PROMPT_VERSION = 1


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _state(value: Any) -> bool:
    return _text(value) or (isinstance(value, dict) and bool(value))


def _string_array(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not _text(item) for item in value):
        errors.append(f"{label} must be a string array.")


def validate_prompt_pack(
    prompt_pack: Any,
    shot_plan: dict[str, Any] | None = None,
) -> ValidationResult:
    """Validate global prompt rules and per-shot prompt deltas.

    When a source shot plan is supplied, shot ids and locked durations are
    cross-checked. A duration mismatch is a warning so a human can decide
    whether the prompt pack intentionally changes the source contract.
    """

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(prompt_pack, dict):
        return ValidationResult(False, ["The prompt pack root must be a JSON object."], [], {})

    if prompt_pack.get("contract") != PROMPT_CONTRACT:
        errors.append(f"contract must be '{PROMPT_CONTRACT}'.")
    if prompt_pack.get("version") != PROMPT_VERSION:
        errors.append(f"version must be {PROMPT_VERSION}.")
    if not _text(prompt_pack.get("project")):
        errors.append("project must be a non-empty string.")

    global_rules = prompt_pack.get("global_rules")
    if not isinstance(global_rules, dict):
        errors.append("global_rules must be an object.")
        global_rules = {}
    for field_name in ("character_anchors", "scene_anchors", "stability", "avoid"):
        if field_name in global_rules:
            _string_array(global_rules[field_name], f"global_rules.{field_name}", errors)
    if "style" in global_rules and not _text(global_rules["style"]):
        errors.append("global_rules.style must be a non-empty string.")

    shots = prompt_pack.get("shots")
    shot_ids: set[str] = set()
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array.")
        shots = []
    elif len(shots) > 100:
        errors.append("shots cannot contain more than 100 entries.")

    prompt_durations: dict[str, float] = {}
    for index, shot in enumerate(shots):
        label = f"shots[{index}]"
        if not isinstance(shot, dict):
            errors.append(f"{label} must be an object.")
            continue
        shot_id = shot.get("shot_id")
        if not isinstance(shot_id, str) or not SHOT_ID_PATTERN.fullmatch(shot_id):
            errors.append(f"{label}.shot_id must match {SHOT_ID_PATTERN.pattern!r}.")
        elif shot_id in shot_ids:
            errors.append(f"{label}.shot_id is duplicated: {shot_id}.")
        else:
            shot_ids.add(shot_id)

        duration_s = shot.get("duration_s")
        if not _number(duration_s) or not 0.25 <= float(duration_s) <= 60:
            errors.append(f"{label}.duration_s must be between 0.25 and 60 seconds.")
        elif isinstance(shot_id, str):
            prompt_durations[shot_id] = float(duration_s)

        for field_name in (
            "primary_task",
            "action_causality",
            "camera_job",
            "prompt",
        ):
            if not _text(shot.get(field_name)):
                errors.append(f"{label}.{field_name} must be a non-empty string.")
        if isinstance(shot.get("prompt"), str) and len(shot["prompt"]) > 20000:
            errors.append(f"{label}.prompt cannot exceed 20000 characters.")
        for field_name in ("entry_state", "exit_state"):
            if not _state(shot.get(field_name)):
                errors.append(f"{label}.{field_name} must be a non-empty string or object.")
        if shot.get("evidence") not in SUPPORTED_EVIDENCE:
            errors.append(f"{label}.evidence must be one of {sorted(SUPPORTED_EVIDENCE)}.")
        for field_name in ("source_shot_id", "source_panel"):
            if field_name in shot and not _text(shot[field_name]):
                errors.append(f"{label}.{field_name} must be a non-empty string when provided.")
        if "revision_notes" in shot:
            _string_array(shot["revision_notes"], f"{label}.revision_notes", errors)

    source_shot_ids: set[str] = set()
    source_durations: dict[str, float] = {}
    if shot_plan is not None:
        plan_result = validate_plan(shot_plan)
        errors.extend(f"shot_plan: {error}" for error in plan_result.errors)
        warnings.extend(f"shot_plan: {warning}" for warning in plan_result.warnings)
        if isinstance(shot_plan, dict) and isinstance(shot_plan.get("shots"), list):
            for source_shot in shot_plan["shots"]:
                if not isinstance(source_shot, dict) or not isinstance(source_shot.get("id"), str):
                    continue
                source_id = source_shot["id"]
                source_shot_ids.add(source_id)
                if _number(source_shot.get("duration_s")):
                    source_durations[source_id] = float(source_shot["duration_s"])
        for index, shot in enumerate(shots):
            if not isinstance(shot, dict):
                continue
            shot_id = shot.get("source_shot_id", shot.get("shot_id"))
            if shot_id not in source_shot_ids:
                errors.append(f"shots[{index}] must reference a shot in the source shot plan.")
                continue
            duration_s = prompt_durations.get(shot.get("shot_id"))
            source_duration = source_durations.get(shot_id)
            if duration_s is not None and source_duration is not None and duration_s != source_duration:
                warnings.append(
                    f"shots[{index}].duration_s differs from source shot {shot_id}; confirm the locked duration."
                )

    summary = {
        "prompt_shot_count": len(shots),
        "prompt_shot_ids": sorted(shot_ids),
        "source_shot_count": len(source_shot_ids),
        "global_rule_fields": sorted(global_rules),
    }
    return ValidationResult(not errors, errors, warnings, summary)


def validate_prompt_pack_file(
    path: str | Path,
    shot_plan_path: str | Path | None = None,
) -> ValidationResult:
    """Load and validate a prompt pack, optionally against a shot plan."""

    prompt_pack = load_json(path)
    shot_plan = load_json(shot_plan_path) if shot_plan_path else None
    return validate_prompt_pack(prompt_pack, shot_plan)
