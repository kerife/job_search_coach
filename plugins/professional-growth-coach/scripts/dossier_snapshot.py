"""Canonical, content-bound identifiers for executive career dossiers."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping


SNAPSHOT_PATTERN = re.compile(r"snap-dossier-sha256-[0-9a-f]{64}\Z")


def snapshot_for_dossier(dossier: Mapping[str, object]) -> str:
    if not isinstance(dossier, Mapping):
        raise ValueError("dossier must be an object")
    canonical = json.dumps(
        dossier,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()
    return f"snap-dossier-sha256-{digest}"


def is_snapshot(value: object) -> bool:
    return isinstance(value, str) and SNAPSHOT_PATTERN.fullmatch(value) is not None
