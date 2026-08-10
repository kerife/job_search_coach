# Dossier-to-Practice Handoff v1 Design

## Goal

Make a recruiter-practice session sourced from an executive-career dossier
provably traceable to the dossier's selected decision-changing question and
evidence, while keeping the vacancy requirement as a separate identity-free
source.

## Problem

The dossier validator and recruiter-practice validator currently validate each
artifact independently. A practice payload can therefore use well-formed but
unrelated `Q-`, `R-`, `F-`, `C-`, and `E-` identifiers and an arbitrary
`snap-dossier-###` value. The practice renderer hides those identifiers, but
the hidden provenance boundary is still weak because no canonical bridge binds
the two artifacts.

## Chosen design

Add an additive `dossier-recruiter-practice-handoff-v1` sidecar and a pure
builder/validator pair. The builder consumes:

1. a dossier that has already passed the existing dossier validator;
2. an identity-free vacancy summary and requirement supplied separately; and
3. a synthetic `snap-dossier-###` snapshot supplied by the caller.

The builder accepts only a `requires_confirmation` dossier bridge whose
`question_rank` is `1`, whose selected question has
`linked_copy_category="screen_bridge"`, and whose source evidence states are
`verified` or `candidate_reported`. It emits a sidecar containing:

- the opaque source snapshot and dossier rank;
- the dossier bridge's exact claim IDs and evidence IDs;
- the selected question's exact evidence IDs and one source fact evidence ID;
- a sanitized source-fact projection preserving the dossier evidence state;
- the identity-free vacancy `safe_context`, requirement, and a derived
  practice question using closed `Q-001`/`R-001`/`F-001` projection IDs; and
- the exact practice `handoff_context` with `draft_only=true` and
  `external_actions_authorized=false`.

The projection IDs are target-artifact IDs, not claims that the dossier
contains Q/R/F records. The sidecar names the dossier rank and C/E records as
the source provenance, and the validator checks the target session against the
sidecar projection.

## Validation boundary

`validate_dossier_recruiter_practice_handoff` must reject:

- a dossier that is not valid, is `ready`/`omit`, lacks rank 1, or has a
  non-`screen_bridge` selected question;
- an unknown, duplicate, or unrelated dossier claim/evidence ID;
- a bridge evidence set that does not match the dossier claim relationships;
- a selected question evidence ID that is unknown or whose source state is
  `unknown`;
- a practice fact whose state or summary differs from the selected source
  evidence;
- a practice session whose Q/R/F IDs, requirement, source snapshot, question
  text/kind, or fact references drift from the sidecar;
- a promoted `candidate_reported` fact, fabricated snapshot, prefilled answer,
  numeric score, auto-start flag, or any external-action flag; and
- raw profile/reply text, URLs, contact data, source IDs in prose, or other
  private fields in the sidecar's sanitized summaries.

The existing dossier-v1 and recruiter-practice-session-v1 schemas remain
unchanged. The new schema is closed (`additionalProperties: false`), uses no
external dependency, and is validated by the repository's dependency-free
schema harness plus the custom semantic validator.

## Privacy and rendering

The sidecar is an internal contract artifact. Existing renderers continue to
hide Q/R/F/C/E identifiers, snapshots, source enums, raw answer text, URLs,
and source summaries. No buttons, forms, links, `aria-live`, or external
actions are introduced. Direct practice sessions without a sidecar continue
to validate and render unchanged.

## Test evidence

The cycle must include a positive dossier-plus-vacancy fixture, a matching
practice session, and mutation tests for rank/state/snapshot/Q-R-F/C-E/fact
drift, raw/private values, and automatic execution. It must run the existing
practice, dossier, schema-conformance, static, privacy, and full-plugin gates.

