# Compact receipt breakpoint design

## Problem

The checkpoint and conversion-outcome receipts use `@media (min-width: 40rem)`
for their two-column fact grid. At the default 16px root size, that query
matches exactly 640px, while the design-system contract says the compact
receipts remain one column at 640px and below.

## Decision

Keep the existing base one-column grid and move the wide layout threshold to
`min-width: 641px` in both compact CSS assets. Synchronize the Superdesign raw
theme dumps and preserve all tokens, copy, semantics, print, dark, reduced
motion, and forced-colors rules.

## Acceptance

- At 640 CSS px, both fact grids remain one column.
- At 641 CSS px and above, both fact grids use the existing two-column layout.
- The two CSS assets and their Superdesign dumps remain byte-for-byte aligned.
- Static tests reject a `40rem`/640px inclusive boundary and protect both assets.
- Existing renderer output, accessibility semantics, and action/privacy contracts
  remain unchanged.

## Verification boundary

This is a CSS contract correction. No browser screenshot is claimed in this
cycle; static media-query evidence and renderer/parity tests are authoritative.
