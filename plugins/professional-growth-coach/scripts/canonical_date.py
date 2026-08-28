"""Strict calendar-date parsing shared by recruiter review contracts."""

from __future__ import annotations

import datetime as dt
import re


_DATE_PATTERN = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")


def parse_canonical_date(value: object, *, field: str = "date") -> dt.date:
    """Parse only the contract's canonical YYYY-MM-DD representation."""
    if not isinstance(value, str) or not _DATE_PATTERN.fullmatch(value):
        raise ValueError(f"{field} must be an ISO date")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO date") from error
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be an ISO date")
    return parsed


def date_arg(value: str) -> dt.date:
    """argparse adapter that preserves a stable diagnostic for --as-of."""
    return parse_canonical_date(value, field="--as-of")
