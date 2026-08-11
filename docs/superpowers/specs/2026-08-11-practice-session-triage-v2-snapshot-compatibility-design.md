# Practice Session v2 Triage Snapshot Compatibility

## Goal

Allow a recruiter-practice-session v2 handoff sourced from triage v2 to carry
the triage content-bound snapshot, without weakening the exact v1 contract.

## Contract

- `recruiter-practice-session-v1` remains unchanged and accepts only
  `snap-triage-###` for `private_recruiter_reply_triage`.
- `recruiter-practice-session-v2` accepts either legacy `snap-triage-###` or
  content-bound `snap-triage-sha256-<64 lowercase hexadecimal characters>` when
  `handoff_context.source=private_recruiter_reply_triage`.
- A v2 practice validator does not recompute the triage digest: the triage
  validator already binds that handle to the source triage payload. Practice
  validation continues checking source, question, requirement, fact, and
  delivery projections.
- Dossier source remains restricted to
  `snap-dossier-sha256-<64 lowercase hexadecimal characters>`.

## Privacy and rendering

The snapshot remains an internal handoff handle. Practice-session validators
must not echo it in errors or render it in HTML/chat. Existing renderer output
and no-external-action boundaries remain unchanged.

## Acceptance

1. A valid v2 practice session with a triage SHA-256 snapshot passes the Python
   validator and v2 JSON schema.
2. The same v2 shape with a malformed triage snapshot fails both contracts.
3. A v1 practice session with a triage SHA-256 snapshot still fails (legacy
   compatibility is exact).
4. Existing v1/v2 fixtures, practice renderer tests, and triage tests remain
   green.
