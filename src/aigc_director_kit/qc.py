"""Evidence-bound validation for optional render and video QC reports."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .contract import SUPPORTED_EVIDENCE, ValidationResult, load_json


QC_CONTRACT = "aigc-director-qc-report"
QC_VERSION = 1
QC_STATUS = frozenset({"pass", "fail", "unverified", "not_run"})
QC_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_array(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not _text(item) for item in value):
        errors.append(f"{label} must be a string array.")


def validate_qc_report(report: Any) -> ValidationResult:
    """Validate QC evidence without opening or interpreting a media file."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(report, dict):
        return ValidationResult(False, ["The QC report root must be a JSON object."], [], {})

    if report.get("contract") != QC_CONTRACT:
        errors.append(f"contract must be '{QC_CONTRACT}'.")
    if report.get("version") != QC_VERSION:
        errors.append(f"version must be {QC_VERSION}.")
    if not _text(report.get("project")):
        errors.append("project must be a non-empty string.")

    artifact = report.get("artifact")
    artifact_available = False
    if not isinstance(artifact, dict):
        errors.append("artifact must be an object.")
    else:
        if not _text(artifact.get("label")):
            errors.append("artifact.label must be a non-empty string.")
        if not isinstance(artifact.get("available"), bool):
            errors.append("artifact.available must be boolean.")
        else:
            artifact_available = artifact["available"]

    overall_status = report.get("overall_status")
    if overall_status not in QC_STATUS:
        errors.append(f"overall_status must be one of {sorted(QC_STATUS)}.")

    checks = report.get("checks")
    check_ids: set[str] = set()
    observed_count = 0
    failed_count = 0
    decisive_count = 0
    if not isinstance(checks, list) or not checks:
        errors.append("checks must be a non-empty array.")
        checks = []
    elif len(checks) > 64:
        errors.append("checks cannot contain more than 64 entries.")

    for index, check in enumerate(checks):
        label = f"checks[{index}]"
        if not isinstance(check, dict):
            errors.append(f"{label} must be an object.")
            continue
        check_id = check.get("id")
        if not isinstance(check_id, str) or not QC_ID_PATTERN.fullmatch(check_id):
            errors.append(f"{label}.id must match {QC_ID_PATTERN.pattern!r}.")
        elif check_id in check_ids:
            errors.append(f"{label}.id is duplicated: {check_id}.")
        else:
            check_ids.add(check_id)
        status = check.get("status")
        evidence = check.get("evidence")
        if status not in QC_STATUS:
            errors.append(f"{label}.status must be one of {sorted(QC_STATUS)}.")
        if evidence not in SUPPORTED_EVIDENCE:
            errors.append(f"{label}.evidence must be one of {sorted(SUPPORTED_EVIDENCE)}.")
        if not _text(check.get("notes")):
            errors.append(f"{label}.notes must be a non-empty string.")
        if status in {"pass", "fail"}:
            decisive_count += 1
            if evidence != "observed":
                errors.append(f"{label} pass/fail status requires observed evidence.")
        if evidence == "observed":
            observed_count += 1
            if not artifact_available:
                errors.append(f"{label} cannot use observed evidence when artifact.available is false.")
        if status == "fail":
            failed_count += 1

    if overall_status in {"pass", "fail"}:
        if not artifact_available:
            errors.append("overall_status pass/fail requires artifact.available to be true.")
        if observed_count == 0 or decisive_count == 0:
            errors.append("overall_status pass/fail requires at least one observed pass/fail check.")
    if overall_status == "pass" and failed_count:
        errors.append("overall_status pass cannot contain a failed check.")
    if overall_status == "fail" and not failed_count:
        warnings.append("overall_status fail has no failed check; confirm the report summary.")

    for field_name in ("limitations", "source_shot_ids"):
        if field_name in report:
            _string_array(report[field_name], field_name, errors)

    summary = {
        "check_count": len(checks),
        "observed_check_count": observed_count,
        "failed_check_count": failed_count,
        "artifact_available": artifact_available,
        "overall_status": overall_status,
    }
    return ValidationResult(not errors, errors, warnings, summary)


def validate_qc_report_file(path: str | Path) -> ValidationResult:
    """Load and validate a QC report without inspecting the referenced media."""

    return validate_qc_report(load_json(path))
