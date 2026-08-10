# LinkedIn fixture duplicate-key boundary

## Goal

Make the LinkedIn client-report fixture loader fail closed on duplicate JSON
object keys so hidden values cannot be overwritten before privacy and schema
validation.

## Evidence and scope

`validate_linkedin_client_report.load_bundle()` currently calls `json.loads`
without an `object_pairs_hook`. A fixture containing an unsafe first
`fixture_id` and a valid second `fixture_id` is therefore reduced to the last
value and accepted by both `validate_fixture_bundle()` and the CLI. The change
is limited to this loader boundary and its CLI parsing path; schemas, report
rendering, source registry behavior, and existing closed-field validation stay
unchanged.

## Design

Add a local ordered-pairs hook that raises the existing bounded `ValueError`
contract when a key repeats. Use that hook in both `load_bundle()` and the CLI
bundle parse so direct callers and command-line validation share the same
behavior. Diagnostics must be short and must not echo input values, paths, or
fixture contents. Regular JSON objects, nested objects, and arrays remain
accepted when their keys are unique.

## Acceptance

- A valid fixture still loads and validates unchanged.
- Duplicate top-level and nested keys raise a bounded duplicate-key error.
- A duplicate containing an email or other forbidden value is rejected before
  last-write-wins can hide it.
- The CLI exits nonzero with no accepted-bundle output and does not echo the
  duplicated value.
- Existing LinkedIn report, privacy, schema, and plugin tests remain green.
