# Reproducible release validation

The release validation contract is macOS arm64 with CPython 3.11.15. It uses an
ignored, repository-local environment and the sole locked dependency in
`requirements/release-validation.txt`. The bootstrap does not upgrade pip or
install unrelated packages; its install contract is
`--require-hashes --only-binary=:all: --no-deps`.

From the repository root, create or refresh the environment:

```bash
bash scripts/bootstrap_release_validation.sh
```

The executable release runner verifies these SHA-256 digests before either
validator can execute:

- `quick_validate.py`: `1fd66498c219616fd9249eacdf16c458412ea9065a9d887fd716aeef03907762`
- `validate_plugin.py`: `6ff4bc1cc8ca94827c30c8299951efdac900ff38a5069c03e9a6554fc194a723`

After the initial checks, the runner copies both validators into a private
temporary directory, re-hashes those copies, and executes only the verified
copies. This keeps the release gate stable if an input path changes while the
remaining checks are running.

With `CODEX_SYSTEM_SKILLS_ROOT` set to the system skills directory, run:

```bash
bash scripts/run_release_validation.sh
```

Before changing the plugin manifest, run the repository integration gates from
the repository root:

```bash
python3 -B -m unittest tests.test_plugin_structure tests.test_repository_privacy -v
python3 -B plugins/professional-growth-coach/tests/run_static_checks.py
python3 -B scripts/check_repository_privacy.py
```

The static gate treats the executive dossier schema, validator, renderer,
source registry, HTML/CSS assets, and skill reference as one installed-relative
package. It rejects direct, broken, and intermediate symlinks; parses the schema
and registry; requires one bounded inline style and script; and executes the
package-local validator and renderer from an unrelated directory against a
valid fixture plus an invalid mutation. It also rejects network-capable asset
tokens, verifies generated output paths stay ignored, and revalidates the
pressure-summary source hashes. The privacy gate scans committed evaluation
evidence and an explicit dossier schema/validator/renderer/assets/test inventory.
Any generated dossier artifact forced into the Git index is read from its
immutable stage-zero blob by object ID, with regular-file, size, and UTF-8 checks;
ordinary ignored, unstaged artifacts remain local. Findings expose only path,
rule ID, and count.

The dossier's deterministic content boundary is deliberately explicit. Every
unsupported technology from the request must be recorded in
`requested_technology_terms`, bound to the exact claim IDs and evidence paraphrases;
the validator rejects an unbound or unsupported requested technology in ready copy.
This deterministic boundary extracts arbitrary explicit expertise/specialist promotions
from ready copy after Unicode-format normalization and requires an exact ledger term plus
a bound allowed claim. Because raw requests are not retained, requested technologies that
are both omitted from the ledger and never promoted as expertise cannot be reconstructed
later; the skill contract therefore requires every explicitly requested technology to be
populated before validation.
Identity labels, self-introductions, raw-copy indicators, contacts, profile URLs,
and structured identity fields are rejected. Contextual person/company
disclosures (for example, a named person paired with `described` or a company
paired with `works at`) are also rejected before triage rendering. A standalone
proper name still cannot be distinguished reliably from a product, role, or
organization without the original private profile or a per-candidate denylist,
either of which would violate this identity-free package boundary. Therefore
upstream evidence must still be paraphrased and redacted before construction.
Because the triage locale contract is limited to `en`/`es`, prose letters from
unsupported writing systems are rejected as well; future multilingual support
must replace that guard with an explicit locale-aware redaction policy. The
validator's fixed privacy booleans are not proof about undeclared external input.

Only after those gates and independent review pass may the source manifest move
to the approved release version and describe evidence-backed private HTML
LinkedIn diagnostics. Re-run the integration gates, the full test suite, and the
checksum-gated official validators on that exact tree. The marketplace file must
remain byte-identical, and this release-validation workflow does not install the
plugin or modify its cache or Codex configuration.

Any interpreter, wheel, requirements hash, or official-validator digest change
requires an explicit lock and evidence update. Do not satisfy this release gate
from a global Python installation or a mutable developer dependency cache.
