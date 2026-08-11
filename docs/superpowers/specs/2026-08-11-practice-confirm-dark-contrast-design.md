# Practice Confirm Dark-Contrast Design

## Context

The practice feedback state `confirm` keeps its light-theme background in the
dark-mode cascade. Its inherited light text therefore has insufficient
contrast and can hide a candidate-facing observation.

## Decision

Inside the existing screen-scoped dark media block, map
`.feedback-item--confirm` to `var(--gold-soft)` with `var(--decision-term)` as
its accent and `var(--ink)` as its text color. Add the matching label override.
Leave the base light rule, print rules, forced-colors system colors, DOM, copy,
IDs, and actions unchanged.

## Verification

Static contrast tests require the dark foreground/background pair to meet 4.5:1
and require the selector to be inside the dark block before print. EN/ES
feedback render tests preserve the `Confirm`/`Confirmar` copy and existing
forced-colors/print contracts.
