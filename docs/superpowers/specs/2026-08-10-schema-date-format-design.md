# Enforce real calendar dates in private schemas

## Goal

Ensure schema-only consumers reject impossible calendar dates in the private
recruiter conversion outcome and follow-through checkpoint artifacts.

## Design

Add Draft 2020-12 `format: "date"` to the existing `event_date` and
`observed_date` string properties while retaining their explicit ISO regexes.
Python validators remain responsible for injected `as_of` chronology and
calendar validation. No fields, renderer copy, routing, or persistence change.

## Verification

Add schema tests using `jsonschema.FormatChecker` proving valid fixture dates
pass and impossible dates such as `2026-02-30` fail for both schemas. Existing
runtime validator and renderer suites must stay green.
