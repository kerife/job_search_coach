# Recruiter Screen Preparation Design

## Goal

Turn the private LinkedIn dossier from a diagnosis into a short, usable rehearsal
for the first recruiter conversation. The artifact should help the candidate
decide what to say, what evidence supports it, and what must be confirmed before
using it publicly. It must remain evidence-safe, private, and draft-only.

## Product decision

Extend the existing `screen_bridge` presentation instead of introducing a new
schema version. The closed dossier already contains the necessary fields:
`state`, `copy`, `why_it_works`, `claim_ids`, `evidence_ids`, `claim_boundary`,
and `question_rank`. Reusing them preserves v1 compatibility and keeps the
feature independently testable.

## Client experience

After the verdict and priorities, show one semantic card titled “Preparación para
la primera conversación” (localized in English when needed):

1. A categorical readiness state: “Listo para conversar”, “Falta confirmar”, or
   “En pausa”. The state is derived only from `screen_bridge.state`; no numeric
   readiness score is invented.
2. A 30-second opener from `screen_bridge.copy`, labeled as a private draft.
3. An evidence strip showing up to three supported evidence-backed points. It
   uses existing claim/evidence references and natural text; IDs never appear.
4. A “No afirmar todavía” boundary from `claim_boundary` and a clear distinction
   between known, missing, and confirmation-required material.
5. One prominent decision question when `question_rank` links the bridge to the
   rank-1 question. No additional question is invented.
6. A small “ensayo” marker in the seven-day plan when a private review action is
   present. It is a rehearsal step, never a message, connection, calendar, or
   publication action.

The existing verdict, three priorities, seven dimensions, copy cards, analytics,
market card, and no-action sentence remain unchanged. The card must fit the first
viewport, reflow without horizontal scrolling, print without splitting its
heading from its content, and preserve the current forest/paper/coral/gold visual
language and typography contrast from the approved Superdesign draft.

## Data and safety boundaries

- No schema v2, new score, readiness percentage, recruiter identity, contact
  target, recruiter promise, interview probability, or market claim is added.
- `screen_bridge` remains private, draft-only, and action-state `not_executed`.
- Evidence state is rendered as natural language; raw profile text, URLs, IDs,
  private analytics, and confidential employer details remain prohibited.
- Unsupported technologies stay in confirmation/omit or do-not-change copy and
  cannot enter the opener.
- Analytics and market evidence remain separate from the LinkedIn quality score.
- Missing visual, analytics, or market evidence is unavailable/not requested/not
  researched, never zero and never a blocker when the rest of the dossier is
  honest.

## Implementation shape

- Add a focused renderer section that consumes the existing `screen_bridge`,
  linked question, claims/evidence, and plan fields.
- Add localized labels and semantic HTML (`section`, `h2`, `ol`/`dl`, visible
  text states, `aria-labelledby`) using the existing inline CSS tokens.
- Add only the CSS needed for the card, readiness chips, evidence strip, and
  print/mobile behavior. No remote assets, gradients, or decorative-only meter.
- Keep validator and action/privacy checks unchanged unless a new rendering path
  exposes a regression; any change must have a focused RED test first.

## Verification criteria

1. Valid Spanish and English fixtures render the card with the correct localized
   labels, 30-second draft, evidence points, boundary, linked rank-1 question,
   and rehearsal marker.
2. `screen_bridge` states `requires_confirmation`, `omit`, and unavailable data
   render categorical states without numeric readiness.
3. A bridge with unsupported technology, external action, outcome promise, raw
   identity, or private data is rejected or safely omitted; no artifact leaks it.
4. Existing four canonical artifacts remain 3/7/3, one question, one link,
   one no-action sentence, 0600, and complete scorer pass.
5. Responsive, print, CSP/offline, privacy, static, full-suite, and official
   plugin validators remain green.
6. The increment is committed, provenance refreshed, cachebuster run exactly
   once, installed from `job-search-coach-local`, and verified in a fresh smoke
   scenario before the next cycle.
