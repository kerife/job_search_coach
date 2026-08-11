# Case Provenance ID Type Guard Design

## Goal

Prevent non-scalar provenance handles from passing the isolated case contract
when optional record IDs are supplied.

## Design

Keep the existing optionality of `source_id`, `claim_id`, `intervention_id`,
and `outcome_id` so current fixtures remain compatible. In `_validate_records`,
when the record-specific ID field is present, require a non-empty string and
emit a deterministic path-specific diagnostic. Do not require new IDs, infer
formats, or enforce uniqueness in this increment.

## Alternatives

- Requiring every ID would improve completeness but break existing canonical
  fixtures and expand the contract beyond the demonstrated bug.
- Coercing numbers/objects to strings would create ambiguous handles and weaken
  provenance, so it is rejected.
- Schema-only changes would leave the CLI validator permissive, so runtime and
  test coverage are the authoritative boundary here.

## Acceptance

- Supplied dict/list/int/bool IDs return `rc=2` with a fixed path diagnostic.
- Diagnostics do not echo the malformed value or private content.
- Omitted IDs and valid string IDs preserve existing behavior.
- Focused, static, privacy, full, release, publish, and install gates remain
  green.
