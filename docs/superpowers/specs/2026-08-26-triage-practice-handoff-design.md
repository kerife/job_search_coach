# Private triage-to-practice handoff

## Status and scope

This design turns the existing private recruiter-reply triage handoff into a
verifiable input for the existing recruiter-practice-session-v2 consumer. It is
an offline, identity-free composition boundary: it does not send a reply,
contact a recruiter, schedule a meeting, persist an answer, or start practice
automatically.

The source remains `private-recruiter-reply-triage-v2`. The new contract is
`private-recruiter-triage-practice-handoff-v1`; the existing triage and practice
schemas are not widened.

## Goals

1. Accept only a triage in `state=ready_for_private_prep` with
   `handoff_allowed=true` and a verified fact.
2. Recompute the triage snapshot and require it to match both handoff packet
   snapshots, fact/question references, and preparation scope.
3. Project only safe context, one safe question, and one verified fact into a
   new unanswered practice-session-v2 object. The practice requirement is a
   fixed, scope-specific coaching requirement (`R-001`), not an inferred
   vacancy or employer requirement.
4. Bind the consumer session to the triage snapshot through an exact
   `handoff_context` with `source=private_recruiter_reply_triage`,
   `question_rank=1`, `draft_only=true`, and
   `external_actions_authorized=false`.
5. Give the renderer a static triage route cue: validated triage → private
   rehearsal → private review. States remain textual and the cue is not a
   button, link, form, or progress tracker.

## Non-goals and safety boundaries

- No raw recruiter reply, recruiter/candidate name, contact information, URL,
  proposed time, answer text, or internal source ID is copied to the rendered
  artifact.
- `clarify_first` and `stop` inputs are rejected, even if a handoff object is
  present or flags are tampered with.
- The builder never trusts a supplied snapshot, scope, question ID, or fact ID
  without recomputing and cross-checking against the validated triage.
- No network, upload, message, calendar, public edit, ranking, score, fit claim,
  or outcome promise is introduced.

## Contract and data flow

The builder accepts a validated triage mapping and returns a closed handoff
mapping:

```text
{
  schema_version: private-recruiter-triage-practice-handoff-v1,
  source_artifact_kind: private_recruiter_reply_triage,
  source_snapshot: snap-triage-sha256-(64 lowercase hexadecimal characters),
  prep_scope: one supported practice question kind,
  practice_session: object accepted by recruiter-practice-session-v2,
  delivery: {
    draft_only: true,
    external_actions_authorized: false,
    manual_reentry_required: true,
    auto_start: false,
    local_save_mode: disabled,
    raw_reply_retained: false
  }
}
```

The practice projection uses `ui_locale` and `content_locale` from triage,
maps its safe context to `stage=recruiter_screen` and
`vacancy_state=safe_summary_provided`, and sets `state=ready_to_practice`,
`observed_answer=null`, and pre-answer feedback with an unknown score. The
question kind is the triage `prep_scope`; its text is the validated safe
question text. The requirement summary and rubric are fixed bilingual copy
selected by that kind, so no vacancy or employer claim is invented.

## Components

- `schemas/private-recruiter-triage-practice-handoff-v1.schema.json`: closed
  wrapper contract and delivery invariants.
- `scripts/build_private_recruiter_triage_practice_handoff.py`: fail-closed
  validation, snapshot recomputation, projection, and practice consumer
  validation.
- `tests/test_private_recruiter_triage_practice_handoff.py`: ES/EN golden
  cases, state and snapshot tamper cases, reference mismatch, redaction, and
  consumer acceptance.
- Existing practice renderer/CSS: a triage-specific static route cue, with
  print, forced-colors, high-contrast, narrow-layout, and reduced-motion rules.
- `README.md` and `skills/prepare-role-interviews/references/interview-map.md`:
  describe the composition boundary and manual re-entry rule.
- `.superdesign/init/theme.md`: exact raw CSS parity plus a compact token note.

## Failure handling

The builder returns deterministic validation errors or raises a bounded
composition error; it never falls back to a partial session. The CLI exits
non-zero for malformed JSON, invalid triage state, stale snapshot, unsupported
references, or unsafe prose. A caller must explicitly pass the returned
`practice_session` to the existing practice validator/renderer; no automatic
execution occurs.

## Verification

TDD starts with failing builder and renderer tests. The implementation is ready
only when focused tests, the full plugin suite, static schema/privacy checks,
source/cache parity, and the repository suite pass. Release provenance must
bind fixtures to the commit immediately before the final attestation commit.
Visual QA is limited to Superdesign raw-CSS parity and static responsive,
print, forced-color, and high-contrast assertions; local `file://` screenshot
claims remain unverified unless a supported browser session is available.
