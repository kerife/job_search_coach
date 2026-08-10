# Job Search Coach private artifact design system

## Product context

Job Search Coach produces private, offline, candidate-facing HTML artifacts for
career diagnosis, recruiter-reply triage, recruiter-screen practice,
follow-through checkpoints, and observed outcomes. The UI helps a candidate
decide what is supported, what remains unknown, what to rehearse, and what the
next safe manual step is. It never performs outreach, schedules a meeting,
predicts an interview, persists a raw practice answer, or exposes internal IDs.

## Target journey

1. The executive dossier explains the current positioning and evidence.
2. A screen-preparation card identifies one truthful question and its boundary.
3. Recruiter practice presents the same safe context and question for private
   rehearsal.
4. The candidate answers manually in the originating private Codex conversation.
5. Feedback remains categorical, evidence-bound, ephemeral, and non-predictive.

The current design task must improve the clarity of steps 3 and 4 without
adding a form, fake button, link, persistence, automatic transfer, recruiter
identity, or external action.

## Visual language

- Preserve the existing editorial document aesthetic: calm, sober, private,
  evidence-led, and printable.
- Use only the existing colors:
  - paper `#f6f4ee`
  - surface `#ffffff`
  - forest `#173e30`
  - ink `#1b1c1a`
  - forest soft `#dce5e0`
  - coral `#b9513a`
  - coral soft `#f6e0da`
  - line `#b8c7c0`
  - gold-compatible caution `#f5ecd8` with text `#5c4a12`
- Display headings use `Georgia, "Times New Roman", Times, serif`.
- Body text uses `-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica,
  Arial, sans-serif`.
- Preserve square corners, thin borders, restrained left-edge accents, and no
  decorative gradients or remote assets.
- Body text stays at least 16px with line-height around 1.55 and a maximum
  reading measure of 72ch.
- Desktop content width is 920px for practice/triage and 1160px for the dossier.

## Layout and hierarchy

- One document-level `h1`; named `section` or `aside` regions use stable
  `aria-labelledby` relationships.
- Keep the decision sequence linear:
  state → safe context → question → source/handoff → next manual step →
  question-kind-aware answer structure → evidence → safe boundary → no-action
  footer.
- Question and evidence are supporting context. The next manual step must be
  visually prominent but must not look interactive.
- Use the existing forest-filled next-step panel only for a real manual action.
- At 640px and below, preserve one column, at least 0.5rem side gutters, no
  horizontal scrolling, and the same semantic reading order.

## State and content rules

- State labels describe what the static artifact can truthfully support. Avoid
  “waiting” language when the document cannot receive input.
- Guidance varies by validated question kind:
  `screen_opening`, `proof_example`, `eligibility_boundary`,
  `compensation_boundary`, and `missing_detail`.
- Context/action/result is appropriate only for an evidence example. Boundary
  questions instead guide the candidate to distinguish known, unknown, and the
  minimum clarification to ask or state.
- Eligibility and compensation copy must never assert rights, availability,
  amounts, fit, outcomes, or promises.
- Do not render raw enum values, internal Q/R/F/C/E/OBS/RB identifiers,
  snapshots, recruiter identity, URLs, raw replies, or raw stored answers.

## Accessibility and resilience

- Preserve the skip link and all existing visible focus treatment.
- All `aria-labelledby` and `aria-describedby` references must resolve to unique
  IDs in the same document.
- Never rely on color alone; combine label, text, border style, and hierarchy.
- Preserve reduced-motion, forced-colors, and `prefers-contrast: more` support.
- Print keeps question, source/handoff, answer structure, next step, evidence,
  and boundary intact without splitting headings from their content.
- No remote fonts, images, scripts, forms, network calls, or relaxed CSP.

## Design constraints for Superdesign

Use ONLY the fonts, colors, spacing, and component styles defined above and in
the supplied source CSS. Do not introduce any fonts, colors, gradients, rounded
cards, floating navigation, decorative illustrations, or visual styles not in
this design system. Preserve the existing document shell and candidate-facing
copy unless a variation explicitly tests a clearer truthful continuation.
