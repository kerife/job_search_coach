# Feedback next-version bridge

## Context

In `feedback_available`, the practice renderer already shows fixed feedback, a
governing decision, and a three-stage continuity rail. The rail names a pending
next version, but the immediate transition after the decision is not explicit;
the candidate must infer how to continue. The existing contract is private,
no-save-by-default, and manual-only.

## Brainstorm decision

We considered (1) making the existing rail interactive, (2) restoring the old
`practice-next-action--feedback_available` panel, or (3) adding a small static
bridge immediately after the decision while preserving the rail as a map. The
third option best closes the loop without introducing controls, duplicate
heavy panels, or external-action affordances. The bridge will state three fixed
movements—keep, adjust, check—selected only by the governing label.

## Decision

For every validated `feedback_available` session, render exactly one
`.practice-next-version` section after `.practice-decision` and before the
existing `.continuity-rail`. It uses only locale, question kind, and the
closed governing label. It never projects observed answers, feedback
statements, IDs, snapshots, references, URLs, paths, or action state.

Copy is fixed and localized:

- ES kicker `Antes de volver a practicar`, title `Siguiente versión`, intro
  `Haz un solo ajuste; conserva la evidencia ya confirmada.`
- EN kicker `Before you rehearse again`, title `Next version`, intro
  `Make one adjustment; keep the confirmed evidence already in place.`
- Three labels are `Conserva / Ajusta / Comprueba` or `Keep / Adjust / Check`;
  their content is a closed table for `solid`, `confirm`, and `do_not_assert`.

## Visual and accessibility contract

Use the local Superdesign theme: `var(--forest-soft)` panel, `var(--forest)`
left border, bounded measure, three columns on desktop and one column at
`max-width: 640px`. Preserve dark mode, forced colors, `prefers-contrast: more`,
print break avoidance, reduced motion, CSP, and one internal skip link only.
The section is informational: no buttons, forms, links, scripts, live regions,
or dynamic data attributes.

## Acceptance criteria

1. ES/EN × five question kinds × three governing labels produce exactly one
   localized bridge only in `feedback_available`.
2. Markup order is feedback → decision → next-version → continuity rail →
   evidence/boundary, with a resolvable unique heading id.
3. Ready/awaiting sessions omit the bridge; the old
   `practice-next-action--feedback_available` class remains absent.
4. No private answer/statement/ID/snapshot/URL/path/contact/credential or
   active control appears in the bridge or receipt.
5. CSS parity with `.superdesign/init/theme.md` and all responsive/a11y/print
   contracts are tested; README and interview-map describe the manual bridge.
