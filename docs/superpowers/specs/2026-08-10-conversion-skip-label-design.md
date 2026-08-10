# Conversion skip label design

## Goal

Give the private conversion-outcome skip link a localized action label while preserving the visual kicker separately.

## Scope

Add a closed `skip` copy value for EN/ES, use it only in the anchor, and keep `kicker` in the visible header. Preserve `href="#main-content"`, focusable main target, CSP, offline/no-action output, and all privacy rules. No schema or routing changes.

## Acceptance

Both locales render a localized “skip to main content” action, the kicker is not inside the anchor, and deterministic renderer/contract tests plus diff/static checks pass.
