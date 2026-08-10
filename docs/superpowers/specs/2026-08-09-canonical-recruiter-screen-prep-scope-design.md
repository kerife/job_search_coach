# Canonical recruiter-screen preparation scope

## Goal

Make every ready recruiter-reply `prep_scope` directly assignable to
`practice.question.kind`. The `screen_invite` route must use the same closed
literal from triage question through handoff packet, reentry packet, and
practice question. The handoff remains a partial, manual input and does not
construct a complete practice session by itself.

## Decision

Adopt `screen_opening` as the only canonical value. Remove
`recruiter_screen_opening` from the triage schema, validator, renderer lookup,
fixtures, and tests. Reject the removed alias rather than accepting or
normalizing two representations indefinitely.

This is an intentional fail-closed migration of the repository-internal 0.x
contract. The handoff is manual, `local_save_mode=disabled`, raw replies are
not retained, and no automatic transfer or external action exists. The
repository contains no durable consumer or adapter for the alias. Before
implementation, scan the repository and active plugin installation again. If
any durable consumer outside managed plugin caches is identified, stop the
in-place change and publish a versioned triage/reentry migration instead.
Otherwise, existing manually retained artifacts containing the alias are
intentionally incompatible and must be regenerated from the canonical
contract.

## Contract and data flow

For each ready triage classification, `question.kind`,
`handoff.packet.prep_scope`, `handoff.reentry_packet.prep_scope`, and the
resulting `practice.question.kind` use one identical value:

| Triage classification | Canonical value |
| --- | --- |
| `screen_invite` | `screen_opening` |
| `request_for_proof` | `proof_example` |
| `eligibility_question` | `eligibility_boundary` |
| `compensation_question` | `compensation_boundary` |
| `unknown` | `missing_detail` |

The validator compares the packet and reentry values directly with
`question.kind`; no special translation table remains. Packet and reentry
continue to require exact parity with one another and preserve all existing
Q/F/context/snapshot, unanswered-state, no-save, no-auto-start, and
no-external-action invariants.

## Rendering

Visible output does not change. `screen_opening` maps to the existing localized
labels `Screen opening` and `Apertura de filtro` in both the preparation-scope
and reentry-scope surfaces. The raw enum remains absent from candidate-facing
HTML and accessibility text. The other four scope labels and all sequencing,
privacy, responsive, print, and forced-colors behavior remain unchanged.

## Failure behavior

- `recruiter_screen_opening` is invalid in either packet.
- A packet or reentry scope that differs from `question.kind` is invalid.
- Packet and reentry scopes that differ from one another are invalid.
- No compatibility fallback silently rewrites malformed or unknown values.
- Validation fails before rendering. Manual practice-session construction may
  reuse validated packet fields for their corresponding context and handoff
  references. This migration makes only `prep_scope` directly assignable to
  `practice.question.kind`; all remaining required practice fields must still
  be supplied and independently validated.

## Verification

Use TDD with a table-driven cross-contract test covering all five ready
classifications. Start from a complete validator-approved practice fixture and
copy only the validated reentry `prep_scope` into `practice.question.kind`;
the `screen_invite` case must fail before implementation and all five must pass
after the migration. Every subcase asserts literal equality across
`question.kind`, packet scope, reentry scope, and `practice.question.kind`,
while retaining triage source, `snap-triage-*`, and `question_rank=1` handoff
invariants. The test does not claim that the reentry packet supplies the full
practice requirement, question text, or fact summary.

Add negative coverage proving that `recruiter_screen_opening` is rejected by
the triage schema and Python validator in two independent cases: alias only in
the packet with canonical reentry, and alias only in reentry with canonical
packet. Each case must assert its field-specific enum error, so one closed
definition cannot mask an alias still accepted by the other.
Preserve renderer assertions for the localized screen-opening label, existing `aria-labelledby` and
`aria-describedby` relationships, heading/region order, and absence of both
the canonical and removed raw enums from visible or accessible text. No HTML
or CSS changes are permitted outside the closed localization lookup needed for
the canonical key. Run the triage validator and renderer suites,
recruiter-practice integration suite, private schema-conformance gate, full
plugin tests, static checks, and `git diff --check` before publication.

## Non-goals

Do not expand practice enums, add an adapter, change candidate-facing copy,
start practice automatically, retain reply/answer content, expose internal
identifiers, or authorize messaging, calendar, contact, or other external
actions.
