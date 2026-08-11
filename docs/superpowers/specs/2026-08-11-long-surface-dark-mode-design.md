# Long Surface Dark-Mode Design

## Context

The long dossier, practice, and recruiter-triage surfaces force a light
color scheme while compact recruiter receipts already support dark mode. A
single session therefore changes theme between related artifacts, and several
light-only hardcoded panels would become low-contrast if only the root tokens
changed.

## Decision

Add an independent `@media screen and (prefers-color-scheme: dark)` block to
each existing CSS asset. Reuse the compact dark palette for paper, surface,
ink, muted, and line; use contrast-checked Professional Growth Coach brand
tokens for forest, coral, gold, and their soft panels. Override the known
light-only state/panel selectors in the same block. Keep print styles light,
keep forced-colors after the dark block with system colors, and do not change
DOM, copy, IDs, schemas, or actions.

## Verification

Static tests require exact dark media scope/order, palette tokens, contrast
ratios, print-light behavior, and forced-colors footer/boundary colors. Render
tests preserve EN/ES continuity copy and stop-copy contracts. The Superdesign
theme raw CSS dumps must remain byte-identical to all three assets.
