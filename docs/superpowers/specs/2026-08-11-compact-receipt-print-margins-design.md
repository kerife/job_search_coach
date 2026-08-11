# Compact Receipt Print Margins

## Goal

Make printed compact receipts use the same deterministic page margins as the
other private HTML artifacts without changing screen layout or copy.

## Contract

Both compact receipt stylesheets declare `@page { size: auto; margin: 14mm; }`.
The rule is print-only and applies to checkpoint and conversion outcome
receipts. Existing card atomicity, forced-colors, reduced-motion, and mobile
rules remain unchanged.

## Acceptance

- English and Spanish checkpoint/outcome renders contain the `@page` rule.
- The Superdesign theme dumps match both source stylesheets exactly.
- Existing receipt copy, ARIA, privacy, and no-action boundaries remain intact.
