# Shortlist batch next-step prominence

## Decision

Promote the recruiter shortlist's safe batch decision into one static panel
before the target rows. The panel is derived only from the validated
`batch_decision`, uses fixed bilingual copy, and never becomes a message,
calendar, link, or save control. Label the artifact date as a localized review
date and expose it through a semantic `<time>` element.

## Product contract

- `advance`: review the draft locally before any contact.
- `clarify`: collect recipient context before drafting.
- `pause`: record the observation and pause the search.
- `stop`: record the stop and do not continue with the batch.

The existing row-level decision details remain unchanged. The panel is placed
after the overview and before the target list so the client sees the decision
and manual next step in sequence. It remains offline, identity-free,
non-interactive, print-safe, forced-colors-safe, and responsive.

## Acceptance criteria

1. ES/EN renders show one localized review date with `<time datetime>`.
2. Every validated batch decision maps to fixed copy and a corresponding
   closed state class; no private IDs, URLs, controls, or raw input text are
   projected.
3. The panel keeps the existing mobile, print, forced-colors, and dark-mode
   surface contracts, with Superdesign's raw CSS dump synchronized.
