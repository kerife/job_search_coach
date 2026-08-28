#!/usr/bin/env python3
"""Validate the declared color family of each canonical offline artifact."""

from __future__ import annotations

import re
from pathlib import Path


HEX_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")

FAMILY_ASSETS = {
    "dossier": (
        "assets/executive-career-dossier-v1.css",
        "assets/executive-career-dossier-v2.css",
    ),
    "practice_triage": (
        "assets/recruiter-practice-session-v1.css",
        "assets/private-recruiter-reply-triage-v1.css",
    ),
    "compact_receipt": (
        "assets/private-recruiter-followthrough-checkpoint-v1.css",
        "assets/private-recruiter-conversion-outcome-v1.css",
    ),
    "recruiter_review": (
        "assets/recruiter-target-shortlist-v1.css",
        "assets/recruiter-target-decision-gate-v1.css",
        "assets/recruiter-target-screen-intake-v1.css",
        "assets/private-recruiter-screen-debrief-v1.css",
        "assets/private-recruiter-next-stage-review-v1.css",
    ),
}

FAMILY_COLORS = {
    "dossier": frozenset(
        {
            "#101521",
            "#173e30",
            "#1a1a1a",
            "#182235",
            "#223b35",
            "#39443f",
            "#3b301f",
            "#3f282d",
            "#4f5955",
            "#53605a",
            "#5d5a55",
            "#5f718e",
            "#654c10",
            "#7c2f1e",
            "#be9338",
            "#c8c0b5",
            "#d96c52",
            "#dce5e0",
            "#e2ddd6",
            "#8fc9b0",
            "#b8c4d8",
            "#f2c970",
            "#f3f6ff",
            "#f5ecd8",
            "#f6f4ee",
            "#f7e4df",
            "#ff9f8d",
            "#ffffff",
        }
    ),
    "practice_triage": frozenset(
        {
            "#101521",
            "#173e30",
            "#1b1c1a",
            "#182235",
            "#223b35",
            "#3b301f",
            "#3f282d",
            "#46534d",
            "#5f718e",
            "#5c4a12",
            "#854117",
            "#9fc4b4",
            "#8fc9b0",
            "#b8c7c0",
            "#b8c4d8",
            "#b9513a",
            "#dce5e0",
            "#dfbf70",
            "#f3f6ff",
            "#f5d68a",
            "#f5ecd8",
            "#f6e0da",
            "#f6f4ee",
            "#f7ecd5",
            "#f8f7f2",
            "#ff9f8d",
            "#ffffff",
        }
    ),
    "compact_receipt": frozenset(
        {
            "#101521",
            "#172033",
            "#182235",
            "#315bd6",
            "#52637d",
            "#536174",
            "#5f718e",
            "#8eb2ff",
            "#b8c4d8",
            "#d9dfeb",
            "#f3f6ff",
            "#f4f6fa",
            "#ffffff",
        }
    ),
    # The recruiter flow currently has five intentionally distinct legacy
    # surfaces; this shared family allowlist makes future additions fail
    # closed without silently dropping any existing token.
    "recruiter_review": frozenset(
        {
            "#000000",
            "#0b6477",
            "#101a35",
            "#101521",
            "#10171d",
            "#101820",
            "#10232a",
            "#111927",
            "#126782",
            "#157347",
            "#16202a",
            "#172033",
            "#17212b",
            "#176b4d",
            "#182235",
            "#18232d",
            "#1c2738",
            "#20313b",
            "#315bd6",
            "#3b4a55",
            "#40515e",
            "#52606d",
            "#536174",
            "#536176",
            "#5c6975",
            "#5f718e",
            "#69d39a",
            "#7057a2",
            "#75d2e4",
            "#76c7dc",
            "#8a4b08",
            "#8a5a00",
            "#8eb2ff",
            "#9a6700",
            "#a43d3d",
            "#adbac4",
            "#b42318",
            "#b4c0ca",
            "#b8c4d8",
            "#b9c5d8",
            "#c5a7f4",
            "#c7d2e5",
            "#c8d2dc",
            "#cbd5dc",
            "#d9dfeb",
            "#e7bd65",
            "#ecf2f6",
            "#edf2fa",
            "#eef3f7",
            "#f3f6fb",
            "#f3f6ff",
            "#f4f6fa",
            "#f5f7f8",
            "#f5f7fa",
            "#ff938a",
            "#ff8f8f",
            "#ffc078",
            "#ffffff",
        }
    ),
}


def normalize_hex(value: str) -> str:
    value = value.lower()
    if len(value) == 4:
        return "#" + "".join(char * 2 for char in value[1:])
    return value


def validate_css_text(css: str, family: str, asset_name: str) -> list[str]:
    allowed = FAMILY_COLORS[family]
    return [
        f"{family} {asset_name} uses unapproved color {color}"
        for color in sorted({normalize_hex(match) for match in HEX_COLOR.findall(css)} - allowed)
    ]


def validate_palette_assets(plugin_root: Path) -> list[str]:
    errors: list[str] = []
    for family, assets in FAMILY_ASSETS.items():
        for relative in assets:
            path = plugin_root / relative
            if not path.is_file():
                errors.append(f"{family} {relative} is missing")
                continue
            errors.extend(validate_css_text(path.read_text(encoding="utf-8"), family, relative))
    return errors


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    problems = validate_palette_assets(root)
    for problem in problems:
        print(problem)
    raise SystemExit(1 if problems else 0)
