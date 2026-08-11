"""Acceptance contract for the Professional Growth Coach migration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "professional-growth-coach"
MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
EXPECTED_SKILLS = (
    "professional-growth-coach",
    "optimize-professional-profile",
    "explore-career-options",
    "research-professional-market",
    "optimize-career-assets",
    "prepare-role-interviews",
    "recommend-career-learning",
    "track-career-outcomes",
)


class ProfessionalGrowthContractTests(unittest.TestCase):
    def test_manifest_and_marketplace_use_the_new_identity(self) -> None:
        self.assertTrue(MANIFEST.is_file(), f"missing manifest: {MANIFEST}")
        self.assertTrue(MARKETPLACE.is_file(), f"missing marketplace: {MARKETPLACE}")

        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        marketplace = json.loads(MARKETPLACE.read_text(encoding="utf-8"))

        self.assertEqual(manifest["name"], "professional-growth-coach")
        self.assertEqual(manifest["interface"]["displayName"], "Professional Growth Coach")
        self.assertEqual(marketplace["name"], "professional-growth-coach-local")
        self.assertEqual(marketplace["plugins"][0]["name"], "professional-growth-coach")
        self.assertEqual(
            marketplace["plugins"][0]["source"]["path"],
            "./plugins/professional-growth-coach",
        )

    def test_active_skill_inventory_uses_growth_names(self) -> None:
        self.assertTrue((PLUGIN_ROOT / "skills").is_dir())
        discovered = tuple(sorted(path.name for path in (PLUGIN_ROOT / "skills").iterdir()))
        self.assertEqual(discovered, tuple(sorted(EXPECTED_SKILLS)))

    def test_workplace_continuity_boundary_is_explicit(self) -> None:
        active_files = (
            PLUGIN_ROOT / "README.md",
            PLUGIN_ROOT / "skills" / "professional-growth-coach" / "SKILL.md",
            PLUGIN_ROOT / "skills" / "explore-career-options" / "SKILL.md",
            PLUGIN_ROOT
            / "skills"
            / "explore-career-options"
            / "references"
            / "path-scoring.md",
            PLUGIN_ROOT
            / "skills"
            / "professional-growth-coach"
            / "references"
            / "routing.md",
        )
        for path in active_files:
            self.assertTrue(path.is_file(), f"missing active contract file: {path}")
        combined = "\n".join(path.read_text(encoding="utf-8") for path in active_files)
        for marker in (
            "preserve_current_employment_by_default",
            "no_resignation_recommendation=true",
            "staying_and_growing_is_valid",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, combined)

    def test_python311_can_import_the_linkedin_validator(self) -> None:
        locked_python = REPO_ROOT / ".release-validation-venv" / "bin" / "python"
        self.assertTrue(locked_python.is_file(), f"missing locked interpreter: {locked_python}")
        scripts = PLUGIN_ROOT / "scripts"
        result = subprocess.run(
            [
                str(locked_python),
                "-B",
                "-c",
                "import validate_linkedin_client_report",
            ],
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONPATH": str(scripts)},
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_active_marketplace_has_no_legacy_identity(self) -> None:
        active = "\n".join(
            path.read_text(encoding="utf-8")
            for path in (MARKETPLACE, MANIFEST)
            if path.is_file()
        )
        self.assertNotIn("job-search-coach-local", active)
        self.assertNotIn('"job-search-coach"', active)


if __name__ == "__main__":
    unittest.main()
