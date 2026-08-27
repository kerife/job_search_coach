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
renders one bounded unavailable state, while validated dated vacancy evidence
uses the base comparison table without changing the LinkedIn score.
When a validated market-learning dossier is supplied, each vacancy card adds
location, arrangement, source type, alignment, evidence coverage, and a
qualitative band, plus a passive public-source link and the sample research
date; learning decision cards expose provider/source provenance and recorded
unknowns. Directional evidence and non-inferred eligibility remain visible
boundaries. Source labels are localized from the closed market enums.
At screen widths up to 680px, its signal cells stack with localized labels;
print keeps the semantic table layout and no horizontal-scroll affordance is
required.
The section-coverage ledger likewise keeps a single facts column at 640px and
below, preserving the same semantic reading order without horizontal scrolling.
The v2 opening keeps the verdict and recruiter scan together in the first
decision row, followed by a localized `reading-path` landmark. Its four static
fragment links target section coverage, coaching priorities, market evidence,
and first-conversation preparation; links keep visible focus, print cleanly,
and stack into 44px touch targets at 640px and below.

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

The renderer validates a candidate-supplied outcome, computes the localized evidence-count label, and writes a compact offline receipt. The default CLI receipt is path-free; `--include-artifact-path` is an explicit trusted-caller opt-in.
