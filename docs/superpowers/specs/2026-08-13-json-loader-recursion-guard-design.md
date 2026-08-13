# JSON Loader Recursion Guard Design

## Problem

Five supported JSON loaders call `json.loads()` before their existing
application-level nesting checks. On CPython 3.11, a valid ~2 KiB JSON array
with roughly 1,000 nested arrays raises `RecursionError` during decoding. The
CLI exits with a traceback instead of the validator's bounded input error.

## Decision

Catch `RecursionError` alongside the existing JSON decode and duplicate-key
errors in the five loaders:

- recruiter practice session
- private recruiter reply triage
- private recruiter conversion outcome
- private recruiter follow-through checkpoint/receipt loader
- executive career dossier

Map it to each loader's existing deterministic invalid-JSON/load error. Do not
raise the JSON nesting limit, add dependencies, interpolate input, or change
schemas. The existing `_assert_max_depth` checks remain authoritative for
decoded structures that fit within Python's decoder recursion budget.

## User-visible contract

- CLI return codes remain the loader's existing input-error code.
- stderr contains one stable safe message and no traceback or local path.
- Valid shallow JSON and existing malformed/duplicate-key behavior are
  unchanged.

## Verification

Add a shared test matrix that writes a bounded deeply nested JSON document and
invokes each loader/CLI boundary. Assert deterministic failure, no traceback,
and the loader-specific safe message. Keep a control case for the existing
`validate_case` behavior and run the full plugin, static, privacy, release, and
root suites before publishing.
