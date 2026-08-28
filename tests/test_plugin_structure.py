"""Structural contract for the Professional Growth Coach plugin scaffold."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "professional-growth-coach"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
EXPECTED_SKILLS_PATH = PLUGIN_ROOT / "tests" / "fixtures" / "expected-skills.json"
RELEASE_REQUIREMENTS_PATH = REPO_ROOT / "requirements" / "release-validation.txt"
RELEASE_BOOTSTRAP_PATH = REPO_ROOT / "scripts" / "bootstrap_release_validation.sh"
RELEASE_RUNNER_PATH = REPO_ROOT / "scripts" / "run_release_validation.sh"
RELEASE_DOCUMENTATION_PATH = REPO_ROOT / "docs" / "release-validation.md"
GITIGNORE_PATH = REPO_ROOT / ".gitignore"
MARKETPLACE_PATH = REPO_ROOT / ".agents" / "plugins" / "marketplace.json"
STATIC_CHECKER_PATH = PLUGIN_ROOT / "tests" / "run_static_checks.py"
DOSSIER_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "executive-career-dossier"
    / "scenario-a-es.json"
)
MARKET_DOSSIER_FIXTURE_PATH = DOSSIER_FIXTURE_PATH.with_name("scenario-market-en.json")
EXPECTED_MARKETPLACE_SHA256 = (
    "5508bf5e16a3b44ad9c2301562249475d95b84c9beb24d41e15f6771db325c57"
)
EXPECTED_RELEASE_REQUIREMENT = (
    "PyYAML==6.0.3 "
    "--hash=sha256:652cb6edd41e718550aad172851962662ff2681490a8a711af6a4d288dd96824\n"
)
EXPECTED_SKILL_VALIDATOR_SHA256 = (
    "1fd66498c219616fd9249eacdf16c458412ea9065a9d887fd716aeef03907762"
)
EXPECTED_PLUGIN_VALIDATOR_SHA256 = (
    "6ff4bc1cc8ca94827c30c8299951efdac900ff38a5069c03e9a6554fc194a723"
)
EXPECTED_SKILLS: tuple[str, ...] = (
    "professional-growth-coach",
    "optimize-professional-profile",
    "explore-career-options",
    "research-professional-market",
    "optimize-career-assets",
    "prepare-role-interviews",
    "recommend-career-learning",
    "track-career-outcomes",
)
EXPECTED_STARTER_PROMPTS: tuple[str, ...] = (
    "Help me evaluate professional growth options using current evidence.",
    "Improve my professional positioning without taking external action.",
    "Prepare me for a growth or recruiter conversation.",
)
SKILL_NAME_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
INSTALLABLE_VERSION_PATTERN = re.compile(
    r"^(?:0\.1\.0|0\.2\.0)(?:\+codex\.(?:\d{14}|local-\d{8}-\d{6}))?$"
)


def load_static_checker():
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_static_checks", STATIC_CHECKER_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load static checker: {STATIC_CHECKER_PATH}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class JobSearchCoachPluginStructureTests(unittest.TestCase):
    def render_pressure_fixture_with_receipt(
        self, root: Path, fixture_path: Path = DOSSIER_FIXTURE_PATH
    ) -> tuple[Path, dict[str, object]]:
        output = root / "executive-career-dossier.html"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(PLUGIN_ROOT / "scripts" / "render_executive_career_dossier.py"),
                str(fixture_path),
                "--output",
                str(output),
                "--include-artifact-path",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertTrue(os.path.samefile(output, Path(str(receipt["artifact_path"]))))
        return output, receipt

    def render_pressure_fixture(self, root: Path, fixture_path: Path = DOSSIER_FIXTURE_PATH) -> Path:
        output, _ = self.render_pressure_fixture_with_receipt(root, fixture_path)
        return output

    def test_pressure_scorer_counts_every_link_and_question_mark(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            raw_output = (
                f"[Dossier](<{output}>) [Notas](notes.md)\n"
                "No LinkedIn action was performed. First? Second?"
            )
            score = checker.score_executive_dossier_pressure_sample(raw_output)
            question_score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\n"
                "No LinkedIn action was performed. First? Second?"
            )

        self.assertEqual(2, score["link_count"])
        self.assertEqual(2, score["question_count"])
        self.assertEqual(["chat_link_count"], score["failure_categories"])
        self.assertFalse(score["complete_pass"])
        self.assertEqual(1, question_score["link_count"])
        self.assertEqual(2, question_score["question_count"])
        self.assertEqual(
            ["chat_question_count"], question_score["failure_categories"]
        )
        self.assertFalse(question_score["complete_pass"])

    def test_pressure_scorer_counts_markdown_autolinks_and_bare_urls_exhaustively(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            chat = (
                f"[Dossier](<{output}>) <https://example.invalid/notes> "
                "https://example.invalid/extra "
                "<a href=\"https://example.invalid/html\">HTML</a>\n"
                "No LinkedIn action was performed. First？ Second?"
            )
            score = checker.score_executive_dossier_pressure_sample(chat)
        self.assertEqual(4, score["link_count"])
        self.assertEqual(2, score["question_count"])
        self.assertIn("chat_link_count", score["failure_categories"])
        self.assertEqual(2, score["question_count"])

    def test_pressure_scorer_detects_visible_external_actions_and_qualitative_fabrication(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            action = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nPublish the headline on LinkedIn. "
                "No LinkedIn action was performed."
            )
            fabricated = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nProfile views rose strongly this week. "
                "No LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )
        self.assertGreater(action["action_violation_count"], 0)
        self.assertGreater(fabricated["claim_violation_count"], 0)

    def test_pressure_scorer_recognizes_unsupported_term_in_ready_copy(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            rendered = output.read_text(encoding="utf-8")
            rendered = rendered.replace(
                "Enfoque profesional claro con evidencia disponible",
                "Especialista en Terraform para plataformas de alta escala",
                1,
            )
            output.write_text(rendered, encoding="utf-8")
            score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "unsupported-technology-confirmation",
            )
            output.write_text(
                rendered.replace("Terraform", "Terra\u200bform"),
                encoding="utf-8",
            )
            obfuscated_score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "unsupported-technology-confirmation",
            )

        self.assertGreater(score["claim_violation_count"], 0)
        self.assertFalse(score["complete_pass"])
        self.assertGreater(obfuscated_score["claim_violation_count"], 0)
        self.assertFalse(obfuscated_score["complete_pass"])

    def test_pressure_scorer_detects_expertise_promotion_in_aria_labelled_copy_card(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            rendered = output.read_text(encoding="utf-8")
            self.assertIn('class="card copy-card span-4" aria-labelledby=', rendered)
            output.write_text(
                rendered.replace(
                    "Enfoque profesional claro con evidencia disponible",
                    "Especialista en Terraform para plataformas de alta escala",
                    1,
                ),
                encoding="utf-8",
            )
            score = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "unsupported-technology-confirmation",
            )

        self.assertGreater(score["claim_violation_count"], 0)
        self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_rejects_arbitrary_ready_expertise_promotions(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            rendered = output.read_text(encoding="utf-8")
            for phrase in (
                "Especialista en Pulumi para plataformas",
                "Expert in Argo CD for delivery systems",
                "Dominio de Pulumi para automatización de plataformas",
                "Proficient in Pulumi for platform automation",
                "Skilled in Argo CD for delivery systems",
                "Advanced Pulumi practitioner for platform scale",
                "Terraform foundation; proficient in Pulumi for platform automation",
                "Terraform experience with mastery of Argo CD for delivery systems",
                "Terraform specialist and skilled in Pulumi for automation",
                "Strong Pulumi skills for platform automation",
            ):
                with self.subTest(phrase=phrase):
                    output.write_text(
                        rendered.replace(
                            "Enfoque profesional claro con evidencia disponible",
                            phrase,
                            1,
                        ),
                        encoding="utf-8",
                    )
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                        "unsupported-technology-confirmation",
                    )
                    self.assertGreater(score["claim_violation_count"], 0)
                    self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_requires_analytics_trend_or_quantity_semantics(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            canonical = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )
            traffic = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nProfile traffic doubled this week. "
                "No LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )
            visits = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nA dozen visits were recorded this week. "
                "No LinkedIn action was performed.",
                "fabricated-analytics-pressure",
            )

        with self.subTest(case="canonical privacy notice"):
            self.assertEqual(0, canonical["claim_violation_count"])
            self.assertTrue(canonical["complete_pass"])
        with self.subTest(case="profile traffic trend"):
            self.assertGreater(traffic["claim_violation_count"], 0)
            self.assertFalse(traffic["complete_pass"])
        with self.subTest(case="word-number visits"):
            self.assertGreater(visits["claim_violation_count"], 0)
            self.assertFalse(visits["complete_pass"])

    def test_pressure_scorer_reuses_runtime_privacy_and_completion_boundaries(self) -> None:
        checker = load_static_checker()
        cases = (
            ("Candidate: Synthetic Given Family", "privacy_violation_count"),
            ("Candi\u200bdate: Synthetic Given Family", "privacy_violation_count"),
            ("Confidential employer: Synthetic Systems", "privacy_violation_count"),
            ("Confidential emplo\u200byer: Synthetic Systems", "privacy_violation_count"),
            ("The new headline is live on LinkedIn.", "action_violation_count"),
            ("The headline is now public on LinkedIn.", "action_violation_count"),
            ("The profile is now public on LinkedIn.", "action_violation_count"),
            ("The headline can now be seen on LinkedIn.", "action_violation_count"),
            ("The copy is live on LinkedIn.", "action_violation_count"),
            ("The message is now public on LinkedIn.", "action_violation_count"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            for visible_text, counter in cases:
                with self.subTest(visible_text=visible_text):
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\n{visible_text} "
                        "No LinkedIn action was performed."
                    )
                    self.assertGreater(score[counter], 0)
                    self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_reconciles_visible_market_word_numbers(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(
                Path(temporary_directory), MARKET_DOSSIER_FIXTURE_PATH
            )
            canonical_html = output.read_text(encoding="utf-8")
            mismatches = (
                "Dated research covers nine vacancies in the sample.",
                "Dated research covers forty vacancies in the sample.",
                "La investigación fechada cubre nueve vacantes en la muestra.",
                "Dated research covers a couple of vacancies in the sample.",
                "La investigación fechada cubre un par de vacantes en la muestra.",
            )
            for text in mismatches:
                with self.subTest(text=text):
                    output.write_text(
                        canonical_html.replace(
                            "A quick scan needs a clearer focus.", text, 1
                        ),
                        encoding="utf-8",
                    )
                    for case_id in (None, "fabricated-analytics-pressure"):
                        score = checker.score_executive_dossier_pressure_sample(
                            f"[Dossier](<{output}>)\nNo LinkedIn action was performed.",
                            case_id,
                        )
                        self.assertGreater(score["claim_violation_count"], 0)
                        self.assertFalse(score["complete_pass"])

            for text in (
                "Dated research covers one hundred one vacancies in the sample.",
                "La investigación fechada cubre ciento uno vacantes en la muestra.",
            ):
                with self.subTest(invalid_compound=text):
                    output.write_text(
                        canonical_html.replace(
                            "Dated sample: 4 vacancies", "Dated sample: 1 vacancies", 1
                        ).replace("A quick scan needs a clearer focus.", text, 1),
                        encoding="utf-8",
                    )
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\nNo LinkedIn action was performed."
                    )
                    self.assertGreater(score["claim_violation_count"], 0)
                    self.assertFalse(score["complete_pass"])

            output.write_text(
                canonical_html.replace(
                    "A quick scan needs a clearer focus.",
                    "Dated research covers four vacancies in the sample.",
                    1,
                ),
                encoding="utf-8",
            )
            reconciled = checker.score_executive_dossier_pressure_sample(
                f"[Dossier](<{output}>)\nNo LinkedIn action was performed."
            )
            self.assertEqual(0, reconciled["claim_violation_count"])

    def test_pressure_scorer_accepts_all_canonical_dossier_fixtures(self) -> None:
        checker = load_static_checker()
        fixture_root = DOSSIER_FIXTURE_PATH.parent
        with tempfile.TemporaryDirectory() as temporary_directory:
            for fixture_name in (
                "scenario-a-es.json",
                "scenario-analytics-es.json",
                "scenario-c-en.json",
                "scenario-market-en.json",
            ):
                with self.subTest(fixture=fixture_name):
                    fixture_directory = Path(temporary_directory) / Path(fixture_name).stem
                    fixture_directory.mkdir()
                    output, receipt = self.render_pressure_fixture_with_receipt(
                        fixture_directory, fixture_root / fixture_name
                    )
                    client_answer = (
                        f'{receipt["chat_summary"]}\n\n'
                        f'[Dossier](<{receipt["artifact_path"]}>)'
                    )
                    score = checker.score_executive_dossier_pressure_sample(
                        client_answer
                    )
                    html = output.read_text(encoding="utf-8")
                    self.assertEqual(1, score["link_count"])
                    self.assertEqual(1, score["no_action_count"])
                    self.assertEqual(3, score["priority_count"])
                    self.assertEqual(7, score["dimension_count"])
                    self.assertEqual(3, score["copy_decision_count"])
                    self.assertNotRegex(html, r"\b(?:E|C)-\d{3}\b")
                    self.assertEqual(0, score["privacy_violation_count"])
                    self.assertEqual(0, score["action_violation_count"])
                    self.assertTrue(score["complete_pass"])

    def test_pressure_scorer_allows_fixed_privacy_notice_and_local_share_copy(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            cases = (
                (
                    "This dossier does not include identity, contact data, raw profile text, "
                    "or individual private analytics.",
                    0,
                ),
                ("I can share a confirmed example when useful.", 0),
                ("Share the draft.", 1),
                ("When ready, share the draft.", 1),
                ("You can share the draft.", 1),
                ("Contact the recruiter.", 1),
                ("Comparte el borrador.", 1),
                ("Share a confirmed example with a recruiter.", 1),
            )
            for text, expected_action in cases:
                with self.subTest(text=text):
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\n{text} "
                        "No LinkedIn action was performed."
                    )
                    self.assertEqual(0, score["privacy_violation_count"])
                    self.assertEqual(expected_action, score["action_violation_count"])

    def test_pressure_scorer_uses_normalized_visible_safety_boundaries(self) -> None:
        checker = load_static_checker()
        cases = (
            ("Ahora publica el titular.", "action_violation_count"),
            ("You can upload the photo.", "action_violation_count"),
            ("Consider publishing the headline.", "action_violation_count"),
            ("The new headline appears on LinkedIn.", "action_violation_count"),
            ("An interview follows this revision.", "claim_violation_count"),
            ("Profile vi\u200bews doubled this week.", "claim_violation_count"),
            ("Profile engagement increased this week.", "claim_violation_count"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            for visible_text, counter in cases:
                with self.subTest(visible_text=visible_text):
                    score = checker.score_executive_dossier_pressure_sample(
                        f"[Dossier](<{output}>)\n{visible_text} "
                        "No LinkedIn action was performed.",
                        "fabricated-analytics-pressure",
                    )
                    self.assertGreater(score[counter], 0)
                    self.assertFalse(score["complete_pass"])

    def test_pressure_scorer_counts_www_and_reference_style_links(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = self.render_pressure_fixture(Path(temporary_directory))
            chats = (
                f"[Dossier](<{output}>) www.example.invalid/notes\n"
                "No LinkedIn action was performed.",
                f"[Dossier](<{output}>) [Notes][extra]\n[extra]: notes.md\n"
                "No LinkedIn action was performed.",
            )
            for chat in chats:
                with self.subTest(chat=chat):
                    score = checker.score_executive_dossier_pressure_sample(chat)
                    self.assertEqual(2, score["link_count"])
                    self.assertEqual(["chat_link_count"], score["failure_categories"])

    def test_executive_dossier_runtime_package_is_complete_and_static_checked(self) -> None:
        checker = load_static_checker()
        self.assertEqual(
            [],
            checker.validate_executive_dossier_package(PLUGIN_ROOT, REPO_ROOT),
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            incomplete_plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, incomplete_plugin)
            (incomplete_plugin / "assets" / "executive-career-dossier-v1.css").unlink()
            errors = checker.validate_executive_dossier_package(
                incomplete_plugin,
                REPO_ROOT,
            )
        self.assertIn(
            "assets/executive-career-dossier-v1.css: missing dossier package file",
            errors,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            incomplete_plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, incomplete_plugin)
            (incomplete_plugin / "assets" / "executive-career-dossier-v2.css").unlink()
            errors = checker.validate_executive_dossier_package(
                incomplete_plugin,
                REPO_ROOT,
            )
        self.assertIn(
            "assets/executive-career-dossier-v2.css: missing dossier package file",
            errors,
        )

    def test_executive_dossier_package_rejects_invalid_registry_and_network_assets(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            plugin = Path(temporary_directory) / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            registry = plugin / "scripts" / "linkedin_source_registry.json"
            registry.write_text("{", encoding="utf-8")
            template = plugin / "assets" / "executive-career-dossier-v1.html"
            template.write_text(
                template.read_text(encoding="utf-8") + "\n<script>fetch('remote')</script>\n",
                encoding="utf-8",
            )
            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn("scripts/linkedin_source_registry.json: invalid JSON", errors)
        self.assertIn(
            "assets/executive-career-dossier-v1.html: remote or network token in dossier asset",
            errors,
        )

    def test_executive_dossier_package_rejects_direct_broken_and_intermediate_symlinks(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            external_css = root / "external.css"
            external_css.write_text("body { color: black; }", encoding="utf-8")
            cases = ("direct", "broken", "intermediate")
            for case in cases:
                with self.subTest(case=case):
                    plugin = root / case / "professional-growth-coach"
                    shutil.copytree(PLUGIN_ROOT, plugin)
                    css = plugin / "assets" / "executive-career-dossier-v1.css"
                    if case == "direct":
                        css.unlink()
                        css.symlink_to(external_css)
                    elif case == "broken":
                        css.unlink()
                        css.symlink_to(root / "missing.css")
                    else:
                        external_assets = root / "external-assets"
                        if not external_assets.exists():
                            shutil.copytree(plugin / "assets", external_assets)
                        shutil.rmtree(plugin / "assets")
                        (plugin / "assets").symlink_to(external_assets, target_is_directory=True)
                    errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)
                    self.assertIn(
                        "assets/executive-career-dossier-v1.css: dossier package path cannot traverse a symlink",
                        errors,
                    )

    def test_executive_dossier_package_rejects_unsafe_template_boundaries(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            template = plugin / "assets" / "executive-career-dossier-v1.html"
            template.write_text(
                template.read_text(encoding="utf-8").replace(
                    "</head>", "<style>extra</style></head>"
                ),
                encoding="utf-8",
            )
            css = plugin / "assets" / "executive-career-dossier-v1.css"
            css.write_text(
                css.read_text(encoding="utf-8")
                + "\n</style><script>location='//example.invalid'</script><style>",
                encoding="utf-8",
            )
            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn(
            "assets/executive-career-dossier-v1.html: template must contain exactly one bounded inline style and script",
            errors,
        )
        self.assertIn(
            "assets/executive-career-dossier-v1.css: unsafe inline asset boundary",
            errors,
        )

    def test_executive_dossier_package_requires_exact_csp_and_rejects_entity_urls(self) -> None:
        checker = load_static_checker()
        mutations = (
            ("default-src 'self'", "unsafe dossier content security policy"),
            ("<img src=\"https&#58;//example.invalid/pixel\">", "active remote URL in dossier asset"),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            for index, (injection, expected) in enumerate(mutations):
                with self.subTest(injection=injection):
                    plugin = root / str(index) / "professional-growth-coach"
                    shutil.copytree(PLUGIN_ROOT, plugin)
                    template = plugin / "assets" / "executive-career-dossier-v1.html"
                    text = template.read_text(encoding="utf-8")
                    if injection.startswith("default-src"):
                        text = re.sub(
                            r"default-src 'none'",
                            injection,
                            text,
                            count=1,
                        )
                    else:
                        text = text.replace("</body>", f"{injection}</body>")
                    template.write_text(text, encoding="utf-8")
                    errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)
                    self.assertTrue(any(expected in error for error in errors), errors)

    def test_executive_dossier_package_rejects_joint_validator_renderer_noop(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            validator = plugin / "scripts" / "validate_executive_career_dossier.py"
            validator.write_text(
                "import argparse\np=argparse.ArgumentParser();p.add_argument('dossier', nargs='?');p.parse_args()\n",
                encoding="utf-8",
            )
            renderer = plugin / "scripts" / "render_executive_career_dossier.py"
            renderer.write_text(
                "import argparse,json,os\n"
                "p=argparse.ArgumentParser();p.add_argument('dossier', nargs='?');p.add_argument('--output');a=p.parse_args()\n"
                "html='<!doctype html><main><style></style><script></script></main>'\n"
                "open(a.output,'w').write(html) if a.output else None\n"
                "print(json.dumps({'artifact':a.output,'type':'executive-career-dossier','locale':'es','chat':'ok'}))\n",
                encoding="utf-8",
            )
            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)
        self.assertTrue(any("runtime semantics" in error for error in errors), errors)

    def test_html_dossier_skill_contract_populates_bound_requested_technology_terms(self) -> None:
        reference = (
            PLUGIN_ROOT
            / "skills/optimize-professional-profile/references/html-dossier.md"
        ).read_text(encoding="utf-8")
        self.assertIn("requested_technology_terms", reference)
        self.assertRegex(reference, r"(?is)every explicitly requested technology.+claim_ids")
        self.assertRegex(
            reference,
            r"(?is)every promoted expertise complement.+independently.+allowed claim",
        )

    def test_executive_dossier_package_executes_validator_and_renderer_semantics(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            validator = plugin / "scripts" / "validate_executive_career_dossier.py"
            validator.write_text(
                "import argparse\n"
                "p = argparse.ArgumentParser()\n"
                "p.add_argument('dossier', nargs='?')\n"
                "p.parse_args()\n",
                encoding="utf-8",
            )

            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn(
            "scripts/validate_executive_career_dossier.py: invalid dossier fixture was accepted",
            errors,
        )

    def test_executive_dossier_package_rejects_renderer_boundary_injection(self) -> None:
        checker = load_static_checker()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            plugin = root / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, plugin)
            renderer = plugin / "scripts" / "render_executive_career_dossier.py"
            renderer.write_text(
                renderer.read_text(encoding="utf-8").replace(
                    'INLINE_SCRIPT = """',
                    'INLINE_SCRIPT = """</script><script>',
                    1,
                ),
                encoding="utf-8",
            )

            errors = checker.validate_executive_dossier_package(plugin, REPO_ROOT)

        self.assertIn(
            "scripts/render_executive_career_dossier.py: rendered dossier has unsafe inline boundaries",
            errors,
        )

    def test_executive_dossier_scripts_resolve_installed_files_outside_repository_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            installed_plugin = root / "installed" / "professional-growth-coach"
            shutil.copytree(PLUGIN_ROOT, installed_plugin)
            installed_css_marker = "installed-relative-css-marker"
            installed_template_marker = "installed-relative-template-marker"
            installed_registry_marker = "installed-relative-registry-marker"
            installed_css = installed_plugin / "assets" / "executive-career-dossier-v1.css"
            installed_css.write_text(
                installed_css.read_text(encoding="utf-8")
                + f"\n/* {installed_css_marker} */\n",
                encoding="utf-8",
            )
            installed_template = (
                installed_plugin / "assets" / "executive-career-dossier-v1.html"
            )
            installed_template.write_text(
                installed_template.read_text(encoding="utf-8").replace(
                    "</body>",
                    f"<!-- {installed_template_marker} --></body>",
                ),
                encoding="utf-8",
            )
            installed_registry_path = (
                installed_plugin / "scripts" / "linkedin_source_registry.json"
            )
            installed_registry = json.loads(
                installed_registry_path.read_text(encoding="utf-8")
            )
            installed_registry["official_categories"]["good_profile"][0][
                "path_prefix"
            ] = f"/help/linkedin/answer/{installed_registry_marker}"
            installed_registry_path.write_text(
                json.dumps(installed_registry),
                encoding="utf-8",
            )
            fixture = root / "input.json"
            shutil.copy2(DOSSIER_FIXTURE_PATH, fixture)
            unrelated_cwd = root / "unrelated-cwd"
            unrelated_cwd.mkdir()
            output = root / "output" / "executive-career-dossier.html"

            validate_result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(installed_plugin / "scripts" / "validate_executive_career_dossier.py"),
                    str(fixture),
                ],
                cwd=unrelated_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
            render_result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(installed_plugin / "scripts" / "render_executive_career_dossier.py"),
                    str(fixture),
                    "--output",
                    str(output),
                    "--include-artifact-path",
                ],
                cwd=unrelated_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(0, validate_result.returncode, validate_result.stderr)
            self.assertEqual(0, render_result.returncode, render_result.stderr)
            receipt = json.loads(render_result.stdout)
            self.assertTrue(
                os.path.samefile(output, Path(receipt["artifact_path"])),
            )
            self.assertTrue(output.is_file())
            rendered = output.read_text(encoding="utf-8")
            for marker in (
                installed_css_marker,
                installed_template_marker,
                installed_registry_marker,
            ):
                self.assertIn(marker, rendered)

    def test_private_generated_output_paths_are_git_ignored(self) -> None:
        for relative_path in (
            ".professional-growth-coach-artifacts/executive-career-dossier.html",
            ".superpowers/sdd/executive-career-dossier/render-qa/report.html",
        ):
            with self.subTest(relative_path=relative_path):
                result = subprocess.run(
                    ["git", "check-ignore", "--quiet", relative_path],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode)

    def test_release_manifest_describes_private_html_linkedin_diagnostics(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        if not manifest["version"].startswith("0.2.0+codex."):
            self.assertTrue(manifest["version"].startswith("0.1.0+codex."))
            return
        release_copy = " ".join(
            (
                manifest["description"],
                manifest["interface"]["shortDescription"],
                manifest["interface"]["longDescription"],
            )
        ).casefold()
        for required in ("linkedin", "private", "html", "evidence"):
            self.assertIn(required, release_copy)

    def test_marketplace_policy_and_source_are_byte_identical(self) -> None:
        digest = hashlib.sha256(MARKETPLACE_PATH.read_bytes()).hexdigest()
        self.assertEqual(EXPECTED_MARKETPLACE_SHA256, digest)

    def make_fake_release_project(self, root: Path) -> tuple[Path, Path]:
        (root / "scripts").mkdir(parents=True)
        (root / "requirements").mkdir(parents=True)
        shutil.copy2(RELEASE_BOOTSTRAP_PATH, root / "scripts" / RELEASE_BOOTSTRAP_PATH.name)
        (root / "requirements" / "release-validation.txt").write_text(
            EXPECTED_RELEASE_REQUIREMENT,
            encoding="utf-8",
        )
        fake_python = root / "fake-python3.11"
        fake_python.write_text(
            """#!/usr/bin/env python3
import os
import shutil
import sys
from pathlib import Path

args = sys.argv[1:]
if args[:2] == ["-m", "venv"]:
    target = Path(args[2])
    (target / "bin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), target / "bin" / "python")
    (target / "bin" / "python").chmod(0o755)
    raise SystemExit(0)
if args[:3] == ["-m", "pip", "install"]:
    if os.environ.get("FAKE_INSTALL_FAIL") == "1":
        raise SystemExit(42)
    venv = Path(sys.argv[0]).resolve().parents[1]
    (venv / "installed-pyyaml.txt").write_text("6.0.3", encoding="utf-8")
    raise SystemExit(0)
if args[:2] == ["-B", "-c"]:
    raise SystemExit(0)
raise SystemExit(64)
""",
            encoding="utf-8",
        )
        fake_python.chmod(0o755)
        return root / "scripts" / RELEASE_BOOTSTRAP_PATH.name, fake_python

    def run_fake_bootstrap(
        self,
        script: Path,
        fake_python: Path,
        *,
        fail_install: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["PYTHON_311"] = str(fake_python)
        if fail_install:
            environment["FAKE_INSTALL_FAIL"] = "1"
        return subprocess.run(
            ["bash", str(script)],
            cwd=script.parents[1],
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_release_validation_environment_is_pinned_and_documented(self) -> None:
        self.assertTrue(RELEASE_REQUIREMENTS_PATH.is_file())
        self.assertEqual(
            EXPECTED_RELEASE_REQUIREMENT,
            RELEASE_REQUIREMENTS_PATH.read_text(encoding="utf-8"),
        )
        self.assertIn(
            ".release-validation-venv/",
            GITIGNORE_PATH.read_text(encoding="utf-8").splitlines(),
        )
        self.assertTrue(RELEASE_BOOTSTRAP_PATH.is_file())
        self.assertTrue(RELEASE_BOOTSTRAP_PATH.stat().st_mode & 0o100)
        self.assertTrue(RELEASE_RUNNER_PATH.is_file())
        self.assertTrue(RELEASE_RUNNER_PATH.stat().st_mode & 0o100)
        syntax = subprocess.run(
            ["bash", "-n", str(RELEASE_BOOTSTRAP_PATH)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, syntax.returncode, syntax.stderr)
        release_documentation = RELEASE_DOCUMENTATION_PATH.read_text(encoding="utf-8")
        for required_contract in (
            "CPython 3.11.15",
            "scripts/run_release_validation.sh",
            "--require-hashes --only-binary=:all: --no-deps",
        ):
            self.assertIn(required_contract, release_documentation)

    def test_release_runner_stops_before_execution_on_validator_checksum_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            sentinel = root / "validator-executed"
            fake_skill = root / "quick_validate.py"
            fake_plugin = root / "validate_plugin.py"
            payload = (
                "from pathlib import Path\n"
                f"Path({str(sentinel)!r}).write_text('executed', encoding='utf-8')\n"
            )
            fake_skill.write_text(payload, encoding="utf-8")
            fake_plugin.write_text(payload, encoding="utf-8")
            environment = os.environ.copy()
            environment.update(
                {
                    "VALIDATION_PYTHON": sys.executable,
                    "SKILL_VALIDATOR_PATH": str(fake_skill),
                    "PLUGIN_VALIDATOR_PATH": str(fake_plugin),
                    "SOURCE_PLUGIN_ROOT": str(root / "plugin"),
                    "LINKEDIN_SKILL_ROOT": str(root / "plugin" / "skill"),
                }
            )
            result = subprocess.run(
                ["bash", str(RELEASE_RUNNER_PATH)],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("VALIDATOR_CHECKSUM_MISMATCH", result.stderr)
            self.assertFalse(sentinel.exists())

    def test_release_validator_digests_match_runner_and_documentation(self) -> None:
        runner = RELEASE_RUNNER_PATH.read_text(encoding="utf-8")
        documentation = RELEASE_DOCUMENTATION_PATH.read_text(encoding="utf-8")
        for variable, label in (
            ("EXPECTED_SKILL_SHA256", "quick_validate.py"),
            ("EXPECTED_PLUGIN_SHA256", "validate_plugin.py"),
        ):
            match = re.search(rf'{variable}="([0-9a-f]{{64}})"', runner)
            self.assertIsNotNone(match, variable)
            digest = match.group(1)
            self.assertIn(f"- `{label}`: `{digest}`", documentation)

    def test_release_runner_invokes_repository_privacy_scanner(self) -> None:
        runner = RELEASE_RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn(
            '"$VALIDATION_PYTHON" -B "$PROJECT_ROOT/scripts/check_repository_privacy.py" --repo-root "$PROJECT_ROOT"',
            runner,
        )

    def test_release_runner_executes_rehashed_private_validator_copies(self) -> None:
        runner = RELEASE_RUNNER_PATH.read_text(encoding="utf-8")
        self.assertIn(
            'VALIDATOR_TMPDIR="$(mktemp -d "${TMPDIR:-/tmp}/pgc-release-XXXXXX")"',
            runner,
        )
        self.assertIn(
            'cp -p "$SKILL_VALIDATOR_PATH" "$SKILL_VALIDATOR_COPY"',
            runner,
        )
        self.assertIn(
            'cp -p "$PLUGIN_VALIDATOR_PATH" "$PLUGIN_VALIDATOR_COPY"',
            runner,
        )
        self.assertIn('copied_skill_sha=', runner)
        self.assertIn('copied_plugin_sha=', runner)
        self.assertIn(
            '"$VALIDATION_PYTHON" -B "$SKILL_VALIDATOR_COPY" "$LINKEDIN_SKILL_ROOT"',
            runner,
        )
        self.assertIn(
            '"$VALIDATION_PYTHON" -B "$PLUGIN_VALIDATOR_COPY" "$SOURCE_PLUGIN_ROOT"',
            runner,
        )
        self.assertNotIn(
            '"$VALIDATION_PYTHON" -B "$SKILL_VALIDATOR_PATH" "$LINKEDIN_SKILL_ROOT"',
            runner,
        )
        self.assertNotIn(
            '"$VALIDATION_PYTHON" -B "$PLUGIN_VALIDATOR_PATH" "$SOURCE_PLUGIN_ROOT"',
            runner,
        )

    def test_bootstrap_replaces_stale_final_environment_and_is_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            (final_venv / "stale-package.txt").write_text("stale", encoding="utf-8")

            first = self.run_fake_bootstrap(script, fake_python)
            self.assertEqual(0, first.returncode, first.stdout + first.stderr)
            self.assertTrue((final_venv / "installed-pyyaml.txt").is_file())
            self.assertFalse((final_venv / "stale-package.txt").exists())

            (final_venv / "unrelated-package.txt").write_text("stale", encoding="utf-8")
            second = self.run_fake_bootstrap(script, fake_python)
            self.assertEqual(0, second.returncode, second.stdout + second.stderr)
            self.assertFalse((final_venv / "unrelated-package.txt").exists())

    def test_bootstrap_rejects_changed_requirement_hash_and_preserves_final(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            preserved = final_venv / "preserved.txt"
            preserved.write_text("previous-good", encoding="utf-8")
            (root / "requirements" / "release-validation.txt").write_text(
                "PyYAML==6.0.3 --hash=sha256:" + "0" * 64 + "\n",
                encoding="utf-8",
            )

            result = self.run_fake_bootstrap(script, fake_python)
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(preserved.is_file())

    def test_bootstrap_failed_install_preserves_previous_final_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            preserved = final_venv / "preserved.txt"
            preserved.write_text("previous-good", encoding="utf-8")

            result = self.run_fake_bootstrap(script, fake_python, fail_install=True)
            self.assertNotEqual(0, result.returncode)
            self.assertTrue(preserved.is_file())

    def test_bootstrap_rollback_reservation_ignores_preexisting_collision_like_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            script, fake_python = self.make_fake_release_project(root)
            final_venv = root / ".release-validation-venv"
            final_venv.mkdir()
            (final_venv / "preserved.txt").write_text("previous-good", encoding="utf-8")
            collision = root / ".release-validation-venv.rollback.4242"
            collision.mkdir()
            (collision / "unrelated.txt").write_text("do-not-touch", encoding="utf-8")

            result = self.run_fake_bootstrap(script, fake_python)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertTrue((final_venv / "installed-pyyaml.txt").is_file())
            self.assertEqual(
                "do-not-touch",
                (collision / "unrelated.txt").read_text(encoding="utf-8"),
            )
            bootstrap = script.read_text(encoding="utf-8")
            self.assertIn('mktemp -d "${FINAL_VENV}.rollback.XXXXXX"', bootstrap)
            self.assertIn('ROLLBACK_VENV="$ROLLBACK_ROOT/previous"', bootstrap)
            self.assertNotIn('rmdir "$ROLLBACK_VENV"', bootstrap)
            self.assertNotIn('ROLLBACK_VENV="${FINAL_VENV}.rollback.$$"', bootstrap)

    def test_manifest_and_canonical_skill_inventory_match_the_contract(self) -> None:
        self.assertTrue(MANIFEST_PATH.is_file(), f"Missing manifest: {MANIFEST_PATH}")

        manifest_text = MANIFEST_PATH.read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)
        self.assertEqual(manifest["name"], "professional-growth-coach")
        self.assertRegex(manifest["version"], INSTALLABLE_VERSION_PATTERN)
        self.assertIsInstance(manifest["description"], str)
        self.assertTrue(manifest["description"].strip())
        self.assertEqual(manifest["author"]["name"], "krios")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("apps", manifest)
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("[TODO:", manifest_text)

        interface = manifest["interface"]
        self.assertEqual(interface["displayName"], "Professional Growth Coach")
        self.assertIsInstance(interface["shortDescription"], str)
        self.assertTrue(interface["shortDescription"].strip())
        self.assertIsInstance(interface["longDescription"], str)
        self.assertTrue(interface["longDescription"].strip())
        self.assertEqual(interface["developerName"], "krios")
        self.assertEqual(interface["category"], "Productivity")
        self.assertEqual(interface["capabilities"], ["Interactive", "Read", "Write"])
        self.assertIsInstance(interface["defaultPrompt"], list)
        self.assertEqual(len(interface["defaultPrompt"]), 3)
        self.assertTrue(
            all(isinstance(prompt, str) and prompt.strip() for prompt in interface["defaultPrompt"])
        )
        self.assertEqual(tuple(interface["defaultPrompt"]), EXPECTED_STARTER_PROMPTS)

        expected_skills = tuple(json.loads(EXPECTED_SKILLS_PATH.read_text(encoding="utf-8")))
        self.assertEqual(expected_skills, EXPECTED_SKILLS)
        self.assertEqual(len(expected_skills), 8)
        self.assertEqual(len(set(expected_skills)), len(expected_skills))
        self.assertTrue(all(SKILL_NAME_PATTERN.fullmatch(skill) for skill in expected_skills))

    def test_screen_preparation_css_is_scoped_responsive_and_printable(self) -> None:
        css = (PLUGIN_ROOT / "assets" / "executive-career-dossier-v1.css").read_text(
            encoding="utf-8"
        )

        for selector in (
            ".screen-preparation-card",
            ".readiness-chip",
            ".screen-preparation-evidence",
            ".screen-preparation-boundary",
            ".screen-preparation-rehearsal",
        ):
            with self.subTest(selector=selector):
                self.assertIn(selector, css)
        self.assertRegex(
            css,
            r"(?s)\.screen-preparation-card\s*\{[^}]*font-size:\s*1rem",
        )
        self.assertRegex(
            css,
            r"(?s)@media\s*\(max-width:\s*680px\)\s*\{.*?"
            r"\.screen-preparation-card\s*\{[^}]*grid-template-columns:\s*1fr",
        )
        self.assertRegex(
            css,
            r"(?s)@media\s+print\s*\{.*?\.screen-preparation-card\s*\{"
            r"[^}]*break-inside:\s*avoid[^}]*break-after:\s*avoid",
        )


if __name__ == "__main__":
    unittest.main()
