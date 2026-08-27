# Plan: private JSON loader hardening

## Goal

Ensure extreme JSON inputs cannot bypass opaque private CLI boundaries or emit
runtime tracebacks.

## Task 1 — Loader implementation and black-box tests

Harden `load_triage` in
`build_private_recruiter_triage_practice_handoff.py`, `load_handoff` in
`validate_private_recruiter_triage_practice_handoff.py`, and `load_triage` in
`validate_private_recruiter_reply_triage.py`: catch `ValueError`, enforce
`_assert_max_depth` after decoding, and preserve existing typed errors. Add
subprocess and library tests for oversized integers, deep nesting, and no-echo
traceback invariants while keeping valid fixtures green.

## Task 2 — Documentation and regression matrix

Document the shared loader invariant in README and the relevant preparation/
triage reference. Extend static/privacy checks or focused tests so all three
entry points are covered, including duplicate-key, symlink, size, UTF-8, and
opaque error contracts.

## Task 3 — Release, install, and publication

Bump cachebuster, install and smoke-test all three private loaders, verify
source/cache parity and provenance, run plugin/static/privacy/release/root
suites, obtain independent release review, then push
`git push origin HEAD:main` and verify remote equality.

## Verification

- Focused loader/subprocess tests and `git diff --check`.
- Plugin/static/privacy/release gates and exact source/cache parity.
- Full root suite and installed extreme-input smoke with no traceback.
