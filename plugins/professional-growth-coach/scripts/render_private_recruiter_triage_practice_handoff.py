#!/usr/bin/env python3
"""Render one validated private triage-practice handoff as offline HTML."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any


class HandoffRenderError(ValueError):
    """A private handoff cannot be rendered safely."""


class _ArgumentError(ValueError):
    pass


class _PrivateArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise _ArgumentError


@lru_cache(maxsize=None)
def _load_sibling(name: str) -> Any:
    path = Path(__file__).with_name(f"{name}.py")
    specification = importlib.util.spec_from_file_location(
        f"private_triage_handoff_renderer_{name}", path
    )
    if specification is None or specification.loader is None:
        raise RuntimeError("private renderer dependency is unavailable")
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    scripts_dir = str(path.parent)
    added_path = scripts_dir not in sys.path
    if added_path:
        sys.path.insert(0, scripts_dir)
    try:
        specification.loader.exec_module(module)
    finally:
        if added_path:
            sys.path.remove(scripts_dir)
    return module


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise HandoffRenderError("handoff is invalid")
    return value


def render_handoff_html(handoff: Mapping[str, object]) -> str:
    """Validate a closed wrapper then render only its in-memory session projection."""
    validator = _load_sibling("validate_private_recruiter_triage_practice_handoff")
    if validator.validate_handoff(handoff):
        raise HandoffRenderError("handoff validation failed")
    session = _mapping(handoff.get("practice_session"))
    delivery = _mapping(handoff.get("delivery"))
    renderer = _load_sibling("render_recruiter_practice_session")
    return renderer.render_session_html(session, handoff_delivery=delivery)


def write_handoff_html(handoff_path: Path, output_path: Path, *, force: bool = False) -> dict[str, object]:
    """Load, validate, project and atomically write one private HTML artifact."""
    validator = _load_sibling("validate_private_recruiter_triage_practice_handoff")
    try:
        handoff = validator.load_handoff(Path(handoff_path))
    except validator.HandoffLoadError as error:
        raise HandoffRenderError("handoff input is invalid") from error
    html = render_handoff_html(handoff)
    try:
        expanded = Path(output_path).expanduser()
    except RuntimeError as error:
        raise OSError("output path is unavailable") from error
    output = Path(os.path.abspath(os.fspath(expanded)))
    renderer = _load_sibling("render_recruiter_practice_session")
    renderer._atomic_private_write(output, html.encode("utf-8"), force=force)
    return {"artifact_type": "text/html", "schema_version": handoff["schema_version"]}


def _error(code: str) -> None:
    print(json.dumps({"error": {"code": code}}, separators=(",", ":")), file=sys.stderr)


def _cli(argv: list[str] | None = None) -> int:
    parser = _PrivateArgumentParser(description="Render a private triage practice handoff.")
    parser.add_argument("handoff", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    try:
        arguments = parser.parse_args(argv)
    except _ArgumentError:
        _error("invalid_arguments")
        return 3
    except SystemExit as error:
        return 0 if error.code == 0 else 3
    try:
        receipt = write_handoff_html(arguments.handoff, arguments.output, force=arguments.force)
    except HandoffRenderError:
        _error("invalid_input")
        return 2
    except FileExistsError:
        _error("output_exists")
        return 3
    except OSError:
        _error("unsafe_output")
        return 3
    print(json.dumps(receipt, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
