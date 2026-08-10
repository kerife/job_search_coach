#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
FINAL_VENV="$PROJECT_ROOT/.release-validation-venv"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements/release-validation.txt"
PYTHON_311="${PYTHON_311:-python3.11}"
EXPECTED_REQUIREMENT="PyYAML==6.0.3 --hash=sha256:652cb6edd41e718550aad172851962662ff2681490a8a711af6a4d288dd96824"
BUILD_VENV=""
ROLLBACK_ROOT=""
ROLLBACK_VENV=""

cleanup() {
  if [[ -n "$BUILD_VENV" && -d "$BUILD_VENV" ]]; then
    rm -rf "$BUILD_VENV"
  fi
  if [[ -n "$ROLLBACK_ROOT" && -d "$ROLLBACK_ROOT" ]]; then
    if [[ -n "$ROLLBACK_VENV" && -d "$ROLLBACK_VENV" && ! -e "$FINAL_VENV" ]]; then
      mv "$ROLLBACK_VENV" "$FINAL_VENV"
    fi
    rm -rf "$ROLLBACK_ROOT"
  fi
}
trap cleanup EXIT HUP INT TERM

if [[ ! -f "$REQUIREMENTS_FILE" ]]; then
  echo "RELEASE_REQUIREMENT_MISSING" >&2
  exit 1
fi
IFS= read -r actual_requirement < "$REQUIREMENTS_FILE"
if [[ "$actual_requirement" != "$EXPECTED_REQUIREMENT" ]] || [[ "$(wc -l < "$REQUIREMENTS_FILE" | tr -d ' ')" != "1" ]]; then
  echo "RELEASE_REQUIREMENT_MISMATCH" >&2
  exit 1
fi
if ! command -v "$PYTHON_311" >/dev/null 2>&1; then
  echo "release validation requires CPython 3.11.15" >&2
  exit 1
fi

"$PYTHON_311" -B -c \
  'import platform, sys; assert platform.python_implementation() == "CPython"; assert sys.version_info[:3] == (3, 11, 15); assert sys.platform == "darwin"; assert platform.machine() == "arm64"'

BUILD_VENV="$(mktemp -d "${FINAL_VENV}.build.XXXXXX")"
"$PYTHON_311" -m venv "$BUILD_VENV"
"$BUILD_VENV/bin/python" -m pip install \
  --disable-pip-version-check \
  --require-hashes \
  --only-binary=:all: \
  --no-deps \
  -r "$REQUIREMENTS_FILE"

VALIDATION_VENV="$BUILD_VENV" "$BUILD_VENV/bin/python" -B -c \
  'import os, platform, sys, yaml; from pathlib import Path; root = Path(os.environ["VALIDATION_VENV"]).resolve(); assert platform.python_implementation() == "CPython"; assert sys.version_info[:3] == (3, 11, 15); assert sys.platform == "darwin"; assert platform.machine() == "arm64"; assert yaml.__version__ == "6.0.3"; assert Path(yaml.__file__).resolve().is_relative_to(root)'

if [[ -e "$FINAL_VENV" ]]; then
  ROLLBACK_ROOT="$(mktemp -d "${FINAL_VENV}.rollback.XXXXXX")"
  ROLLBACK_VENV="$ROLLBACK_ROOT/previous"
  mv "$FINAL_VENV" "$ROLLBACK_VENV"
fi
if ! mv "$BUILD_VENV" "$FINAL_VENV"; then
  if [[ -n "$ROLLBACK_VENV" && -d "$ROLLBACK_VENV" ]]; then
    mv "$ROLLBACK_VENV" "$FINAL_VENV"
    ROLLBACK_VENV=""
    rmdir "$ROLLBACK_ROOT"
    ROLLBACK_ROOT=""
  fi
  exit 1
fi
BUILD_VENV=""
if [[ -n "$ROLLBACK_ROOT" && -d "$ROLLBACK_ROOT" ]]; then
  rm -rf "$ROLLBACK_ROOT"
  ROLLBACK_ROOT=""
  ROLLBACK_VENV=""
fi
