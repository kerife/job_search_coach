# Executive dossier copy-status accessibility

## Goal

Make copy results perceivable without changing the private, draft-only
behavior of executive dossier copy controls.

## Contract

- Every copyable card keeps the stable button name `Copiar borrador` (or the
  existing localized equivalent).
- Each button references an adjacent status node with `aria-describedby`.
- The status node uses `role="status"`, `aria-live="polite"`, and
  `aria-atomic="true"`.
- Success and failure messages are fixed localized copy; draft text is never
  echoed into status, attributes, or logs.
- Print output hides the control and status through the existing `no-print`
  boundary. No network, persistence, or authorization behavior changes.
- Cards marked `Necesita confirmación` remain visibly marked; copy remains a
  private draft action and receives an accessible boundary description.

## Acceptance

1. Each copy button points to exactly one live status node.
2. JavaScript updates only the generic status message and leaves the button
   accessible name stable on success and fallback failure.
3. Both locales render the status semantics and confirmation boundary.
4. Existing privacy, CSP, print, and deterministic-rendering tests remain
   green.
