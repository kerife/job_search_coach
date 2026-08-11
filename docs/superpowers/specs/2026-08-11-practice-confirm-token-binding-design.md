# Practice Confirm Dark Token Binding

## Context

The dark practice stylesheet uses `var(--gold-soft)` for the confirm feedback
panel, but the token is not declared. Browsers therefore discard the override
and retain the light panel background while dark text is applied. The current
test is a false positive because it checks the declaration text and compares
hard-coded colors that are not connected to the stylesheet token.

## Design

Declare `--gold-soft: #3b301f` in the practice dark `:root`, keep the existing
confirm-panel selector, and copy the exact CSS block into the Superdesign theme
dump. Update the accessibility test to parse the dark token declaration and
calculate contrast from that declared value against `--ink`; the test must fail
if the token is missing or the selector points at an undeclared token.

## Boundaries

- No DOM, copy, schema, action, or state changes.
- No changes to print, reduced-motion, or forced-colors behavior.
- The compact/dossier palettes remain unchanged.
- Browser computed-style evidence is deferred because the current environment
  cannot open the local `file://` artifacts in a shared browser tab.

## Acceptance

1. RED reproduces the missing `--gold-soft` declaration.
2. GREEN declares `--gold-soft: #3b301f` before the confirm override.
3. The test derives both foreground and background from CSS tokens and proves a
   contrast ratio of at least 4.5:1.
4. The theme dump and shipped CSS are byte-parity synchronized.
5. Practice rendering, dark-mode tests, static checks, full plugin tests, and
   the installed smoke remain green.
