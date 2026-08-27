# Key page dependency trees

The trees use logical artifact paths rather than web URLs. Dependencies include local runtime reads and dynamic local validator imports; Python standard-library imports are intentionally omitted.

## /executive-career-dossier (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py`
  - `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py`
- `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
- `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`

The renderer validates a closed dossier payload, generates header/main HTML in Python, inlines the stylesheet and an artifact-specific script, and writes offline HTML. CLI receipts expose artifact type, locale, and summary by default; trusted callers add `--include-artifact-path` when they need the absolute local output link. In-process render receipts remain rich and retain the path.

The v2 entry point `plugins/professional-growth-coach/scripts/render_executive_career_dossier_v2.py`
composes the same document shell after validating the complete section ledger
and coaching extensions. Its market region is conditional: `not_researched`
renders one bounded unavailable state plus a static next-research panel with
scope, sample, source, date, and read-only boundary, while validated dated vacancy evidence
uses the base comparison table without changing the LinkedIn score.
When a validated market-learning dossier is supplied, each vacancy card adds
location, arrangement, source type, alignment, evidence coverage, and a
qualitative band, plus a passive public-source link and the sample research
date; learning decision cards expose provider/source provenance and recorded
unknowns. Each new vacancy card also renders a textual access/publication
freshness line (90-day window, or an explicit unknown publication date) and a
title-contextual accessible source name. Directional evidence and
non-inferred eligibility remain visible boundaries. Source labels are localized
from the closed market enums.
At screen widths up to 680px, its signal cells stack with localized labels;
print keeps the semantic table layout and no horizontal-scroll affordance is
required.
The section-coverage ledger likewise keeps a single facts column at 640px and
below, preserving the same semantic reading order without horizontal scrolling.
The v2 opening keeps the verdict and recruiter scan together in the first
decision row, followed by a localized `reading-path` landmark. Its four
fragment links target section coverage, coaching priorities, market evidence,
and first-conversation preparation; on screen the landmark remains sticky
through all four regions and marks the nearest target with
`aria-current="location"`, including hash and keyboard navigation. No-script,
print, and reduced-motion fallbacks remain safe, and mobile uses a larger
scroll offset for the stacked links. Links stack into 44px touch targets at
640px and below.

## /recruiter-practice-session (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_recruiter_practice_session.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_recruiter_practice_session.py`
- `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.html`
- `plugins/professional-growth-coach/assets/recruiter-practice-session-v1.css`

The renderer validates a private practice session and generates the document's header/main HTML from the supplied state.

## /private-recruiter-reply-triage (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_reply_triage.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_private_recruiter_reply_triage.py`
- `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-reply-triage-v1.css`

The renderer validates the identity-free triage record, then emits its header, decision sections, and optional manual handoff as HTML. Its CLI receipt omits the local artifact path by default; use `--include-artifact-path` only for a trusted caller that must deliver a verified local link.
Unknown CLI arguments return a fixed opaque diagnostic and never reflect the
rejected value; sibling safety helpers also resolve for direct module imports.

## /private-recruiter-followthrough-checkpoint (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
  - `plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`

The renderer validates a candidate-supplied checkpoint and linked receipt, replaces every template token, and writes a compact offline artifact. The default CLI receipt is path-free; `--include-artifact-path` is an explicit trusted-caller opt-in.

## /private-recruiter-conversion-outcome (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`
- `plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.html`
- `plugins/professional-growth-coach/assets/recruiter-target-shortlist-v1.css`

The shortlist route is intentionally static and offline: `route_recruiter_request` runs the builder → validator → renderer chain and returns both the validated artifact and private in-memory HTML; no network or external-action surface is part of the page. Missing target context returns one bounded intake question instead.

## /recruiter-target-decision-gate (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_recruiter_target_decision_gate.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/build_recruiter_target_decision_gate.py`
- `plugins/professional-growth-coach/scripts/validate_recruiter_target_decision_gate.py`
- `plugins/professional-growth-coach/assets/recruiter-target-decision-gate-v1.html`
- `plugins/professional-growth-coach/assets/recruiter-target-decision-gate-v1.css`

The gate is a static decision brief: it binds and revalidates the full shortlist snapshot, presents reconciled decision counts and one row per target, then stops at a manual screen-context or interview-preparation review boundary. Its legacy screen context accepts only bounded, non-contact-shaped prose; it contains no controls, network calls, contact details, URLs, message actions, or calendar actions. The route handoff returns this private in-memory HTML whenever the gate artifact validates; an intake failure remains artifact-free.

## /recruiter-target-screen-intake (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_recruiter_target_screen_intake.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/build_recruiter_target_screen_intake.py`
- `plugins/professional-growth-coach/scripts/validate_recruiter_target_screen_intake.py`
- `plugins/professional-growth-coach/assets/recruiter-target-screen-intake-v1.html`
- `plugins/professional-growth-coach/assets/recruiter-target-screen-intake-v1.css`

The screen-intake brief is target-specific and snapshot-bound. It reconciles exactly four checks (`target_context`, `proof_packet`, `low_friction_ask`, and `screen_readiness`) and permits `manual_prepare_role_interviews_review` only for an `advance` target with all checks passing. Other decisions remain in intake or stop-and-record states; a validated blocked artifact still gets the same private in-memory HTML handoff, while an invalid target remains artifact-free. The artifact never sends, schedules, or auto-starts preparation.

## /private-recruiter-screen-debrief (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_screen_debrief.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/build_private_recruiter_screen_debrief.py`
- `plugins/professional-growth-coach/scripts/validate_private_recruiter_screen_debrief.py`
- `plugins/professional-growth-coach/assets/private-recruiter-screen-debrief-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-screen-debrief-v1.css`

The debrief is a private post-screen bridge bound to a completed `screen_attended` checkpoint and a ready target-specific intake. `route_recruiter_screen_debrief_intake` first returns an artifact-free prompt for requirement coverage, scope, and team context; once supplied, the debrief records exactly three coverage topics, bounded unknown counts, supported fact counts, and a manual decision. Complete coverage exposes `ready` with `manual_prepare_next_stage_review`; incomplete coverage exposes `needs_intake` for context collection; stop decisions expose terminal `stopped` with recording only. Every validated state returns the private in-memory HTML handoff, while the renderer hides all internal IDs and notes and performs no follow-up action.

The renderer validates a candidate-supplied outcome, computes the localized evidence-count label, and writes a compact offline receipt. The default CLI receipt is path-free; `--include-artifact-path` is an explicit trusted-caller opt-in.

## /private-recruiter-next-stage-review (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_next_stage_review.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/build_private_recruiter_next_stage_review.py`
- `plugins/professional-growth-coach/scripts/validate_private_recruiter_next_stage_review.py`
- `plugins/professional-growth-coach/assets/private-recruiter-next-stage-review-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-next-stage-review-v1.css`

The review requires a manually selected forward stage transition and a validated source debrief. It renders localized current-stage → target-stage labels in the header plus a three-topic checklist with ready/blocked state; when blocked, a structured “clarify before continuing” list names only the pending topics. The route returns the same private in-memory HTML contract for ready, blocked, and terminal stop artifacts. It preserves the source snapshot and replay binding, and exposes no raw answers or external controls.

The five recruiter target surfaces share a localized, non-interactive continuity rail rendered by `scripts/recruiter_continuity_rail.py`. It lists shortlist, decision gate, screen intake, screen debrief, and next-stage review, marks only the current surface with `aria-current="step"`, and remains identity-free, responsive, print-safe, forced-colors-safe, and offline. It is an orientation aid only: it does not infer completed stages or expose links or actions.

Outcome and follow-through receipts share a non-interactive continuity rail:
the supplied observation/receipt is `recorded`, one manual safe step is
`pending` and marked with `aria-current="step"`, and manual review is
`blocked`. A stop decision is a terminal `stopped` recorded rail with no continuation.

Recruiter practice sessions and triage handoffs reuse the same visual contract:
completed evidence is `recorded`, the next private rehearsal/re-entry is the
single pending or blocked `aria-current="step"`, and no step becomes an action
control.
