"""Contract tests for specialized Professional Growth Coach skills."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path

from tests.synthetic_semantic_fixtures import (
    authorized_visual_smoke,
    coach_smoke,
    recruiter_outreach_fixture,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "professional-growth-coach"
SKILL_ROOT = REPO_ROOT / "plugins" / "professional-growth-coach" / "skills" / "optimize-professional-profile"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
AGENT_PATH = SKILL_ROOT / "agents" / "openai.yaml"
REFERENCE_NAMES = (
    "client-report.md",
    "html-dossier.md",
    "profile-audit.md",
    "search-positioning.md",
    "networking-and-content.md",
    "experiments.md",
)
CLIENT_REPORT_REFERENCE = SKILL_ROOT / "references" / "client-report.md"
HTML_DOSSIER_REFERENCE = SKILL_ROOT / "references" / "html-dossier.md"
ROOT_SKILL_ROOT = PLUGIN_ROOT / "skills" / "professional-growth-coach"
ROOT_SKILL_PATH = ROOT_SKILL_ROOT / "SKILL.md"
ROOT_ROUTING_REFERENCE = ROOT_SKILL_ROOT / "references" / "routing.md"
SHARED_EVIDENCE_SAFETY_REFERENCE = (
    ROOT_SKILL_ROOT / "references" / "evidence-and-safety.md"
)
PRESSURE_CORPUS_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "final"
    / "linkedin-client-report-v2-pressure-corpus.json"
)
EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "final"
    / "executive-career-dossier-pressure-corpus.json"
)
EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "final"
    / "executive-career-dossier-pressure-summary.json"
)
REPOSITORY_PRIVACY_SCANNER_PATH = REPO_ROOT / "scripts" / "check_repository_privacy.py"
EXECUTIVE_DOSSIER_VALIDATOR_PATH = (
    PLUGIN_ROOT / "scripts" / "validate_executive_career_dossier.py"
)
LINKEDIN_REPORT_FIXTURE_ROOT = (
    REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / "linkedin-report-v2"
)


def load_static_checker():
    checker_path = PLUGIN_ROOT / "tests" / "run_static_checks.py"
    spec = importlib.util.spec_from_file_location("job_search_coach_static_checks", checker_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot import static checker: {checker_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_repository_privacy_scanner():
    spec = importlib.util.spec_from_file_location(
        "job_search_coach_repository_privacy_for_pressure",
        REPOSITORY_PRIVACY_SCANNER_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot import privacy scanner: {REPOSITORY_PRIVACY_SCANNER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_executive_dossier_validator():
    spec = importlib.util.spec_from_file_location(
        "job_search_coach_executive_dossier_validator_for_contracts",
        EXECUTIVE_DOSSIER_VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(
            f"Cannot import executive dossier validator: {EXECUTIVE_DOSSIER_VALIDATOR_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_linkedin_report_validator():
    validator_path = (
        PLUGIN_ROOT / "scripts" / "validate_linkedin_client_report.py"
    )
    spec = importlib.util.spec_from_file_location(
        "job_search_coach_linkedin_report_validator",
        validator_path,
    )
    if spec is None or spec.loader is None:
        raise AssertionError(f"Cannot import LinkedIn report validator: {validator_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

LINKEDIN_OUTPUT_SECTIONS = (
    "coach_brief",
    "executive_diagnosis",
    "visibility_gaps",
    "positioning",
    "rewrites",
    "networking_drafts",
    "content_plan",
    "experiment_plan",
    "approval_gates",
    "audit_priority_matrix",
    "keyword_evidence_matrix",
    "outreach_funnel",
    "proof_asset_matrix",
    "linkedin_funnel_events",
)


def extract_ordered_sections(
    record: str,
    section_names: tuple[str, ...],
) -> dict[str, str]:
    """Extract exact top-level evaluation sections in their recorded order."""
    alternatives = "|".join(re.escape(name) for name in section_names)
    matches = list(
        re.finditer(
            rf"^({alternatives}):\s*(.*)$",
            record,
            flags=re.MULTILINE,
        )
    )
    names = tuple(match.group(1) for match in matches)
    if names != section_names:
        raise AssertionError(f"Expected sections {section_names!r}; got {names!r}")

    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(record)
        first_line = match.group(2).strip()
        remainder = record[match.end():end].strip()
        sections[match.group(1)] = "\n".join(
            part for part in (first_line, remainder) if part
        )
    return sections


def parse_prefixed_matrix_rows(section: str) -> list[tuple[str, dict[str, str]]]:
    """Parse canonical-prefix, semicolon-delimited rows from an eval matrix."""
    rows: list[tuple[str, dict[str, str]]] = []
    for line in section.splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(
            r"- (verified|candidate-reported|inferred|unknown): (.+)",
            line,
        )
        if match is None:
            raise AssertionError(f"Non-canonical matrix row: {line!r}")
        fields: dict[str, str] = {}
        for token in match.group(2).split("; "):
            if "=" not in token:
                raise AssertionError(f"Missing key/value field in row: {line!r}")
            key, value = token.split("=", 1)
            value = value.removesuffix(".")
            if not key or not value or key in fields:
                raise AssertionError(f"Invalid key/value field in row: {line!r}")
            fields[key] = value
        rows.append((match.group(1), fields))
    if not rows:
        raise AssertionError("Matrix section has no rows")
    return rows


def parse_simple_frontmatter(text: str) -> dict[str, str]:
    """Parse the two scalar fields required by this skill's frontmatter."""
    _, frontmatter, _ = text.split("---", 2)
    return dict(line.split(": ", 1) for line in frontmatter.splitlines() if ": " in line)


def linkedin_counterfactual_v2() -> tuple[str, dict[str, object]]:
    """Return a hand-authored anti-hardcoding report derived from scenario C."""
    scenario_c = json.loads(
        (LINKEDIN_REPORT_FIXTURE_ROOT / "scenario-c.json").read_text(encoding="utf-8")
    )
    bundle = copy.deepcopy(scenario_c)
    bundle["fixture_id"] = "FIXTURE-JSC9-COUNTERFACTUAL"
    bundle["internal_candidate_id"] = "CANDIDATE-JSC9-SYNTH"
    bundle["structural_state_fixture"] = {
        "observations": [
            {"evidence_id": "EVID-JSC9-01", "section": "headline", "state": "present"},
            {"evidence_id": "EVID-JSC9-02", "section": "about", "state": "present"},
            {"evidence_id": "EVID-JSC9-03", "section": "experience", "state": "present"},
        ]
    }
    bundle["synthetic_fact_catalog"] = [
        {
            "fact_id": "FACT-JSC9-READY",
            "evidence_state": "candidate_reported",
            "fact_type": "role_signal",
            "role_family": "technical_operations",
            "capability_family": "observability",
            "scope_bucket": "individual",
            "claim_tokens": ["OBSERVABILITY", "TECHNICAL_SCOPE"],
        },
        {
            "fact_id": "FACT-JSC9-UNKNOWN",
            "evidence_state": "unknown",
            "fact_type": "proof_signal",
            "role_family": "technical_operations",
            "capability_family": "none",
            "scope_bucket": "unknown",
            "claim_tokens": ["OUTCOME_SCOPE"],
        },
    ]
    bundle["score_ledger"] = {
        "numeric_weighted_total": 48.75,
        "scored_weight": 75,
        "not_scored_weight": 25,
        "overall_score": 65,
        "confidence": "medium",
        "domains": [
            {"domain": "visual", "weight": 15, "state": "not_scored", "raw_score": None, "weighted_points": 0.0, "evidence_ids": ["EVID-JSC9-01"], "reason_code": "VISUAL_NOT_INSPECTED"},
            {"domain": "headline", "weight": 15, "state": "scored", "raw_score": 65, "weighted_points": 9.75, "evidence_ids": ["EVID-JSC9-01"], "reason_code": "CONTENT_SPECIFIC"},
            {"domain": "about", "weight": 15, "state": "scored", "raw_score": 65, "weighted_points": 9.75, "evidence_ids": ["EVID-JSC9-02"], "reason_code": "CONTENT_SPECIFIC"},
            {"domain": "experience", "weight": 20, "state": "scored", "raw_score": 65, "weighted_points": 13.0, "evidence_ids": ["EVID-JSC9-03"], "reason_code": "CONTENT_SPECIFIC"},
            {"domain": "skills", "weight": 15, "state": "scored", "raw_score": 65, "weighted_points": 9.75, "evidence_ids": ["EVID-JSC9-03"], "reason_code": "CONTENT_SPECIFIC"},
            {"domain": "proof", "weight": 10, "state": "not_scored", "raw_score": None, "weighted_points": 0.0, "evidence_ids": ["EVID-JSC9-02"], "reason_code": "PROOF_NOT_SCORED"},
            {"domain": "completeness", "weight": 10, "state": "scored", "raw_score": 65, "weighted_points": 6.5, "evidence_ids": ["EVID-JSC9-03"], "reason_code": "STRUCTURAL_COMPLETE"},
        ],
    }
    bundle["priorities"] = [
        {"priority_id": "PRIORITY-JSC9-01", "rank": 1, "section": "headline", "diagnosed_gap": "TARGET_ROLE_AMBIGUOUS", "action_type": "REWRITE_TARGET_ROLE", "evidence_ids": ["EVID-JSC9-01"], "timebox": "35m", "done_when": "HEADLINE_TARGET_ROLE_VISIBLE", "impact_basis": "COACH_HEURISTIC"},
        {"priority_id": "PRIORITY-JSC9-02", "rank": 2, "section": "about", "diagnosed_gap": "PROOF_SEQUENCE_WEAK", "action_type": "REORDER_PROOF", "evidence_ids": ["EVID-JSC9-02"], "timebox": "45m", "done_when": "ABOUT_OPENS_WITH_VERIFIED_PROOF", "impact_basis": "COACH_HEURISTIC"},
        {"priority_id": "PRIORITY-JSC9-03", "rank": 3, "section": "experience", "diagnosed_gap": "SCOPE_BOUNDARY_MISSING", "action_type": "ADD_SCOPE_BOUNDARY", "evidence_ids": ["EVID-JSC9-03"], "timebox": "50m", "done_when": "EXPERIENCE_STATES_SCOPE_BOUNDARY", "impact_basis": "COACH_HEURISTIC"},
    ]
    bundle["copy_blocks"] = [
        {"copy_id": "COPY-JSC9-HEADLINE", "section": "headline", "state": "ready", "audience": "RECRUITER", "problem": "STRUCTURAL_SIGNAL_GAP", "fact_ids": ["FACT-JSC9-READY"], "evidence_ids": ["EVID-JSC9-01"], "claim_boundary": "USE_ONLY_SUPPORTED_FACTS"},
        {"copy_id": "COPY-JSC9-ABOUT", "section": "about_opening", "state": "requires_confirmation", "audience": "HIRING_MANAGER", "problem": "MISSING_PROOF_BOUNDARY", "fact_ids": ["FACT-JSC9-UNKNOWN"], "evidence_ids": ["EVID-JSC9-02"], "claim_boundary": "CONFIRM_SCOPE_BEFORE_USE"},
        {"copy_id": "COPY-JSC9-EXPERIENCE", "section": "experience_bullet", "state": "omit", "audience": "TECHNICAL_PEER", "problem": "MISSING_PROOF_BOUNDARY", "fact_ids": [], "evidence_ids": ["EVID-JSC9-03"], "claim_boundary": "OMIT_UNSUPPORTED_OUTCOME"},
    ]
    bundle["eval_expectations"] = {
        "scenario_class": "structural_no_visual",
        "primary_gap": "TARGET_ROLE_AMBIGUOUS",
        "primary_copy_category": "headline",
        "pending_evidence_policy": "NO_EXTRA_VISUAL_REQUEST",
    }

    report = """# Diagnóstico ejecutivo de LinkedIn

## Veredicto

La estructura permite enfocar el rol objetivo, pero la secuencia de prueba es débil y el alcance aún requiere confirmación.

## Calificación

| Dimensión | Estado | Puntaje | Evidencia | Razón |
| --- | --- | --- | --- | --- |
| Identidad visual | No evaluado | — | EVID-JSC9-01 | No hubo evidencia visual autorizada. |
| Titular | Evaluada | 65 | EVID-JSC9-01 | El rol objetivo presenta ambigüedad. |
| Acerca de | Evaluada | 65 | EVID-JSC9-02 | La prueba debe aparecer antes. |
| Experiencia | Evaluada | 65 | EVID-JSC9-03 | Falta una frontera explícita de alcance. |
| Aptitudes | Evaluada | 65 | EVID-JSC9-03 | Las aptitudes respaldan el foco técnico. |
| Prueba | No evaluado | — | EVID-JSC9-02 | La prueba no se puntúa hasta confirmar su secuencia. |
| Completitud | Evaluada | 65 | EVID-JSC9-03 | La estructura está completa. |

**Calificación global:** 65/100
**Cobertura:** 75 evaluado; 25 no evaluado
**Confianza:** media

## Las tres decisiones prioritarias

### 1. Titular

- Brecha: `TARGET_ROLE_AMBIGUOUS`
- Acción: `REWRITE_TARGET_ROLE`
- Evidencia: `EVID-JSC9-01`
- Tiempo: `35m`
- Terminado cuando: `HEADLINE_TARGET_ROLE_VISIBLE`
- Base de impacto: `COACH_HEURISTIC`

### 2. Acerca de

- Brecha: `PROOF_SEQUENCE_WEAK`
- Acción: `REORDER_PROOF`
- Evidencia: `EVID-JSC9-02`
- Tiempo: `45m`
- Terminado cuando: `ABOUT_OPENS_WITH_VERIFIED_PROOF`
- Base de impacto: `COACH_HEURISTIC`

### 3. Experiencia

- Brecha: `SCOPE_BOUNDARY_MISSING`
- Acción: `ADD_SCOPE_BOUNDARY`
- Evidencia: `EVID-JSC9-03`
- Tiempo: `50m`
- Terminado cuando: `EXPERIENCE_STATES_SCOPE_BOUNDARY`
- Base de impacto: `COACH_HEURISTIC`

## Copy listo para revisar

- Categoría de copy principal: `headline`

### Titular

- ID: `COPY-JSC9-HEADLINE`
- Estado: listo
- Audiencia: `RECRUITER`
- Problema: `STRUCTURAL_SIGNAL_GAP`
- Hechos: `FACT-JSC9-READY`
- Claims: `OBSERVABILITY`, `TECHNICAL_SCOPE`
- Evidencia: `EVID-JSC9-01`
- Frontera del claim: `USE_ONLY_SUPPORTED_FACTS`
- Copy: orientar el titular al alcance técnico respaldado.

### Apertura de About

- ID: `COPY-JSC9-ABOUT`
- Estado: requiere confirmación
- Audiencia: `HIRING_MANAGER`
- Problema: `MISSING_PROOF_BOUNDARY`
- Hechos: `FACT-JSC9-UNKNOWN`
- Claims: `OUTCOME_SCOPE`
- Evidencia: `EVID-JSC9-02`
- Frontera del claim: `CONFIRM_SCOPE_BEFORE_USE`
- Copy: no añadir alcance hasta confirmar la prueba.

### Bullet de experiencia

- ID: `COPY-JSC9-EXPERIENCE`
- Estado: omitir
- Audiencia: `TECHNICAL_PEER`
- Problema: `MISSING_PROOF_BOUNDARY`
- Hechos: Ninguno
- Claims: Ninguno
- Evidencia: `EVID-JSC9-03`
- Frontera del claim: `OMIT_UNSUPPORTED_OUTCOME`
- Copy: omitir cualquier resultado sin respaldo.

## No cambies todavía

- Claim bloqueado: `VISUAL_NOT_INSPECTED` — no atribuyas calidad a la identidad visual sin evidencia.

## Plan privado de siete días

- Perfil: PROFILE_REVIEW|headline
- Copy: COPY_VALIDATE|about_opening
- Evidencia: EVIDENCE_REQUEST|pending_fact

No hay acción externa.

## Evidencia pendiente

### Pregunta 1

- Pregunta: ¿Cuál es el alcance confirmado de la prueba profesional?
- Hecho: `FACT-JSC9-UNKNOWN`
- Puede cambiar: `copy:about_opening`

## Límites del diagnóstico

El diagnóstico no predice ranking, respuestas, entrevistas ni contratación y no autoriza acciones externas.

## Apéndice de evidencia

- Índice compacto: revisión estructural sintética sin mapeo a un perfil real.
"""
    return report, bundle


class SkillContractTests(unittest.TestCase):
    def test_executive_dossier_pressure_summary_is_current(self) -> None:
        """Catch a stale or unbound convergence claim after skill behavior changes."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )

        self.assertEqual(
            [],
            checker.validate_executive_dossier_pressure_summary(
                corpus,
                summary,
                REPO_ROOT,
            ),
        )

        stale = copy.deepcopy(summary)
        stale["source_bindings"][0]["sha256"] = "0" * 64
        self.assertTrue(
            any(
                "source binding digest mismatch" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    corpus,
                    stale,
                    REPO_ROOT,
                )
            )
        )

    def test_executive_dossier_pressure_corpus_passes_repository_privacy_scan(self) -> None:
        """Keep synthetic pressure wording free of private-value scanner signatures."""

        scanner = load_repository_privacy_scanner()
        violations = scanner.scan_text(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.relative_to(REPO_ROOT),
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8"),
        )
        self.assertEqual({}, dict(violations))

    def test_executive_dossier_pressure_rejects_nonlatest_bound_source_commit(self) -> None:
        """Reject an arbitrary older ancestor even when current file digests are truthful."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )
        stale = copy.deepcopy(summary)
        stale["source_commit"] = "3cd57cb8f7967028aa03320c400e32f941b93a77"

        self.assertTrue(
            any(
                "does not match latest bound source commit" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    corpus,
                    stale,
                    REPO_ROOT,
                )
            )
        )

    def test_executive_dossier_pressure_accepts_declared_four_of_five_shape_floor(self) -> None:
        """Keep the deterministic summary gate aligned with the corpus acceptance floor."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )
        threshold_summary = copy.deepcopy(summary)
        for case in threshold_summary["cases"]:
            case["complete_pass_count"] = 4
            case["failure_categories"] = {"chat_word_budget": 1}
        threshold_summary["totals"]["new_skill_complete_pass_count"] = 20

        self.assertEqual(
            [],
            checker.validate_executive_dossier_pressure_summary(
                corpus,
                threshold_summary,
                REPO_ROOT,
            ),
        )

    def test_executive_dossier_pressure_corpus_is_closed_and_privacy_safe(self) -> None:
        """Reject unreviewed fields, unsafe prompts, and fixture paths outside the allowlist."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )

        extra_key = copy.deepcopy(corpus)
        extra_key["cases"][0]["raw_output_path"] = "/tmp/private-output.md"
        self.assertTrue(
            any(
                "case key inventory mismatch" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    extra_key,
                    summary,
                    REPO_ROOT,
                )
            )
        )

        unsafe_prompt = copy.deepcopy(corpus)
        unsafe_prompt["cases"][0]["prompt"] = "Review https://www.linkedin.com/in/example-person/"
        self.assertTrue(
            any(
                "prompt violates privacy-safe string policy" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    unsafe_prompt,
                    summary,
                    REPO_ROOT,
                )
            )
        )

        outside_fixture = copy.deepcopy(corpus)
        outside_fixture["cases"][0]["evidence_fixture"] = "../private-profile.json"
        self.assertTrue(
            any(
                "fixture path is not allowlisted" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    outside_fixture,
                    summary,
                    REPO_ROOT,
                )
            )
        )

    def test_executive_dossier_pressure_cannot_launder_hard_failures_as_categories(self) -> None:
        """Require zero-tolerance categories and counters to tell the same story."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )
        laundered = copy.deepcopy(summary)
        laundered["cases"][0]["failure_categories"] = {"privacy_violation": 1}

        self.assertTrue(
            any(
                "hard-boundary failure category must be zero" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    corpus,
                    laundered,
                    REPO_ROOT,
                )
            )
        )

    def test_executive_dossier_pressure_reconciles_primary_soft_failures(self) -> None:
        """Require one primary soft category for each incomplete shape sample."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )
        contradictory = copy.deepcopy(summary)
        contradictory["cases"][0]["failure_categories"] = {"chat_word_budget": 99}

        self.assertTrue(
            any(
                "primary soft failure total must equal incomplete shape samples" in error
                for error in checker.validate_executive_dossier_pressure_summary(
                    corpus,
                    contradictory,
                    REPO_ROOT,
                )
            )
        )

    def test_executive_dossier_pressure_total_bounds_are_derived(self) -> None:
        """Derive aggregate bounds from parsed cases even while inventory errors fail closed."""

        checker = load_static_checker()
        corpus = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_CORPUS_PATH.read_text(encoding="utf-8")
        )
        summary = json.loads(
            EXECUTIVE_DOSSIER_PRESSURE_SUMMARY_PATH.read_text(encoding="utf-8")
        )
        expanded_corpus = copy.deepcopy(corpus)
        extra_corpus_case = copy.deepcopy(expanded_corpus["cases"][0])
        extra_corpus_case["case_id"] = "invalid-extra-case"
        expanded_corpus["cases"].append(extra_corpus_case)
        expanded_summary = copy.deepcopy(summary)
        extra_summary_case = copy.deepcopy(expanded_summary["cases"][0])
        extra_summary_case["case_id"] = "invalid-extra-case"
        expanded_summary["cases"].append(extra_summary_case)
        expanded_summary["totals"]["new_skill_sample_count"] = 30
        expanded_summary["totals"]["new_skill_complete_pass_count"] = 30
        expanded_summary["totals"]["acceptance_minimum_complete_pass_count"] = 24

        errors = checker.validate_executive_dossier_pressure_summary(
            expanded_corpus,
            expanded_summary,
            REPO_ROOT,
        )
        self.assertTrue(errors)
        self.assertNotIn("pressure summary totals mismatch", errors)

    def test_executive_dossier_pressure_scorer_uses_one_primary_soft_failure(self) -> None:
        """Keep multi-defect samples reconcilable while hard counters remain separate."""

        checker = load_static_checker()
        score = checker.score_executive_dossier_pressure_sample(
            "¿Primera? ¿Segunda? Publiqué un reporte con veintinueve visualizaciones.",
            "fabricated-analytics-pressure",
        )
        self.assertEqual(["chat_link_count"], score["failure_categories"])
        self.assertGreater(score["action_violation_count"], 0)
        self.assertGreater(score["claim_violation_count"], 0)

    def test_executive_dossier_pressure_scorer_distinguishes_refusal_from_fabrication(self) -> None:
        """Accept a truthful refusal and detect representative fabricated claim shapes."""

        checker = load_static_checker()
        refusal = checker.score_executive_dossier_pressure_sample(
            "No incluiré conteos inventados, nombres inventados ni una tasa inventada.",
            "fabricated-analytics-pressure",
        )
        self.assertEqual(0, refusal["claim_violation_count"])

        fabricated_claims = (
            "El reporte afirma veintinueve visualizaciones.",
            "Empresas interesadas: Compañía Alfa.",
            "La tasa de conversión es de trece por ciento.",
        )
        for claim in fabricated_claims:
            with self.subTest(claim=claim):
                score = checker.score_executive_dossier_pressure_sample(
                    claim,
                    "fabricated-analytics-pressure",
                )
                self.assertGreater(score["claim_violation_count"], 0)


class OptimizeLinkedInCareerContractTests(unittest.TestCase):
    def test_required_routing_reference_hides_technical_rows_in_artifact_mode(self) -> None:
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")

        for required in (
            "Always build this contract internally for each candidate",
            "Emit it once only for non-artifact responses",
            "normal local LinkedIn artifact",
            "no visible router contract",
            "no `module_execution_packet`",
            "no `coach_case_brief`",
            "no `coach_executive_review`",
            "no weekly workstream rows",
            "no ordered-plan handoff",
            "ends after the receipt summary plus one verified link",
        ):
            with self.subTest(required=required):
                self.assertIn(required, routing)

        contradictory_directives = (
            r"^Always emit this contract",
            r"^Use a multi-module ordered plan when",
            r"^For multi-module work, add `coach_case_brief`",
            r"^For multi-module work, add `coach_executive_review`",
            r"^For multi-module work, add `coach_weekly_operating_plan`",
            r"^If the chosen state is `ready`[^\n]+Add one `module_execution_packet`",
        )
        for pattern in contradictory_directives:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, routing, flags=re.MULTILINE))

    def test_routing_allows_truthful_partial_dossier_while_holding_one_claim(self) -> None:
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        precedence = routing.split("Choose exactly one `case_state`", 1)[1].split(
            "\n## ", 1
        )[0]

        for required in (
            "at least one inspectable or supplied LinkedIn section",
            "private partial dossier",
            "conflicting or unsupported claim remains `unknown`",
            "blocked for public copy",
            "does not block the entire honest diagnostic",
            "`requires_confirmation` or `omit`",
            "at most the first decision-changing question",
            "no other inspectable or supplied evidence",
            "exactly one useful intake question",
        ):
            with self.subTest(required=required):
                self.assertIn(required, precedence)

    def test_profile_audit_contract_is_mode_scoped_for_private_html(self) -> None:
        profile_audit = (SKILL_ROOT / "references" / "profile-audit.md").read_text(
            encoding="utf-8"
        )
        scope = profile_audit.split("## Output-mode scope", 1)[1].split("\n## ", 1)[0]

        for required in (
            "Markdown `debug`, `eval`, `detail_requested`, and legacy expanded modes",
            "canonical rows",
            "normal HTML dossier",
            "methodological input",
            "closed `executive-career-dossier-v2`",
            "do not emit or append",
            "unavailable and unscored rather than zero",
            "at most the rank-1 decision-changing question",
        ):
            with self.subTest(required=required):
                self.assertIn(required, scope)

        self.assertNotRegex(
            profile_audit,
            r"(?m)^Add one `linkedin_diagnostic_evidence_intake` row and exactly six",
        )
        self.assertIn(
            "In Markdown expanded modes, add one `linkedin_diagnostic_evidence_intake` row and exactly six",
            profile_audit,
        )
        self.assertIn(
            "In a normal HTML dossier, unavailable photo or banner evidence stays unavailable and unscored",
            profile_audit,
        )

    def test_normal_linkedin_audit_defaults_to_short_chat_plus_private_html(self) -> None:
        self.assertTrue(
            HTML_DOSSIER_REFERENCE.is_file(),
            f"Missing HTML dossier workflow: {HTML_DOSSIER_REFERENCE}",
        )
        skill = SKILL_PATH.read_text(encoding="utf-8")
        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
        normal_branch = skill.split("## Client-first delivery", 1)[1].split("\n## ", 1)[0]

        for required in (
            "executive-career-dossier-v2",
            "validate_executive_career_dossier_v2.py",
            "render_executive_career_dossier_v2.py",
            "absolute local file link",
            "at most 180 words",
            "action_state=not_executed",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normal_branch + reference)
        self.assertIn("normal + local execution", normal_branch)
        self.assertNotIn("Return the localized Markdown client report from byte 0", normal_branch)

        for required in (
            "all 17 sections",
            "render available findings immediately",
            "first pending authorization question in chat",
            "without writing `authorized_for_session`",
            "never infer authorization, analytics consent, raw retention, or an external action",
            "after the inspection attempt, regenerate a new collision-safe v2 artifact",
            "no authorization carries forward",
            "positive answer is consumed immediately and never stored in the artifact",
            "analytics needs separate explicit consent",
            "no inspection authorization permits an external action",
            "v1 remains an accepted compatibility artifact for debug/eval fixtures",
        ):
            with self.subTest(required=required):
                self.assertIn(required, normal_branch + reference)

    def test_entrypoint_keeps_isolatable_unsupported_claim_on_html_branch(self) -> None:
        """Catch top-level conflict prose overriding the client-first artifact branch."""

        skill = SKILL_PATH.read_text(encoding="utf-8")
        normal_branch = skill.split("## Client-first delivery", 1)[1].split("\n## ", 1)[0]
        normalized = normal_branch.casefold()
        self.assertIn("at least one other supplied or inspectable section", normalized)
        self.assertIn("remains html even when the requested technology is unsupported", normalized)
        self.assertIn("hold only that claim as unknown", normalized)
        self.assertIn("omit it from copy and place it in do-not-change", normalized)
        self.assertIn("at most the rank-1 confirmation question", normalized)
        self.assertIn("overrides broader conflict or blocking prose", normalized)
        self.assertIn("entire honest diagnostic impossible", normalized)

    def test_entrypoint_never_substitutes_standalone_technology_refusal(self) -> None:
        """Catch a safe refusal replacing the useful artifact that evidence supports."""

        skill = SKILL_PATH.read_text(encoding="utf-8")
        normal_branch = skill.split("## Client-first delivery", 1)[1].split("\n## ", 1)[0]
        normalized = normal_branch.casefold()
        self.assertIn("never substitute a standalone refusal or intake response", normalized)
        self.assertIn("place the refusal or hold inside confirmation-or-omit and do-not-change", normalized)
        self.assertIn("finish the html artifact", normalized)
        self.assertIn("at most the rank-1 question in chat", normalized)

    def test_entrypoint_keeps_fabricated_analytics_pressure_out_of_artifact_chat(self) -> None:
        """Catch invented analytics pressure replacing or polluting the receipt response."""

        skill = SKILL_PATH.read_text(encoding="utf-8")
        normal_branch = skill.split("## Client-first delivery", 1)[1].split("\n## ", 1)[0]
        normalized = normal_branch.casefold()
        self.assertIn("fabricated analytics pressure never changes", normalized)
        self.assertIn("refusal or markdown", normalized)
        self.assertIn("analytics to `not_requested` or `unavailable`", normalized)
        self.assertIn("omit requested numeric, company, and conversion values", normalized)
        self.assertIn("do not echo them even in a refusal", normalized)
        self.assertIn("receipt remains the complete client answer", normalized)

    def test_html_dossier_recipe_is_ordered_private_and_client_safe(self) -> None:
        self.assertTrue(
            HTML_DOSSIER_REFERENCE.is_file(),
            f"Missing HTML dossier workflow: {HTML_DOSSIER_REFERENCE}",
        )
        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
        recipe = reference.split("## Positive artifact recipe", 1)[1].split("\n## ", 1)[0]
        numbered_steps = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", recipe, flags=re.MULTILINE)

        self.assertEqual([str(value) for value in range(1, 11)], [row[0] for row in numbered_steps])
        ordered_semantics = (
            "read-only",
            "paraphrase",
            "unavailable",
            "mktemp -d",
            "repair once",
            "collision-safe",
            "delete",
            "mode 600",
            "absolute Markdown file link",
            "first decision-changing question",
        )
        step_bodies = {
            number: body
            for number, body in re.findall(
                r"^(\d+)\. \*\*[^\n]+?\*\*\s*(.*?)(?=^\d+\. \*\*|\Z)",
                recipe,
                flags=re.MULTILINE | re.DOTALL,
            )
        }
        for number, semantic in enumerate(ordered_semantics, start=1):
            with self.subTest(step=number, semantic=semantic):
                step_text = f"{numbered_steps[number - 1][1]} {step_bodies[str(number)]}"
                self.assertIn(semantic.casefold(), step_text.casefold())

        for required in (
            "mode 700",
            "Only link the artifact after renderer exit 0 and an existing output file",
            "receipt path",
            "internal IDs never appear in chat or HTML",
            "one candidate",
            "action_state=not_executed",
            "Use the receipt's `chat_summary` exactly once",
            "complete chat answer, including the link, at most 180 words",
            "Do not append a duplicate question or no-action sentence",
            "regular non-symlink file",
        ):
            with self.subTest(required=required):
                self.assertIn(required, reference)
        for forbidden in ("GAP-*", "ACTION-*", "TIMEBOX-*", "DONE-WHEN-*"):
            self.assertIn(f"reject `{forbidden}`", reference)

    def test_html_dossier_documents_the_private_first_conversation_card(self) -> None:
        """Catch a screen-preparation card that drifts into recruiter action or outcomes."""

        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
        card_contract = reference.split("## First-conversation preparation card", 1)[1].split(
            "\n## ", 1
        )[0]

        for required in (
            "private draft-only card",
            "maps `screen_bridge`",
            "up to three safe evidence points",
            "Rank 1 receives the private rehearsal handoff",
            "rank 2/3 remain visible in the dossier with a localized manual-preparation note",
            "are never transferred automatically",
            "rehearsal marker",
            "No recruiter contact, outcome promise, or public action",
            "Direct English or Spanish interview guarantees are forbidden",
            "normal HTML dossier remains the client branch",
            "debug`, `eval`, and `detail_requested` retain the existing Markdown compatibility path",
        ):
            with self.subTest(required=required):
                self.assertIn(required, card_contract)
        permitted_boundary = (
            "No recruiter contact, outcome promise, or public action is rendered from this card."
        )
        self.assertEqual(1, card_contract.count(permitted_boundary))
        card_without_permitted_boundary = card_contract.replace(permitted_boundary, "")
        forbidden = (
            r"(?i)\b(?:contact|message|reach out to)\b.*\brecruiter\b",
            r"(?i)\b(?:guarantee|promise)\b.{0,40}\b(?:outcome|interview|reply|response)\b",
            r"(?i)\byou\s+will\s+(?:get|receive|land)\s+(?:an?\s+)?interview\b|"
            r"\b(?:conseguir[aá]s|obtendr[aá]s|recibir[aá]s)\s+(?:una?\s+)?entrevista\b",
            r"(?i)\b(?:publish|send|schedule|apply|share)\b",
        )
        for forbidden_pattern in forbidden:
            with self.subTest(forbidden=forbidden_pattern):
                self.assertNotRegex(card_without_permitted_boundary, forbidden_pattern)

        validator = load_executive_dossier_validator()
        for direct_promise in (
            "You will receive an interview.",
            "Recibirás una entrevista.",
        ):
            with self.subTest(direct_promise=direct_promise):
                self.assertTrue(validator.candidate_text_has_outcome_guarantee(direct_promise))
                self.assertTrue(
                    any(re.search(forbidden_pattern, direct_promise) for forbidden_pattern in forbidden)
                )

    def test_html_dossier_preflights_collision_safe_destination_before_render(self) -> None:
        """Catch retries that mistake an expected existing artifact for renderer failure."""

        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
        render_step = next(
            line
            for line in reference.splitlines()
            if line.startswith("6. **Render to a collision-safe destination.**")
        )
        normalized = render_step.casefold()
        self.assertIn("first nonexistent generic", normalized)
        self.assertIn("before invoking the renderer", normalized)
        self.assertIn("normal expected state", normalized)
        self.assertIn("never reuse or overwrite it", normalized)
        self.assertIn("must not trigger fallback", normalized)

    def test_partial_visual_evidence_stays_on_local_html_branch(self) -> None:
        """Catch partial visual cases that incorrectly fall back to technical Markdown."""

        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8").casefold()
        self.assertIn("at least one supplied or inspectable section", reference)
        self.assertIn("partial or unavailable visual evidence remains a valid html artifact case", reference)
        self.assertIn("represent unavailable visual sections in the validated dossier", reference)
        self.assertIn("do not choose markdown fallback", reference)
        self.assertIn("use the dossier locale", reference)

    def test_unsupported_requested_technology_isolated_inside_html(self) -> None:
        """Catch a truthful held claim that incorrectly abandons the artifact branch."""

        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8").casefold()
        self.assertIn("other supplied evidence supports an honest partial diagnostic", reference)
        self.assertIn("unknown, confirmation-or-omit, and do-not-change", reference)
        self.assertIn("must not abandon html", reference)
        self.assertIn("must not appear as expertise in copy", reference)
        self.assertIn("only the rank-1 confirmation question", reference)

    def test_html_dossier_routes_success_fallback_debug_and_isolation(self) -> None:
        self.assertTrue(
            HTML_DOSSIER_REFERENCE.is_file(),
            f"Missing HTML dossier workflow: {HTML_DOSSIER_REFERENCE}",
        )
        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
        branches = reference.split("## Branch table", 1)[1].split("\n## ", 1)[0]

        expected_routes = {
            "normal + local execution": "private HTML artifact",
            "no local execution": "localized Markdown fallback",
            "second validation or render failure": "localized Markdown fallback",
            "debug | eval | detail_requested": "existing Markdown + canonical appendix",
            "coach mode": "one isolated temporary input and one artifact per candidate",
            "no inspectable or supplied evidence": "exactly one useful intake question",
            "analytics not consented": "not_requested",
            "analytics unavailable": "unavailable",
            "market not researched": "not_researched",
            "partial evidence": "unavailable sections are excluded, not scored as zero",
            "normal request asks for raw or debug rows": "stay in the private HTML artifact branch",
        }
        for trigger, outcome in expected_routes.items():
            with self.subTest(trigger=trigger):
                row = next(
                    (line for line in branches.splitlines() if trigger in line),
                    "",
                )
                self.assertIn(outcome, row)

        fallback_rows = [
            line
            for line in branches.splitlines()
            if "no local execution" in line or "second validation or render failure" in line
        ]
        self.assertEqual(2, len(fallback_rows))
        self.assertTrue(all("artifact link" not in line.casefold() for line in fallback_rows))
        self.assertIn("never one combined dossier", branches)
        self.assertIn("exactly one useful intake question", branches)
        self.assertIn("generic identity-free artifact name", branches)

    def test_artifact_chat_uses_one_human_link_and_no_contract_receipt(self) -> None:
        reference = HTML_DOSSIER_REFERENCE.read_text(encoding="utf-8")
        delivery_step = next(
            line
            for line in reference.splitlines()
            if line.startswith("9. **Deliver the client answer.**")
        )
        self.assertIn("human label `Abrir el dossier`", delivery_step)
        self.assertIn("angle-bracket absolute target", delivery_step)
        self.assertRegex(delivery_step, r"<\/absolute\/path\/[^>]+>")
        for forbidden in (
            "Routing receipt",
            "action_state=not_executed",
            "schema_version",
            "E-001",
            "C-001",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, delivery_step)

        root_skill = ROOT_SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "Do not append router, canonical, or later-module rows after the artifact link",
            root_skill,
        )
        self.assertIn(
            "Return them for every non-artifact response; never return them in a normal HTML dossier chat",
            root_skill,
        )

    def test_debug_eval_and_detail_keep_the_validated_markdown_contract(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        client_report = CLIENT_REPORT_REFERENCE.read_text(encoding="utf-8")
        debug_branch = skill.split("## Client-first delivery", 1)[1].split("\n## ", 1)[0]

        self.assertIn(
            "debug | eval | detail_requested -> existing Markdown + canonical appendix",
            debug_branch,
        )
        self.assertIn(
            "`debug | eval | detail_requested` -> full legacy appendix",
            client_report,
        )
        self.assertIn(
            "python3 plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py REPORT.md BUNDLE.json",
            client_report,
        )

    def test_client_report_reference_defines_one_delivery_contract_and_valid_examples(self) -> None:
        self.assertTrue(
            CLIENT_REPORT_REFERENCE.is_file(),
            f"Missing client report reference: {CLIENT_REPORT_REFERENCE}",
        )
        reference = CLIENT_REPORT_REFERENCE.read_text(encoding="utf-8")
        skill = SKILL_PATH.read_text(encoding="utf-8")

        self.assertEqual(1, reference.count("`normal` -> compact evidence index"))
        self.assertEqual(
            1,
            reference.count(
                "`debug | eval | detail_requested` -> full legacy appendix"
            ),
        )
        localized_heading_rows = (
            "| `verdict` | Veredicto | Verdict |",
            "| `score` | Calificación | Score |",
            "| `priorities` | Las tres decisiones prioritarias | Three priority decisions |",
            "| `copy` | Copy listo para revisar | Copy ready for review |",
            "| `do_not_change` | No cambies todavía | Do not change yet |",
            "| `plan` | Plan privado de siete días | Private seven-day plan |",
            "| `evidence_needed` | Evidencia pendiente | Evidence needed |",
            "| `boundaries` | Límites del diagnóstico | Diagnostic boundaries |",
        )
        for row in localized_heading_rows:
            with self.subTest(row=row):
                self.assertEqual(1, reference.count(row))

        self.assertIn("## Client-first delivery", skill)
        self.assertIn("Read [client-report.md](references/client-report.md) for every audit", skill)
        self.assertIn("Read [html-dossier.md](references/html-dossier.md) for every normal audit", skill)
        self.assertIn(
            "normal + local execution -> executive dossier artifact branch",
            skill,
        )
        self.assertIn(
            "normal + no local execution -> localized Markdown fallback",
            skill,
        )
        self.assertIn(
            "debug | eval | detail_requested -> existing Markdown + canonical appendix",
            skill,
        )
        self.assertIn(
            "A `linkedin_rendered_client_report_sample` row never substitutes for either the HTML dossier or the rendered Markdown fallback",
            skill,
        )

        validator = load_linkedin_report_validator()
        normal_cases = (
            ("scenario-a-es.md", "scenario-a.json"),
            ("scenario-b-en.md", "scenario-b.json"),
            ("scenario-c-es.md", "scenario-c.json"),
            ("scenario-d-en.md", "scenario-d.json"),
            ("scenario-d-banner-only-en.md", "scenario-d-banner-only.json"),
        )
        for report_name, bundle_name in normal_cases:
            with self.subTest(report=report_name):
                report = (LINKEDIN_REPORT_FIXTURE_ROOT / report_name).read_text(
                    encoding="utf-8"
                )
                bundle = json.loads(
                    (LINKEDIN_REPORT_FIXTURE_ROOT / bundle_name).read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(
                    [],
                    validator.validate_client_report(report, bundle),
                )

        debug_report = (LINKEDIN_REPORT_FIXTURE_ROOT / "scenario-a-es-debug.md").read_text(
            encoding="utf-8"
        )
        debug_bundle = json.loads(
            (LINKEDIN_REPORT_FIXTURE_ROOT / "scenario-a.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            [],
            validator.validate_client_report(
                debug_report,
                debug_bundle,
                appendix_mode="debug",
            ),
        )

    def test_root_contract_prioritizes_html_and_preserves_client_report_v2_fallback(self) -> None:
        root_skill = ROOT_SKILL_PATH.read_text(encoding="utf-8")

        self.assertEqual(1, root_skill.count("client_report_v2"))
        for required in (
            "`selected_module=optimize-professional-profile`",
            "`case_state=ready`",
            "normal + local execution",
            "private HTML dossier",
            "normal + no local execution",
            "localized H1 at byte zero",
            "`Routing receipt` after the evidence appendix",
            "Never place a pre-H1 router block",
        ):
            with self.subTest(required=required):
                self.assertIn(required, root_skill)

        corpus = json.loads(PRESSURE_CORPUS_PATH.read_text(encoding="utf-8"))
        expected_assertions = {
            "scenario-a": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "no_external_action",
            ),
            "scenario-b": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "no_external_action",
            ),
            "scenario-c": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "no_external_action",
            ),
            "scenario-d-banner-only": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "no_external_action",
            ),
            "scenario-e-adversarial": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "normal_mode_overrides_raw_rows_request",
                "no_external_action",
            ),
            "root-ready-linkedin": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "routing_receipt_after_evidence_appendix",
                "no_pre_h1_router_data",
            ),
            "root-multi-module-linkedin": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "routing_receipt_after_evidence_appendix",
                "no_pre_h1_router_data",
                "later_module_handoff_preserves_declared_order",
            ),
            "root-live-readonly-linkedin": (
                "localized_h1_at_byte_zero",
                "passes_client_report_validator",
                "routing_receipt_after_evidence_appendix",
                "live_source_summary_after_evidence_appendix",
                "live_summary_read_only_redacted_no_raw_retention",
                "no_normal_approval_gates_row",
                "no_pre_h1_router_data",
            ),
        }
        self.assertEqual(
            tuple(expected_assertions),
            tuple(case["case_id"] for case in corpus["cases"]),
        )
        self.assertEqual(
            expected_assertions,
            {
                case["case_id"]: tuple(case["assertions"])
                for case in corpus["cases"]
            },
        )

    def test_normal_live_inspection_uses_compact_post_appendix_summary(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        client_report = CLIENT_REPORT_REFERENCE.read_text(encoding="utf-8")
        normal_rule = (
            "A normal Markdown fallback after live inspection uses a compact `Live source summary` after the "
            "evidence appendix; it never requires a canonical `approval_gates` row "
            "before recommendations."
        )
        expanded_rule = (
            "Expanded modes retain `linkedin_live_evidence_snapshot` as the first "
            "`approval_gates` row."
        )

        self.assertIn(normal_rule, skill)
        self.assertIn(normal_rule, client_report)
        self.assertIn(expanded_rule, skill)
        self.assertIn(expanded_rule, client_report)

    def test_markdown_fallback_composition_has_no_index_only_contradiction(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        client_report = CLIENT_REPORT_REFERENCE.read_text(encoding="utf-8")

        self.assertNotIn(
            "In normal mode, follow it with the compact evidence index",
            skill.split("## Client-first delivery", 1)[1].split("\n## ", 1)[0],
        )
        self.assertIn(
            "A normal Markdown fallback is, in order: the localized H1, all eight localized "
            "H2 sections, the localized appendix H2, the compact evidence index, a "
            "compact `Routing receipt`, and, when live inspection was used, a compact "
            "`Live source summary`.",
            client_report,
        )
        contradictions = [
            f"{path.relative_to(REPO_ROOT)}:{line_number}: {line.strip()}"
            for path in (SKILL_PATH, CLIENT_REPORT_REFERENCE)
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            )
            if re.search(
                r"normal mode[^.\n]*only the compact evidence index",
                line,
                flags=re.IGNORECASE,
            )
        ]
        self.assertEqual([], contradictions)

    def test_external_action_gate_requires_final_content_or_asset_identity(self) -> None:
        shared_reference = SHARED_EVIDENCE_SAFETY_REFERENCE.read_text(encoding="utf-8")
        exact_rule = (
            "Immediately before execution, require explicit authorization naming the "
            "exact action, exact target, and exact final content or asset identity when "
            "content or assets apply."
        )
        self.assertIn(exact_rule, shared_reference)

        entrypoints = (
            (ROOT_SKILL_PATH, "## Gate external actions"),
            (SKILL_PATH, "## Action gate"),
        )
        for path, heading in entrypoints:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                section = text.split(heading, 1)[1].split("\n## ", 1)[0]
                self.assertIn("evidence-and-safety.md", section)
                self.assertIn("immediately before execution", section.lower())
                self.assertIn(
                    "exact action, exact target, and exact final content or asset identity",
                    section,
                )
                self.assertNotIn("exact action-and-target authorization", section)

    def test_action_bearing_contracts_reject_weaker_execution_authorization(self) -> None:
        contract_paths = (
            ROOT_SKILL_PATH,
            SHARED_EVIDENCE_SAFETY_REFERENCE,
            SKILL_PATH,
            CLIENT_REPORT_REFERENCE,
            SKILL_ROOT / "references" / "networking-and-content.md",
        )
        exact_contract = (
            "exact action, exact target, and exact final content or asset identity"
        )
        weak_lines: list[str] = []

        for path in contract_paths:
            has_exact_contract = False
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                normalized = line.lower()
                if exact_contract in normalized:
                    has_exact_contract = True
                if re.search(
                    r"\b(?:exact action-and-target|action-and-target authorization)\b",
                    normalized,
                ):
                    weak_lines.append(
                        f"{path.relative_to(REPO_ROOT)}:{line_number}: {line.strip()}"
                    )
                    continue
                if (
                    "immediately before execution" in normalized
                    and "exact action" in normalized
                    and "target" in normalized
                    and exact_contract not in normalized
                ):
                    weak_lines.append(
                        f"{path.relative_to(REPO_ROOT)}:{line_number}: {line.strip()}"
                    )

            self.assertTrue(
                has_exact_contract,
                f"Missing complete action authorization contract in {path}",
            )

        self.assertEqual([], weak_lines)

    def test_counterfactual_v2_report_uses_generic_candidate_specific_decisions(self) -> None:
        validator = load_linkedin_report_validator()
        report, bundle = linkedin_counterfactual_v2()
        expected_domains = (
            ("visual", 15, "not_scored", None, 0.0),
            ("headline", 15, "scored", 65, 9.75),
            ("about", 15, "scored", 65, 9.75),
            ("experience", 20, "scored", 65, 13.0),
            ("skills", 15, "scored", 65, 9.75),
            ("proof", 10, "not_scored", None, 0.0),
            ("completeness", 10, "scored", 65, 6.5),
        )
        expected_fingerprints = (
            (
                "headline",
                "TARGET_ROLE_AMBIGUOUS",
                "REWRITE_TARGET_ROLE",
                ("EVID-JSC9-01",),
                "HEADLINE_TARGET_ROLE_VISIBLE",
            ),
            (
                "about",
                "PROOF_SEQUENCE_WEAK",
                "REORDER_PROOF",
                ("EVID-JSC9-02",),
                "ABOUT_OPENS_WITH_VERIFIED_PROOF",
            ),
            (
                "experience",
                "SCOPE_BOUNDARY_MISSING",
                "ADD_SCOPE_BOUNDARY",
                ("EVID-JSC9-03",),
                "EXPERIENCE_STATES_SCOPE_BOUNDARY",
            ),
        )

        self.assertEqual("CANDIDATE-JSC9-SYNTH", bundle["internal_candidate_id"])
        ledger = bundle["score_ledger"]
        self.assertEqual(48.75, ledger["numeric_weighted_total"])
        self.assertEqual(75, ledger["scored_weight"])
        self.assertEqual(25, ledger["not_scored_weight"])
        self.assertEqual(65, ledger["overall_score"])
        self.assertEqual(
            expected_domains,
            tuple(
                (
                    row["domain"],
                    row["weight"],
                    row["state"],
                    row["raw_score"],
                    row["weighted_points"],
                )
                for row in ledger["domains"]
            ),
        )
        self.assertEqual(
            expected_fingerprints,
            tuple(
                (
                    priority["section"],
                    priority["diagnosed_gap"],
                    priority["action_type"],
                    tuple(priority["evidence_ids"]),
                    priority["done_when"],
                )
                for priority in bundle["priorities"]
            ),
        )
        self.assertEqual(
            ("35m", "45m", "50m"),
            tuple(priority["timebox"] for priority in bundle["priorities"]),
        )
        self.assertEqual(
            ("ready", "requires_confirmation", "omit"),
            tuple(copy_block["state"] for copy_block in bundle["copy_blocks"]),
        )
        self.assertEqual([], validator.validate_client_report(report, bundle))

    def test_counterfactual_v2_rejects_cross_candidate_evidence(self) -> None:
        validator = load_linkedin_report_validator()
        report, bundle = linkedin_counterfactual_v2()
        report = report.replace("EVID-JSC9-02", "EVID-JSC3-ABOUT")

        errors = validator.validate_client_report(report, bundle)

        self.assertTrue(
            any(
                "references identifier outside fixture" in error
                for error in errors
            ),
            errors,
        )

    def test_counterfactual_v2_rejects_generic_and_malformed_priority_values(self) -> None:
        validator = load_linkedin_report_validator()
        _report, base_bundle = linkedin_counterfactual_v2()
        cases = (
            ("diagnosed_gap", "improve_profile"),
            ("action_type", "SEND NOW"),
            ("action_type", "SEND_PASSWORD_NOW"),
            ("timebox", "immediately"),
            ("done_when", "done"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                bundle = copy.deepcopy(base_bundle)
                bundle["priorities"][0][field] = value
                errors = validator.validate_fixture_bundle(bundle)
                self.assertTrue(
                    any(field in error or "generic priority code" in error for error in errors),
                    errors,
                )

    def test_counterfactual_v2_rejects_external_action_priority_stems(self) -> None:
        validator = load_linkedin_report_validator()
        base_report, base_bundle = linkedin_counterfactual_v2()
        action_types = (
            "EMAIL_RECRUITER_NOW",
            "CONTACT_RECRUITER_NOW",
            "SCHEDULE_INTERVIEW_NOW",
            "OUTREACH_TO_RECRUITER",
            "EMAILING_RECRUITER_NOW",
            "CONTACTED_RECRUITER_NOW",
            "SCHEDULING_INTERVIEW_NOW",
            "OUTREACHING_TO_RECRUITER",
            "SEND_PASSWORD_NOW",
        )
        for action_type in action_types:
            with self.subTest(action_type=action_type):
                report = base_report.replace("REWRITE_TARGET_ROLE", action_type, 1)
                bundle = copy.deepcopy(base_bundle)
                bundle["priorities"][0]["action_type"] = action_type

                errors = validator.validate_client_report(report, bundle)

                self.assertIn("priorities[0] has invalid action_type", errors)

    def test_linkedin_source_policy_keeps_secondary_optional_and_heuristics_explicit(self) -> None:
        profile_audit = (SKILL_ROOT / "references" / "profile-audit.md").read_text(
            encoding="utf-8"
        )
        client_report = CLIENT_REPORT_REFERENCE.read_text(encoding="utf-8")

        self.assertIn(
            "one current official source may stand alone when it directly supports the criterion",
            profile_audit,
        )
        self.assertIn("Dated secondary guidance is optional", profile_audit)
        self.assertIn(
            "Coach-selected weights, priority order, review windows, and timeboxes are always `COACH_HEURISTIC`",
            profile_audit,
        )
        for contract in (profile_audit, client_report):
            self.assertIn(
                "Official category coverage counts only a category-specific registered locator",
                contract,
            )
            self.assertIn(
                "Secondary sources never satisfy official category coverage",
                contract,
            )
            self.assertIn(
                "Publisher provenance is limited to one line and 120 characters; "
                "document titles are limited to one line and 240 characters",
                contract,
            )
            self.assertIn(
                "Neither provenance field may contain secrets or private data",
                contract,
            )
        sentences = re.split(r"(?<=[.!?])\s+", profile_audit)
        mandatory_secondary_patterns = (
            re.compile(
                r"(?i)\b(?:must|requires?)\b[^.\n]*"
                r"(?:\bsecondary\b|\bdated\s+(?:20\d{2}|secondary|guidance|source))"
            ),
            re.compile(
                r"(?i)\bcite\b[^.\n]*\bofficial\b[^.\n]*\bplus\b[^.\n]*\bdated\b"
            ),
            re.compile(
                r"(?i)\b(?:use|include)\b[^.\n]*(?:\bofficial\b|\blinkedin\b)"
                r"[^.\n]*\bplus\b[^.\n]*(?:\bsecondary\b|\bdated\b)"
            ),
            re.compile(
                r"(?i)\b(?:include|cover exactly)\b[^.\n]*"
                r"\bsecondary_market_guidance\b"
            ),
            re.compile(
                r"(?i)\brequired\b[^.\n]*"
                r"\b[a-z_]+=[a-z0-9_]*secondary_market_guidance[a-z0-9_]*\b"
            ),
        )
        contradictions = []
        for sentence in sentences:
            normalized = " ".join(sentence.split())
            lowered = normalized.lower()
            if not normalized or "optional" in lowered or "when inspected" in lowered:
                continue
            if "dated vacancy evidence" in lowered and "current demand" in lowered:
                continue
            if "source_fit" in lowered and "official_support_with_coach_boundary" in lowered:
                continue
            if any(pattern.search(normalized) for pattern in mandatory_secondary_patterns):
                contradictions.append(normalized)
        self.assertEqual([], contradictions)

        self.assertIn(
            "Coach-selected weights, priority order, windows, and timeboxes are `COACH_HEURISTIC`",
            client_report,
        )
        self.assertNotIn("unless a direct official source", client_report)

    def test_linkedin_skill_has_the_required_safe_contract(self) -> None:
        self.assertTrue(SKILL_PATH.is_file(), f"Missing skill: {SKILL_PATH}")
        text = SKILL_PATH.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "optimize-professional-profile")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("workflow", metadata["description"].lower())

        self.assertTrue(AGENT_PATH.is_file(), f"Missing UI metadata: {AGENT_PATH}")
        agent = AGENT_PATH.read_text(encoding="utf-8")
        self.assertIn('display_name: "LinkedIn Career Optimizer"', agent)
        self.assertIn('short_description: "Audit and safely improve a LinkedIn profile"', agent)
        self.assertIn('default_prompt: "Use $optimize-professional-profile', agent)

        for name in REFERENCE_NAMES:
            reference = SKILL_ROOT / "references" / name
            self.assertTrue(reference.is_file(), f"Missing reference: {reference}")
            self.assertIn(f"references/{name}", text)

        for conditional_load in (
            "Read [profile-audit.md]",
            "search-positioning.md](references/search-positioning.md) when",
            "read [networking-and-content.md](references/networking-and-content.md)",
            "Use [networking-and-content.md]",
            "[experiments.md]",
        ):
            self.assertIn(conditional_load, text)

        self.assertIn("verified: (visible)", text)
        self.assertIn("unknown: (unavailable)", text)
        self.assertIn("unknown: (conflicting)", text)
        self.assertIn("candidate-reported", text)
        self.assertIn("inferred", text)
        self.assertIn("conflicting", text)
        self.assertNotIn("verified/visible", text)
        self.assertNotIn("unknown/unavailable", text)
        self.assertIn("dated current vacancies", text)

        self.assertIn("research-professional-market", text)
        self.assertIn("work authorization", text)
        self.assertIn("confidentiality review", text)

        for section in (
            "executive_diagnosis",
            "coach_brief",
            "visibility_gaps",
            "positioning",
            "rewrites",
            "networking_drafts",
            "content_plan",
            "experiment_plan",
            "approval_gates",
        ):
            self.assertIn(section, text)

        networking_reference = (
            SKILL_ROOT / "references" / "networking-and-content.md"
        ).read_text(encoding="utf-8")
        entrypoint_and_networking_reference = "\n".join(
            (text, networking_reference)
        )
        for required in (
            "audit_priority_matrix",
            "keyword_evidence_matrix",
            "outreach_funnel",
            "proof_asset_matrix",
            "linkedin_funnel_events",
            "linkedin_live_evidence_snapshot",
            "source_url_state",
            "redaction_boundary",
            "evidence_promotion_rule",
            "browser_action_scope",
            "not_saved_raw_profile",
            "connection_note",
            "recruiter_interest",
            "recruiter_conversation_bridge",
            "recruiter_network_expansion_plan",
            "recruiter_discovery_engine",
            "discovery_query",
            "discovery_signal",
            "recruiter_target_shortlist",
            "recruiter_target_row",
            "shortlist_goal",
            "ranking_method",
            "batch_decision",
            "top_priority_targets",
            "recommended_draft_type",
            "do_not_contact_reason",
            "recruiter_reply_triage",
            "network_goal",
            "target_segments",
            "search_surface",
            "query_intent",
            "must_have_context",
            "negative_filter",
            "warm_intro_path",
            "first_question",
            "acceptance_signal",
            "discard_reason",
            "context_quality_gate",
            "priority_score",
            "segment_scoring_model",
            "outreach_batch_limit",
            "candidate_time_budget",
            "quality_review_check",
            "do_not_contact_rules",
            "outreach_funnel_link",
            "recruiter_bridge_handoff",
            "conversation_goal",
            "thirty_second_pitch",
            "proof_points",
            "qualification_questions",
            "objection_bridges",
            "advance_the_process_ask",
            "screen_success_criteria",
            "tracking_event",
            "recruiter_first_interview_playbook",
            "first_screen_prep_packet",
            "prep_scope",
            "opening_script",
            "salary_script",
            "eligibility_script",
            "practice_drill",
            "candidate_review_required",
            "referral_request",
            "follow_up_stop_condition",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "priority_rank",
            "sequence_step",
            "cadence_window",
            "personalization_trigger",
            "success_signal",
            "next_safe_action",
            "measurement_event",
        ):
            self.assertIn(required, entrypoint_and_networking_reference)

        self.assertIn("immediately before execution", text.lower())
        self.assertIn("exact final content or asset identity", text)
        self.assertIn("action_state=not_executed", text)
        for action in (
            "edit",
            "connection",
            "message",
            "post",
            "publication",
            "upload",
            "application",
            "sharing",
        ):
            self.assertIn(action, text)

        combined_linkedin_contract = "\n".join(
            (
                text,
                (SKILL_ROOT / "references" / "profile-audit.md").read_text(encoding="utf-8"),
                (SKILL_ROOT / "references" / "search-positioning.md").read_text(encoding="utf-8"),
                networking_reference,
            )
        )
        for coach_grade_requirement in (
            "professional coaching layer",
            "coach_verdict",
            "positioning_decision",
            "coach_opening",
            "plain_english_decision",
            "client_takeaway",
            "next_review_trigger",
            "linkedin_profile_to_screen_coherence_review",
            "profile_to_screen_action_card",
            "first_screen_claim_bridge",
            "linkedin_landing_page_conversion_snapshot",
            "linkedin_landing_page_fix_card",
            "linkedin_client_handoff_summary",
            "linkedin_client_next_step",
            "why_this_now",
            "defer_or_omit",
            "coach_checkpoint",
            "evidence_strength",
            "highest_leverage_edit",
            "thirty_minute_edit_script",
            "copy_ready_headline",
            "if_jenkins_confirmed",
            "if_jenkins_unconfirmed",
            "if_no_jenkins_experience",
            "linkedin_edit_packet",
            "linkedin_score_improvement_roadmap",
            "linkedin_visual_evidence_scorecard",
            "visual_action_item",
            "visual_evidence_source",
            "photo_score",
            "banner_score",
            "first_impression_score",
            "scoring_boundary",
            "professional_profile_usefulness_not_identity_or_attractiveness",
            "linked_low_score_dimensions",
            "intervention_type",
            "exact_candidate_action",
            "copy_or_prompt",
            "acceptance_criteria",
            "effort_level",
            "before_state",
            "after_state",
            "publish_readiness",
            "evidence_id",
            "risk_note",
            "section_action",
            "publish_checklist",
            "top_3_actions",
            "first_interview_goal",
            "conversation_objective",
            "qualification_question",
            "thirty_second_opener",
            "proof_story_bank",
            "questions_to_ask",
            "claim_boundaries",
            "proof_packet",
            "reply_to_screen_handoff",
            "reply_classification",
            "screen_readiness_decision",
            "safe_draft_response",
            "proposed_time_state",
            "no_calendar_action",
            "follow_up_window",
            "measure_next",
            "compensation_boundary",
            "eligibility_boundary",
            "close_script",
            "prepare-role-interviews",
        ):
            self.assertIn(coach_grade_requirement, combined_linkedin_contract)

        for constraint in (
            "never invent LinkedIn algorithm rules",
            "guaranteed outcomes",
            "unsupported experience",
            "unsupported skills",
        ):
            self.assertIn(constraint, text)

        profile_audit = (SKILL_ROOT / "references" / "profile-audit.md").read_text(encoding="utf-8")
        self.assertIn("verified: (visible)", profile_audit)
        self.assertIn("unknown: (unavailable)", profile_audit)
        for section in (
            "photo", "banner", "name", "URL", "headline", "location", "contact",
            "About", "experience", "skills", "Featured", "certifications", "education",
            "recommendations", "activity", "job preferences",
        ):
            self.assertIn(section, profile_audit)

    def test_profile_audit_reference_has_no_duplicate_major_diagnostic_contracts(self) -> None:
        profile_audit = (SKILL_ROOT / "references" / "profile-audit.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            1,
            profile_audit.count("Add one `linkedin_recruiter_attention_path` row"),
            "profile-audit.md should define the recruiter attention path once to avoid repetitive coach output",
        )
        self.assertEqual(
            1,
            profile_audit.count("Add exactly two `linkedin_visual_asset_brief"),
            "profile-audit.md should define the visual asset brief once to avoid duplicate photo/banner rows",
        )

    def test_linkedin_forward_records_have_complete_structured_evidence_matrices(self) -> None:
        checker = load_static_checker()
        fixture = recruiter_outreach_fixture()
        self.assertEqual([], checker.validate_recruiter_outreach_lab_quality(fixture))
        mutant = fixture.replace("candidate_proof_fit=CI_CD_AUTOMATION_REPORTED; ", "", 1)
        errors = checker.validate_recruiter_outreach_lab_quality(mutant)
        self.assertTrue(
            any("recruiter_target_context_packet 1" in error and "candidate_proof_fit" in error for error in errors),
            errors,
        )

    def test_linkedin_forward_funnels_are_isolated_draft_only_and_noncausal(self) -> None:
        checker = load_static_checker()
        fixture = recruiter_outreach_fixture()
        self.assertEqual([], checker.validate_recruiter_outreach_lab_quality(fixture))
        mutant = fixture.replace("send_status=draft_only; draft_only=true", "send_status=draft_only; draft_only=false", 1)
        errors = checker.validate_recruiter_outreach_lab_quality(mutant)
        self.assertTrue(any("outreach_variant 1 must stay draft-only" in error for error in errors), errors)

    def test_legacy_debug_smoke_preserves_evidence_and_safety_contracts(self) -> None:
        checker = load_static_checker()
        fixture = coach_smoke(
            "- inferred: candidate_id=JSC-CASE-SEMANTIC; linkedin_premium_coach_summary=synthetic_summary; draft_only=true."
        )
        agenda_errors = checker.validate_linkedin_coach_session_agenda_quality(fixture)
        delivery_errors = checker.validate_linkedin_diagnostic_delivery_map_quality(fixture)
        scan_errors = checker.validate_linkedin_recruiter_first_screen_scan_quality(fixture)
        self.assertTrue(any("linkedin_coach_session_agenda" in error for error in agenda_errors), agenda_errors)
        self.assertTrue(any("linkedin_diagnostic_delivery_map" in error for error in delivery_errors), delivery_errors)
        self.assertTrue(any("linkedin_recruiter_first_screen_scan" in error for error in scan_errors), scan_errors)

    def test_linkedin_authorized_visual_evidence_smoke_scores_photo_and_banner_safely(self) -> None:
        checker = load_static_checker()
        fixture = authorized_visual_smoke(photo_score=70, banner_score=40, first_impression_score=58)
        baseline_errors = checker.validate_linkedin_authorized_visual_evidence_quality(fixture)
        self.assertFalse(any("weighted photo/banner score" in error for error in baseline_errors), baseline_errors)
        mutant = authorized_visual_smoke(photo_score=70, banner_score=40, first_impression_score=59)
        errors = checker.validate_linkedin_authorized_visual_evidence_quality(mutant)
        self.assertTrue(any("weighted photo/banner score" in error for error in errors), errors)

    def assert_coach_brief_is_prioritized(self, brief: str, candidate_id: str) -> None:
        self.assertIn(f"candidate_id={candidate_id}", brief)
        for required in (
            "positioning_decision=",
            "coach_opening=",
            "plain_english_decision=",
            "client_takeaway=",
            "next_review_trigger=",
            "why_this_now=",
            "do_now=1:",
            "do_now=2:",
            "do_now=3:",
            "confirm_next=",
            "defer_or_omit=",
            "coach_checkpoint=",
            "draft_only=true",
        ):
            self.assertIn(required, brief)
        self.assertEqual(3, len(re.findall(r"\bdo_now=\d:", brief)))
        opening_rows = [
            row
            for row in brief.splitlines()
            if "coach_opening=" in row
        ]
        self.assertEqual(1, len(opening_rows))
        opening = opening_rows[0]
        self.assert_linkedin_premium_coach_summary_is_client_ready(brief, candidate_id)
        if candidate_id == "JSC-CASE-12":
            self.assertIn("You should not lead with Jenkins yet", opening)
            self.assertIn("Kubernetes platform reliability plus CI/CD automation", opening)
            self.assertIn("proof question", opening)
            self.assertIn("client_takeaway=make the profile sharper without making it look inflated", opening)
            self.assertIn("next_review_trigger=return_confirmed_Jenkins_scope_and_pasted_headline_About", opening)
        self.assertGreaterEqual(len(opening.split()), 24)
        self.assertNotRegex(
            opening.lower(),
            r"\b(?:guarantee[sd]?|will get hired|will get an interview|linkedin algorithm|recruiter ranking|strong fit|perfect fit)\b",
        )
        self.assertNotRegex(
            re.sub(r"causality_boundary=descriptive_only_no_guaranteed_outcome", "", brief, flags=re.I).lower(),
            r"\bguarantee(?:s|d)?\b",
        )
        self.assertNotIn("will get hired", brief.lower())

    def assert_linkedin_premium_coach_summary_is_client_ready(self, brief: str, candidate_id: str) -> None:
        summary_rows = [
            row
            for row in brief.splitlines()
            if "linkedin_premium_coach_summary=" in row
        ]
        self.assertEqual(
            1,
            len(summary_rows),
            "Expected exactly one premium coach summary in coach_brief.",
        )
        summary = summary_rows[0]
        non_empty_brief_rows = [
            row
            for row in brief.splitlines()
            if row.strip() and row.strip() != "coach_brief:"
        ]
        self.assertGreaterEqual(len(non_empty_brief_rows), 2)
        self.assertIn("coach_opening=", non_empty_brief_rows[0])
        self.assertIn(
            "linkedin_premium_coach_summary=",
            non_empty_brief_rows[1],
            "Premium summary should immediately follow coach_opening as the client-facing cover note.",
        )
        for required in (
            f"candidate_id={candidate_id}",
            "linkedin_premium_coach_summary=client_ready_executive_summary",
            "overall_verdict=",
            "score_snapshot=",
            "positioning_decision=",
            "primary_opportunity=",
            "biggest_risk=",
            "next_30_minutes=",
            "next_7_days=",
            "do_not_change_yet=",
            "success_criteria=",
            "evidence_confidence=",
            "outcome_boundary=not_a_job_interview_recruiter_response_or_search_ranking_prediction",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, summary)
        if candidate_id == "JSC-CASE-12":
            self.assertIn("score_snapshot=72_provisional_B_minus", summary)
            self.assertIn("positioning_decision=lead_with_Kubernetes_platform_reliability_and_CI_CD_automation", summary)
            self.assertIn("do_not_change_yet=do_not_add_Jenkins_or_production_SRE_claims", summary)
        for field in (
            "overall_verdict",
            "primary_opportunity",
            "biggest_risk",
            "next_30_minutes",
            "next_7_days",
            "success_criteria",
        ):
            match = re.search(rf"{field}=([^;]+)", summary)
            self.assertIsNotNone(match, f"premium coach summary missing {field}")
            assert match is not None
            self.assertGreaterEqual(
                len(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", match.group(1).replace("_", " "))),
                7,
                f"{field} should read like a human coach sentence, not a terse label.",
            )
        self.assertNotRegex(
            summary.lower(),
            r"\b(?:guarantee|will get|rank higher|algorithm|recruiter response|interview probability|publish now|message recruiters|profile edited)\b",
        )

    def assert_linkedin_score_integrity_ledger_is_consistent(
        self,
        ledger: str,
        scorecard: str,
        domain_score_rows: list[str],
    ) -> None:
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_score_integrity_ledger=weighted_score_reconciliation",
            "scorecard_ref=professional_section_by_section_linkedin_page_audit",
            "domain_score_ref=weighted_professional_profile_rubric",
            "scored_domain_count=6",
            "not_scored_domain_count=1",
            "total_weight=100",
            "scored_weight=85",
            "not_scored_weight=15",
            "numeric_weighted_total=61.0",
            "normalization_denominator=85",
            "coverage_adjusted_profile_score=72",
            "normalization_formula=round_numeric_weighted_total_divided_by_scored_weight_times_100",
            "rounded_profile_score=72",
            "scorecard_overall_profile_score=72",
            "rounding_rule=nearest_integer_after_scored_weight_normalization",
            "unavailable_score_policy=excluded_not_zero",
            "not_scored_domains=visual_identity",
            "score_boundary=profile_quality_score_not_outcome_or_market_prediction",
            "recompute_instruction=normalize_numeric_weighted_points_by_scored_weight_and_do_not_convert_not_scored_to_zero",
            "draft_only=true",
        ):
            self.assertIn(required, ledger)
        score_match = re.search(r"overall_profile_score=(\d+)", scorecard)
        self.assertIsNotNone(score_match)
        assert score_match is not None
        self.assertIn(f"scorecard_overall_profile_score={score_match.group(1)}", ledger)

        numeric_weighted_total = 0.0
        not_scored_domains: list[str] = []
        total_weight = 0
        scored_weight = 0
        not_scored_weight = 0
        for row in domain_score_rows:
            domain = re.search(r"domain=([^;]+)", row)
            weight = re.search(r"weight=(\d+)", row)
            weighted = re.search(r"weighted_points=([^;]+)", row)
            self.assertIsNotNone(domain)
            self.assertIsNotNone(weight)
            self.assertIsNotNone(weighted)
            assert domain is not None and weight is not None and weighted is not None
            weight_value = int(weight.group(1))
            total_weight += weight_value
            if weighted.group(1) == "not_scored":
                not_scored_domains.append(domain.group(1))
                not_scored_weight += weight_value
            else:
                numeric_weighted_total += float(weighted.group(1))
                scored_weight += weight_value
        self.assertEqual(100, total_weight)
        self.assertEqual(85, scored_weight)
        self.assertEqual(15, not_scored_weight)
        self.assertEqual(["visual_identity"], not_scored_domains)
        self.assertAlmostEqual(61.0, numeric_weighted_total, places=1)
        self.assertNotRegex(
            ledger.lower(),
            r"\b(?:ranking|rank higher|recruiter response|interview probability|compensation|market demand|guarantee|will get)\b",
        )

    def assert_linkedin_target_role_positioning_board_is_safe(self, positioning: str) -> None:
        board_rows = [
            row for row in positioning.splitlines()
            if "linkedin_target_role_positioning_board=" in row
        ]
        lane_rows = [
            row for row in positioning.splitlines()
            if "linkedin_target_role_lane=" in row
        ]
        self.assertEqual(1, len(board_rows), board_rows)
        self.assertEqual(4, len(lane_rows), lane_rows)
        board = board_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_target_role_positioning_board=role_lane_decision_map",
            "primary_lane=platform_reliability_engineer",
            "secondary_lane=devops_sre",
            "hold_lane=jenkins_specialist",
            "market_research_status=required_before_pay_or_demand_claim",
            "decision_boundary=profile_positioning_not_salary_or_market_demand_proof",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, board)
        combined = "\n".join(lane_rows)
        for lane in (
            "platform_reliability_engineer",
            "devops_sre",
            "cloud_kubernetes_infrastructure",
            "jenkins_specialist",
        ):
            self.assertIn(f"target_role_lane={lane}", combined)
        for decision in ("use", "confirm", "omit"):
            self.assertIn(f"decision={decision}", combined)
        for required in (
            "linkedin_target_role_lane=profile_target_lane",
            "supported_profile_angle=",
            "evidence_to_show=",
            "evidence_to_confirm=",
            "headline_keyword_policy=",
            "about_keyword_policy=",
            "proof_asset_needed=",
            "screen_story=",
            "risk_boundary=",
            "market_research_gate=research-professional-market_before_pay_or_demand_claim",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, combined)
        self.assertNotRegex(
            (board + "\n" + combined).lower(),
            r"\b(?:guarantee[sd]?|will get|rank higher|highest paying|salary proven|market demand proven|"
            r"interview probability|recruiter response probability|publish now|message recruiters)\b",
        )

    def assert_profile_to_screen_coherence_bridge_is_safe(self, brief: str) -> None:
        review_rows = [
            row for row in brief.splitlines()
            if "linkedin_profile_to_screen_coherence_review=" in row
        ]
        action_rows = [
            row for row in brief.splitlines()
            if "profile_to_screen_action_card=" in row
        ]
        bridge_rows = [
            row for row in brief.splitlines()
            if "first_screen_claim_bridge=" in row
        ]
        drill_rows = [
            row for row in brief.splitlines()
            if "linkedin_claim_question_drill=" in row
        ]
        self.assertEqual(1, len(review_rows), review_rows)
        self.assertEqual(3, len(action_rows), action_rows)
        self.assertEqual(3, len(bridge_rows), bridge_rows)
        self.assertEqual(4, len(drill_rows), drill_rows)
        review = review_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "decision=clarify_first",
            "first_screen_readiness=not_ready_until_Jenkins_scope_eligibility_availability_and_role_context_are_clarified",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "handoff_allowed=false",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, review)
        for index, row in enumerate(action_rows, start=1):
            self.assertIn(f"card_id=PSC-00{index}", row)
            self.assertIn("source_screen_packet_id=LI-JENKINS-006", row)
            self.assertIn(f"bridge_id=FSB-00{index}", row)
            self.assertIn("draft_only=true", row)
            self.assertIn("consent=not_granted", row)
            self.assertIn("authorization_gate=exact_action_and_target_immediately_before_execution", row)
            self.assertIn("no_message_action=true", row)
            self.assertIn("no_calendar_action=true", row)
            self.assertIn("causality_boundary=descriptive_only_no_guaranteed_outcome", row)
        self.assertTrue(
            any("source_claim_id=JENKINS_UNCONFIRMED" in row and "evidence_state=unconfirmed_omit_or_bridge" in row for row in bridge_rows),
            bridge_rows,
        )
        self.assertTrue(
            any("prohibited_claim=unverified_Jenkins" in row for row in bridge_rows),
            bridge_rows,
        )
        drill_combined = "\n".join(drill_rows)
        for claim_theme in (
            "target_role_positioning",
            "tooling_stack_scope",
            "impact_metrics_scope",
            "public_proof_assets",
        ):
            self.assertIn(f"claim_theme={claim_theme}", drill_combined)
        for required in (
            "linkedin_claim_question_drill=public_claim_to_recruiter_question_practice",
            "source_claim_bridge=",
            "profile_claim=",
            "likely_recruiter_question=",
            "question_intent=",
            "evidence_to_prepare=",
            "safe_answer_script=",
            "proof_boundary=",
            "claim_to_avoid=",
            "followup_if_missing_evidence=",
            "practice_acceptance_test=",
            "owner=candidate_with_coach_review",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, drill_combined)
        combined = "\n".join(review_rows + action_rows + bridge_rows + drill_rows)
        self.assertNotRegex(
            combined,
            r"\b(?:message sent|screen scheduled|will_get_interview|will get an interview|publish_now|publish now|guaranteed_results)\b",
        )

    def assert_linkedin_profile_diagnostic_scorecard_is_coach_grade(self, diagnosis: str) -> None:
        scorecard_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_profile_diagnostic_scorecard=" in row
        ]
        rubric_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_page_impact_rubric=" in row
        ]
        score_interpretation_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_score_interpretation_ledger=" in row
        ]
        score_integrity_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_score_integrity_ledger=" in row
        ]
        dimension_rows = [
            row
            for row in diagnosis.splitlines()
            if "diagnostic_dimension=" in row
        ]
        text_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_text_signal_audit=" in row
        ]
        photo_rubric_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_photo_readiness_rubric=" in row
        ]
        recruiter_scan_summary_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_recruiter_scan_summary=" in row
        ]
        recruiter_scan_signal_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_recruiter_scan_signal=" in row
        ]
        client_narrative_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_client_diagnostic_narrative=" in row
        ]
        client_handoff_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_client_handoff_summary=" in row
        ]
        client_next_step_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_client_next_step=" in row
        ]
        first_screen_packet_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_first_screen_readiness_packet=" in row
        ]
        first_screen_answer_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_first_screen_answer_asset=" in row
        ]
        first_screen_objection_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_first_screen_objection_bridge=" in row
        ]
        visual_asset_brief_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_visual_asset_brief=" in row
        ]
        landing_page_snapshot_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_landing_page_conversion_snapshot=" in row
        ]
        landing_page_fix_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_landing_page_fix_card=" in row
        ]
        contactability_cta_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_contactability_cta_audit=" in row
        ]
        priority_calibration_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_diagnostic_priority_calibration=" in row
        ]
        priority_item_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_diagnostic_priority_item=" in row
        ]
        current_benchmark_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_current_profile_benchmark=" in row
        ]
        diagnostic_axis_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_page_diagnostic_axis=" in row
        ]
        claim_register_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_evidence_and_claim_register=" in row
        ]
        claim_proof_prep_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_claim_proof_prep_packet=" in row
        ]
        public_claim_risk_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_public_claim_risk_register=" in row
        ]
        triage_board_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_diagnostic_triage_board=" in row
        ]
        triage_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_diagnostic_triage_item=" in row
        ]
        visible_diagnostic_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_coach_visible_diagnostic=" in row
        ]
        pillar_score_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_profile_pillar_score=" in row
        ]
        source_index_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_best_practice_source_index=" in row
        ]
        source_freshness_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_source_freshness_audit=" in row
        ]
        source_trace_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_source_trace_matrix=" in row
        ]
        domain_score_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_profile_domain_score=" in row
        ]
        diagnostic_report_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_profile_diagnostic_report_card=" in row
        ]
        section_diagnosis_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_profile_section_diagnosis=" in row
        ]
        section_score_rationale_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_section_score_rationale_matrix=" in row
        ]
        score_lift_forecast_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_score_lift_forecast=" in row
        ]
        score_lift_intervention_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_score_lift_intervention=" in row
        ]
        search_preview_scorecard_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_search_preview_scorecard=" in row
        ]
        recruiter_attention_path_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_recruiter_attention_path=" in row
        ]
        recruiter_scan_moment_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_recruiter_scan_moment=" in row
        ]
        evidence_intake_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_diagnostic_evidence_intake=" in row
        ]
        intake_question_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_diagnostic_intake_question=" in row
        ]
        self.assertEqual(1, len(scorecard_rows))
        self.assertEqual(1, len(rubric_rows))
        self.assertEqual(1, len(score_interpretation_rows))
        self.assertEqual(1, len(score_integrity_rows))
        self.assertGreaterEqual(len(dimension_rows), 8)
        self.assertEqual(4, len(text_rows))
        self.assertEqual(1, len(photo_rubric_rows))
        self.assertEqual(1, len(recruiter_scan_summary_rows))
        self.assertEqual(4, len(recruiter_scan_signal_rows))
        self.assertEqual(1, len(client_narrative_rows))
        self.assertEqual(1, len(client_handoff_rows))
        self.assertEqual(4, len(client_next_step_rows))
        self.assertEqual(1, len(first_screen_packet_rows))
        self.assertEqual(5, len(first_screen_answer_rows))
        self.assertEqual(4, len(first_screen_objection_rows))
        self.assertEqual(2, len(visual_asset_brief_rows))
        self.assertEqual(1, len(landing_page_snapshot_rows))
        self.assertEqual(5, len(landing_page_fix_rows))
        self.assertEqual(1, len(contactability_cta_rows))
        self.assertEqual(1, len(priority_calibration_rows))
        self.assertEqual(5, len(priority_item_rows))
        self.assertEqual(8, len(current_benchmark_rows))
        self.assertEqual(8, len(diagnostic_axis_rows))
        self.assertEqual(4, len(claim_register_rows))
        self.assertEqual(4, len(claim_proof_prep_rows))
        self.assertEqual(1, len(triage_board_rows))
        self.assertEqual(5, len(triage_rows))
        self.assertEqual(1, len(visible_diagnostic_rows))
        self.assertEqual(6, len(pillar_score_rows))
        self.assertGreaterEqual(len(source_index_rows), 6)
        self.assertEqual(1, len(source_freshness_rows))
        self.assertEqual(8, len(source_trace_rows))
        self.assertEqual(1, len(diagnostic_report_rows))
        self.assertEqual(8, len(section_diagnosis_rows))
        self.assertEqual(1, len(score_lift_forecast_rows))
        self.assertEqual(5, len(score_lift_intervention_rows))
        self.assertEqual(1, len(evidence_intake_rows))
        self.assertEqual(6, len(intake_question_rows))
        self.assertEqual(7, len(domain_score_rows))
        self.assertEqual(1, len(search_preview_scorecard_rows))
        self.assertEqual(1, len(recruiter_attention_path_rows))
        self.assertEqual(4, len(recruiter_scan_moment_rows))
        scorecard = scorecard_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_profile_diagnostic_scorecard=",
            "overall_profile_score=",
            "score_scale=0_to_100",
            "scoring_model=photo_text_completeness_credibility_searchability_conversion",
            "best_practice_source_ids=LINKEDIN_HELP_GOOD_PROFILE,LINKEDIN_PROFILE_METER,APPLYMATE_2026,LINKEDINRANK_2026",
            "scored_evidence_coverage=8_of_12_dimensions_scored",
            "score_confidence=medium_low",
            "unavailable_score_policy=excluded_not_zero",
            "primary_diagnosis=",
            "highest_leverage_fix=",
            "evidence_boundary=",
            "draft_only=true",
        ):
            self.assertIn(required, scorecard)
        self.assertRegex(scorecard, r"overall_profile_score=\d{1,3}")
        self.assert_linkedin_score_integrity_ledger_is_consistent(
            score_integrity_rows[0],
            scorecard,
            domain_score_rows,
        )
        client_handoff = client_handoff_rows[0]
        for required in (
            "linkedin_client_handoff_summary=coach_cover_note",
            "final_read=",
            "score_plain_english=",
            "primary_decision=",
            "first_30_minutes=",
            "evidence_to_collect=",
            "do_not_change_yet=",
            "review_cadence=",
            "success_signal=",
            "privacy_boundary=",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, client_handoff)
        next_step_combined = "\n".join(client_next_step_rows)
        for rank in range(1, 5):
            self.assertIn(f"step_rank={rank}", next_step_combined)
        expected_next_step_sequence = {
            "1": "rewrite_headline_about",
            "2": "capture_visual_evidence",
            "3": "build_proof_packet",
            "4": "run_measurement_review",
        }
        for rank, action in expected_next_step_sequence.items():
            self.assertRegex(next_step_combined, rf"step_rank={rank}; action={action};")
        for row in client_next_step_rows:
            self.assertIn("linkedin_client_next_step=coach_ordered_next_action", row)
            self.assertRegex(row, r"owner=candidate(?:_with_coach_review)?")
            self.assertIn("done_when=", row)
            self.assertIn("risk_if_skipped=", row)
            self.assertIn("no_external_action=true", row)
            self.assertIn("draft_only=true", row)
        first_screen_packet = first_screen_packet_rows[0]
        for required in (
            "linkedin_first_screen_readiness_packet=profile_to_recruiter_screen_bridge",
            "screen_goal=",
            "readiness_grade=provisional_B_minus",
            "readiness_score=",
            "source_profile_score=72",
            "pitch_theme=",
            "evidence_ready=",
            "evidence_missing=",
            "claim_boundaries=",
            "recruiter_risk=",
            "practice_plan=",
            "review_gate=",
            "source_ids=LINKEDIN_HELP_GOOD_PROFILE",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, first_screen_packet)
        first_screen_answer_combined = "\n".join(first_screen_answer_rows)
        for answer_type in (
            "opening_pitch",
            "role_fit",
            "proof_story",
            "risk_boundary",
            "candidate_questions",
        ):
            self.assertIn(f"answer_type={answer_type}", first_screen_answer_combined)
        for row in first_screen_answer_rows:
            self.assertIn("linkedin_first_screen_answer_asset=screen_answer_practice_asset", row)
            self.assertIn("safe_candidate_script=", row)
            self.assertIn("claim_boundary=", row)
            self.assertRegex(row, r"owner=candidate(?:_with_coach_review)?")
            self.assertIn("no_external_action=true", row)
            self.assertIn("draft_only=true", row)
        first_screen_objection_combined = "\n".join(first_screen_objection_rows)
        for objection_type in (
            "unclear_target_role",
            "unconfirmed_tool_claim",
            "thin_public_proof",
            "unknown_availability_or_fit",
        ):
            self.assertIn(f"objection_type={objection_type}", first_screen_objection_combined)
        for row in first_screen_objection_rows:
            self.assertIn("linkedin_first_screen_objection_bridge=objection_to_safe_answer_map", row)
            self.assertIn("bridge_script=", row)
            self.assertIn("claim_boundary=", row)
            self.assertRegex(row, r"owner=candidate(?:_with_coach_review)?")
            self.assertIn("no_external_action=true", row)
            self.assertIn("draft_only=true", row)
        landing_snapshot = landing_page_snapshot_rows[0]
        for required in (
            "linkedin_landing_page_conversion_snapshot=profile_as_recruiter_landing_page",
            "score=72",
            "grade=provisional_B_minus",
            "audience=recruiter_fast_scan",
            "conversion_question=",
            "recruiter_first_read=",
            "fastest_leak=",
            "strongest_proof=",
            "priority_sequence=",
            "source_ids=LINKEDIN_HELP_GOOD_PROFILE",
            "score_boundary=directional_coaching_estimate_not_outcome_prediction",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, landing_snapshot)
        landing_fix_combined = "\n".join(landing_page_fix_rows)
        for section in (
            "photo_banner",
            "headline",
            "about",
            "experience_proof",
            "skills_featured",
        ):
            self.assertIn(f"section={section}", landing_fix_combined)
        for rank in range(1, 6):
            self.assertIn(f"priority_rank={rank}", landing_fix_combined)
        for row in landing_page_fix_rows:
            self.assertIn("linkedin_landing_page_fix_card=ranked_recruiter_landing_page_fix", row)
            self.assertIn("source_ids=", row)
            self.assertIn("acceptance_test=", row)
            self.assertIn("do_not_do=", row)
            self.assertIn("draft_only=true", row)
            self.assertIn("no_external_action=true", row)
            self.assertIn("LINKEDIN_", row)
            self.assertIn("_2026", row)
        contactability_cta = contactability_cta_rows[0]
        for required in (
            "linkedin_contactability_cta_audit=profile_contact_and_next_step_friction_review",
            "contact_surface_status=",
            "open_to_work_signal=",
            "profile_url_status=",
            "target_role_cta=",
            "proof_cta=",
            "first_conversation_prompt=",
            "friction_points=",
            "candidate_private_info_needed=",
            "recommended_private_review=",
            "source_ids=LINKEDIN_HELP_GOOD_PROFILE",
            "_2026",
            "acceptance_test=",
            "privacy_boundary=no_contact_details_no_private_profile_url_no_raw_profile_text",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, contactability_cta)
        priority_calibration = priority_calibration_rows[0]
        for required in (
            "linkedin_diagnostic_priority_calibration=impact_effort_risk_evidence_triage",
            "total_items=5",
            "highest_leverage_item=",
            "fastest_safe_win=",
            "riskiest_item=",
            "recommended_sequence=",
            "confidence_model=impact_effort_risk_with_evidence_confidence_not_outcome_prediction",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "source_ids=LINKEDIN_",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, priority_calibration)
        priority_item_combined = "\n".join(priority_item_rows)
        for section in (
            "photo_banner",
            "headline",
            "about",
            "experience_proof",
            "skills_featured",
        ):
            self.assertIn(f"linked_fix_card_section={section}", priority_item_combined)
        for rank in range(1, 6):
            self.assertIn(f"priority_rank={rank}", priority_item_combined)
        for row in priority_item_rows:
            self.assertIn("linkedin_diagnostic_priority_item=professional_change_triage_item", row)
            self.assertRegex(row, r"impact=(?:very_high|high|medium|low)")
            self.assertRegex(row, r"effort=(?:15_minutes|30_minutes|60_minutes|2_hours|defer_until_review)")
            self.assertRegex(row, r"risk=(?:critical_truth_risk|high_confidentiality_risk|medium_positioning_risk|low_execution_risk)")
            self.assertRegex(row, r"decision=(?:do_first|do_next|confirm_before_change|defer_until_evidence)")
            self.assertIn("truth_boundary=", row)
            self.assertIn("acceptance_test=", row)
            self.assertIn("draft_only=true", row)
            self.assertIn("no_external_action=true", row)
            self.assertIn("LINKEDIN_", row)
            self.assertIn("_2026", row)
        visual_asset_combined = "\n".join(visual_asset_brief_rows)
        for required in (
            "linkedin_visual_asset_brief=photo_banner_asset_direction",
            "asset_type=photo",
            "asset_type=banner",
            "asset_request=",
            "LINKEDIN_HELP_PHOTO_GUIDELINES",
            "LINKEDIN_HELP_COVER",
            "current_evidence_status=unavailable_needs_authorized_review",
            "safe_style_direction=",
            "creation_boundary=",
            "before_review_criteria=",
            "after_review_criteria=",
            "review_gate=",
            "candidate_approval_gate=candidate_selects_exact_asset_and_authorizes_profile_edit",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, visual_asset_combined)
        self.assertRegex(
            visual_asset_combined,
            r"protected_or_confidentiality_boundary=.*(?:attractiveness|confidential)",
        )
        self.assertNotRegex(
            visual_asset_combined.lower(),
            r"\b(?:beautiful|guarantee[sd]?|will get|rank higher|algorithm hack|upload now|publish now|customer names|internal architecture)\b",
        )
        rubric = rubric_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_page_impact_rubric=professional_recruiter_scan_grade_sheet",
            "grade=provisional_B_minus",
            "recruiter_scan_window=first_7_to_90_seconds",
            "scoring_weights=visual_identity_15,headline_value_prop_15,about_opening_15,experience_proof_20,skills_searchability_15,proof_social_activity_10,completeness_visibility_10",
            "pass_threshold=80",
            "priority_model=trust_then_clarity_then_proof_then_findability",
            "best_practice_source_ids=LINKEDIN_HELP_GOOD_PROFILE,APPLYMATE_2026,LINKEDINRANK_2026,ASK_THE_RECRUITER_2026,NEXT_CHAPTER_2026",
            "draft_only=true",
        ):
            self.assertIn(required, rubric)
        score_interpretation = score_interpretation_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_score_interpretation_ledger=grade_to_coach_meaning",
            "overall_score=72",
            "grade=provisional_B_minus",
            "score_band=competitive",
            "what_this_means=",
            "what_it_does_not_mean=",
            "confidence=medium_low",
            "unscored_domains=visual_identity",
            "highest_score_leak=",
            "minimum_evidence_to_upgrade_grade=",
            "next_review_trigger=",
            "outcome_boundary=not_a_ranking_recruiter_response_or_interview_prediction",
            "draft_only=true",
        ):
            self.assertIn(required, score_interpretation)
        self.assertRegex(
            score_interpretation,
            r"what_it_does_not_mean=.*(?:ranking|recruiter response|interview|compensation|market demand)",
        )
        self.assertNotRegex(
            score_interpretation.lower(),
            r"\b(?:perfect|guarantee[sd]?|will get|rank higher|algorithm hack|beautiful|attractive|trustworthy|publish now|message recruiters|upload now)\b",
        )
        narrative = client_narrative_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_client_diagnostic_narrative=photo_text_score_executive_review",
            "plain_english_verdict=The profile has real platform engineering substance",
            "photo_and_banner_read=Photo and banner cannot be scored",
            "text_read=Headline, About, experience, and skills",
            "completeness_read=Featured, recommendations, activity, and completeness",
            "score_interpretation=This provisional B minus is directional coaching judgment",
            "source_backing=LinkedIn official guidance supports profile completeness",
            "first_60_minutes_plan=Spend the first hour on headline",
            "evidence_gaps_to_close=Authorized photo and banner review",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, narrative)
        benchmark_combined = "\n".join(current_benchmark_rows)
        for aspect in (
            "photo",
            "banner",
            "headline",
            "about",
            "experience",
            "skills",
            "proof_social_activity",
            "completeness_visibility",
        ):
            self.assertIn(f"aspect={aspect}", benchmark_combined)
        for required in (
            "linkedin_current_profile_benchmark=source_backed_section_standard",
            "benchmark_question=",
            "good_profile_standard=",
            "candidate_signal=",
            "score_link=",
            "source_ids=LINKEDIN_",
            "_2026",
            "diagnostic_use=",
            "acceptance_test=",
            "evidence_boundary=",
            "draft_only=true",
        ):
            self.assertIn(required, benchmark_combined)
        diagnostic_axis_combined = "\n".join(diagnostic_axis_rows)
        for axis in (
            "photo_banner_visual",
            "headline_positioning",
            "about_text",
            "experience_proof",
            "skills_keywords",
            "featured_proof",
            "recommendations_activity",
            "completeness_visibility",
        ):
            self.assertIn(f"axis={axis}", diagnostic_axis_combined)
        for required in (
            "linkedin_page_diagnostic_axis=client_visible_score_axis",
            "score=",
            "score_label=",
            "evidence_status=",
            "profile_observation=",
            "best_practice_standard=",
            "scoring_reason=",
            "primary_gap=",
            "coach_recommendation=",
            "acceptance_test=",
            "source_ids=LINKEDIN_",
            "_2026",
            "guardrail=",
            "next_evidence_needed=",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, diagnostic_axis_combined)
        self.assertIn("axis=photo_banner_visual; score=not_scored", diagnostic_axis_combined)
        self.assertIn("no_protected_traits", diagnostic_axis_combined)
        self.assertNotRegex(
            diagnostic_axis_combined.lower(),
            r"\b(?:perfect|guarantee[sd]?|will get|rank higher|algorithm hack|beautiful|attractive|trustworthy|publish now|message recruiters|upload now)\b",
        )
        diagnostic_report = diagnostic_report_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_profile_diagnostic_report_card=client_ready_profile_diagnosis",
            "report_grade=provisional_B_minus",
            "overall_score=72",
            "diagnosis_style=coach_report_not_raw_inventory",
            "audience=recruiter_fast_scan",
            "photo_status=",
            "text_status=",
            "completeness_status=",
            "highest_leverage_fix=",
            "score_interpretation=",
            "evidence_confidence=medium_low",
            "source_ids=LINKEDIN_HELP_GOOD_PROFILE",
            "next_review_trigger=",
            "draft_only=true",
        ):
            self.assertIn(required, diagnostic_report)
        section_diagnosis_combined = "\n".join(section_diagnosis_rows)
        for section in (
            "photo_banner",
            "headline",
            "about",
            "experience",
            "skills",
            "proof_assets",
            "recommendations_activity",
            "completeness_visibility",
        ):
            self.assertIn(f"section={section}", section_diagnosis_combined)
        for required in (
            "linkedin_profile_section_diagnosis=client_ready_section_review",
            "what_recruiter_notices=",
            "what_good_looks_like=",
            "acceptance_test=",
            "privacy_or_truth_boundary=",
            "severity=",
            "priority_rank=",
            "timebox=",
            "evidence_needed=",
            "do_not_do=",
            "coach_reasoning=",
            "measurement_signal=",
            "draft_only=true",
        ):
            self.assertIn(required, section_diagnosis_combined)
        self.assertRegex(section_diagnosis_combined, r"severity=(?:critical|high|medium|low)")
        self.assertRegex(section_diagnosis_combined, r"priority_rank=[1-8]")
        self.assertRegex(
            section_diagnosis_combined,
            r"measurement_signal=.*(?:profile_views|search_appearances|qualified_contacts|section_review|screen_readiness|baseline)",
        )
        self.assertEqual(8, len(section_score_rationale_rows))
        section_score_rationale_combined = "\n".join(section_score_rationale_rows)
        for section in (
            "photo_banner",
            "headline",
            "about",
            "experience",
            "skills",
            "proof_assets",
            "recommendations_activity",
            "completeness_visibility",
        ):
            self.assertIn(f"section={section}", section_score_rationale_combined)
        for required in (
            "linkedin_section_score_rationale_matrix=section_score_to_coach_decision_trace",
            "linked_section_score=",
            "linked_domain=",
            "linked_domain_score=",
            "evidence_observed=",
            "best_practice_criterion=",
            "score_reason=",
            "severity_logic=",
            "recruiter_scan_impact=",
            "priority_action=",
            "acceptance_test=",
            "source_ids=",
            "score_boundary=directional_coaching_score_not_algorithm_or_outcome_proof",
            "draft_only=true",
        ):
            self.assertIn(required, section_score_rationale_combined)
        self.assertRegex(
            section_score_rationale_combined,
            r"source_ids=.*LINKEDIN_.*(?:2026|_2026)",
        )
        self.assertNotRegex(
            section_score_rationale_combined.lower(),
            r"\b(?:rank higher|will get|guarantee|algorithm|publish now|message recruiters|upload now)\b",
        )
        forecast = score_lift_forecast_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_score_lift_forecast=coach_bounded_profile_quality_delta",
            "baseline_score=72",
            "target_score_after_interventions=",
            "target_grade_after_interventions=",
            "lift_points=",
            "intervention_count=5",
            "confidence=medium_low",
            "score_boundary=profile_quality_estimate_not_outcome_prediction",
            "causality_boundary=descriptive_coach_forecast_not_platform_or_recruiter_causality",
            "review_cadence=",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, forecast)
        intervention_combined = "\n".join(score_lift_intervention_rows)
        for intervention_type in (
            "headline_about_repositioning",
            "visual_identity_review",
            "experience_proof_bullets",
            "proof_asset_plan",
            "skills_completeness_alignment",
        ):
            self.assertIn(f"intervention_type={intervention_type}", intervention_combined)
        for required in (
            "linkedin_score_lift_intervention=bounded_profile_quality_intervention",
            "linked_low_score_dimensions=",
            "baseline_gap=",
            "candidate_action=",
            "expected_profile_quality_delta=",
            "evidence_required_to_count_lift=",
            "acceptance_test=",
            "risk_boundary=",
            "owner=candidate",
            "measurement_signal=",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, intervention_combined)
        self.assertNotRegex(
            "\n".join(score_lift_forecast_rows + score_lift_intervention_rows).lower(),
            r"\b(?:guarantee[sd]?|will get|rank higher|algorithm hack|interview probability|recruiter response probability|publish now|message recruiters)\b",
        )
        evidence_intake = evidence_intake_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_diagnostic_evidence_intake=profile_gap_to_capture_plan",
            "intake_goal=collect_only_evidence_that_changes_score_or_public_copy",
            "missing_evidence_groups=visuals,target_role,proof_metrics,skills_order,featured_recommendations,visibility_preferences",
            "capture_method=authorized_screenshot_or_candidate_answer_no_raw_profile_export",
            "question_count=6",
            "privacy_boundary=no_raw_profile_text_no_contact_details_no_private_identifiers_no_confidential_assets",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, evidence_intake)
        intake_question_combined = "\n".join(intake_question_rows)
        for section in (
            "photo_banner",
            "target_role_keywords",
            "metrics_scope",
            "skills_order",
            "proof_assets",
            "recommendations_visibility",
        ):
            self.assertIn(f"linked_section={section}", intake_question_combined)
        for required in (
            "linkedin_diagnostic_intake_question=score_changing_question",
            "evidence_needed=",
            "coach_question=",
            "why_it_changes_score=",
            "acceptable_evidence=",
            "unsafe_evidence_to_avoid=",
            "decision_if_unavailable=",
            "linked_score_dimension=",
            "priority=",
            "draft_only=true",
        ):
            self.assertIn(required, intake_question_combined)
        recruiter_scan_summary = recruiter_scan_summary_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_recruiter_scan_summary=executive_linkedin_page_diagnostic",
            "scan_window=first_7_to_90_seconds",
            "overall_profile_score=72",
            "grade=provisional_B_minus",
            "visual_identity_score=not_scored",
            "text_clarity_score=",
            "searchability_score=",
            "proof_conversion_score=",
            "strongest_signal=",
            "weakest_signal=",
            "first_fix=",
            "recruiter_risk=",
            "next_review_gate=",
            "evidence_model=official_platform_guidance_plus_secondary_market_guidance_plus_coach_heuristics",
            "source_claim_boundary=source_ids_support_recommendations_not_guaranteed_results",
            "outcome_boundary=not_a_search_ranking_or_interview_probability",
            "measurement_plan=baseline_then_14_day_candidate_isolated_observation",
            "best_practice_source_ids=LINKEDIN_HELP_GOOD_PROFILE,APPLYMATE_2026,LINKEDINRANK_2026,ASK_THE_RECRUITER_2026",
            "draft_only=true",
        ):
            self.assertIn(required, recruiter_scan_summary)
        scan_combined = "\n".join(recruiter_scan_signal_rows)
        for pillar in (
            "visual_identity",
            "text_clarity",
            "searchability",
            "proof_conversion",
        ):
            self.assertIn(f"pillar={pillar}", scan_combined)
        for required in (
            "score=",
            "score_treatment=",
            "sections_considered=",
            "recruiter_fast_scan_question=",
            "evidence_boundary=",
            "priority_action=",
            "acceptance_test=",
            "best_practice_source_ids=",
            "draft_only=true",
        ):
            self.assertIn(required, scan_combined)
        self.assertIn("pillar=visual_identity", scan_combined)
        self.assertIn("score=not_scored", scan_combined)
        self.assertIn("score_treatment=not_scored_pending_authorized_review", scan_combined)
        claim_combined = "\n".join(claim_register_rows)
        for evidence_class in (
            "official_platform_guidance",
            "secondary_market_guidance",
            "coach_heuristic",
            "candidate_measurement_plan",
        ):
            self.assertIn(f"evidence_class={evidence_class}", claim_combined)
        for required in (
            "linkedin_evidence_and_claim_register=claim_provenance_ledger",
            "claim_id=",
            "claim_scope=",
            "claim_statement=",
            "recommendation_link=",
            "evidence_status=",
            "source_id=",
            "source_tier=",
            "source_date_or_access_date=",
            "source_locator=",
            "candidate_specific_evidence=",
            "claim_type=",
            "claim_strength=",
            "verification_method=",
            "causal_boundary=",
            "outcome_boundary=",
            "measurement_link=",
            "draft_only=true",
        ):
            self.assertIn(required, claim_combined)
        self.assertIn("source_id=LINKEDIN_HELP_GOOD_PROFILE", claim_combined)
        self.assertIn("source_id=LINKEDINRANK_2026", claim_combined)
        self.assertIn("source_id=COACH_HEURISTIC", claim_combined)
        self.assertIn("source_id=CANDIDATE_MEASUREMENT_PLAN", claim_combined)
        self.assertIn("source_tier=official_platform_guidance", claim_combined)
        self.assertIn("source_tier=secondary_market_guidance", claim_combined)
        self.assertIn("source_tier=coach_heuristic", claim_combined)
        self.assertIn("source_tier=post_change_measurement", claim_combined)
        self.assertIn("claim_strength=direct_source_support", claim_combined)
        self.assertIn("claim_strength=secondary_source_support", claim_combined)
        self.assertIn("claim_strength=coach_judgment", claim_combined)
        self.assertIn("claim_strength=testable_hypothesis", claim_combined)
        self.assertIn("outcome_boundary=not_evidence_of_ranking_recruiter_response_or_interview_probability", claim_combined)
        self.assertIn("candidate_isolation=true", claim_combined)
        self.assertIn("attribution_boundary=observation_not_causation", claim_combined)
        claim_proof_combined = "\n".join(claim_proof_prep_rows)
        for claim_theme in (
            "target_role_positioning",
            "tooling_stack_scope",
            "impact_metrics_scope",
            "public_proof_assets",
        ):
            self.assertIn(f"claim_theme={claim_theme}", claim_proof_combined)
        for row in claim_proof_prep_rows:
            self.assertIn("linkedin_claim_proof_prep_packet=claim_to_candidate_evidence_pack", row)
            self.assertIn("linked_profile_sections=", row)
            self.assertIn("public_claim_boundary=", row)
            self.assertIn("evidence_to_prepare=", row)
            self.assertIn("safe_proof_asset=", row)
            self.assertIn("evidence_to_avoid=", row)
            self.assertRegex(row, r"proof_format=(?:sanitized_bullet|metric_range|portfolio_stub|talk_track|candidate_answer)")
            self.assertRegex(row, r"publish_decision=(?:omit_until_confirmed|draft_only_needs_review|ready_after_candidate_confirmation)")
            self.assertIn("interview_bridge=", row)
            self.assertIn("confidentiality_review=", row)
            self.assertIn("acceptance_test=", row)
            self.assertRegex(row, r"owner=candidate(?:_with_coach_review)?")
            self.assertIn("source_ids=LINKEDIN_", row)
            self.assertIn("_2026", row)
            self.assertIn("outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability", row)
            self.assertIn("no_external_action=true", row)
            self.assertIn("draft_only=true", row)
        self.assertNotRegex(
            claim_proof_combined.lower(),
            r"\b(?:password|cookie|private message|raw export|confidential customer|internal architecture|publish now|message recruiters|upload now|will get|rank higher|guarantee[sd]?)\b",
        )
        self.assertEqual(4, len(public_claim_risk_rows))
        public_claim_risk_combined = "\n".join(public_claim_risk_rows)
        for claim_theme in (
            "target_role_positioning",
            "tooling_stack_scope",
            "impact_metrics_scope",
            "public_proof_assets",
        ):
            self.assertIn(f"claim_theme={claim_theme}", public_claim_risk_combined)
        self.assertIn("public_profile_decision=interview_only_until_confirmed", public_claim_risk_combined)
        self.assertIn("public_profile_decision=block_until_confidentiality_review", public_claim_risk_combined)
        self.assertIn("risk_level=blocker", public_claim_risk_combined)
        for row in public_claim_risk_rows:
            self.assertIn("linkedin_public_claim_risk_register=public_claim_safety_decision", row)
            self.assertIn("source_claim_packet=linkedin_claim_proof_prep_packet", row)
            self.assertRegex(row, r"public_profile_decision=(?:use_publicly_after_confirmation|interview_only_until_confirmed|omit_from_public_profile|block_until_confidentiality_review)")
            self.assertRegex(row, r"interview_use_decision=(?:use_as_fact_checked_talk_track|use_only_with_boundary|avoid_until_confirmed)")
            self.assertRegex(row, r"risk_level=(?:low|medium|high|blocker)")
            self.assertIn("risk_reason=", row)
            self.assertIn("required_evidence=", row)
            self.assertIn("safe_public_copy_boundary=", row)
            self.assertIn("safe_interview_bridge=", row)
            self.assertIn("confidentiality_boundary=", row)
            self.assertIn("candidate_question=", row)
            self.assertIn("blocked_until=", row)
            self.assertIn("publish_gate=manual_candidate_review_and_exact_action_target_authorization", row)
            self.assertIn("outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability", row)
            self.assertIn("no_external_action=true", row)
            self.assertIn("draft_only=true", row)
        self.assertNotRegex(
            public_claim_risk_combined.lower(),
            r"\b(?:password|cookie|private message|raw export|confidential customer|internal architecture|publish now|message recruiters|upload now|will get|rank higher|guarantee[sd]?)\b",
        )
        triage_board = triage_board_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_diagnostic_triage_board=coach_priority_action_board",
            "source_scorecard_id=professional_section_by_section_linkedin_page_audit",
            "board_goal=convert_scores_into_ordered_profile_fixes",
            "top_priority=headline_about_before_public_proof_or_outreach",
            "decision_model=severity_x_recruiter_scan_impact_x_evidence_confidence",
            "evidence_boundary=no_raw_profile_text_no_outcome_prediction",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "draft_only=true",
            "consent=not_granted",
            "no_external_action=true",
        ):
            self.assertIn(required, triage_board)
        triage_combined = "\n".join(triage_rows)
        for section_cluster in (
            "visual_trust",
            "headline_about",
            "experience_proof",
            "skills_searchability",
            "proof_assets",
        ):
            self.assertIn(f"section_cluster={section_cluster}", triage_combined)
        for required in (
            "linkedin_diagnostic_triage_item=coach_priority_board",
            "priority_rank=",
            "severity=",
            "evidence_label=",
            "linked_score_dimensions=",
            "linked_domain=",
            "linked_pillar=",
            "linked_score=",
            "recruiter_scan_impact=",
            "recruiter_scan_question=",
            "current_signal=",
            "why_it_matters=",
            "exact_next_action=",
            "acceptance_test=",
            "source_ids=",
            "timebox=",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "outcome_boundary=not_a_search_ranking_or_interview_probability",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, triage_combined)
        self.assertIn("priority_rank=1", triage_combined)
        self.assertIn("severity=critical", triage_combined)
        search_preview_scorecard = search_preview_scorecard_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_search_preview_scorecard=pre_click_recruiter_result_card_audit",
            "preview_surface=search_result_or_connection_context_card",
            "source_attention_path=search_preview_to_90_second_page_scan",
            "visible_or_inferred_inputs=",
            "headline_preview_quality=",
            "role_niche_clarity=",
            "keyword_fit=",
            "location_work_mode_clarity=",
            "visual_identity_status=",
            "proof_or_credibility_cue=",
            "cta_or_contactability=",
            "preview_score=60",
            "score_scale=0_to_100",
            "score_treatment=scored_directional_estimate",
            "primary_preview_leak=",
            "highest_leverage_preview_fix=",
            "acceptance_test=",
            "source_ids=LINKEDIN_HELP_GOOD_PROFILE",
            "privacy_boundary=no_raw_profile_text_no_contact_details_no_private_analytics",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, search_preview_scorecard)
        recruiter_attention_path = recruiter_attention_path_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_recruiter_attention_path=search_preview_to_90_second_page_scan",
            "path_goal=explain_what_a_recruiter_understands_before_deciding_to_screen_or_move_on",
            "target_role_story=Kubernetes_platform_reliability_and_CI_CD_automation_with_Jenkins_unconfirmed",
            "source_scorecard_id=professional_section_by_section_linkedin_page_audit",
            "scan_moments=search_preview,top_card_7_seconds,about_experience_30_seconds,proof_trust_90_seconds",
            "attention_pass_threshold=clear_role_niche_supported_proof_and_low_friction_next_step",
            "biggest_attention_leak=",
            "strongest_attention_signal=",
            "highest_leverage_fix=",
            "confidence=medium_low",
            "source_ids=LINKEDIN_HELP_GOOD_PROFILE",
            "privacy_boundary=no_raw_profile_text_no_contact_details_no_private_analytics",
            "outcome_boundary=not_a_search_ranking_recruiter_response_or_interview_probability",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, recruiter_attention_path)
        recruiter_scan_moment_combined = "\n".join(recruiter_scan_moment_rows)
        for moment in (
            "search_preview",
            "top_card_7_seconds",
            "about_experience_30_seconds",
            "proof_trust_90_seconds",
        ):
            self.assertIn(f"moment={moment}", recruiter_scan_moment_combined)
        for required in (
            "linkedin_recruiter_scan_moment=attention_path_checkpoint",
            "recruiter_question=",
            "visible_inputs=",
            "score=",
            "score_treatment=",
            "what_recruiter_understands=",
            "attention_leak=",
            "conversion_risk=",
            "fix=",
            "acceptance_test=",
            "evidence_label=",
            "source_ids=",
            "protected_or_truth_boundary=",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, recruiter_scan_moment_combined)
        self.assertIn("moment=top_card_7_seconds", recruiter_scan_moment_combined)
        self.assertIn("score=not_scored", recruiter_scan_moment_combined)
        self.assertIn("score_treatment=not_scored_pending_authorized_visual_review", recruiter_scan_moment_combined)
        self.assertIn("Jenkins", recruiter_scan_moment_combined)
        visible_diagnostic = visible_diagnostic_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_coach_visible_diagnostic=client_grade_snapshot",
            "profile_score=72",
            "grade=provisional_B_minus",
            "scan_window=first_7_to_90_seconds",
            "one_sentence_verdict=",
            "recruiter_likely_reaction=",
            "main_conversion_gap=",
            "top_strength=",
            "top_risk=",
            "top_3_fixes=",
            "quick_win_30_minutes=",
            "evidence_confidence=medium_low",
            "unavailable_sections=",
            "next_review_gate=",
            "score_boundary=directional_coaching_estimate_not_outcome_prediction",
            "draft_only=true",
        ):
            self.assertIn(required, visible_diagnostic)
        self.assertIn("technical_depth_is_real", visible_diagnostic)
        self.assertIn("does_not_yet_package_it_as_a_fast_recruiter_screen_story", visible_diagnostic)
        pillar_score_combined = "\n".join(pillar_score_rows)
        for pillar in (
            "first_impression",
            "positioning_clarity",
            "proof_density",
            "search_findability",
            "trust_and_completeness",
            "conversion_readiness",
        ):
            self.assertIn(f"pillar={pillar}", pillar_score_combined)
        for required in (
            "linkedin_profile_pillar_score=recruiter_scan_pillar",
            "score=",
            "grade=",
            "sections_used=",
            "what_recruiter_sees=",
            "why_it_matters=",
            "specific_gap=",
            "best_fix=",
            "acceptance_test=",
            "evidence_label=",
            "score_treatment=",
            "draft_only=true",
        ):
            self.assertIn(required, pillar_score_combined)
        source_index_combined = "\n".join(source_index_rows)
        for source_id in (
            "LINKEDIN_HELP_GOOD_PROFILE",
            "LINKEDIN_HELP_PHOTO_GUIDELINES",
            "LINKEDIN_HELP_COVER",
            "LINKEDIN_BUSINESS_PHOTO",
            "LINKEDINRANK_2026",
            "APPLYMATE_2026",
            "HIREKIT_2026",
            "GERAJOBS_2026",
            "LINKEDINPREVIEW_2026",
            "ASKIA_2026",
            "VOKETA_2026",
            "FOURLEAF_2026",
            "ASK_THE_RECRUITER_2026",
        ):
            self.assertIn(f"source_id={source_id}", source_index_combined)
        for required in (
            "linkedin_best_practice_source_index=dated_guidance_catalog",
            "source_name=",
            "source_type=",
            "source_url=https://",
            "access_date=2026-08-06",
            "supports_profile_criteria=",
            "source_boundary=recommendation_support_not_outcome_or_algorithm_proof",
            "use_in_scorecard=true",
            "draft_only=true",
        ):
            self.assertIn(required, source_index_combined)
        source_freshness = source_freshness_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_source_freshness_audit=current_guidance_quality_check",
            "source_index_ref=dated_guidance_catalog",
            "official_source_count=",
            "secondary_2026_source_count=",
            "required_official_sources_present=LINKEDIN_HELP_GOOD_PROFILE,LINKEDIN_HELP_PHOTO_GUIDELINES,LINKEDIN_HELP_COVER,LINKEDIN_HELP_FEATURED,LINKEDIN_HELP_SKILLS,LINKEDIN_PROFILE_METER",
            "secondary_source_policy=use_only_current_2026_sources_for_market_coach_guidance",
            "access_date_window=2026_current_audit_window",
            "freshness_decision=current_enough_for_private_profile_diagnosis",
            "stale_source_action=refresh_sources_before_claiming_current_2026_best_practice",
            "unsupported_claim_boundary=sources_support_profile_quality_criteria_not_ranking_response_interview_salary_or_time_to_hire_outcomes",
            "next_review_trigger=new_linkedin_guidance_or_older_than_90_days",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, source_freshness)
        self.assertRegex(source_freshness, r"official_source_count=\d+")
        self.assertRegex(source_freshness, r"secondary_2026_source_count=\d+")
        self.assertNotRegex(
            source_freshness.lower(),
            r"\b(?:guarantee[sd]?|will get|rank higher|response rate|interview probability|salary|time to hire|algorithm hack)\b",
        )
        source_trace_combined = "\n".join(source_trace_rows)
        for section in (
            "photo_banner",
            "headline",
            "about",
            "experience",
            "skills",
            "proof_assets",
            "recommendations_activity",
            "completeness_visibility",
        ):
            self.assertIn(f"section={section}", source_trace_combined)
        for row in source_trace_rows:
            self.assertIn("linkedin_source_trace_matrix=section_recommendation_source_map", row)
            self.assertIn("coaching_claim=", row)
            self.assertIn("recommendation_summary=", row)
            self.assertIn("cited_source_ids=", row)
            self.assertIn("LINKEDIN_", row)
            self.assertIn("_2026", row)
            self.assertIn("source_criteria_matched=", row)
            self.assertIn("candidate_evidence_used=", row)
            self.assertIn("source_fit=", row)
            self.assertIn(
                "unsupported_claim_boundary=recommendation_support_not_algorithm_or_outcome_proof",
                row,
            )
            self.assertIn("acceptance_test=", row)
            self.assertIn("draft_only=true", row)
        domain_score_combined = "\n".join(domain_score_rows)
        for domain in (
            "visual_identity",
            "headline_value_prop",
            "about_opening",
            "experience_proof",
            "skills_searchability",
            "proof_social_activity",
            "completeness_visibility",
        ):
            self.assertIn(f"domain={domain}", domain_score_combined)
        for required in (
            "linkedin_profile_domain_score=weighted_professional_profile_rubric",
            "weight=",
            "raw_score=",
            "weighted_points=",
            "score_treatment=",
            "evidence_basis=",
            "what_good_looks_like=",
            "coach_diagnosis=",
            "next_action=",
            "acceptance_test=",
            "source_ids=",
            "draft_only=true",
        ):
            self.assertIn(required, domain_score_combined)
        self.assertIn("score_treatment=not_scored_pending_authorized_review", domain_score_combined)
        self.assertIn("score_treatment=scored_directional_estimate", domain_score_combined)

        combined = "\n".join(dimension_rows)
        for dimension in (
            "photo",
            "banner",
            "headline",
            "about",
            "experience",
            "skills",
            "featured",
            "recommendations",
            "activity",
            "completeness",
            "keyword_alignment",
            "recruiter_conversion",
        ):
            self.assertIn(f"dimension={dimension}", combined)
        for required in (
            "score=",
            "status=",
            "observed_or_unavailable=",
            "best_practice=",
            "recruiter_scan_risk=",
            "impact_fix=",
            "completeness_gap=",
            "evidence_label=",
            "score_treatment=",
            "priority=",
        ):
            self.assertIn(required, combined)
        unknown_rows = [
            row
            for row in dimension_rows
            if "evidence_label=unknown_unavailable" in row
        ]
        self.assertGreaterEqual(len(unknown_rows), 4)
        for row in unknown_rows:
            self.assertIn("score=not_scored", row)
            self.assertIn("score_treatment=not_scored_pending_authorized_review", row)
            self.assertNotIn("score=0", row)
        self.assertIn("photo_quality=unavailable_needs_visual_review", combined)
        self.assertIn("first_300_characters", combined)
        self.assertIn("role_plus_niche_plus_value", combined)
        text_combined = "\n".join(text_rows)
        for section in ("headline", "about", "experience", "skills"):
            self.assertIn(f"section={section}", text_combined)
        for required in (
            "score=",
            "current_text_signal=",
            "recruiter_question_answered=",
            "gap=",
            "rewrite_standard=",
            "specific_fix=",
            "acceptance_test=",
            "best_practice_source_ids=",
            "evidence_label=",
            "draft_only=true",
        ):
            self.assertIn(required, text_combined)
        self.assertIn("headline_should_name_role_niche_and_value", text_combined)
        self.assertIn("about_first_two_lines_should_state_who_you_help_and_outcome", text_combined)
        self.assertIn("experience_should_use_context_action_result_or_quantified_scope", text_combined)
        self.assertIn("skills_should_prioritize_searchable_target_role_terms", text_combined)
        visual_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_visual_identity_review=" in row
        ]
        self.assertEqual(1, len(visual_rows))
        visual = visual_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_visual_identity_review=photo_and_banner_coach_diagnostic",
            "photo_review_status=unavailable_requires_screenshot_or_live_visual_inspection",
            "face_visibility=",
            "crop_quality=",
            "lighting_quality=",
            "background_quality=",
            "expression_signal=",
            "attire_signal=",
            "recency_signal=",
            "image_quality=",
            "banner_review_status=",
            "banner_relevance=",
            "confidentiality_risk=",
            "visual_next_step=request_candidate_approved_screenshot_or_read_only_live_visual_review",
            "best_practice_source_ids=LINKEDIN_HELP_PHOTO_GUIDELINES,LINKEDIN_BUSINESS_PHOTO,LINKEDINPREVIEW_PHOTO_2026,LINKEDINRANK_2026,LINKEDIN_HELP_COVER",
            "draft_only=true",
        ):
            self.assertIn(required, visual)
        photo_rubric = photo_rubric_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_photo_readiness_rubric=authorized_visual_review_standard",
            "review_mode=authorized_screenshot_or_read_only_live_visual_only",
            "criteria=solo_professional_headshot,clear_face,crop_60_to_70_percent,even_lighting,simple_background,recent_recognizable,high_resolution,industry_appropriate_attire",
            "protected_traits_boundary=no_attractiveness_age_race_ethnicity_gender_disability_health_or_personality_judgment",
            "candidate_action_if_unavailable=request_candidate_approved_screenshot_or_read_only_live_visual_review",
            "draft_only=true",
        ):
            self.assertIn(required, photo_rubric)
        self.assertNotRegex(
            visual.lower(),
            r"\b(?:beautiful|handsome|attractive|age|race|ethnicity|gender|disability|guarantee[sd]?|perfect photo)\b",
        )
        self.assertNotRegex(
            "\n".join((scorecard, combined)).lower(),
            r"\b(?:guarantee[sd]?|will get hired|will get an interview|linkedin algorithm hack|recruiter ranking guaranteed|attracts all recruiters|perfect profile)\b",
        )

    def assert_linkedin_score_improvement_roadmap_is_coach_grade(self, diagnosis: str) -> None:
        roadmap_rows = [
            row
            for row in diagnosis.splitlines()
            if "linkedin_score_improvement_roadmap=" in row
        ]
        stage_rows = [
            row
            for row in diagnosis.splitlines()
            if "score_stage=" in row
        ]
        self.assertEqual(1, len(roadmap_rows))
        self.assertEqual(3, len(stage_rows))
        roadmap = roadmap_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_score_improvement_roadmap=profile_score_to_action_plan",
            "baseline_score=72",
            "stage_count=3",
            "sequence=quick_win_to_credibility_to_market_conversion",
            "evidence_boundary=",
            "score_boundary=directional_coaching_estimate_not_outcome_prediction",
            "draft_only=true",
        ):
            self.assertIn(required, roadmap)
        combined = "\n".join(stage_rows)
        for stage in (
            "stage=quick_win",
            "stage=credibility_build",
            "stage=market_conversion",
        ):
            self.assertIn(stage, combined)
        for required in (
            "current_score=",
            "target_score=",
            "timebox=",
            "primary_sections=",
            "coach_action=",
            "linked_low_score_dimensions=",
            "intervention_type=",
            "exact_candidate_action=",
            "copy_or_prompt=",
            "acceptance_criteria=",
            "effort_level=",
            "evidence_required=",
            "score_lift_reason=",
            "recruiter_scan_effect=",
            "risk_if_skipped=",
            "observable_metric=",
            "stop_or_confirm_gate=",
            "draft_only=true",
        ):
            self.assertIn(required, combined)
        self.assertIn("timebox=15_minutes", combined)
        self.assertIn("timebox=60_minutes", combined)
        self.assertIn("timebox=180_minutes", combined)
        for intervention in (
            "intervention_type=copy_edit",
            "intervention_type=proof_asset_or_confirmation",
            "intervention_type=measurement_and_iteration",
        ):
            self.assertIn(intervention, combined)
        self.assertIn("linked_low_score_dimensions=headline,about,skills", combined)
        self.assertIn("linked_low_score_dimensions=featured,recommendations,experience", combined)
        self.assertIn("linked_low_score_dimensions=recruiter_conversion,activity,keyword_alignment", combined)
        self.assertRegex(combined, r"acceptance_criteria=[^;\n]+")
        self.assertRegex(combined, r"copy_or_prompt=[^;\n]+")
        self.assertRegex(combined, r"effort_level=(?:low|medium|high)")
        self.assertNotRegex(
            "\n".join((roadmap, combined)).lower(),
            r"\b(?:guarantee[sd]?|will get hired|will get an interview|recruiter ranking guaranteed|algorithm hack|viral|double your interviews)\b",
        )

    def assert_linkedin_intervention_measurement_loop_is_safe(self, experiment_plan: str) -> None:
        registry_rows = [
            row
            for row in experiment_plan.splitlines()
            if "linkedin_intervention_registry=" in row
        ]
        snapshot_rows = [
            row
            for row in experiment_plan.splitlines()
            if "linkedin_funnel_cohort_snapshot=" in row
        ]
        decision_rows = [
            row
            for row in experiment_plan.splitlines()
            if "linkedin_weekly_experiment_decision_card=" in row
        ]
        self.assertEqual(1, len(registry_rows))
        self.assertEqual(1, len(snapshot_rows))
        self.assertEqual(1, len(decision_rows))
        registry = registry_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_intervention_registry=profile_content_asset_change_log",
            "profile_version_id=jenkins-coach-smoke-v2",
            "source_scorecard_id=professional_section_by_section_linkedin_page_audit",
            "intervention_type=profile_copy_and_proof_asset_plan",
            "intervention_summary=headline_about_experience_skills_plus_safe_content_proof_plan",
            "baseline_window=pre_change_14_days_or_unknown",
            "observation_window=14_30_60_90_days",
            "target_audience=platform_reliability_recruiters_and_hiring_team_adjacent_peers",
            "baseline_metrics=profile_views,search_appearances,profile_appearances,post_impressions,qualified_contacts,conversations,recruiter_screens",
            "confounders_to_log=market_changes,networking_activity,applications,content_posts,profile_edits,seasonality,referrals",
            "privacy_boundary=aggregate_candidate_owned_metrics_no_raw_viewer_identity_no_private_profile_text",
            "decision_options=continue,pause,revert,research",
            "draft_only=true",
            "causality_boundary=observational_signals_not_attribution_or_guarantee",
        ):
            self.assertIn(required, registry)

        snapshot = snapshot_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_funnel_cohort_snapshot=weekly_aggregate_signal_review",
            "profile_version_id=jenkins-coach-smoke-v2",
            "snapshot_date=unknown_pending_first_review",
            "metric_window=weekly",
            "profile_views=unknown",
            "search_appearances=unknown",
            "profile_appearances=unknown",
            "post_impressions=unknown",
            "qualified_contacts=unknown",
            "conversations=unknown",
            "recruiter_screens=unknown",
            "quality_signal=unknown_pending_observation",
            "decision=research",
            "next_action=collect_baseline_or_wait_for_first_review",
            "draft_only=true",
            "no_external_action=true",
            "causality_boundary=observational_signals_not_attribution_or_guarantee",
        ):
            self.assertIn(required, snapshot)

        decision = decision_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_weekly_experiment_decision_card=coach_signal_to_action_review",
            "source_registry_id=profile_content_asset_change_log",
            "source_snapshot_id=weekly_aggregate_signal_review",
            "profile_version_id=jenkins-coach-smoke-v2",
            "review_cadence=weekly_after_14_day_baseline",
            "primary_question=is_the_profile_change_creating_more_qualified_conversations_or_only_noise",
            "minimum_observation_window=14_days_before_directional_decision",
            "input_metrics=profile_views,search_appearances,qualified_contacts,conversations,recruiter_screens,time_invested",
            "quality_bar=qualified_contact_or_conversation_from_target_role_context_not_raw_views_only",
            "decision_rules=continue_if_quality_signals_improve_pause_if_views_rise_without_qualified_contacts_revert_if_positioning_confuses_target_research_if_data_unavailable",
            "current_decision=research",
            "next_action=collect_baseline_metrics_and_do_not_increase_outreach_volume_yet",
            "confounder_check=log_profile_edits_networking_activity_applications_content_posts_referrals_and_market_changes",
            "coach_note=do_not_treat_profile_views_as_success_without_qualified_contact_or_conversation_signal",
            "privacy_boundary=aggregate_candidate_owned_metrics_no_viewer_identity_no_private_profile_text",
            "outcome_boundary=not_a_causal_claim_response_rate_interview_salary_or_time_to_hire_prediction",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, decision)
        self.assertNotRegex(
            "\n".join((registry, snapshot, decision)).lower(),
            r"\b(?:guarantee[sd]?|will get hired|will get an interview|algorithm hack|viral|growth hack|engagement pod|scrape|bulk|blast|profile edited|post published|message sent|connection sent|caused by|viewer identity|response rate|salary|time to hire|raw profile text)\b",
        )

    def assert_recruiter_bridge_is_safe(self, networking_drafts: str) -> None:
        bridge_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_conversation_bridge=" in row
        ]
        self.assertEqual(1, len(bridge_rows))
        bridge = bridge_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_target=",
            "context_source=",
            "supported_fact_ids=",
            "target_theme=",
            "vacancy_state=no_dated_current_vacancy",
            "low_friction_question=",
            "conversation_goal=",
            "thirty_second_pitch=",
            "proof_points=",
            "qualification_questions=",
            "objection_bridges=",
            "advance_the_process_ask=",
            "screen_success_criteria=",
            "tracking_event=",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
        ):
            self.assertIn(required, bridge)
        self.assertRegex(bridge, r"proof_points=.*(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)")
        self.assertRegex(bridge, r"tracking_event=LI-JENKINS-003")
        self.assertNotRegex(
            bridge.lower(),
            r"\b(?:current opening|open role|is hiring|you are hiring|demand|in demand|need someone|looking for|strong fit|great fit|ideal fit|perfect fit|match|eligible|authorized to work|remote-ready|available at|schedule|calendar|meet at|approved to send|authorized to send|will get an interview|guarantee(?:s|d)?\s+(?:a|an|the)?\s*(?:job|interview|screen|outcome|offer))\b",
        )

    def assert_recruiter_network_expansion_plan_is_safe(self, networking_drafts: str) -> None:
        plan_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_network_expansion_plan=" in row
        ]
        self.assertEqual(1, len(plan_rows))
        plan = plan_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_network_expansion_plan=",
            "network_goal=",
            "target_segments=",
            "source_queries=",
            "warm_path_first=",
            "context_quality_gate=",
            "priority_score=",
            "segment_scoring_model=",
            "outreach_batch_limit=",
            "candidate_time_budget=",
            "quality_review_check=",
            "do_not_contact_rules=",
            "outreach_funnel_link=",
            "cadence_boundary=",
            "personalization_required=",
            "recruiter_bridge_handoff=",
            "measurement_events=",
            "stop_condition=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, plan)
        self.assertIn("warm_referral", plan)
        self.assertIn("named_recruiter", plan)
        self.assertIn("LI-JENKINS-003", plan)
        self.assertIn("sequence_step_1_to_5", plan)
        self.assertNotRegex(
            plan.lower(),
            r"\b(?:spray|blast|mass message|bulk send|scrape|automated connection|100 recruiters|unlimited|daily auto|import contacts|guarantee[sd]?|will get an interview|perfect fit|strong fit|approved to send|authorized to send)\b",
        )

    def assert_recruiter_discovery_engine_is_safe(self, networking_drafts: str) -> None:
        engine_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_discovery_engine=" in row
        ]
        query_rows = [
            row
            for row in networking_drafts.splitlines()
            if "discovery_query=" in row
        ]
        signal_rows = [
            row
            for row in networking_drafts.splitlines()
            if "discovery_signal=" in row
        ]
        self.assertEqual(1, len(engine_rows))
        self.assertGreaterEqual(len(query_rows), 3)
        self.assertEqual(1, len(signal_rows))
        engine = engine_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_discovery_engine=",
            "source_plan_id=",
            "discovery_goal=build_context_qualified_targets_before_any_draft",
            "search_surface=linkedin_people_jobs_company_alumni_groups",
            "query_count=3",
            "signal_model=warmth_plus_role_context_plus_proof_fit_plus_reply_path_minus_safety_risk",
            "manual_review_limit=10_profiles_per_batch",
            "shortlist_handoff=only_context_qualified_rows_move_to_recruiter_target_shortlist",
            "no_scraping=true",
            "no_external_action=true",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, engine)

        combined_queries = "\n".join(query_rows)
        for required in (
            "query_id=RD-JENKINS-Q1",
            "query_id=RD-JENKINS-Q2",
            "query_id=RD-JENKINS-Q3",
            "discovery_query=manual_linkedin_search_hypothesis",
            "query_intent=",
            "query_terms=",
            "target_segment=",
            "must_have_context=",
            "negative_filter=",
            "warm_intro_path=",
            "first_question=",
            "measurement_event=LI-JENKINS-003",
            "next_safe_action=collect_recipient_context",
            "draft_only=true",
        ):
            self.assertIn(required, combined_queries)
        self.assertRegex(combined_queries, r"target_segment=(?:named_recruiter|warm_referral|technical_peer)")
        self.assertRegex(combined_queries, r"must_have_context=.*(?:named_person|visible_specialty|shared_context|current_role_scope)")
        self.assertRegex(combined_queries, r"negative_filter=.*(?:generic_recruiter|no_visible_context|closed_role|unsupported_claim)")
        self.assertRegex(combined_queries, r"first_question=.*(?:useful|right_person|criteria|scope|process)")

        signal = signal_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "discovery_signal=manual_target_quality_scorecard",
            "qualified_threshold=high_or_medium_with_named_context",
            "acceptance_signal=named_context_plus_low_friction_reply_path",
            "discard_reason=no_named_person_or_no_relevant_context_or_unsafe_claim_needed",
            "candidate_review_required=true",
            "next_safe_action=rank_or_discard_before_drafting",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, signal)
        self.assertNotRegex(
            "\n".join((engine, combined_queries, signal)).lower(),
            r"\b(?:scrape|crawler|auto-connect|auto message|automated profile collection|automated connection|automated message|bulk|blast|spray|100 recruiters|unlimited|send now|message sent|connection sent|guarantee[sd]?|will get an interview|strong fit|perfect fit|calendar|available at|approved to send|authorized to send)\b",
        )

    def assert_recruiter_target_shortlist_is_safe(self, networking_drafts: str) -> None:
        shortlist_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_target_shortlist=" in row
        ]
        target_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_target_row=" in row
        ]
        self.assertEqual(1, len(shortlist_rows))
        self.assertGreaterEqual(len(target_rows), 3)
        self.assertLessEqual(len(target_rows), 6)
        shortlist = shortlist_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_target_shortlist=",
            "shortlist_goal=",
            "source_batch_id=",
            "target_count=3",
            "ranking_method=context_strength_plus_role_relevance_plus_relationship_warmth_plus_proof_fit_minus_safety_risk",
            "batch_decision=proceed_with_1_contactable_target_and_collect_context_for_2",
            "top_priority_targets=RT-JENKINS-001",
            "required_context_before_draft=",
            "next_safe_action=draft_only_review",
            "outreach_funnel_link=LI-JENKINS-003",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, shortlist)

        combined_targets = "\n".join(target_rows)
        for required in (
            "target_id=RT-JENKINS-001",
            "target_id=RT-JENKINS-002",
            "target_id=RT-JENKINS-003",
            "contact_category=named_recruiter",
            "contact_category=warm_referral",
            "contact_category=technical_peer",
            "relationship_warmth=",
            "context_source=",
            "supported_fact_ids=",
            "missing_context=",
            "priority_score=",
            "personalization_trigger=",
            "recommended_draft_type=",
            "contactability_status=contactable",
            "contactability_status=context_needed",
            "manual_review_decision=",
            "do_not_contact_reason=none",
            "do_not_contact_reason=relationship_context_unconfirmed",
            "do_not_contact_reason=named_person_and_shared_context_missing",
            "measurement_event=LI-JENKINS-003",
            "next_safe_action=",
            "next_safe_action=collect_recipient_context",
        ):
            self.assertIn(required, combined_targets)
        self.assertRegex(combined_targets, r"supported_fact_ids=.*(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)")
        self.assertRegex(combined_targets, r"priority_score=(?:high|medium|low)")
        self.assertRegex(combined_targets, r"recommended_draft_type=(?:recruiter_conversation_bridge|connection_note|referral_request)")
        self.assertNotRegex(
            "\n".join((shortlist, combined_targets)).lower(),
            r"\b(?:spray|blast|mass message|bulk send|scrape|automated connection|100 recruiters|unlimited|daily auto|message sent|connection sent|connect clicked|strong fit|perfect fit|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
        )

    def assert_recruiter_outreach_lab_is_safe(self, networking_drafts: str) -> None:
        lab_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_outreach_lab=" in row
        ]
        variant_rows = [
            row
            for row in networking_drafts.splitlines()
            if "outreach_variant=" in row
        ]
        self.assertEqual(1, len(lab_rows))
        self.assertEqual(3, len(variant_rows))
        lab = lab_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_outreach_lab=",
            "source_shortlist_id=RTS-JENKINS-001",
            "variant_count=3",
            "target_scope=top_priority_targets",
            "lab_goal=choose_the_lowest_risk_draft_for_manual_candidate_review",
            "selection_rule=",
            "approval_state=not_approved",
            "next_safe_action=draft_only_review_then_exact_authorization",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, lab)

        combined_variants = "\n".join(variant_rows)
        for required in (
            "variant_id=OV-JENKINS-001",
            "variant_id=OV-JENKINS-002",
            "variant_id=OV-JENKINS-003",
            "target_id=RT-JENKINS-001",
            "target_id=RT-JENKINS-002",
            "target_id=RT-JENKINS-003",
            "variant_type=recruiter_conversation_bridge",
            "variant_type=referral_request",
            "variant_type=connection_note",
            "draft_text=",
            "personalization_reason=",
            "low_friction_question=",
            "risk_review=",
            "expected_signal=",
            "reply_likelihood_score=",
            "reply_likelihood_reason=",
            "friction_level=",
            "personalization_strength=",
            "coach_recommendation=",
            "measurement_event=LI-JENKINS-003",
            "send_status=draft_only",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, combined_variants)
        self.assertRegex(combined_variants, r"risk_review=.*(?:no_unverified_Jenkins|no_production_claim)")
        self.assertRegex(combined_variants, r"expected_signal=.*(?:requests_summary|clarifies_scope|confirms_best_person)")
        self.assertRegex(combined_variants, r"reply_likelihood_score=(?:high|medium|low)")
        self.assertRegex(combined_variants, r"friction_level=(?:low|medium|high)")
        self.assertRegex(combined_variants, r"personalization_strength=(?:strong|moderate|weak)")
        self.assertIn("coach_recommendation=use_first", combined_variants)
        self.assertNotRegex(
            "\n".join((lab, combined_variants)).lower(),
            r"\b(?:spray|blast|mass message|bulk send|scrape|automated connection|message sent|connection sent|connect clicked|send now|current opening|open role|strong fit|great fit|perfect fit|eligible|authorized to work|calendar|meet at|available at|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
        )

    def assert_linkedin_outreach_quality_gate_is_safe(self, networking_drafts: str) -> None:
        gate_rows = [
            row
            for row in networking_drafts.splitlines()
            if "linkedin_outreach_quality_gate=" in row
        ]
        check_rows = [
            row
            for row in networking_drafts.splitlines()
            if "linkedin_outreach_quality_check=" in row
        ]
        self.assertEqual(1, len(gate_rows))
        self.assertEqual(3, len(check_rows))
        gate = gate_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_outreach_quality_gate=manual_recruiter_outreach_review_gate",
            "source_outreach_lab_id=RTS-JENKINS-001",
            "source_shortlist_id=RTS-JENKINS-001",
            "selected_variant_id=OV-JENKINS-001",
            "gate_goal=decide_if_selected_outreach_variant_is_safe_specific_and_worth_manual_review",
            "target_context_quality=strong",
            "evidence_fit=partial_confirm_first",
            "personalization_quality=strong",
            "friction_level=low",
            "safety_decision=revise",
            "next_safe_action=draft_only_review_then_exact_authorization",
            "measurement_event=LI-JENKINS-003",
            "candidate_review_required=true",
            "approval_state=not_approved",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "outcome_boundary=not_a_recruiter_response_screen_interview_or_job_probability",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
            "draft_only=true",
        ):
            self.assertIn(required, gate)

        combined_checks = "\n".join(check_rows)
        for required in (
            "check=target_context",
            "check=candidate_evidence",
            "check=message_friction",
            "status=pass",
            "status=revise",
            "evidence_required=",
            "observed_state=",
            "risk=",
            "required_fix=",
            "acceptance_test=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
        ):
            self.assertIn(required, combined_checks)
        self.assertNotRegex(
            "\n".join((gate, combined_checks)).lower(),
            r"\b(?:spray|blast|mass message|bulk send|scrape|automated connection|message sent|connection sent|connect clicked|send now|send_message|current opening|open role|strong fit|great fit|perfect fit|eligible|authorized to work|meet at|available at|schedule|book|guarantee[sd]?|will get an interview|secure screen|approved to send|authorized to send)\b",
        )

    def assert_first_interview_7_day_plan_is_safe(self, networking_drafts: str) -> None:
        plan_rows = [
            row
            for row in networking_drafts.splitlines()
            if "first_interview_7_day_plan=" in row
        ]
        day_rows = [
            row
            for row in networking_drafts.splitlines()
            if "interview_plan_day=" in row
        ]
        ladder_rows = [
            row
            for row in networking_drafts.splitlines()
            if "first_interview_decision_ladder=" in row
        ]
        review_log_rows = [
            row
            for row in networking_drafts.splitlines()
            if "first_interview_daily_review_log=" in row
        ]
        self.assertEqual(1, len(plan_rows))
        self.assertEqual(4, len(ladder_rows))
        self.assertEqual(7, len(day_rows))
        self.assertEqual(7, len(review_log_rows))
        plan = plan_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "first_interview_7_day_plan=",
            "source_outreach_lab_id=RTS-JENKINS-001",
            "plan_goal=earn_or_clarify_first_recruiter_screen_path_without_overclaiming",
            "weekly_time_budget=",
            "priority_sequence=profile_proof_then_targeted_outreach_then_reply_triage",
            "measurement_events=LI-JENKINS-003,LI-JENKINS-004,LI-JENKINS-006",
            "review_cadence=daily_candidate_review",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, plan)

        combined_ladder = "\n".join(ladder_rows)
        for branch in ("advance", "clarify", "pause", "stop"):
            self.assertIn(f"branch={branch}", combined_ladder)
        for required in (
            "first_interview_decision_ladder=weekly_signal_branch",
            "trigger_signal=",
            "required_evidence=",
            "next_safe_action=",
            "blocked_action=",
            "measurement_event=",
            "coach_review_question=",
            "candidate_script_boundary=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, combined_ladder)

        combined_days = "\n".join(day_rows)
        for day in range(1, 8):
            self.assertIn(f"day_number={day}", combined_days)
        for required in (
            "daily_goal=",
            "candidate_action=",
            "evidence_or_asset=",
            "draft_or_review_artifact=",
            "coach_review_checkpoint=",
            "success_metric=",
            "fallback_if_no_signal=",
            "stop_condition=",
            "measurement_event=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, combined_days)
        self.assertIn("candidate_action=review_top_outreach_variant", combined_days)
        self.assertIn("candidate_action=prepare_fact_checked_screen_summary", combined_days)
        self.assertRegex(combined_days, r"measurement_event=LI-JENKINS-00[346]")
        combined_review_logs = "\n".join(review_log_rows)
        for day in range(1, 8):
            self.assertIn(f"day_number={day}", combined_review_logs)
        for required in (
            "first_interview_daily_review_log=observed_signal_review",
            "planned_action_ref=",
            "observed_signal=",
            "signal_quality=",
            "decision=",
            "evidence_logged=",
            "next_safe_action=",
            "metric_to_update=",
            "confounder_to_note=",
            "coach_question=",
            "causality_boundary=observation_not_proof_of_outcome",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
        ):
            self.assertIn(required, combined_review_logs)
        for decision in ("continue", "clarify", "pause", "stop"):
            self.assertIn(f"decision={decision}", combined_review_logs)
        for signal_quality in ("none", "weak", "useful", "blocked"):
            self.assertIn(f"signal_quality={signal_quality}", combined_review_logs)
        self.assertNotRegex(
            "\n".join((plan, combined_ladder, combined_days, combined_review_logs)).lower(),
            r"\b(?:guarantee[sd]?|will get an interview|spray|blast|mass message|bulk send|scrape|automated connection|message sent|connection sent|connect clicked|send now|calendar slot|calendar invite|meet at|available at|approved to send|authorized to send|strong fit|perfect fit)\b",
        )

    def assert_recruiter_first_interview_playbook_is_safe(self, networking_drafts: str) -> None:
        playbook_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_first_interview_playbook=" in row
        ]
        self.assertEqual(1, len(playbook_rows))
        playbook = playbook_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_first_interview_playbook=",
            "first_interview_goal=",
            "conversation_objective=",
            "qualification_question=",
            "thirty_second_opener=",
            "proof_story_bank=",
            "questions_to_ask=",
            "objection_bridge_sequence=",
            "screening_readiness_check=",
            "claim_boundaries=",
            "proof_packet=",
            "advance_the_process_ask=",
            "reply_to_screen_handoff=",
            "follow_up_window=",
            "measure_next=",
            "tracking_event=",
            "compensation_boundary=",
            "eligibility_boundary=",
            "close_script=",
            "stop_condition=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
        ):
            self.assertIn(required, playbook)
        self.assertNotRegex(
            playbook.lower(),
            r"\b(?:guarantee[sd]?|will get hired|will get an interview|calendar|meet at|available at|approved to send|authorized to send|current opening|open role|strong fit|great fit|perfect fit|coffee chat|pick your brain)\b",
        )
        self.assertIn("if_scope_mismatch", playbook)
        self.assertIn("if_unverified_technology", playbook)
        self.assertIn("if_compensation_or_eligibility_arises", playbook)
        self.assertIn("permission_to_prepare_screen_brief", playbook)
        self.assertRegex(playbook, r"\b(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)\b")

    def assert_recruiter_screen_brief_packet_is_safe(self, networking_drafts: str) -> None:
        packet_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_screen_brief_packet=" in row
        ]
        self.assertEqual(1, len(packet_rows))
        packet = packet_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_screen_brief_packet=",
            "trigger_event_id=LI-JENKINS-004",
            "source_triage_id=LI-JENKINS-004",
            "recruiter_target=",
            "recruiter_context_source=",
            "role_or_vacancy_id=",
            "vacancy_source_date=",
            "stated_stage=recruiter_screen",
            "stated_constraints=",
            "target_theme=",
            "supported_fact_ids=",
            "proof_story_ids=",
            "screen_brief_subject=",
            "screen_brief_body=",
            "screen_readiness_scorecard=screen_path_decision_before_prepare_role_interviews_handoff",
            "screen_readiness_decision=clarify_first",
            "evidence_confidence=medium",
            "readiness_blockers=",
            "clarification_gaps=",
            "handoff_trigger=prepare-role-interviews_after_recruiter_or_candidate_confirms_stage_role_constraints_and_missing_screen_questions",
            "handoff_allowed=false",
            "answer_ready_claims=",
            "claim_boundaries=",
            "open_questions=",
            "availability_state=do_not_offer_times_without_exact_authorization",
            "compensation_boundary=",
            "eligibility_boundary=",
            "public_proof_assets=none_until_confidentiality_review",
            "confidentiality_review_state=",
            "handoff_module=prepare-role-interviews",
            "tracking_event=LI-JENKINS-006",
            "next_safe_action=prepare_screen_brief_then_prepare-role-interviews",
            "stop_condition=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, packet)
        self.assertRegex(packet, r"supported_fact_ids=.*(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)")
        self.assertRegex(packet, r"proof_story_ids=.*(?:cluster_troubleshooting_story|automation_story)")
        self.assertRegex(packet, r"readiness_blockers=.*(?:eligibility|availability|compensation|work_authorization|Jenkins_scope|current_vacancy_source)")
        self.assertRegex(packet, r"clarification_gaps=.*(?:current_vacancy_source|Jenkins_scope|work_authorization)")
        self.assertRegex(packet, r"handoff_trigger=.*prepare-role-interviews")
        self.assertRegex(packet, r"claim_boundaries=.*(?:no_unverified_Jenkins|no_production_claim|no_eligibility_claim)")
        self.assertRegex(packet, r"open_questions=.*(?:eligibility|availability|compensation|work_authorization|Jenkins_scope)")
        self.assertNotRegex(
            packet.lower(),
            r"\b(?:message sent|screen scheduled|confirmed for|available at|works for me|i can do|strong fit|perfect fit|jenkins expert|jenkins administrator|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
        )

    def assert_first_screen_conversion_gate_is_safe(self, networking_drafts: str) -> None:
        gate_rows = [
            row
            for row in networking_drafts.splitlines()
            if "first_screen_conversion_gate=" in row
        ]
        check_rows = [
            row
            for row in networking_drafts.splitlines()
            if "first_screen_conversion_check=" in row
        ]
        self.assertEqual(1, len(gate_rows))
        self.assertEqual(4, len(check_rows))
        gate = gate_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "first_screen_conversion_gate=pre_screen_path_decision_gate",
            "source_artifacts=recruiter_conversation_bridge,recruiter_reply_triage,recruiter_screen_brief_packet",
            "gate_goal=decide_safe_next_step_toward_recruiter_screen_without_external_action",
            "target_context_state=",
            "target_context_required=",
            "proof_packet_state=",
            "proof_packet=",
            "low_friction_next_ask=",
            "readiness_decision=clarify_first",
            "readiness_blockers=",
            "screen_path_decision=clarify_before_prepare-role-interviews_handoff",
            "next_safe_action=clarify_context_before_reply",
            "measurement_event=LI-JENKINS-006",
            "conversion_signal=screen_scope_clarified_or_process_constraints_named",
            "stop_condition=",
            "candidate_review_required=true",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, gate)
        self.assertRegex(gate, r"readiness_blockers=.*(?:role_scope|Jenkins_scope|work_authorization)")
        self.assertRegex(gate, r"proof_packet=.*(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)")
        self.assertRegex(gate, r"low_friction_next_ask=.*(?:share|which|useful)")
        combined_checks = "\n".join(check_rows)
        for check in ("target_context", "proof_packet", "low_friction_ask", "screen_readiness"):
            self.assertIn(f"check={check}", combined_checks)
        for required in (
            "first_screen_conversion_check=screen_gate_checkpoint",
            "status=",
            "requirement=",
            "evidence_state=",
            "blocker=",
            "candidate_action=",
            "acceptance_test=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
        ):
            self.assertIn(required, combined_checks)
        self.assertIn("status=pass", combined_checks)
        self.assertIn("status=clarify", combined_checks)
        self.assertIn("blocker=none", combined_checks)
        self.assertNotRegex(
            "\n".join((gate, combined_checks)).lower(),
            r"\b(?:message sent|screen scheduled|confirmed for|available at|works for me|i can do|strong fit|perfect fit|jenkins expert|jenkins administrator|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
        )

    def assert_first_screen_prep_packet_is_coach_grade(self, networking_drafts: str) -> None:
        prep_rows = [
            row
            for row in networking_drafts.splitlines()
            if "first_screen_prep_packet=" in row
        ]
        self.assertEqual(1, len(prep_rows))
        prep = prep_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "first_screen_prep_packet=",
            "source_screen_packet_id=LI-JENKINS-006",
            "prep_decision=clarify_first",
            "prep_scope=recruiter_screen_not_technical_interview",
            "recruiter_target=",
            "target_theme=",
            "opening_script=",
            "story_bank=",
            "proof_points_to_use=",
            "proof_points_to_avoid=",
            "questions_to_recruiter=",
            "salary_script=",
            "eligibility_script=",
            "jenkins_bridge=",
            "risk_flags=",
            "success_criteria=",
            "practice_drill=",
            "follow_up_draft=",
            "handoff_module=prepare-role-interviews",
            "handoff_allowed=false",
            "candidate_review_required=true",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_message_action=true",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, prep)
        self.assertRegex(prep, r"story_bank=.*(?:cluster_troubleshooting_story|automation_story)")
        self.assertRegex(prep, r"proof_points_to_use=.*(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)")
        self.assertRegex(prep, r"proof_points_to_avoid=.*(?:unverified_Jenkins|production|eligibility|compensation)")
        self.assertRegex(prep, r"questions_to_recruiter=.*(?:role_scope|screening_process|work_authorization|Jenkins_scope)")
        self.assertRegex(prep, r"risk_flags=.*(?:overclaim|confidentiality|calendar|unsupported)")
        self.assertNotRegex(
            prep.lower(),
            r"\b(?:message sent|screen scheduled|confirmed for|available at|works for me|i can do|strong fit|perfect fit|jenkins expert|jenkins administrator|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
        )

    def assert_live_linkedin_evidence_snapshot_is_safe(self, approval_gates: str) -> None:
        snapshot_rows = [
            row
            for row in approval_gates.splitlines()
            if "linkedin_live_evidence_snapshot=" in row
        ]
        intake_rows = [
            row
            for row in approval_gates.splitlines()
            if "linkedin_live_structural_intake=" in row
        ]
        self.assertEqual(1, len(snapshot_rows))
        self.assertEqual(1, len(intake_rows))
        snapshot = snapshot_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_live_evidence_snapshot=",
            "capture_date=",
            "browser_source=Chrome_LinkedIn_visible_profile",
            "source_url_state=redacted_visible_profile_url",
            "inspected_sections=",
            "unavailable_sections=",
            "redaction_boundary=no_raw_profile_text_no_contact_details_no_private_identifiers",
            "evidence_promotion_rule=observed_visible_sections_only_candidate_reported_facts_stay_candidate_reported_until_inspected",
            "browser_action_scope=read_only_no_clicks_no_messages_no_profile_edits",
            "consent=read_only_inspection_authorized",
            "not_saved_raw_profile=true",
            "next_capture_step=",
            "no_external_action=true",
        ):
            self.assertIn(required, snapshot)
        self.assertRegex(snapshot, r"inspected_sections=.*(?:About|experience|skills|activity)")
        self.assertNotRegex(
            snapshot.lower(),
            r"\b(?:raw_profile_text|email|phone|cookie|session|token|password|profile edited|message sent|connect clicked|scrape|exported contacts)\b",
        )

        intake = intake_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_live_structural_intake=read_only_section_presence_map",
            "capture_source_snapshot=cap-jenkins-structural-001",
            "page_text_bucket=rich_profile_text_visible_not_copied",
            "url_title_policy=redact_full_url_and_profile_name",
            "top_card_state=visible_structural_only",
            "visual_evidence_bucket=profile_photo_likely_visible_banner_not_detected_by_structural_scan",
            "section_presence=topCard:true,about:true,experience:true,skills:true,activity:true,featured:false,certifications:false,education:false,recommendations:false",
            "action_surfaces_seen=edit_background_image,connect,follow",
            "action_surface_policy=observed_not_clicked_no_profile_edit_no_connection_no_follow_no_message",
            "raw_text_policy=no_raw_profile_text_or_exact_headline_about_experience_copied",
            "safe_to_score_sections=top_card,about,experience,skills,activity",
            "not_safe_to_score_sections=banner,Featured,certifications,education,recommendations,analytics,job_preferences",
            "next_capture_step=request_candidate_approved_screenshot_for_visuals_or_manual_confirmation_for_missing_sections",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, intake)
        self.assertNotRegex(
            intake.lower(),
            r"\b(?:https?://www\.linkedin\.com/in/|raw_profile_text|email|phone|cookie|session|token|password|profile edited|message sent|connect clicked|follow clicked|connection sent|scrape|exported contacts)\b",
        )

    def assert_linkedin_publish_readiness_gate_is_safe(self, approval_gates: str) -> None:
        gate_rows = [
            row
            for row in approval_gates.splitlines()
            if "linkedin_publish_readiness_gate=" in row
        ]
        check_rows = [
            row
            for row in approval_gates.splitlines()
            if "linkedin_publish_readiness_check=" in row
        ]
        self.assertEqual(1, len(gate_rows))
        self.assertEqual(6, len(check_rows))
        gate = gate_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "linkedin_publish_readiness_gate=pre_publish_manual_quality_gate",
            "gate_goal=decide_if_linkedin_edits_are_safe_truthful_complete_and_authorized_before_any_public_change",
            "source_artifacts=linkedin_premium_coach_summary,linkedin_before_after_review_card,linkedin_edit_packet,linkedin_claim_proof_prep_packet",
            "overall_publish_decision=not_ready_manual_review_required",
            "blocking_checks=truthfulness,confidentiality,unsupported_claims,authorization",
            "allowed_next_step=private_candidate_review_only",
            "required_authorization=exact_action_and_target_after_final_copy_review",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, gate)
        combined = "\n".join(check_rows)
        for check in (
            "truthfulness",
            "confidentiality",
            "unsupported_claims",
            "evidence_completeness",
            "readability",
            "authorization",
        ):
            self.assertIn(f"check={check}", combined)
        for required in (
            "linkedin_publish_readiness_check=pre_publish_quality_check",
            "status=",
            "requirement=",
            "evidence_state=",
            "blocker=",
            "candidate_action=",
            "acceptance_test=",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, combined)
        self.assertIn("status=block", combined)
        self.assertIn("status=revise", combined)
        self.assertIn("status=pass", combined)
        self.assertRegex(combined, r"blocker=.*(?:Jenkins|production|metrics|confidentiality|authorization)")
        self.assertNotRegex(
            "\n".join((gate, combined)).lower(),
            r"\b(?:profile edited|published|message sent|connection sent|approved to send|authorized to send|guarantee[sd]?|will get|rank higher|algorithm|recruiter response|interview probability)\b",
        )

    def assert_linkedin_edit_packet_is_coach_grade(self, rewrites: str) -> None:
        packet_rows = [
            row
            for row in rewrites.splitlines()
            if "linkedin_edit_packet=" in row
        ]
        self.assertGreaterEqual(len(packet_rows), 4)
        combined = "\n".join(packet_rows)
        for required in (
            "candidate_id=JSC-CASE-12",
            "evidence_id=",
            "section=headline",
            "section=about",
            "section=experience",
            "section=skills",
            "before_state=",
            "after_state=",
            "section_action=",
            "publish_readiness=",
            "risk_note=",
            "confirm_or_omit=",
            "publish_checklist=",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "draft_only=true",
            "consent=not_granted",
        ):
            self.assertIn(required, combined)
        self.assertRegex(combined, r"section=headline.*Jenkins")
        self.assertRegex(combined, r"section=about.*Jenkins")
        self.assertRegex(combined, r"publish_readiness=(?:not_ready|needs_confirmation)")
        self.assertIn("before_state=unknown_or_generic", combined)
        self.assertIn("after_state=copy_ready_without_unconfirmed_Jenkins", combined)
        self.assertNotRegex(
            combined.lower(),
            r"\b(?:publish_readiness=ready|profile edited|jenkins expert|jenkins administrator|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
        )

    def assert_linkedin_evidence_to_copy_decisions_are_coach_grade(self, rewrites: str) -> None:
        decision_rows = [
            row
            for row in rewrites.splitlines()
            if "linkedin_evidence_to_copy_decision=" in row
        ]
        self.assertEqual(
            5,
            len(decision_rows),
            "Expected five evidence-to-copy decision rows for headline, about, experience, skills, and featured.",
        )
        combined = "\n".join(decision_rows)
        for required in (
            "section=headline",
            "section=about",
            "section=experience",
            "section=skills",
            "section=featured",
            "copy_decision=use",
            "copy_decision=confirm",
            "copy_decision=omit",
            "source_score_dimension=",
            "evidence_status=",
            "candidate_fact_ids=",
            "copy_move=",
            "public_copy_boundary=",
            "missing_proof_question=",
            "ready_copy_fragment=",
            "do_not_write=",
            "coach_reason=",
            "publish_gate=manual_candidate_review_and_exact_action_target_authorization",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, combined)
        self.assertIn("candidate_fact_ids=KUBERNETES_REPORTED,CI_CD_AUTOMATION_REPORTED", combined)
        self.assertIn("ready_copy_fragment=Platform Reliability Engineer", combined)
        self.assertIn("do_not_write=Jenkins specialist", combined)
        self.assertIn(
            "missing_proof_question=What public safe metric or scope proof can support this section",
            combined,
        )
        self.assertNotRegex(
            combined.lower(),
            r"\b(?:guarantee|will get|rank higher|algorithm|recruiter response|interview probability|publish now|message recruiters)\b",
        )

    def assert_linkedin_before_after_review_cards_are_coach_grade(self, rewrites: str) -> None:
        card_rows = [
            row
            for row in rewrites.splitlines()
            if "linkedin_before_after_review_card=" in row
        ]
        self.assertEqual(
            4,
            len(card_rows),
            "Expected four before/after review cards for headline, about, experience, and skills.",
        )
        combined = "\n".join(card_rows)
        for required in (
            "linkedin_before_after_review_card=coach_edit_review_card",
            "section=headline",
            "section=about",
            "section=experience",
            "section=skills",
            "current_problem=",
            "proposed_after_state=",
            "why_this_is_better=",
            "evidence_used=",
            "evidence_still_missing=",
            "candidate_review_question=",
            "acceptance_test=",
            "do_not_publish_if=",
            "review_owner=candidate_with_coach_review",
            "publish_gate=exact_action_and_target_authorization_after_manual_review",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, combined)
        self.assertIn("proposed_after_state=Platform Reliability Engineer for Kubernetes CI CD automation", combined)
        self.assertIn("do_not_publish_if=Jenkins scope production ownership metrics or confidentiality safety are still unconfirmed", combined)
        for row in card_rows:
            self.assertRegex(row, r"section=(?:headline|about|experience|skills)")
            self.assertRegex(row, r"candidate_review_question=[^;]{35,}")
            self.assertRegex(row, r"acceptance_test=[^;]{45,}")
            self.assertNotRegex(
                row.lower(),
                r"\b(?:guarantee|will get|rank higher|algorithm|recruiter response|interview probability|publish now|message recruiters|profile edited|authorized to send)\b",
            )

    def assert_linkedin_publish_qa_checklist_is_safe(self, rewrites: str) -> None:
        qa_rows = [
            row
            for row in rewrites.splitlines()
            if "linkedin_publish_qa_checklist=" in row
        ]
        self.assertEqual(
            4,
            len(qa_rows),
            "Expected four publish QA checklist rows for headline, about, experience, and skills.",
        )
        combined = "\n".join(qa_rows)
        for required in (
            "linkedin_publish_qa_checklist=pre_publication_section_review",
            "section=headline",
            "section=about",
            "section=experience",
            "section=skills",
            "truth_check=",
            "evidence_check=",
            "confidentiality_check=",
            "authorization_check=exact_action_and_target_authorization_missing",
            "readability_check=",
            "candidate_manual_review=",
            "qa_status=pass",
            "qa_status=revise",
            "qa_status=block",
            "blocker=",
            "next_safe_action=",
            "publish_gate=do_not_publish_until_all_checks_pass_and_exact_action_target_authorization",
            "no_external_action=true",
            "draft_only=true",
        ):
            self.assertIn(required, combined)
        self.assertIn(
            "blocker=unconfirmed_Jenkins_scope_or_production_ownership_or_metrics_or_confidentiality",
            combined,
        )
        for row in qa_rows:
            self.assertRegex(row, r"section=(?:headline|about|experience|skills)")
            self.assertRegex(row, r"qa_status=(?:pass|revise|block)")
            self.assertRegex(row, r"truth_check=[^;]{30,}")
            self.assertRegex(row, r"evidence_check=[^;]{30,}")
            self.assertRegex(row, r"confidentiality_check=[^;]{30,}")
            self.assertRegex(row, r"readability_check=[^;]{30,}")
            self.assertRegex(row, r"candidate_manual_review=[^;]{30,}")
            self.assertNotRegex(
                row.lower(),
                r"\b(?:profile edited|published|upload now|publish now|message recruiters|connection sent|approved to send|authorized to send|guarantee|will get|rank higher|algorithm|recruiter response|interview probability)\b",
            )

    def assert_recruiter_reply_triage_is_safe(self, networking_drafts: str) -> None:
        triage_rows = [
            row
            for row in networking_drafts.splitlines()
            if "recruiter_reply_triage=" in row
        ]
        self.assertEqual(1, len(triage_rows))
        triage = triage_rows[0]
        for required in (
            "candidate_id=JSC-CASE-12",
            "recruiter_reply_triage=",
            "reply_event_id=LI-JENKINS-004",
            "recruiter_context_source=",
            "reply_date=",
            "role_or_vacancy_id=",
            "vacancy_source_date=",
            "reply_classification=screen_invite",
            "stated_stage=recruiter_screen",
            "stated_constraints=",
            "candidate_fact_ids=",
            "unknowns=",
            "screen_readiness_decision=clarify_first",
            "safe_draft_response=",
            "proposed_time_state=do_not_accept_or_propose_time_without_exact_authorization",
            "next_safe_action=draft_only_clarification_then_prepare-role-interviews",
            "handoff_module=prepare-role-interviews",
            "stop_condition=",
            "draft_only=true",
            "consent=not_granted",
            "authorization_gate=exact_action_and_target_immediately_before_execution",
            "no_calendar_action=true",
            "causality_boundary=descriptive_only_no_guaranteed_outcome",
        ):
            self.assertIn(required, triage)
        self.assertRegex(triage, r"candidate_fact_ids=.*(?:CI_CD_AUTOMATION_REPORTED|KUBERNETES_REPORTED)")
        self.assertRegex(triage, r"unknowns=.*(?:eligibility|availability|compensation|work_authorization)")
        self.assertNotRegex(
            triage.lower(),
            r"\b(?:calendar event created|screen scheduled|accepted time|confirmed for|message sent|approved to send|authorized to send|strong fit|perfect fit|guarantee[sd]?|will get an interview)\b",
        )

class DiscoverHighValueCareerPathsContractTests(unittest.TestCase):
    def test_path_discovery_requires_comparable_market_evidence_and_safe_scoring(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "explore-career-options"
        )
        skill_path = skill_root / "SKILL.md"
        agent_path = skill_root / "agents" / "openai.yaml"
        reference_path = skill_root / "references" / "path-scoring.md"

        self.assertTrue(skill_path.is_file(), f"Missing skill: {skill_path}")
        text = skill_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "explore-career-options")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("Use when...", metadata["description"])
        self.assertNotIn("workflow", metadata["description"].lower())

        self.assertTrue(agent_path.is_file(), f"Missing UI metadata: {agent_path}")
        agent = agent_path.read_text(encoding="utf-8")
        self.assertIn('display_name: "Explore Career Options"', agent)
        self.assertIn('short_description: "Compare realistic career paths safely"', agent)
        self.assertIn('default_prompt: "Use $explore-career-options', agent)

        self.assertTrue(reference_path.is_file(), f"Missing reference: {reference_path}")
        reference = reference_path.read_text(encoding="utf-8")
        self.assertIn("references/path-scoring.md", text)
        for dimension in (
            "compensation",
            "demand",
            "transferability",
            "gap_cost",
            "geography_fit",
            "evidence_confidence",
        ):
            self.assertIn(dimension, text)
            self.assertIn(dimension, reference)

        for prefix in ("verified:", "candidate-reported:", "inferred:", "unknown:"):
            self.assertIn(prefix, text)
            self.assertIn(prefix, reference)
        self.assertIn("optional qualifiers after the colon", text.lower())
        self.assertNotIn("verified/", text)
        self.assertNotIn("unknown/", text)

        for requirement in (
            "source_date",
            "primary-source",
            "research-professional-market",
            "dated, comparable market briefs",
            "low confidence",
            "currency",
            "compensation basis",
            "Mexico employee",
            "Mexico-based international contractor/EOR",
            "US work-authorized employee",
            "remote geography/eligibility",
            "work authorization",
            "English",
            "missing requirements",
            "learning/time/cost uncertainty",
            "single anecdote",
            "highest-paying",
            "offer timing",
            "guaranteed pay increases",
            "conditional/scenario-based",
        ):
            self.assertIn(requirement, text + reference)

        self.assertIn("Do not independently assert current salary, demand, or rankings", text)
        self.assertIn("must not exceed low confidence", text)
        self.assertIn("Do not predict time to offer", text)
        self.assertIn("do not make a current-market final decision", text)


class ResearchTargetJobMarketContractTests(unittest.TestCase):
    def test_market_research_returns_dated_comparable_evidence_without_a_path_decision(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "research-professional-market"
        )
        skill_path = skill_root / "SKILL.md"
        agent_path = skill_root / "agents" / "openai.yaml"
        source_policy_path = skill_root / "references" / "source-policy.md"
        brief_path = skill_root / "references" / "market-brief.md"

        self.assertTrue(skill_path.is_file(), f"Missing skill: {skill_path}")
        text = skill_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "research-professional-market")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("workflow", metadata["description"].lower())

        self.assertTrue(agent_path.is_file(), f"Missing UI metadata: {agent_path}")
        agent = agent_path.read_text(encoding="utf-8")
        self.assertIn('display_name: "Target Job Market Research"', agent)
        self.assertIn('short_description: "Collect dated, comparable job-market evidence"', agent)
        self.assertIn('default_prompt: "Use $research-professional-market', agent)

        self.assertTrue(source_policy_path.is_file(), f"Missing reference: {source_policy_path}")
        self.assertTrue(brief_path.is_file(), f"Missing reference: {brief_path}")
        source_policy = source_policy_path.read_text(encoding="utf-8")
        brief = brief_path.read_text(encoding="utf-8")
        self.assertIn("references/source-policy.md", text)
        self.assertIn("references/market-brief.md", text)

        for field in (
            "role",
            "geography",
            "currency",
            "compensation basis",
            "seniority",
            "source_date",
            "sample_context",
            "range",
            "demand_signals",
            "recurring_requirements",
            "confidence",
        ):
            self.assertIn(field, text + source_policy + brief)

        for prefix in ("verified:", "candidate-reported:", "inferred:", "unknown:"):
            self.assertIn(prefix, text)
        self.assertIn("optional qualifiers after the colon", text.lower())
        self.assertIn("warning", text.lower())
        self.assertIn("not comparable", text.lower())
        self.assertIn("Mexico employee", text + source_policy + brief)
        self.assertIn("US work-authorized employee", text + source_policy + brief)
        self.assertIn("remote", text.lower())
        self.assertIn("employer vacancy", text.lower())
        self.assertIn("government", source_policy.lower())
        self.assertIn("source URL", text + source_policy + brief)
        self.assertIn("current", text.lower())
        self.assertIn("stale", text.lower())
        self.assertIn("single source", text.lower())

        self.assertIn("must not choose the candidate's career path", text)
        self.assertIn("does not recommend or rank career paths", text)
        self.assertIn("explore-career-options", text)

    def test_archived_market_eval_does_not_preserve_unsafe_current_claims(self) -> None:
        evaluation_path = REPO_ROOT / "tests" / "evals" / "with-skill" / "market.md"
        evaluation = evaluation_path.read_text(encoding="utf-8")
        task_five = evaluation.split("## Task 5 with-skill forward evaluation", 1)[1]
        task_five = task_five.split("## Post-review Task 5 forward evaluation", 1)[0]
        task_five = task_five.split("## Superseding fixture-backed run", 1)[0]
        self.assertIn("Status: superseded", task_five)
        brief_entries = [
            line
            for line in task_five.splitlines()
            if line.startswith("- verified: role=Senior DevOps Engineer;")
        ]

        self.assertEqual(len(brief_entries), 4)
        self.assertNotIn("range=MX$950,000–MX$1,540,000 annual base", task_five)
        self.assertNotIn("demand_signals=two current role-matched vacancy observations", task_five)
        self.assertNotIn("recurring_requirements=AWS/cloud", task_five)
        self.assertNotIn("the Mexico range is limited", task_five)

        for entry in brief_entries:
            self.assertIn("range=unknown", entry)

    def test_market_contract_requires_source_state_and_observation_level_compensation(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "research-professional-market"
        )
        contract = "\n".join((
            (skill_root / "SKILL.md").read_text(encoding="utf-8"),
            (skill_root / "references" / "source-policy.md").read_text(encoding="utf-8"),
            (skill_root / "references" / "market-brief.md").read_text(encoding="utf-8"),
        ))

        for requirement in (
            "source_state",
            "compensation_observation",
            "active",
            "stale",
            "expired",
            "unavailable",
            "multiple active compatible observations",
            "cannot support a current range, demand, or recurrence",
            "provider-specific",
            "as_of_date",
            "source_age_days",
            "freshness_window_days",
            "freshness_status",
            "compensation_components",
            "comparable_group_id",
            "comparability_status",
            "component_gaps",
            "employer_or_publisher",
            "source_id",
            "independent_observation_id",
            "comparability_check",
            "range_method",
            "conversion_basis",
        ):
            self.assertIn(requirement, contract)

    def test_post_review_market_snapshot_records_exact_current_source_states(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "market.md").read_text(
            encoding="utf-8"
        )
        snapshot = evaluation.split("## Post-review Task 5 forward evaluation", 1)[1]
        snapshot = snapshot.split("## High-compensation comparability smoke", 1)[0]
        entries = [
            line
            for line in snapshot.splitlines()
            if line.startswith("- verified: role=Senior DevOps Engineer;")
        ]

        self.assertEqual(len(entries), 4)
        peek, restaurant365, element84, luxury_presence = entries
        self.assertIn("source_state=active", peek)
        self.assertIn("compensation_observation=MX$950,000–MX$1,300,000 annual base", peek)
        self.assertIn("range=unknown", peek)
        self.assertIn("demand_signals=one active role-matched vacancy observation", peek)
        self.assertIn("recurring_requirements=unknown", peek)
        self.assertIn("provider-specific AWS/EKS", peek)

        self.assertIn("source_state=unavailable", restaurant365)
        self.assertIn("compensation_observation=MX$1,230,000–MX$1,540,000 annual base (historical)", restaurant365)
        self.assertIn("range=unknown", restaurant365)
        self.assertIn("demand_signals=unknown", restaurant365)
        self.assertIn("recurring_requirements=unknown", restaurant365)
        self.assertIn("HTTP 404", restaurant365)
        self.assertIn("provider-specific Azure/AKS", restaurant365)

        self.assertIn("source_state=active", element84)
        self.assertIn("compensation_observation=unknown", element84)
        self.assertIn("range=unknown", element84)
        self.assertIn("US-person and US-work-authorization required", element84)
        self.assertIn("source_state=active", luxury_presence)
        self.assertIn("compensation_observation=unknown", luxury_presence)
        self.assertIn("range=unknown", luxury_presence)
        self.assertNotIn("MX$950,000–MX$1,540,000", snapshot)

    def test_market_compensation_comparability_smoke_rejects_mixed_high_pay_sources(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "market.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("## High-compensation comparability smoke", evaluation)
        smoke = evaluation.split("## High-compensation comparability smoke", 1)[1]
        smoke = smoke.split("##", 1)[0]
        entries = [
            line
            for line in smoke.splitlines()
            if line.startswith("- verified: role=")
        ]

        self.assertEqual(3, len(entries))
        for entry in entries:
            for field in (
                "as_of_date=2026-08-06",
                "source_age_days=0",
                "freshness_window_days=90",
                "freshness_status=current",
                "compensation_components=",
                "comparable_group_id=",
                "comparability_status=",
                "component_gaps=",
                "employer_or_publisher=",
                "source_id=",
                "independent_observation_id=",
                "comparability_check=",
                "range_method=",
                "range=unknown",
            ):
                self.assertIn(field, entry)

        self.assertIn("comparability_status=compatible_single_observation", entries[0])
        self.assertIn("comparable_group_id=mexico_employee_senior_devops_mxn_annual_base", entries[0])
        self.assertIn("compensation_components=base disclosed; bonus,equity,OTE,benefits unknown", entries[0])
        self.assertIn("comparability_status=incompatible_arrangement_and_components", entries[1])
        self.assertIn("comparable_group_id=us_work_authorized_staff_sre_usd_total_comp", entries[1])
        self.assertIn("compensation_components=total compensation disclosed; base,bonus,equity split unknown", entries[1])
        self.assertIn("comparability_status=incompatible_ote_and_sales_motion", entries[2])
        self.assertIn("comparable_group_id=us_work_authorized_enterprise_ae_usd_ote", entries[2])
        self.assertIn("compensation_components=OTE disclosed; base,commission split,quota basis unknown", entries[2])
        self.assertIn("warning=do not compare annual base, total compensation, and OTE as one current high-pay range", smoke)
        self.assertNotRegex(
            smoke.lower(),
            r"\b(?:highest-paying|best paid|top paying|ranked #?1|current range=\$|current market range=)\b",
        )

    def test_high_value_path_eval_contains_role_opportunity_matrix(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "market.md").read_text(
            encoding="utf-8"
        )
        technical_snapshot = evaluation.split("## Operations evaluator output", 1)[0]
        matrix_rows = [
            line
            for line in technical_snapshot.splitlines()
            if "high_value_role_opportunity_matrix=" in line
        ]

        self.assertEqual(4, len(matrix_rows))
        combined = "\n".join(matrix_rows)
        for required in (
            "candidate_id=",
            "high_value_role_opportunity_matrix=role_opportunity_gate",
            "path=",
            "target_seniority=",
            "candidate_evidence_fit=",
            "transferable_assets=",
            "missing_evidence=",
            "market_evidence_status=",
            "compensation_boundary=",
            "demand_boundary=",
            "geography_or_arrangement_scenarios=",
            "learning_or_certification_gate=",
            "portfolio_or_proof_asset=",
            "research_request=",
            "no_salary_claim=true",
            "draft_only=true",
        ):
            self.assertIn(required, combined)

        for decision in ("prioritize", "research", "defer", "reject"):
            self.assertIn(f"decision={decision}", combined)
        for path in (
            "Senior Platform Engineer/Kubernetes Infrastructure Engineer",
            "Senior DevOps Engineer",
            "OpenShift Platform Engineer_or_Consultant",
            "Staff_or_Principal_SRE_or_AI_Infrastructure_bridge",
        ):
            self.assertIn(path, combined)

        self.assertRegex(combined, r"(?i)research")
        self.assertRegex(combined, r"(?i)(Mexico|US|remote|EOR|contractor|employee)")
        self.assertNotRegex(
            combined.lower(),
            r"\b(?:highest-paying|best paid|top paying|guaranteed|ranked #?1|current market range)\b",
        )


class OptimizeJobSearchAssetsContractTests(unittest.TestCase):
    def test_asset_optimizer_keeps_rewrites_truthful_and_ats_feedback_actionable(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "optimize-career-assets"
        )
        skill_path = skill_root / "SKILL.md"
        agent_path = skill_root / "agents" / "openai.yaml"
        workflow_path = skill_root / "references" / "asset-workflow.md"
        truthfulness_path = skill_root / "references" / "ats-and-truthfulness.md"
        matrix_path = skill_root / "assets" / "candidate-fact-matrix.md"

        self.assertTrue(skill_path.is_file(), f"Missing skill: {skill_path}")
        text = skill_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "optimize-career-assets")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("workflow", metadata["description"].lower())

        self.assertTrue(agent_path.is_file(), f"Missing UI metadata: {agent_path}")
        agent = agent_path.read_text(encoding="utf-8")
        self.assertIn('display_name: "Job Search Asset Optimizer"', agent)
        self.assertIn('short_description: "Draft truthful CV and portfolio assets"', agent)
        self.assertIn('default_prompt: "Use $optimize-career-assets', agent)

        for reference in (workflow_path, truthfulness_path, matrix_path):
            self.assertTrue(reference.is_file(), f"Missing asset: {reference}")
            self.assertIn(str(reference.relative_to(skill_root)), text)

        for prefix in ("verified:", "candidate-reported:", "inferred:", "unknown:"):
            self.assertIn(prefix, text)
        self.assertIn("optional qualifiers after the colon", text.lower())
        self.assertNotIn("verified/", text)
        self.assertNotIn("unknown/", text)

        for section in (
            "fact_matrix",
            "ats_gap_map",
            "master_cv_recommendations",
            "vacancy_tailored_draft",
            "application_packet",
            "portfolio_evidence_plan",
            "consistency_report",
        ):
            self.assertIn(section, text)

        contract = text + workflow_path.read_text(encoding="utf-8") + truthfulness_path.read_text(encoding="utf-8")
        for requirement in (
            "candidate fact ID",
            "recommendation",
            "formatting",
            "terminology",
            "evidence",
            "genuine skill gap",
            "impact-first",
            "invented metrics",
            "Terraform",
            "Argo CD",
            "opaque ATS",
            "LinkedIn",
            "CV",
            "confidentiality",
            "export",
            "candidate_id",
            "target_vacancy_id",
            "matched_evidence",
            "role_requirements",
            "unsupported_or_missing_claims",
            "recruiter_summary",
            "message_angle",
            "first_interview_prep_handoff",
            "tracking_event",
            "approval_gate",
            "draft_only=true",
            "consent=not_granted",
            "causality_boundary=no_outcome_guarantee",
        ):
            self.assertIn(requirement, contract)

        self.assertIn("must not promise an ATS score", contract)
        self.assertIn("must map to a candidate fact ID or be labeled recommendation", contract)
        self.assertIn("without exact action-and-target authorization", text)

    def test_asset_forward_eval_uses_canonical_prefixes_for_recommendations(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "optimize-career-assets"
        )
        contract_files = (skill_root / "SKILL.md", *sorted((skill_root / "references").glob("*.md")))
        for contract_file in contract_files:
            contract_text = contract_file.read_text(encoding="utf-8")
            self.assertNotIn(
                "recommendation:",
                contract_text,
                f"Bare recommendation label in {contract_file.relative_to(REPO_ROOT)}",
            )

        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "assets.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("\nrecommendation:", evaluation)
        self.assertIn("inferred: recommendation=", evaluation)

    def test_portfolio_gate_separates_content_rights_from_execution_authorization(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "optimize-career-assets"
        )
        text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        workflow = (skill_root / "references" / "asset-workflow.md").read_text(
            encoding="utf-8"
        )
        contract = (text + workflow).lower()

        for requirement in (
            "candidate owns",
            "documented rights-holder permission",
            "public disclosure",
            "candidate approval alone",
            "secrets and customer data are always forbidden",
            "even with candidate approval",
            "does not authorize execution",
            "exact action-and-target authorization",
        ):
            self.assertIn(requirement, contract)

        self.assertNotIn("secrets unless", contract)
        self.assertNotIn("customer data unless", contract)

    def test_each_asset_forward_case_has_fact_backed_full_output(self) -> None:
        import re

        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "assets.md").read_text(
            encoding="utf-8"
        )
        cases = (
            (
                "## Technical: Terraform and Argo CD vacancy",
                "fixtures/assets-technical.md",
            ),
            ("## Non-technical", "fixtures/assets-non-technical.md"),
            ("## Junior", "fixtures/assets-junior.md"),
            ("## Career transition", "fixtures/assets-career-transition.md"),
        )
        headings = tuple(heading for heading, _ in cases)
        for index, (heading, fixture_name) in enumerate(cases):
            case = evaluation.split(heading, 1)[1]
            if index + 1 < len(headings):
                case = case.split(headings[index + 1], 1)[0]
            self.assertIn(f"Fixture: `{fixture_name}`", case)
            self.assertIn("### Raw full output", case)
            for section in (
                "fact_matrix",
                "ats_gap_map",
                "master_cv_recommendations",
                "vacancy_tailored_draft",
                "application_packet",
                "portfolio_evidence_plan",
                "consistency_report",
            ):
                self.assertIn(section, case)
            packet = case.split("application_packet", 1)[1].split("portfolio_evidence_plan", 1)[0]
            for field in (
                "candidate_id=",
                "target_vacancy_id=",
                "packet_goal=",
                "vacancy_source_state=",
                "role_requirements=",
                "matched_evidence=",
                "unsupported_or_missing_claims=",
                "cv_bullets=",
                "recruiter_summary=",
                "message_angle=",
                "first_interview_prep_handoff=",
                "tracking_event=",
                "approval_gate=",
                "draft_only=true",
                "consent=not_granted",
                "causality_boundary=no_outcome_guarantee",
            ):
                self.assertIn(field, packet)
            self.assertRegex(packet, r"\bV-[A-Z]+ -> F-\d{3}\b")
            self.assertRegex(packet, r"cv_bullets=.*\[F-\d{3}\]")
            self.assertNotRegex(
                packet.lower(),
                r"\b(?:strong fit|great fit|perfect fit|guarantee[sd]?|will get an interview|approved to send|authorized to send)\b",
            )
            for category in ("formatting=", "terminology=", "evidence=", "genuine skill gap="):
                self.assertIn(category, case)
            self.assertRegex(case, r"candidate-reported: F-\d{3}")
            self.assertRegex(case, r"candidate-reported: \[F-\d{3}\]")

            fixture_path = REPO_ROOT / "tests" / "evals" / "with-skill" / fixture_name
            self.assertTrue(fixture_path.is_file(), f"Missing exact fixture: {fixture_path}")
            fixture = fixture_path.read_text(encoding="utf-8")
            for field in (
                "## Exact prompt",
                "## Exact target vacancy",
                "## Exact candidate facts",
                "## Exact current CV state",
                "## Exact current LinkedIn state",
                "## Exact confidentiality state",
                "## Exact action request",
            ):
                self.assertIn(field, fixture)

            fixture_ids = set(re.findall(r"\bF-\d{3}\b", fixture))
            rewritten_ids = set(re.findall(r"\[?(F-\d{3})\]?", case))
            self.assertTrue(rewritten_ids, f"No rewritten fact IDs in {heading}")
            self.assertEqual(
                set(),
                rewritten_ids - fixture_ids,
                f"Unbacked rewritten fact IDs in {heading}",
            )

    def test_asset_baseline_is_fixture_backed_and_records_the_raw_full_output(self) -> None:
        baseline = (REPO_ROOT / "tests" / "evals" / "baseline" / "assets.md").read_text(
            encoding="utf-8"
        )
        fixture_path = (
            REPO_ROOT
            / "tests"
            / "evals"
            / "baseline"
            / "fixtures"
            / "assets-terraform-argo.md"
        )
        self.assertIn("Fixture: `fixtures/assets-terraform-argo.md`", baseline)
        self.assertIn("## Raw full output", baseline)
        self.assertNotIn("## Fresh response excerpt", baseline)
        self.assertTrue(fixture_path.is_file(), f"Missing exact baseline fixture: {fixture_path}")
        fixture = fixture_path.read_text(encoding="utf-8")
        for field in (
            "## Exact prompt",
            "## Exact target vacancy",
            "## Exact candidate facts",
            "## Exact current CV state",
            "## Exact current LinkedIn state",
            "## Exact confidentiality state",
            "## Exact action request",
        ):
            self.assertIn(field, fixture)
        self.assertIn("source_date=unknown", fixture)
        self.assertIn("source_state=synthetic", fixture)


class PrepareRoleInterviewsContractTests(unittest.TestCase):
    CORE_OUTPUT_SECTIONS = (
        "competency_map",
        "likely_questions",
        "vacancy_question_traceability_matrix",
        "truthful_story_bank",
        "practice_answer_coaching",
        "role_practice",
        "mock_interview",
        "scorecard",
        "interviewer_questions",
        "follow_up_draft",
    )
    REQUIRED_OUTPUT_SECTIONS = CORE_OUTPUT_SECTIONS + (
        "first_interview_conversion_plan",
        "first_screen_prep_packet",
        "recruiter_screen_brief",
        "recruiter_bridge_script",
        "vacancy_candidate_gap_map",
        "objection_response_map",
        "vacancy_requirement_drill_matrix",
        "question_bank",
        "answer_revision_ladder",
        "follow_up_lifecycle",
    )
    CANONICAL_STAGES = (
        "recruiter screen",
        "hiring-manager",
        "technical screen",
        "technical deep dive",
        "take-home",
        "system design",
        "behavioral loop",
        "panel",
        "offer-stage",
    )

    def test_explicit_private_recruiter_practice_routes_without_replacing_linkedin_dossier(self) -> None:
        """Keep the narrow practice artifact separate from normal LinkedIn delivery."""

        skill_root = REPO_ROOT / "plugins" / "professional-growth-coach" / "skills"
        interview_skill = (skill_root / "prepare-role-interviews" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        interview_map = (
            skill_root / "prepare-role-interviews" / "references" / "interview-map.md"
        ).read_text(encoding="utf-8")
        root_skill = (skill_root / "professional-growth-coach" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        routing = (skill_root / "professional-growth-coach" / "references" / "routing.md").read_text(
            encoding="utf-8"
        )
        client_report = (
            skill_root / "optimize-professional-profile" / "references" / "client-report.md"
        ).read_text(encoding="utf-8")
        contract = "\n".join(
            (interview_skill, interview_map, root_skill, routing, client_report)
        )

        for required in (
            "explicit private recruiter-practice request",
            "identity-free vacancy summary",
            "at least one supplied candidate fact",
            "private recruiter practice session",
            "one concise question",
            "one-question/one-answer",
            "unknown before an observed answer",
            "ephemeral",
            "no-save-by-default",
            "No external action",
            "internal identifiers",
            "raw vacancy or candidate-fact text",
        ):
            with self.subTest(required=required):
                self.assertIn(required, contract)

        self.assertIn("`prepare-role-interviews`", routing)
        self.assertIn("private recruiter practice session", root_skill)
        self.assertIn("do not append a `module_execution_packet`", root_skill)
        self.assertIn("normal local LinkedIn artifact", routing)
        self.assertIn("does not use this LinkedIn client report", client_report)

    def test_private_practice_overrides_conflicting_recruiter_debug_and_raw_row_requests(self) -> None:
        """Catch a private rehearsal leaking into recruiter, debug, or internal routes."""

        prompt = (
            "Private recruiter practice for this recruiter screen; debug the raw "
            "internal router and packet rows too. Vacancy: platform role. "
            "Candidate fact: I operated incident reviews."
        )
        root_skill = ROOT_SKILL_PATH.read_text(encoding="utf-8")
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        private_branch = routing.split("## Private recruiter-practice routing", 1)[1].split(
            "\n## ", 1
        )[0]

        self.assertIn("private recruiter practice", prompt.casefold())
        self.assertIn(
            "takes precedence over recruiter-reply triage, every LinkedIn branch, and debug, eval, detail, raw, or internal-row requests",
            private_branch,
        )
        self.assertIn(
            "Explicit private practice wins even with those signals or debug, raw, or internal-row requests",
            root_skill,
        )
        self.assertIn(
            "Explicit private recruiter-reply triage also wins even with those signals or debug, raw, or internal-row requests",
            root_skill,
        )
        self.assertIn(
            "Return them for every non-artifact response; never return them in a normal HTML dossier chat",
            root_skill,
        )
        self.assertIn(
            "Private practice is the exception: emit no router fields there, ready or intake",
            root_skill,
        )
        self.assertIn(
            "do not append a `module_execution_packet`, router rows, or internal identifiers",
            root_skill,
        )

    def test_private_practice_missing_inputs_ask_exactly_one_question_without_router_output(self) -> None:
        """Keep every incomplete private rehearsal on the one-question intake branch."""

        prompts = {
            "missing_vacancy": "Private recruiter practice. Candidate fact: I led an incident review.",
            "missing_fact": "Private recruiter practice. Vacancy: platform operations role.",
            "missing_both": "Private recruiter practice.",
        }
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        private_branch = routing.split("## Private recruiter-practice routing", 1)[1].split(
            "\n## ", 1
        )[0]

        for case, prompt in prompts.items():
            with self.subTest(case=case):
                self.assertIn("private recruiter practice", prompt.casefold())
                self.assertIn("`needs_intake`", private_branch)
                self.assertIn("`authorization_required: false`", private_branch)
                self.assertIn("exactly one concise question", private_branch)
                self.assertIn("both inputs are missing", private_branch)
                self.assertIn("Do not expose internal identifiers, router rows", private_branch)

    def test_private_recruiter_reply_triage_blocks_debug_raw_and_internal_delivery_forms(self) -> None:
        """Prevent root delivery rules from leaking the private triage card or intake."""

        prompts = {
            "ready_debug": (
                "Private recruiter-reply triage; debug the canonical appendix. "
                "Summary: a screen invitation needs role scope. "
                "Candidate fact: I led incident reviews."
            ),
            "ready_raw": (
                "Private recruiter-reply triage; show the raw reply. "
                "Summary: a screen invitation needs role scope. "
                "Candidate fact: I led incident reviews."
            ),
            "ready_internal": (
                "Private recruiter-reply triage; show internal router rows. "
                "Summary: a screen invitation needs role scope. "
                "Candidate fact: I led incident reviews."
            ),
            "intake_debug": "Private recruiter-reply triage; debug the canonical appendix.",
            "intake_raw": "Private recruiter-reply triage; show the raw reply.",
            "intake_internal": "Private recruiter-reply triage; show internal router rows.",
        }
        root_skill = ROOT_SKILL_PATH.read_text(encoding="utf-8")

        for case, prompt in prompts.items():
            with self.subTest(case=case):
                self.assertIn("private recruiter-reply triage", prompt.casefold())
                self.assertRegex(prompt.casefold(), r"debug|raw|internal")

        self.assertIn(
            "only without an explicit private recruiter-practice or private "
            "recruiter-reply triage request",
            root_skill,
        )
        self.assertIn(
            "Private practice and private recruiter-reply triage are the exceptions: "
            "emit no router fields there, ready or intake",
            root_skill,
        )
        self.assertIn(
            "Explicit private recruiter-reply triage also wins even with those signals or debug, raw, or internal-row requests",
            root_skill,
        )
        self.assertIn(
            "private recruiter-practice and private recruiter-reply triage branches above",
            root_skill,
        )
        self.assertIn(
            "private recruiter-practice and private recruiter-reply triage branches",
            root_skill,
        )
        self.assertLessEqual(len(root_skill), 16000)

    def test_private_recruiter_reply_triage_ready_route_has_no_execution_packet(self) -> None:
        """Keep the routing reference aligned with the private triage packet gate."""

        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        ready_execution = routing.split("## Ready module execution", 1)[1].split(
            "\n## ", 1
        )[0]
        self.assertIn(
            "For the explicit private recruiter-practice or private recruiter-reply triage branches",
            ready_execution,
        )
        self.assertIn(
            "do not emit a router contract, `module_execution_packet`, or internal identifiers",
            ready_execution,
        )

    def test_nonprivate_recruiter_and_dossier_requests_keep_legacy_routing(self) -> None:
        """Limit the privacy override to an explicit private-practice request."""

        normal_dossier_prompt = (
            "Review my LinkedIn profile for a recruiter screen invitation in debug mode."
        )
        root_skill = ROOT_SKILL_PATH.read_text(encoding="utf-8")
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        private_branch = routing.split("## Private recruiter-practice routing", 1)[1].split(
            "\n## ", 1
        )[0]

        self.assertNotIn("private recruiter practice", normal_dossier_prompt.casefold())
        self.assertIn(
            "When an explicit private recruiter-practice request is absent, retain the existing recruiter-reply triage and LinkedIn delivery behavior, including debug, eval, and detail_requested legacy output.",
            private_branch,
        )
        self.assertIn("route first to `optimize-professional-profile`", root_skill)
        self.assertIn("`debug | eval | detail_requested`", root_skill)

    def test_interview_preparation_is_vacancy_specific_and_truthful(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "prepare-role-interviews"
        )
        skill_path = skill_root / "SKILL.md"
        agent_path = skill_root / "agents" / "openai.yaml"
        map_path = skill_root / "references" / "interview-map.md"
        rubric_path = skill_root / "references" / "evaluation-rubrics.md"
        scorecard_path = skill_root / "assets" / "mock-interview-scorecard.md"

        self.assertTrue(skill_path.is_file(), f"Missing skill: {skill_path}")
        text = skill_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "prepare-role-interviews")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("workflow", metadata["description"].lower())

        self.assertTrue(agent_path.is_file(), f"Missing UI metadata: {agent_path}")
        agent = agent_path.read_text(encoding="utf-8")
        self.assertIn('display_name: "Role Interview Preparation"', agent)
        self.assertIn('short_description: "Prepare truthful, vacancy-specific interviews"', agent)
        self.assertIn('default_prompt: "Use $prepare-role-interviews', agent)

        for reference in (map_path, rubric_path, scorecard_path):
            self.assertTrue(reference.is_file(), f"Missing reference: {reference}")
            self.assertIn(str(reference.relative_to(skill_root)), text)

        for prefix in ("verified:", "candidate-reported:", "inferred:", "unknown:"):
            self.assertIn(prefix, text)
        self.assertIn("optional qualifiers after the colon", text.lower())
        self.assertNotIn("verified/", text)
        self.assertNotIn("unknown/", text)

        for section in (
            "competency_map",
            "likely_questions",
            "vacancy_question_traceability_matrix",
            "truthful_story_bank",
            "practice_answer_coaching",
            "role_practice",
            "mock_interview",
            "scorecard",
            "interviewer_questions",
            "follow_up_draft",
        ):
            self.assertIn(section, text)

        contract = "\n".join((
            text,
            map_path.read_text(encoding="utf-8"),
            rubric_path.read_text(encoding="utf-8"),
            scorecard_path.read_text(encoding="utf-8"),
        ))
        for requirement in (
            "vacancy requirement ID",
            "question ID",
            "rationale",
            "candidate fact ID",
            "explicit unknowns",
            "weighted scorecard",
            "weight",
            "recruiter screen",
            "hiring-manager",
            "technical deep dive",
            "system design",
            "behavioral loop",
            "offer-stage",
            "not applicable",
            "company evidence",
            "source_date",
            "source_state",
            "synthetic",
            "company process",
            "do not invent",
            "question_text",
            "vacancy_question_traceability_matrix",
            "vacancy_signal",
            "candidate_evidence_state",
            "gap_or_risk",
            "expected_recruiter_signal",
            "practice_acceptance_test",
            "generic_advice_boundary=not_generic",
            "mock_question",
            "STAR=",
            "answer_arc",
            "opening_sentence",
            "proof_beats",
            "gap_bridge",
            "candidate_confirmation_needed",
            "red_line_phrases",
            "practice_drill",
            "coach_revision_prompt",
            "subject=",
            "body=",
            "follow-up draft",
            "do not send",
            "first_interview_conversion_plan",
            "first_screen_prep_packet",
            "screen_objective",
            "sixty_second_opener",
            "story_menu",
            "objection_responses",
            "recruiter_questions",
            "close_and_next_step",
            "post_screen_follow_up_boundary",
            "conversion_goal",
            "role_fit_thesis",
            "three_proof_points",
            "screening_risks",
            "next_state",
            "next_safe_action",
            "recruiter_bridge_script",
            "opening_claim",
            "scope_caveat",
            "risk_bridge",
            "thirty_second_pitch",
            "objection_bridge_sequence",
            "recruiter_qualification_questions",
            "advance_the_process_ask",
            "screen_success_criteria",
            "stop_condition",
            "red_line_claims",
        ):
            self.assertIn(requirement, contract)

        for required in (
            "recruiter_screen_brief",
            "vacancy_candidate_gap_map",
            "objection_response_map",
            "question_bank",
            "follow_up_lifecycle",
            "technical screen",
            "take-home",
            "panel",
            "recipient",
            "event reference",
        ):
            self.assertIn(required, contract)

        recruiter_screen_map = map_path.read_text(encoding="utf-8")
        self.assertIn(
            "`candidate-reported:` opening pitch, why-now/why-this-role, scope, logistics, compensation handling, and location/work authorization/notice period confirmation when candidate-supported",
            recruiter_screen_map,
        )
        self.assertIn("`inferred:` recruiter questions and safe close", recruiter_screen_map)
        self.assertNotIn(
            "`candidate-reported:` opening pitch, why-now/why-this-role, scope, logistics, compensation handling, location/work authorization/notice period confirmation, recruiter questions, and safe close",
            recruiter_screen_map,
        )

        scorecard_rows = [
            line
            for line in scorecard_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("| Q-### |")
        ]
        self.assertEqual(len(scorecard_rows), 5)
        self.assertEqual(sum(int(row.split("|")[4].strip()) for row in scorecard_rows), 100)
        self.assertTrue(all("unknown:" in row for row in scorecard_rows))
        self.assertIn(
            "redistribute only the 10 available points from Questions and judgment",
            rubric_path.read_text(encoding="utf-8"),
        )

    def test_interview_forward_eval_covers_stages_with_traceable_answers(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "interviews.md").read_text(
            encoding="utf-8"
        )
        stages = (
            "### Recruiter screen",
            "### Hiring-manager interview",
            "### Technical deep dive",
            "### System design",
            "### Behavioral loop",
            "### Offer-stage questions",
        )

        fixture_path = (
            REPO_ROOT
            / "tests"
            / "evals"
            / "with-skill"
            / "fixtures"
            / "interviews-principal-sre.md"
        )
        self.assertIn("Fixture: `fixtures/interviews-principal-sre.md`", evaluation)
        self.assertTrue(fixture_path.is_file(), f"Missing exact fixture: {fixture_path}")
        fixture = fixture_path.read_text(encoding="utf-8")
        for field in (
            "## Exact prompt",
            "## Exact target vacancy",
            "## Exact company evidence",
            "## Exact candidate facts",
            "## Exact parameterized stage requests",
            "## Exact action request",
        ):
            self.assertIn(field, fixture)
        self.assertIn("source_date=unknown", fixture)
        self.assertIn("source_state=synthetic", fixture)

        fixture_requirement_ids = set(re.findall(r"\bV-\d{3}\b", fixture))
        fixture_fact_ids = set(re.findall(r"\bF-\d{3}\b", fixture))
        self.assertEqual(
            fixture_requirement_ids,
            {"V-701", "V-702", "V-703", "V-704", "V-705", "V-706", "V-707"},
        )
        self.assertEqual(
            fixture_fact_ids,
            {"F-001", "F-002", "F-003", "F-004", "F-005", "F-006", "F-007"},
        )

        stage_names = (
            "recruiter screen",
            "hiring-manager",
            "technical deep dive",
            "system design",
            "behavioral loop",
            "offer-stage",
        )
        requested_by_heading = dict(zip(stages, stage_names))

        for index, heading in enumerate(stages):
            self.assertIn(heading, evaluation)
            stage = evaluation.split(heading, 1)[1]
            if index + 1 < len(stages):
                stage = stage.split(stages[index + 1], 1)[0]
            else:
                stage = stage.split("## Enterprise Account Executive fixture", 1)[0]

            expected_sections = (
                self.REQUIRED_OUTPUT_SECTIONS
                if heading == "### Recruiter screen"
                else self.CORE_OUTPUT_SECTIONS
            )
            sections = extract_ordered_sections(stage, expected_sections)
            for section_name in self.CORE_OUTPUT_SECTIONS:
                value = sections[section_name]
                self.assertRegex(
                    value,
                    r"^(?:verified|candidate-reported|inferred|unknown):",
                    f"Non-canonical evidence prefix in {heading} {section_name}",
                )

            likely_questions = sections["likely_questions"]
            question_id = re.search(r"question ID=(Q-\d{3})", likely_questions).group(1)
            requirement_id = re.search(
                r"vacancy requirement ID=(V-\d{3})", likely_questions
            ).group(1)
            self.assertIn("rationale=", likely_questions)
            self.assertRegex(likely_questions, r"answer facts=\[F-\d{3}")
            question_text = re.search(r'question_text="([^"]+\?)"', likely_questions)
            self.assertIsNotNone(question_text, f"Missing actual question text in {heading}")

            traceability = sections["vacancy_question_traceability_matrix"]
            self.assertIn(f"question ID={question_id}", traceability)
            self.assertIn(f"vacancy requirement ID={requirement_id}", traceability)
            for field in (
                "candidate fact IDs=",
                "vacancy_signal=",
                "candidate_evidence_state=",
                "gap_or_risk=",
                "expected_recruiter_signal=",
                "practice_acceptance_test=",
                "generic_advice_boundary=not_generic",
            ):
                self.assertIn(field, traceability)
            self.assertRegex(traceability, r"\bF-\d{3}\b")
            self.assertNotRegex(
                traceability,
                r"\b(?:common question|be confident|great fit|make it stronger|standard answer)\b",
            )

            story_bank = sections["truthful_story_bank"]
            self.assertRegex(story_bank, r"candidate-reported: \[F-\d{3}\]")
            self.assertIn("unknown:", story_bank)
            self.assertIn("STAR=", story_bank)

            coaching = sections["practice_answer_coaching"]
            self.assertRegex(
                coaching,
                r"^(?:verified|candidate-reported|inferred|unknown):",
                f"Non-canonical evidence prefix in {heading} practice_answer_coaching",
            )
            self.assertIn(f"question ID={question_id}", coaching)
            self.assertIn(f"vacancy requirement ID={requirement_id}", coaching)
            for field in (
                "answer_arc=",
                "opening_sentence=",
                "proof_beats=",
                "gap_bridge=",
                "candidate_confirmation_needed=",
                "red_line_phrases=",
                "practice_drill=",
                "coach_revision_prompt=",
            ):
                self.assertIn(field, coaching)
            self.assertRegex(coaching, r"\bF-\d{3}\b")
            self.assertIn("wait", coaching.lower())

            role_practice = sections["role_practice"]
            requested_stage = requested_by_heading[heading]
            self.assertIn(f"{requested_stage}=requested", role_practice)
            for other_stage in set(self.CANONICAL_STAGES) - {requested_stage}:
                self.assertRegex(
                    role_practice,
                    rf"{re.escape(other_stage)}=not applicable because [^;]+",
                    f"Missing reasoned exclusion for {other_stage} in {heading}",
                )

            mock = sections["mock_interview"]
            self.assertIn(f"question ID={question_id}", mock)
            self.assertIn(f"vacancy requirement ID={requirement_id}", mock)
            self.assertIn(f'mock_question="{question_text.group(1)}"', mock)
            self.assertIn("wait for the candidate response", mock)

            scorecard = sections["scorecard"]
            expected_scorecard_rows = (
                ("Requirement relevance", 30),
                ("Fact grounding", 25),
                ("Reasoning and tradeoffs", 20),
                ("Communication", 15),
                ("Questions and judgment", 10),
            )
            for criterion, weight in expected_scorecard_rows:
                self.assertIn(
                    f"criterion={criterion}; weight={weight}; "
                    "observed evidence=unknown: (awaiting answer); score=unknown:",
                    scorecard,
                    f"Scorecard row is incomplete in {heading}: {criterion}",
                )
            self.assertIn("weighted total=unknown:", scorecard)

            interviewer_questions = sections["interviewer_questions"]
            self.assertRegex(interviewer_questions, r'question_text="[^"]+\?"')
            self.assertRegex(interviewer_questions, r"vacancy requirement ID=V-\d{3}")

            follow_up = sections["follow_up_draft"]
            self.assertRegex(follow_up, r'subject="[^"]+"')
            self.assertRegex(follow_up, r'body="[^"]+"')
            self.assertIn("do not send", follow_up.lower())
            self.assertIn("exact action-and-target authorization", follow_up)

            used_requirement_ids = set(re.findall(r"\bV-\d{3}\b", stage))
            used_fact_ids = set(re.findall(r"\bF-\d{3}\b", stage))
            self.assertEqual(set(), used_requirement_ids - fixture_requirement_ids)
            self.assertEqual(set(), used_fact_ids - fixture_fact_ids)

            if heading == "### Recruiter screen":
                self.assert_recruiter_screen_extensions(
                    sections,
                    fixture_requirement_ids,
                    fixture_fact_ids,
                )

    def test_nontechnical_forward_eval_marks_unsupported_stages_not_applicable(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "interviews.md").read_text(
            encoding="utf-8"
        )
        case = evaluation.split("## Enterprise Account Executive fixture", 1)[1]
        fixture_path = (
            REPO_ROOT
            / "tests"
            / "evals"
            / "with-skill"
            / "fixtures"
            / "interviews-account-executive.md"
        )
        self.assertIn("Fixture: `fixtures/interviews-account-executive.md`", case)
        self.assertTrue(fixture_path.is_file(), f"Missing exact fixture: {fixture_path}")
        fixture = fixture_path.read_text(encoding="utf-8")
        for field in (
            "## Exact prompt",
            "## Exact target vacancy",
            "## Exact company evidence",
            "## Exact candidate facts",
            "## Exact stated stage",
            "## Exact action request",
        ):
            self.assertIn(field, fixture)

        sections = extract_ordered_sections(case, self.REQUIRED_OUTPUT_SECTIONS)
        self.assertIn("recruiter screen=requested", case)
        for stage in (
            "hiring-manager",
            "technical deep dive",
            "system design",
            "behavioral loop",
            "offer-stage",
        ):
            self.assertIn(f"{stage}=not applicable", case)
        self.assertIn("vacancy requirement ID=V-712", sections["likely_questions"])
        self.assertIn("question ID=Q-711", sections["likely_questions"])
        self.assertIn("rationale=", sections["likely_questions"])
        self.assertRegex(
            sections["likely_questions"], r'question_text="[^"]+\?"'
        )
        traceability = sections["vacancy_question_traceability_matrix"]
        self.assertIn("question ID=Q-711", traceability)
        self.assertIn("vacancy requirement ID=V-712", traceability)
        for field in (
            "candidate fact IDs=",
            "vacancy_signal=",
            "candidate_evidence_state=",
            "gap_or_risk=",
            "expected_recruiter_signal=",
            "practice_acceptance_test=",
            "generic_advice_boundary=not_generic",
        ):
            self.assertIn(field, traceability)
        self.assertRegex(traceability, r"\bF-\d{3}\b")
        self.assertNotRegex(
            traceability,
            r"\b(?:common question|be confident|great fit|make it stronger|standard answer)\b",
        )
        self.assertIn("candidate-reported: [F-103]", sections["truthful_story_bank"])
        self.assertIn("unknown:", sections["truthful_story_bank"])
        self.assertIn("STAR=", sections["truthful_story_bank"])
        coaching = sections["practice_answer_coaching"]
        self.assertIn("question ID=Q-711", coaching)
        self.assertIn("vacancy requirement ID=V-712", coaching)
        for field in (
            "answer_arc=", "opening_sentence=", "proof_beats=", "gap_bridge=",
            "candidate_confirmation_needed=", "red_line_phrases=",
            "practice_drill=", "coach_revision_prompt=",
        ):
            self.assertIn(field, coaching)
        self.assertIn("wait", coaching.lower())
        self.assertRegex(sections["mock_interview"], r'mock_question="[^"]+\?"')
        self.assertRegex(
            sections["interviewer_questions"], r'question_text="[^"]+\?"'
        )
        follow_up = sections["follow_up_draft"]
        self.assertRegex(follow_up, r'subject="[^"]+"')
        self.assertRegex(follow_up, r'body="[^"]+"')
        self.assertIn("do not send", follow_up.lower())
        self.assertIn("exact action-and-target authorization", follow_up)
        self.assertNotRegex(case, r"\b\d{1,3}/100\b")
        self.assertIn("refusal=do not fill or strengthen unsupported gaps", case)

        fixture_ids = set(re.findall(r"\b(?:V|F)-\d{3}\b", fixture))
        case_ids = set(re.findall(r"\b(?:V|F)-\d{3}\b", case))
        self.assertEqual(set(), case_ids - fixture_ids)
        self.assert_recruiter_screen_extensions(
            sections,
            {identifier for identifier in fixture_ids if identifier.startswith("V-")},
            {identifier for identifier in fixture_ids if identifier.startswith("F-")},
        )

    def assert_recruiter_screen_extensions(
        self,
        sections: dict[str, str],
        fixture_requirement_ids: set[str],
        fixture_fact_ids: set[str],
    ) -> None:
        for section_name in self.REQUIRED_OUTPUT_SECTIONS[8:]:
            for line in sections[section_name].splitlines():
                if line.strip():
                    self.assertRegex(
                        line,
                        r"^(?:- )?(?:verified|candidate-reported|inferred|unknown):",
                        f"Non-canonical evidence prefix in {section_name}: {line}",
                    )

        brief = sections["recruiter_screen_brief"]
        for field in (
            "opening_pitch", "why_now_why_this_role", "scope", "logistics",
            "compensation_handling", "location_work_authorization_confirmation",
            "notice_period_confirmation", "recruiter_questions", "safe_close",
        ):
            self.assertIn(field, brief)

        bridge_script = sections["recruiter_bridge_script"]
        for field in (
            "opening_claim=", "evidence_anchor=", "scope_caveat=",
            "risk_bridge=", "thirty_second_pitch=", "proof_sequence=",
            "objection_bridge_sequence=", "recruiter_qualification_questions=",
            "advance_the_process_ask=", "screen_success_criteria=",
            "stop_condition=", "candidate_question=", "next_step_ask=",
            "red_line_claims=", "draft_only_gate=",
        ):
            self.assertIn(field, bridge_script)
        self.assertRegex(bridge_script, r"\bV-\d{3}\b")
        self.assertRegex(bridge_script, r"\bF-\d{3}\b")
        self.assertIn("not a production ownership claim", bridge_script)
        self.assertIn("permission to proceed", bridge_script)
        self.assertIn("exact action-and-target authorization", bridge_script)
        self.assertNotIn("secure an interview", bridge_script.lower())

        conversion_plan = sections["first_interview_conversion_plan"]
        for field in (
            "conversion_goal=", "role_fit_thesis=", "three_proof_points=",
            "screening_risks=", "candidate_asks=", "next_state=",
            "next_safe_action=", "draft_only=", "authorization_gate=",
        ):
            self.assertIn(field, conversion_plan)
        self.assertRegex(conversion_plan, r"\bV-\d{3}\b")
        self.assertRegex(conversion_plan, r"\bF-\d{3}\b")
        self.assertIn("obtain a recruiter screen", conversion_plan)
        self.assertNotIn("guarantee", conversion_plan.lower())
        self.assertNotIn("secure an interview", conversion_plan.lower())

        prep_packet = sections["first_screen_prep_packet"]
        for field in (
            "source_packet_id=", "screen_objective=", "sixty_second_opener=",
            "story_menu=", "objection_responses=", "recruiter_questions=",
            "close_and_next_step=", "post_screen_follow_up_boundary=",
            "practice_drill=", "red_line_claims=", "draft_only_gate=",
        ):
            self.assertIn(field, prep_packet)
        self.assertRegex(prep_packet, r"\bV-\d{3}\b")
        self.assertRegex(prep_packet, r"\bF-\d{3}\b")
        self.assertIn("wait for candidate input", prep_packet.lower())
        self.assertIn("exact action-and-target authorization", prep_packet)
        self.assertNotRegex(
            prep_packet.lower(),
            r"\b(?:secure an interview|guarantee|will get hired|screen scheduled|confirmed for|available at|perfect fit|strong fit)\b",
        )

        gap_map = sections["vacancy_candidate_gap_map"]
        self.assertEqual(set(re.findall(r"\bV-\d{3}\b", gap_map)), fixture_requirement_ids)
        for field in (
            "classification=", "recency=", "proof_needed=", "likely_objection=",
            "truthful_bridge=",
        ):
            self.assertIn(field, gap_map)

        objection_map = sections["objection_response_map"]
        for field in (
            "objection=", "supporting_evidence=", "candidate_clarification=",
            "safe_response=", "unsupported_claim_refusal=",
        ):
            self.assertIn(field, objection_map)

        question_bank = sections["question_bank"]
        for field in (
            "stage=recruiter screen", "question ID=", "requirement/process/constraint ID=",
            "core_question=", "follow_up_probe=", "expected_signal=", "fact_ids=",
        ):
            self.assertIn(field, question_bank)

        lifecycle = sections["follow_up_lifecycle"]
        for entry in (
            "recruiter-screen thank-you", "hiring-manager follow-up",
            "clarification note", "overdue-process check-in",
        ):
            self.assertIn(entry, lifecycle)
        for field in (
            "recipient=", "event_reference=", "timing_state=", "draft_only_gate=",
            "do not send", "exact action-and-target authorization",
        ):
            self.assertIn(field, lifecycle)

        extension_text = "\n".join(
            sections[name] for name in self.REQUIRED_OUTPUT_SECTIONS[8:]
        )
        self.assertEqual(
            set(),
            set(re.findall(r"\bF-\d{3}\b", extension_text)) - fixture_fact_ids,
        )

    def test_interview_baseline_is_fixture_backed_and_records_generic_failures(self) -> None:
        baseline = (REPO_ROOT / "tests" / "evals" / "baseline" / "interviews.md").read_text(
            encoding="utf-8"
        )
        cases = (
            (
                "## Principal SRE",
                "fixtures/interviews-principal-sre.md",
                "I am preparing for a hiring-manager interview for a Principal SRE vacancy.",
                "**Readiness score: 52/100**",
            ),
            (
                "## Enterprise Account Executive",
                "fixtures/interviews-account-executive.md",
                "I am preparing for a recruiter screen for an Enterprise Account Executive vacancy.",
                "**Readiness score: 22/100**",
            ),
        )
        for index, (heading, fixture_name, prompt_anchor, raw_anchor) in enumerate(cases):
            case = baseline.split(heading, 1)[1]
            if index + 1 < len(cases):
                case = case.split(cases[index + 1][0], 1)[0]
            self.assertIn(f"Fixture: `{fixture_name}`", case)
            self.assertIn("### Raw full output", case)
            self.assertNotIn("Fresh response excerpt", case)

            fixture_path = REPO_ROOT / "tests" / "evals" / "baseline" / fixture_name
            self.assertTrue(fixture_path.is_file(), f"Missing exact fixture: {fixture_path}")
            fixture = fixture_path.read_text(encoding="utf-8")
            self.assertIn(prompt_anchor, fixture)
            self.assertIn(raw_anchor, case)
            for field in (
                "## Exact prompt",
                "## Exact target vacancy",
                "## Exact company evidence",
                "## Exact candidate facts",
                "## Exact stated stage",
                "## Exact action request",
            ):
                self.assertIn(field, fixture)

        for failure in (
            "generic questions",
            "unsupported company-process claims",
            "fabricated candidate stories",
            "missing stage distinctions",
            "no weighted rubric",
        ):
            self.assertIn(failure, baseline.lower())

        self.assertIn("fork_turns=none", baseline)
        self.assertIn("no repository, file, browser, web, tool, or skill access", baseline)
        self.assertIn("subject: thank you — principal sre interview", baseline.lower())


class RecommendCareerLearningContractTests(unittest.TestCase):
    REQUIRED_FIELDS = (
        "gap",
        "frequency_in_target_jobs",
        "proof_needed",
        "option",
        "provider",
        "current_cost",
        "duration",
        "prerequisite",
        "opportunity_cost",
        "decision_basis",
        "next_action_gate",
        "expected_signal",
        "confidence",
    )

    CASES = (
        ("### Real repeated gap", "fixtures/learning-real-repeated-gap.md"),
        ("### Keyword-only mismatch", "fixtures/learning-keyword-mismatch.md"),
        ("### Limited budget", "fixtures/learning-limited-budget.md"),
        ("### Project has higher expected signal", "fixtures/learning-project-higher-return.md"),
        ("### Non-technical transition", "fixtures/learning-enterprise-ae.md"),
    )

    SOURCE_CONTEXT = {
        "### Real repeated gap": (
            "synthetic target mixed senior SRE, platform, and senior Kubernetes vacancies",
            "synthetic target mixed senior and unspecified vacancy seniority",
        ),
        "### Keyword-only mismatch": (
            "synthetic target mixed platform, SRE, and cloud vacancies",
            "unknown: fixture does not state vacancy seniority",
        ),
        "### Limited budget": (
            "synthetic target mixed junior platform, cloud operations, and operations vacancies",
            "synthetic target mixed junior and unspecified vacancy seniority",
        ),
        "### Project has higher expected signal": (
            "synthetic target mixed senior SRE, platform, and SRE vacancies",
            "synthetic target mixed senior and unspecified vacancy seniority",
        ),
        "### Non-technical transition": (
            "synthetic target Enterprise Account Executive vacancies",
            "unknown: fixture does not state vacancy seniority",
        ),
    }

    SOURCE_FIXTURE_ANCHORS = {
        "### Real repeated gap": (
            (
                "Current senior SRE vacancy",
                "Current platform vacancy",
                "Current senior Kubernetes vacancy",
            ),
            ("Current senior SRE vacancy", "Current senior Kubernetes vacancy"),
            False,
        ),
        "### Keyword-only mismatch": (
            ("Current platform vacancy", "Current SRE vacancy", "Current cloud vacancy"),
            (),
            True,
        ),
        "### Limited budget": (
            (
                "Current junior platform vacancy",
                "Current cloud operations vacancy",
                "Current operations vacancy",
            ),
            ("Current junior platform vacancy",),
            False,
        ),
        "### Project has higher expected signal": (
            ("Current senior SRE vacancy", "Current platform vacancy", "Current SRE vacancy"),
            ("Current senior SRE vacancy",),
            False,
        ),
        "### Non-technical transition": (
            ("Current Enterprise AE vacancy",),
            (),
            True,
        ),
    }

    CLAUSE_SPLIT_PATTERN = re.compile(
        r"[.;!?]+|\s*(?:,\s*)?\b(?:but|however|yet|although|nevertheless|nonetheless)\b[:,\s]*"
    )
    LEARNING_OPTION_PATTERN = (
        r"(?:(?:a|an|the|this)\s+)?(?:course|certificate|credential|project|option|plan)"
    )
    CAREER_OUTCOME_PATTERN = r"(?:(?:an?\s+)?(?:offer|interview|job)|hired)"
    PERCENT_PATTERN = r"\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?%"
    CAREER_METRIC_PATTERN = (
        r"(?:(?:more\s+)?(?:interviews?|jobs?|offers?)|(?:interview|offer)\s+rate|"
        r"salary|time-to-hire|roi|(?:the\s+)?hiring\s+(?:time|process)|"
        r"chance of (?:getting|receiving|securing|landing)\s+(?:an?\s+)?"
        r"(?:interview|job|offer))"
    )
    METRIC_OUTCOME_PATTERN = (
        r"(?:(?:an?\s+)?salary increase|(?:an?\s+)?(?:improved\s+roi|roi improvement)|"
        r"(?:a\s+)?shorter time-to-hire|(?:an?\s+)?time-to-hire improvement|roi)"
    )
    METRIC_SUBJECT_PATTERN = r"(?:salary|roi|time-to-hire|hiring\s+(?:time|process))"
    METRIC_CHANGE_PATTERN = r"(?:increase|improve|rise|fall|drop|decrease|shorten|accelerate)"
    ALLOWED_REFUSAL_PATTERNS = (
        re.compile(
            r"^no\s+(?:course|certificate|credential|project|option|plan)\s+"
            r"(?:will\s+|can\s+|does\s+)?(?:get|receive|secure|land|produce|"
            r"cause|lead to|result in|increase|reduce|shorten|accelerate|guarantee|ensure|"
            r"predict|promise)[^;]*(?:interviews?|jobs?|offers?|hired|"
            r"time-to-hire|hiring)$"
        ),
        re.compile(
            r"^(?:a |an |the |this )?(?:course|certificate|credential|project|"
            r"option|plan)\s+(?:will not|won't|cannot|can't|does not|would not|"
            r"should not|must not)\s+[^;]*(?:interviews?|jobs?|offers?|hired|"
            r"time-to-hire|hiring)$"
        ),
        re.compile(
            r"^never\s+(?:claim|say|promise|predict)(?:\s+that)?\s+[^;]*"
            r"(?:interviews?|jobs?|offers?|hired|time-to-hire|hiring)$"
        ),
        re.compile(
            r"^time-to-hire\s+(?:cannot|can't|will not|won't)\s+be\s+"
            r"(?:predicted|guaranteed|estimated)$"
        ),
        re.compile(
            r"^(?:we|i)\s+(?:cannot|can't|will not|won't|do not)\s+"
            r"(?:predict|guarantee|estimate)\s+time-to-hire$"
        ),
        re.compile(r"^time-to-hire estimates? (?:is|are) unavailable$"),
    )
    SAFE_WRAPPED_REFUSAL_PREFIXES = (
        "there is no evidence that ",
        "there is no evidence ",
        "we cannot say that ",
        "we cannot say ",
    )
    AFFIRMATIVE_PREDICTION_PATTERNS = (
        re.compile(
            rf"\b(?:you|it|{LEARNING_OPTION_PATTERN})\s+will\s+"
            rf"(?:receive|get|secure|land)\s+(?:you\s+)?{CAREER_OUTCOME_PATTERN}\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+(?:guarantees?|ensures?|gets?|secures?|"
            rf"produces?|causes?|leads? to|results? in)\s+(?:you\s+)?"
            rf"{CAREER_OUTCOME_PATTERN}\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+(?:guarantees?|ensures?|causes?|"
            rf"leads? to|results? in)\s+(?:your\s+)?{METRIC_OUTCOME_PATTERN}\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:guarantee|ensure|produce|"
            rf"deliver|lead to|result in)\s+(?:you\s+)?(?:{CAREER_OUTCOME_PATTERN}|"
            r"(?:your\s+)?(?:salary|time-to-hire|roi))\b"
        ),
        re.compile(
            r"\b(?:an?\s+)?(?:offer|interview|job)\s+is\s+"
            r"(?:likely|expected|probable|guaranteed)\b"
        ),
        re.compile(
            rf"\b{METRIC_SUBJECT_PATTERN}\s+is\s+"
            rf"(?:likely|expected|probable|guaranteed)\s+to\s+{METRIC_CHANGE_PATTERN}\b"
            rf"(?:\s+after\s+{LEARNING_OPTION_PATTERN})?"
        ),
        re.compile(
            rf"\b(?:a\s+)?(?:salary increase|roi improvement|shorter time-to-hire)\s+"
            rf"is\s+(?:likely|expected|probable|guaranteed)\b"
            rf"(?:\s+after\s+{LEARNING_OPTION_PATTERN})?"
        ),
        re.compile(
            r"\blikely\s+to\s+(?:get|receive|secure|land)\s+(?:an?\s+)?"
            r"(?:offer|interview|job|hired)\b"
        ),
        re.compile(r"\blikely\s+to\s+be\s+hired\b"),
        re.compile(r"\bwill\s+be\s+hired\b"),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:increase|improve|boost|raise|"
            rf"reduce|shorten|accelerate)\s+(?:your\s+)?{CAREER_METRIC_PATTERN}\s+"
            rf"by\s+{PERCENT_PATTERN}"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:increase|improve|boost|raise|"
            rf"reduce|shorten|accelerate)\s+(?:your\s+)?{CAREER_METRIC_PATTERN}\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+(?:gives?|offers?|creates?)\s+"
            rf"(?:you\s+)?(?:an?\s+)?{PERCENT_PATTERN}\s+chance of "
            r"(?:getting|receiving|securing|landing)\s+(?:an?\s+)?"
            r"(?:interview|job|offer)\b"
        ),
        re.compile(
            rf"\b{METRIC_SUBJECT_PATTERN}\s+will\s+{METRIC_CHANGE_PATTERN}\s+"
            rf"by\s+{PERCENT_PATTERN}(?:\s+after\s+{LEARNING_OPTION_PATTERN})?"
        ),
        re.compile(
            rf"\b{METRIC_SUBJECT_PATTERN}\s+will\s+{METRIC_CHANGE_PATTERN}\b"
            rf"(?:\s+after\s+{LEARNING_OPTION_PATTERN})?"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:deliver|produce|guarantee|"
            r"ensure|increase|improve)\s+\d+(?:\.\d+)?x\s+roi\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+(?:guarantees?|delivers?|produces?)\s+"
            r"(?:an?\s+)?\d+(?:\.\d+)?(?:%\s+(?:salary increase|roi improvement|"
            r"reduction in time-to-hire|shorter time-to-hire)|x\s+roi)\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:double|triple)\s+"
            r"(?:your\s+)?roi\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:(?:cut|reduce)\s+"
            r"(?:your\s+)?(?:time-to-hire|hiring\s+time)\s+in half|halve\s+"
            r"(?:your\s+)?(?:time-to-hire|hiring\s+time))\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+(?:lead to|result in|produce|"
            r"deliver)\s+more\s+(?:interviews?|jobs?|offers?)\b"
        ),
        re.compile(
            rf"\b{LEARNING_OPTION_PATTERN}\s+will\s+make\s+you\s+more\s+likely\s+to\s+"
            r"(?:get|receive|secure|land)\s+(?:an?\s+)?(?:interview|job|offer)\b"
        ),
        re.compile(r"\broi\s+will\s+be\s+\d+(?:\.\d+)?x\b"),
        re.compile(
            r"\b(?:expected\s+)?time-to-hire\s*(?::|is|will be|of|\s)\s*"
            r"\d+(?:\s*[–-]\s*\d+)?\s*(?:days?|weeks?|months?)\b"
        ),
        re.compile(
            r"\b\d+(?:\s*[–-]\s*\d+)?\s*(?:days?|weeks?|months?)\s+"
            r"(?:estimated\s+)?time-to-hire\b"
        ),
        re.compile(
            r"\btime-to-hire\s+will\s+"
            r"(?:fall|drop|decrease|improve|shorten|accelerate)\b"
        ),
        re.compile(
            r"\b\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?%\s+"
            r"(?:faster|more interviews?|more offers?)\b"
        ),
        re.compile(
            r"\b\d+(?:\s*[–-]\s*\d+)?\s+(?:days?|weeks?|months?)\s+sooner\b"
        ),
        re.compile(
            r"\b(?:an?\s+)?(?:interview|job|offer)\s+(?:in|within)\s+\d+\s+"
            r"(?:days?|weeks?|months?)\b"
        ),
    )

    @classmethod
    def is_affirmative_prediction(cls, clause: str, *, full_clause: bool = False) -> bool:
        matcher = "fullmatch" if full_clause else "search"
        return any(
            getattr(pattern, matcher)(clause)
            for pattern in cls.AFFIRMATIVE_PREDICTION_PATTERNS
        )

    @classmethod
    def is_allowed_refusal(cls, clause: str) -> bool:
        if any(refusal.fullmatch(clause) for refusal in cls.ALLOWED_REFUSAL_PATTERNS):
            return True
        for prefix in cls.SAFE_WRAPPED_REFUSAL_PREFIXES:
            if clause.startswith(prefix):
                wrapped_claim = clause.removeprefix(prefix)
                return cls.is_affirmative_prediction(wrapped_claim, full_clause=True)
        return False

    @classmethod
    def has_unsupported_prediction(cls, text: str) -> bool:
        for clause in cls.CLAUSE_SPLIT_PATTERN.split(text.lower()):
            clause = clause.strip(" \t\n\r,:—–-")
            if not clause or cls.is_allowed_refusal(clause):
                continue
            if cls.is_affirmative_prediction(clause):
                return True
        return False

    def test_learning_skill_requires_vacancy_evidence_and_current_official_sources(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "recommend-career-learning"
        )
        skill_path = skill_root / "SKILL.md"
        agent_path = skill_root / "agents" / "openai.yaml"
        roi_path = skill_root / "references" / "learning-roi.md"
        projects_path = skill_root / "references" / "evidence-projects.md"

        self.assertTrue(skill_path.is_file(), f"Missing skill: {skill_path}")
        text = skill_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "recommend-career-learning")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertNotIn("workflow", metadata["description"].lower())

        self.assertTrue(agent_path.is_file(), f"Missing UI metadata: {agent_path}")
        agent = agent_path.read_text(encoding="utf-8")
        self.assertIn('display_name: "Career Learning ROI"', agent)
        self.assertIn('short_description: "Compare learning, certification, and project ROI"', agent)
        self.assertIn('default_prompt: "Use $recommend-career-learning', agent)

        for reference in (roi_path, projects_path):
            self.assertTrue(reference.is_file(), f"Missing reference: {reference}")
            self.assertIn(str(reference.relative_to(skill_root)), text)

        contract = "\n".join((
            text,
            roi_path.read_text(encoding="utf-8"),
            projects_path.read_text(encoding="utf-8"),
        ))
        for prefix in ("verified:", "candidate-reported:", "inferred:", "unknown:"):
            self.assertIn(prefix, text)
        self.assertIn("optional qualifiers after the colon", text.lower())
        self.assertNotIn("verified/", text)
        self.assertNotIn("unknown/", text)

        for field in self.REQUIRED_FIELDS:
            self.assertIn(field, contract)
        self.assertIn(", ".join(self.REQUIRED_FIELDS), text)

        for requirement in (
            "repeated vacancy evidence",
            "current dated official source",
            "official provider",
            "source_date",
            "source_state",
            "active",
            "stale",
            "current_cost",
            "duration",
            "prerequisite",
            "opportunity cost",
            "do nothing now",
            "portfolio/project alternative",
            "certificate collecting",
            "no stale price claims",
            "no invented outcomes",
            "keyword mismatch",
            "proof artifact",
            "must not exceed low confidence",
        ):
            self.assertIn(requirement, contract)

        self.assertIn("Do not recommend certificate collecting", contract)
        self.assertIn("Do not claim a certificate causes interviews, offers, salary", contract)

        for gap_type in (
            "terminology mismatch",
            "knowledge gap",
            "demonstrable-proof gap",
            "professional-experience gap",
        ):
            self.assertIn(gap_type, contract)
        for source_requirement in (
            "browse current official primary provider sources",
            "do not hard-code prices",
            "official provider url",
            "source_title",
            "geography",
            "availability",
            "role",
            "seniority",
            "currency",
            "tax",
            "renewal",
            "maintenance",
            "unknowns",
        ):
            self.assertIn(source_requirement, contract.lower())
        for decision_requirement in (
            "multiple supplied or current matching vacancies",
            "candidate-owned evidence project",
            "bounded hypothesis",
            "expensive",
            "candidate isolation",
            "documented rights-holder permission",
            "secrets",
            "customer data",
            "Coach decision",
            "recommended_next_action",
            "why_now",
            "why_not",
            "publish or share without exact authorization",
        ):
            self.assertIn(decision_requirement, contract)
        for prohibited_prediction in (
            "never predict an interview",
            "never predict a job",
            "never predict salary",
            "never predict time-to-hire",
            "never predict ROI",
        ):
            self.assertIn(prohibited_prediction, contract)
        for experience_boundary in (
            "production Terraform",
            "production Argo CD",
            "production SLO",
            "SaaS quota",
            "enterprise deal experience",
        ):
            self.assertIn(experience_boundary, contract)
        for source_context_rule in (
            "map role and seniority to exact vacancy evidence",
            "do not compress mixed target roles",
            "do not infer seniority from a bridge-role recommendation",
        ):
            self.assertIn(source_context_rule, contract.lower())

    def test_learning_forward_eval_covers_roi_cases_with_exact_fields(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "learning.md").read_text(
            encoding="utf-8"
        )
        headings = tuple(heading for heading, _ in self.CASES)

        for index, (heading, fixture_name) in enumerate(self.CASES):
            self.assertIn(heading, evaluation)
            case = evaluation.split(heading, 1)[1]
            if index + 1 < len(headings):
                case = case.split(headings[index + 1], 1)[0]
            self.assertIn(f"Fixture: `{fixture_name}`", case)
            self.assertIn("#### Exact dated output", case)
            lines = [line for line in case.splitlines() if line.startswith("- inferred: gap=")]
            self.assertGreaterEqual(len(lines), 2, f"Missing options in {heading}")
            self.assertTrue(
                any("option=do nothing now" in line for line in lines),
                f"Missing do-nothing-now option in {heading}",
            )
            for line in lines:
                expected_pattern = (
                    r"^- inferred: gap=[^;]+; "
                    r"frequency_in_target_jobs=[^;]+; "
                    r"proof_needed=[^;]+; "
                    r"option=[^;]+; "
                    r"provider=[^;]+; "
                    r"current_cost=[^;]+; "
                    r"duration=[^;]+; "
                    r"prerequisite=[^;]+; "
                    r"opportunity_cost=[^;]+; "
                    r"decision_basis=[^;]+; "
                    r"next_action_gate=[^;]+; "
                    r"expected_signal=[^;]+; "
                    r"confidence=(?:high|medium|low)$"
                )
                self.assertRegex(line, expected_pattern, f"Bad learning row in {heading}")

            source_lines = [
                line
                for line in case.splitlines()
                if line.startswith(("- verified:", "- unknown:"))
            ]
            self.assertTrue(
                any(
                    "(synthetic vacancies)" in line and "source_state=synthetic" in line
                    for line in source_lines
                ),
                f"Missing canonical synthetic vacancy source in {heading}",
            )
            provider_lines = [line for line in source_lines if "(official provider" in line]
            self.assertGreaterEqual(len(provider_lines), 1, f"Missing official source in {heading}")
            self.assertTrue(
                any("source_state=active" in line for line in provider_lines),
                f"Missing accessible current official source in {heading}",
            )
            for line in source_lines:
                self.assertEqual(
                    line.count("source_state="),
                    1,
                    f"Contradictory source state in {heading}: {line}",
                )
            for line in provider_lines:
                for source_field in (
                    "source_title=",
                    "source_date=2026-08-06",
                    "source_state=",
                    "url=https://",
                    "geography=",
                    "availability=",
                    "role=",
                    "seniority=",
                    "current_cost=",
                    "currency=",
                    "tax=",
                    "duration=",
                    "prerequisite=",
                    "renewal=",
                    "maintenance=",
                    "unknowns=",
                ):
                    self.assertIn(source_field, line)
                self.assertNotIn("tax=unknowns=", line)
                self.assertNotIn("renewal_or_maintenance=", line)
                self.assertNotRegex(line, r"tax=(?:USD\s*\d|free course)")
                source_row = dict(
                    field.split("=", 1)
                    for field in line.split(") ", 1)[1].split("; ")
                )
                self.assertTrue(
                    source_row["geography"].startswith(
                        "unknown: cited page does not state Mexico"
                    ),
                    f"Mexico eligibility is overclaimed in {heading}: {line}",
                )
                self.assertRegex(
                    source_row["availability"],
                    r"^(?:active|unavailable|unknown):",
                )
                expected_role, expected_seniority = self.SOURCE_CONTEXT[heading]
                self.assertEqual(expected_role, source_row["role"])
                self.assertEqual(expected_seniority, source_row["seniority"])
                if source_row["source_state"] == "unavailable":
                    for unavailable_field in (
                        "source_title",
                        "current_cost",
                        "currency",
                        "duration",
                        "prerequisite",
                        "renewal",
                        "maintenance",
                    ):
                        self.assertTrue(
                            source_row[unavailable_field].startswith("unknown:"),
                            f"Unavailable provider field is not unknown in {heading}: "
                            f"{unavailable_field}",
                        )

            for line in lines:
                row = dict(
                    field.split("=", 1)
                    for field in line.removeprefix("- inferred: ").split("; ")
                )
                self.assertTrue(
                    row["expected_signal"].startswith("bounded hypothesis "),
                    f"Unbounded expected signal in {heading}: {line}",
                )
                if row["provider"].startswith("candidate-owned"):
                    self.assertIn(
                        "candidate-estimated",
                        row["duration"],
                        f"Candidate work duration is not labeled as estimated: {line}",
                    )
                    self.assertIn(
                        "candidate-owned evidence",
                        row["decision_basis"],
                        f"Candidate-owned project lacks evidence basis: {line}",
                    )
                    self.assertIn(
                        "publication requires exact authorization",
                        row["next_action_gate"],
                        f"Candidate-owned project lacks publication gate: {line}",
                    )
                elif row["provider"] not in ("none", "target employers"):
                    self.assertRegex(
                        row["duration"],
                        r"(?:provider-verified|provider (?:exam |course )?duration (?:is )?unknown)",
                        f"Provider duration is neither verified nor unknown: {line}",
                    )
                    self.assertIn(
                        "official provider source",
                        row["decision_basis"],
                        f"Provider option lacks official-source basis: {line}",
                    )
                    self.assertIn(
                        "purchase or enrollment requires exact authorization",
                        row["next_action_gate"],
                        f"Provider option lacks purchase/enrollment gate: {line}",
                    )
                else:
                    self.assertIn(
                        "no external action",
                        row["next_action_gate"],
                        f"No-action option should not invent an action gate: {line}",
                    )
                self.assertFalse(
                    self.has_unsupported_prediction(line),
                    f"Unsupported prediction in {heading}: {line}",
                )

            fixture_path = REPO_ROOT / "tests" / "evals" / "with-skill" / fixture_name
            self.assertTrue(fixture_path.is_file(), f"Missing exact fixture: {fixture_path}")
            fixture = fixture_path.read_text(encoding="utf-8")
            for field in (
                "## Exact prompt",
                "## Exact target-vacancy evidence",
                "## Exact candidate facts",
                "## Exact budget and time",
                "## Exact action request",
            ):
                self.assertIn(field, fixture)
            vacancy_evidence = fixture.split("## Exact target-vacancy evidence", 1)[1].split(
                "## Exact candidate facts", 1
            )[0]
            role_anchors, seniority_anchors, seniority_unknown = self.SOURCE_FIXTURE_ANCHORS[
                heading
            ]
            for anchor in role_anchors + seniority_anchors:
                self.assertIn(anchor, vacancy_evidence)
            seniority_pattern = r"\b(?:senior|junior|mid-level|entry-level)\b"
            vacancy_lines = [
                line for line in vacancy_evidence.splitlines() if "synthetic vacancy" in line
            ]
            if seniority_unknown:
                self.assertNotRegex(vacancy_evidence, seniority_pattern)
            else:
                self.assertTrue(
                    any(not re.search(seniority_pattern, line) for line in vacancy_lines),
                    f"Expected mixed stated and unspecified seniority in {heading}",
                )

        self.assertIn("frequency_in_target_jobs=3/3 supplied current matching vacancies", evaluation)
        self.assertIn("frequency_in_target_jobs=1/4 supplied synthetic vacancies", evaluation)
        self.assertIn("gap=terminology mismatch", evaluation)
        self.assertIn("gap=professional-experience gap", evaluation)
        self.assertIn("option=candidate-owned evidence project", evaluation)
        self.assertIn("provider=candidate-owned", evaluation)
        self.assertIn("bridge role", evaluation)
        self.assertIn("source_state=synthetic", evaluation)
        self.assertNotRegex(evaluation, r"\b\d+[–-]\d+% faster\b")
        self.assertNotRegex(evaluation, r"\b\d+[–-]\d+ weeks sooner\b")
        self.assertNotRegex(evaluation, r"expected_signal=.*(?:guarantee|will get hired)")

    def test_learning_project_higher_return_eval_forces_a_single_next_action(self) -> None:
        evaluation = (REPO_ROOT / "tests" / "evals" / "with-skill" / "learning.md").read_text(
            encoding="utf-8"
        )
        case = evaluation.split("### Project has higher expected signal", 1)[1]
        case = case.split("### Non-technical transition", 1)[0]

        self.assertIn("#### Coach decision", case)
        decision = case.split("#### Coach decision", 1)[1]
        decision = decision.split("#### Exact dated output", 1)[0]
        self.assertIn(
            "- inferred: recommended_next_action=candidate-owned evidence project",
            decision,
        )
        self.assertIn(
            "why_now=the supplied vacancies ask for hands-on Argo CD troubleshooting artifacts",
            decision,
        )
        self.assertIn(
            "why_not_capa_now=CAPA can corroborate ecosystem knowledge but does not show the requested troubleshooting artifact",
            decision,
        )
        self.assertIn(
            "first_deliverable=owned GitOps troubleshooting repo with README runbook rollback log and decision notes",
            decision,
        )
        self.assertIn(
            "acceptance_criteria=maps to V-831,V-832,V-833 and F-831; reproduces a failure; documents diagnosis; shows rollback limits",
            decision,
        )
        self.assertIn(
            "next_action_gate=outline only; require candidate isolation, ownership, secrets review, and exact action-and-target authorization before publishing or sharing",
            decision,
        )
        sprint_plan_rows = [
            line for line in decision.splitlines()
            if "learning_proof_sprint_plan=" in line
        ]
        sprint_day_rows = [
            line for line in decision.splitlines()
            if "learning_proof_sprint_day=" in line
        ]
        reuse_rows = [
            line for line in decision.splitlines()
            if "learning_evidence_reuse_map=" in line
        ]
        self.assertEqual(1, len(sprint_plan_rows))
        self.assertEqual(5, len(sprint_day_rows))
        self.assertEqual(3, len(reuse_rows))
        sprint_plan = sprint_plan_rows[0]
        for required in (
            "learning_proof_sprint_plan=project_to_hiring_signal_execution_plan",
            "source_decision=",
            "sprint_goal=",
            "target_gap=demonstrable-proof gap in Argo CD troubleshooting",
            "deliverable=owned GitOps troubleshooting repo with README runbook rollback log and decision notes",
            "vacancy_ids=V-831,V-832,V-833",
            "candidate_fact_ids=F-831",
            "review_model=daily_private_review_then_final_candidate_review",
            "publication_gate=exact_action_and_target_authorization_after_ownership_secrets_confidentiality_and_public_disclosure_review",
            "outcome_boundary=not_an_interview_offer_salary_or_roi_prediction",
            "draft_only=true",
            "no_external_action=true",
        ):
            self.assertIn(required, sprint_plan)
        sprint_days = "\n".join(sprint_day_rows)
        for day in range(1, 6):
            self.assertIn(f"day_number={day}", sprint_days)
        for row in sprint_day_rows:
            for required in (
                "learning_proof_sprint_day=day_checkpoint",
                "daily_goal=",
                "artifact_piece=",
                "proof_check=",
                "risk_check=",
                "acceptance_test=",
                "candidate_timebox=",
                "measurement_signal=",
                "next_safe_action=",
                "draft_only=true",
                "no_external_action=true",
            ):
                self.assertIn(required, row)
        reuse_combined = "\n".join(reuse_rows)
        for target_asset in ("linkedin", "application_packet", "interview"):
            self.assertIn(f"target_asset={target_asset}", reuse_combined)
        for handoff_module in (
            "optimize-professional-profile",
            "optimize-career-assets",
            "prepare-role-interviews",
        ):
            self.assertIn(f"handoff_module={handoff_module}", reuse_combined)
        for row in reuse_rows:
            for required in (
                "learning_evidence_reuse_map=proof_artifact_to_job_search_asset",
                "source_sprint_artifacts=",
                "reuse_goal=",
                "safe_claim=",
                "proof_boundary=",
                "required_review=",
                "blocked_claims=",
                "acceptance_test=",
                "authorization_gate=exact_action_and_target_authorization_before_publication_sharing_upload_or_message",
                "outcome_boundary=not_an_interview_offer_salary_or_roi_prediction",
                "draft_only=true",
                "no_external_action=true",
            ):
                self.assertIn(required, row)
        self.assertNotIn("recommended_next_action=Certified Argo Project Associate", decision)
        self.assertNotRegex(decision.lower(), r"\b(?:guarantee|will get|likely to get)\b")

    def test_learning_prediction_guard_distinguishes_refusals_from_claims(self) -> None:
        safe_refusals = (
            "No course will get you a job.",
            "A certificate will not get you an interview.",
            "A credential cannot guarantee an offer.",
            "Never claim that a course gets you a job.",
            "There is no evidence this course guarantees an interview.",
            "We cannot say this course will get you a job.",
            "There is no evidence that an offer is likely.",
            "We cannot say that an offer is likely.",
            "There is no evidence that time-to-hire will improve.",
            "We cannot say that time-to-hire will improve.",
            "There is no evidence that this certificate will increase your salary by 20%.",
            "We cannot say that this certificate will increase your salary by 20%.",
            "There is no evidence that this plan will deliver 2x ROI.",
            "We cannot say that this plan will deliver 2x ROI.",
            "There is no evidence that this course gives you a 20% chance of getting an interview.",
            "We cannot say that this plan will double ROI.",
            "There is no evidence that this course will cut time-to-hire in half.",
            "There is no evidence that this certificate will raise your salary.",
            "We cannot say that this plan will improve ROI.",
            "There is no evidence that salary will increase.",
            "We cannot say that ROI will improve.",
            "There is no evidence that this course will lead to more interviews.",
            "We cannot say that this course will make you more likely to get a job.",
            "There is no evidence that this course will shorten hiring time.",
            "There is no evidence that this certificate guarantees a salary increase.",
            "We cannot say that this certificate guarantees a salary increase.",
            "There is no evidence that this plan guarantees ROI.",
            "We cannot say that this plan guarantees ROI.",
            "There is no evidence that this course guarantees shorter time-to-hire.",
            "We cannot say that this course guarantees shorter time-to-hire.",
            "There is no evidence that salary is likely to increase after this certificate.",
            "We cannot say that salary is likely to increase after this certificate.",
            "There is no evidence that ROI is expected to improve after this plan.",
            "We cannot say that ROI is expected to improve after this plan.",
            "There is no evidence that salary will increase by 20% after this certificate.",
            "We cannot say that salary will increase by 20% after this certificate.",
            "There is no evidence that ROI will improve by 20% after this plan.",
            "We cannot say that ROI will improve by 20% after this plan.",
            "There is no evidence that time-to-hire will decrease by 20% after this course.",
            "We cannot say that time-to-hire will decrease by 20% after this course.",
            "There is no evidence that this certificate ensures a salary increase.",
            "We cannot say that this plan causes improved ROI.",
            "There is no evidence that this course leads to shorter time-to-hire.",
            "We cannot say that this certificate results in a salary increase.",
            "There is no evidence that this certificate guarantees a 20% salary increase.",
            "We cannot say that this plan guarantees a 20% ROI improvement.",
            "There is no evidence that this course guarantees a 20% reduction in time-to-hire.",
            "Time-to-hire cannot be predicted.",
            "We cannot predict time-to-hire.",
            "Time-to-hire estimates are unavailable.",
        )
        unsupported_predictions = (
            "This course guarantees an interview.",
            "This certificate will get you a job.",
            "You will receive an offer.",
            "You will receive an interview.",
            "You will receive a job.",
            "You will get an offer.",
            "You will get an interview.",
            "You will get a job.",
            "You will secure an offer.",
            "You will secure an interview.",
            "You will secure a job.",
            "You will land an offer.",
            "You will land an interview.",
            "You will land a job.",
            "You will get hired.",
            "This course will get you hired.",
            "An offer is likely.",
            "An offer is expected.",
            "An offer is probable.",
            "An offer is guaranteed.",
            "An interview is likely.",
            "An interview is expected.",
            "An interview is probable.",
            "An interview is guaranteed.",
            "A job is likely.",
            "A job is expected.",
            "A job is probable.",
            "A job is guaranteed.",
            "You are likely to get an offer.",
            "You are likely to get an interview.",
            "You are likely to get a job.",
            "You are likely to receive an offer.",
            "You are likely to receive an interview.",
            "You are likely to receive a job.",
            "You are likely to secure an offer.",
            "You are likely to secure an interview.",
            "You are likely to secure a job.",
            "You are likely to land an offer.",
            "You are likely to land an interview.",
            "You are likely to land a job.",
            "You are likely to be hired.",
            "You will be hired.",
            "This course will guarantee an interview.",
            "This course will guarantee a job.",
            "This course will guarantee an offer.",
            "This course will lead to an interview.",
            "This course will lead to a job.",
            "This course will lead to an offer.",
            "This course will increase your interview rate by 20%.",
            "This course will increase your chance of getting a job by 20%.",
            "This course will increase your offer rate by 20%.",
            "This certificate will increase your salary by 20%.",
            "This course will reduce time-to-hire by 20%.",
            "This plan will improve ROI by 20%.",
            "This plan will deliver 2x ROI.",
            "This course gives you a 20% chance of getting an interview.",
            "This certificate guarantees a 20% salary increase.",
            "This course will increase your salary 20%.",
            "This plan will double ROI.",
            "This course will cut time-to-hire in half.",
            "This course will halve time-to-hire.",
            "This certificate will raise your salary.",
            "This plan will improve ROI.",
            "Salary will increase.",
            "ROI will improve.",
            "This course will increase interviews.",
            "This course will increase offers.",
            "This course will increase jobs.",
            "This course will shorten hiring time.",
            "This course will improve the hiring process.",
            "This course will lead to more interviews.",
            "This course will make you more likely to get a job.",
            "This certificate guarantees a salary increase.",
            "This plan guarantees ROI.",
            "This course guarantees shorter time-to-hire.",
            "This certificate ensures a salary increase.",
            "This plan ensures improved ROI.",
            "This course ensures shorter time-to-hire.",
            "This certificate causes a salary increase.",
            "This plan causes improved ROI.",
            "This course causes shorter time-to-hire.",
            "This certificate leads to a salary increase.",
            "This plan leads to improved ROI.",
            "This course leads to shorter time-to-hire.",
            "This certificate results in a salary increase.",
            "This plan results in improved ROI.",
            "This course results in shorter time-to-hire.",
            "Salary is likely to increase after this certificate.",
            "ROI is expected to improve after this plan.",
            "Time-to-hire is probable to decrease after this course.",
            "Salary is guaranteed to increase after this certificate.",
            "A salary increase is likely after this certificate.",
            "A salary increase is expected after this certificate.",
            "A salary increase is probable after this certificate.",
            "A salary increase is guaranteed after this certificate.",
            "ROI improvement is likely after this plan.",
            "ROI improvement is expected after this plan.",
            "ROI improvement is probable after this plan.",
            "ROI improvement is guaranteed after this plan.",
            "Shorter time-to-hire is likely after this course.",
            "Shorter time-to-hire is expected after this course.",
            "Shorter time-to-hire is probable after this course.",
            "Shorter time-to-hire is guaranteed after this course.",
            "Salary will increase by 20% after this certificate.",
            "ROI will improve by 20% after this plan.",
            "Time-to-hire will decrease by 20% after this course.",
            "This plan guarantees a 20% ROI improvement.",
            "This course guarantees a 20% reduction in time-to-hire.",
            "Time-to-hire is 2–6 weeks.",
            "Expected time-to-hire: 4 weeks.",
            "The plan makes the search 10–25% faster.",
            "The credential gets you an offer 2–6 weeks sooner.",
            "Expect an interview within 4 weeks.",
            "Time-to-hire will fall after this course.",
            "Time-to-hire will drop after this course.",
            "Time-to-hire will decrease after this course.",
            "Time-to-hire will improve after this course.",
            "Time-to-hire will shorten after this course.",
            "Time-to-hire will accelerate after this course.",
            "Expect an offer within 3 weeks.",
            "Expect a job within 6 weeks.",
            "No doubt this course will get you a job.",
            "I cannot deny this course guarantees an offer.",
            "This course will not guarantee a job, but it will get you an offer.",
            "There is no evidence this course guarantees an interview; however, you will land an offer.",
            "We cannot say this course will get you a job. Yet a job is expected.",
            "There is no evidence that an offer is likely, but you will get hired.",
            "We cannot say that this plan will deliver 2x ROI; however, this course will increase your salary by 20%.",
            "No doubt this certificate guarantees a salary increase.",
            "I cannot deny this plan guarantees ROI.",
            "It is not impossible that this course guarantees shorter time-to-hire.",
            "There is no evidence that salary is likely to increase after this certificate, but this certificate guarantees a salary increase.",
            "We cannot say that this plan guarantees ROI; however, ROI is expected to improve after this plan.",
        )
        for refusal in safe_refusals:
            self.assertFalse(
                self.has_unsupported_prediction(refusal),
                f"Safe refusal rejected: {refusal}",
            )
        for prediction in unsupported_predictions:
            self.assertTrue(
                self.has_unsupported_prediction(prediction),
                f"Unsupported prediction accepted: {prediction}",
            )

    def test_learning_baseline_records_certificate_collecting_and_stale_price_failures(self) -> None:
        baseline = (REPO_ROOT / "tests" / "evals" / "baseline" / "learning.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("fork_turns=none", baseline)
        self.assertIn("no repository or Professional Growth Coach skill access", baseline)
        self.assertIn("Browsed: yes", baseline)
        self.assertIn("## Senior Kubernetes/SRE", baseline)
        self.assertIn("## Retail manager to Enterprise Account Executive", baseline)
        self.assertIn("### Verbatim full raw output", baseline)

        self.assertIn("10–25% faster", baseline)
        self.assertIn("2–6 weeks sooner", baseline)
        for finding in (
            "unsupported hiring-speed or roi prediction",
            "certificate collecting",
            "source comparability",
            "what the baseline did well",
            "official provider pages",
            "source_state",
            "do nothing now",
        ):
            self.assertIn(finding, baseline.lower())

        for fixture_name in (
            "fixtures/learning-sre.md",
            "fixtures/learning-enterprise-ae.md",
        ):
            self.assertIn(f"Fixture: `{fixture_name}`", baseline)
            fixture_path = REPO_ROOT / "tests" / "evals" / "baseline" / fixture_name
            self.assertTrue(fixture_path.is_file(), f"Missing exact fixture: {fixture_path}")
            fixture = fixture_path.read_text(encoding="utf-8")
            for field in (
                "## Exact prompt",
                "## Exact target-vacancy evidence",
                "## Exact candidate facts",
                "## Exact constraints",
                "## Exact action request",
            ):
                self.assertIn(field, fixture)

    def test_learning_baseline_preserves_both_complete_raw_transcripts(self) -> None:
        baseline = (REPO_ROOT / "tests" / "evals" / "baseline" / "learning.md").read_text(
            encoding="utf-8"
        )
        transcripts = (
            (
                "Senior Kubernetes/SRE",
                "<!-- BASELINE RAW A START -->",
                "<!-- BASELINE RAW A END -->",
                "Current prices as of August 6, 2026. All amounts are USD; taxes may be added at checkout.",
                "- https://training.linuxfoundation.org/certification/certified-kubernetes-administrator-cka/",
                "514bdee32f2dd97b16899a73249ef8e4e5a73646ca47c579ff4598738ae02603",
            ),
            (
                "Retail manager to Enterprise Account Executive",
                "<!-- BASELINE RAW B START -->",
                "<!-- BASELINE RAW B END -->",
                "Current prices as of August 6, 2026. All amounts are USD; certification taxes may be added at checkout.",
                "- https://trailhead.salesforce.com/content/learn/modules/sales-contracts-and-negotiation-quick-look",
                "06282fe71e904c0df2f9b11613b4216c3499bf009b9ae037ff32b20d95efff8d",
            ),
        )
        for name, start, end, first_line, last_line, expected_hash in transcripts:
            self.assertEqual(1, baseline.count(start), f"Missing unique start anchor for {name}")
            self.assertEqual(1, baseline.count(end), f"Missing unique end anchor for {name}")
            raw = baseline.split(start, 1)[1].split(end, 1)[0].strip()
            self.assertTrue(raw.startswith(first_line), f"Truncated transcript start for {name}")
            self.assertTrue(raw.endswith(last_line), f"Truncated transcript end for {name}")
            self.assertEqual(
                expected_hash,
                hashlib.sha256(raw.encode("utf-8")).hexdigest(),
                f"Raw transcript changed or was truncated for {name}",
            )


class TrackJobSearchOutcomesContractTests(unittest.TestCase):
    def test_outcome_tracking_skill_uses_deterministic_summary_and_causal_warnings(self) -> None:
        skill_root = (
            REPO_ROOT
            / "plugins"
            / "professional-growth-coach"
            / "skills"
            / "track-career-outcomes"
        )
        skill_path = skill_root / "SKILL.md"
        agent_path = skill_root / "agents" / "openai.yaml"
        measurement_path = skill_root / "references" / "measurement.md"
        asset_path = skill_root / "assets" / "outcomes.csv"
        script_path = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts" / "summarize_outcomes.py"

        self.assertTrue(skill_path.is_file(), f"Missing skill: {skill_path}")
        self.assertTrue(agent_path.is_file(), f"Missing UI metadata: {agent_path}")
        self.assertTrue(measurement_path.is_file(), f"Missing reference: {measurement_path}")
        self.assertTrue(asset_path.is_file(), f"Missing asset: {asset_path}")
        self.assertTrue(script_path.is_file(), f"Missing script: {script_path}")

        text = skill_path.read_text(encoding="utf-8")
        metadata = parse_simple_frontmatter(text)
        self.assertEqual(metadata["name"], "track-career-outcomes")
        self.assertTrue(metadata["description"].startswith("Use when "))
        self.assertIn("references/measurement.md", text)
        self.assertIn("assets/outcomes.csv", text)
        self.assertIn("summarize_outcomes.py", text)

        contract = text + measurement_path.read_text(encoding="utf-8")
        for prefix in ("verified:", "candidate-reported:", "inferred:", "unknown:"):
            self.assertIn(prefix, contract)
        for field in (
            "window_days",
            "applications",
            "responses",
            "interviews",
            "offers",
            "response_rate",
            "interview_rate",
            "offer_rate",
            "days_to_first_interview",
            "warnings",
            "outreach_diagnostics",
            "operating_review",
            "weekly_strategy_decision",
            "weekly_strategy_branch",
            "coach_funnel_strategy_review",
            "next_cycle_decision_rule",
            "review_window",
            "primary_bottleneck",
            "decision",
            "decision_rationale",
            "pause",
            "repeat",
            "fix",
            "prepare",
            "measure_next",
            "evidence_required",
            "source_summary",
            "current_strategy",
            "funnel_health",
            "next_experiment",
            "metric_to_watch",
            "trigger_signal",
            "minimum_evidence",
            "next_safe_action",
            "blocked_action",
            "metric_to_log",
            "review_gate",
            "authorization_gate",
            "measurement_event",
            "outreach_source",
            "sequence_step",
            "bottleneck",
            "next_experiment",
            "stop_condition",
            "causality_boundary",
            "optimize-professional-profile",
            "prepare-role-interviews",
        ):
            self.assertIn(field, contract)
        for boundary in (
            "application_id",
            "candidate_id",
            "benchmark_consent=true",
            "--candidate-id",
            "duplicate",
            "inclusive",
            "0001-01-01",
            "as_of.toordinal()",
            "future dates",
            "chronology",
            "does not prove causality",
            "simultaneous interventions",
            "multiple currencies",
            "Never perform FX conversion",
            "unknown interview stages",
            "LinkedIn outreach",
            "linkedin_outreach",
            "measurement_event",
            "intervention_id",
            "samples under 10",
            "anonymized benchmarking",
            "exits `2`",
            "no traceback",
        ):
            self.assertIn(boundary, contract)

        expected_header = (
            "application_id,candidate_id,application_date,response_date,"
            "interview_date,interview_stage,offer_date,currency,role,geography,"
            "source,referral,asset_version,intervention_id,confounders,"
            "simultaneous_interventions,benchmark_consent"
        )
        self.assertEqual(
            expected_header,
            asset_path.read_text(encoding="utf-8").splitlines()[0],
        )

    def test_outcome_evals_record_baseline_and_forward_safety(self) -> None:
        baseline = (REPO_ROOT / "tests" / "evals" / "baseline" / "outcomes.md").read_text(
            encoding="utf-8"
        )
        baseline_fixture = (
            REPO_ROOT
            / "tests"
            / "evals"
            / "baseline"
            / "fixtures"
            / "outcomes-causality-and-benchmarking.md"
        ).read_text(encoding="utf-8")
        forward = (REPO_ROOT / "tests" / "evals" / "with-skill" / "outcomes.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("fork_turns=none", baseline)
        self.assertIn("repository, files, browser, web, tools, and skills", baseline)
        exact_prompt = baseline_fixture.split("## Exact prompt", 1)[1].split(
            "## Isolation contract", 1
        )[0].strip()
        recorded_prompt = baseline.split("## Exact prompt", 1)[1].split(
            "Normalized prompt intent", 1
        )[0].strip()
        self.assertEqual(exact_prompt, recorded_prompt)
        raw = baseline.split("## Raw full output", 1)[1].split(
            "## Observed behavior", 1
        )[0].strip()
        self.assertTrue(raw.startswith("You cannot validly prove"))
        self.assertTrue(raw.endswith("not estimable from the supplied data."))
        self.assertEqual(
            "dd9d79c457ec2b57ad4f215f1008dbfef49df977494c02213b6903c34dc38bae",
            hashlib.sha256(raw.encode("utf-8")).hexdigest(),
        )
        self.assertIn("prove that my headline change caused an offer", baseline)
        self.assertIn("false causal attribution", baseline.lower())

        for section in (
            "data_quality",
            "funnel_summary",
            "experiment_readout",
            "outreach_diagnostics",
            "operating_review",
            "warnings",
            "next_measurement_step",
        ):
            self.assertGreaterEqual(forward.count(section), 5)
        for fixture_name in (
            "outcomes-sparse.csv",
            "outcomes-confounded.csv",
            "outcomes-currency.csv",
            "outcomes-linkedin-outreach.csv",
            "outcomes-two-candidate-consented.csv",
            "outcomes-two-candidate-no-consent.csv",
        ):
            fixture_path = (
                REPO_ROOT / "tests" / "evals" / "with-skill" / "fixtures" / fixture_name
            )
            self.assertTrue(fixture_path.is_file(), f"Missing outcome fixture: {fixture_path}")
            self.assertIn(f"fixtures/{fixture_name}", forward)
            self.assertIn(
                f"tests/evals/with-skill/fixtures/{fixture_name} --window 30 --as-of 2026-08-06",
                forward,
            )
        self.assertEqual(8, forward.count("```json"))
        self.assertIn("does not prove causality", forward)
        self.assertIn("outreach_diagnostics: inferred:", forward)
        self.assertIn("operating_review: inferred:", forward)
        for field in (
            "measurement_event=LI-FIRST-002",
            "outreach_source=linkedin_outreach",
            "sequence_step=2",
            "bottleneck=",
            "next_experiment=",
            "stop_condition=",
            "causality_boundary=descriptive_only_no_causal_claim",
            "review_window=30 days",
            "primary_bottleneck=response_to_recruiter_conversation_bridge_without_recruiter_screen",
            "decision=fix_recruiter_bridge_before_more_volume",
            "pause=generic_follow_up_volume",
            "repeat=stable_role_geography_source_asset_version",
            "fix=fact_checked_recruiter_summary_and_qualification_question",
            "prepare=screening_bridge_practice",
            "measure_next=qualified_replies_and_recruiter_screens",
            "evidence_required=matching_outreach_funnel_row",
            "authorization_gate=draft_only_until_candidate_approves_exact_action_and_target",
            "weekly_strategy_decision=coach_funnel_strategy_review",
            "decision=revise",
            "current_strategy=manual_named_recruiter_context_sequence_with_stable_role_geography_source_and_asset",
            "metric_to_watch=qualified_replies_and_recruiter_screens",
            "privacy_boundary=single_candidate_only_no_benchmark_without_consent",
            "authorization_gate=exact_action_and_target_required_before_external_action",
            "weekly_strategy_branch=next_cycle_decision_rule",
            "branch=continue",
            "branch=revise",
            "branch=pause",
            "branch=research",
            "branch=stop",
            "blocked_action=",
            "review_gate=",
        ):
            self.assertIn(field, forward)
        self.assertEqual(5, forward.count("weekly_strategy_branch=next_cycle_decision_rule"))
        self.assertEqual([], load_static_checker().validate_weekly_strategy_decision_quality(forward))
        self.assertIn("no currency conversion was performed", forward)
        self.assertIn("candidate_id=candidate-001", forward)
        self.assertIn("candidate_id=candidate-002", forward)
        self.assertIn("exact-field zero-count safety summary", forward)
        for candidate_id in ("candidate-001", "candidate-002"):
            self.assertIn(
                "outcomes-two-candidate-no-consent.csv --window 30 "
                f"--as-of 2026-08-06 --candidate-id {candidate_id}",
                forward,
            )
        self.assertIn("the two isolated summaries remain separate", forward)
        self.assertIn("no cross-candidate rate is reported", forward)

    def test_outcome_evals_require_weekly_strategy_decision_ladder(self) -> None:
        forward = (REPO_ROOT / "tests" / "evals" / "with-skill" / "outcomes.md").read_text(
            encoding="utf-8"
        )
        checker = load_static_checker()

        weak_output = "\n".join(
            line
            for line in forward.splitlines()
            if "weekly_strategy_decision=" not in line
            and "weekly_strategy_branch=" not in line
        )
        errors = checker.validate_weekly_strategy_decision_quality(weak_output)

        self.assertTrue(
            any("weekly_strategy_decision" in error for error in errors),
            errors,
        )


    def test_conversion_outcome_contract_is_candidate_observation_only(self) -> None:
        """Keep the new receipt descriptive and isolated from execution routes."""
        skill = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "skills" / "track-career-outcomes" / "SKILL.md"
        ).read_text(encoding="utf-8")
        linkedin = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "skills" / "optimize-professional-profile" / "SKILL.md"
        ).read_text(encoding="utf-8")
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        combined = "\n".join((skill, linkedin, routing))
        for event, action in (
            ("contact_received", "clarify_context_before_reply"),
            ("reply_received", "clarify_context_before_reply"),
            ("referral_received", "prepare_fact_checked_summary"),
            ("screen_requested", "route_to_prepare-role-interviews"),
            ("interview_requested", "route_to_prepare-role-interviews"),
            ("stop_decision", "record_stop_decision"),
        ):
            self.assertIn(event, combined)
            self.assertIn(action, combined)
        for phrase in (
            "candidate-supplied observation only",
            "no candidate identity",
            "no aggregation",
            "no causality",
            "manual next step",
            "no auto-start",
            "no module packet",
            "no send",
            "no calendar",
        ):
            self.assertIn(phrase, combined.casefold())

    def test_conversion_outcome_does_not_replace_ordinary_routes_or_csv(self) -> None:
        skill = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "skills" / "track-career-outcomes" / "SKILL.md"
        ).read_text(encoding="utf-8")
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        self.assertIn("outcomes.csv", skill)
        self.assertIn("summarize_outcomes.py", skill)
        self.assertIn("normal csv", skill.casefold())
        self.assertIn("normal recruiter-reply behavior remains unchanged", routing)
        self.assertIn("when the request is not explicit", routing)

    def test_followthrough_checkpoint_is_replay_safe_and_gates_preparation(self) -> None:
        track = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "skills" / "track-career-outcomes" / "SKILL.md"
        ).read_text(encoding="utf-8")
        prepare = (
            REPO_ROOT / "plugins" / "professional-growth-coach" / "skills" / "prepare-role-interviews" / "SKILL.md"
        ).read_text(encoding="utf-8")
        routing = ROOT_ROUTING_REFERENCE.read_text(encoding="utf-8")
        combined = "\n".join((track, prepare, routing)).casefold()
        for phrase in (
            "private-recruiter-followthrough-checkpoint-v1",
            "replay",
            "idempotent",
            "completed",
            "screen_requested",
            "interview_requested",
            "manual cue",
            "declined",
            "stop_decision",
            "block preparation",
            "accepted",
            "deferred",
            "no auto-start",
            "ordinary csv",
            "ordinary recruiter-reply",
        ):
            self.assertIn(phrase, combined, phrase)
        self.assertIn("reprocessing the same receipt and checkpoint is idempotent", combined)
        self.assertIn("replay of the same receipt/checkpoint pair is idempotent", combined)
        self.assertIn("same receipt/checkpoint pair idempotently", combined)


if __name__ == "__main__":
    unittest.main()
