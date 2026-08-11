# Dossier Dark-Label Contrast Design

## Context

The dossier dark palette fixes body and heading contrast, but the reusable
`.label` class retains its light-theme `#53605a` color. On the dark surface
this is 2.42:1, below the 4.5:1 text threshold, and appears across evidence,
plan, and preparation cards.

## Decision

Inside the existing screen-scoped dossier dark media block, set
`.dossier-document .label { color: var(--muted); }`. Keep the light rule,
print behavior, forced-colors system colors, DOM, copy, and actions unchanged;
synchronize the raw Superdesign dump.

## Verification

The dark accessibility test requires the label override and checks the
`--muted`/`--surface` pair at or above 4.5:1. Existing dossier EN/ES renderer,
print, forced-colors, theme parity, and design-token tests remain green.
