# Professional Growth Coach private artifact design system

## Product context

Professional Growth Coach produces private, offline, candidate-facing HTML artifacts for
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

For the executive LinkedIn dossier v2 exploration, extend that journey without
changing the visual family:

1. state the verdict and evidence coverage honestly;
2. show a complete per-section inspection and current-session authorization
   ledger;
3. explain exactly three priorities as section-named coach conversations with
   blank, non-persisted templates;
4. show five separately validated vacancy evidence-alignment cards in the
   complete state, or the real one-to-four-card limited state with its actual
   denominator, or one honest unavailable-market state;
5. compare reputable learning with cheaper proof, project, direct-application,
   and no-learning options;
6. finish with evidence, limitations, privacy, and no-external-action copy.

The current design task must improve the clarity of steps 3 and 4 without
adding a form, fake button, link, persistence, automatic transfer, recruiter
identity, or external action.

The v2 renderer now keeps the honest unavailable-market card for
`not_researched` inputs, while a validated `dated_vacancy_evidence` context
renders the existing editorial comparison table and its sanitized public
research links. Market rows remain separate from the LinkedIn score; no
unvalidated vacancy, employer, salary, ranking, or eligibility claim may enter
the surface.

The dated market table keeps native table semantics and, at screen widths up to
680px, presents each signal cell as a labelled vertical stack using localized
labels. The print layout remains tabular, and the responsive treatment does not
depend on horizontal scrolling.

## Visual language

- Preserve the existing editorial document aesthetic: calm, sober, private,
  evidence-led, and printable.
- Use only the declared color of the artifact family. The base editorial
  palette is:
  - paper `#f6f4ee`
  - surface `#ffffff`
  - forest `#173e30`
  - ink `#1b1c1a`
  - forest soft `#dce5e0`
  - coral `#b9513a`
  - coral soft `#f6e0da`
  - line `#b8c7c0`
  - gold-compatible caution `#f5ecd8` with text `#5c4a12`
- Family boundaries are intentional and machine-checked by
  `scripts/validate_design_tokens.py`:
  - **Dossier:** its established editorial legacy aliases include ink
    `#1a1a1a`, muted `#e2ddd6`, coral `#d96c52`, gold `#be9338`, coral soft
    `#f7e4df`, and their existing contrast companions.
  - **Practice / triage:** the shared editorial palette may use decision gold
    `#dfbf70`, caution ink/soft `#854117`/`#f7ecd5`, rehearsal surface
    `#f8f7f2`, muted border `#9fc4b4`, and hint ink `#46534d`.
  - **Compact receipts:** the separate blue receipt family uses ink
    `#172033`, accent `#315bd6`, muted `#536174`, line `#d9dfeb`, and paper
    `#f4f6fa`.
- Do not copy a color between families without a visual and print review. The
  allowlist is a consistency guard, not permission to recolor an artifact.
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

For dossier v2, generated values and prose are placeholders only. Never use a
generated company, vacancy, score, course, metric, authorization state, impact
claim, or outcome promise as product copy or fixture evidence. Use native
`progress` plus visible text for alignment charts; keep the detailed
requirement explanation authoritative. A complete market matrix has five
labelled vacancy columns; a limited matrix has exactly its real `N` columns and
no padding. At 320px, coverage and matrix rows become labelled stacks rather
than making horizontal scrolling the only access path. The market matrix uses
localized cell labels while retaining table semantics. Print preserves all
labels and text states. No critical decision is hidden in a closed accordion.
Templates are static text, not controls or stored answers.
