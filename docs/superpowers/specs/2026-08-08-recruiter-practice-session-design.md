# Recruiter Practice Session Design

## Goal

Add a private, vacancy-backed practice session that turns the dossier's positioning into one observable recruiter-screen rehearsal. It must wait for an actual candidate response before giving feedback and must never predict hiring or perform outreach.

## Product decision

Keep the existing executive dossier schema v1 and `screen_bridge` unchanged. Add a separate validated session artifact/CLI contract so a vacancy, candidate facts, one question, and one optional observed answer cannot be confused with the profile diagnostic.

## Client flow

1. Context strip: recruiter-screen stage plus safe vacancy state; no recruiter/company identity, URLs, or raw vacancy text.
2. Focus card: one fact-bounded opener and up to three evidence-labelled proof points.
3. Prompt card: exactly one vacancy requirement, one question, and a visible rubric criterion.
4. Before response: state `awaiting_answer`; score is `unknown` and no readiness percentage appears.
5. After response: feedback separates `sólido`, `confirmar`, and `no afirmar`; each observation cites only supplied facts/rubric language.
6. End state: one private drill and the no-action footer. Answers remain ephemeral unless an explicit local save mode is selected.

## Safety and state contract

- States are categorical: `not_ready_missing_vacancy`, `not_ready_missing_candidate_facts`, `ready_to_practice`, `awaiting_answer`, `feedback_available`, `confirmation_required`, `omit_or_pause`, and `session_complete`.
- No numeric readiness, weighted total, hiring likelihood, recruiter promise, compensation claim, or outcome prediction before an observed answer.
- No recruiter identity/contact, raw profile/CV/vacancy text, private analytics, or external action.
- Unsupported claims remain unknown/confirmation-required; exact confidentiality, authorization, availability, and compensation boundaries remain visible.
- Raw answers are not printed by default. Any local saved artifact is mode 0600 and contains only the validated session.

## Visual and accessibility direction

Use the approved Superdesign forest/paper/coral/gold palette, serif contrast, flat cards, and editorial spacing. Render a full-width session section with explicit text chips, logical headings, labelled input when interactive, `aria-live=polite` for feedback, keyboard-sized controls, reduced-motion support, single-column mobile flow, and a compact print summary.

## Verification

- Valid vacancy/fact fixture reaches `ready_to_practice` and renders one prompt.
- Missing vacancy/facts fail closed without an empty score.
- No-answer session has `unknown` score; observed answer alone enables feedback.
- Unsupported technology, identity, contact, raw text, action, guarantee, and private analytics mutations reject or omit safely.
- English/Spanish labels, offline CSP, privacy, 0600 output, mobile/print, full suite, static, schema, and official validators remain green.
