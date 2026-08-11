# Plan: close candidate identity leakage in triage

1. Add a focused validator/renderer regression using the canonical clarify
   fixture and mutate each prose field with an explicit candidate-name marker.
2. Run the focused test to confirm RED against the current validator.
3. Extend only the existing identity regex with bounded English/Spanish
   candidate markers; preserve generic candidate evidence prose.
4. Run focused triage/privacy/schema/renderer tests and the full plugin/root
   gates.
5. Bump the plugin cachebuster once, install the canonical marketplace entry,
   compare source/cache exactly, run installed smoke, refresh provenance and
   attestation, and rerun final gates.
