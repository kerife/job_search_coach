# Dossier article-card accessible naming

## Context

The executive dossier renders priority, dimension, visual-review, and copy
cards as semantic `<article>` landmarks. Their visible `h3` headings are
present, but the articles do not reference those headings, so assistive
technology exposes 15 repeated landmarks without a name.

## Decision

Give each existing card heading a deterministic ID and add
`aria-labelledby` to its containing article:

- priorities: `priority-title-{rank}`
- dimensions: reuse `dimension-title-{dimension}`
- visual review: `visual-title-{photo|banner}`
- copy blocks: `copy-title-{index}`

Keep the existing article elements, visual order, text, CSS, copy-button
behavior, localization, print output, and data contracts unchanged. Do not
add CSS or Superdesign theme markup because the theme dump contains styles,
not renderer-generated HTML.

## Verification

Add Spanish and English renderer assertions that every target article has one
unique `aria-labelledby` reference resolving to its own `h3`, while question
cards and existing progress references remain valid. Run the dossier renderer,
dark/parity/print, privacy/static, and full plugin suites. No browser capture
is required for this semantic-only change; OS/browser visual QA remains a
separate follow-up.
