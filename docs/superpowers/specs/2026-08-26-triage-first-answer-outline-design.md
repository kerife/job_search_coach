# Triage-first answer outline

## Context

The recruiter practice HTML currently places triage route and handoff metadata
between the question/claim boundary and the rehearsal scaffold. That makes the
first useful response pattern harder to find at the moment the candidate needs
it. The existing `REHEARSAL_COPY` already contains a safe, localized three-step
answer structure for every validated question kind.

## Decision

For sessions whose validated handoff source is
`private_recruiter_reply_triage`, render one static answer-outline section
immediately after `.practice-claim-guardrail` and before
`.triage-practice-route`. The section uses only `locale`, the closed
`question_kind`, and `REHEARSAL_COPY`; it must not interpolate context,
question text, facts, snapshots, identifiers, answers, feedback, or handoff
content. Existing rehearsal remains in its current position for non-triage
sessions, so the feature does not alter dossier or unsourced flows.

## Product and visual contract

- Spanish: `Tu primera respuesta` / `Guion para responder`.
- English: `Your first answer` / `Answer outline`.
- Reuse the existing hint and three steps for all five question kinds.
- Use a semantic `<section>` and `<ol>`, with a variant class
  `practice-rehearsal--triage-first-answer` and a unique accessible heading id.
- Follow the local Superdesign theme in `.superdesign/init/theme.md`: forest
  left border, `var(--forest-soft)` surface, bounded measure, three columns on
  desktop and one column at `max-width: 640px`.
- Preserve dark mode, forced-colors, `prefers-contrast: more`, print,
  reduced-motion, CSP, and no-network/no-form/no-script boundaries.

## Acceptance criteria

1. Both locales and all five question kinds render exactly one outline only for
   triage source, with the exact order question → claim guardrail → outline →
   route.
2. Dossier and unsourced sessions do not render the outline and retain their
   existing order and markup.
3. The outline contains no internal IDs, snapshots, URLs, paths, contacts,
   credentials, raw answer/feedback text, forms, buttons, links, or scripts.
4. Rendering rejects unsupported locale/kind through existing fail-closed
   validation; static copy is HTML-escaped as a defensive invariant.
5. Tests cover the full matrix, order, privacy sentinels, responsive/accessibility
   CSS contracts, and documentation scope.

## Documentation scope

README and the interview-map reference must state that the outline is a static,
localized visual scaffold for a private triage practice and is not a saved
answer, a synthesis of the recruiter reply, or an external action.
