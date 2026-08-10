# Require explicit conversion reference dates

## Goal

Make the private recruiter conversion validator and renderer CLI outcomes
reproducible by requiring an explicit `--as-of YYYY-MM-DD` reference date.

## Design

Change only the two CLI parsers so `--as-of` is required. Existing library APIs
and direct renderer calls may still use their current optional `today`/`as_of`
parameters for compatibility. Missing or malformed CLI dates use the existing
input-error code 3; `--help` remains code 0. A supplied date is passed through
unchanged and future events continue to be rejected relative to it.

No schema, artifact fields, routing, rendering copy, or external actions change.

## Verification

Add RED tests for missing `--as-of` on validator and renderer, then assert GREEN
for valid injected dates, malformed dates, help, and future-date rejection.
Run focused conversion tests, static checks, and installed CLI smoke.
