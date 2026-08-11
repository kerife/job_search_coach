# Compact receipt contrast design

## Context

The private follow-through checkpoint and conversion outcome receipts support
print, reduced motion, and forced colors, but they do not provide a
`prefers-contrast: more` treatment. The local design system requires that mode
to preserve hierarchy for users who request stronger contrast.

## Decision

Add one CSS-only `@media (prefers-contrast: more)` block to each compact receipt
stylesheet:

- `.checkpoint-card` / `.outcome-card` receive a 2px ink border and no shadow.
- fact-row top borders become 2px ink borders.
- `.checkpoint-boundary` / `.outcome-boundary` use a thicker accent marker and
  ink-colored text.

The change is semantic styling only. It does not alter copy, locale selection,
stop-decision continuity disclaimers, HTML structure, schemas, print rules,
forced-colors rules, network behavior, or external actions.

## Acceptance

1. Both CSS files contain one `prefers-contrast: more` block with the card,
   facts, and boundary selectors.
2. Existing EN/ES render tests and stop/non-stop copy remain unchanged.
3. Focused CSS assertions pass for both assets; compact receipt, plugin,
   privacy, static, and release gates remain green.
4. No new forms, links, scripts, remote resources, or data fields are added.

## Limitation

No browser screenshot or operating-system high-contrast capture is claimed when
the local-file browser policy blocks the artifact. Static CSS and renderer
assertions are the evidence for this increment.
