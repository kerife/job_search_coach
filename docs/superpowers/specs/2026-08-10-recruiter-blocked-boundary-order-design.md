# Recruiter blocked boundary order design

## Goal

Place the existing fixed `Do not assert`/`No afirmar` section immediately after the next-safe-action section, before any ready handoff content.

## Boundaries

This is an HTML assembly order change only. It preserves blocked prose validation, localization, the ready-only handoff, clarify/stop behavior, and all privacy/action restrictions. No schema, data, routing, or copy changes.

## Acceptance

Ready EN/ES output orders `next-safe-action < blocked < handoff`; clarify/stop retain one blocked section and no handoff. Existing blocked labels/items, aria-labelledby, list semantics, and no-link/button/form checks remain intact.
