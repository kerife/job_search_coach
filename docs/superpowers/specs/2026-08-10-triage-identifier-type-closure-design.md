# Triage Identifier Type Closure

## Context

The triage v1 and v2 Python validators require identifier and snapshot values to
be strings. Their JSON Schemas currently use `pattern` without `type: "string"`
on those same properties. A schema-only consumer can therefore accept a number
or boolean where the runtime validator rejects it.

## Design

Add `type: "string"` to every identifier or snapshot property whose contract is
already expressed by a string pattern in both triage schemas. Cover fact and
question IDs, fact-reference array items, handoff packet IDs, and snapshot
values. Keep the patterns, enums, closed objects, renderers, and v1/v2 payload
shapes unchanged.

## Acceptance

- Canonical triage v1 and mixed-locale triage v2 fixtures remain valid in both
  the custom validator and dependency-free schema checker.
- A numeric or boolean value in each identifier/snapshot field is rejected by
  both layers without echoing the value.
- Existing renderer output and privacy boundaries are unchanged.
- Focused schema, triage, plugin, root, privacy, static, and release gates pass.
