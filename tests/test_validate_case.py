"""Behavioral contract for the isolated Professional Growth Coach case validator."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "plugins" / "professional-growth-coach" / "scripts" / "validate_case.py"


CASE_ISOLATION_MUTATIONS = (
    (("unexpected",), True, "case has unsupported field: unexpected"),
    (("target", "unexpected"), True, "target has unsupported field: unexpected"),
    (
        ("sources", 0, "unexpected"),
        True,
        "sources[0] has unsupported field: unexpected",
    ),
    (
        ("interventions",),
        [{"candidate_id": "candidate-001", "unexpected": True}],
        "interventions[0] has unsupported field: unexpected",
    ),
    (
        ("outcomes",),
        [{"candidate_id": "candidate-001", "unexpected": True}],
        "outcomes[0] has unsupported field: unexpected",
    ),
    (
        ("target", "person_id"),
        "candidate-foreign",
        "target.person_id must match case candidate_id",
    ),
    (
        ("sources", 0, "metadata", "subject_id"),
        "candidate-foreign",
        "sources[0].metadata.subject_id must match case candidate_id",
    ),
    (("password",), "synthetic", "case contains sensitive key segment at password"),
    (
        ("consent", "session"),
        "synthetic",
        "case contains sensitive key segment at consent.session",
    ),
    (
        ("target", "contact"),
        "synthetic",
        "case contains sensitive key segment at target.contact",
    ),
    (
        ("sources", 0, "metadata", "api_key"),
        "synthetic",
        "case contains sensitive key segment at sources[0].metadata.api_key",
    ),
    (
        ("claims", 0, "metadata", "nested", "raw_profile"),
        "synthetic",
        "case contains sensitive key segment at claims[0].metadata.nested.raw_profile",
    ),
    (
        ("target", "constraints"),
        ["Authorization: Bearer SYNTHETIC_VALUE"],
        "case contains credential-shaped value at target.constraints[0]",
    ),
    (
        ("target", "constraints"),
        ["Authorization: Basic U1lOVEhFVElDX1ZBTFVF"],
        "case contains credential-shaped value at target.constraints[0]",
    ),
    (
        ("claims", 0, "text"),
        "password=SYNTHETIC_VALUE",
        "case contains credential-shaped value at claims[0].text",
    ),
    (
        ("interventions",),
        [
            {
                "candidate_id": "candidate-001",
                "description": "Contact person@example.invalid",
            }
        ],
        "case contains credential-shaped value at interventions[0].description",
    ),
    (
        ("outcomes",),
        [
            {
                "candidate_id": "candidate-001",
                "value": "Call +52 55 1234 5678",
            }
        ],
        "case contains credential-shaped value at outcomes[0].value",
    ),
    (
        ("claims", 0, "text"),
        "https://www.linkedin.com/in/synthetic-sentinel/",
        "case contains credential-shaped value at claims[0].text",
    ),
    (
        ("claims", 0, "text"),
        "Stored at /Users/synthetic/profile.txt",
        "case contains credential-shaped value at claims[0].text",
    ),
    (
        ("outcomes",),
        [
            {
                "candidate_id": "candidate-001",
                "benchmark_candidate_ids": ["candidate-foreign"],
            }
        ],
        "outcomes[0].benchmark_candidate_ids requires consent.benchmark=true",
    ),
)


def valid_case() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "candidate_id": "candidate-001",
        "mode": "self-service",
        "consent": {},
        "target": {"roles": ["Platform Engineer"]},
        "sources": [
            {
                "candidate_id": "candidate-001",
                "source_id": "source-001",
                "kind": "cv",
                "evidence_label": "candidate-reported",
            }
        ],
        "claims": [
            {
                "candidate_id": "candidate-001",
                "claim_id": "claim-001",
                "text": "Operates Kubernetes clusters.",
                "evidence_label": "verified",
            }
        ],
        "interventions": [],
        "outcomes": [],
    }


def set_path(root: object, path: tuple[object, ...], value: object) -> None:
    current = root
    for segment in path[:-1]:
        if isinstance(segment, int):
            assert isinstance(current, list)
            current = current[segment]
        else:
            assert isinstance(current, dict)
            if segment not in current:
                current[segment] = {}
            current = current[segment]
    final = path[-1]
    if isinstance(final, int):
        assert isinstance(current, list)
        current[final] = value
    else:
        assert isinstance(current, dict)
        current[final] = value


def run_validator(case: object) -> subprocess.CompletedProcess[str]:
    return run_validator_contents(json.dumps(case))


def run_validator_contents(contents: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        case_path = Path(temporary_directory) / "case.json"
        case_path.write_text(contents, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(case_path)],
            capture_output=True,
            text=True,
            check=False,
        )


def run_validator_bytes(contents: bytes) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as temporary_directory:
        case_path = Path(temporary_directory) / "case.json"
        case_path.write_bytes(contents)
        return subprocess.run(
            [sys.executable, str(VALIDATOR), str(case_path)],
            capture_output=True,
            text=True,
            check=False,
        )


def load_validator_module():
    specification = importlib.util.spec_from_file_location("validate_case", VALIDATOR)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class ValidateCaseTests(unittest.TestCase):
    def test_accepts_a_valid_isolated_case(self) -> None:
        result = run_validator(valid_case())

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_rejects_a_case_without_a_candidate_id(self) -> None:
        case = valid_case()
        del case["candidate_id"]

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "candidate_id is required\n")

    def test_rejects_an_invalid_evidence_label(self) -> None:
        case = valid_case()
        case["claims"] = [
            {
                "candidate_id": "candidate-001",
                "text": "Operates Kubernetes clusters.",
                "evidence_label": "observed",
            }
        ]

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertIn("claims[0].evidence_label must be one of", result.stderr)

    def test_rejects_linkedin_profile_url_without_scheme(self) -> None:
        values = (
            "https://www.linkedin.com/in/synthetic-sentinel/",
            "www.linkedin.com/in/synthetic-sentinel/",
            "linkedin.com/in/synthetic-sentinel/",
            "https://www.linkedin.com/pub/synthetic-sentinel/42/7b/123",
            "www.linkedin.com/pub/synthetic-sentinel/42/7b/123",
            "linkedin.com/pub/synthetic-sentinel/42/7b/123",
        )
        for value in values:
            with self.subTest(value=value):
                case = valid_case()
                case["claims"][0]["text"] = value

                result = run_validator(case)

                self.assertEqual(result.returncode, 2)
                self.assertIn(
                    "case contains credential-shaped value at claims[0].text",
                    result.stderr,
                )
                self.assertNotIn(value, result.stderr)

    def test_schema_version_must_be_exactly_one_point_zero(self) -> None:
        module = load_validator_module()
        for value in ("1.1", None):
            with self.subTest(value=value):
                case = valid_case()
                case["schema_version"] = value

                self.assertIn(
                    "schema_version must equal 1.0",
                    module.validate_case(case),
                )

    def test_defaults_benchmark_consent_to_false(self) -> None:
        module = load_validator_module()

        case = valid_case()
        normalized = module.normalize_case(case)

        self.assertIs(normalized["consent"]["benchmark"], False)
        self.assertNotIn("benchmark", case["consent"])

    def test_rejects_closed_schema_identity_and_sensitive_data_mutations(self) -> None:
        module = load_validator_module()
        for path, value, expected in CASE_ISOLATION_MUTATIONS:
            with self.subTest(path=path, expected=expected):
                case = valid_case()
                set_path(case, path, value)

                self.assertIn(expected, module.validate_case(case))

    def test_unicode_variants_cannot_mask_sensitive_identity_or_credential_data(self) -> None:
        module = load_validator_module()
        mutations = (
            (
                ("ｐａｓｓｗｏｒｄ",),
                "synthetic",
                "case contains sensitive key segment at ｐａｓｓｗｏｒｄ",
            ),
            (
                ("sources", 0, "metadata", "api\u200b_key"),
                "synthetic",
                "case contains sensitive key segment at sources[0].metadata.api\u200b_key",
            ),
            (
                ("target", "person‐id"),
                "candidate-foreign",
                "target.person‐id must match case candidate_id",
            ),
            (
                ("sources", 0, "metadata", "candidate\u200b_id"),
                "candidate-foreign",
                "sources[0].metadata.candidate\u200b_id must match case candidate_id",
            ),
            (
                ("claims", 0, "text"),
                "pass\u200bword=SYNTHETIC_VALUE",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "access‐key=SYNTHETIC_VALUE",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "client—secret: SYNTHETIC_VALUE",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "Stored at /private/synthetic/profile.txt",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "Stored at ~/synthetic/profile.txt",
                "case contains credential-shaped value at claims[0].text",
            ),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path, value=value):
                case = valid_case()
                set_path(case, path, value)

                self.assertIn(expected, module.validate_case(case))

    def test_compact_keys_combining_marks_assignments_and_local_paths_are_rejected(self) -> None:
        module = load_validator_module()
        mutations = (
            (
                ("APIKey",),
                "synthetic",
                "case contains sensitive key segment at APIKey",
            ),
            (
                ("APIKEY",),
                "synthetic",
                "case contains sensitive key segment at APIKEY",
            ),
            (
                ("pa\u0301ssword",),
                "synthetic",
                "case contains sensitive key segment at pa\u0301ssword",
            ),
            (
                ("claims", 0, "text"),
                "client.secret=SYNTHETIC_VALUE",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "access/key=SYNTHETIC_VALUE",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "api/key=SYNTHETIC_VALUE",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "Stored at /tmp/synthetic/profile.txt",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "Stored at /var/tmp/synthetic/profile.txt",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "Stored at ./synthetic/profile.txt",
                "case contains credential-shaped value at claims[0].text",
            ),
            (
                ("claims", 0, "text"),
                "Stored at ../synthetic/profile.txt",
                "case contains credential-shaped value at claims[0].text",
            ),
        )
        for path, value, expected in mutations:
            with self.subTest(path=path, value=value):
                case = valid_case()
                set_path(case, path, value)

                self.assertIn(expected, module.validate_case(case))

    def test_bare_authorization_schemes_distinguish_credentials_from_career_copy(self) -> None:
        module = load_validator_module()
        positives = (
            "Authorization: Bearer alphabeticprose",
            "Authorization: Basic alphabeticprose",
            "Basic dXNlcjpwYXNz",
            "Basic YTpi",
            "Basic dXNlcjpwYXNzIQ==",
            "Bearer eyJhbGciOiJIUzI1NiJ9.abc123_DEF456",
            "Bearer abcdefghijklmnopqrstuvwxyz012345",
        )
        negatives = (
            "Basic Python skills",
            "Basic troubleshooting",
            "Bearer of team responsibility",
            "basic skill set",
            "Basic C++ proficiency",
            "Basic CI/CD knowledge",
            "Basic day-to-day operations",
            "Basic tier-1 support",
            "Basic 24/7 support",
            "Bearer of-record responsibility",
            "Bearer abcdefghijklmnopqrstuvwxyzABCDEFGH",
        )
        for value in positives:
            with self.subTest(value=value, state="credential"):
                case = valid_case()
                case["claims"][0]["text"] = value
                self.assertIn(
                    "case contains credential-shaped value at claims[0].text",
                    module.validate_case(case),
                )
        for value in negatives:
            with self.subTest(value=value, state="prose"):
                case = valid_case()
                case["claims"][0]["text"] = value
                self.assertNotIn(
                    "case contains credential-shaped value at claims[0].text",
                    module.validate_case(case),
                )

    def test_authorization_headers_reject_any_nonempty_value(self) -> None:
        module = load_validator_module()
        credential_headers = (
            "Authorization: Digest realm=synthetic",
            "authorization: Token synthetic-value",
            "AUTHORIZATION: Negotiate synthetic-value",
            "Authorization: AWS4-HMAC-SHA256 synthetic-value",
            "Authorization: Custom synthetic-value",
            "Ａｕｔｈｏｒｉｚａｔｉｏｎ： Custom synthetic-value",
            "Author\u200bization∶ Custom synthetic-value",
            "Author\u2060ization﹕ Custom synthetic-value",
        )
        empty_headers = (
            "Authorization:",
            "authorization:   ",
            "Ａｕｔｈｏｒｉｚａｔｉｏｎ：",
            "Author\u200bization∶   ",
        )
        for value in credential_headers:
            with self.subTest(value=value, state="credential"):
                case = valid_case()
                case["claims"][0]["text"] = value
                self.assertIn(
                    "case contains credential-shaped value at claims[0].text",
                    module.validate_case(case),
                )
        for value in empty_headers:
            with self.subTest(value=value, state="empty"):
                case = valid_case()
                case["claims"][0]["text"] = value
                self.assertEqual([], module.validate_case(case))

    def test_recursive_validation_reports_cycles_without_crashing(self) -> None:
        module = load_validator_module()

        cyclic_mapping: dict[str, object] = {}
        cyclic_mapping["loop"] = cyclic_mapping
        cyclic_list: list[object] = []
        cyclic_list.append(cyclic_list)
        for value, suffix in (
            (cyclic_mapping, ".loop"),
            (cyclic_list, "[0]"),
        ):
            with self.subTest(entrypoint="validate_case", suffix=suffix):
                case = valid_case()
                case["target"]["constraints"] = value
                try:
                    errors = module.validate_case(case)
                except RecursionError:  # pragma: no cover - names totality regression
                    self.fail("validate_case leaked RecursionError for a cyclic container")
                self.assertIn(
                    f"case contains cyclic container at target.constraints{suffix}",
                    errors,
                )

        walkers = (
            ("json", lambda value: module._walk_json_domain(value, "")),
            ("safety", module._walk_sensitive_data),
            (
                "identity",
                lambda value: module._walk_identity_fields(
                    value,
                    "candidate-001",
                    False,
                ),
            ),
        )
        for walker_name, walker in walkers:
            for value, expected_path in (
                (cyclic_mapping, "loop"),
                (cyclic_list, "[0]"),
            ):
                with self.subTest(walker=walker_name, path=expected_path):
                    try:
                        errors = walker(value)
                    except RecursionError:  # pragma: no cover - names totality regression
                        self.fail(f"{walker_name} walker leaked RecursionError")
                    self.assertIn(
                        f"case contains cyclic container at {expected_path}",
                        errors,
                    )

    def test_compact_identity_aliases_remain_bound_to_the_case_candidate(self) -> None:
        module = load_validator_module()
        mutations = (
            ("PERSONID", "candidate-foreign"),
            ("personid", "candidate-foreign"),
            ("candidateid", "candidate-foreign"),
            ("CANDIDATEID", "candidate-foreign"),
            ("SUBJECTIDENTIFIERS", ["candidate-foreign"]),
            ("subjectidentifiers", ["candidate-foreign"]),
            ("PersonIdentifier", "candidate-foreign"),
            ("candidateIdentifiers", ["candidate-foreign"]),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                case = valid_case()
                case["target"][key] = value

                self.assertIn(
                    f"target.{key} must match case candidate_id",
                    module.validate_case(case),
                )

    def test_deep_acyclic_containers_return_path_specific_errors(self) -> None:
        module = load_validator_module()

        def nested_mapping(depth: int) -> dict[str, object]:
            root: dict[str, object] = {}
            current = root
            for _ in range(depth):
                nested: dict[str, object] = {}
                current["nested"] = nested
                current = nested
            return root

        def nested_list(depth: int) -> list[object]:
            root: list[object] = []
            current = root
            for _ in range(depth):
                nested: list[object] = []
                current.append(nested)
                current = nested
            return root

        walkers = (
            ("json", lambda value: module._walk_json_domain(value, "")),
            ("safety", module._walk_sensitive_data),
            (
                "identity",
                lambda value: module._walk_identity_fields(
                    value,
                    "candidate-001",
                    False,
                ),
            ),
        )
        for shape, value, path_fragment in (
            ("mapping", nested_mapping(1200), "nested.nested"),
            ("list", nested_list(1200), "[0][0]"),
        ):
            for walker_name, walker in walkers:
                with self.subTest(shape=shape, walker=walker_name):
                    try:
                        errors = walker(value)
                    except RecursionError:  # pragma: no cover - names totality regression
                        self.fail(f"{walker_name} walker leaked RecursionError")
                    self.assertTrue(
                        any(
                            error.startswith("case exceeds maximum nesting depth at ")
                            and path_fragment in error
                            for error in errors
                        ),
                        errors,
                    )

            with self.subTest(shape=shape, walker="validate_case"):
                case = valid_case()
                case["target"]["constraints"] = value
                try:
                    errors = module.validate_case(case)
                except RecursionError:  # pragma: no cover - names totality regression
                    self.fail("validate_case leaked RecursionError")
                self.assertTrue(
                    any(
                        error.startswith(
                            "case exceeds maximum nesting depth at target.constraints"
                        )
                        for error in errors
                    ),
                    errors,
                )

    def test_shared_acyclic_containers_are_not_reported_as_cycles(self) -> None:
        module = load_validator_module()
        shared = {"safe": "synthetic"}
        value = {"left": shared, "right": shared}
        walkers = (
            module._walk_sensitive_data,
            lambda item: module._walk_identity_fields(
                item,
                "candidate-001",
                False,
            ),
            lambda item: module._walk_json_domain(item, ""),
        )
        for walker in walkers:
            with self.subTest(walker=getattr(walker, "__name__", "json")):
                self.assertFalse(
                    any("cyclic container" in error for error in walker(value))
                )

    def test_cli_reports_deep_json_without_a_traceback(self) -> None:
        case = valid_case()
        nested: list[object] = []
        case["target"]["constraints"] = nested
        for _ in range(150):
            child: list[object] = []
            nested.append(child)
            nested = child

        result = run_validator_contents(json.dumps(case))

        self.assertEqual(2, result.returncode)
        self.assertTrue(
            result.stderr.startswith(
                "case exceeds maximum nesting depth at target.constraints"
            ),
            result.stderr,
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_malformed_object_values_return_path_specific_errors_deterministically(self) -> None:
        module = load_validator_module()
        cases = (
            (
                lambda case: case.__setitem__(1, "synthetic"),
                "case contains non-string key of type int at case",
            ),
            (
                lambda case: case["claims"][0].__setitem__("text", b"synthetic"),
                "case contains non-JSON value type bytes at claims[0].text",
            ),
        )
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                case = valid_case()
                mutate(case)
                try:
                    first = module.validate_case(case)
                    second = module.validate_case(case)
                except Exception as error:  # pragma: no cover - names totality regression
                    self.fail(f"malformed object leaked {type(error).__name__}")
                self.assertEqual(first, second)
                self.assertIn(expected, first)

    def test_non_string_key_errors_have_canonical_order_independent_of_insertion(self) -> None:
        module = load_validator_module()
        first = valid_case()
        first[1] = "synthetic"
        first[b"synthetic"] = "synthetic"
        second = valid_case()
        second[b"synthetic"] = "synthetic"
        second[1] = "synthetic"

        self.assertEqual(module.validate_case(first), module.validate_case(second))

    def test_benchmark_candidate_ids_require_a_list_of_non_empty_strings(self) -> None:
        module = load_validator_module()
        for value in ("candidate-002", None, ["candidate-002", None], [""]):
            with self.subTest(value=value):
                case = valid_case()
                case["consent"]["benchmark"] = True
                case["outcomes"] = [
                    {
                        "candidate_id": "candidate-001",
                        "outcome_id": "outcome-001",
                        "benchmark_candidate_ids": value,
                    }
                ]

                self.assertIn(
                    "outcomes[0].benchmark_candidate_ids must be a list of non-empty strings",
                    module.validate_case(case),
                )

    def test_rejects_mixed_candidate_ids_in_one_record(self) -> None:
        case = valid_case()
        case["sources"] = [
            {
                "candidate_id": "candidate-002",
                "source_id": "source-002",
                "kind": "cv",
                "evidence_label": "candidate-reported",
            }
        ]

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr,
            "sources[0].candidate_id must match case candidate_id\n",
        )

    def test_reports_multiple_errors_as_newline_delimited_records(self) -> None:
        case = valid_case()
        del case["schema_version"]
        case["mode"] = "batch"
        case["claims"][0].pop("evidence_label")
        case["interventions"] = [{
            "candidate_id": "candidate-002",
            "intervention_id": "intervention-002",
        }]

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr.splitlines(),
            [
                "schema_version is required",
                "mode must be self-service or coach",
                "claims[0].evidence_label must be one of: "
                "verified, candidate-reported, inferred, unknown",
                "interventions[0].candidate_id must match case candidate_id",
            ],
        )

    def test_rejects_a_non_object_json_document(self) -> None:
        result = run_validator(["candidate-001"])

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "case must be a JSON object\n")

    def test_rejects_malformed_json(self) -> None:
        result = run_validator_contents('{"candidate_id": ')

        self.assertEqual(result.returncode, 2)
        self.assertTrue(result.stderr.startswith("invalid case file: "))
        self.assertEqual(result.stderr.count("\n"), 1)

    def test_unreadable_input_does_not_echo_private_path(self) -> None:
        sentinel = "token_sk_live_SENTINEL_12345678901234567890"
        missing = Path(tempfile.gettempdir()) / sentinel
        result = subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), str(missing)],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "invalid case file: unable to read input\n")
        self.assertNotIn(sentinel, result.stderr)

    def test_rejects_symlink_input_without_reading_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            target = directory / "target.json"
            input_path = directory / "input.json"
            target.write_text(json.dumps(valid_case()), encoding="utf-8")
            input_path.symlink_to(target)

            result = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), str(input_path)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "invalid case file: unable to read input\n")
        self.assertNotIn("target.json", result.stderr)

    def test_rejects_intermediate_parent_symlink_without_reading_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            external = root / "external"
            alias = root / "alias"
            external.mkdir()
            target = external / "case.json"
            target.write_text(json.dumps(valid_case()), encoding="utf-8")
            alias.symlink_to(external, target_is_directory=True)

            result = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), str(alias / "case.json")],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "invalid case file: unable to read input\n")
        self.assertNotIn("candidate-001", result.stderr)

    def test_accepts_relative_regular_case_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            directory = Path(temporary_directory)
            (directory / "case.json").write_text(
                json.dumps(valid_case()), encoding="utf-8"
            )
            result = subprocess.run(
                [sys.executable, "-B", str(VALIDATOR), "case.json"],
                cwd=directory,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_case_input_over_safe_size_limit(self) -> None:
        oversized = valid_case()
        oversized["target"]["constraints"] = ["x" * 64_001]

        result = run_validator_bytes(json.dumps(oversized).encode("utf-8"))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr,
            "invalid case file: input exceeds safe size limit\n",
        )
        self.assertNotIn("x" * 100, result.stderr)

    def test_accepts_case_input_at_safe_size_limit(self) -> None:
        validator = load_validator_module()
        boundary_case = valid_case()
        boundary_case["target"]["constraints"] = [""]
        base_size = len(json.dumps(boundary_case).encode("utf-8"))
        boundary_case["target"]["constraints"] = [
            "x" * (validator.MAX_CASE_BYTES - base_size)
        ]
        encoded = json.dumps(boundary_case).encode("utf-8")

        self.assertEqual(len(encoded), validator.MAX_CASE_BYTES)
        result = run_validator_bytes(encoded)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_caps_cli_diagnostics_for_many_unsupported_keys(self) -> None:
        case = valid_case()
        case.update({f"u{index:04d}": "x" for index in range(3_000)})

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 16_384)
        self.assertIn(
            "validation diagnostics truncated; additional errors omitted\n",
            result.stderr,
        )
        self.assertNotIn("u2999", result.stderr)

    def test_caps_cli_diagnostic_for_one_long_key(self) -> None:
        case = valid_case()
        sentinel = "Z" * 60_000
        case[sentinel] = "x"

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertLessEqual(len(result.stderr.encode("utf-8")), 16_384)
        self.assertEqual(
            result.stderr,
            "validation diagnostics truncated; additional errors omitted\n",
        )
        self.assertNotIn(sentinel, result.stderr)

    def test_cli_diagnostic_cap_preserves_utf8_boundaries(self) -> None:
        case = valid_case()
        case.update({f"campo-ñ-{index:04d}": "x" for index in range(1_000)})

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        result.stderr.encode("utf-8").decode("utf-8")
        self.assertTrue(
            result.stderr.endswith(
                "validation diagnostics truncated; additional errors omitted\n"
            )
        )

    def test_cli_escapes_control_characters_in_unknown_field_diagnostics(self) -> None:
        case = valid_case()
        case["ordinary\nINJECTED\x1b[31m\x7f"] = "x"

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr,
            "case has unsupported field: ordinary\\u000aINJECTED\\u001b[31m\\u007f\n",
        )
        self.assertNotIn("\nINJECTED", result.stderr)
        self.assertNotIn("\x1b", result.stderr)

    def test_email_classifier_skips_values_without_at_sign(self) -> None:
        validator = load_validator_module()

        class UnexpectedEmailSearch:
            def search(self, value: str) -> object:
                raise AssertionError("email regex should not run without an at sign")

        original = validator._EMAIL_VALUE
        validator._EMAIL_VALUE = UnexpectedEmailSearch()
        try:
            self.assertFalse(validator._is_credential_shaped_value("a" * 64_000))
        finally:
            validator._EMAIL_VALUE = original

        self.assertFalse(validator._is_credential_shaped_value("a" * 64_000 + "@x"))

    def test_rejects_duplicate_top_level_key_without_echoing_hidden_content(self) -> None:
        contents = json.dumps(valid_case(), separators=(",", ":"))
        needle = '"claims":[{"candidate_id":"candidate-001","claim_id":"claim-001","text":"Operates Kubernetes clusters.","evidence_label":"verified"}]'
        replacement = (
            '"claims":[{"candidate_id":"candidate-001","claim_id":"claim-001","text":"https://www.linkedin.com/in/real-person/",'
            '"evidence_label":"verified"}],'
            + needle
        )
        self.assertIn(needle, contents)

        result = run_validator_contents(contents.replace(needle, replacement, 1))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "invalid case file: duplicate JSON key\n")
        self.assertNotIn("real-person", result.stderr)

    def test_rejects_duplicate_nested_key_without_echoing_key_name(self) -> None:
        contents = json.dumps(valid_case(), separators=(",", ":"))
        needle = '"candidate_id":"candidate-001","claim_id":"claim-001","text":"Operates Kubernetes clusters."'
        replacement = '"candidate_id":"candidate-leaked","candidate_id":"candidate-001","claim_id":"claim-001","text":"Operates Kubernetes clusters."'
        self.assertIn(needle, contents)

        result = run_validator_contents(contents.replace(needle, replacement, 1))

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "invalid case file: duplicate JSON key\n")
        self.assertNotIn("candidate_id", result.stderr)

    def test_rejects_sensitive_unsupported_keys_without_echoing_sentinels(self) -> None:
        cases = (
            (("jane@example.invalid",), "jane@example.invalid", "safe"),
            (("target", "contact_jane@example.invalid"), "contact_jane@example.invalid", "safe"),
            (("sources", 0, "token_sk_live_SENTINEL_12345678901234567890"), "token_sk_live_SENTINEL_12345678901234567890", "safe"),
            (("claims", 0, "jane@example.invalid"), "jane@example.invalid", "safe"),
            (("interventions",), "contact_jane@example.invalid", [{"candidate_id": "candidate-001", "contact_jane@example.invalid": "safe"}]),
            (("outcomes",), "token_sk_live_SENTINEL_12345678901234567890", [{"candidate_id": "candidate-001", "token_sk_live_SENTINEL_12345678901234567890": "safe"}]),
        )
        for path, sentinel, value in cases:
            with self.subTest(path=path):
                case = valid_case()
                set_path(case, path, value)

                result = run_validator(case)

                self.assertEqual(result.returncode, 2)
                self.assertNotIn(sentinel, result.stderr)
                self.assertTrue(result.stderr.strip(), result.stderr)

    def test_rejects_non_string_optional_provenance_ids(self) -> None:
        cases = (
            ("sources", "source_id"),
            ("claims", "claim_id"),
            ("interventions", "intervention_id"),
            ("outcomes", "outcome_id"),
        )
        for field, id_field in cases:
            for value in ({}, [], 7, True):
                with self.subTest(field=field, value=value):
                    case = valid_case()
                    case[field] = [{"candidate_id": "candidate-001", id_field: value}]
                    if field in {"sources", "claims"}:
                        case[field][0]["evidence_label"] = "verified"
                    result = run_validator(case)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn(
                        f"{field}[0].{id_field} must be a non-empty string",
                        result.stderr,
                    )
                    self.assertNotIn(str(value), result.stderr)

    def test_rejects_missing_provenance_ids(self) -> None:
        cases = (
            ("sources", "source_id"),
            ("claims", "claim_id"),
            ("interventions", "intervention_id"),
            ("outcomes", "outcome_id"),
        )
        for field, id_field in cases:
            with self.subTest(field=field):
                case = valid_case()
                if field == "sources":
                    case[field] = [{
                        "candidate_id": "candidate-001",
                        "kind": "cv",
                        "evidence_label": "verified",
                    }]
                elif field == "claims":
                    case[field] = [{
                        "candidate_id": "candidate-001",
                        "text": "Operates Kubernetes clusters.",
                        "evidence_label": "verified",
                    }]
                elif field == "interventions":
                    case[field] = [{
                        "candidate_id": "candidate-001",
                        "kind": "practice",
                        "description": "Private rehearsal",
                        "occurred_at": "2026-08-11",
                    }]
                else:
                    case[field] = [{
                        "candidate_id": "candidate-001",
                        "kind": "screen",
                        "value": "Observed",
                        "observed_at": "2026-08-11",
                    }]
                result = run_validator(case)
                self.assertEqual(result.returncode, 2)
                self.assertIn(
                    f"{field}[0].{id_field} is required",
                    result.stderr,
                )

    def test_rejects_duplicate_provenance_ids_without_echoing_values(self) -> None:
        cases = (
            (
                "sources",
                "source_id",
                [
                    {
                        "candidate_id": "candidate-001",
                        "source_id": "source-001",
                        "kind": "cv",
                        "evidence_label": "candidate-reported",
                    },
                    {
                        "candidate_id": "candidate-001",
                        "source_id": "source-001",
                        "kind": "article",
                        "evidence_label": "verified",
                    },
                ],
            ),
            (
                "claims",
                "claim_id",
                [
                    {
                        "candidate_id": "candidate-001",
                        "claim_id": "claim-001",
                        "text": "Operates Kubernetes clusters.",
                        "evidence_label": "verified",
                    },
                    {
                        "candidate_id": "candidate-001",
                        "claim_id": "claim-001",
                        "text": "Leads incident response.",
                        "evidence_label": "inferred",
                    },
                ],
            ),
            (
                "interventions",
                "intervention_id",
                [
                    {
                        "candidate_id": "candidate-001",
                        "intervention_id": "intervention-001",
                        "kind": "practice",
                        "description": "Private rehearsal",
                        "occurred_at": "2026-08-11",
                    },
                    {
                        "candidate_id": "candidate-001",
                        "intervention_id": "intervention-001",
                        "kind": "research",
                        "description": "Market evidence review",
                        "occurred_at": "2026-08-12",
                    },
                ],
            ),
            (
                "outcomes",
                "outcome_id",
                [
                    {
                        "candidate_id": "candidate-001",
                        "outcome_id": "outcome-001",
                        "kind": "screen",
                        "value": "Observed",
                        "observed_at": "2026-08-11",
                    },
                    {
                        "candidate_id": "candidate-001",
                        "outcome_id": "outcome-001",
                        "kind": "interview",
                        "value": "Advanced",
                        "observed_at": "2026-08-12",
                    },
                ],
            ),
        )
        for field, id_field, records in cases:
            with self.subTest(field=field):
                case = valid_case()
                case[field] = records
                result = run_validator(case)
                self.assertEqual(result.returncode, 2)
                self.assertIn(
                    f"{field}[1].{id_field} must be unique",
                    result.stderr,
                )
                self.assertNotIn(records[0][id_field], result.stderr)

    def test_cli_rejects_invalid_utf8_without_a_traceback(self) -> None:
        result = run_validator_bytes(b'{"candidate_id":"\xff"}')

        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertTrue(result.stderr.startswith("invalid case file: "), result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(1, result.stderr.count("\n"))

    def test_rejects_missing_evidence_label(self) -> None:
        case = valid_case()
        case["claims"][0].pop("evidence_label")

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr,
            "claims[0].evidence_label must be one of: "
            "verified, candidate-reported, inferred, unknown\n",
        )

    def test_rejects_mixed_ids_in_each_case_record_collection(self) -> None:
        for field in ("sources", "claims", "interventions", "outcomes"):
            with self.subTest(field=field):
                case = valid_case()
                record = {"candidate_id": "candidate-002"}
                record[
                    {
                        "sources": "source_id",
                        "claims": "claim_id",
                        "interventions": "intervention_id",
                        "outcomes": "outcome_id",
                    }[field]
                ] = f"{field[:-1]}-002"
                if field in {"sources", "claims"}:
                    record["evidence_label"] = "candidate-reported"
                case[field] = [record]

                result = run_validator(case)

                self.assertEqual(result.returncode, 2)
                self.assertEqual(
                    result.stderr,
                    f"{field}[0].candidate_id must match case candidate_id\n",
                )

    def test_rejects_benchmark_candidate_ids_without_benchmark_consent(self) -> None:
        case = valid_case()
        case["outcomes"] = [
            {
                "candidate_id": "candidate-001",
                "outcome_id": "outcome-001",
                "benchmark_candidate_ids": ["candidate-002"],
            }
        ]

        result = run_validator(case)

        self.assertEqual(result.returncode, 2)
        self.assertEqual(
            result.stderr,
            "outcomes[0].benchmark_candidate_ids requires consent.benchmark=true\n",
        )

    def test_accepts_benchmark_candidate_ids_with_benchmark_consent(self) -> None:
        case = valid_case()
        case["consent"]["benchmark"] = True
        case["outcomes"] = [
            {
                "candidate_id": "candidate-001",
                "outcome_id": "outcome-001",
                "benchmark_candidate_ids": ["candidate-002"],
            }
        ]

        result = run_validator(case)

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_revoking_benchmark_consent_invalidates_the_same_case(self) -> None:
        module = load_validator_module()
        case = valid_case()
        case["consent"]["benchmark"] = True
        case["outcomes"] = [
            {
                "candidate_id": "candidate-001",
                "outcome_id": "outcome-001",
                "benchmark_candidate_ids": ["candidate-002"],
            }
        ]

        self.assertEqual(module.validate_case(case), [])
        case["consent"]["benchmark"] = False
        self.assertIn(
            "outcomes[0].benchmark_candidate_ids requires consent.benchmark=true",
            module.validate_case(case),
        )

    def test_rejects_missing_or_extra_cli_arguments(self) -> None:
        for arguments in ([], ["case.json", "extra.json"]):
            with self.subTest(arguments=arguments):
                result = subprocess.run(
                    [sys.executable, str(VALIDATOR), *arguments],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stderr, "usage: validate_case.py CASE.json\n")


if __name__ == "__main__":
    unittest.main()
