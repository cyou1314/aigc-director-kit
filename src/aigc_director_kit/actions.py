"""License-neutral action catalog search and bounded request compilation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def load_action_library(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8-sig") as handle:
        library = json.load(handle)
    if not isinstance(library, dict):
        raise ValueError("The action library root must be a JSON object.")
    if library.get("contract") != "aigc-director-action-library" or library.get("version") != 1:
        raise ValueError("Action library must use aigc-director-action-library version 1.")
    actions = library.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ValueError("Action library must contain a non-empty actions array.")
    ids: set[str] = set()
    for index, action in enumerate(actions):
        label = f"actions[{index}]"
        if not isinstance(action, dict):
            raise ValueError(f"{label} must be an object.")
        action_id = action.get("id")
        if not isinstance(action_id, str) or not action_id.strip():
            raise ValueError(f"{label}.id must be a non-empty string.")
        if action_id in ids:
            raise ValueError(f"Duplicate action id: {action_id}.")
        ids.add(action_id)
        if not isinstance(action.get("display_name"), str) or not action["display_name"].strip():
            raise ValueError(f"{label}.display_name must be a non-empty string.")
        if not isinstance(action.get("duration_s"), (int, float)) or action["duration_s"] <= 0:
            raise ValueError(f"{label}.duration_s must be positive.")
        for key in ("aliases", "tags"):
            if key in action and (
                not isinstance(action[key], list) or any(not isinstance(item, str) for item in action[key])
            ):
                raise ValueError(f"{label}.{key} must be a string array.")
    return library


def _phrases(action: dict[str, Any]) -> list[str]:
    values = [
        str(action.get("id", "")),
        str(action.get("display_name", "")),
        *[str(value) for value in action.get("aliases", [])],
    ]
    return sorted({value for value in values if value}, key=lambda value: (-len(value), value))


def list_actions(
    library: dict[str, Any],
    query: str = "",
    *,
    category: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search action ids, names, aliases and tags without inventing matches."""

    if limit < 1:
        raise ValueError("limit must be positive.")
    needle = query.casefold().strip()
    selected: list[dict[str, Any]] = []
    for action in library.get("actions", []):
        if category and action.get("category") != category:
            continue
        searchable = [
            str(action.get("id", "")),
            str(action.get("display_name", "")),
            *[str(value) for value in action.get("aliases", [])],
            *[str(value) for value in action.get("tags", [])],
        ]
        if needle and not any(needle in value.casefold() for value in searchable):
            continue
        selected.append(
            {
                "id": action["id"],
                "display_name": action.get("display_name", action["id"]),
                "category": action.get("category", "uncategorized"),
                "duration_s": action.get("duration_s"),
                "aliases": list(action.get("aliases", [])),
                "tags": list(action.get("tags", [])),
            }
        )
        if len(selected) >= limit:
            break
    return selected


def _match_actions(text: str, library: dict[str, Any]) -> list[dict[str, Any]]:
    folded = text.casefold()
    candidates: list[dict[str, Any]] = []
    for catalog_index, action in enumerate(library.get("actions", [])):
        for phrase in _phrases(action):
            start = folded.find(phrase.casefold())
            if start < 0:
                continue
            candidates.append(
                {
                    "id": action["id"],
                    "display_name": action.get("display_name", action["id"]),
                    "position": start,
                    "end": start + len(phrase),
                    "matched_phrase": phrase,
                    "entry": action,
                    "catalog_index": catalog_index,
                }
            )
    candidates.sort(
        key=lambda item: (
            item["position"],
            -(item["end"] - item["position"]),
            item["catalog_index"],
        )
    )
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    occupied: list[tuple[int, int]] = []
    for candidate in candidates:
        if candidate["id"] in selected_ids:
            continue
        start, end = candidate["position"], candidate["end"]
        if any(start < other_end and other_start < end for other_start, other_end in occupied):
            continue
        selected.append(candidate)
        selected_ids.add(candidate["id"])
        occupied.append((start, end))
    return sorted(selected, key=lambda item: (item["position"], item["catalog_index"]))


def _parse_speed(text: str) -> tuple[float, list[str]]:
    notes: list[str] = []
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:倍|x)", text, re.IGNORECASE)
    if match:
        speed = float(match.group(1))
        if speed <= 0:
            raise ValueError("speed multiplier must be positive.")
        notes.append(f"explicit {speed:g}x speed")
        return speed, notes
    if any(token in text for token in ("慢速", "缓慢", "慢一点", "slow")):
        notes.append("slow modifier -> 0.8x")
        return 0.8, notes
    if any(token in text for token in ("快速", "迅速", "快一点", "fast")):
        notes.append("fast modifier -> 1.25x")
        return 1.25, notes
    return 1.0, notes


def _parse_blend(text: str) -> float:
    match = re.search(r"(?:过渡|衔接|融合|blend)\s*(\d+(?:\.\d+)?)\s*(?:秒|s)", text, re.IGNORECASE)
    return float(match.group(1)) if match else 0.35


def compile_action_request(text: str, library: dict[str, Any], output_fps: float = 24.0) -> dict[str, Any]:
    """Compile a request into known action ids and explicit modifiers."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a non-empty string.")
    if not isinstance(output_fps, (int, float)) or output_fps <= 0:
        raise ValueError("output_fps must be positive.")
    matches = _match_actions(text, library)
    available = [
        {"id": action["id"], "display_name": action.get("display_name", action["id"])}
        for action in library.get("actions", [])
    ]
    if not matches:
        return {
            "contract": "aigc-director-action-request",
            "version": 1,
            "valid": False,
            "input": text,
            "error": "No supported action was matched; no motion was invented.",
            "available_actions": available,
        }

    speed, notes = _parse_speed(text)
    strength = 0.65 if any(token in text for token in ("轻微", "小幅", "幅度小")) else 1.0
    blend_s = _parse_blend(text)
    in_place = any(token in text for token in ("原地", "in place", "in-place"))
    sequence: list[dict[str, Any]] = []
    duration_s = 0.0
    for index, match in enumerate(matches):
        action = match["entry"]
        action_duration = float(action["duration_s"]) / speed
        transition = 0.0 if index == 0 else min(blend_s, action_duration / 2)
        duration_s += action_duration - transition
        sequence.append(
            {
                "id": match["id"],
                "display_name": match["display_name"],
                "matched_phrase": match["matched_phrase"],
                "time_scale": speed,
                "strength": strength,
                "blend_s": transition,
                "root_motion_scale": 0.0 if in_place else 1.0,
            }
        )

    return {
        "contract": "aigc-director-action-request",
        "version": 1,
        "valid": True,
        "input": text,
        "matched_actions": sequence,
        "modifiers": {
            "speed_scale": speed,
            "strength": strength,
            "blend_s": blend_s,
            "in_place": in_place,
            "notes": notes,
        },
        "duration_s": round(max(duration_s, 0.0), 6),
        "output_fps": float(output_fps),
        "confidence": "high",
        "boundaries": [
            "Only actions already present in the supplied catalog are selected.",
            "No missing choreography, contacts, facial acting, or camera movement is invented.",
            "A runtime adapter must map action ids to actual motion assets separately.",
        ],
    }
