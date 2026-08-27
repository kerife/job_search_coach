# Plan: private CLI receipt hardening

## Goal

Close the direct CLI data channel without changing library-level behavior or
the private HTML artifact contract.

## Task 1 — Renderer CLI boundary

Introduce a private argument parser/error path in
`render_recruiter_practice_session.py`. Keep `write_session_html` and
`RenderReceipt` unchanged for library callers, but make `_cli` emit a fixed
opaque JSON receipt and fixed bounded errors. Add subprocess tests for success,
unknown arguments, invalid paths, and sentinel values; assert no path,
question, summary, URL, contact, ID, snapshot, or credential reaches stdout or
stderr.

## Task 2 — Validator CLI boundary and docs

Apply the same non-echoing parser/error contract to
`validate_recruiter_practice_session.py`, add focused subprocess coverage, and
document the distinction between rich library receipts and opaque direct CLI
receipts in README and the interview-preparation reference. Preserve existing
diagnostic behavior for bounded, fixed validation messages.

## Task 3 — Release, install, and publication

Bump the plugin cachebuster, install and smoke-test the plugin, verify source
and cache parity, run plugin/static/privacy/release/root suites, refresh the
immediate-parent attestation, obtain independent release review, then execute
the authorized `git push origin HEAD:main` and verify remote equality.

## Verification

- Focused renderer/validator subprocess tests and `git diff --check`.
- Plugin static/privacy/release gates and plugin test suite.
- `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -p 'test_*.py' -q`.
- Source/cache parity and installed smoke with opaque receipts.
