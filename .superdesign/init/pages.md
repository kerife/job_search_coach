# Key page dependency trees

The trees use logical artifact paths rather than web URLs. Dependencies include local runtime reads and dynamic local validator imports; Python standard-library imports are intentionally omitted.

## /executive-career-dossier (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_executive_career_dossier.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_executive_career_dossier.py`
  - `plugins/professional-growth-coach/scripts/validate_linkedin_client_report.py`
- `plugins/professional-growth-coach/assets/executive-career-dossier-v1.html`
- `plugins/professional-growth-coach/assets/executive-career-dossier-v1.css`

The renderer validates a closed dossier payload, generates header/main HTML in Python, inlines the stylesheet and an artifact-specific script, and writes offline HTML.

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

The renderer validates the identity-free triage record, then emits its header, decision sections, and optional manual handoff as HTML.

## /private-recruiter-followthrough-checkpoint (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_followthrough_checkpoint.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_private_recruiter_followthrough_checkpoint.py`
  - `plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-followthrough-checkpoint-v1.css`

The renderer validates a candidate-supplied checkpoint and linked receipt, replaces every template token, and writes a compact offline artifact.

## /private-recruiter-conversion-outcome (offline artifact)

Entry: `plugins/professional-growth-coach/scripts/render_private_recruiter_conversion_outcome.py`

Dependencies:

- `plugins/professional-growth-coach/scripts/validate_private_recruiter_conversion_outcome.py`
- `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.html`
- `plugins/professional-growth-coach/assets/private-recruiter-conversion-outcome-v1.css`

The renderer validates a candidate-supplied outcome, computes the localized evidence-count label, and writes a compact offline receipt.
