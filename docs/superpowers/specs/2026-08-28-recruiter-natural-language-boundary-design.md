# Recruiter natural-language boundary refinement

## Decision

Keep the existing artifact-free recruiter handoff architecture and make the
natural-language classifier recognize common English/Spanish variants without
weakening its safety boundaries. Defined articles (`the`, `el`, `la`) and
future calendar language (a weekday or month date attached to a future-tense
screen) route to screen preparation. A completed screen followed by
`not yet ready for the next stage` routes to next-stage review. Reply/send
synonyms preserve the authorization flag even when no specialized recruiter
route is selected.

The shared five-surface rail keeps `aria-current="step"`, but its visible
marker says `Current review surface` / `Superficie actual de revisión` so the
marker identifies location without implying that earlier stages are complete.

## Boundaries

- Future-date detection is scoped to future-tense verbs and does not classify a
  completed screen described with a past-tense date as non-attendance.
- A positive `spoke with`/`hablé con` or completed-screen statement remains
  post-screen language unless the event itself is negated.
- Authorization is a safety receipt only; no message, email, calendar event,
  recruiter contact, or preparation action is performed.
- No schema fields, identifiers, contacts, URLs, raw requests, or external
  assets are added.

## Verification

Focused tests cover the new article, future-date, readiness-negation,
authorization-synonym, and rail-copy cases in English and Spanish. Existing
responsive, print, forced-colors, privacy, provenance, and renderer contracts
remain in force; the Superdesign route/theme context is updated with the same
copy and routing boundary.
