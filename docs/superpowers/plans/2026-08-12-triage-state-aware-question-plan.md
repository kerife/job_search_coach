# State-aware recruiter triage question plan

## Goal

Align the rendered question surface with triage state so the candidate sees one
question when clarification is required, one question in the ready handoff,
and no continuation question after a stop decision.

## Tasks

- [ ] Add EN/ES state-specific renderer assertions and verify RED against the
  current unconditional section.
- [ ] Gate the standalone question section on `clarify_first` only.
- [ ] Update the renderer contract documentation and run focused/full suites.
- [ ] Run static, privacy, release, cache, and installed smoke gates; publish
  and reload the plugin.

## Boundaries

No schema, validator, question text, handoff packet, IDs, external actions, or
visual layout changes are in scope.
