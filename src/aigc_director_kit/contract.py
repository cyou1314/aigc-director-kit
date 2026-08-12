"""Deterministic validation for the public shot-plan contract."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SUPPORTED_EVIDENCE = frozenset({"observed", "inferred", "designed"})
SUPPORTED_RIGS = frozenset(
    {"tripod", "dolly", "crane", "gimbal", "controlled_handheld", "free"}
)
SHOT_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


@dataclass
class ValidationResult:
    """Machine-readable validation output."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract": "aigc-director-validation-result",
            "version": 1,
            "valid": self.valid,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "summary": dict(self.summary),
        }


def load_json(path: str | Path) -> Any:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def load_plan(path: str | Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise ValueError("The shot plan root must be a JSON object.")
    return value


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _state(value: Any) -> bool:
    return _text(value) or (isinstance(value, dict) and bool(value))


def _vec3(value: Any, label: str, errors: list[str]) -> bool:
    if not isinstance(value, list) or len(value) != 3:
        errors.append(f"{label} must be an array of 3 finite numbers.")
        return False
    valid = True
    for index, item in enumerate(value):
        if not _number(item):
            errors.append(f"{label}[{index}] must be a finite number.")
            valid = False
    return valid


def _check_camera(camera: Any, label: str, duration_s: float, errors: list[str]) -> None:
    if not isinstance(camera, dict):
        errors.append(f"{label} must be an object.")
        return
    rig = camera.get("rig")
    if rig not in SUPPORTED_RIGS:
        errors.append(f"{label}.rig must be one of {sorted(SUPPORTED_RIGS)}.")
    if not _text(camera.get("job")):
        errors.append(f"{label}.job must be a non-empty string.")
    path = camera.get("path")
    if not isinstance(path, list) or len(path) < 2:
        errors.append(f"{label}.path must contain at least two keyframes.")
        return
    previous_time = -1.0
    for index, point in enumerate(path):
        point_label = f"{label}.path[{index}]"
        if not isinstance(point, dict):
            errors.append(f"{point_label} must be an object.")
            continue
        time_s = point.get("time_s")
        if not _number(time_s) or not 0 <= float(time_s) <= duration_s:
            errors.append(f"{point_label}.time_s must be inside the shot duration.")
        elif float(time_s) <= previous_time:
            errors.append(f"{point_label}.time_s must be strictly increasing.")
        else:
            previous_time = float(time_s)
        _vec3(point.get("position"), f"{point_label}.position", errors)
        if "look_at" in point:
            _vec3(point["look_at"], f"{point_label}.look_at", errors)
    for name, minimum, maximum in (("focal_length_mm", 10, 200), ("focus_distance_m", 0.01, 10000)):
        if name in camera and (
            not _number(camera[name]) or not minimum <= float(camera[name]) <= maximum
        ):
            errors.append(f"{label}.{name} must be between {minimum} and {maximum}.")


def _check_string_list(value: Any, label: str, errors: list[str], maximum: int | None = None) -> None:
    if not isinstance(value, list) or not value or (maximum is not None and len(value) > maximum):
        size_text = f" with at most {maximum} items" if maximum is not None else ""
        errors.append(f"{label} must be a non-empty string array{size_text}.")
        return
    if any(not _text(item) for item in value):
        errors.append(f"{label} must contain only non-empty strings.")


def validate_plan(plan: Any) -> ValidationResult:
    """Validate a plan without touching referenced external assets."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(plan, dict):
        return ValidationResult(False, ["The shot plan root must be a JSON object."], [], {})

    if plan.get("contract") != "aigc-director-shot-plan":
        errors.append("contract must be 'aigc-director-shot-plan'.")
    if plan.get("version") != 1:
        errors.append("version must be 1.")
    if not _text(plan.get("project")):
        errors.append("project must be a non-empty string.")

    fps = plan.get("fps")
    if not _number(fps) or not 1 <= float(fps) <= 120:
        errors.append("fps must be between 1 and 120.")

    resolution = plan.get("resolution")
    if not isinstance(resolution, dict):
        errors.append("resolution must be an object with width and height.")
    else:
        for key in ("width", "height"):
            value = resolution.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or not 16 <= value <= 16384:
                errors.append(f"resolution.{key} must be an integer between 16 and 16384.")

    shots = plan.get("shots")
    if not isinstance(shots, list) or not shots:
        errors.append("shots must be a non-empty array.")
        shots = []
    elif len(shots) > 100:
        errors.append("shots cannot contain more than 100 entries.")

    seen_ids: set[str] = set()
    total_duration = 0.0
    shot_ids: list[str] = []
    for index, shot in enumerate(shots):
        label = f"shots[{index}]"
        if not isinstance(shot, dict):
            errors.append(f"{label} must be an object.")
            continue
        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not SHOT_ID_PATTERN.fullmatch(shot_id):
            errors.append(f"{label}.id must match {SHOT_ID_PATTERN.pattern!r}.")
        elif shot_id in seen_ids:
            errors.append(f"{label}.id is duplicated: {shot_id}.")
        else:
            seen_ids.add(shot_id)
            shot_ids.append(shot_id)

        duration_s = shot.get("duration_s")
        if not _number(duration_s) or not 0.25 <= float(duration_s) <= 60:
            errors.append(f"{label}.duration_s must be between 0.25 and 60 seconds.")
            duration_s = 0.0
        else:
            total_duration += float(duration_s)

        for field_name in ("intent", "next_handle"):
            if not _text(shot.get(field_name)):
                errors.append(f"{label}.{field_name} must be a non-empty string.")
        evidence = shot.get("evidence")
        if evidence not in SUPPORTED_EVIDENCE:
            errors.append(f"{label}.evidence must be one of {sorted(SUPPORTED_EVIDENCE)}.")
        for state_name in ("entry_state", "exit_state"):
            if not _state(shot.get(state_name)):
                errors.append(f"{label}.{state_name} must be a non-empty string or object.")
        _check_camera(shot.get("camera"), f"{label}.camera", float(duration_s), errors)

        if "attention_order" in shot:
            _check_string_list(shot["attention_order"], f"{label}.attention_order", errors, 5)
        if "beats" in shot:
            _check_string_list(shot["beats"], f"{label}.beats", errors)
        if "continuous_take" in shot and not isinstance(shot["continuous_take"], bool):
            errors.append(f"{label}.continuous_take must be boolean.")

    for previous, current in zip(shots, shots[1:]):
        if not isinstance(previous, dict) or not isinstance(current, dict):
            continue
        previous_exit = previous.get("exit_state")
        current_entry = current.get("entry_state")
        if _state(previous_exit) and _state(current_entry) and previous_exit != current_entry:
            warnings.append(
                f"{previous.get('id', 'previous')} -> {current.get('id', 'current')}: "
                "entry_state differs from the previous exit_state; confirm the intended handoff."
            )

    total_frames = math.ceil(total_duration * float(fps)) if _number(fps) else 0
    summary = {
        "shot_count": len(shots),
        "shot_ids": shot_ids,
        "total_duration_s": round(total_duration, 6),
        "total_frames": total_frames,
        "fps": fps if _number(fps) else None,
    }
    return ValidationResult(not errors, errors, warnings, summary)


def validate_plan_file(path: str | Path) -> ValidationResult:
    return validate_plan(load_plan(path))
