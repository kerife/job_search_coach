# Recruiter Receipt Manual Next Step Design

## Problem

Conversion outcome and follow-through checkpoint receipts can display the
validated action `route_to_prepare-role-interviews` as “Route to interview
preparation” / “Dirige a preparación de entrevista”, but the offline artifact
does not explain how a person should continue. The receipt has no controls by
design, so the route label becomes a dead end after a high-intent milestone.

## Decision

Add a static, named continuation region immediately after the facts/boundary
content, rendered only when the validated next-safe-action is
`route_to_prepare-role-interviews`:

- EN heading: `Manual next step`
- EN copy: `Return to the private Codex conversation, re-enter interview preparation manually, and answer the one safe recruiter-screen question. This receipt does not contact, send, or schedule anything.`
- ES heading: `Siguiente paso manual`
- ES copy: `Regresa a la conversación privada de Codex, vuelve a entrar manualmente a la preparación de entrevista y responde la única pregunta segura de filtro inicial. Este recibo no contacta, envía ni agenda nada.`

Use the existing receipt card/facts/boundary visual language and a semantic
`section` with a unique localized heading ID. Do not add a button, link, form,
icon, score, progress indicator, raw IDs, route enum, candidate prose, or
filesystem path. Clarify, stop, and already-manual states omit the region.

## Surfaces and accessibility

Apply the same renderer contract to conversion outcome and follow-through
checkpoint. Extend only existing asset CSS hooks for spacing, print atomicity,
preferred contrast, and forced-color system boundaries; keep 320px reflow and
the current no-external-action boundary. The region is informational and must
not create a new interactive surface.

## Verification

TDD tests cover route-valued EN/ES outcome and checkpoint fixtures, omission for
clarify/stop/manual states, v2 locale behavior, exact copy once, no raw enum or
interactive element, accessible naming, print/forced-color hooks, and 320px
render contracts. Existing validator, privacy, and atomic-write behavior stays
unchanged.
