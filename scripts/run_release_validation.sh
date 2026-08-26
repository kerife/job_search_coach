#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd -P)"
SYSTEM_SKILLS_ROOT="${CODEX_SYSTEM_SKILLS_ROOT:-${CODEX_HOME:-$HOME/.codex}/skills/.system}"
VALIDATION_PYTHON="${VALIDATION_PYTHON:-$PROJECT_ROOT/.release-validation-venv/bin/python}"
SKILL_VALIDATOR_PATH="${SKILL_VALIDATOR_PATH:-$SYSTEM_SKILLS_ROOT/skill-creator/scripts/quick_validate.py}"
PLUGIN_VALIDATOR_PATH="${PLUGIN_VALIDATOR_PATH:-$SYSTEM_SKILLS_ROOT/plugin-creator/scripts/validate_plugin.py}"
SOURCE_PLUGIN_ROOT="${SOURCE_PLUGIN_ROOT:-$PROJECT_ROOT/plugins/professional-growth-coach}"
LINKEDIN_SKILL_ROOT="${LINKEDIN_SKILL_ROOT:-$SOURCE_PLUGIN_ROOT/skills/optimize-professional-profile}"
EXPECTED_SKILL_SHA256="1fd66498c219616fd9249eacdf16c458412ea9065a9d887fd716aeef03907762"
EXPECTED_PLUGIN_SHA256="6ff4bc1cc8ca94827c30c8299951efdac900ff38a5069c03e9a6554fc194a723"

for required_path in "$VALIDATION_PYTHON" "$SKILL_VALIDATOR_PATH" "$PLUGIN_VALIDATOR_PATH"; do
  if [[ ! -f "$required_path" ]]; then
    echo "RELEASE_VALIDATION_INPUT_MISSING" >&2
    exit 1
  fi
done

actual_skill_sha="$(shasum -a 256 "$SKILL_VALIDATOR_PATH" | awk '{print $1}')"
actual_plugin_sha="$(shasum -a 256 "$PLUGIN_VALIDATOR_PATH" | awk '{print $1}')"
if [[ "$actual_skill_sha" != "$EXPECTED_SKILL_SHA256" ]]; then
  echo "VALIDATOR_CHECKSUM_MISMATCH: quick_validate.py" >&2
  exit 1
fi
if [[ "$actual_plugin_sha" != "$EXPECTED_PLUGIN_SHA256" ]]; then
  echo "VALIDATOR_CHECKSUM_MISMATCH: validate_plugin.py" >&2
  exit 1
fi

VALIDATION_VENV="$(cd "$(dirname "$VALIDATION_PYTHON")/.." && pwd -P)"
VALIDATION_VENV="$VALIDATION_VENV" "$VALIDATION_PYTHON" -B -c \
  'import os, platform, sys, yaml; from pathlib import Path; root = Path(os.environ["VALIDATION_VENV"]).resolve(); assert platform.python_implementation() == "CPython"; assert sys.version_info[:3] == (3, 11, 15); assert sys.platform == "darwin"; assert platform.machine() == "arm64"; assert yaml.__version__ == "6.0.3"; assert Path(yaml.__file__).resolve().is_relative_to(root)'

"$VALIDATION_PYTHON" -B "$SKILL_VALIDATOR_PATH" "$LINKEDIN_SKILL_ROOT"
PYTHONDONTWRITEBYTECODE=1 "$VALIDATION_PYTHON" -B "$PLUGIN_VALIDATOR_PATH" "$SOURCE_PLUGIN_ROOT"
