"""Adversarial current-tree privacy contract for tracked evaluation evidence."""

from __future__ import annotations

import copy
import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNER_PATH = REPO_ROOT / "scripts" / "check_repository_privacy.py"
LINKEDIN_CLOSED_VOCABULARY_SCHEMA_PATH = (
    REPO_ROOT / "tests" / "fixtures" / "linkedin-closed-vocabulary.schema.json"
)
INVENTORY_PATHS = (
    Path("docs/superpowers/plans/2026-08-05-job-search-coach-plugin.md"),
    Path("docs/superpowers/plans/2026-08-07-linkedin-client-report-v2.md"),
    Path("tests/evals/final/installed-smoke-test.md"),
    Path("tests/evals/baseline/linkedin.md"),
    Path("tests/evals/with-skill/linkedin.md"),
)
REPLACED_MARKDOWN = (
    Path("tests/evals/baseline/linkedin.md"),
    Path("tests/evals/with-skill/linkedin.md"),
    Path("tests/evals/final/installed-smoke-test.md"),
    Path("tests/evals/final/cycle-1.md"),
    Path("tests/evals/final/cycle-2.md"),
)
REPLACED_DIRECTORIES = (
    Path("tests/evals/final/cycle-1"),
    Path("tests/evals/final/cycle-2"),
)
DOSSIER_FIXTURE_PATHS = (
    Path("tests/evals/with-skill/fixtures/executive-career-dossier/scenario-a-es.json"),
    Path("tests/evals/with-skill/fixtures/executive-career-dossier/scenario-c-en.json"),
)
RECRUITER_PRACTICE_FIXTURE_PATH = (
    REPO_ROOT
    / "tests"
    / "evals"
    / "with-skill"
    / "fixtures"
    / "recruiter-practice-session"
    / "session-es.json"
)
DOSSIER_SOURCE_INVENTORY_PATHS = (
    Path("plugins/professional-growth-coach/schemas/executive-career-dossier-v1.schema.json"),
    Path("plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/scripts/render_executive_career_dossier.py"),
    Path("plugins/professional-growth-coach/assets/executive-career-dossier-v1.html"),
    Path("plugins/professional-growth-coach/assets/executive-career-dossier-v1.css"),
    Path("tests/test_executive_career_dossier.py"),
)


def load_scanner():
    specification = importlib.util.spec_from_file_location(
        "job_search_coach_repository_privacy", SCANNER_PATH
    )
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load repository privacy scanner: {SCANNER_PATH}")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def replaced_paths() -> tuple[Path, ...]:
    paths = list(REPLACED_MARKDOWN)
    for directory in REPLACED_DIRECTORIES:
        paths.extend(
            path.relative_to(REPO_ROOT)
            for path in sorted((REPO_ROOT / directory).iterdir())
            if path.is_file() and path.suffix.lower() in {".json", ".md"}
        )
    return tuple(paths)


def invalid_dossier_with_private_analytics_container() -> dict[str, object]:
    return {
        "schema_version": "executive-career-dossier-v1",
        "analytics": {
            "state": "not_requested",
            "reason": "Not requested.",
            "profile_views": {"value": "PRIVATE-MARKER"},
        },
        "privacy": {
            "raw_private_analytics_included": False,
            "aggregate_analytics_included": False,
        },
    }


class RepositoryPrivacyTests(unittest.TestCase):
    def test_recruiter_practice_validator_loader_restores_sys_path(self) -> None:
        scanner = load_scanner()
        previous_path = list(sys.path)
        scanner._load_recruiter_practice_validator.cache_clear()

        validator = scanner._load_recruiter_practice_validator()

        self.assertTrue(callable(validator))
        self.assertEqual(previous_path, sys.path)

    def test_valid_recruiter_session_elides_only_its_exact_safe_schema_markers(self) -> None:
        scanner = load_scanner()
        path = RECRUITER_PRACTICE_FIXTURE_PATH.relative_to(REPO_ROOT)
        session = json.loads(RECRUITER_PRACTICE_FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertNotIn("SECRET_ASSIGNMENT", scanner.scan_text(path, json.dumps(session)))

        for label, mutate in (
            (
                "true guard",
                lambda value: value["delivery"].__setitem__("external_actions_authorized", True),
            ),
            (
                "additional delivery field",
                lambda value: value["delivery"].__setitem__("unexpected", "value"),
            ),
            (
                "changed session marker",
                lambda value: value.__setitem__("session_kind", "private_recruiter_practice_changed"),
            ),
        ):
            with self.subTest(label=label):
                mutated = copy.deepcopy(session)
                mutate(mutated)
                violations = scanner.scan_text(path, json.dumps(mutated))
                self.assertGreater(violations["SECRET_ASSIGNMENT"], 0)

        prose_mutation = copy.deepcopy(session)
        prose_mutation["question"]["text"] = "authorization: Bearer synthetic-value-12345"
        self.assertGreater(
            scanner.scan_text(path, json.dumps(prose_mutation))["SECRET_ASSIGNMENT"], 0
        )

        invalid_json = RECRUITER_PRACTICE_FIXTURE_PATH.read_text(encoding="utf-8").replace(
            "false", "False", 1
        )
        self.assertGreater(scanner.scan_text(path, invalid_json)["SECRET_ASSIGNMENT"], 0)

    def test_force_staged_private_dossier_artifact_is_scanned_without_value_echo(self) -> None:
        scanner = load_scanner()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(
                ["git", "init", "--quiet"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            (root / ".gitignore").write_text(
                ".professional-growth-coach-artifacts/\n.superpowers/\n",
                encoding="utf-8",
            )
            artifact_path = Path(
                ".professional-growth-coach-artifacts/accidental-executive-dossier.json"
            )
            artifact = root / artifact_path
            artifact.parent.mkdir(parents=True)
            payload = {
                "candidate_name": "Synthetic Candidate",
                "contact_email": "synthetic@example.invalid",
                "analytics": {"profile_views": 42},
            }
            text = json.dumps(payload)
            artifact.write_text(text, encoding="utf-8")
            unstaged_path = Path(".superpowers/private-render.json")
            unstaged = root / unstaged_path
            unstaged.parent.mkdir(parents=True)
            unstaged.write_text(text, encoding="utf-8")
            subprocess.run(
                ["git", "add", "--force", artifact_path.as_posix()],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            staged_paths = scanner.staged_release_artifact_paths(root)
            self.assertIn(artifact_path, staged_paths)
            self.assertNotIn(unstaged_path, staged_paths)
            self.assertIn(artifact_path, scanner.scan_paths(root))
            violations = scanner.scan_text(artifact_path, text)

        for rule_id in ("NAME_FIELD", "EMAIL_ADDRESS", "PRIVATE_ANALYTICS_VALUE"):
            self.assertIn(rule_id, violations)
            finding = scanner.format_finding(
                artifact_path,
                rule_id,
                violations[rule_id],
            )
            self.assertNotIn("Synthetic Candidate", finding)
            self.assertNotIn("synthetic@example.invalid", finding)
            self.assertNotIn("42", finding)

    def test_force_staged_artifact_is_read_from_index_not_mutable_worktree(self) -> None:
        scanner = load_scanner()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            (root / ".gitignore").write_text(
                ".professional-growth-coach-artifacts/\n",
                encoding="utf-8",
            )
            relative = Path(".professional-growth-coach-artifacts/private.json")
            artifact = root / relative
            artifact.parent.mkdir(parents=True)
            artifact.write_text(
                json.dumps(
                    {
                        "candidate_name": "Synthetic Given Family",
                        "contact_email": "synthetic@example.invalid",
                        "profile_views": 42,
                    }
                ),
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "--force", relative.as_posix()],
                cwd=root,
                check=True,
            )
            artifact.write_text("{}", encoding="utf-8")

            indexed_text = scanner.read_staged_release_artifact_text(root, relative)
            violations = scanner.scan_text(relative, indexed_text)

        for rule_id in ("NAME_FIELD", "EMAIL_ADDRESS", "PRIVATE_ANALYTICS_VALUE"):
            self.assertIn(rule_id, violations)

    def test_privacy_cli_reads_captured_oids_and_detects_index_snapshot_change(self) -> None:
        scanner = load_scanner()
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            relative = Path(".professional-growth-coach-artifacts/private.json")
            artifact = root / relative
            artifact.parent.mkdir(parents=True)
            artifact.write_text(
                json.dumps({"candidate_name": "Synthetic Given Family"}),
                encoding="utf-8",
            )
            subprocess.run(
                ["git", "add", "--force", relative.as_posix()],
                cwd=root,
                check=True,
            )
            artifact.write_text("{}", encoding="utf-8")

            records = scanner.staged_release_artifact_snapshot(root)
            self.assertEqual(1, len(records))
            captured_oid = records[0].object_id
            artifact.write_text("{}", encoding="utf-8")
            subprocess.run(["git", "add", "--force", relative.as_posix()], cwd=root, check=True)

            captured_text = scanner.read_staged_release_artifact_text(root, records[0])
            self.assertIn("Synthetic Given Family", captured_text)
            current_records = scanner.staged_release_artifact_snapshot(root)
            self.assertNotEqual(captured_oid, current_records[0].object_id)

            snapshots = iter((records, current_records))
            scanner.staged_release_artifact_snapshot = lambda repo_root: next(snapshots)
            scanner.tracked_eval_paths = lambda repo_root: ()
            scanner.required_marker_paths = lambda repo_root: ()
            scanner.INVENTORY_PATHS = ()
            scanner.DOSSIER_SOURCE_INVENTORY_PATHS = ()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                result = scanner.main(["--repo-root", str(root)])

        self.assertEqual(1, result)
        self.assertIn("STAGED_INDEX_CHANGED", output.getvalue())

    def test_valid_closed_runtime_dossiers_admit_only_safe_analytics_sentinels(self) -> None:
        scanner = load_scanner()
        for path in DOSSIER_FIXTURE_PATHS:
            with self.subTest(path=path):
                text = (REPO_ROOT / path).read_text(encoding="utf-8")
                self.assertEqual({}, scanner.scan_text(path, text))

    def test_dossier_analytics_allowance_rejects_malicious_mutations_without_echo(self) -> None:
        scanner = load_scanner()

        def private_numeric_value(payload: dict[str, object]) -> str:
            payload["analytics"]["profile_view_count"] = 314
            return "314"

        def private_string_value(payload: dict[str, object]) -> str:
            payload["analytics"]["profile_view_count"] = "private-observation"
            return "private-observation"

        def extra_analytics_field(payload: dict[str, object]) -> str:
            payload["analytics"]["window"] = "not_observed"
            return "not_observed"

        def unsafe_analytics_state(payload: dict[str, object]) -> str:
            payload["analytics"]["state"] = "observed_aggregate"
            return "observed_aggregate"

        def arbitrary_dossier_kind(payload: dict[str, object]) -> str:
            payload["dossier_kind"] = "arbitrary_dossier"
            return "arbitrary_dossier"

        def raw_analytics_flag(payload: dict[str, object]) -> str:
            payload["privacy"]["raw_private_analytics_included"] = True
            return "True"

        def aggregate_analytics_flag(payload: dict[str, object]) -> str:
            payload["privacy"]["aggregate_analytics_included"] = True
            return "True"

        def nested_analytics_alias(payload: dict[str, object]) -> str:
            payload["analytics"]["payload"] = {"profile_views": 271}
            return "271"

        def raw_text_analytics_value(payload: dict[str, object]) -> str:
            payload["analytics"]["reason"] = "Profile views: 619."
            return "619"

        cases = (
            ("private numeric value", private_numeric_value),
            ("private string value", private_string_value),
            ("extra analytics field", extra_analytics_field),
            ("unsafe analytics state", unsafe_analytics_state),
            ("arbitrary dossier kind", arbitrary_dossier_kind),
            ("raw analytics flag", raw_analytics_flag),
            ("aggregate analytics flag", aggregate_analytics_flag),
            ("nested analytics alias", nested_analytics_alias),
            ("raw text analytics value", raw_text_analytics_value),
        )
        for path in DOSSIER_FIXTURE_PATHS:
            fixture = json.loads((REPO_ROOT / path).read_text(encoding="utf-8"))
            for label, mutate in cases:
                with self.subTest(path=path, label=label):
                    payload = copy.deepcopy(fixture)
                    private_value = mutate(payload)
                    violations = scanner.scan_text(
                        path,
                        json.dumps(payload, ensure_ascii=False),
                    )
                    self.assertIn("PRIVATE_ANALYTICS_VALUE", violations)
                    finding = scanner.format_finding(
                        path,
                        "PRIVATE_ANALYTICS_VALUE",
                        violations["PRIVATE_ANALYTICS_VALUE"],
                    )
                    self.assertNotIn(private_value, finding)

    def test_duplicate_key_json_keeps_conservative_structured_and_raw_scanning(self) -> None:
        scanner = load_scanner()
        dossier = (REPO_ROOT / DOSSIER_FIXTURE_PATHS[0]).read_text(encoding="utf-8")
        cases = (
            (
                "reviewer reproducer",
                '{"dup":1,"dup":2,"candidate_id":"CASE-ALPHA",'
                '"employer":"ORG-ALPHA","title":"ROLE-ALPHA",'
                '"location":"REGION-ALPHA"}',
                "SINGLING_OUT_STRUCTURED_COMBINATION",
                "CASE-ALPHA",
            ),
            (
                "nested duplicate",
                '{"record":{"dup":1,"dup":2,"candidate_id":"CASE-BETA",'
                '"employer":"ORG-BETA","title":"ROLE-BETA",'
                '"location":"REGION-BETA"}}',
                "SINGLING_OUT_STRUCTURED_COMBINATION",
                "CASE-BETA",
            ),
            (
                "duplicate identity key",
                '{"candidate_id":"CASE-OLD","candidate_id":"CASE-GAMMA",'
                '"employer":"ORG-GAMMA","title":"ROLE-GAMMA",'
                '"location":"REGION-GAMMA"}',
                "SINGLING_OUT_STRUCTURED_COMBINATION",
                "CASE-GAMMA",
            ),
            (
                "duplicate dossier key disables allowance",
                dossier.replace("{", '{"dup":1,"dup":2,', 1),
                "PRIVATE_ANALYTICS_VALUE",
                "No se solicitó una observación agregada.",
            ),
            (
                "duplicate key preserves raw analytics container",
                '{"dup":1,"dup":2,"profile_views":{"value":"PRIVATE-MARKER"}}',
                "PRIVATE_ANALYTICS_VALUE",
                "PRIVATE-MARKER",
            ),
        )
        for label, text, rule_id, private_value in cases:
            with self.subTest(label=label):
                violations = scanner.scan_text(Path("synthetic.json"), text)
                self.assertIn(rule_id, violations)
                finding = scanner.format_finding(Path("synthetic.json"), rule_id, violations[rule_id])
                self.assertNotIn(private_value, finding)

    def test_duplicate_ancestor_json_is_rejected_independent_of_value_order(self) -> None:
        scanner = load_scanner()
        sensitive = (
            '{"candidate_id":"CASE-ANCESTOR","employer":"ORG-ANCESTOR",'
            '"title":"ROLE-ANCESTOR","location":"REGION-ANCESTOR"}'
        )
        cases = (
            ("reviewer reproducer", f'{{"record":{sensitive},"record":{{}}}}'),
            ("reversed values", f'{{"record":{{}},"record":{sensitive}}}'),
            (
                "nested overwritten ancestor",
                f'{{"envelope":{{"record":{sensitive},"record":{{}}}}}}',
            ),
            (
                "nested reversed ancestor",
                f'{{"envelope":{{"record":{{}},"record":{sensitive}}}}}',
            ),
        )
        for label, text in cases:
            with self.subTest(label=label):
                violations = scanner.scan_text(Path("synthetic.json"), text)
                self.assertIn("DUPLICATE_JSON_KEY", violations)
                finding = scanner.format_finding(
                    Path("synthetic.json"),
                    "DUPLICATE_JSON_KEY",
                    violations["DUPLICATE_JSON_KEY"],
                )
                self.assertNotIn("CASE-ANCESTOR", finding)

    def test_dossier_validator_return_contract_fails_closed_without_echo(self) -> None:
        scanner = load_scanner()
        fixture = invalid_dossier_with_private_analytics_container()

        class TruthyReturn:
            def __bool__(self) -> bool:
                return True

        class EmptyListSubclass(list):
            pass

        cases = (
            ("none", None),
            ("empty string", ""),
            ("empty tuple", ()),
            ("empty dict", {}),
            ("empty set", set()),
            ("empty list subclass", EmptyListSubclass()),
            ("non-string list entry", [1]),
            ("truthy custom object", TruthyReturn()),
        )
        for label, validator_result in cases:
            with self.subTest(label=label):
                scanner._load_dossier_validator = (
                    lambda result=validator_result: lambda value: result
                )
                violations = scanner.scan_text(
                    Path("synthetic.json"),
                    json.dumps(fixture),
                )
                self.assertIn("PRIVATE_ANALYTICS_VALUE", violations)
                finding = scanner.format_finding(
                    Path("synthetic.json"),
                    "PRIVATE_ANALYTICS_VALUE",
                    violations["PRIVATE_ANALYTICS_VALUE"],
                )
                self.assertNotIn("PRIVATE-MARKER", finding)

    def test_dossier_validator_exceptions_fail_closed_without_echo(self) -> None:
        scanner = load_scanner()
        text = json.dumps(invalid_dossier_with_private_analytics_container())

        for boundary in ("load", "call"):
            for exception_type in (SyntaxError, RuntimeError, UnicodeError):
                with self.subTest(boundary=boundary, exception=exception_type.__name__):
                    if boundary == "load":
                        def raising_loader(error=exception_type):
                            raise error("PRIVATE-MARKER")

                        scanner._load_dossier_validator = raising_loader
                    else:
                        def raising_validator(value, error=exception_type):
                            raise error("PRIVATE-MARKER")

                        scanner._load_dossier_validator = lambda: raising_validator
                    violations = scanner.scan_text(Path("synthetic.json"), text)
                    self.assertIn("PRIVATE_ANALYTICS_VALUE", violations)
                    finding = scanner.format_finding(
                        Path("synthetic.json"),
                        "PRIVATE_ANALYTICS_VALUE",
                        violations["PRIVATE_ANALYTICS_VALUE"],
                    )
                    self.assertNotIn("PRIVATE-MARKER", finding)

    def test_dossier_validator_does_not_swallow_process_control_exceptions(self) -> None:
        scanner = load_scanner()
        text = json.dumps(invalid_dossier_with_private_analytics_container())
        for exception_type in (KeyboardInterrupt, SystemExit):
            with self.subTest(boundary="load", exception=exception_type.__name__):
                def raising_loader(error=exception_type):
                    raise error("process control")

                scanner._load_dossier_validator = raising_loader
                with self.assertRaises(exception_type):
                    scanner.scan_text(Path("synthetic.json"), text)
            with self.subTest(boundary="call", exception=exception_type.__name__):
                def raising_validator(value, error=exception_type):
                    raise error("process control")

                scanner._load_dossier_validator = lambda: raising_validator
                with self.assertRaises(exception_type):
                    scanner.scan_text(Path("synthetic.json"), text)

    def test_scope_is_git_backed_and_includes_the_five_exact_inventory_paths(self) -> None:
        scanner = load_scanner()
        expected = (
            set(scanner.tracked_eval_paths(REPO_ROOT))
            | set(INVENTORY_PATHS)
            | set(DOSSIER_SOURCE_INVENTORY_PATHS)
            | set(scanner.staged_release_artifact_paths(REPO_ROOT))
        )
        self.assertEqual(expected, set(scanner.scan_paths(REPO_ROOT)))
        self.assertEqual(5, len(INVENTORY_PATHS))
        self.assertEqual(
            set(DOSSIER_SOURCE_INVENTORY_PATHS),
            set(scanner.DOSSIER_SOURCE_INVENTORY_PATHS),
        )

    def test_dossier_source_inventory_uses_non_overbroad_source_scanning(self) -> None:
        scanner = load_scanner()
        for path in DOSSIER_SOURCE_INVENTORY_PATHS:
            with self.subTest(path=path):
                text = (REPO_ROOT / path).read_text(encoding="utf-8")
                self.assertEqual({}, scanner.scan_repository_source_text(path, text))

        private_source = (
            'candidate_name = "Nonplaceholder Given Family"\n'
            'contact_email = "person@private.example"\n'
        )
        violations = scanner.scan_repository_source_text(
            Path("plugins/professional-growth-coach/scripts/example.py"),
            private_source,
        )
        self.assertIn("NAME_FIELD", violations)
        self.assertIn("EMAIL_ADDRESS", violations)

    def test_nfkc_format_char_and_bounded_escape_decoding_cannot_hide_values(self) -> None:
        scanner = load_scanner()
        cases = {
            "fullwidth-and-format": "ｌｉｎｋｅｄｉｎ．ｃｏｍ／ｉｎ／synthetic\u200bdecoy",
            "url-encoded": "%6c%69%6e%6b%65%64%69%6e%2e%63%6f%6d%2f%69%6e%2fsynthetic-decoy",
            "double-url-encoded": "%256c%2569%256e%256b%2565%2564%2569%256e%252e%2563%256f%256d%252f%2569%256e%252fsynthetic-decoy",
            "json-escaped": r"linkedin\u002ecom\u002fin\u002fsynthetic-decoy",
        }
        for label, text in cases.items():
            with self.subTest(label=label):
                self.assertIn(
                    "LINKEDIN_PROFILE_URL",
                    scanner.scan_text(Path("synthetic.md"), text),
                )

    def test_decoded_json_scalars_and_canonical_rendering_are_scanned(self) -> None:
        scanner = load_scanner()
        payload = {
            "no_real_profile_mapping": True,
            "nested": {
                "value": "linkedin.com\\u002fin\\u002fsynthetic-decoy",
            },
        }
        violations = scanner.scan_text(
            Path("synthetic.json"), json.dumps(payload)
        )
        self.assertIn("LINKEDIN_PROFILE_URL", violations)

    def test_private_value_rule_families_cover_schemeless_and_cross_line_forms(self) -> None:
        scanner = load_scanner()
        cases = {
            "schemeless-profile": ("linkedin.com/in/synthetic-decoy", "LINKEDIN_PROFILE_URL"),
            "handle": ("profile_handle: @synthetic-decoy", "SOCIAL_HANDLE"),
            "email": ("contact: person@example.invalid", "EMAIL_ADDRESS"),
            "phone": ("contact: +1 (202) 555-0199", "PHONE_NUMBER"),
            "local-path": ("evidence: /Users/synthetic/private.txt", "LOCAL_USER_PATH"),
            "secret": ("access_token = SYNTHETIC_SECRET_VALUE_123", "SECRET_ASSIGNMENT"),
            "analytics-forward": ("profile views\nvalue: 314", "PRIVATE_ANALYTICS_VALUE"),
            "analytics-reverse": ("314 observations\nsearch appearances", "PRIVATE_ANALYTICS_VALUE"),
            "name-field": ("display_name: Synthetic Person", "NAME_FIELD"),
        }
        for label, (text, rule_id) in cases.items():
            with self.subTest(label=label):
                self.assertIn(rule_id, scanner.scan_text(Path("synthetic.md"), text))

    def test_release_version_timestamp_is_not_misclassified_as_phone(self) -> None:
        scanner = load_scanner()
        self.assertNotIn(
            "PHONE_NUMBER",
            scanner.scan_text(
                Path("synthetic.md"),
                "installed_cache_version: 0.2.0+codex.20260813022934",
            ),
        )

    def test_current_private_aliases_and_literal_assignments_are_rejected(self) -> None:
        scanner = load_scanner()
        cases = {
            "analytics-snake-case": (
                '"profile_view_count": "JSC-SYNTHETIC-NUMERIC-SENTINEL"',
                "PRIVATE_ANALYTICS_VALUE",
            ),
            "analytics-spanish": (
                "visitas al perfil: JSC-SYNTHETIC-NUMERIC-SENTINEL",
                "PRIVATE_ANALYTICS_VALUE",
            ),
            "quoted-secret": (
                '"client_secret": "JSC-SYNTHETIC-SECRET-SENTINEL"',
                "SECRET_ASSIGNMENT",
            ),
            "free-form-target-name": (
                '"recruiter_target": "Synthetic Given Family"',
                "NAME_FIELD",
            ),
        }
        for label, (text, rule_id) in cases.items():
            with self.subTest(label=label):
                self.assertIn(rule_id, scanner.scan_text(Path("synthetic.md"), text))

    def test_normalized_key_families_reject_generic_private_aliases(self) -> None:
        scanner = load_scanner()
        cases = {
            "generic-secret": ('"secret": "JSC-SYNTHETIC-SECRET-SENTINEL"', "SECRET_ASSIGNMENT"),
            "given-name": ('"givenName": "Synthetic"', "NAME_FIELD"),
            "family-name": ('"family_name": "Example"', "NAME_FIELD"),
            "legal-name": ('"legalName": "Synthetic Example"', "NAME_FIELD"),
            "surname": ('"surname": "Example"', "NAME_FIELD"),
            "analytics-total": ('"profileVisitTotal": 314', "PRIVATE_ANALYTICS_VALUE"),
            "analytics-search-count": ('"search_result_count": 271', "PRIVATE_ANALYTICS_VALUE"),
        }
        for label, (text, rule_id) in cases.items():
            with self.subTest(label=label):
                self.assertIn(rule_id, scanner.scan_text(Path("synthetic.json"), text))

    def test_structured_cross_field_singling_out_is_rejected(self) -> None:
        scanner = load_scanner()
        payload = {
            "no_real_profile_mapping": True,
            "candidate_id": "JSC-CASE-ALPHA",
            "employer": "Example Organization",
            "title": "Example Role",
            "location": "Example Region",
            "observed_at": "2030-01-02",
            "metric": 314,
        }
        violations = scanner.scan_text(Path("synthetic.json"), json.dumps(payload))
        self.assertIn("SINGLING_OUT_STRUCTURED_COMBINATION", violations)

    def test_four_singling_out_dimensions_fail_without_an_identity_field(self) -> None:
        scanner = load_scanner()
        payload = {
            "employer": "JSC-ORGANIZATION-ALPHA",
            "title": "role_family_unknown",
            "location": "geography_bucket_unknown",
            "observed_at": "JSC-DATE-UNKNOWN",
        }
        violations = scanner.scan_text(Path("synthetic.json"), json.dumps(payload))
        self.assertIn("SINGLING_OUT_STRUCTURED_COMBINATION", violations)

    def test_nested_candidate_record_dimensions_are_aggregated(self) -> None:
        scanner = load_scanner()
        payload = {
            "candidate_record": {
                "work": {"employer": "JSC-ORGANIZATION-ALPHA"},
                "assignment": {"title": "role_family_unknown"},
                "place": {"location": "geography_bucket_unknown"},
                "timing": {"observed_at": "JSC-DATE-UNKNOWN"},
            }
        }
        violations = scanner.scan_text(Path("synthetic.json"), json.dumps(payload))
        self.assertIn("SINGLING_OUT_STRUCTURED_COMBINATION", violations)

    def test_every_nested_object_aggregates_normalized_dimension_families(self) -> None:
        scanner = load_scanner()
        anonymous = {
            "arbitrary_envelope": {
                "work": {"business_org_name": "JSC-ORGANIZATION-ALPHA"},
                "position": {"position_seniority_level": "role_family_unknown"},
                "place": {"home_geographic_area": "geography_bucket_unknown"},
                "timing": {"event_timestamp": "JSC-DATE-UNKNOWN"},
            }
        }
        identified = {
            "another_container": {
                "subject_reference": "JSC-CASE-ALPHA",
                "employing_entity": "JSC-ORGANIZATION-ALPHA",
                "job_role_label": "role_family_unknown",
                "team_scope_scale": "scope_bucket_unknown",
            }
        }
        for payload in (anonymous, identified):
            with self.subTest(keys=tuple(payload)):
                violations = scanner.scan_text(Path("synthetic.json"), json.dumps(payload))
                self.assertIn("SINGLING_OUT_STRUCTURED_COMBINATION", violations)

    def test_schema_marker_cannot_disable_nested_record_aggregation(self) -> None:
        scanner = load_scanner()
        payload = {
            "$schema": "https://example.test/synthetic-schema",
            "arbitrary_record": {
                "business_org_name": "JSC-ORGANIZATION-ALPHA",
                "position_seniority_level": "role_family_unknown",
                "home_geographic_area": "geography_bucket_unknown",
                "event_timestamp": "JSC-DATE-UNKNOWN",
            },
        }
        violations = scanner.scan_text(Path("synthetic.json"), json.dumps(payload))
        self.assertIn("SINGLING_OUT_STRUCTURED_COMBINATION", violations)

    def test_public_market_allowlist_requires_the_exact_parsed_row_schema(self) -> None:
        scanner = load_scanner()
        valid = (
            "market_public_source_row=vacancy_observation; source_id=JSC-SRC-001; "
            "source_url=https://example.invalid/public; role_family=platform; "
            "geography_bucket=region_alpha; observation_date=2030-01-02; "
            "compensation_bucket=band_beta; no_real_profile_mapping=true"
        )
        self.assertNotIn(
            "SINGLING_OUT_STRUCTURED_COMBINATION",
            scanner.scan_text(Path("tests/evals/with-skill/market.md"), valid),
        )
        self.assertIn(
            "SINGLING_OUT_STRUCTURED_COMBINATION",
            scanner.scan_text(Path("tests/evals/with-skill/linkedin.md"), valid),
        )
        near_miss = valid + "; candidate_id=JSC-CASE-ALPHA"
        self.assertIn(
            "SINGLING_OUT_STRUCTURED_COMBINATION",
            scanner.scan_text(Path("tests/evals/with-skill/market.md"), near_miss),
        )

    def test_non_mapping_marker_requires_boolean_true_or_exact_markdown_field(self) -> None:
        scanner = load_scanner()
        accepted = (
            (Path("fixture.json"), '{"no_real_profile_mapping": true}'),
            (Path("fixture.md"), "no_real_profile_mapping: true\n"),
        )
        rejected = (
            (Path("fixture.json"), '{"no_real_profile_mapping": false}'),
            (Path("fixture.json"), '{"no_real_profile_mapping": "true"}'),
            (Path("fixture.md"), "no_real_profile_mapping: false\n"),
            (Path("fixture.md"), "provenance_marker: no_real_profile_mapping\n"),
        )
        for path, text in accepted:
            self.assertTrue(scanner.has_true_non_mapping_marker(path, text))
        for path, text in rejected:
            self.assertFalse(scanner.has_true_non_mapping_marker(path, text))

    def test_linkedin_replacement_uses_the_exact_closed_vocabulary_schema(self) -> None:
        scanner = load_scanner()
        artifact_path = Path("tests/evals/with-skill/linkedin.md")
        artifact = (REPO_ROOT / artifact_path).read_text(encoding="utf-8")
        schema = json.loads(
            LINKEDIN_CLOSED_VOCABULARY_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        self.assertEqual([], scanner.validate_closed_vocabulary_artifact(artifact_path, artifact, schema))

        unapproved = artifact + "\nJSC-UNAPPROVED-FREE-FORM-SENTINEL sentence\n"
        errors = scanner.validate_closed_vocabulary_artifact(artifact_path, unapproved, schema)
        self.assertIn("CLOSED_VOCABULARY_TOKEN", errors)

    def test_tracked_plans_contain_no_residual_substitution_fragments(self) -> None:
        first_plan = (REPO_ROOT / INVENTORY_PATHS[0]).read_text(encoding="utf-8")
        second_plan = (REPO_ROOT / INVENTORY_PATHS[1]).read_text(encoding="utf-8")
        self.assertNotIn("JSC-FAMILY", first_plan)
        self.assertNotIn("priosrity", second_plan.casefold())
        self.assertNotIn("scenarios-", second_plan.casefold())
        for residual_instruction in (
            "legacy repository-local evidence",
            "preserves: legacy",
            "continues running its existing jenkins-specific legacy validators",
        ):
            self.assertNotIn(residual_instruction, second_plan.casefold())

    def test_all_replaced_artifacts_have_true_non_mapping_marker_and_no_live_claim(self) -> None:
        scanner = load_scanner()
        failures: list[str] = []
        for path in replaced_paths():
            text = (REPO_ROOT / path).read_text(encoding="utf-8")
            if not scanner.has_true_non_mapping_marker(path, text):
                failures.append(f"{path}: NON_MAPPING_MARKER")
            if path.suffix == ".json":
                artifact = json.loads(text)
                if artifact.get("artifact_kind") != "deterministic-regression-fixture":
                    failures.append(f"{path}: LIVE_PROVENANCE")
        if failures:
            self.fail("replacement violations (path and rule only):\n" + "\n".join(failures))

    def test_current_tree_privacy_gate_reports_only_path_rule_and_count(self) -> None:
        scanner = load_scanner()
        rendered = scanner.format_finding(
            Path("tests/evals/synthetic.md"),
            "SECRET_ASSIGNMENT",
            1,
        )
        self.assertEqual(
            "tests/evals/synthetic.md: SECRET_ASSIGNMENT: count=1",
            rendered,
        )
        result = subprocess.run(
            ["python3", "-B", str(SCANNER_PATH), "--repo-root", str(REPO_ROOT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for line in result.stdout.splitlines():
            self.assertRegex(line, r"^[^:]+: [A-Z0-9_]+: count=\d+$")


if __name__ == "__main__":
    unittest.main()
