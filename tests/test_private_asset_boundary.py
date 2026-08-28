from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts" / "private_asset_loader.py"
TRIAGE_RENDERER_PATH = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts" / "render_private_recruiter_reply_triage.py"
TRIAGE_FIXTURE = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "private-recruiter-reply-triage" / "ready-es.json"


def load_helper():
    specification = importlib.util.spec_from_file_location("private_asset_loader", HELPER_PATH)
    assert specification is not None and specification.loader is not None
    helper = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(helper)
    return helper


def load_triage_renderer():
    scripts_root = str(REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts")
    if scripts_root not in sys.path:
        sys.path.insert(0, scripts_root)
    specification = importlib.util.spec_from_file_location("asset_boundary_triage_renderer", TRIAGE_RENDERER_PATH)
    assert specification is not None and specification.loader is not None
    renderer = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = renderer
    specification.loader.exec_module(renderer)
    return renderer


class PrivateAssetBoundaryTests(unittest.TestCase):
    def test_asset_error_is_handled_as_file_io_failure(self) -> None:
        helper = load_helper()

        self.assertTrue(issubclass(helper.PrivateAssetError, OSError))

    def test_all_canonical_renderer_assets_pass_the_regular_file_boundary(self) -> None:
        helper = load_helper()

        self.assertEqual(
            [],
            helper.validate_asset_paths(REPO_ROOT / "plugins" / "professional-growth-coach"),
        )

    def test_regular_canonical_asset_is_read(self) -> None:
        helper = load_helper()

        content = helper.read_private_asset(
            REPO_ROOT / "plugins" / "professional-growth-coach",
            REPO_ROOT / "plugins" / "professional-growth-coach" / "assets" / "recruiter-practice-session-v1.css",
            "renderer asset",
        )

        self.assertIn("--paper", content)

    def test_dossier_market_css_extension_is_a_canonical_private_asset(self) -> None:
        helper = load_helper()
        for relative, marker in (
            ("assets/executive-career-dossier-v2.css", ".section-coverage-list"),
            ("assets/career-market-learning-dossier-v1.css", ".market-summary"),
        ):
            with self.subTest(relative=relative):
                self.assertIn(relative, helper.CANONICAL_RENDERER_ASSETS)
                content = helper.read_private_asset(
                    REPO_ROOT / "plugins" / "professional-growth-coach",
                    REPO_ROOT / "plugins" / "professional-growth-coach" / relative,
                )
                self.assertIn(marker, content)

    def test_direct_symlink_is_rejected_without_echoing_target(self) -> None:
        helper = load_helper()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "plugin"
            root.mkdir()
            external = Path(directory) / "external.css"
            external.write_text("EXTERNAL-ASSET-MARKER", encoding="utf-8")
            linked = root / "asset.css"
            linked.symlink_to(external)

            with self.assertRaisesRegex(helper.PrivateAssetError, "renderer asset input must be a regular file") as context:
                helper.read_private_asset(root, linked, "renderer asset")

        self.assertNotIn(str(external), str(context.exception))
        self.assertNotIn("EXTERNAL-ASSET-MARKER", str(context.exception))

    def test_intermediate_and_broken_symlinks_are_rejected(self) -> None:
        helper = load_helper()

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "plugin"
            root.mkdir()
            external_dir = base / "external-assets"
            external_dir.mkdir()
            (external_dir / "template.html").write_text("external", encoding="utf-8")
            (root / "assets").symlink_to(external_dir, target_is_directory=True)
            broken = root / "broken.css"
            broken.symlink_to(base / "missing.css")

            for candidate in (root / "assets" / "template.html", broken):
                with self.subTest(candidate=candidate):
                    with self.assertRaisesRegex(helper.PrivateAssetError, "renderer asset input must be a regular file"):
                        helper.read_private_asset(root, candidate, "renderer asset")

    def test_triage_renderer_rejects_symlinked_template_before_embedding_content(self) -> None:
        renderer = load_triage_renderer()
        triage = json.loads(TRIAGE_FIXTURE.read_text(encoding="utf-8"))
        original_template = renderer.TEMPLATE_PATH
        with tempfile.TemporaryDirectory() as directory:
            external = Path(directory) / "external.html"
            external.write_text("EXTERNAL-ASSET-MARKER", encoding="utf-8")
            renderer.TEMPLATE_PATH = Path(directory) / "template.html"
            renderer.TEMPLATE_PATH.symlink_to(external)
            try:
                with self.assertRaises(renderer.ASSET_LOADER.PrivateAssetError) as context:
                    renderer.render_triage_html(triage)
            finally:
                renderer.TEMPLATE_PATH = original_template

        self.assertNotIn("EXTERNAL-ASSET-MARKER", str(context.exception))

    def test_package_root_swap_after_preflight_fails_closed(self) -> None:
        helper = load_helper()
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "plugin"
            root.mkdir()
            (root / "assets").mkdir()
            (root / "assets" / "asset.css").write_text("SAFE-ASSET", encoding="utf-8")
            external = base / "external"
            external.mkdir()
            (external / "assets").mkdir()
            (external / "assets" / "asset.css").write_text("EXTERNAL-ASSET-MARKER", encoding="utf-8")
            original = helper._regular_package_path

            def swap_root(plugin_root: Path, asset_path: Path) -> Path:
                resolved = original(plugin_root, asset_path)
                backup = base / "plugin-original"
                os.rename(root, backup)
                os.rename(external, root)
                return resolved

            helper._regular_package_path = swap_root
            try:
                with self.assertRaises(helper.PrivateAssetError):
                    helper.read_private_asset(root, root / "assets" / "asset.css")
            finally:
                helper._regular_package_path = original

            self.assertEqual(
                "SAFE-ASSET",
                (base / "plugin-original" / "assets" / "asset.css").read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
