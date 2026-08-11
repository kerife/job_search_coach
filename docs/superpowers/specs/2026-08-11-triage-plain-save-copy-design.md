# Triage Plain Save Copy Design

## Context

The private recruiter triage renderer correctly keeps `delivery.local_save_mode`
as an internal closed enum, but its footer currently exposes the literal
`local_save_mode=disabled` to employees. That is implementation vocabulary,
not a useful user-facing explanation, and it is read aloud by assistive
technology.

## Decision

Keep the schema and validator value unchanged. Replace only the localized
visible footer labels with plain outcome copy:

- English: `Nothing is saved on this device.`
- Spanish: `No se guarda nada en este dispositivo.`

The sentence remains visible in ready, clarify, and stop states and remains
inside the printable footer. It does not change triage state, external-action
behavior, privacy validation, or the stop-specific employment boundary.

## Alternatives and trade-off

Keeping the enum is rejected because it exposes schema vocabulary. “Local
saving is disabled for privacy” is clearer than the current label but adds a
causal claim that the renderer does not need to make. The selected sentence
states only the observable storage boundary.

## Verification

EN/ES ready, clarify, and stop renders must contain the plain sentence exactly
once, contain no `local_save_mode=` or old copy, and preserve internal fixture
validation of `delivery.local_save_mode=disabled`. Existing HTML structure,
print visibility, forced-colors/dark hooks, no-action guarantees, and stop
continuity copy remain unchanged.
