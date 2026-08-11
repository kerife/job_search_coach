"""Content-bound provenance identifiers for private recruiter triage v2."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping


SNAPSHOT_PREFIX = "snap-triage-sha256-"
_SNAPSHOT = re.compile(r"snap-triage-sha256-[0-9a-f]{64}")


def _payload_without_snapshot_fields(triage: Mapping[str, object]) -> dict[str, object]:
    payload = copy.deepcopy(dict(triage))
    handoff = payload.get("handoff")
    if not isinstance(handoff, Mapping):
        return payload
    handoff_copy = dict(handoff)
    payload["handoff"] = handoff_copy
    for packet_name in ("packet", "reentry_packet"):
        packet = handoff_copy.get(packet_name)
        if isinstance(packet, Mapping):
            packet_copy = dict(packet)
            packet_copy.pop("source_snapshot", None)
            handoff_copy[packet_name] = packet_copy
    return payload


def snapshot_for_triage(triage: Mapping[str, object]) -> str:
    """Return the deterministic v2 snapshot for a JSON-like triage mapping."""

    payload = _payload_without_snapshot_fields(triage)
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"{SNAPSHOT_PREFIX}{hashlib.sha256(canonical).hexdigest()}"


def is_snapshot(value: object) -> bool:
    return isinstance(value, str) and _SNAPSHOT.fullmatch(value) is not None
