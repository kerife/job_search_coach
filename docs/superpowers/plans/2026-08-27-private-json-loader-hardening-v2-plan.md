# Plan: uniform private JSON loader hardening v2

## Task 1 — validators and focused regressions

- Add `ValueError` to the JSON decode boundary in the four affected validators.
- Add oversized-integer fixtures/tests for direct loader and CLI paths, asserting
  typed errors, fixed `rc=3`, empty stdout, no traceback/raw echo.
- Run focused validator/renderer suites and compile checks.

## Task 2 — release gates and documentation

- Document the uniform failure boundary in README and relevant skill references.
- Run static/privacy/official validator gates and the full plugin/root suites.
- Verify no schema, HTML, CSS, IDs, URLs, controls, or external-action changes.

## Task 3 — install, attest, review, publish

- Bump the plugin cachebuster and install the exact local version.
- Verify source/cache parity, digest, installed oversized-integer smoke across all
  affected loaders/renderers, and provenance fixtures.
- Commit the attestation with `source_commit` set to its immediate parent.
- Obtain independent release review, push `HEAD:main`, and verify the remote ref.
