# Practice answer boundary

## Goal

Make the first recruiter-practice decision explicit: show what is safe to say
before the candidate rehearses an answer.

## Behavior

- Render exactly one static `.practice-claim-guardrail` section for sessions
  whose `handoff_context.source` is `private_recruiter_reply_triage`.
- Place it immediately after the question and before the triage route,
  next-action, rehearsal, and continuity sections.
- Use fixed bilingual UI copy. The only dynamic prose is the already validated
  fact summary, escaped through the existing renderer path.
- For a verified fact, label it “Usa solo evidencia confirmada” / “Use only
  confirmed evidence”. The handoff builder projects only verified facts, so the
  renderer must not invent a candidate-reported variant.
- Do not add buttons, links, forms, scripts, IDs from source artifacts, raw
  replies, URLs, answer storage, or claims about interview likelihood.
- Preserve existing output for dossier-sourced and unsourced sessions.

## Visual/accessibility contract

Use existing practice tokens and the Superdesign raw-theme convention. The
section has a coral/gold left border, readable list hierarchy, one-column layout
below 640px, explicit dark/forced-colors/high-contrast rules, print
`break-inside: avoid`, and no motion beyond existing reduced-motion behavior.

## Testing

Add ES/EN triage-source renderer tests for exactly one guardrail, order after the
question, escaped dynamic fact prose, absence of source IDs/URLs/actions, and
legacy-source preservation. Assert CSS contains mobile, dark, forced-colors,
contrast, print, and reduced-motion rules and remains byte-identical to the
Superdesign theme dump.
