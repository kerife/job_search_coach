"""Structural contract for client-first LinkedIn Markdown reports."""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts" / "validate_linkedin_client_report.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "linkedin-report-v2"

specification = importlib.util.spec_from_file_location("validate_linkedin_client_report", VALIDATOR_PATH)
assert specification is not None and specification.loader is not None
validator = importlib.util.module_from_spec(specification)
specification.loader.exec_module(validator)


class LinkedInClientReportParsingTests(unittest.TestCase):
    def report(self, name: str) -> str:
        return (FIXTURE_ROOT / name).read_text(encoding="utf-8")

    def bundle(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def errors(
        self,
        report_name: str,
        bundle_name: str,
        *,
        appendix_mode: str = "normal",
    ) -> list[str]:
        return validator.validate_client_report(
            self.report(report_name),
            self.bundle(bundle_name),
            appendix_mode=appendix_mode,
        )

    def test_report_starts_at_byte_zero_and_has_eight_ordered_sections(self) -> None:
        parsed = validator.parse_client_report(self.report("scenario-a-es.md"))
        self.assertEqual("es", parsed.locale)
        self.assertTrue(parsed.client_report.startswith("# Diagnóstico ejecutivo de LinkedIn\n"))
        self.assertEqual(validator.SECTION_KEYS, tuple(parsed.section_bodies))

    def test_english_report_uses_the_explicit_english_heading_map(self) -> None:
        parsed = validator.parse_client_report(self.report("scenario-b-en.md"))
        self.assertEqual("en", parsed.locale)
        self.assertEqual(
            tuple(validator.HEADING_MAP["en"][key] for key in validator.SECTION_KEYS),
            tuple(validator.HEADING_MAP["en"][key] for key in parsed.section_bodies),
        )

    def test_parsed_report_is_immutable_and_contains_only_structural_layers(self) -> None:
        parsed = validator.parse_client_report(self.report("scenario-a-es.md"))
        self.assertEqual(
            ("locale", "client_report", "evidence_appendix", "section_bodies"),
            parsed._fields,
        )
        with self.assertRaises(AttributeError):
            parsed.locale = "en"
        with self.assertRaises(TypeError):
            parsed.section_bodies["verdict"] = "replacement"

    def test_first_localized_appendix_heading_is_the_layer_boundary(self) -> None:
        markdown = self.report("scenario-a-es.md") + "\n## Veredicto\n\nAppendix-only heading.\n"
        parsed = validator.parse_client_report(markdown)
        self.assertNotIn("## Apéndice de evidencia", parsed.client_report)
        self.assertIn("## Veredicto", parsed.evidence_appendix)
        self.assertNotIn("Appendix-only heading.", parsed.section_bodies["boundaries"])

    def test_content_before_h1_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "client report must start at byte 0 with a localized H1",
        ):
            validator.parse_client_report("Prelude\n" + self.report("scenario-a-es.md"))

    def test_contract_row_cannot_substitute_for_rendered_report(self) -> None:
        errors = validator.validate_client_report(
            "- inferred: candidate_id=x; linkedin_rendered_client_report_sample=x.",
            self.bundle("scenario-a.json"),
        )
        self.assertIn("client report must start at byte 0 with a localized H1", errors)

    def test_report_requires_exactly_one_matching_localized_appendix_boundary(self) -> None:
        report = self.report("scenario-a-es.md")
        cases = (
            (report.replace("## Apéndice de evidencia", "## Evidence appendix"), "missing"),
            (report + "\n## Apéndice de evidencia\n\nSecond boundary.\n", "duplicate"),
        )
        for markdown, case in cases:
            with self.subTest(case=case), self.assertRaisesRegex(
                ValueError,
                "report requires exactly one localized appendix boundary",
            ):
                validator.parse_client_report(markdown)

    def test_missing_duplicate_or_reordered_client_section_is_rejected(self) -> None:
        report = self.report("scenario-a-es.md")
        cases = (
            (report.replace("## Evidencia pendiente\n", "### Evidencia pendiente\n", 1), "missing"),
            (report.replace("## Evidencia pendiente\n", "## Veredicto\n", 1), "duplicate"),
            (
                report.replace("## Veredicto\n", "## TEMPORAL\n", 1)
                .replace("## Calificación\n", "## Veredicto\n", 1)
                .replace("## TEMPORAL\n", "## Calificación\n", 1),
                "reordered",
            ),
        )
        for markdown, case in cases:
            with self.subTest(case=case), self.assertRaisesRegex(
                ValueError,
                "client report sections are missing, duplicated, or out of order",
            ):
                validator.parse_client_report(markdown)

    def test_commonmark_line_classifier_tracks_fence_marker_length_and_indented_code(self) -> None:
        markdown = "\n".join(
            (
                "live",
                "   ````python",
                "## fenced heading",
                "```",
                "~~~~",
                "`````",
                "live again",
                "  ~~~ details",
                "### tilde heading",
                "   ~~~~~",
                "    ## four-space heading",
                "\t| tab-indented | row |",
                "Inline `## heading` remains live.",
            )
        )

        classified = validator._classify_markdown_lines(markdown)

        self.assertEqual(tuple(markdown.splitlines()), tuple(line for line, _ in classified))
        self.assertEqual(
            (False, True, True, True, True, True, False, True, True, True, True, True, False),
            tuple(is_code for _, is_code in classified),
        )

    def test_commonmark_indentation_uses_four_column_tab_stops(self) -> None:
        lines = (
            " \t| one-space tab table |",
            "  \t- Two-space tab: localized field",
            "   \t### three-space tab heading",
            " \t```",
            "## live after indented fence",
        )

        classified = validator._classify_markdown_lines("\n".join(lines))

        self.assertEqual(
            (True, True, True, True, False),
            tuple(is_code for _, is_code in classified),
        )

        report = self.report("scenario-a-es.md")
        for prefix in (" \t", "  \t", "   \t"):
            with self.subTest(prefix=repr(prefix), structure="table"):
                mutated = report.replace(
                    "| Dimensión | Estado | Puntaje | Evidencia | Razón |",
                    f"{prefix}| Dimensión | Estado | Puntaje | Evidencia | Razón |",
                    1,
                )
                self.assertIn(
                    "score table requires the localized five-column header",
                    validator.validate_client_report(
                        mutated,
                        self.bundle("scenario-a.json"),
                    ),
                )
            with self.subTest(prefix=repr(prefix), structure="localized field"):
                mutated = report.replace(
                    "- Brecha: `GAP-A-PRIMARY`",
                    f"{prefix}- Brecha: `GAP-A-PRIMARY`",
                    1,
                )
                self.assertIn(
                    "priority 1 missing required field: diagnosed_gap",
                    validator.validate_client_report(
                        mutated,
                        self.bundle("scenario-a.json"),
                    ),
                )

        indented_fence = report.replace(
            "## Calificación\n",
            " \t```\n## Calificación\n",
            1,
        )
        self.assertEqual(
            [],
            validator.validate_client_report(
                indented_fence,
                self.bundle("scenario-a.json"),
            ),
        )

    def test_fenced_or_indented_structure_is_not_live_markdown(self) -> None:
        report = self.report("scenario-a-es.md")
        headings = tuple(
            f"## {validator.HEADING_MAP['es'][key]}"
            for key in validator.SECTION_KEYS
        )
        wrappers = (
            lambda heading: f"```\n{heading}\n```",
            lambda heading: f"   ~~~~ markdown\n{heading}\n   ~~~~~",
            lambda heading: f"````` details\n{heading}\n``````",
            lambda heading: f"    {heading}",
        )
        for index, heading in enumerate(headings):
            markdown = report.replace(
                f"{heading}\n",
                f"{wrappers[index % len(wrappers)](heading)}\n",
                1,
            )
            with self.subTest(heading=heading), self.assertRaisesRegex(
                ValueError,
                "client report sections are missing, duplicated, or out of order",
            ):
                validator.parse_client_report(markdown)

        hidden_table_header = report.replace(
            "| Dimensión | Estado | Puntaje | Evidencia | Razón |\n",
            "```\n| Dimensión | Estado | Puntaje | Evidencia | Razón |\n```\n",
            1,
        )
        self.assertIn(
            "score table requires the localized five-column header",
            validator.validate_client_report(hidden_table_header, self.bundle("scenario-a.json")),
        )

        hidden_priority_heading = report.replace(
            "### 1. Titular\n",
            "~~~~\n### 1. Titular\n~~~~\n",
            1,
        )
        self.assertIn(
            "report requires exactly three complete priorities",
            validator.validate_client_report(hidden_priority_heading, self.bundle("scenario-a.json")),
        )

        hidden_localized_field = report.replace(
            "- Brecha: `GAP-A-PRIMARY`",
            "    - Brecha: `GAP-A-PRIMARY`",
            1,
        )
        self.assertIn(
            "priority 1 missing required field: diagnosed_gap",
            validator.validate_client_report(hidden_localized_field, self.bundle("scenario-a.json")),
        )

        debug_report = self.report("scenario-a-es-debug.md")
        hidden_debug_heading = debug_report.replace(
            "### coach_brief\n",
            "```\n### coach_brief\n```\n",
            1,
        )
        self.assertIn(
            "debug appendix sections are missing, duplicated, or out of order",
            validator.validate_client_report(
                hidden_debug_heading,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )
        hidden_debug_row = debug_report.replace(
            "- verified: candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=client_first_summary",
            "    - verified: candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=client_first_summary",
            1,
        )
        self.assertIn(
            "legacy appendix section coach_brief requires at least one canonical row",
            validator.validate_client_report(
                hidden_debug_row,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_unclosed_fence_is_rejected(self) -> None:
        for opening, shorter_or_wrong_close in (("````", "```"), ("~~~~", "```")):
            with self.subTest(opening=opening), self.assertRaisesRegex(
                ValueError,
                "unclosed Markdown fence",
            ):
                validator.parse_client_report(
                    self.report("scenario-a-es.md")
                    + f"\n{opening}\nnon-structural code\n{shorter_or_wrong_close}\n"
                )

    def test_inline_code_cannot_impersonate_structure_and_remains_valid_prose(self) -> None:
        report = self.report("scenario-a-es.md").replace(
            "\n## Calificación\n",
            "\nLos ejemplos `## Veredicto`, `### Titular` y `| Dimensión |` son texto.\n\n"
            "## Calificación\n",
            1,
        )

        self.assertEqual(
            [],
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_lf_and_crlf_reports_share_the_same_exact_byte_zero_contract(self) -> None:
        cases = (
            ("scenario-a-es.md", "scenario-a.json", "normal"),
            ("scenario-a-es-debug.md", "scenario-a.json", "debug"),
            ("scenario-b-en.md", "scenario-b.json", "normal"),
        )
        for report_name, bundle_name, mode in cases:
            crlf_report = self.report(report_name).replace("\n", "\r\n")
            with self.subTest(report=report_name):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        crlf_report,
                        self.bundle(bundle_name),
                        appendix_mode=mode,
                    ),
                )

    def test_markdown_line_boundaries_are_only_crlf_lf_or_cr(self) -> None:
        reports = (
            ("scenario-a-es.md", "scenario-a.json", "normal"),
            ("scenario-a-es-debug.md", "scenario-a.json", "debug"),
            ("scenario-b-en.md", "scenario-b.json", "normal"),
        )
        for report_name, bundle_name, mode in reports:
            cr_report = self.report(report_name).replace("\n", "\r")
            with self.subTest(boundary="CR", report=report_name):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        cr_report,
                        self.bundle(bundle_name),
                        appendix_mode=mode,
                    ),
                )

    def test_unicode_non_markdown_boundaries_cannot_create_nested_structure(self) -> None:
        report = self.report("scenario-a-es.md")
        debug_report = self.report("scenario-a-es-debug.md")
        for boundary in ("\u2028", "\u0085", "\v", "\f"):
            with self.subTest(boundary=ascii(boundary), structure="table"):
                mutant = report.replace(
                    "\n| Dimensión | Estado | Puntaje | Evidencia | Razón |",
                    f"{boundary}| Dimensión | Estado | Puntaje | Evidencia | Razón |",
                    1,
                )
                self.assertIn(
                    "score table requires the localized five-column header",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )
            with self.subTest(boundary=ascii(boundary), structure="H3"):
                mutant = report.replace(
                    "## Las tres decisiones prioritarias\n\n### 1. Titular",
                    f"## Las tres decisiones prioritarias\n{boundary}### 1. Titular",
                    1,
                )
                self.assertIn(
                    "report requires exactly three complete priorities",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )
            with self.subTest(boundary=ascii(boundary), structure="field"):
                mutant = report.replace(
                    "\n- Brecha: `GAP-A-PRIMARY`",
                    f"{boundary}- Brecha: `GAP-A-PRIMARY`",
                    1,
                )
                self.assertIn(
                    "priority 1 missing required field: diagnosed_gap",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )
            with self.subTest(boundary=ascii(boundary), structure="debug row"):
                mutant = debug_report.replace(
                    "### coach_brief\n\n- verified:",
                    f"### coach_brief\n{boundary}- verified:",
                    1,
                )
                self.assertIn(
                    "legacy appendix section coach_brief requires at least one canonical row",
                    validator.validate_client_report(
                        mutant,
                        self.bundle("scenario-a.json"),
                        appendix_mode="debug",
                    ),
                )
            with self.subTest(boundary=ascii(boundary), structure="blocked item"):
                mutant = report.replace(
                    "\n- Claim bloqueado: `CAPABILITY_UNVERIFIED`",
                    f"{boundary}- Claim bloqueado: `CAPABILITY_UNVERIFIED`",
                    1,
                )
                self.assertIn(
                    "visible blocked claims do not match fixture blocked_claims",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )
            with self.subTest(boundary=ascii(boundary), structure="plan item"):
                mutant = report.replace(
                    "\n- Perfil: PROFILE_REVIEW|headline",
                    f"{boundary}- Perfil: PROFILE_REVIEW|headline",
                    1,
                )
                self.assertIn(
                    "private seven-day plan requires closed action and target codes",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )

        report = self.report("scenario-a-es.md")
        invalid_boundaries = ("\u2028", "\u0085", "\v", "\f")
        for boundary in invalid_boundaries:
            with self.subTest(boundary=ascii(boundary), placement="H1"):
                mutant = report.replace("\n", boundary, 1)
                self.assertIn(
                    "client report must start at byte 0 with a localized H1",
                    validator.validate_client_report(
                        mutant,
                        self.bundle("scenario-a.json"),
                    ),
                )
            with self.subTest(boundary=ascii(boundary), placement="H2"):
                mutant = report.replace(
                    "\n## Calificación\n",
                    f"{boundary}## Calificación{boundary}",
                    1,
                )
                self.assertIn(
                    "client report sections are missing, duplicated, or out of order",
                    validator.validate_client_report(
                        mutant,
                        self.bundle("scenario-a.json"),
                    ),
                )
            with self.subTest(boundary=ascii(boundary), placement="appendix"):
                mutant = report.replace(
                    "\n## Apéndice de evidencia\n",
                    f"{boundary}## Apéndice de evidencia{boundary}",
                    1,
                )
                self.assertIn(
                    "report requires exactly one localized appendix boundary",
                    validator.validate_client_report(
                        mutant,
                        self.bundle("scenario-a.json"),
                    ),
                )

        crlf_report = self.report("scenario-a-es.md").replace("\n", "\r\n")
        for prefix in ("Prelude\r\n", "\ufeff"):
            with self.subTest(prefix=repr(prefix)):
                self.assertIn(
                    "client report must start at byte 0 with a localized H1",
                    validator.validate_client_report(
                        prefix + crlf_report,
                        self.bundle("scenario-a.json"),
                    ),
                )

    def test_report_locale_must_match_bundle_locale(self) -> None:
        errors = validator.validate_client_report(
            self.report("scenario-b-en.md"),
            self.bundle("scenario-a.json"),
        )
        self.assertIn("client report locale must match fixture locale", errors)

    def test_sparse_reports_below_four_hundred_fifty_words_are_allowed(self) -> None:
        self.assertEqual([], self.errors("scenario-c-es.md", "scenario-c.json"))

    def test_photo_only_and_banner_only_reports_are_valid_structural_inputs(self) -> None:
        cases = (
            ("scenario-d-en.md", "scenario-d.json"),
            ("scenario-d-banner-only-en.md", "scenario-d-banner-only.json"),
        )
        for report_name, bundle_name in cases:
            with self.subTest(report=report_name):
                self.assertEqual([], self.errors(report_name, bundle_name))

    def test_client_report_word_limit_counts_score_prose_but_not_score_table_rows(self) -> None:
        report = self.report("scenario-a-es.md")
        score_tail = "\n## Las tres decisiones prioritarias"
        prose_overflow = report.replace(score_tail, "\n" + "palabra " * 801 + score_tail, 1)
        table_padding = report.replace(score_tail, "\n| " + "dato " * 600 + "|" + score_tail, 1)
        self.assertIn(
            "client report exceeds 800 words excluding the score table",
            validator.validate_client_report(prose_overflow, self.bundle("scenario-a.json")),
        )
        self.assertNotIn(
            "client report exceeds 800 words excluding the score table",
            validator.validate_client_report(table_padding, self.bundle("scenario-a.json")),
        )

    def test_normal_appendix_word_limit_is_two_hundred_fifty(self) -> None:
        report = self.report("scenario-a-es.md")
        appendix_overflow = report.split("\n## Apéndice de evidencia\n", 1)[0]
        appendix_overflow += "\n## Apéndice de evidencia\n\n" + "detalle " * 251
        self.assertIn(
            "normal evidence appendix exceeds 250 words",
            validator.validate_client_report(appendix_overflow, self.bundle("scenario-a.json")),
        )

    def test_complete_normal_payload_word_limit_is_one_thousand_one_hundred(self) -> None:
        report = self.report("scenario-a-es.md")
        score_tail = "\n## Las tres decisiones prioritarias"
        payload_overflow = report.replace(score_tail, "\n| " + "dato " * 1200 + "|" + score_tail, 1)
        self.assertIn(
            "normal report payload exceeds 1100 words",
            validator.validate_client_report(payload_overflow, self.bundle("scenario-a.json")),
        )

    def test_sensitive_contract_tokens_are_rejected_before_the_appendix(self) -> None:
        report = self.report("scenario-a-es.md")
        cases = (
            "candidate_id=SENTINEL",
            "linkedin_hidden_contract=SENTINEL",
            "(candidate_id=SENTINEL)",
            "`linkedin_hidden_contract=SENTINEL`",
            "\tcandidate_id=SENTINEL",
        )
        for token in cases:
            with self.subTest(token=token):
                markdown = report.replace("## Veredicto\n", f"## Veredicto\n\n{token}\n", 1)
                self.assertIn(
                    "client report cannot contain legacy contract markers",
                    validator.validate_client_report(markdown, self.bundle("scenario-a.json")),
                )

    def test_contract_tokens_inside_larger_identifiers_are_not_false_positives(self) -> None:
        report = self.report("scenario-a-es.md")
        markdown = report.replace(
            "## Veredicto\n",
            "## Veredicto\n\narchive_candidate_id=SENTINEL and my_linkedin_note=SENTINEL\n",
            1,
        )
        self.assertEqual(
            [],
            validator.validate_client_report(markdown, self.bundle("scenario-a.json")),
        )

    def test_generic_canonical_contract_row_is_rejected_before_the_appendix(self) -> None:
        report = self.report("scenario-a-es.md")
        row = "- verified: alpha=one; beta=two"
        markdown = report.replace("## Veredicto\n", f"## Veredicto\n\n{row}\n", 1)
        self.assertIn(
            "client report cannot contain legacy contract markers",
            validator.validate_client_report(markdown, self.bundle("scenario-a.json")),
        )

    def test_markdown_indented_canonical_rows_are_rejected_in_both_layers(self) -> None:
        report = self.report("scenario-a-es.md")
        row = "  - verified: alpha=one; beta=two"
        client_markdown = report.replace("## Veredicto\n", f"## Veredicto\n\n{row}\n", 1)
        appendix_markdown = report.replace("- Índice compacto:", f"{row}\n\n- Índice compacto:", 1)
        self.assertIn(
            "client report cannot contain legacy contract markers",
            validator.validate_client_report(client_markdown, self.bundle("scenario-a.json")),
        )
        self.assertIn(
            "normal evidence appendix cannot contain canonical contract rows",
            validator.validate_client_report(appendix_markdown, self.bundle("scenario-a.json")),
        )

    def test_normal_appendix_rejects_canonical_contract_rows(self) -> None:
        report = self.report("scenario-a-es.md")
        markdown = report.replace(
            "- Índice compacto:",
            "- verified: candidate_id=CANDIDATE-JSC1-SYNTH; appendix_row=legacy\n\n- Índice compacto:",
            1,
        )
        self.assertIn(
            "normal evidence appendix cannot contain canonical contract rows",
            validator.validate_client_report(markdown, self.bundle("scenario-a.json")),
        )

    def test_unknown_appendix_mode_is_rejected(self) -> None:
        errors = validator.validate_client_report(
            self.report("scenario-a-es.md"),
            self.bundle("scenario-a.json"),
            appendix_mode="expanded",
        )
        self.assertIn("unsupported appendix mode: expanded", errors)

    def test_complete_debug_appendix_is_accepted(self) -> None:
        self.assertEqual(
            [],
            self.errors(
                "scenario-a-es-debug.md",
                "scenario-a.json",
                appendix_mode="debug",
            ),
        )
        parsed = validator.parse_client_report(self.report("scenario-a-es-debug.md"))
        sections = validator.parse_full_debug_appendix(parsed)
        self.assertEqual(
            validator.LEGACY_APPENDIX_SECTION_KEYS,
            tuple(section.key for section in sections),
        )

    def test_eval_and_detail_requested_modes_use_the_same_full_debug_contract(self) -> None:
        for mode in ("eval", "detail_requested"):
            with self.subTest(mode=mode):
                self.assertEqual(
                    [],
                    self.errors(
                        "scenario-a-es-debug.md",
                        "scenario-a.json",
                        appendix_mode=mode,
                    ),
                )

    def test_debug_appendix_rejects_a_missing_legacy_section(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        start = report.index("### networking_drafts\n")
        end = report.index("### content_plan\n")
        markdown = report[:start] + report[end:]
        self.assertIn(
            "debug appendix sections are missing, duplicated, or out of order",
            validator.validate_client_report(
                markdown,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_debug_appendix_rejects_reordered_legacy_sections(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        markdown = report.replace("### positioning", "### TEMPORARY", 1)
        markdown = markdown.replace("### rewrites", "### positioning", 1)
        markdown = markdown.replace("### TEMPORARY", "### rewrites", 1)
        self.assertIn(
            "debug appendix sections are missing, duplicated, or out of order",
            validator.validate_client_report(
                markdown,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_debug_appendix_rejects_a_duplicate_legacy_section(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        duplicate = (
            "\n### coach_brief\n\n"
            "- verified: candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=duplicate\n"
        )
        self.assertIn(
            "debug appendix sections are missing, duplicated, or out of order",
            validator.validate_client_report(
                report + duplicate,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_debug_appendix_rejects_cross_candidate_identity(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        markdown = report.replace(
            "candidate_id=CANDIDATE-JSC1-SYNTH",
            "candidate_id=CANDIDATE-JSC2-SYNTH",
            1,
        )
        self.assertIn(
            "debug appendix candidate_id must match fixture internal_candidate_id",
            validator.validate_client_report(
                markdown,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_debug_candidate_identity_cannot_be_supplied_by_free_form_prose(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        markdown = report.replace(
            "## Apéndice de evidencia\n",
            "## Apéndice de evidencia\n\ncandidate_id=CANDIDATE-JSC1-SYNTH\n",
            1,
        )
        markdown = markdown.replace("candidate_id=CANDIDATE-JSC1-SYNTH; ", "alpha=one; ")
        self.assertIn(
            "debug appendix candidate_id must match fixture internal_candidate_id",
            validator.validate_client_report(
                markdown,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_every_debug_canonical_row_requires_exactly_one_candidate_id(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        missing = report.replace(
            "candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=client_first_summary",
            "alpha=one; coach_brief=client_first_summary",
            1,
        )
        duplicate = report.replace(
            "candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=client_first_summary",
            "candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=client_first_summary; "
            "candidate_id=CANDIDATE-JSC1-SYNTH",
            1,
        )
        for case, markdown in (("missing", missing), ("duplicate", duplicate)):
            with self.subTest(case=case):
                self.assertIn(
                    "debug appendix candidate_id must match fixture internal_candidate_id",
                    validator.validate_client_report(
                        markdown,
                        self.bundle("scenario-a.json"),
                        appendix_mode="debug",
                    ),
                )

    def test_debug_appendix_rejects_candidate_id_tokens_outside_canonical_rows(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        cases = (
            "candidate_id=CANDIDATE-JSC1-SYNTH",
            "(candidate_id=CANDIDATE-JSC2-SYNTH)",
        )
        for token in cases:
            with self.subTest(token=token):
                markdown = report.replace(
                    "## Apéndice de evidencia\n",
                    f"## Apéndice de evidencia\n\n{token}\n",
                    1,
                )
                self.assertIn(
                    "debug appendix candidate_id must match fixture internal_candidate_id",
                    validator.validate_client_report(
                        markdown,
                        self.bundle("scenario-a.json"),
                        appendix_mode="debug",
                    ),
                )

    def test_expanded_candidate_identifier_is_allowed_only_in_exact_candidate_id_value_spans(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        cases = (
            report + "\n\nCANDIDATE-JSC1-SYNTH\n",
            report.replace(
                "candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=client_first_summary",
                "candidate_id=CANDIDATE-JSC1-SYNTH; note=CANDIDATE-JSC1-SYNTH; "
                "coach_brief=client_first_summary",
                1,
            ),
        )
        for markdown in cases:
            with self.subTest(marker=markdown[-80:]):
                self.assertIn(
                    "client report contains forbidden internal candidate identifier",
                    validator.validate_client_report(
                        markdown,
                        self.bundle("scenario-a.json"),
                        appendix_mode="debug",
                    ),
                )

    def test_debug_appendix_rejects_a_canonical_row_before_the_boundary(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        row = "- verified: candidate_id=CANDIDATE-JSC1-SYNTH; misplaced_row=true"
        markdown = report.replace("## Veredicto\n", f"## Veredicto\n\n{row}\n", 1)
        self.assertIn(
            "client report cannot contain legacy contract markers",
            validator.validate_client_report(
                markdown,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_debug_appendix_rejects_a_partial_appendix_even_with_a_valid_row(self) -> None:
        report = self.report("scenario-a-es.md").split("\n## Apéndice de evidencia\n", 1)[0]
        report += (
            "\n## Apéndice de evidencia\n\n### coach_brief\n\n"
            "- verified: candidate_id=CANDIDATE-JSC1-SYNTH; coach_brief=partial\n"
        )
        self.assertIn(
            "debug appendix sections are missing, duplicated, or out of order",
            validator.validate_client_report(
                report,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )

    def test_each_debug_section_requires_a_canonical_row(self) -> None:
        report = self.report("scenario-a-es-debug.md")
        markdown = report.replace(
            "- candidate-reported: candidate_id=CANDIDATE-JSC1-SYNTH; rewrites=private_review_drafts",
            "Narrative without a canonical row.",
            1,
        )
        self.assertIn(
            "legacy appendix section rewrites requires at least one canonical row",
            validator.validate_client_report(
                markdown,
                self.bundle("scenario-a.json"),
                appendix_mode="debug",
            ),
        )


class LinkedInClientReportDecisionTests(unittest.TestCase):
    def report(self, name: str) -> str:
        return (FIXTURE_ROOT / name).read_text(encoding="utf-8")

    def bundle(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def replace_once(self, text: str, old: str, new: str) -> str:
        self.assertEqual(1, text.count(old), f"mutation source must occur exactly once: {old}")
        return text.replace(old, new, 1)

    def test_localized_priority_and_copy_blocks_parse_into_structured_decisions(self) -> None:
        cases = (
            ("scenario-a-es.md", "es", "headline"),
            ("scenario-b-en.md", "en", "about_opening"),
        )
        for name, expected_locale, expected_primary_copy in cases:
            with self.subTest(report=name):
                if not hasattr(validator, "parse_priority_blocks"):
                    self.fail("validator must expose parse_priority_blocks")
                if not hasattr(validator, "parse_copy_blocks"):
                    self.fail("validator must expose parse_copy_blocks")
                parsed = validator.parse_client_report(self.report(name))
                priorities = validator.parse_priority_blocks(parsed)
                copies = validator.parse_copy_blocks(parsed)
                self.assertEqual(expected_locale, parsed.locale)
                self.assertEqual((1, 2, 3), tuple(priority.rank for priority in priorities))
                self.assertEqual(
                    {"headline", "about_opening", "experience_bullet"},
                    {copy_block.section for copy_block in copies},
                )
                self.assertEqual(
                    expected_primary_copy,
                    validator.parse_visible_primary_copy_category(parsed),
                )

    def test_priority_fingerprint_is_structured_and_ordered(self) -> None:
        if not hasattr(validator, "priority_fingerprint"):
            self.fail("validator must expose priority_fingerprint")
        priority = self.bundle("scenario-a.json")["priorities"][0]
        self.assertEqual(
            (
                "headline",
                "GAP-A-PRIMARY",
                "ACTION-A-HEADLINE",
                ("EVID-JSC1-PRIORITY-1",),
                "DONE-WHEN-A-1",
            ),
            validator.priority_fingerprint(priority),
        )

    def test_canonical_fixtures_keep_closed_priority_action_enums(self) -> None:
        report = self.report("scenario-a-es.md")
        base_bundle = self.bundle("scenario-a.json")
        for action_type in (
            "REWRITE_TARGET_ROLE",
            "EMAIL_RECRUITER_NOW",
            "CONTACT_RECRUITER_NOW",
            "SCHEDULE_INTERVIEW_NOW",
            "OUTREACH_TO_RECRUITER",
        ):
            with self.subTest(action_type=action_type):
                mutant = self.replace_once(
                    report,
                    "ACTION-A-HEADLINE",
                    action_type,
                )
                bundle = copy.deepcopy(base_bundle)
                bundle["priorities"][0]["action_type"] = action_type

                errors = validator.validate_client_report(mutant, bundle)

                self.assertIn("priorities[0] has invalid action_type", errors)

    def test_canonical_contract_cannot_be_renamed_into_generic_mode(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "ACTION-A-HEADLINE",
            "REWRITE_TARGET_ROLE",
        )
        identity_pairs = (
            ("FIXTURE-JSC9-RENAMED", "CANDIDATE-JSC1-SYNTH"),
            ("FIXTURE-JSC1-TECHNICAL-SIGNAL-DISPERSED", "CANDIDATE-JSC9-SYNTH-RENAMED"),
            ("FIXTURE-JSC1-TECHNICAL-SIGNAL-DISPERSED", "CANDIDATE-JSC2-SYNTH"),
            ("FIXTURE-JSC1-RENAMED", "CANDIDATE-JSC9-SYNTH-RENAMED"),
            ("FIXTURE-JSC9-RENAMED", "CANDIDATE-JSC1-SYNTH-RENAMED"),
        )
        for fixture_id, candidate_id in identity_pairs:
            with self.subTest(
                fixture_id=fixture_id,
                candidate_id=candidate_id,
            ):
                bundle = self.bundle("scenario-a.json")
                bundle["fixture_id"] = fixture_id
                bundle["internal_candidate_id"] = candidate_id
                bundle["priorities"][0]["action_type"] = "REWRITE_TARGET_ROLE"

                errors = validator.validate_client_report(report, bundle)

                self.assertIn(
                    "fixture and internal_candidate_id discriminators must match",
                    errors,
                )
                self.assertIn("priorities[0] has invalid action_type", errors)

    def test_report_requires_exactly_three_complete_priorities(self) -> None:
        report = self.report("scenario-a-es.md")
        missing_block = self.replace_once(report, "### 3. Experiencia", "#### 3. Experiencia")
        missing_field = self.replace_once(
            report,
            "- Tiempo: `TIMEBOX-A-1`",
            "- Duración: `TIMEBOX-A-1`",
        )
        bundle = self.bundle("scenario-a.json")
        self.assertIn(
            "report requires exactly three complete priorities",
            validator.validate_client_report(missing_block, bundle),
        )
        self.assertIn(
            "priority 1 missing required field: timebox",
            validator.validate_client_report(missing_field, bundle),
        )

    def test_report_requires_exactly_three_complete_copy_categories(self) -> None:
        report = self.replace_once(
            self.report("scenario-b-en.md"),
            "### Experience bullet",
            "#### Experience bullet",
        )
        self.assertIn(
            "report copy must cover exactly headline, about_opening, and experience_bullet",
            validator.validate_client_report(report, self.bundle("scenario-b.json")),
        )

    def test_decision_references_use_the_evidence_and_fact_namespaces(self) -> None:
        report = self.report("scenario-a-es.md")
        cases = (
            (
                self.replace_once(report, "EVID-JSC1-PRIORITY-1", "FACT-JSC1-READY"),
                "priority 1 references unknown evidence",
            ),
            (
                self.replace_once(report, "FACT-JSC1-READY", "EVID-JSC1-HEADLINE"),
                "copy headline references unknown fact",
            ),
            (
                self.replace_once(report, "EVID-JSC1-PRIORITY-1", "EVID-JSC1-MISSING"),
                "priority 1 references unknown evidence",
            ),
        )
        bundle = self.bundle("scenario-a.json")
        for mutant, expected in cases:
            with self.subTest(expected=expected):
                self.assertTrue(
                    any(expected in error for error in validator.validate_client_report(mutant, bundle))
                )

    def test_unknown_reference_errors_do_not_echo_supplied_values(self) -> None:
        report = self.report("scenario-a-es.md")
        for sentinel in ("person@example.com", "EVID-JSC1-PRIVATE"):
            with self.subTest(sentinel=sentinel):
                mutant = self.replace_once(report, "EVID-JSC1-PRIORITY-1", sentinel)

                errors = validator.validate_client_report(
                    mutant, self.bundle("scenario-a.json")
                )

                self.assertTrue(
                    any(
                        "priority 1 references unknown evidence" in error
                        for error in errors
                    )
                )
                self.assertNotIn(sentinel, "\n".join(errors))

    def test_duplicate_priority_fingerprints_are_rejected(self) -> None:
        report = self.report("scenario-a-es.md")
        replacements = {
            "### 2. Acerca de": "### 2. Titular",
            "GAP-A-SECONDARY": "GAP-A-PRIMARY",
            "ACTION-A-ABOUT": "ACTION-A-HEADLINE",
            "EVID-JSC1-PRIORITY-2": "EVID-JSC1-PRIORITY-1",
            "DONE-WHEN-A-2": "DONE-WHEN-A-1",
        }
        for old, new in replacements.items():
            report = self.replace_once(report, old, new)
        self.assertIn(
            "report priorities must have three distinct fingerprints",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_generic_priority_codes_are_rejected_even_with_metadata(self) -> None:
        report = self.report("scenario-a-es.md")
        cases = (
            ("GAP-A-PRIMARY", "improve_profile"),
            ("ACTION-A-HEADLINE", "add_keywords"),
            ("ACTION-A-HEADLINE", "create_content"),
        )
        for old, generic in cases:
            with self.subTest(code=generic):
                mutant = self.replace_once(report, old, generic)
                self.assertIn(
                    f"generic priority code is not allowed: {generic}",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )

    def test_ready_copy_cannot_use_unconfirmed_fact(self) -> None:
        bundle = self.bundle("scenario-a.json")
        unknown_fact = next(
            fact
            for fact in bundle["synthetic_fact_catalog"]
            if fact["evidence_state"] == "unknown"
        )
        bundle["copy_blocks"][0]["fact_ids"].append(unknown_fact["fact_id"])
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "- Hechos: `FACT-JSC1-READY`",
            f"- Hechos: `FACT-JSC1-READY`, `{unknown_fact['fact_id']}`",
        )
        self.assertIn(
            f"ready copy references unsupported fact {unknown_fact['fact_id']}",
            validator.validate_client_report(report, bundle),
        )

    def test_ready_copy_cannot_duplicate_a_blocked_claim(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["blocked_claims"].append("FACT-JSC1-READY")
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "- Claim bloqueado: `CAPABILITY_UNVERIFIED`",
            "- Claim bloqueado: `CAPABILITY_UNVERIFIED`\n- Claim bloqueado: `FACT-JSC1-READY`",
        )
        self.assertIn(
            "blocked_claims has invalid value: FACT-JSC1-READY",
            validator.validate_client_report(report, bundle),
        )

    def test_confirmation_state_requires_an_unconfirmed_fact(self) -> None:
        bundle = self.bundle("scenario-a.json")
        unknown_fact = next(
            fact
            for fact in bundle["synthetic_fact_catalog"]
            if fact["fact_id"] == "FACT-JSC1-UNKNOWN"
        )
        unknown_fact["evidence_state"] = "verified"
        self.assertIn(
            "copy about_opening requires confirmation but has no unconfirmed fact",
            validator.validate_client_report(self.report("scenario-a-es.md"), bundle),
        )

    def test_do_not_change_has_at_most_three_explicit_items(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "## Plan privado de siete días",
            "- Claim bloqueado: `ONE`\n- Claim bloqueado: `TWO`\n- Claim bloqueado: `THREE`\n\n## Plan privado de siete días",
        )
        self.assertIn(
            "do not change section must contain at most three explicit items",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_commonmark_plus_items_count_toward_do_not_change_limit(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "## Plan privado de siete días",
            "+ Primer item\n+ Segundo item\n+ Tercer item\n\n## Plan privado de siete días",
        )
        self.assertIn(
            "do not change section must contain at most three explicit items",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_visible_blocked_claim_accepts_commonmark_plus_marker(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "- Claim bloqueado: `CAPABILITY_UNVERIFIED`",
            "+ Claim bloqueado: `CAPABILITY_UNVERIFIED`",
        )
        self.assertEqual(
            [],
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_private_seven_day_plan_rejects_outreach_and_external_work(self) -> None:
        baseline = self.report("scenario-b-en.md")
        mutants = (
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "- Outreach: PROFILE_REVIEW|about_opening",
            ),
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "- Profile: apply for a role and contact recruiters on LinkedIn.",
            ),
            self.replace_once(
                baseline,
                "No external action is performed.",
                "Apply for roles and prepare interviews externally.",
            ),
            self.replace_once(
                baseline,
                "No external action is performed.",
                "1. Apply for roles and contact recruiters.",
            ),
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "1. Learning: review an unrelated course.",
            ),
            self.replace_once(
                baseline,
                "No external action is performed.",
                "Reach out to recruiters during the week.",
            ),
            self.replace_once(
                baseline,
                "No external action is performed.",
                "Study an unrelated course during the week.",
            ),
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "1. Profile: messaged recruiters about open roles.",
            ),
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "- Profile: connected with recruiters.",
            ),
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "- Profile: published the revised headline.",
            ),
            self.replace_once(
                baseline,
                "- Profile: PROFILE_REVIEW|about_opening",
                "- Profile: complete an unrelated course.",
            ),
            self.replace_once(
                self.report("scenario-a-es.md"),
                "No se ejecuta ninguna acción externa.",
                "Me postulé a vacantes durante la semana.",
            ),
            self.replace_once(
                self.report("scenario-a-es.md"),
                "- Perfil: PROFILE_REVIEW|headline",
                "- Perfil: mensajear y contactar reclutadores.",
            ),
        )
        for report in mutants:
            with self.subTest(report=report):
                bundle_name = (
                    "scenario-a.json"
                    if report.startswith("# Diagnóstico ejecutivo")
                    else "scenario-b.json"
                )
                self.assertIn(
                    "private seven-day plan requires closed action and target codes",
                    validator.validate_client_report(report, self.bundle(bundle_name)),
                )

    def test_private_plan_rejects_action_synonyms_structurally(self) -> None:
        english = self.report("scenario-b-en.md")
        spanish = self.report("scenario-a-es.md")
        cases = (
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: EMAIL candidates."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: send role mail."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: invite peers."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: send invitations."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: follow peers."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: comment weekly."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: endorse peers."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: like updates."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: share the headline."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: review recruiter notes."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: research companies."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: review connections."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: draft a post."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: grow the network."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: make a call."),
            (english, "- Profile: PROFILE_REVIEW|about_opening", "- Profile: schedule reviews."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: enviar CORRÉO a colegas."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: invitar colegas."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: seguir colegas."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: comentar semanalmente."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: recomendar colegas."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: dar me gusta a novedades."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: revisar reclutadores."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: investigar empresas."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: revisar conexiones."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: crear una publicación."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: ampliar la red profesional."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: hacer llamadas."),
            (spanish, "- Perfil: PROFILE_REVIEW|headline", "- Perfil: agendar revisiones."),
        )
        for baseline, old, new in cases:
            with self.subTest(action=new):
                report = self.replace_once(baseline, old, new)
                bundle_name = (
                    "scenario-a.json"
                    if report.startswith("# Diagnóstico ejecutivo")
                    else "scenario-b.json"
                )
                self.assertIn(
                    "private seven-day plan requires closed action and target codes",
                    validator.validate_client_report(report, self.bundle(bundle_name)),
                )

    def test_private_plan_requires_closed_action_target_grammar(self) -> None:
        report = self.report("scenario-a-es.md")
        self.assertEqual(
            [],
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )
        mutations = (
            ("PROFILE_REVIEW|headline", "PROFILE_REWRITE|headline"),
            ("PROFILE_REVIEW|headline", "PROFILE_REVIEW|title"),
            ("PROFILE_REVIEW|headline", "PROFILE_REVIEW|pending_fact"),
            ("PROFILE_REVIEW|headline", "COPY_VALIDATE|about_opening"),
            ("PROFILE_REVIEW|headline", "PROFILE_REVIEW|headline after review"),
            ("PROFILE_REVIEW|headline", "PROFILE_REVIEW|headline|extra"),
            ("PROFILE_REVIEW|headline", "review the headline"),
        )
        for old, new in mutations:
            with self.subTest(payload=new):
                mutant = self.replace_once(report, old, new)
                self.assertIn(
                    "private seven-day plan requires closed action and target codes",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )

    def test_priority_impact_basis_requires_a_supported_coach_heuristic(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["priorities"][0]["impact_basis"] = "CURRENT_OFFICIAL_SOURCE"
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "- Terminado cuando: `DONE-WHEN-A-1`\n- Base de impacto: `COACH_HEURISTIC`",
            "- Terminado cuando: `DONE-WHEN-A-1`\n- Base de impacto: `CURRENT_OFFICIAL_SOURCE`",
        )
        self.assertIn(
            "priority 1 impact basis must be COACH_HEURISTIC without direct official support",
            validator.validate_client_report(report, bundle),
        )

    def test_evidence_question_must_change_the_decision_that_uses_its_fact(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "`copy:about_opening`",
            "`copy:headline`",
        )
        self.assertIn(
            "evidence question 1 does not change its declared decision",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_scenario_c_requests_only_the_minimum_decision_changing_evidence(self) -> None:
        baseline = self.report("scenario-c-es.md")
        duplicate = self.replace_once(
            baseline,
            "## Límites del diagnóstico",
            (
                "### Pregunta 2\n\n"
                "- Pregunta: ¿Cuál es el alcance confirmado del ejemplo de experiencia?\n"
                "- Hecho: `FACT-JSC3-UNKNOWN`\n"
                "- Puede cambiar: `copy:experience_bullet`\n\n"
                "## Límites del diagnóstico"
            ),
        )
        missing = self.replace_once(baseline, "### Pregunta 1", "#### Pregunta 1")
        arbitrary_priority = self.replace_once(
            baseline,
            "## Límites del diagnóstico",
            (
                "### Pregunta 2\n\n"
                "- Pregunta: ¿Cambiaría este hecho una prioridad sin relación?\n"
                "- Hecho: `FACT-JSC3-UNKNOWN`\n"
                "- Puede cambiar: `priority:1`\n\n"
                "## Límites del diagnóstico"
            ),
        )
        for report in (duplicate, missing, arbitrary_priority):
            with self.subTest(report=report):
                self.assertIn(
                    "pending evidence questions must exactly match confirmation copy decisions",
                    validator.validate_client_report(report, self.bundle("scenario-c.json")),
                )

    def test_copy_requires_actual_text_and_claims_bound_to_fact_tokens(self) -> None:
        baseline = self.report("scenario-a-es.md")
        mutants = (
            (
                self.replace_once(
                    baseline,
                    "- Frontera del claim: `USE_ONLY_SUPPORTED_FACTS`\n- Copy: presentar confiabilidad de plataformas y alcance de equipo.",
                    "- Frontera del claim: `USE_ONLY_SUPPORTED_FACTS`",
                ),
                "copy headline requires nonempty actual copy",
            ),
            (
                self.replace_once(
                    baseline,
                    "- Claims: `RELIABILITY`, `TECHNICAL_SCOPE`",
                    "- Claims: `AUTOMATION`",
                ),
                "copy headline claims do not match referenced fact tokens",
            ),
            (
                self.replace_once(
                    baseline,
                    "- Claims: ninguno",
                    "- Claims: `OUTCOME_SCOPE`",
                ),
                "copy experience_bullet omit state requires empty claims",
            ),
        )
        for report, expected in mutants:
            with self.subTest(expected=expected):
                self.assertIn(
                    expected,
                    validator.validate_client_report(report, self.bundle("scenario-a.json")),
                )

    def test_uncontrolled_claim_errors_do_not_echo_supplied_values(self) -> None:
        baseline = self.report("scenario-a-es.md")
        claim_fields = (
            (
                "headline",
                "- Claims: `RELIABILITY`, `TECHNICAL_SCOPE`",
                "- Claims: `{sentinel}`",
            ),
            (
                "about_opening",
                "- Claims: `AUTOMATION`",
                "- Claims: `{sentinel}`",
            ),
            (
                "experience_bullet",
                "- Claims: ninguno",
                "- Claims: `{sentinel}`",
            ),
        )
        for sentinel in ("person@example.com", "EVID-JSC1-PRIVATE"):
            for section, original, replacement in claim_fields:
                with self.subTest(sentinel=sentinel, section=section):
                    report = self.replace_once(
                        baseline,
                        original,
                        replacement.format(sentinel=sentinel),
                    )
                    errors = validator.validate_client_report(
                        report,
                        self.bundle("scenario-a.json"),
                    )
                    self.assertTrue(
                        any(
                            f"copy {section} has uncontrolled claim" in error
                            for error in errors
                        )
                    )
                    self.assertNotIn(sentinel, "\n".join(errors))

    def test_actual_copy_and_claims_cannot_expose_a_blocked_claim_code(self) -> None:
        baseline = self.report("scenario-a-es.md")
        mutants = (
            self.replace_once(
                baseline,
                "presentar confiabilidad de plataformas y alcance de equipo.",
                "presentar CAPABILITY_UNVERIFIED como capacidad confirmada.",
            ),
            self.replace_once(
                baseline,
                "- Claims: `RELIABILITY`, `TECHNICAL_SCOPE`",
                "- Claims: `RELIABILITY`, `TECHNICAL_SCOPE`, `CAPABILITY_UNVERIFIED`",
            ),
        )
        for report in mutants:
            with self.subTest(report=report):
                self.assertIn(
                    "copy headline exposes blocked claim CAPABILITY_UNVERIFIED",
                    validator.validate_client_report(report, self.bundle("scenario-a.json")),
                )

    def test_actual_copy_cannot_expose_undeclared_or_unsupported_fact_tokens(self) -> None:
        baseline = self.report("scenario-a-es.md")
        for token in ("AUTOMATION", "automation"):
            with self.subTest(token=token):
                report = self.replace_once(
                    baseline,
                    "presentar confiabilidad de plataformas y alcance de equipo.",
                    f"presentar {token} como capacidad confirmada y lista para publicar.",
                )
                self.assertIn(
                    "copy headline actual copy exposes undeclared or unsupported claim AUTOMATION",
                    validator.validate_client_report(report, self.bundle("scenario-a.json")),
                )

    def test_actual_copy_normalizes_controlled_claim_and_blocked_code_variants(self) -> None:
        baseline = self.report("scenario-a-es.md")
        cases = (
            (
                "automation-enabled",
                "copy headline actual copy exposes undeclared or unsupported claim AUTOMATION",
            ),
            (
                "AuToMaTiOn_enabled",
                "copy headline actual copy exposes undeclared or unsupported claim AUTOMATION",
            ),
            (
                "AUTO-MATION",
                "copy headline actual copy exposes undeclared or unsupported claim AUTOMATION",
            ),
            (
                "AUTO_MATION",
                "copy headline actual copy exposes undeclared or unsupported claim AUTOMATION",
            ),
            (
                "A U T O M A T I O N",
                "copy headline actual copy exposes undeclared or unsupported claim AUTOMATION",
            ),
            (
                "capability_unverified",
                "copy headline exposes blocked claim CAPABILITY_UNVERIFIED",
            ),
            (
                "capability-unverified",
                "copy headline exposes blocked claim CAPABILITY_UNVERIFIED",
            ),
            (
                "CaPaBiLiTy UnVeRiFiEd",
                "copy headline exposes blocked claim CAPABILITY_UNVERIFIED",
            ),
            (
                "CAPA-BILITY_UNVERIFIED",
                "copy headline exposes blocked claim CAPABILITY_UNVERIFIED",
            ),
        )
        for exposed_code, expected in cases:
            with self.subTest(exposed_code=exposed_code):
                report = self.replace_once(
                    baseline,
                    "presentar confiabilidad de plataformas y alcance de equipo.",
                    f"presentar {exposed_code} como capacidad confirmada.",
                )
                self.assertIn(
                    expected,
                    validator.validate_client_report(report, self.bundle("scenario-a.json")),
                )

    def test_pending_evidence_requires_meaningful_question_text(self) -> None:
        baseline = self.report("scenario-a-es.md")
        original = (
            "¿La capacidad de automatización fue utilizada directamente y qué alcance "
            "puede describirse sin revelar información confidencial?"
        )
        for replacement in ("", "TBD", "Pregunta pendiente"):
            with self.subTest(replacement=replacement):
                report = self.replace_once(baseline, original, replacement)
                self.assertIn(
                    "evidence question 1 requires meaningful question text",
                    validator.validate_client_report(report, self.bundle("scenario-a.json")),
                )

    def test_visible_primary_copy_category_must_match_bundle_expectation(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "- Categoría de copy principal: `headline`",
            "- Categoría de copy principal: `about_opening`",
        )
        self.assertIn(
            "visible primary copy category does not match fixture",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_decision_reference_lists_are_duplicate_free_in_bundle_and_report(self) -> None:
        baseline = self.report("scenario-a-es.md")
        cases = (
            (
                ("priorities", 0, "evidence_ids"),
                "EVID-JSC1-PRIORITY-1",
                "- Evidencia: `EVID-JSC1-PRIORITY-1`",
                "- Evidencia: `EVID-JSC1-PRIORITY-1`, `EVID-JSC1-PRIORITY-1`",
                "priority 1 has duplicate evidence EVID-JSC1-PRIORITY-1",
                "priorities[0].evidence_ids has duplicate evidence_id: EVID-JSC1-PRIORITY-1",
            ),
            (
                ("copy_blocks", 0, "fact_ids"),
                "FACT-JSC1-READY",
                "- Hechos: `FACT-JSC1-READY`",
                "- Hechos: `FACT-JSC1-READY`, `FACT-JSC1-READY`",
                "copy headline has duplicate fact FACT-JSC1-READY",
                "copy_blocks[0].fact_ids has duplicate fact_id: FACT-JSC1-READY",
            ),
            (
                ("copy_blocks", 0, "evidence_ids"),
                "EVID-JSC1-HEADLINE",
                "- Evidencia: `EVID-JSC1-HEADLINE`",
                "- Evidencia: `EVID-JSC1-HEADLINE`, `EVID-JSC1-HEADLINE`",
                "copy headline has duplicate evidence EVID-JSC1-HEADLINE",
                "copy_blocks[0].evidence_ids has duplicate evidence_id: EVID-JSC1-HEADLINE",
            ),
        )
        for path, duplicate, old, new, report_error, bundle_error in cases:
            with self.subTest(path=path):
                bundle = self.bundle("scenario-a.json")
                target = bundle[path[0]][path[1]][path[2]]
                target.append(duplicate)
                report = self.replace_once(baseline, old, new)
                self.assertIn(bundle_error, validator.validate_client_report(report, bundle))
                self.assertIn(bundle_error, validator.validate_fixture_bundle(bundle))

    def test_untrusted_parser_and_generic_diagnostics_redact_api_and_cli(self) -> None:
        sentinel = "/Users/PRIVATE_SENTINEL/parser.json"
        baseline = self.report("scenario-a-es.md")
        cases = (
            (
                "| Identidad visual | Evaluada | 60 |",
                f"| {sentinel} | Evaluada | 60 |",
                "score table has unknown dimension: <redacted-field>",
            ),
            (
                "### Titular",
                f"### {sentinel}",
                "copy section has unexpected H3: <redacted-field>",
            ),
            (
                "- Acción: `ACTION-A-HEADLINE`",
                f"- Acción: `{sentinel}/profile/improve`",
                "generic priority code is not allowed: <redacted-field>",
            ),
        )
        for old, new, expected in cases:
            with self.subTest(expected=expected):
                report = self.replace_once(baseline, old, new)
                errors = validator.validate_client_report(report, self.bundle("scenario-a.json"))
                self.assertIn(expected, errors)
                self.assertNotIn(sentinel, "\n".join(errors))

                with tempfile.TemporaryDirectory() as temporary:
                    report_path = Path(temporary) / "parser-sentinel.md"
                    report_path.write_text(report, encoding="utf-8")
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            str(VALIDATOR_PATH),
                            str(report_path),
                            str(FIXTURE_ROOT / "scenario-a.json"),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(2, result.returncode)
                self.assertIn(expected, result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_cli_bounds_large_report_diagnostic_output(self) -> None:
        baseline = self.report("scenario-a-es.md")
        extra_priorities = "".join(f"### {rank}. Titular\n\n" for rank in range(4, 5004))
        report = baseline.replace("## Copy listo para revisar", extra_priorities + "## Copy listo para revisar", 1)
        with tempfile.TemporaryDirectory() as temporary:
            report_path = Path(temporary) / "oversized-diagnostics.md"
            bundle_path = Path(temporary) / "bundle.json"
            report_path.write_text(report, encoding="utf-8")
            bundle_path.write_text(json.dumps(self.bundle("scenario-a.json")), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR_PATH), str(report_path), str(bundle_path)],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(2, result.returncode)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 16_384)
        self.assertTrue(result.stderr.endswith("validation diagnostics truncated; additional errors omitted\n"))

    def test_report_duplicate_reference_diagnostics_redact_untrusted_values_api_and_cli(self) -> None:
        sentinel = "/Users/PRIVATE_SENTINEL/reference.json"
        baseline = self.report("scenario-a-es.md")
        cases = (
            (
                "- Evidencia: `EVID-JSC1-PRIORITY-1`",
                f"- Evidencia: `{sentinel}`, `{sentinel}`",
                f"priority 1 has duplicate evidence <redacted-value>",
            ),
            (
                "- Hechos: `FACT-JSC1-READY`",
                f"- Hechos: `{sentinel}`, `{sentinel}`",
                f"copy headline has duplicate fact <redacted-value>",
            ),
            (
                "- Evidencia: `EVID-JSC1-HEADLINE`",
                f"- Evidencia: `{sentinel}`, `{sentinel}`",
                f"copy headline has duplicate evidence <redacted-value>",
            ),
        )
        for old, new, expected in cases:
            with self.subTest(expected=expected):
                report = self.replace_once(baseline, old, new)
                errors = validator.validate_client_report(report, self.bundle("scenario-a.json"))
                self.assertIn(expected, errors)
                self.assertNotIn(sentinel, "\n".join(errors))

                with tempfile.TemporaryDirectory() as temporary:
                    report_path = Path(temporary) / "report.md"
                    report_path.write_text(report, encoding="utf-8")
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-B",
                            str(VALIDATOR_PATH),
                            str(report_path),
                            str(FIXTURE_ROOT / "scenario-a.json"),
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                self.assertEqual(2, result.returncode)
                self.assertIn(expected, result.stderr)
                self.assertNotIn(sentinel, result.stderr)

    def test_copy_section_rejects_unexpected_h3_blocks(self) -> None:
        extra = (
            "### Profile summary\n\n"
            "- ID: `COPY-JSC1-EXTRA`\n"
            "- Estado: listo\n"
            "- Audiencia: `RECRUITER`\n"
            "- Problema: `TECHNICAL_SIGNAL_DISPERSED`\n"
            "- Hechos: `FACT-JSC1-READY`\n"
            "- Claims: `RELIABILITY`, `TECHNICAL_SCOPE`\n"
            "- Evidencia: `EVID-JSC1-HEADLINE`\n"
            "- Frontera del claim: `USE_ONLY_SUPPORTED_FACTS`\n"
            "- Copy: resumen extra.\n\n"
        )
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "## No cambies todavía",
            extra + "## No cambies todavía",
        )
        self.assertIn(
            "copy section has unexpected H3: Profile summary",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_numbered_do_not_change_items_count_toward_the_limit(self) -> None:
        report = self.replace_once(
            self.report("scenario-a-es.md"),
            "## Plan privado de siete días",
            "1. Primer item\n2. Segundo item\n3. Tercer item\n\n## Plan privado de siete días",
        )
        self.assertIn(
            "do not change section must contain at most three explicit items",
            validator.validate_client_report(report, self.bundle("scenario-a.json")),
        )

    def test_scenarios_a_and_b_are_materially_different(self) -> None:
        if not hasattr(validator, "validate_report_pair_differentiation"):
            self.fail("validator must expose validate_report_pair_differentiation")
        errors = validator.validate_report_pair_differentiation(
            self.report("scenario-a-es.md"),
            self.bundle("scenario-a.json"),
            self.report("scenario-b-en.md"),
            self.bundle("scenario-b.json"),
        )
        self.assertEqual([], errors)

    def test_copying_a_decisions_into_b_fails_material_differentiation(self) -> None:
        if not hasattr(validator, "validate_report_pair_differentiation"):
            self.fail("validator must expose validate_report_pair_differentiation")
        report_a = self.report("scenario-a-es.md")
        copied = self.report("scenario-b-en.md")
        replacements = {
            "### 1. About": "### 1. Headline",
            "### 2. Experience": "### 2. About",
            "### 3. Proof": "### 3. Experience",
            "GAP-B-PRIMARY": "GAP-A-PRIMARY",
            "GAP-B-SECONDARY": "GAP-A-SECONDARY",
            "GAP-B-PROOF": "GAP-A-PROOF",
            "ACTION-B-ABOUT": "ACTION-A-HEADLINE",
            "ACTION-B-EXPERIENCE": "ACTION-A-ABOUT",
            "ACTION-B-HEADLINE": "ACTION-A-EXPERIENCE",
            "EVID-JSC2-PRIORITY-1": "EVID-JSC1-PRIORITY-1",
            "EVID-JSC2-PRIORITY-2": "EVID-JSC1-PRIORITY-2",
            "EVID-JSC2-PRIORITY-3": "EVID-JSC1-PRIORITY-3",
            "TIMEBOX-B-1": "TIMEBOX-A-1",
            "TIMEBOX-B-2": "TIMEBOX-A-2",
            "TIMEBOX-B-3": "TIMEBOX-A-3",
            "DONE-WHEN-B-1": "DONE-WHEN-A-1",
            "DONE-WHEN-B-2": "DONE-WHEN-A-2",
            "DONE-WHEN-B-3": "DONE-WHEN-A-3",
            "COPY-JSC2-PRIMARY": "COPY-JSC1-PRIMARY",
            "Primary copy category: `about_opening`": "Primary copy category: `headline`",
        }
        for old, new in replacements.items():
            copied = self.replace_once(copied, old, new)
        errors = validator.validate_report_pair_differentiation(
            report_a,
            self.bundle("scenario-a.json"),
            copied,
            self.bundle("scenario-b.json"),
        )
        self.assertIn("report pair must differ in at least two priority fingerprints", errors)
        self.assertIn("report pair must not reuse the same primary diagnosed gap", errors)
        self.assertIn("report B: copy about_opening does not match fixture copy_id", errors)
        self.assertIn("report pair must recommend a different primary copy category", errors)

    def test_pair_differentiation_binds_each_report_to_its_supplied_bundle(self) -> None:
        errors = validator.validate_report_pair_differentiation(
            self.report("scenario-a-es.md"),
            self.bundle("scenario-b.json"),
            self.report("scenario-b-en.md"),
            self.bundle("scenario-a.json"),
        )
        self.assertIn("report A: client report locale must match fixture locale", errors)
        self.assertIn("report B: client report locale must match fixture locale", errors)

    def test_malformed_decision_inputs_return_errors_instead_of_exceptions(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["priorities"] = {"not": "a list"}
        try:
            errors = validator.validate_client_report(self.report("scenario-a-es.md"), bundle)
        except Exception as error:  # pragma: no cover - the assertion names the regression
            self.fail(f"malformed decision bundle leaked {type(error).__name__}")
        self.assertIn("priorities must be a list", errors)
        malformed_report = self.replace_once(
            self.report("scenario-a-es.md"),
            "- Tiempo: `TIMEBOX-A-1`",
            "- Duración: `TIMEBOX-A-1`",
        )
        pair_errors = validator.validate_report_pair_differentiation(
            malformed_report,
            self.bundle("scenario-a.json"),
            self.report("scenario-b-en.md"),
            self.bundle("scenario-b.json"),
        )
        self.assertIn("report pair requires complete structured decisions", pair_errors)


class LinkedInClientReportSafetyTests(unittest.TestCase):
    def report(self, name: str = "scenario-a-es.md") -> str:
        return (FIXTURE_ROOT / name).read_text(encoding="utf-8")

    def bundle(self, name: str = "scenario-a.json") -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def add_to_verdict(self, text: str) -> str:
        return self.report().replace(
            "\n## Calificación\n",
            f"\n{text}\n\n## Calificación\n",
            1,
        )

    def complete_source_catalog(self, bundle: dict[str, object]) -> list[dict[str, object]]:
        return bundle["source_catalog"]

    def secondary_source(self) -> dict[str, object]:
        return {
            "source_id": "SOURCE-JSC1-SECONDARY-1",
            "source_category": "job_match",
            "source_class": "secondary",
            "url": "https://www.themuse.com/advice/linkedin-profile-tips",
            "publisher": "The Muse",
            "document_title": "LinkedIn Profile Tips",
            "access_date": "2026-08-01",
            "reachability": "reachable",
            "scope": "PROFILE_GUIDANCE",
            "inference_limit": "NO_INDIVIDUAL_OUTCOME_INFERENCE",
            "fallback": "COACH_HEURISTIC",
        }

    def test_report_privacy_scanner_rejects_recursive_contact_and_profile_values(self) -> None:
        cases = (
            ("Contacto: person@example.invalid", "client report contains forbidden email-like value"),
            ("Teléfono: +52 55 1234 5678", "client report contains forbidden phone-like value"),
            (
                "Perfil: https://www.linkedin.com/in/synthetic-sentinel/",
                "client report contains forbidden LinkedIn profile URL value",
            ),
            ("Archivo: /Users/synthetic/profile.txt", "client report contains forbidden local-path value"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_candidate_facing_privacy_rejects_legacy_linkedin_profile_url_forms(self) -> None:
        for value in (
            "https://www.linkedin.com/pub/synthetic-sentinel/42/7b/123",
            "www.linkedin.com/pub/synthetic-sentinel/42/7b/123",
            "linkedin.com/pub/synthetic-sentinel/42/7b/123",
        ):
            with self.subTest(value=value):
                errors = validator.validate_candidate_facing_text(value)
                self.assertIn(
                    "client report contains forbidden LinkedIn profile URL value",
                    errors,
                )
                self.assertNotIn(value, "\n".join(errors))

    def test_report_rejects_cross_candidate_identifiers_in_visible_and_normal_appendix_prose(self) -> None:
        foreign_bundle = self.bundle("scenario-b.json")
        tokens = (
            (
                foreign_bundle["structural_state_fixture"]["observations"][0]["evidence_id"],
                "client report references identifier outside fixture",
            ),
            (
                foreign_bundle["source_catalog"][0]["source_id"],
                "client report references identifier outside fixture",
            ),
            (
                foreign_bundle["internal_candidate_id"],
                "client report contains forbidden internal candidate identifier",
            ),
            (
                foreign_bundle["fixture_id"],
                "client report contains forbidden fixture identifier",
            ),
        )
        report = self.report()
        appendix_heading = "## Apéndice de evidencia"
        for token, expected in tokens:
            for layer, mutated in (
                (
                    "visible",
                    report.replace(
                        appendix_heading,
                        f"Referencia sintética: {token}.\n\n{appendix_heading}",
                        1,
                    ),
                ),
                ("normal_appendix", f"{report}\n\nReferencia sintética: {token}."),
            ):
                with self.subTest(layer=layer, token=token):
                    self.assertIn(
                        expected,
                        validator.validate_client_report(mutated, self.bundle()),
                    )

    def test_report_identifier_extraction_normalizes_unicode_separators_in_every_namespace_and_layer(self) -> None:
        foreign_bundle = self.bundle("scenario-b.json")
        tokens = (
            (
                foreign_bundle["fixture_id"],
                "client report contains forbidden fixture identifier",
            ),
            (
                foreign_bundle["internal_candidate_id"],
                "client report contains forbidden internal candidate identifier",
            ),
            (
                foreign_bundle["structural_state_fixture"]["observations"][0]["evidence_id"],
                "client report references identifier outside fixture",
            ),
            (
                foreign_bundle["synthetic_fact_catalog"][0]["fact_id"],
                "client report references identifier outside fixture",
            ),
            (
                foreign_bundle["source_catalog"][0]["source_id"],
                "client report references identifier outside fixture",
            ),
            (
                foreign_bundle["priorities"][0]["priority_id"],
                "client report references identifier outside fixture",
            ),
            (
                foreign_bundle["copy_blocks"][0]["copy_id"],
                "client report references identifier outside fixture",
            ),
        )
        separators = ("‐", "‑", "‒", "–", "—", "−", "⁃")
        report = self.report()
        appendix_heading = "## Apéndice de evidencia"
        for (token, expected), separator in zip(tokens, separators):
            unicode_token = token.replace("-", separator)
            for layer, mutated in (
                (
                    "visible",
                    report.replace(
                        appendix_heading,
                        f"Referencia sintética: {unicode_token}.\n\n{appendix_heading}",
                        1,
                    ),
                ),
                (
                    "normal_appendix",
                    f"{report}\n\nReferencia sintética: {unicode_token}.",
                ),
            ):
                with self.subTest(namespace=token.split("-", 1)[0], layer=layer):
                    self.assertIn(
                        expected,
                        validator.validate_client_report(mutated, self.bundle()),
                    )

    def test_fixture_identifier_grammar_rejects_single_suffix_forms(self) -> None:
        mutations = (
            (("fixture_id",), "FIXTURE-ONLY", "fixture has invalid fixture_id"),
            (
                ("internal_candidate_id",),
                "CANDIDATE-SYNTH-ONLY",
                "fixture has invalid internal_candidate_id",
            ),
            (
                ("structural_state_fixture", "observations", 0, "evidence_id"),
                "EVID-ONLY",
                "observation has invalid evidence_id",
            ),
            (
                ("synthetic_fact_catalog", 0, "fact_id"),
                "FACT-ONLY",
                "synthetic_fact_catalog[0] has invalid fact_id",
            ),
            (
                ("source_catalog", 0, "source_id"),
                "SOURCE-ONLY",
                "source_catalog[0] has invalid source_id",
            ),
            (
                ("priorities", 0, "priority_id"),
                "PRIORITY-ONLY",
                "priorities[0] has invalid priority_id",
            ),
            (
                ("copy_blocks", 0, "copy_id"),
                "COPY-ONLY",
                "copy_blocks[0] has invalid copy_id",
            ),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path):
                bundle = self.bundle()
                target = bundle
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = value

                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_identifier_grammar_requires_the_reserved_jsc_discriminator(self) -> None:
        cases = (
            ("fixture_id", "FIXTURE-B2B-TECHNICAL", "FIXTURE-JSC2-TECHNICAL"),
            (
                "internal_candidate_id",
                "CANDIDATE-V2-SYNTH",
                "CANDIDATE-JSC2-SYNTH",
            ),
            ("evidence_id", "EVID-P1-VISUAL", "EVID-JSC2-VISUAL"),
            ("fact_id", "FACT-SOC2-READY", "FACT-JSC2-READY"),
            ("source_id", "SOURCE-IPV6-OFFICIAL", "SOURCE-JSC2-OFFICIAL"),
            ("priority_id", "PRIORITY-P1-FIRST", "PRIORITY-JSC2-FIRST"),
            ("copy_id", "COPY-V2-PRIMARY", "COPY-JSC2-PRIMARY"),
        )
        for field, ambiguous, unambiguous in cases:
            with self.subTest(field=field, state="ambiguous"):
                self.assertIsNone(validator._ID_PATTERNS[field].fullmatch(ambiguous))
            with self.subTest(field=field, state="unambiguous"):
                self.assertIsNotNone(
                    validator._ID_PATTERNS[field].fullmatch(unambiguous)
                )

    def test_fixture_and_candidate_identifier_discriminators_must_match(self) -> None:
        bundle = self.bundle()
        bundle["fixture_id"] = "FIXTURE-JSC1-RENAMED"
        bundle["internal_candidate_id"] = "CANDIDATE-JSC2-SYNTH"

        self.assertIn(
            "fixture and internal_candidate_id discriminators must match",
            validator.validate_fixture_bundle(bundle),
        )

    def test_identifier_extraction_normalizes_every_separator_in_every_layer(self) -> None:
        tokens = (
            (
                "FIXTURE-JSC2-LEADERSHIP-STORY-GENERAL",
                "client report contains forbidden fixture identifier",
            ),
            (
                "CANDIDATE-JSC2-SYNTH",
                "client report contains forbidden internal candidate identifier",
            ),
            (
                "EVID-JSC2-VISUAL",
                "client report references identifier outside fixture",
            ),
            (
                "FACT-JSC2-READY",
                "client report references identifier outside fixture",
            ),
            (
                "SOURCE-JSC2-1",
                "client report references identifier outside fixture",
            ),
            (
                "PRIORITY-JSC2-1",
                "client report references identifier outside fixture",
            ),
            (
                "COPY-JSC2-PRIMARY",
                "client report references identifier outside fixture",
            ),
        )
        separators = ("_", "\u00ad", "‐", "‑", "‒", "–", "—", "―", "−", "⁃")
        report = self.report()
        appendix_heading = "## Apéndice de evidencia"
        for token, expected in tokens:
            for separator in separators:
                separated_token = token.replace("-", separator)
                for layer, mutated in (
                    (
                        "visible",
                        report.replace(
                            appendix_heading,
                            f"Referencia sintética: {separated_token}.\n\n{appendix_heading}",
                            1,
                        ),
                    ),
                    (
                        "normal_appendix",
                        f"{report}\n\nReferencia sintética: {separated_token}.",
                    ),
                ):
                    with self.subTest(
                        namespace=token.split("-", 1)[0],
                        separator=separator,
                        layer=layer,
                    ):
                        self.assertIn(
                            expected,
                            validator.validate_client_report(mutated, self.bundle()),
                        )

    def test_lowercase_foreign_identifiers_remain_forbidden_in_every_layer(self) -> None:
        tokens = (
            (
                "FIXTURE-JSC2-LEADERSHIP-STORY-GENERAL",
                "client report contains forbidden fixture identifier",
            ),
            (
                "CANDIDATE-JSC2-SYNTH",
                "client report contains forbidden internal candidate identifier",
            ),
            (
                "EVID-JSC2-VISUAL",
                "client report references identifier outside fixture",
            ),
            (
                "FACT-JSC2-READY",
                "client report references identifier outside fixture",
            ),
            (
                "SOURCE-JSC2-1",
                "client report references identifier outside fixture",
            ),
            (
                "PRIORITY-JSC2-1",
                "client report references identifier outside fixture",
            ),
            (
                "COPY-JSC2-PRIMARY",
                "client report references identifier outside fixture",
            ),
        )
        report = self.report()
        appendix_heading = "## Apéndice de evidencia"
        for token, expected in tokens:
            lowercase_token = token.lower()
            for layer, mutated in (
                (
                    "visible",
                    report.replace(
                        appendix_heading,
                        f"Referencia sintética: {lowercase_token}.\n\n{appendix_heading}",
                        1,
                    ),
                ),
                (
                    "normal_appendix",
                    f"{report}\n\nReferencia sintética: {lowercase_token}.",
                ),
            ):
                with self.subTest(namespace=token.split("-", 1)[0], layer=layer):
                    self.assertIn(
                        expected,
                        validator.validate_client_report(mutated, self.bundle()),
                    )

    def test_identifier_scanner_does_not_treat_ordinary_adjective_prose_as_ids(self) -> None:
        report = self.add_to_verdict(
            "Use fact-based, source-backed, priority-aware, and copy-ready review."
        )

        self.assertEqual([], validator.validate_client_report(report, self.bundle()))

    def test_identifier_scanner_does_not_treat_multiword_prose_as_ids(self) -> None:
        for phrase in (
            "source-code-based",
            "copy-review-ready",
            "fact-check-ready",
            "priority-skill-based",
            "source-AI-based",
            "copy-AI-ready",
            "priority-IT-driven",
            "fixture-UI-ready",
            "source-R-based",
            "source-B2B-ready",
            "copy-v2-ready",
            "priority-P1-driven",
            "fact-SOC2-ready",
            "source-IPv6-ready",
        ):
            with self.subTest(phrase=phrase):
                report = self.add_to_verdict(f"Use a {phrase} recommendation.")

                self.assertEqual(
                    [],
                    validator.validate_client_report(report, self.bundle()),
                )

    def test_report_rejects_raw_profile_aliases_and_private_analytics_values(self) -> None:
        cases = (
            ("raw_profile_text=synthetic biography", "client report contains forbidden raw-profile alias"),
            ("profile_ocr: synthetic transcription", "client report contains forbidden raw-profile alias"),
            ("analytics_value=47", "client report contains forbidden private analytics value"),
            ("search_appearances_count: 19", "client report contains forbidden private analytics value"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_hyphenated_placeholders_remain_forbidden(self) -> None:
        for marker, placeholder in (
            ("TBD-VALUE", "tbd"),
            ("GENERIC-COPY", "generic"),
            ("CRITERIA-PENDING", "criteria"),
        ):
            with self.subTest(marker=marker):
                errors = validator.validate_client_report(
                    self.add_to_verdict(marker),
                    self.bundle(),
                )
                self.assertIn(
                    f"client report contains forbidden placeholder: {placeholder}",
                    errors,
                )

    def test_case_insensitive_placeholders_are_blocking(self) -> None:
        for placeholder in ("x", "CRITERIA", "Generic", "tBd"):
            with self.subTest(placeholder=placeholder):
                self.assertIn(
                    f"client report contains forbidden placeholder: {placeholder.casefold()}",
                    validator.validate_client_report(
                        self.add_to_verdict(f"Valor provisional: {placeholder}"),
                        self.bundle(),
                    ),
                )

    def test_confirmation_marker_requires_a_decision_changing_question(self) -> None:
        report = self.add_to_verdict("[CONFIRMAR DESPUÉS]").replace(
            "### Pregunta 1", "#### Pregunta 1", 1
        )
        self.assertIn(
            "confirmation marker requires a concrete decision-changing question",
            validator.validate_client_report(report, self.bundle()),
        )

    def test_report_rejects_protected_trait_visual_inference(self) -> None:
        for text in (
            "La foto indica que la persona parece joven.",
            "Visual evidence suggests the person's gender.",
        ):
            with self.subTest(text=text):
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_protected_visual_inference_is_rejected_for_bounded_classes_in_both_locales(self) -> None:
        traits = (
            "age",
            "disability",
            "race",
            "gender",
            "health",
            "nationality",
            "pregnancy",
            "religion",
            "sexual orientation",
            "edad",
            "discapacidad",
            "raza",
            "género",
            "salud",
            "nacionalidad",
            "embarazo",
            "religión",
            "orientación sexual",
        )
        for trait in traits:
            text = (
                f"The photo suggests the candidate's {trait}."
                if trait in traits[:9]
                else f"La foto sugiere la {trait} de la persona."
            )
            with self.subTest(trait=trait):
                errors = validator.validate_client_report(
                    self.add_to_verdict(text),
                    self.bundle(),
                )
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    errors,
                )
                self.assertEqual(
                    1,
                    errors.count(
                        "client report cannot infer a protected trait from visual evidence"
                    ),
                )

    def test_protected_inference_is_bidirectional_with_predicate_scoped_negation(self) -> None:
        unsafe = (
            "The candidate's age appears evident in the photo.",
            "The candidate appears pregnant in the profile image.",
            "La nacionalidad parece evidente en la foto.",
            "La persona parece embarazada en la imagen del perfil.",
            "The photo is not current and suggests the candidate's age.",
            "La foto no está actualizada y sugiere la edad de la persona.",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_protected_inference_binds_visual_and_trait_to_one_predicate_clause(self) -> None:
        unsafe = (
            "The photo indicated the candidate's age.",
            "The candidate's religion is revealed by the photo.",
            "La foto infiere la edad de la persona.",
            "Infiero la nacionalidad a partir de la foto.",
            "The photo is not current and indicated the candidate's age.",
            "La foto no está actualizada e infiere la edad de la persona.",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_protected_inference_supports_predicate_chains_and_label_colons(self) -> None:
        unsafe = (
            "The photo suggested the candidate's age.",
            "The photo inferred the candidate's religion.",
            "The photo showed the candidate's pregnancy.",
            "La foto indicó la edad de la persona.",
            "La foto sugirió el género de la persona.",
            "La foto reveló la salud de la persona.",
            "Photo: suggested the candidate's age.",
            "Foto: sugirió la edad de la persona.",
            "The photo does not seem to indicate age, but the image suggested gender.",
            "La foto no permite inferir la edad, pero la imagen reveló el género.",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        boundaries = (
            "The photo does not seem to indicate the candidate's age.",
            "The photo cannot clearly indicate the candidate's age.",
            "La foto no permite claramente inferir la edad de la persona.",
            "Photo: does not seem to indicate the candidate's age.",
        )
        for text in boundaries:
            with self.subTest(kind="boundary", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        boundaries = (
            "The photo cannot reliably indicate the candidate's age.",
            "The photo can't reliably indicate the candidate's age.",
            "The photo doesn't indicate the candidate's age.",
            "The photo does not reliably indicate the candidate's age.",
            "La foto no permite inferir la edad de la persona.",
            "No podemos inferir la edad a partir de la foto.",
            "Do not infer age from the photo, but the copy suggests a stronger headline.",
            "No infieras la edad de la foto; la evidencia sugiere revisar el titular.",
        )
        for text in boundaries:
            with self.subTest(kind="boundary", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_protected_inference_handles_finite_appearance_and_full_negation_chains(self) -> None:
        unsafe = (
            "The photo looked old.",
            "The candidate appeared pregnant in the profile image.",
            "La foto parecía indicar que la persona era mayor.",
            "La persona aparentó estar embarazada en la foto.",
            "The photo does not suggest age and later appeared to show pregnancy.",
            "La foto no parece indicar la edad y después aparentó mostrar un embarazo.",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        boundaries = (
            "The photo does not suggest age and should not be used to infer pregnancy.",
            "The photo cannot be used to infer age.",
            "The photo is not able to indicate pregnancy.",
            "La foto no se puede usar para inferir la edad.",
        )
        for text in boundaries:
            with self.subTest(kind="boundary", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_protected_inference_binds_each_coordinated_predicate_complement(self) -> None:
        boundaries = (
            "The photo does not suggest age and looks professional.",
            "La foto no sugiere la edad y parece profesional.",
        )
        for text in boundaries:
            with self.subTest(kind="boundary", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        unsafe = (
            "The photo does not suggest age and looks old.",
            "La foto no sugiere la edad y parece embarazada.",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report cannot infer a protected trait from visual evidence",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        boundaries = (
            "Do not infer age from a photo.",
            "The photo does not indicate the candidate's religion.",
            "No infieras la edad a partir de una foto.",
            "La foto no sugiere la religión de la persona.",
        )
        for text in boundaries:
            with self.subTest(kind="boundary", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_report_rejects_claimed_external_action(self) -> None:
        for text in (
            "Se publicó el titular revisado en LinkedIn.",
            "Me postulé a la vacante desde LinkedIn.",
            "I connected with the recruiter on LinkedIn.",
        ):
            with self.subTest(text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_common_external_action_claims_are_rejected_in_both_locales(self) -> None:
        claims = (
            "I edited your LinkedIn profile.",
            "I updated your LinkedIn profile.",
            "I changed your LinkedIn headline.",
            "I sent the recruiter a message.",
            "I uploaded the asset to LinkedIn.",
            "I applied to the vacancy on LinkedIn.",
            "I scheduled the recruiter screen.",
            "I published the post on LinkedIn.",
            "I shared the post on LinkedIn.",
            "I connected with the recruiter on LinkedIn.",
            "Edité tu perfil de LinkedIn.",
            "Actualicé tu perfil de LinkedIn.",
            "Cambié tu titular de LinkedIn.",
            "Envié un mensaje al reclutador.",
            "Subí el recurso a LinkedIn.",
            "Me postulé a la vacante en LinkedIn.",
            "Programé la entrevista con reclutamiento.",
            "Publiqué el post en LinkedIn.",
            "Compartí el post en LinkedIn.",
            "Me conecté con el reclutador en LinkedIn.",
        )
        for text in claims:
            with self.subTest(text=text):
                errors = validator.validate_client_report(
                    self.add_to_verdict(text),
                    self.bundle(),
                )
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    errors,
                )
                self.assertEqual(
                    1,
                    errors.count(
                        "client report cannot claim an external action was executed"
                    ),
                )

    def test_completed_actions_preserve_diacritics_grammar_and_scoped_negation(self) -> None:
        executed = (
            "I've already updated your LinkedIn profile.",
            "We have just scheduled the recruiter screen.",
            "The LinkedIn profile has already been edited.",
            "The recruiter messages were successfully sent.",
            "Yo ya actualicé tu perfil de LinkedIn.",
            "Hemos actualizado tu perfil de LinkedIn.",
            "Nosotros publicamos el post en LinkedIn.",
            "Los mensajes al reclutador fueron enviados.",
            "No esperé y actualicé tu perfil de LinkedIn.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_completed_actions_bind_each_verb_to_an_external_action_target(self) -> None:
        executed = (
            "Editamos el perfil de LinkedIn.",
            "Actualizamos tu titular de LinkedIn.",
            "Publicamos el post en LinkedIn.",
            "Ya actualizamos tu perfil de LinkedIn.",
            "I previously updated your LinkedIn profile.",
            "I had updated your LinkedIn profile.",
            "We had already scheduled the recruiter screen.",
            "Se editó el perfil de LinkedIn.",
            "Se envió el mensaje al reclutador.",
            "Se subió el recurso a LinkedIn.",
            "Se aplicó a la vacante en LinkedIn.",
            "Se programó la entrevista con reclutamiento.",
            "Se compartió el post en LinkedIn.",
            "Se conectó con el reclutador en LinkedIn.",
            "Me registré en LinkedIn para la vacante.",
            "Me inscribí en la vacante de LinkedIn.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_completed_actions_require_explicit_external_object_grammar(self) -> None:
        executed = (
            "I'd updated your LinkedIn profile.",
            "We'd previously updated your LinkedIn profile.",
            "Nos postulamos a la vacante de LinkedIn.",
            "Nos inscribimos en la vacante de LinkedIn.",
            "Presentamos la solicitud en LinkedIn.",
            "Se postuló a la vacante en LinkedIn.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        technical = (
            "I applied reliability controls to the application.",
            "I submitted application metrics to the dashboard.",
            "I connected monitoring to the recruiter database.",
        )
        for text in technical:
            with self.subTest(kind="technical", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        nonexecuted = (
            "No lo actualicé en LinkedIn.",
            "Nunca lo publiqué en LinkedIn.",
            "No la envié al reclutador por LinkedIn.",
            "I applied reliability controls to LinkedIn workloads.",
            "I scheduled Kubernetes workloads while reviewing the LinkedIn profile.",
            "Queue messages were sent before the LinkedIn review.",
            "I shared ownership of the LinkedIn migration.",
            "I applied reliability controls; the LinkedIn vacancy remained unchanged.",
            "I scheduled Kubernetes workloads; the recruiter screen remained pending.",
            "Queue messages were sent; the recruiter reviewed the LinkedIn copy.",
        )
        for text in nonexecuted:
            with self.subTest(kind="not executed", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_completed_actions_cover_application_families_without_technical_false_positives(self) -> None:
        executed = (
            "I applied to a vacancy on LinkedIn.",
            "I applied for this job on LinkedIn.",
            "I submitted my application yesterday.",
            "I submitted an application to LinkedIn yesterday.",
            "The application was submitted yesterday.",
            "I registered for the vacancy on LinkedIn.",
            "The application was registered yesterday.",
            "I presented the application to LinkedIn.",
            "The application was presented yesterday.",
            "Nos registramos en la vacante de LinkedIn.",
            "Se registró en la vacante de LinkedIn.",
            "Se presentó la solicitud en LinkedIn.",
            "La solicitud fue presentada ayer.",
            "La solicitud fue registrada ayer.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        technical = (
            "I sent telemetry to the recruiter service.",
            "I scheduled recruiter metrics collection.",
            "I scheduled interview workload backups.",
            "I shared post-processing metrics.",
            "Recruiter metrics were sent to the dashboard.",
            "Interview workloads were scheduled nightly.",
        )
        for text in technical:
            with self.subTest(kind="technical", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_completed_actions_bind_destinations_plural_forms_and_object_heads(self) -> None:
        executed = (
            "I submitted an application to Acme.",
            "I submitted an application through the portal.",
            "Applications were submitted.",
            "I presented our application.",
            "Se inscribió en la vacante.",
            "La solicitud ha sido presentada.",
            "I sent a recruiter message.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        technical = (
            "I sent telemetry to the recruiter database.",
            "I sent metrics to the recruiter queue.",
            "I scheduled the interview data pipeline.",
            "I shared post-processing metrics.",
            "I updated LinkedIn workloads.",
            "LinkedIn logs were updated.",
            "I uploaded LinkedIn logs to the archive.",
        )
        for text in technical:
            with self.subTest(kind="technical", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_completed_actions_bind_full_destinations_and_reject_technical_object_heads(self) -> None:
        executed = (
            "I submitted an application to Acme Corp.",
            "I submitted an application through the company portal.",
            "I presented our application to Acme.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        technical = (
            "I connected the recruiter database to monitoring.",
            "I connected the recruiter service to observability.",
            "I sent recruiter message queues to the dashboard.",
            "I sent recruiter metrics to the dashboard.",
            "I scheduled the interview data pipeline.",
            "I shared post processing metrics.",
            "I shared post-processing metrics.",
            "I uploaded logs to LinkedIn.",
            "I uploaded LinkedIn workloads to the test service.",
            "LinkedIn logs were updated.",
        )
        for text in technical:
            with self.subTest(kind="technical", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_completed_actions_restore_bounded_ordinary_object_forms(self) -> None:
        executed = (
            "A recruiter message was sent on LinkedIn.",
            "I submitted an application to Acme, Inc.",
            "I sent a message to the recruiter.",
            "I messaged a recruiter.",
            "I uploaded my resume to LinkedIn.",
            "I uploaded our CV to LinkedIn.",
            "I shared my post on LinkedIn.",
            "I shared our post through LinkedIn.",
            "I connected with a recruiter on LinkedIn.",
        )
        for text in executed:
            with self.subTest(text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        nonexecuted = (
            "No actualicé tu perfil de LinkedIn.",
            "I did not update your LinkedIn profile.",
            "The LinkedIn profile was not updated.",
            "El perfil presente se mantiene privado.",
        )
        for text in nonexecuted:
            with self.subTest(kind="not executed", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_completed_application_destinations_allow_bounded_organization_text(self) -> None:
        executed = (
            "I submitted an application to Acme & Partners.",
            "I submitted an application to Acme (Remote).",
            "I presented the application to Acme Global Technology Services.",
        )
        for text in executed:
            with self.subTest(kind="executed", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        bounded_out = (
            "I submitted an application to Acme International Platform Engineering "
            "Research Operations and Customer Experience Division.",
            "I presented the application to Acme / Internal.",
        )
        for text in bounded_out:
            with self.subTest(kind="bounded out", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        self.assertEqual(
            [],
            validator.validate_client_report(
                self.add_to_verdict("I submitted application metrics to the dashboard."),
                self.bundle(),
            ),
        )

    def test_credential_shapes_are_rejected_independently(self) -> None:
        values = (
            "access_token=SYNTHETIC_CREDENTIAL_VALUE",
            "password: SYNTHETIC_CREDENTIAL_VALUE",
            "api-key = SYNTHETIC_CREDENTIAL_VALUE",
            "Authorization: Bearer SYNTHETIC_CREDENTIAL_VALUE",
            "Authorization: Basic U1lOVEhFVElDX0NSRURFTlRJQUw=",
        )
        for text in values:
            with self.subTest(text=text):
                errors = validator.validate_client_report(
                    self.add_to_verdict(text),
                    self.bundle(),
                )
                self.assertIn(
                    "client report contains credential-shaped content",
                    errors,
                )
                self.assertEqual(
                    1,
                    errors.count("client report contains credential-shaped content"),
                )

    def test_credential_assignment_keys_accept_bounded_word_separators(self) -> None:
        assignments = (
            "APIkey=SYNTHETIC_CREDENTIAL_VALUE",
            "API key=SYNTHETIC_CREDENTIAL_VALUE",
            "API   key: SYNTHETIC_CREDENTIAL_VALUE",
            "accesstoken=SYNTHETIC_CREDENTIAL_VALUE",
            "access token = SYNTHETIC_CREDENTIAL_VALUE",
            "access-token: SYNTHETIC_CREDENTIAL_VALUE",
            "private key=SYNTHETIC_CREDENTIAL_VALUE",
            "private_key: SYNTHETIC_CREDENTIAL_VALUE",
        )
        for text in assignments:
            with self.subTest(text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_generic_secret_labels_require_secret_shaped_values(self) -> None:
        unsafe = (
            "credential=SYNTHETIC_CREDENTIAL_VALUE",
            "secret: SYNTHETIC_SECRET_VALUE",
            "credential value=SYNTHETIC_CREDENTIAL_VALUE",
            "secret-token: SYNTHETIC_SECRET_VALUE",
            "password=leadership",
            "api key=certification",
            "credential value=synthetic",
            "secret-token: synthetic",
            "secret key=leadership",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_generic_secret_labels_distinguish_opaque_tokens_from_career_credentials(self) -> None:
        opaque = (
            "credential=abcdefghijklmnop",
            "secret: AbCdEfGhIjKlMnOp",
            "credential: opaquealphabeticvalue",
            "secret=LongSyntheticOpaqueWord",
        )
        for text in opaque:
            with self.subTest(kind="opaque", text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        career = (
            "Credential: Solutions Architect",
            "Credential: Certified Kubernetes Administrator",
            "Credential: Associate certification",
            "Credential: Cloud-Professional",
            "Secret: professional leadership requires discretion",
            "Credential: platform certification supports the target role",
        )
        for text in career:
            with self.subTest(kind="career", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        for text in ("password=Administrator", "api key=Professional"):
            with self.subTest(kind="specific key", text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        benign = (
            "Credential: certification-based leadership evidence.",
            "Credential: AWS-Certified-Solutions-Architect preparation.",
            "Leadership secret: communicate clearly and document decisions.",
        )
        for text in benign:
            with self.subTest(kind="benign", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_generic_secret_labels_parse_leading_tokens_and_bound_career_exemptions(self) -> None:
        unsafe = (
            "credential=abcdefghijklmnop followed by a local note",
            "secret: AbCdEfGhIjKlMnOp # rotated locally",
            "credential=OpaqueArchitectPayload99",
            "secret=CertifiedOpaquePayload99",
            "credential=abcdefghijklmnop\u2028review only",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        career = (
            "Credential: Google Cloud Engineer",
            "Credential: HashiCorp Terraform Associate",
        )
        for text in career:
            with self.subTest(kind="career", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_generic_credentials_use_explicit_bounded_title_patterns(self) -> None:
        career = (
            "Credential: AWS-Solutions-Architect-2025",
            "Credential: Kubernetes2025Administrator",
            "Credential: AZ104Certification",
            "Credential: Google-Cloud-Engineer-2025",
        )
        for text in career:
            with self.subTest(kind="career", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        unsafe = (
            "Secret: transparent-leadership practices build trust",
            "Credential: architect-secret-token-value",
            "Credential: certified-private-key-value",
            "Credential: HashiCorp-Terraform-003",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_generic_credentials_require_a_bounded_career_title_term(self) -> None:
        career = (
            "Credential: Microsoft Azure Administrator 2025",
            "Credential: Red Hat Certified Engineer 2025",
            "Credential: Microsoft-Azure-Administrator-2025",
            "Credential: Red-Hat-Certified-Engineer-2025",
            "Credential: Linux-Platform-Professional-v2",
        )
        for text in career:
            with self.subTest(kind="career", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        unsafe = (
            "Secret: Microsoft-Azure-Administrator-2025",
            "Credential: Microsoft-Certified-Engineer-secret",
            "Credential: Microsoft-Azure-Administrator-2025 token value",
            "Credential: Red-Hat-Certified-Engineer-password",
            "api key=Microsoft-Azure-Administrator-2025",
        )
        for text in unsafe:
            with self.subTest(kind="unsafe", text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_generic_credentials_scan_forbidden_components_before_opaque_shape(self) -> None:
        unsafe = (
            "Credential: Microsoft token Azure Administrator",
            "Credential: Microsoft-ToKeN-Azure-Administrator",
            "Credential: Microsoft_token_Azure_Administrator",
            "Credential: Microsoft\u2028ToKeN Azure Administrator",
            "Credential: Microsoft\u0085TOKEN Azure Administrator",
            "Credential: Microsoft\vtoken Azure Administrator",
            "Credential: Microsoft\ftoken Azure Administrator",
        )
        for text in unsafe:
            with self.subTest(text=text):
                self.assertIn(
                    "client report contains credential-shaped content",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        career = (
            "Credential: Microsoft Azure Administrator 2025",
            "Credential: Red Hat Certified Engineer 2025",
            "Credential: IBM Cloud Professional v3",
        )
        for text in career:
            with self.subTest(text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        benign = (
            "Review key concepts for the API certification.",
            "Use passwordless authentication and never expose credentials.",
            "Keep the access-token-free checklist in private review.",
        )
        for text in benign:
            with self.subTest(kind="benign", text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_bounded_safety_scanners_allow_boundary_prose_and_nonexecuted_drafts(self) -> None:
        boundary_prose = (
            "Never expose credentials or Authorization headers.",
            "Draft an updated LinkedIn headline for private review.",
            "Do not schedule recruiter calls or publish profile changes.",
            "Never infer age, disability, ethnicity, race, gender, health, nationality, "
            "pregnancy, religion, or sexual orientation from a photo.",
            "Nunca expongas credenciales ni encabezados de autorización.",
            "Prepara un titular actualizado de LinkedIn para revisión privada.",
        )
        for text in boundary_prose:
            with self.subTest(text=text):
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.add_to_verdict(text),
                        self.bundle(),
                    ),
                )

    def test_report_rejects_outcome_guarantees(self) -> None:
        for text in (
            "Este cambio garantiza entrevistas.",
            "This headline guarantees recruiter responses.",
            "This change will get you interviews.",
        ):
            with self.subTest(text=text):
                self.assertIn(
                    "client report cannot guarantee an employment or platform outcome",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_inspection_authorization_cannot_imply_external_authorization(self) -> None:
        for text in (
            "La inspección autorizada también autoriza publicar los cambios.",
            "Authorized inspection permits editing the profile.",
        ):
            with self.subTest(text=text):
                self.assertIn(
                    "profile inspection authorization cannot authorize an external action",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_fixture_privacy_scans_nested_values_but_allows_only_proven_source_urls(self) -> None:
        bundle = self.bundle()
        bundle["priorities"][0]["done_when"] = "person@example.invalid"
        self.assertIn(
            "fixture contains forbidden email-like value at priorities[0].done_when",
            validator.validate_fixture_bundle(bundle),
        )
        bundle = self.bundle()
        bundle["source_catalog"][0]["scope"] = "https://www.linkedin.com/help/linkedin/answer/a507663"
        self.assertIn(
            "fixture contains forbidden URL value outside source_catalog[].url at source_catalog[0].scope",
            validator.validate_fixture_bundle(bundle),
        )

    def test_sources_require_every_official_category_and_secondary_cannot_substitute(self) -> None:
        bundle = self.bundle()
        catalog = self.complete_source_catalog(bundle)
        catalog[0]["source_class"] = "secondary"
        missing = catalog[0]["source_category"]
        self.assertIn(
            f"source_catalog missing required official source category: {missing}",
            validator.validate_client_report(self.report(), bundle),
        )

    def test_official_category_requires_its_registered_locator(self) -> None:
        bundle = self.bundle()
        catalog = self.complete_source_catalog(bundle)
        good_profile_url = next(
            source["url"]
            for source in catalog
            if source["source_category"] == "good_profile"
        )
        job_match = next(
            source
            for source in catalog
            if source["source_category"] == "job_match"
        )
        job_match["url"] = good_profile_url

        errors = validator.validate_fixture_bundle(bundle)

        self.assertIn(
            "source_catalog[5] official URL is not registered for source_category job_match",
            errors,
        )
        self.assertIn(
            "source_catalog missing required official source category: job_match",
            errors,
        )

    def test_genuine_secondary_source_is_allowed_but_never_counts_as_official(self) -> None:
        bundle = self.bundle()
        bundle["source_catalog"].append(self.secondary_source())
        self.assertEqual([], validator.validate_fixture_bundle(bundle))

        bundle["source_catalog"] = [
            source
            for source in bundle["source_catalog"]
            if not (
                source["source_class"] == "official"
                and source["source_category"] == "job_match"
            )
        ]
        self.assertIn(
            "source_catalog missing required official source category: job_match",
            validator.validate_fixture_bundle(bundle),
        )

    def test_exactly_one_official_source_is_required_per_category(self) -> None:
        bundle = self.bundle()
        duplicate = copy.deepcopy(bundle["source_catalog"][0])
        duplicate["source_id"] = "SOURCE-JSC1-GOOD-PROFILE-DUPLICATE"
        bundle["source_catalog"].append(duplicate)
        self.assertIn(
            "source_catalog requires exactly one official source for category: good_profile",
            validator.validate_fixture_bundle(bundle),
        )

        bundle = self.bundle()
        first = self.secondary_source()
        second = self.secondary_source()
        second["source_id"] = "SOURCE-JSC1-SECONDARY-2"
        second["url"] = "https://www.themuse.com/advice/how-to-use-linkedin"
        bundle["source_catalog"].extend((first, second))
        self.assertEqual([], validator.validate_fixture_bundle(bundle))

    def test_secondary_source_requires_publisher_and_document_title(self) -> None:
        for field in ("publisher", "document_title"):
            with self.subTest(field=field, state="missing"):
                bundle = self.bundle()
                source = self.secondary_source()
                source.pop(field)
                bundle["source_catalog"].append(source)
                self.assertIn(
                    f"source_catalog[8] secondary source requires non-empty {field}",
                    validator.validate_fixture_bundle(bundle),
                )
            with self.subTest(field=field, state="empty"):
                bundle = self.bundle()
                source = self.secondary_source()
                source[field] = ""
                bundle["source_catalog"].append(source)
                self.assertIn(
                    f"source_catalog[8] secondary source requires non-empty {field}",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_official_source_provenance_fields_are_permitted_but_optional(self) -> None:
        for field in ("publisher", "document_title"):
            with self.subTest(field=field):
                bundle = self.bundle()
                bundle["source_catalog"][0].pop(field)
                self.assertEqual([], validator.validate_fixture_bundle(bundle))

    def test_provenance_is_single_line_bounded_and_privacy_safe(self) -> None:
        cases = (
            ("publisher", "Line one\nLine two", "single line of at most 120 characters"),
            ("publisher", "Line one\u0085Line two", "single line of at most 120 characters"),
            ("publisher", "Line one\u2028Line two", "single line of at most 120 characters"),
            ("publisher", "Line one\u2029Line two", "single line of at most 120 characters"),
            ("publisher", "Line one\vLine two", "single line of at most 120 characters"),
            ("publisher", "Line one\x1eLine two", "single line of at most 120 characters"),
            ("publisher", "p" * 121, "single line of at most 120 characters"),
            ("document_title", "t" * 241, "single line of at most 240 characters"),
            ("publisher", "Research access_token archive", "sensitive or private content"),
            ("document_title", "Contact person@example.invalid", "sensitive or private content"),
            ("publisher", "raw_profile_text archive", "sensitive or private content"),
            ("document_title", "analytics_value snapshot", "sensitive or private content"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field, expected=expected):
                bundle = self.bundle()
                source = self.secondary_source()
                source[field] = value
                bundle["source_catalog"].append(source)
                self.assertIn(
                    f"source_catalog[8] {field} must be a {expected}"
                    if expected.startswith("single")
                    else f"source_catalog[8] {field} contains {expected}",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_secondary_url_rejects_credentials_ports_ips_local_private_and_profile_hosts(self) -> None:
        cases = (
            (
                "https://user:pass@career.example.org/article",
                "source_catalog[8] secondary URL cannot include credentials",
            ),
            (
                "https://career.example.org:8443/article",
                "source_catalog[8] secondary URL cannot include a port",
            ),
            (
                "https://203.0.113.10/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://localhost/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://docs.internal/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://10.0.0.8/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://www.linkedin.com/in/synthetic-sentinel/",
                "source_catalog[8] secondary URL cannot be a LinkedIn profile URL",
            ),
            (
                "https://127.1/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://0177.0.0.1/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://0x7f000001/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://sub.localhost/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://example.com/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://docs.example.invalid/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://docs.example.test/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://service.alt/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://sub.service.alt/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://private.onion/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://host.home.arpa/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://service.arpa/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://xn--bcher-kva.public-domain.com/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://bücher.public-domain.com/article",
                "source_catalog[8] secondary URL host must be a public hostname",
            ),
            (
                "https://www.linkedin.com/in",
                "source_catalog[8] secondary URL cannot be a LinkedIn profile URL",
            ),
            (
                "https://www.linkedin.com/pub",
                "source_catalog[8] secondary URL cannot be a LinkedIn profile URL",
            ),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                bundle = self.bundle()
                source = self.secondary_source()
                source["url"] = url
                bundle["source_catalog"].append(source)
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_source_url_metadata_scans_decoded_keys_and_values_for_secret_markers(self) -> None:
        suffixes = (
            "?note=access%5Ftoken%3Dopaque",
            "?note=access%255Ftoken%253Dopaque",
            "#note=client%255Fsecret",
            "?note=BEARER%2520opaque",
        )
        official_base = "https://www.linkedin.com/help/linkedin/answer/a554351"
        secondary_base = "https://www.themuse.com/advice/linkedin-profile-tips"
        for source_class, base, expected in (
            (
                "official",
                official_base,
                "source_catalog[0] official URL cannot include a sensitive query or fragment",
            ),
            (
                "secondary",
                secondary_base,
                "source_catalog[8] secondary URL cannot include a sensitive query or fragment",
            ),
        ):
            for suffix in suffixes:
                with self.subTest(source_class=source_class, suffix=suffix):
                    bundle = self.bundle()
                    if source_class == "official":
                        bundle["source_catalog"][0]["url"] = base + suffix
                    else:
                        source = self.secondary_source()
                        source["url"] = base + suffix
                        bundle["source_catalog"].append(source)
                    self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_secondary_url_rejects_non_https_and_sensitive_query_or_fragment(self) -> None:
        cases = (
            (
                "http://www.themuse.com/advice/linkedin-profile-tips",
                "source_catalog[8] secondary URL must use HTTPS",
            ),
            (
                "https://www.themuse.com/advice/linkedin-profile-tips?token=opaque",
                "source_catalog[8] secondary URL cannot include a sensitive query or fragment",
            ),
            (
                "https://www.themuse.com/advice/linkedin-profile-tips#password=opaque",
                "source_catalog[8] secondary URL cannot include a sensitive query or fragment",
            ),
            (
                "https://www.themuse.com/advice/linkedin-profile-tips?next=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fsentinel",
                "source_catalog[8] secondary URL cannot include a sensitive query or fragment",
            ),
            (
                "https://www.themuse.com/advice/linkedin-profile-tips?redirect_access_token=opaque",
                "source_catalog[8] secondary URL cannot include a sensitive query or fragment",
            ),
            (
                "https://www.themuse.com/advice/linkedin-profile-tips?access%255Ftoken=opaque",
                "source_catalog[8] secondary URL cannot include a sensitive query or fragment",
            ),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                bundle = self.bundle()
                source = self.secondary_source()
                source["url"] = url
                bundle["source_catalog"].append(source)
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_official_locator_requires_a_decoded_path_segment_boundary(self) -> None:
        base = "https://www.linkedin.com/help/linkedin/answer/a554351"
        valid = (base, f"{base}/", f"{base}/details")
        invalid = (
            f"{base}evil",
            f"{base}%65vil",
            f"{base}%2565vil",
        )
        for url in valid:
            with self.subTest(url=url, expected="valid"):
                self.assertTrue(
                    validator._is_registered_official_source("good_profile", url)
                )
        for url in invalid:
            with self.subTest(url=url, expected="invalid"):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = url
                self.assertIn(
                    "source_catalog[0] official URL is not registered for source_category good_profile",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_source_authorities_reject_zero_ports_and_empty_credentials(self) -> None:
        cases = (
            (
                "https://www.linkedin.com:0/help/linkedin/answer/a554351",
                "https://www.themuse.com:0/advice/linkedin-profile-tips",
                "secondary URL cannot include a port",
            ),
            (
                "https://www.linkedin.com:0000/help/linkedin/answer/a554351",
                "https://www.themuse.com:0000/advice/linkedin-profile-tips",
                "secondary URL cannot include a port",
            ),
            (
                "https://@www.linkedin.com/help/linkedin/answer/a554351",
                "https://@www.themuse.com/advice/linkedin-profile-tips",
                "secondary URL cannot include credentials",
            ),
            (
                "https://:@www.linkedin.com/help/linkedin/answer/a554351",
                "https://:@www.themuse.com/advice/linkedin-profile-tips",
                "secondary URL cannot include credentials",
            ),
        )
        for official_url, secondary_url, secondary_error in cases:
            with self.subTest(source_class="official", url=official_url):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = official_url
                self.assertIn(
                    "source_catalog[0] official URL is not registered for source_category good_profile",
                    validator.validate_fixture_bundle(bundle),
                )
            with self.subTest(source_class="secondary", url=secondary_url):
                bundle = self.bundle()
                source = self.secondary_source()
                source["url"] = secondary_url
                bundle["source_catalog"].append(source)
                self.assertIn(
                    f"source_catalog[8] {secondary_error}",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_source_urls_reject_raw_encoded_and_double_encoded_backslash_paths(self) -> None:
        official_base = "https://www.linkedin.com/help/linkedin/answer/a554351/"
        secondary_base = "https://www.linkedin.com/"
        for path in (r"in\sentinel", "in%5Csentinel", "in%255Csentinel"):
            with self.subTest(source_class="official", path=path):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = official_base + path
                self.assertIn(
                    "source_catalog[0] official URL is not registered for source_category good_profile",
                    validator.validate_fixture_bundle(bundle),
                )
            with self.subTest(source_class="secondary", path=path):
                bundle = self.bundle()
                source = self.secondary_source()
                source["url"] = secondary_base + path
                bundle["source_catalog"].append(source)
                self.assertIn(
                    "source_catalog[8] secondary URL cannot include a backslash path",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_official_urls_reject_sensitive_query_and_fragment_metadata(self) -> None:
        base = "https://www.linkedin.com/help/linkedin/answer/a554351"
        for suffix in (
            "?access_token=opaque",
            "?client_secret=opaque",
            "?redirect_access_token=opaque",
            "?access%255Ftoken=opaque",
            "?ａｃｃｅｓｓ＿ｔｏｋｅｎ=opaque",
            "#ToKeN=opaque",
        ):
            with self.subTest(suffix=suffix):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = base + suffix
                self.assertIn(
                    "source_catalog[0] official URL cannot include a sensitive query or fragment",
                    validator.validate_fixture_bundle(bundle),
                )

    def test_source_ids_are_unique_and_official_urls_use_registered_locators(self) -> None:
        bundle = self.bundle()
        catalog = self.complete_source_catalog(bundle)
        catalog[1]["source_id"] = catalog[0]["source_id"]
        catalog[2]["url"] = "http://www.linkedin.com/help/linkedin/answer/a507663"
        catalog[3]["url"] = "https://www.linkedin.com.evil.invalid/help/linkedin/answer/a507663"
        errors = validator.validate_client_report(self.report(), bundle)
        self.assertIn(f"source_catalog has duplicate source_id: {catalog[0]['source_id']}", errors)
        self.assertIn(
            "source_catalog[2] official URL is not registered for source_category cover_image",
            errors,
        )
        self.assertIn(
            "source_catalog[3] official URL is not registered for source_category featured_section",
            errors,
        )

    def test_official_source_url_exception_does_not_hide_private_query_values(self) -> None:
        bundle = self.bundle()
        bundle["source_catalog"][0]["url"] = (
            "https://www.linkedin.com/help/linkedin/answer/a507663?contact=person@example.invalid"
        )
        self.assertIn(
            "fixture contains forbidden email-like value at source_catalog[0].url",
            validator.validate_fixture_bundle(bundle),
        )

    def test_official_source_url_canonicalization_blocks_encoded_private_values(self) -> None:
        cases = (
            (
                "https://www.linkedin.com/help/linkedin/answer/a?contact=person%40example.invalid",
                "fixture contains forbidden email-like value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/answer/a?next=https%3A%2F%2Fwww.linkedin.com%2Fin%2Fsentinel",
                "fixture contains forbidden LinkedIn profile URL value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/answer/a?phone=%2B525512345678",
                "fixture contains forbidden phone-like value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/%252e%252e/in/sentinel",
                "source_catalog[0] official URL is not registered for source_category good_profile",
            ),
        )
        for url, expected in cases:
            with self.subTest(url=url):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = url
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

    def test_unicode_format_characters_cannot_mask_url_or_report_privacy_values(self) -> None:
        encoded_urls = (
            (
                "https://www.linkedin.com/help/linkedin/answer/a?contact=person%E2%80%8B%40example.invalid",
                "fixture contains forbidden email-like value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/answer/a?phone=%2B52%E2%80%8B5512345678",
                "fixture contains forbidden phone-like value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/answer/a?next=https%3A%2F%2Fwww.linked%E2%80%8Bin.com%2Fin%2Fsentinel",
                "fixture contains forbidden LinkedIn profile URL value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/answer/person%E2%80%8B%40example.invalid",
                "fixture contains forbidden email-like value at source_catalog[0].url",
            ),
            (
                "https://www.linkedin.com/help/linkedin/answer/a#phone=%2B52%E2%80%8B5512345678",
                "fixture contains forbidden phone-like value at source_catalog[0].url",
            ),
        )
        for url, expected in encoded_urls:
            with self.subTest(url=url):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = url
                self.assertIn(expected, validator.validate_fixture_bundle(bundle))

        report_values = (
            (
                "Contacto: person\u200b@example.invalid",
                "client report contains forbidden email-like value",
            ),
            (
                "Teléfono: +52\u200b5512345678",
                "client report contains forbidden phone-like value",
            ),
            (
                "Perfil: https://www.linked\u200bin.com/in/sentinel",
                "client report contains forbidden LinkedIn profile URL value",
            ),
            (
                "raw\u200b_profile_text=biography",
                "client report contains forbidden raw-profile alias",
            ),
            (
                "analytics\u200b_value=47",
                "client report contains forbidden private analytics value",
            ),
            (
                "[CONFIRMAR\u200b DESPUÉS]",
                "confirmation marker requires a concrete decision-changing question",
            ),
        )
        for text, expected in report_values:
            with self.subTest(text=text):
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_official_source_registry_rejects_path_traversal_and_invalid_ports(self) -> None:
        for url in (
            "https://www.linkedin.com/help/linkedin/../in/synthetic-sentinel/",
            "https://www.linkedin.com:invalid/help/linkedin/answer/a507663",
        ):
            with self.subTest(url=url):
                bundle = self.bundle()
                bundle["source_catalog"][0]["url"] = url
                try:
                    errors = validator.validate_fixture_bundle(bundle)
                except Exception as error:  # pragma: no cover - names the security regression
                    self.fail(f"malformed official URL leaked {type(error).__name__}")
                self.assertIn(
                    "source_catalog[0] official URL is not registered for source_category good_profile",
                    errors,
                )

    def test_source_state_uses_evaluation_date_with_89_90_91_day_boundary(self) -> None:
        evaluation_date = date(2026, 8, 7)
        source = self.bundle()["source_catalog"][0]
        for age, expected in ((89, "current"), (90, "current"), (91, "stale")):
            with self.subTest(age=age):
                source["access_date"] = (evaluation_date - timedelta(days=age)).isoformat()
                self.assertEqual(expected, validator.resolve_source_state(source, evaluation_date))
        source["reachability"] = "unreachable"
        self.assertEqual("unreachable", validator.resolve_source_state(source, evaluation_date))

    def test_evaluation_and_access_dates_require_canonical_calendar_form(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["evaluation_date"] = "2026-W33-4"
        self.assertIn("fixture has invalid evaluation_date", validator.validate_fixture_bundle(bundle))
        bundle = self.bundle("scenario-a.json")
        bundle["source_catalog"][0]["access_date"] = "2026-W33-4"
        self.assertIn("source_catalog[0] has invalid access_date", validator.validate_fixture_bundle(bundle))

    def test_stale_or_unreachable_source_requires_blocking_fallback(self) -> None:
        for reachability, age in (("reachable", 91), ("unreachable", 1)):
            with self.subTest(reachability=reachability):
                bundle = self.bundle()
                catalog = self.complete_source_catalog(bundle)
                catalog[0]["reachability"] = reachability
                catalog[0]["access_date"] = (
                    date.fromisoformat(bundle["evaluation_date"]) - timedelta(days=age)
                ).isoformat()
                catalog[0]["fallback"] = "CURRENT_OFFICIAL_SOURCE"
                self.assertIn(
                    f"source {catalog[0]['source_id']} resolved {validator.resolve_source_state(catalog[0], date.fromisoformat(bundle['evaluation_date']))} and must degrade to COACH_HEURISTIC or BLOCK_CLAIM",
                    validator.validate_client_report(self.report(), bundle),
                )

    def test_malformed_safety_and_source_objects_return_errors_without_throwing(self) -> None:
        mutations = (
            ("eval_expectations", []),
            ("source_catalog", {"not": "a list"}),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                bundle = self.bundle()
                bundle[field] = value
                try:
                    errors = validator.validate_client_report(self.report(), bundle)
                except Exception as error:  # pragma: no cover - names the robustness regression
                    self.fail(f"malformed {field} leaked {type(error).__name__}")
                self.assertTrue(errors)
        bundle = self.bundle()
        bundle["source_catalog"][0]["fallback"] = []
        try:
            errors = validator.validate_client_report(self.report(), bundle)
        except Exception as error:  # pragma: no cover - names the robustness regression
            self.fail(f"malformed source fallback leaked {type(error).__name__}")
        self.assertIn("source_catalog[0] has invalid fallback", errors)

    def test_report_safety_is_unicode_and_token_order_invariant(self) -> None:
        cases = (
            ("Valor provisional: ＴＢＤ", "client report contains forbidden placeholder: tbd"),
            ("Valor provisional: T\u200bBD", "client report contains forbidden placeholder: tbd"),
            ("The photo indicates the candidate's religion.", "client report cannot infer a protected trait from visual evidence"),
            ("La foto sugiere que es mujer.", "client report cannot infer a protected trait from visual evidence"),
            ("P-H-O-T-O indicates R-E-L-I-G-I-O-N.", "client report cannot infer a protected trait from visual evidence"),
            ("I sent the recruiter a message on LinkedIn.", "client report cannot claim an external action was executed"),
            ("Publiqué el titular revisado en LinkedIn.", "client report cannot claim an external action was executed"),
            ("This headline ensures more interviews.", "client report cannot guarantee an employment or platform outcome"),
            ("The probability of an individual interview is 70%.", "individual outcome probability is not allowed"),
            ("Score math uses a 2x multiplier.", "aggregate 2x claims cannot affect score math"),
            ("El cálculo del puntaje usa multiplicador 2×.", "aggregate 2x claims cannot affect score math"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_semantic_safety_classes_cover_completed_certainty_and_probability_variants(self) -> None:
        cases = (
            (
                "He enviado un mensaje al reclutador en LinkedIn.",
                "client report cannot claim an external action was executed",
            ),
            (
                "El mensaje al reclutador fue enviado en LinkedIn.",
                "client report cannot claim an external action was executed",
            ),
            (
                "This headline will definitely lead to interviews.",
                "client report cannot guarantee an employment or platform outcome",
            ),
            (
                "Entrevistas ciertas e inevitables resultarán de este titular.",
                "client report cannot guarantee an employment or platform outcome",
            ),
            (
                "Your chance of an interview is 70%.",
                "individual outcome probability is not allowed",
            ),
            (
                "Una entrevista para ti tiene una posibilidad del 70%.",
                "individual outcome probability is not allowed",
            ),
            (
                "70% is your interview chance.",
                "individual outcome probability is not allowed",
            ),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_completed_application_and_causal_outcome_language_is_blocked(self) -> None:
        completed_actions = (
            "We submitted the application on LinkedIn.",
            "Presenté la solicitud en LinkedIn.",
        )
        for text in completed_actions:
            with self.subTest(kind="completed_action", text=text):
                self.assertIn(
                    "client report cannot claim an external action was executed",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

        causal_claims = (
            "This headline gets you interviews.",
            "This headline can get interviews.",
            "This headline can lead to interviews.",
            "This headline leads to interviews.",
            "This change may result in recruiter responses.",
            "This change results in recruiter responses.",
            "This copy can cause interviews.",
            "This copy causes interviews.",
            "This copy can produce recruiter responses.",
            "This copy delivers job interviews.",
            "This headline can drive interview responses.",
            "This update boosts recruiter responses.",
            "This headline can increase interview chances.",
            "Este titular consigue entrevistas.",
            "Este cambio genera respuestas de reclutadores.",
            "Este titular aumenta las entrevistas.",
        )
        for text in causal_claims:
            with self.subTest(kind="causal_outcome", text=text):
                self.assertIn(
                    "client report cannot guarantee an employment or platform outcome",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_scenario_c_rejects_evidence_requests_outside_question_blocks(self) -> None:
        for request in (
            "También comparte una captura adicional de tu actividad para completar el análisis.",
            "Envía tu foto y banner completos aunque ninguna decisión actual dependa de ellos.",
        ):
            with self.subTest(request=request):
                report = self.report("scenario-c-es.md").replace(
                    "## Límites del diagnóstico",
                    f"{request}\n\n## Límites del diagnóstico",
                    1,
                )
                self.assertIn(
                    "scenario C evidence requests must appear only in canonical decision-changing questions",
                    validator.validate_client_report(report, self.bundle("scenario-c.json")),
                )

    def test_scenario_c_ignores_only_fields_in_live_canonical_question_blocks(self) -> None:
        base = self.report("scenario-c-es.md")
        fake_headings = (
            "```text\n### Pregunta 99\n```",
            "    ### Pregunta 99",
        )
        for fake_heading in fake_headings:
            with self.subTest(fake_heading=fake_heading):
                report = base.replace(
                    "### Pregunta 1",
                    (
                        f"{fake_heading}\n"
                        "- Pregunta: Necesitamos evidencia adicional.\n\n"
                        "### Pregunta 1"
                    ),
                    1,
                )
                self.assertIn(
                    "scenario C evidence requests must appear only in canonical decision-changing questions",
                    validator.validate_client_report(report, self.bundle("scenario-c.json")),
                )

    def test_scenario_c_no_extra_visual_policy_checks_full_question_and_prose(self) -> None:
        base = self.report("scenario-c-es.md")
        for visual_object in (
            "screenshot", "captura", "photo", "foto", "banner", "image", "imagen",
            "activity", "actividad",
        ):
            with self.subTest(location="question", visual_object=visual_object):
                report = base.replace(
                    "¿Cuál es el alcance confirmado del ejemplo de experiencia?",
                    (
                        "¿Cuál es el alcance confirmado del ejemplo de experiencia? "
                        f"También comparte una {visual_object} adicional."
                    ),
                    1,
                )
                self.assertIn(
                    "scenario C cannot request extra visual evidence",
                    validator.validate_client_report(report, self.bundle("scenario-c.json")),
                )

        for request in (
            "Necesito una captura adicional de actividad.",
            "I need an additional activity image.",
        ):
            with self.subTest(location="prose", request=request):
                report = base.replace(
                    "## Límites del diagnóstico",
                    f"{request}\n\n## Límites del diagnóstico",
                    1,
                )
                self.assertIn(
                    "scenario C evidence requests must appear only in canonical decision-changing questions",
                    validator.validate_client_report(report, self.bundle("scenario-c.json")),
                )

    def test_scenario_c_no_extra_visual_policy_scans_the_entire_pending_section(self) -> None:
        base = self.report("scenario-c-es.md")
        prose_cases = (
            "Please attach an additional screenshot.",
            "Muestra una captura adicional.",
            "Quisiera una foto adicional.",
            "Could you include one more banner image?",
            "screenshot",
            "captura",
            "photo",
            "foto",
            "banner",
            "image",
            "imagen",
            "activity",
            "actividad",
        )
        for prose in prose_cases:
            with self.subTest(prose=prose):
                report = base.replace(
                    "## Límites del diagnóstico",
                    f"{prose}\n\n## Límites del diagnóstico",
                    1,
                )
                self.assertIn(
                    "scenario C cannot request extra visual evidence",
                    validator.validate_client_report(report, self.bundle("scenario-c.json")),
                )

    def test_client_report_requires_a_fully_valid_fixture_before_parsing(self) -> None:
        cases = (
            (
                lambda bundle: bundle.pop("authorization_state"),
                "fixture missing required field: authorization_state",
            ),
            (
                lambda bundle: bundle["authorization_state"].update(external_actions="authorized"),
                "authorization_state has invalid external_actions",
            ),
            (
                lambda bundle: bundle.update(fixture_id="invalid"),
                "fixture has invalid fixture_id",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                bundle = self.bundle()
                mutate(bundle)
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.report(), bundle),
                )

    def test_source_derived_lift_probability_and_two_x_math_are_rejected(self) -> None:
        cases = (
            ("An official source proves a 20% lift.", "source-derived lift cannot be used in the client report"),
            ("Individual interview probability is 70%.", "individual outcome probability is not allowed"),
            ("The source contributes 2x to score math.", "aggregate 2x claims cannot affect score math"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertIn(
                    expected,
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_coach_heuristic_cannot_be_presented_as_linkedin_measurement_or_causality(self) -> None:
        for text in (
            "COACH_HEURISTIC is a LinkedIn measurement of recruiter ranking.",
            "COACH_HEURISTIC guarantees that recruiter response will increase.",
        ):
            with self.subTest(text=text):
                self.assertIn(
                    "COACH_HEURISTIC cannot be presented as a LinkedIn measurement or causal guarantee",
                    validator.validate_client_report(self.add_to_verdict(text), self.bundle()),
                )

    def test_scenario_c_cannot_request_evidence_that_changes_no_current_decision(self) -> None:
        report = self.report("scenario-c-es.md").replace(
            "## Límites del diagnóstico",
            (
                "### Pregunta 2\n\n"
                "- Pregunta: ¿Qué otro detalle visual puede compartirse?\n"
                "- Hecho: `FACT-JSC3-READY`\n"
                "- Puede cambiar: `score:visual`\n\n"
                "## Límites del diagnóstico"
            ),
            1,
        )
        self.assertIn(
            "scenario C cannot request evidence that changes no current decision",
            validator.validate_client_report(report, self.bundle("scenario-c.json")),
        )

    def test_advisory_rubric_is_versioned_and_cannot_override_validation(self) -> None:
        rubric_path = REPO_ROOT / "plugins" / "professional-growth-coach" / "tests" / "linkedin-client-report-advisory-rubric.json"
        rubric = json.loads(rubric_path.read_text(encoding="utf-8"))
        self.assertFalse(rubric["blocking"])
        self.assertTrue(rubric["cannot_override_deterministic_failure"])
        self.assertEqual(
            {"specificity", "decision_utility", "evidence_fidelity", "differentiation", "clarity", "actionability", "boundaries"},
            set(rubric["axes"]),
        )
        self.assertEqual(
            {"prompt_version", "rubric_version", "model", "textual_evidence"},
            set(rubric["required_result_fields"]),
        )
        parameters = inspect.signature(validator.validate_client_report).parameters
        self.assertNotIn("advisory", parameters)
        self.assertNotIn("override", parameters)
        self.assertFalse(hasattr(validator, "combine_validation"))


class LinkedInClientReportCliTests(unittest.TestCase):
    REPORT_A = FIXTURE_ROOT / "scenario-a-es.md"
    BUNDLE_A = FIXTURE_ROOT / "scenario-a.json"
    BUNDLE_B = FIXTURE_ROOT / "scenario-b.json"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(VALIDATOR_PATH), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cli_accepts_valid_pair_without_output(self) -> None:
        result = self.run_cli(str(self.REPORT_A), str(self.BUNDLE_A))
        self.assertEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("", result.stderr)

    def test_cli_returns_two_for_cross_case_pair(self) -> None:
        result = self.run_cli(str(self.REPORT_A), str(self.BUNDLE_B))
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("report evidence does not belong to fixture", result.stderr)

    def test_cli_errors_are_sorted_unique_and_one_per_stderr_line(self) -> None:
        result = self.run_cli(str(self.REPORT_A), str(self.BUNDLE_B))
        lines = result.stderr.splitlines()
        self.assertEqual(sorted(set(lines)), lines)
        self.assertTrue(all(line and "\n" not in line for line in lines))

    def test_cli_reports_file_and_json_failures_without_tracebacks(self) -> None:
        missing = self.run_cli("/no/such/report.md", str(self.BUNDLE_A))
        self.assertEqual(2, missing.returncode)
        self.assertEqual("", missing.stdout)
        self.assertNotIn("Traceback", missing.stderr)
        invalid_json = self.run_cli(str(self.REPORT_A), str(self.REPORT_A))
        self.assertEqual(2, invalid_json.returncode)
        self.assertNotIn("Traceback", invalid_json.stderr)

    def test_cli_has_no_advisory_override_interface(self) -> None:
        result = self.run_cli(
            str(self.REPORT_A), str(self.BUNDLE_A), "--advisory-override"
        )
        self.assertEqual(2, result.returncode)
        self.assertNotEqual("", result.stderr)

    def test_cli_converts_unhashable_nested_json_types_to_deterministic_errors(self) -> None:
        base = json.loads(self.BUNDLE_A.read_text(encoding="utf-8"))
        mutations = (
            lambda bundle: bundle["copy_blocks"][0].update(section=[]),
            lambda bundle: bundle["synthetic_fact_catalog"][0].update(claim_tokens=[[]]),
            lambda bundle: bundle.update(blocked_claims=[[]]),
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, mutate in enumerate(mutations):
                with self.subTest(index=index):
                    bundle = copy.deepcopy(base)
                    mutate(bundle)
                    path = Path(directory) / f"bundle-{index}.json"
                    path.write_text(json.dumps(bundle), encoding="utf-8")
                    result = self.run_cli(str(self.REPORT_A), str(path))
                    self.assertEqual(2, result.returncode)
                    self.assertEqual("", result.stdout)
                    self.assertNotEqual("", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)
                    lines = result.stderr.splitlines()
                    self.assertEqual(sorted(set(lines)), lines)


class LinkedInClientReportScoreTests(unittest.TestCase):
    def report(self, name: str) -> str:
        return (FIXTURE_ROOT / name).read_text(encoding="utf-8")

    def bundle(self, name: str) -> dict[str, object]:
        return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))

    def test_score_table_parses_all_seven_typed_localized_dimensions(self) -> None:
        self.assertTrue(hasattr(validator, "parse_score_table"))
        parsed = validator.parse_client_report(self.report("scenario-c-es.md"))
        rows = validator.parse_score_table(parsed)
        self.assertEqual(7, len(rows))
        self.assertEqual(
            ("domain", "state", "score", "evidence_ids", "reason"),
            rows[0]._fields,
        )
        self.assertEqual(
            ("visual", "not_scored", None, ("EVID-JSC3-VISUAL",)),
            (rows[0].domain, rows[0].state, rows[0].score, rows[0].evidence_ids),
        )
        self.assertEqual(
            ("headline", "about", "experience", "skills", "proof", "completeness"),
            tuple(row.domain for row in rows[1:]),
        )
        self.assertTrue(all(row.reason for row in rows))

    def test_half_up_score_uses_nonlegacy_values(self) -> None:
        self.assertTrue(hasattr(validator, "calculate_half_up_score"))
        cases = ((47.0, 70, 67), (50.5, 100, 51), (64.0, 85, 75), (79.0, 90, 88), (88.0, 100, 88))
        for points, weight, expected in cases:
            with self.subTest(points=points, weight=weight):
                self.assertEqual(expected, validator.calculate_half_up_score(points, weight))
        self.assertIsNone(validator.calculate_half_up_score(0.0, 0))

    def test_all_hand_authored_report_scores_reconcile_with_their_bundles(self) -> None:
        cases = (
            ("scenario-a-es.md", "scenario-a.json"),
            ("scenario-a-es-debug.md", "scenario-a.json"),
            ("scenario-b-en.md", "scenario-b.json"),
            ("scenario-c-es.md", "scenario-c.json"),
            ("scenario-d-en.md", "scenario-d.json"),
            ("scenario-d-banner-only-en.md", "scenario-d-banner-only.json"),
        )
        for report_name, bundle_name in cases:
            with self.subTest(report=report_name):
                mode = "debug" if report_name.endswith("-debug.md") else "normal"
                self.assertEqual(
                    [],
                    validator.validate_client_report(
                        self.report(report_name),
                        self.bundle(bundle_name),
                        appendix_mode=mode,
                    ),
                )

    def test_visible_overall_score_cannot_disagree_with_ledger(self) -> None:
        report = self.report("scenario-c-es.md").replace("64/100", "61/100", 1)
        errors = validator.validate_client_report(report, self.bundle("scenario-c.json"))
        self.assertIn("visible overall score 61 does not match ledger score 64", errors)

    def test_visible_domain_state_and_score_cannot_disagree_with_ledger(self) -> None:
        report = self.report("scenario-a-es.md")
        state_mutant = report.replace(
            "| Titular | Evaluada | 40 |",
            "| Titular | No evaluado | 40 |",
            1,
        )
        score_mutant = report.replace(
            "| Titular | Evaluada | 40 |",
            "| Titular | Evaluada | 41 |",
            1,
        )
        bundle = self.bundle("scenario-a.json")
        self.assertIn(
            "visible state for headline does not match ledger",
            validator.validate_client_report(state_mutant, bundle),
        )
        self.assertIn(
            "visible domain score for headline does not match ledger",
            validator.validate_client_report(score_mutant, bundle),
        )

    def test_each_score_row_requires_a_reason_and_evidence(self) -> None:
        report = self.report("scenario-a-es.md")
        missing_evidence = report.replace(
            "| Titular | Evaluada | 40 | EVID-JSC1-HEADLINE |",
            "| Titular | Evaluada | 40 |  |",
            1,
        )
        missing_reason = report.replace(
            "| Titular | Evaluada | 40 | EVID-JSC1-HEADLINE | La señal técnica está dispersa. |",
            "| Titular | Evaluada | 40 | EVID-JSC1-HEADLINE |  |",
            1,
        )
        bundle = self.bundle("scenario-a.json")
        self.assertIn(
            "score row headline requires evidence",
            validator.validate_client_report(missing_evidence, bundle),
        )
        self.assertIn(
            "score row headline requires a reason",
            validator.validate_client_report(missing_reason, bundle),
        )

    def test_score_table_requires_exactly_the_seven_canonical_dimensions(self) -> None:
        report = self.report("scenario-a-es.md")
        missing = report.replace(
            "| Aptitudes | Evaluada | 60 | EVID-JSC1-SKILLS | El contenido es específico. |\n",
            "",
            1,
        )
        self.assertIn(
            "score table must contain exactly the seven canonical dimensions",
            validator.validate_client_report(missing, self.bundle("scenario-a.json")),
        )

    def test_not_scored_dimensions_use_an_em_dash_and_are_excluded(self) -> None:
        self.assertTrue(hasattr(validator, "parse_score_table"))
        parsed = validator.parse_client_report(self.report("scenario-c-es.md"))
        visual = validator.parse_score_table(parsed)[0]
        self.assertEqual("not_scored", visual.state)
        self.assertIsNone(visual.score)
        report = self.report("scenario-c-es.md").replace(
            "| Identidad visual | No evaluado | — |",
            "| Identidad visual | No evaluado | 0 |",
            1,
        )
        self.assertIn(
            "unavailable dimension visual must be not scored, not zero",
            validator.validate_client_report(report, self.bundle("scenario-c.json")),
        )

    def test_partial_visual_modes_reject_an_aggregate_visual_score(self) -> None:
        cases = (
            (
                "scenario-d-en.md",
                "scenario-d.json",
                "| Visual identity | Not scored | — |",
                "| Visual identity | Scored | 60 |",
            ),
            (
                "scenario-d-banner-only-en.md",
                "scenario-d-banner-only.json",
                "| Visual identity | Not scored | — |",
                "| Visual identity | Scored | 60 |",
            ),
        )
        for report_name, bundle_name, old, new in cases:
            with self.subTest(report=report_name):
                report = self.report(report_name).replace(old, new, 1)
                self.assertIn(
                    "partial or structural visual evidence cannot have an aggregate visual score",
                    validator.validate_client_report(report, self.bundle(bundle_name)),
                )

    def test_visible_coverage_and_confidence_must_match_scored_coverage(self) -> None:
        report = self.report("scenario-c-es.md")
        coverage_mutant = report.replace(
            "**Cobertura:** 85 evaluado; 15 no evaluado",
            "**Cobertura:** 100 evaluado; 0 no evaluado",
            1,
        )
        confidence_mutant = report.replace("**Confianza:** media", "**Confianza:** alta", 1)
        bundle = self.bundle("scenario-c.json")
        self.assertIn(
            "visible coverage denominator/exclusions do not match ledger",
            validator.validate_client_report(coverage_mutant, bundle),
        )
        self.assertIn(
            "visible confidence does not match scored coverage",
            validator.validate_client_report(confidence_mutant, bundle),
        )

    def test_ledger_confidence_must_be_derived_from_scored_coverage(self) -> None:
        bundle = self.bundle("scenario-c.json")
        bundle["score_ledger"]["confidence"] = "high"
        self.assertIn(
            "ledger confidence does not match scored coverage",
            validator.validate_client_report(self.report("scenario-c-es.md"), bundle),
        )

    def test_report_rejects_unknown_and_cross_candidate_score_evidence(self) -> None:
        report = self.report("scenario-c-es.md")
        cases = ("EVID-JSC3-MISSING", "EVID-JSC1-HEADLINE")
        for evidence_id in cases:
            with self.subTest(evidence_id=evidence_id):
                mutant = report.replace("EVID-JSC3-HEADLINE", evidence_id, 1)
                self.assertIn(
                    "score row references unknown evidence",
                    validator.validate_client_report(mutant, self.bundle("scenario-c.json")),
                )

    def test_visible_domain_evidence_must_match_ledger_domain_evidence(self) -> None:
        report = self.report("scenario-a-es.md")
        cases = (
            "EVID-JSC1-ABOUT",
            "EVID-JSC1-HEADLINE, EVID-JSC1-HEADLINE",
        )
        for replacement in cases:
            with self.subTest(replacement=replacement):
                mutant = report.replace("EVID-JSC1-HEADLINE", replacement, 1)
                self.assertIn(
                    "visible evidence for headline does not match ledger",
                    validator.validate_client_report(mutant, self.bundle("scenario-a.json")),
                )

    def test_ledger_domain_evidence_ids_must_be_duplicate_free(self) -> None:
        bundle = self.bundle("scenario-a.json")
        headline = next(
            row for row in bundle["score_ledger"]["domains"] if row["domain"] == "headline"
        )
        headline["evidence_ids"].append("EVID-JSC1-HEADLINE")
        self.assertEqual(
            ["score_ledger.domains[1].evidence_ids has duplicate evidence_id: EVID-JSC1-HEADLINE"],
            validator.validate_client_report(self.report("scenario-a-es.md"), bundle),
        )

    def test_ledger_weighted_points_and_overall_score_reconcile(self) -> None:
        report = self.report("scenario-a-es.md")
        bundle = self.bundle("scenario-a.json")
        points_mutant = copy.deepcopy(bundle)
        points_mutant["score_ledger"]["numeric_weighted_total"] = 57.0
        overall_mutant = copy.deepcopy(bundle)
        overall_mutant["score_ledger"]["overall_score"] = 57
        self.assertIn(
            "score_ledger numeric_weighted_total does not reconcile",
            validator.validate_client_report(report, points_mutant),
        )
        self.assertIn(
            "score_ledger overall_score does not reconcile",
            validator.validate_client_report(report, overall_mutant),
        )

    def test_each_scored_ledger_row_recomputes_weighted_points_from_raw_score(self) -> None:
        bundle = self.bundle("scenario-a.json")
        headline = next(
            row for row in bundle["score_ledger"]["domains"] if row["domain"] == "headline"
        )
        headline["raw_score"] = 41
        report = self.report("scenario-a-es.md").replace(
            "| Titular | Evaluada | 40 |",
            "| Titular | Evaluada | 41 |",
            1,
        )
        self.assertIn(
            "score_ledger.domains[1] weighted_points do not reconcile",
            validator.validate_client_report(report, bundle),
        )

    def test_ledger_requires_all_seven_canonical_domains(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["score_ledger"]["domains"] = bundle["score_ledger"]["domains"][:-1]
        try:
            errors = validator.validate_client_report(self.report("scenario-a-es.md"), bundle)
        except Exception as error:  # pragma: no cover - the assertion names the regression
            self.fail(f"incomplete score ledger leaked {type(error).__name__}")
        self.assertIn("score_ledger must contain exactly the seven canonical domains", errors)

    def test_ledger_coverage_weights_must_follow_scored_domain_states(self) -> None:
        bundle = self.bundle("scenario-a.json")
        visual = bundle["score_ledger"]["domains"][0]
        visual["state"] = "not_scored"
        visual["raw_score"] = None
        visual["weighted_points"] = 0.0
        bundle["score_ledger"]["numeric_weighted_total"] = 49.0
        bundle["score_ledger"]["overall_score"] = 49
        report = self.report("scenario-a-es.md").replace(
            "| Identidad visual | Evaluada | 60 |",
            "| Identidad visual | No evaluado | — |",
            1,
        ).replace("58/100", "49/100", 1)
        self.assertIn(
            "score_ledger coverage weights do not reconcile",
            validator.validate_client_report(report, bundle),
        )

    def test_malformed_score_report_returns_a_deterministic_error(self) -> None:
        report = self.report("scenario-b-en.md").replace(
            "| Dimension | Status | Score | Evidence | Reason |",
            "| Dimension | Status | Score | Evidence | Basis |",
            1,
        )
        self.assertIn(
            "score table requires the localized five-column header",
            validator.validate_client_report(report, self.bundle("scenario-b.json")),
        )

    def test_malformed_score_bundle_returns_a_deterministic_error(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle.pop("score_ledger")
        self.assertIn(
            "fixture missing required field: score_ledger",
            validator.validate_client_report(self.report("scenario-a-es.md"), bundle),
        )

    def test_unhashable_nested_score_bundle_value_returns_an_error_not_an_exception(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["score_ledger"]["domains"][0]["state"] = ["scored"]
        try:
            errors = validator.validate_client_report(self.report("scenario-a-es.md"), bundle)
        except Exception as error:  # pragma: no cover - the assertion names the regression
            self.fail(f"malformed score bundle leaked {type(error).__name__}")
        self.assertIn("score_ledger.domains[0] has invalid state", errors)

    def test_invalid_evidence_modes_return_an_error_not_an_exception(self) -> None:
        for evidence_mode in (["authorized_visual_visible"], {"mode": "authorized_visual_visible"}, "unknown"):
            with self.subTest(evidence_mode=evidence_mode):
                bundle = self.bundle("scenario-a.json")
                bundle["evidence_mode"] = evidence_mode
                try:
                    errors = validator.validate_client_report(self.report("scenario-a-es.md"), bundle)
                except Exception as error:  # pragma: no cover - the assertion names the regression
                    self.fail(f"malformed evidence_mode leaked {type(error).__name__}")
                self.assertIn("fixture has invalid evidence_mode", errors)

    def test_huge_nested_score_bundle_value_returns_an_error_not_an_exception(self) -> None:
        bundle = self.bundle("scenario-a.json")
        bundle["score_ledger"]["domains"][0]["weighted_points"] = 10**1000
        try:
            errors = validator.validate_client_report(self.report("scenario-a-es.md"), bundle)
        except Exception as error:  # pragma: no cover - the assertion names the regression
            self.fail(f"malformed score bundle leaked {type(error).__name__}")
        self.assertIn("score_ledger.domains[0] has invalid weighted_points", errors)

    def test_non_text_report_returns_an_error_not_an_exception(self) -> None:
        try:
            errors = validator.validate_client_report(None, self.bundle("scenario-a.json"))
        except Exception as error:  # pragma: no cover - the assertion names the regression
            self.fail(f"malformed report leaked {type(error).__name__}")
        self.assertEqual(["client report must be Markdown text"], errors)


if __name__ == "__main__":
    unittest.main()
