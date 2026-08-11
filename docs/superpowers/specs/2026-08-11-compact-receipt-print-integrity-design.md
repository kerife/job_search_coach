# Compact receipt print integrity design

## Context

The checkpoint and conversion receipts keep their heading, facts, safe next
step, and continuity boundary in one article, but their print rules currently
only remove shadow and the skip link. A page break can therefore separate the
heading/facts from the boundary in a printed handoff.

## Decision

Add `break-inside: avoid` and `page-break-inside: avoid` to the two compact
receipt cards inside their existing `@media print` blocks. This is a CSS-only
change: screen layout, copy, semantics, mobile behavior, forced-colors, and
offline boundaries remain unchanged.

## Acceptance

1. Checkpoint and outcome print CSS each protects its card with both modern and
   legacy page-break declarations.
2. Stop and non-stop EN/ES receipts retain the same action, facts, boundary,
   and localized labels.
3. Existing 320px/40rem responsive, reduced-motion, prefers-contrast,
   forced-colors, and print hooks remain present.
4. Focused renderer tests, plugin/static/privacy/release gates, root tests,
   source/cache parity, and installed smoke checks remain green.
