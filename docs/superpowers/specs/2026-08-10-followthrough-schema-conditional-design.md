# Follow-through schema conditional invariants

## Goal

Make the JSON Schema for `private_recruiter_followthrough_checkpoint_v1`
enforce the same action/event invariants as the Python validator, so schema-only
consumers cannot accept an inconsistent checkpoint.

## Design

Add Draft 2020-12 `allOf` conditionals to the existing closed schema:

- `accepted`, `deferred`, and `declined` require `next_measurement_event` to be
  `unknown` and their exact `next_safe_action` constants.
- `completed` with `screen_prepared` or `interview_requested` requires
  `route_to_prepare-role-interviews`.
- `completed` with `stop_decision` requires `record_stop_decision`.
- Other completed events require `clarify_context_before_reply`.

The Python validator remains authoritative for cross-artifact receipt/date
checks; this change only closes the schema-level state mapping gap. No renderer,
routing, delivery, or free-form fields change.

## Verification

Add schema-only mutation tests using `jsonschema.Draft202012Validator` for every
valid mapping branch and representative wrong action/event combinations. Existing
Python validator and renderer tests must remain green.
