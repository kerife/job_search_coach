# Compact receipt forced-colors boundary design

## Context

The compact checkpoint and outcome receipts use a thick left boundary marker
for safe-next-step context. Their forced-colors rule currently uses the
shorthand `border: 1px solid CanvasText`, which resets that marker to a thin
one-pixel border.

## Decision

Keep the existing system color and card border behavior, but add an explicit
`border-left-width: .25rem` to each boundary selector in the forced-colors
media query. This preserves a non-color-only hierarchy without changing copy,
screen layout, print behavior, or receipt semantics.

## Acceptance

1. Both compact forced-colors blocks retain `CanvasText` and a boundary
   `border-left-width` of at least `.25rem`.
2. EN/ES stop and non-stop receipts retain their existing localized action and
   continuity boundary copy.
3. Existing print, reduced-motion, prefers-contrast, mobile, privacy, and
   no-action contracts remain green.
