# Private JSON UTF-8 boundary design

## Problem

The private triage, practice, follow-through checkpoint, and conversion-outcome
loaders catch filesystem errors and JSON syntax errors, but an invalid UTF-8
file raises `UnicodeDecodeError` before the loader's bounded error contract.
The CLI can therefore emit a traceback instead of a deterministic, privacy-safe
input error.

## Decision

Catch `UnicodeError` at the same loader boundary as `OSError`/JSON decoding for
all four private JSON surfaces. Re-raise the existing surface-specific
`*LoadError` with the generic `input is not valid JSON` message. Keep the
existing return code, schema checks, size limits, and valid UTF-8 output
unchanged.

## Acceptance

- A one-byte invalid UTF-8 input exits with code 3.
- stderr contains only the existing generic surface-specific invalid-JSON
  message; it contains no traceback or decoder details.
- Direct loader calls raise the surface-specific load error.
- Existing valid, malformed-JSON, symlink, and size-limit tests remain green.
- No renderer HTML, schema, copy, ID, action, or external side effect changes.

## Verification boundary

This is an input/diagnostic contract change; browser screenshots are not needed.
The release must still pass the plugin validator, static/privacy gates, full
plugin tests, root tests, source/cache parity, installed renderer smoke, and
provenance checks.
