# Compact Receipt Forced-Colors Surfaces

## Goal

Make compact receipts explicit and readable in forced-colors mode, matching
the system-color contract used by the dossier and practice artifacts.

## Contract

Under `@media (forced-colors: active)`, each receipt card uses
`background: Canvas; color: CanvasText`, and its boundary uses
`color: CanvasText`. Existing CanvasText borders, left markers, print rules,
and normal-mode copy remain unchanged.

## Acceptance

- Checkpoint and outcome renders expose the explicit system-color declarations.
- Theme dumps match both source stylesheets.
- EN/ES copy, ARIA, print, mobile, and no-action boundaries remain unchanged.
