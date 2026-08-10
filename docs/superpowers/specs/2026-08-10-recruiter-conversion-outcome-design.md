# Recruiter Conversion Outcome Receipt Design

## Goal

Turn a candidate-supplied recruiter signal into a private, dated observation
that selects one safe next step, without claiming causality, fit, interview
probability, or performing any external action.

## Current evidence

- LinkedIn career contracts require dated, candidate-isolated funnel events and
  observable conversion signals, but the plugin has no dedicated closed
  artifact or renderer for them.
- The private triage/re-entry artifacts already establish the privacy boundary:
  no raw reply, identity/contact, URLs, calendar, auto-start, or answer scoring.
- Existing outcome summarization is CSV-oriented and does not validate the
  evidence/version/action boundary for a single recruiter event.

## Proposed artifact

Create `private_recruiter_conversion_outcome_v1`, a closed JSON artifact with:

- `schema_version`, `artifact_kind`, `locale` (`en`/`es`).
- `event_date` (`YYYY-MM-DD`) supplied by the candidate.
- `event_type`: `contact_received`, `reply_received`, `referral_received`,
  `screen_requested`, `interview_requested`, or `stop_decision`.
- `source_artifact_id`: one internal `D-###` draft/bridge reference.
- `source_version`: a bounded non-secret version label such as `draft-v1`.
- `fact_ids`: one to three internal `F-###` references; no candidate IDs.
- `observation_state`: constant `observed_candidate_reported`.
- `next_safe_action`, mapped exactly as follows: `contact_received` and
  `reply_received` → `clarify_context_before_reply`; `referral_received` →
  `prepare_fact_checked_summary`; `screen_requested` and
  `interview_requested` → `route_to_prepare-role-interviews`; `stop_decision`
  → `record_stop_decision`.
- `delivery`: immutable `draft_only=true`, `external_actions_authorized=false`,
  `no_message_action=true`, `no_calendar_action=true`, `raw_event_retained=false`,
  and `local_save_mode=disabled`.

The artifact contains no free-form event text. It rejects raw recruiter prose,
identity/company/contact names, URLs, times, compensation, outcome/fit/offer
guarantees, scores, candidate IDs, mixed candidate evidence, and extra fields.
`source_artifact_id` is exactly `D-###`; fact IDs are exactly `F-###`; and the
source version is an ASCII label of 1–32 letters, digits, dot, underscore, or
hyphen. The date must be real calendar syntax and not later than an injected
validator `as_of` date (defaulting to today). This artifact deliberately has
no candidate ID or cross-artifact registry; it validates only the single
artifact's declared ID namespace and references. A receipt never auto-creates a module packet or reuses a candidate
answer. `screen_requested` and `interview_requested` route only to a later
manual preparation request.

## Renderer and routing

Add an offline deterministic EN/ES card showing event type, date, evidence count,
and the fixed next-safe-action copy. Internal IDs remain in validated JSON but
are omitted from HTML. The card has no links, buttons, forms, send/calendar
controls, or raw-event interpolation. Add a private outcome branch below
private triage/re-entry and above ordinary outcome tracking; normal dossier and
legacy CSV behavior remain unchanged.

## Verification

- Contract RED/GREEN tests cover all event mappings, date validation, missing or
  extra fields, unknown event type, source/version/fact references, mixed
  candidates, raw/identity/action/outcome/score injection, and delivery gates.
- Renderer tests cover EN/ES localization, escaped fixed output, ID omission,
  ready-only deterministic behavior, accessibility/print/forced-color hooks,
  and mode `0600` atomic writes.
- Routing tests prove no auto-send, no calendar, no module execution packet,
  and unchanged normal LinkedIn behavior.
- Release gates include focused/full tests, privacy/static/schema/official
  validators, one cachebuster invocation, source/cache identity, and smoke for
  each event mapping.

## Non-goals

No LinkedIn browsing, recruiter network expansion, message sending, scheduling,
candidate identity storage, causal attribution, aggregate benchmarking, offer
prediction, or scorecard before observed evidence.
