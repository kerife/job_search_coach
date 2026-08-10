# Recruiter question order design

## Goal

Make the concrete safe question appear immediately after the manual re-entry cue in a ready private recruiter triage card, before the input receipt.

## Boundaries

- Renderer/order-only change; no schema, routing, persistence, or authorization changes.
- Ready cards keep exactly one escaped safe question and omit it for clarify/stop.
- English and Spanish output preserve existing labels, privacy prohibitions, accessibility, print, mobile, and forced-colors behavior.
- The receipt remains present, but follows the preview so administrative input guidance does not interrupt the decision.

## Acceptance evidence

The focused renderer tests assert `next_step < preview < receipt` for both ready fixtures, preserve ready-only rendering and omission in clarify/stop, and continue rejecting IDs, links, actions, calendar language, and duplicate question marks. The full renderer suite and diff check must pass before release.
